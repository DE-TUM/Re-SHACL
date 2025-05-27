from rdflib.namespace import RDFS, Namespace
from pyshacl.consts import SH_path, SH_node
from pyshacl.pytypes import GraphLike

SH = Namespace("http://www.w3.org/ns/shacl#")
SH_class = SH["class"]
RDFS_subPropertyOf = RDFS.subPropertyOf


def extract_targets_and_paths(shapes, vg: GraphLike):
    found_node_targets = set()
    target_classes = set()
    path_value = set()
    shape_linked_target = set()
    sh_class = set()
    target_nodes = set()

    for s in shapes:
        targets = s.target_nodes()
        target_nodes.update(targets)

        focus = s.focus_nodes(vg)
        found_node_targets.update(focus)
        target_classes.update(s.target_classes())
        target_classes.update(s.implicit_class_targets())

        target_property = set(s.property_shapes())

        if len(set(s.target_classes())) == 0:
            for prop in target_property:
                path_value.update(s.sg.graph.objects(prop, SH_path))

        for prop in target_property:
            if list(s.sg.graph.objects(prop, SH_node)):
                shape_linked_target.update(s.sg.graph.objects(prop, SH_path))
            if list(s.sg.graph.objects(prop, SH_class)):
                sh_class.update(s.sg.graph.objects(prop, SH_class))

        target_classes.update(sh_class)

        for prop in target_property:
            path_value.update(s.sg.graph.objects(prop, SH_path))

    # Closure over rdfs:subPropertyOf for paths
    extra_paths = set()
    for path in path_value:
        for super_prop in vg.transitive_objects(path, RDFS_subPropertyOf):
            if super_prop != path:
                extra_paths.add(super_prop)
    path_value.update(extra_paths)

    # Closure over rdfs:subClassOf for target classes
    extra_classes = set()
    for cls in target_classes:
        for subclass in vg.transitive_subjects(RDFS.subClassOf, cls):
            if subclass != cls:
                extra_classes.add(subclass)
    target_classes.update(extra_classes)

    # Add linked focus nodes from shape_linked_target
    for path in shape_linked_target:
        for obj in vg.objects(None, path):
            found_node_targets.add(obj)

    # Init same_nodes dictionary
    same_nodes = {node: set() for node in found_node_targets}

    return found_node_targets, target_classes, path_value, same_nodes, shape_linked_target, target_nodes
