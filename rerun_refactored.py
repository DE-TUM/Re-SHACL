"""
Re-run refactored implementation only to update outputs.
"""
from src.pipeline.run_pipeline import run_merging_pipeline

print("="*60)
print("RUNNING REFACTORED (test_graphs/DG_1.ttl)")
print("="*60)

dg_path = "test_graphs/DG_1.ttl"
sg_path = "test_graphs/SG_1.ttl"

g_refact, same_as_dict_refact, shapes_refact = run_merging_pipeline(
    dg_path,
    shacl_graph=sg_path,
    data_graph_format='turtle',
    shacl_graph_format='turtle'
)

print(f"\nRefactored Results:")
print(f"  Total triples: {len(g_refact)}")
print(f"  same_as_dict entries: {len(same_as_dict_refact)}")

# Save to output
import os
output_dir = "Outputs"
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "dg1_refactored.ttl")
g_refact.serialize(output_path, format="turtle")

print(f"\nSaved to: {output_path}")
print("="*60)
