from ..core.domain_range import target_domain_range, target_range
from ..core.merge import (
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
    focus_targets,
    class_targets,
    paths,
    same_nodes,
    shape_linked_targets,
    target_nodes,
    target_properties,
):
    target_domain_range(vg, focus_targets, same_nodes, class_targets)

    for node in focus_targets:
        while not all_focus_merged(vg, node, focus_targets):
            merge_same_focus(vg, same_nodes, node, target_nodes, shapes, shape_graph)

    while not all_targetClasses_merged(vg, class_targets) or not all_samePath_merged(vg, paths):
        merge_target_classes(vg, focus_targets, same_nodes, class_targets)
        target_range(vg, focus_targets, same_nodes, class_targets)

        merge_same_property(
            vg,
            paths,
            focus_targets,
            same_nodes,
            class_targets,
            shapes,
            target_properties,
            shape_graph
        )

        for node in focus_targets:
            while not all_focus_merged(vg, node, focus_targets):
                merge_same_focus(vg, same_nodes, node, target_nodes, shapes, shape_graph)

        for path in shape_linked_targets:
            for obj in vg.objects(None, path):
                if obj not in focus_targets:
                    focus_targets.add(obj)
                    same_nodes[obj] = set()

    from rdflib.namespace import RDFS
    for node in focus_targets:
        for p, o in vg.predicate_objects(node):
            for super_p in vg.transitive_objects(p, RDFS.subPropertyOf):
                if super_p != p:
                    vg.add((node, super_p, o))
