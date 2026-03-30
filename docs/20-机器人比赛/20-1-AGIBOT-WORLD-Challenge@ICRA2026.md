# 20-1 AGIBOT WORLD Challenge@ICRA2026

## 概述

AGIBOT WORLD Challenge@ICRA2026 是由智元机器人（AgiBot）举办的具身智能机器人国际竞赛，作为 ICRA 2026 的官方竞赛项目。该赛事聚焦于机器人的推理与动作预测能力，涵盖从基础到复杂的渐进式任务，是展示具身智能研究成果的重要平台。

---

## 赛道介绍：Reasoning to Action

Reasoning to Action 赛道专注于评估模型在推理和动作预测方面的能力，基于 G2 机器人、AgiBot World 开放数据集和 Genie Sim 3.0 仿真平台。该赛道旨在弥合 Sim2Real（仿真到真实）差距，实现从开放词汇理解到物理交互的稳健泛化。

### 任务类型

赛道包含 **10 个渐进式挑战任务**，涵盖：

| 任务类别 | 描述 |
|----------|------|
| 双臂协作 | 涉及多臂协同操作的基础任务 |
| 长时序操作 | 复杂的长周期机器人操作任务 |
| 高精度操作 | 物流分拣、办公整理、零售服务、日常生活服务等 |

### 技术特点

- **仿真平台**：Genie Sim 3.0（开源工具包）
- **数据集**：AgiBot World 百万级高质量双臂操作数据集
- **评测系统**：分步计算成功率，生成详细性能指标

---

## 数据集

### Reasoning2Action 仿真数据集

| 平台 | 链接 |
|------|------|
| HuggingFace（含深度） | [数据集地址](https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026/tree/main/Reasoning2Action-Sim) |
| ModelScope（含深度） | [数据集地址](https://modelscope.cn/datasets/AgibotWorld/AgiBotWorldChallenge-2026/tree/master/Reasoning2Action-Sim) |
| HuggingFace（不含深度） | [低门槛版本](https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026/tree/main/Reasoning2Action-Sim) |
| ModelScope（不含深度） | [低门槛版本](https://modelscope.cn/datasets/AgibotWorld/AgiBotWorldChallenge-2026/tree/master/Reasoning2Action-Sim) |

### AgiBot World 完整数据集

参与者还可使用 AgiBot World 百万级高质量数据集：
[HuggingFace](https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta)

### 数据使用规则

- ✅ 允许使用其他公开数据集和预训练权重
- ✅ 允许通过 Genie Sim 收集自己的数据
- ❌ 获奖需在技术报告中明确描述数据使用情况

---

## 基线模型：ACoT-VLA

主办方提供基线模型 **ACoT-VLA** 作为参考实现，帮助参赛者熟悉训练/测试/提交流程。

| 项目 | 链接 |
|------|------|
| 基线代码 | [AgibotTech/ACoT-VLA](https://github.com/AgibotTech/ACoT-VLA) |

参与者可使用自己的模型替代基线模型以获得更好的性能。

---

## 评测工具：Genie Sim 3.0

Genie Sim 3.0 是开源的仿真评测平台，提供与测试服务器对齐的场景、资产和任务。

### 本地闭环评测流程

1. 按照用户指南逐步运行基线模型推理和 ICRA 任务
2. 确认 demo 成功后，集成自己的策略
3. 在本地环境验证
4. 提交到测试服务器参与排行榜挑战

### 评测指标

评测系统通过分步计算每一步的成功率来生成详细性能指标，详见竞赛空间的 Metrics 标签页。

---

## 提交规则

### 提交格式

1. 构建包含模型、代码和所有依赖项的 **Docker 镜像**
2. 将镜像推送到公开可访问的镜像仓库
3. 在测试服务器上提交完整镜像 URL

### 提交限制

- 每队每天最多 **2 次** 提交机会
- 强烈建议在提交前通过 Genie Sim 3.0 进行充分的本地测试

### 提交方式

1. 点击左侧导航栏底部的 **"New Submission"** 按钮
2. 填写镜像 URL 和相关信息
3. 系统自动拉取并运行镜像进行评测

### 查看结果

- 点击 **"My Submissions"** 查看所有提交记录
- 获取每条提交的详细评测结果
- 评测失败时可下载日志文件诊断问题

---

## 排行榜

- 点击 **"Leaderboard"** 查看当前排名
- 排名基于各队最高分提交计算
- 仅团队的最高评测分数计入排名

### 关键时间节点

| 日期 | 事项 |
|------|------|
| 4月20日 | 所有提交截止 |
| 4月30日 | 最终在线竞赛排名公布 |

---

## 参赛支持

### 邮箱支持

技术问题、合作咨询：agibot-world-challenge@agibot.com

### 社区交流

| 平台 | 链接 |
|------|------|
| Discord | [加入讨论](https://discord.gg/9UTYfReA) |
| 飞书群 | [加入讨论](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=a1br0b87-830e-4f36-ad6b-a275e8ad0dc9&qr_code=true) |

---

## 快速开始指南

### 环境准备

```bash
# 1. 克隆 Genie Sim 3.0
git clone https://github.com/your-repo/genie-sim.git

# 2. 安装依赖
cd genie-sim
pip install -r requirements.txt

# 3. 下载数据集
python scripts/download_data.py --dataset Reasoning2Action-Sim
```

### 运行基线

```bash
# 4. 运行基线模型
python run_baseline.py --model ACoT-VLA --task 01

# 5. 本地验证
python evaluate.py --local --submit
```

### 提交作品

```bash
# 6. 构建 Docker 镜像
docker build -t your-image:v1 .

# 7. 推送到镜像仓库
docker push your-registry.com/your-image:v1

# 8. 在测试服务器提交
# 访问 https://agibot-world.com/challenge2026/reasoning2action
# 点击 New Submission 填写镜像 URL
```

---

## 总结

AGIBOT WORLD Challenge@ICRA2026 是具身智能领域的重要竞赛，提供了：

- ✅ 10 个渐进式挑战任务，涵盖双臂协作、长时序操作、高精度操作
- ✅ 百万级高质量数据集支持
- ✅ 开源基线模型 ACoT-VLA 和 Genie Sim 3.0 评测工具
- ✅ 完整的训练-测试-提交流程
- ✅ 丰富的社区支持资源

本课程为你提供了完整的竞赛介绍和数据获取指南，后续课程将深入讲解具体任务攻略和获奖策略。

---

## 延伸阅读

- [Genie Sim 3.0 用户指南](https://agibot-world.com/sim-evaluation/docs/#/v3?id=_35-agibot-world-challenge-reasoning-to-action-tasks-icra)
- [ACoT-VLA 基线模型](https://github.com/AgibotTech/ACoT-VLA)
- [AgiBot World 数据集](https://huggingface.co/datasets/agibot-world/AgiBotWorld-Beta)