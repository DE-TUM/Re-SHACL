from rdflib.namespace import OWL, RDFS
from pyshacl.consts import SH_path
from src.utils.merge_helpers import all_subProperties_merged, all_property_merged
from src.core.owl_semantics.domain_range import check_domain_range
from src.core.owl_semantics import (
    apply_symmetric_property,
    apply_transitive_property,
    apply_inverse_properties,
    apply_functional_property,
    apply_inverse_functional_property
)


def merge_same_property(g, properties, focus_nodes, same_nodes, class_targets, shapes, property_shape_nodes, shacl_graph):
    properties_set = set(properties)  # Used to conditionally rewrite shapes
    for focus_property in properties:
        merge_subproperties(g, focus_property)
        merge_equivalent_properties(g, focus_property, properties_set, shapes, property_shape_nodes, shacl_graph)
        apply_property_semantics(g, focus_property, focus_nodes, same_nodes, class_targets)


def merge_subproperties(g, focus_property):
    while not all_subProperties_merged(g, focus_property):
        for sub_p in g.subjects(RDFS.subPropertyOf, focus_property):
            if (focus_property, RDFS.subPropertyOf, sub_p) in g:
                g.add((focus_property, OWL.sameAs, sub_p))
            else:
                for p3 in g.subjects(RDFS.subPropertyOf, sub_p):
                    if focus_property != p3:
                        g.add((p3, RDFS.subPropertyOf, focus_property))

                for c in g.objects(focus_property, RDFS.domain):
                    g.add((sub_p, RDFS.domain, c))
                for c in g.objects(focus_property, RDFS.range):
                    g.add((sub_p, RDFS.range, c))
                for s, o in g.subject_objects(sub_p):
                    g.add((s, focus_property, o))

            g.remove((sub_p, RDFS.subPropertyOf, focus_property))


def merge_equivalent_properties(g, focus_property, properties_set, shapes, property_shape_nodes, shacl_graph):
    while not all_property_merged(g, focus_property):
        _replace_equivalent_predicates(g, focus_property, OWL.equivalentProperty)
        _replace_equivalent_predicates(g, focus_property, OWL.sameAs)

        for same_p in g.objects(focus_property, OWL.sameAs):
            if same_p == focus_property:
                g.remove((same_p, OWL.sameAs, same_p))
                continue

            for pred, obj in g.predicate_objects(same_p):
                g.remove((same_p, pred, obj))
                g.add((focus_property, pred, obj))

            for subj, pred in g.subject_predicates(same_p):
                g.remove((subj, pred, same_p))
                g.add((subj, pred, focus_property))

            for subj, obj in g.subject_objects(same_p):
                g.remove((subj, same_p, obj))
                g.add((subj, focus_property, obj))

            if same_p in properties_set:
                rewrite_property_in_shapes(same_p, focus_property, shapes, property_shape_nodes, shacl_graph)

            g.remove((focus_property, OWL.sameAs, same_p))


def _replace_equivalent_predicates(g, focus_property, predicate):
    for p in g.subjects(predicate, focus_property):
        if p != focus_property:
            g.remove((p, predicate, focus_property))
            g.add((focus_property, OWL.sameAs, p))
    for p in g.objects(focus_property, predicate):
        if p != focus_property:
            g.remove((focus_property, predicate, p))
            g.add((focus_property, OWL.sameAs, p))

    # Clean reflexive sameAs if present
    g.remove((focus_property, OWL.sameAs, focus_property))


def rewrite_property_in_shapes(old_prop, new_prop, shapes, property_shape_nodes, shacl_graph):
    if old_prop == new_prop:
        return
    for blank_node in property_shape_nodes:
        if old_prop in shacl_graph.objects(blank_node, SH_path):
            shacl_graph.remove((blank_node, SH_path, old_prop))
            shacl_graph.add((blank_node, SH_path, new_prop))


def apply_property_semantics(g, prop, focus_nodes, same_nodes, class_targets):
    apply_symmetric_property(g, prop)
    apply_transitive_property(g, prop)
    apply_inverse_properties(g, prop)
    check_domain_range(g, prop, focus_nodes, same_nodes, class_targets)
    apply_functional_property(g, prop)
    apply_inverse_functional_property(g, prop)
