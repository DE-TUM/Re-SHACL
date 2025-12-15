from rdflib import RDF
from rdflib.namespace import OWL, RDFS
from pyshacl.consts import RDFS_subClassOf
from src.utils.safe_transitive import safe_transitive_objects, safe_transitive_subjects


def _infer_type_and_track(
    g, node, cls, discovered_focus_nodes, same_nodes, target_classes, *,
    track_if_cls_in_targets=False
):
    """
    Adds inferred type(s) to the node and optionally tracks focus nodes.

    Parameters:
    - track_if_cls_in_targets: if True, only track if `cls ∈ target_classes`
    
    IMPORTANT: Original only adds the DIRECT class, not superclasses.
    Superclass closure happens separately at the very end.
    """
    # Only add the direct class (matching original behavior)
    g.add((node, RDF.type, cls))

    should_track = (not track_if_cls_in_targets) or (cls in target_classes)
    if should_track and node not in discovered_focus_nodes:
        discovered_focus_nodes.add(node)
        same_nodes[node] = set()


def _expand_property_type(
    g, prop, cls, discovered_focus_nodes, same_nodes, target_classes, *,
    on_subject: bool, track_if_cls_in_targets=False, add_equiv_to_subprop=True
):
    """
    Expands property-based typing using rdfs:range or rdfs:domain
    through equivalentProperty and subPropertyOf closure.
    
    Args:
        add_equiv_to_subprop: If True, materialize owl:equivalentProperty as rdfs:subPropertyOf.
                             Original is inconsistent: does this for domain but NOT for range in target_domain_range.
    """
    # Materialize owl:equivalentProperty as symmetric rdfs:subPropertyOf (if requested)
    if add_equiv_to_subprop:
        for ep in safe_transitive_objects(g, prop, OWL.equivalentProperty):
            g.add((ep, RDFS.subPropertyOf, prop))
            g.add((prop, RDFS.subPropertyOf, ep))
            # Note: original does NOT remove the equivalentProperty edge

        for ep in safe_transitive_subjects(g, OWL.equivalentProperty, prop):
            g.add((ep, RDFS.subPropertyOf, prop))
            g.add((prop, RDFS.subPropertyOf, ep))
            # Note: original does NOT remove the equivalentProperty edge

    all_props = set(safe_transitive_subjects(g, RDFS.subPropertyOf, prop)).union(
        safe_transitive_objects(g, prop, OWL.equivalentProperty),
        safe_transitive_subjects(g, OWL.equivalentProperty, prop)
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
    """Process rdfs:range constraints for target classes.
    
    Original does NOT have a while loop - runs exactly once.
    Original DOES add equiv→subprop edges for range properties.
    """
    for cls in target_classes:
        for pp in g.subjects(RDFS.range, cls):
            # add **ep ⊑ pp** for every equivalentProperty (matching original lines 160-161)
            for ep in safe_transitive_objects(g, pp, OWL.equivalentProperty):
                g.add((ep, RDFS.subPropertyOf, pp))
            for ep in safe_transitive_subjects(g, OWL.equivalentProperty, pp):
                g.add((ep, RDFS.subPropertyOf, pp))

            _expand_property_type(
                g, pp, cls,
                discovered_focus_nodes, same_nodes, target_classes,
                on_subject=False,
                add_equiv_to_subprop=False  # Already done above
            )


def target_domain_range(g, discovered_focus_nodes, same_nodes, target_classes):
    """Process rdfs:domain and rdfs:range constraints for target classes.
    
    Original does NOT have a while loop - runs exactly once.
    Note: Original does NOT add equiv→subprop for range, only for domain.
    """
    for cls in target_classes:
        # Range (no equiv→subprop conversion in original)
        for prop in g.subjects(RDFS.range, cls):
            _expand_property_type(
                g, prop, cls, discovered_focus_nodes, same_nodes, target_classes,
                on_subject=False, add_equiv_to_subprop=False
            )
        # Domain (with equiv→subprop conversion in original)
        for prop in g.subjects(RDFS.domain, cls):
            _expand_property_type(
                g, prop, cls, discovered_focus_nodes, same_nodes, target_classes,
                on_subject=True, add_equiv_to_subprop=True
            )


def check_domain_range(g, p, discovered_focus_nodes, same_nodes, target_classes):
    # ----- domain ------------------------------------------------------
    for cls in g.objects(p, RDFS.domain):
        for subj, _ in g.subject_objects(p):
            _infer_type_and_track(
                g, subj, cls,
                discovered_focus_nodes, same_nodes, target_classes,
                track_if_cls_in_targets=True,   # ⇐ legacy rule
            )

    # ----- range -------------------------------------------------------
    for cls in g.objects(p, RDFS.range):
        for _, obj in g.subject_objects(p):
            _infer_type_and_track(
                g, obj, cls,
                discovered_focus_nodes, same_nodes, target_classes,
                track_if_cls_in_targets=True,
            )