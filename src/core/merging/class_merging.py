# ------------------------------------------------------------
# class_merging.py   –   new merge_target_classes (cycle-free)
# ------------------------------------------------------------
from rdflib.namespace import RDF, RDFS, OWL

def merge_target_classes(g,
                         found_node_targets,
                         same_nodes,
                         target_classes):
    """
    One-pass, cycle-free equivalent-class merge.

    • Computes the full equivalence closure of every class that is already in
      `target_classes`.
    • Removes all owl:equivalentClass / owl:sameAs triples inside the component.
    • Inserts *symmetric* rdfs:subClassOf links (A ⊑ B and B ⊑ A) once –
      that is enough for downstream reasoning, and it satisfies
      `sameClasses_merged` without needing a loop.
    • Propagates rdf:type up the class hierarchy incrementally.
    """

    super_map           = _build_superclass_map(g)   # { C : frozenset(supers) }
    newly_found_nodes   = set()                      # will become focus nodes
    newly_found_classes = set()                      # added to target_classes

    # Work on a snapshot to avoid “set modified during iteration”
    for cls in list(target_classes):

        # --- gather *all* classes equivalent to `cls` ---------------------
        eq_classes = _expand_equivalent_classes(g, cls)
        if not eq_classes:
            continue                    # nothing to merge for this component

        # -----------------------------------------------------------------
        # 1) Copy explicit rdf:type between every pair (inst, eq_cls / cls)
        # -----------------------------------------------------------------
        delta_pairs = []                # (instance, direct_class) just added
        for eq_cls in eq_classes:
            newly_found_classes.add(eq_cls)

            # inst : eq_cls  ⇒  inst : cls
            for inst in g.subjects(RDF.type, eq_cls):
                delta_pairs.append((inst, cls))
                newly_found_nodes.add(inst)
                g.add((inst, RDF.type, cls))

            # inst : cls  ⇒  inst : eq_cls
            for inst in g.subjects(RDF.type, cls):
                delta_pairs.append((inst, eq_cls))
                g.add((inst, RDF.type, eq_cls))

            # -------------------------------------------------------------
            # 2) Eliminate *all* equivalence links between cls & eq_cls
            # -------------------------------------------------------------
            _remove_equiv(g, cls, eq_cls)

            # -------------------------------------------------------------
            # 3) Record *symmetric* subClassOf edges (DAG remains acyclic)
            # -------------------------------------------------------------
            g.add((cls,    RDFS.subClassOf, eq_cls))
            g.add((eq_cls, RDFS.subClassOf, cls))

        # -----------------------------------------------------------------
        # 4) Propagate the fresh (inst, direct_class) pairs up the DAG
        # -----------------------------------------------------------------
        _propagate_types_incremental(g, delta_pairs, super_map)

    # ---------------------------------------------------------------------
    # 5) Update global “targets” tracking structures
    # ---------------------------------------------------------------------
    for inst in newly_found_nodes:
        if inst not in found_node_targets:
            same_nodes[inst] = set()
    found_node_targets.update(newly_found_nodes)
    target_classes.update(newly_found_classes)


# -----------------------------------------------------------------


# =========================== helpers =============================

def _expand_equivalent_classes(g, cls):
    todo, seen = {cls}, set()
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)

        nbrs = set(g.subjects(OWL.equivalentClass, c))
        nbrs |= set(g.objects(c, OWL.equivalentClass))
        nbrs |= set(g.subjects(OWL.sameAs,         c))
        nbrs |= set(g.objects(c, OWL.sameAs))
        todo |= nbrs
    seen.discard(cls)
    return seen


def _remove_equiv(g, a, b):
    g.remove((a, OWL.equivalentClass, b))
    g.remove((b, OWL.equivalentClass, a))
    g.remove((a, OWL.sameAs,          b))
    g.remove((b, OWL.sameAs,          a))


# ----------  incremental superclass propagation ------------------

def _build_superclass_map(g):
    """
    Returns { C : frozenset(all super-classes of C, incl. indirect) }.
    Runs one BFS over the subclass DAG – negligible versus data size.
    """
    direct = {}
    for sub, _, sup in g.triples((None, RDFS.subClassOf, None)):
        direct.setdefault(sub, set()).add(sup)

    # simple fixed-point computation
    supers = {c: set(p) for c, p in direct.items()}
    changed = True
    while changed:
        changed = False
        for c in list(supers):
            new = set()
            for p in supers[c]:
                new |= supers.get(p, set())
            if new - supers[c]:
                supers[c].update(new)
                changed = True
    # freeze the sets to avoid accidental mutation later
    return {c: frozenset(p) for c, p in supers.items()}


def _propagate_types_incremental(g, delta_pairs, super_map):
    """
    `delta_pairs` : iterable of (instance, class) triples *just* inserted.
    Adds rdf:type for every (instance, super) where `super` is in the map.
    """
    add = g.add
    for inst, cls in delta_pairs:
        for sup in super_map.get(cls, ()):
            add((inst, RDF.type, sup))
# -----------------------------------------------------------------
