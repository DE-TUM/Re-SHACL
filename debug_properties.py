"""
Debug script to check property relationships in DG_1.ttl
"""
from rdflib import Graph, OWL, Namespace

g = Graph()
g.parse("test_graphs/DG_1.ttl", format="turtle")

SCHEMA = Namespace("http://schema.org/")

print("="*60)
print("ALL PROPERTY SAMEAS RELATIONSHIPS")
print("="*60)

for s, p, o in g.triples((None, OWL.sameAs, None)):
    # Check if subject or object looks like a property
    s_str = str(s)
    o_str = str(o)
    if 'schema.org' in s_str or 'schema.org' in o_str:
        print(f"{s} owl:sameAs {o}")

print("\n" + "="*60)
print("PROPERTIES IN SCHEMA NAMESPACE")
print("="*60)

# Get all unique properties used in the graph
props = set()
for s, p, o in g:
    if str(p).startswith("http://schema.org/"):
        props.add(p)

for prop in sorted(props, key=str):
    print(f"  {prop}")

print("\n" + "="*60)
print("CHECKING schema:name and schema:nn")
print("="*60)

print(f"\nschema:name in graph: {(SCHEMA.name, None, None) in g or (None, SCHEMA.name, None) in g or (None, None, SCHEMA.name) in g}")
print(f"schema:nn in graph: {(SCHEMA.nn, None, None) in g or (None, SCHEMA.nn, None) in g or (None, None, SCHEMA.nn) in g}")

print("\nTriples involving schema:name:")
for s, p, o in g:
    if s == SCHEMA.name or p == SCHEMA.name or o == SCHEMA.name:
        print(f"  {s} {p} {o}")

print("\nTriples involving schema:nn:")
for s, p, o in g:
    if s == SCHEMA.nn or p == SCHEMA.nn or o == SCHEMA.nn:
        print(f"  {s} {p} {o}")
