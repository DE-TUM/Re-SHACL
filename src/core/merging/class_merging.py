from rdflib.namespace import RDF, OWL, RDFS

from src.utils.merge_helpers import sameClasses_merged


def merge_target_classes(g, found_node_targets, same_nodes, target_classes):
    eq_target_classes = set()
    eq_target_nodes = set()

    for cls in target_classes:
        while not sameClasses_merged(g, cls):
            eq_classes = find_equivalent_classes(g, cls)

            for eq_cls in eq_classes:
                eq_target_classes.add(eq_cls)

                for subj in g.subjects(RDF.type, eq_cls):
                    eq_target_nodes.add(subj)
                    g.add((subj, RDF.type, cls))

                for subj in g.subjects(RDF.type, cls):
                    g.add((subj, RDF.type, eq_cls))

                remove_equivalence_and_add_subclass_links(g, cls, eq_cls)

    for new_node in eq_target_nodes:
        if new_node not in found_node_targets:
            same_nodes[new_node] = set()

    found_node_targets.update(eq_target_nodes)
    target_classes.update(eq_target_classes)


def find_equivalent_classes(g, cls):
    eqs = set()
    for eq in g.subjects(OWL.equivalentClass, cls):
        eqs.add(eq)
    for eq in g.objects(cls, OWL.equivalentClass):
        eqs.add(eq)
    for eq in g.subjects(OWL.sameAs, cls):
        eqs.add(eq)
    for eq in g.objects(cls, OWL.sameAs):
        eqs.add(eq)
    return eqs


def remove_equivalence_and_add_subclass_links(g, a, b):
    g.remove((a, OWL.equivalentClass, b))
    g.remove((b, OWL.equivalentClass, a))
    g.remove((a, OWL.sameAs, b))
    g.remove((b, OWL.sameAs, a))
    g.add((a, RDFS.subClassOf, b))
    g.add((b, RDFS.subClassOf, a))
