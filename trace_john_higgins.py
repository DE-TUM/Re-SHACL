import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rdflib
from rdflib import Graph, RDF, OWL

# Load graphs
print("Loading graphs...")
g1 = Graph()  # refactored
g1.parse("src/fused_refactor_test.ttl", format="ttl")

g2 = Graph()  # original
g2.parse("src/fused_reshacl_test.ttl", format="ttl")

subject = rdflib.URIRef("http://dbpedia.org/resource/John_Higgins")

# Check the sameAs structure
print(f"=== {subject} ===\n")

print("In ORIGINAL (g2):")
sameas_obj_g2 = list(g2.objects(subject, OWL.sameAs))
sameas_subj_g2 = list(g2.subjects(OWL.sameAs, subject))
print(f"  subject owl:sameAs ?: {len(sameas_obj_g2)} entities")
if sameas_obj_g2[:3]:
    for e in sameas_obj_g2[:3]:
        print(f"    - {e}")
print(f"  ? owl:sameAs subject: {len(sameas_subj_g2)} entities")
if sameas_subj_g2[:3]:
    for e in sameas_subj_g2[:3]:
        print(f"    - {e}")

print("\nIn REFACTORED (g1):")
sameas_obj_g1 = list(g1.objects(subject, OWL.sameAs))
sameas_subj_g1 = list(g1.subjects(OWL.sameAs, subject))
print(f"  subject owl:sameAs ?: {len(sameas_obj_g1)} entities")
if sameas_obj_g1[:3]:
    for e in sameas_obj_g1[:3]:
        print(f"    - {e}")
print(f"  ? owl:sameAs subject: {len(sameas_subj_g1)} entities")
if sameas_subj_g1[:3]:
    for e in sameas_subj_g1[:3]:
        print(f"    - {e}")

# Now the crucial question: where did the types go?
# Check if there's a DIFFERENT representative that has the types
print("\n=== Searching for where the types went ===")

# Get one of the missing types
missing_type = rdflib.URIRef("http://dbpedia.org/class/yago/CausalAgent100007347")

# In original, who has this type?
entities_with_type_g2 = [s for s, p, o in g2.triples((None, RDF.type, missing_type))]
print(f"\nEntities with {missing_type} in ORIGINAL: {len(entities_with_type_g2)}")

# Check if any of John_Higgins' sameAs cluster has it in refactored
all_related_g1 = set(sameas_obj_g1) | set(sameas_subj_g1) | {subject}
print(f"\nJohn_Higgins related cluster in refactored: {len(all_related_g1)}")

for entity in all_related_g1:
    if (entity, RDF.type, missing_type) in g1:
        print(f"  ✓ {entity} has the type in refactored")
        
# Check if the type exists anywhere else in refactored
entities_with_type_g1 = [s for s, p, o in g1.triples((None, RDF.type, missing_type))]
print(f"\nTotal entities with {missing_type} in REFACTORED: {len(entities_with_type_g1)}")

# Check if John_Higgins was supposed to be a TARGET NODE
print("\n=== Target node analysis ===")
# Look at the data to see if John_Higgins is targeted by shapes

# Load original data graph (before merging)
print("Loading original data graph...")
orig_data = Graph()
orig_data.parse("source/Datasets/EnDe-Lite50.ttl", format="ttl")

# Check if John_Higgins exists in original
exists_in_orig = any(orig_data.triples((subject, None, None)))
print(f"John_Higgins exists in original data: {exists_in_orig}")

if exists_in_orig:
    types_in_orig_data = list(orig_data.objects(subject, RDF.type))
    print(f"Types in original data: {len(types_in_orig_data)}")
    print(f"Sample types:")
    for t in types_in_orig_data[:5]:
        print(f"  - {t}")
