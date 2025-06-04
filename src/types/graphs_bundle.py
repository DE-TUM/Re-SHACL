from pyshacl import ShapesGraph
from rdflib import Graph
from dataclasses import dataclass


@dataclass
class GraphsBundle:
    data_graph: Graph
    shapes_graph: ShapesGraph
