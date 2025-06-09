"""
focus_merging.py
----------------
Merge a cluster of owl:sameAs-equivalent *focus* nodes.

Side effects
============
1. **Data graph  (g)**
   • normalises owl:sameAs direction               («eq-sym»)
   • copies triples to the focus representative    («eq-rep-s», «eq-rep-o»)
   • removes duplicates / reflexive links

2. **Shapes graph (sg)**
   • rewrites sh:targetNode so shapes still point
     to the surviving representative

3. **Identity map  (same_as_dict)  i.e. N**
   • updates the set of originals per representative
"""

from __future__ import annotations
from rdflib import Graph, OWL
from pyshacl.consts import SH_targetNode
from typing import Set

from src.types import GraphsBundle
from src.types.merge_inputs import MergeInputs


def merge_same_focus(
    graphs: GraphsBundle,
    inputs: MergeInputs,
    focus,  # surviving representative
) -> None:
    """
    Merge all nodes owl:sameAs-equivalent to *focus* into *focus* itself.

    Side-effects
    ------------
    • graphs.data_graph   – triples copied / owl:sameAs normalised
    • graphs.shapes_graph – sh:targetNode rewritten
    • inputs.same_as_dict – identity map updated
    """
    g: Graph = graphs.data_graph
    sg_wrapper = graphs.shapes_graph
    sg: Graph = sg_wrapper.graph
    shapes = sg_wrapper.shapes

    same_as_dict = inputs.same_as_dict

    # -------------------------------------------------- 0. bookkeeping --
    same_as_dict.setdefault(focus, set())

    if not any(g.objects(focus, OWL.sameAs)) and not any(g.subjects(OWL.sameAs, focus)):
        return  # nothing to merge

    # -------------------------------------------------- 1. eq-sym -------
    _normalise_same_as_edges(g, focus)

    # -------------------------------------------------- 2. merge loop ---
    # Collect full sameAs transitive closure
    to_merge = set()
    stack = [focus]

    while stack:
        current = stack.pop()
        for neighbor in g.objects(current, OWL.sameAs):
            if neighbor != focus and neighbor not in to_merge:
                to_merge.add(neighbor)
                stack.append(neighbor)
        for neighbor in g.subjects(OWL.sameAs, current):
            if neighbor != focus and neighbor not in to_merge:
                g.remove((neighbor, OWL.sameAs, current))
                to_merge.add(neighbor)
                stack.append(neighbor)

    # Now merge all transitive nodes into focus
    for other in to_merge:
        _merge_equivalent_node(g, focus, other)
        _update_identity_map(same_as_dict, focus, other)
        _rewrite_shape_targets(shapes, sg, old=other, new=focus)
        g.remove((focus, OWL.sameAs, other))

    # -------------------------------------------------- 3. cleanup ------
    g.remove((focus, OWL.sameAs, focus))


# ====================================================================== #
#  Helper functions
# ====================================================================== #
def _normalise_same_as_edges(g: Graph, focus) -> None:
    """Flip  ?s owl:sameAs focus  →  focus owl:sameAs ?s   (eq-sym)."""
    for subj in list(g.subjects(OWL.sameAs, focus)):
        if subj != focus:
            g.remove((subj, OWL.sameAs, focus))
            g.add((focus, OWL.sameAs, subj))


def _merge_equivalent_node(g: Graph, focus, other) -> None:
    """Copy every triple that mentions *other* onto *focus*, skipping owl:sameAs."""
    for p, o in list(g.predicate_objects(other)):
        g.remove((other, p, o))
        if p != OWL.sameAs:
            g.add((focus, p, o))

    for s, p in list(g.subject_predicates(other)):
        g.remove((s, p, other))
        if p != OWL.sameAs:
            g.add((s, p, focus))



def _update_identity_map(same_as_dict, focus, other) -> None:
    """Add *other* (and its previous equivalents) to the focus entry in N."""
    same_set = same_as_dict[focus]
    same_set.add(other)

    if other in same_as_dict:
        same_set.update(same_as_dict[other])
        del same_as_dict[other]


def _rewrite_shape_targets(shapes, sg: Graph, *, old, new) -> None:
    """Rewrite sh:targetNode from *old* to *new* inside the shapes graph."""
    for shape in shapes:
        if (shape.node, SH_targetNode, old) in sg:
            sg.remove((shape.node, SH_targetNode, old))
            sg.add((shape.node, SH_targetNode, new))
