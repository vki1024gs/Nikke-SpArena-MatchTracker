"""从左到右贪婪最长匹配，将昵称串解析为5人全名。内置完整性验证。"""
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from common import alias_map as load_alias_map, fullnames

CLEAN_RE = re.compile(r'[^\w一-鿾：:]')


def clean_input(raw: str) -> str:
    """去除标点、空格等噪声。"""
    return CLEAN_RE.sub('', raw)


def build_alias_map():
    """通过 common.py 加载别名映射和角色全集。"""
    return load_alias_map(), set(fullnames())


def resolve(input_str, amap, fnames):
    """贪婪最长匹配。返回 (结果列表, 匹配日志, 警告列表)。"""
    input_str = input_str.lower()
    result = []
    seen = {}
    warns = []
    debug_log = []
    i = 0
    n = len(input_str)
    counter = {}
    while i < n:
        best = None
        best_len = 0
        best_source = ""
        for alias, candidates in amap.items():
            if input_str.startswith(alias, i) and len(alias) > best_len:
                best_len = len(alias)
                best_source = "alias"
                cnt = counter.get(alias, 0)
                best = candidates[cnt % len(candidates)]
        for name in fnames:
            if input_str.startswith(name.lower(), i) and len(name) > best_len:
                best = name
                best_len = len(name)
                best_source = "fullname"
        if best is None:
            warns.append(f"无法识别: '{input_str[i:]}', 停止解析")
            break
        if best in seen:
            warns.append(f"重复角色: {best}（位置 {seen[best]} 和 {i}）")
        else:
            seen[best] = i
        result.append(best)
        matched = input_str[i:i + best_len]
        debug_log.append({
            "pos": i,
            "matched": matched,
            "result": best,
            "source": best_source,
        })
        for alias, candidates in amap.items():
            if matched.startswith(alias) and best in candidates:
                counter[alias] = counter.get(alias, 0) + 1
                break
        i += best_len
    return result, debug_log, warns


def validate(names, fnames):
    """验证结果：恰好5人、无重复、均为有效角色。"""
    issues = []
    if len(names) != 5:
        issues.append(f"解析出 {len(names)} 人，需要恰好5人")
    if len(set(names)) != len(names):
        issues.append("存在重复角色")
    for n in names:
        if n not in fnames:
            issues.append(f"未知角色: {n}")
    return issues


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python alias_mapping.py <昵称串> [--json] [--debug]", file=sys.stderr)
        sys.exit(1)

    debug_mode = "--debug" in sys.argv
    json_mode = "--json" in sys.argv
    raw_input = sys.argv[1]
    cleaned = clean_input(raw_input)

    if cleaned != raw_input:
        print(f"[INFO] 输入已清洗: '{raw_input}' → '{cleaned}'", file=sys.stderr)

    amap, fnames = build_alias_map()
    names, debug_log, warns = resolve(cleaned, amap, fnames)

    # 输出警告（所有模式）
    for w in warns:
        print(f"[WARN] {w}", file=sys.stderr)

    # 验证
    issues = validate(names, fnames)

    if debug_mode:
        for entry in debug_log:
            print(f"[DEBUG] pos={entry['pos']} matched='{entry['matched']}' → {entry['result']} ({entry['source']})", file=sys.stderr)
        for issue in issues:
            print(f"[FAIL] {issue}", file=sys.stderr)

    # stdout 输出
    if json_mode:
        print(json.dumps({
            "input": cleaned,
            "names": names,
            "count": len(names),
            "complete": len(issues) == 0,
            "issues": issues,
        }, ensure_ascii=False))
    else:
        for n in names:
            print(n)

    # 有验证失败 → exit 1
    sys.exit(1 if issues else 0)
