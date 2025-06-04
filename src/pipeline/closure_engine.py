from rdflib import RDFS, RDF, OWL

from src.core.owl_semantics.domain_range import target_domain_range, target_range
from ..core.merging import (
    merge_same_focus,
    merge_same_property,
    merge_target_classes,
)
from ..utils.merge_helpers import (
    all_focus_merged,
    all_samePath_merged,
    all_targetClasses_merged,
)

from ..types import GraphsBundle, ShapeTargets

# -------------------------------------------------------------
# closure_engine.py  –  updated run_closure_loop (v2, stable)
# -------------------------------------------------------------
from rdflib.namespace import RDFS

MAX_PASSES          = 25_000   # absolute safety valve
STABLE_THRESHOLD    = 2        # how many identical snapshots ⇒ convergence


def _snapshot(g, targets):
    """Returns an (int, int, int, int) = (#triples, #classes, #paths, #focus)."""
    return (
        len(g),
        len(targets.target_classes),
        len(targets.property_paths),
        len(targets.focus_nodes),
    )


def run_closure_loop(graphs: GraphsBundle, shapes, targets: ShapeTargets):
    """
    Alternating materialisation / merge loop that finishes when the graph
    and all convergence-relevant target sets have stopped growing.
    """
    g  = graphs.data_graph
    sg = graphs.shapes_graph

    # ---------- bootstrap -------------------------------------------------
    target_domain_range(
        g, targets.focus_nodes, targets.same_as_dict, targets.target_classes
    )
    _resolve_all_same_as_clusters(g, sg, shapes, targets)

    # ---------- main fixed-point iteration --------------------------------
    prev_snap      = _snapshot(g, targets)
    stable_counter = 0

    for passes in range(1, MAX_PASSES + 1):

        # -- step 1: class / property merges --------------------------------
        merge_target_classes(
            g,
            targets.focus_nodes,
            targets.same_as_dict,
            targets.target_classes,
        )

        target_range(
            g, targets.focus_nodes, targets.same_as_dict, targets.target_classes
        )

        merge_same_property(
            g,
            targets.property_paths,
            targets.focus_nodes,
            targets.same_as_dict,
            targets.target_classes,
            shapes,
            targets.property_shape_nodes,
            sg,
        )

        # -- step 2: local RDFS/OWL closures --------------------------------
        _add_subclass_closure(g, targets.focus_nodes)
        _add_subproperty_closure(g, targets.focus_nodes)

        # -- step 3: sameAs cluster reduction -------------------------------
        _resolve_all_same_as_clusters(g, sg, shapes, targets)

        # -- step 4: bring in any newly discovered focus nodes --------------
        _expand_discovered_focus_nodes(g, targets)

        # -- step 5: did *anything* grow? -----------------------------------
        snap = _snapshot(g, targets)

        if snap == prev_snap:
            stable_counter += 1
            if stable_counter >= STABLE_THRESHOLD:
                # Graph + targets stable → done
                return
        else:
            stable_counter = 0  # reset   – still making progress

        prev_snap = snap

    # ----------------------------------------------------------------------
    # exceeded MAX_PASSES
    raise RuntimeError(
        f"run_closure_loop: exceeded {MAX_PASSES} iterations without convergence "
        f"(last snapshot {prev_snap})"
    )



def _resolve_all_same_as_clusters(g, sg, shapes, targets: ShapeTargets):
    for node in list(targets.focus_nodes):
        while not all_focus_merged(g, node, targets.focus_nodes):
            merge_same_focus(g, targets.same_as_dict, node, targets.target_nodes, shapes, sg)

def _closure_converged(g, targets: ShapeTargets) -> bool:
    return all_targetClasses_merged(g, targets.target_classes) and all_samePath_merged(g, targets.property_paths)

def _expand_discovered_focus_nodes(g, targets: ShapeTargets) -> bool:
    new_nodes = []
    for path in targets.shape_path_properties:
        for obj in g.objects(None, path):
            if obj not in targets.focus_nodes:
                new_nodes.append(obj)

    if new_nodes:
        for obj in new_nodes:
            targets.focus_nodes.add(obj)
            targets.same_as_dict[obj] = set()
        return True
    return False

def _add_subproperty_closure(g, focus_nodes: set):
    for node in focus_nodes:
        for p, o in g.predicate_objects(node):
            for super_p in g.transitive_objects(p, RDFS.subPropertyOf):
                if super_p != p:
                    g.add((node, super_p, o))

def _add_subclass_closure(g, focus_nodes: set):
    for node in focus_nodes:
        for cls in g.objects(node, RDF.type):
            # Skip if cls is a property (avoid corrupting graph)
            if (cls, RDF.type, RDF.Property) in g or (cls, RDF.type, OWL.ObjectProperty) in g:
                continue
            for super_cls in g.transitive_objects(cls, RDFS.subClassOf):
                if super_cls != cls:
                    g.add((node, RDF.type, super_cls))
