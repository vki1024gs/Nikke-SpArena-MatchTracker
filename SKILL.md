---
name: nikke-pvp
description: NIKKE PVP 竞技场配队辅助 — 查询对局 / 记录对局。
category: gaming
---

# NIKKE PVP 竞技场配队辅助

## 职责

主 skill 只负责 **分派子技能** 与 **验证子技能的输出结果**。具体实现细节见 `PITFALLS.md`。

## 子技能

| 子技能 | 职责 |
|---|---|
| `query` | 查询历史对局 — LLM 仅写 70 字分析，Python（`query_output.py`）编排全部数据板块。三步调用：先跑脚本获取 `[ANALYSIS_CONTEXT]`，LLM 生成分析后 `--assemble` 组装最终结果。详见 `sub-skills/query/SKILL.md`。 |
| `match-recorder` | 记录新对局 — 非结构化文本解析为结构化 TOML 条目。 |
| `alias_mapping` | 角色昵称解析。 |
| `match-maintain` | 数据表维护。 |

## 编排脚本

- `sub-skills/query/query_output.py` — 查询输出编排：运行 4 个子脚本，拼接 4 个数据板块，仅将 `[ANALYSIS_CONTEXT]` 留给 LLM。

## 路径配置

所有路径以 `config.toml` 为准。完整目录结构见 `STRUCTURE.md`。

## 分派流程

1. 根据用户请求匹配对应子技能（query / match-recorder / alias_mapping / match-maintain）。
2. 将子技能对应的 SKILL.md 内容加载到上下文中。
3. 提供必要的输入参数（数据路径、schema 路径等，参见 `config.toml`）。

## 验证

**validate_record（强制）**：`match_recorder` 写入 TOML 后必须执行。LLM 解析非结构化文本，字段遗漏、枚举值错误、ID 不递增均真实发生过，validate 是数据完整性的最后防线。

**query 流程的防护机制**：`query_output.py` 是纯 Python 脚本，格式确定性 100%。真正的防护已内置于脚本层：`calc_team_charge.py` 和 `match_finder.py` 带 `NIKKE_QUERY_SUB=1` env var 守卫，LLM 无法跳过 `query_output.py` 直接调用它们（会 `sys.exit(1)`）。因此 query 流程**不需要** LLM 手动执行 validate_query。若需要调试子脚本，加 `--debug` 绕过守卫。


## 项目约定

- **归档目录**：`*.archive/` 文件夹用于存放废弃的旧文件，已在 `.gitignore` 中忽略。命名统一用 `.archive` 前缀。
- **Schema 唯一入口**：`sub-skills/match_recorder/schema/match_schema.toml`，所有项目通过 `config.toml` 的 `paths.match_schema` 引用。


## 维护日志

- **[2026-05-11] validate_record.py 修复**：脚本中 `tomllib.load(f.read()...)` 报错（AttributeError: 'str' object has no attribute 'read'），已修正为 `tomllib.loads(f.read()...)`。

## Pitfall 参考

具体脚本行为、TOML 序列化细节、爆裂链计算约束、Schema 变更全链路步骤等，见 [PITFALLS.md](PITFALLS.md)。

---

## 合并自 nikke-pjjc（2026-05-13 归档合并）

以下为原 `nikke-pjjc` skill 中的独特规则与陷阱，已并入本 skill。

### 输出风格：禁止机械式报告
- **禁止**说"根据 Workflow X"、"信号核查："、"分析如下"等元描述。
- **禁止负面报告**：队伍没有某个信号/机制时，**什么都不说**。不要输出"无"、"未发现"。
- 建议部分必须是**一段自然的话**，融入输出末尾。

### TOML 格式陷阱
- **带 `+` 的充能值**：`charge_speed_pvp.toml` 中 `value = 28.4+` 在 TOML 内联表中非法，必须加引号：`value = "28.4+"`。
- **充能表列为 2RL/50SMG/3RL**：50SMG=196帧，无 31AR 列。
- **容器无 unzip**：用 Python `zipfile` 模块解压。

### 别名冲突处理
- `诺` 同时映射到 诺雅/诺伊斯：单个`诺`→优先诺雅，`诺诺`连续→第一个诺伊斯第二个诺雅。

