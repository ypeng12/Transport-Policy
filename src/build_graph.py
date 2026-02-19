# -*- coding: utf-8 -*-
"""
build_graph.py — 构建有向加权图
将边列表转换为 NetworkX DiGraph，边带权重属性。
"""

import networkx as nx
from .schemas import WEIGHT_COL


def build_directed_graph(edges_df, meta_df=None):
    """
    从聚合后的边 DataFrame 构建有向加权图。
    支持注入地理元数据 (lat, lng, city, name)。
    """
    G = nx.DiGraph()

    for _, row in edges_df.iterrows():
        u, v = row["origin"], row["dest"]
        w = row[WEIGHT_COL]

        if G.has_edge(u, v):
            G[u][v]["weight"] += w
        else:
            G.add_edge(u, v, weight=w)

    # 注入节点元数据
    meta_dict = {}
    if meta_df is not None:
        meta_dict = meta_df.set_index("id").to_dict("index")

    for node in G.nodes():
        # 计算节点属性：总吞吐量
        in_w = sum(d["weight"] for _, _, d in G.in_edges(node, data=True))
        out_w = sum(d["weight"] for _, _, d in G.out_edges(node, data=True))
        G.nodes[node]["throughput"] = in_w + out_w

        # 挂载元数据
        if node in meta_dict:
            m = meta_dict[node]
            G.nodes[node]["lat"] = m.get("lat")
            G.nodes[node]["lng"] = m.get("lng")
            G.nodes[node]["city"] = m.get("city")
            G.nodes[node]["full_name"] = m.get("name")
        else:
            # 默认值
            G.nodes[node]["lat"] = None
            G.nodes[node]["lng"] = None

    print(f"[build_graph] 图构建完成: {G.number_of_nodes()} 节点, "
          f"{G.number_of_edges()} 条边 (已附加元数据)")
    return G
