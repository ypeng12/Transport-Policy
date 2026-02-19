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

# ====================================================================
#  高级分析 (Advanced Analysis & Classification)
# ====================================================================

def classify_hubs(centrality_df, major_threshold=0.6, regional_threshold=0.2):
    """
    机场等级分类: 核心枢纽 (Major) / 区域中心 (Regional) / 普通支线 (Feeder)
    评分逻辑: 70% 度中心性 + 30% DomiRank (反映全局与局部重要性)
    """
    df = centrality_df.copy()

    # 归一化输入
    def norm(s): return (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else s * 0

    score = 0.7 * norm(df["total_degree"]) + 0.3 * norm(df["domirank"])
    df["hub_score"] = score

    def get_class(s):
        if s >= major_threshold: return "Major Hub"
        if s >= regional_threshold: return "Regional Hub"
        return "Feeder"

    df["category"] = df["hub_score"].apply(get_class)
    print(f"[metrics] 机场分类完成: {df['category'].value_counts().to_dict()}")
    return df


def analyze_small_world(G, stats_dict):
    """
    分析网络的“小世界”特性。
    逻辑: 比较实际网络与等规模随机网络 (Erdos-Renyi) 的 L 和 C。
    小世界网络特征: C_actual >> C_random 且 L_actual ≈ L_random
    """
    n, e = stats_dict["num_nodes"], stats_dict["num_edges"]
    if n < 3: return stats_dict

    # 等规模随机图的理论值
    p = e / (n * (n - 1) / 2) if n > 1 else 0
    c_rand = p
    l_rand = np.log(n) / np.log(max(1.1, stats_dict["num_edges"] / n))

    c_actual = stats_dict["clustering_coefficient"]
    l_actual = stats_dict["avg_shortest_path"]

    stats_dict["small_world_ratio_c"] = c_actual / c_rand if c_rand > 0 else 0
    stats_dict["small_world_ratio_l"] = l_actual / l_rand if l_rand > 0 else 0

    is_small_world = (stats_dict["small_world_ratio_c"] > 3) and (stats_dict["small_world_ratio_l"] < 2)
    stats_dict["is_small_world"] = bool(is_small_world)

    print(f"[metrics] 小世界分析: C_ratio={stats_dict['small_world_ratio_c']:.2f}, "
          f"L_ratio={stats_dict['small_world_ratio_l']:.2f}, SmallWorld={is_small_world}")
    return stats_dict


def generate_key_insights(centrality_df, stats_dict):
    """
    自动生成定性研究结论 (Key Insights)
    """
    temp_df = centrality_df.sort_values("hub_score", ascending=False)
    top_hub = temp_df.iloc[0]["node"]
    top_domi = centrality_df.nlargest(1, "domirank").iloc[0]["node"]

    insights = []
    insights.append(f"1. 网络拓扑分析: 该网络规模为 {stats_dict['num_nodes']} 个节点，"
                    f"密度为 {stats_dict['density']:.4f}。")

    if stats_dict.get("is_small_world"):
        insights.append("2. 结构特性: 表现出显著的'小世界'特性，具备高效的货物中转能力。")
    else:
        insights.append("2. 结构特性: 网络连接相对稀疏，中转效率仍有提升空间。")

    insights.append(f"3. 核心枢纽: '{top_hub}' 是全网最关键的流量节点和关口。")

    if top_hub != top_domi:
        insights.append(f"4. 局部控制力: 值得关注的是 '{top_domi}' 展现出极高的 DomiRank (支配力)，"
                        f"在其所在区域具有极强的局部统治地位。")

    print(f"[metrics] 已生成 {len(insights)} 条关键结论")
    return insights


def compute_all_centralities(G, pagerank_params=None, domirank_params=None, classification_params=None):
    """
    计算所有 5 种节点中心性指标 + 自动分类等级。
    """
    if pagerank_params is None: pagerank_params = {}
    if domirank_params is None: domirank_params = {}
    if classification_params is None: classification_params = {}

    print("\n" + "=" * 60)
    print(" 计算节点中心性与分类")
    print("=" * 60)

    # ... 原有计算逻辑 ...
    # (由于 replace_file_content 规则，我在这里重新组装整个函数逻辑)

    # 1-5 中心性计算
    centrality_df = degree_centrality(G)
    bc = betweenness_centrality(G)
    cc = closeness_centrality(G)
    pr = pagerank(G, **pagerank_params)
    dr = domirank(G, **domirank_params)

    centrality_df["betweenness"] = centrality_df["node"].map(bc)
    centrality_df["closeness"] = centrality_df["node"].map(cc)
    centrality_df["pagerank"] = centrality_df["node"].map(pr)
    centrality_df["domirank"] = centrality_df["node"].map(dr)

    # 新增分类步骤
    centrality_df = classify_hubs(
        centrality_df,
        major_threshold=classification_params.get("major_hub_threshold", 0.6),
        regional_threshold=classification_params.get("regional_hub_threshold", 0.2)
    )

    centrality_df = centrality_df.sort_values("hub_score", ascending=False).reset_index(drop=True)
    return centrality_df


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
