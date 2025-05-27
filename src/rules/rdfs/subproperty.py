# fusion/rules/rdfs/subproperty.py

from rdflib import Graph, RDFS

def _apply_subproperty_closure(g: Graph):
    """
    Adds all inferred triples from rdfs:subPropertyOf relationships.
    For any triple (s, p1, o) and (p1, rdfs:subPropertyOf, p2), add (s, p2, o).
    """
    subproperty_map = {}

    # Build a map of all subPropertyOf relationships
    for sub, sup in g.subject_objects(RDFS.subPropertyOf):
        subproperty_map.setdefault(sub, set()).add(sup)

    # Compute transitive closure of subPropertyOf relationships
    changed = True
    while changed:
        changed = False
        for sub, sups in list(subproperty_map.items()):
            new_sups = set()
            for sup in sups:
                new_sups.update(subproperty_map.get(sup, set()))
            if not new_sups.issubset(sups):
                subproperty_map[sub].update(new_sups)
                changed = True

    # For each (s, p1, o), add (s, p2, o) for each p2 in closure of p1
    new_triples = set()
    for p1 in subproperty_map:
        for s, o in g.subject_objects(p1):
            for p2 in subproperty_map[p1]:
                new_triples.add((s, p2, o))

    for triple in new_triples:
        g.add(triple)
