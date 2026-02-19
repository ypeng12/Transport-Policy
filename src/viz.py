# -*- coding: utf-8 -*-
"""
viz.py — 可视化模块
生成 6 种图表，用于论文展示:
  1. 网络拓扑图 (Network Graph)
  2. 中心性柱状图 (Centrality Bar Charts)
  3. 中心性热力图 (Centrality Heatmap)
  4. 鲁棒性曲线 (Robustness Curves)
  5. 度分布图 (Degree Distribution, log-log)
  6. 中心性相关矩阵 (Centrality Correlation Matrix)
"""

import os
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")  # 非交互后端，防止弹窗问题
import matplotlib.pyplot as plt
import seaborn as sns

# 设置全局字体，确保中文显示
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 色彩方案 — 论文级配色
COLORS = {
    "degree": "#2196F3",
    "betweenness": "#FF9800",
    "closeness": "#4CAF50",
    "pagerank": "#E91E63",
    "domirank": "#9C27B0",
    "random": "#9E9E9E",
}


def _save_fig(fig, path, dpi=150):
    """保存图片并关闭"""
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  [viz] 已保存: {path}")


# ====================================================================
#  1. 网络拓扑图
# ====================================================================

def plot_network_graph(G, centrality_df, output_dir, dpi=150):
    """
    绘制网络拓扑图:
    - 节点大小 ∝ 总度
    - 节点颜色 ∝ PageRank
    - 边宽度 ∝ 权重
    """
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))

    # 布局: spring layout (Fruchterman-Reingold)
    pos = nx.spring_layout(G, k=2.5, iterations=50, seed=42, weight="weight")

    # 节点大小: 根据总度归一化
    degrees = dict(G.degree(weight="weight"))
    max_deg = max(degrees.values()) if degrees else 1
    node_sizes = [300 + 2500 * (degrees.get(n, 0) / max_deg) for n in G.nodes()]

    # 节点颜色: PageRank
    pr_map = dict(zip(centrality_df["node"], centrality_df["pagerank"]))
    node_colors = [pr_map.get(n, 0) for n in G.nodes()]

    # 边宽度: 归一化权重
    edge_weights = [d.get("weight", 1) for _, _, d in G.edges(data=True)]
    max_ew = max(edge_weights) if edge_weights else 1
    edge_widths = [0.3 + 3.0 * (w / max_ew) for w in edge_weights]

    # 绘制边
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        width=edge_widths,
        alpha=0.25,
        edge_color="#888888",
        arrows=True,
        arrowsize=8,
        connectionstyle="arc3,rad=0.06",
    )

    # 绘制节点
    nodes = nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        cmap=plt.cm.YlOrRd,
        edgecolors="#333333",
        linewidths=0.8,
        alpha=0.9,
    )

    # 标签
    nx.draw_networkx_labels(
        G, pos, ax=ax,
        font_size=8,
        font_weight="bold",
        font_color="#222222",
    )

    # 颜色条
    sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd,
                                norm=plt.Normalize(
                                    vmin=min(node_colors),
                                    vmax=max(node_colors)))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("PageRank", fontsize=11)

    ax.set_title("航空货运网络拓扑图\n(节点大小=加权度, 颜色=PageRank)",
                 fontsize=14, fontweight="bold")
    ax.axis("off")

    _save_fig(fig, os.path.join(output_dir, "network_graph.png"), dpi)


# ====================================================================
#  2. 中心性柱状图 (Top-N)
# ====================================================================

