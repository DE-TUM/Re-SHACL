"""Quick comparison without detailed printing"""
from ReSHACL.re_shacl import merged_graph
from src.pipeline.run_pipeline import run_merging_pipeline
from rdflib import compare

print("Running original...")
g_orig, sd_orig, _ = merged_graph('source/Datasets/EnDe-Lite50.ttl', 'source/ShapesGraphs/Shape_30.ttl')
print(f"Original: {len(g_orig)} triples, {len(sd_orig)} same_as_dict entries")

print("\nRunning refactored...")
g_ref, sd_ref, _ = run_merging_pipeline('source/Datasets/EnDe-Lite50.ttl', 'source/ShapesGraphs/Shape_30.ttl')
print(f"Refactored: {len(g_ref)} triples, {len(sd_ref)} same_as_dict entries")

print(f"\nDifference: {len(g_ref) - len(g_orig)} triples")
print(f"same_as_dict difference: {len(sd_ref) - len(sd_orig)}")

print("\nChecking isomorphism...")
is_iso = compare.to_isomorphic(g_orig) == compare.to_isomorphic(g_ref)
print(f"Isomorphic: {is_iso}")

if not is_iso:
    in_both, in_orig, in_ref = compare.graph_diff(g_orig, g_ref)
    print(f"\nTriples in both: {len(in_both)}")
    print(f"Only in original: {len(in_orig)}")
    print(f"Only in refactored: {len(in_ref)}")
    
    # Count by predicate
    from collections import Counter
    orig_preds = Counter(p for _, p, _ in in_orig)
    ref_preds = Counter(p for _, p, _ in in_ref)
    
    print("\nTop 10 missing predicates:")
    for pred, count in orig_preds.most_common(10):
        print(f"  {pred.n3()}: {count}")
    
    print("\nTop 10 extra predicates:")
    for pred, count in ref_preds.most_common(10):
        print(f"  {pred.n3()}: {count}")
