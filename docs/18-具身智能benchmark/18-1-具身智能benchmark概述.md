# 18-1 具身智能 Benchmark 概述

**版本**: V1.0
**作者**: Wendy | **课程系列**: ROS2机器人仿真与应用实践
**适用对象**: 具备具身智能基础，了解机器人仿真环境和强化学习基本概念
**前置知识**: 机器人学基础（第二章）、强化学习基础（14-1）、Python/PyTorch 基础

---

## 一、课程概述

当我们训练好一个具身智能模型后，一个关键问题随之而来——**如何科学地评估它的能力？**

不同研究团队用不同的实验环境、不同指标，导致结果难以对比。A团队报告"成功率 95%"，B团队报告"成功率 90%"，但两者的任务难度、环境配置、评测协议可能完全不同，无法直接比较。

**Benchmark（基准评测）** 正是为解决这一问题而生的标准化工具，它让不同算法在同一套"考题"下比试，让研究结果可对比、可复现、可追溯。

本课程聚焦具身智能 Benchmark 概述，介绍：

1. **Benchmark 基础** — 什么是 Benchmark、为什么需要 Benchmark
2. **主流 Benchmark** — RLBench、MetaWorld、CALVIN、ManiSkill、HM3D
3. **评估指标体系** — 任务成功率、效率、泛化性、安全性
4. **Benchmark 设计原则** — 任务多样性、难度梯度、可复现性
5. **代码实战** — 简化 Benchmark 框架与评估指标计算

---

## 二、章节设计

**模块一：Benchmark 基础** — 概念、重要性、核心要素
**模块二：主流 Benchmark** — RLBench、MetaWorld、CALVIN、ManiSkill、HM3D
**模块三：评估指标体系** — 成功率、效率、泛化性、安全性
**模块四：Benchmark 设计原则** — 多样性、梯度、可复现性
**模块五：代码实战** — 简化 Benchmark 框架、评估指标、数据加载
**模块六：练习题与答案**

---

## 三、理论内容

### 3.1 Benchmark 概述

#### 3.1.1 什么是 Benchmark

Benchmark（基准测试）是用于**标准化评估机器人或智能体能力**的工具集，包含四大核心组件：

```
┌─────────────────────────────────────────────────────┐
│                   Benchmark 四大组件                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ① 任务集合（Task Suite）                           │
│     预定义的任务清单，明确定义"做什么"              │
│     例如："将红色方块放入蓝色盒子"                  │
│                                                     │
│  ② 评测环境（Environment）                          │
│     仿真器（Isaac Gym / MuJoCo / Habitat）          │
│     或真实物理场景（真实家庭/办公室）               │
│                                                     │
│  ③ 评估指标（Metrics）                              │
│     可量化的性能衡量标准                             │
│     例如：成功率、完成时间、抓取稳定性              │
│                                                     │
│  ④ 评测协议（Protocol）                             │
│     统一的实验流程、评测次数、随机种子               │
│     例如：每个任务 100 个 episode，报告均值±标准差  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

用公式表达：

$$
\text{Benchmark} = \text{Task Suite} + \text{Environment} + \text{Metrics} + \text{Protocol}
$$

**Benchmark 与普通实验的核心区别**：

| 对比维度 | 普通实验 | Benchmark |
|----------|----------|-----------|
| **任务定义** | 自己设计，自由发挥 | 标准化任务集合 |
| **对比基准** | 无或仅对比自己的消融实验 | 公开排行榜，所有人同一标准 |
| **复现性** | 难复现（代码/环境差异） | 高可复现（开源环境+固定种子） |
| **泛化评估** | 通常只测一个场景 | 多场景/多难度级别 |
| **社区认可** | 内部使用 | 学术/工业界广泛认可 |

#### 3.1.2 具身智能 Benchmark 的重要性

具身智能 Benchmark 对研究社区的价值体现在四个维度：

**① 促进公平比较**
没有 Benchmark，A 和 B 两个团队各说各话，互相不服。Benchmark 提供了统一的"考场"，让不同算法在同一套题目下比试。

**② 加速研究迭代**
研究者可以在 Benchmark 上快速验证想法，而不用从零搭建评测环境。类似刷 LeetCode 对程序员的帮助——有标准题目、有官方评测、有排行榜。

**③ 发现能力短板**
Benchmark 的多维度指标能揭示模型的薄弱环节——是抓取精度不够？还是泛化能力弱？明确指向改进方向。

**④ 推动落地应用**
工业界选型时，Benchmark 成绩是重要的参考依据。高分算法更可能被选中部署到真实机器人上。

```
真实机器人部署
     ↑
     │  参考 Benchmark 排行榜筛选候选算法
     │
Benchmark 评测 ──→ 算法 A (SR=92%) ──→ 候选
     │           算法 B (SR=78%) ──→ 淘汰
     │
     ↑ 验证算法可行性（Sim-to-Real）
     │
仿真环境研发 ──→ 算法迭代 ──→ Benchmark 验证
```

#### 3.1.3 评估维度

具身智能 Benchmark 通常从以下维度评估智能体能力：

| 评估维度 | 核心问题 | 典型指标 |
|---------|---------|---------|
| **任务完成度** | 机器人能否完成任务？ | 成功率（SR）、任务完成率 |
| **执行效率** | 机器人完成任务的速度/代价？ | 路径长度、SPL、回合长度 |
| **泛化能力** | 在新场景/新物体上的表现？ | 新场景 SR、零样本迁移率 |
| **安全性** | 机器人是否会碰撞或损坏物体？ | 碰撞率、受力峰值 |
| **鲁棒性** | 对干扰的抵抗能力？ | 光照变化鲁棒性、噪声容忍度 |

---

### 3.2 主流 Benchmark 详解

#### 3.2.1 RLBench — 视觉引导机械臂操作 Benchmark

**RLBench**（Reinforcement Learning Benchmark）由伦敦帝国理工学院（Imperial College London）推出，是当前**视觉引导机器人操作**领域最流行的 Benchmark 之一。

**论文**：[RLBench: The Robot Learning Benchmark & Learning Environment](https://arxiv.org/abs/1909.12271)

**GitHub**：`https://github.com/step Jamal/rlbench`

**核心特点**：

