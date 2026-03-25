# 15-3 GAIL 生成对抗模仿学习

!!! info "前置知识"
    - 强化学习基础（策略梯度、TRPO、PPO）
    - GAN（生成对抗网络）基本原理
    - 模仿学习（行为克隆、DAgger）
    - 深度学习（神经网络、PyTorch 基础）

---

> **前置说明**：行为克隆直接复制专家动作，但会遇到"分布偏移"问题——智能体一旦偏离专家见过的状态，误差会不断累积。2016年，Ho 和 Ermon 在论文《Generative Adversarial Imitation Learning》中提出了 GAIL，将博弈论中的生成对抗思想引入模仿学习，让智能体在与判别器的对抗中自发学会专家行为。本节将从 GAN 到 GAIL 的思想迁移出发，系统讲解 GAIL 的核心原理、实现细节与训练技巧。

---

## 1. GAIL 概述

### 1.1 从 GAN 到 GAIL

**生成对抗网络（GAN）**的核心思想是通过对抗训练让生成器 $G$ 学会模拟真实数据分布：

```
真实数据 → 判别器 D → 判断真假
生成器 G(z) → 判别器 D → 判断真假
          ↓ 对抗优化
生成器学会模拟真实分布
```

**GAIL 沿用了这一框架，但将"生成图片"替换为"生成轨迹"**：

| GAN | GAIL |
|-----|------|
| 生成器 $G$ 生成图片 | 策略 $\pi$ 生成轨迹 |
| 判别器 $D$ 区分真实图片/生成图片 | 判别器 $D$ 区分专家轨迹/策略轨迹 |
| 真实数据分布 $p_{data}$ | 专家轨迹分布 $\pi_E$ |
| 生成器学着骗过判别器 | 策略学着骗过判别器 |

```
专家轨迹 (s,a) → 判别器 D → 输出：这是专家行为
策略轨迹 π(s,a) → 判别器 D → 输出：这是策略行为
               ↓ 对抗优化
            策略越来越像专家
```

### 1.2 GAIL 的核心思想

**不直接模仿动作，而是学习一个隐式的奖励函数。**

GAIL 的关键洞察是：与其让智能体记住"在状态 $s$ 下应该动作为 $a$"，不如让它学会"判断一个 $(s,a)$ 对有多像专家行为"。判别器的输出可以被当作奖励信号，驱动策略优化向专家行为靠拢。

这解决了行为克隆的两个核心问题：
1. **不需要逐状态地复制动作**，而是通过奖励泛化到未见过的状态
2. **不需要在线访问专家**，对抗信号来自判别器自身

### 1.3 与 IRL 的关系

GAIL 本质上是 IRL 的一个实用近似。传统 IRL 需要解决内层 RL 优化问题（给定奖励找最优策略）和外层 IRL 优化问题（给定轨迹推断奖励），计算代价极高。GAIL 用判别器代替了显式奖励推断，用 PPO/TRPO 代替了内层 RL，用神经网络端到端地同时学习奖励和策略。

```
┌─────────────────────────────────────────────────────────────┐
│                    逆向强化学习 (IRL)                          │
│   max_{r} min_{π} [ -log P(π_E | r) + λH(π) ]               │
│   内层：RL 求解最优策略（计算代价高）                           │
└─────────────────────────────────────────────────────────────┘
                              ↓ 近似
┌─────────────────────────────────────────────────────────────┐
│                  生成对抗模仿学习 (GAIL)                        │
│   min_{π} max_{D} [ -log D(s,a_E) - log(1-D(s,a_π)) ]       │
│   用判别器代替显式奖励函数，用 PPO 代替内层 RL                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. GAIL 原理详解

### 2.1 问题建模

给定专家轨迹数据集 $\mathcal{D}_E = \{\tau_1, \tau_2, ..., \tau_N\}$，其中每个轨迹 $\tau = (s_0, a_0, s_1, a_1, ..., s_T)$。

GAIL 寻找一个参数化的判别器 $D_\omega(s,a)$，它输出一个概率——给定状态-动作对 $(s,a)$ 来自专家轨迹的可能性。同时优化一个策略 $\pi_\phi(a|s)$，让它生成的轨迹能够"骗过"判别器。

### 2.2 判别器设计

判别器 $D_\omega(s,a)$ 是一个二分类神经网络，接收状态-动作对作为输入，输出一个标量表示"该 $(s,a)$ 来自专家"概率。

**网络结构**（以连续控制任务为例）：

```python
class Discriminator(nn.Module):
    """
    GAIL 判别器网络
    输入：状态-动作对 (s, a)
    输出：属于专家的概率 D(s,a) ∈ [0, 1]
    """
    def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
        super().__init__()
        # 将状态和动作拼接输入
        input_dim = state_dim + action_dim
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())  # 输出概率
        self.network = nn.Sequential(*layers)
    
    def forward(self, state, action):
        """
        前向传播
        Args:
            state: 状态张量 (batch_size, state_dim)
            action: 动作张量 (batch_size, action_dim)
        Returns:
            D(s,a): 专家概率 (batch_size, 1)
        """
        # 拼接状态和动作
        sa = torch.cat([state, action], dim=-1)
        return self.network(sa)
    
    def get_reward(self, state, action):
        """
        从判别器获取奖励信号（供策略优化使用）
        奖励函数：r(s,a) = log(D(s,a)) - log(1 - D(s,a))
        当 D→1（像专家）→ 奖励高；当 D→0（不像专家）→ 奖励低
        """
        d = self.forward(state, action)
        # 使用 log(D) - log(1-D) 作为奖励
        reward = torch.log(d + 1e-8) - torch.log(1 - d + 1e-8)
        return reward
```

**损失函数**：

判别器的目标是区分专家轨迹和策略轨迹，最小化二元交叉熵损失：

$$
\mathcal{L}(\omega) = -\mathbb{E}_{(s,a) \sim \pi_E}[\log D_\omega(s,a)] - \mathbb{E}_{(s,a) \sim \pi}[\log(1 - D_\omega(s,a))]
$$

```python
def compute_discriminator_loss(D, states_exp, actions_exp, states_pol, actions_pol):
    """
    计算判别器损失
    Args:
        D: 判别器网络
        states_exp, actions_exp: 专家状态-动作对
        states_pol, actions_pol: 策略状态-动作对
    Returns:
        判别器损失 (标量)
    """
    # 专家样本：标签为 1（真）
    exp_output = D(states_exp, actions_exp)
    loss_exp = F.binary_cross_entropy(exp_output, torch.ones_like(exp_output))
    
    # 策略样本：标签为 0（假）
    pol_output = D(states_pol, actions_pol)
    loss_pol = F.binary_cross_entropy(pol_output, torch.zeros_like(pol_output))
    
    return loss_exp + loss_pol
