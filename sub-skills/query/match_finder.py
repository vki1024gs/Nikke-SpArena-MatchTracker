#!/usr/bin/env python3
"""匹配历史对局 — 根据队伍重叠度和爆裂链相似度打分排序。"""
import os
import sys
from pathlib import Path

# 项目根目录（sub-skills/query/ → 上三级到根）
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import load_config, chara_map

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def calc_burst_chain_for_team(team_names, cmap):
    """简化版爆裂链计算，返回 [b1_name, b2_name, b3_name]。"""
    # 复用 calc_burst_chain 的逻辑
    members = []
    for name in team_names:
        name = name.strip()
        burst = cmap.get(name)
        if burst is None:
            continue
        members.append({"name": name, "burst": burst})

    # B1_CHAIN_RULES
    B1_RULES = [
        {"type": "extra", "name": "阿妮斯：超级巨星", "extra_burst": "1"},
    ]

    chain = []
    used = set()

    # B1
    for i, m in enumerate(members):
        if i in used:
            continue
        if m["burst"] == "1" or m["burst"] == "X":
            chain.append(m["name"])
            if m["burst"] != "X":
                used.add(i)
                for rule in B1_RULES:
                    if rule["type"] == "extra" and m["name"] == rule["name"]:
                        for m2 in members[i + 1:]:
                            if m2["burst"] == rule["extra_burst"]:
                                chain.append(m2["name"])
                                break
            break
    else:
        chain.append("无")

    # B2
    for i, m in enumerate(members):
        if i in used:
            continue
        if m["burst"] == "2" or m["burst"] == "X":
            chain.append(m["name"])
            if m["burst"] != "X":
                used.add(i)
            break
    else:
        chain.append("无")

    # B3
    for i, m in enumerate(members):
        if i in used:
            continue
        if m["burst"] == "3" or m["burst"] == "X":
            chain.append(m["name"])
            if m["burst"] != "X":
                used.add(i)
            break
    else:
        chain.append("无")

    return chain


def calc_order_similarity(team_a, team_b):
    """计算顺序相似度：顺序完全相同返回 1.0，否则按位置匹配比例。"""
    if len(team_a) != len(team_b):
        return 0.0
    matches = sum(1 for a, b in zip(team_a, team_b) if a == b)
    return matches / len(team_a)


def calc_chain_overlap(chain_a, chain_b):
    """计算爆裂链重叠：返回 (b1_match, b2_match, b3_match) 的布尔元组。"""
    # 取前3个有效角色（排除"无"）
    def valid(c):
        return [x for x in c if x != "无"]

    va = valid(chain_a)
    vb = valid(chain_b)

    b1 = len(va) > 0 and len(vb) > 0 and va[0] == vb[0]
    b2 = len(va) > 1 and len(vb) > 1 and va[1] == vb[1]
    b3 = len(va) > 2 and len(vb) > 2 and va[2] == vb[2]

    return b1, b2, b3


def score_match(team_names, match_entry, cmap):
    """计算单条对局的匹配分数。返回 (总分, 人员数, 链匹配, 描述)。"""
    defender = match_entry.get("defender_team", [])

    team_set = set(team_names)
    def_set = set(defender)

    # 1. 人员重叠
    overlap = team_set & def_set
    overlap_count = len(overlap)
    overlap_ratio = overlap_count / 5

    # 2. 顺序相似度
    order_sim = calc_order_similarity(team_names, defender)

    # 3. 爆裂链相似度
    query_chain = calc_burst_chain_for_team(team_names, cmap)
    def_chain = calc_burst_chain_for_team(defender, cmap)
    b1, b2, b3 = calc_chain_overlap(query_chain, def_chain)
    chain_matches = sum([b1, b2, b3])

    # 4. 综合评分
    person_score = overlap_ratio * 60
    chain_score = (chain_matches / 3) * 30
    order_score = 10.0 if order_sim == 1.0 and overlap_count == 5 else 0

    total = person_score + chain_score + order_score

    # 5. 匹配情形描述
    desc_parts = []
    if overlap_count == 5:
        desc_parts.append("5人完全匹配")
        if order_sim == 1.0:
            desc_parts.append("顺序相同")
        else:
            desc_parts.append("顺序不同")
    else:
        desc_parts.append(f"{overlap_count}人重叠")

    chain_bits = ''.join('123'[i] for i in range(3) if [b1, b2, b3][i])
    if chain_bits == "123":
        chain_desc = "爆裂链完全相同"
    elif chain_bits:
        chain_desc = f"爆裂{chain_bits}相同"
    else:
        chain_desc = "爆裂链无匹配"
    desc_parts.append(chain_desc)

    desc = "，".join(desc_parts)

    return round(total, 1), overlap_count, chain_matches, desc


