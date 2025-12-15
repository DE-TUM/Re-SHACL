from src.pipeline.run_pipeline import run_merging_pipeline
from rdflib import Namespace

DBP = Namespace('http://dbpedia.org/ontology/')
DUL = Namespace('http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#')

g, same_dict, sg = run_merging_pipeline(
    'source/Datasets/EnDe-Lite50.ttl',
    'source/ShapesGraphs/Shape_30.ttl',
    data_graph_format='ttl',
    shacl_graph_format='ttl'
)

wiki_subjects = set(g.subjects(DBP.wikiPageWikiLink, None))
assoc_subjects = set(g.subjects(DUL.associatedWith, None))

print(f"Subjects with wikiPageWikiLink: {len(wiki_subjects)}")
print(f"Subjects with dul:associatedWith: {len(assoc_subjects)}")
print(f"Overlap: {len(wiki_subjects & assoc_subjects)}")
print(f"Missing dul:associatedWith for: {len(wiki_subjects - assoc_subjects)} subjects")
