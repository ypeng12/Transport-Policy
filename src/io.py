# -*- coding: utf-8 -*-
"""
io.py — 数据读写工具
提供 CSV / JSON 的加载和保存功能，自动创建输出目录。
"""

import os
import json
import pandas as pd


def load_csv(path, **kwargs):
    """
    加载 CSV 文件为 DataFrame。

    Parameters
    ----------
    path : str
        CSV 文件路径
    **kwargs
        传递给 pd.read_csv 的额外参数

    Returns
    -------
    pd.DataFrame
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"数据文件不存在: {path}")
    print(f"[io] 加载数据: {path}")
    return pd.read_csv(path, **kwargs)


def save_csv(df, path, index=False):
    """保存 DataFrame 为 CSV"""
    _ensure_dir(path)
    df.to_csv(path, index=index, encoding="utf-8-sig")
    print(f"[io] 已保存 CSV: {path}")


def save_json(data, path, ensure_ascii=False):
    """保存字典为 JSON 文件"""
    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=ensure_ascii)
    print(f"[io] 已保存 JSON: {path}")


def _ensure_dir(filepath):
    """如果目录不存在则创建"""
    d = os.path.dirname(filepath)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
