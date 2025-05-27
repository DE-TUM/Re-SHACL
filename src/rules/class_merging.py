from rdflib import RDF, OWL, RDFS


def merge_equivalent_classes(g, shapes):
    target_classes = set()
    for shape in shapes:
        target_classes.update(shape.target_classes())
        target_classes.update(shape.implicit_class_targets())

    visited = set()

    for c in list(target_classes):
        if c in visited:
            continue

        equivalents = set()
        equivalents.update(g.objects(c, OWL.equivalentClass))
        equivalents.update(g.subjects(OWL.equivalentClass, c))
        equivalents.update(g.objects(c, OWL.sameAs))
        equivalents.update(g.subjects(OWL.sameAs, c))

        for eq_class in equivalents:
            if eq_class == c:
                continue
            visited.add(eq_class)
            for s in g.subjects(RDF.type, eq_class):
                g.add((s, RDF.type, c))
            for s in g.subjects(RDF.type, c):
                g.add((s, RDF.type, eq_class))
            g.add((c, RDFS.subClassOf, eq_class))
            g.add((eq_class, RDFS.subClassOf, c))
            # Optional: remove owl:sameAs or owl:equivalentClass triples
            # g.remove((c, OWL.equivalentClass, eq_class))
            # g.remove((eq_class, OWL.equivalentClass, c))

        visited.add(c)