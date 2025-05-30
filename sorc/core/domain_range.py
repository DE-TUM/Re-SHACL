from rdflib import RDF
from rdflib.namespace import OWL, RDFS
from pyshacl.consts import RDFS_subClassOf

def _add_type_and_track(g, node, cls, target_nodes, same_nodes):
    g.add((node, RDF.type, cls))
    if cls in target_nodes and node not in target_nodes:
        target_nodes.add(node)
        same_nodes[node] = set()


def _expand_property_type(g, prop, cls, target_nodes, same_nodes):
    # Get all equivalent and subproperties
    all_props = set(g.transitive_subjects(RDFS_subClassOf, prop)).union(
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
    for cls in target_classes:
        for prop in g.subjects(RDFS.range, cls):
            _expand_property_type(g, prop, cls, target_nodes, same_nodes)
        for prop in g.subjects(RDFS.domain, cls):
            _expand_property_type(g, prop, cls, target_nodes, same_nodes)


def check_domain_range(g, p, target_nodes, same_nodes, target_classes):
    for cls in g.objects(p, RDFS.domain):
        for s, _ in g.subject_objects(p):
            _add_type_and_track(g, s, cls, target_nodes, same_nodes)

    for cls in g.objects(p, RDFS.range):
        for _, o in g.subject_objects(p):
            _add_type_and_track(g, o, cls, target_nodes, same_nodes)

    return target_nodes