def plot_centrality_bars(centrality_df, output_dir, top_n=15, dpi=150):
    """
    为每种中心性指标绘制 Top-N 机场柱状图 (2×3 子图)
    """
    metrics_to_plot = [
        ("total_degree", "总度 (Total Degree)", COLORS["degree"]),
        ("in_degree", "入度 (In-Degree)", "#64B5F6"),
        ("out_degree", "出度 (Out-Degree)", "#1565C0"),
        ("betweenness", "中介中心性 (Betweenness)", COLORS["betweenness"]),
        ("closeness", "接近中心性 (Closeness)", COLORS["closeness"]),
        ("pagerank", "PageRank", COLORS["pagerank"]),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()

    for idx, (col, title, color) in enumerate(metrics_to_plot):
        ax = axes[idx]
        top = centrality_df.nlargest(top_n, col)
        ax.barh(top["node"][::-1], top[col][::-1], color=color, alpha=0.85,
                edgecolor="white", linewidth=0.5)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Score", fontsize=10)
        ax.tick_params(labelsize=9)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle(f"各中心性指标 Top-{top_n} 机场", fontsize=16, fontweight="bold", y=1.01)
    fig.tight_layout()
    _save_fig(fig, os.path.join(output_dir, "centrality_bars.png"), dpi)

    # 单独画 DomiRank
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    top = centrality_df.nlargest(top_n, "domirank")
    ax2.barh(top["node"][::-1], top["domirank"][::-1],
             color=COLORS["domirank"], alpha=0.85,
             edgecolor="white", linewidth=0.5)
    ax2.set_title(f"DomiRank Top-{top_n} 机场", fontsize=14, fontweight="bold")
    ax2.set_xlabel("DomiRank Score", fontsize=11)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    fig2.tight_layout()
    _save_fig(fig2, os.path.join(output_dir, "domirank_bars.png"), dpi)


# ====================================================================
#  3. 中心性热力图
# ====================================================================

def plot_centrality_heatmap(centrality_df, output_dir, dpi=150):
    """
    热力图: 所有机场 × 所有中心性指标（归一化后）
    """
    metric_cols = ["total_degree", "betweenness", "closeness", "pagerank", "domirank"]
    labels_cn = ["总度", "中介中心性", "接近中心性", "PageRank", "DomiRank"]

    df = centrality_df.set_index("node")[metric_cols].copy()

    # Min-Max 归一化，方便对比
    for col in metric_cols:
        cmin, cmax = df[col].min(), df[col].max()
        if cmax > cmin:
            df[col] = (df[col] - cmin) / (cmax - cmin)
        else:
            df[col] = 0.0

    df.columns = labels_cn

    fig, ax = plt.subplots(figsize=(10, max(8, len(df) * 0.4)))
    sns.heatmap(df, annot=True, fmt=".2f", cmap="YlOrRd",
                linewidths=0.5, linecolor="white",
                cbar_kws={"label": "归一化分值"},
                ax=ax)
    ax.set_title("各机场中心性指标热力图（归一化）", fontsize=14, fontweight="bold")
    ax.set_ylabel("")
    ax.tick_params(labelsize=9)
    fig.tight_layout()
    _save_fig(fig, os.path.join(output_dir, "centrality_heatmap.png"), dpi)


# ====================================================================
#  4. 鲁棒性曲线
# ====================================================================

def plot_robustness_curves(robustness_df, output_dir, dpi=150):
    """
    绘制 NGC vs 移除比例曲线
    每种攻击策略一条线
    """
    fig, ax = plt.subplots(figsize=(10, 7))

    strategies = robustness_df["strategy"].unique()

    for strat in strategies:
        sub = robustness_df[robustness_df["strategy"] == strat]
        color = COLORS.get(strat, "#333333")
        linestyle = "--" if strat == "random" else "-"
        marker = "" if strat == "random" else "o"
        ax.plot(sub["fraction_removed"], sub["ngc"],
                label=strat.capitalize(),
                color=color, linewidth=2, linestyle=linestyle,
                marker=marker, markersize=4, alpha=0.85)

    ax.set_xlabel("移除节点比例 (Fraction Removed)", fontsize=12)
    ax.set_ylabel("巨型连通子图比例 (NGC)", fontsize=12)
    ax.set_title("网络鲁棒性: 定向攻击 vs 随机攻击", fontsize=14, fontweight="bold")
    ax.legend(fontsize=10, framealpha=0.9)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    _save_fig(fig, os.path.join(output_dir, "robustness_curves.png"), dpi)


# ====================================================================
#  5. 度分布图 (Log-Log)
# ====================================================================

def plot_degree_distribution(G, output_dir, dpi=150):
    """
    度分布: log-log 图
    检验是否符合幂律分布 (scale-free network)
    """
    degrees = [d for _, d in G.degree(weight=None)]  # 无权度
    degree_counts = {}
    for d in degrees:
        degree_counts[d] = degree_counts.get(d, 0) + 1

    x = sorted(degree_counts.keys())
    y = [degree_counts[d] / len(degrees) for d in x]  # 概率

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 左图: 普通度分布
    axes[0].bar(x, y, color=COLORS["degree"], alpha=0.8, edgecolor="white")
    axes[0].set_xlabel("度 (Degree)", fontsize=11)
    axes[0].set_ylabel("概率 P(k)", fontsize=11)
    axes[0].set_title("度分布", fontsize=13, fontweight="bold")
    axes[0].spines["top"].set_visible(False)
    axes[0].spines["right"].set_visible(False)

    # 右图: Log-Log
    x_nz = [xi for xi, yi in zip(x, y) if xi > 0 and yi > 0]
    y_nz = [yi for xi, yi in zip(x, y) if xi > 0 and yi > 0]

    if x_nz and y_nz:
        axes[1].scatter(x_nz, y_nz, color=COLORS["degree"], alpha=0.8,
                        s=60, edgecolors="#333", linewidths=0.5)
        axes[1].set_xscale("log")
        axes[1].set_yscale("log")

    axes[1].set_xlabel("度 k (log)", fontsize=11)
    axes[1].set_ylabel("P(k) (log)", fontsize=11)
    axes[1].set_title("度分布 (Log-Log)", fontsize=13, fontweight="bold")
    axes[1].spines["top"].set_visible(False)
    axes[1].spines["right"].set_visible(False)

    fig.suptitle("网络度分布分析", fontsize=15, fontweight="bold", y=1.02)
    fig.tight_layout()
    _save_fig(fig, os.path.join(output_dir, "degree_distribution.png"), dpi)


# ====================================================================
#  6. 中心性相关矩阵
# ====================================================================

def plot_correlation_matrix(centrality_df, output_dir, dpi=150):
    """
    绘制各中心性指标之间的 Pearson 相关系数矩阵
    帮助理解不同指标之间的关系
    """
    metric_cols = ["total_degree", "betweenness", "closeness", "pagerank", "domirank"]
    labels_cn = ["总度", "中介中心性", "接近中心性", "PageRank", "DomiRank"]

    corr = centrality_df[metric_cols].corr()
    corr.index = labels_cn
    corr.columns = labels_cn

    fig, ax = plt.subplots(figsize=(8, 7))

    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    sns.heatmap(corr, annot=True, fmt=".3f",
                cmap="RdBu_r", center=0,
                vmin=-1, vmax=1,
                mask=mask,
                square=True,
                linewidths=1, linecolor="white",
                cbar_kws={"label": "Pearson 相关系数"},
                ax=ax)
    ax.set_title("中心性指标相关矩阵", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save_fig(fig, os.path.join(output_dir, "correlation_matrix.png"), dpi)


# ====================================================================
#  1. 网络拓扑图 (带地理坐标)
# ====================================================================

def plot_spatial_topology(G, centrality_df, output_dir, classification_cfg, dpi=150):
    """
    绘制空间拓扑图:
    - 节点位置使用真实的 Lat/Lng
    - 颜色区分 Major Hubs (绿色), Regional (紫色)
    - 边显示为航线弧线
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 12))

    # 获取坐标
    pos = {}
    for node, data in G.nodes(data=True):
        if data.get("lat") and data.get("lng"):
            pos[node] = (data["lng"], data["lat"]) # X=lng, Y=lat
        else:
            # 如果没坐标，使用布局生成一个远离的坐标
            pos[node] = (100, 20) 

    # 分类映射
    cat_map = dict(zip(centrality_df["node"], centrality_df["category"]))
    colors_cfg = classification_cfg.get("colors", {})
    
    node_colors = []
    for node in G.nodes():
        cat = cat_map.get(node, "Feeder")
        if cat == "Major Hub": node_colors.append(colors_cfg.get("major_hub", "#10B981"))
        elif cat == "Regional Hub": node_colors.append(colors_cfg.get("regional_hub", "#6366F1"))
        else: node_colors.append(colors_cfg.get("feeder", "#94A3B8"))

    # 绘制边
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        alpha=0.15,
        edge_color="#CBD5E1",
        width=1.0,
        arrows=True,
        arrowsize=10,
        connectionstyle="arc3,rad=0.1", # 弧线
    )

    # 绘制节点
    degrees = dict(G.degree(weight="weight"))
    max_deg = max(degrees.values()) if degrees else 1
    node_sizes = [200 + 1500 * (degrees.get(n, 0) / max_deg) for n in G.nodes()]

    nx.draw_networkx_nodes(
        G, pos, ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors="white",
        linewidths=1.5,
        alpha=0.9,
    )

    # 标签
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_weight="bold", font_color="#1E293B")

    # 图例
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Major Hubs',
               markerfacecolor=colors_cfg.get("major_hub", "#10B981"), markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Regional Hubs',
               markerfacecolor=colors_cfg.get("regional_hub", "#6366F1"), markersize=10),
        Line2D([0], [0], marker='o', color='w', label='Feeder Airports',
               markerfacecolor=colors_cfg.get("feeder", "#94A3B8"), markersize=10),
    ]
    ax.legend(handles=legend_elements, loc='lower left', frameon=True, fontsize=10)

    ax.set_title("航空货运网络空间拓扑图 (Spatial Topology Map)", fontsize=14, fontweight="bold")
    ax.set_facecolor("#F8FAFC")
    ax.grid(True, linestyle='--', alpha=0.3)
    
    _save_fig(fig, os.path.join(output_dir, "spatial_topology.png"), dpi)


def generate_all_plots(G, centrality_df, robustness_df, output_dir, classification_cfg=None, top_n=15, dpi=150):
    """
    生成所有可视化图表。
    """
    if classification_cfg is None: classification_cfg = {}
    
    print("\n" + "=" * 60)
    print(" 生成可视化图表")
    print("=" * 60)

    print("\n[0/7] 空间拓扑图 (Spatial Topology)...")
    plot_spatial_topology(G, centrality_df, output_dir, classification_cfg, dpi)

    print("[1/7] 网络概览图...")
    plot_network_graph(G, centrality_df, output_dir, dpi)

    print("[2/7] 中心性柱状图...")
    plot_centrality_bars(centrality_df, output_dir, top_n, dpi)

    print("[3/7] 中心性热力图...")
    plot_centrality_heatmap(centrality_df, output_dir, dpi)

    print("[4/7] 鲁棒性曲线...")
    plot_robustness_curves(robustness_df, output_dir, dpi)

    print("[5/7] 度分布图...")
    plot_degree_distribution(G, output_dir, dpi)

    print("[6/7] 相关矩阵...")
    plot_correlation_matrix(centrality_df, output_dir, dpi)

    print(f"\n✅ 所有图表已保存至 {output_dir}")
