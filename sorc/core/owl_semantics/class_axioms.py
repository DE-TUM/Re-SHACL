# core/owl_semantics/class_axioms.py

from rdflib.namespace import RDF, OWL
from sorc.errors import FusionRuntimeError


def check_disjoint_classes(g, class_list):
    """
    Implements OWL disjointWith (cax-dw) and complementOf (cls-com) validation.
    Raises errors if disjoint/complement constraints are violated.
    """
    for cls in class_list:
        # Check OWL:complementOf violations
        for complement in g.objects(cls, OWL.complementOf):
            for instance in g.subjects(RDF.type, cls):
                if (instance, RDF.type, complement) in g:
                    raise FusionRuntimeError(
                        f"Complement classes {cls} and {complement} have shared individual {instance}"
                    )
        for complement in g.subjects(OWL.complementOf, cls):
            for instance in g.subjects(RDF.type, complement):
                if (instance, RDF.type, cls) in g:
                    raise FusionRuntimeError(
                        f"Complement classes {complement} and {cls} have shared individual {instance}"
                    )

        # Check OWL:disjointWith violations
        for disjoint in g.objects(cls, OWL.disjointWith):
            for instance in g.subjects(RDF.type, cls):
                if (instance, RDF.type, disjoint) in g:
                    raise FusionRuntimeError(
                        f"Disjoint classes {cls} and {disjoint} have shared individual {instance}"
                    )
        for disjoint in g.subjects(OWL.disjointWith, cls):
            for instance in g.subjects(RDF.type, disjoint):
                if (instance, RDF.type, cls) in g:
                    raise FusionRuntimeError(
                        f"Disjoint classes {disjoint} and {cls} have shared individual {instance}"
                    )
