"""Quick comparison of refactored output only (no original - too slow)"""
from src.pipeline.run_pipeline import run_merging_pipeline
import rdflib
from rdflib import OWL, RDF, RDFS

print("Running refactored...")
g, same_dict, sg = run_merging_pipeline('source/Datasets/EnDe-Lite50.ttl', 'source/ShapesGraphs/Shape_30.ttl')

print(f"\nRefactored Results:")
print(f"  Total triples: {len(g)}")
print(f"  owl:sameAs triples: {len(list(g.triples((None, OWL.sameAs, None))))}")
print(f"  same_as_dict entries: {len(same_dict)}")
print(f"  Total equivalents tracked: {sum(len(v) for v in same_dict.values())}")

# Count by predicate
from collections import Counter
predicates = Counter(p for _, p, _ in g)
print(f"\nTop 10 predicates:")
for pred, count in predicates.most_common(10):
    print(f"  {pred}: {count}")

# Check for any orphaned sameAs
all_sameas = set()
for s, _, o in g.triples((None, OWL.sameAs, None)):
    all_sameas.add(s)
    all_sameas.add(o)

print(f"\nNodes involved in owl:sameAs: {len(all_sameas)}")
print(f"Nodes in same_as_dict: {len(same_dict)}")

# Check for reflexive or symmetric issues
reflexive = len(list(g.triples((None, OWL.sameAs, None))))
print(f"\nTotal owl:sameAs triples in graph: {reflexive}")

# Verify all sameAs are properly directed
for s, _, o in g.triples((None, OWL.sameAs, None)):
    if (o, OWL.sameAs, s) in g:
        print(f"WARNING: Bidirectional sameAs found: {s} <-> {o}")
        break
else:
    print("All owl:sameAs edges are unidirectional ✓")
