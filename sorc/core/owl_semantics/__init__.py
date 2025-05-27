# core/owl_semantics/__init__.py

# Property-level axioms (OWL prp-* rules)
from .property_axioms import (
    apply_symmetric_property,
    apply_transitive_property,
    apply_inverse_properties,
    apply_functional_property,
    apply_inverse_functional_property,
)

# Class-level axioms (OWL cls-*, cax-* rules)
from .class_axioms import (
    check_disjoint_classes,
)

# Individual-level axioms (OWL eq/diff rules)
from .individual_axioms import (
    check_same_as_conflict,
    check_irreflexive_property,
)

# Validation that halts the pipeline
from .validate_checks import (
    check_asymmetric_property,
    check_irreflexive_property,
    check_sameas_differentfrom_conflict,
    check_disjoint_classes,
    check_complement_classes,
)
