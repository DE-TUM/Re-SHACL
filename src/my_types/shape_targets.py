# from dataclasses import dataclass
# from typing import Set, Dict
#
# from pyshacl import ShapesGraph
# from rdflib import Graph, Namespace, RDFS
# from rdflib.term import Node
# from pyshacl.consts import SH_path, SH_node
# from pyshacl.pytypes import GraphLike
#
# from src.types import GraphsBundle
#
# SH = Namespace("http://www.w3.org/ns/shacl#")
# SH_class = SH["class"]
# RDFS_subPropertyOf = RDFS.subPropertyOf
#
#
# @dataclass
# class ShapeTargets:
#     focus_nodes: Set[Node]
#     target_classes: Set[Node]
#     property_paths: Set[Node]
#     same_as_dict: Dict[Node, Set[Node]]
#     shape_path_properties: Set[Node]
#     target_nodes: Set[Node]
#     property_shape_nodes: Set[Node]
#
#     @classmethod
#     def from_graph_bundle(cls, graphs: GraphsBundle) -> "ShapeTargets":
#         st = cls._initialize_empty()
#         shapes_graph = ShapesGraph(graphs.shapes_graph, None)
#         shapes = shapes_graph.shapes
#
#         for shape in shapes:
#             cls._extract_targets_and_shapes(shape, graphs.data_graph, st)
#
#         cls._expand_sub_properties(graphs.data_graph, st)
#         cls._expand_sub_classes(graphs.data_graph, st)
#         cls._discover_additional_focus_nodes(graphs.data_graph, st)
#         cls._init_same_as_dict(st)
#
#         return st
#
#     @staticmethod
#     def _initialize_empty() -> "ShapeTargets":
#         return ShapeTargets(set(), set(), set(), {}, set(), set(), set())
#
#     @staticmethod
#     def _extract_targets_and_shapes(shape, data_graph: GraphLike, st: "ShapeTargets"):
#         st.target_nodes.update(shape.target_nodes())
#         st.focus_nodes.update(shape.focus_nodes(data_graph))
#
#         t_classes = set(shape.target_classes())
#         implicit = set(shape.implicit_class_targets())
#         st.target_classes.update(t_classes)
#         st.target_classes.update(implicit)
#
#         property_shapes = set(shape.property_shapes())
#         st.property_shape_nodes.update(property_shapes)
#
#         for ps in property_shapes:
#             paths = set(shape.sg.graph.objects(ps, SH_path))
#             st.property_paths.update(paths)
#
#             if not t_classes:
#                 st.property_paths.update(paths)
#
#             if list(shape.sg.graph.objects(ps, SH_node)):
#                 st.shape_path_properties.update(paths)
#             if list(shape.sg.graph.objects(ps, SH_class)):
#                 st.target_classes.update(shape.sg.graph.objects(ps, SH_class))
#
#     @staticmethod
#     def _expand_sub_properties(data_graph: GraphLike, st: "ShapeTargets"):
#         extra = set()
#         for path in st.property_paths:
#             for super_path in data_graph.transitive_objects(path, RDFS_subPropertyOf):
#                 if super_path != path:
#                     extra.add(super_path)
#         st.property_paths.update(extra)
#
#     @staticmethod
#     def _expand_sub_classes(data_graph: GraphLike, st: "ShapeTargets"):
#         extra = set()
#         for cls in st.target_classes:
#             for sub in data_graph.transitive_subjects(RDFS.subClassOf, cls):
#                 if sub != cls:
#                     extra.add(sub)
#         st.target_classes.update(extra)
#
#     @staticmethod
#     def _discover_additional_focus_nodes(data_graph: GraphLike, st: "ShapeTargets"):
#         for path in st.shape_path_properties:
#             for obj in data_graph.objects(None, path):
#                 st.focus_nodes.add(obj)
#
#     @staticmethod
#     def _init_same_as_dict(st: "ShapeTargets"):
#         st.same_as_dict = {node: set() for node in st.focus_nodes}
