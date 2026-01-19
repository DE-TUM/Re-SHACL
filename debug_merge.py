import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rdflib import Graph, OWL, RDF
from src.pipeline.run_pipeline import run_merging_pipeline
from src.core.load import load_data_graph, load_shapes_graph
from src.my_types import GraphsBundle
from src.my_types.merge_inputs import extract_merge_inputs

if __name__ == "__main__":
    dg_path = "test_graphs/DG_1.ttl"
    sg_path = "test_graphs/SG_1.ttl"
    
    print("Loading graphs...")
    data_graph_loaded = load_data_graph(dg_path, 'turtle')
    shapes_graph = load_shapes_graph(sg_path, 'turtle')
    
    print("\n" + "="*80)
    print("INITIAL DATA GRAPH")
    print("="*80)
    print(f"Total triples: {len(data_graph_loaded)}")
    
    print("\n--- All owl:sameAs triples ---")
    for s, p, o in data_graph_loaded.triples((None, OWL.sameAs, None)):
        print(f"  {s} owl:sameAs {o}")
    
    print("\n--- Instances of schema:Student ---")
    from rdflib import Namespace
    SCHEMA = Namespace("http://schema.org/")
    for s in data_graph_loaded.subjects(RDF.type, SCHEMA.Student):
        print(f"  {s}")
    
    graphs = GraphsBundle(data_graph=data_graph_loaded, shapes_graph=shapes_graph)
    inputs = extract_merge_inputs(graphs)
    
    print("\n" + "="*80)
    print("EXTRACTED MERGE INPUTS (before domain/range)")
    print("="*80)
    print(f"Target classes: {len(inputs.target_classes)}")
    for cls in inputs.target_classes:
        print(f"  {cls}")
    
    print(f"\nDiscovered focus nodes: {len(inputs.discovered_focus_nodes)}")
    for node in inputs.discovered_focus_nodes:
        print(f"  {node}")
    
    # Now run domain/range inference
    from src.core.owl_semantics.domain_range import target_domain_range
    target_domain_range(data_graph_loaded, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)
    
    print("\n" + "="*80)
    print("AFTER DOMAIN/RANGE INFERENCE")
    print("="*80)
    print(f"Discovered focus nodes: {len(inputs.discovered_focus_nodes)}")
    for node in inputs.discovered_focus_nodes:
        print(f"  {node}")
    
    print(f"\nProperty paths: {len(inputs.property_paths)}")
    for prop in inputs.property_paths:
        print(f"  {prop}")
    
    print(f"\nSame-as dict (initial): {len(inputs.same_as_dict)}")
    for key, vals in inputs.same_as_dict.items():
        print(f"  {key} -> {vals}")
    
    # Check which nodes are in sameAs relationships
    print("\n--- Nodes with owl:sameAs relationships ---")
    all_sameas_nodes = {s for s, _, _ in data_graph_loaded.triples((None, OWL.sameAs, None))} | \
                       {o for _, _, o in data_graph_loaded.triples((None, OWL.sameAs, None))}
    for node in all_sameas_nodes:
        in_focus = "YES" if node in inputs.discovered_focus_nodes else "NO"
        print(f"  {node} - in discovered_focus_nodes: {in_focus}")
        for obj in data_graph_loaded.objects(node, OWL.sameAs):
            print(f"    -> sameAs: {obj}")
        for subj in data_graph_loaded.subjects(OWL.sameAs, node):
            print(f"    <- sameAs: {subj}")
