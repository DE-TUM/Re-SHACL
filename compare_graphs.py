import sys
import os

# Add the root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rdflib
from rdflib import Graph, RDF
from collections import Counter

# Load both graphs
g1 = Graph()
g1.parse("src/fused_refactor_test.ttl", format="ttl")

g2 = Graph()
g2.parse("src/fused_reshacl_test.ttl", format="ttl")

print("Triples in g1 but not in g2:")
diff_len_g1 = len(g1 - g2)
print(diff_len_g1)

diff_len_g2 = len(g2 - g1)
print("\nTriples in g2 but not in g1:")
print(diff_len_g2)

# Count how many of the differences involve blank nodes
bnode_diff_1 = sum(1 for s, p, o in g1 - g2 if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode))
bnode_diff_2 = sum(1 for s, p, o in g2 - g1 if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode))

print("\nTriples with blank nodes in g1 - g2:", bnode_diff_1)
print("Triples with blank nodes in g2 - g1:", bnode_diff_2)

print("\ng1 total triples:", len(g1))
print("g2 total triples:", len(g2))

diff_g2 = list(g2 - g1)

pred_counts = Counter()
type_statements = []

for s, p, o in diff_g2:
    pred_counts[p] += 1
    if p == RDF.type:
        type_statements.append((s, o))

print("\nPredicate frequency in g2 - g1 (top 10):")
for pred, count in pred_counts.most_common(10):
    print(f"{pred}: {count}")

print(f"\nTotal rdf:type statements missing: {len(type_statements)}")

# Show some sample missing type statements
print("\nSample missing rdf:type statements (first 10):")
for i, (s, o) in enumerate(type_statements[:10]):
    print(f"  {s} rdf:type {o}")
