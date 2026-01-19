# core/owl_semantics/property_axioms.py

from rdflib.namespace import OWL, RDF
from src.errors import FusionRuntimeError
from src.utils.safe_transitive import safe_transitive_objects


def apply_symmetric_property(g, prop):
    """Implements OWL SymmetricProperty (prp-symp)"""
    if (prop, RDF.type, OWL.SymmetricProperty) in g:
        for s, o in g.subject_objects(prop):
            g.add((o, prop, s))


def apply_transitive_property(g, prop):
    """Implements OWL TransitiveProperty (prp-trp)"""
    if (prop, RDF.type, OWL.TransitiveProperty) in g:
        for s, o in g.subject_objects(prop):
            for o2 in safe_transitive_objects(g, o, prop):
                g.add((s, prop, o2))


def apply_inverse_properties(g, prop):
    """Implements OWL inverseOf (prp-inv)"""
    for inv1 in g.subjects(OWL.inverseOf, prop):
        for x, y in g.subject_objects(inv1):
            g.add((y, prop, x))
        for x, y in g.subject_objects(prop):
            g.add((y, inv1, x))

    for inv2 in g.objects(prop, OWL.inverseOf):
        for x, y in g.subject_objects(inv2):
            g.add((y, prop, x))
        for x, y in g.subject_objects(prop):
            g.add((y, inv2, x))


def apply_functional_property(g, prop):
    """Implements OWL FunctionalProperty (prp-fp)"""
    if (prop, RDF.type, OWL.FunctionalProperty) in g:
        for s, o1 in g.subject_objects(prop):
            for o2 in g.objects(s, prop):
                if o1 != o2:
                    g.add((o1, OWL.sameAs, o2))


def apply_inverse_functional_property(g, prop):
    """Implements OWL InverseFunctionalProperty (prp-ifp)
    
    Creates sameAs edges for subjects with the same value.
    Direction matters: creates (s1, sameAs, s2) which later makes s1 the canonical representative.
    Uses consistent ordering to prefer lowercase URIs as canonical.
    """
    if (prop, RDF.type, OWL.InverseFunctionalProperty) in g:
        for s1, o in g.subject_objects(prop):
            for s2 in g.subjects(prop, o):
                if s1 != s2:
                    # Prefer lowercase version as canonical (e.g., :alice over :Alice)
                    # Compare case-insensitively, but if equal, prefer lowercase
                    s1_str = str(s1)
                    s2_str = str(s2)
                    
                    # If one ends with lowercase and other with uppercase of same name, prefer lowercase
                    s1_local = s1_str.split('#')[-1].split('/')[-1]
                    s2_local = s2_str.split('#')[-1].split('/')[-1]
                    
                    if s1_local.lower() == s2_local.lower():
                        # Same name different case - prefer lowercase
                        if s1_local.islower() and not s2_local.islower():
                            g.add((s1, OWL.sameAs, s2))
                        elif s2_local.islower() and not s1_local.islower():
                            g.add((s2, OWL.sameAs, s1))
                        else:
                            # Both same case or both mixed - use alphabetical
                            if s1_str < s2_str:
                                g.add((s1, OWL.sameAs, s2))
                            else:
                                g.add((s2, OWL.sameAs, s1))
                    else:
                        # Different names - use alphabetical order for determinism
                        if s1_str < s2_str:
                            g.add((s1, OWL.sameAs, s2))
                        else:
                            g.add((s2, OWL.sameAs, s1))
