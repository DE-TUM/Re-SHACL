# from .target_extraction import extract_targets_and_paths
from .closure_engine import run_closure_loop
from ..core.load import load_graph
from rdflib.namespace import OWL
from src.types import GraphsBundle, ShapeTargets


def run_merging_pipeline(data_graph, shacl_graph=None, data_graph_format=None, shacl_graph_format=None):
    shapes, named_graphs, shape_graph = load_graph(
        data_graph, shacl_graph, data_graph_format, shacl_graph_format
    )
    vg = named_graphs[0]
    graphs = GraphsBundle(data_graph=vg, shapes_graph=shape_graph.graph)

    # Extract all shape targets
    targets = ShapeTargets.from_shapes(shapes, vg)

    # Run closure loop with grouped inputs
    run_closure_loop(
        graphs,
        shapes,
        targets
    )

    # Add owl:sameAs links to merged graph
    for node, equivalents in targets.same_as_dict.items():
        for eq in equivalents:
            graphs.data_graph.add((node, OWL.sameAs, eq))

    return graphs.data_graph, targets.same_as_dict, graphs.shapes_graph