| 特点 | 说明 |
|------|------|
| **大规模任务库** | 101 个预定义任务，覆盖抓取、放置、开门、操作抽屉等 |
| **丰富的任务变体** | 每个任务支持 100+ 个不同的初始/目标配置，大幅增加数据多样性 |
| **视觉引导** | 每个任务提供 RGB 相机、深度相机、分割掩码等多视角视觉输入 |
| **动作空间** | 支持关节空间（joint positions）和末端执行器空间（EE pose） |
| **MoveIt! 集成** | 内置逆运动学求解，支持复杂机械臂规划 |
| **演示数据** | 提供每个任务的专家演示轨迹（Motion Planning 生成） |

**RLBench 任务分类**：

| 类别 | 任务示例 | 难度特点 |
|------|---------|---------|
| **基础操作** | close drawer, open door, turn tap | 单步简单操作 |
| **抓取放置** | pick and place object, stack blocks | 精确抓取+放置 |
| **多步操作** | open fridge and place, push button then open | 多步顺序操作 |
| **精细操作** | insert peg into hole, screw bulb | 精确对准 |
| **视觉推理** | find and reach, open specific colored box | 需要视觉理解 |

**支持的机器人模型**：

```
- Franka Panda（7 DoF 机械臂）
- Fetch Robot（移动机械臂）
- KUKA IIWA
- WidowX
- Sawyer（部分支持）
```

**RLBench 的评测指标**：

| 指标 | 说明 |
|------|------|
| **成功率（SR）** | 任务完成的比例，核心指标 |
| **平均奖励** | 强化学习策略的累计奖励 |
| **Demo Success Rate** | BC/IL 方法用专家演示训练后的成功率 |
| **路径长度** | 完成任务的总动作步数 |

**适用场景**：视觉策略学习（Visual Policy Learning）、模仿学习（IL）、强化学习（RL）的机器人操作任务评测。

---

#### 3.2.2 MetaWorld — 多任务元学习 Benchmark

**MetaWorld** 由斯坦福大学 RL Workgroup 推出，是专门为**元强化学习（Meta-RL）**研究设计的**多任务机器人操作 Benchmark**。

