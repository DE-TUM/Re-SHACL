# core/merging/property_merging.py  –  legacy-accurate & fast
from rdflib.namespace import RDF, RDFS, OWL, SH
from pyshacl.consts import SH_path

from src.core.owl_semantics.domain_range import check_domain_range
from src.core.owl_semantics import (
    apply_symmetric_property,
    apply_transitive_property,
    apply_inverse_properties,
    apply_functional_property,
    apply_inverse_functional_property,
)


# ------------------------------------------------------------------ #
#   public entry point
# ------------------------------------------------------------------ #
def merge_same_property(graphs, inputs):
    """
    Legacy two-while-loop property merge – translated exactly, with faster
    iterators and one safety fix (remove rep ⊑ sub after scm-eqp2).
    """
    g   = graphs.data_graph
    sg  = graphs.shapes_graph.graph
    shapes = graphs.shapes_graph.shapes
    prop_shapes = {ps for sh in shapes for ps in sh.property_shapes()}

    for focus in (inputs.property_paths):       # legacy iterated over a copy
        _collapse_subproperty_chain(g, focus)
        _collapse_equivalent_properties(g, focus, prop_shapes, sg, set(inputs.property_paths))
        _apply_semantics(g, focus, inputs)


# ------------------------------------------------------------------ #
#   helper – find if equivalence loop must run again
# ------------------------------------------------------------------ #
def _needs_property_merge(g, prop) -> bool:
    return (
        _non_empty(g.objects(prop, OWL.sameAs)) or
        _non_empty(g.subjects(OWL.sameAs, prop)) or
        _non_empty(g.objects(prop, OWL.equivalentProperty)) or
        _non_empty(g.subjects(OWL.equivalentProperty, prop))
    )


def _non_empty(it) -> bool:
    """True  iff  the rdflib iterator yields at least one result."""
    return next(iter(it), None) is not None

# ------------------------------------------------------------------ #
#   step 1 – legacy subPropertyOf while-loop
# ------------------------------------------------------------------ #
def _collapse_subproperty_chain(g, rep):
    i = 0
    changed = True
    while changed:
        changed = False
        i += 1
        # ----------------------------------------------------------
        # print how many subPropertyOf edges still point to *rep*
        if i % 20 == 1:            # print every 20th iteration
            dangling = sum(1 for _ in g.subjects(RDFS.subPropertyOf, rep))
            print(f"[subChain] {rep}  iteration {i}  dangling sub⊑rep: {dangling}")
        for sub in (g.subjects(RDFS.subPropertyOf, rep)):
            changed = True
            if (rep, RDFS.subPropertyOf, sub) in g:            # scm-eqp2
                g.add((rep, OWL.sameAs, sub))
                g.remove((rep, RDFS.subPropertyOf, sub))       # ★ remove forward edge
            else:
                for p3 in g.subjects(RDFS.subPropertyOf, sub):  # scm-spo
                    if rep != p3:
                        g.add((p3, RDFS.subPropertyOf, rep))

                for d in g.objects(rep, RDFS.domain):           # scm-dom2
                    g.add((sub, RDFS.domain, d))
                for r in g.objects(rep, RDFS.range):            # scm-rng2
                    g.add((sub, RDFS.range, r))
                for s, o in (g.subject_objects(sub)):      # prp-spo1
                    g.add((s, rep, o))

            g.remove((sub, RDFS.subPropertyOf, rep))


# ------------------------------------------------------------------ #
#   step 2 – legacy equivalentProperty / sameAs while-loop
# ------------------------------------------------------------------ #
def _collapse_equivalent_properties(g, rep, prop_shapes, sg, path_set):
    j = 0
    while _needs_property_merge(g, rep):
        j += 1
        # ----------------------------------------------------------
        if j % 20 == 1:
            same_as = (sum(1 for _ in g.objects(rep, OWL.sameAs)) +
                       sum(1 for _ in g.subjects(OWL.sameAs, rep)))
            equiv   = (sum(1 for _ in g.objects(rep, OWL.equivalentProperty)) +
                       sum(1 for _ in g.subjects(OWL.equivalentProperty, rep)))
            print(f"[equivLoop] {rep}  iter {j}  sameAs:{same_as}  equivP:{equiv}")
        g.remove((rep, OWL.sameAs, rep))                       # clean reflexive

        # ---- convert equivalentProperty edges into sameAs
        for p in (g.subjects(OWL.equivalentProperty, rep)):
            g.remove((p, OWL.equivalentProperty, rep))
            g.add((rep, OWL.sameAs, p))
        for p in (g.objects(rep, OWL.equivalentProperty)):
            g.remove((rep, OWL.equivalentProperty, p))
            g.add((rep, OWL.sameAs, p))

        # ---- normalise incoming sameAs direction
        for p in (g.subjects(OWL.sameAs, rep)):
            g.remove((p, OWL.sameAs, rep))
            g.add((rep, OWL.sameAs, p))

        # ---- merge every sameAs peer into rep
        for same_p in (g.objects(rep, OWL.sameAs)):
            g.remove((same_p, OWL.sameAs, same_p))             # drop reflexive

            if same_p != rep:
                # copy predicate/object triples
                for pred, obj in (g.predicate_objects(same_p)):
                    g.remove((same_p, pred, obj))
                    g.add((rep, pred, obj))

                # copy subject/predicate triples
                for subj, pred in (g.subject_predicates(same_p)):
                    g.remove((subj, pred, same_p))
                    g.add((subj, pred, rep))

                # rewrite (subj same_p obj) → (subj rep obj)
                for subj, obj in (g.subject_objects(same_p)):
                    g.add((subj, rep, obj))
                    g.remove((subj, same_p, obj))

                # rewrite SHACL property-shapes paths
                if same_p in path_set:
                    for b in prop_shapes:
                        if (b, SH_path, same_p) in sg:
                            sg.remove((b, SH_path, same_p))
                            sg.add((b, SH_path, rep))

            g.remove((rep, OWL.sameAs, same_p))                # drop edge

        # end while _needs_property_merge


# ------------------------------------------------------------------ #
#   step 3 – semantics (unchanged)
# ------------------------------------------------------------------ #
def _apply_semantics(g, prop, inputs):
    apply_symmetric_property(g, prop)
    apply_transitive_property(g, prop)
    apply_inverse_properties(g, prop)
    check_domain_range(g, prop,
                       inputs.discovered_focus_nodes,
                       inputs.same_as_dict,
                       inputs.target_classes)
    apply_functional_property(g, prop)
    apply_inverse_functional_property(g, prop)
