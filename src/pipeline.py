# -*- coding: utf-8 -*-
"""
pipeline.py — 端到端分析流水线
串联: 数据加载 → 预处理 → 建图 → 指标计算 → 鲁棒性模拟 → 可视化 → 保存结果
"""

import os
import yaml

from .io import load_csv, save_csv, save_json
from .schemas import validate_dataframe
from .preprocess import run_preprocess
from .build_graph import build_directed_graph
from .metrics import compute_all_centralities, compute_network_stats
from .robustness import run_robustness
from .viz import generate_all_plots


def load_config(config_path):
    """加载 YAML 配置文件"""
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    print(f"[pipeline] 已加载配置: {config_path}")
    return cfg


def run_pipeline(config_path, project_root=None):
    """
    运行完整分析流水线。

    Parameters
    ----------
    config_path : str
        YAML 配置文件路径
    project_root : str, optional
        项目根目录，用于拼接相对路径。默认为当前工作目录。
    """
    if project_root is None:
        project_root = os.getcwd()

    # ---- 加载配置 ----
    cfg = load_config(config_path)
    raw_path = os.path.join(project_root, cfg["data"]["raw_path"])
    output_dir = os.path.join(project_root, cfg["data"]["processed_dir"])

    pr_params = cfg.get("pagerank", {})
    dr_params = cfg.get("domirank", {})
    rob_cfg = cfg.get("robustness", {})
    viz_cfg = cfg.get("visualization", {})

    print("\n" + "#" * 60)
    print("#  航空货运网络复杂网络分析")
    print("#  Air Cargo Complex Network Analysis")
    print("#" * 60)

    # ======== Step 1: 数据加载与验证 ========
    print("\n📂 Step 1: 加载原始数据...")
    df = load_csv(raw_path)
    df = validate_dataframe(df)
    print(f"   原始数据: {len(df)} 行, {df['origin'].nunique() + df['dest'].nunique()} 个涉及机场代码")

    # ======== Step 2: 预处理与聚合 ========
    print("\n⚙️  Step 2: 数据预处理...")
    edges = run_preprocess(df, time_group=None)  # 全时段聚合
    save_csv(edges, os.path.join(output_dir, "aggregated_edges.csv"))

    # ======== Step 3: 构建有向加权图 ========
    print("\n🔗 Step 3: 构建有向加权图...")
    G = build_directed_graph(edges)

    # ======== Step 4: 计算节点中心性 ========
    print("\n📊 Step 4: 计算节点中心性...")
    pagerank_params = {
        "alpha": pr_params.get("alpha", 0.85),
        "max_iter": pr_params.get("max_iter", 100),
        "tol": pr_params.get("tol", 1e-6),
    }
    domirank_params = {
        "sigma": dr_params.get("sigma", None),
        "theta": dr_params.get("theta", 1.0),
        "beta": dr_params.get("beta", 1.0),
        "max_iter": dr_params.get("max_iter", 500),
        "tol": dr_params.get("tol", 1e-6),
    }

    centrality_df = compute_all_centralities(
        G,
        pagerank_params=pagerank_params,
        domirank_params=domirank_params,
    )
    save_csv(centrality_df, os.path.join(output_dir, "node_centralities.csv"))

    # 打印 Top-5 概览
    print("\n📋 Top-5 机场 (按总度):")
    print(centrality_df.head(5).to_string(index=False))

    # ======== Step 5: 计算网络整体指标 ========
    print("\n📈 Step 5: 计算网络整体指标...")
    net_stats = compute_network_stats(G)
    save_json(net_stats, os.path.join(output_dir, "network_stats.json"))

    # ======== Step 6: 鲁棒性模拟 ========
    print("\n🛡️  Step 6: 鲁棒性模拟...")
    strategies = rob_cfg.get("strategies", ["degree", "betweenness", "pagerank", "random"])
    random_runs = rob_cfg.get("random_runs", 10)

    robustness_df = run_robustness(
        G,
        strategies=strategies,
        random_runs=random_runs,
        domirank_params=domirank_params,
    )
    save_csv(robustness_df, os.path.join(output_dir, "robustness_results.csv"))

    # ======== Step 7: 可视化 ========
    print("\n🎨 Step 7: 生成可视化...")
    top_n = viz_cfg.get("top_n", 15)
    dpi = viz_cfg.get("figure_dpi", 150)

    generate_all_plots(
        G, centrality_df, robustness_df,
        output_dir=output_dir,
        top_n=top_n,
        dpi=dpi,
    )

    # ======== 完成 ========
    print("\n" + "#" * 60)
    print("#  ✅ 分析完成！所有结果保存在:")
    print(f"#     {output_dir}")
    print("#" * 60)

    return {
        "graph": G,
        "centrality": centrality_df,
        "network_stats": net_stats,
        "robustness": robustness_df,
    }
