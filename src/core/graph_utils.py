# === core/graph_utils.py ===
from rdflib.namespace import RDFS, SH


def expand_paths(path_value, graph):
    extra = set()
    for p in path_value:
        for sub in graph.transitive_objects(p, RDFS.subPropertyOf):
            if sub != p:
                extra.add(sub)
    return extra


def expand_subclasses(classes, graph):
    extra = set()
    for c in classes:
        for sub in graph.transitive_subjects(RDFS.subClassOf, c):
            if sub != c:
                extra.add(sub)
    return extra


def extract_targets(shapes, graph):
    found_node_targets = set()
    target_classes = set()
    path_value = set()
    shape_linked_target = set()
    target_property = set()

    for s in shapes:
        found_node_targets.update(s.focus_nodes(graph))
        target_classes.update(s.target_classes())
        target_classes.update(s.implicit_class_targets())

        for prop in s.property_shapes():
            target_property.add(prop)
            path_value.update(s.sg.graph.objects(prop, SH.path))
            if list(s.sg.graph.objects(prop, SH.node)):
                shape_linked_target.update(s.sg.graph.objects(prop, SH.path))
            if list(s.sg.graph.objects(prop, SH.class_)):
                target_classes.update(s.sg.graph.objects(prop, SH.class_))

        if not s.target_classes():
            for prop in s.property_shapes():
                path_value.update(s.sg.graph.objects(prop, SH.path))

    return found_node_targets, target_classes, path_value, shape_linked_target, target_property