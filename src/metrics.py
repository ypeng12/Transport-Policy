# -*- coding: utf-8 -*-
"""
metrics.py — 网络指标计算
包含 5 种节点中心性 + 4 种网络整体指标。

节点中心性:
  1. 度中心性 (Degree) — 含入度、出度、总度
  2. 中介中心性 (Betweenness)
  3. 接近中心性 (Closeness)
  4. PageRank
  5. DomiRank — 本文创新点，迭代求解支配力

网络整体指标:
  1. 网络密度 (Density)
  2. 聚类系数 (Clustering Coefficient)
  3. 平均最短路径长度 (Average Shortest Path Length)
  4. 巨型连通子图比例 (NGC — Normalized Giant Component)
"""

import numpy as np
import networkx as nx
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigs
import pandas as pd


# ====================================================================
#  节点中心性 (Node Centrality)
# ====================================================================

def degree_centrality(G):
    """
    度中心性: k_i = k_i_in + k_i_out
    连接越多 → 越核心

    返回 DataFrame 含 in_degree, out_degree, total_degree
    """
    in_deg = dict(G.in_degree(weight="weight"))
    out_deg = dict(G.out_degree(weight="weight"))
    nodes = list(G.nodes())

    data = {
        "node": nodes,
        "in_degree": [in_deg.get(n, 0) for n in nodes],
        "out_degree": [out_deg.get(n, 0) for n in nodes],
        "total_degree": [in_deg.get(n, 0) + out_deg.get(n, 0) for n in nodes],
    }
    return pd.DataFrame(data)


def betweenness_centrality(G, weight="weight"):
    """
    中介中心性: C_B(i) = Σ σ_st(i) / σ_st
    在多少条最短路径上充当 "中转站"
    删掉它 → 很多路径断掉 → 桥梁节点
    """
    bc = nx.betweenness_centrality(G, weight=weight, normalized=True)
    return bc


def closeness_centrality(G, weight="weight"):
    """
    接近中心性: C_C(i) = (N-1) / Σ d(i,j)
    到其他机场平均距离是否近
    越靠 "网络中心"，分值越高

    注意: 对于加权图，NetworkX 把 weight 当作 "距离"
    这里我们需要将 weight 转化为距离 (取倒数)
    """
    # 创建副本，将权重转化为距离 (1/weight)
    G_dist = G.copy()
    for u, v, d in G_dist.edges(data=True):
        w = d.get(weight, 1)
        d["distance"] = 1.0 / w if w > 0 else float("inf")

    cc = nx.closeness_centrality(G_dist, distance="distance")
    return cc


def pagerank(G, alpha=0.85, max_iter=100, tol=1e-6, weight="weight"):
    """
    PageRank: PR(i) = (1-α)/N + α × Σ PR(u)/L(u)
    被重要机场指向的机场更重要
    不是 "连得多"，而是 "连到谁"
    """
    pr = nx.pagerank(G, alpha=alpha, max_iter=max_iter, tol=tol, weight=weight)
    return pr


