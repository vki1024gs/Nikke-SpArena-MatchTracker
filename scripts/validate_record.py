#!/usr/bin/env python3
"""验证 matches.toml 最新条目是否符合 match_schema.toml 定义。

schema 是字段集合、类型、顺序的唯一权威来源。
"""
import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import load_config, validate_result


def load_schema():
    cfg = load_config()
    schema_path = ROOT / cfg["paths"]["match_schema"]
    with open(schema_path, "rb") as f:
        return tomllib.load(f)


def validate(matches_path: str):
    schema = load_schema()
    fields_def = schema["fields"]

    with open(matches_path, "rb") as f:
        matches = tomllib.loads(f.read().decode("utf-8"))["match"]

    if not matches:
        return ["matches.toml 为空"]

    last = matches[-1]
    issues = []

    # 1. 必填字段检查
    for fname, fdef in fields_def.items():
        if fdef.get("required") and fname not in last:
            issues.append(f"缺少必填字段: {fname}")

    # 2. 枚举值检查
    for fname, fdef in fields_def.items():
        if fname not in last:
            continue
        val = last[fname]
        if fdef.get("type") == "enum" and "enum_values" in fdef:
            allowed = fdef["enum_values"]
            if val not in allowed:
                issues.append(f"{fname} 值不合法: '{val}'（应为 {allowed}）")

    # 3. 数组长度检查
    for fname, fdef in fields_def.items():
        if fname not in last or fdef.get("type") != "array":
            continue
        val = last[fname]
        if not isinstance(val, list):
            issues.append(f"{fname} 类型错误: 期望 array, 得到 {type(val).__name__}")
            continue
        if "min_items" in fdef and len(val) < fdef["min_items"]:
            issues.append(f"{fname} 元素不足: {len(val)} < {fdef['min_items']}")
        if "max_items" in fdef and len(val) > fdef["max_items"]:
            issues.append(f"{fname} 元素过多: {len(val)} > {fdef['max_items']}")

    # 4. Map 键检查（defender_burst / attacker_burst）
    for fname, fdef in fields_def.items():
        if fname not in last or fdef.get("type") != "map":
            continue
        val = last[fname]
        if not isinstance(val, dict):
            issues.append(f"{fname} 类型错误: 期望 map, 得到 {type(val).__name__}")
            continue
        for key in fdef.get("keys", []):
            if key not in val:
                issues.append(f"{fname} 缺少键: {key}")

    # 5. 字符串模式检查（id）
    for fname, fdef in fields_def.items():
        if fname not in last or fdef.get("type") not in ("string", "text"):
            continue
        if "pattern" in fdef and not re.match(fdef["pattern"], str(last[fname])):
            issues.append(f"{fname} 不匹配模式: '{last[fname]}' (预期 {fdef['pattern']})")

    # 6. ID 递增检查
    if len(matches) >= 2:
        prev_id = int(str(matches[-2].get("id", "0")))
        curr_id = int(str(last.get("id", "0")))
        if curr_id <= prev_id:
            issues.append(f"id 未递增: {curr_id} <= {prev_id}")

    return issues


if __name__ == "__main__":
    cfg = load_config()
    default_matches = str(ROOT / cfg["paths"]["matches"])
    matches_path = sys.argv[1] if len(sys.argv) > 1 else default_matches
    issues = validate(matches_path)
    if not validate_result("record", issues):
        sys.exit(1)
    sys.exit(0)
