# -*- coding: utf-8 -*-
"""
robustness.py — 网络鲁棒性模拟
通过有策略地逐步移除节点，观察网络连通性 (NGC) 的衰减。
支持按不同中心性指标进行 "定向攻击"，以及随机攻击基线。
"""

import copy
import random
import numpy as np
import networkx as nx
import pandas as pd
from . import metrics as met


def _ngc(G):
    """计算当前图的巨型连通子图比例"""
    if len(G) == 0:
        return 0.0
    largest = max(nx.weakly_connected_components(G), key=len)
    return len(largest) / len(G)


def _get_ranking(G, strategy, domirank_params=None):
    """
    按给定策略对节点排序（从高到低）。

    Parameters
    ----------
    G : nx.DiGraph
    strategy : str
        'degree' / 'betweenness' / 'pagerank' / 'domirank'
    domirank_params : dict

    Returns
    -------
    list  排序后的节点列表 (最重要 → 最不重要)
    """
    if strategy == "degree":
        scores = dict(G.degree(weight="weight"))
    elif strategy == "betweenness":
        scores = met.betweenness_centrality(G)
    elif strategy == "pagerank":
        scores = met.pagerank(G)
    elif strategy == "domirank":
        params = domirank_params or {}
        scores = met.domirank(G, **params)
    else:
        raise ValueError(f"未知策略: {strategy}")

    # 按分值降序排列
    return sorted(scores, key=scores.get, reverse=True)


def targeted_attack(G, strategy, domirank_params=None):
    """
    定向攻击模拟:
    按照指定中心性从高到低逐步移除节点，记录每步的 NGC。

    Parameters
    ----------
    G : nx.DiGraph
    strategy : str
        攻击策略名称
    domirank_params : dict

    Returns
    -------
    pd.DataFrame
        columns: ['fraction_removed', 'ngc', 'strategy']
    """
    print(f"  [robustness] 定向攻击: {strategy}")
    G_copy = G.copy()
    n_total = len(G_copy)

    if n_total == 0:
        return pd.DataFrame(columns=["fraction_removed", "ngc", "strategy"])

    ranking = _get_ranking(G_copy, strategy, domirank_params)

    records = [{"fraction_removed": 0.0, "ngc": _ngc(G_copy), "strategy": strategy}]

    for i, node in enumerate(ranking):
        if node in G_copy:
            G_copy.remove_node(node)
        frac = (i + 1) / n_total
        ngc_val = _ngc(G_copy) if len(G_copy) > 0 else 0.0
        records.append({"fraction_removed": frac, "ngc": ngc_val, "strategy": strategy})

    return pd.DataFrame(records)


def random_attack(G, n_runs=10):
    """
    随机攻击基线:
    随机顺序移除节点，重复 n_runs 次取平均值。

    Parameters
    ----------
    G : nx.DiGraph
    n_runs : int

    Returns
    -------
    pd.DataFrame
    """
    print(f"  [robustness] 随机攻击: {n_runs} 次平均")
    n_total = len(G)
    nodes = list(G.nodes())

    if n_total == 0:
        return pd.DataFrame(columns=["fraction_removed", "ngc", "strategy"])

    # 每次运行都记录 NGC
    all_ngc = np.zeros((n_runs, n_total + 1))

    for run in range(n_runs):
        G_copy = G.copy()
        order = nodes.copy()
        random.shuffle(order)

        all_ngc[run, 0] = _ngc(G_copy)

        for i, node in enumerate(order):
            if node in G_copy:
                G_copy.remove_node(node)
            all_ngc[run, i + 1] = _ngc(G_copy) if len(G_copy) > 0 else 0.0

    # 取平均
    avg_ngc = all_ngc.mean(axis=0)
    fractions = np.arange(n_total + 1) / n_total

    records = [
        {"fraction_removed": float(fractions[i]), "ngc": float(avg_ngc[i]),
         "strategy": "random"}
        for i in range(n_total + 1)
    ]
    return pd.DataFrame(records)


def run_robustness(G, strategies, random_runs=10, domirank_params=None):
    """
    运行完整的鲁棒性模拟。

    Parameters
    ----------
    G : nx.DiGraph
    strategies : list of str
        例如 ['degree', 'betweenness', 'pagerank', 'domirank', 'random']
    random_runs : int
    domirank_params : dict

    Returns
    -------
    pd.DataFrame
        所有策略的结果合并
    """
    print("\n" + "=" * 60)
    print(" 鲁棒性模拟 (Robustness Simulation)")
    print("=" * 60)

    results = []

    for strat in strategies:
        if strat == "random":
            df = random_attack(G, n_runs=random_runs)
        else:
            df = targeted_attack(G, strat, domirank_params=domirank_params)
        results.append(df)

    combined = pd.concat(results, ignore_index=True)
    print(f"\n✅ 鲁棒性模拟完成 ({len(strategies)} 种策略)")
    return combined
