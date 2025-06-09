from dataclasses import dataclass
from typing import Set, Dict
from rdflib import Graph, Namespace, RDFS
from rdflib.term import Node
from pyshacl.consts import SH_path, SH_node
from pyshacl.pytypes import GraphLike

from src.types.found_targets import FoundTargets
from src.types.graphs_bundle import GraphsBundle


SH = Namespace("http://www.w3.org/ns/shacl#")
SH_class = SH["class"]
RDFS_subPropertyOf = RDFS.subPropertyOf


@dataclass
class MergeInputs:
    target_classes: Set[Node]     # C
    discovered_focus_nodes: Set[Node]        # P
    property_paths: Set[Node]     # F
    same_as_dict: Dict[Node, Set[Node]]  # N
    found: FoundTargets


def extract_merge_inputs(graphs: GraphsBundle) -> MergeInputs:
    data_graph = graphs.data_graph
    shapes = graphs.shapes_graph.shapes

    target_classes, declared_target_nodes, initial_focus_nodes, property_paths, shape_path_properties = _extract_targets(shapes, data_graph)
    _expand_sub_properties(data_graph, property_paths)
    _expand_sub_classes(data_graph, target_classes)

    found = FoundTargets.from_initial_sets(
        data_graph=data_graph,
        declared_target_nodes=declared_target_nodes,
        target_classes=target_classes,
        shape_path_properties=shape_path_properties,
    )

    # Create focus_nodes: declared + referenced
    discovered_focus_nodes = set(initial_focus_nodes)
    discovered_focus_nodes.update(found.referenced_shape_targets)

    # Discover additional focus nodes dynamically
    _discover_additional_focus_nodes(data_graph, shape_path_properties, discovered_focus_nodes)

    # Initialize same_as_dict from current focus_nodes
    same_as_dict = {node: set() for node in discovered_focus_nodes}

    # Extend target_classes with subclass discovery
    target_classes.update(found.class_targets)

    # Set final declared_target_nodes into the found object
    found.declared_target_nodes.update(declared_target_nodes)

    return MergeInputs(
        target_classes=target_classes,
        discovered_focus_nodes=discovered_focus_nodes,
        property_paths=property_paths,
        same_as_dict=same_as_dict,
        found=found,
    )


def _extract_targets(shapes, data_graph: GraphLike):
    target_classes = set()
    property_paths = set()
    shape_path_properties = set()
    declared_target_nodes = set()
    initial_focus_nodes = set()

    for shape in shapes:
        # Static SHACL declarations
        declared_target_nodes.update(shape.target_nodes())

        # Evaluated focus nodes (based on target declarations in the shape)
        initial_focus_nodes.update(shape.focus_nodes(data_graph))

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

    return target_classes, declared_target_nodes, initial_focus_nodes, property_paths, shape_path_properties




def _expand_sub_properties(data_graph, property_paths: Set[Node]):
    expanded = set()
    for path in list(property_paths):
        supers = data_graph.transitive_objects(path, RDFS.subPropertyOf)
        subs   = data_graph.transitive_subjects(RDFS.subPropertyOf, path)
        expanded.update(supers)
        expanded.update(subs)
    property_paths.update(expanded)


def _expand_sub_classes(data_graph: GraphLike, target_classes: Set[Node]):
    extra = {
        sub
        for cls in target_classes
        for sub in data_graph.transitive_subjects(RDFS.subClassOf, cls)
        if sub != cls
    }
    target_classes.update(extra)


def _discover_additional_focus_nodes(data_graph: GraphLike, shape_path_properties: Set[Node], discovered_nodes: Set[Node]):
    for path in shape_path_properties:
        discovered_nodes.update(data_graph.objects(None, path))
