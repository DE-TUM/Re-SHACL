from typing import Union, Optional
from rdflib import Graph, Dataset, ConjunctiveGraph
from pyshacl import ShapesGraph
from pyshacl.pytypes import GraphLike
from pyshacl.monkey import rdflib_bool_patch, rdflib_bool_unpatch
from pyshacl.rdfutil import load_from_source


def load_data_graph(source: Union[GraphLike, str, bytes], rdf_format: Optional[str] = None) -> Graph:
    """
    Loads a data graph from path, bytes, or Graph-like input.
    If it's a dataset or conjunctive graph, returns the first named graph.
    """
    graph = load_from_source(source, rdf_format=rdf_format, multigraph=True, do_owl_imports=False)

    if isinstance(graph, (Dataset, ConjunctiveGraph)):
        return _extract_named_graphs(graph)[0]
    elif isinstance(graph, Graph):
        return graph
    else:
        raise ValueError("Unsupported RDF input type for data graph.")


def load_shapes_graph(source: Union[GraphLike, str, bytes], rdf_format: Optional[str] = None) -> ShapesGraph:
    """
    Loads a SHACL shapes graph from path, bytes, or Graph-like input.
    Wraps the result in a ShapesGraph and triggers shape extraction.
    """
    rdflib_bool_patch()
    graph = load_from_source(source, rdf_format=rdf_format, multigraph=False, do_owl_imports=False)
    rdflib_bool_unpatch()

    if not isinstance(graph, Graph):
        raise ValueError("SHACL graph must be a single rdflib.Graph")

    return ShapesGraph(graph, None)


def _extract_named_graphs(dataset: Union[Dataset, ConjunctiveGraph]) -> list[Graph]:
    """
    Converts all named graphs in a dataset into rdflib.Graph objects.
    """
    return [
        Graph(dataset.store, ctx, namespace_manager=dataset.namespace_manager)
        if not isinstance(ctx, Graph) else ctx
        for ctx in dataset.store.contexts(None)
    ]
