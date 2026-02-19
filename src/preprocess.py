# -*- coding: utf-8 -*-
"""
preprocess.py — 数据预处理与聚合
计算边权重 (weight = flights × payload_tonnes)，并按 OD 对聚合。
支持按月度或季度进行时间聚合。
"""

import pandas as pd
from .schemas import WEIGHT_COL


def compute_weight(df):
    """
    计算边权重: weight = flights × payload_tonnes
    权重反映 "运力" —— 航班频率 × 单次载荷
    """
    df[WEIGHT_COL] = df["flights"] * df["payload_tonnes"]
    print(f"[preprocess] 已计算权重列 '{WEIGHT_COL}' = flights × payload_tonnes")
    return df


def aggregate_edges(df, time_group=None):
    """
    按 (origin, dest) 聚合边，汇总权重和航班数。

    Parameters
    ----------
    df : pd.DataFrame
        含权重列的航班数据
    time_group : str or None
        时间聚合粒度:
        - None  : 不按时间分组，全部聚合
        - 'M'   : 按月聚合
        - 'Q'   : 按季度聚合

    Returns
    -------
    pd.DataFrame
        聚合后的边列表
    """
    group_cols = ["origin", "dest"]

    if time_group:
        # 将 date 转为 pandas Period 用于分组
        df = df.copy()
        df["period"] = pd.to_datetime(df["date"]).dt.to_period(time_group)
        group_cols = ["period"] + group_cols

    agg_dict = {
        WEIGHT_COL: "sum",
        "flights": "sum",
    }
    # 保留可选字段的均值（用于参考）
    if "distance_km" in df.columns:
        agg_dict["distance_km"] = "mean"

    result = df.groupby(group_cols, as_index=False).agg(agg_dict)

    if time_group and "period" in result.columns:
        result["period"] = result["period"].astype(str)

    n_edges = len(result)
    n_nodes = len(set(result["origin"]) | set(result["dest"]))
    print(f"[preprocess] 聚合完成: {n_nodes} 个节点, {n_edges} 条边")

    return result


def run_preprocess(df, meta_df=None, time_group=None):
    """
    预处理主流程: 计算权重 → 聚合边 (+ 验证元数据)
    """
    df = compute_weight(df)
    edges = aggregate_edges(df, time_group=time_group)

    if meta_df is not None:
        # 确保所有 OD 对的机场都在元数据中
        missing = set(edges["origin"]) | set(edges["dest"]) - set(meta_df["id"])
        if missing:
            print(f"  [preprocess] ⚠️ 警告: 部分机场缺少地理元数据: {missing}")

    return edges
