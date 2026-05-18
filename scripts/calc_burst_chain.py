#!/usr/bin/env python3
"""计算爆裂链 — 只关注角色和爆裂阶段，不涉及充能数据。"""
import sys
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import chara_map, load_toml

# 各阶段爆裂链特殊规则
# type = "extra"：该角色触发后，追加寻找同/其他阶段的爆裂
B1_CHAIN_RULES = [
    {"type": "extra", "name": "阿妮斯：超级巨星", "extra_burst": "1"},
]

# burst = "X" 的角色可在多个阶段重复使用
BURSTX_CHARACTERS = [
    {"type": "universal", "name": "小红帽"},
]


def resolve_team(team_names, cmap):
    members = []
    for name in team_names:
        name = name.strip()
        burst = cmap.get(name)
        if burst is None:
            raise ValueError(f"找不到角色: {name}")
        members.append({"name": name, "burst": burst})
    return members


def calc_b1(members, used):
    """计算爆裂 1 链。burst="X" 的角色可参与 B1，但不能触发 extra1（超阿 1 转 1）。"""
    for i, m in enumerate(members):
        if i in used:
            continue
        if m["burst"] == "1" or m["burst"] == "X":
            entry = dict(m)
            entry["burst"] = "1"
            chain = [entry]
            # X 不消耗自身（可复用），且不触发 extra 规则
            if m["burst"] != "X":
                used.add(i)
                for rule in B1_CHAIN_RULES:
                    if rule["type"] == "extra" and m["name"] == rule["name"]:
                        for m2 in members[i + 1:]:
                            if m2["burst"] == rule["extra_burst"]:
                                chain.append(m2)
                                break
            return chain
    return [{"name": "无", "burst": "1"}]


def calc_b2(members, used):
    for i, m in enumerate(members):
        if i in used:
            continue
        if m["burst"] == "2" or m["burst"] == "X":
            entry = dict(m)
            entry["burst"] = "2"
            if m["burst"] != "X":
                used.add(i)
            return [entry]
    return [{"name": "无", "burst": "2"}]


def calc_b3(members, used):
    for i, m in enumerate(members):
        if i in used:
            continue
        if m["burst"] == "3" or m["burst"] == "X":
            entry = dict(m)
            entry["burst"] = "3"
            if m["burst"] != "X":
                used.add(i)
            return [entry]
    return [{"name": "无", "burst": "3"}]


def calc_burst_chain(members):
    chain = []
    used = set()
    chain.extend(calc_b1(members, used))
    chain.extend(calc_b2(members, used))
    chain.extend(calc_b3(members, used))
    return chain


def print_burst_chain(chain):
    for m in chain:
        if m["name"] == "无":
            print(f"爆裂 {m['burst']}: 无")
        else:
            print(f"爆裂 {m['burst']}: {m['name']}")


def print_meta(team_names):
    """提取队伍角色机制与备注，供 LLM 参考，避免其读取全量 toml。"""
    chara_data = load_toml("chara_list")
    chara_map_full = {c["name"]: c for c in chara_data.get("characters", [])}
    
    for name in team_names:
        entry = chara_map_full.get(name, {})
        mech = ", ".join(entry.get("mechanics", []))
        notes = entry.get("notes", "")
        
        mech_str = f"[{mech}] " if mech else ""
        
        if mech or notes:
            print(f"[META] {name}: {mech_str}{notes[:50]}...")
        else:
            print(f"[META] {name}: 无特殊机制")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python calc_burst_chain.py '角色1,角色2,角色3,角色4,角色5'", file=sys.stderr)
        sys.exit(1)

    cmap = chara_map()
    if len(sys.argv) > 2:
        team = [s.strip() for s in sys.argv[1:]]
    else:
        team = [s.strip() for s in sys.argv[1].split(",")]

    members = resolve_team(team, cmap)
    chain = calc_burst_chain(members)
    print_burst_chain(chain)
    print_meta(team)
