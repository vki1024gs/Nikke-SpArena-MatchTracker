---
name: query
description: 查询历史对局 — LLM 仅负责撰写 70 字分析，其余全由 Python 编排。
---

# 查询对局

## 输入
用户提供队伍简写昵称串（如 `娜海emt帽lpls`）。

## 交互约束

**静默执行**：收到查询后直接完成三步调用流程。禁止播报执行进度、脚本调用过程或 `[ANALYSIS_CONTEXT]`；成功时仅输出 Step 3 的最终组装结果。仅在执行失败或需要用户补充信息时，简短说明原因。

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

## 内部子脚本

`query_output.py` 是唯一入口，内部依次调用以下脚本：

| 子脚本 | 职责 |
|---|---|
| `alias_mapping.py` | 将昵称串解析为 5 人全名。 |
| `calc_burst_chain.py` | 计算爆裂顺序并提取角色机制。 |
| `calc_team_charge.py` | 生成全队充能明细表。 |
| `match_finder.py` | 匹配历史对局并生成推荐结果。 |

## 执行约束

- 分析必须来自 `[ANALYSIS_CONTEXT]`，禁止自行读取角色数据或凭记忆补充。
- 分析文本传给 `--assemble` 时必须使用双引号包裹。
- 禁止跳过任一步骤，禁止直接调用内部子脚本。
- Step 3 的输出即最终答案，必须原样返回，不得精简、复述或重新格式化。
