from core.loader import load_graph
from core.graph_utils import extract_targets, expand_subclasses, expand_paths
from core.merger import (
    target_domain_range, target_range,
    merge_same_focus, merge_same_property, merge_target_classes
)
from rules.consistency import all_focus_merged, all_targetClasses_merged, all_samePath_merged
from rdflib.namespace import RDFS, OWL


def merged_graph(data_graph, shacl_graph=None, data_graph_format=None, shacl_graph_format=None):
    shapes, named_graphs, shape_graph = load_graph(data_graph, shacl_graph, data_graph_format, shacl_graph_format)
    vg = named_graphs[0]
    shape_g = shape_graph.graph

    # === Initialize ===
    found_node_targets, target_classes, path_value, shape_linked_target, target_property = extract_targets(shapes, vg)
    same_nodes = {n: set() for n in found_node_targets}
    target_nodes = set(found_node_targets)

    # === Expand ===
    path_value.update(expand_paths(path_value, vg))
    target_classes.update(expand_subclasses(target_classes, vg))
    for p in shape_linked_target:
        for x in vg.objects(None, p):
            found_node_targets.add(x)
            if x not in same_nodes:
                same_nodes[x] = set()

    target_domain_range(vg, found_node_targets, same_nodes, target_classes)

    # === Merge sameAs nodes ===
    for focus in found_node_targets:
        while not all_focus_merged(vg, focus, found_node_targets):
            merge_same_focus(vg, same_nodes, focus, target_nodes, shapes, shape_g)

    # === Iterate ===
    while not all_targetClasses_merged(vg, target_classes) or not all_samePath_merged(vg, path_value):
        merge_target_classes(vg, found_node_targets, same_nodes, target_classes)
        target_range(vg, found_node_targets, same_nodes, target_classes)
        merge_same_property(vg, path_value, found_node_targets, same_nodes, target_classes, shapes, target_property, shape_g)

        for focus in found_node_targets:
            while not all_focus_merged(vg, focus, found_node_targets):
                merge_same_focus(vg, same_nodes, focus, target_nodes, shapes, shape_g)

        for p in shape_linked_target:
            for x in vg.objects(None, p):
                if x not in same_nodes:
                    found_node_targets.add(x)
                    same_nodes[x] = set()

    # === Add subProperty super triples ===
    for node in found_node_targets:
        for p, o in vg.predicate_objects(node):
            for sup in vg.transitive_objects(p, RDFS.subPropertyOf):
                if sup != p:
                    vg.add((node, sup, o))

    for s, same_set in same_nodes.items():
        for o in same_set:
            vg.add((s, OWL.sameAs, o))

    return vg, same_nodes, shape_g