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
from .metrics import (
    compute_all_centralities, 
    compute_network_stats,
    analyze_small_world,
    generate_key_insights
)
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
    运行完整分析流水线 (v2 增强版)。
    """
    if project_root is None:
        project_root = os.getcwd()

    # ---- 加载配置 ----
    cfg = load_config(config_path)
    raw_path = os.path.join(project_root, cfg["data"]["raw_path"])
    output_dir = os.path.join(project_root, cfg["data"]["processed_dir"])
    meta_path = cfg["data"].get("metadata_path")
    if meta_path:
        meta_path = os.path.join(project_root, meta_path)

    class_cfg = cfg.get("classification", {})
    pr_params = cfg.get("pagerank", {})
    dr_params = cfg.get("domirank", {})
    rob_cfg = cfg.get("robustness", {})
    viz_cfg = cfg.get("visualization", {})

    print("\n" + "#" * 60)
    print("#  航空货运网络复杂网络分析 (v2)")
    print("#  Air Cargo Complex Network Analysis")
    print("#" * 60)

    # ======== Step 1: 数据加载与验证 ========
    print("\n📂 Step 1: 加载原始数据...")
    df = load_csv(raw_path)
    df = validate_dataframe(df)
    
    meta_df = None
    if meta_path and os.path.exists(meta_path):
        meta_df = load_csv(meta_path)
        print(f"   已加载机场元数据: {len(meta_df)} 行")

    # ======== Step 2: 预处理与建图 ========
    print("\n⚙️  Step 2: 数据预处理与建图...")
    edges = run_preprocess(df, meta_df=meta_df, time_group=None)
    save_csv(edges, os.path.join(output_dir, "aggregated_edges.csv"))
    
    G = build_directed_graph(edges, meta_df=meta_df)

    # ======== Step 4: 指标计算与分类 ========
    print("\n📊 Step 3: 指标计算与分类...")
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
        classification_params=class_cfg
    )
    save_csv(centrality_df, os.path.join(output_dir, "node_centralities.csv"))

    # ======== Step 5: 计算整体指标 & 小世界分析 ========
    print("\n📈 Step 4: 网络整体指标与特性分析...")
    net_stats = compute_network_stats(G)
    net_stats = analyze_small_world(G, net_stats)
    save_json(net_stats, os.path.join(output_dir, "network_stats.json"))

    # ======== Step 6: 鲁棒性模拟 ========
    print("\n🛡️  Step 5: 鲁棒性模拟...")
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
    print("\n🎨 Step 6: 生成可视化...")
    generate_all_plots(
        G, centrality_df, robustness_df,
        output_dir=output_dir,
        classification_cfg=class_cfg,
        top_n=viz_cfg.get("top_n", 15),
        dpi=viz_cfg.get("figure_dpi", 150),
    )

    # ======== Step 8: 结论生成 ========
    insights = generate_key_insights(centrality_df, net_stats)
    print("\n" + "*" * 40)
    print(" 研究结论 (Key Insights)")
    print("*" * 40)
    for line in insights:
        print(line)

    print("\n" + "#" * 60)
    print("#  ✅ 分析完成！所有结果保存在:")
    print(f"#     {output_dir}")
    print("#" * 60)

    return {
        "graph": G,
        "centrality": centrality_df,
        "network_stats": net_stats,
        "robustness": robustness_df,
        "insights": insights
    }
