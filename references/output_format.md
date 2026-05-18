# 输出格式常量对照

4 个板块分隔符必须严格对称（左右各 8 个━），标题固定不变：

```python
SEP_QUERY = "**━━━━━━━━ 查询结果 ━━━━━━━━**"
SEP_CHARGE = "**━━━━━━━━ 充能计算 ━━━━━━━━**"
SEP_BURST = "**💥 爆裂链 💥**"
SEP_TABLE = "**📊 充能明细 📊**"
SEP_HISTORY = "**━━━━━━━━ 历史对局 ━━━━━━━━**"
SEP_ANALYSIS = "**━━━━━━━━ 队伍分析 ━━━━━━━━**"
```

## 验证命令

```bash
grep -n 'SEP_' sub-skills/query/query_output.py | grep -v 'def \|"""'
```

检查项：
1. 左右━数量相等（各 8 个）
2. `run_match_finder` 中 body_lines 不逐行 strip()
3. `format_lite` 队伍列表用 `', '.join()` 输出逗号分隔文本，非 Python list repr
4. `[id=XXXX]` 后附加 `[source]` 标签（`论坛`/`自建`），无值时不输出

## 已修复的 bug

- [2026-05] SEP_ANALYSIS 左 9 右 8━不对称 → 修正为 8:8
- [2026-05] run_match_finder 中 body_lines 逐行 strip() 吃掉缩进 → 改为 `"\n".join(body_lines).strip()`
- [2026-05] format_lite 队伍列表输出 Python repr → 改为 `', '.join(defender)`
- [2026-05] format_lite `[id=XXXX]` 追加 `[source]` 标签（论坛/自建）
- [2026-05] query 子脚本加 `NIKKE_QUERY_SUB` env var 守卫，禁止 LLM 直接调用
