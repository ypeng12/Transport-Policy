# -*- coding: utf-8 -*-
"""
run_pipeline.py — 命令行入口脚本
用法: python scripts/run_pipeline.py --config configs/config.yaml
"""

import argparse
import os
import sys

# 将项目根目录加入 sys.path，确保 src 包可以导入
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="航空货运网络复杂网络分析 (Air Cargo Complex Network Analysis)"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=os.path.join(PROJECT_ROOT, "configs", "config.yaml"),
        help="配置文件路径 (默认: configs/config.yaml)",
    )
    args = parser.parse_args()

    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(PROJECT_ROOT, config_path)

    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"配置文件: {config_path}")

    run_pipeline(config_path, project_root=PROJECT_ROOT)


if __name__ == "__main__":
    main()
