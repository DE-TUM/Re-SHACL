from rdflib.namespace import SH
from ..rules.owl_rules import (
    check_inverse_functional_property,
    check_functional_property,
    check_transitive_property,
    check_symmetric_property,
    check_inverse_of,
    check_domain_range,
)
from ..rules.consistency import all_focus_merged, all_property_merged, all_sub_properties_merged, same_classes_merged
from rdflib import OWL, RDF, RDFS


def target_domain_range(g, target_nodes, same_nodes, target_classes):
    for c in target_classes:
        for pp in g.subjects(RDFS.range, c):
            for ss, oo in g.subject_objects(pp):
                g.add((oo, RDF.type, c))
                if oo not in target_nodes:
                    target_nodes.add(oo)
                    same_nodes[oo] = set()

        for p in g.subjects(RDFS.domain, c):
            for s, o in g.subject_objects(p):
                g.add((s, RDF.type, c))
                if s not in target_nodes:
                    target_nodes.add(s)
                    same_nodes[s] = set()


def target_range(g, target_nodes, same_nodes, target_classes):
    for c in target_classes:
        for p in g.subjects(RDFS.range, c):
            for s, o in g.subject_objects(p):
                g.add((o, RDF.type, c))
                if o not in target_nodes:
                    target_nodes.add(o)
                    same_nodes[o] = set()


def merge_target_classes(g, found_node_targets, same_nodes, target_classes):
    eq_classes = set()
    eq_targets = set()
    for c in list(target_classes):
        while not same_classes_merged(g, c):
            for c2 in g.subjects(OWL.equivalentClass, c):
                eq_classes.add(c2)
                for x in g.subjects(RDF.type, c2):
                    eq_targets.add(x)
                    g.add((x, RDF.type, c))
                g.remove((c2, OWL.equivalentClass, c))
                g.add((c2, RDFS.subClassOf, c))
                g.add((c, RDFS.subClassOf, c2))

            for c2 in g.objects(c, OWL.equivalentClass):
                eq_classes.add(c2)
                for x in g.subjects(RDF.type, c2):
                    eq_targets.add(x)
                    g.add((x, RDF.type, c))
                g.remove((c, OWL.equivalentClass, c2))
                g.add((c2, RDFS.subClassOf, c))
                g.add((c, RDFS.subClassOf, c2))

    for x in eq_targets:
        if x not in found_node_targets:
            same_nodes[x] = set()
    found_node_targets.update(eq_targets)
    target_classes.update(eq_classes)


def merge_same_property(g, properties, found_node_targets, same_nodes, target_classes, shapes, target_property, shacl_graph):
    for p in list(properties):
        while not all_sub_properties_merged(g, p):
            for sub in g.subjects(RDFS.subPropertyOf, p):
                if (p, RDFS.subPropertyOf, sub) in g:
                    g.add((p, OWL.sameAs, sub))
                else:
                    for x, y in g.subject_objects(sub):
                        g.add((x, p, y))
                g.remove((sub, RDFS.subPropertyOf, p))

        while not all_property_merged(g, p):
            for same in g.subjects(OWL.sameAs, p):
                if same != p:
                    for x, y in g.subject_objects(same):
                        g.add((x, p, y))
                    g.remove((same, OWL.sameAs, p))
                    g.add((p, OWL.sameAs, same))

            for same in g.objects(p, OWL.sameAs):
                if same != p:
                    for x, y in g.subject_objects(same):
                        g.add((x, p, y))
                    g.remove((p, OWL.sameAs, same))

            check_symmetric_property(g, p)
            check_transitive_property(g, p)
            check_inverse_of(g, p)
            check_domain_range(g, p, found_node_targets, same_nodes, target_classes)
            check_functional_property(g, p)
            check_inverse_functional_property(g, p)


def merge_same_focus(g, same_nodes, focus, target_nodes, shapes, shape_g):
    for s in g.subjects(OWL.sameAs, focus):
        if s != focus:
            g.remove((s, OWL.sameAs, focus))
            g.add((focus, OWL.sameAs, s))

    for o in list(g.objects(focus, OWL.sameAs)):
        if o != focus:
            same_nodes[focus].add(o)
            if o in same_nodes:
                same_nodes[focus].update(same_nodes[o])
                del same_nodes[o]
            for p, y in g.predicate_objects(o):
                g.add((focus, p, y))
                g.remove((o, p, y))
            for x, p in g.subject_predicates(o):
                g.add((x, p, focus))
                g.remove((x, p, o))
            g.remove((focus, OWL.sameAs, o))
