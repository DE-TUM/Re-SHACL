from dataclasses import dataclass
from typing import Set, Dict
from rdflib import Graph, Namespace, RDFS
from rdflib.term import Node
from pyshacl.consts import SH_path, SH_node
from pyshacl.pytypes import GraphLike
from src.types.graphs_bundle import GraphsBundle


SH = Namespace("http://www.w3.org/ns/shacl#")
SH_class = SH["class"]
RDFS_subPropertyOf = RDFS.subPropertyOf


@dataclass
class MergeInputs:
    target_classes: Set[Node]     # C
    focus_nodes: Set[Node]        # P
    property_paths: Set[Node]     # F
    same_as_dict: Dict[Node, Set[Node]]  # N


def extract_merge_inputs(graphs: GraphsBundle) -> MergeInputs:
    data_graph = graphs.data_graph
    shapes = graphs.shapes_graph.shapes

    target_classes, focus_nodes, property_paths, target_nodes, shape_path_properties = _extract_targets(shapes, data_graph)
    _expand_sub_properties(data_graph, property_paths)
    _expand_sub_classes(data_graph, target_classes)
    _discover_additional_focus_nodes(data_graph, shape_path_properties, focus_nodes)

    same_as_dict = {node: set() for node in focus_nodes}

    return MergeInputs(
        target_classes=target_classes,
        focus_nodes=focus_nodes,
        property_paths=property_paths,
        same_as_dict=same_as_dict,
    )


def _extract_targets(shapes, data_graph: GraphLike):
    target_classes = set()
    focus_nodes = set()
    property_paths = set()
    target_nodes = set()
    shape_path_properties = set()

    for shape in shapes:
        target_nodes.update(shape.target_nodes())
        focus_nodes.update(shape.focus_nodes(data_graph))

        t_classes = set(shape.target_classes())
        implicit = set(shape.implicit_class_targets())
        target_classes.update(t_classes)
        target_classes.update(implicit)

        property_shapes = set(shape.property_shapes())
        for ps in property_shapes:
            paths = set(shape.sg.graph.objects(ps, SH_path))
            property_paths.update(paths)

            if not t_classes:
                property_paths.update(paths)

            if list(shape.sg.graph.objects(ps, SH_node)):
                shape_path_properties.update(paths)
            if list(shape.sg.graph.objects(ps, SH_class)):
                target_classes.update(shape.sg.graph.objects(ps, SH_class))

    return target_classes, focus_nodes, property_paths, target_nodes, shape_path_properties


def _expand_sub_properties(data_graph: GraphLike, property_paths: Set[Node]):
    extra = {
        super_path
        for path in property_paths
        for super_path in data_graph.transitive_objects(path, RDFS_subPropertyOf)
        if super_path != path
    }
    property_paths.update(extra)


def _expand_sub_classes(data_graph: GraphLike, target_classes: Set[Node]):
    extra = {
        sub
        for cls in target_classes
        for sub in data_graph.transitive_subjects(RDFS.subClassOf, cls)
        if sub != cls
    }
    target_classes.update(extra)


def _discover_additional_focus_nodes(data_graph: GraphLike, shape_path_properties: Set[Node], focus_nodes: Set[Node]):
    for path in shape_path_properties:
        focus_nodes.update(data_graph.objects(None, path))
