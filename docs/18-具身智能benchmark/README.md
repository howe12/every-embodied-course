# 18-具身智能 Benchmark

> **前置课程**：16-VLA 大模型、17-VLN 大模型

具身智能 Benchmark（基准评测）是用于标准化评估机器人或智能体能力的工具集，包含任务集合、评测环境、评估指标和评测协议。本章节系统介绍当前主流的具身智能 Benchmark（RLBench、MetaWorld、CALVIN、ManiSkill、HM3D 等），帮助读者掌握 Benchmark 的设计理念、评估指标体系和代码使用方法。

---

## 课程目录

| 序号 | 课程 | 状态 | 说明 |
|------|------|------|------|
| 18-1 | [具身智能 Benchmark 概述](./18-1-具身智能benchmark概述.md) | ✅ | Benchmark 概念、主流 Benchmark 详解、评估指标、代码实战 |
| 18-2 | [CALVIN 基准](./18-2-CALVIN-基准.md) | 🔄 | 语言条件化长程任务链，ABCD 四级难度 |
| 18-3 | [Franka Kitchen 环境](./18-3-Franka-Kitchen-环境.md) | ⏳ | 多步厨房操作任务，真实机器人仿真 |
| 18-4 | [RLBench 基准](./18-4-RLBench-基准.md) | ⏳ | 101 个视觉引导操作任务，MoveIt! 集成 |
| 18-5 | [Benchmark 项目实战](./18-5-Benchmark-项目实战.md) | ⏳ | 综合 Benchmark 评测实战 |

## 开发进度

- ✅ 已完成：1/5
- 🔄 编写中：1（18-2）
- ⏳ 待编写：3

## 前置知识

- 具身智能基础（第一章）
- 机器人学基础（第二章）
- 强化学习基础（14-1，推荐）
- Python / PyTorch 基础

## 学习目标

- 理解 Benchmark 的核心概念和设计原则
- 了解主流具身智能 Benchmark（RLBench、MetaWorld、CALVIN、ManiSkill、HM3D）的特点和应用场景
- 掌握评估方法与核心指标（SR、SPL、泛化能力）
- 具备 Benchmark 评测方案设计能力
- 能够使用代码框架进行标准化评测

## 章节脉络

```
17-VLN 大模型（导航）
     ↓
18-1 Benchmark 概述 ← 当前
     ↓
18-2 CALVIN 基准（语言操控）
18-3 Franka Kitchen（多步操作）
18-4 RLBench（视觉引导操作）
18-5 Benchmark 项目实战
```

---

## 相关资源

- RLBench GitHub: `https://github.com/stepjam/RLBench`
- MetaWorld GitHub: `https://github.com/rlworkgroup/metaworld`
- CALVIN GitHub: `https://github.com/calvin-dataset/calvin`
- ManiSkill GitHub: `https://github.com/haosulab/ManiSkill`
- Habitat Lab GitHub: `https://github.com/facebookresearch/habitat-lab`
- HM3D Dataset: `https://matterport.com/`

---

*本章节正在持续更新中...*