```

### 2.3 奖励函数定义

GAIL 的巧妙之处在于：**判别器的输出可以直接作为奖励信号**。

GAIL 的奖励函数为：

$$
r(s,a) = \log D(s,a) - \log(1 - D(s,a))
$$

这个奖励函数的物理含义是：
- **$D(s,a) \to 1$**（判别器确信是专家）→ $r \to +\infty$（高奖励，策略应该多做这类行为）
- **$D(s,a) \to 0$**（判别器确信是策略）→ $r \to -\infty$（负奖励，策略应该避免这类行为）
- **$D(s,a) = 0.5$**（无法区分）→ $r = 0$（中立）

GAIL 的完整优化目标（联合目标）为：

$$
\min_{\pi} \max_{D} \mathbb{E}_{\pi}[\log(1 - D(s,a))] + \mathbb{E}_{\pi_E}[\log D(s,a)]
$$

### 2.4 策略优化

获得奖励信号 $r(s,a)$ 后，用任意的强化学习算法优化策略。论文原版使用 TRPO，实践中 PPO 更为常用且稳定。

```python
def compute_policy_loss(policy, states, actions, old_log_probs, advantages):
    """
    计算 PPO 策略损失
    Args:
        policy: 策略网络
        states: 状态批次
        actions: 动作批次
        old_log_probs: 旧策略的对数概率
        advantages: 优势函数估计
    Returns:
        policy_loss: PPO clipped surrogate loss
    """
    # 计算新策略的对数概率
    dist = policy.get_distribution(states)
    new_log_probs = dist.log_prob(actions)
    
    # PPO clipped surrogate objective
    ratio = torch.exp(new_log_probs - old_log_probs)
    surr1 = ratio * advantages
    surr2 = torch.clamp(ratio, 1 - 0.2, 1 + 0.2) * advantages
    policy_loss = -torch.min(surr1, surr2).mean()
    
    return policy_loss
