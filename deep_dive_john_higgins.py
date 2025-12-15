import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rdflib
from rdflib import Graph, RDF, OWL

# Load both graphs
print("Loading graphs...")
g1 = Graph()  # refactored
g1.parse("src/fused_refactor_test.ttl", format="ttl")

g2 = Graph()  # original
g2.parse("src/fused_reshacl_test.ttl", format="ttl")

# Pick John_Higgins as test case
subject = rdflib.URIRef("http://dbpedia.org/resource/John_Higgins")
missing_type = rdflib.URIRef("http://dbpedia.org/class/yago/CausalAgent100007347")

print(f"Analyzing: {subject}")
print(f"Missing type: {missing_type}\n")

# Get all sameAs related entities in original
sameas_g2 = set(g2.objects(subject, OWL.sameAs)) | set(g2.subjects(OWL.sameAs, subject))
sameas_g2.add(subject)
print(f"Entities in sameAs cluster (original): {len(sameas_g2)}")

# Check which of these have the missing type in original
has_missing_type_g2 = [e for e in sameas_g2 if (e, RDF.type, missing_type) in g2]
print(f"Entities with missing_type in original: {len(has_missing_type_g2)}")
if has_missing_type_g2:
    print(f"  Examples: {has_missing_type_g2[:3]}")

# Check in refactored
sameas_g1 = set(g1.objects(subject, OWL.sameAs)) | set(g1.subjects(OWL.sameAs, subject))
sameas_g1.add(subject)
print(f"\nEntities in sameAs cluster (refactored): {len(sameas_g1)}")

has_missing_type_g1 = [e for e in sameas_g1 if (e, RDF.type, missing_type) in g1]
print(f"Entities with missing_type in refactored: {len(has_missing_type_g1)}")

# Check if subject itself has the type
print(f"\nDoes subject have missing_type in original? {(subject, RDF.type, missing_type) in g2}")
print(f"Does subject have missing_type in refactored? {(subject, RDF.type, missing_type) in g1}")

# Get all types of subject in both versions
types_g1 = set(g1.objects(subject, RDF.type))
types_g2 = set(g2.objects(subject, RDF.type))

print(f"\nSubject types in original: {len(types_g2)}")
print(f"Subject types in refactored: {len(types_g1)}")

# Get types from all sameAs entities in original
all_types_from_sameas_g2 = set()
for entity in sameas_g2:
    all_types_from_sameas_g2.update(g2.objects(entity, RDF.type))

print(f"\nAll types from sameAs cluster in original: {len(all_types_from_sameas_g2)}")

# Compare
missing_in_refactored = types_g2 - types_g1
extra_in_refactored = types_g1 - types_g2

print(f"\nTypes in original but not refactored: {len(missing_in_refactored)}")
print(f"Types in refactored but not original: {len(extra_in_refactored)}")

# Check if missing_type was on the subject directly in original
print(f"\n=== KEY QUESTION ===")
print(f"Was missing_type directly on subject in original? {missing_type in types_g2}")
print(f"If yes, why wasn't it transferred?")

# Check if subject's triples were properly copied
print(f"\n=== Checking triple transfer ===")
predicate_objects_g2 = list(g2.predicate_objects(subject))[:10]
print(f"Sample predicate-objects for subject in original:")
for p, o in predicate_objects_g2[:5]:
    print(f"  {p} -> {o}")
    # Check if this exists in refactored
    exists = (subject, p, o) in g1
    print(f"    Exists in refactored: {exists}")
