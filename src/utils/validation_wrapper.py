from pyshacl import validate
from rdflib import Graph
from typing import Union, Optional, Tuple

from ..core.loader import load_graph


def validate_fused_graph(
    data_graph: Union[str, bytes, Graph],
    shacl_graph: Union[str, bytes, Graph],
    data_graph_format: Optional[str] = None,
    shacl_graph_format: Optional[str] = None,
    inference: Optional[str] = "none",
    abort_on_error: bool = False,
    advanced: bool = True,
) -> Tuple[bool, Graph, str]:
    """
    Runs SHACL validation on a fused/inferred RDF graph.

    Parameters:
    - data_graph: The RDF graph after inference/merging (file path, bytes, or Graph object)
    - shacl_graph: The SHACL shapes graph
    - data_graph_format: Format of the data graph (e.g., 'turtle')
    - shacl_graph_format: Format of the shapes graph
    - inference: Type of inference ('rdfs', 'owlrl', 'none')
    - abort_on_error: If True, raises exception on error
    - advanced: If True, enables advanced SHACL features

    Returns:
    - A tuple (conforms, results_graph, results_text)
    """
    conforms, results_graph, results_text = validate(
        data_graph=data_graph,
        shacl_graph=shacl_graph,
        data_graph_format=data_graph_format,
        shacl_graph_format=shacl_graph_format,
        inference=inference,
        abort_on_error=abort_on_error,
        advanced=advanced,
        serialize_report_graph=True,
    )
    return conforms, results_graph, results_text
