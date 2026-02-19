# -*- coding: utf-8 -*-
"""
schemas.py — 数据字段定义与验证
定义 CSV 必需列和可选列的常量，并提供 DataFrame 校验函数。
"""

# ===== 必需字段 =====
REQUIRED_COLS = ["date", "origin", "dest"]

# ===== 可选字段及其默认值 =====
OPTIONAL_DEFAULTS = {
    "flights": 1,
    "aircraft_type": "GENERIC",
    "payload_tonnes": 20.0,   # 默认载荷 (吨)
    "distance_km": 0.0,
}

# ===== 权重字段（预处理后生成）=====
WEIGHT_COL = "weight"


def validate_dataframe(df):
    """
    校验 DataFrame 是否包含必需列。
    缺失的可选列会自动填充默认值。

    Parameters
    ----------
    df : pd.DataFrame
        原始航班数据

    Returns
    -------
    pd.DataFrame
        校验并补全后的 DataFrame

    Raises
    ------
    ValueError
        缺少必需列时抛出
    """
    # 检查必需列
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必需列: {missing}")

    # 填充缺失的可选列
    for col, default in OPTIONAL_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
            print(f"  [schemas] 自动填充缺失列 '{col}' = {default}")

    # 类型强制转换
    df["date"] = df["date"].astype(str)
    df["origin"] = df["origin"].astype(str).str.strip().str.upper()
    df["dest"] = df["dest"].astype(str).str.strip().str.upper()
    df["flights"] = df["flights"].astype(float).astype(int)
    df["payload_tonnes"] = df["payload_tonnes"].astype(float)

    return df
