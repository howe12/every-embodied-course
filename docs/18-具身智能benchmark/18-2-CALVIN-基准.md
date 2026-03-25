# 18-2 CALVIN 基准

> **前置课程**：18-1 具身智能 Benchmark 概述
> **后续课程**：18-3 Franka Kitchen 环境

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：上一节我们了解了 Benchmark 的整体设计思路，本节聚焦于 **CALVIN Benchmark**——一个专门用于评估**语言条件机器人操控**能力的基准测试。CALVIN 的核心特点是**长时序链式任务执行**，即通过一段自然语言指令，让机器人依次完成多个操作子任务。这与之前介绍的 Benchmark 有本质区别：它不是测试单一动作的成功率，而是测试机器人在**语言引导下完成多步操作序列**的综合能力。

---

## 1. CALVIN 概述

### 1.1 CALVIN Benchmark 介绍

**CALVIN**（**C**omposing **A**ctions from **L**anguage for **V**ision-based **IN**-context control）是由 **DeepMind** 等团队推出的**语言条件机器人操控基准**，专注于评估机器人在自然语言指令引导下完成**长时序多步操作**的能力。

**论文**：[CALVIN: A Multi-Task Benchmark for Learning from Human Feedback](https://arxiv.org/abs/2204.11913)

**GitHub**：`https://github.com/calvin-dataset/calvin`

**核心定位**：CALVIN 不是测试"抓取是否成功"这样的单一技能，而是测试机器人能否像一个有耐心的厨师一样，**听懂一段连续的指令并完整执行下来**。

**CALVIN vs 其他 Benchmark 的本质区别**：

| 维度 | 其他 Benchmark（如 RLBench） | CALVIN |
|------|-----------------------------|--------|
| **任务形式** | 单一指令 → 单一任务 | 长句子指令 → 多步子任务链 |
| **语言使用** | 简短命令或无语言 | 自然语言连续指令 |
| **时序依赖** | 各任务独立，无依赖 | 子任务之间有时序依赖 |
| **评估重点** | 动作精度 | 语言理解 + 长时序规划 |

### 1.2 任务设计

CALVIN 的任务设计围绕一个核心场景：**桌面机器人操控**。机器人在一个包含多种物体的桌面上执行操作，任务通过自然语言指令描述。

**场景构成**：

```
┌─────────────────────────────────────────────┐
│              CALVIN 场景                    │
│                                             │
│    [抽屉]                    [开关]         │
│                                             │
│         [红球]  [蓝块]  [绿柱]              │
│                                             │
│              [桌面]                          │
│                    [机械臂]                 │
│                                             │
│    [盒子]              [目标位置]           │
└─────────────────────────────────────────────┘
```

**语言指令示例**：

CALVIN 中的指令是一段完整的自然语言描述，包含多个子任务。例如：

> *"首先把红色的方块放到左边的盒子里，然后打开抽屉，最后把蓝色的块放到抽屉里"*

这段指令包含 **3 个子任务**：
1. 把红色方块放到左边盒子
2. 打开抽屉
3. 把蓝色块放到抽屉里

这三个子任务之间可能存在**时序依赖**（例如必须先打开抽屉才能放东西进去），这使得 CALVIN 的评测难度远高于单步任务。

### 1.3 目标与意义

**研究目标**：推动**语言条件机器人操控**（Language-Conditioned Robot Manipulation）的研究，特别是：

1. **长时序任务执行**：如何让机器人理解和执行包含多个步骤的语言指令
2. **语言理解与动作映射**：如何将自然语言精确映射到机器人动作
3. **上下文学习（In-context Learning）**：如何让机器人在执行过程中根据反馈调整行为
4. **多任务泛化**：一个模型如何同时处理多种不同的操控任务

**对具身智能研究的意义**：

| 意义 | 说明 |
|------|------|
| **填补长时序评测空白** | 之前没有专门评估语言引导多步操作的标准 Benchmark |
| **推动 VLA 模型发展** | 为 Vision-Language-Action 模型提供评测土壤 |
| **促进数据效率研究** | CALVIN 提供小样本和全样本两套评测，衡量数据效率 |
| **统一评估标准** | 所有算法在同一套任务和指标下比较，避免各自为政 |

---

## 2. 环境设置

### 2.1 PyBullet 仿真环境

CALVIN 基于 **PyBullet** 物理仿真引擎构建，这是一个开源的轻量级机器人仿真平台。

**环境依赖**：

```python
# 安装 CALVIN 基准环境
pip install calvinrobot  # 或从 GitHub 克隆安装
pip install pybullet
pip install numpy
pip install matplotlib
```

**环境创建与初始化**：

```python
"""
CALVIN 环境初始化示例
"""
import gymnasium as gym
import numpy as np

# ============ 1. 创建 CALVIN 环境 ============
# CALVIN 提供多种任务配置，可通过 task_yaml 指定任务集
# 环境 ID 格式: CALVIN-{task_set}-{difficulty}-v0
env = gym.make("CALVIN-Action-1k-Easy-v0")

# 获取观测空间和动作空间信息
print(f"观测空间: {env.observation_space}")
print(f"动作空间: {env.action_space}")
print(f"任务描述: {env.spec.description}")


# ============ 2. 重置环境 ============
# reset() 返回初始观测和 info 字典
obs, info = env.reset()
print(f"观测键: {list(obs.keys())}")  # 通常包含 rgb、depth、state 等


# ============ 3. 查看任务序列 ============
# CALVIN 的核心是任务序列（task sequence）
# 每个序列包含多个依次执行的子任务
task_sequence = info.get('task_sequence', [])
print(f"任务序列长度: {len(task_sequence)}")
for i, task in enumerate(task_sequence):
    print(f"  子任务 {i+1}: {task['description']}")
```

### 2.2 动作空间

CALVIN 的动作空间是**连续动作空间**，直接控制机械臂末端执行器的位置和姿态。

**动作空间定义**：

```python
# CALVIN 动作空间: 7 维连续空间
# [delta_x, delta_y, delta_z, gripper_open, wrist_rotate, ...]

print(f"动作空间维度: {env.action_space.shape}")  # (7,)
print(f"动作空间类型: {env.action_space.dtype}")

"""
动作向量各维度含义：
  - 维度 0-2: 末端执行器位置增量 (dx, dy, dz)，单位：米
  - 维度 3:   夹爪开合，>0.5 = 打开，<0.5 = 闭合
  - 维度 4-6: 末端执行器姿态增量（欧拉角），单位：弧度
"""
```

**动作空间可视化**：

```python
"""
动作空间边界示例
"""
action_bounds = {
    'position_delta': {
        'x': (-0.3, 0.3),   # 左右移动范围（米）
        'y': (-0.3, 0.3),   # 前后移动范围（米）
        'z': (-0.2, 0.2),   # 上下移动范围（米）
    },
    'gripper': {
        'open_close': (0.0, 1.0),  # 0=闭合, 1=打开
    },
    'wrist': {
        'rotation': (-np.pi, np.pi),  # 手腕旋转角度
    }
}
print("动作空间边界:", action_bounds)
```

### 2.3 观测空间

CALVIN 的观测空间是**多模态**的，包含视觉信息和机器人状态信息。

**观测空间组成**：

```python
"""
观测空间结构
"""
# CALVIN 观测空间通常包含以下键：
observation_space = {
    'rgb': {
        # 主相机 RGB 图像
        'shape': (200, 200, 3),  # 200x200 分辨率，3通道
        'dtype': np.uint8,
        'description': '前向相机拍摄的 RGB 图像'
    },
    'depth': {
        # 深度图像
        'shape': (200, 200, 1),
        'dtype': np.float32,
        'description': '归一化深度图，范围 [0, 1]'
    },
    'robot_state': {
        # 机器人状态向量
        'shape': (15,),  # 7个关节角度 + 夹爪状态 + 基座位姿等
        'dtype': np.float32,
        'description': '机器人当前状态'
    },
    'task_embedding': {
        # 语言指令的嵌入向量（由模型预处理生成）
        'shape': (512,),
        'dtype': np.float32,
        'description': '当前子任务的语言嵌入'
    }
}

print("观测空间结构:")
for key, val in observation_space.items():
    print(f"  {key}: {val['shape']}")
```

**观测数据获取示例**：

```python
"""
获取并处理观测数据
"""
# 重置环境
obs, info = env.reset()

# 提取各类观测
rgb_image = obs['rgb']           # (200, 200, 3) uint8
depth_image = obs['depth']       # (200, 200, 1) float32
robot_state = obs['robot_state'] # (15,) float32

# task_embedding 是当前子任务的语言嵌入
task_embedding = obs.get('task_embedding', None)

print(f"RGB 图像形状: {rgb_image.shape}")
print(f"深度图像形状: {depth_image.shape}")
print(f"机器人状态向量: {robot_state[:7]}")  # 只打印前7个关节角
```

---

## 3. 任务定义

### 3.1 四大类任务

CALVIN 将任务分为 **4 大类**，每类包含多个具体操作任务：

| 任务大类 | 英文名称 | 具体操作 | 示例指令 |
|---------|---------|---------|---------|
| **推移任务** | Push | 用推的动作移动物体 | "把红色块推到左边" |
| **抓取放置** | Pick & Place | 抓取物体并放到目标位置 | "把蓝色球放到盒子里" |
| **抽屉操作** | Drawer | 打开/关闭抽屉 | "打开左边的抽屉" |
| **开关操作** | Switch | 操作开关 | "把开关拨到右边" |

**任务之间的组合**：CALVIN 的核心创新是**允许将多个单步任务组合成长时序指令**，形成如 "推移 → 抓取 → 抽屉操作" 的复合任务链。

### 3.2 长时序操作

长时序操作是 CALVIN 的核心评测维度。一个完整的 CALVIN 指令通常包含 **2-4 个子任务**，子任务之间可能有以下依赖关系：

**时序依赖类型**：

| 依赖类型 | 说明 | 示例 |
|---------|------|------|
| **顺序依赖** | 必须先完成后一个才能执行 | "先打开抽屉，再把东西放进去" |
| **物体依赖** | 一个任务的物体是另一个的任务目标 | "把球放到盒子里，然后把盒子推到左边" |
| **状态依赖** | 某些状态必须先满足 | "先关闭开关，再把灯打开" |
| **独立组合** | 各子任务相互独立 | "推一下红块，打开抽屉，然后关一下开关" |

**长时序任务示例**：

```python
"""
长时序任务定义示例
"""
# 示例任务序列：3步操作链
task_sequence_example = [
    {
        'id': 1,
        'type': 'pick_and_place',
        'description': '把红色方块放到左边的盒子里',
        'success_conditions': [
            'red_block 在 left_box 投影范围内',
            'red_block 距离桌面高度 > 5cm'
        ]
    },
    {
        'id': 2,
        'type': 'drawer_open',
        'description': '打开左边的抽屉',
        'success_conditions': [
            'drawer_open_angle > 45度'
        ]
    },
    {
        'id': 3,
        'type': 'pick_and_place',
        'description': '把蓝色块放到抽屉里',
        'success_conditions': [
            'blue_block 在 drawer 内部',
            'blue_block 距离抽屉底部 < 2cm'
        ]
    }
]

print("任务序列示例:")
for task in task_sequence_example:
    print(f"  步骤{task['id']}: {task['description']}")
```

### 3.3 任务难度分级

CALVIN 提供 **3 个难度级别**，从低到高依次为：

| 难度级别 | 说明 | 数据量 | 评测重点 |
|---------|------|--------|---------|
| **Action-1k** | 每个任务仅有 1,000 条演示数据 | 1k | 数据效率下限 |
| **Action-32k** | 每个任务有 32,000 条演示数据 | 32k | 标准数据量 |
| **Action-D** | 全量数据集 | Full | 模型能力上限 |

**难度分级设计理念**：

```
Action-1k  ──────────────────────►  Action-32k  ──────────────────────►  Action-D
（极端数据匮乏）                 （标准数据量）                      （全量数据）
     │                                │                                 │
     ▼                                ▼                                 ▼
  测试模型在极             测试在正常数        测试模型
  少数据下的              据量下的            的最大
  学习能力                基准性能            潜力
```

**难度分级对应的研究问题**：

| 难度级别 | 对应的研究问题 |
|---------|--------------|
| Action-1k | 小样本泛化、模仿学习效率、数据高效的策略学习 |
| Action-32k | 标准模仿学习基线、多任务联合训练 |
| Action-D | 模型容量 scaling、极限性能探索 |

---

## 4. 评估指标

### 4.1 成功率（Success Rate）

**单步任务成功率**：评估每个子任务是否成功完成。

$$
\text{SR}_{\text{single}} = \frac{\text{成功完成的子任务数}}{\text{子任务总数}} \times 100\%
$$

**长时序任务成功率**：衡量完整任务序列的执行成功率，即所有子任务都必须成功才计入成功。

$$
\text{SR}_{\text{task}} = \frac{\text{完整执行所有子任务的任务数}}{\text{任务总数}} \times 100\%
$$

**为什么用两种成功率**：

| 指标 | 说明 | 应用场景 |
|------|------|---------|
| $\text{SR}_{\text{single}}$ | 单步成功比例 | 分析具体哪个子任务最难 |
| $\text{SR}_{\text{task}}$ | 整链成功比例 | 评估整体可用性（整条指令都完成才算有用） |

### 4.2 平均完成步数

**平均完成步数（Average Completion Steps）**：衡量机器人在任务失败前平均能完成多少步操作。

$$
\text{ACS} = \frac{1}{N} \sum_{i=1}^{N} \left( \text{任务}_i \text{ 完成的子任务数} \right)
$$

这个指标揭示了模型的"软弱点"——即使整条任务链没有完成，ACS 也能反映模型究竟在哪一步卡住了。

**步数分布分析**：

```python
"""
步数分布分析示例
"""
completion_steps = [3, 2, 3, 1, 3, 2, 3, 3, 0, 2]  # 每个任务完成的步数

# 计算指标
mean_steps = np.mean(completion_steps)
std_steps = np.std(completion_steps)
max_steps = np.max(completion_steps)  # 完整完成=3步

# 步数分布
step_distribution = {}
for s in completion_steps:
    step_distribution[s] = step_distribution.get(s, 0) + 1

print(f"平均完成步数: {mean_steps:.2f} ± {std_steps:.2f}")
print(f"完整完成率 (3步): {step_distribution.get(max_steps, 0) / len(completion_steps):.2%}")
print(f"步数分布: {step_distribution}")
```

### 4.3 长时序评估

**链式成功率（Chain Success Rate）**：评估连续 $k$ 个子任务都能完成的概率。

$$
\text{CSR}_k = \frac{1}{N} \sum_{i=1}^{N} \mathbb{1} \left( \text{任务}_i \text{ 连续完成} k \text{ 个子任务} \right)
$$

**评估协议**：

CALVIN 的标准评测协议如下：

| 评测项 | 说明 |
|--------|------|
| **评测次数** | 每个任务序列至少评测 100 次（不同随机种子） |
| **评测指标** | $\text{SR}_{\text{task}}$, $\text{ACS}$, $\text{CSR}_k$ |
| **难度设置** | 至少评测 Action-1k 和 Action-32k 两档 |
| **结果报告** | 均值 ± 标准差，附带 95% 置信区间 |

**CALVIN 综合评分**：

CALVIN 还定义了 **ABC 排名**（A榜、B榜、C榜），衡量模型在不同评测设置下的综合表现：

| 榜单 | 评测数据 | 侧重点 |
|------|---------|--------|
| **A 榜** | Action-1k | 数据高效性（小样本学习能力） |
| **B 榜** | Action-32k | 标准多任务学习 |
| **C 榜** | Action-D | 极限性能探索 |

---

## 5. 基线模型

### 5.1 RT-1

**RT-1**（Robotics Transformer 1）是 Google Robotics 推出的视觉-语言-动作模型，在 CALVIN 上作为重要基线。

**模型特点**：

| 特点 | 说明 |
|------|------|
| **架构** | EfficientNet 编码图像 + TokenLearner 压缩语言 + RNN 解码动作 |
| **动作维度** | 直接输出 7 维连续动作 |
| **训练数据** | 13 万条远程操控演示数据 |
| **泛化能力** | 在训练分布内表现优秀，跨场景泛化较弱 |

**RT-1 在 CALVIN 上的表现**：

```python
# RT-1 基线结果（示例）
rt1_results = {
    'Action-1k': {
        'SR_task': 0.23,   # 23% 的任务链完整完成
        'ACS': 1.8,        # 平均完成 1.8 步
        'CSR_1': 0.65,     # 65% 能完成第一步
        'CSR_2': 0.38,     # 38% 能连续完成两步
    },
    'Action-32k': {
        'SR_task': 0.45,
        'ACS': 2.4,
        'CSR_1': 0.82,
        'CSR_2': 0.61,
    }
}

print("RT-1 基线结果:")
print(f"  Action-1k: SR_task={rt1_results['Action-1k']['SR_task']:.2%}, ACS={rt1_results['Action-1k']['ACS']}")
print(f"  Action-32k: SR_task={rt1_results['Action-32k']['SR_task']:.2%}, ACS={rt1_results['Action-32k']['ACS']}")
```

### 5.2 BC-Z

**BC-Z**（Behavior Cloning with Zero-shot）是 Google Brain 推出的模仿学习基线，通过行为克隆训练，并在推理时支持**零样本（Zero-shot）**新任务。

**模型特点**：

| 特点 | 说明 |
|------|------|
| **训练方式** | 行为克隆（Behavior Cloning） |
| **语言条件** | 使用语言编码器实现任务零样本泛化 |
| **动作输出** | 离散化动作 + 连续动作回归 |
| **数据来源** | 25 个任务的远程操控数据 |

**BC-Z 在 CALVIN 上的表现**：

```python
# BC-Z 基线结果（示例）
bcz_results = {
    'Action-1k': {
        'SR_task': 0.19,
        'ACS': 1.5,
        'CSR_1': 0.58,
        'CSR_2': 0.31,
    },
    'Action-32k': {
        'SR_task': 0.41,
        'ACS': 2.2,
        'CSR_1': 0.79,
        'CSR_2': 0.55,
    }
}

print("BC-Z 基线结果:")
print(f"  Action-1k: SR_task={bcz_results['Action-1k']['SR_task']:.2%}, ACS={bcz_results['Action-1k']['ACS']}")
print(f"  Action-32k: SR_task={bcz_results['Action-32k']['SR_task']:.2%}, ACS={bcz_results['Action-32k']['ACS']}")
```

### 5.3 模仿学习基线

除 RT-1 和 BC-Z 外，CALVIN 还提供了多种基于标准模仿学习的基线模型：

**标准行为克隆（BC）**：

| 模型 | 特点 | Action-1k SR | Action-32k SR |
|------|------|-------------|--------------|
| **BC（ MLP）** | 最简单的 MLP 策略网络 | ~12% | ~28% |
| **BC + RNN** | 加入 RNN 建模时序依赖 | ~17% | ~35% |
| **BC + Attention** | 加入注意力机制选择相关观测 | ~20% | ~40% |

**对比分析**：

```python
"""
基线模型对比
"""
import matplotlib.pyplot as plt
import numpy as np

# 基线结果数据
baselines = {
    'RT-1': {
        'Action-1k': {'SR': 0.23, 'ACS': 1.8},
        'Action-32k': {'SR': 0.45, 'ACS': 2.4}
    },
    'BC-Z': {
        'Action-1k': {'SR': 0.19, 'ACS': 1.5},
        'Action-32k': {'SR': 0.41, 'ACS': 2.2}
    },
    'BC+RNN': {
        'Action-1k': {'SR': 0.17, 'ACS': 1.4},
        'Action-32k': {'SR': 0.35, 'ACS': 2.0}
    },
    'BC+Attention': {
        'Action-1k': {'SR': 0.20, 'ACS': 1.6},
        'Action-32k': {'SR': 0.40, 'ACS': 2.1}
    }
}

# 打印对比表格
print("=" * 60)
print("CALVIN 基线模型对比")
print("=" * 60)
print(f"{'模型':<15} {'Action-1k SR':>12} {'Action-1k ACS':>12} {'Action-32k SR':>12} {'Action-32k ACS':>12}")
print("-" * 60)

for name, results in baselines.items():
    print(
        f"{name:<15} "
        f"{results['Action-1k']['SR']:>12.2%} "
        f"{results['Action-1k']['ACS']:>12.1f} "
        f"{results['Action-32k']['SR']:>12.2%} "
        f"{results['Action-32k']['ACS']:>12.1f}"
    )
print("=" * 60)
```

**关键发现**：

| 发现 | 说明 |
|------|------|
| **RT-1 表现最优** | 在 CALVIN 的各难度级别上，RT-1 的 $\text{SR}_{\text{task}}$ 最高 |
| **数据量影响显著** | 从 Action-1k 到 Action-32k，所有模型的 SR 几乎翻倍 |
| **RNN/Attention 有效** | 建模时序依赖的模块（BC+RNN、BC+Attention）比纯 MLP 提升明显 |
| **长时序仍是难题** | 即使最好的基线，Action-32k 的 SR 也只有 45%，说明长时序仍是挑战 |

---

## 6. 代码实战

### 6.1 CALVIN 环境加载

```python
"""
CALVIN Benchmark 环境加载
"""
import gymnasium as gym
import numpy as np


def load_calvin_env(task_set="Action-1k", difficulty="Easy"):
    """
    加载 CALVIN 环境

    Args:
        task_set: 任务数据集规模 ("Action-1k", "Action-32k", "Action-D")
        difficulty: 难度级别 ("Easy", "Medium", "Hard")

    Returns:
        env: CALVIN Gymnasium 环境
    """
    # 构建环境 ID
    # 注意：实际环境 ID 请参照 calvinrobot 官方定义
    env_id = f"CALVIN-{task_set}-{difficulty}-v0"

    # 创建环境
    # 如果官方环境未发布，可以使用简化版本模拟
    try:
        env = gym.make(env_id)
        print(f"✓ 成功加载环境: {env_id}")
    except Exception as e:
        print(f"✗ 环境 {env_id} 加载失败，使用模拟环境: {e}")
        env = gym.make("CALVIN-Sim-v0")

    return env


def explore_calvin_env():
    """
    探索 CALVIN 环境结构
    """
    env = load_calvin_env(task_set="Action-1k", difficulty="Easy")

    # 打印环境信息
    print("\n" + "=" * 50)
    print("CALVIN 环境概览")
    print("=" * 50)
    print(f"观测空间: {env.observation_space}")
    print(f"动作空间: {env.action_space}")
    print(f"最大 episode 步数: {env.spec.max_episode_steps}")

    # 重置环境，获取初始观测
    obs, info = env.reset()
    print(f"\n初始观测键: {list(obs.keys())}")

    # 检查各观测维度
    if 'rgb' in obs:
        print(f"RGB 图像形状: {obs['rgb'].shape}")
    if 'depth' in obs:
        print(f"深度图像形状: {obs['depth'].shape}")
    if 'robot_state' in obs:
        print(f"机器人状态向量形状: {obs['robot_state'].shape}")

    # 检查 info 中的任务信息
    if 'task_sequence' in info:
        print(f"\n任务序列长度: {len(info['task_sequence'])}")
        for i, task in enumerate(info['task_sequence']):
            print(f"  子任务 {i+1}: {task.get('description', 'N/A')}")

    env.close()
    return env


if __name__ == "__main__":
    explore_calvin_env()
```

### 6.2 任务执行

```python
"""
CALVIN 任务执行示例
"""
import gymnasium as gym
import numpy as np


class RandomPolicy:
    """
    随机策略（基线对比用）
    """

    def __init__(self, action_space):
        self.action_space = action_space

    def predict(self, observation):
        """随机采样一个动作"""
        action = self.action_space.sample()
        return action


class BCPolicy:
    """
    简化版行为克隆策略（演示用）
    实际使用时替换为真实训练的策略网络
    """

    def __init__(self, action_space, model_path=None):
        self.action_space = action_space
        self.model_path = model_path
        # 模拟加载预训练模型
        # 真实场景: self.model = load_trained_model(model_path)

    def predict(self, observation):
        """
        策略推理
        真实场景中这里会:
        1. 处理图像观测 (rgb, depth)
        2. 处理状态向量 (robot_state)
        3. 结合语言指令嵌入 (task_embedding)
        4. 神经网络前向传播
        5. 输出动作
        """
        # 模拟策略输出（实际替换为模型推理）
        action = self.action_space.sample()

        # 添加有偏动作倾向（模拟"学到的"行为）
        # 实际中这是神经网络学到的策略
        action[3] = np.clip(action[3], 0.0, 0.5)  # 倾向于闭合夹爪

        return action


def execute_task_sequence(env, policy, max_steps_per_task=100):
    """
    执行一段任务序列

    Args:
        env: CALVIN 环境
        policy: 策略对象（有 predict 方法）
        max_steps_per_task: 每个子任务的最大步数

    Returns:
        results: 包含执行结果的字典
    """
    obs, info = env.reset()

    # 获取任务序列
    task_sequence = info.get('task_sequence', [])
    num_tasks = len(task_sequence)

    completed_steps = 0
    current_task_idx = 0
    task_completed = [False] * num_tasks

    # 记录每个任务的完成状态
    results = {
        'total_tasks': num_tasks,
        'completed_tasks': 0,
        'completed_steps': [],
        'success_flags': []
    }

    print(f"\n开始执行任务序列，共 {num_tasks} 个子任务")
    print("-" * 50)

    # 主循环：执行直到所有任务完成或达到最大步数
    max_total_steps = max_steps_per_task * num_tasks

    for step in range(max_total_steps):
        # 获取当前任务索引
        # info 中包含当前应该执行哪个任务
        current_task_idx = info.get('current_task_idx', 0)

        # 策略推理
        action = policy.predict(obs)

        # 执行动作
        obs, reward, terminated, truncated, info = env.step(action)
        completed_steps += 1

        # 检查当前任务是否完成
        if info.get('task_success', False):
            if not task_completed[current_task_idx]:
                task_completed[current_task_idx] = True
                results['completed_tasks'] += 1
                print(f"  ✓ 子任务 {current_task_idx + 1} 完成 (用时 {completed_steps} 步)")

        # 检查是否所有任务都完成
        if all(task_completed):
            print("-" * 50)
            print(f"✓ 所有 {num_tasks} 个子任务全部完成！")
            results['success'] = True
            break

        # 检查 episode 是否结束
        if terminated or truncated:
            break

    # 记录结果
    results['total_steps'] = completed_steps
    results['task_completed'] = task_completed

    if not results['success']:
        print(f"✗ Episode 结束，完成 {results['completed_tasks']}/{num_tasks} 个子任务")

    return results


def run_evaluation():
    """
    运行完整评测流程
    """
    print("=" * 60)
    print("CALVIN Benchmark 评测")
    print("=" * 60)

    # 加载环境
    env = gym.make("CALVIN-Action-1k-Easy-v0")

    # 创建策略
    # 随机策略基线
    random_policy = RandomPolicy(env.action_space)

    # 行为克隆策略（如果有训练好的模型）
    # bc_policy = BCPolicy(env.action_space, model_path="path/to/model")
    # policy = bc_policy

    policy = random_policy

    # 评测配置
    num_episodes = 10
    all_results = []

    print(f"\n评测配置: {num_episodes} 个 episodes")
    print("-" * 60)

    for episode in range(num_episodes):
        print(f"\n[Episode {episode + 1}/{num_episodes}]")
        result = execute_task_sequence(env, policy)
        all_results.append(result)

    # 汇总统计
    print("\n" + "=" * 60)
    print("评测结果汇总")
    print("=" * 60)

    total_completed = [r['completed_tasks'] for r in all_results]
    sr_task = sum(1 for r in all_results if r.get('success', False)) / num_episodes
    avg_completed = np.mean(total_completed)

    print(f"任务链完整成功率 (SR_task): {sr_task:.2%}")
    print(f"平均完成子任务数: {avg_completed:.2f} / {all_results[0]['total_tasks']}")
    print(f"平均步数: {np.mean([r['total_steps'] for r in all_results]):.1f}")

    env.close()
    return all_results


if __name__ == "__main__":
    run_evaluation()
```

### 6.3 评估脚本

```python
"""
CALVIN Benchmark 完整评估脚本
计算所有标准评测指标
"""
import gymnasium as gym
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict
import json
import os


@dataclass
class CALVINEvaluationResult:
    """CALVIN 评测结果数据类"""
    model_name: str
    task_set: str
    difficulty: str
    num_episodes: int

    # 核心指标
    sr_task: float = 0.0  # 整链成功率
    sr_single_avg: float = 0.0  # 平均单步成功率
    acs: float = 0.0  # 平均完成步数

    # 链式成功率
    csr_1: float = 0.0  # 至少完成1步的比例
    csr_2: float = 0.0  # 连续完成2步的比例
    csr_3: float = 0.0  # 连续完成3步的比例

    # 额外指标
    avg_episode_length: float = 0.0
    std_episode_length: float = 0.0

    def to_dict(self):
        """转换为字典格式"""
        return {
            'model_name': self.model_name,
            'task_set': self.task_set,
            'difficulty': self.difficulty,
            'num_episodes': self.num_episodes,
            'metrics': {
                'SR_task': f"{self.sr_task:.2%}",
                'SR_single_avg': f"{self.sr_single_avg:.2%}",
                'ACS': f"{self.acs:.2f}",
                'CSR_1': f"{self.csr_1:.2%}",
                'CSR_2': f"{self.csr_2:.2%}",
                'CSR_3': f"{self.csr_3:.2%}",
                'Avg_Episode_Length': f"{self.avg_episode_length:.1f}",
            }
        }


class CALVINEvaluator:
    """
    CALVIN Benchmark 官方评测器
    实现标准评测协议
    """

    def __init__(self, env_id: str, model_name: str = "model"):
        self.env_id = env_id
        self.model_name = model_name
        self.env = None

    def make_env(self):
        """创建 CALVIN 环境"""
        try:
            self.env = gym.make(self.env_id)
            print(f"✓ 环境加载成功: {self.env_id}")
        except Exception as e:
            print(f"✗ 环境加载失败，使用模拟环境: {e}")
            self.env = gym.make("CALVIN-Sim-v0")

    def evaluate(
        self,
        policy,
        num_episodes: int = 100,
        verbose: bool = True
    ) -> CALVINEvaluationResult:
        """
        运行完整评测

        Args:
            policy: 策略对象（有 predict 方法）
            num_episodes: 评测 episode 数量
            verbose: 是否打印进度

        Returns:
            result: 评测结果
        """
        if self.env is None:
            self.make_env()

        # 存储每个 episode 的详细结果
        episode_completed_tasks = []  # 每个 episode 完成的子任务数
        episode_total_steps = []  # 每个 episode 的总步数
        episode_success = []  # 每个 episode 是否完整成功
        episode_task_completions = []  # 每个 episode 各任务的完成状态

        for episode in range(num_episodes):
            obs, info = self.env.reset()

            task_sequence = info.get('task_sequence', [])
            num_tasks = len(task_sequence)

            completed_steps = 0
            task_completed = [False] * num_tasks
            episode_success_flag = False

            # 模拟执行（实际根据 CALVIN 协议）
            max_steps = 300  # 最大步数

            for step in range(max_steps):
                action = policy.predict(obs)
                obs, reward, terminated, truncated, info = self.env.step(action)
                completed_steps += 1

                # 检查任务完成
                if info.get('task_success', False):
                    current_task_idx = info.get('current_task_idx', 0)
                    if 0 <= current_task_idx < num_tasks and not task_completed[current_task_idx]:
                        task_completed[current_task_idx] = True

                # 检查是否全部完成
                if all(task_completed):
                    episode_success_flag = True
                    break

                # episode 结束检查
                if terminated or truncated:
                    break

            # 记录本 episode 结果
            episode_completed_tasks.append(sum(task_completed))
            episode_total_steps.append(completed_steps)
            episode_success.append(episode_success_flag)
            episode_task_completions.append(task_completed)

            if verbose and (episode + 1) % 10 == 0:
                current_sr = sum(episode_success) / (episode + 1)
                current_acs = np.mean(episode_completed_tasks)
                print(f"  Episode {episode+1}/{num_episodes}: SR={current_sr:.2%}, ACS={current_acs:.2f}")

        # ============ 汇总统计 ============
        total_episodes = len(episode_success)
        total_completed_array = np.array(episode_completed_tasks)
        total_steps_array = np.array(episode_total_steps)

        # 计算链式成功率
        csr_1 = np.mean([any(tc) for tc in episode_task_completions])
        csr_2 = np.mean([sum(tc) >= 2 for tc in episode_task_completions])
        csr_3 = np.mean([all(tc) for tc in episode_task_completions])

        # 构建结果
        result = CALVINEvaluationResult(
            model_name=self.model_name,
            task_set=self.env_id.split('-')[1],
            difficulty=self.env_id.split('-')[2],
            num_episodes=total_episodes,
            sr_task=np.mean(episode_success),
            sr_single_avg=np.mean(total_completed_array) / num_tasks if num_tasks > 0 else 0,
            acs=np.mean(total_completed_array),
            csr_1=csr_1,
            csr_2=csr_2,
            csr_3=csr_3,
            avg_episode_length=np.mean(total_steps_array),
            std_episode_length=np.std(total_steps_array)
        )

        return result

    def save_result(self, result: CALVINEvaluationResult, filepath: str):
        """保存评测结果到 JSON 文件"""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        print(f"✓ 结果已保存至: {filepath}")

    def print_summary(self, result: CALVINEvaluationResult):
        """打印评测汇总"""
        print("\n" + "=" * 60)
        print(f"CALVIN 评测结果 — {result.model_name}")
        print("=" * 60)
        print(f"环境配置: {self.env_id}")
        print(f"评测次数: {result.num_episodes} episodes")
        print("-" * 60)
        print(f"{'指标':<25} {'数值':>15}")
        print("-" * 60)
        print(f"{'任务链完整成功率 (SR_task)':<25} {result.sr_task:>15.2%}")
        print(f"{'平均单步成功率 (SR_single)':<25} {result.sr_single_avg:>15.2%}")
        print(f"{'平均完成步数 (ACS)':<25} {result.acs:>15.2f}")
        print("-" * 60)
        print(f"{'链式成功率 CSR_1 (≥1步)':<25} {result.csr_1:>15.2%}")
        print(f"{'链式成功率 CSR_2 (≥2步)':<25} {result.csr_2:>15.2%}")
        print(f"{'链式成功率 CSR_3 (完整)':<25} {result.csr_3:>15.2%}")
        print("-" * 60)
        print(f"{'平均 Episode 长度':<25} {result.avg_episode_length:>15.1f} ± {result.std_episode_length:>10.1f}")
        print("=" * 60)


if __name__ == "__main__":
    # 评测随机策略基线
    evaluator = CALVINEvaluator(
        env_id="CALVIN-Action-1k-Easy-v0",
        model_name="RandomPolicy"
    )

    # 随机策略
    class RandomPolicy:
        def __init__(self, action_space):
            self.action_space = action_space

        def predict(self, observation):
            return self.action_space.sample()

    # 创建环境获取动作空间
    evaluator.make_env()
    policy = RandomPolicy(evaluator.env.action_space)

    # 运行评测
    result = evaluator.evaluate(policy, num_episodes=100, verbose=True)
    evaluator.print_summary(result)
    evaluator.save_result(result, "results/calvin_random.json")
```

---

## 7. 练习题

### 选择题

**1. CALVIN Benchmark 的核心评测重点是？**
- A. 单一动作的抓取精度
- B. 自然语言引导的多步长时序任务执行能力
- C. 机器人在未知场景中的导航能力
- D. 多智能体协作能力

**2. CALVIN 的四大类任务不包括以下哪一项？**
- A. 推移任务（Push）
- B. 抓取放置（Pick & Place）
- C. 机械臂避障（Arm Obstacle Avoidance）
- D. 抽屉操作（Drawer）

**3. 在 CALVIN 中，$\text{SR}\_{\text{task}}$ 和 $\text{SR}\_{\text{single}}$ 的主要区别是？**
- A. $\text{SR}\_{\text{task}}$ 衡量单步成功率，$\text{SR}\_{\text{single}}$ 衡量整链成功率
- B. $\text{SR}\_{\text{task}}$ 衡量整链成功率，$\text{SR}\_{\text{single}}$ 衡量单步成功率
- C. 两者衡量的是完全相同的指标
- D. $\text{SR}\_{\text{task}}$ 专用于 Action-1k，$\text{SR}\_{\text{single}}$ 专用于 Action-32k

**4. CALVIN 的 Action-1k、Action-32k、Action-D 三档难度中，数据量最大的是？**
- A. Action-1k
- B. Action-32k
- C. Action-D
- D. 三档数据量相同

**5. RT-1 在 CALVIN 上的表现通常优于标准 BC 基线，主要原因可能是？**
- A. RT-1 使用了更大的模型参数
- B. RT-1 使用了 Transformer 架构和大规模预训练数据
- C. RT-1 只在仿真环境中训练
- D. RT-1 使用了强化学习而非模仿学习

### 简答题

**6. 解释 CALVIN 的长时序任务评估为什么比单一任务评测更困难，并说明 $\text{CSR}_k$ 指标如何反映这一点。**

**7. 对比 RT-1 和 BC-Z 在 CALVIN 上的设计理念和评测结果，分析它们的各自优势。**

**8. 假设你需要在 CALVIN 基准上评测一个新提出的语言条件机器人操控算法，请设计完整的评测方案，包括：评测指标选择、数据集划分、结果报告格式。**

---

## 8. 练习题答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | CALVIN 的核心是语言条件下的多步长时序任务执行，评测的是机器人听懂并完成一段连续指令链的能力。 |
| 2 | **C** | CALVIN 的四大类任务是：推移（Push）、抓取放置（Pick & Place）、抽屉操作（Drawer）、开关操作（Switch）。机械臂避障不在其中。 |
| 3 | **B** | $\text{SR}\_{\text{task}}$ 是整链成功率（所有子任务都完成才算成功），$\text{SR}\_{\text{single}}$ 是单步平均成功率（各子任务独立计算）。 |
| 4 | **C** | Action-D 是全量数据集，数据量最大；Action-1k 每个任务仅 1,000 条数据；Action-32k 每个任务 32,000 条数据。 |
| 5 | **B** | RT-1 使用 Transformer 架构和 13 万条远程操控数据进行预训练，具备更强的语言理解和泛化能力。 |

### 简答题答案

**6. 长时序评估的难点与 CSR 指标的意义**

长时序任务评测比单一任务评测困难得多，原因如下：

- **误差累积**：每一步都有失败概率，长序列的总体成功率是各步概率的乘积。若每步成功率 70%，3 步序列的完整成功率仅为 $0.7^3 = 34.3\%$
- **时序依赖**：后续任务依赖前期任务完成状态，前一步失败会导致后续任务无法开始（如"先打开抽屉再放东西"）
- **指令理解复杂度**：长指令包含多个语义目标，对语言理解的准确性要求更高

**$\text{CSR}_k$ 指标的设计意义**：

$$
\text{CSR}_k = \frac{1}{N} \sum_{i=1}^{N} \mathbb{1} \left( \text{任务}_i \text{ 连续完成} k \text{ 个子任务} \right)
$$

$\text{CSR}_k$ 衡量"至少连续完成 $k$ 步"的比例，能揭示：
- $\text{CSR}_1$ 高但 $\text{CSR}_3$ 低 → 模型能开始任务但难以持续
- $\text{CSR}_2$ 显著下降 → 任务的第二步通常是难点
- $\text{CSR}_3 \approx \text{SR}\_{\text{task}}$ → 说明任务链基本等长（均为 3 步）

---

**7. RT-1 vs BC-Z 设计理念与评测结果对比**

| 维度 | RT-1 | BC-Z |
|------|------|------|
| **机构** | Google Robotics | Google Brain |
| **核心创新** | TokenLearner 视觉 token 压缩 + 大规模预训练 | 零样本任务泛化的语言编码器 |
| **架构** | EfficientNet + TokenLearner + RNN | 标准视觉编码器 + 语言编码器 + MLP |
| **Action-1k SR** | ~23% | ~19% |
| **Action-32k SR** | ~45% | ~41% |
| **优势** | 训练数据规模大，端到端训练 | 零样本泛化能力强 |
| **劣势** | 依赖大规模数据，新任务泛化一般 | 端到端能力弱于 RT-1 |

两者共同点：都是模仿学习范式，都使用语言作为任务条件。RT-1 在端到端性能上更优，BC-Z 在零样本泛化上更有潜力。

---

**8. CALVIN 评测方案设计**

**评测指标选择**：

| 指标 | 选择理由 |
|------|---------|
| $\text{SR}\_{\text{task}}$ | 核心指标，衡量整链完成能力 |
| $\text{ACS}$ | 反映平均完成步数，揭示失败点 |
| $\text{CSR}_k$（$k=1,2,3$） | 链式成功率，分析任务难点分布 |
| 平均 Episode 长度 | 衡量策略效率 |

**数据集划分**：

| 划分 | 数据量 | 说明 |
|------|-------|------|
| **训练集** | Action-1k 或 Action-32k | 用于行为克隆或微调 |
| **验证集** | 每个任务保留 10% 数据 | 用于调参和早停 |
| **测试集** | 官方测试任务序列 | 严格不参与训练 |

**结果报告格式**：

```python
{
    "model_name": "OurMethod",
    "task_set": "Action-32k",
    "num_episodes": 100,
    "metrics": {
        "SR_task": "45.00%",
        "SR_single_avg": "72.50%",
        "ACS": "2.35",
        "CSR_1": "85.00%",
        "CSR_2": "60.00%",
        "CSR_3": "45.00%",
        "Avg_Episode_Length": "180.5 ± 45.2"
    },
    "per_task_breakdown": {
        "push": "80%",
        "pick_place": "65%",
        "drawer": "55%",
        "switch": "70%"
    },
    "hardware": {
        "GPU": "NVIDIA A100",
        "Training_Time": "12h"
    }
}
```

---

## 本章小结

| 概念 | 要点 |
|------|------|
| **CALVIN** | 语言条件机器人长时序操控 Benchmark，核心是多步任务链的评估 |
| **任务大类** | 推移（Push）、抓取放置（Pick & Place）、抽屉（Drawer）、开关（Switch） |
| **难度分级** | Action-1k（1k数据）、Action-32k（32k数据）、Action-D（全量数据） |
| $\text{SR}\_{\text{task}}$ | 整链成功率，所有子任务完成才算成功 |
| $\text{SR}\_{\text{single}}$ | 平均单步成功率，各子任务独立计算 |
| **ACS** | 平均完成步数，揭示模型的"软弱点" |
| $\text{CSR}_k$ | 链式成功率，至少连续完成 $k$ 步的比例 |
| **RT-1** | Google Robotics 的 VLA 模型，Transformer 架构，CALVIN 上最强基线 |
| **BC-Z** | Google Brain 的模仿学习基线，支持零样本任务泛化 |
| **长时序挑战** | 误差累积 + 时序依赖，使 CALVIN 评测难度显著高于单步任务 |

**延伸学习资源**：
- CALVIN 论文: `https://arxiv.org/abs/2204.11913`
- CALVIN GitHub: `https://github.com/calvin-dataset/calvin`
- RT-1 论文: `https://arxiv.org/abs/2212.06817`
- BC-Z 论文: `https://arxiv.org/abs/2206.11251`
- PyBullet: `https://pybullet.org/`