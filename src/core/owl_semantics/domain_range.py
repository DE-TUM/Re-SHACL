from rdflib import RDF
from rdflib.namespace import OWL, RDFS
from pyshacl.consts import RDFS_subClassOf


def _add_type_and_track(g, node, cls, target_nodes, same_nodes):
    """
    Adds type triple and expands through equivalentClass and subClassOf closure.
    """
    types_to_add = {cls}
    types_to_add.update(g.objects(cls, OWL.equivalentClass))
    types_to_add.update(g.subjects(OWL.equivalentClass, cls))
    types_to_add.update(g.transitive_objects(cls, RDFS_subClassOf))

    for inferred_cls in types_to_add:
        g.add((node, RDF.type, inferred_cls))

    if cls in target_nodes and node not in target_nodes:
        target_nodes.add(node)
        same_nodes[node] = set()


def _expand_property_type(g, prop, cls, target_nodes, same_nodes):
    """
    Expands property-based typing using rdfs:range or rdfs:domain
    through equivalentProperty and subPropertyOf closure.
    """
    # Materialize: owl:equivalentProperty(x, y) ⇒ rdfs:subPropertyOf(x, y)
    for ep in g.transitive_objects(prop, OWL.equivalentProperty):
        g.add((ep, RDFS.subPropertyOf, prop))
    for ep in g.transitive_subjects(OWL.equivalentProperty, prop):
        g.add((ep, RDFS.subPropertyOf, prop))

    all_props = set(g.transitive_subjects(RDFS.subPropertyOf, prop)).union(
        g.transitive_objects(prop, OWL.equivalentProperty),
        g.transitive_subjects(OWL.equivalentProperty, prop)
    )
    all_props.add(prop)

    for p in all_props:
        for s, o in g.subject_objects(p):
            _add_type_and_track(g, o, cls, target_nodes, same_nodes)
            _add_type_and_track(g, s, cls, target_nodes, same_nodes)


def target_range(g, target_nodes, same_nodes, target_classes):
    for cls in target_classes:
        for prop in g.subjects(RDFS.range, cls):
            _expand_property_type(g, prop, cls, target_nodes, same_nodes)


def target_domain_range(g, target_nodes, same_nodes, target_classes):
    """
    Applies both domain and range-based typing until closure is reached.
    """
    changed = True
    while changed:
        changed = False
        initial_size = len(target_nodes)
        for cls in target_classes:
            for prop in g.subjects(RDFS.range, cls):
                _expand_property_type(g, prop, cls, target_nodes, same_nodes)
            for prop in g.subjects(RDFS.domain, cls):
                _expand_property_type(g, prop, cls, target_nodes, same_nodes)
        changed = len(target_nodes) > initial_size


def check_domain_range(g, p, target_nodes, same_nodes, target_classes):
    for cls in g.objects(p, RDFS.domain):
        for s, _ in g.subject_objects(p):
            _add_type_and_track(g, s, cls, target_nodes, same_nodes)

    for cls in g.objects(p, RDFS.range):
        for _, o in g.subject_objects(p):
            _add_type_and_track(g, o, cls, target_nodes, same_nodes)

    return target_nodes
