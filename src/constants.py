# constants.py
from rdflib.namespace import RDF, RDFS, OWL, SH

RDFS_SUBPROPERTYOF = RDFS.subPropertyOf
RDFS_SUBCLASSOF = RDFS.subClassOf
OWL_EQUIVALENTCLASS = OWL.equivalentClass
OWL_SAMEAS = OWL.sameAs
SH_PATH = SH.path
SH_NODE = SH.node
SH_TARGETNODE = SH.targetNode
SH_CLASS = SH["class"]