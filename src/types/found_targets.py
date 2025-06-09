# src/types/found_targets.py
from dataclasses import dataclass, field
from typing import Set
from rdflib.term import Node
from rdflib import RDFS
from pyshacl.pytypes import GraphLike


@dataclass
class FoundTargets:
    declared_target_nodes: Set[Node] = field(default_factory=set)
    referenced_shape_targets: Set[Node] = field(default_factory=set)
    class_targets: Set[Node] = field(default_factory=set)

    @staticmethod
    def from_initial_sets(
            data_graph: GraphLike,
            declared_target_nodes: Set[Node],
            target_classes: Set[Node],
            shape_path_properties: Set[Node],
    ) -> "FoundTargets":
        referenced_shape_targets = {
            o
            for path in shape_path_properties
            for o in data_graph.objects(None, path)
        }

        class_targets = {
            sub
            for cls in target_classes
            for sub in data_graph.transitive_subjects(RDFS.subClassOf, cls)
            if sub != cls
        }

        return FoundTargets(
            declared_target_nodes=declared_target_nodes,
            referenced_shape_targets=referenced_shape_targets,
            class_targets=class_targets,
        )

