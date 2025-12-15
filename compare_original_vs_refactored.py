"""
Compare original re_shacl.py against refactored implementation.
"""
from ReSHACL.re_shacl import merged_graph
from src.pipeline.run_pipeline import run_merging_pipeline
import rdflib
from rdflib import compare

print("="*60)
print("RUNNING ORIGINAL (re_shacl.py)")
print("="*60)
g_orig, same_as_dict_orig, shapes_orig = merged_graph(
    'source/Datasets/EnDe-Lite50.ttl',
    'source/ShapesGraphs/Shape_30.ttl'
)
print(f"\nOriginal Results:")
print(f"  Total triples: {len(g_orig)}")
sameAs_orig = list(g_orig.triples((None, rdflib.OWL.sameAs, None)))
print(f"  owl:sameAs triples: {len(sameAs_orig)}")
print(f"  same_as_dict entries: {len(same_as_dict_orig)}")

print("\n" + "="*60)
print("RUNNING REFACTORED")
print("="*60)
g_refact, same_as_dict_refact, shapes_refact = run_merging_pipeline(
    'source/Datasets/EnDe-Lite50.ttl',
    'source/ShapesGraphs/Shape_30.ttl'
)
print(f"\nRefactored Results:")
print(f"  Total triples: {len(g_refact)}")
sameAs_refact = list(g_refact.triples((None, rdflib.OWL.sameAs, None)))
print(f"  owl:sameAs triples: {len(sameAs_refact)}")
print(f"  same_as_dict entries: {len(same_as_dict_refact)}")

print("\n" + "="*60)
print("COMPARISON")
print("="*60)
print(f"Triple count difference: {len(g_refact) - len(g_orig)}")
print(f"owl:sameAs difference: {len(sameAs_refact) - len(sameAs_orig)}")
print(f"same_as_dict difference: {len(same_as_dict_refact) - len(same_as_dict_orig)}")

print("\nChecking graph isomorphism...")
iso_orig = compare.to_isomorphic(g_orig)
iso_refact = compare.to_isomorphic(g_refact)
is_isomorphic = iso_orig == iso_refact

print(f"Graphs are isomorphic: {is_isomorphic}")

if not is_isomorphic:
    print("\n" + "="*60)
    print("ANALYZING DIFFERENCES")
    print("="*60)
    
    in_both, in_orig, in_refact = compare.graph_diff(g_orig, g_refact)
    
    print(f"\nTriples in both: {len(in_both)}")
    print(f"Triples only in original: {len(in_orig)}")
    print(f"Triples only in refactored: {len(in_refact)}")
    
    if len(in_orig) > 0:
        print(f"\nMissing from refactored (first 20):")
        pred_count_orig = {}
        for s, p, o in list(in_orig)[:20]:
            print(f"  {s} {p} {o}")
            pred_count_orig[p] = pred_count_orig.get(p, 0) + 1
        
        if len(in_orig) > 20:
            print("\nPredicate distribution in missing triples:")
            for pred, count in sorted(pred_count_orig.items(), key=lambda x: -x[1])[:10]:
                print(f"  {pred}: {count}")
    
    if len(in_refact) > 0:
        print(f"\nExtra in refactored (first 20):")
        pred_count_refact = {}
        for s, p, o in list(in_refact)[:20]:
            print(f"  {s} {p} {o}")
            pred_count_refact[p] = pred_count_refact.get(p, 0) + 1
        
        if len(in_refact) > 20:
            print("\nPredicate distribution in extra triples:")
            for pred, count in sorted(pred_count_refact.items(), key=lambda x: -x[1])[:10]:
                print(f"  {pred}: {count}")

print("\n" + "="*60)
print("DONE")
print("="*60)
