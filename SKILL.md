---
name: nikke-pvp
description: NIKKE PVP 竞技场配队辅助 — 查询对局 / 记录对局。
category: gaming
---

# NIKKE PVP 竞技场配队辅助

## 职责

主 skill 只负责 **分派子技能** 与 **验证子技能的输出结果**。

## 子技能

| 子技能 | 职责 |
|---|---|
| `query` | 查询历史对局。详见 `sub-skills/query/SKILL.md`。 |
| `match-recorder` | 记录新对局 — 非结构化文本解析为结构化 TOML 条目。 |
| `alias_mapping` | 角色昵称解析。 |

## 路径配置

所有路径以 `config.toml` 为准。完整目录结构见 `STRUCTURE.md`。

## 分派流程

1. 根据用户请求匹配对应子技能（query / match-recorder / alias_mapping）。
2. 将子技能对应的 SKILL.md 内容加载到上下文中。
3. 提供必要的输入参数（数据路径、schema 路径等，参见 `config.toml`）。

## 验证

**validate_record（强制）**：`match_recorder` 写入 TOML 后必须执行。LLM 解析非结构化文本，字段遗漏、枚举值错误、ID 不递增均真实发生过，validate 是数据完整性的最后防线。