### 写脚本前先问规则
- 不要假设充能计算逻辑、公式、输出格式。用户有明确的游戏机制认知，必须先确认再写。
- 数据替换后必须抽查验证：用 CSV 数据重建 TOML 后，挑几个角色去 CSV 里对照数值。

---

## 合并自 nikke-pjjc-log（2026-05-13 归档合并）

以下为原 `nikke-pjjc-log` skill 中的独特规则与陷阱。

### 输出格式硬规则
- **标题格式**：必须使用 `**━━━━━━━━ 标题 ━━━━━━━━**`（左右各 8 个━）。**禁止**使用 Emoji、`===` 下划线或普通 `###` 标题。
- **充能明细表表头**：只写角色名，禁止加 `(Hits)`。Hits 信息只出现在数据格内：`[值]% (hX)`。
- **充能计算必须是完整 5 人**：少人充能相加结果无效，不得计算。
- **若任意阶段 ≥100%，则立即停止后续计算**（不再算 50SMG/3RL）。

### 爆裂阶段判定
- 双爆裂 2 ≠ 能开 2 次爆裂。开爆裂的人由 `burst_chain_speed.py` 输出决定，禁止自行判断。

### suggest 子技能 — 机制核查
- 只查脚本爆裂链中的 3 人。机制数据直接来自 `chara_list_pvp.toml` 的 `mechanics` 字段（格式为"机制：解释"）。
- 核查结果融入为**一段自然的话**，不要列表，不要标题。若无机制，则不输出该段落。
- 详见 [references/suggest.md](references/suggest.md)。

## 输出格式规范 (Query)

4 个数据板块必须原样输出，LLM **禁止压缩或摘要**：

1. **分隔符**：`**━━━━━━━━ 标题 ━━━━━━━━**`（左右各 8 个━），标题后必须空一行。
2. **队伍分析**：标题为 `队伍分析`（非"分析"），≤70 字。
3. **历史对局**：内部字段（匹配度/id/防守方/进攻方/胜负）之间以空行分隔，`[id=XXXX]` 独占一行。队伍名以逗号分隔，**禁止**使用 Python list repr (`['a', 'b']`)。
4. **术语汉化**：`margin: decisive`→`完胜`，`margin: close`→`险胜`，`notes:`→`备注:`。
5. **脚本职责**：`query_output.py` 负责拼接板块；`match_finder.py` 负责历史匹配。LLM 仅负责撰写"队伍分析"板块的 70 字文本并调用 `--assemble`。

## Query 子技能 Pitfalls (2026-05-11)

- **子脚本 env var 守卫**：`calc_team_charge.py` 和 `match_finder.py` 受 `NIKKE_QUERY_SUB=1` 环境变量保护，直接运行会拒绝执行。仅 `--debug` 可绕过。
- **match_finder.py 来源标签**：历史对局 `[id=XXXX]` 后附加 `[source]` 标签（如 `[论坛]`/`[自建]`），取自 matches.toml 的 `source` 字段。
- **禁止压缩脚本输出**：LLM 收到 `query_output.py --assemble` 结果后，必须**原样粘贴全部 4 个板块**（查询结果、充能计算、历史对局、分析），禁止将充能明细表压缩为摘要行、禁止删减角色列表、禁止用自然语言复述表格数据。脚本输出 = 最终输出。
- **板块标题**：`查询结果`、`充能计算`、`历史对局`、`队伍分析`（注意是 `队伍分析` 不是 `分析`）
- **分隔符严格对称**：4 个板块分隔符左右━数量必须一致（各 8 个）
- **历史对局缩进**：`run_match_finder` 对 body_lines 只做整体 `.strip()`，禁止逐行 `.strip()`，否则 `  进攻方:` 缩进丢失。
- **validate_record.py TOML 解析**：脚本使用 `tomllib.loads()` 解析文件内容（`tomllib.load()` 会导致 `AttributeError`）。
- **中英文分离**：`match_finder.py` 输出原始英文 key（`margin`, `notes`），汉化由 `query_output.py` 的 `translate_history_terms()` 处理。

## 输出格式审计

4 个板块分隔符（`SEP_*` 常量）必须严格对称、标题固定。详细对照表和已修复 bug 列表见子技能 `query` 的 `references/output_format.md`。用户曾指出 `SEP_ANALYSIS` 不对称、`SEP_CHARGE` 标题缺"队伍"前缀、历史对局缩进丢失等问题。
