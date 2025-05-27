
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
SH_class = SH["class"]

from rdflib.namespace import Namespace
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
RDFS = Namespace(RDFS_PFX)
RDFS_subPropertyOf = RDFS.subPropertyOf


if TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph
def check_domain_range(g, p, target_nodes, same_nodes, target_classes):
    for o in g.objects(p, RDFS.domain):  # RULE prp-dom
        for x, y in g.subject_objects(p):
            g.add((x, RDF.type, o))
            if (o in target_classes) and (not x in target_nodes):
                target_nodes.add(x)
                same_set = set()
                same_nodes.update({x: same_set})

    for o in g.objects(p, RDFS.range):  # RULE prp-rng
        for x, y in g.subject_objects(p):
            g.add((y, RDF.type, o))
            if (o in target_classes) and (not y in target_nodes):
                target_nodes.add(y)
                same_set = set()
                same_nodes.update({y: same_set})

    return target_nodes


def target_range(g, target_nodes, same_nodes, target_classes):
    for c in target_classes:
        # range
        for pp in g.subjects(RDFS.range, c):

            ep_lis = {s for s in g.transitive_subjects(OWL.equivalentProperty, pp)}

            ep2 = {s for s in g.transitive_objects(pp, OWL.equivalentProperty)}

            ep_lis = ep_lis.union(ep2)
            for ep in ep_lis:
                g.add((ep, RDFS_subPropertyOf, pp))

            sp = g.transitive_subjects(RDFS_subPropertyOf, pp)
            for subp in sp:
                ep1 = {s for s in g.transitive_subjects(OWL.equivalentProperty, subp)}

                ep3 = {s for s in g.transitive_objects(subp, OWL.equivalentProperty)}

                ep1 = ep1.union(ep3)
                for ep in ep1:

                    for ss, oo in g.subject_objects(ep):
                        g.add((oo, RDF.type, c))
                        if not oo in target_nodes:
                            target_nodes.add(oo)
                            same_set = set()
                            same_nodes.update({oo: same_set})

                for ss, oo in g.subject_objects(subp):
                    g.add((oo, RDF.type, c))
                    if not oo in target_nodes:
                        target_nodes.add(oo)
                        same_set = set()
                        same_nodes.update({oo: same_set})

            for s1, oo in g.subject_objects(pp):
                g.add((oo, RDF.type, c))
                if not oo in target_nodes:
                    target_nodes.add(oo)
                    same_set = set()
                    same_nodes.update({oo: same_set})


def target_domain_range(g, target_nodes, same_nodes, target_classes):
    for c in target_classes:
        # range
        for pp in g.subjects(RDFS.range, c):

            ep_lis = {s for s in g.transitive_subjects(OWL.equivalentProperty, pp)}

            ep2 = {s for s in g.transitive_objects(pp, OWL.equivalentProperty)}

            ep_lis = ep_lis.union(ep2)
            for ep in ep_lis:

                for ss, oo in g.subject_objects(ep):
                    g.add((oo, RDF.type, c))
                    if not oo in target_nodes:
                        target_nodes.add(oo)
                        same_set = set()
                        same_nodes.update({oo: same_set})

            sp = g.transitive_subjects(RDFS_subPropertyOf, pp)
            for subp in sp:
                ep1 = {s for s in g.transitive_subjects(OWL.equivalentProperty, subp)}

                ep3 = {s for s in g.transitive_objects(subp, OWL.equivalentProperty)}

                ep1 = ep1.union(ep3)
                for ep in ep1:

                    for ss, oo in g.subject_objects(ep):
                        g.add((oo, RDF.type, c))
                        if not oo in target_nodes:
                            target_nodes.add(oo)
                            same_set = set()
                            same_nodes.update({oo: same_set})

                for ss, oo in g.subject_objects(subp):
                    g.add((oo, RDF.type, c))
                    if not oo in target_nodes:
                        target_nodes.add(oo)
                        same_set = set()
                        same_nodes.update({oo: same_set})

            for s1, oo in g.subject_objects(pp):
                g.add((oo, RDF.type, c))
                if not oo in target_nodes:
                    target_nodes.add(oo)
                    same_set = set()
                    same_nodes.update({oo: same_set})

        # domain
        for p in g.subjects(RDFS.domain, c):

            ep1 = {s for s in g.transitive_subjects(OWL.equivalentProperty, p)}

            ep2 = {s for s in g.transitive_objects(p, OWL.equivalentProperty)}
            ep2 = ep2.union(ep1)
            for ep in ep2:
                g.add((ep, RDFS_subPropertyOf, p))

            sp = g.transitive_subjects(RDFS_subPropertyOf, p)
            for subp in sp:
                ep3 = {s for s in g.transitive_subjects(OWL.equivalentProperty, subp)}

                ep4 = {s for s in g.transitive_objects(subp, OWL.equivalentProperty)}
                ep3 = ep3.union(ep4)
                for ep in ep3:

                    for ss, o in g.subject_objects(ep):
                        g.add((ss, RDF.type, c))
                        if not ss in target_nodes:
                            target_nodes.add(ss)
                            same_set = set()
                            same_nodes.update({ss: same_set})

                for ss, o in g.subject_objects(subp):
                    g.add((ss, RDF.type, c))
                    if not ss in target_nodes:
                        target_nodes.add(ss)
                        same_set = set()
                        same_nodes.update({ss: same_set})

            for s, o in g.subject_objects(p):
                if not (s, RDF.type, c) in g:
                    g.add((s, RDF.type, c))
                if not s in target_nodes:
                    target_nodes.add(s)
                    same_set = set()
                    same_nodes.update({s: same_set})