**论文**：[Meta-World: A Benchmark and Evaluation for Multi-Task and Meta Reinforcement Learning](https://arxiv.org/abs/1910.10843)

**GitHub**：`https://github.com/rlworkgroup/metaworld`

**核心特点**：

| 特点 | 说明 |
|------|------|
| **50 个独立任务** | 涵盖抓取、放置、推、开门、操作杆、抽屉、挂衣架等 |
| **标准化 API** | 与 OpenAI Gym/MuJoCo 兼容，易于接入 |
| **任务可分离** | 每个任务可单独评测，也可组合成多任务/元学习评测 |
| **元学习友好** | 明确定义了训练任务和测试任务的划分，用于评估泛化能力 |
| **高可复现性** | 固定随机种子、标准化初始化，实验可完全复现 |

**MetaWorld 50 个任务一览**：

| 任务类型 | 具体任务（部分） | 操控对象 |
|---------|----------------|---------|
| **抓取类** | reach, push, pick & place, pull | 物体位置操作 |
| **开门类** | door-open, door-close, window-open | 铰链关节操作 |
| **抽屉类** | drawer-open, drawer-close, cabinet-open | 平移关节操作 |
| **杆操作** | lever-pull, button-press, pendulum-swing | 旋转关节操作 |
| **堆叠类** | stack, assembly, bin-picking | 多物体协调 |
| **工具操作** | sweep-to dust, hammer, stick-push | 使用工具 |

**MetaWorld 的训练/测试划分**：

MetaWorld 最重要的设计是明确定义了多层次的泛化评测协议：

| 协议 | 训练任务 | 测试任务 | 评估目标 |
|------|---------|---------|---------|
| **MT10** | 10 个训练任务 | 同一 10 个任务（不同初始化） | 多任务学习 |
| **MT50** | 50 个训练任务 | 50 个任务 | 大规模多任务 |
| **ML10** | 10 个训练任务 | 5 个新任务 | 元学习泛化 |
| **ML45** | 45 个训练任务 | 5 个新任务 | 困难元迁移 |

```
训练阶段 ──→ 在训练任务上学习（MT10/MT50）或学习快速适应能力（ML10/ML45）
     │
     ↓
测试阶段 ──→ 在全新测试任务上评测泛化能力
```

**MetaWorld 的评测指标**：

| 指标 | 说明 |
|------|------|
| **平均成功率** | 所有评测任务的平均 SR |
| **训练效率** | 达到特定成功率所需的样本数 |
| **元学习适应速度** | 在新任务上微调后达到成功的步数 |
| **跨任务迁移率** | 在新任务上相对随机策略的提升幅度 |

**适用场景**：元强化学习算法（如 MAML、RL^2）、多任务策略学习、机器人操作技能迁移研究。

---

#### 3.2.3 CALVIN — 语言控制机器人操作 Benchmark

**CALVIN**（Calving Lifestyle with Language）由 DeepMind 团队推出，是专注于**语言条件化机器人操作**的 Benchmark，强调**长程多步任务执行**。

**论文**：[CALVIN: A Multi-Task Benchmark for Learning Language- Conditioned Robot Manipulation](https://arxiv.org/abs/2207.03225)

**GitHub**：`https://github.com/calvin-dataset/calvin`

**核心特点**：

| 特点 | 说明 |
|------|------|
| **长程任务链** | 每个任务需要连续执行 4 个子指令（如"打开抽屉 → 取出杯子 → 关上抽屉 → 放到桌上"） |
| **自然语言指令** | 使用自然语言描述动作，而非简化的符号指令 |
| **自由形式语言** | 同一动作有多种自然语言表述（"拿起" = "grasp" = "pick up"） |
| **Sim-to-Real 友好** | 设计时考虑了仿真到真实的迁移 |
| **ABCD 四个难度级别** | A 最简单，D 最困难，支持难度渐进式评测 |

**CALVIN 任务场景**：

```
CALVIN Environment（桌面操作台）
├── 场景组成
│   ├── 桌面（Table）
│   ├── 抽屉（Drawer）— 可开关
│   ├── 彩色方块（Red/Green/Blue Blocks）
│   ├── 目标位置（Target Zones）
│   └── 障碍物（Obstacles）
│
└── 任务链示例（Task Chain）
    指令 1: "pick the red block"      → 完成抓取
    指令 2: "place it in the drawer"  → 完成放置
    指令 3: "close the drawer"        → 关闭抽屉
    指令 4: "push the green block"    → 推物体
```

**CALVIN 的难度级别**：

| 难度 | 特点 | 适用场景 |
|------|------|---------|
| **Level A** | 单步指令，固定初始状态 | 算法基础能力验证 |
| **Level B** | 单步指令，随机初始状态 | 泛化到随机初始化 |
| **Level C** | 长程任务链（4步），固定初始状态 | 长程规划能力 |
| **Level D** | 长程任务链（4步），随机初始状态 | 最困难，综合能力 |

**CALVIN 评测指标**：

| 指标 | 说明 |
|------|------|
| **任务完成率（FCR）** | 完整任务链完成的比例 |
| **平均完成步数（ASR）** | 每条指令的平均成功率 |
| **语言对齐分数** | 评估语言描述与动作的匹配程度 |
| **长程依赖得分** | 后序指令对前序指令的依赖处理能力 |

**适用场景**：语言条件化策略学习（Language-Conditioned RL）、多步任务规划、指令跟随（Instruction Following）研究。

---

#### 3.2.4 ManiSkill — 高保真机器人操作 Benchmark

**ManiSkill** 是由 NVIDIA 团队推出基于 **SAPIEN** 仿真平台的**高保真机器人操作 Benchmark**，强调物理真实性和视觉真实感的结合。

**论文**：[ManiSkill: A Unified Benchmark for Generalizable Manipulation Skills](https://arxiv.org/abs/2303.08797)

**GitHub**：`https://github.com/haosulab/ManiSkill`

**核心特点**：

| 特点 | 说明 |
|------|------|
| **高保真物理仿真** | 基于 SAPIEN 引擎，关节物理、碰撞、摩擦力高度真实 |
| **真实几何模型** | 使用真实 CAD 模型而非简化几何体 |
| **统一 API** | 与 OpenAI Gym API 兼容，支持 Python 接口 |
| **大规模演示数据** | 提供每个任务数千条专家演示轨迹（使用 Motion Planning 自动生成） |
| **GPU 并行渲染** | 支持 GPU 并行环境渲染，适合大规模数据生成 |
| **丰富物体类别** | 涵盖日常物体（杯子、盒子、工具等） |

**ManiSkill 任务分类**：

| 类别 | 任务数量 | 任务示例 |
|------|---------|---------|
| **单臂操作** | 20+ | pick and place, push, drawer open/close |
| **双臂协同** | 10+ | hand over, two-arm assembly |
| **精细操作** | 10+ | peg insertion, cable routing |
| **工具使用** | 10+ | hammer, screwdriver, wrench |

**ManiSkill 的视觉输入**：

```
ManiSkill 支持的观测模态：
├── 关节状态（Joint States）  — 机器人关节位置/速度/力矩
├── RGB 相机图像             — 物理渲染的 RGB 图像
├── 深度图像（Depth）        — 深度图
├── 法向量（Normal Map）     — 表面法向量
├── 分割掩码（Segmentation） — 语义分割
└── Point Cloud              — 深度点云
```

**ManiSkill vs 其他 Benchmark**：

| 维度 | ManiSkill | RLBench | MetaWorld |
|------|-----------|---------|-----------|
| **物理仿真保真度** | ★★★★★（SAPIEN） | ★★★（PyBullet） | ★★★（MuJoCo） |
| **视觉真实感** | ★★★★★（GPU 渲染） | ★★★ | ★★ |
| **任务数量** | 20+ | 101 | 50 |
| **演示数据** | ✓（自动生成） | ✓ | ✓ |
| **支持 GPU 并行** | ✓ | ✗ | 部分 |
| **适用研究** | Sim-to-Real、视觉策略 | 模仿学习、RL | 元学习、多任务 |

**ManiSkill 的评测指标**：

| 指标 | 说明 |
|------|------|
| **成功率（SR）** | 任务完成比例 |
| **SPL（面向操作的 SPL）** | 考虑动作效率的成功率变体 |
| **平直抓取成功率** | 仅抓取阶段的成功率 |
| **平均奖励** | 强化学习策略质量 |
| **Sim-to-Real Gap** | 仿真到真实的性能迁移率 |

**适用场景**：高保真机器人操作研究、Sim-to-Real 迁移、视觉-语言-动作（VLA）策略学习。

---

#### 3.2.5 Habitat-Matterport 3D（HM3D）— 真实室内导航 Benchmark

**HM3D**（Habitat-Matterport 3D Dataset）是 Meta AI 推出的**基于真实住宅3D扫描的室内导航 Benchmark**，是当前最具影响力的具身导航评测环境之一。

**论文**：[Habitat-Matterport 3D Dataset (HM3D): 1000 Large-scale 3D Environments for Embodied AI](https://arxiv.org/abs/2109.08228)

**官网**：`https://matterport.com/`

**GitHub**：`https://github.com/facebookresearch/habitat-lab`

**核心特点**：

| 特点 | 说明 |
|------|------|
| **真实 3D 扫描** | 1000 个真实住宅环境的 Matterport 3D 扫描，包含真实家具、纹理、光照 |
| **物理真实性** | 基于 Habitat 仿真器，提供精确的物理模拟（碰撞、导航） |
| **大规模场景** | 1000 个不同场景，远超之前数据集（如 MP3D 的 90 个） |
| **语义标注** | 提供物体类别、房间类型等语义信息 |
| **多任务支持** | 支持 ObjectNav、PointNav、ImageNav、VLN 等多种导航任务 |
| **高效仿真** | CPU 上可达数千步/秒，适合大规模 RL 训练 |

**HM3D 场景示例**：

```
HM3D 数据集包含的真实住宅环境：
├── 公寓（Apartments）     — 现代都市风格
├── 独栋住宅（Houses）     — 家庭居住环境
├── 办公室（Offices）      — 工作场景
└── 混合场景

每个场景包含：
├── 3D 网格模型（Mesh）    — 几何结构
├── RGB-D 图像序列         — 视觉观测
├── 相机位姿（Camera Pose） — 6DoF 位姿
└── 语义分割标注           — 物体/房间语义
```

**HM3D 主要评测任务**：

| 任务 | 描述 | 成功条件 |
|------|------|---------|
| **ObjectNav** | 找到指定类别的物体 | 到达物体 1m 范围内 |
| **PointNav** | 导航到指定坐标点 | 到达目标点 0.2m 内 |
| **ImageNav** | 根据目标图像导航 | 到达与图像匹配的位置 |
| **VLN-CE** | 根据语言指令导航 | 到达指令描述位置 |
| **Exploration** | 探索未知环境 | 在限定步数内覆盖率最大化 |

**HM3D 的评测指标**：

| 指标 | 说明 |
|------|------|
| **成功率（SR）** | 任务完成比例 |
| **SPL** | 成功率 × 路径效率（核心导航指标） |
| **Distance to Success** | 最终位置到成功阈值的平均距离 |
| **Collisions** | 碰撞次数（安全性） |
| **Episode Length** | 平均回合长度 |

**SPL 计算公式**（Habitat 官方定义）：

$$
\text{SPL} = \frac{1}{N} \sum_{i=1}^{N} \left[ \mathbb{1}_{s_i} \cdot \frac{\ell_i^*}{\max(\ell_i, \ell_i^*)} \right]
$$

其中：
- $N$ 是评测 episode 总数
- $\mathbb{1}_{s_i}$ 是第 $i$ 个 episode 是否成功（1=成功，0=失败）
- $\ell_i^*$ 是第 $i$ 个 episode 的最短路径长度
- $\ell_i$ 是实际路径长度

**适用场景**：室内导航研究、视觉-语言导航（VLN）、场景理解、Sim-to-Real 迁移。

---

### 3.3 主流 Benchmark 总览与对比

| Benchmark | 专注领域 | 仿真平台 | 任务数 | 核心特点 | 机构 |
|-----------|---------|---------|-------|---------|------|
| **RLBench** | 视觉引导机械臂操作 | PyBullet | 101 | 大规模任务库、多视角视觉、MoveIt! 集成 | Imperial College London |
| **MetaWorld** | 多任务/元学习操作 | MuJoCo | 50 | 明确定义训练/测试划分、元学习友好 | Stanford |
| **CALVIN** | 语言条件化操作 | PyBullet | 26 | 长程任务链、自然语言指令 | DeepMind |
| **ManiSkill** | 高保真操作 | SAPIEN | 20+ | 高保真物理+视觉、GPU 渲染 | NVIDIA |
| **HM3D** | 室内导航 | Habitat | 1000 场景 | 真实住宅 3D 扫描、大规模场景 | Meta AI |
| **HomeBench** | 家庭服务机器人 | Habitat | 多任务 | 导航+操作结合 | Meta AI |
| **VIMA-Bench** | 多模态 VLA | MuJoCo | 17 | 视觉-语言-动作多模态 | NVIDIA |

**Benchmark 选择指南**：

```
选择 Benchmark 的决策树：

1. 研究方向是什么？
   ├── 机械臂操作
   │   ├── 需要高保真物理？  → ManiSkill
   │   ├── 需要多任务泛化？  → MetaWorld
   │   ├── 需要视觉策略？    → RLBench
   │   └── 需要语言指令？    → CALVIN
   │
   └── 导航任务
       ├── 室内环境？        → HM3D
       └── 室外环境？        → StreetVLN

2. 需要真实感吗？
   ├── 极高（Sim-to-Real）→ ManiSkill / HM3D
   └── 一般仿真研究        → RLBench / MetaWorld / CALVIN

3. 需要演示数据吗？
   └── 是                  → RLBench / ManiSkill / CALVIN 均有
```

---

### 3.4 评估指标体系

#### 3.4.1 任务成功率（Success Rate, SR）

成功率是最直观的核心指标，表示任务完成的比例。

$$
\text{SR} = \frac{\text{成功回合数}}{\text{总回合数}} \times 100\%
$$

**分级标准**（通常约定俗成）：

| 成功率范围 | 评价 | 含义 |
|-----------|------|------|
| 95% - 100% | 接近饱和 | 算法已足够好，改进空间小 |
| 80% - 94% | 良好 | 可用于实际场景 |
| 50% - 79% | 一般 | 需要继续优化 |
| < 50% | 较差 | 算法尚不成熟 |

**注意事项**：
- 任务定义必须严格清晰（"完全放入" vs "部分放入" 差异很大）
- 成功率对随机种子敏感，建议跑 100+ episodes 取统计显著性
- 有些任务天然有随机性（物体初始位置），成功率本身有上限

#### 3.4.2 效率指标

效率指标衡量机器人**完成任务的速度或代价**。

| 指标 | 公式/说明 | 含义 |
|------|---------|------|
| **Average Episode Length** | 回合内平均步数 | 越短=越高效 |
| **Path Length / SPL** | 实际路径/最优路径 | SPL = SR × (最优路径/实际路径) |
| **Time to Success** | 首次成功的时间 | 越短=学习/执行越快 |
| **Average Return** | 累计奖励均值 | 越高=策略越好 |
| **Energy / Force** | 消耗能量或力矩积分 | 越少=越节能 |

#### 3.4.3 泛化能力指标

泛化能力衡量算法在**新场景/新任务**上的表现，是机器人落地的关键。

| 指标 | 评估方式 | 说明 |
|------|---------|------|
| **新物体泛化** | 训练时未见过的物体类别 | 测试视觉/物理泛化 |
| **新场景泛化** | 训练时未见过的室内布局 | 测试空间理解泛化 |
| **新任务泛化** | 任务组合的新任务 | 测试任务分解能力 |
| **Sim-to-Real Gap** | 仿真指标 vs 真实指标差距 | 评估仿真真实性 |

**泛化实验设计原则**：
- 训练集和测试集必须严格分离（无数据泄露）
- 泛化难度要梯度上升（从相似到差异大）
- 记录基线模型在新场景下的退化程度

#### 3.4.4 安全性指标

| 指标 | 适用场景 | 说明 |
|------|---------|------|
| **Collision Rate** | 导航任务 | 碰撞次数，越少越安全 |
| **Force Exerted** | 精细操作 | 末端执行器受力，越小越安全 |
| **Fall Rate** | 双足/移动机器人 | 摔倒频率，反映平衡能力 |
| **Human Intervention Rate** | 人机协作 | 需要人工接管频率 |

---

### 3.5 Benchmark 设计原则

一个优秀的具身智能 Benchmark 需要满足以下设计原则：

#### 3.5.1 任务多样性

Benchmark 应覆盖足够多样的任务类型，以全面评估智能体的能力：

```
任务多样性维度：
├── 操作类型：抓取、放置、推、插入、旋转、装配...
├── 物体类别：刚性物体、柔性物体、透明物体、多关节物体...
├── 场景类型：桌面、厨房、卧室、办公室...
├── 指令形式：目标状态、自然语言、演示轨迹...
└── 难度梯度：单步、多步、长程规划、零样本...
```

#### 3.5.2 难度梯度

好的 Benchmark 应具有明确的难度分级，让研究者能精确定位算法能力：

| 难度级别 | 特点 | 示例 |
|---------|------|------|
| **Level 1（Easy）** | 单步任务，固定初始状态 | "抓取指定物体" |
| **Level 2（Medium）** | 单步任务，随机初始状态 | "抓取任意位置的指定物体" |
| **Level 3（Hard）** | 多步任务链，固定初始状态 | "打开抽屉 → 放入物体 → 关闭抽屉" |
| **Level 4（Expert）** | 多步任务链，随机初始状态 | 新物体+新场景+长程任务 |

#### 3.5.3 可复现性

可复现性是 Benchmark 信任度的基础：

| 要素 | 要求 | 实现方式 |
|------|------|---------|
| **环境固定** | 仿真器版本、参数完全固定 | Docker 镜像/固定 commit hash |
| **随机种子** | 所有随机源可控制 | 显式设置 numpy/random/env seed |
| **评估协议** | 评测次数、平均方式标准化 | 官方评测脚本 |
| **数据集划分** | 训练/验证/测试严格分离 | 官方固定划分 |

#### 3.5.4 实际应用价值

Benchmark 的设计应贴近真实应用场景：

- **有意义的任务**：任务应模拟真实世界需求，而非为评测人为构造
- **可部署性**：仿真环境达标后，算法应能迁移到真实机器人
- **可扩展性**：易于添加新任务、新物体、新场景

---

## 四、代码实现

### 4.1 简化 Benchmark 框架

下面实现一个通用的 Benchmark 评测框架，可适配 RLBench、MetaWorld、CALVIN 等环境：

```python
"""
简化具身智能 Benchmark 评测框架
实现通用的任务评测 API，支持多种 Benchmark 环境
"""
import gymnasium as gym
import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Any
from enum import Enum
import json
import os


class BenchmarkType(Enum):
    """支持的 Benchmark 类型枚举"""
    RLBENCH = "rlbench"
    METAWORLD = "metaworld"
    CALVIN = "calvin"
    MANISKILL = "maniskill"
    HM3D = "hm3d"
    CUSTOM = "custom"


@dataclass
class EvaluationMetrics:
    """评测指标数据类"""
    # 基础指标
    success_rate: float = 0.0          # 任务成功率
    avg_episode_length: float = 0.0    # 平均回合长度
    std_episode_length: float = 0.0    # 回合长度标准差
    avg_reward: float = 0.0            # 平均累计奖励
    std_reward: float = 0.0            # 奖励标准差

    # 效率指标
    spl: float = 0.0                   # SPL（Success weighted by Path Length）
    optimal_path_ratio: float = 0.0    # 路径效率比

    # 安全指标
    collision_rate: float = 0.0        # 碰撞率
    max_force: float = 0.0             # 最大受力

    # 泛化指标
    generalization_gap: float = 0.0    # 泛化差距（训练 vs 测试）

    # 额外指标
    extra: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, float]:
        """转换为字典，便于序列化和打印"""
        result = {
            'success_rate': self.success_rate,
            'avg_episode_length': self.avg_episode_length,
            'std_episode_length': self.std_episode_length,
            'avg_reward': self.avg_reward,
            'std_reward': self.std_reward,
            'spl': self.spl,
            'optimal_path_ratio': self.optimal_path_ratio,
            'collision_rate': self.collision_rate,
            'max_force': self.max_force,
            'generalization_gap': self.generalization_gap,
        }
        result.update(self.extra)
        return result


class BenchmarkEvaluator:
    """
    通用 Benchmark 评测器

    支持：
    - 批量评测多个任务
    - 多种策略（随机、BC、RL 等）
    - 统计指标计算（均值、标准差、置信区间）
    - 结果保存与对比
    """

    def __init__(
        self,
        env_id: str,
        benchmark_type: BenchmarkType = BenchmarkType.CUSTOM,
        policy_name: str = "policy",
        seed: Optional[int] = None
    ):
        """
        初始化评测器

        Args:
            env_id: Gymnasium 环境 ID（如 "rlbench:reach-v0"）
            benchmark_type: Benchmark 类型
            policy_name: 策略名称（用于日志和报告）
            seed: 随机种子（用于结果复现）
        """
        self.env_id = env_id
        self.benchmark_type = benchmark_type
        self.policy_name = policy_name
        self.seed = seed
        self.env: Optional[gym.Env] = None

        # 评测结果记录
        self.episode_records: List[Dict[str, Any]] = []

    def make_env(self) -> gym.Env:
        """创建评测环境"""
        if self.env is not None:
            return self.env

        self.env = gym.make(self.env_id)

        # 设置随机种子
        if self.seed is not None:
            if hasattr(self.env, 'seed'):
                self.env.seed(self.seed)
            # Gymnasium v26+ 使用 np_random_generator
            try:
                self.env.reset(seed=self.seed)
            except Exception:
                pass

        return self.env

    def close(self):
        """关闭环境并释放资源"""
        if self.env is not None:
            self.env.close()
            self.env = None

    def evaluate(
        self,
        policy: Callable[[np.ndarray, Dict], np.ndarray],
        num_episodes: int = 100,
        render: bool = False,
        max_steps: Optional[int] = None,
        extra_info_fn: Optional[Callable[[gym.Env, Dict], Dict]] = None
    ) -> EvaluationMetrics:
        """
        在单个任务上评测策略

        Args:
            policy: 策略函数，输入 (observation, info) 输出 action
            num_episodes: 评测回合数
            render: 是否渲染环境
            max_steps: 最大步数限制（None 表示使用环境默认值）
            extra_info_fn: 额外信息提取函数

        Returns:
            EvaluationMetrics: 评测指标对象
        """
        env = self.make_env()

        # 获取环境默认最大步数
        if max_steps is None:
            max_steps = getattr(env, '_max_episode_steps', float('inf'))

        # 记录数据
        episode_lengths = []
        episode_rewards = []
        episode_success = []
        episode_optimal = []
        episode_collisions = []
        episode_forces = []

        for episode in range(num_episodes):
            # 重置环境
            obs, info = env.reset()

            done = False
            step_count = 0
            episode_reward = 0.0
            episode_collisions = 0
            episode_force_list = []
            path_length = 0.0
            optimal_path = info.get('optimal_path_length', 1.0)

            # 额外指标收集器
            extra_collector = {}

            while not done and step_count < max_steps:
                # 渲染（如需要）
                if render:
                    env.render()

                # 策略推理
                action = policy(obs, info)

                # 环境一步执行
                obs, reward, terminated, truncated, info = env.step(action)

                done = terminated or truncated
                step_count += 1
                episode_reward += reward
                path_length += 1.0

                # 收集安全性指标
                if 'collision' in info:
                    episode_collisions += int(info['collision'])
                if 'force'
                # 收集受力数据
                if 'force' in info:
                    episode_force_list.append(float(info['force']))

                # 收集额外指标
                if extra_info_fn is not None:
                    extra = extra_info_fn(env, info)
                    for k, v in extra.items():
                        extra_collector.setdefault(k, []).append(v)

            # 记录本回合数据
            is_success = bool(info.get('success', False))
            episode_lengths.append(step_count)
            episode_rewards.append(episode_reward)
            episode_success.append(is_success)

            # 计算路径效率
            optimal_ratio = optimal_path / max(path_length, optimal_path)
            episode_optimal.append(optimal_ratio)

            # 记录安全指标
            episode_collisions_list.append(episode_collisions)
            if episode_force_list:
                episode_forces.append(max(episode_force_list))

            # 记录额外指标
            self.episode_records.append({
                'episode': episode,
                'success': is_success,
                'length': step_count,
                'reward': episode_reward,
                'collisions': episode_collisions,
                'max_force': max(episode_force_list) if episode_force_list else 0.0,
                'extra': {k: np.mean(v) for k, v in extra_collector.items()}
            })

            # 定期打印进度
            if (episode + 1) % 20 == 0:
                current_sr = sum(episode_success) / len(episode_success)
                print(f"  [{episode+1}/{num_episodes}] SR={current_sr:.2%}")

        # ============ 计算并返回评测指标 ============
        num_success = sum(episode_success)

        metrics = EvaluationMetrics(
            success_rate=num_success / num_episodes,
            avg_episode_length=float(np.mean(episode_lengths)),
            std_episode_length=float(np.std(episode_lengths)),
            avg_reward=float(np.mean(episode_rewards)),
            std_reward=float(np.std(episode_rewards)),
            optimal_path_ratio=float(np.mean(episode_optimal)),
            collision_rate=float(np.sum(episode_collisions_list)) / max(1, sum(episode_lengths)),
            max_force=float(np.max(episode_forces)) if episode_forces else 0.0,
            extra={k: float(np.mean([r['extra'][k] for r in self.episode_records
                                     if k in r['extra']]))
                   for k in extra_collector.keys()}
        )

        # 计算 SPL（成功率加权路径效率）
        # SPL = SR * 平均路径效率
        metrics.spl = metrics.success_rate * metrics.optimal_path_ratio

        return metrics

    def save_results(self, filepath: str):
        """保存评测结果到 JSON 文件"""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

        data = {
            'env_id': self.env_id,
            'benchmark_type': self.benchmark_type.value,
            'policy_name': self.policy_name,
            'seed': self.seed,
            'num_episodes': len(self.episode_records),
            'metrics': self.episode_records
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"评测结果已保存至: {filepath}")

    def print_summary(self, metrics: EvaluationMetrics):
        """打印评测汇总报告"""
        print("\n" + "=" * 60)
        print(f"Benchmark 评测汇总")
        print(f"环境: {self.env_id} | 策略: {self.policy_name}")
        print("=" * 60)

        m = metrics.to_dict()
        for key, value in m.items():
            if isinstance(value, float):
                print(f"  {key:<25}: {value:.4f}")
            else:
                print(f"  {key:<25}: {value}")

        print("=" * 60)


class MultiTaskBenchmarkEvaluator:
    """
    多任务 Benchmark 评测器
    支持跨多个任务/场景的批量评测
    """

    def __init__(
        self,
        benchmark_type: BenchmarkType,
        task_list: List[str],
        policy_name: str = "policy",
        seed: int = 42
    ):
        """
        初始化多任务评测器

        Args:
            benchmark_type: Benchmark 类型
            task_list: 任务/环境 ID 列表
            policy_name: 策略名称
            seed: 随机种子
        """
        self.benchmark_type = benchmark_type
        self.task_list = task_list
        self.policy_name = policy_name
        self.seed = seed
        self.results: Dict[str, EvaluationMetrics] = {}

    def evaluate_all(
        self,
        policy_fn: Callable[[str], Callable],
        num_episodes_per_task: int = 50,
        **kwargs
    ) -> Dict[str, EvaluationMetrics]:
        """
        在所有任务上评测策略

        Args:
            policy_fn: 任务 ID -> 策略函数的映射
            num_episodes_per_task: 每个任务的评测回合数
            **kwargs: 传递给 BenchmarkEvaluator.evaluate 的额外参数

        Returns:
            Dict[str, EvaluationMetrics]: 任务 ID -> 评测指标的映射
        """
        print(f"\n{'='*60}")
        print(f"多任务 Benchmark 评测")
        print(f"Benchmark: {self.benchmark_type.value}")
        print(f"任务数: {len(self.task_list)}")
        print(f"每任务评测回合数: {num_episodes_per_task}")
        print(f"{'='*60}\n")

        for task_id in self.task_list:
            print(f"\n>>> 评测任务: {task_id}")

            # 创建评测器
            evaluator = BenchmarkEvaluator(
                env_id=task_id,
                benchmark_type=self.benchmark_type,
                policy_name=self.policy_name,
                seed=self.seed
            )

            # 获取该任务的策略
            policy = policy_fn(task_id)

            # 评测
            try:
                metrics = evaluator.evaluate(
                    policy=policy,
                    num_episodes=num_episodes_per_task,
                    **kwargs
                )
                self.results[task_id] = metrics
                evaluator.print_summary(metrics)
            except Exception as e:
                print(f"  任务 {task_id} 评测失败: {e}")

            evaluator.close()

        return self.results

    def compute_average_metrics(self) -> EvaluationMetrics:
        """计算所有任务的平均指标"""
        all_metrics = list(self.results.values())

        avg_metrics = EvaluationMetrics()
        if not all_metrics:
            return avg_metrics

        # 对所有浮点字段取平均
        for field_name in ['success_rate', 'avg_episode_length', 'spl',
                           'collision_rate', 'avg_reward']:
            if hasattr(avg_metrics, field_name):
                values = [getattr(m, field_name) for m in all_metrics]
                setattr(avg_metrics, field_name, float(np.mean(values)))

        return avg_metrics

    def print_comparison_table(self):
        """打印多任务评测对比表"""
        print("\n" + "=" * 80)
        print(f"多任务评测对比表")
        print("=" * 80)
        print(f"{'任务':<30} {'SR':>8} {'SPL':>8} {'平均长度':>10} {'碰撞率':>10}")
        print("-" * 80)

        for task_id, metrics in self.results.items():
            print(
                f"{task_id:<30} "
                f"{metrics.success_rate:>8.2%} "
                f"{metrics.spl:>8.3f} "
                f"{metrics.avg_episode_length:>10.1f} "
                f"{metrics.collision_rate:>10.3f}"
            )

        print("-" * 80)
        avg = self.compute_average_metrics()
        print(
            f"{'平均':<30} "
            f"{avg.success_rate:>8.2%} "
            f"{avg.spl:>8.3f} "
            f"{avg.avg_episode_length:>10.1f} "
            f"{avg.collision_rate:>10.3f}"
        )
        print("=" * 80)


# ============ 使用示例 ============
if __name__ == "__main__":
    # 示例 1：单个任务评测（以 MetaWorld 为例）
    print("\n" + "#" * 60)
    print("# 示例 1：MetaWorld 单任务评测")
    print("#" * 60)

    # 注意：实际运行需要安装 metaworld
    # pip install metaworld
    # env_id = "Metaworld-reach-v1"

    evaluator = BenchmarkEvaluator(
        env_id="FetchReachDense-v2",  # 使用 FetchReach 作为示例
        benchmark_type=BenchmarkType.CUSTOM,
        policy_name="RandomPolicy"
    )

    def random_policy(observation, info):
        """随机策略（作为基线）"""
        return evaluator.env.action_space.sample()

    # 运行评测
    metrics = evaluator.evaluate(
        policy=random_policy,
        num_episodes=50,
        render=False
    )

    evaluator.print_summary(metrics)
    evaluator.save_results("benchmark_results/fetch_reach_random.json")
    evaluator.close()

    # 示例 2：多任务评测框架演示
    print("\n" + "#" * 60)
    print("# 示例 2：多任务 Benchmark 评测框架")
    print("#" * 60)

    # 定义任务列表（实际使用时替换为真实 Benchmark 任务 ID）
    sample_tasks = [
        "Metaworld-reach-v1",
        "Metaworld-pick_place-v2",
        "Metaworld-drawer_open-v1",
    ]

    multi_evaluator = MultiTaskBenchmarkEvaluator(
        benchmark_type=BenchmarkType.METAWORLD,
        task_list=sample_tasks,
        policy_name="RandomPolicy",
        seed=42
    )

    def get_policy_for_task(task_id):
        """为每个任务创建策略（示例中使用随机策略）"""
        return lambda obs, info: np.random.uniform(-1, 1, size=4)

    # 注意：实际评测时取消注释下面的代码
    # results = multi_evaluator.evaluate_all(
    #     policy_fn=get_policy_for_task,
    #     num_episodes_per_task=50
    # )
    # multi_evaluator.print_comparison_table()

    print("\n[提示] 请安装对应 Benchmark 的环境后运行真实评测：")
    print("  RLBench: pip install rlbench")
    print("  MetaWorld: pip install metaworld")
    print("  ManiSkill: pip install maniskill")
    print("  Habitat: pip install habitat-sim habitat-lab")

---

## 五、练习题

### 选择题

**1. Benchmark 的核心作用是什么？**
- A. 加速机器人本体的开发
- B. 提供标准化的评测环境和方法，实现公平比较
- C. 直接提升机器人的操作精度
- D. 替代强化学习训练

**2. SPL（Success weighted by Path Length）指标同时考虑了？**
- A. 成功率和泛化能力
- B. 成功率和路径效率
- C. 抓取稳定性和成功率
- D. 能耗和执行时间

**3. RLBench Benchmark 的主要特点是什么？**
- A. 专注于元强化学习研究
- B. 基于真实住宅 3D 扫描的室内导航
- C. 大规模视觉引导机械臂操作任务库，支持 MoveIt! 集成
- D. 高保真物理仿真和 GPU 渲染

**4. MetaWorld 的核心设计目的是？**
- A. 评测语言条件化机器人操作
- B. 为元强化学习算法提供标准化的多任务评测
- C. 提供高保真的机器人操作仿真
- D. 评估机器人在真实家庭环境中的导航能力

**5. CALVIN Benchmark 强调的核心能力是？**
- A. 单步抓取操作的精确度
- B. 长程多步任务链的执行和自然语言指令跟随
- C. 元学习算法在新任务上的适应速度
- D. 高保真物理仿真下的操作策略

**6. ManiSkill 与其他 Benchmark 相比最突出的特点是？**
- A. 支持 101 个视觉引导操作任务
- B. 明确定义了元学习的训练/测试任务划分
- C. 基于 SAPIEN 引擎的高保真物理仿真和 GPU 渲染
- D. 基于真实住宅 3D 扫描的室内导航

**7. HM3D（Habitat-Matterport 3D）的核心优势是？**
- A. 提供 101 个预定义的视觉引导操作任务
- B. 提供 50 个多任务操作 Benchmark
- C. 提供 1000 个真实住宅 3D 扫描场景的大规模导航 Benchmark
- D. 专注于语言条件化机器人操作任务

**8. 泛化能力评测的关键设计原则是？**
- A. 训练集和测试集完全相同，确保公平比较
- B. 训练集和测试集严格分离，且测试场景代表新情况
- C. 只在最简单的场景上测试以确保成功率
- D. 多次测试取平均值即可，无需其他设计

### 简答题

**9. 解释什么是 Sim-to-Real Gap，以及为什么它是具身智能 Benchmark 评测中的重要考量因素。**

**10. 对比 RLBench、MetaWorld、CALVIN、ManiSkill 四个 Benchmark 的侧重点、应用场景和核心评测指标。**

**11. 你正在开发一个桌面机器人操作任务，需要选择合适的 Benchmark 进行评测。请说明你会选择哪个 Benchmark，并给出评测方案设计（包括任务选择、指标选择、泛化测试方案）。**

---

## 六、练习题答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | Benchmark 的核心作用是标准化评测，让不同算法在统一的任务、环境、指标下进行公平比较。 |
| 2 | **B** | SPL = Success × (最优路径 / 实际路径)，同时衡量了成功率和路径效率。 |
| 3 | **C** | RLBench 提供 101 个视觉引导机械臂操作任务，支持多视角视觉输入和 MoveIt! 集成。 |
| 4 | **B** | MetaWorld 专门为元强化学习设计，明确定义了训练任务和测试任务的划分（MT10/MT50/ML10/ML45）。 |
| 5 | **B** | CALVIN 强调语言条件化长程任务链，每个任务需要连续执行 4 个子指令。 |
| 6 | **C** | ManiSkill 基于 NVIDIA SAPIEN 引擎，提供高保真物理仿真和 GPU 并行渲染。 |
| 7 | **C** | HM3D 提供 1000 个真实住宅的 Matterport 3D 扫描，是当前最大规模的室内导航 Benchmark。 |
| 8 | **B** | 泛化能力测试的核心是确保训练集和测试集严格分离，且测试场景代表算法在实际部署中会遇到的新情况。 |

### 简答题答案

**9. Sim-to-Real Gap 的概念与重要性**

**Sim-to-Real Gap（仿真-现实差距）**指的是机器人在仿真环境中训练得到的策略，在迁移到真实物理世界时性能下降的现象。这是具身智能 Benchmark 评测中的核心考量因素，原因如下：

- **物理真实性不足**：仿真器的物理参数（摩擦力、关节刚度、传感器噪声）与真实机器人存在偏差
- **视觉差异**：仿真生成的图像与真实相机拍摄的图像在纹理、光照、阴影上有本质区别
- **传感器噪声模型**：真实传感器（IMU、深度相机、力矩传感器）的噪声特性难以精确建模
- **控制延迟**：仿真中的控制循环是理想化的，真实机器人存在通信延迟和控制滞后

**评测意义**：一个在仿真 Benchmark 上表现优秀的算法，如果 Sim-to-Real Gap 过大，则无法实际部署。因此评测时应该：
1. 报告仿真指标的同时说明可能的现实差距
2. 在 Benchmark 中包含 Domain Randomization（领域随机化）测试
3. 尽可能提供实机评测子集（如 ManiSkill、RLBench 支持的仿真+实物双测）

---

**10. RLBench、MetaWorld、CALVIN、ManiSkill 四大 Benchmark 对比**

| 维度 | RLBench | MetaWorld | CALVIN | ManiSkill |
|------|---------|-----------|--------|-----------|
| **侧重点** | 视觉引导机械臂操作 | 多任务/元学习 | 语言条件化长程操作 | 高保真操作 |
| **核心任务** | 101 个视觉操作任务（抓取、放置、开门等） | 50 个多任务操作（reach/push/drawer等） | 26 个语言指令任务，4步任务链 | 20+ 高保真操作任务 |
| **仿真平台** | PyBullet | MuJoCo | PyBullet | SAPIEN |
| **视觉输入** | 多视角 RGB/D/分割 | 无（状态空间） | RGB 相机 | GPU 渲染 RGB/D/点云 |
| **核心指标** | 成功率、演示成功率 | 平均 SR、元学习适应速度 | FCR（任务链完成率）、ASR | 成功率、SPL、Sim-to-Real Gap |
| **适用研究** | 视觉策略学习、模仿学习 | 元强化学习、多任务迁移 | 语言跟随、多步规划 | Sim-to-Real、高保真策略 |

---

**11. 桌面机器人操作 Benchmark 评测方案设计**

**选择 Benchmark**：根据任务需求有三个可选方案：

| 方案 | Benchmark | 适用场景 |
|------|-----------|---------|
| **首选** | ManiSkill | 高保真操作，需要 Sim-to-Real 落地 |
| **次选** | RLBench | 视觉策略学习，强调多视角视觉输入 |
| **备选** | MetaWorld + CALVIN | 需要多任务泛化或语言指令跟随 |

**推荐方案：以 ManiSkill 为例的评测方案**

**① 任务选择**

| 任务类型 | 具体任务 | 难度级别 |
|---------|---------|---------|
| 基础操作 | pick and place、push | Easy → Medium |
| 精细操作 | peg insertion in hole | Medium → Hard |
| 多步操作 | open drawer → place → close drawer | Hard |

**② 评测指标选择**

| 指标类型 | 指标名称 | 说明 |
|---------|---------|------|
| 核心指标 | SR（成功率） | 任务完成比例，主衡量标准 |
| 效率指标 | 平均回合长度 | 操作效率 |
| 安全性指标 | 碰撞次数、最大受力 | 物理安全性 |
| 泛化指标 | 新物体 SR、新场景 SR | 跨物体/跨场景泛化 |

**③ 泛化测试方案**

```
第一阶段：同分布评测
  → 在训练场景/物体上评测，验证算法基本能力

第二阶段：物体泛化
  → 保留 20% 未见物体类别，评估在新物体上的成功率退化

第三阶段：Sim-to-Real 验证
  → 在仿真达标后（SR > 85%），在真实机器人上验证
  → 记录仿真-真实差距，分析主要失败原因
```

---

## 本章小结

| 概念 | 要点 |
|------|------|
| **Benchmark** | 标准化评测工具 = 任务集合 + 评测环境 + 评估指标 + 评测协议 |
| **RLBench** | 101 个视觉引导机械臂操作任务，多视角视觉，MoveIt! 集成 |
| **MetaWorld** | 50 个任务，明确定义元学习训练/测试划分（ML10/ML45） |
| **CALVIN** | 语言条件化长程任务链（4步），ABCD 四级难度 |
| **ManiSkill** | SAPIEN 高保真仿真，GPU 渲染，Sim-to-Real 友好 |
| **HM3D** | 1000 个真实住宅 3D 扫描场景，最大规模室内导航 Benchmark |
| **成功率（SR）** | 最核心指标，任务完成比例，对随机种子敏感需多次评测 |
| **SPL** | 同时衡量成功率和路径效率，适合导航任务 |
| **泛化能力** | 在新场景/新物体上的表现，训练-测试严格分离 |
| **Sim-to-Real Gap** | 仿真与真实的性能差距，通过 Domain Randomization 缩小 |

**延伸学习资源**：
- RLBench: `https://github.com/stepjam/RLBench`
- MetaWorld: `https://github.com/rlworkgroup/metaworld`
- CALVIN: `https://github.com/calvin-dataset/calvin`
- ManiSkill: `https://github.com/haosulab/ManiSkill`
- HM3D/Habitat: `https://github.com/facebookresearch/habitat-lab`
- Habitat-Matterport 3D Dataset: `https://matterport.com/`
