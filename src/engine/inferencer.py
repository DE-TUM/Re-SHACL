from ..core.loader import load_graph
from ..rules.domain_range import apply_domain_range_rules
from ..rules.class_merging import merge_equivalent_classes
from ..rules.same_as import resolve_same_as
from ..rules.property_rules import apply_property_inference


class Inferencer:
    def __init__(self):
        self.config = {
            "merge_same_as": True,
            "infer_domain_range": True,
            "merge_equivalent_classes": True,
            "apply_property_inference": True,
        }

    def with_same_as_merging(self, value: bool):
        self.config["merge_same_as"] = value
        return self

    def with_domain_range_inference(self, value: bool):
        self.config["infer_domain_range"] = value
        return self

    def with_class_merging(self, value: bool):
        self.config["merge_equivalent_classes"] = value
        return self

    def with_property_inference(self, value: bool):
        self.config["apply_property_inference"] = value
        return self

    def run(self, data_graph, shacl_graph, data_graph_format=None, shacl_graph_format=None):
        shapes, graphs, shape_graph = load_graph(
            data_graph, shacl_graph, data_graph_format, shacl_graph_format
        )
        g = graphs[0]

        if self.config["infer_domain_range"]:
            apply_domain_range_rules(g, shapes)

        if self.config["merge_equivalent_classes"]:
            merge_equivalent_classes(g, shapes)

        if self.config["apply_property_inference"]:
            apply_property_inference(g, shapes)

        if self.config["merge_same_as"]:
            resolve_same_as(g, shapes)

        return g
