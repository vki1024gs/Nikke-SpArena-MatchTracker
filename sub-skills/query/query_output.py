#!/usr/bin/env python3
"""查询输出编排 — 纯 Python 拼接 4 个数据板块，仅将分析上下文留给 LLM 生成。

用法:
    python query_output.py <昵称串>          # 输出完整结果 + [ANALYSIS_CONTEXT]
    python query_output.py <昵称串> --assemble <分析文本>  # 填入分析，输出最终结果
"""
import sys
import re
import os
from pathlib import Path
from subprocess import run, PIPE

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import load_config


# ─── 分隔符常量 ───
SEP_QUERY = "**━━━━━━━━ 查询结果 ━━━━━━━━**"
SEP_CHARGE = "**━━━━━━━━ 充能计算 ━━━━━━━━**"
SEP_BURST = "**💥 爆裂链 💥**"
SEP_TABLE = "**📊 充能明细 📊**"
SEP_HISTORY = "**━━━━━━━━ 历史对局 ━━━━━━━━**"
SEP_ANALYSIS = "**━━━━━━━━ 队伍分析 ━━━━━━━━**"


def resolve_names(nickname_str: str) -> list[str]:
    """运行 alias_mapping，返回 5 人全名列表。"""
    script = ROOT / "sub-skills/alias_mapping/alias_mapping.py"
    r = run([sys.executable, str(script), nickname_str, "--json"],
            capture_output=True, text=True)
    import json
    data = json.loads(r.stdout)
    if not data.get("complete"):
        print(f"[ERROR] 名称解析失败: {data.get('issues', [])}", file=sys.stderr)
        sys.exit(1)
    return data["names"]


def run_burst_chain(names: list[str]) -> tuple[str, list[str]]:
    """运行 calc_burst_chain，返回 (爆裂链文本, [META 行列表])。"""
    script = ROOT / "scripts/calc_burst_chain.py"
    r = run([sys.executable, str(script), ",".join(names)],
            capture_output=True, text=True)
    lines = r.stdout.strip().split("\n")
    burst_lines = []
    meta_lines = []
    for line in lines:
        if line.startswith("[META]"):
            meta_lines.append(line)
        elif line.startswith("爆裂"):
            burst_lines.append(line)
    burst_text = "\n".join(
        f"- {line}" for line in burst_lines
    )
    return burst_text, meta_lines


def run_charge_table(names: list[str]) -> str:
    """运行 calc_team_charge，返回 Markdown 表格原文。"""
    script = ROOT / "scripts/calc_team_charge.py"
    r = run([sys.executable, str(script), ",".join(names)],
            capture_output=True, text=True,
            env={**__import__("os").environ, "NIKKE_QUERY_SUB": "1"})
    return r.stdout.strip()


def run_match_finder(names: list[str]) -> tuple[str, str, str, str]:
    """运行 match_finder，返回 (header_line, similar_def_line, summary_line, history_body)。"""
    script = ROOT / "sub-skills/query/match_finder.py"
    r = run([sys.executable, str(script), ",".join(names)],
            capture_output=True, text=True,
            env={**os.environ, "NIKKE_QUERY_SUB": "1"})
    lines = r.stdout.strip().split("\n")

    header = ""
    similar_def = ""
    summary = ""
    body_lines = []
    in_body = False

    for line in lines:
        if line.startswith("[HEADER]"):
            header = line.replace("[HEADER] ", "")
        elif line.startswith("[SIMILAR_DEF]"):
            similar_def = line.replace("[SIMILAR_DEF] ", "")
        elif line.startswith("[SUMMARY]"):
            summary = line.replace("[SUMMARY] ", "")
        elif line.startswith("-" * 40):
            in_body = True
        elif in_body:
            body_lines.append(line)

    history_body = "\n".join(body_lines).strip()
    return header, similar_def, summary, history_body


def parse_header(header: str) -> tuple[str, str]:
    """从 header 提取 (分数, 详情)。如 '匹配度: 78分 (4人重叠，爆裂链完全相同)'。"""
    m = re.match(r"匹配度:\s*([\d.]+)分\s*(.*)", header)
    if m:
        return m.group(1), m.group(2).strip("()")
    return "0", header


