from src.rules.rdfs.domain_range import apply_domain_range_rules
from src.rules.rdfs.subproperty import _apply_subproperty_closure


def apply_rdfs_axioms(g, shapes):
    _apply_subproperty_closure(g)
    apply_domain_range_rules(g, shapes)