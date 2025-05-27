from .core.domain_range import *
from .core.load import load_graph
from .core.merge import *
from .core.owl_semantics import *
from .utils.merge_helpers import *

from pyshacl.pytypes import GraphLike


from rdflib.namespace import OWL, SH


from typing import TYPE_CHECKING, Optional,  Union

from pyshacl.consts import (
    SH_path,
    SH_node,
    RDFS_subClassOf,
)



SH_class = SH["class"]

from rdflib.namespace import Namespace
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
RDFS = Namespace(RDFS_PFX)
RDFS_subPropertyOf = RDFS.subPropertyOf


if TYPE_CHECKING:
    from pyshacl.shapes_graph import ShapesGraph


def merged_graph(
        data_graph: Union[GraphLike, str, bytes],
        shacl_graph: Optional[Union[GraphLike, str, bytes]] = None,
        data_graph_format: Optional[str] = None,
        shacl_graph_format: Optional[str] = None,
):

    shapes, named_graphs, shape_graph = load_graph( data_graph, shacl_graph, data_graph_format ,shacl_graph_format)

    shape_g = shape_graph.graph

    # print("shape_graph:",type(shape_graph))
    # print("shape_graph.graph:",type(shape_graph.graph))
    # print("shape_g:",type(shape_g))

    vg = named_graphs[0]
    found_node_targets = set()
    target_classes = set()
    path_value = set()
    found_target_classes = set()
    global_path = set()
    same_nodes = dict()

    shape_linked_target = set()
    sh_class = set()

    target_nodes =set()
    for s in shapes:
        targets = s.target_nodes()
        target_nodes.update(targets)

        focus = s.focus_nodes(vg)
        found_node_targets.update(focus)
        target_classes.update(s.target_classes())
        target_classes.update(s.implicit_class_targets())

        target_property =set(s.property_shapes())

        if len(set(s.target_classes()) )== 0:
            for blin in target_property:
                global_path.update(s.sg.graph.objects(blin, SH_path))

        for kind_property in target_property:
            if len(set(s.sg.graph.objects(kind_property, SH_node)) )!= 0 :

                shape_linked_target.update(s.sg.graph.objects(kind_property, SH_path))

            if len(set(s.sg.graph.objects(kind_property, SH_class)) )!= 0 :
                sh_class.update(s.sg.graph.objects(kind_property, SH_class))

        target_classes.update(sh_class)

        for blin in target_property:
            path_value.update(s.sg.graph.objects(blin, SH_path))


    fa_p = set()
    for tp in path_value:
        vp = vg.transitive_objects(tp, RDFS_subPropertyOf)
        for propertis in vp :
            if propertis == tp:
                continue
            fa_p.add(propertis)
    path_value.update(fa_p)

    for tc in target_classes:
        subc = vg.transitive_subjects(RDFS_subClassOf, tc)
        for subclass in subc:
            if subclass == tc:
                continue
            found_target_classes.add(subclass)
    target_classes.update(found_target_classes)


    for path_ahead in shape_linked_target:
        for x in vg.objects(None, path_ahead):
            found_node_targets.add(x)

    for f in found_node_targets:
        same_set = set()
        same_nodes.update({f: same_set})

    target_domain_range(vg, found_node_targets, same_nodes, target_classes)

    for focus_node in found_node_targets:

        while not all_focus_merged(vg, focus_node, found_node_targets):

            merge_same_focus(vg, same_nodes, focus_node, target_nodes, shapes, shape_g)
            # check_com_dw(vg, target_classes)

    while (not all_targetClasses_merged(vg, target_classes)) or (not all_samePath_merged(vg, path_value)):

        merge_target_classes(vg, found_node_targets, same_nodes, target_classes)
        target_range(vg, found_node_targets, same_nodes, target_classes)

        # merge same properties
        merge_same_property(vg, path_value, found_node_targets, same_nodes, target_classes, shapes, target_property, shape_g)

        # merge same nodes
        for focus_node in found_node_targets:

            while not all_focus_merged(vg, focus_node, found_node_targets):

                merge_same_focus(vg, same_nodes, focus_node, target_nodes, shapes, shape_g)
                # check_com_dw(vg, target_classes)


        for path_ahead in shape_linked_target:
            for x in vg.objects(None, path_ahead):
                if x not in found_node_targets:
                    found_node_targets.add(x)
                    same_set = set()
                    same_nodes.update({x: same_set})

    for node in found_node_targets:
        for p ,o in vg.predicate_objects(node):
            subp = vg.transitive_objects(p ,RDFS_subPropertyOf)
            for subpropertyOf in iter(subp):
                if subpropertyOf == p:
                    continue
                else:
                    vg.add((node ,subpropertyOf ,o))

    # Add all original triples with property owl:sameAs
    for k in same_nodes:
        for se in same_nodes[k]:
            vg.add((k, OWL.sameAs, se))


    return vg, same_nodes, shape_g # output_shapes
