from typing import Union, Optional

import rdflib
from pyshacl import ShapesGraph
from pyshacl.monkey import rdflib_bool_patch, rdflib_bool_unpatch
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import load_from_source


def load_graph(data_graph: Union[GraphLike, str, bytes],
               shacl_graph: Optional[Union[GraphLike, str, bytes]] = None,
               data_graph_format: Optional[str] = None,
               shacl_graph_format: Optional[str] = None,
               ):
    loaded_dg = load_from_source(data_graph, rdf_format=data_graph_format, multigraph=True, do_owl_imports=False)
    if not isinstance(loaded_dg, rdflib.Graph):
        raise RuntimeError("data_graph must be a rdflib Graph object")

    if shacl_graph is not None:
        rdflib_bool_patch()
        loaded_sg = load_from_source(
            shacl_graph, rdf_format=shacl_graph_format, multigraph=False, do_owl_imports=False)
        rdflib_bool_unpatch()
    else:
        loaded_sg = None

    assert isinstance(loaded_sg, rdflib.Graph), "shacl_graph must be a rdflib Graph object"
    shape_graph = ShapesGraph(loaded_sg, None)  # type: ShapesGraph

    shapes = shape_graph.shapes  # This property getter triggers shapes harvest.

    the_target_graph = loaded_dg
    if isinstance(the_target_graph, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
        named_graphs = [
            rdflib.Graph(the_target_graph.store, i, namespace_manager=the_target_graph.namespace_manager)
            if not isinstance(i, rdflib.Graph)
            else i
            for i in the_target_graph.store.contexts(None)
        ]
    else:
        named_graphs = [the_target_graph]

    return shapes, named_graphs, shape_graph

