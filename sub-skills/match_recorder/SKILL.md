---
name: match-recorder
description: 记录新对局 — 非结构化文本解析为结构化 TOML 条目，追加到 matches.toml。
---

# 记录对局

## 输入
用户提供非结构化对局文本（双方阵容昵称串、胜负、margin、备注等）。

## 流程

1. **提取信息**：从用户文本中解析双方阵容、胜负、margin、备注。若缺必填信息（result 或 source），**必须向用户确认**。
2. **默认规则**：未标明防守/进攻时，第一个队伍默认防守方，第二个默认进攻方。
3. **调用 match_recorder.py 生成并追加 TOML 条目**：脚本写入前根据 Schema 校验必填字段和枚举值。

```
python3 sub-skills/match_recorder/match_recorder.py "<防守方昵称串>" "<进攻方昵称串>" \
    --result defender_win|attacker_win \
    --source 论坛|自建|其他 \
    [--margin 值] \
    [--trust low|medium|high] \
    [--custom-def-tag "标签"] \
    [--notes "备注"] \
    [--dry-run]
```

4. **验证**：运行 `python3 scripts/validate_record.py data/matches.toml`。若 FAIL，根据报错手动修正。
5. **回复确认**：仅输出新增条目的全名和关键信息，不重复全表。

## 参数映射表（LLM 从用户文本中提取 → 转为 CLI 参数）

| 用户说法 | CLI 参数 | 说明 |
|----------|----------|------|
| 防守赢 / 攻守失败 / 守胜 | `--result defender_win` | 防守方胜利 |
| 进攻赢 / 攻击胜 / 防守输 | `--result attacker_win` | 进攻方胜利 |
| 来源论坛 | `--source 论坛` | 必填 |
| 来源自建 | `--source 自建` | 必填 |
| 来源其他 | `--source 其他` | 必填 |
| margin close / easy / 胶着 等 | `--margin 值` | 可选 |
| trust low / medium / high | `--trust 值` | 可选，默认 medium |
| 私密标签 | `--custom-def-tag "内容"` | 可选，默认空 |
| 备注说明 | `--notes "内容"` | 可选 |

## 必填字段
- `result`：必须由 LLM 从用户文本判断，无法推断时询问用户
- `source`：必须明确来源（论坛/自建/其他）

## Schema

字段定义以 `sub-skills/match_recorder/schema/match_schema.toml` 为唯一权威来源。

## Pitfalls
- **唯一数据源**：脚本默认读取 `config.toml` 的 `paths.matches`，并将新条目追加到该文件。
- **`--dry-run` 仅用于调试**：完整生成条目并输出到 stdout，但不写入任何文件。
