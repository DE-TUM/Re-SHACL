"""Compare found_node_targets between original and refactored."""
from ReSHACL.re_shacl import merged_graph as original_merged_graph
from src.pipeline.run_pipeline import run_merging_pipeline
from rdflib import Namespace

print("Running original...")
# Patch to capture found_node_targets
import ReSHACL.re_shacl as orig_module

original_found_nodes = None

# Monkey patch to capture found_node_targets
original_merged = orig_module.merged_graph

def patched_merged(*args, **kwargs):
    global original_found_nodes
    result = original_merged(*args, **kwargs)
    # The found_node_targets is local, but we can infer it from the graph
    # by checking which nodes had superproperty expansion
    return result

g_orig, same_orig, sg_orig = original_merged_graph(
    'source/Datasets/EnDe-Lite50.ttl',
    'source/ShapesGraphs/Shape_30.ttl',
    data_graph_format='ttl',
    shacl_graph_format='ttl'
)

print("Running refactored...")
from src.my_types.merge_inputs import extract_merge_inputs
from src.my_types import GraphsBundle
from src.core.load import load_data_graph, load_shapes_graph
from rdflib import Graph

# Run refactored with access to discovered_focus_nodes
data_graph_loaded = load_data_graph('source/Datasets/EnDe-Lite50.ttl', 'ttl')
shapes_graph = load_shapes_graph('source/ShapesGraphs/Shape_30.ttl', 'ttl')
graphs = GraphsBundle(data_graph=data_graph_loaded, shapes_graph=shapes_graph)
inputs = extract_merge_inputs(graphs)

print(f"\nInitial discovered_focus_nodes: {len(inputs.discovered_focus_nodes)}")
print(f"Initial target_classes: {len(inputs.target_classes)}")
print(f"Initial property_paths: {len(inputs.property_paths)}")
print(f"shape_path_properties: {len(inputs.shape_path_properties)}")

from src.pipeline.closure_engine import run_closure_loop
run_closure_loop(graphs, inputs)

print(f"\nFinal discovered_focus_nodes: {len(inputs.discovered_focus_nodes)}")

# Now compare subjects that have dul:associatedWith
DUL = Namespace('http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#')
DBP = Namespace('http://dbpedia.org/ontology/')

orig_assoc_subjects = set(g_orig.subjects(DUL.associatedWith, None))
refact_assoc_subjects = set(data_graph_loaded.subjects(DUL.associatedWith, None))

orig_wiki_subjects = set(g_orig.subjects(DBP.wikiPageWikiLink, None))
refact_wiki_subjects = set(data_graph_loaded.subjects(DBP.wikiPageWikiLink, None))

print(f"\nOriginal:")
print(f"  Subjects with wikiPageWikiLink: {len(orig_wiki_subjects)}")
print(f"  Subjects with dul:associatedWith: {len(orig_assoc_subjects)}")
print(f"  Coverage: {len(orig_assoc_subjects) / len(orig_wiki_subjects) * 100:.1f}%")

print(f"\nRefactored:")
print(f"  Subjects with wikiPageWikiLink: {len(refact_wiki_subjects)}")
print(f"  Subjects with dul:associatedWith: {len(refact_assoc_subjects)}")
print(f"  Coverage: {len(refact_assoc_subjects) / len(refact_wiki_subjects) * 100:.1f}%")

print(f"\nMissing dul:associatedWith: {len(orig_assoc_subjects - refact_assoc_subjects)} subjects")
print(f"Extra dul:associatedWith: {len(refact_assoc_subjects - orig_assoc_subjects)} subjects")

# Check if missing subjects are in discovered_focus_nodes
missing_assoc = orig_assoc_subjects - refact_assoc_subjects
in_focus = sum(1 for s in missing_assoc if s in inputs.discovered_focus_nodes)
print(f"\nOf the {len(missing_assoc)} missing subjects, {in_focus} ARE in discovered_focus_nodes")
print(f"This means {len(missing_assoc) - in_focus} are NOT in discovered_focus_nodes")