def domirank(G, sigma=None, theta=1.0, beta=1.0, max_iter=500, tol=1e-6):
    """
    DomiRank — 本文的创新中心性指标

    核心思想: 如果一个节点周围都是弱节点，它就具有 "支配力"

    动态方程:
        dΓ_i/dt = σ × (θ × k_i − Σ_j w_ij × Γ_j) − β × Γ_i

    离散迭代:
        Γ(t+1) = σ × (θ × k − A @ Γ(t)) − β × Γ(t)

    其中:
        σ (sigma) — 耦合强度，需满足 |σ| < 1/ρ(A)，ρ(A) 为邻接矩阵谱半径
        θ (theta) — 度项的缩放系数
        β (beta)  — 衰减/阻尼项
        A          — 加权邻接矩阵
        k          — 加权度向量

    Parameters
    ----------
    G : nx.DiGraph
    sigma : float or None
        如果为 None，自动计算安全值 σ = -0.9 / ρ(A)
    theta : float
    beta : float
    max_iter : int
    tol : float

    Returns
    -------
    dict  { node: domirank_score }
    """
    nodes = list(G.nodes())
    n = len(nodes)
    node_idx = {nd: i for i, nd in enumerate(nodes)}

    # 构建邻接矩阵 A (稀疏矩阵)
    rows, cols, vals = [], [], []
    for u, v, d in G.edges(data=True):
        i, j = node_idx[u], node_idx[v]
        w = d.get("weight", 1.0)
        rows.append(i)
        cols.append(j)
        vals.append(w)

    A = csr_matrix((vals, (rows, cols)), shape=(n, n))

    # 加权度向量 k_i = Σ_j A_ij (出度 + 入度方向都考虑，这里用行和+列和)
    k_out = np.array(A.sum(axis=1)).flatten()   # 出度权重
    k_in = np.array(A.sum(axis=0)).flatten()    # 入度权重
    k = k_out + k_in  # 总加权度

    # 计算谱半径 ρ(A) — 用于确定 sigma 的安全范围
    try:
        # 对称化邻接矩阵来估算谱半径 (A + A^T) / 2
        A_sym = (A + A.T) / 2.0
        eigenvalues = eigs(A_sym.astype(float), k=1, which="LM", return_eigenvectors=False)
        spectral_radius = float(np.abs(eigenvalues[0]))
    except Exception:
        # 如果稀疏特征值分解失败，用 Frobenius 范数估计
        spectral_radius = float(np.sqrt((A.multiply(A)).sum()))

    print(f"[metrics] DomiRank: 谱半径 ρ(A) ≈ {spectral_radius:.4f}")

    # 自动确定 sigma (负值表示竞争机制)
    if sigma is None:
        if spectral_radius > 0:
            sigma = -0.9 / spectral_radius
        else:
            sigma = -0.1
        print(f"[metrics] DomiRank: 自动设定 σ = {sigma:.6f}")
    else:
        # 检查稳定性条件
        if spectral_radius > 0 and abs(sigma) >= 1.0 / spectral_radius:
            safe_sigma = -0.9 / spectral_radius
            print(f"[metrics] ⚠️ 给定 σ={sigma} 不满足 |σ| < 1/ρ(A)={1/spectral_radius:.6f}")
            print(f"[metrics] 自动调整为安全值 σ = {safe_sigma:.6f}")
            sigma = safe_sigma

    # 迭代求解
    Gamma = np.zeros(n, dtype=float)  # 初始 DomiRank 值全为 0
    A_dense = A.toarray().astype(float)  # 转为密集矩阵加速小规模计算

    for iteration in range(max_iter):
        # Γ(t+1) = σ × (θ × k − A @ Γ(t)) − β × Γ(t)
        # 注意这里用 (A + A^T) 使有向图的影响双向传播
        interaction = (A_dense + A_dense.T) @ Gamma
        Gamma_new = sigma * (theta * k - interaction) - beta * Gamma

        # 收敛判断
        diff = np.linalg.norm(Gamma_new - Gamma)
        if diff < tol:
            print(f"[metrics] DomiRank: 第 {iteration+1} 次迭代收敛 (diff={diff:.2e})")
            Gamma = Gamma_new
            break
        Gamma = Gamma_new
    else:
        print(f"[metrics] DomiRank: 达到最大迭代次数 {max_iter}, diff={diff:.2e}")

    # 归一化到 [0, 1]
    g_min, g_max = Gamma.min(), Gamma.max()
    if g_max > g_min:
        Gamma_norm = (Gamma - g_min) / (g_max - g_min)
    else:
        Gamma_norm = np.zeros(n)

    return {nodes[i]: float(Gamma_norm[i]) for i in range(n)}


# ====================================================================
#  网络整体指标 (Network-Level Metrics)
# ====================================================================

def network_density(G):
    """
    网络密度: D = E / (N × (N-1))
    衡量连接的稠密程度
    """
    return nx.density(G)


def clustering_coefficient(G):
    """
    平均聚类系数: 机场的邻居之间是否互相连接
    """
    # NetworkX 对有向图也支持 clustering
    return nx.average_clustering(G)


