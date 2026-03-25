# 14-3 深度强化学习算法（DQN、PPO）

**版本**: V2.0  
**作者**: Wendy | **课程系列**: ROS2机器人仿真与应用实践  
**适用对象**: 具备强化学习基础，希望深入深度强化学习的学员  
**前置知识**: 强化学习基础概念（Q学习、MDP、策略与价值函数）

---

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 14-3 |
| 课程名称 | 深度强化学习算法（DQN、PPO） |
| 所属模块 | 14-强化学习 (RL) |
| 难度等级 | ⭐⭐⭐⭐☆ |
| 预计学时 | 6小时 |
| 前置知识 | 强化学习基础（MDP、价值函数、贝尔曼方程） |

---

## 目录

1. [深度强化学习概述](#1-深度强化学习概述)
2. [DQN算法详解](#2-dqn算法详解)
3. [PPO算法详解](#3-ppo算法详解)
4. [其他DRL算法](#4-其他drl算法)
5. [代码实战](#5-代码实战)
6. [练习题](#6-练习题)
7. [参考答案](#7-参考答案)

---

## 一、深度强化学习概述

### 1.1 深度学习 + 强化学习

传统的**表格型强化学习**（如 Q-Learning）在状态空间和动作空间较小时表现出色——用一张 Q 表存储每个状态-动作对的价值，通过迭代更新逐步逼近最优策略。然而，当面对现实世界的复杂任务时，这种方法的局限性立刻显现：

| 场景 | 状态空间 | 传统方法瓶颈 |
|------|----------|-------------|
| Atari 游戏 | 210×160 像素图像 | Q 表无法枚举 |
| 机器人控制 | 关节角度+速度+力矩 | 连续空间无法离散化 |
| 自动驾驶 | 多传感器融合+时序 | 高维状态组合爆炸 |

**深度强化学习（Deep Reinforcement Learning, DRL）** 的核心思想是：用**深度神经网络**代替 Q 表或策略表格来逼近价值函数或策略函数。神经网络具有强大的函数逼近能力，能够从高维原始输入（如图像）中自动提取有用特征，直接学习从感知到动作的端到端映射。

### 1.2 深度 Q 网络（DQN）核心思想

DQN（Deep Q-Network）由 DeepMind 于 2013 年在论文 *"Playing Atari with Deep Reinforcement Learning"* 中首次提出，是**首个成功将深度学习与强化学习结合**的算法。

DQN 的核心创新有两点：
1. **用卷积神经网络逼近 Q 函数**：输入原始像素，输出每个动作的 Q 值
2. **引入经验回放和目标网络**：解决神经网络的非平稳学习问题

### 1.3 连续动作空间 vs 离散动作空间

理解动作空间的类型对选择合适算法至关重要：

| 类型 | 定义 | 示例 | 适用算法 |
|------|------|------|---------|
| **离散动作空间** | 动作数量有限，可枚举 | 左/右、上/下 | DQN、Q-Learning |
| **连续动作空间** | 动作是连续值（向量） | 关节扭矩、速度 | PPO、SAC、TD3 |

**关键区别**：
- **离散空间**：可以用 $\max_a Q(s,a)$ 选择最优动作
- **连续空间**：无法枚举所有动作，需要 Actor-Critic 或其他方法直接输出动作值

> **重要提示**：DQN 天然只支持离散动作空间；PPO 通过调整网络输出层可同时支持离散和连续空间。

---

## 二、DQN算法详解

### 2.1 从 Q 表到 Q 网络

在传统 Q 学习中，Q 函数以表格形式存储：

$$
Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]
$$

当状态空间连续或巨大时（例如机器人摄像头图像有无数种像素组合），Q 表既无法存储也无法高效查询。

**DQN 的核心思想**：用神经网络 $Q_\theta(s, a)$ 代替 Q 表。输入状态 $s$，输出每个动作 $a$ 的 Q 值估计。

DQN 的损失函数定义为：

$$
L(\theta) = \mathbb{E}_{(s,a,r,s')\sim \mathcal{D}}\left[\left(r + \gamma \max_{a'} Q_{\theta'}(s', a') - Q_\theta(s, a)\right)^2\right]
$$

其中 $\theta$ 是当前 Q 网络（Online Network）的参数，$\theta'$ 是目标网络（Target Network）的参数。

### 2.2 经验回放（Experience Replay）

如果直接用连续收集的样本训练神经网络，会遇到两个严重问题：

1. **数据相关性**：连续帧画面几乎相同，样本间存在时间相关性，导致网络收敛到局部最优
2. **数据利用率低**：每个样本只被使用一次

DQN 引入了**经验回放缓冲区**（Experience Replay Buffer）：智能体与环境交互产生的每条经验 $(s, a, r, s', \text{done})$ 都存入一个有限大小的循环缓冲区。训练时，从缓冲区中**随机抽样**一小批样本进行梯度下降。

**经验回放的优势**：
- 打破样本间的时间相关性
- 每个样本可被重复使用，提高数据效率
- 打乱样本顺序使梯度更新更稳定

### 2.3 目标网络（Target Network）

在 DQN 损失函数中，目标值 $r + \gamma \max_{a'} Q_{\theta'}(s', a')$ 本身依赖于网络参数 $\theta'$。如果每步同时更新 $\theta$ 和目标值，就像追逐一个不断移动的靶子，训练极不稳定。

**解决方案**：维护两个神经网络——
- **在线网络（Online Network）**：负责选择动作和计算当前 Q 值
- **目标网络（Target Network）**：负责计算目标 Q 值

目标网络的参数 $\theta'$ **每隔固定步数**才从在线网络硬拷贝过来（也可以使用软更新 $\theta' \leftarrow \tau \theta + (1-\tau)\theta'$）。

### 2.4 Double DQN

DQN 使用 $\max_{a'} Q_{\theta'}(s', a')$ 估计目标 Q 值，但"最大化"操作会**放大 Q 值的噪声**，导致**过估计（Overestimation）**——估计值系统性高于真实值。

**Double DQN**（Hasselt et al., 2015）通过解耦动作选择和动作评估来解决此问题：

- 用**在线网络**选择最优动作：$a^* = \arg\max_{a'} Q_\theta(s', a')$
- 用**目标网络**评估该动作：$Q_{\theta'}(s', a^*)$

更新公式：

$$
L(\theta) = \mathbb{E}\left[\left(r + \gamma Q_{\theta'}(s', \arg\max_{a'} Q_\theta(s', a')) - Q_\theta(s, a)\right)^2\right]
$$

实验表明，Double DQN 通常能稳定提升性能 2-5%。

### 2.5 Dueling DQN

**Dueling DQN**（Wang et al., 2015）观察到：在许多状态中，不同动作的 Q 值差异不大，真正重要的是**状态的价值 $V(s)$** 而非动作的相对优劣。

它将 Q 网络分成两条支路：

$$
Q(s, a) = V(s) + A(s, a)
$$

其中：
- $V(s)$：状态价值函数（该状态平均能获得多少奖励）
- $A(s, a)$：动作优势函数（选择动作 $a$ 比平均好多少）

通过这种分解，Dueling DQN 能更高效地学习状态价值，尤其在动作不影响结果的状态中表现更好。

---

## 三、PPO算法详解

### 3.1 策略梯度（Policy Gradient）回顾

不同于 DQN 通过估计 Q 值间接决策，**策略梯度方法**直接参数化策略函数 $\pi_\theta(a|s)$，直接输出每个动作的概率分布。

策略梯度定理：

$$
\nabla_\theta J(\theta) = \mathbb{E}_{s\sim d^\pi, a\sim\pi_\theta}\left[\nabla_\theta \log \pi_\theta(a|s) \cdot Q^{\pi_\theta}(s, a)\right]
$$

通俗理解：如果某个动作在某个状态下获得的 Q 值越高，我们就要增大在这个状态下选择这个动作的概率——通过增大 $\log \pi_\theta(a|s)$ 乘以 $Q$ 值的梯度来实现。

**经典策略梯度方法（如 REINFORCE）的问题**：
- **早熟收敛**：策略可能在找到次优解后停止探索
- **策略崩溃**：单次更新幅度过大导致性能断崖式下降

### 3.2 TRPO 原理

**TRPO（Trust Region Policy Optimization）** 通过约束新旧策略的 KL 散度来保证策略更新在"信任区域"内：

$$
\max_\theta \mathbb{E}_t\left[\frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)} \hat{A}_t\right]
$$

$$
\text{s.t.} \quad \mathbb{E}_t\left[\text{KL}(\pi_{\theta_{\text{old}}}(\cdot|s_t) \| \pi_\theta(\cdot|s_t))\right] \leq \delta
$$

TRPO 通过复杂的二阶优化（共轭梯度 + 线搜索）求解，计算开销大且难以与很多网络架构兼容。

### 3.3 PPO-Clip 目标函数

**PPO（Proximal Policy Optimization）** 是 TRPO 的简化版本，通过一阶优化实现了类似效果，因其实现简单、效果优异成为**当前最流行的 RL 算法**。

PPO 的核心是**裁剪概率比**（Clipped Probability Ratio）。定义重要性采样比率：

$$
r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)}
$$

PPO-Clip 目标函数：

$$
L^{\text{CLIP}}(\theta) = \mathbb{E}_t\left[\min\left(r_t(\theta) \cdot \hat{A}_t,\ \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) \cdot \hat{A}_t\right)\right]
$$

**直观理解**：

| 情况 | 机制 |
|------|------|
| $A_t > 0$（正优势） | 鼓励增大该动作概率，但 $r_t$ 最多到 $1+\epsilon$ |
| $A_t < 0$（负优势） | 鼓励减小该动作概率，但 $r_t$ 最少到 $1-\epsilon$ |

**Clip 函数的作用**：充当"安全阀"，防止策略在单次更新中变化过大（超过 $\pm\epsilon$ 的幅度），避免灾难性的策略退化。

### 3.4 PPO 与 DQN 对比

| 特性 | DQN | PPO |
|------|-----|-----|
| **算法类型** | 值函数方法（Value-based） | 策略梯度方法（Policy-based） |
| **输出** | 每个动作的 Q 值 | 每个动作的概率分布 |
| **动作空间** | 离散动作 | 离散 + 连续动作 |
| **策略类型** | 确定性策略（$\epsilon$-贪心） | 随机策略 |
| **数据利用** | Off-policy（经验回放） | On-policy（也可 Off-policy 变体） |
| **稳定性** | 较稳定（目标网络加持） | 非常稳定（Clip 机制） |
| **超参数敏感度** | 中等 | 相对不敏感 |
| **采样效率** | 高（数据复用） | 低（每次更新需重新采样） |
| **收敛速度** | 较慢 | 较快 |
| **典型应用** | Atari 游戏、简单控制 | 机器人控制、自动驾驶、大语言模型对齐 |

---

## 四、其他DRL算法

### 4.1 A3C（异步优势 Actor-Critic）

**A3C（Asynchronous Advantage Actor-Critic）** 由 DeepMind 于 2016 年提出，是 Actor-Critic 框架的异步并行版本。

**核心思想**：
- 多个独立的环境副本（Worker）并行运行
- 每个 Worker 有独立的网络副本，定期与全局网络同步
- 利用多样化的异步数据打破时间相关性

**优势**：
- 不需要经验回放（并行数据本身就是多样化的）
- 训练更稳定，收敛更快
- 可以在 CPU 上高效训练（无需 GPU）

**A3C 的贡献**：证明了异步并行是训练深度 RL 算法的有效方式，启发了后续大量并行训练方法。

### 4.2 SAC（软 Actor-Critic）

**SAC（Soft Actor-Critic）** 由 Haarnoja et al., 2018 提出，是一种**最大熵**强化学习算法。

**核心创新**：在原有奖励基础上加入**熵正则项**：

$$
J(\pi) = \mathbb{E}_{t}\left[r_t + \alpha \mathcal{H}(\pi(\cdot|s_t))\right]
$$

其中 $\alpha$ 是温度参数，控制探索与利用的平衡。

**特点**：
- **Off-policy**：使用经验回放，数据效率高
- **随机策略**：通过最大化熵鼓励持续探索
- **自动温度调整**：SAC 能自动学习最优的 $\alpha$ 值
- **连续动作空间原生支持**：高斯策略输出连续动作

SAC 在许多连续控制任务上表现优异，是机器人控制领域的热门选择。

### 4.3 TD3（Twin Delayed DDPG）

**TD3（Twin Delayed Deep Deterministic Policy Gradient）** 由 Fujimoto et al., 2018 提出，是 DDPG 的改进版本，针对**连续动作空间**设计。

**TD3 的三大技巧**：

1. **双重 Q 网络（Clipped Double Q）**：维护两个 Q 网络，取较小者作为目标值，减少过估计
   $$
   y(r, s', d) = r + \gamma \min_{i=1,2} Q_{\theta_i'}(s', \pi_{\phi'}(s'))
   $$

2. **延迟策略更新（Delayed Policy Updates）**： Critic 更新频率更高，Actor 每隔 $d$ 步才更新一次，减少策略评估误差的累积

3. **目标策略平滑（Target Policy Smoothing）**：在目标动作上添加少量噪声，使价值估计更平滑
   $$
   a' = \pi_{\phi'}(s') + \text{clip}(\epsilon, -c, c), \quad \epsilon \sim \mathcal{N}(0, \sigma)
   $$

TD3 在许多连续控制任务上取得了 SOTA 表现，是 DDPG 的直接替代品。

---

## 五、代码实战

### 5.1 PyTorch DQN 实现

CartPole 是一个经典控制问题：让杆子保持直立。状态是 4 维连续值（车位置、车速度、杆角度、杆角速度），动作是离散的左/右推车。

```python
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import gym
from collections import deque
import random

# 设置随机种子保证可复现性
torch.manual_seed(42)
np.random.seed(42)
random.seed(42)


# ----------------------
# 1. 定义Q网络
# ----------------------
class QNetwork(nn.Module):
    """
    Q网络：输入状态，输出每个动作的Q值
    使用两层隐藏层，每层128个神经元
    """
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(QNetwork, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, state):
        return self.net(state)


# ----------------------
# 2. 经验回放缓冲区
# ----------------------
class ReplayBuffer:
    """
    经验回放缓冲区：存储(s,a,r,s',done)，支持随机采样
    使用deque实现固定大小的循环缓冲区
    """
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        """将一条经验存入缓冲区"""
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        """从缓冲区随机采样一批经验"""
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards),
            np.array(next_states),
            np.array(dones)
        )
    
    def __len__(self):
        return len(self.buffer)


# ----------------------
# 3. DQN智能体
# ----------------------
class DQNAgent:
    def __init__(self, state_dim, action_dim, config):
        self.gamma = config.get('gamma', 0.99)           # 折扣因子
        self.epsilon = config.get('epsilon_start', 1.0)  # 初始探索率
        self.epsilon_min = config.get('epsilon_min', 0.01)  # 最小探索率
        self.epsilon_decay = config.get('epsilon_decay', 0.995)  # 探索率衰减系数
        self.lr = config.get('lr', 1e-3)                # 学习率
        self.batch_size = config.get('batch_size', 64)  # 批次大小
        self.target_update_freq = config.get('target_update_freq', 100)  # 目标网络更新频率
        
        self.action_dim = action_dim
        self.total_steps = 0
        
        # 在线网络和目标网络（参数相同初始化）
        self.q_net = QNetwork(state_dim, action_dim)
        self.target_net = QNetwork(state_dim, action_dim)
        self.target_net.load_state_dict(self.q_net.state_dict())
        
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=self.lr)
        self.replay_buffer = ReplayBuffer(capacity=config.get('replay_capacity', 10000))
    
    def select_action(self, state, training=True):
        """
        ε-贪心策略选择动作
        训练时随机探索，评估时利用
        """
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.q_net(state_t)
            return q_values.argmax(dim=1).item()
    
    def store_transition(self, state, action, reward, next_state, done):
        """存储一条转移经验到回放缓冲区"""
        self.replay_buffer.push(state, action, reward, next_state, done)
    
    def update(self):
        """
        从经验回放缓冲区随机采样，更新Q网络
        """
        if len(self.replay_buffer) < self.batch_size:
            return None
        
        # 随机采样一批经验
        states, actions, rewards, next_states, dones = \
            self.replay_buffer.sample(self.batch_size)
        
        # 转换为 Tensor
        states_t = torch.FloatTensor(states)
        actions_t = torch.LongTensor(actions)
        rewards_t = torch.FloatTensor(rewards)
        next_states_t = torch.FloatTensor(next_states)
        dones_t = torch.FloatTensor(dones)
        
        # 计算当前Q值（在线网络）
        q_values = self.q_net(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)
        
        # 计算目标Q值（使用目标网络）
        with torch.no_grad():
            next_q_values = self.target_net(next_states_t).max(dim=1)[0]
            target_q_values = rewards_t + self.gamma * next_q_values * (1 - dones_t)
        
        # 计算损失并更新
        loss = nn.MSELoss()(q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        # 梯度裁剪，防止梯度爆炸
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # ε衰减
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.total_steps += 1
        
        # 定期更新目标网络（硬拷贝）
        if self.total_steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())
        
        return loss.item()


# ----------------------
# 4. Double DQN实现（可选扩展）
# ----------------------
class DoubleDQNAgent(DQNAgent):
    """
    Double DQN：使用在线网络选择动作，目标网络评估动作
    减少Q值过估计问题
    """
    def update(self):
        if len(self.replay_buffer) < self.batch_size:
            return None
        
        states, actions, rewards, next_states, dones = \
            self.replay_buffer.sample(self.batch_size)
        
        states_t = torch.FloatTensor(states)
        actions_t = torch.LongTensor(actions)
        rewards_t = torch.FloatTensor(rewards)
        next_states_t = torch.FloatTensor(next_states)
        dones_t = torch.FloatTensor(dones)
        
        # 当前Q值
        q_values = self.q_net(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)
        
        with torch.no_grad():
            # Double DQN: 用在线网络选择最优动作
            best_actions = self.q_net(next_states_t).argmax(dim=1, keepdim=True)
            # 用目标网络评估该动作的价值
            next_q_values = self.target_net(next_states_t).gather(1, best_actions).squeeze(1)
            target_q_values = rewards_t + self.gamma * next_q_values * (1 - dones_t)
        
        loss = nn.MSELoss()(q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.total_steps += 1
        
        if self.total_steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())
        
        return loss.item()


# ----------------------
# 5. 训练主循环
# ----------------------
def train_dqn(env_name='CartPole-v1', episodes=500, max_steps=500, use_double=False):
    """
    训练DQN或Double DQN智能体
    
    参数:
        env_name: Gym环境名称
        episodes: 最大训练回合数
        max_steps: 每回合最大步数
        use_double: 是否使用Double DQN
    """
    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    
    config = {
        'gamma': 0.99,
        'epsilon_start': 1.0,
        'epsilon_min': 0.01,
        'epsilon_decay': 0.995,
        'lr': 1e-3,
        'batch_size': 64,
        'target_update_freq': 100,
        'replay_capacity': 10000,
    }
    
    agent_class = DoubleDQNAgent if use_double else DQNAgent
    agent_name = "Double DQN" if use_double else "DQN"
    agent = agent_class(state_dim, action_dim, config)
    
    returns = []
    
    print("=" * 60)
    print(f"开始训练 {agent_name} ({env_name})")
    print("=" * 60)
    
    for episode in range(episodes):
        state, _ = env.reset(seed=42)
        total_reward = 0
        episode_losses = []
        
        for step in range(max_steps):
            action = agent.select_action(state)
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
            
            agent.store_transition(state, action, reward, next_state, done)
            loss = agent.update()
            if loss is not None:
                episode_losses.append(loss)
            
            state = next_state
            total_reward += reward
            
            if done:
                break
        
        returns.append(total_reward)
        avg_loss = np.mean(episode_losses) if episode_losses else 0
        
        if episode % 20 == 0:
            avg_reward = np.mean(returns[-20:])
            print(f"Episode {episode:4d} | Avg Reward (last 20): {avg_reward:6.1f} | "
                  f"ε: {agent.epsilon:.3f} | Loss: {avg_loss:.4f}")
        
        # CartPole-v1: 连续20回合平均奖励 >= 450 视为解决
        if len(returns) >= 20 and np.mean(returns[-20:]) >= 450:
            print(f"\n🎉 任务完成！连续20回合平均奖励达到 {np.mean(returns[-20:]):.1f}")
            break
    
    env.close()
    return returns


if __name__ == '__main__':
    # 训练标准DQN
    returns = train_dqn(episodes=500)
    
    # 取消注释可训练Double DQN进行对比
    # returns = train_dqn(episodes=500, use_double=True)
```

### 5.2 PPO 简化实现

PPO 需要同时维护策略网络（Actor）和价值网络（Critic），并显式计算新旧策略的概率比。

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributions as distributions
import numpy as np
import gym
from collections import deque

# 设置随机种子
torch.manual_seed(42)
np.random.seed(42)


# ----------------------
# 1. 定义Actor-Critic网络
# ----------------------
class ActorCritic(nn.Module):
    """
    Actor-Critic架构：
    - Actor（策略网络）：输出动作的logits
    - Critic（价值网络）：输出状态价值V(s)
    - 共享底层特征提取层
    """
    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super(ActorCritic, self).__init__()
        # 共享特征提取层
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
        )
        # Actor头：输出动作 logits
        self.actor = nn.Linear(hidden_dim, action_dim)
        # Critic头：输出状态价值
        self.critic = nn.Linear(hidden_dim, 1)
    
    def forward(self, state):
        features = self.shared(state)
        action_logits = self.actor(features)
        value = self.critic(features)
        return action_logits, value


# ----------------------
# 2. PPO损失计算
# ----------------------
def compute_ppo_loss(old_log_probs, new_log_probs, advantages, clip_eps=0.2):
    """
    计算PPO裁剪损失函数
    
    参数:
        old_log_probs: 旧策略下采样动作的对数概率
        new_log_probs: 新策略下采样动作的对数概率
        advantages: 优势函数估计
        clip_eps: 裁剪边界（默认0.2）
    
    返回:
        裁剪后的策略损失（标量）
    """
    # 概率比 r(θ) = exp(log π_new - log π_old)
    ratio = torch.exp(new_log_probs - old_log_probs)
    
    # 未裁剪的策略损失
    surr1 = ratio * advantages
    
    # 裁剪后的策略损失
    surr2 = torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps) * advantages
    
    # 外层 min 取下界，确保我们优化的是下界（更保守的估计）
    policy_loss = -torch.min(surr1, surr2).mean()
    
    return policy_loss


# ----------------------
# 3. PPO智能体
# ----------------------
class PPOAgent:
    def __init__(self, state_dim, action_dim, config):
        self.gamma = config.get('gamma', 0.99)
        self.gae_lambda = config.get('gae_lambda', 0.95)  # GAE参数
        self.clip_eps = config.get('clip_eps', 0.2)       # PPO裁剪边界
        self.k_epochs = config.get('k_epochs', 10)        # 每次数据采集后的更新轮数
        self.mini_batch_size = config.get('mini_batch_size', 64)  # 批次大小
        self.actor_lr = config.get('actor_lr', 3e-4)      # Actor学习率
        self.critic_lr = config.get('critic_lr', 1e-3)    # Critic学习率
        self.entropy_coef = config.get('entropy_coef', 0.01)  # 熵正则系数
        self.value_coef = config.get('value_coef', 0.5)   # 价值损失系数
        self.max_grad_norm = config.get('max_grad_norm', 0.5)  # 梯度裁剪阈值
        
        self.action_dim = action_dim
        
        # 创建策略网络（Actor-Critic）
        self.policy = ActorCritic(state_dim, action_dim)
        self.optimizer = optim.Adam([
            {'params': self.policy.shared.parameters(), 'lr': self.actor_lr},
            {'params': self.policy.actor.parameters(), 'lr': self.actor_lr},
            {'params': self.policy.critic.parameters(), 'lr': self.critic_lr},
        ])
    
    def select_action(self, state):
        """
        从当前策略采样动作，返回动作、对数概率、价值估计
        """
        with torch.no_grad():
            state_t = torch.FloatTensor(state)
            action_logits, value = self.policy(state_t)
            dist = distributions.Categorical(logits=action_logits)
            action = dist.sample()
            return action.item(), dist.log_prob(action), value.item()
    
    def compute_gae(self, rewards, values, dones, next_value):
        """
        计算广义优势估计（GAE）
        
        GAE通过对TD误差的加权求和来估计优势函数，
        平衡了偏差和方差：
        - lambda=1: 高方差低偏差
        - lambda=0: 低方差高偏差（等同于TD(0)）
        """
        advantages = []
        gae = 0
        values = list(values) + [next_value]
        
        for t in reversed(range(len(rewards))):
            # TD误差
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            # 累加带折扣的TD误差
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        return torch.FloatTensor(advantages)
    
    def update(self, trajectory):
        """
        用收集的轨迹数据更新策略网络
        
        trajectory: dict，包含 keys: states, actions, rewards, dones, log_probs, values
        """
        states = torch.FloatTensor(np.array(trajectory['states']))
        actions = torch.LongTensor(trajectory['actions'])
        old_log_probs = torch.FloatTensor(trajectory['log_probs'])
        old_values = torch.FloatTensor(trajectory['values'])
        rewards = np.array(trajectory['rewards'])
        dones = np.array(trajectory['dones'])
        
        # 计算优势估计
        with torch.no_grad():
            _, next_value = self.policy(states[-1:])
            next_value = next_value.item()
        
        advantages = self.compute_gae(rewards, old_values.numpy(), dones, next_value)
        # 标准化优势函数（减小方差）
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 回报（用于价值网络学习）
        returns = advantages + old_values
        returns = (returns - returns.mean()) / (returns.std() + 1e-8)
        
        # K轮更新
        for _ in range(self.k_epochs):
            # 随机打乱并分批次
            indices = torch.randperm(len(states))
            for start in range(0, len(states), self.mini_batch_size):
                end = min(start + self.mini_batch_size, len(states))
                idx = indices[start:end]
                
                batch_states = states[idx]
                batch_actions = actions[idx]
                batch_old_log_probs = old_log_probs[idx]
                batch_old_values = old_values[idx]
                batch_advantages = advantages[idx]
                batch_returns = returns[idx]
                
                # 获取新的 log_prob 和 value
                action_logits, values_pred = self.policy(batch_states)
                dist = distributions.Categorical(logits=action_logits)
                new_log_probs = dist.log_prob(batch_actions)
                entropy = dist.entropy().mean()
                
                # PPO策略损失（使用clip约束）
                policy_loss = compute_ppo_loss(
                    batch_old_log_probs, new_log_probs, batch_advantages, self.clip_eps
                )
                
                # 价值损失（回归到回报）
                value_loss = nn.MSELoss()(values_pred.squeeze(), batch_returns)
                
                # 总损失 = 策略损失 + 价值损失 - 熵正则（熵鼓励探索）
                total_loss = (
                    policy_loss 
                    + self.value_coef * value_loss 
                    - self.entropy_coef * entropy
                )
                
                self.optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.optimizer.step()


# ----------------------
# 4. 轨迹数据采集
# ----------------------
def collect_trajectory(env, agent, max_steps=2048):
    """
    采集一条轨迹的数据
    
    返回:
        trajectory: 轨迹数据字典
        episode_reward: 总奖励
    """
    trajectory = {
        'states': [], 'actions': [], 'rewards': [],
        'dones': [], 'log_probs': [], 'values': []
    }
    
    state, _ = env.reset(seed=42)
    episode_reward = 0
    
    for _ in range(max_steps):
        action, log_prob, value = agent.select_action(state)
        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        
        trajectory['states'].append(state)
        trajectory['actions'].append(action)
        trajectory['rewards'].append(reward)
        trajectory['dones'].append(done)
        trajectory['log_probs'].append(log_prob)
        trajectory['values'].append(value)
        
        state = next_state
        episode_reward += reward
        
        if done:
            state, _ = env.reset()
    
    return trajectory, episode_reward


# ----------------------
# 5. 训练主循环
# ----------------------
def train_ppo(env_name='CartPole-v1', total_steps=100000):
    """
    训练PPO智能体
    
    参数:
        env_name: Gym环境名称
        total_steps: 最大训练步数
    """
    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.n
    
    config = {
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_eps': 0.2,
        'k_epochs': 10,
        'mini_batch_size': 64,
        'actor_lr': 3e-4,
        'critic_lr': 1e-3,
        'entropy_coef': 0.01,
        'value_coef': 0.5,
        'max_grad_norm': 0.5,
    }
    
    agent = PPOAgent(state_dim, action_dim, config)
    
    episode_rewards = deque(maxlen=20)
    step_count = 0
    update_count = 0
    
    print("=" * 60)
    print(f"开始训练 PPO ({env_name})")
    print("=" * 60)
    
    while step_count < total_steps:
        trajectory, episode_reward = collect_trajectory(env, agent)
        step_count += len(trajectory['rewards'])
        
        agent.update(trajectory)
        update_count += 1
        
        episode_rewards.append(episode_reward)
        
        if update_count % 10 == 0:
            avg_reward = np.mean(list(episode_rewards)[-20:])
            print(f"Steps: {step_count:7d} | Updates: {update_count:3d} | "
                  f"Avg Reward (last 20): {avg_reward:6.1f}")
        
        if step_count >= total_steps:
            break
    
    env.close()
    print(f"\n🎉 训练完成！总计 {update_count} 次策略更新")


if __name__ == '__main__':
    print("=" * 60)
    print("开始训练 PPO (CartPole-v1)")
    print("=" * 60)
    train_ppo(total_steps=100000)
```

### 5.3 算法对比实验

运行以下实验观察 DQN 和 PPO 的训练差异：

```python
import matplotlib.pyplot as plt
import numpy as np

def compare_algorithms():
    """
    对比DQN和PPO在CartPole上的训练曲线
    运行后会自动绘制奖励曲线对比图
    """
    # 训练DQN（缩短episodes以加快演示）
    dqn_returns = train_dqn(env_name='CartPole-v1', episodes=300)
    
    # 训练PPO（缩短steps以加快演示）
    ppo_returns = train_ppo(env_name='CartPole-v1', total_steps=50000)
    
    # 绘制训练曲线
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    # DQN奖励曲线（平滑处理）
    window = 10
    dqn_smooth = np.convolve(dqn_returns, np.ones(window)/window, mode='valid')
    plt.plot(dqn_smooth, label='DQN', color='blue')
    plt.xlabel('Episode')
    plt.ylabel('Reward (smoothed)')
    plt.title('DQN Training Curve')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    # PPO奖励曲线
    plt.plot(ppo_returns, label='PPO', color='green', alpha=0.5)
    ppo_smooth = np.convolve(ppo_returns, np.ones(window)/window, mode='valid')
    plt.plot(ppo_smooth, label='PPO (smoothed)', color='green')
    plt.xlabel('Episode')
    plt.ylabel('Reward')
    plt.title('PPO Training Curve')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('dqn_vs_ppo.png', dpi=150)
    plt.show()
    
    print("=" * 60)
    print("DQN vs PPO 对比总结：")
    print(f"  DQN 最终平均奖励（最后20回合）: {np.mean(dqn_returns[-20:]):.1f}")
    print(f"  PPO 最终平均奖励（最后20回合）: {np.mean(ppo_returns[-20:]):.1f}")
    print("=" * 60)


if __name__ == '__main__':
    compare_algorithms()
```

**运行结果观察**：

| 指标 | DQN | PPO |
|------|-----|-----|
| 收敛所需 episodes/steps | ~200-300 episodes | ~20000-50000 steps |
| 训练曲线波动 | 较大 | 平滑 |
| 最终性能 | 稳定在 450+ | 稳定在 450+ |
| 采样效率 | 高（off-policy复用） | 低（on-policy） |

---

## 六、练习题

### 选择题

**1. 【单选】DQN 中经验回放缓冲区的主要作用是？**

A. 存储 Q 表的值  
B. 打破训练样本的时间相关性  
C. 增加折扣因子  
D. 提高学习率

**2. 【单选】PPO 算法中，Clip 函数的核心作用是？**

A. 裁剪梯度防止爆炸  
B. 限制新旧策略的概率比变化幅度  
C. 减少 Q 值的过估计  
D. 加快收敛速度

**3. 【单选】以下哪个算法专门针对连续动作空间设计？**

A. DQN  
B. Double DQN  
C. TD3  
D. Dueling DQN

**4. 【多选】以下关于 DQN 和 PPO 的说法正确的有？**

A. DQN 是 Off-policy 算法，PPO 是 On-policy 算法  
B. DQN 只能处理离散动作空间  
C. PPO 通过 Clip 机制稳定策略更新  
D. 两者都使用目标网络

**5. 【简答】请简述 Double DQN 如何解决 DQN 的过估计问题。**

---

## 七、参考答案

### 选择题答案

**1. 答案：B**

解析：DQN 的经验回放缓冲区存储智能体与环境交互产生的经验 $(s, a, r, s', done)$。随机从缓冲区中抽样打破了连续样本间的时间相关性，使梯度更新更稳定。A 选项 Q 表是传统 Q 学习的方法；C、D 选项与经验回放无关。

**2. 答案：B**

解析：PPO 的 Clip 函数将新旧策略的概率比 $r_t(\theta) = \pi_\theta(a_t|s_t) / \pi_{\theta_{old}}(a_t|s_t)$ 限制在 $[1-\epsilon, 1+\epsilon]$ 范围内，防止策略在单次更新中变化过大导致性能崩溃。A 选项梯度裁剪是 `torch.nn.utils.clip_grad_norm_` 的作用；C 选项减少过估计是 Double DQN 的贡献；D 选项不是 Clip 的主要目的。

**3. 答案：C**

解析：TD3（Twin Delayed Deep Deterministic Policy Gradient）是专门为连续动作空间设计的算法，使用确定性策略输出连续动作值。DDPG/DQN 系列的其他变体（Double DQN、Dueling DQN）仍然只适用于离散动作空间。A、B、D 选项的算法都是基于离散动作空间的 Q 学习变体。

**4. 答案：A、B、C**

解析：
- A 正确：DQN 使用经验回放是 Off-policy；PPO 默认使用当前策略采集数据是 On-policy
- B 正确：DQN 的 $\max_a Q(s,a)$ 天然只适用于离散动作空间
- C 正确：PPO 通过 Clip 限制策略变化幅度，保证训练稳定
- D 错误：DQN 使用目标网络，但 PPO 不使用目标网络（其稳定性来自 Clip 机制）

**5. 答案：**

Double DQN 通过**解耦动作选择和动作评估**来解决 DQN 的过估计问题：

- **标准 DQN**：目标 Q 值 = $r + \gamma \max_{a'} Q_{\theta'}(s', a')$，使用目标网络同时选择最优动作并评估，容易放大 Q 值噪声导致系统性过估计

- **Double DQN**：分两步计算
  1. 用**在线网络**选择最优动作：$a^* = \arg\max_{a'} Q_\theta(s', a')$
  2. 用**目标网络**评估该动作：$Q_{\theta'}(s', a^*)$

这样避免了"用最大估计值作为最大真实值"的过度乐观问题，减少过估计，使价值估计更准确，训练更稳定。

---

## 知识衔接

本章两个算法与前序内容形成清晰的演进脉络：

**从 Q 学习到 DQN**：第 14-2 章的 Q 学习用表格存储状态-动作对的价值，DQN 用神经网络代替了这个表格。这个替换带来了表达能力的飞跃（可以处理图像输入），但也引入了训练稳定性问题——这正是经验回放和目标网络被引入的原因。

**从策略梯度到 PPO**：策略梯度方法直接优化策略参数，但天然是 On-policy 的——每次更新后历史数据失效。PPO 通过重要性采样和 Clip 机制部分解决了这个问题，在保持更新方向正确的同时限制更新幅度，实现了稳定高效的策略优化。

**与后续内容的关联**：这两个算法构成了现代深度强化学习的基石。DQN 的思想启发了后续诸多值函数方法（如 Dueling DQN、Double DQN、Rainbow）；PPO 的简洁有效使其成为 Actor-Critic 族算法的标杆，后续的 A2C/A3C、SAC、TD3 等都可以看作 PPO 思想的延伸。第 14-4 章的机器人 RL 训练实战将直接基于这些算法实现具身智能控制。

---

*本章完 | 下一章：[14-4 机器人强化学习训练实战](14-4-机器人强化学习训练实战.md)*
