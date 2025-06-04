"""
closure_engine.py
-----------------
Runs the three execution steps of the Re-SHACL graph–merging algorithm:

    Step 1  (extraction)   – already handled in extract_merge_inputs()
    Step 2 · Phase 1       – class–related reasoning
    Step 2 · Phase 2       – property–path reasoning
    Step 3                – owl:sameAs entity merging
    Step 4                – shape rewriting (TBD)

The loop iterates Phase 1 ➝ Phase 2 ➝ Same-As merge ➝ node-expansion until
no new triples / classes / paths / focus nodes are added.
"""

import logging
from rdflib import RDF, RDFS, OWL, Namespace
from pyshacl.consts import SH_path, SH_node

from src.core.owl_semantics.domain_range import target_domain_range, target_range
from ..core.merging import merge_same_focus, merge_same_property, merge_target_classes
from ..utils.merge_helpers import (
    all_focus_merged,
    all_samePath_merged,
    all_targetClasses_merged,   # kept for debugging / unit-tests
)

from ..types import GraphsBundle
from ..types.merge_inputs import MergeInputs

# --- SHACL constants ----------------------------------------------------
SH = Namespace("http://www.w3.org/ns/shacl#")
SH_class = SH["class"]

# --- logging ------------------------------------------------------------
log = logging.getLogger(__name__)

# ---- algorithm constants ----------------------------------------------
MAX_PASSES       = 25_000   # absolute safety valve
STABLE_THRESHOLD = 2        # identical snapshots ⇒ convergence


# ----------------------------------------------------------------------- #
#  Public entry point
# ----------------------------------------------------------------------- #
def run_closure_loop(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    """
    Executes Phase 1 → Phase 2 inside a fix-point loop, then performs a final
    subclass/subproperty closure.

    Args
    ----
    graphs : GraphsBundle       The data + shapes graph bundle.
    inputs : MergeInputs        The C, P, F, N structures extracted earlier.
    """
    g  = graphs.data_graph
    sg = graphs.shapes_graph
    shapes = sg.shapes

    prev_snap, stable = _snapshot(g, inputs), 0
    log.debug("closure-loop start  | %s", prev_snap)

    for passes in range(1, MAX_PASSES + 1):
        _run_phase_1_class_reasoning(g, inputs)
        _run_phase_2_property_reasoning(graphs, inputs)
        _run_step_3_same_as(g, sg, shapes, inputs)
        _expand_discovered_focus_nodes(g, inputs)

        snap = _snapshot(g, inputs)
        log.debug("iteration %-6d | %s", passes, snap)

        if snap == prev_snap:
            stable += 1
            if stable >= STABLE_THRESHOLD:
                break
        else:
            stable = 0
        prev_snap = snap
    else:
        raise RuntimeError("closure_loop exceeded MAX_PASSES without convergence")

    # final local closures (subClassOf / subPropertyOf)
    _add_subclass_closure(g, inputs.focus_nodes)
    _add_subproperty_closure(g, inputs.focus_nodes)
    log.debug("closure-loop done   | %s", _snapshot(g, inputs))


# ----------------------------------------------------------------------- #
#  Phase 1  — class-related reasoning
# ----------------------------------------------------------------------- #
def _run_phase_1_class_reasoning(g, inputs: MergeInputs) -> None:
    log.debug("Phase 1  (class)")
    target_domain_range(g, inputs.focus_nodes, inputs.same_as_dict, inputs.target_classes)
    _add_subclass_closure(g, inputs.focus_nodes)
    merge_target_classes(g, inputs.focus_nodes, inputs.same_as_dict, inputs.target_classes)
    target_range(g, inputs.focus_nodes, inputs.same_as_dict, inputs.target_classes)


# ----------------------------------------------------------------------- #
#  Phase 2  — property-path reasoning
# ----------------------------------------------------------------------- #
def _run_phase_2_property_reasoning(graphs: GraphsBundle, inputs: MergeInputs) -> None:
    log.debug("Phase 2  (properties)")
    g = graphs.data_graph
    merge_same_property(graphs, inputs)
    _add_subproperty_closure(g, inputs.focus_nodes)


# ----------------------------------------------------------------------- #
#  Step 3   — owl:sameAs entity merging
# ----------------------------------------------------------------------- #
def _run_step_3_same_as(g, sg, shapes, inputs: MergeInputs) -> None:
    log.debug("Step 3   (sameAs merge)")
    target_nodes = set(inputs.same_as_dict.keys())
    for node in list(inputs.focus_nodes):
        while not all_focus_merged(g, node, inputs.focus_nodes):
            merge_same_focus(g, inputs.same_as_dict, node, target_nodes, shapes, sg)


# ----------------------------------------------------------------------- #
#  Helper functions
# ----------------------------------------------------------------------- #
def _snapshot(g, inputs: MergeInputs) -> tuple[int, int, int, int]:
    """ (#triples, |C|, |F|, |P| ) """
    return len(g), len(inputs.target_classes), len(inputs.property_paths), len(inputs.focus_nodes)


def _expand_discovered_focus_nodes(g, inputs: MergeInputs) -> None:
    new = {
        obj
        for p in _shape_path_properties(g)
        for obj in g.objects(None, p)
        if obj not in inputs.focus_nodes
    }
    if new:
        for n in new:
            inputs.focus_nodes.add(n)
            inputs.same_as_dict[n] = set()
        log.debug("  +%d new focus nodes", len(new))


def _shape_path_properties(g):
    return {
        p
        for s, p, _ in g.triples((None, SH_path, None))
        if (s, SH_node, None) in g or (s, SH_class, None) in g
    }


def _add_subproperty_closure(g, focus_nodes: set) -> None:
    for node in focus_nodes:
        for p, o in g.predicate_objects(node):
            for super_p in g.transitive_objects(p, RDFS.subPropertyOf):
                if super_p != p:
                    g.add((node, super_p, o))


def _add_subclass_closure(g, focus_nodes: set) -> None:
    for node in focus_nodes:
        for cls in g.objects(node, RDF.type):
            if (cls, RDF.type, RDF.Property) in g or (cls, RDF.type, OWL.ObjectProperty) in g:
                continue
            for super_cls in g.transitive_objects(cls, RDFS.subClassOf):
                if super_cls != cls:
                    g.add((node, RDF.type, super_cls))
