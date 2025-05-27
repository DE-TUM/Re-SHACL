from rdflib.namespace import RDF, RDFS, OWL, SH
from rdflib import Namespace

SH_class = SH["class"]
RDFS_PFX = 'http://www.w3.org/2000/01/rdf-schema#'
RDFS_NS = Namespace(RDFS_PFX)
RDFS_subPropertyOf = RDFS_NS.subPropertyOf
RDFS_subClassOf = RDFS_NS.subClassOf

__all__ = [
    "RDF", "RDFS", "OWL", "SH", "SH_class", "RDFS_subPropertyOf", "RDFS_subClassOf"
]