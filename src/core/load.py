from typing import Union, Optional

import rdflib
from pyshacl.monkey import rdflib_bool_patch, rdflib_bool_unpatch
from pyshacl.pytypes import GraphLike
from pyshacl.rdfutil import load_from_source
from pyshacl import ShapesGraph
from rdflib import Graph, Dataset, ConjunctiveGraph

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


def load_data_graph(path: str, format: str = "turtle") -> Graph:
    g = Graph()
    g.parse(path, format=format)

    if isinstance(g, (Dataset, ConjunctiveGraph)):
        named_graphs = _extract_named_graphs(g)
        return named_graphs[0]  # preserve old behavior, but make it explicit
    elif isinstance(g, Graph):
        return g
    else:
        raise ValueError("Unsupported RDF input type.")


def _extract_named_graphs(dataset: Union[Dataset, ConjunctiveGraph]) -> list[Graph]:
    return [
        Graph(dataset.store, ctx, namespace_manager=dataset.namespace_manager)
        if not isinstance(ctx, Graph)
        else ctx
        for ctx in dataset.store.contexts(None)
    ]


def load_shapes_graph(path: str, format: str = "turtle") -> ShapesGraph:
    sg = Graph()
    sg.parse(path, format=format)
    shapes_graph = ShapesGraph(sg, None)

    return shapes_graph