def build_query_section(header: str, similar_def: str, summary: str) -> str:
    """组装查询结果板块。"""
    score, desc = parse_header(header)
    lines = [SEP_QUERY, ""]
    lines.append(f"匹配度: {score}分 ({desc})")

    # 相似防守队：仅当匹配度 < 100
    if similar_def and score != "100":
        lines.append(similar_def)

    # 推荐进攻队
    lines.append(summary)
    return "\n".join(lines)


def build_charge_section(burst_text: str, charge_table: str) -> str:
    """组装充能计算板块。"""
    parts = [SEP_CHARGE, "", SEP_BURST, burst_text, "", SEP_TABLE, charge_table]
    return "\n".join(parts)


def translate_history_terms(body: str) -> str:
    """翻译历史对局中的英文术语为中文。"""
    body = body.replace("margin: decisive", "完胜")
    body = body.replace("margin: close", "险胜")
    body = body.replace("notes:", "备注:")
    return body


def build_history_section(body: str) -> str:
    """组装历史对局板块。"""
    if not body:
        body = "无匹配记录"
    body = translate_history_terms(body)
    return f"{SEP_HISTORY}\n\n{body}"


def build_analysis_context(meta_lines: list[str], history_body: str,
                           charge_table: str, score: str) -> str:
    """生成分析板块的上下文，供 LLM 撰写 70 字中性陈述。"""
    # 从充能表提取最快阶段的总计充能
    charge_summary = ""
    for line in charge_table.split("\n"):
        if line.startswith("| **"):
            parts = [p.strip() for p in line.strip("| ").split("|")]
            if len(parts) >= 2:
                phase = parts[0].strip("**")
                total = parts[1]
                charge_summary += f"{phase}: {total}; "

    # 从历史对局提取 notes
    notes = []
    for line in history_body.split("\n"):
        if line.strip().startswith("notes:"):
            notes.append(line.strip().replace("notes:", "").strip())

    lines = [
        "[ANALYSIS_CONTEXT]",
        "--- META 信息 ---",
    ]
    lines.extend(meta_lines)
    lines.append("--- 充能数据 ---")
    lines.append(charge_summary.rstrip("; "))
    if notes:
        lines.append("--- 历史备注 ---")
        lines.extend(notes)
    lines.append("--- 匹配度 ---")
    lines.append(f"{score}分")
    lines.append(
        "请根据以上信息生成严格一段话（≤70字），"
        "中性陈述该防守队伍特点，禁止教学词汇（注、然而、但是），"
        "优先引用备注和机制，其次充能速度。"
    )
    return "\n".join(lines)


def assemble_final(nickname_str: str, analysis_text: str = "") -> str:
    """完整流程：运行脚本 → 拼接板块 → 返回最终结果。"""
    names = resolve_names(nickname_str)
    print(f"[INFO] 解析阵容: {', '.join(names)}", file=sys.stderr)

    burst_text, meta_lines = run_burst_chain(names)
    charge_table = run_charge_table(names)
    header, similar_def, summary, history_body = run_match_finder(names)
    score, _ = parse_header(header)

    # 组装 4 个数据板块
    query_sec = build_query_section(header, similar_def, summary)
    charge_sec = build_charge_section(burst_text, charge_table)
    history_sec = build_history_section(history_body)

    sections = [query_sec, "", charge_sec, "", history_sec]

    if analysis_text:
        # 已有分析文本，直接拼接
        sections.append("")
        sections.append(f"{SEP_ANALYSIS}\n\n{analysis_text}")
    else:
        # 输出分析上下文供 LLM 撰写
        ctx = build_analysis_context(meta_lines, history_body, charge_table, score)
        sections.append("")
        sections.append(ctx)

    return "\n".join(sections)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python query_output.py <昵称串>", file=sys.stderr)
        print("      python query_output.py <昵称串> --assemble <分析文本>", file=sys.stderr)
        sys.exit(1)

    nickname = sys.argv[1]

    if "--assemble" in sys.argv:
        idx = sys.argv.index("--assemble")
        if idx + 1 < len(sys.argv):
            analysis = sys.argv[idx + 1]
        else:
            print("[ERROR] --assemble 需要分析文本参数", file=sys.stderr)
            sys.exit(1)
    else:
        analysis = ""

    result = assemble_final(nickname, analysis)
    print(result)
