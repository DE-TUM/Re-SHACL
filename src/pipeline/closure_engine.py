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

from ..types import GraphsBundle
from ..types.merge_inputs import MergeInputs

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

    _run_step_3_same_as(graphs, inputs)

    while _not_converged(g, inputs):
        passes += 1
        if passes > MAX_PASSES:
            raise RuntimeError("closure_loop exceeded MAX_PASSES")

        _run_phase_1_class_reasoning(g, inputs)
        _run_phase_2_property_reasoning(graphs, inputs)
        _run_step_3_same_as(graphs, inputs)
        _expand_discovered_focus_nodes(g, inputs)

        snap = _snapshot(g, inputs)
        log.debug("iteration %-6d | %s", passes, snap)

        if snap == prev_snap:
            stable += 1
            if stable >= STABLE_THRESHOLD and not _not_converged(g, inputs):
                break
        else:
            stable = 0
        prev_snap = snap
    else:
        raise RuntimeError("closure_loop exceeded MAX_PASSES without convergence")

    # Final merge cleanup – catches late-discovered sameAs
    for focus_node in list(inputs.discovered_focus_nodes):
        while not all_focus_merged(graphs.data_graph, focus_node):
            merge_same_focus(graphs, inputs, focus_node)

    _add_subclass_closure(g, inputs.discovered_focus_nodes)
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

    # old_size = len(inputs.discovered_focus_nodes)
    target_domain_range(g, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)
    # if len(inputs.discovered_focus_nodes) > old_size:
    #     inputs.target_nodes.update(inputs.focus_nodes)

    _add_subclass_closure(g, inputs.discovered_focus_nodes)
    merge_target_classes(g, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)

    # old_size = len(inputs.discovered_focus_nodes)
    target_range(g, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)
    # if len(inputs.focus_nodes) > old_size:
    #     inputs.target_nodes.update(inputs.focus_nodes)


def _run_phase_2_property_reasoning(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    log.debug("Phase 2  (properties)")
    merge_same_property(graphs, inputs)


def _run_step_3_same_as(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    log.debug("Step 3   (sameAs merge)")

    for focus_node in list(inputs.discovered_focus_nodes):
        while not all_focus_merged(graphs.data_graph, focus_node):
            merge_same_focus(graphs, inputs, focus_node)

    _add_subproperty_closure(graphs.data_graph, inputs.discovered_focus_nodes)


def _snapshot(g, inputs: MergeInputs) -> tuple[int, int, int, int]:
    return len(g), len(inputs.target_classes), len(inputs.property_paths), len(inputs.discovered_focus_nodes)


def _expand_discovered_focus_nodes(g, inputs: MergeInputs) -> None:
    new = {
        obj
        for p in _shape_path_properties(g)
        for obj in g.objects(None, p)
        if obj not in inputs.discovered_focus_nodes
    }
    if new:
        for n in new:
            inputs.discovered_focus_nodes.add(n)
            # inputs.target_nodes.add(n)
            inputs.same_as_dict.setdefault(n, set())
        log.debug("  +%d new focus nodes", len(new))


def _shape_path_properties(g):
    return {
        p
        for s, p, _ in g.triples((None, SH_path, None))
        if (s, SH_node, None) in g or (s, SH_class, None) in g
    }


def _add_subproperty_closure(g, discovered_focus_nodes: set) -> None:
    """
    Adds inferred triples via rdfs:subPropertyOf for all predicate-object pairs
    of all nodes in `found_node_targets`.

    Equivalent to the original vg.add(...) loop in merged_graph().
    """
    for node in discovered_focus_nodes:
        for p, o in g.predicate_objects(node):
            for super_p in g.transitive_objects(p, RDFS.subPropertyOf):
                if super_p != p:
                    g.add((node, super_p, o))


def _add_subclass_closure(g, discovered_focus_nodes: set) -> None:
    for node in discovered_focus_nodes:
        for cls in g.objects(node, RDF.type):
            if (cls, RDF.type, RDF.Property) in g or (cls, RDF.type, OWL.ObjectProperty) in g:
                continue
            for super_cls in g.transitive_objects(cls, RDFS.subClassOf):
                if super_cls != cls:
                    g.add((node, RDF.type, super_cls))
