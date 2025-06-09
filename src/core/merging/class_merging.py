# ------------------------------------------------------------
# class_merging.py   –   new merge_target_classes (cycle-free)
# ------------------------------------------------------------

from rdflib.namespace import RDF, RDFS, OWL


def merge_target_classes(g, discovered_focus_nodes, same_nodes, target_classes):
    super_map = _build_superclass_map(g)
    newly_found_nodes = set()
    newly_found_classes = set()
    seen_classes = set()

    for cls in list(target_classes):
        if cls in seen_classes:
            continue

        eq_classes = _expand_equivalent_classes(g, cls) | {cls}
        seen_classes.update(eq_classes)

        if len(eq_classes) <= 1:
            continue

        rep = _pick_representative(eq_classes)
        delta_pairs = _sync_instance_types(g, rep, eq_classes, newly_found_nodes)
        _add_symmetric_subclass_edges(g, rep, eq_classes)
        _remove_equivalence_links(g, eq_classes)
        _propagate_types_incremental(g, delta_pairs, super_map)

        newly_found_classes.update(eq_classes)

    _update_tracking_structures(newly_found_nodes, newly_found_classes,
                                same_nodes, discovered_focus_nodes, target_classes)


# =========================== helpers =============================
def _expand_equivalent_classes(g, cls):
    todo, seen = {cls}, set()
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        todo.update(g.subjects(OWL.equivalentClass, c))
        todo.update(g.objects(c, OWL.equivalentClass))
        todo.update(g.subjects(OWL.sameAs, c))
        todo.update(g.objects(c, OWL.sameAs))
    seen.discard(cls)
    return seen


def _pick_representative(eq_classes):
    return min(eq_classes)


def _sync_instance_types(g, rep, eq_classes, newly_found_nodes):
    delta_pairs = []
    for eq_cls in eq_classes:
        for inst in g.subjects(RDF.type, eq_cls):
            g.add((inst, RDF.type, rep))
            newly_found_nodes.add(inst)
            delta_pairs.append((inst, rep))
        for inst in g.subjects(RDF.type, rep):
            g.add((inst, RDF.type, eq_cls))
            delta_pairs.append((inst, eq_cls))
    return delta_pairs


def _add_symmetric_subclass_edges(g, rep, eq_classes):
    for eq_cls in eq_classes:
        if eq_cls != rep:
            g.add((rep, RDFS.subClassOf, eq_cls))
            g.add((eq_cls, RDFS.subClassOf, rep))


def _remove_equivalence_links(g, eq_classes):
    for a in eq_classes:
        for b in eq_classes:
            g.remove((a, OWL.equivalentClass, b))
            g.remove((b, OWL.equivalentClass, a))
            g.remove((a, OWL.sameAs, b))
            g.remove((b, OWL.sameAs, a))


def _update_tracking_structures(new_nodes, new_classes, same_nodes, focus_nodes, target_classes):
    for inst in new_nodes:
        same_nodes.setdefault(inst, set())
    focus_nodes.update(new_nodes)
    target_classes.update(new_classes)


def _build_superclass_map(g):
    direct = {}
    for sub, _, sup in g.triples((None, RDFS.subClassOf, None)):
        direct.setdefault(sub, set()).add(sup)
    supers = {c: set(p) for c, p in direct.items()}
    changed = True
    while changed:
        changed = False
        for c in list(supers):
            inherited = set()
            for p in supers[c]:
                inherited |= supers.get(p, set())
            if inherited - supers[c]:
                supers[c].update(inherited)
                changed = True
    return {c: frozenset(p) for c, p in supers.items()}


def _propagate_types_incremental(g, delta_pairs, super_map):
    for inst, cls in delta_pairs:
        for sup in super_map.get(cls, ()):
            g.add((inst, RDF.type, sup))
# -----------------------------------------------------------------
