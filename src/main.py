from src.pipeline.run_pipeline import run_merging_pipeline

if __name__ == "__main__":
    g = "../source/Datasets/EnDe-Lite50.ttl"
    sg = "../source/ShapesGraphs/Shape_30.ttl"
    fused_graph, same_dic, shapes = run_merging_pipeline(g, shacl_graph=sg, data_graph_format='turtle', shacl_graph_format='turtle')
