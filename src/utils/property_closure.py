# -----------------------------------------------------------
# property_closure.py   –  utility you can drop in any module
# -----------------------------------------------------------
from rdflib.namespace import RDFS
from rdflib import Graph

def build_superproperty_map(g: Graph):
    """
    Returns  { P : frozenset(all super-properties of P, incl. indirect) }.
    """
    direct = {}
    for sub, _, sup in g.triples((None, RDFS.subPropertyOf, None)):
        direct.setdefault(sub, set()).add(sup)

    supers = {p: set(s) for p, s in direct.items()}
    changed = True
    while changed:
        changed = False
        for p in list(supers):
            new = set()
            for s in supers[p]:
                new |= supers.get(s, set())
            if new - supers[p]:
                supers[p].update(new)
                changed = True
    return {p: frozenset(s) for p, s in supers.items()}


def propagate_subproperty_closure(g: Graph, super_map):
    """
    Materialises  (s P o) ⇒ (s Q o)  for every Q ∈ super_map[P].
    Runs in O(|G|·avg-super) which is linear in practice.
    """
    add = g.add
    for p in super_map:
        supers = super_map[p]
        if not supers:
            continue
        for s, o in g.subject_objects(p):
            for q in supers:
                add((s, q, o))
