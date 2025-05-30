# core/owl_semantics/individual_axioms.py

from rdflib.namespace import OWL
from src.errors import FusionRuntimeError


def check_same_as_conflict(g, s, o):
    """
    Ensures OWL:sameAs and OWL:differentFrom are not used on the same individuals.
    Raises FusionRuntimeError if conflict is found.
    """
    if (s, OWL.differentFrom, o) in g or (o, OWL.differentFrom, s) in g:
        raise FusionRuntimeError(
            f"Invalid use: 'sameAs' and 'differentFrom' used on the same individuals: ({s}, {o})"
        )


def check_irreflexive_property(g, p):
    """
    Enforces OWL IrreflexiveProperty (prp-irp).
    Raises FusionRuntimeError if (x, p, x) exists.
    """
    from rdflib.namespace import RDF

    if (p, RDF.type, OWL.IrreflexiveProperty) in g:
        for x, y in g.subject_objects(p):
            if x == y:
                raise FusionRuntimeError(
                    f"Irreflexive property {p} used reflexively on node {x}"
                )
