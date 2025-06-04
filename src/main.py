from ReSHACL.re_shacl import merged_graph
from src.pipeline.run_pipeline import run_merging_pipeline

if __name__ == "__main__":
    g = "../source/Datasets/EnDe-Lite50.ttl"
    sg = "../source/ShapesGraphs/Shape_30.ttl"
    print("Re-FACTOR Re-SHACL starting...")
    fused_graph, same_dic, shapes_graph = run_merging_pipeline(g, shacl_graph=sg, data_graph_format='turtle', shacl_graph_format='turtle')
    print("Re-FACTOR Re-SHACL done...")
    fused_graph.serialize("fused_refactor_test.ttl", format="turtle")

    # print("Re-SHACL starting...")
    # fg, sd, ss = merged_graph(g, shacl_graph=sg, data_graph_format='turtle', shacl_graph_format='turtle')
    # print("Re-SHACL done...")
    # fg.serialize("fused_reshacl_test.ttl", format="turtle")
