import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rdflib
from rdflib import Graph, RDF, OWL, RDFS

# Load both graphs
print("Loading graphs...")
g1 = Graph()  # refactored
g1.parse("src/fused_refactor_test.ttl", format="ttl")

g2 = Graph()  # original
g2.parse("src/fused_reshacl_test.ttl", format="ttl")

# Get all missing type triples
missing_types = [(s, o) for s, p, o in (g2 - g1) if p == RDF.type]

# Categorize missing types
print("=== CATEGORIZING MISSING TYPES ===\n")

# Category 1: Subject doesn't exist in refactored (merged away)
subjects_not_in_g1 = [(s, o) for s, o in missing_types if not any(g1.triples((s, None, None)))]
print(f"1. Subject merged away: {len(subjects_not_in_g1)}")

# Category 2: Subject exists but type is missing
subjects_exist_type_missing = [(s, o) for s, o in missing_types if any(g1.triples((s, None, None)))]
print(f"2. Subject exists but type missing: {len(subjects_exist_type_missing)}")

# Analyze category 2 in detail
print("\n=== ANALYZING SUBJECTS WITH MISSING TYPES ===")
for s, missing_type in subjects_exist_type_missing[:10]:
    print(f"\n{s}")
    print(f"  Missing type: {missing_type}")
    
    # Get all types the subject has in both graphs
    types_g1 = set(g1.objects(s, RDF.type))
    types_g2 = set(g2.objects(s, RDF.type))
    
    print(f"  Types in refactored: {len(types_g1)}")
    print(f"  Types in original: {len(types_g2)}")
    
    # Check if missing_type is a superclass of any type in g1
    is_superclass_of_existing = False
    for t in types_g1:
        if (t, RDFS.subClassOf, missing_type) in g1 or (t, RDFS.subClassOf, missing_type) in g2:
            is_superclass_of_existing = True
            print(f"  Note: {missing_type} is a superclass of {t} (which subject HAS)")
            break
    
    if not is_superclass_of_existing:
        # Check if the class is related to sameAs entities
        sameas_related = list(g2.objects(s, OWL.sameAs)) + list(g2.subjects(OWL.sameAs, s))
        if sameas_related:
            print(f"  Related via sameAs to: {len(sameas_related)} entities")
            # Check if any of those have the missing type
            for related in sameas_related[:3]:
                if (related, RDF.type, missing_type) in g2:
                    print(f"    {related} has the missing type in original")

print("\n\n=== HYPOTHESIS TEST ===")
# Check if the 349 extra missing types are due to subclass inference not being applied
superclass_related = 0
for s, missing_type in subjects_exist_type_missing:
    types_g1 = set(g1.objects(s, RDF.type))
    for t in types_g1:
        # Check if any superclass relationship exists
        if (t, RDFS.subClassOf, missing_type) in g1 or (t, RDFS.subClassOf, missing_type) in g2:
            superclass_related += 1
            break

print(f"Missing types that are superclasses of existing types: {superclass_related}")
print(f"Missing types not explained by subclass: {len(subjects_exist_type_missing) - superclass_related}")

# Check the closure operation in refactored version
print("\n=== Checking subclass closure application ===")
# Sample a subject that exists in both
for s, missing_type in subjects_exist_type_missing[:5]:
    print(f"\nSubject: {s}")
    print(f"Missing type: {missing_type}")
    
    # Get direct types
    types_g1 = list(g1.objects(s, RDF.type))
    print(f"Direct types in refactored: {len(types_g1)}")
    
    # Check if missing_type should be inferred via subClassOf
    for t in types_g1:
        # Check transitive closure
        superclasses = list(g1.transitive_objects(t, RDFS.subClassOf))
        if missing_type in superclasses:
            print(f"  ERROR: {missing_type} is a superclass of {t} but wasn't added!")
            break
