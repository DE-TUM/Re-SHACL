"""Quick check of discovered_focus_nodes count."""
from src.pipeline.run_pipeline import run_merging_pipeline
from src.my_types.merge_inputs import extract_merge_inputs
from src.my_types import GraphsBundle
from src.core.load import load_data_graph, load_shapes_graph
from src.pipeline.closure_engine import run_closure_loop
from rdflib import Namespace

# Run refactored with access to discovered_focus_nodes
data_graph_loaded = load_data_graph('source/Datasets/EnDe-Lite50.ttl', 'ttl')
shapes_graph = load_shapes_graph('source/ShapesGraphs/Shape_30.ttl', 'ttl')
graphs = GraphsBundle(data_graph=data_graph_loaded, shapes_graph=shapes_graph)
inputs = extract_merge_inputs(graphs)

print(f"Initial discovered_focus_nodes: {len(inputs.discovered_focus_nodes)}")
print(f"shape_path_properties: {len(inputs.shape_path_properties)}")

run_closure_loop(graphs, inputs)

print(f"Final discovered_focus_nodes: {len(inputs.discovered_focus_nodes)}")

# Add superproperty closure
from src.pipeline.closure_engine import _add_subproperty_closure
_add_subproperty_closure(data_graph_loaded, inputs.discovered_focus_nodes)

# Check coverage
DUL = Namespace('http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#')
DBP = Namespace('http://dbpedia.org/ontology/')

wiki_subjects = set(data_graph_loaded.subjects(DBP.wikiPageWikiLink, None))
assoc_subjects = set(data_graph_loaded.subjects(DUL.associatedWith, None))

print(f"\nSubjects with wikiPageWikiLink: {len(wiki_subjects)}")
print(f"Subjects with dul:associatedWith: {len(assoc_subjects)}")
print(f"Coverage: {len(assoc_subjects) / len(wiki_subjects) * 100:.1f}%")
print(f"\nwikiPageWikiLink subjects in discovered_focus_nodes: {len(wiki_subjects & inputs.discovered_focus_nodes)}")
print(f"wikiPageWikiLink subjects NOT in discovered_focus_nodes: {len(wiki_subjects - inputs.discovered_focus_nodes)}")
