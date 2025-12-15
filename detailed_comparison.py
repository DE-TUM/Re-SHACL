import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rdflib
from rdflib import Graph, RDF, RDFS, OWL
from collections import defaultdict

# Load both graphs
print("Loading graphs...")
g1 = Graph()  # refactored
g1.parse("src/fused_refactor_test.ttl", format="ttl")

g2 = Graph()  # original
g2.parse("src/fused_reshacl_test.ttl", format="ttl")

print(f"Refactored (g1): {len(g1)} triples")
print(f"Original (g2): {len(g2)} triples")
print()

# Analyze missing rdf:type statements
missing_types = [(s, o) for s, p, o in (g2 - g1) if p == RDF.type]
print(f"Missing {len(missing_types)} rdf:type statements in refactored version")

# Check if these subjects exist in both graphs
subjects_missing_types = set(s for s, _ in missing_types)
print(f"Number of unique subjects missing types: {len(subjects_missing_types)}")

# Check if subjects exist in refactored graph
subjects_in_refactor = set()
subjects_not_in_refactor = set()
for subj in subjects_missing_types:
    if any(g1.triples((subj, None, None))):
        subjects_in_refactor.add(subj)
    else:
        subjects_not_in_refactor.add(subj)

print(f"Subjects that exist in refactored: {len(subjects_in_refactor)}")
print(f"Subjects that don't exist in refactored: {len(subjects_not_in_refactor)}")
print()

# Analyze what types are missing
print("Missing type classes (top 20):")
missing_type_classes = defaultdict(int)
for _, cls in missing_types:
    missing_type_classes[cls] += 1

for cls, count in sorted(missing_type_classes.items(), key=lambda x: -x[1])[:20]:
    print(f"  {count:4d} x {cls}")
print()

# Check if missing types might be due to subclass inference
print("Checking if missing types are related to subclass inference...")
sample_count = 0
for subj, missing_cls in missing_types[:20]:
    # Get all types the subject has in refactored version
    types_in_refactor = set(g1.objects(subj, RDF.type))
    
    if types_in_refactor:
        # Check if any type in refactor is a subclass of missing_cls
        is_subclass_related = any(
            (t, RDFS.subClassOf, missing_cls) in g1 or
            (t, RDFS.subClassOf, missing_cls) in g2
            for t in types_in_refactor
        )
        
        if is_subclass_related:
            sample_count += 1
            if sample_count <= 5:
                print(f"  {subj}")
                print(f"    Missing: {missing_cls}")
                print(f"    Has types: {list(types_in_refactor)[:3]}")
                print()

# Check domain/range inference differences
print("\nChecking domain/range related differences...")
missing_domain_range_types = 0
for subj, missing_cls in missing_types[:100]:
    # Check if subject is involved in properties that have domain/range = missing_cls
    for _, prop, obj in g1.triples((subj, None, None)):
        if (prop, RDFS.range, missing_cls) in g2:
            missing_domain_range_types += 1
            print(f"  Range inference missing: ({subj}, {prop}, {obj}) should infer {subj} type {missing_cls}")
            break
        if (prop, RDFS.domain, missing_cls) in g2:
            missing_domain_range_types += 1
            print(f"  Domain inference missing: {subj} with property {prop} should infer type {missing_cls}")
            break
    
    for pred, _, obj in g1.triples((None, None, subj)):
        if (pred, RDFS.domain, missing_cls) in g2:
            missing_domain_range_types += 1
            print(f"  Domain inference missing: {subj} as subject of {pred} should infer type {missing_cls}")
            break

print(f"\nTotal domain/range inference issues found: {missing_domain_range_types}")
