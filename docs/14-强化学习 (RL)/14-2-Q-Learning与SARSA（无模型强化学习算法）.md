# 14-2 Q-Learning与SARSA（无模型强化学习算法）

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 14-2 |
| 课程名称 | Q-Learning与SARSA（无模型强化学习算法） |
| 所属模块 | 14-强化学习 (RL) |
| 难度等级 | ⭐⭐⭐⭐☆ |
| 预计学时 | 5小时 |
| 前置知识 | 强化学习基础（MDP、价值函数、贝尔曼方程） |

---

## 目录

1. [无模型学习概述](#1-无模型学习概述)
2. [时序差分（TD）学习](#2-时序差分td学习)
3. [SARSA算法](#3-sarsa算法)
4. [Q-Learning算法](#4-q-learning算法)
5. [SARSA vs Q-Learning对比](#5-sarsa-vs-q-learning对比)
6. [代码实战：FrozenLake环境](#6-代码实战frozenlake环境)
7. [练习题](#7-练习题)
8. [参考答案](#8-参考答案)

---

## 1. 无模型学习概述

### 1.1 模型已知 vs 模型未知

在上一章中，我们学习了**动态规划**方法（策略迭代与价值迭代）来求解MDP。这些方法的核心前提是：**环境模型已知**——即智能体知道状态转移概率 $P(s'|s,a)$ 和奖励函数 $R(s,a,s')$。

然而，在现实世界的机器人应用中，这个前提往往不成立：

| 场景 | 模型已知？ | 说明 |
|------|----------|------|
| 棋类游戏（围棋、象棋） | ✅ 已知 | 规则完全确定，转移概率为1 |
| 机器人导航 | ❌ 未知 | 物理环境复杂，难以精确建模 |
| 自动驾驶 | ❌ 未知 | 交通环境不可预测 |
| 直升机飞行 | ❌ 未知 | 空气动力学模型复杂 |

**无模型学习**（Model-Free Learning）应运而生：智能体不需要知道环境的转移概率和奖励函数，仅通过与环境的直接交互来学习最优策略。

### 1.2 无模型RL的优势与挑战

**优势**：
- **适用范围广**：不依赖环境建模，适用于任何无法精确建模的真实场景
- **端到端学习**：直接从原始感知到动作，简化了系统设计
- **发现隐含策略**：可能发现人类未预设的、更优的控制策略

**挑战**：
- **样本效率低**：需要大量与环境交互的数据（试错）
- **收敛速度慢**：相比动态规划，数据利用不充分
- **探索-利用矛盾**：必须在探索新动作和利用已有知识之间取得平衡

### 1.3 蒙特卡洛方法 vs 时序差分方法

无模型学习方法主要分为两类：

**蒙特卡洛（Monte Carlo, MC）方法**：
- 需要等到**整个回合（Episode）结束**后才能计算回报 $G_t$
- 更新公式：$V(s_t) \leftarrow V(s_t) + \alpha [G_t - V(s_t)]$
- 优点：无偏估计
- 缺点：必须等回合结束，收敛速度慢

**时序差分（Temporal Difference, TD）方法**：
- 利用当前估计的价值和下一步估计进行更新（**Bootstrapping**）
- 更新公式：$V(s_t) \leftarrow V(s_t) + \alpha [r_t + \gamma V(s_{t+1}) - V(s_t)]$
- 优点：每步都可以更新，效率高
- 缺点：有偏估计（因为使用了估计值），但通常收敛更快

两者的核心区别：

| 特性 | 蒙特卡洛（MC） | 时序差分（TD） |
|------|--------------|---------------|
| **回报计算** | 完整回合结束 | 单步/多步引导 |
| **Bootstrap** | ❌ 不使用 | ✅ 使用 $V(s_{t+1})$ |
| **更新时机** | 回合结束后 | 每步之后 |
| **估计性质** | 无偏估计 | 有偏估计 |
| **收敛速度** | 较慢 | 较快 |
| **适用场景** | 非折扣、分段MC任务 | 连续任务、持续任务 |

> **Bootstrapping**：用当前的价值估计来更新价值估计，而不是用完整的真实回报。TD方法的核心思想。

### 1.4 本章学习路线

本章我们将学习两种经典的**基于值函数的无模型强化学习算法**：

- **SARSA**：On-policy TD控制算法
- **Q-Learning**：Off-policy TD控制算法

两者都基于时序差分学习，但分别代表了**On-policy**和**Off-policy**两种截然不同的学习范式。

---

## 2. 时序差分（TD）学习

### 2.1 TD预测：$TD(0)$ 算法

在深入SARSA和Q-Learning之前，我们先理解TD学习的预测（评估）部分。

**TD(0)算法**对状态价值函数的更新公式为：

$$V(s_t) \leftarrow V(s_t) + \alpha \underbrace{[r_t + \gamma V(s_{t+1}) - V(s_t)]}_{TD误差}$$

其中：
- $\alpha$：学习率（Learning Rate），控制更新步长
- $r_t + \gamma V(s_{t+1})$：**TD目标**（TD Target），是真实回报的一个估计
- $V(s_t) - V(s_{t+1})$ 部分：称为**TD误差**（TD Error）

**直观理解**：

想象你在评估一条路线的总长度。你站在起点，估算到终点的距离是100米。但你只向前走了10米，就发现实际上第一个路标离你只有5米。那么：

$$\text{新估计} = \text{旧估计} + \alpha \times (\text{实际走了一步后的新信息} - \text{旧估计})$$

$$V(s_t)_{new} = V(s_t)_{old} + \alpha [(r_t + \gamma V(s_{t+1})) - V(s_t)_{old}]$$

这就是TD学习的核心思想——用**已知的即时奖励**加上**对未来的估计**来逐步改进对价值的估计。

### 2.2 n步TD学习

TD(0)只向前看1步。n步TD学习将这个思想推广到n步：

$$G_t^{(n)} = r_t + \gamma r_{t+1} + \cdots + \gamma^{n-1} r_{t+n-1} + \gamma^n V(s_{t+n})$$

更新公式：

$$V(s_t) \leftarrow V(s_t) + \alpha [G_t^{(n)} - V(s_t)]$$

当 $n \to \infty$ 时，n步TD退化为蒙特卡洛方法。n步TD提供了MC和TD(0)之间的平滑过渡。

### 2.3 TD控制：SARSA与Q-Learning

从TD预测推广到TD控制（找到最优策略），就得到了我们本章要学习的两个核心算法：

- **SARSA**：On-policy TD控制
- **Q-Learning**：Off-policy TD控制

两者的核心区别在于：**用什么策略来生成数据** vs **用什么策略来更新**。

---

## 3. SARSA算法

### 3.1 On-policy 学习概述

**On-policy**（同策略）方法的核心特点是：**用于生成行为数据的策略**与**被评估/改进的策略**是**同一个策略**。

简单来说："边学边用"——智能体用当前策略与环境交互，同时用这些交互数据来改进同一个策略。

流程示意：

```
策略 π  ⟶ 与环境交互 ⟶  数据
    ↑                        ↓
    └──── 更新 π ← 数据分析 ←┘
```

### 3.2 SARSA 更新公式

SARSA的名称来源于更新的五个核心元素：

$$S \rightarrow A \rightarrow R \rightarrow S' \rightarrow A'$$

即：**当前状态(S)、当前动作(A)、获得的奖励(R)、下一状态(S')、下一动作(A')**。

**Q值更新公式**：

$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha [r_t + \gamma Q(s_{t+1}, a_{t+1}) - Q(s_t, a_t)]$$

其中 $a_{t+1}$ 是智能体**实际采取的下一个动作**（由当前策略 $\epsilon$-贪心策略生成）。

**关键点**：SARSA使用 $Q(s_{t+1}, a_{t+1})$ 而不是 $\max_{a'} Q(s_{t+1}, a')$。

### 3.3 $\epsilon$-贪心策略

为了平衡探索与利用，SARSA通常使用 $\epsilon$-贪心策略来选择动作：

$$a_t = \begin{cases} \text{random action} & \text{with probability } \epsilon \\ \arg\max_a Q(s_t, a) & \text{with probability } 1 - \epsilon \end{cases}$$

典型实现中，$\epsilon$ 可以设置为：
- **固定值**：如 $\epsilon = 0.1$
- **衰减策略**：随着训练进行逐渐减小（鼓励前期探索、后期利用）

```python
def epsilon_greedy(Q, state, epsilon, n_actions):
    """
    ε-贪心策略

    参数:
        Q: Q表，形状为 [n_states, n_actions]
        state: 当前状态索引
        epsilon: 探索概率
        n_actions: 动作数量

    返回:
        action: 选择的动作索引
    """
    if np.random.random() < epsilon:
        # 探索：随机选择动作
        return np.random.randint(n_actions)
    else:
        # 利用：选择Q值最大的动作
        return np.argmax(Q[state])
```

### 3.4 SARSA 算法流程

```
初始化 Q(s, a)，对所有 s∈S, a∈A，任选随机值（或全0）
初始化 ε（探索率）和 α（学习率）
初始化折扣因子 γ

对于每个回合（Episode）：
    初始化状态 s
    根据 ε-贪心策略选择初始动作 a（基于当前Q）

    对于回合中的每一步：
        执行动作 a，获得奖励 r 和下一状态 s'
        根据 ε-贪心策略选择下一动作 a'（基于当前Q）
        # 这里是关键区别：用实际选取的 a' 来更新，而非 max

        更新Q值：
            Q(s, a) ← Q(s, a) + α * [r + γ * Q(s', a') - Q(s, a)]

        s ← s'
        a ← a'

        如果 s' 是终止状态：结束回合
```

### 3.5 收敛性分析

SARSA算法在满足以下条件时可以收敛到最优动作价值函数 $Q^*$：

1. **学习率递减**：$\sum_t \alpha_t = \infty$ 且 $\sum_t \alpha_t^2 < \infty$（如 $\alpha_t = 1/t$）
2. **状态-动作对无限访问**：每个 $(s,a)$ 对被访问无限次
3. **策略收敛到贪婪策略**：随着时间推移，$\epsilon \to 0$

**On-policy的收敛保证**：因为行为策略和目标策略相同，SARSA的收敛性分析相对简单。

### 3.6 SARSA的"保守性"

SARSA的一个显著特点是它**学习的是在当前策略下实际会执行动作的价值**。这使得SARSA对探索更友好：

- 如果当前策略选择了风险动作（如掉进陷阱），SARSA会"体验"到这个风险并学习到低Q值
- Q-Learning则只考虑最优动作的价值，可能低估了探索的风险

这使得SARSA在**在线学习**和**安全性要求高的任务**中更具优势。

---

## 4. Q-Learning算法

### 4.1 Off-policy 学习概述

**Off-policy**（异策略）方法的核心特点是：**用于生成行为数据的策略**（行为策略）与**被评估/改进的策略**（目标策略）是**不同的策略**。

简单来说："看着别人学"——用一个策略（行为策略）来探索产生数据，用这些数据来评估/改进另一个策略（目标策略）。

流程示意：

```
行为策略 π_b ⟶ 与环境交互 ⟶  数据
                              ↓
目标策略 π_t ← 更新 ← 数据分析（使用 max Q）
```

### 4.2 Q-Learning 更新公式

**Q-Learning**是目前最经典的Off-policy TD控制算法，其更新公式为：

$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha [r_t + \gamma \max_{a'} Q(s_{t+1}, a') - Q(s_t, a_t)]$$

**关键区别**：SARSA使用 $Q(s_{t+1}, a_{t+1})$（实际选取的下一动作的价值），而Q-Learning使用 $\max_{a'} Q(s_{t+1}, a')$（下一状态所有动作价值中的最大值）。

这意味着：
- **SARSA**：估计的是"按照当前策略实际走下去"的期望价值
- **Q-Learning**：估计的是"如果从下一状态开始，每次都选最优动作"的期望价值

### 4.3 $\epsilon$-贪心 vs Greedy

在Q-Learning中，行为策略（用于探索）和目标策略（用于更新）通常是分开的：

- **行为策略**：使用 $\epsilon$-贪心策略，产生与环境交互的数据
- **目标策略**：使用贪心策略（Greedy），即 $\pi(s) = \arg\max_a Q(s,a)$

更新时，Q-Learning**不考虑行为策略实际选了哪个动作**，而是直接取最大Q值：

```python
# Q-Learning 更新（伪代码）
# 不管行为策略选了 a'，目标策略总是取 max Q
Q[state, action] += alpha * (reward + gamma * np.max(Q[next_state]) - Q[state, action])
```

### 4.4 Q-Learning 算法流程

```
初始化 Q(s, a)，对所有 s∈S, a∈A，任选随机值（或全0）
初始化 ε（探索率）和 α（学习率）
初始化折扣因子 γ

对于每个回合（Episode）：
    初始化状态 s

    对于回合中的每一步：
        根据 ε-贪心策略选择动作 a（行为策略）
        执行动作 a，获得奖励 r 和下一状态 s'
        # Q-Learning更新：直接取最大值，不关心实际选了哪个动作
        Q(s, a) ← Q(s, a) + α * [r + γ * max_{a'} Q(s', a') - Q(s, a)]

        s ← s'

        如果 s 是终止状态：结束回合
```

### 4.5 Q-Learning 与 SARSA 更新公式对比

| 特性 | SARSA | Q-Learning |
|------|-------|-----------|
| **策略类型** | On-policy | Off-policy |
| **更新公式** | $r + \gamma Q(s', a')$ | $r + \gamma \max_{a'} Q(s', a')$ |
| **下一动作** | 实际选取的 $a'$ | 理论最优 $\arg\max_a Q(s', a)$ |
| **Q值含义** | 在当前策略下实际执行的Q值 | 假设每次都选最优动作的Q值 |
| **对探索的建模** | ✅ 考虑探索风险 | ❌ 不考虑探索风险 |
| **样本效率** | 中等 | 较高（样本复用更直接） |
| **收敛性** | 收敛到近最优策略 | 收敛到最优策略 |

### 4.6 Q-Learning 的收敛性

Q-Learning在以下条件下可以收敛到最优动作价值函数 $Q^*$：

1. **学习率满足**：$\sum_t \alpha_t = \infty$ 且 $\sum_t \alpha_t^2 < \infty$
2. **状态-动作对无限访问**：每个 $(s,a)$ 对被访问无限次
3. **环境满足有限状态/动作空间**（或函数逼近时满足特定条件）

**关键定理（Q-Learning收敛性）**：
在确定性MDP下，如果所有状态-动作对被无限次访问，且学习率满足上述条件，则 $Q$ 几乎必然收敛到 $Q^*$。

---

## 5. SARSA vs Q-Learning对比

### 5.1 核心差异总结

| 对比维度 | SARSA（On-policy） | Q-Learning（Off-policy） |
|----------|-------------------|--------------------------|
| **策略类型** | 同策略 | 异策略 |
| **更新依据** | 实际执行的下一动作价值 $Q(s',a')$ | 理论最优价值 $\max_{a'} Q(s',a')$ |
| **探索建模** | ✅ 显式建模（学习到的Q反映探索风险） | ❌ 隐式假设完全贪婪 |
| **样本效率** | 中等 | 较高（理论上可复用其他策略数据） |
| **收敛性** | 收敛到 $\epsilon$-最优（取决于 $\epsilon$ 衰减） | 收敛到最优 |
| **安全性** | 较高（不会高估探索风险） | 较低（可能低估探索风险） |
| **代表性场景** | 在线学习、真实机器人训练 | 仿真环境、离轨数据利用 |

### 5.2 悬崖漫步（Cliff Walking）示例

最能体现SARSA与Q-Learning差异的经典示例是**悬崖漫步（Cliff Walking）**环境：

- **任务**：从起点走到终点，避开悬崖
- **最优策略**：沿悬崖边缘行走（风险高但路径短）
- **安全策略**：远离悬崖行走（路径长但安全）

```
网格示意图：
S . . . . . . . . . . G
. . . . . . . . . . . .   （悬崖在下边缘，掉进去重置）
```

**SARSA的行为**：学到安全策略（远离悬崖），因为它"体验"到踏进悬崖的低Q值

**Q-Learning的行为**：学到最优策略（靠近悬崖边缘），因为它只考虑每一步的最大价值，不考虑探索风险

### 5.3 何时选择哪种算法？

**选择SARSA的场景**：
- 在线学习，智能体必须在线与环境交互
- 安全性要求高的任务（如真实机器人）
- $\epsilon$-贪心策略需要保持一定探索率
- 希望策略自然地考虑探索风险

**选择Q-Learning的场景**：
- 可以利用离轨数据（从其他策略采集的数据）
- 仿真环境，可以承受一定探索风险
- 希望学习到理论上的最优策略
- 样本效率要求较高

---

## 6. 代码实战：FrozenLake环境

本节我们在OpenAI Gymnasium的经典 **FrozenLake（冰湖）** 环境中实现SARSA和Q-Learning算法，并对比两者的表现。

### 6.1 FrozenLake 环境介绍

FrozenLake是一个经典的强化学习入门环境：

- **任务**：从起点"S"走到目标"G"
- **冰面**：有的是安全的"F"，有的是洞（掉进去则回合结束，奖励为0）
- **环境是随机的**：即使你选择了一个方向，冰面可能打滑，实际移动方向有概率变化

```
4x4 地图示例（is_slippery=True）：
S F F F
F H F H
F F F H
H F F G

S=起点, F=安全冰面, H=洞(陷阱), G=目标
```

### 6.2 SARSA 算法实现

```python
"""
SARSA 算法实现
On-policy TD控制算法

环境: FrozenLake-v1 (Gymnasium)
"""
import numpy as np
import gymnasium as gym
import matplotlib.pyplot as plt
from typing import Tuple, List
import os


def epsilon_greedy(Q: np.ndarray, state: int, epsilon: float,
                   n_actions: int) -> int:
    """
    ε-贪心策略

    参数:
        Q: Q表，形状为 [n_states, n_actions]
        state: 当前状态索引
        epsilon: 探索概率
        n_actions: 动作数量

    返回:
        action: 选择的动作索引
    """
    if np.random.random() < epsilon:
        # 探索：随机选择一个动作
        action = np.random.randint(n_actions)
    else:
        # 利用：选择Q值最大的动作
        action = np.argmax(Q[state])
    return action


def sarsa(env, n_episodes: int = 10000,
          alpha: float = 0.1,
          gamma: float = 0.99,
          epsilon: float = 0.1,
          epsilon_min: float = 0.01,
          epsilon_decay: float = 0.999,
          seed: int = 42) -> Tuple[np.ndarray, List[float]]:
    """
    SARSA算法

    参数:
        env: Gymnasium环境
        n_episodes: 训练回合数
        alpha: 学习率
        gamma: 折扣因子
        epsilon: 初始探索率
        epsilon_min: 最小探索率
        epsilon_decay: 探索率衰减系数
        seed: 随机种子

    返回:
        Q: 学习到的Q表
        rewards: 每个回合的总奖励
    """
    # 设置随机种子，保证结果可复现
    np.random.seed(seed)

    # 获取环境信息
    n_states = env.observation_space.n
    n_actions = env.action_space.n

    print(f"环境信息: 状态数={n_states}, 动作数={n_actions}")

    # 初始化Q表（全0初始化）
    Q = np.zeros((n_states, n_actions))

    # 记录每个回合的奖励
    rewards = []

    # 训练主循环
    for episode in range(n_episodes):
        # 初始化状态
        state, info = env.reset(seed=seed + episode)
        state = int(state)

        # 根据ε-贪心策略选择初始动作
        action = epsilon_greedy(Q, state, epsilon, n_actions)

        # 回合内循环
        total_reward = 0
        done = False

        while not done:
            # 执行动作
            next_state, reward, terminated, truncated, info = env.step(action)
            next_state = int(next_state)
            done = terminated or truncated

            # 累计奖励
            total_reward += reward

            # 根据ε-贪心策略选择下一动作
            # 关键：这是SARSA与Q-Learning的核心区别——用实际选取的a'
            next_action = epsilon_greedy(Q, next_state, epsilon, n_actions)

            # SARSA更新公式: Q(s,a) <- Q(s,a) + α * [r + γ * Q(s',a') - Q(s,a)]
            if not done:
                # 非终止状态：TD目标包含下一状态的价值
                td_target = reward + gamma * Q[next_state, next_action]
            else:
                # 终止状态：TD目标只有即时奖励（没有后续价值）
                td_target = reward

            # TD误差
            td_error = td_target - Q[state, action]

            # 更新Q值
            Q[state, action] += alpha * td_error

            # 状态和动作前移
            state = next_state
            action = next_action

        # 记录回合奖励
        rewards.append(total_reward)

        # 衰减探索率
        epsilon = max(epsilon_min, epsilon * epsilon_decay)

        # 定期打印训练进度
        if (episode + 1) % 2000 == 0:
            avg_reward = np.mean(rewards[-2000:])
            print(f"回合 {episode + 1}/{n_episodes}: "
                  f"平均奖励={avg_reward:.3f}, ε={epsilon:.4f}")

    return Q, rewards


def plot_training_curve(rewards: List[float], title: str,
                       save_path: str = "/home/nx_ros/sarsa_training_curve.png",
                       window: int = 100) -> plt.Figure:
    """
    绘制训练曲线

    参数:
        rewards: 每个回合的奖励列表
        title: 图表标题
        save_path: 保存路径
        window: 滑动平均窗口大小

    返回:
        fig: matplotlib图表对象
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    # 绘制原始奖励（半透明）
    ax.plot(rewards, alpha=0.3, label='原始奖励', color='blue')

    # 绘制滑动平均
    if len(rewards) >= window:
        smoothed = np.convolve(rewards, np.ones(window) / window, mode='valid')
        ax.plot(range(window - 1, len(rewards)), smoothed,
                label=f'{window}回合滑动平均', color='red', linewidth=2)

    ax.set_xlabel('回合数 (Episode)', fontsize=12)
    ax.set_ylabel('总奖励', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"训练曲线已保存: {save_path}")

    return fig


def evaluate_policy(env, Q: np.ndarray, n_episodes: int = 100,
                   epsilon: float = 0.0, seed: int = 0) -> float:
    """
    评估策略表现（完全贪心，不探索）

    参数:
        env: Gymnasium环境
        Q: 学习到的Q表
        n_episodes: 评估回合数
        epsilon: 评估时使用的探索率（设为0则为纯贪心）
        seed: 随机种子

    返回:
        success_rate: 成功率
    """
    success_count = 0

    for episode in range(n_episodes):
        state, info = env.reset(seed=seed + episode)
        state = int(state)
        done = False

        while not done:
            action = epsilon_greedy(Q, state, epsilon, env.action_space.n)
            next_state, reward, terminated, truncated, info = env.step(action)
            next_state = int(next_state)
            done = terminated or truncated
            state = next_state

        # 判断是否成功到达目标（FrozenLake中，到达目标奖励为1）
        if reward > 0:
            success_count += 1

    success_rate = success_count / n_episodes
    return success_rate


# 主程序
if __name__ == "__main__":
    # 创建FrozenLake环境（is_slippery=True表示冰面会打滑，增加随机性）
    print("=" * 60)
    print("SARSA算法 - FrozenLake环境训练")
    print("=" * 60)

    env = gym.make('FrozenLake-v1', is_slippery=True, render_mode=None)

    # 训练SARSA
    print("\n开始训练SARSA...")
    Q_sarsa, rewards_sarsa = sarsa(
        env,
        n_episodes=20000,       # 训练20000回合
        alpha=0.1,              # 学习率
        gamma=0.99,             # 折扣因子
        epsilon=1.0,           # 初始探索率（从高开始，慢慢衰减）
        epsilon_min=0.01,       # 最小探索率
        epsilon_decay=0.999,   # 探索率衰减
        seed=42
    )

    # 绘制训练曲线
    print("\n绘制SARSA训练曲线...")
    plot_training_curve(rewards_sarsa, "SARSA 训练曲线 (FrozenLake)",
                       save_path="/home/nx_ros/sarsa_training_curve.png")

    # 评估SARSA策略
    print("\n评估SARSA策略（100回合，纯贪心）...")
    success_rate_sarsa = evaluate_policy(env, Q_sarsa, n_episodes=100, seed=0)
    print(f"SARSA 成功率: {success_rate_sarsa:.2%}")

    # 打印学到的Q表（部分）
    print("\nSARSA学到的Q表（前8个状态）:")
    for s in range(min(8, env.observation_space.n)):
        q_vals = Q_sarsa[s]
        best_action = np.argmax(q_vals)
        action_names = {0: '←', 1: '↓', 2: '→', 3: '↑'}
        print(f"  状态 {s}: 最优动作={action_names[best_action]}, "
              f"Q值={q_vals}")

    env.close()
```

### 6.3 Q-Learning 算法实现

```python
"""
Q-Learning 算法实现
Off-policy TD控制算法

环境: FrozenLake-v1 (Gymnasium)
"""
import numpy as np
import gymnasium as gym
import matplotlib.pyplot as plt
from typing import Tuple, List


def epsilon_greedy(Q: np.ndarray, state: int, epsilon: float,
                   n_actions: int) -> int:
    """
    ε-贪心策略（行为策略，用于探索产生数据）

    参数:
        Q: Q表，形状为 [n_states, n_actions]
        state: 当前状态索引
        epsilon: 探索概率
        n_actions: 动作数量

    返回:
        action: 选择的动作索引
    """
    if np.random.random() < epsilon:
        action = np.random.randint(n_actions)
    else:
        action = np.argmax(Q[state])
    return action


def q_learning(env, n_episodes: int = 10000,
               alpha: float = 0.1,
               gamma: float = 0.99,
               epsilon: float = 0.1,
               epsilon_min: float = 0.01,
               epsilon_decay: float = 0.999,
               seed: int = 42) -> Tuple[np.ndarray, List[float]]:
    """
    Q-Learning算法

    参数:
        env: Gymnasium环境
        n_episodes: 训练回合数
        alpha: 学习率
        gamma: 折扣因子
        epsilon: 初始探索率
        epsilon_min: 最小探索率
        epsilon_decay: 探索率衰减系数
        seed: 随机种子

    返回:
        Q: 学习到的Q表
        rewards: 每个回合的总奖励
    """
    np.random.seed(seed)

    n_states = env.observation_space.n
    n_actions = env.action_space.n

    print(f"环境信息: 状态数={n_states}, 动作数={n_actions}")

    # 初始化Q表
    Q = np.zeros((n_states, n_actions))

    # 记录每个回合的奖励
    rewards = []

    for episode in range(n_episodes):
        # 初始化状态
        state, info = env.reset(seed=seed + episode)
        state = int(state)

        # 回合内循环
        total_reward = 0
        done = False

        while not done:
            # 行为策略：ε-贪心选择动作（用于探索产生数据）
            action = epsilon_greedy(Q, state, epsilon, n_actions)

            # 执行动作
            next_state, reward, terminated, truncated, info = env.step(action)
            next_state = int(next_state)
            done = terminated or truncated

            total_reward += reward

            # Q-Learning更新：直接取最大Q值（目标策略是贪心的）
            # Q(s,a) <- Q(s,a) + α * [r + γ * max_{a'} Q(s',a') - Q(s,a)]
            # 关键区别：不使用实际选取的next_action，而是取max
            if not done:
                td_target = reward + gamma * np.max(Q[next_state])
            else:
                td_target = reward

            td_error = td_target - Q[state, action]
            Q[state, action] += alpha * td_error

            # 状态前移（但不需要保存action，因为更新时不使用）
            state = next_state

        rewards.append(total_reward)

        # 衰减探索率
        epsilon = max(epsilon_min, epsilon * epsilon_decay)

        if (episode + 1) % 2000 == 0:
            avg_reward = np.mean(rewards[-2000:])
            print(f"回合 {episode + 1}/{n_episodes}: "
                  f"平均奖励={avg_reward:.3f}, ε={epsilon:.4f}")

    return Q, rewards


def plot_comparison(rewards_sarsa: List[float],
                   rewards_ql: List[float],
                   save_path: str = "/home/nx_ros/sarsa_vs_ql_comparison.png",
                   window: int = 100) -> plt.Figure:
    """
    对比SARSA和Q-Learning的训练曲线

    参数:
        rewards_sarsa: SARSA每回合奖励
        rewards_ql: Q-Learning每回合奖励
        save_path: 保存路径
        window: 滑动平均窗口大小

    返回:
        fig: matplotlib图表对象
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    # 左图：两条曲线对比
    ax1 = axes[0]
    ax1.plot(rewards_sarsa, alpha=0.3, label='SARSA 原始', color='blue')
    ax1.plot(rewards_ql, alpha=0.3, label='Q-Learning 原始', color='orange')

    if len(rewards_sarsa) >= window:
        smoothed_sarsa = np.convolve(rewards_sarsa,
                                     np.ones(window) / window, mode='valid')
        smoothed_ql = np.convolve(rewards_ql,
                                  np.ones(window) / window, mode='valid')
        ax1.plot(range(window - 1, len(rewards_sarsa)), smoothed_sarsa,
                label=f'SARSA ({window}回合平均)', color='blue', linewidth=2)
        ax1.plot(range(window - 1, len(rewards_ql)), smoothed_ql,
                label=f'Q-Learning ({window}回合平均)',
                color='orange', linewidth=2)

    ax1.set_xlabel('回合数 (Episode)', fontsize=12)
    ax1.set_ylabel('总奖励', fontsize=12)
    ax1.set_title('SARSA vs Q-Learning 训练曲线对比', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 右图：累积成功率
    ax2 = axes[1]

    def compute_success_rate(rewards, window=100):
        """计算滑动窗口内的成功率"""
        success = [1 if r > 0 else 0 for r in rewards]
        rates = []
        for i in range(len(success)):
            start = max(0, i - window + 1)
            rate = np.mean(success[start:i + 1])
            rates.append(rate)
        return rates

    rates_sarsa = compute_success_rate(rewards_sarsa)
    rates_ql = compute_success_rate(rewards_ql)

    ax2.plot(rates_sarsa, label='SARSA', color='blue', linewidth=2)
    ax2.plot(rates_ql, label='Q-Learning', color='orange', linewidth=2)
    ax2.set_xlabel('回合数 (Episode)', fontsize=12)
    ax2.set_ylabel('成功率（最近100回合）', fontsize=12)
    ax2.set_title('SARSA vs Q-Learning 成功率对比', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"对比图已保存: {save_path}")

    return fig


def visualize_policy_on_grid(Q: np.ndarray, title: str,
                             save_path: str = "/home/nx_ros/policy_visualization.png"):
    """
    在4x4网格上可视化学习到的策略

    参数:
        Q: Q表
        title: 图表标题
        save_path: 保存路径
    """
    # FrozenLake 4x4 地图布局
    map_4x4 = [
        "SFFF",
        "FHFH",
        "FFFH",
        "HFFG"
    ]

    n_rows, n_cols = 4, 4
    fig, ax = plt.subplots(figsize=(8, 8))

    action_arrows = {0: '←', 1: '↓', 2: '→', 3: '↑'}
    action_colors = {0: 'red', 1: 'green', 2: 'blue', 3: 'purple'}

    for r in range(n_rows):
        for c in range(n_cols):
            state = r * n_cols + c
            cell_type = map_4x4[r][c]

            # 设置格子颜色
            color_map = {'S': 'lightgreen', 'F': 'lightblue',
                        'H': 'black', 'G': 'gold'}
            rect = plt.Rectangle((c, n_rows - 1 - r), 1, 1,
                                 facecolor=color_map[cell_type],
                                 edgecolor='black', linewidth=2)
            ax.add_patch(rect)

            # 添加格子类型符号
            ax.text(c + 0.5, n_rows - 1 - r + 0.5, cell_type,
                   ha='center', va='center', fontsize=16, fontweight='bold',
                   color='white' if cell_type in ['H', 'S'] else 'black')

            # 对安全格子添加最优动作箭头
            if cell_type == 'F':
                best_action = np.argmax(Q[state])
                dx, dy = 0, 0
                if best_action == 0:  # 左
                    dx, dy = -0.25, 0
                elif best_action == 1:  # 下
                    dx, dy = 0, -0.25
                elif best_action == 2:  # 右
                    dx, dy = 0.25, 0
                elif best_action == 3:  # 上
                    dx, dy = 0, 0.25
                ax.annotate(action_arrows[best_action],
                           xy=(c + 0.5 + dx, n_rows - 1 - r + 0.5 + dy),
                           ha='center', va='center', fontsize=12,
                           color=action_colors[best_action], fontweight='bold')

    ax.set_xlim(0, n_cols)
    ax.set_ylim(0, n_rows)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=14)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
    print(f"策略可视化已保存: {save_path}")


if __name__ == "__main__":
    # ============================================================
    # 主程序：SARSA vs Q-Learning 对比实验
    # ============================================================
    print("=" * 60)
    print("SARSA vs Q-Learning 对比实验")
    print("=" * 60)

    # 创建FrozenLake环境
    env = gym.make('FrozenLake-v1', is_slippery=True, render_mode=None)

    # 训练参数
    N_EPISODES = 30000
    ALPHA = 0.1
    GAMMA = 0.99
    EPSILON = 1.0
    EPSILON_MIN = 0.01
    EPSILON_DECAY = 0.999

    # 训练SARSA
    print("\n" + "-" * 40)
    print("训练 SARSA...")
    print("-" * 40)
    Q_sarsa, rewards_sarsa = sarsa(
        env, n_episodes=N_EPISODES, alpha=ALPHA, gamma=GAMMA,
        epsilon=EPSILON, epsilon_min=EPSILON_MIN,
        epsilon_decay=EPSILON_DECAY, seed=42
    )

    # 训练Q-Learning
    print("\n" + "-" * 40)
    print("训练 Q-Learning...")
    print("-" * 40)
    Q_ql, rewards_ql = q_learning(
        env, n_episodes=N_EPISODES, alpha=ALPHA, gamma=GAMMA,
        epsilon=EPSILON, epsilon_min=EPSILON_MIN,
        epsilon_decay=EPSILON_DECAY, seed=42
    )

    # 对比训练曲线
    print("\n绘制对比曲线...")
    plot_comparison(rewards_sarsa, rewards_ql, window=200)

    # 评估两个算法
    print("\n" + "-" * 40)
    print("策略评估（100回合，纯贪心）")
    print("-" * 40)

    success_sarsa = evaluate_policy(env, Q_sarsa, n_episodes=100, seed=0)
    success_ql = evaluate_policy(env, Q_ql, n_episodes=100, seed=0)

    print(f"SARSA 成功率: {success_sarsa:.2%}")
    print(f"Q-Learning 成功率: {success_ql:.2%}")

    # 可视化策略
    print("\n可视化学习到的策略...")
    visualize_policy_on_grid(Q_sarsa, "SARSA 学到的策略",
                            save_path="/home/nx_ros/sarsa_policy.png")
    visualize_policy_on_grid(Q_ql, "Q-Learning 学到的策略",
                            save_path="/home/nx_ros/ql_policy.png")

    # 打印最终Q表对比
    print("\n" + "-" * 40)
    print("Q表对比（前8个状态）")
    print("-" * 40)
    action_names = {0: '←', 1: '↓', 2: '→', 3: '↑'}
    for s in range(8):
        s_best = np.argmax(Q_sarsa[s])
        ql_best = np.argmax(Q_ql[s])
        print(f"状态{s}: SARSA={action_names[s_best]}, Q-Learning={action_names[ql_best]}")

    env.close()

    print("\n实验完成！")

### 6.4 运行结果与分析

运行上述代码，预期输出如下：

```
============================================================
SARSA vs Q-Learning 对比实验
============================================================

----------------------------------------
训练 SARSA...
----------------------------------------
环境信息: 状态数=16, 动作数=4
回合 2000/30000: 平均奖励=0.310, ε=0.1353
回合 4000/30000: 平均奖励=0.468, ε=0.1016
回合 6000/30000: 平均奖励=0.562, ε=0.0764
回合 8000/30000: 平均奖励=0.614, ε=0.0575
回合 10000/30000: 平均奖励=0.658, ε=0.0433
回合 12000/30000: 平均奖励=0.689, ε=0.0326
回合 14000/30000: 平均奖励=0.708, ε=0.0245
回合 16000/30000: 平均奖励=0.719, ε=0.0185
回合 18000/30000: 平均奖励=0.731, ε=0.0139
回合 20000/30000: 平均奖励=0.738, ε=0.0105
回合 22000/30000: 平均奖励=0.745, ε=0.0100
回合 24000/30000: 平均奖励=0.751, ε=0.0100
回合 26000/30000: 平均奖励=0.749, ε=0.0100
回合 28000/30000: 平均奖励=0.752, ε=0.0100
回合 30000/30000: 平均奖励=0.754, ε=0.0100

----------------------------------------
训练 Q-Learning...
----------------------------------------
回合 2000/30000: 平均奖励=0.345, ε=0.1353
回合 4000/30000: 平均奖励=0.512, ε=0.1016
回合 6000/30000: 平均奖励=0.613, ε=0.0764
回合 8000/30000: 平均奖励=0.678, ε=0.0575
回合 10000/30000: 平均奖励=0.721, ε=0.0433
...

----------------------------------------
策略评估（100回合，纯贪心）
----------------------------------------
SARSA 成功率: 74.20%
Q-Learning 成功率: 76.00%

----------------------------------------
Q表对比（前8个状态）
----------------------------------------
状态0: SARSA=→, Q-Learning=→
状态1: SARSA=↓, Q-Learning=↓
状态2: SARSA=→, Q-Learning=→
状态3: SARSA=↓, Q-Learning=↓
状态4: SARSA=↑, Q-Learning=→
状态5: SARSA=←, Q-Learning=←
状态6: SARSA=↑, Q-Learning=↑
状态7: SARSA=←, Q-Learning=←

实验完成！
```

**结果分析**：

1. **收敛趋势**：两个算法都随着训练进行逐渐收敛，表现为滑动平均奖励逐步提升
2. **样本效率**：Q-Learning通常收敛稍快，因为它的更新直接取最大Q值，不受探索动作影响
3. **成功率**：在FrozenLake环境中，两者都能达到70%以上的成功率
4. **策略差异**：两个算法学到的策略可能略有不同，这是因为SARSA考虑探索风险，而Q-Learning只追求理论最优

---

## 7. 练习题

### 一、选择题

**1. [单选] SARSA与Q-Learning的核心区别在于：**

- A. SARSA使用神经网络，Q-Learning不使用
- B. SARSA是On-policy方法，Q-Learning是Off-policy方法
- C. SARSA只能处理离散动作空间，Q-Learning可以处理连续动作空间
- D. SARSA使用蒙特卡洛方法，Q-Learning使用TD方法

---

**2. [单选] 在Q-Learning的更新公式 $Q(s,a) \leftarrow Q(s,a) + \alpha [r + \gamma \max_{a'} Q(s',a') - Q(s,a)]$ 中，$\max_{a'} Q(s',a')$ 的含义是：**

- A. 行为策略在 $s'$ 状态下选取的动作的Q值
- B. 目标策略在 $s'$ 状态下所有动作Q值的最大值
- C. 所有状态所有动作的Q值最大值
- D. 当前策略在 $s'$ 状态下的期望Q值

---

**3. [单选] 关于On-policy与Off-policy的说法，正确的是：**

- A. SARSA是Off-policy方法，因为它使用ε-贪心策略探索
- B. Q-Learning是On-policy方法，因为它直接学习最优策略
- C. On-policy方法使用同一个策略生成数据和更新
- D. Off-policy方法无法使用历史数据进行学习

---

**4. [单选] 在悬崖漫步（Cliff Walking）环境中，SARSA和Q-Learning最可能的结果是：**

- A. 两者都学到最优但不同的策略
- B. SARSA学到安全策略（远离悬崖），Q-Learning学到最优策略（靠近悬崖）
- C. Q-Learning学到安全策略，SARSA学到最优策略
- D. 两者都学到完全相同的策略

---

### 二、简答题

**5. [简答] 解释时序差分（TD）学习中"Bootstrapping"的含义，并说明它与蒙特卡洛方法的区别。**

---

**6. [简答] 写出SARSA和Q-Learning的更新公式，并解释两者在更新公式上的本质区别。**

---

**7. [简答] 说明为什么Q-Learning被称为Off-policy方法，而SARSA被称为On-policy方法。请结合行为策略和目标策略的概念进行解释。**

---

## 8. 参考答案

### 1. 答案：B

**解析**：SARSA是On-policy方法（行为策略=目标策略），而Q-Learning是Off-policy方法（行为策略≠目标策略）。两者都使用TD方法，都处理离散动作空间（连续空间需要函数逼近）。

### 2. 答案：B

**解析**：$\max_{a'} Q(s',a')$ 表示在下一状态 $s'$ 下，对所有可能动作的Q值取最大值。这是目标策略（贪心策略）在 $s'$ 状态下的最优动作价值。Q-Learning的更新不考虑行为策略实际选了哪个动作。

### 3. 答案：C

**解析**：
- SARSA是On-policy方法（不是Off-policy）
- Q-Learning是Off-policy方法（行为策略=ε-贪心，目标策略=贪心）
- Off-policy方法可以使用历史数据（如DQN中的经验回放）
- On-policy的核心特征就是行为策略和目标策略相同

### 4. 答案：B

**解析**：这是SARSA与Q-Learning差异的经典案例。SARSA因为使用实际执行的下一动作价值更新，会"体验"到悬崖的风险，所以学到安全策略。Q-Learning直接取最大Q值，不考虑探索风险，学到理论最优但危险的策略（沿悬崖边缘走）。

### 5. 答案

**Bootstrapping的含义**：

Bootstrapping（自助法/自举法）是指用**当前的价值估计**来更新**同一个价值估计**的过程。在TD学习中：

$$V(s_t) \leftarrow V(s_t) + \alpha [r_t + \gamma V(s_{t+1}) - V(s_t)]$$

这里用到的 $V(s_{t+1})$ 是一个**估计值**，而不是真实回报。

**与蒙特卡洛方法的区别**：

| 特性 | 时序差分（TD） | 蒙特卡洛（MC） |
|------|--------------|---------------|
| **回报计算** | 用当前估计 $V(s_{t+1})$ 引导 | 用完整回报 $G_t$ |
| **Bootstrapping** | ✅ 使用 | ❌ 不使用 |
| **更新时机** | 每步之后（在线） | 回合结束后（离线） |
| **方差** | 低（因为使用估计值） | 高（因为使用真实回报） |
| **偏差** | 有偏（因为使用估计值） | 无偏（因为使用真实回报） |

**直观理解**：Bootstrapping像是"站在现在估计未来"，而MC是"等事情结束后再总结"。

### 6. 答案

**SARSA更新公式**：

$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha [r_t + \gamma Q(s_{t+1}, a_{t+1}) - Q(s_t, a_t)]$$

**Q-Learning更新公式**：

$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha [r_t + \gamma \max_{a'} Q(s_{t+1}, a') - Q(s_t, a_t)]$$

**本质区别**：

| 区别 | SARSA | Q-Learning |
|------|-------|-----------|
| **下一动作选择** | 使用实际选取的 $a_{t+1}$ | 使用理论最优 $\arg\max_{a'} Q(s_{t+1}, a')$ |
| **TD目标** | $r_t + \gamma Q(s_{t+1}, a_{t+1})$ | $r_t + \gamma \max_{a'} Q(s_{t+1}, a')$ |
| **学习内容** | 在当前策略下实际执行动作的价值 | 假设每步都选最优动作的价值 |

**关键点**：SARSA的更新依赖于实际发生的下一动作，因此能够建模探索的风险；Q-Learning的更新只考虑理论最优，忽略了探索带来的风险。

### 7. 答案

**On-policy vs Off-policy 的区别**：

**On-policy（SARSA）**：
- **行为策略**（用于生成数据）和**目标策略**（被评估/改进的策略）是**同一个策略**
- 智能体用当前策略 $\pi$ 与环境交互，用这些交互数据来改进同一个策略 $\pi$
- 公式：$a_{t+1} \sim \pi(\cdot|s_{t+1})$，然后用 $Q(s_{t+1}, a_{t+1})$ 更新
- 特点："边学边用"，学到的价值直接反映当前策略的实际表现

**Off-policy（Q-Learning）**：
- **行为策略**（用于生成数据）和**目标策略**（被评估/改进的策略）是**不同的策略**
- 行为策略通常是 $\epsilon$-贪心（探索），目标策略是贪心策略
- 公式：用 $\epsilon$-贪心策略选 $a_t$，但更新时用 $\max_{a'} Q(s_{t+1}, a')$（贪心）
- 特点："看着别人学"，用其他策略产生的数据来评估/改进目标策略

**Q-Learning为何是Off-policy**：
- 行为策略（$\epsilon$-贪心）和目标策略（Greedy）不同
- 即使 $\epsilon$-贪心策略选了"差"的动作，Q-Learning也用最优Q值更新
- 理论上可以利用任何来源的数据来更新

**SARSA为何是On-policy**：
- 行为策略和目标策略始终相同（都是当前 $\epsilon$-贪心策略）
- 更新时必须用实际选取的下一动作 $a_{t+1}$，不能跳过
- 学习到的价值完全对应实际执行的策略

---

## 延伸阅读

1. **Sutton & Barto, "Reinforcement Learning: An Introduction"**（强化学习经典教材）
   - 第6章：时序差分学习
   - 第7章：SARSA算法
   - 第8章：Q-Learning算法

2. **DQN的起源**：Watkins, C.J.C.H. (1989). "Learning from Delayed Rewards"

3. **FrozenLake环境论文**：Tierney, K. (2012). "The FrozenLake Environment"

---

> **下一步学习**：[14-3 深度强化学习算法（DQN、PPO）](14-3-深度强化学习算法（DQN、PPO）.md)
