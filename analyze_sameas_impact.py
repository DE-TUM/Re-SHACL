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

# Find all sameAs relationships in original
print("=== Analyzing owl:sameAs relationships ===\n")

# Count type statements for entities involved in sameAs
type_count_in_sameas_g2 = 0
type_count_in_sameas_g1 = 0
sameas_pairs = set()

for s, p, o in g2.triples((None, OWL.sameAs, None)):
    if s != o:  # skip reflexive
        sameas_pairs.add((s, o))
        
print(f"Total distinct sameAs pairs in original: {len(sameas_pairs)}")

# For each pair, count how many type statements exist for the subject
for subj, obj in list(sameas_pairs)[:20]:
    types_subj_g2 = list(g2.objects(subj, RDF.type))
    types_obj_g2 = list(g2.objects(obj, RDF.type))
    
    # Check if subject exists in refactored
    exists_in_g1 = any(g1.triples((subj, None, None)))
    
    print(f"\n{subj}")
    print(f"  -> sameAs {obj}")
    print(f"  Original: subj has {len(types_subj_g2)} types, obj has {len(types_obj_g2)} types")
    print(f"  Refactored: subj exists = {exists_in_g1}")
    
    if exists_in_g1:
        types_subj_g1 = list(g1.objects(subj, RDF.type))
        print(f"  Refactored: subj has {len(types_subj_g1)} types")
    else:
        # Check if obj exists in refactored (merged into obj)
        obj_exists = any(g1.triples((obj, None, None)))
        if obj_exists:
            types_obj_g1 = list(g1.objects(obj, RDF.type))
            print(f"  Refactored: obj has {len(types_obj_g1)} types (subj merged into obj)")
        else:
            print(f"  Refactored: neither subj nor obj exist!")
            
    type_count_in_sameas_g2 += len(types_subj_g2)
    
print(f"\n\n=== SUMMARY ===")
print(f"Type statements in sameAs subjects (first 20 pairs) in original: {type_count_in_sameas_g2}")

# Calculate the actual difference
print("\n=== Checking if difference is just from sameAs merging ===")
# Get all subjects involved in sameAs in g2
sameas_subjects_g2 = set()
for s, _, o in g2.triples((None, OWL.sameAs, None)):
    if s != o:
        sameas_subjects_g2.add(s)
        sameas_subjects_g2.add(o)

print(f"Unique entities involved in sameAs in original: {len(sameas_subjects_g2)}")

# Count their type statements
sameas_type_count_g2 = sum(len(list(g2.objects(s, RDF.type))) for s in sameas_subjects_g2)
print(f"Total type statements for sameAs entities in original: {sameas_type_count_g2}")

# Count how many of these entities don't exist in refactored
missing_in_g1 = sum(1 for s in sameas_subjects_g2 if not any(g1.triples((s, None, None))))
print(f"Entities from sameAs that don't exist in refactored: {missing_in_g1}")

# Count type statements for those missing entities
missing_type_count = sum(len(list(g2.objects(s, RDF.type))) for s in sameas_subjects_g2 
                          if not any(g1.triples((s, None, None))))
print(f"Type statements for entities that were merged away: {missing_type_count}")

print(f"\nMissing types from comparison: {len([1 for s, p, o in (g2 - g1) if p == RDF.type])}")
print(f"Types from merged entities: {missing_type_count}")
print(f"Difference: {len([1 for s, p, o in (g2 - g1) if p == RDF.type]) - missing_type_count}")
