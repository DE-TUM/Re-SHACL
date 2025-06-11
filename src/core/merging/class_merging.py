# class_merging_legacy_loop.py  –  original semantics + super-map
from rdflib.namespace import RDF, RDFS, OWL


def merge_target_classes(g,
                         discovered_focus_nodes: set,
                         same_nodes: dict,
                         target_classes: set) -> None:
    """
    Original edge-by-edge rewriting loop (sameClasses_merged logic) **plus**
    modern superclass-map propagation.
    """

    super_map          = _build_superclass_map(g)
    delta_nodes        = set()           # instances newly seen
    delta_classes      = set()           # classes touched

    for cls in (target_classes):
        while _has_equiv_links(g, cls):
            # ---- ∀ in-edges  x ≡ cls  ----------------------------------
            for x in (g.subjects(OWL.equivalentClass, cls)):
                _rewrite_edge(g, x, cls, delta_nodes, same_nodes)
                delta_classes.add(x)
            for x in (g.subjects(OWL.sameAs, cls)):
                _rewrite_edge(g, x, cls, delta_nodes, same_nodes)

            # ---- ∀ out-edges cls ≡ y  ----------------------------------
            for y in (g.objects(cls, OWL.equivalentClass)):
                _rewrite_edge(g, cls, y, delta_nodes, same_nodes)
                delta_classes.add(y)
            for y in (g.objects(cls, OWL.sameAs)):
                _rewrite_edge(g, cls, y, delta_nodes, same_nodes)

    # -------- propagate rdf:type up the DAG once for all new instances ---
    _propagate_types_incremental(g, delta_nodes, super_map)

    # -------- bookkeeping ----------------------------------------------
    for inst in delta_nodes:
        same_nodes.setdefault(inst, set())
    discovered_focus_nodes.update(delta_nodes)
    target_classes.update(delta_classes)


# ======================================================================
# helper-routines
# ======================================================================
def _has_equiv_links(g, cls) -> bool:
    return (
        any(g.subjects(OWL.equivalentClass, cls)) or
        any(g.objects(cls,  OWL.equivalentClass)) or
        any(g.subjects(OWL.sameAs,          cls)) or
        any(g.objects(cls,  OWL.sameAs))
    )


def _rewrite_edge(g, a, b, delta_nodes, same_nodes):
    """
    Implements *one* rewrite step:

      a  (owl:sameAs | owl:equivalentClass)  b
         ⇒
      a ⊑ b   &   b ⊑ a  +  rdf:type copies  +  remove equiv triple
    """
    # copy rdf:type both directions
    for inst in g.subjects(RDF.type, a):
        g.add((inst, RDF.type, b)); delta_nodes.add(inst)
    for inst in g.subjects(RDF.type, b):
        g.add((inst, RDF.type, a)); delta_nodes.add(inst)

    # drop equivalence triple (both directions for safety)
    g.remove((a, OWL.equivalentClass, b))
    g.remove((b, OWL.equivalentClass, a))
    g.remove((a, OWL.sameAs,          b))
    g.remove((b, OWL.sameAs,          a))

    # add symmetric rdfs:subClassOf
    g.add((a, RDFS.subClassOf, b))
    g.add((b, RDFS.subClassOf, a))

    # identity map
    same_nodes.setdefault(a, set()).add(b)


def _build_superclass_map(g):
    direct = {}
    for s, _, o in g.triples((None, RDFS.subClassOf, None)):
        direct.setdefault(s, set()).add(o)
    supers = {c: set(p) for c, p in direct.items()}
    changed = True
    while changed:
        changed = False
        for c in (supers):
            inherited = {p for p in supers[c] for p in supers.get(p, ())}
            if inherited - supers[c]:
                supers[c].update(inherited)
                changed = True
    return {c: frozenset(p) for c, p in supers.items()}


def _propagate_types_incremental(g, new_nodes, super_map):
    for inst in new_nodes:
        for cls in g.objects(inst, RDF.type):
            for sup in super_map.get(cls, ()):
                g.add((inst, RDF.type, sup))
