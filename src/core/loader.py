import rdflib
from typing import Union, Optional
from pyshacl.rdfutil import load_from_source
from pyshacl.monkey import rdflib_bool_patch, rdflib_bool_unpatch
from pyshacl.pytypes import GraphLike
from pyshacl.shapes_graph import ShapesGraph


def load_graph(
    data_graph: Union[GraphLike, str, bytes],
    shacl_graph: Optional[Union[GraphLike, str, bytes]] = None,
    data_graph_format: Optional[str] = None,
    shacl_graph_format: Optional[str] = None,
):
    loaded_dg = load_from_source(data_graph, rdf_format=data_graph_format, multigraph=True, do_owl_imports=False)
    if not isinstance(loaded_dg, rdflib.Graph):
        raise RuntimeError("data_graph must be an rdflib Graph")

    if shacl_graph is not None:
        rdflib_bool_patch()
        loaded_sg = load_from_source(shacl_graph, rdf_format=shacl_graph_format, multigraph=False, do_owl_imports=False)
        rdflib_bool_unpatch()
    else:
        loaded_sg = None

    if loaded_sg is not None and not isinstance(loaded_sg, rdflib.Graph):
        raise RuntimeError("shacl_graph must be an rdflib Graph")

    shape_graph = ShapesGraph(loaded_sg, None)
    shapes = shape_graph.shapes

    if isinstance(loaded_dg, (rdflib.Dataset, rdflib.ConjunctiveGraph)):
        named_graphs = [
            rdflib.Graph(loaded_dg.store, i, namespace_manager=loaded_dg.namespace_manager)
            if not isinstance(i, rdflib.Graph) else i
            for i in loaded_dg.store.contexts(None)
        ]
    else:
        named_graphs = [loaded_dg]

    return shapes, named_graphs, shape_graph