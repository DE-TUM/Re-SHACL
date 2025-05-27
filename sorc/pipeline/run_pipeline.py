from .target_extraction import extract_targets_and_paths
from .closure_engine import run_closure_loop
from ..core.load import load_graph
from rdflib.namespace import OWL


def run_merging_pipeline(data_graph, shacl_graph=None, data_graph_format=None, shacl_graph_format=None):
    shapes, named_graphs, shape_graph = load_graph(data_graph, shacl_graph, data_graph_format, shacl_graph_format)
    vg = named_graphs[0]

    # Step 1: extract targets and paths
    focus_targets, class_targets, paths, same_nodes, shape_linked_targets, target_nodes = extract_targets_and_paths(shapes, vg)

    # Step 2: run merge closure loop
    target_properties = set()
    for s in shapes:
        target_properties.update(s.property_shapes())

    run_closure_loop(vg, shape_graph.graph, shapes, focus_targets, class_targets, paths, same_nodes, shape_linked_targets, target_nodes, target_properties)

    # Step 3: owl:sameAs link insertions
    for k in same_nodes:
        for se in same_nodes[k]:
            vg.add((k, OWL.sameAs, se))

    return vg, same_nodes, shape_graph.graph
