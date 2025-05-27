# utils/shape_utils.py
from rdflib.namespace import RDF, RDFS, OWL, SH
from ..constants import (
    SH_CLASS,
    SH_NODE,
    SH_PATH,
    SH_TARGETNODE,
    RDFS_SUBCLASSOF,
    RDFS_SUBPROPERTYOF,
)

def collect_focus_nodes(shapes, data_graph):
    focus_nodes = set()
    for shape in shapes:
        focus_nodes.update(shape.focus_nodes(data_graph))
    return focus_nodes

def collect_target_classes(shapes):
    target_classes = set()
    for shape in shapes:
        target_classes.update(shape.target_classes())
        target_classes.update(shape.implicit_class_targets())
    return target_classes

def collect_property_paths(shapes):
    path_values = set()
    for shape in shapes:
        for prop in shape.property_shapes():
            path_values.update(shape.sg.graph.objects(prop, SH_PATH))
    return path_values

def collect_shape_linked_paths(shapes):
    shape_paths = set()
    for shape in shapes:
        for prop in shape.property_shapes():
            if any(shape.sg.graph.objects(prop, SH_NODE)):
                shape_paths.update(shape.sg.graph.objects(prop, SH_PATH))
    return shape_paths

def collect_shape_classes(shapes):
    shape_classes = set()
    for shape in shapes:
        for prop in shape.property_shapes():
            shape_classes.update(shape.sg.graph.objects(prop, SH_CLASS))
    return shape_classes

def collect_target_nodes(shapes):
    target_nodes = set()
    for shape in shapes:
        target_nodes.update(shape.target_nodes())
    return target_nodes

def expand_subproperties(graph, properties):
    expanded = set(properties)
    for prop in properties:
        for sub in graph.transitive_objects(prop, RDFS_SUBPROPERTYOF):
            if sub != prop:
                expanded.add(sub)
    return expanded

def expand_subclasses(graph, classes):
    expanded = set(classes)
    for cls in classes:
        for sub in graph.transitive_subjects(RDFS_SUBCLASSOF, cls):
            if sub != cls:
                expanded.add(sub)
    return expanded

def extract_shape_paths_and_targets(shapes, graph):
    """
    Helper that returns:
    - target_nodes
    - target_classes (explicit + SHACL-inferred)
    - path_values (property shapes)
    - shape_linked_paths (via sh:node)
    """
    target_nodes = collect_target_nodes(shapes)
    target_classes = collect_target_classes(shapes)
    shape_classes = collect_shape_classes(shapes)
    target_classes.update(shape_classes)

    path_values = collect_property_paths(shapes)
    shape_linked_paths = collect_shape_linked_paths(shapes)

    path_values = expand_subproperties(graph, path_values)
    target_classes = expand_subclasses(graph, target_classes)

    for p in shape_linked_paths:
        for x in graph.objects(None, p):
            target_nodes.add(x)

    return target_nodes, target_classes, path_values, shape_linked_paths
