#!/usr/bin/env python3
"""计算全队充能速度 — 只关注充能数据，不涉及爆裂链。"""
import os
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import charge_map, phases

CHARGE_PHASES = phases()


def resolve_charge(team_names, chmap):
    members = []
    for name in team_names:
        name = name.strip()
        ch = chmap.get(name)
        members.append({"name": name, "charge": ch})
    return members


def calc_cumulative_charge(members):
    results = []
    for label in CHARGE_PHASES:
        total = 0.0
        for m in members:
            ch = m.get("charge")
            if ch:
                v = ch.get(label, {}).get("value", 0)
                if isinstance(v, str):
                    v = float(v.rstrip("+"))
                total += v
        results.append((label, total))
        if total >= 100:
            break
    return results


def fmt_charge(ch):
    return {
        phase: f"{ch.get(phase, {}).get('value', '?')}% ({ch.get(phase, {}).get('hits', '?')}hits)"
        for phase in CHARGE_PHASES
    }


def print_team_speed(members, cumulative):
    char_headers = []
    for m in members:
        ch = m.get("charge")
        if ch:
            char_headers.append(f"{m['name']} ({ch.get('weapon', '?')})")
        else:
            char_headers.append(m['name'])
    headers = [""] + ["全队总计"] + char_headers

    rows = []
    for label in CHARGE_PHASES:
        row_parts = []
        total = 0.0
        for m in members:
            ch = m.get("charge")
            if ch:
                parts = fmt_charge(ch)
                val = ch.get(label, {}).get("value", 0)
                if isinstance(val, str):
                    val = float(val.rstrip("+"))
                total += val
                row_parts.append(parts[label])
            else:
                row_parts.append("-")

        # 阈值判定逻辑：2RL > 100% -> (过快)
        status = ""
        if label == "2RL" and total > 100:
            status = " (过快)"
        
        row = [f"**{label}**", f"{total:.1f}%{status}"] + row_parts
        rows.append(row)
        if total >= 100:
            break

    # 输出表格格式
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join("-" for _ in headers) + " |")
    for row in rows:
        print("| " + " | ".join(row) + " |")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("team", nargs="?", help="5人全名，逗号分隔")
    parser.add_argument("--debug", action="store_true", help="绕过 query_output.py 直接运行（调试用）")
    args = parser.parse_args()

    if not args.debug and os.environ.get("NIKKE_QUERY_SUB") != "1":
        print("[ERROR] 此脚本仅供 query_output.py 内部调用。调试请用 --debug，正常查询请用 query_output.py", file=sys.stderr)
        sys.exit(1)

    if not args.team:
        print("用法: python calc_team_charge.py '角色1,角色2,角色3,角色4,角色5'", file=sys.stderr)
        sys.exit(1)

    chmap = charge_map()
    team = [s.strip() for s in args.team.split(",")]

    members = resolve_charge(team, chmap)
    cumulative = calc_cumulative_charge(members)
    print_team_speed(members, cumulative)
