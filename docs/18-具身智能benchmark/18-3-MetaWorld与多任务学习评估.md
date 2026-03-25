# 18-3 MetaWorld 与多任务学习评估

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 18-3 |
| 课程名称 | MetaWorld 与多任务学习评估 |
| 所属模块 | 18-具身智能benchmark |
| 难度等级 | ⭐⭐⭐⭐☆ |
| 预计学时 | 4小时 |
| 前置知识 | 强化学习基础（14-1）、多任务学习概念、PyTorch 基础、具身智能 Benchmark 概述（18-1） |

---

## 目录

1. [MetaWorld 概述](#1-metaworld-概述)
2. [任务设计详解](#2-任务设计详解)
3. [评估协议](#3-评估协议)
4. [基线方法与 SOTA](#4-基线方法与-sota)
5. [代码实现](#5-代码实现)
6. [练习题](#6-练习题)
7. [参考答案](#7-参考答案)

---

## 1. MetaWorld 概述

### 1.1 为什么需要 MetaWorld

在真实机器人场景中，训练一个能**泛化到新任务**的智能体比在单一任务上达到高表现更重要。传统强化学习方法在单一任务上表现优秀，但在新任务上需要从零训练。**元强化学习（Meta-RL）** 旨在让智能体 "学会如何学习"，从而快速适应新任务。

**论文**：[Meta-World: A Benchmark and Evaluation for Multi-Task and Meta Reinforcement Learning](https://arxiv.org/abs/1910.10843)

**GitHub**：`https://github.com/rlworkgroup/metaworld`

**MetaWorld 核心数据一览**：

| 指标 | 数值 |
|------|------|
| 任务总数 | 50 |
| 任务变体数 | 每个任务 200 个随机初始化 |
| 仿真引擎 | MuJoCo |
| 观测类型 | 状态空间（无视觉输入） |
| 动作空间 | 4DoF（机械臂末端 + gripper） |
| 机械臂模型 | Sawyer 7DoF 机械臂 |
| 发布年份 | 2019 |
| 支持框架 | OpenAI Gym / Gymnasium |

**MetaWorld 解决了什么问题**：

```
传统单任务 RL 的困境：
  任务 A 训练 → 达到 95% SR（需要 10M 步）
  任务 B 训练 → 达到 92% SR（需要 12M 步）
  任务 C 训练 → 达到 88% SR（需要 15M 步）
  问题：每个新任务都需要大量训练样本，无法快速迁移

MetaWorld 推动的解决方案：
  训练阶段 ──→ 学习 "学会如何学习"
               ↓
  测试阶段 ──→ 在新任务上少量微调即可达到高表现
               （few-shot adaptation）
```

### 1.2 ML10 / ML45 划分

MetaWorld 最核心的设计是**标准化的训练/测试任务划分**，用于评估算法的元学习泛化能力：

| 协议 | 训练任务数 | 测试任务数 | 评测目标 |
|------|-----------|-----------|---------|
| **MT10** | 10 | — | 多任务学习（在训练任务上联合优化） |
| **MT50** | 50 | — | 大规模多任务学习 |
| **ML10** | 10 | 5 | 元学习泛化（训练任务→新任务） |
| **ML45** | 45 | 5 | 困难元迁移（少量训练任务→完全新任务） |

```
MT10 / MT50 协议（多任务学习）：
┌──────────────────────────────────────────────────────────┐
│  训练阶段                                                 │
│    同时在 10/50 个训练任务上联合优化策略                   │
│    目标：所有训练任务平均 SR 最大化                       │
│                                                          │
│  评测阶段                                                 │
│    在相同的 10/50 个任务上评测（不同初始化）              │
│    报告：所有任务的平均成功率                             │
└──────────────────────────────────────────────────────────┘

ML10 / ML45 协议（元学习泛化）：
┌──────────────────────────────────────────────────────────┐
│  训练阶段                                                 │
│    在 10/45 个训练任务上学习快速适应能力                  │
│    每个任务提供少量演示轨迹（K-shot，K 通常为 1 或 10）  │
│    学习如何根据新任务快速调整策略                         │
│                                                          │
│  评测阶段                                                 │
│    在完全不同的 5 个新任务上评测                          │
│    每个新任务提供少量交互样本进行快速微调                 │
│    报告：新任务的平均成功率                              │
└──────────────────────────────────────────────────────────┘
```

**ML10 训练任务列表**：

| 任务名 | 操作类型 | 描述 |
|--------|---------|------|
| reach | 到达 | 末端执行器移动到目标位置 |
| push | 推动 | 推动方块到目标位置 |
| pick & place | 抓取放置 | 抓取方块并放置到目标位置 |
| drawer open | 抽屉打开 | 拉开抽屉 |
| drawer close | 抽屉关闭 | 推回抽屉 |
| door open | 门打开 | 打开门 |
| door close | 门关闭 | 关闭门 |
| button press topdown | 按钮按下 | 从上方按下按钮 |
| peg unplug side | 插销拔出 | 从侧面拔出插销 |
| window open | 窗户打开 | 打开窗户 |

**ML45 测试任务（部分）**：

| 任务名 | 操作类型 |
|--------|---------|
| basketball | 将球放入篮子 |
| hand insert | 将物体插入指定位置 |
| lever pull | 下拉杠杆 |
| coffee push | 推咖啡杯 |
| soccer | 将球踢入目标区域 |

---

## 2. 任务设计详解

### 2.1 桌面操作任务

MetaWorld 所有任务都在**Sawyer 机械臂**的桌面操作环境中进行：

```
MetaWorld 仿真环境布局

俯视图（Top-down View）：
┌──────────────────────────────────────────────────────┐
│                                                       │
│   ┌─────────┐                    ┌─────────┐         │
│   │ 目标区域 │                    │ 目标区域 │         │
│   │(Target) │                    │(Target) │         │
│   └─────────┘                    └─────────┘         │
│                                                       │
│                  ┌──────────┐                        │
│                  │  物体    │                        │
│                  │(Object)  │                        │
│                  └──────────┘                        │
│                                                       │
│         ┌────────────────────────────────┐           │
│         │         桌面 (Table)           │           │
│         └────────────────────────────────┘           │
│                                                       │
│                    ┌─────────┐                        │
│                    │ Sawyer  │                       │
│                    │ 机械臂  │                       │
│                    └─────────┘                       │
│                                                       │
└──────────────────────────────────────────────────────┘
```

**环境组成**：

| 组件 | 说明 |
|------|------|
| **Sawyer 机械臂** | 7DoF 工业机械臂，末端带有平行夹爪 |
| **桌面** | 固定工作平面，物体在其上滑动 |
| **操作物体** | 方块、圆柱、插销等（不同任务不同物体） |
| **目标区域** | 用虚线或颜色标记的目标位置 |
| **障碍物** | 部分任务有门、抽屉等关节障碍 |

### 2.2 任务难度分级

MetaWorld 的 50 个任务按难度分为三个级别：

| 难度级别 | 任务数量 | 特征 | 示例任务 |
|---------|---------|------|---------|
| **Level 1（Easy）** | ~15 | 单步操作，无障碍，物体大 | reach, push, button press |
| **Level 2（Medium）** | ~20 | 抓取+放置，或有简单障碍 | pick & place, drawer open |
| **Level 3（Hard）** | ~15 | 多步操作，精确对准，工具使用 | assembly, hammer, sweep |

**难度因子分析**：

| 难度因子 | 简单 | 中等 | 困难 |
|---------|------|------|------|
| **操作步骤** | 单步（到达/推动） | 两步（抓取+移动） | 多步（开→放→关） |
| **对准精度** | 宽松（5cm+） | 中等（1-5cm） | 精确（<1cm） |
| **物体大小** | 大方块 | 中等物体 | 小物体/细杆 |
| **障碍物** | 无 | 1 个简单障碍 | 多个/复杂结构 |
| **动作序列** | 单一动作 | 两个动作 | 三个以上动作 |

**任务分类树状图**：

```
MetaWorld 50 个任务
│
├── 到达/推动类（~10 个）
│   ├── reach              # 到达目标点（最简单）
│   ├── push               # 推动物体到目标
│   ├── pull-back-ball      # 拉回球
│   └── window-open         # 打开窗户
│
├── 抓取放置类（~15 个）
│   ├── pick & place        # 抓取并放置（核心）
│   ├── pick & place side  # 侧面放置
│   ├── throw object       # 抛掷物体
│   ├── reach & push       # 到达+推动组合
│   └── coffee push        # 推咖啡杯
│
├── 关节操作类（~15 个）
│   ├── drawer-open        # 抽屉打开
│   ├── drawer-close       # 抽屉关闭
│   ├── door-open          # 门打开
│   ├── door-close         # 门关闭
│   ├── button-press       # 按钮按下
│   ├── lever-pull         # 杠杆下拉
│   └── window-open        # 窗户打开
│
├── 精细操作类（~5 个）
│   ├── peg-insert-side    # 插销侧面插入
│   ├── peg-unplug-side    # 插销侧面拔出
│   ├── insert-hand-release # 插入手动释放
│   └── screw-pickup        # 螺丝拧起
│
└── 工具使用/组合类（~5 个）
    ├── hammer             # 锤子敲击
    ├── sweep               # 扫帚清扫
    ├── stick-push          # 棍子推物
    └── assembly           # 装配任务
```

### 2.3 观察空间与动作空间

**观测空间（Observation Space）**：

MetaWorld 采用**纯状态空间**观测，无视觉输入，观测向量维度为 37 维：

| 观测维度 | 名称 | 维度 | 说明 |
|---------|------|------|------|
| 末端执行器位置 | ee_pos | 3 | 夹爪末端在 Cartesian 空间的 (x, y, z) 坐标 |
| 末端执行器旋转 | ee_quat | 4 | 夹爪四元数旋转 (qx, qy, qz, qw) |
| 末端执行器速度 | ee_vel | 3 | 夹爪末端线速度 (vx, vy, vz) |
| 末端执行器角速度 | ee_ang_vel | 3 | 夹爪末端角速度 (wx, wy, wz) |
| 关节位置 | joint_pos | 7 | 7 个关节的角度 |
| 关节速度 | joint_vel | 7 | 7 个关节的角速度 |
| 目标位置 | goal | 3 | 任务目标的位置（仅在目标条件任务中） |
| Gripper 开合度 | gripper | 1 | 夹爪状态（0=闭合，1=打开） |
| 物体位置 | object_pos | 3 | 目标物体位置（xyz） |
| 物体旋转 | object_rot | 4 | 目标物体四元数旋转 |
| 物体速度 | object_vel | 3 | 目标物体线速度 |
| 物体角速度 | object_ang_vel | 3 | 目标物体角速度 |

**观测向量公式**：

$$
o_t = [\underbrace{ee_{pos}, ee_{quat}, ee_{vel}, ee_{ang\_vel}}_{\text{末端执行器状态（16维）}}; \underbrace{joint_{pos}, joint_{vel}}_{\text{关节状态（14维）}}; \underbrace{gripper}_{\text{夹爪（1维）}}; \underbrace{object_{pos}, object_{rot}, object_{vel}, object_{ang\_vel}}_{\text{物体状态（13维）}}]
$$

$$
\text{dim}(o_t) = 16 + 14 + 1 + 13 = 44 \text{ 维（部分任务有额外目标坐标）}
$$

**动作空间（Action Space）**：

| 维度 | 名称 | 范围 | 说明 |
|------|------|------|------|
| 0-2 | delta_xyz | [-1, 1] | 末端执行器位置的增量 |
| 3 | rotation | [-1, 1] | 旋转控制（部分任务固定） |
| 4-6 | delta_rot | [-1, 1] | 末端执行器的欧拉角增量 |
| 7 | gripper | [-1, 1] | 夹爪控制（-1=闭合，1=打开） |

**简化动作空间（MT10/MT50 常用）**：

| 维度 | 范围 | 说明 |
|------|------|------|
| 0-2 | [-1, 1] | 末端执行器位置的 (dx, dy, dz) 增量 |
| 3 | [-1, 1] | 夹爪控制（-1=闭合，1=打开） |

---

## 3. 评估协议

### 3.1 元学习评估流程

MetaWorld 的元学习评测遵循严格的**内任务-外任务**分离原则：

```
MetaWorld 元学习评测流程

┌─────────────────────────────────────────────────────────┐
│  Step 1: 任务准备                                        │
│    ├─ 选择 ML10 或 ML45 协议                             │
│    ├─ 确定训练任务集合（10 个或 45 个）                  │
│    └─ 确定测试任务集合（5 个新任务）                      │
│                                                         │
│  Step 2: 元训练（Meta-Training）                          │
│    ├─ 对每个训练任务采样 K 个演示轨迹（K-shot）          │
│    ├─ 梯度更新学习快速适应参数                           │
│    └─ 使用 MAML/PEARL 等元学习算法更新 meta-policy       │
│                                                         │
│  Step 3: 元测试（Meta-Testing）                           │
│    ├─ 对每个测试任务提供 K 个演示轨迹（adaptation）      │
│    ├─ 快速微调 meta-policy 到测试任务（inner loop）     │
│    └─ 在测试任务上评估 adaptation 后的策略               │
│                                                         │
│  Step 4: 结果报告                                        │
│    ├─ 报告测试任务上的平均成功率                         │
│    └─ 与基线方法（随机策略、MAML、MT）对比               │
└─────────────────────────────────────────────────────────┘
```

**ML10 完整评测配置**：

| 配置项 | 数值 | 说明 |
|-------|------|------|
| 训练任务数 | 10 | 训练集内任务 |
| 测试任务数 | 5 | 训练集外新任务 |
| 每任务训练样本 | 10,000 步 | 梯度更新用 |
| 每任务测试评估 | 500 步 | 最终评测 |
| K-shot | 1 或 10 | Few-shot 适应样本数 |
| 评测初始化变体 | 200 | 每个任务 200 种随机初始化 |
| 评测 episodes | 10 | 每个变体 1 episode |
| 成功判定阈值 | 目标位置 < 5cm | 物体到达目标区域 |

### 3.2 任务间迁移评估

**任务间迁移（Inter-Task Transfer）** 是 MetaWorld 的核心评测维度：

```
任务间迁移类型

类型 A：同构迁移（Homogeneous Transfer）
  └─→ 任务 A 训练 → 任务 A 测试（同一任务不同初始化）
       例：pick & place（初始化变体1）→ pick & place（初始化变体2）

类型 B：异构迁移（Heterogeneous Transfer）
  └─→ 任务 A 训练 → 任务 B 测试（不同任务）
       例：drawer-open 训练 → drawer-close 测试

类型 C：技能迁移（Skill Transfer）
  └─→ 任务 A 训练 → 任务 B 测试（B 需要 A 的子技能）
       例：reach 训练 → pick & place 测试（两者都需要精确到达）
```

**迁移效率矩阵**：

| 源任务 | 目标任务 | 迁移效率 | 说明 |
|--------|---------|---------|------|
| reach | push | 高 | 精确到达是 push 的基础 |
| reach | pick & place | 高 | 抓取前需要接近物体 |
| push | pick & place | 中 | push 学会移动物体，pick 需要额外抓取技能 |
| drawer-open | drawer-close | 中 | 两个任务使用相同关节，但方向相反 |
| reach | hammer | 低 | 锤子需要额外工具使用技能 |

### 3.3 少样本适应

**少样本适应（Few-shot Adaptation）** 是元学习在 MetaWorld 上的核心评测机制：

```
少样本适应流程（K-shot Adaptation）

1. 预训练阶段（Meta-Training）
   └─→ 在 10 个训练任务上学习 meta-policy
        └─→ 学习任务无关的通用技能表示
        └─→ 学习快速适应新任务的梯度更新方向

2. Few-shot 适应阶段（Adaptation）
   └─→ 在 5 个新测试任务上
        └─→ 每个任务提供 K 个演示轨迹（K 通常取 1, 5, 10）
        └─→ 执行 K 步梯度更新（或 inference-time adaptation）
        └─→ 得到 task-specific policy

3. 评测阶段（Evaluation）
   └─→ 在测试任务上运行 adaptation 后的 policy
   └─→ 记录成功率
```

**K-shot 实验设计**：

| K 值 | 数据量 | 评测难度 | 典型应用场景 |
|------|--------|---------|------------|
| K=1 | 1 条演示/测试任务 | 最困难 | 极限少样本泛化 |
| K=5 | 5 条演示/测试任务 | 困难 | 真实机器人场景（数据昂贵） |
| K=10 | 10 条演示/测试任务 | 中等 | 实用少样本 |
| K=100 | 100 条演示/测试任务 | 简单 | 标准模仿学习 |

**MetaWorld 官方评测指标**：

| 指标 | 公式/定义 | 含义 |
|------|---------|------|
| **Average Success Rate** | $\frac{1}{N_{test}}\sum_{i=1}^{N_{test}} SR_i$ | 所有测试任务的平均成功率 |
| **Per-Task Success Rate** | 单个测试任务的成功率 | 每个任务独立评估 |
| **Sample Efficiency** | 达到 SR > 80% 所需的样本数 | 训练效率 |
| **Adaptation Steps** | 适应新任务所需的梯度更新步数 | 元学习速度 |
| **Cross-Task Transfer Gain** | 元学习 SR - 随机策略 SR | 迁移带来的提升 |

---

## 4. 基线方法与 SOTA

### 4.1 MAML（Model-Agnostic Meta-Learning）

**MAML**（Model-Agnostic Meta-Learning）是 MetaWorld 论文中的核心基线方法，由 Chelsea Finn 等人提出：

**核心思想**：

```
MAML = 学习一个初始化参数 θ，使得在少量梯度更新后能快速适应新任务

核心洞察：
  └─→ 不是直接学习一个能解决所有任务的单一策略
  └─→ 而是学习一个 "好的起始点"（初始化参数）
  └─→ 新任务只需几步梯度下降即可快速适应

数学形式：
  给定任务分布 p(T)
  学习初始化参数 θ*，使得：

  θ* = argmin_θ Σ_{T_i ~ p(T)} L_{T_i}(f_{θ_i'})

  其中 θ_i' = θ - α ∇_θ L_{T_i}(f_θ)
       （对每个任务 T_i 做一步梯度更新）
```

**MAML 算法流程**：

```
MAML 两层梯度更新

外循环（Meta-Update）：
  for 每个 meta-epoch:
      采样一批训练任务 {T_1, ..., T_n}
      
      for 每个训练任务 T_i:
          # 内循环（Task-specific Adaptation）
          使用 K 个样本计算任务损失 L_{T_i}
          执行一步梯度更新：θ_i' = θ - α ∇_θ L_{T_i}(f_θ)
          
          # 使用更新后的策略在新样本上计算损失
          计算适应后的损失 L_{T_i}(f_{θ_i'})
      
      # 外循环（元更新）
      汇总所有任务的适应后损失
      更新 meta-parameter：θ = θ - β ∇_θ Σ_i L_{T_i}(f_{θ_i'})
```

**MAML 在 MetaWorld 上的表现**：

| 协议 | MT10 | MT50 | ML10 | ML45 |
|------|------|------|------|------|
| **随机策略** | 10% | 2% | 5% | 2% |
| **MT10/MT50** | 85% | 75% | — | — |
| **MAML** | 88% | 78% | 45% | 30% |
| **MAML + HER** | 90% | 80% | 50% | 35% |

> 注：HER（Hindsight Experience Replay）是一种将失败经验重标记为目标的技术，可与 MAML 结合使用。

### 4.2 PEARL（Probabilistic Embeddings for Actor-Critic Reinforcement Learning）

**PEARL** 由 Sergey Levine 等人提出，是一种**基于概率嵌入的元强化学习方法**：

**核心思想**：

```
PEARL = 任务嵌入 + 上下文推理 + 元学习

核心洞察：
  └─→ 每个任务可以用一个低维嵌入向量 z 表示
  └─→ 智能体通过上下文推断当前任务的嵌入
  └─→ 将任务嵌入加入策略输入，实现任务条件化

架构：
  上下文编码器（Inference Network）
    └─→ 输入：历史 (s, a, r) 轨迹
    └─→ 输出：任务嵌入 z ~ q(z | context)
    
  任务条件化策略
    └─→ 输入：状态 s 和任务嵌入 z
    └─→ 输出：动作 a = π(a | s, z)
    
  任务条件化 Q 函数
    └─→ 输入：状态 s、动作 a、任务嵌入 z
    └─→ 输出：Q(s, a, z)
```

**PEARL vs MAML 对比**：

| 维度 | MAML | PEARL |
|------|------|-------|
| **适应方式** | 梯度更新参数 | 推断任务嵌入 |
| **适应速度** | 慢（需要梯度计算） | 快（仅推理嵌入） |
| **表示能力** | 隐式任务知识 | 显式任务嵌入 |
| **计算成本** | 高（二阶梯度） | 中（上下文编码） |
| **探索策略** | 固定（ε-greedy） | 任务感知探索 |

**PEARL 在 MetaWorld 上的表现**：

| 协议 | MT10 | ML10 |
|------|------|------|
| **MAML** | 88% | 45% |
| **PEARL** | 86% | 52% |
| **MAML + Dropout** | 89% | 48% |
| **PEARL + HER** | 90% | 55% |

### 4.3 基于梯度的元学习方法总览

```
元学习方法分类

┌─────────────────────────────────────────────────────────┐
│                  基于梯度的元学习方法                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  一阶方法（First-Order）                                  │
│    └─ FOMAML（First-Order MAML）                        │
│       └─ 忽略二阶梯量，简化计算                          │
│       └─ 速度更快，但性能略低                            │
│                                                          │
│    └─ Reptile                                            │
│       └─ 迭代式初始化更新                                │
│       └─ 简化版元学习                                    │
│                                                          │
│  二阶方法（Second-Order）                                │
│    └─ MAML                                               │
│       └─ 完整二阶梯量更新                                │
│       └─ 性能最优，计算成本高                            │
│                                                          │
│  概率化方法（Probabilistic）                              │
│    └─ PEARL                                              │
│       └─ 任务嵌入 + 上下文推断                           │
│                                                          │
│    └─ PMAML（Probabilistic MAML）                       │
│       └─ 任务不确定性建模                                │
│                                                          │
│  行动者-评论家扩展（Actor-Critic Extensions）              │
│    └─ AC-MAML                                            │
│    └─ MAML-TRPO                                          │
│    └─ MB-MAML（Model-Based MAML）                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**主要元学习方法对比**：

| 方法 | 适应方式 | 样本效率 | 计算成本 | 适合场景 |
|------|---------|---------|---------|---------|
| **FOMAML** | 梯度更新 | 中 | 低 | 快速原型验证 |
| **Reptile** | 迭代更新 | 中 | 低 | 简单任务 |
| **MAML** | 梯度更新 | 高 | 高（二阶） | 标准元学习 |
| **PEARL** | 嵌入推断 | 高 | 中 | 任务嵌入有效时 |
| **MB-MAML** | 模型预测梯度 | 最高 | 最高 | 样本极其昂贵时 |

---

## 5. 代码实现

### 5.1 MetaWorld 环境加载

```python
"""
MetaWorld 环境加载与基础使用
"""
import numpy as np
import gymnasium as gym
from metaworld.envs import (
    ALL_V2_ENVIRONMENTS_GOAL_HIDDEN,
    ALL_V2_ENVIRONMENTS_GOAL_OBSERVABLE,
)
from metaworld import MetaWorldEnv


def create_metaworld_env(task_name, seed=None, goal_observable=True):
    """
    创建 MetaWorld 环境
    
    Args:
        task_name: 任务名称（如 "reach-v2", "pick-place-v2"）
        seed: 随机种子（用于环境初始化）
        goal_observable: 是否在观测中包含目标位置
                        - True: 目标位置在 obs 中（Goal Observable）
                        - False: 目标位置隐藏，需要探索（Goal Hidden）
    
    Returns:
        env: Gymnasium 兼容环境
    """
    # 选择环境变体
    if goal_observable:
        env_cls_dict = ALL_V2_ENVIRONMENTS_GOAL_OBSERVABLE
    else:
        env_cls_dict = ALL_V2_ENVIRONMENTS_GOAL_HIDDEN
    
    # 获取环境类
    if task_name not in env_cls_dict:
        available = list(env_cls_dict.keys())
        raise ValueError(
            f"任务 '{task_name}' 不存在！\n"
            f"可用任务列表：{available[:10]}... （共 {len(available)} 个）"
        )
    
    env_cls = env_cls_dict[task_name]
    
    # 创建环境实例
    env = env_cls()
    
    # 设置随机种子
    if seed is not None:
        env.seed(seed)
        np.random.seed(seed)
    
    return env


def get_observation(obs):
    """
    解析 MetaWorld 观测向量
    
    MetaWorld 观测向量组成：
    - 关节位置/速度
    - 末端执行器位置
    - 物体位置/旋转/速度
    - 目标位置（goal_observable=True 时）
    - gripper 状态
    
    Args:
        obs: 原始观测向量（numpy array 或 dict）
    
    Returns:
        info: 解析后的字典
    """
    # MetaWorld v2 观测格式
    info = {
        '末端执行器位置': obs[:3],          # ee_pos (x, y, z)
        '末端执行器旋转': obs[3:7],          # ee_quat (qx, qy, qz, qw)
        '关节位置': obs[7:14],              # joint positions (7 DoF)
        '关节速度': obs[14:21],             # joint velocities
        'gripper 状态': obs[21],            # gripper open/close
        '物体位置': obs[22:25],             # object position
        '物体旋转': obs[25:29],             # object rotation
        '物体速度': obs[29:32],             # object velocity
        '物体角速度': obs[32:35],           # object angular velocity
    }
    
    # goal_observable=True 时包含目标
    if len(obs) > 35:
        info['目标位置'] = obs[35:38]        # goal position
    
    return info


def print_task_info(env):
    """
    打印任务信息
    
    Args:
        env: MetaWorld 环境实例
    """
    print(f"任务名称: {env.task_name}")
    print(f"动作空间: {env.action_space}")
    print(f"观测空间: {env.observation_space}")
    print(f"成功条件: {env._get_success}")


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("MetaWorld 环境加载示例")
    print("=" * 60)
    
    # 加载单个任务环境
    print("\n>>> 加载 reach-v2 任务环境...")
    env = create_metaworld_env("reach-v2", seed=42)
    print_task_info(env)
    
    # 重置环境，获取初始观测
    obs, info = env.reset()
    print(f"\n初始观测维度: {obs.shape}")
    
    # 解析观测
    obs_info = get_observation(obs)
    print("\n观测解析：")
    for key, value in obs_info.items():
        print(f"  {key}: {value}")
    
    # 执行随机动作测试
    print("\n>>> 执行 5 步随机动作测试...")
    for step in range(5):
        action = env.action_space.sample()  # 随机动作
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        print(f"  Step {step+1}: reward={reward:.3f}, done={done}, success={info.get('success', False)}")
    
    env.close()
    print("\n环境关闭成功！")
    
    # 列出可用的所有任务
    print("\n>>> 可用任务列表（前 20 个）：")
    all_tasks = list(ALL_V2_ENVIRONMENTS_GOAL_OBSERVABLE.keys())
    for i, task in enumerate(all_tasks[:20]):
        print(f"  {i+1}. {task}")
    print(f"  ...（共 {len(all_tasks)} 个任务）")
```

### 5.2 元学习训练循环

```python
"""
MetaWorld 元学习训练循环实现
基于 MAML 算法的简化实现
"""
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
from copy import deepcopy


@dataclass
class MAMLConfig:
    """MAML 训练配置"""
    inner_lr: float = 0.1      # 内循环学习率（任务适应步长）
    outer_lr: float = 0.001   # 外循环学习率（元更新步长）
    inner_steps: int = 5      # 内循环梯度步数
    batch_size: int = 20       # 每个任务的采样步数
    meta_batch_size: int = 10 # 外循环采样的任务数
    epochs: int = 1000        # 元训练轮数
    seed: int = 42            # 随机种子


class SimplePolicy(nn.Module):
    """
    简化的 MLP 策略网络
    
    输入：状态维度（observation_dim）
    输出：动作维度（action_dim）
    """
    
    def __init__(self, obs_dim, action_dim, hidden_dim=128):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(obs_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh()  # 动作输出归一化到 [-1, 1]
        )
    
    def forward(self, obs):
        """前向传播"""
        return self.network(obs)
    
    def get_action(self, obs, deterministic=False):
        """
        根据观测获取动作
        
        Args:
            obs: 观测向量 [obs_dim]
            deterministic: 是否使用确定性策略
        
        Returns:
            action: 动作向量 [action_dim]
        """
        with torch.no_grad():
            obs_tensor = torch.FloatTensor(obs).unsqueeze(0)
            action = self.forward(obs_tensor).squeeze(0).numpy()
        return action


def collect_trajectory(
    env,
    policy: SimplePolicy,
    max_steps: int = 200,
    render: bool = False
) -> Tuple[List, List, List, List]:
    """
    采集一条轨迹
    
    Args:
        env: Gymnasium 环境
        policy: 策略网络
        max_steps: 最大步数
        render: 是否渲染
    
    Returns:
        observations: 观测列表
        actions: 动作列表
        rewards: 奖励列表
        dones: 终止标记列表
    """
    obs_list, action_list, reward_list, done_list = [], [], [], []
    
    obs, info = env.reset()
    
    for step in range(max_steps):
        if render:
            env.render()
        
        # 获取动作
        action = policy.get_action(obs)
        
        # 执行动作
        next_obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        
        # 记录
        obs_list.append(obs)
        action_list.append(action)
        reward_list.append(reward)
        done_list.append(done)
        
        obs = next_obs
        
        if done:
            break
    
    return obs_list, action_list, reward_list, done_list


def compute_returns(rewards: List[float], gamma: float = 0.99) -> List[float]:
    """
    计算折扣累计奖励
    
    Args:
        rewards: 奖励序列
        gamma: 折扣因子
    
    Returns:
        returns: 折扣累计奖励序列
    """
    returns = []
    G = 0.0
    
    for r in reversed(rewards):
        G = r + gamma * G
        returns.insert(0, G)
    
    return returns


def inner_update(
    policy: SimplePolicy,
    obs_list: List[np.ndarray],
    action_list: List[np.ndarray],
    reward_list: List[float],
    inner_lr: float,
    inner_steps: int,
    device: str = 'cpu'
) -> SimplePolicy:
    """
    MAML 内循环：任务特定适应
    
    使用几条轨迹的损失更新策略参数，得到适应后的策略
    
    Args:
        policy: 原始策略网络
        obs_list: 观测列表
        action_list: 动作列表
        reward_list: 奖励列表
        inner_lr: 内循环学习率
        inner_steps: 内循环步数
        device: 计算设备
    
    Returns:
        adapted_policy: 适应后的策略网络
    """
    # 复制策略（分离梯度）
    adapted_policy = deepcopy(policy)
    optimizer = optim.Adam(adapted_policy.parameters(), lr=inner_lr)
    
    # 计算折扣回报
    returns = compute_returns(reward_list)
    
    # 准备数据为 Tensor
    obs_tensor = torch.FloatTensor(np.array(obs_list)).to(device)
    action_tensor = torch.FloatTensor(np.array(action_list)).to(device)
    returns_tensor = torch.FloatTensor(np.array(returns)).to(device)
    
    for step in range(inner_steps):
        # 前向传播
        predicted_actions = adapted_policy(obs_tensor)
        
        # 计算损失（简单用 MSE，实际可用策略梯度）
        # 此处演示用行为克隆风格：预测动作 vs 专家动作
        # 实际 MAML 应使用策略梯度损失
        loss = nn.MSELoss()(predicted_actions, action_tensor)
        
        # 梯度更新
        optimizer.zero_grad()
        loss
        # 梯度更新
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    return adapted_policy


def maml_meta_update(
    policy: SimplePolicy,
    task_losses: List[float],
    outer_lr: float
) -> SimplePolicy:
    """
    MAML 外循环：元参数更新
    
    根据所有任务的适应后损失，更新 meta-parameter
    
    Args:
        policy: 原始策略网络
        task_losses: 每个任务适应后的损失列表
        outer_lr: 外循环学习率
    
    Returns:
        updated_policy: 元更新后的策略网络
    """
    # 计算平均损失
    avg_loss = np.mean(task_losses)
    
    # 计算梯度并更新
    # 注：此处为简化版，实际 MAML 使用高阶梯度
    optimizer = optim.Adam(policy.parameters(), lr=outer_lr)
    optimizer.zero_grad()
    
    # 反向传播（近似）
    for name, param in policy.named_parameters():
        if param.grad is None:
            # 如果没有梯度，设置虚拟梯度
            param.grad = torch.zeros_like(param)
    
    optimizer.step()
    
    return policy


def train_maml(
    metaworld_train_tasks: List[str],
    config: MAMLConfig
):
    """
    MAML 元训练主循环
    
    Args:
        metaworld_train_tasks: 训练任务名称列表
        config: 训练配置
    
    Returns:
        trained_policy: 训练好的 meta-policy
    """
    # 创建设兆网络
    # 获取第一个环境的维度信息
    sample_env = create_metaworld_env(metaworld_train_tasks[0])
    obs_dim = sample_env.observation_space.shape[0]
    action_dim = sample_env.action_space.shape[0]
    sample_env.close()
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    policy = SimplePolicy(obs_dim, action_dim).to(device)
    
    print(f"\n{'='*60}")
    print(f"MAML 元训练开始")
    print(f"设备: {device}")
    print(f"训练任务数: {len(metaworld_train_tasks)}")
    print(f"元批次大小: {config.meta_batch_size}")
    print(f"{'='*60}\n")
    
    # 预热阶段：创建环境缓存
    envs = {}
    for task_name in metaworld_train_tasks:
        envs[task_name] = create_metaworld_env(task_name, seed=config.seed)
    
    for epoch in range(config.epochs):
        # ========== 外循环：采样任务 ==========
        # 随机选择 meta_batch_size 个任务
        sampled_tasks = np.random.choice(
            metaworld_train_tasks,
            size=config.meta_batch_size,
            replace=True
        )
        
        task_losses = []
        
        for task_name in sampled_tasks:
            env = envs[task_name]
            
            # 采集适应前轨迹（用于计算内循环梯度）
            pre_obs, pre_actions, pre_rewards, _ = collect_trajectory(
                env, policy, max_steps=config.batch_size
            )
            
            # 内循环：在任务上快速适应
            adapted_policy = inner_update(
                policy,
                pre_obs, pre_actions, pre_rewards,
                inner_lr=config.inner_lr,
                inner_steps=config.inner_steps,
                device=device
            )
            
            # 采集适应后轨迹（用于计算外循环梯度）
            post_obs, post_actions, post_rewards, _ = collect_trajectory(
                env, adapted_policy, max_steps=config.batch_size
            )
            
            # 计算适应后损失
            post_returns = compute_returns(post_rewards)
            # 简化：用负回报作为损失
            task_loss = -np.mean(post_returns)
            task_losses.append(task_loss)
        
        # ========== 外循环：元更新 ==========
        policy = maml_meta_update(
            policy,
            task_losses,
            outer_lr=config.outer_lr
        )
        
        # 定期打印进度
        if (epoch + 1) % 100 == 0:
            avg_loss = np.mean(task_losses)
            print(f"Epoch {epoch+1}/{config.epochs}, "
                  f"Avg Task Loss: {avg_loss:.3f}")
    
    # 关闭所有环境
    for env in envs.values():
        env.close()
    
    return policy


### 5.3 多任务评估代码

```python
"""
MetaWorld 多任务评估框架
"""
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import json
import os


@dataclass
class EvaluationResult:
    """单任务评测结果"""
    task_name: str
    success_rate: float           # 成功率
    mean_reward: float            # 平均累计奖励
    mean_episode_length: float    # 平均回合长度
    success_std: float            # 成功率标准差
    num_episodes: int             # 评测回合数


@dataclass
class MultiTaskBenchmarkResult:
    """多任务 Benchmark 评测结果"""
    results: Dict[str, EvaluationResult]
    
    @property
    def overall_success_rate(self) -> float:
        """所有任务平均成功率"""
        all_srs = [r.success_rate for r in self.results.values()]
        return np.mean(all_srs)
    
    @property
    def overall_reward(self) -> float:
        """所有任务平均奖励"""
        all_rewards = [r.mean_reward for r in self.results.values()]
        return np.mean(all_rewards)
    
    def generate_report(self) -> str:
        """生成评测报告"""
        lines = []
        lines.append("=" * 70)
        lines.append("MetaWorld 多任务评测报告")
        lines.append("=" * 70)
        lines.append(f"\n【总体统计】")
        lines.append(f"  任务总数: {len(self.results)}")
        lines.append(f"  平均成功率: {self.overall_success_rate:.2%}")
        lines.append(f"  平均奖励: {self.overall_reward:.3f}")
        lines.append(f"\n【Per-Task 结果】")
        lines.append(f"{'任务名':<40} {'SR':>8} {'奖励':>10} {'长度':>8}")
        lines.append("-" * 70)
        
        for task_name, result in sorted(self.results.items()):
            lines.append(
                f"{task_name:<40} "
                f"{result.success_rate:>8.2%} "
                f"{result.mean_reward:>10.3f} "
                f"{result.mean_episode_length:>8.1f}"
            )
        
        lines.append("=" * 70)
        return "\n".join(lines)


class MetaWorldEvaluator:
    """
    MetaWorld 多任务评估器
    
    支持：
    - 单任务/多任务批量评测
    - MT10/MT50/ML10/ML45 协议
    - 结果保存与对比
    """
    
    def __init__(self, seed: int = 42):
        """
        初始化评估器
        
        Args:
            seed: 随机种子
        """
        self.seed = seed
        self.envs: Dict[str, any] = {}
    
    def load_task(self, task_name: str):
        """加载指定任务环境"""
        if task_name not in self.envs:
            self.envs[task_name] = create_metaworld_env(task_name, seed=self.seed)
        return self.envs[task_name]
    
    def evaluate_task(
        self,
        task_name: str,
        policy_fn: Callable,
        num_episodes: int = 100,
        max_steps: int = 500
    ) -> EvaluationResult:
        """
        评测单个任务
        
        Args:
            task_name: 任务名称
            policy_fn: 策略函数，输入 obs 输出 action
            num_episodes: 评测回合数
            max_steps: 每回合最大步数
        
        Returns:
            EvaluationResult: 评测结果
        """
        env = self.load_task(task_name)
        
        successes = []
        rewards = []
        lengths = []
        
        for episode in range(num_episodes):
            obs, info = env.reset()
            episode_reward = 0.0
            step_count = 0
            done = False
            
            while not done and step_count < max_steps:
                # 策略推理
                action = policy_fn(obs)
                
                # 环境执行
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated
                
                episode_reward += reward
                step_count += 1
            
            # 记录结果
            successes.append(bool(info.get('success', False)))
            rewards.append(episode_reward)
            lengths.append(step_count)
        
        return EvaluationResult(
            task_name=task_name,
            success_rate=np.mean(successes),
            mean_reward=np.mean(rewards),
            mean_episode_length=np.mean(lengths),
            success_std=np.std(successes),
            num_episodes=num_episodes
        )
    
    def evaluate_multi_task(
        self,
        task_list: List[str],
        policy_fn: Callable,
        num_episodes_per_task: int = 50,
        max_steps: int = 500
    ) -> MultiTaskBenchmarkResult:
        """
        批量评测多个任务
        
        Args:
            task_list: 任务名称列表
            policy_fn: 策略函数
            num_episodes_per_task: 每任务评测回合数
            max_steps: 每回合最大步数
        
        Returns:
            MultiTaskBenchmarkResult: 多任务评测结果
        """
        results = {}
        
        print(f"\n{'='*60}")
        print(f"MetaWorld 多任务评测")
        print(f"任务数: {len(task_list)}")
        print(f"每任务评测回合数: {num_episodes_per_task}")
        print(f"{'='*60}\n")
        
        for task_name in task_list:
            print(f">>> 评测任务: {task_name}")
            
            try:
                result = self.evaluate_task(
                    task_name=task_name,
                    policy_fn=policy_fn,
                    num_episodes=num_episodes_per_task,
                    max_steps=max_steps
                )
                results[task_name] = result
                print(f"  成功率: {result.success_rate:.2%}, "
                      f"平均奖励: {result.mean_reward:.3f}")
            except Exception as e:
                print(f"  评测失败: {e}")
        
        benchmark_result = MultiTaskBenchmarkResult(results)
        print(f"\n{'='*60}")
        print(f"总体成功率: {benchmark_result.overall_success_rate:.2%}")
        print(f"{'='*60}")
        
        return benchmark_result
    
    def evaluate_ml_protocol(
        self,
        train_tasks: List[str],
        test_tasks: List[str],
        meta_policy_fn: Callable,
        k_shot: int = 10,
        num_adapt_episodes: int = 5,
        num_eval_episodes: int = 50
    ) -> Dict[str, float]:
        """
        评测 ML10/ML45 协议
        
        Args:
            train_tasks: 训练任务列表
            test_tasks: 测试任务列表
            meta_policy_fn: 元策略函数，返回 (adapted_policy_fn, adaptation_info)
            k_shot: Few-shot 样本数
            num_adapt_episodes: 适应阶段评测回合数
            num_eval_episodes: 最终评测回合数
        
        Returns:
            metrics: ML 评测指标字典
        """
        print(f"\n{'='*60}")
        print(f"MetaWorld ML 协议评测")
        print(f"训练任务数: {len(train_tasks)}")
        print(f"测试任务数: {len(test_tasks)}")
        print(f"K-shot: {k_shot}")
        print(f"{'='*60}\n")
        
        # 在测试任务上评测（few-shot adaptation）
        test_results = {}
        
        for task_name in test_tasks:
            print(f">>> 测试任务: {task_name}")
            
            env = self.load_task(task_name)
            
            # Few-shot adaptation
            # （此处简化，实际应调用 meta_policy_fn 执行梯度更新）
            print(f"  执行 {k_shot}-shot 适应...")
            
            # 定义适应后的策略
            def adapted_policy(obs):
                # 简化的随机策略（实际应使用梯度更新后的策略）
                return env.action_space.sample()
            
            # 评测适应后策略
            successes = []
            for episode in range(num_eval_episodes):
                obs, info = env.reset()
                done = False
                step_count = 0
                
                while not done and step_count < 500:
                    action = adapted_policy(obs)
                    obs, reward, terminated, truncated, info = env.step(action)
                    done = terminated or truncated
                    step_count += 1
                
                successes.append(bool(info.get('success', False)))
            
            sr = np.mean(successes)
            test_results[task_name] = sr
            print(f"  测试成功率: {sr:.2%}")
        
        # 汇总结果
        avg_sr = np.mean(list(test_results.values()))
        
        metrics = {
            'avg_test_success_rate': avg_sr,
            'test_success_rates': test_results,
            'num_train_tasks': len(train_tasks),
            'num_test_tasks': len(test_tasks),
            'k_shot': k_shot,
        }
        
        print(f"\n{'='*60}")
        print(f"ML 评测结果")
        print(f"平均测试成功率: {avg_sr:.2%}")
        print(f"{'='*60}")
        
        return metrics
    
    def save_results(self, results, filepath: str):
        """
        保存评测结果到 JSON 文件
        
        Args:
            results: 评测结果对象
            filepath: 保存路径
        """
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        
        if isinstance(results, MultiTaskBenchmarkResult):
            data = {
                'overall_sr': float(results.overall_success_rate),
                'overall_reward': float(results.overall_reward),
                'per_task': {
                    name: {
                        'sr': float(r.success_rate),
                        'reward': float(r.mean_reward),
                        'length': float(r.mean_episode_length),
                        'std': float(r.success_std),
                        'episodes': r.num_episodes,
                    }
                    for name, r in results.results.items()
                }
            }
        elif isinstance(results, dict):
            data = results
        else:
            data = {'results': str(results)}
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"评测结果已保存至: {filepath}")


# ============ 使用示例 ============
if __name__ == "__main__":
    print("=" * 60)
    print("MetaWorld 多任务评估代码示例")
    print("=" * 60)
    
    # 步骤 1：加载任务
    print("\n>>> 加载 MetaWorld 任务...")
    
    # ML10 任务划分示例
    ml10_train_tasks = [
        "reach-v2", "push-v2", "pick-place-v2",
        "drawer-open-v2", "drawer-close-v2",
        "door-open-v2", "door-close-v2",
        "button-press-topdown-v2", "peg-unplug-side-v2", "window-open-v2"
    ]
    ml10_test_tasks = [
        "basket-v2", "lever-pull-v2", "coffee-push-v2",
        "soccer-v2", "hand-insert-v2"
    ]
    
    print(f"ML10 训练任务: {len(ml10_train_tasks)}")
    print(f"ML10 测试任务: {len(ml10_test_tasks)}")
    
    # 步骤 2：创建评估器
    evaluator = MetaWorldEvaluator(seed=42)
    
    # 步骤 3：定义策略函数
    def random_policy(obs):
        """随机策略（基线）"""
        # 创建一个假的动作空间
        return np.random.uniform(-1, 1, size=4)
    
    # 步骤 4：评测 MT10 协议（多任务学习）
    print("\n>>> 评测 MT10 协议（多任务学习）...")
    print("提示：以下为代码结构展示，实际运行需要安装 metaworld")
    print("pip install metaworld")
    
    # 实际评测代码：
    # mt_results = evaluator.evaluate_multi_task(
    #     task_list=ml10_train_tasks,
    #     policy_fn=random_policy,
    #     num_episodes_per_task=50,
    #     max_steps=500
    # )
    # print(mt_results.generate_report())
    # evaluator.save_results(mt_results, "results/metaworld_mt10.json")
    
    # 步骤 5：评测 ML10 协议（元学习）
    print("\n>>> 评测 ML10 协议（元学习泛化）...")
    
    # 实际评测代码：
    # ml_metrics = evaluator.evaluate_ml_protocol(
    #     train_tasks=ml10_train_tasks,
    #     test_tasks=ml10_test_tasks,
    #     meta_policy_fn=lambda: (random_policy, {}),
    #     k_shot=10,
    #     num_adapt_episodes=5,
    #     num_eval_episodes=50
    # )
    # evaluator.save_results(ml_metrics, "results/metaworld_ml10.json")
    
    print("\n[提示] 请安装 metaworld 后运行真实评测：")
    print("  pip install metaworld")
    print("  # ML10/MT10 任务需要从 metaworld 导入对应任务")
    
    # 关闭评估器
    for env in evaluator.envs.values():
        env.close()
    
    print("\n评测框架初始化完成！")

---

## 6. 练习题

### 选择题

**1. MetaWorld 包含多少个独立的任务？**
- A. 26 个
- B. 50 个
- C. 101 个
- D. 45 个

**2. MetaWorld 的 ML10 协议中，训练任务和测试任务的数量分别是？**
- A. 10 个训练，5 个测试
- B. 5 个训练，10 个测试
- C. 45 个训练，5 个测试
- D. 50 个训练，0 个测试

**3. MetaWorld 采用的仿真引擎和机械臂模型分别是？**
- A. PyBullet + Franka Panda
- B. MuJoCo + Sawyer
- C. Isaac Gym + Fetch
- D. Habitat + Spot

**4. MAML 的核心学习目标是什么？**
- A. 学习一个能直接解决所有任务的单一策略
- B. 学习一个能快速适应新任务的初始化参数
- C. 学习每个任务的最优 Q 值函数
- D. 学习任务之间的相似度度量

**5. PEARL 与 MAML 的主要区别是？**
- A. PEARL 使用梯度更新， MAML 使用嵌入推断
- B. PEARL 使用嵌入推断， MAML 使用梯度更新
- C. PEARL 不需要内循环， MAML 不需要外循环
- D. PEARL 是一阶方法， MAML 是二阶方法

**6. MetaWorld 的观测空间是纯状态空间，关于其维度说法正确的是？**
- A. 37 维，包含关节位置、末端执行器位置、目标位置
- B. 44 维，包含关节状态、末端执行器状态、物体状态
- C. 100+ 维，包含图像特征
- D. 10 维，仅包含目标位置

**7. MT10 和 ML10 协议的主要区别是？**
- A. MT10 在训练任务上评测， ML10 在测试任务上评测
- B. MT10 测试任务， ML10 训练任务
- C. MT10 不需要元学习， ML10 不需要多任务学习
- D. 两者完全等价，只是命名不同

**8. 关于 Few-shot Adaptation，以下说法正确的是？**
- A. K=1 表示每个测试任务需要 1 万步交互
- B. K 值越小，任务越困难，对元学习算法要求越高
- C. K-shot 只用于训练阶段，测试阶段不需要
- D. K-shot adaptation 仅在 MAML 中使用，其他方法不使用

### 简答题

**9. 解释 MetaWorld 的 ML10/ML45 协议设计，并说明这两种协议分别适合评估什么类型的多任务/元学习算法。**

**10. 描述 MAML 的两层梯度更新机制（内循环 + 外循环），并解释为什么这种设计能够让智能体快速适应新任务。**

**11. 对比 MAML 和 PEARL 两种元学习方法在适应方式、计算成本和表示能力上的差异。**

**12. 假设你在 MetaWorld 上评估一个新的元强化学习算法，请设计一个完整的评测方案，包括任务选择、指标定义、K-shot 配置和结果分析方法。**

---

## 7. 参考答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | MetaWorld 包含 50 个独立任务，涵盖抓取、放置、推、开门、抽屉等操作。 |
| 2 | **A** | ML10 表示 10 个训练任务 + 5 个测试任务的元学习协议。 |
| 3 | **B** | MetaWorld 使用 MuJoCo 仿真引擎和 Sawyer 7DoF 机械臂。 |
| 4 | **B** | MAML 的核心目标是学习一个"好的初始化参数"，使得新任务只需几步梯度更新即可适应。 |
| 5 | **B** | PEARL 使用概率任务嵌入 + 上下文推断来适应新任务；MAML 使用梯度更新。 |
| 6 | **B** | MetaWorld 观测空间约 44 维，包含关节状态（14）、末端执行器状态（16）、物体状态（13）、gripper（1）等。 |
| 7 | **A** | MT10 在训练任务上评测（多任务学习）；ML10 在测试任务上评测（元学习泛化到新任务）。 |
| 8 | **B** | K 值越小意味着可用数据越少，任务越困难，对元学习算法的快速适应能力要求越高。 |

### 简答题答案

**9. ML10/ML45 协议设计与适用算法**

**ML10 协议设计**：
- 训练阶段：在 10 个训练任务上学习元知识（学会如何学习）
- 测试阶段：在 5 个全新的测试任务上评估泛化能力
- K-shot：每个测试任务提供 K 个演示/交互样本用于快速适应

**ML45 协议设计**：
- 训练阶段：在 45 个训练任务上学习
- 测试阶段：在 5 个全新任务上评估
- 特点：训练任务远多于 ML10，测试任务比例更小，难度更高

**适用算法分析**：

| 协议 | 适用算法 | 原因 |
|------|---------|------|
| **ML10** | 通用元学习算法（MAML、PEARL、Reptile） | 10 个任务足以学习快速适应能力 |
| **ML45** | 强元学习算法（完整 MAML、MB-MAML） | 更多训练任务提供更丰富的任务分布，对算法要求更高 |
| **MT10** | 多任务学习算法（联合优化） | 仅评测在训练任务上的表现，不测试新任务泛化 |

---

**10. MAML 两层梯度更新机制**

```
MAML 内外循环机制

【内循环（Inner Loop）— 任务特定适应】
  对每个训练任务 T_i：
    1. 用当前 meta-parameter θ 采集 K 条轨迹
    2. 计算任务损失 L_{T_i}(f_θ)
    3. 执行梯度更新：θ_i' = θ - α ∇_θ L_{T_i}(f_θ)
    4. 用更新后的策略在新样本上计算损失 L_{T_i}(f_{θ_i'})

【外循环（Outer Loop）— 元更新】
  1. 汇总所有任务的适应后损失
  2. 执行元梯度更新：θ = θ - β ∇_θ Σ_i L_{T_i}(f_{θ_i'})
```

**快速适应的原因**：

1. **学习好的初始化**：θ* 使得任何任务从它出发，只需少量梯度更新就能收敛
2. **任务无关的通用技能**：梯度方向 θ - α∇L 编码了跨任务的通用调整方向
3. **高效利用任务分布**：外循环让 θ 朝着"所有任务都好"的方向优化
4. **与模型无关**：无论策略网络结构如何，MAML 都适用

---

**11. MAML vs PEARL 对比**

| 维度 | MAML | PEARL |
|------|------|-------|
| **适应方式** | 梯度更新参数 θ | 推断任务嵌入 z |
| **内循环** | 需要几步梯度计算 | 仅前向传播推断 z |
| **计算成本** | 高（二阶梯度） | 中（上下文编码） |
| **表示能力** | 隐式（参数空间） | 显式（嵌入空间） |
| **探索策略** | 固定（ε-greedy） | 任务感知（基于嵌入） |
| **适用场景** | 任务分布简单、样本昂贵 | 任务嵌入能有效区分时 |

**PEARL 的优势**：
- 不需要计算二阶梯量，计算更高效
- 任务嵌入 z 提供可解释的任务表示
- 可以利用探索策略（根据 z 调整探索程度）

**MAML 的优势**：
- 对任务结构假设更少，通用性更强
- 梯度更新能够更直接地调整策略参数
- 在低样本场景下（MAML 的核心应用）更鲁棒

---

**12. 元学习算法完整评测方案**

**① 任务选择**

| 协议 | 训练任务 | 测试任务 | 评测目标 |
|------|---------|---------|---------|
| **ML10** | reach, push, pick-place, drawer-open/close, door-open/close, button-press, peg-unplug, window-open | basketball, lever-pull, coffee-push, soccer, hand-insert | 元学习泛化（标准） |
| **ML45** | 45 个训练任务 | 5 个新任务 | 困难迁移 |

**② 评测指标体系**

| 指标类型 | 指标名称 | 计算方式 |
|---------|---------|---------|
| **核心指标** | 平均测试成功率 | 所有测试任务 SR 的均值 |
| **核心指标** | 成功率标准差 | 反映跨任务一致性 |
| **效率指标** | Few-shot 样本效率 | 达到 SR > 80% 所需的 K 值 |
| **基线对比** | 相对随机策略提升 | 元学习 SR - 随机 SR |
| **收敛指标** | 元训练曲线 | 外循环 loss 随 epoch 变化 |

**③ K-shot 配置**

| K 值 | 评测目标 | 典型使用 |
|------|---------|---------|
| K=1 | 极限少样本 | 验证算法的极致泛化能力 |
| K=5 | 少样本 | 真实机器人场景（数据昂贵） |
| K=10 | 中等样本 | 标准元学习评测 |
| K=100 | 大量样本 | 对比普通多任务学习 |

**④ 实验配置**

```python
eval_config = {
    # 任务配置
    'train_tasks': ml10_train_tasks,     # 10 个训练任务
    'test_tasks': ml10_test_tasks,        # 5 个测试任务
    
    # 训练配置
    'meta_batch_size': 10,                # 外循环任务采样数
    'inner_steps': 5,                     # 内循环步数
    'inner_lr': 0.1,                      # 内循环学习率
    
    # 评测配置
    'k_shot_values': [1, 5, 10, 100],     # 评测多个 K 值
    'adapt_episodes': 10,                 # 适应阶段 episodes
    'eval_episodes': 50,                  # 最终评测 episodes
    'max_steps': 500,                     # 每回合最大步数
    
    # 对比基线
    'baselines': ['random', 'MT10', 'MAML', 'PEARL'],
}
```

**⑤ 结果分析方法**

```
1. Per-Task 分析：每个测试任务的成功率柱状图
2. K-shot 曲线：横轴=K值，纵轴=成功率，学习曲线分析
3. 基线对比：与随机策略、MAML、PEARL 的对比表格
4. 统计显著性：多次随机种子下的均值±标准差
5. 失败模式分析：归类测试任务的失败原因（精确度不够/探索不足/物理交互困难）
```

