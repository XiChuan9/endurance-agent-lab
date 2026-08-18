# Endurance Agent Lab（中文说明）

**Endurance Agent Lab 是一个用于构建可靠 AI 耐力训练教练 Agent 的开源评估与工程框架。它由专家标注案例、可复用 Skill、确定性计算工具、纵向运动员场景和可复现模型评估组成。**

它的第一目标不是“做一个会聊天的 AI 跑步教练”，而是把教练判断拆成可追踪、可验证、可迭代的工程系统。

## 你现在可以直接做什么

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

eal doctor
eal validate
eal demo --clean
```

上述 demo 不调用任何付费模型，会把 30 个基准案例完整跑一遍，并生成 JSON、Markdown 和 HTML 报告。规则基线是**有意与 v0.1 claim code 对齐的管线回归 oracle**；预期 100% 只证明协议、评分和文件链路正确，不代表通用 AI 教练能力。示例报告位于 `examples/reports/`。

审计“半马历史 PB 约 66 分、当前目标 70 分、主要问题是连续性和耐久而不是速度”的案例：

```bash
eal audit --case END-016 --provider rules
```

## 用于真实运动员

真实数据默认只能放到 `private/`，该目录不会被 Git 提交：

```bash
eal track init athlete-001
cp examples/private-athlete-context.template.yaml private/athlete-001-context.yaml
# 填写真实但经过授权的数据

eal track add athlete-001 private/athlete-001-context.yaml \
  --effective-date 2026-08-18

eal track audit athlete-001 --provider rules
```

使用 OpenAI：

```bash
pip install -e ".[openai]"
cp .env.example .env
# 在 .env 填写 OPENAI_API_KEY

eal audit --case END-016 --provider openai --model gpt-5.6-luna
```

评估其他模型或系统生成的结构化结果：

```bash
eal eval --provider replay --replay-dir examples/replay \
  --model external-system --case END-016
```

`examples/replay/END-016.json` 只用于验证导入与评分链路，不代表外部模型成绩。

## 三个核心模块

1. `training-plan-auditor`：先审计数据，再判断运动员状态、目标、限制因素和计划结构，最后给出 KEEP/MODIFY/REMOVE/ADD/HOLD 建议。
2. `EnduranceBench`：第一版 30 个案例，每个案例有必须识别、禁止识别和 hard fail 条件。
3. `Eval Runner`：保存模型、Skill、benchmark、代码版本、每个案例输入输出、评分和失败类型，使每次改动都能回归比较。

## 开源与商业化

公开部分提供方法论可信度和生态贡献；真实运动员数据、生产级数据连接、教练工作台、批量交付、私有偏好数据和运营系统可以保持私有。两者并不冲突。

完整中文操作方法见：[MVP 实际使用手册](docs/MVP_OPERATING_GUIDE.zh-CN.md)。
