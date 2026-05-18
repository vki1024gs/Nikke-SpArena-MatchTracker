# 输出格式常量对照

当前 `query_output.py` 中的分隔符常量（左右各 8 个━，标题后跟空行）：

```python
SEP_QUERY = "**━━━━━━━━ 查询结果 ━━━━━━━━**"
SEP_CHARGE = "**━━━━━━━━ 充能计算 ━━━━━━━━**"
SEP_BURST = "**💥 爆裂链 💥**"
SEP_TABLE = "**📊 充能明细 📊**"
SEP_HISTORY = "**━━━━━━━━ 历史对局 ━━━━━━━━**"
SEP_ANALYSIS = "**━━━━━━━━ 队伍分析 ━━━━━━━━**"
```

## 历史对局术语汉化（translate_history_terms）

| 原文 | 译文 |
|------|------|
| `margin: decisive` | `完胜` |
| `margin: close` | `险胜` |
| `notes:` | `备注:` |

## 历史对局格式（match_finder.py format_lite）

```
匹配度: XX.X分 (X人重叠，爆裂XX相同)

[id=XXXX]

防守方: 角色A, 角色B, 角色C, 角色D, 角色E

进攻方: 角色A, 角色B, 角色C, 角色D, 角色E

胜负: 防守方胜 | 完胜

备注: xxx
```

各字段以空行分隔，不缩进，队伍名逗号分隔（非 Python list repr）。

## 验证命令

```bash
grep -n 'SEP_' sub-skills/query/query_output.py | grep -v 'def \|"""'
```

检查项：
1. 左右━数量相等（各 8 个）
2. 标题后跟空行（Markdown 渲染换行）
3. `translate_history_terms` 包含 margin/notes 映射

## 变更记录

- 2026-05: SEP_ANALYSIS 左 9 右 8━不对称 → 8:8
- 2026-05: SEP_ANALYSIS 标题"分析"→"队伍分析"，添加空行
- 2026-05: SEP_HISTORY 后添加空行
- 2026-05: SEP_QUERY 后添加空行
- 2026-05: match_finder format_lite 队伍列表改用逗号分隔（非 list repr）
- 2026-05: 添加 translate_history_terms（margin/notes 汉化）
