from rdflib import Graph
from rdflib.namespace import OWL
from rdflib.term import Node

from .closure_engine import run_closure_loop
from ..core.load import load_data_graph, load_shapes_graph
from src.types.merge_inputs import extract_merge_inputs, MergeInputs
from src.types import GraphsBundle


def run_merging_pipeline(
        data_graph, shacl_graph=None, data_graph_format=None, shacl_graph_format=None
) -> tuple[Graph, dict[Node, set[Node]], Graph]:
    """
    Executes the full merging pipeline:

    1. Loads RDF and SHACL graphs from given file paths or RDFLib inputs.
    2. Extracts key elements used in reasoning:
       - target classes (C)
       - focus nodes (P)
       - relevant properties (F)
       - same-as identity tracking (N)
    3. Performs reasoning, inference, and merging on the data graph.
    4. Annotates the resulting graph with owl:sameAs triples for all merged entities.
    5. Returns the final fused graph, same-as dictionary, and the parsed shapes graph.

    Returns:
        - fused_data_graph: Graph after reasoning and merging
        - same_as_dict: Dict[node → set[node]] of merged identities
        - shapes_graph: Original parsed SHACL shapes graph
    """
    data_graph_loaded = load_data_graph(data_graph, data_graph_format)
    shapes_graph = load_shapes_graph(shacl_graph, shacl_graph_format)

    graphs = GraphsBundle(data_graph=data_graph_loaded, shapes_graph=shapes_graph)

    # Extract target sets for reasoning: C, P, F, N
    inputs: MergeInputs = extract_merge_inputs(graphs)

    # Execute inference and closure over graph + targets
    run_closure_loop(graphs, inputs)

    # Inject owl:sameAs links into the data graph
    _add_same_as_triples(graphs.data_graph, inputs.same_as_dict)

    return graphs.data_graph, inputs.same_as_dict, graphs.shapes_graph.graph


def _add_same_as_triples(graph: Graph, same_as_dict: dict[Node, set[Node]]):
    for node, equivalents in same_as_dict.items():
        for eq in equivalents:
            graph.add((node, OWL.sameAs, eq))
