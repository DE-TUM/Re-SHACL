"""Check what paths are in shape_linked_target in the original."""
from pyshacl import validate
from rdflib import Graph
from pyshacl.consts import SH_path, SH_node

shapes_graph = Graph()
shapes_graph.parse('source/ShapesGraphs/Shape_30.ttl', format='ttl')

# Find all property shapes with sh:node
shape_linked_target = set()
for ps in shapes_graph.subjects():
    if list(shapes_graph.objects(ps, SH_node)):
        paths = list(shapes_graph.objects(ps, SH_path))
        shape_linked_target.update(paths)
        
print(f"Paths with sh:node: {len(shape_linked_target)}")
for p in list(shape_linked_target)[:10]:
    print(f"  {p}")
