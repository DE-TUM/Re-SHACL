import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ReSHACL.re_shacl import merged_graph
from src.pipeline.run_pipeline import run_merging_pipeline

if __name__ == "__main__":
    # Test with DG_1.ttl and SG_1.ttl
    dg_path = "test_graphs/DG_1.ttl"
    sg_path = "test_graphs/SG_1.ttl"
    
    print("="*80)
    print(f"Testing with {dg_path} and {sg_path}")
    print("="*80)
    
    print("\n" + "="*80)
    print("Running ORIGINAL Re-SHACL...")
    print("="*80)
    fg1, sd1, ss1 = merged_graph(dg_path, shacl_graph=sg_path, 
                                  data_graph_format='turtle', shacl_graph_format='turtle')
    print("Original Re-SHACL done.")
    
    print("\n" + "="*80)
    print("Running REFACTORED Re-SHACL...")
    print("="*80)
    fg2, sd2, ss2 = run_merging_pipeline(dg_path, shacl_graph=sg_path, 
                                          data_graph_format='turtle', shacl_graph_format='turtle')
    print("Refactored Re-SHACL done.")
    
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    
    # Compare graph sizes
    print(f"\nGraph sizes:")
    print(f"  Original:    {len(fg1)} triples")
    print(f"  Refactored:  {len(fg2)} triples")
    print(f"  Difference:  {len(fg2) - len(fg1)}")
    
    # Compare same_as dictionaries
    print(f"\nSame-as dictionaries:")
    print(f"  Original:    {len(sd1)} entries")
    print(f"  Refactored:  {len(sd2)} entries")
    
    # Print same-as details
    print(f"\nOriginal same-as dict:")
    for key, values in sd1.items():
        print(f"  {key} -> {values}")
    
    print(f"\nRefactored same-as dict:")
    for key, values in sd2.items():
        print(f"  {key} -> {values}")
    
    # Compare shapes graphs
    print(f"\nShapes graphs:")
    print(f"  Original:    {len(ss1)} triples")
    print(f"  Refactored:  {len(ss2)} triples")
    
    # Save results
    output_dir = "Outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    fg1_output = os.path.join(output_dir, "dg1_original.ttl")
    fg2_output = os.path.join(output_dir, "dg1_refactored.ttl")
    
    fg1.serialize(fg1_output, format="turtle")
    fg2.serialize(fg2_output, format="turtle")
    
    print(f"\n" + "="*80)
    print(f"Output files saved:")
    print(f"  Original:    {fg1_output}")
    print(f"  Refactored:  {fg2_output}")
    print("="*80)
    
    # Check if graphs are isomorphic
    from rdflib.compare import to_isomorphic, graph_diff
    iso1 = to_isomorphic(fg1)
    iso2 = to_isomorphic(fg2)
    
    if iso1 == iso2:
        print("\n✓ Graphs are ISOMORPHIC (semantically equivalent)")
    else:
        print("\n✗ Graphs are NOT isomorphic")
        print("\nComputing differences...")
        in_both, in_first, in_second = graph_diff(fg1, fg2)
        print(f"\n  Triples in both:        {len(in_both)}")
        print(f"  Only in original:       {len(in_first)}")
        print(f"  Only in refactored:     {len(in_second)}")
        
        if len(in_first) > 0:
            print("\n  Sample triples only in original (first 10):")
            for i, triple in enumerate(in_first):
                if i >= 10:
                    break
                print(f"    {triple}")
        
        if len(in_second) > 0:
            print("\n  Sample triples only in refactored (first 10):")
            for i, triple in enumerate(in_second):
                if i >= 10:
                    break
                print(f"    {triple}")
