"""Safe transitive closure utilities that handle cycles."""
from typing import Set, Iterable
from rdflib.term import Node
from pyshacl.pytypes import GraphLike


def safe_transitive_subjects(graph: GraphLike, predicate: Node, start: Node) -> Set[Node]:
    """
    Get all subjects transitively related to start via predicate.
    Handles cycles by tracking visited nodes.
    
    For example, if we have: A predicate B, B predicate C
    Then safe_transitive_subjects(graph, predicate, C) returns {A, B, C}
    """
    visited = set()
    to_visit = {start}
    
    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)
        
        # Get all subjects where (subject, predicate, current)
        for subject in graph.subjects(predicate, current):
            if subject not in visited:
                to_visit.add(subject)
    
    return visited


def safe_transitive_objects(graph: GraphLike, start: Node, predicate: Node) -> Set[Node]:
    """
    Get all objects transitively related to start via predicate.
    Handles cycles by tracking visited nodes.
    
    For example, if we have: A predicate B, B predicate C
    Then safe_transitive_objects(graph, predicate, A) returns {A, B, C}
    """
    visited = set()
    to_visit = {start}
    
    while to_visit:
        current = to_visit.pop()
        if current in visited:
            continue
        visited.add(current)
        
        # Get all objects where (current, predicate, object)
        for obj in graph.objects(current, predicate):
            if obj not in visited:
                to_visit.add(obj)
    
    return visited
