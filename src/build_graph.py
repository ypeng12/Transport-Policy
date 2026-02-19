# -*- coding: utf-8 -*-
"""
build_graph.py — 构建有向加权图
将边列表转换为 NetworkX DiGraph，边带权重属性。
"""

import networkx as nx
from .schemas import WEIGHT_COL


def build_directed_graph(edges_df):
    """
    从聚合后的边 DataFrame 构建有向加权图。

    Parameters
    ----------
    edges_df : pd.DataFrame
        至少包含 origin, dest, weight 列

    Returns
    -------
    nx.DiGraph
        有向加权图，边属性含 weight
    """
    G = nx.DiGraph()

    for _, row in edges_df.iterrows():
        u, v = row["origin"], row["dest"]
        w = row[WEIGHT_COL]

        # 如果同一 OD 对有多条记录（不同时间段），叠加权重
        if G.has_edge(u, v):
            G[u][v]["weight"] += w
        else:
            G.add_edge(u, v, weight=w)

    # 计算节点属性：总吞吐量 = 入权重 + 出权重
    for node in G.nodes():
        in_w = sum(d["weight"] for _, _, d in G.in_edges(node, data=True))
        out_w = sum(d["weight"] for _, _, d in G.out_edges(node, data=True))
        G.nodes[node]["throughput"] = in_w + out_w

    print(f"[build_graph] 图构建完成: {G.number_of_nodes()} 节点, "
          f"{G.number_of_edges()} 条边")
    return G
