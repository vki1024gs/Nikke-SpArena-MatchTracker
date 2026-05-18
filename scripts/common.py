#!/usr/bin/env python3
"""公共模块 — 配置加载、数据读取、工具函数。所有脚本 import 此模块。"""
import sys
from pathlib import Path

# Python < 3.11 兼容：3.11+ 内置 tomllib，之前需要 pip install tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# scripts/common.py — 父目录即项目根（SKILL.md 同级）
ROOT = Path(__file__).resolve().parent.parent


def load_config():
    with open(ROOT / "config.toml", "rb") as f:
        return tomllib.load(f)


def load_toml(name):
    """根据 config 中的路径名加载 toml 文件。"""
    cfg = load_config()
    rel = cfg["paths"][name]
    with open(ROOT / rel, "rb") as f:
        return tomllib.load(f)


def chara_map():
    data = load_toml("chara_list")
    return {c["name"]: c["burst"] for c in data["characters"]}


def charge_map():
    data = load_toml("charge_speed")
    return {c["name"]: c for c in data["charge"]}


def alias_map():
    data = load_toml("alias_mapping")
    result = {}
    for fullname, aliases in data.items():
        for alias in aliases:
            result.setdefault(alias.lower(), []).append(fullname)
    return result


def fullnames():
    data = load_toml("chara_list")
    return [c["name"] for c in data["characters"]]


def phases():
    return load_config()["charge"]["phases"]


def validate_result(label, issues):
    """统一 validate 脚本的 stderr 输出格式。"""
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}", file=sys.stderr)
        print(f"[VALIDATE] {label}: {len(issues)} issue(s) found", file=sys.stderr)
        return False
    else:
        print(f"[VALIDATE] {label}: passed", file=sys.stderr)
        return True
