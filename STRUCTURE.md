# NIKKE PVP 配队助手 — 项目结构

## 概览

基于 Claude 技能的 NIKKE 竞技场配队分析工具，提供对局查询、记录、维护三大功能。

## 目录结构

```
nikke-pvp/
├── SKILL.md                          # 主入口：意图识别、子技能路由、全局规则
├── STRUCTURE.md                      # 本文档：项目结构说明
├── config.toml                       # 全局配置：数据路径、充能阶段
├── .gitignore                        # 忽略规则：__pycache__、.archive/、.old/、data/
│
├── data/                             # 运行数据
│   └── matches.toml                  # 对局数据库（主数据，追加模式）
│
├── references/                       # 参考数据（只读）
│   └── characters_pvp.toml           # 角色资料 + charge_2RL/charge_50SMG/charge_3RL 充能数据
│
├── scripts/                          # 通用脚本（所有子技能共享）
│   ├── common.py                     # 公共模块：配置加载、数据读取、工具函数
│   ├── calc_burst_chain.py           # 爆裂链计算（角色+阶段，附 [META] 输出）
│   ├── calc_team_charge.py           # 全队充能速度计算（Markdown 明细表格）
│   └── __pycache__/                  # Python 编译缓存（git 忽略）
│
└── sub-skills/                       # 子技能
    ├── query/                        # 查询对局
    │   ├── SKILL.md                  # 三步流程：数据编排 → LLM分析 → 组装输出
    │   ├── match_finder.py           # 历史对局匹配（人员重叠+爆裂链打分）
    │   └── references/
    │       └── output_format.md      # 输出格式审计说明
    │
    ├── match_recorder/               # 记录对局
    │   ├── SKILL.md                  # 流程：解析→校验→追加
    │   ├── match_recorder.py         # 记录脚本
    │   └── schema/
    │       └── match_schema.toml     # 唯一 Schema：字段顺序/必填/可选/合法值
    │
    └── alias_mapping/                # 名称解析（共享）
        ├── SKILL.md                  # 昵称→全名解析规则
        ├── alias_mapping.py          # 解析脚本（贪婪最长匹配）
        └── alias_mapping_pvp.toml    # 昵称映射表
```

## 忽略规则（.gitignore）

| 模式 | 说明 |
|------|------|
| `__pycache__/`, `*.pyc` | Python 编译缓存 |
| `.archive/` | 各模块归档目录（旧版脚本、历史备份等） |
| `data/` | 运行数据目录 |
| `.old/` | 归档旧代码目录 |

## 子技能说明

| 子技能 | 入口 | 主要功能 |
|--------|------|----------|
| query | `sub-skills/query/SKILL.md` | 查询队伍充能、匹配历史、生成分析 |
| match_recorder | `sub-skills/match_recorder/SKILL.md` | 提交新对局记录到 matches.toml |
| alias_mapping | `sub-skills/alias_mapping/SKILL.md` | 昵称简写→角色全名解析 |

## 匹配打分规则（match_finder.py）

| 维度 | 满分 | 说明 |
|------|------|------|
| 人员重叠 | 60分 | 5人=60，4人=48，3人=36 |
| 爆裂链匹配 | 30分 | B1B2B3全同=30，2个=20，1个=10 |
| 顺序完全匹配 | 10分 | 5人且顺序相同 |

满分 100 分，低于 50 分视为无匹配。

## 验证基准

**`match_schema.toml` 是字段集合、类型、顺序的唯一权威来源。** 子技能的所有输出必须与此文件一致，验证时以 schema 为准而非任何文档。
