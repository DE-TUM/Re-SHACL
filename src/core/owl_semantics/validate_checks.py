# core/owl_semantics/validate_checks.py

from rdflib.namespace import RDF, OWL
from src.errors import FusionRuntimeError


def check_asymmetric_property(g):
    """
    Enforces OWL AsymmetricProperty (prp-asyp).
    Raises FusionRuntimeError if (x, p, y) and (y, p, x) both exist.
    """
    for p in g.subjects(RDF.type, OWL.AsymmetricProperty):
        for x, y in g.subject_objects(p):
            if (y, p, x) in g:
                raise FusionRuntimeError(
                    f"Violation: AsymmetricProperty {p} used symmetrically on ({x}, {y}) and ({y}, {x})"
                )


def check_irreflexive_property(g):
    """
    Enforces OWL IrreflexiveProperty (prp-irp).
    Raises FusionRuntimeError if (x, p, x) exists.
    """
    for p in g.subjects(RDF.type, OWL.IrreflexiveProperty):
        for x, y in g.subject_objects(p):
            if x == y:
                raise FusionRuntimeError(
                    f"Violation: IrreflexiveProperty {p} used reflexively on ({x}, {y})"
                )


def check_sameas_differentfrom_conflict(g):
    """
    Ensures OWL:sameAs and OWL:differentFrom are not used on the same individuals.
    """
    for s, o in g.subject_objects(OWL.sameAs):
        if (s, OWL.differentFrom, o) in g or (o, OWL.differentFrom, s) in g:
            raise FusionRuntimeError(
                f"Conflict: sameAs and differentFrom used on same individuals: ({s}, {o})"
            )


def check_disjoint_classes(g, class_list):
    """
    Enforces OWL disjointWith constraints (cax-dw).
    """
    for cls in class_list:
        for disjoint in g.objects(cls, OWL.disjointWith):
            for x in g.subjects(RDF.type, cls):
                if (x, RDF.type, disjoint) in g:
                    raise FusionRuntimeError(
                        f"Disjoint class violation: {cls} and {disjoint} both assigned to {x}"
                    )
        for disjoint in g.subjects(OWL.disjointWith, cls):
            for x in g.subjects(RDF.type, disjoint):
                if (x, RDF.type, cls) in g:
                    raise FusionRuntimeError(
                        f"Disjoint class violation: {disjoint} and {cls} both assigned to {x}"
                    )


def check_complement_classes(g, class_list):
    """
    Enforces OWL complementOf constraints (cls-com).
    """
    for cls in class_list:
        for complement in g.objects(cls, OWL.complementOf):
            for x in g.subjects(RDF.type, cls):
                if (x, RDF.type, complement) in g:
                    raise FusionRuntimeError(
                        f"Complement violation: {cls} and {complement} both assigned to {x}"
                    )
        for complement in g.subjects(OWL.complementOf, cls):
            for x in g.subjects(RDF.type, complement):
                if (x, RDF.type, cls) in g:
                    raise FusionRuntimeError(
                        f"Complement violation: {complement} and {cls} both assigned to {x}"
                    )
