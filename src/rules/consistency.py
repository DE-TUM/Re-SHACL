from rdflib import Graph
from rdflib.namespace import RDF, OWL
from ..errors import FusionRuntimeError


def check_disjoint_classes(g: Graph, cls):
    for dis in g.objects(cls, OWL.disjointWith):
        for x in g.subjects(RDF.type, cls):
            if (x, RDF.type, dis) in g:
                raise FusionRuntimeError(f"Disjoint classes {cls} and {dis} have common member {x}")

    for dis in g.subjects(OWL.disjointWith, cls):
        for x in g.subjects(RDF.type, dis):
            if (x, RDF.type, cls) in g:
                raise FusionRuntimeError(f"Disjoint classes {cls} and {dis} have common member {x}")


def check_complementary_classes(g: Graph, cls):
    for comp in g.objects(cls, OWL.complementOf):
        for x in g.subjects(RDF.type, cls):
            if (x, RDF.type, comp) in g:
                raise FusionRuntimeError(f"Complementary classes {cls} and {comp} both apply to {x}")

    for comp in g.subjects(OWL.complementOf, cls):
        for x in g.subjects(RDF.type, comp):
            if (x, RDF.type, cls) in g:
                raise FusionRuntimeError(f"Complementary classes {cls} and {comp} both apply to {x}")