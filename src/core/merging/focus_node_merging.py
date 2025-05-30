from rdflib.namespace import OWL
from pyshacl.consts import SH_targetNode


def merge_same_focus(g, same_nodes, focus, target_nodes, shapes, shacl_graph):
    normalize_sameAs_edges(g, focus)

    for o in list(g.objects(focus, OWL.sameAs)):
        if o == focus:
            g.remove((focus, OWL.sameAs, focus))
            continue

        merge_focus_equivalents(g, focus, o)
        update_same_nodes_dict(same_nodes, focus, o)

        if o in target_nodes:
            rewrite_shape_target_nodes(shapes, shacl_graph, o, focus)

        g.remove((focus, OWL.sameAs, o))


def normalize_sameAs_edges(g, focus):
    for s in list(g.subjects(OWL.sameAs, focus)):
        if s != focus:
            g.remove((s, OWL.sameAs, focus))
            g.add((focus, OWL.sameAs, s))


def merge_focus_equivalents(g, focus, other):
    for p, o in list(g.predicate_objects(other)):
        g.remove((other, p, o))
        g.add((focus, p, o))

    for s, p in list(g.subject_predicates(other)):
        g.remove((s, p, other))
        g.add((s, p, focus))


def update_same_nodes_dict(same_nodes, focus, other):
    same_set = same_nodes[focus]
    same_set.add(other)

    if other in same_nodes:
        same_set.update(same_nodes[other])
        del same_nodes[other]


def rewrite_shape_target_nodes(shapes, shacl_graph, old_node, new_node):
    for shape in shapes:
        if old_node in shacl_graph.objects(shape.node, SH_targetNode):
            shacl_graph.remove((shape.node, SH_targetNode, old_node))
            shacl_graph.add((shape.node, SH_targetNode, new_node))
