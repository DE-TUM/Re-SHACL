from rdflib import Graph
from rdflib.namespace import RDF, OWL
from ..errors import FusionRuntimeError


def check_transitive_property(g: Graph, p):
    if (p, RDF.type, OWL.TransitiveProperty) in g:
        for s, o in g.subject_objects(p):
            for oo in g.transitive_objects(o, p):
                g.add((s, p, oo))


def check_symmetric_property(g: Graph, p):
    if (p, RDF.type, OWL.SymmetricProperty) in g:
        for x, y in g.subject_objects(p):
            g.add((y, p, x))


def check_asymmetric_property(g: Graph, p):
    if (p, RDF.type, OWL.AsymmetricProperty) in g:
        for x, y in g.subject_objects(p):
            if (y, p, x) in g:
                raise FusionRuntimeError(f"Asymmetric property {p} used incorrectly on {x} and {y}")


def check_irreflexive_property(g: Graph, p):
    if (p, RDF.type, OWL.IrreflexiveProperty) in g:
        for x, y in g.subject_objects(p):
            if x == y:
                raise FusionRuntimeError(f"Irreflexive property {p} used on reflexive pair {x}")


def check_functional_property(g: Graph, p):
    if (p, RDF.type, OWL.FunctionalProperty) in g:
        for x, y1 in g.subject_objects(p):
            for y2 in g.objects(x, p):
                if y1 != y2:
                    g.add((y1, OWL.sameAs, y2))


def check_inverse_functional_property(g: Graph, p):
    if (p, RDF.type, OWL.InverseFunctionalProperty) in g:
        for x1, y in g.subject_objects(p):
            for x2 in g.subjects(p, y):
                if x1 != x2:
                    g.add((x1, OWL.sameAs, x2))