def find_matches(matches_path, team_names, min_score=50, top_n=100):
    """查找匹配的历史对局。"""
    cmap = chara_map()

    with open(matches_path, "rb") as f:
        data = tomllib.load(f)

    results = []
    for m in data.get("match", []):
        score, overlap, chain, desc = score_match(team_names, m, cmap)
        if score >= min_score:
            results.append({
                "score": score,
                "overlap": overlap,
                "chain_matches": chain,
                "desc": desc,
                "match": m,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def format_lite(r):
    """lite模式：防守方、进攻方、胜负关系、margin、notes。"""
    m = r["match"]
    mid = m.get("id", "?")
    defender = m.get("defender_team", [])
    attacker = m.get("attacker_team", [])
    result = m.get("result", "")
    margin = m.get("margin", "")
    notes = m.get("notes", "")

    result_label = "防守方胜" if result == "defender_win" else "进攻方胜"

    source = m.get("source", "")
    source_tag = f" [{source}]" if source else ""

    lines = []
    lines.append(f"匹配度: {r['score']}分 ({r['desc']})")
    lines.append("")
    lines.append(f"[id={mid}]{source_tag}")
    lines.append("")
    lines.append(f"防守方: {', '.join(defender)}")
    lines.append("")
    lines.append(f"进攻方: {', '.join(attacker)}")
    lines.append("")
    if margin and margin != "unknown":
        lines.append(f"胜负: {result_label} | margin: {margin}")
    else:
        lines.append(f"胜负: {result_label}")
    lines.append("")
    if notes:
        lines.append(f"notes: {notes}")
    return "\n".join(lines)


def format_full(r):
    """full模式：完整 TOML 原文。"""
    m = r["match"]
    mid = m.get("id", "?")

    lines = []
    lines.append(f"匹配度: {r['score']}分 ({r['desc']})")
    lines.append(f"[[match]]")
    for key, val in m.items():
        if isinstance(val, list):
            lines.append(f'{key} = {val}')
        elif isinstance(val, dict):
            # 结构化爆裂链 Map 处理
            lines.append(f"\n[match.{key}]")
            for k, v in val.items():
                lines.append(f'{k} = {v}')
        else:
            lines.append(f'{key} = "{val}"')
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="匹配历史对局")
    parser.add_argument("team", help="5人全名，逗号分隔")
    parser.add_argument("--full", action="store_true", help="输出完整 TOML match 原文（默认 lite 模式）")
    parser.add_argument("--debug", action="store_true", help="绕过 query_output.py 直接运行（调试用）")
    args = parser.parse_args()

    if not args.debug and os.environ.get("NIKKE_QUERY_SUB") != "1":
        print("[ERROR] 此脚本仅供 query_output.py 内部调用。调试请用 --debug，正常查询请用 query_output.py", file=sys.stderr)
        sys.exit(1)

    cfg = load_config()
    matches_path = ROOT / cfg["paths"]["matches"]

    team = [s.strip() for s in args.team.split(",")]
    results = find_matches(str(matches_path), team)

    # 0. Header: 统一输出匹配度信息
    if results:
        best = results[0]
        print(f"[HEADER] 匹配度: {best['score']}分 ({best['desc']})")
    else:
        print("[HEADER] 匹配度: 无匹配记录")

    # 1. 相似防守队（仅当匹配度非 100% 时显示）
    if results and results[0]["score"] < 100:
        best_def = results[0]["match"].get("defender_team", [])
        print(f"[SIMILAR_DEF] 相似防守队: {', '.join(best_def)}")

    # 2. 推荐进攻队逻辑
    rec = None
    for r in results:
        m = r["match"]
        if m.get("result") == "attacker_win":
            rec = m.get("attacker_team", [])
            break

    if rec:
        print(f"[SUMMARY] 推荐进攻队: {', '.join(rec)}")
    else:
        print("[SUMMARY] 推荐进攻队: 无历史胜绩参考")
    
    print("-" * 40)

    if not results:
        print("无匹配记录")
    else:
        # 按 result 分组，各自取 top
        attacker_wins = [r for r in results if r["match"].get("result") == "attacker_win"][:2]
        defender_wins = [r for r in results if r["match"].get("result") == "defender_win"][:1]
        selected = attacker_wins + defender_wins

        fmt = format_full if args.full else format_lite
        for r in selected:
            print(fmt(r))
            print()
