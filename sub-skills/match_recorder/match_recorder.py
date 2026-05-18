"""记录对局 — 将双方阵容和爆裂链写入 TOML 格式的 match 条目。"""
import argparse
import sys
from pathlib import Path
from datetime import date

# 模块加载：alias_mapping 和 burst_chain_speed 在父目录的不同子目录下
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "sub-skills" / "alias_mapping"))
sys.path.insert(0, str(ROOT / "scripts"))

import alias_mapping
from common import load_config, chara_map
import calc_burst_chain as burst_logic

VALID_SOURCES = {"论坛", "自建", "其他"}
VALID_RESULTS = {"defender_win", "attacker_win"}


def get_next_id(matches_path: Path) -> int:
    """读取 matches.toml 最后一条 id，+1 返回。"""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib

    with open(matches_path, "rb") as f:
        matches = tomllib.loads(f.read().decode("utf-8")).get("match", [])
    if not matches:
        return 1
    return int(matches[-1]["id"]) + 1


def resolve_team(nickname_str: str) -> list[str]:
    """调用 alias_mapping 解析队伍全名，失败时 exit(1)。"""
    cleaned = alias_mapping.clean_input(nickname_str)
    amap, fnames = alias_mapping.build_alias_map(alias_mapping.TOML_PATH)
    names, _, warns = alias_mapping.resolve(cleaned, amap, fnames)

    for w in warns:
        print(f"[WARN] {w}", file=sys.stderr)

    issues = alias_mapping.validate(names, fnames)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}", file=sys.stderr)
        sys.exit(1)
    return names


def build_burst_map(team_names: list[str]) -> dict:
    """返回爆裂链的结构化 Map (结构化 Map 格式)。"""
    cmap = chara_map()
    members = burst_logic.resolve_team(team_names, cmap)
    chain = burst_logic.calc_burst_chain(members)

    result = {"B1": [], "B2": [], "B3": []}
    for m in chain:
        name = m["name"] if m["name"] != "无" else None
        if name:
            result[f"B{m['burst']}"].append(name)
    return result


def to_toml_array(items: list[str]) -> str:
    """将字符串列表格式化为 TOML 数组。"""
    import json
    return json.dumps(items, ensure_ascii=False)


def to_toml_table(key: str, data: dict) -> str:
    """将 Map 格式化为 TOML Table (TOML Table 格式)。"""
    lines = [f"\n[{key}]"]
    for k, v in data.items():
        lines.append(f'{k} = {to_toml_array(v)}')
    return "\n".join(lines)


def render_match(defender: list[str], attacker: list[str], *,
                 result: str, margin: str, source: str,
                 trust: str, custom_def_tag: str,
                 notes: str) -> str:
    """生成单个 match 条目的 TOML 文本（动态读取 schema）。"""
    cfg = load_config()
    matches_path = ROOT / cfg["paths"]["matches"]
    schema_path = ROOT / cfg["paths"]["match_schema"]

    # 读取 schema 字段定义，按 order 排序
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib
    with open(schema_path, "rb") as f:
        schema = tomllib.loads(f.read().decode("utf-8"))

    fields = schema.get("fields", {})
    sorted_fields = sorted(
        [(k, v) for k, v in fields.items()],
        key=lambda x: x[1].get("order", 999)
    )

    next_id = get_next_id(matches_path)
    def_burst = build_burst_map(defender)
    att_burst = build_burst_map(attacker)

    # 动态值映射（包含 burst）
    value_map = {
        "id": f"{next_id:04d}",
        "date": str(date.today()),
        "defender_team": defender,
        "attacker_team": attacker,
        "result": result,
        "margin": margin,
        "source": source,
        "trust": trust,
        "custom_def_tag": custom_def_tag,
        "notes": notes,
        "defender_burst": def_burst,
        "attacker_burst": att_burst,
    }

    def to_toml_value(val) -> str:
        if isinstance(val, list):
            return to_toml_array(val)
        if isinstance(val, dict):
            parts = [f"{k} = {to_toml_array(v)}" for k, v in val.items()]
            return "{" + ", ".join(parts) + "}"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        return f'"{val}"'

    lines = ["[[match]]"]
    for fname, fdef in sorted_fields:
        val = value_map.get(fname, fdef.get("default"))
        lines.append(f"{fname} = {to_toml_value(val)}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="记录对局")
    parser.add_argument("defender", help="防守方昵称串，逗号分隔")
    parser.add_argument("attacker", help="进攻方昵称串，逗号分隔")
    parser.add_argument("--result", default=None, help="必填: defender_win / attacker_win")
    parser.add_argument("--margin", default="unknown")
    parser.add_argument("--source", default=None, help="必填: 论坛 / 自建 / 其他")
    parser.add_argument("--trust", default="medium")
    parser.add_argument("--notes", default="")
    parser.add_argument("--custom-def-tag", default="", help="防守方私密标签")
    parser.add_argument("--output", help="输出文件路径（默认 stdout）")
    args = parser.parse_args()

    # 必填校验
    missing = []
    if not args.result:
        missing.append("result (defender_win / attacker_win)")
    if not args.source:
        missing.append("source (论坛 / 自建 / 其他)")
    if missing:
        for m in missing:
            print(f"[ERROR] {m} 是必填字段", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 解析防守方: {args.defender}", file=sys.stderr)
    defender = resolve_team(args.defender)
    print(f"[INFO] 解析进攻方: {args.attacker}", file=sys.stderr)
    attacker = resolve_team(args.attacker)

    entry = render_match(
        defender, attacker,
        result=args.result,
        margin=args.margin,
        source=args.source,
        trust=args.trust,
        custom_def_tag=args.custom_def_tag,
        notes=args.notes,
    )

    if args.output:
        with open(args.output, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"[INFO] 已追加到: {args.output}", file=sys.stderr)
    
    # 无论是否写入文件，始终输出内容到 stdout
    print(entry, end="")


if __name__ == "__main__":
    main()
