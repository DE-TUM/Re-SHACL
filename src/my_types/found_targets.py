# src/types/found_targets.py
from dataclasses import dataclass, field
from typing import Set
from rdflib.term import Node
from rdflib import RDFS
from pyshacl.pytypes import GraphLike
from src.utils.safe_transitive import safe_transitive_subjects


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

        class_targets = set()
        for cls in target_classes:
            # Use safe_transitive_subjects to avoid infinite loops with cycles
            all_subs = safe_transitive_subjects(data_graph, RDFS.subClassOf, cls)
            # Exclude the class itself
            all_subs.discard(cls)
            class_targets.update(all_subs)

        return FoundTargets(
            declared_target_nodes=declared_target_nodes,
            referenced_shape_targets=referenced_shape_targets,
            class_targets=class_targets,
        )

