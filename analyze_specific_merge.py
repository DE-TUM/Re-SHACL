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

# Pick a specific missing subject to analyze
missing_subj = rdflib.URIRef("http://dbpedia.org/resource/Sadanoumi_Takashi")
merged_into = rdflib.URIRef("http://de.dbpedia.org/resource/Sadanoumi_Takashi")

print(f"\nAnalyzing: {missing_subj}")
print(f"Merged into: {merged_into}")
print()

# Check in original graph
print("=== IN ORIGINAL (g2) ===")
print(f"Missing subject exists: {any(g2.triples((missing_subj, None, None)))}")
print(f"Merged-into exists: {any(g2.triples((merged_into, None, None)))}")

if any(g2.triples((missing_subj, None, None))):
    types_missing = list(g2.objects(missing_subj, RDF.type))
    print(f"Types of missing_subj: {len(types_missing)}")
    for t in types_missing[:5]:
        print(f"  - {t}")

if any(g2.triples((merged_into, None, None))):
    types_merged = list(g2.objects(merged_into, RDF.type))
    print(f"Types of merged_into: {len(types_merged)}")
    for t in types_merged[:5]:
        print(f"  - {t}")

print(f"\nSameAs relationship in g2:")
print(f"  {missing_subj} sameAs ? : {list(g2.objects(missing_subj, OWL.sameAs))[:3]}")
print(f"  ? sameAs {missing_subj} : {list(g2.subjects(OWL.sameAs, missing_subj))[:3]}")

print("\n=== IN REFACTORED (g1) ===")
print(f"Missing subject exists: {any(g1.triples((missing_subj, None, None)))}")
print(f"Merged-into exists: {any(g1.triples((merged_into, None, None)))}")

if any(g1.triples((missing_subj, None, None))):
    types_missing = list(g1.objects(missing_subj, RDF.type))
    print(f"Types of missing_subj: {len(types_missing)}")
    for t in types_missing[:5]:
        print(f"  - {t}")

if any(g1.triples((merged_into, None, None))):
    types_merged = list(g1.objects(merged_into, RDF.type))
    print(f"Types of merged_into: {len(types_merged)}")
    for t in types_merged[:5]:
        print(f"  - {t}")

print(f"\nSameAs relationship in g1:")
sameas_obj = list(g1.objects(missing_subj, OWL.sameAs))
sameas_subj = list(g1.subjects(OWL.sameAs, missing_subj))
print(f"  {missing_subj} sameAs ? : {sameas_obj[:3]}")
print(f"  ? sameAs {missing_subj} : {sameas_subj[:3]}")

# Check if types were properly transferred
if any(g2.triples((missing_subj, None, None))):
    original_types = set(g2.objects(missing_subj, RDF.type))
    refactored_types = set(g1.objects(merged_into, RDF.type)) if any(g1.triples((merged_into, None, None))) else set()
    
    missing_types_in_merge = original_types - refactored_types
    print(f"\n=== TYPE TRANSFER ANALYSIS ===")
    print(f"Original had {len(original_types)} types")
    print(f"Refactored has {len(refactored_types)} types for merged_into")
    print(f"Missing in transfer: {len(missing_types_in_merge)}")
    if missing_types_in_merge:
        print("Sample missing types:")
        for t in list(missing_types_in_merge)[:5]:
            print(f"  - {t}")