def average_shortest_path(G):
    """
    平均最短路径长度: L = 1/(N(N-1)) × Σ d(i,j)
    衡量网络效率

    注意: 只在最大强连通子图上计算（否则可能不连通）
    """
    # 获取最大强连通分量 (Strongly Connected Component)
    if nx.is_strongly_connected(G):
        scc = G
    else:
        largest_scc = max(nx.strongly_connected_components(G), key=len)
        scc = G.subgraph(largest_scc).copy()
        print(f"[metrics] 图不是强连通的，在最大强连通子图上计算 "
              f"({len(scc)}/{len(G)} 节点)")

    if len(scc) <= 1:
        return float("inf")

    return nx.average_shortest_path_length(scc)


def giant_component_ratio(G):
    """
    巨型连通子图比例 (NGC):
    NGC = |V_GC| / N

    用弱连通分量 (weakly connected) 衡量
    """
    if len(G) == 0:
        return 0.0
    largest_wcc = max(nx.weakly_connected_components(G), key=len)
    return len(largest_wcc) / len(G)


# ====================================================================
#  汇总计算
# ====================================================================

def compute_all_centralities(G, pagerank_params=None, domirank_params=None):
    """
    计算所有 5 种节点中心性指标，返回合并后的 DataFrame。

    Parameters
    ----------
    G : nx.DiGraph
    pagerank_params : dict, optional
        PageRank 参数 (alpha, max_iter, tol)
    domirank_params : dict, optional
        DomiRank 参数 (sigma, theta, beta, max_iter, tol)

    Returns
    -------
    pd.DataFrame
        每行一个机场，列为各中心性分值
    """
    if pagerank_params is None:
        pagerank_params = {}
    if domirank_params is None:
        domirank_params = {}

    print("\n" + "=" * 60)
    print(" 计算节点中心性")
    print("=" * 60)

    # 1. 度中心性
    print("\n[1/5] 度中心性 (Degree)...")
    deg_df = degree_centrality(G)

    # 2. 中介中心性
    print("[2/5] 中介中心性 (Betweenness)...")
    bc = betweenness_centrality(G)

    # 3. 接近中心性
    print("[3/5] 接近中心性 (Closeness)...")
    cc = closeness_centrality(G)

    # 4. PageRank
    print("[4/5] PageRank...")
    pr = pagerank(G, **pagerank_params)

    # 5. DomiRank
    print("[5/5] DomiRank...")
    dr = domirank(G, **domirank_params)

    # 合并为一张表
    result = deg_df.copy()
    result["betweenness"] = result["node"].map(bc)
    result["closeness"] = result["node"].map(cc)
    result["pagerank"] = result["node"].map(pr)
    result["domirank"] = result["node"].map(dr)

    # 按总度排序
    result = result.sort_values("total_degree", ascending=False).reset_index(drop=True)

    print(f"\n✅ 节点中心性计算完成 ({len(result)} 个机场)")
    return result


def compute_network_stats(G):
    """
    计算 4 种网络整体指标，返回字典。

    Returns
    -------
    dict
        包含 density, clustering, avg_shortest_path, ngc
    """
    print("\n" + "=" * 60)
    print(" 计算网络整体指标")
    print("=" * 60)

    stats = {}

    print("[1/4] 网络密度...")
    stats["density"] = network_density(G)
    print(f"       Density = {stats['density']:.6f}")

    print("[2/4] 聚类系数...")
    stats["clustering_coefficient"] = clustering_coefficient(G)
    print(f"       Clustering = {stats['clustering_coefficient']:.6f}")

    print("[3/4] 平均最短路径...")
    stats["avg_shortest_path"] = average_shortest_path(G)
    print(f"       Avg Path = {stats['avg_shortest_path']:.4f}")

    print("[4/4] 巨型连通子图比例 (NGC)...")
    stats["ngc"] = giant_component_ratio(G)
    print(f"       NGC = {stats['ngc']:.4f}")

    # 附加基本信息
    stats["num_nodes"] = G.number_of_nodes()
    stats["num_edges"] = G.number_of_edges()

    print(f"\n✅ 网络指标计算完成 (N={stats['num_nodes']}, E={stats['num_edges']})")
    return stats
