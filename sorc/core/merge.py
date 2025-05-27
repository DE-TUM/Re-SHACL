from .domain_range import check_domain_range
from .owl_semantics import *
from ..errors import FusionRuntimeError
from pyshacl.pytypes import GraphLike
import rdflib

from rdflib.namespace import OWL, RDF, RDFS, SH
from rdflib import Graph
from pyshacl.shapes_graph import ShapesGraph

from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Set, Tuple, Union

from pyshacl.monkey import rdflib_bool_patch, rdflib_bool_unpatch
from pyshacl.rdfutil import (
    load_from_source,
)
from pyshacl.consts import (
    SH_path,
    SH_node,
    RDFS_subClassOf,
    SH_targetNode,
)

from ..utils.merge_helpers import sameClasses_merged, all_subProperties_merged, all_property_merged

SH_class = SH["class"]

from rdflib.namespace import Namespace
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
RDFS = Namespace(RDFS_PFX)
RDFS_subPropertyOf = RDFS.subPropertyOf


if TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph


def merge_target_classes(g, found_node_targets, same_nodes, target_classes):  # TODO: subClass use cases
    eq_targetClass = set()
    eq_targetNodes = set()
    for c in target_classes:
        while not sameClasses_merged(g, c):
            # print("Merge Classes")
            for c1 in g.subjects(OWL.equivalentClass, c): # c1 == c
                eq_targetClass.add(c1)
                for s in g.subjects(RDF.type, c1):
                    eq_targetNodes.add(s)
                    g.add((s, RDF.type, c))
                for ss in g.subjects(RDF.type, c):
                    g.add((ss, RDF.type, c1))
                g.remove((c1, OWL.equivalentClass, c))
                g.add((c1, RDFS.subClassOf, c))
                g.add((c, RDFS.subClassOf, c1))
            for c2 in g.objects(c, OWL.equivalentClass): # c == c2
                eq_targetClass.add(c2)
                for s in g.subjects(RDF.type, c2):
                    eq_targetNodes.add(s)
                    g.add((s, RDF.type, c))
                for ss in g.subjects(RDF.type, c):
                    g.add((ss, RDF.type, c2))
                g.remove((c, OWL.equivalentClass, c2))
                g.add((c2, RDFS.subClassOf, c))
                g.add((c, RDFS.subClassOf, c2))
            for c1 in g.subjects(OWL.sameAs, c): # c1 == c
                eq_targetClass.add(c1)
                for s in g.subjects(RDF.type, c1):
                    eq_targetNodes.add(s)
                    g.add((s, RDF.type, c))
                for ss in g.subjects(RDF.type, c):
                    g.add((ss, RDF.type, c1))
                g.remove((c1, OWL.sameAs, c))
                g.add((c1, RDFS.subClassOf, c))
                g.add((c, RDFS.subClassOf, c1))
            for c2 in g.objects(c, OWL.sameAs): # c == c2
                eq_targetClass.add(c2)
                for s in g.subjects(RDF.type, c2):
                    eq_targetNodes.add(s)
                    g.add((s, RDF.type, c))
                for ss in g.subjects(RDF.type, c):
                    g.add((ss, RDF.type, c2))
                g.remove((c, OWL.equivalentClass, c2))
                g.add((c2, RDFS.subClassOf, c))
                g.add((c, RDFS.subClassOf, c2))


    for new_node in eq_targetNodes:
        if new_node not in found_node_targets:
            same_set = set()
            same_nodes.update({new_node: same_set})

    found_node_targets.update(eq_targetNodes)
    target_classes.update(eq_targetClass)



