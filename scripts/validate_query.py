#!/usr/bin/env python3
"""检查查询输出是否符合格式规范。"""
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import validate_result


def validate(text: str):
    issues = []

    required_sections = ["查询结果", "充能计算", "爆裂链", "充能明细", "历史对局", "分析"]
    for name in required_sections:
        if name not in text:
            issues.append(f"缺少板块: {name}")

    # 标题格式：必须用加粗分隔符，禁止 Markdown 标题
    if re.search(r"^#{1,3}\s", text, re.MULTILINE):
        issues.append("使用了 Markdown 标题（# / ###），必须用 **━━━━━━━━ 标题 ━━━━━━━━** 分隔符")

    # 禁止 === 下划线
    if re.search(r"[=]{3,}", text):
        issues.append("禁止使用 === 下划线")

    return issues


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    issues = validate(text)
    if not validate_result("query", issues):
        sys.exit(1)
    sys.exit(0)
