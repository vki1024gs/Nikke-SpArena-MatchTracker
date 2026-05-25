---
name: query
description: 查询历史对局 — LLM 仅负责撰写 70 字分析，其余全由 Python 编排。
---

# 查询对局

## 输入
用户提供队伍简写（如 `娜海emt帽lpls`）。

### 三步调用流程

#### Step 1：运行编排脚本 → 获取完整数据 + [ANALYSIS_CONTEXT]
```bash
cd /opt/data/skills/nikke-pvp
python3 sub-skills/query/query_output.py "<昵称串>"
```

#### Step 2：LLM 阅读 [ANALYSIS_CONTEXT] → 生成 ≤70 字分析段落
从 `[ANALYSIS_CONTEXT]` 中提取信息，撰写严格一段话的防守方特点陈述。
- **优先级**：1.历史备注（notes） → 2.角色机制（META） → 3.充能速度
- **约束**：仅一段话、不换行、不列表、零教学词汇（禁止"注"、"然而"、"但是"）、中立陈述

#### Step 3：组装最终输出
```bash
python3 sub-skills/query/query_output.py "<昵称串>" --assemble "<分析文本>"
```

## query_output.py 内部子脚本说明

`query_output.py` 是**唯一入口**，内部通过 subprocess 调用 4 个子脚本，自动完成全部数据编排。LLM **无需也不应该**直接调用这些子脚本。

| 子脚本 | 职责 | 输入 | 输出（被 query_output.py 解析） |
|--------|------|------|------------------------------|
| `alias_mapping.py` | 昵称 → 5人全名 | 昵称串 + `--json` | JSON: `{names, complete, issues}` |
| `calc_burst_chain.py` | 爆裂顺序 + 角色机制 | 5人全名(逗号分隔) | `爆裂 N: 角色名` + `[META]` 行 |
| `calc_team_charge.py` | 全队充能明细表 | 5人全名(逗号分隔) | Markdown 表格（含阈值标注） |
| `match_finder.py` | 历史对局匹配评分 | 5人全名(逗号分隔) | `[HEADER]`/`[SIMILAR_DEF]`/`[SUMMARY]`/分隔线后详情 |

**内部组件说明**：`calc_team_charge.py` 和 `match_finder.py` 是 `query_output.py` 的专用内部组件。正常流程中**禁止直接调用**——脚本自带守卫，无 `NIKKE_QUERY_SUB=1` 环境变量时会直接 `sys.exit(1)`。仅故障排查时可加 `--debug` 绕过守卫。

**信任保证**：
- 所有子脚本的 stdout/stderr 已被 `query_output.py` 完整捕获和解析
- 分隔符、表格格式、字段提取全部由 Python 处理，无 LLM 格式化环节
- 名称解析失败时 `query_output.py` 会 `sys.exit(1)` 并在 stderr 输出原因
- `[ANALYSIS_CONTEXT]` 是机器生成的结构化上下文，直接引用即可，无需二次验证

## Pitfalls

- **[META] 来源唯一**：分析必须来自 `query_output.py` 输出的 `[ANALYSIS_CONTEXT]`，**禁止 LLM 自行读取 `characters_pvp.toml`**
- **充能数据不重复判断**：充能表中若有 `(过快)` 标注，原样引用即可，不要改写或额外解释
- **`--assemble` 参数需引号包裹**：分析文本含空格/标点时，必须用双引号包裹传入
- **禁止直接调用内部子脚本**：`calc_team_charge.py` 和 `match_finder.py` 是 `query_output.py` 的专用内部组件，自带 env var 守卫，直接运行会 `sys.exit(1)`。仅调试时可用 `--debug` 绕过。零散脚本的存在是为了排查故障，不是正常流程的入口。
- **板块标题固定**：`查询结果`、`充能计算`、`历史对局`、`队伍分析`。标题变更需同步更新 `SEP_*` 常量
- **历史对局术语汉化（query_output.py `translate_history_terms`）**：`margin: decisive`→`完胜`，`margin: close`→`险胜`，`notes:`→`备注:`
- **禁止跳过三步流程**：用户查询必须严格执行 Step 1 → Step 2 → Step 3（`--assemble`），禁止省略任何步骤或凭记忆输出结果。（2026-05-12）
- **禁止 LLM 压缩数据板块**：充能明细表、历史对局等必须原样输出脚本结果，不得精简或复述。
