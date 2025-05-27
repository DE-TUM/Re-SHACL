from rdflib import RDF, OWL, RDFS
from rdflib.namespace import RDFS



def apply_property_inference(g, shapes):
    properties = set()
    for shape in shapes:
        for prop_shape in shape.property_shapes():
            path = next(shape.sg.graph.objects(prop_shape, shape.sg.SH_path), None)
            if path is not None:
                properties.add(path)

    for prop in properties:
        _apply_subproperty_closure(g, prop)
        _apply_equivalent_property_expansion(g, prop)
        _apply_symmetric_property(g, prop)
        _apply_transitive_property(g, prop)
        _apply_inverse_property(g, prop)
        _apply_functional_property(g, prop)
        _apply_inverse_functional_property(g, prop)


def _apply_subproperty_closure(g, prop):
    for sub_p in g.subjects(RDFS.subPropertyOf, prop):
        for s, o in g.subject_objects(sub_p):
            g.add((s, prop, o))


def _apply_equivalent_property_expansion(g, prop):
    for eq in g.objects(prop, OWL.equivalentProperty):
        g.add((eq, RDFS.subPropertyOf, prop))
        g.add((prop, RDFS.subPropertyOf, eq))
    for eq in g.subjects(OWL.equivalentProperty, prop):
        g.add((eq, RDFS.subPropertyOf, prop))
        g.add((prop, RDFS.subPropertyOf, eq))


def _apply_symmetric_property(g, prop):
    if (prop, RDF.type, OWL.SymmetricProperty) in g:
        for x, y in g.subject_objects(prop):
            g.add((y, prop, x))


def _apply_transitive_property(g, prop):
    if (prop, RDF.type, OWL.TransitiveProperty) in g:
        for s, o in g.subject_objects(prop):
            for oo in g.transitive_objects(o, prop):
                g.add((s, prop, oo))


def _apply_inverse_property(g, prop):
    for inverse in g.objects(prop, OWL.inverseOf):
        for s, o in g.subject_objects(prop):
            g.add((o, inverse, s))
        for s, o in g.subject_objects(inverse):
            g.add((o, prop, s))
    for inverse in g.subjects(OWL.inverseOf, prop):
        for s, o in g.subject_objects(prop):
            g.add((o, inverse, s))
        for s, o in g.subject_objects(inverse):
            g.add((o, prop, s))


def _apply_functional_property(g, prop):
    if (prop, RDF.type, OWL.FunctionalProperty) in g:
        for s in g.subjects(None, prop):
            values = list(g.objects(s, prop))
            for i in range(len(values)):
                for j in range(i + 1, len(values)):
                    g.add((values[i], OWL.sameAs, values[j]))


def _apply_inverse_functional_property(g, prop):
    if (prop, RDF.type, OWL.InverseFunctionalProperty) in g:
        for o in g.objects(None, prop):
            subjects = list(g.subjects(prop, o))
            for i in range(len(subjects)):
                for j in range(i + 1, len(subjects)):
                    g.add((subjects[i], OWL.sameAs, subjects[j]))
