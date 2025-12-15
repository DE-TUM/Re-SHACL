"""
Save refactored output and compare with original if cached exists.
This avoids re-running the slow original code.
"""
import pickle
from pathlib import Path
from src.pipeline.run_pipeline import run_merging_pipeline
import rdflib
from rdflib import OWL, RDF, RDFS
from collections import Counter

CACHE_DIR = Path("Outputs")
CACHE_DIR.mkdir(exist_ok=True)
REFACTORED_CACHE = CACHE_DIR / "refactored_output.pkl"
ORIGINAL_CACHE = CACHE_DIR / "original_output.pkl"

print("=" * 60)
print("REFACTORED OUTPUT ANALYSIS")
print("=" * 60)

print("\nRunning refactored code...")
g_refactored, same_dict, sg = run_merging_pipeline(
    'source/Datasets/EnDe-Lite50.ttl', 
    'source/ShapesGraphs/Shape_30.ttl'
)

# Save refactored output
print(f"Saving refactored output to {REFACTORED_CACHE}...")
with open(REFACTORED_CACHE, 'wb') as f:
    pickle.dump((g_refactored, same_dict), f)

# Analyze refactored
print(f"\n{'Refactored Statistics:'}")
print(f"  Total triples: {len(g_refactored)}")
sameas_count = len(list(g_refactored.triples((None, OWL.sameAs, None))))
print(f"  owl:sameAs triples: {sameas_count}")
print(f"  same_as_dict entries: {len(same_dict)}")
print(f"  Total equivalents: {sum(len(v) for v in same_dict.values())}")

# Predicate distribution
predicates = Counter(p for _, p, _ in g_refactored)
print(f"\n  Top predicates:")
for pred, count in predicates.most_common(15):
    pred_str = str(pred).split('/')[-1].split('#')[-1]
    print(f"    {pred_str}: {count}")

# Type distribution  
type_objs = Counter(o for _, p, o in g_refactored if p == RDF.type)
print(f"\n  Top types ({len(type_objs)} unique):")
for typ, count in type_objs.most_common(10):
    typ_str = str(typ).split('/')[-1].split('#')[-1]
    print(f"    {typ_str}: {count}")

# Check if original cached exists
if ORIGINAL_CACHE.exists():
    print(f"\n{'=' * 60}")
    print("COMPARING WITH CACHED ORIGINAL")
    print("=" * 60)
    
    with open(ORIGINAL_CACHE, 'rb') as f:
        g_original, original_same_dict = pickle.load(f)
    
    print(f"\nOriginal statistics:")
    print(f"  Total triples: {len(g_original)}")
    orig_sameas = len(list(g_original.triples((None, OWL.sameAs, None))))
    print(f"  owl:sameAs triples: {orig_sameas}")
    
    # Compare
    print(f"\nDifference Analysis:")
    print(f"  Triple count difference: {len(g_refactored) - len(g_original)}")
    print(f"  owl:sameAs difference: {sameas_count - orig_sameas}")
    
    # Graph diff
    print(f"\nComputing graph differences...")
    iso1 = rdflib.compare.to_isomorphic(g_refactored)
    iso2 = rdflib.compare.to_isomorphic(g_original)
    
    if iso1 == iso2:
        print("✓ GRAPHS ARE ISOMORPHIC - Semantically equivalent!")
    else:
        in_both, in_first, in_second = rdflib.compare.graph_diff(iso1, iso2)
        print(f"✗ Graphs differ:")
        print(f"    Triples only in refactored: {len(in_first)}")
        print(f"    Triples only in original: {len(in_second)}")
        
        # Analyze differences by predicate
        if len(in_first) > 0:
            missing_preds = Counter(p for _, p, _ in in_first)
            print(f"\n  Extra in refactored (by predicate):")
            for pred, count in missing_preds.most_common(10):
                pred_str = str(pred).split('/')[-1].split('#')[-1]
                print(f"    {pred_str}: {count}")
        
        if len(in_second) > 0:
            extra_preds = Counter(p for _, p, _ in in_second)
            print(f"\n  Missing from refactored (by predicate):")
            for pred, count in extra_preds.most_common(10):
                pred_str = str(pred).split('/')[-1].split('#')[-1]
                print(f"    {pred_str}: {count}")
else:
    print(f"\n{'=' * 60}")
    print(f"No cached original found at {ORIGINAL_CACHE}")
    print("To compare, run original and save with:")
    print("  from ReSHACL.re_shacl_rdfs_withoutM import main")
    print("  g_orig, sd_orig = main(...)")
    print(f"  import pickle; pickle.dump((g_orig, sd_orig), open('{ORIGINAL_CACHE}', 'wb'))")
    print("=" * 60)
