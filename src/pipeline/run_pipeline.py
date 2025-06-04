# from .target_extraction import extract_targets_and_paths
from .closure_engine import run_closure_loop
from ..core.load import load_graph, load_data_graph, load_shapes_graph
from rdflib.namespace import OWL
from src.types import GraphsBundle, ShapeTargets


def run_merging_pipeline(data_graph, shacl_graph=None, data_graph_format=None, shacl_graph_format=None):
    vg = load_data_graph(data_graph, data_graph_format)
    shapes_graph = load_shapes_graph(shacl_graph, shacl_graph_format)

    graphs = GraphsBundle(data_graph=vg, shapes_graph=shapes_graph)

    targets = ShapeTargets.from_graph_bundle(graphs)
    run_closure_loop(graphs, graphs.shapes_graph.shapes, targets)

    for node, equivalents in targets.same_as_dict.items():
        for eq in equivalents:
            graphs.data_graph.add((node, OWL.sameAs, eq))

    return graphs.data_graph, targets.same_as_dict, graphs.shapes_graph.graph
