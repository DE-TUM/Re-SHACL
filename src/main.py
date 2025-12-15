import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ReSHACL.re_shacl import merged_graph
from src.pipeline.run_pipeline import run_merging_pipeline

if __name__ == "__main__":
    # Get the absolute paths relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    g = os.path.join(project_root, "source", "Datasets", "EnDe-Lite50.ttl")
    sg = os.path.join(project_root, "source", "ShapesGraphs", "Shape_30.ttl")
    print("="*60)
    print("Running ORIGINAL Re-SHACL...")
    print("="*60)
    fg1, sd1, ss1 = merged_graph(g, shacl_graph=sg, data_graph_format='turtle', shacl_graph_format='turtle')
    print("Original Re-SHACL done.")
    fg1.serialize("fused_reshacl_test.ttl", format="turtle")
    
    print("\n" + "="*60)
    print("Running REFACTORED Re-SHACL...")
    print("="*60)
    fg2, sd2, ss2 = run_merging_pipeline(g, shacl_graph=sg, data_graph_format='turtle', shacl_graph_format='turtle')
    print("Refactored Re-SHACL done.")
    fg2.serialize("fused_refactor_test.ttl", format="turtle")
    
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    # Compare graph sizes
    print(f"\nGraph sizes:")
    print(f"  Original:    {len(fg1)} triples")
    print(f"  Refactored:  {len(fg2)} triples")
    print(f"  Difference:  {len(fg2) - len(fg1)}")
    
    # Compare same_as dictionaries
    print(f"\nSame-as dictionaries:")
    print(f"  Original:    {len(sd1)} entries")
    print(f"  Refactored:  {len(sd2)} entries")
    
    # Compare shapes graphs
    print(f"\nShapes graphs:")
    print(f"  Original:    {len(ss1)} triples")
    print(f"  Refactored:  {len(ss2)} triples")
    
    # Check if graphs are isomorphic
    from rdflib.compare import to_isomorphic, graph_diff
    iso1 = to_isomorphic(fg1)
    iso2 = to_isomorphic(fg2)
    
    if iso1 == iso2:
        print("\n[SUCCESS] Graphs are ISOMORPHIC (semantically identical)")
    else:
        print("\n[DIFFERENCE] Graphs are NOT isomorphic")
        in_both, in_first, in_second = graph_diff(iso1, iso2)
        print(f"  Triples only in original:   {len(in_first)}")
        print(f"  Triples only in refactored: {len(in_second)}")
        
        # Write differences to files for inspection
        print("\n  Writing differences to files...")
        with open("diff_only_in_original.txt", "w", encoding="utf-8") as f:
            for triple in in_first:
                f.write(f"{triple}\n")
        print(f"  - diff_only_in_original.txt ({len(in_first)} triples)")
        
        with open("diff_only_in_refactored.txt", "w", encoding="utf-8") as f:
            for triple in in_second:
                f.write(f"{triple}\n")
        print(f"  - diff_only_in_refactored.txt ({len(in_second)} triples)")
        
        # Analyze difference patterns
        print("\n  Analyzing patterns...")
        from collections import Counter
        
        # Count predicates in differences
        orig_preds = Counter(str(t[1]) for t in in_first)
        ref_preds = Counter(str(t[1]) for t in in_second)
        
        print(f"\n  Top predicates only in ORIGINAL:")
        for pred, count in orig_preds.most_common(5):
            print(f"    {count:4d}x  {pred}")
        
        print(f"\n  Top predicates only in REFACTORED:")
        for pred, count in ref_preds.most_common(5):
            print(f"    {count:4d}x  {pred}")
    
    print("\n" + "="*60)
