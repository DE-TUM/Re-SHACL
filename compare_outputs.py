#!/usr/bin/env python
"""Compare the two output files without Unicode issues."""
from rdflib import Graph
from rdflib.compare import to_isomorphic, graph_diff
from collections import Counter

print("Loading graphs...")
g1 = Graph()
g1.parse("fused_reshacl_test.ttl", format="turtle")
print(f"Original: {len(g1)} triples")

g2 = Graph()
g2.parse("fused_refactor_test.ttl", format="turtle")
print(f"Refactored: {len(g2)} triples")

print("\nComparing...")
iso1 = to_isomorphic(g1)
iso2 = to_isomorphic(g2)

if iso1 == iso2:
    print("✓ GRAPHS ARE ISOMORPHIC")
else:
    print("✗ GRAPHS DIFFER")
    in_both, in_first, in_second = graph_diff(iso1, iso2)
    print(f"\nOnly in original:   {len(in_first)} triples")
    print(f"Only in refactored: {len(in_second)} triples")
    
    # Analyze predicates
    print("\n--- Top predicates ONLY in ORIGINAL ---")
    preds1 = Counter(str(t[1]) for t in in_first)
    for pred, count in preds1.most_common(10):
        print(f"  {count:5d}x  {pred}")
    
    print("\n--- Top predicates ONLY in REFACTORED ---")
    preds2 = Counter(str(t[1]) for t in in_second)
    for pred, count in preds2.most_common(10):
        print(f"  {count:5d}x  {pred}")
    
    # Write to files
    print("\nWriting differences to files...")
    with open("diff_only_original.txt", "w", encoding="utf-8") as f:
        for triple in sorted(in_first):
            f.write(f"{triple}\n")
    
    with open("diff_only_refactored.txt", "w", encoding="utf-8") as f:
        for triple in sorted(in_second):
            f.write(f"{triple}\n")
    
    print("  - diff_only_original.txt")
    print("  - diff_only_refactored.txt")
