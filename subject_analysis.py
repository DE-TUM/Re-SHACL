import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rdflib
from rdflib import Graph, RDF, RDFS, OWL

# Load both graphs
print("Loading graphs...")
g1 = Graph()  # refactored
g1.parse("src/fused_refactor_test.ttl", format="ttl")

g2 = Graph()  # original
g2.parse("src/fused_reshacl_test.ttl", format="ttl")

# Find subjects that exist in original but not refactored
print("\n=== Subjects in original but not in refactored ===")
subjects_g2 = set(s for s, _, _ in g2)
subjects_g1 = set(s for s, _, _ in g1)

missing_subjects = subjects_g2 - subjects_g1
print(f"Subjects in original but not refactored: {len(missing_subjects)}")
print("\nSample missing subjects:")
for i, subj in enumerate(list(missing_subjects)[:10]):
    print(f"\n{i+1}. {subj}")
    # Show what triples involve this subject in original
    triples = list(g2.triples((subj, None, None)))[:5]
    for s, p, o in triples:
        print(f"   ({s}, {p}, {o})")

# Check if missing subjects are involved in owl:sameAs
print("\n\n=== Checking if missing subjects are merged via owl:sameAs ===")
sameas_map = {}
for missing in list(missing_subjects)[:10]:
    # Check if this subject has sameAs in original
    same_as_targets = list(g2.objects(missing, OWL.sameAs))
    same_as_sources = list(g2.subjects(OWL.sameAs, missing))
    
    if same_as_targets or same_as_sources:
        print(f"\n{missing}:")
        if same_as_targets:
            print(f"  sameAs targets: {same_as_targets[:3]}")
            # Check if any of these exist in refactored
            exists_in_g1 = [t for t in same_as_targets if any(g1.triples((t, None, None)))]
            if exists_in_g1:
                print(f"  ✓ Merged into: {exists_in_g1}")
        if same_as_sources:
            print(f"  sameAs sources: {same_as_sources[:3]}")
            exists_in_g1 = [s for s in same_as_sources if any(g1.triples((s, None, None)))]
            if exists_in_g1:
                print(f"  ✓ Merged into: {exists_in_g1}")

# Check for extra subjects in refactored
extra_subjects = subjects_g1 - subjects_g2
print(f"\n\n=== Extra subjects in refactored: {len(extra_subjects)} ===")
if len(extra_subjects) > 0:
    print("Sample extra subjects:")
    for i, subj in enumerate(list(extra_subjects)[:5]):
        print(f"\n{i+1}. {subj}")
        triples = list(g1.triples((subj, None, None)))[:3]
        for s, p, o in triples:
            print(f"   ({s}, {p}, {o})")

# Analyze the 26 subjects that exist but have missing types
print("\n\n=== Subjects with missing types (exist in both graphs) ===")
missing_types = [(s, o) for s, p, o in (g2 - g1) if p == RDF.type]
subjects_missing_types = set(s for s, _ in missing_types)
subjects_in_both = subjects_missing_types & subjects_g1

print(f"Subjects in both graphs but missing types: {len(subjects_in_both)}")
for i, subj in enumerate(list(subjects_in_both)[:5]):
    print(f"\n{i+1}. {subj}")
    
    # Types in original
    types_g2 = set(g2.objects(subj, RDF.type))
    types_g1 = set(g1.objects(subj, RDF.type))
    missing = types_g2 - types_g1
    extra = types_g1 - types_g2
    
    print(f"   Types in original: {len(types_g2)}")
    print(f"   Types in refactor: {len(types_g1)}")
    print(f"   Missing types: {len(missing)}")
    if missing:
        print(f"   Sample missing: {list(missing)[:3]}")
    print(f"   Extra types: {len(extra)}")
    if extra:
        print(f"   Sample extra: {list(extra)[:3]}")
