# fuse.py
from engine.inferencer import Inferencer

def fuse_graphs(data_graph, shacl_graph, data_graph_format=None, shacl_graph_format=None, config_overrides=None):
    inferencer = Inferencer()

    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(inferencer, f"with_{key}"):
                getattr(inferencer, f"with_{key}")(value)

    return inferencer.run(data_graph, shacl_graph, data_graph_format, shacl_graph_format)


if __name__ == '__main__':
    dg = "../source/Datasets/EnDe-Lite50.ttl"
    sg = "../source/ShapesGraphs/Shape_30.ttl"
    final_graph = fuse_graphs(
        data_graph=dg,
        shacl_graph=sg,
        data_graph_format="turtle",
        shacl_graph_format="turtle",
        config_overrides={
            "same_as_merging": False,
            "domain_range_inference": False,
            "class_merging": False,
            "property_inference": False
        }
    )