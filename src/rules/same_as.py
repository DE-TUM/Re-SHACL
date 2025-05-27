from rdflib import OWL, RDF

def resolve_same_as(graph, shapes):
    """
    Resolves owl:sameAs relationships by propagating all relevant triples.
    """
    target_nodes = set()

    for s in shapes:
        target_nodes.update(s.target_nodes())
        target_nodes.update(s.focus_nodes(graph))

    for node in list(target_nodes):
        _resolve_node_same_as(graph, node, target_nodes)


def _resolve_node_same_as(graph, node, target_nodes):
    if (node, OWL.sameAs, node) not in graph:
        graph.add((node, OWL.sameAs, node))  # Reflexivity

    for subject in graph.subjects(OWL.sameAs, node):  # Enforce symmetry
        if subject != node:
            graph.add((node, OWL.sameAs, subject))
            target_nodes.add(subject)

    for equivalent in list(graph.objects(node, OWL.sameAs)):
        if equivalent != node:
            target_nodes.add(equivalent)
            for p, o in graph.predicate_objects(node):
                graph.add((equivalent, p, o))
            for s, p in graph.subject_predicates(node):
                graph.add((s, p, equivalent))