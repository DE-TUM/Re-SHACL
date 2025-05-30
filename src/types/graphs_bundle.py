from dataclasses import dataclass

from rdflib import Graph


@dataclass
class GraphsBundle:
    data_graph: Graph
    shapes_graph: Graph
