from rdflib import RDF
from rdflib.namespace import OWL, RDFS
from pyshacl.consts import RDFS_subClassOf


def _infer_type_and_track(
    g, node, cls, discovered_focus_nodes, same_nodes, target_classes, *,
    track_if_cls_in_targets=False
):
    """
    Adds inferred type(s) to the node and optionally tracks focus nodes.

    Parameters:
    - track_if_cls_in_targets: if True, only track if `cls ∈ target_classes`
    """
    types_to_add = {cls}
    types_to_add.update(g.objects(cls, OWL.equivalentClass))
    types_to_add.update(g.subjects(OWL.equivalentClass, cls))
    types_to_add.update(g.transitive_objects(cls, RDFS_subClassOf))

    for inferred_cls in types_to_add:
        g.add((node, RDF.type, inferred_cls))

    if (
        (not track_if_cls_in_targets) or
        (cls in target_classes)
    ) and node not in discovered_focus_nodes:
        discovered_focus_nodes.add(node)
        same_nodes[node] = set()


def _expand_property_type(
    g, prop, cls, discovered_focus_nodes, same_nodes, target_classes, *,
    on_subject: bool, track_if_cls_in_targets=False
):
    """
    Expands property-based typing using rdfs:range or rdfs:domain
    through equivalentProperty and subPropertyOf closure.
    """
    # Materialize owl:equivalentProperty as symmetric rdfs:subPropertyOf
    for ep in g.transitive_objects(prop, OWL.equivalentProperty):
        g.add((ep, RDFS.subPropertyOf, prop))
        g.add((prop, RDFS.subPropertyOf, ep))
        g.remove((prop, OWL.equivalentProperty, ep))

    for ep in g.transitive_subjects(OWL.equivalentProperty, prop):
        g.add((ep, RDFS.subPropertyOf, prop))
        g.add((prop, RDFS.subPropertyOf, ep))
        g.remove((ep, OWL.equivalentProperty, prop))

    all_props = set(g.transitive_subjects(RDFS.subPropertyOf, prop)).union(
        g.transitive_objects(prop, OWL.equivalentProperty),
        g.transitive_subjects(OWL.equivalentProperty, prop)
    )
    all_props.add(prop)

    for p in all_props:
        for s, o in g.subject_objects(p):
            node = s if on_subject else o
            _infer_type_and_track(
                g, node, cls,
                discovered_focus_nodes, same_nodes, target_classes,
                track_if_cls_in_targets=track_if_cls_in_targets
            )


def target_range(g, discovered_focus_nodes, same_nodes, target_classes):
    for cls in target_classes:
        for prop in g.subjects(RDFS.range, cls):
            _expand_property_type(
                g, prop, cls, discovered_focus_nodes, same_nodes, target_classes,
                on_subject=False
            )


def target_domain_range(g, discovered_focus_nodes, same_nodes, target_classes):
    changed = True
    while changed:
        changed = False
        initial_size = len(discovered_focus_nodes)
        for cls in target_classes:
            for prop in g.subjects(RDFS.range, cls):
                _expand_property_type(
                    g, prop, cls, discovered_focus_nodes, same_nodes, target_classes,
                    on_subject=False
                )
            for prop in g.subjects(RDFS.domain, cls):
                _expand_property_type(
                    g, prop, cls, discovered_focus_nodes, same_nodes, target_classes,
                    on_subject=True
                )
        changed = len(discovered_focus_nodes) > initial_size


def check_domain_range(g, p, discovered_focus_nodes, same_nodes, target_classes):
    for cls in g.objects(p, RDFS.domain):
        for s, _ in g.subject_objects(p):
            _infer_type_and_track(
                g, s, cls, discovered_focus_nodes, same_nodes, target_classes,
                track_if_cls_in_targets=True
            )
    for cls in g.objects(p, RDFS.range):
        for _, o in g.subject_objects(p):
            _infer_type_and_track(
                g, o, cls, discovered_focus_nodes, same_nodes, target_classes,
                track_if_cls_in_targets=True
            )
