from rdflib import Graph, Namespace
from rdflib.namespace import RDFS

g = Graph()
g.parse('source/dbpedia_ontology.owl', format='xml')

DUL = Namespace('http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#')
assoc = DUL.associatedWith

subs = list(g.subjects(RDFS.subPropertyOf, assoc))
print(f'Subproperties of dul:associatedWith: {len(subs)}')
for s in subs[:20]:
    print(f'  {s}')
