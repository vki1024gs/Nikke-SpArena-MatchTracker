# 测试用例表

每个查询串恰好触发一种 WARN 或 FAIL 组合。

| # | 输入串 | stdout (结果) | stderr 信号 | 含义 |
|---|--------|---------------|-------------|------|
| 1 | `诺白贝海豺` | 诺雅/布兰儿/贝斯蒂/海伦/豺狼 | 无 | **正常**：恰好5人 |
| 2 | `诺白贝海X` | 4人结果 | `[WARN] 无法识别: 'x'` | 输入含未知字符 |
| 3 | `诺雅诺雅白贝海` | 5人结果 | `[WARN] 重复角色: 诺雅`<br>`[FAIL] 存在重复角色` | 同一角色出现两次 |
| 4 | `诺白贝` | 3人结果 | `[FAIL] 解析出 3 人，需要恰好5人` | 全部匹配但不足5人 |
| 5 | `诺白贝海豺猫` | 6人结果 | `[FAIL] 解析出 6 人，需要恰好5人` | 输入过长，超过5人 |
| 6 | `猫猫` | 2人结果 | `[WARN] 重复角色: 尼罗`<br>`[FAIL] 解析出 2 人` + `[FAIL] 存在重复角色` | 重复 + 不足5人 |
| 7 | `诺白贝海猫X` | 5人结果(猫→尼罗后停) | `[WARN] 无法识别: 'x'` | 5人已匹配但输入有剩余字符（正常通过，仅 WARN） |

## 快速测试

```bash
cd sub-skills/alias_mapping
# 逐个测试
python3 alias_mapping.py "诺白贝海豺"        # 正常
python3 alias_mapping.py "诺白贝海X"          # WARN 无法识别
python3 alias_mapping.py "诺雅诺雅白贝海"     # WARN 重复
python3 alias_mapping.py "诺白贝"             # FAIL 不足5人
python3 alias_mapping.py "诺白贝海豺猫"       # FAIL 超过5人
python3 alias_mapping.py "猫猫"               # WARN重复 + FAIL重复+不足

# 查看所有信号（含debug详情）
python3 alias_mapping.py "<输入串>" --debug 2>&1
```
