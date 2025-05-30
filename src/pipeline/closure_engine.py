from rdflib import RDFS

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


def run_closure_loop(graphs: GraphsBundle, shapes, targets: ShapeTargets):
    g = graphs.data_graph
    sg = graphs.shapes_graph

    # Phase 1: Domain/range expansion
    target_domain_range(g, targets.focus_nodes, targets.same_as_dict, targets.target_classes)

    # Phase 2: Resolve owl:sameAs clusters
    _resolve_all_same_as_clusters(g, sg, shapes, targets)

    # Phase 3: Closure loop over classes and properties
    while not _closure_converged(g, targets):
        merge_target_classes(g, targets.focus_nodes, targets.same_as_dict, targets.target_classes)
        target_range(g, targets.focus_nodes, targets.same_as_dict, targets.target_classes)

        merge_same_property(
            g,
            targets.property_paths,
            targets.focus_nodes,
            targets.same_as_dict,
            targets.target_classes,
            shapes,
            targets.property_shape_nodes,
            sg
        )

        _resolve_all_same_as_clusters(g, sg, shapes, targets)

        if _expand_discovered_focus_nodes(g, targets):
            continue  # Restart loop if expansion occurred

    # Phase 4: RDFS subPropertyOf closure
    _add_subproperty_closure(g, targets.focus_nodes)


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
