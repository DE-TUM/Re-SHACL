from .target_extraction import extract_targets_and_paths
from .closure_engine import run_closure_loop
from ..core.load import load_graph
from rdflib.namespace import OWL


def run_merging_pipeline(data_graph, shacl_graph=None, data_graph_format=None, shacl_graph_format=None):
    shapes, named_graphs, shape_graph = load_graph(
        data_graph, shacl_graph, data_graph_format, shacl_graph_format
    )
    vg = named_graphs[0]

    # Step 1: extract targets, paths, property shape nodes
    (
        focus_targets,
        class_targets,
        paths,
        same_nodes,
        shape_path_properties,
        target_nodes,
        property_shape_nodes
    ) = extract_targets_and_paths(shapes, vg)

    # Step 2: run merge closure loop
    run_closure_loop(
        vg,
        shape_graph.graph,
        shapes,
        focus_targets,
        class_targets,
        paths,
        same_nodes,
        shape_path_properties,
        target_nodes,
        property_shape_nodes
    )

    # Step 3: owl:sameAs link insertions
    for node, equivalents in same_nodes.items():
        for eq in equivalents:
            vg.add((node, OWL.sameAs, eq))

    return vg, same_nodes, shape_graph.graph
