import rdflib
from rdflib import Graph, RDF
from collections import Counter

# Load both graphs
g1 = Graph()
g1.parse("C:/Users/zenon/eclipse-workspace/Re-SHACL/src/fused_refactor_test.ttl", format="ttl")

g2 = Graph()
g2.parse("C:/Users/zenon/eclipse-workspace/Re-SHACL/src/fused_reshacl_test.ttl", format="ttl")

# Compare
# if g1.isomorphic(g2):
#     print("✅ Graphs are equivalent (isomorphic).")
# else:
#     print("❌ Graphs are not equivalent.")


print("Triples in g1 but not in g2:")
diff_len_g1 = len(g1 - g2)
print(diff_len_g1)
diff_len_g2 = len(g2 - g1)
# for triple in g1 - g2:
#     print(triple)
#
print("\nTriples in g2 but not in g1:")
print(diff_len_g2)
# for triple in g2 - g1:
#     print(triple)

# Count how many of the differences involve blank nodes
bnode_diff_1 = sum(1 for s, p, o in g1 - g2 if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode))
bnode_diff_2 = sum(1 for s, p, o in g2 - g1 if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode))

print("Triples with blank nodes in g1 - g2:", bnode_diff_1)
print("Triples with blank nodes in g2 - g1:", bnode_diff_2)


print("g1 total triples:", len(g1))
print("g2 total triples:", len(g2))

#
# diff_g1 = [t for t in g1 - g2 if not isinstance(t[0], rdflib.BNode) and not isinstance(t[2], rdflib.BNode)]
# diff_g2 = [t for t in g2 - g1 if not isinstance(t[0], rdflib.BNode) and not isinstance(t[2], rdflib.BNode)]
#
# for t in diff_g2:
#     if t[0] != t[2]:
#         print(t)
    # if t[1] == RDF.type:
    #     print(t)
    # print(t)


diff_g2 = list(g2 - g1)

pred_counts = Counter()
type_statements = []

for s, p, o in diff_g2:
    pred_counts[p] += 1
    if p == RDF.type:
        type_statements.append((s, o))

print("Predicate frequency in g2 - g1:")
for pred, count in pred_counts.most_common():
    print(f"{pred}: {count}")

print(f"\nTotal rdf:type statements missing: {len(type_statements)}")

# print("Extra types in g2 but not g1:")
# for s, p, o in (g2 - g1):
#     if p == RDF.type:
#         print((s, o))



