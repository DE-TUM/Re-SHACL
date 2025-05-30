
from rdflib.namespace import OWL, RDF, RDFS, SH

SH_class = SH["class"]

from rdflib.namespace import Namespace
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
RDFS = Namespace(RDFS_PFX)
RDFS_subPropertyOf = RDFS.subPropertyOf




def has_merge_candidates(g, node, predicates):
    for pred, direction in predicates:
        if direction == 'obj':
            if any(g.objects(node, pred)):
                return True
        elif direction == 'subj':
            if any(g.subjects(pred, node)):
                return True
    return False

def all_samePath_merged(g, path_values):
    merge_preds = [
        (OWL.sameAs, 'obj'),
        (OWL.sameAs, 'subj'),
        (OWL.equivalentProperty, 'obj'),
        (OWL.equivalentProperty, 'subj'),
        (RDFS.subPropertyOf, 'subj')
    ]
    return all(not has_merge_candidates(g, p, merge_preds) for p in path_values)


def all_property_merged(g, prop):
    merge_preds = [
        (OWL.sameAs, 'obj'),
        (OWL.sameAs, 'subj'),
        (OWL.equivalentProperty, 'obj'),
        (OWL.equivalentProperty, 'subj')
    ]
    return not has_merge_candidates(g, prop, merge_preds)


def all_subProperties_merged(g, p):
    return not any(g.subjects(RDFS.subPropertyOf, p))


def all_focus_merged(g, focus, target_nodes):
    if any(g.objects(focus, OWL.sameAs)):
        return False
    for s in g.subjects(OWL.sameAs, focus):
        if s not in target_nodes:
            return False
    return True


def all_targetClasses_merged(g, target_classes):
    merge_preds = [
        (OWL.sameAs, 'obj'),
        (OWL.sameAs, 'subj'),
        (OWL.equivalentClass, 'obj'),
        (OWL.equivalentClass, 'subj')
    ]
    return all(not has_merge_candidates(g, cls, merge_preds) for cls in target_classes)


def sameClasses_merged(g, target_class):
    merge_preds = [
        (OWL.sameAs, 'obj'),
        (OWL.sameAs, 'subj'),
        (OWL.equivalentClass, 'obj'),
        (OWL.equivalentClass, 'subj')
    ]
    return not has_merge_candidates(g, target_class, merge_preds)
