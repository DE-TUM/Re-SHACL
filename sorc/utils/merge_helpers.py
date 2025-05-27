
from rdflib.namespace import OWL, RDF, RDFS, SH

SH_class = SH["class"]

from rdflib.namespace import Namespace
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
RDFS = Namespace(RDFS_PFX)
RDFS_subPropertyOf = RDFS.subPropertyOf




def all_samePath_merged(g, path_value):
    for p in path_value:
        m1 = [o for o in g.objects(p, OWL.sameAs)]
        m2 = [s for s in g.subjects(OWL.sameAs, p)]
        m3 = [oo for oo in g.objects(p, OWL.equivalentProperty)]
        m4 = [ss for ss in g.subjects(OWL.equivalentProperty, p)]
        m5 = [s for s in g.subjects(RDFS.subPropertyOf, p)]
        if len(m1) != 0 or len(m2) != 0 or len(m3) != 0 or len(m4) != 0 or len(m5) != 0:
            return False
    return True


def all_property_merged(g, property):
    m1 = [o for o in g.objects(property, OWL.sameAs)]
    if len(m1) != 0:
        return False
    m2 = [s for s in g.subjects(OWL.sameAs, property)]
    if len(m2) != 0:
        return False
    m3 = [oo for oo in g.objects(property, OWL.equivalentProperty)]
    if len(m3) != 0:
        return False
    m4 = [ss for ss in g.subjects(OWL.equivalentProperty, property)]
    if len(m4) != 0:
        return False
    return True


def all_focus_merged(g, focus, target_nodes):
    m1 = [o for o in g.objects(focus, OWL.sameAs)]  # focus node = o exists
    if len(m1) != 0:
        return False
    m2 = [s for s in g.subjects(OWL.sameAs, focus)]  # s = focus exists
    for e in m2:
        if e not in target_nodes:
            return False
    return True


def all_subProperties_merged(g, p):
    m1 = [s for s in g.subjects(RDFS.subPropertyOf, p)]
    if len(m1) != 0:
        return False
    return True


def all_targetClasses_merged(g, target_classes):
    for c in target_classes:
        m1 = [s for s in g.subjects(OWL.equivalentClass, c)]
        m2 = [s for s in g.objects(c, OWL.equivalentClass)]
        m3 = [s for s in g.subjects(OWL.sameAs, c)]
        m4 = [s for s in g.objects(c, OWL.sameAs)]
        if len(m1) != 0 or len(m2) != 0 or len(m3) != 0 or len(m4) != 0:
            return False
    return True


def sameClasses_merged(g, target_class):
    m1 = [s for s in g.subjects(OWL.equivalentClass, target_class)]
    m2 = [s for s in g.objects(target_class, OWL.equivalentClass)]
    m3 = [s for s in g.subjects(OWL.sameAs, target_class)]
    m4 = [s for s in g.objects(target_class, OWL.sameAs)]
    if len(m1) != 0 or len(m2) != 0 or len(m3) != 0 or len(m4) != 0:
        return False
    return True