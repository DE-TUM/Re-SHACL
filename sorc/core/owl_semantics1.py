
from ..errors import FusionRuntimeError

from rdflib.namespace import OWL, RDF, SH


SH_class = SH["class"]

from rdflib.namespace import Namespace
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
RDFS = Namespace(RDFS_PFX)
RDFS_subPropertyOf = RDFS.subPropertyOf


def check_symmetricProperty(g, p):  # RULE prp-symp
    if (p, RDF.type, OWL.SymmetricProperty) in g:
        for x, y in g.subject_objects(p):
            g.add((y, p, x))


def check_asymmetricProperty(g, p):  # prp-asyp
    if (p, RDF.type, OWL.AsymmetricProperty) in g:
        for x, y in g.subject_objects(p):
            if (y, p, x) in g:
                raise FusionRuntimeError(
                    "Erroneous usage of asymmetric property %s on %s and %s"
                    % (p, x, y)
                )


def check_transitiveProperty(g, p):
    if (p, RDF.type, OWL.TransitiveProperty) in g:
        for s, o in g.subject_objects(p):
            trans = g.transitive_objects(o, p)
            for oo in trans:
                g.add((s, p, oo))


def check_propertyDisjointWith(g, focus_property):  # prp-pdw
    for p in g.objects(focus_property, OWL.propertyDisjointWith):
        for x, y in g.subject_objects(focus_property):
            if (x, p, y) in g:
                raise FusionRuntimeError(
                    "Erroneous usage of disjoint properties %s and %s on %s and %s"
                    % (focus_property, p, x, y)
                )

    for p in g.subjects(OWL.propertyDisjointWith, focus_property):
        for x, y in g.subject_objects(p):
            if (x, focus_property, y) in g:
                raise FusionRuntimeError(
                    "Erroneous usage of disjoint properties %s and %s on %s and %s"
                    % (p, focus_property, x, y)
                )


def check_inverseOf(g, focus_property):
    for p1 in g.subjects(OWL.inverseOf, focus_property):
        for x, y in g.subject_objects(p1):
            g.add((y, focus_property, x))
        for xx, yy in g.subject_objects(focus_property):
            g.add((yy, p1, xx))
    for p2 in g.objects(focus_property, OWL.inverseOf):
        for x, y in g.subject_objects(p2):
            g.add((y, focus_property, x))
        for xx, yy in g.subject_objects(focus_property):
            g.add((yy, p2, xx))


def check_com_dw(g, class_list):
    for target_class in class_list:
        # RULE cls-com
        for c2 in g.objects(target_class, OWL.complementOf):
            for x in g.subjects(RDF.type, target_class):
                if (x, RDF.type, c2) in g:
                    raise FusionRuntimeError(
                        "Violation of complementarity for classes %s and %s on element %s (or an identical individual with it)"
                        % (target_class, c2, x)
                    )

        for c1 in g.subjects(OWL.complementOf, target_class):
            for x in g.subjects(RDF.type, c1):
                if (x, RDF.type, target_class) in g:
                    raise FusionRuntimeError(
                        "Violation of complementarity for classes %s and %s on element %s (or an identical individual with it)"
                        % (c1, target_class, x)
                    )

        # RULE cax-dw
        for c2 in g.objects(target_class, OWL.disjointWith):
            for x in g.subjects(RDF.type, target_class):
                if (x, RDF.type, c2) in g:
                    raise FusionRuntimeError(
                        "Disjoint classes %s and %s have a common individual %s (or an identical individual with it)"
                        % (target_class, c2, x)
                    )

        for c1 in g.subjects(OWL.disjointWith, target_class):
            for x in g.subjects(RDF.type, c1):
                if (x, RDF.type, target_class) in g:
                    raise FusionRuntimeError(
                        "Disjoint classes %s and %s have a common individual %s (or an identical individual with it)"
                        % (c1, target_class, x)
                    )


def check_eq_diff_erro(g, s, o):
    if (s, OWL.differentFrom, o) in g or (
            o,
            OWL.differentFrom,
            s,
    ) in g:
        raise FusionRuntimeError(
            "'sameAs' and 'differentFrom' cannot be used on the same subject-object pair: (%s, %s)"
            % (s, o)
        )


def check_irreflexiveProperty(g, p):  # RULE prp-irp
    if (p, RDF.type, OWL.IrreflexiveProperty) in g:
        for x, y in g.subject_objects(p):
            if x == y:
                raise FusionRuntimeError(
                    "Irreflexive property used on %s with %s" % (x, p)
                )


def check_FunctionalProperty(g, focus_property):
    # prp-fp
    if (focus_property, RDF.type, OWL.FunctionalProperty) in g:
        for x, y1 in g.subject_objects(focus_property):
            for y2 in g.objects(x, focus_property):
                if y1 != y2:
                    # if y1 in found_node_targets or y2 in found_node_targets
                    g.add((y1, OWL.sameAs, y2))


def check_InverseFunctionalProperty(g, focus_property):
    # prp-ifp
    if (focus_property, RDF.type, OWL.InverseFunctionalProperty) in g:
        for x1, y in g.subject_objects(focus_property):
            for x2 in g.subjects(focus_property, y):
                if x1 != x2:
                    # if x1 in found_node_targets or x2 in found_node_targets
                    g.add((x1, OWL.sameAs, x2))