from rdflib import RDFS

from ..core.domain_range import target_domain_range, target_range
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


def run_closure_loop(
    vg,
    shape_graph,
    shapes,
    found_node_targets,
    target_classes,
    path_value,
    same_nodes,
    shape_path_properties,
    target_nodes,
    property_shape_nodes
):
    target_domain_range(vg, found_node_targets, same_nodes, target_classes)

    for focus_node in list(found_node_targets):
        while not all_focus_merged(vg, focus_node, found_node_targets):
            merge_same_focus(vg, same_nodes, focus_node, target_nodes, shapes, shape_graph)

    while (not all_targetClasses_merged(vg, target_classes)) or (not all_samePath_merged(vg, path_value)):
        merge_target_classes(vg, found_node_targets, same_nodes, target_classes)
        target_range(vg, found_node_targets, same_nodes, target_classes)

        merge_same_property(
            vg,
            path_value,
            found_node_targets,
            same_nodes,
            target_classes,
            shapes,
            property_shape_nodes,
            shape_graph
        )

        for focus_node in list(found_node_targets):
            while not all_focus_merged(vg, focus_node, found_node_targets):
                merge_same_focus(vg, same_nodes, focus_node, target_nodes, shapes, shape_graph)

        for path in shape_path_properties:
            for obj in vg.objects(None, path):
                if obj not in found_node_targets:
                    found_node_targets.add(obj)
                    same_nodes[obj] = set()

    for node in found_node_targets:
        for p, o in vg.predicate_objects(node):
            for super_p in vg.transitive_objects(p, RDFS.subPropertyOf):
                if super_p != p:
                    vg.add((node, super_p, o))
