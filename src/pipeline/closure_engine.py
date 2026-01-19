"""
closure_engine.py
-----------------
Runs the three execution steps of the Re-SHACL graph–merging algorithm.
"""

import logging
from rdflib import RDF, RDFS, OWL, Namespace
from pyshacl.consts import SH_path, SH_node

from src.core.owl_semantics.domain_range import target_domain_range, target_range
from ..core.merging import merge_same_focus, merge_same_property, merge_target_classes
from ..utils.merge_helpers import (
    all_focus_merged,
    all_samePath_merged,
    all_targetClasses_merged, print_not_merged_status,
)
from ..utils.safe_transitive import safe_transitive_objects

from ..my_types import GraphsBundle
from ..my_types.merge_inputs import MergeInputs

# --- SHACL constants ----------------------------------------------------
SH = Namespace("http://www.w3.org/ns/shacl#")
SH_class = SH["class"]

# --- logging ------------------------------------------------------------
log = logging.getLogger(__name__)

# ---- algorithm constants ----------------------------------------------
MAX_PASSES = 50_000
STABLE_THRESHOLD = 10


def run_closure_loop(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    """
    Executes Phase 1 → Phase 2 inside a fix-point loop, then performs a final
    subclass/subproperty closure.
    """
    g = graphs.data_graph
    sg = graphs.shapes_graph
    shapes = sg.shapes

    prev_snap, stable = _snapshot(g, inputs), 0
    log.debug("closure-loop start  | %s", prev_snap)

    passes = 0

    # Initial domain/range inference (before main loop, matching original)
    target_domain_range(g, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)

    # Initial focus node merge (before main loop, matching original)
    # Merge ALL nodes with sameAs relationships, not just discovered_focus_nodes
    # We need to merge them completely, ignoring discovered_focus_nodes restriction
    _merge_all_initial_same_as(graphs, inputs)

    while _not_converged(g, inputs):
        passes += 1
        print(f"ENTERING PASS {passes}")
        if passes > MAX_PASSES:
            raise RuntimeError("closure_loop exceeded MAX_PASSES")

        print("running phase 1")
        _run_phase_1_class_reasoning(g, inputs)
        print("running phase 2")
        _run_phase_2_property_reasoning(graphs, inputs)
        print("running step 3")
        _run_step_3_same_as(graphs, inputs)
        print("running focus node expansion")
        _expand_discovered_focus_nodes(g, inputs)
        print("taking snapshot")
        snap = _snapshot(g, inputs)
        log.debug("iteration %-6d | %s", passes, snap)

        if snap == prev_snap:
            stable += 1
            if stable >= STABLE_THRESHOLD and not _not_converged(g, inputs):
                break
        else:
            stable = 0
        prev_snap = snap

    # Final subproperty closure only (matching original behavior)
    _add_subproperty_closure(g, inputs.discovered_focus_nodes)

    log.debug("closure-loop done   | %s", _snapshot(g, inputs))


def _not_converged(g, inputs):
    not_merged_classes = not all_targetClasses_merged(g, inputs.target_classes)
    not_merged_paths = not all_samePath_merged(g, inputs.property_paths)

    if not_merged_classes or not_merged_paths:
        print_not_merged_status(g, inputs)

    return not_merged_classes or not_merged_paths


def _run_phase_1_class_reasoning(g, inputs: MergeInputs) -> None:
    log.debug("Phase 1  (class)")

    merge_target_classes(g, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)
    target_range(g, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)


def _run_phase_2_property_reasoning(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    log.debug("Phase 2  (properties)")
    merge_same_property(graphs, inputs)


def _run_step_3_same_as(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    log.debug("Step 3   (sameAs merge)")

    # Merge owl:sameAs for individuals, NOT properties
    # Properties are handled separately by property merging
    g = graphs.data_graph
    
    # Find all nodes involved in owl:sameAs relationships (materialize before iterating)
    all_sameas_nodes = {s for s, _, _ in g.triples((None, OWL.sameAs, None))} | \
                       {o for _, _, o in g.triples((None, OWL.sameAs, None))}
    
    # Filter out properties - same logic as in _merge_all_initial_same_as
    property_nodes = set()
    for s, p, o in g:
        if p != OWL.sameAs:
            property_nodes.add(p)
    
    # Also check for explicit property type declarations
    for node in all_sameas_nodes:
        if (node, RDF.type, OWL.ObjectProperty) in g or \
           (node, RDF.type, OWL.DatatypeProperty) in g or \
           (node, RDF.type, OWL.FunctionalProperty) in g or \
           (node, RDF.type, OWL.InverseFunctionalProperty) in g or \
           (node, RDF.type, RDF.Property) in g:
            property_nodes.add(node)
    
    individual_sameas_nodes = all_sameas_nodes - property_nodes
    
    # Merge each individual that has sameAs relationships
    for node in individual_sameas_nodes:
        while not all_focus_merged(g, node, inputs.discovered_focus_nodes):
            merge_same_focus(graphs, inputs, node)


def _snapshot(g, inputs: MergeInputs) -> tuple[int, int, int, int]:
    return len(g), len(inputs.target_classes), len(inputs.property_paths), len(inputs.discovered_focus_nodes)


def _merge_all_initial_same_as(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    """
    Merge all initial owl:sameAs relationships in the data graph.
    
    This function processes explicitly declared owl:sameAs triples and merges
    them completely, starting with nodes in discovered_focus_nodes first (to match original order).
    This matches the original behavior where focus nodes are processed before other nodes.
    
    IMPORTANT: Only processes individuals (focus nodes), not properties.
    Properties are handled separately by property merging.
    """
    g = graphs.data_graph
    
    # Find all nodes involved in owl:sameAs relationships
    all_sameas_nodes = {s for s, _, _ in g.triples((None, OWL.sameAs, None))} | \
                       {o for _, _, o in g.triples((None, OWL.sameAs, None))}
    
    # Filter out properties - only process individuals
    # Properties are nodes that appear as predicates in triples (except owl:sameAs itself)
    property_nodes = set()
    for s, p, o in g:
        if p != OWL.sameAs and p not in property_nodes:
            # p is used as a predicate, so it's a property
            property_nodes.add(p)
    
    # Also check for explicit property type declarations
    from rdflib import RDF
    for node in all_sameas_nodes:
        if (node, RDF.type, OWL.ObjectProperty) in g or \
           (node, RDF.type, OWL.DatatypeProperty) in g or \
           (node, RDF.type, OWL.FunctionalProperty) in g or \
           (node, RDF.type, OWL.InverseFunctionalProperty) in g or \
           (node, RDF.type, RDF.Property) in g:
            property_nodes.add(node)
    
    # IMPORTANT: If a node is sameAs to a property, it's also a property
    # This handles cases like schema:Name which isn't used as predicate but is sameAs to schema:name
    property_closure = set(property_nodes)
    for node in all_sameas_nodes:
        # Check if this node is connected to any property via sameAs
        connected_nodes = set(g.objects(node, OWL.sameAs)) | set(g.subjects(OWL.sameAs, node))
        if connected_nodes & property_nodes:
            property_closure.add(node)
    
    # Remove properties from the set of nodes to process
    individual_sameas_nodes = all_sameas_nodes - property_closure
    
    # Process focus nodes FIRST (to match original behavior)
    # Then process remaining nodes
    focus_nodes_to_process = [n for n in inputs.discovered_focus_nodes if n in individual_sameas_nodes]
    other_nodes_to_process = [n for n in individual_sameas_nodes if n not in inputs.discovered_focus_nodes]
    
    # Process in order: focus nodes first, then others
    for node in focus_nodes_to_process + other_nodes_to_process:
        # Keep merging while this node has unmerged sameAs relationships
        # Match original: merge while has outgoing edges OR incoming edges from non-focus nodes
        while not all_focus_merged(g, node, inputs.discovered_focus_nodes):
            merge_same_focus(graphs, inputs, node)
        
        # Add this node to discovered_focus_nodes if not already there
        if node not in inputs.discovered_focus_nodes:
            inputs.discovered_focus_nodes.add(node)
            inputs.same_as_dict.setdefault(node, set())


def _expand_discovered_focus_nodes(g, inputs: MergeInputs) -> None:
    # Find nodes reached via shape paths
    new = {
        obj
        for p in inputs.shape_path_properties
        for obj in g.objects(None, p)
        if obj not in inputs.discovered_focus_nodes
    }
    
    # Also add nodes involved in owl:sameAs relationships with existing focus nodes
    # (these can be created by functional/inverse functional properties)
    same_as_nodes = set()
    for focus in inputs.discovered_focus_nodes:
        # Nodes that are sameAs to existing focus nodes
        for other in g.objects(focus, OWL.sameAs):
            if other not in inputs.discovered_focus_nodes:
                same_as_nodes.add(other)
        for other in g.subjects(OWL.sameAs, focus):
            if other not in inputs.discovered_focus_nodes:
                same_as_nodes.add(other)
    
    new = new | same_as_nodes
    
    if new:
        for n in new:
            inputs.discovered_focus_nodes.add(n)
            # inputs.target_nodes.add(n)
            inputs.same_as_dict.setdefault(n, set())
        log.debug("  +%d new focus nodes", len(new))





def _add_subproperty_closure(g, discovered_focus_nodes: set) -> None:
    """
    Adds inferred triples via rdfs:subPropertyOf for all predicate-object pairs
    of all nodes in `discovered_focus_nodes`.

    Equivalent to the original vg.add(...) loop in merged_graph().
    """
    added_count = 0
    for node in discovered_focus_nodes:
        for p, o in g.predicate_objects(node):
            for super_p in safe_transitive_objects(g, p, RDFS.subPropertyOf):
                if super_p != p:
                    g.add((node, super_p, o))
                    added_count += 1
    print(f"[DEBUG] Superproperty closure: {len(discovered_focus_nodes)} focus nodes, added {added_count} triples")


def _add_subclass_closure(g, discovered_focus_nodes: set) -> None:
    """NOT USED - kept for reference only. Original doesn't add subclass closure."""
    for node in discovered_focus_nodes:
        for cls in g.objects(node, RDF.type):
            if (cls, RDF.type, RDF.Property) in g or (cls, RDF.type, OWL.ObjectProperty) in g:
                continue
            for super_cls in safe_transitive_objects(g, cls, RDFS.subClassOf):
                if super_cls != cls:
                    g.add((node, RDF.type, super_cls))
