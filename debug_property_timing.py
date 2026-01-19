"""
Check when schema:nn sameAs schema:name exists
"""
from rdflib import OWL, Namespace
from src.core.load import load_data_graph, load_shapes_graph
from src.my_types import GraphsBundle
from src.my_types.merge_inputs import extract_merge_inputs
from src.core.owl_semantics.domain_range import target_domain_range

SCHEMA = Namespace("http://schema.org/")

dg_path = "test_graphs/DG_1.ttl"
sg_path = "test_graphs/SG_1.ttl"

print("="*60)
print("CHECKING INITIAL DATA GRAPH")
print("="*60)

data_graph_loaded = load_data_graph(dg_path, 'turtle')

print(f"\nschema:nn sameAs schema:name exists: {(SCHEMA.nn, OWL.sameAs, SCHEMA.name) in data_graph_loaded}")
print(f"schema:name sameAs schema:Name exists: {(SCHEMA.name, OWL.sameAs, SCHEMA.Name) in data_graph_loaded}")

print("\n="*60)
print("AFTER LOADING AND EXTRACTING INPUTS")
print("="*60)

shapes_graph = load_shapes_graph(sg_path, 'turtle')
graphs = GraphsBundle(data_graph=data_graph_loaded, shapes_graph=shapes_graph)
inputs = extract_merge_inputs(graphs)

print(f"\nschema:nn sameAs schema:name exists: {(SCHEMA.nn, OWL.sameAs, SCHEMA.name) in graphs.data_graph}")
print(f"schema:name sameAs schema:Name exists: {(SCHEMA.name, OWL.sameAs, SCHEMA.Name) in graphs.data_graph}")

print(f"\nschema:nn in property_paths: {SCHEMA.nn in inputs.property_paths}")
print(f"schema:name in property_paths: {SCHEMA.name in inputs.property_paths}")

print("\n="*60)
print("AFTER DOMAIN/RANGE INFERENCE")
print("="*60)

target_domain_range(graphs.data_graph, inputs.discovered_focus_nodes, inputs.same_as_dict, inputs.target_classes)

print(f"\nschema:nn sameAs schema:name exists: {(SCHEMA.nn, OWL.sameAs, SCHEMA.name) in graphs.data_graph}")
print(f"schema:name sameAs schema:Name exists: {(SCHEMA.name, OWL.sameAs, SCHEMA.Name) in graphs.data_graph}")
