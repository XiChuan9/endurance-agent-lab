# Endurance Agent Lab MVP 实际使用手册

## 一、第一次安装

```bash
cd endurance-agent-lab
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
eal doctor
eal validate
eal demo --clean
```

只要 `eal demo` 跑完 30/30，就说明输入协议、Skill、规则引擎、评分器、报告和文件写入已经连通。

## 二、先用公开案例理解系统

```bash
eal audit --case END-016 --provider rules
```

重点阅读：

- `derived.json`：代码计算的事实；
- `audit.json`：结构化判断；
- `audit.md`：教练可读报告；
- `claims`：后续评分和版本比较的核心。

## 三、为当前合作运动员建立私有轨迹

```bash
eal track init hm-athlete-001
cp examples/private-athlete-context.template.yaml private/hm-athlete-001-context.yaml
```

填写原则：

- 只写已知数据；
- 不知道就留空；
- 每周训练按真实执行情况更新；
- 疼痛、静息心率、天气和主观感受使用 `signals`；
- 计划写入 `proposed_plan`；
- 不要把真实姓名、比赛地点等非必要信息写进公开案例。

加入首个快照：

```bash
eal track add hm-athlete-001 private/hm-athlete-001-context.yaml \
  --effective-date 2026-08-18 \
  --notes "恢复期结束前的基线"
```

执行审计：

```bash
eal track audit hm-athlete-001 --provider rules
```

使用 OpenAI 时：

```bash
pip install -e ".[openai]"
cp .env.example .env
# 填 OPENAI_API_KEY
eal track audit hm-athlete-001 --provider openai --model gpt-5.6-luna
```

## 四、每周工作流

1. 从上一份 context 复制一份新文件。
2. 把计划改成实际完成数据。
3. 更新最近周量、关键训练、长跑、RPE、心率和恢复信号。
4. 写入下一阶段 proposed plan。
5. `track add` 生成不可覆盖的新快照。
6. `track audit`。
7. 人工检查：主要 limiter 是否合理、证据是否真实、建议恢复成本是否可承受。
8. 训练执行后继续积累结果。

## 五、如何控制 API 成本

- 日常数据检查和工程回归使用 `rules`，成本为零。
- 真实教练决策先跑一个高质量模型，不要默认多模型全量比较。
- 只对新增或失败案例跑回归：`eal eval --case END-016 --case END-026 ...`。
- 大规模公开 benchmark 比较再使用批量/资助额度。
- 报告中记录 token，不在代码中写死会过期的价格。

## 六、从真实合作抽象公开案例

不要直接复制真实数据。抽象步骤：

1. 确定值得测试的决策冲突；
2. 删除身份、地点、精确日期和无关细节；
3. 使用合成周量和训练课重建同一个推理结构；
4. 写必须识别、禁止识别和 hard fail；
5. 由教练独立复核；
6. 新案例才进入 `benchmarks/`。

## 七、当前 MVP 的边界

第一版不直接连接 Strava/Garmin，也不自动生成完整训练计划。这是有意限制：先证明“输入是否可信、诊断是否正确、计划审计是否可测试”。后续再把 StravaStats 的确定性分析结果接入 `AthleteContext`。