def merge_same_property(g, properties, found_node_targets, same_nodes, target_classes, shapes, target_property, shacl_graph):
    for focus_property in properties:

        while not all_subProperties_merged(g, focus_property):
            # print("Merge subProperties")
            for sub_p in g.subjects(RDFS.subPropertyOf, focus_property):
                if (focus_property, RDFS.subPropertyOf, sub_p) in g: # scm-eqp2
                    g.add((focus_property, OWL.sameAs, sub_p))
                else:
                    for p3 in g.subjects(RDFS.subPropertyOf, sub_p): # RULE scm-spo
                        if focus_property != p3:
                            g.add((p3, RDFS.subPropertyOf, focus_property))

                    for c in g.objects(focus_property ,RDFS.domain): # scm-dom2
                        g.add((sub_p, RDFS.domain, c))

                    for c1 in g.objects(focus_property ,RDFS.range): # scm-rng2
                        g.add((sub_p, RDFS.range, c1))

                    for x, y in g.subject_objects(sub_p): # prp-spo1
                        g.add((x, focus_property, y))

                g.remove((sub_p, RDFS.subPropertyOf, focus_property)) # 可能后退一格


        while not all_property_merged(g, focus_property):
            # print(focus_property)
            g.remove((focus_property, OWL.sameAs, focus_property))

            for p1 in g.subjects(OWL.equivalentProperty, focus_property):
                g.remove((p1, OWL.equivalentProperty, focus_property))
                g.add((focus_property, OWL.sameAs, p1))
            for p2 in g.objects(focus_property, OWL.equivalentProperty):
                g.remove((focus_property, OWL.equivalentProperty, p2))
                g.add((focus_property, OWL.sameAs, p2))

            for same_prop in g.subjects(OWL.sameAs, focus_property):
                g.remove((same_prop, OWL.sameAs, focus_property))
                g.add((focus_property, OWL.sameAs, same_prop))

            for same_property in g.objects(focus_property, OWL.sameAs):
                # check_irreflexiveProperty(g, same_property)
                # check_asymmetricProperty(g, same_property)
                g.remove((same_property, OWL.sameAs, same_property))

                if same_property != focus_property:

                    for p, o in g.predicate_objects(same_property):
                        g.remove((same_property, p, o))
                        g.add((focus_property, p, o))
                    for s, p in g.subject_predicates(same_property):
                        g.remove((s, p, same_property))
                        g.add((s, p, focus_property))
                    for s, o in g.subject_objects(same_property):
                        g.add((s, focus_property, o))
                        g.remove((s, same_property, o))

                    if same_property in properties:
                        # properties.remove(same_property)
                        for s in shapes:  # Shapes graph re-writing
                            for blin in target_property:
                                # if same_property in s.sg.graph.objects(blin, SH_path):
                                #     s.sg.graph.remove((blin, SH_path, same_property))
                                #     s.sg.graph.add((blin, SH_path, focus_property))
                                if same_property in shacl_graph.objects(blin, SH_path):
                                    shacl_graph.remove((blin, SH_path, same_property))
                                    shacl_graph.add((blin, SH_path, focus_property))

                g.remove((focus_property, OWL.sameAs, same_property))


        # check_propertyDisjointWith(g, focus_property)
        check_symmetricProperty(g, focus_property)
        check_transitiveProperty(g, focus_property)
        check_inverseOf(g, focus_property)
        check_domain_range(g, focus_property, found_node_targets, same_nodes, target_classes)
        # check_com_dw(g, target_classes)
        check_FunctionalProperty(g, focus_property)
        check_InverseFunctionalProperty(g, focus_property)




def merge_same_focus(g, same_nodes, focus,  target_nodes, shapes, shacl_graph):
    # eq-sym
    for s in g.subjects(OWL.sameAs, focus): # s = focus node
        # check_eq_diff_erro(g, s, focus)
        if s != focus:
            g.remove((s, OWL.sameAs, focus))
            g.add((focus, OWL.sameAs, s)) # s = focus --> focus = s


    for o in g.objects(focus, OWL.sameAs):   # focus node = o

        # check_eq_diff_erro(g, focus, o)
        same_set = same_nodes[focus]
        same_set.add(o)
        if o != focus :
            if o in same_nodes:
                for i in same_nodes[o]:
                    same_set.add(i)
                del same_nodes[o]

            # for "eq-trans", "eq-rep-s", "eq-rep-o"
            for pp, oo in g.predicate_objects(o): # o pp oo --> focus pp oo
                g.remove((o, pp, oo))
                g.add((focus, pp, oo))

            for ss, pp in g.subject_predicates(o): # ss pp o --> ss pp fucus
                g.remove((ss, pp, o))
                g.add((ss, pp, focus))

            if o in target_nodes :
                for s in shapes:  # Shapes graph re-writing
                    if o in shacl_graph.objects(s.node, SH_targetNode):
                        shacl_graph.remove((s.node, SH_targetNode, o))
                        shacl_graph.add((s.node, SH_targetNode, focus))
            g.remove((focus, OWL.sameAs, o))
            g.remove((focus, OWL.sameAs, focus))
        else:
            g.remove((focus, OWL.sameAs, focus))
