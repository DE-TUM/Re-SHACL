from rdflib import RDF, RDFS
from rdflib.namespace import OWL

def apply_domain_range_rules(g, shapes):
    target_classes = set()
    target_nodes = set()

    for s in shapes:
        target_classes.update(s.target_classes())
        target_classes.update(s.implicit_class_targets())
        for p in s.path_predicates():
            _apply_domain_rule(g, p, target_classes, target_nodes)
            _apply_range_rule(g, p, target_classes, target_nodes)

def _apply_domain_rule(g, p, target_classes, target_nodes):
    for o in g.objects(p, RDFS.domain):
        for x, y in g.subject_objects(p):
            g.add((x, RDF.type, o))
            if o in target_classes and x not in target_nodes:
                target_nodes.add(x)

def _apply_range_rule(g, p, target_classes, target_nodes):
    for o in g.objects(p, RDFS.range):
        for x, y in g.subject_objects(p):
            g.add((y, RDF.type, o))
            if o in target_classes and y not in target_nodes:
                target_nodes.add(y)