```

GAIL 的完整训练循环：

```python
"""
GAIL 训练循环（基于 PPO）
"""
def train_gail(env, expert_trajectories, state_dim, action_dim,
               discriminator_iters=5, ppo_epochs=10, 
               total_timesteps=100000, batch_size=64):
    """
    GAIL 训练主循环
    Args:
        env: Gymnasium 环境
        expert_trajectories: 专家轨迹数据
        state_dim: 状态维度
        action_dim: 动作维度
        discriminator_iters: 每回合判别器更新次数
        ppo_epochs: PPO 策略更新轮数
        total_timesteps: 总训练步数
        batch_size: 批次大小
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 初始化网络
    policy = ActorCritic(state_dim, action_dim).to(device)
    discriminator = Discriminator(state_dim, action_dim).to(device)
    discriminator_optimizer = optim.Adam(discriminator.parameters(), lr=3e-4)
    policy_optimizer = optim.Adam(policy.parameters(), lr=3e-4)
    
    # 准备专家数据
    exp_states = torch.FloatTensor(expert_trajectories['states']).to(device)
    exp_actions = torch.FloatTensor(expert_trajectories['actions']).to(device)
    
    total_steps = 0
    
    while total_steps < total_timesteps:
        # ====== 1. 用当前策略收集轨迹 ======
        rollouts = collect_rollouts(env, policy, num_episodes=10)
        pol_states = torch.FloatTensor(rollouts['states']).to(device)
        pol_actions = torch.FloatTensor(rollouts['actions']).to(device)
        pol_log_probs = torch.FloatTensor(rollouts['log_probs']).to(device)
        pol_advantages = torch.FloatTensor(rollouts['advantages']).to(device)
        
        # ====== 2. 更新判别器 ======
        for _ in range(discriminator_iters):
            exp_indices = torch.randperm(len(exp_states))
            pol_indices = torch.randperm(len(pol_states))
            
            for i in range(0, min(len(exp_indices), len(pol_indices)), batch_size):
                exp_batch_idx = exp_indices[i:i+batch_size]
                pol_batch_idx = pol_indices[i:i+batch_size]
                
                exp_s = exp_states[exp_batch_idx]
                exp_a = exp_actions[exp_batch_idx]
                pol_s = pol_states[pol_batch_idx]
                pol_a = pol_actions[pol_batch_idx]
                
                d_loss = compute_discriminator_loss(
                    discriminator, exp_s, exp_a, pol_s, pol_a
                )
                discriminator_optimizer.zero_grad()
                d_loss.backward()
                discriminator_optimizer.step()
        
        # ====== 3. 用判别器奖励更新策略（PPO） ======
        for _ in range(ppo_epochs):
            new_log_probs = policy.get_log_prob(pol_states, pol_actions)
            
            ratio = torch.exp(new_log_probs - pol_log_probs)
            surr1 = ratio * pol_advantages
            surr2 = torch.clamp(ratio, 1-0.2, 1+0.2) * pol_advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # GAIL 奖励作为额外损失
            reward_loss = -discriminator.get_reward(pol_states, pol_actions).mean()
            
            total_loss = policy_loss + 0.1 * reward_loss
            
            policy_optimizer.zero_grad()
            total_loss.backward()
            policy_optimizer.step()
        
        total_steps += len(rollouts['states'])
        if total_steps % 10000 == 0:
            avg_reward = rollouts['rewards'].mean()
            print(f"Steps: {total_steps}, Avg Reward: {avg_reward:.2f}")
    
    return policy, discriminator
```

---

## 3. GAIL vs IRL

### 3.1 核心区别

| 维度 | GAIL | IRL |
|------|------|-----|
| **优化目标** | 最小化轨迹分布差异（对抗） | 推断隐式奖励函数（逆向） |
| **是否显式建模奖励** | 否（奖励由判别器隐式提供） | 是（显式学习奖励函数） |
| **内层 RL 问题** | 用 PPO/TRPO 近似（无需精确求解） | 需要精确求解（计算代价高） |
| **计算复杂度** | 较低（端到端对抗训练） | 较高（内外层双层优化） |
| **可解释性** | 低（隐式奖励难以解释） | 高（显式奖励函数可分析） |
| **泛化能力** | 依赖判别器的泛化性 | 奖励函数可迁移到新环境 |

### 3.2 优势对比

**GAIL 的优势**：

1. **无需求解内层 RL**：传统 IRL 需要在每步迭代中求解 RL 优化问题，GAIL 用判别器奖励 + PPO 一步近似
2. **样本效率高**：只需要一次专家数据收集，后续对抗训练无需在线专家
3. **端到端可微**：判别器和策略可以联合优化，梯度直接流动
4. **灵活可扩展**：判别器结构可以定制（如引入状态-only 判别器）

**IRL 的优势**：

1. **可解释性强**：学到的奖励函数可以直接分析，理解专家行为动机
2. **可迁移**：奖励函数可以在新环境中复用，或用于 reward shaping
3. **理论保障**：最大熵 IRL 有严格的理论保证

### 3.3 适用场景

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| **大规模连续控制**（机器人操作） | GAIL | 计算效率高，可处理高维动作空间 |
| **需要可解释奖励**（自动驾驶决策分析） | IRL | 显式奖励函数便于分析和验证 |
| **专家数据稀缺** | GAIL | 对抗训练可以泛化，但需要足够覆盖核心状态 |
| **需要迁移到新环境** | IRL | 学到的奖励函数可跨环境复用 |
| **训练稳定性优先** | GAIL + PPO | 实践中比纯 IRL 更稳定 |

---

## 4. GAIL 变体

### 4.1 GAIL-LS（Least Squares GAIL）

**问题**：原始 GAIL 使用 sigmoid 交叉熵损失作为判别器目标，在类别重叠严重时梯度消失，训练不稳定。

**解决**：用最小二乘损失替代交叉熵损失。

**判别器输出改为线性**，不再经过 Sigmoid：

$$
\min_D \mathbb{E}_\pi[(D(s,a) - 1)^2] + \mathbb{E}_{\pi_E}[(D(s,a))^2]
$$

```python
class DiscriminatorLS(nn.Module):
    """
    GAIL-LS 判别器（Least Squares 版本）
    输出为实数值，不使用 Sigmoid
    """
    def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
        super().__init__()
        input_dim = state_dim + action_dim
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, 1))
        # 不使用 Sigmoid，直接输出实数
        self.network = nn.Sequential(*layers)
    
    def forward(self, state, action):
        sa = torch.cat([state, action], dim=-1)
        return self.network(sa)  # 输出实数


def compute_ls_discriminator_loss(D, states_exp, actions_exp, states_pol, actions_pol):
    """Least Squares 判别器损失"""
    # 专家样本：目标值为 1
    exp_output = D(states_exp, actions_exp)
    loss_exp = ((exp_output - 1) ** 2).mean()
    
    # 策略样本：目标值为 0
    pol_output = D(states_pol, actions_pol)
    loss_pol = (pol_output ** 2).mean()
    
    return loss_exp + loss_pol


def gail_ls_reward(D, state, action):
    """GAIL-LS 奖励函数"""
    d = D(state, action)
    # 奖励 = -d^2，策略需要让 d 变小
    return -d.pow(2)
```

### 4.2 AIRL（Adversarial Inverse Reinforcement Learning）

**问题**：GAIL 学到的隐式奖励难以解释，且无法迁移。GAIL 的最优策略对应某个奖励函数，但这个奖励函数本身没有被显式建模。

**解决**：AIRL 同时学习显式奖励函数 $r_\theta(s,a)$ 和一个势函数 $\phi(s)$，使得奖励可解释。

```python
class AIRLDiscriminator(nn.Module):
    """
    AIRL 判别器：同时学习奖励函数和势函数
    f(s,a,s') = r(s,a) + γ*φ(s') - φ(s)
    D = exp(f) / (exp(f) + π(a|s))
    """
    def __init__(self, state_dim, action_dim, gamma=0.99, hidden_dims=[256, 256]):
        super().__init__()
        self.gamma = gamma
        
        # 奖励网络 r(s,a)
        input_dim = state_dim + action_dim
        reward_layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims[:1]:
            reward_layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        reward_layers.append(nn.Linear(prev_dim, 1))
        self.reward_net = nn.Sequential(*reward_layers)
        
        # 势函数网络 φ(s)
        phi_layers = []
        prev_dim = state_dim
        for h_dim in hidden_dims[:1]:
            phi_layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        phi_layers.append(nn.Linear(prev_dim, 1))
        self.phi_net = nn.Sequential(*phi_layers)
    
    def forward(self, state, action, next_state, log_pi=None):
        """
        计算 AIRL 判别器输出
        Args:
            state: 当前状态
            action: 动作
            next_state: 下一状态
            log_pi: 策略在 (s,a) 的对数概率（可选）
        Returns:
            D(s,a,s') - 专家概率
        """
        r = self.reward_net(torch.cat([state, action], dim=-1))
        phi_s = self.phi_net(state)
        phi_sp1 = self.phi_net(next_state)
        
        # f = r + γ*φ(s') - φ(s)
        f = r + self.gamma * phi_sp1 - phi_s
        
        if log_pi is not None:
            # D = sigmoid(f - log_pi)，数值稳定实现
            d = torch.sigmoid(f - log_pi.unsqueeze(-1))
        else:
            d = torch.sigmoid(f)
        
        return d
    
    def get_explicit_reward(self, state, action):
        """获取可解释的显式奖励"""
        return self.reward_net(torch.cat([state, action], dim=-1))
```

### 4.3 Discriminator 设计改进

**状态-only 判别器**：只判断状态 $s$ 而非 $(s,a)$，可减少判别器的过拟合，但需要额外的动作建模。

**能量模型（Energy-based Discriminator）**：用能量函数 $E(s,a)$ 替代概率输出，$p(a|s) \propto \exp(-E(s,a))$。

```python
class EnergyBasedDiscriminator(nn.Module):
    """
    能量模型判别器
    能量越低越像专家行为
    """
    def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
        super().__init__()
        input_dim = state_dim + action_dim
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, 1))
        self.network = nn.Sequential(*layers)
    
    def forward(self, state, action):
        """输出能量值 E(s,a)，越低越像专家"""
        sa = torch.cat([state, action], dim=-1)
        return self.network(sa)  # 无 Sigmoid，能量可正可负
    
    def get_reward(self, state, action):
        """奖励 = -energy，越低能量奖励越高"""
        energy = self.forward(state, action)
        return -energy
```

---

## 5. 训练技巧

### 5.1 数据收集策略

**专家数据质量比数量更重要**。GAIL 对专家轨迹的要求：

| 要求 | 说明 | 建议 |
|------|------|------|
| **状态覆盖度** | 专家轨迹应覆盖策略会遇到的主要状态空间 | 收集多场景、多起始点的轨迹 |
| **动作合理性** | 专家动作应该在智能体的物理能力范围内 | 避免不可能的动作 |
| **轨迹长度** | 每条轨迹应足够长以展示完整任务 | 避免过短的截断轨迹 |
| **数据去噪** | 移除明显错误/噪声的示范 | 人工审核或自动异常检测 |

**策略轨迹收集**：

```python
def collect_rollouts(env, policy, num_episodes=10, max_steps=1000):
    """
    收集策略轨迹
    Args:
        env: Gymnasium 环境
        policy: 策略网络
        num_episodes: 收集的回合数
        max_steps: 每回合最大步数
    Returns:
        rollouts: 包含 states, actions, rewards, log_probs, advantages 的字典
    """
    rollouts = {
        'states': [], 'actions': [], 'rewards': [],
        'log_probs': [], 'advantages': [], 'returns': []
    }
    
    for _ in range(num_episodes):
        state, _ = env.reset()
        episode_states, episode_actions = [], []
        episode_rewards, episode_log_probs = [], []
        episode_dones = []
        
        for step in range(max_steps):
            state_t = torch.FloatTensor(state).unsqueeze(0)
            action, log_prob, _ = policy.get_action(state_t)
            
            next_state, reward, terminated, truncated, _ = env.step(action)
            
            episode_states.append(state)
            episode_actions.append(action)
            episode_rewards.append(reward)
            episode_log_probs.append(log_prob.item() if log_prob is not None else 0.0)
            episode_dones.append(terminated or truncated)
            
            state = next_state
            if terminated or truncated:
                break
        
        # 计算 advantage 和 return（使用 GAE）
        advantages, returns = compute_gae(
            episode_rewards, episode_dones, 
            policy.get_value(state), gamma=0.99, lambda_=0.95
        )
        
        rollouts['states'].extend(episode_states)
        rollouts['actions'].extend(episode_actions)
        rollouts['rewards'].extend(episode_rewards)
        rollouts['log_probs'].extend(episode_log_probs)
        rollouts['advantages'].extend(advantages.tolist())
        rollouts['returns'].extend(returns.tolist())
    
    return rollouts
```

### 5.2 专家数据要求

| 参数 | 建议值 | 说明 |
|------|-------|------|
| 轨迹数量 | 10-100 条 | 取决于任务复杂度 |
| 每条轨迹长度 | 完整覆盖任务 | 至少包含一次完整任务执行 |
| 采样频率 | 与环境步长一致 | 避免过采样导致状态冗余 |
| 状态归一化 | 必须 | 专家状态和策略状态必须使用相同的归一化参数 |

### 5.3 收敛判断

GAIL 收敛的判断标准：

| 指标 | 判断方法 |
|------|---------|
| **判别器 loss** | 趋于 0.5-0.7（无法区分专家和策略） |
| **策略 episode reward** | 逐步提升并趋于稳定 |
| **策略与专家轨迹差异** | 计算轨迹间的 KL/JS 散度 |
| **判别器输出分布** | 专家和策略样本的 $D$ 输出分布重叠 |

```python
def check_convergence(discriminator, expert_states, expert_actions, 
                      policy_states, policy_actions, threshold=0.1):
    """
    检查 GAIL 是否收敛
    Args:
        threshold: 分布重叠阈值
    Returns:
        converged: 是否收敛
        metrics: 诊断指标字典
    """
    with torch.no_grad():
        exp_d = discriminator(expert_states, expert_actions).mean().item()
        pol_d = discriminator(policy_states, policy_actions).mean().item()
    
    # 判别器输出差异
    d_gap = abs(exp_d - pol_d)
    
    metrics = {
        'expert_D_mean': exp_d,
        'policy_D_mean': pol_d,
        'D_gap': d_gap
    }
    
    converged = d_gap < threshold
    return converged, metrics
```

### 5.4 常见问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 判别器快速过拟合 | 专家数据太少 | 增加专家数据，使用正则化 |
| 策略崩溃（reward 爆炸） | 判别器梯度不稳定 | 使用 GAIL-LS 或 PPO clip |
| 策略无法骗过判别器 | 策略探索不足 | 增加 PPO 探索噪声 |
| 训练震荡 | 学习率过大 | 降低学习率，使用学习率调度 |
| 专家数据与策略数据分布差异大 | 数据收集策略不当 | 归一化状态，控制初始状态分布 |

---

## 6. 代码实战：完整 GAIL 实现

### 6.1 项目结构

```
gail_robot/
├── gail.py              # 主训练脚本
├── networks.py          # 网络定义（策略、判别器）
├── utils.py             # 工具函数（数据采集、GAE计算）
├── requirements.txt     # 依赖列表
└── train.sh             # 训练启动脚本
```

### 6.2 网络定义

```python
"""
gail/networks.py - GAIL 网络定义
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


# ============ 策略网络（Actor-Critic）============
class ActorCritic(nn.Module):
    """
    Actor-Critic 策略网络
    - Actor: 输出动作均值和方差（连续控制）
    - Critic: 输出状态价值 V(s)
    """
    def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
        super().__init__()
        self.action_dim = action_dim
        
        # Actor：策略网络
        actor_layers = []
        prev_dim = state_dim
        for h_dim in hidden_dims:
            actor_layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        self.actor = nn.Sequential(*actor_layers)
        self.actor_head = nn.Linear(prev_dim, action_dim)
        
        # Critic：价值网络
        critic_layers = []
        prev_dim = state_dim
        for h_dim in hidden_dims:
            critic_layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        self.critic = nn.Sequential(*critic_layers)
        self.critic_head = nn.Linear(prev_dim, 1)
        
        # 动作输出层初始化（输出方差的对数）
        self.log_std = nn.Parameter(torch.zeros(action_dim))
    
    def forward(self, state):
        """前向传播，同时返回动作分布和状态价值"""
        h = self.actor(state)
        action_mean = self.actor_head(h)
        action_std = torch.exp(self.log_std)
        
        value = self.critic(state)
        value = self.critic_head(value)
        
        return action_mean, action_std, value
    
    def get_action(self, state, deterministic=False):
        """
        采样一个动作
        Args:
            state: 状态张量 (batch_size, state_dim) 或 (state_dim,)
            deterministic: 是否使用确定性策略（仅返回均值）
        Returns:
            action: 动作 numpy 数组
            log_prob: 对数概率
            value: 状态价值
        """
        if state.dim() == 1:
            state = state.unsqueeze(0)
        
        action_mean, action_std, value = self.forward(state)
        
        if deterministic:
            action = action_mean
            log_prob = None
        else:
            dist = torch.distributions.Normal(action_mean, action_std)
            action = dist.sample()
            log_prob = dist.log_prob(action).sum(dim=-1, keepdim=True)
        
        return action.squeeze(0).cpu().numpy(), log_prob, value.squeeze(0)
    
    def get_distribution(self, state):
        """获取当前状态下的动作分布"""
        action_mean, action_std, _ = self.forward(state)
        return torch.distributions.Normal(action_mean, action_std)
    
    def get_log_prob(self, state, action):
        """计算给定状态-动作对的对数概率"""
        dist = self.get_distribution(state)
        return dist.log_prob(action).sum(dim=-1, keepdim=True)
    
    def get_value(self, state):
        """获取状态价值"""
        if state.dim() == 1:
            state = state.unsqueeze(0)
        _, _, value = self.forward(state)
        return value


# ============ GAIL 判别器网络 ============
class Discriminator(nn.Module):
    """
    GAIL 判别器
    输入：状态-动作对 (s, a)
    输出：属于专家的概率 D(s,a) ∈ [0, 1]
    """
    def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
        super().__init__()
        input_dim = state_dim + action_dim
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        layers.extend([
            nn.Linear(prev_dim, 1),
            nn.Sigmoid()
        ])
        self.network = nn.Sequential(*layers)
    
    def forward(self, state, action):
        """
        Args:
            state: 状态张量 (batch, state_dim)
            action: 动作张量 (batch, action_dim)
        Returns:
            D(s,a): 专家概率 (batch, 1)
        """
        sa = torch.cat([state, action], dim=-1)
        return self.network(sa)
    
    def get_reward(self, state, action):
        """
        GAIL 奖励函数
        r(s,a) = log(D(s,a)) - log(1-D(s,a))
        当 D→1（像专家）→ 奖励高
        当 D→0（不像专家）→ 奖励低
        """
        d = self.forward(state, action)
        reward = torch.log(d + 1e-8) - torch.log(1 - d + 1e-8)
        return reward
```

### 6.3 工具函数

```python
"""
gail/utils.py - GAIL 训练工具函数
"""
import torch
import numpy as np


def compute_gae(rewards, dones, last_value, gamma=0.99, lambda_=0.95):
    """
    计算 GAE（Generalized Advantage Estimation）
    用于估计优势函数 A(s,a) = Q(s,a) - V(s)
    Args:
        rewards: 奖励列表
        dones: done 标志列表
        last_value: 最后一个状态的价值估计
        gamma: 折扣因子
        lambda_: GAE 参数
    Returns:
        advantages: 优势估计
        returns: 回报（用于价值网络训练）
    """
    advantages = []
    gae = 0
    values = [last_value] + list(rewards)
    
    # 反向计算 GAE
    for t in reversed(range(len(rewards))):
        delta = rewards[t] + gamma * values[t+1] * (1 - dones[t]) - values[t]
        gae = delta + gamma * lambda_ * (1 - dones[t]) * gae
        advantages.insert(0, gae)
    
    advantages = torch.FloatTensor(advantages)
    returns = advantages + torch.FloatTensor(values[:-1])
    
    # 归一化 advantages（稳定训练）
    if len(advantages) > 1 and advantages.std() > 1e-8:
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
    
    return advantages, returns


def collect_expert_trajectories(env, expert_policy, num_episodes=50, max_steps=1000):
    """
    收集专家轨迹数据
    Args:
        env: Gymnasium 环境
        expert_policy: 专家策略对象（可调用，返回动作 numpy）
        num_episodes: 收集的回合数
        max_steps: 每回合最大步数
    Returns:
        trajectories: 轨迹字典，包含 states, actions
    """
    trajectories = {
        'states': [], 'actions': [], 'rewards': []
    }
    
    for ep in range(num_episodes):
        state, _ = env.reset()
        ep_states, ep_actions, ep_rewards = [], [], []
        
        for step in range(max_steps):
            # 获取专家动作
            if isinstance(expert_policy, torch.nn.Module):
                state_t = torch.FloatTensor(state).unsqueeze(0)
                action, _, _ = expert_policy.get_action(state_t)
            else:
                action = expert_policy.get_action(state)
            
            # 执行动作
            next_state, reward, terminated, truncated, _ = env.step(action)
            
            ep_states.append(state)
            ep_actions.append(action)
            ep_rewards.append(reward)
            
            state = next_state
            if terminated or truncated:
                break
        
        trajectories['states'].extend(ep_states)
        trajectories['actions'].extend(ep_actions)
        trajectories['rewards'].extend(ep_rewards)
    
    return trajectories


def compute_discriminator_loss(D, states_exp, actions_exp, states_pol, actions_pol):
    """
    计算判别器损失（二元交叉熵）
    Args:
        D: 判别器网络
        states_exp, actions_exp: 专家状态-动作对
        states_pol, actions_pol: 策略状态-动作对
    Returns:
        判别器损失 (标量)
    """
    # 专家样本：标签为 1（真）
    exp_output = D(states_exp, actions_exp)
    loss_exp = F.binary_cross_entropy(exp_output, torch.ones_like(exp_output))
    
    # 策略样本：标签为 0（假）
    pol_output = D(states_pol, actions_pol)
    loss_pol = F.binary_cross_entropy(pol_output, torch.zeros_like(pol_output))
    
    return loss_exp + loss_pol


def collect_policy_rollouts(env, policy, num_episodes=10, max_steps=1000):
    """
    用当前策略收集轨迹（带 GAE 计算）
    Args:
        env: Gymnasium 环境
        policy: Actor-Critic 策略网络
        num_episodes: 收集的回合数
        max_steps: 每回合最大步数
    Returns:
        rollouts: 包含 states, actions, rewards, log_probs, advantages 的字典
    """
    rollouts = {
        'states
        'states': [], 'actions': [], 'rewards': [],
        'log_probs': [], 'advantages': [], 'returns': []
    }
    
    for _ in range(num_episodes):
        state, _ = env.reset()
        episode_states, episode_actions = [], []
        episode_rewards, episode_log_probs = [], []
        episode_dones = []
        
        for step in range(max_steps):
            state_t = torch.FloatTensor(state).unsqueeze(0)
            action, log_prob, value = policy.get_action(state_t)
            
            next_state, reward, terminated, truncated, _ = env.step(action)
            
            episode_states.append(state)
            episode_actions.append(action)
            episode_rewards.append(reward)
            episode_log_probs.append(log_prob.item() if log_prob is not None else 0.0)
            episode_dones.append(terminated or truncated)
            
            state = next_state
            if terminated or truncated:
                break
        
        # 计算 GAE advantage
        last_value = policy.get_value(torch.FloatTensor(state).unsqueeze(0)).item()
        advantages, returns = compute_gae(
            episode_rewards, episode_dones, last_value, gamma=0.99, lambda_=0.95
        )
        
        rollouts['states'].extend(episode_states)
        rollouts['actions'].extend(episode_actions)
        rollouts['rewards'].extend(episode_rewards)
        rollouts['log_probs'].extend(episode_log_probs)
        rollouts['advantages'].extend(advantages.tolist())
        rollouts['returns'].extend(returns.tolist())
    
    return rollouts
```

### 6.4 主训练脚本

```python
"""
gail/gail.py - GAIL 主训练脚本
基于 PyTorch + Gymnasium (连续控制任务)
"""
import torch
import torch.nn as nn
import torch.optim as optim
import gymnasium as gym
import numpy as np
from networks import ActorCritic, Discriminator
from utils import (
    compute_discriminator_loss, collect_expert_trajectories,
    collect_policy_rollouts, compute_gae
)


class ExpertPolicy:
    """
    专家策略：基于规则的控制器
    这里以 HalfCheetah-v5 为例，使用随机策略作为占位
    实际使用时替换为真实专家（人工示教、RL 预训练策略等）
    """
    def __init__(self, action_dim):
        self.action_dim = action_dim
    
    def get_action(self, state):
        """随机初始化策略作为专家占位"""
        return np.random.randn(self.action_dim)


def train_gail(env_name='HalfCheetah-v5', 
               expert_trajectories=None,
               total_timesteps=500000,
               discriminator_iters=5,
               ppo_epochs=10,
               batch_size=64,
               lr=3e-4,
               reward_weight=0.1):
    """
    GAIL 训练主函数
    Args:
        env_name: Gymnasium 环境名称
        expert_trajectories: 预加载的专家轨迹（可选）
        total_timesteps: 总训练步数
        discriminator_iters: 每回合判别器更新次数
        ppo_epochs: PPO 策略更新轮数
        batch_size: 批次大小
        lr: 学习率
        reward_weight: GAIL 奖励在策略损失中的权重
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # 创建环境
    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    print(f"State dim: {state_dim}, Action dim: {action_dim}")
    
    # 初始化网络
    policy = ActorCritic(state_dim, action_dim).to(device)
    discriminator = Discriminator(state_dim, action_dim).to(device)
    
    discriminator_optimizer = optim.Adam(discriminator.parameters(), lr=3e-4)
    policy_optimizer = optim.Adam(policy.parameters(), lr=3e-4)
    
    # 收集或加载专家轨迹
    if expert_trajectories is None:
        print("Collecting expert trajectories...")
        expert = ExpertPolicy(action_dim)
        expert_trajectories = collect_expert_trajectories(
            env, expert, num_episodes=50, max_steps=1000
        )
        print(f"Collected {len(expert_trajectories['states'])} expert samples")
    
    exp_states = torch.FloatTensor(expert_trajectories['states']).to(device)
    exp_actions = torch.FloatTensor(expert_trajectories['actions']).to(device)
    
    # 训练循环
    total_steps = 0
    episode_count = 0
    
    while total_steps < total_timesteps:
        # ====== 1. 用当前策略收集轨迹 ======
        rollouts = collect_policy_rollouts(env, policy, num_episodes=10)
        
        pol_states = torch.FloatTensor(rollouts['states']).to(device)
        pol_actions = torch.FloatTensor(rollouts['actions']).to(device)
        pol_log_probs = torch.FloatTensor(rollouts['log_probs']).to(device)
        pol_advantages = torch.FloatTensor(rollouts['advantages']).to(device)
        pol_returns = torch.FloatTensor(rollouts['returns']).to(device)
        
        # ====== 2. 更新判别器 ======
        for _ in range(discriminator_iters):
            # 打乱数据顺序
            exp_indices = torch.randperm(len(exp_states))
            pol_indices = torch.randperm(len(pol_states))
            
            for i in range(0, min(len(exp_indices), len(pol_indices)), batch_size):
                exp_batch_idx = exp_indices[i:i+batch_size]
                pol_batch_idx = pol_indices[i:i+batch_size]
                
                exp_s = exp_states[exp_batch_idx]
                exp_a = exp_actions[exp_batch_idx]
                pol_s = pol_states[pol_batch_idx]
                pol_a = pol_actions[pol_batch_idx]
                
                d_loss = compute_discriminator_loss(
                    discriminator, exp_s, exp_a, pol_s, pol_a
                )
                discriminator_optimizer.zero_grad()
                d_loss.backward()
                discriminator_optimizer.step()
        
        # ====== 3. 用 PPO 更新策略（结合 GAIL 奖励） ======
        for _ in range(ppo_epochs):
            # 重新计算对数概率（因为策略已经更新）
            new_log_probs = policy.get_log_prob(pol_states, pol_actions)
            
            # PPO clipped surrogate objective
            ratio = torch.exp(new_log_probs - pol_log_probs)
            surr1 = ratio * pol_advantages
            surr2 = torch.clamp(ratio, 1 - 0.2, 1 + 0.2) * pol_advantages
            policy_loss = -torch.min(surr1, surr2).mean()
            
            # 价值网络损失
            values = policy.get_value(pol_states)
            value_loss = ((values - pol_returns) ** 2).mean()
            
            # GAIL 奖励损失
            reward_loss = -discriminator.get_reward(pol_states, pol_actions).mean()
            
            # 总损失
            total_loss = policy_loss + 0.5 * value_loss + reward_weight * reward_loss
            
            policy_optimizer.zero_grad()
            total_loss.backward()
            policy_optimizer.step()
        
        total_steps += len(rollouts['states'])
        episode_count += 10
        
        if total_steps % 50000 < 1000:
            avg_reward = np.mean(rollouts['rewards'])
            with torch.no_grad():
                exp_d = discriminator(exp_states[:1000], exp_actions[:1000]).mean().item()
                pol_d = discriminator(pol_states[:1000], pol_actions[:1000]).mean().item()
            print(f"Steps: {total_steps} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"D_exp: {exp_d:.3f} | D_pol: {pol_d:.3f}")
    
    env.close()
    return policy, discriminator


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='GAIL 训练')
    parser.add_argument('--env', type=str, default='HalfCheetah-v5')
    parser.add_argument('--timesteps', type=int, default=500000)
    args = parser.parse_args()
    
    policy, discriminator = train_gail(env_name=args.env, total_timesteps=args.timesteps)
    torch.save(policy.state_dict(), 'gail_policy.pt')
    torch.save(discriminator.state_dict(), 'gail_discriminator.pt')
    print("训练完成，模型已保存")
```

### 6.5 依赖与运行

```text
# requirements.txt
gymnasium==0.29.1
torch>=2.0.0
numpy>=1.21.0
```

```bash
# train.sh
#!/bin/bash
python gail.py --env HalfCheetah-v5 --timesteps 500000
```

---

## 7. 练习题

### 7.1 选择题

1. **GAIL 的核心思想是？**
   - A. 直接模仿专家的每个状态-动作对
   - B. 通过对抗训练让判别器区分专家轨迹和策略轨迹
   - C. 先学习奖励函数，再用 RL 求解最优策略
   - D. 通过大量随机探索找到最优策略

2. **GAIL 的奖励函数来源于？**
   - A. 人工设计的奖励函数
   - B. 判别器的输出
   - C. 环境的原始奖励
   - D. 专家动作的均方误差

3. **GAIL vs IRL 的主要区别是？**
   - A. GAIL 需要在线专家，IRL 不需要
   - B. GAIL 不显式建模奖励函数，IRL 显式建模
   - C. GAIL 比 IRL 更容易过拟合
   - D. GAIL 不需要判别器

4. **GAIL-LS 相比原始 GAIL 的改进是？**
   - A. 使用了更深的网络
   - B. 用最小二乘损失替代交叉熵损失
   - C. 使用了更大的 batch size
   - D. 使用了 TRPO 替代 PPO

5. **判别器收敛时（训练良好），专家样本和策略样本的 D 输出应该？**
   - A. D(专家) = 1, D(策略) = 0
   - B. D(专家) ≈ D(策略) ≈ 0.5
   - C. D(专家) ≈ 0, D(策略) ≈ 1
   - D. D(专家) = 0.5, D(策略) = 0

### 7.2 填空题

6. GAIL 的优化目标可以表示为：$$\min_{\pi} \max_{D} \mathbb{E}_{\pi}[\log(1 - D(s,a))] + \mathbb{E}_{\pi_E}[\log D(s,a)]$$

7. GAIL 的奖励函数为：$$r(s,a) = \log D(s,a) - \log(1 - D(s,a))$$

8. AIRL 在 GAIL 基础上增加了**显式奖励函数**和**势函数**的学习。

9. 判别器过拟合会导致的问题是**策略崩溃或无法学到有效行为**。

10. GAE（Generalized Advantage Estimation）的两个关键参数是 $\gamma$（折扣因子）和 $\lambda$（GAE 系数）。

### 7.3 简答题

11. **简述 GAIL 如何解决行为克隆的分布偏移问题。**

12. **解释为什么 GAIL 的判别器不能训练得太好（过拟合），否则会导致什么问题？**

13. **对比 GAIL 和 AIRL，说明 AIRL 的优势是什么。**

14. **如果 GAIL 训练过程中策略奖励一直很低，请列出至少 3 种可能的原因及解决方案。**

### 7.4 编程题

15. **实现一个简化的 GAIL 判别器类**，包含：
    - `__init__` 方法：接受 state_dim, action_dim, hidden_dims
    - `forward` 方法：接受 state, action，返回 D(s,a)
    - `get_reward` 方法：返回 GAIL 奖励

16. **实现 GAIL 训练循环中的一步判别器更新**，包括：
    - 从专家数据和策略数据中采样
    - 计算二元交叉熵损失
    - 反向传播更新

---

## 8. 答案

### 8.1 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | GAIL 通过判别器区分专家轨迹和策略轨迹，用对抗训练让策略学会骗过判别器 |
| 2 | **B** | GAIL 的奖励来自判别器输出 $r = \log D - \log(1-D)$ |
| 3 | **B** | GAIL 不显式建模奖励函数，用判别器隐式提供奖励；IRL 显式学习奖励 |
| 4 | **B** | GAIL-LS 使用最小二乘损失替代交叉熵，训练更稳定，梯度不消失 |
| 5 | **B** | 判别器收敛时无法区分两者，输出趋于 0.5（最大熵原理） |

### 8.2 填空题答案

6. $\min_{\pi} \max_{D} \mathbb{E}_{\pi}[\log(1 - D(s,a))] + \mathbb{E}_{\pi_E}[\log D(s,a)]$

7. $r(s,a) = \log D(s,a) - \log(1 - D(s,a))$

8. 显式奖励函数；势函数

9. 策略崩溃或无法学到有效行为

10. $\gamma$（折扣因子）；$\lambda$（GAE 系数）

### 8.3 简答题答案

**11. GAIL 如何解决行为克隆的分布偏移问题**

行为克隆的问题是：智能体一旦偏离专家见过的状态，误差会累积，导致越来越大的偏差。GAIL 通过以下方式解决：

- **隐式奖励泛化**：判别器奖励不是逐状态记忆动作，而是学习"什么样的 $(s,a)$ 像专家行为"。即使遇到新状态，判别器也能给出合理的奖励信号。
- **对抗训练**：策略不断与判别器对抗，学会在判别器认为"像专家"的状态-动作对上获得高奖励，自然地向专家分布靠拢。
- **不需要精确复制**：策略只需要最大化奖励，而不需要逐状态地匹配专家动作，这避免了误差累积。

**12. 判别器过拟合会导致的问题**

如果判别器在专家数据上训练得太好（过拟合），会产生以下问题：

- **策略无法获得有效梯度**：当 $D(s,a) \approx 1$（专家）或 $D(s,a) \approx 0$（策略）时，奖励 $r = \log D - \log(1-D)$ 的梯度趋于 0，策略无法从判别器获得有效的学习信号。
- **奖励稀疏化**：过拟合的判别器会记住每一个专家样本，策略如果稍有不同时就会被严厉惩罚，导致奖励信号变得极其稀疏。
- **策略崩溃**：策略面对过拟合的判别器无法获得正反馈，可能崩溃到随机策略或特定行为模式。
- **训练震荡**：判别器过拟合后快速变化，导致策略的优化方向也跟着剧烈变化，训练不稳定。

**13. GAIL vs AIRL 的对比**

| 维度 | GAIL | AIRL |
|------|------|------|
| 奖励函数 | 隐式（判别器输出） | 显式（单独的奖励网络 $r_\theta(s,a)$） |
| 可解释性 | 低（无法直接看到奖励） | 高（显式奖励函数可直接分析） |
| 迁移能力 | 低（判别器难以跨环境复用） | 高（奖励函数可迁移到新环境） |
| 训练稳定性 | 中等 | 较好（AIRL 显式建模势函数） |

AIRL 的核心改进是同时学习一个势函数 $\phi(s)$，使得 $f(s,a,s') = r(s,a) + \gamma \phi(s') - \phi(s)$ 可以被解释为 advantage 的变分近似，学到的 $r(s,a)$ 具有真实的物理含义，可以用于 reward shaping 或跨任务迁移。

**14. GAIL 训练中奖励低的可能原因及解决方案**

1. **判别器过拟合**：专家数据太少，判别器记住了所有专家样本
   - 解决：增加专家数据量，使用数据增强，或在判别器损失中加入正则化

2. **策略探索不足**：策略陷入局部最优，无法生成多样化的轨迹
   - 解决：增大 PPO 的探索噪声（增加 action_std），或使用更大的熵奖励系数

3. **奖励权重过低**：GAIL 奖励在总损失中占比太小，被 PPO 目标覆盖
   - 解决：增大 `reward_weight` 参数（如从 0.1 增加到 0.5 或 1.0）

4. **专家数据质量差**：专家轨迹本身不能很好地完成任务
   - 解决：清洗专家数据，移除噪声或错误的示范，使用更高质量的专家

5. **状态/动作空间未归一化**：专家数据和策略数据尺度差异大
   - 解决：对状态和动作进行归一化处理，确保判别器输入分布一致

### 8.4 编程题答案

**15. 简化 GAIL 判别器实现**

```python
import torch
import torch.nn as nn


class Discriminator(nn.Module):
    """
    简化的 GAIL 判别器
    输入：状态-动作对 (s, a)
    输出：属于专家的概率 D(s,a) ∈ [0, 1]
    """
    def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
        super().__init__()
        input_dim = state_dim + action_dim
        layers = []
        prev_dim = input_dim
        for h_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, h_dim),
                nn.ReLU()
            ])
            prev_dim = h_dim
        layers.extend([
            nn.Linear(prev_dim, 1),
            nn.Sigmoid()
        ])
        self.network = nn.Sequential(*layers)
    
    def forward(self, state, action):
        """
        Args:
            state: 状态张量 (batch_size, state_dim)
            action: 动作张量 (batch_size, action_dim)
        Returns:
            D(s,a): 专家概率 (batch_size, 1)
        """
        sa = torch.cat([state, action], dim=-1)
        return self.network(sa)
    
    def get_reward(self, state, action):
        """
        GAIL 奖励函数
        r(s,a) = log(D(s,a)) - log(1 - D(s,a))
        """
        d = self.forward(state, action)
        reward = torch.log(d + 1e-8) - torch.log(1 - d + 1e-8)
        return reward
```

**16. 判别器一步更新实现**

```python
def update_discriminator_step(D, discriminator_optimizer,
                               exp_states, exp_actions,
                               pol_states, pol_actions,
                               batch_size=64):
    """
    GAIL 判别器一步更新
    Args:
        D: 判别器网络
        discriminator_optimizer: 判别器优化器
        exp_states, exp_actions: 专家状态-动作对
        pol_states, pol_actions: 策略状态-动作对
        batch_size: 批次大小
    Returns:
        d_loss: 本步的判别器损失
    """
    # 准备数据批次
    exp_len = len(exp_states)
    pol_len = len(pol_states)
    num_pairs = min(exp_len, pol_len)
    
    # 打乱顺序
    exp_indices = torch.randperm(exp_len)[:num_pairs]
    pol_indices = torch.randperm(pol_len)[:num_pairs]
    
    exp_s = exp_states[exp_indices]
    exp_a = exp_actions[exp_indices]
    pol_s = pol_states[pol_indices]
    pol_a = pol_actions[pol_indices]
    
    # 专家样本：标签为 1（真实数据）
    exp_output = D(exp_s, exp_a)
    loss_exp = nn.functional.binary_cross_entropy(
        exp_output, torch.ones_like(exp_output)
    )
    
    # 策略样本：标签为 0（生成数据）
    pol_output = D(pol_s, pol_a)
    loss_pol = nn.functional.binary_cross_entropy(
        pol_output, torch.zeros_like(pol_output)
    )
    
    # 总损失
    d_loss = loss_exp + loss_pol
    
    # 反向传播更新
    discriminator_optimizer.zero_grad()
    d_loss.backward()
    discriminator_optimizer.step()
    
    return d_loss.item()
```

---

> **结语**：GAIL 将生成对抗思想引入模仿学习，用对抗训练代替了逐状态的动作复制，解决了行为克隆的分布偏移问题。通过判别器隐式学习奖励函数，结合 PPO/TRPO 等强化学习算法端到端优化策略，是当前机器人示教学习的主流方法之一。下一节我们将学习更多模仿学习的前沿变体与实际应用。
