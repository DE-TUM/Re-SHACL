# core/owl_semantics/property_axioms.py

from rdflib.namespace import OWL, RDF
from sorc.errors import FusionRuntimeError


def apply_symmetric_property(g, prop):
    """Implements OWL SymmetricProperty (prp-symp)"""
    if (prop, RDF.type, OWL.SymmetricProperty) in g:
        for s, o in g.subject_objects(prop):
            g.add((o, prop, s))


def apply_transitive_property(g, prop):
    """Implements OWL TransitiveProperty (prp-trp)"""
    if (prop, RDF.type, OWL.TransitiveProperty) in g:
        for s, o in g.subject_objects(prop):
            for o2 in g.transitive_objects(o, prop):
                g.add((s, prop, o2))


def apply_inverse_properties(g, prop):
    """Implements OWL inverseOf (prp-inv)"""
    for inv1 in g.subjects(OWL.inverseOf, prop):
        for x, y in g.subject_objects(inv1):
            g.add((y, prop, x))
        for x, y in g.subject_objects(prop):
            g.add((y, inv1, x))

    for inv2 in g.objects(prop, OWL.inverseOf):
        for x, y in g.subject_objects(inv2):
            g.add((y, prop, x))
        for x, y in g.subject_objects(prop):
            g.add((y, inv2, x))


def apply_functional_property(g, prop):
    """Implements OWL FunctionalProperty (prp-fp)"""
    if (prop, RDF.type, OWL.FunctionalProperty) in g:
        for s, o1 in g.subject_objects(prop):
            for o2 in g.objects(s, prop):
                if o1 != o2:
                    g.add((o1, OWL.sameAs, o2))


def apply_inverse_functional_property(g, prop):
    """Implements OWL InverseFunctionalProperty (prp-ifp)"""
    if (prop, RDF.type, OWL.InverseFunctionalProperty) in g:
        for s1, o in g.subject_objects(prop):
            for s2 in g.subjects(prop, o):
                if s1 != s2:
                    g.add((s1, OWL.sameAs, s2))
