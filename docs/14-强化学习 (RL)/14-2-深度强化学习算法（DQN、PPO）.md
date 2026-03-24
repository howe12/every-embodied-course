# 14-2 深度强化学习算法（DQN、PPO）

**版本**: V1.0  
**作者**: Wendy | **课程系列**: ROS2机器人仿真与应用实践  
**适用对象**: 具备强化学习基础希望深入深度强化学习的学员  
**前置知识**: 强化学习基础概念（Q学习、MDP、策略与价值函数）

---

## 一、课程概述

上一章我们介绍了强化学习的基础概念，学会了如何用Q学习处理离散动作空间的问题。然而，当状态空间变得极其庞大——比如让机器人从摄像头图像中学习——传统的Q表就显得力不从心了。本章我们将学习两个里程碑式的深度强化学习算法：**DQN（Deep Q-Network）** 和 **PPO（Proximal Policy Optimization）**。

DQN由DeepMind于2013年提出，是首个成功将深度学习与强化学习结合的算法，让智能体仅凭像素输入就能学会玩Atari游戏。PPO则是OpenAI在2017年提出的策略优化算法，因其稳定性和易调参的特性成为当前最流行的强化学习算法之一，被广泛应用于机器人控制、自动驾驶等领域。

学完本章后，你将理解DQN如何利用卷积网络逼近Q函数、为何引入经验回放和目标网络、PPO的裁剪机制如何解决策略更新过大导致性能崩溃的问题，并能在Gym仿真环境中从零实现这两个算法。

---

## 二、章节设计

本章分为三个核心模块，遵循"概念→原理→实现→对比"的递进逻辑：

**模块一：DQN深度Q网络**  
我们从"如何用神经网络代替Q表"这一问题出发，逐步引入经验回放机制打破数据相关性、引入目标网络稳定训练，最终完整实现DQN算法。

**模块二：PPO近端策略优化**  
在回顾策略梯度方法的基础上，理解PPO如何通过裁剪概率比来约束策略更新幅度，解决经典策略梯度方法的"早熟收敛"和"策略崩溃"问题。

**模块三：对比与实践**  
从算法特性、适用场景、优缺点等多个维度横向对比DQN和PPO，并在Gym环境中完成实战练习。

---

## 三、理论内容

### 3.1 DQN（Deep Q-Network）

#### 3.1.1 从Q表到Q网络

在传统Q学习中，我们维护一张Q(s,a)的表格，记录每个状态-动作对的价值。当状态空间连续或极其庞大时（比如游戏画面有无数种像素组合），这张表既无法存储也无法高效查询。

DQN的核心思想很简单：用神经网络来逼近Q函数。输入状态s，输出每个动作a的Q值。这样无论状态多复杂，只要有合适的网络架构，模型总能学会从输入到Q值的映射。

具体而言，DQN的损失函数定义为：

$$L(\theta) = \mathbb{E}_{(s,a,r,s')\sim D}\left[\left(r + \gamma \max_{a'} Q_{\theta'}(s', a') - Q_\theta(s, a)\right)^2\right.$$

其中θ是当前Q网络的参数，θ'是目标网络的参数（稍后详解）。这个损失函数本质上是让当前Q网络的预测值逼近"目标值"——即即时奖励加上下一步的最优Q值。

#### 3.1.2 经验回放（Experience Replay）

如果直接用连续收集的样本训练神经网络，会遇到两个严重问题：第一，数据之间存在时间相关性（比如连续帧画面几乎相同），这会导致网络收敛到局部最优；第二，每个样本只被使用一次，数据利用效率极低。

DQN引入了**经验回放缓冲区**（Experience Replay Buffer）来解决这个问题。具体做法是：智能体与环境交互产生的每条经验(s, a, r, s', done)都存入一个有限大小的循环缓冲区。当缓冲区满了之后，最老的经验被丢弃。每当需要训练时，就从缓冲区中随机抽取一小批样本进行梯度下降。

这个设计带来了几个关键优势：随机抽样的方式打破了样本间的时间相关性；每个样本可以被重复使用，提高了数据效率；而且通过打乱样本顺序，可以使梯度更新更加稳定。

#### 3.1.3 目标网络（Target Network）

仔细观察DQN的损失函数，你会发现目标值`r + γ max_a' Q_θ'(s', a')`本身依赖于网络参数θ'。如果每一步都同时更新θ和目标值，就像在追逐一个不断移动的靶子，训练过程会非常不稳定。

DQN引入了**目标网络**（Target Network）来解决这个问题：维护两个神经网络——一个叫**在线网络**（Online Network），负责选择动作和计算当前Q值；另一个叫**目标网络**（Target Network），负责计算目标Q值。目标网络的参数θ'不每步更新，而是每隔固定步数才从在线网络复制过来。

这个设计大大提高了训练稳定性：目标值的变化速度被刻意放缓，给在线网络足够的时间去逼近它。后续研究（如Double DQN、Dueling DQN）证明，这种"软更新"或定期硬更新的机制对收敛至关重要。

#### 3.1.4 DQN算法流程

完整的DQN训练流程如下：首先初始化在线Q网络和目标网络（参数相同），并创建经验回放缓冲区。然后智能体在环境中运行，每步将经验存入缓冲区，同时从缓冲区随机采样一批样本计算损失并更新在线网络。每隔固定步数（如1000步），将在线网络的参数硬拷贝到目标网络。这个过程循环直到收敛。

### 3.2 PPO（Proximal Policy Optimization）

#### 3.2.1 策略梯度回顾

在深入PPO之前，我们需要回顾策略梯度方法的基本思想。不同于DQN通过估计每个动作的Q值来间接决策，策略梯度方法直接参数化策略函数π(a|s)，直接输出每个动作的概率分布。

策略梯度定理告诉我们，策略π_θ的梯度可以写为：

$$\nabla_\theta J(\theta) = \mathbb{E}_{s\sim d^\pi, a\sim\pi_\theta}\left[\nabla_\theta \log\pi_\theta(a|s) \cdot Q^{\pi_\theta}(s, a)\right]$$

简单来说：如果某个动作在某个状态下得到的Q值越高，我们就要增加在这个状态下选择这个动作的概率——通过增大log概率乘以Q值的梯度来实现。

经典的策略梯度方法（如REINFORCE）面临两个核心问题：**早熟收敛**（策略可能在找到次优解后就停止探索）和**策略崩溃**（单次更新幅度过大导致性能断崖式下降）。

#### 3.2.2 重要性采样与策略更新困境

为什么策略更新幅度过大会导致问题？在标准策略梯度中，我们需要用当前策略与环境交互收集数据，然后更新策略。但每次更新后，策略就变了，之前收集的数据不再与新策略匹配。这被称为"on-policy"问题——我们只能使用当前策略产生的数据。

**重要性采样**（Importance Sampling）是一种允许我们用旧策略的数据来估计新策略期望的数学技巧。对于期望值的估计有如下变换：

$$\mathbb{E}_{a\sim\pi_{\text{new}}}\left[f(a)\right] = \mathbb{E}_{a\sim\pi_{\text{old}}}\left[f(a) \cdot \frac{\pi_{\text{new}}(a)}{\pi_{\text{old}}(a)}\right]$$

但这个变换在策略差距较大时会失效——比率过大的样本会导致方差爆炸。这就是on-policy算法的根本局限：我们必须在新旧策略足够接近时才能安全地进行更新。

#### 3.2.3 PPO的核心：裁剪机制（Clipping）

PPO的核心贡献是提出了一个简单而有效的目标函数，既保留了重要性采样的灵活性，又通过裁剪约束防止策略变化过大。

PPO的损失函数定义为：

$$L^{\text{CLIP}}(\theta) = \mathbb{E}_t\left[\min\left(r_t(\theta) \cdot \hat{A}_t,\ \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) \cdot \hat{A}_t\right)\right]$$

其中r_t(θ) = π_θ(a_t|s_t) / π_{θ_old}(a_t|s_t)是新旧策略的概率比，Â_t是优势函数的估计，ε是一个小超参数（通常取0.2）。

clip函数的作用是：当概率比超出[1-ε, 1+ε]区间时，将其裁剪到边界值。这样，当优势为正（动作比平均好）时，损失函数会鼓励增大该动作的概率，但限制比例不超过1+ε；当优势为负时，函数会限制该动作的概率被过度降低。

直观理解：PPO在说"你可以更新策略，但要一步一步来"。如果一次更新试图把某个动作的概率从0.1变成0.9，clip函数会把这次更新的收益"清零"，迫使智能体采取更保守的更新步骤。

#### 3.2.4 PPO与TRPO的关系

PPO全称"近端策略优化"，它实际上是TRPO（信任区域策略优化）的简化版本。TRPO通过复杂的约束优化（使用共轭梯度和线性搜索）来保证策略更新在信任区域内，计算开销大且难以与很多网络架构兼容。PPO通过clip机制在单目标优化中实现了类似效果，计算效率高得多，实验效果也往往不逊于TRPO，因此迅速成为工业界和学术界的事实标准。

### 3.3 DQN vs PPO：算法特性对比

理解两个算法的差异有助于在实际项目中做出正确选择。

| 特性 | DQN | PPO |
|------|-----|-----|
| **算法类型** | 值函数方法（Value-based） | 策略梯度方法（Policy-based） |
| **输出** | 每个动作的Q值 | 每个动作的概率分布 |
| **动作空间** | 离散动作 | 离散+连续动作 |
| **策略类型** | 确定性策略（ε-贪心） | 随机策略 |
| **数据利用** | Off-policy（经验回放） | On-policy（也可变体为off-policy） |
| **稳定性** | 较稳定（目标网络加持） | 非常稳定（clip机制） |
| **超参数敏感度** | 中等 | 相对不敏感 |
| **采样效率** | 高（经验回放复用数据） | 低（每次更新需要重新采样） |
| **收敛速度** | 较慢 | 较快 |
| **典型应用** | Atari游戏、简单控制 | 机器人控制、自动驾驶、大语言模型对齐 |
| **代表成果** | AlphaGo、Atari玩家 | OpenAI Five、Dactyl机械手 |

DQN的核心优势在于off-policy特性带来的高数据效率——因为可以使用历史任意数据，所以样本利用率极高。但它只能处理离散动作、且策略是确定性的，这在很多连续控制场景中是不够的。PPO则通过随机策略可以更优雅地处理探索-利用平衡，clip机制让其极其稳定可靠，是目前最适合工程实践的强化学习算法之一。

---

## 四、实践内容

### 4.1 DQN代码实现

下面我们用PyTorch在CartPole环境下实现完整的DQN算法。CartPole是一个经典的控制问题：让杆子保持直立，状态是4维连续值（车位置、车速度、杆角度、杆角速度），动作是离散的左/右推车。

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
class DQN(nn.Module):
    """
    Q网络：输入状态，输出每个动作的Q值
    """
    def __init__(self, state_dim, action_dim, hidden_dim=128):
        super(DQN, self).__init__()
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
    """
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
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
        self.gamma = config.get('gamma', 0.99)          # 折扣因子
        self.epsilon = config.get('epsilon_start', 1.0) # 初始探索率
        self.epsilon_min = config.get('epsilon_min', 0.01)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.lr = config.get('lr', 1e-3)
        self.batch_size = config.get('batch_size', 64)
        self.target_update_freq = config.get('target_update_freq', 100)
        
        self.action_dim = action_dim
        self.total_steps = 0
        
        # 在线网络和目标网络
        self.q_net = DQN(state_dim, action_dim)
        self.target_net = DQN(state_dim, action_dim)
        self.target_net.load_state_dict(self.q_net.state_dict())
        
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=self.lr)
        self.replay_buffer = ReplayBuffer(capacity=config.get('replay_capacity', 10000))
    
    def select_action(self, state, training=True):
        """
        ε-贪心策略选择动作
        """
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.q_net(state_t)
            return q_values.argmax(dim=1).item()
    
    def store_transition(self, state, action, reward, next_state, done):
        self.replay_buffer.push(state, action, reward, next_state, done)
    
    def update(self):
        """
        从经验回放缓冲区采样，更新Q网络
        """
        if len(self.replay_buffer) < self.batch_size:
            return
        
        # 随机采样一批经验
        states, actions, rewards, next_states, dones = \
            self.replay_buffer.sample(self.batch_size)
        
        # 转换为Tensor
        states_t = torch.FloatTensor(states)
        actions_t = torch.LongTensor(actions)
        rewards_t = torch.FloatTensor(rewards)
        next_states_t = torch.FloatTensor(next_states)
        dones_t = torch.FloatTensor(dones)
        
        # 计算当前Q值
        q_values = self.q_net(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)
        
        # 计算目标Q值（使用目标网络）
        with torch.no_grad():
            next_q_values = self.target_net(next_states_t).max(dim=1)[0]
            target_q_values = rewards_t + self.gamma * next_q_values * (1 - dones_t)
        
        # 计算损失并更新
        loss = nn.MSELoss()(q_values, target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.q_net.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        # ε衰减
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.total_steps += 1
        
        # 定期更新目标网络
        if self.total_steps % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())
        
        return loss.item()


# ----------------------
# 4. 训练主循环
# ----------------------
def train_dqn(env_name='CartPole-v1', episodes=500, max_steps=500):
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
    
    agent = DQNAgent(state_dim, action_dim, config)
    returns = []
    
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
        
        if np.mean(returns[-20:]) >= 450:
            print(f"\n🎉 任务完成！连续20回合平均奖励达到 {np.mean(returns[-20:]):.1f}")
            break
    
    env.close()
    return returns


if __name__ == '__main__':
    print("=" * 60)
    print("开始训练 DQN (CartPole-v1)")
    print("=" * 60)
    returns = train_dqn(episodes=500)
```

运行这个脚本，你应该能看到智能体从最初只能坚持几步逐渐进步到稳定保持杆子直立（奖励≥195视为成功，≥475视为优秀）。

### 4.2 PPO代码实现

现在实现PPO算法。相比DQN，PPO需要同时维护策略网络和价值网络，并且在更新时显式计算新旧策略的概率比。

```python
import torch
import torch.nn as nn
import torch.optim as optim
import torch.distributions as distributions
import numpy as np
import gym
from collections import deque

torch.manual_seed(42)
np.random.seed(42)

# ----------------------
# 1. 定义Actor-Critic网络
# ----------------------
class ActorCritic(nn.Module):
    """
    Actor-Critic架构：策略网络（Actor）+ 价值网络（Critic）共享底层特征
    """
    def __init__(self, state_dim, action_dim, hidden_dim=64):
        super(ActorCritic, self).__init__()
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
    计算PPO裁剪损失
    
    参数:
        old_log_probs: 旧策略下采样动作的对数概率
        new_log_probs: 新策略下采样动作的对数概率  
        advantages: 优势函数估计
        clip_eps: 裁剪边界 (默认0.2)
    
    返回:
        裁剪后的策略损失和价值损失
    """
    # 概率比 r(θ) = exp(log π_new - log π_old)
    ratio = torch.exp(new_log_probs - old_log_probs)
    
    # 未裁剪的策略损失
    surr1 = ratio * advantages
    
    # 裁剪后的策略损失
    surr2 = torch.clamp(ratio, 1 - clip_eps, 1 + clip_eps) * advantages
    
    # 取较小者（外层min确保我们取下界）
    policy_loss = -torch.min(surr1, surr2).mean()
    
    return policy_loss


# ----------------------
# 3. PPO智能体
# ----------------------
class PPOAgent:
    def __init__(self, state_dim, action_dim, config):
        self.gamma = config.get('gamma', 0.99)
        self.gae_lambda = config.get('gae_lambda', 0.95)  # GAE参数
        self.clip_eps = config.get('clip_eps', 0.2)
        self.k_epochs = config.get('k_epochs', 10)         # 每次收集数据后的更新轮数
        self.mini_batch_size = config.get('mini_batch_size', 64)
        self.actor_lr = config.get('actor_lr', 3e-4)
        self.critic_lr = config.get('critic_lr', 1e-3)
        self.entropy_coef = config.get('entropy_coef', 0.01)  # 熵正则系数
        self.value_coef = config.get('value_coef', 0.5)       # 价值损失系数
        self.max_grad_norm = config.get('max_grad_norm', 0.5)
        
        self.action_dim = action_dim
        
        self.policy = ActorCritic(state_dim, action_dim)
        self.optimizer = optim.Adam([
            {'params': self.policy.shared.parameters(), 'lr': self.actor_lr},
            {'params': self.policy.actor.parameters(), 'lr': self.actor_lr},
            {'params': self.policy.critic.parameters(), 'lr': self.critic_lr},
        ])
    
    def select_action(self, state):
        """从当前策略采样动作"""
        with torch.no_grad():
            state_t = torch.FloatTensor(state)
            action_logits, value = self.policy(state_t)
            dist = distributions.Categorical(logits=action_logits)
            action = dist.sample()
            return action.item(), dist.log_prob(action), value.item()
    
    def compute_gae(self, rewards, values, dones, next_value):
        """
        计算广义优势估计（GAE）
        """
        advantages = []
        gae = 0
        values = list(values) + [next_value]
        
        for t in reversed(range(len(rewards))):
            delta = rewards[t] + self.gamma * values[t + 1] * (1 - dones[t]) - values[t]
            gae = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * gae
            advantages.insert(0, gae)
        
        return torch.FloatTensor(advantages)
    
    def update(self, trajectory):
        """
        用收集的轨迹数据更新策略
        
        trajectory: dict with keys: states, actions, rewards, dones, 
                   log_probs, values
        """
        states = torch.FloatTensor(np.array(trajectory['states']))
        actions = torch.LongTensor(trajectory['actions'])
        old_log_probs = torch.FloatTensor(trajectory['log_probs'])
        rewards = np.array(trajectory['rewards'])
        dones = np.array(trajectory['dones'])
        values = np.array(trajectory['values'])
        
        # 计算优势
        with torch.no_grad():
            _, next_value = self.policy(states[-1:])
            next_value = next_value.item()
        
        advantages = self.compute_gae(rewards, values, dones, next_value)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # K轮更新
        for _ in range(self.k_epochs):
            # 随机打乱并分批次
            indices = torch.randperm(len(states))
            for start in range(0, len(states), self.mini_batch_size):
                end = start + self.mini_batch_size
                idx = indices[start:end]
                
                batch_states = states[idx]
                batch_actions = actions[idx]
                batch_old_log_probs = old_log_probs[idx]
                batch_advantages = advantages[idx]
                
                # 获取新的 log_prob 和 value
                action_logits, values_pred = self.policy(batch_states)
                dist = distributions.Categorical(logits=action_logits)
                new_log_probs = dist.log_prob(batch_actions)
                entropy = dist.entropy().mean()
                
                # PPO策略损失
                policy_loss = compute_ppo_loss(
                    batch_old_log_probs, new_log_probs, batch_advantages, self.clip_eps
                )
                
                # 价值损失
                value_loss = nn.MSELoss()(values_pred.squeeze(), batch_advantages + batch_old_values)
                
                # 总损失 = 策略损失 + 价值损失 + 熵正则
                total_loss = policy_loss + self.value_coef * value_loss - self.entropy_coef * entropy
                
                self.optimizer.zero_grad()
                total_loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.optimizer.step()


# ----------------------
# 4. 训练主循环
# ----------------------
def collect_trajectory(env, agent, max_steps=2048):
    """收集一条轨迹的数据"""
    trajectory = {
        'states': [], 'actions': [], 'rewards': [],
        'dones': [], 'log_probs': [], 'values': []
    }
    
    state, _ = env.reset(seed=42)
    total_reward = 0
    
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
        total_reward += reward
        
        if done:
            state, _ = env.reset()
            total_reward = 0
    
    return trajectory, total_reward


def train_ppo(env_name='CartPole-v1', total_steps=100000, num_envs=1):
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
    
    episode_reward = deque(maxlen=20)
    step_count = 0
    update_count = 0
    
    while step_count < total_steps:
        trajectory, last_reward = collect_trajectory(env, agent)
        step_count += len(trajectory['rewards'])
        
        agent.update(trajectory)
        update_count += 1
        
        # 粗略估计奖励（因为是连续收集，取最后几个的平均）
        recent_reward = np.mean(trajectory['rewards'][-20:])
        episode_reward.append(np.sum(trajectory['rewards']))
        
        if update_count % 10 == 0:
            avg_reward = np.mean(list(episode_reward)[-20:])
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

### 4.3 在Gym环境中实验对比

在实际训练中，我们观察到两个算法的显著差异：

**DQN的特点**：
- 初期探索充分（ε从1.0缓慢衰减），但收敛后策略固定
- 经验回放使得样本利用效率高，但需要较大的缓冲区
- 训练曲线波动较大，但最终性能稳定
- 典型的"一次性突破"：可能在某个节点突然学会并稳定

**PPO的特点**：
- 训练曲线更加平滑，策略持续改进
- 熵正则鼓励持续探索，不容易陷入局部最优
- 采样效率较低（on-policy），但更新稳定
- 在CartPole上通常100-200个epoch即可达到450+的奖励

你可以修改代码中的超参数（如DQN的ε衰减速率、PPO的clip_eps）来感受它们对训练的影响。建议使用tensorboard或matplotlib绘制训练曲线进行对比分析。

---

## 五、知识衔接

本章两个算法与前序内容形成清晰的演进脉络。

**从Q学习到DQN**：第11-1章的Q学习用表格存储状态-动作对的价值，DQN用神经网络代替了这个表格。这个替换带来了表达能力的飞跃（可以处理图像输入），但也引入了训练稳定性问题——这正是经验回放和目标网络被引入的原因。

**从策略梯度到PPO**：策略梯度方法直接优化策略参数，但天然是on-policy的——每次更新后历史数据失效。PPO通过重要性采样和clip机制部分解决了这个问题，在保持更新方向正确的同时限制更新幅度，实现了稳定高效的策略优化。

**与后续内容的关联**：这两个算法构成了现代深度强化学习的基石。DQN的思想启发了后续诸多值函数方法（如Dueling DQN、Double DQN、Rainbow）；PPO的简洁有效使其成为Actor-Critic族算法的标杆，后续的A2C/A3C、PPO-SGC、SAC等都可以看作PPO思想的延伸。后续第12章的视觉驱动机器人控制将直接基于这些算法实现端到端策略学习。

---

## 六、总结拓展

### 6.1 核心要点回顾

本课程涵盖了深度强化学习两个最重要的算法：

**DQN的三个关键设计**：神经网络代替Q表解决大状态空间问题；经验回放打破数据相关性提高样本效率；目标网络稳定训练过程防止目标值震荡。这三个设计各司其职，缺一不可。

**PPO的核心洞察**：策略更新幅度过大会导致性能崩溃。通过限制新旧策略的概率比在1±ε范围内，既保留了策略改进的方向，又防止了极端更新。简洁的clip机制替代了TRPO复杂的约束优化，效果却毫不逊色。

### 6.2 思考题

1. **经验回放的局限性**：经验回放缓冲区中所有样本被平等对待，但显然有些经验比其他经验更重要（比如奖励稀疏环境中的稀疏奖励样本）。请思考如何设计一个优先回放（Prioritized Experience Replay）机制，让"更重要"的经验有更高概率被采样。

2. **DQN的过估计问题**：DQN使用max_a' Q_θ'(s', a')来估计目标Q值，但这会导致过估计（overestimation）——因为最大化操作会放大Q值的噪声。Double DQN通过使用在线网络选择动作、目标网络评估动作来解决这个问题。请简述Double DQN的更新公式，并与标准DQN进行对比。

3. **PPO的适应性**：PPO的clip边界ε是固定的，但在训练初期我们可能希望策略变化快一些，训练后期希望保守一些。请设计一个自适应调整clip边界的方案，并说明其合理性。

4. **算法选择决策**：假设你需要训练一个机器人手臂完成精细操作任务（如抓取鸡蛋），手臂关节角度是连续值、动作空间高维、且奖励信号稀疏。你会选择DQN还是PPO？为什么？如果奖励信号密集但需要持续探索呢？

### 6.3 练习题

**编程练习：实现Double DQN**

在标准DQN代码基础上，实现Double DQN算法。关键修改在于目标Q值的计算方式：

标准DQN: `target = r + γ * Q_target(next_state).max(1)[0]`

Double DQN: `target = r + γ * Q_target(next_state).gather(1, Q_online(next_state).argmax(1, keepdim=True))[0]`

请补全代码并对比两者在CartPole上的训练曲线差异。

**理论练习：PPO损失函数推导**

已知PPO的裁剪目标函数为 L^CLIP(θ) = E[min(r_t(θ)·A_t, clip(r_t(θ), 1-ε, 1+ε)·A_t)]，请分析：
- 当优势A_t > 0（动作为正优势）时，损失函数如何约束概率比r_t(θ)？
- 当优势A_t < 0（动作为负优势）时，损失函数如何约束概率比r_t(θ)？
- clip函数在这个机制中扮演了什么角色？

### 6.4 答案

**思考题答案**

1. **优先回放机制**：可以基于TD误差（|r + γ max_a' Q(s',a') - Q(s,a)|）来衡量样本重要性——TD误差越大，说明当前Q值估计越不准确，该样本越重要。实现方式有两种：基于排序的优先回放（SumTree结构）和基于概率的直接采样。注意需要引入重要性采样修正权重来抵消引入的偏差。

2. **Double DQN公式对比**：标准DQN使用目标网络同时选择和评估动作，可能导致过估计。Double DQN的分治策略将这两个操作解耦：先用在线网络选出最优动作（max_a' Q_online(s', a')），再用目标网络评估该动作的价值（Q_target(s', a*)）。这减少了过度乐观估计，实验通常显示能稳定提升性能2-5%。

3. **自适应clip边界**：可以在训练初期设置较大的ε（如0.3），鼓励大胆探索；随着训练推进逐渐衰减到较小的ε（如0.1），保证收敛稳定性。或者使用基于KL散度的自适应方法：每次更新后计算新旧策略的KL散度，如果KL过大则减小ε，过小则增大ε。这与TRPO的信任区域思想异曲同工。

4. **算法选择**：对于高维连续动作空间、奖励稀疏的精细操作任务，**PPO是更合适的选择**。原因：PPO原生支持连续动作空间（通过高斯策略或混合分布）；随机策略有利于稀疏奖励下的探索；Clip机制保证训练稳定，不会因为某次糟糕的更新毁掉辛苦积累的表现。如果奖励信号密集但需要持续探索，PPO同样适合，但也可以考虑SAC（软Actor-Critic）等off-policy算法获得更高样本效率。

**编程练习答案（Double DQN）**

```python
# 在update()方法中，将目标Q值计算改为：
with torch.no_grad():
    # Double DQN: 用在线网络选择动作，用目标网络评估
    online_next_q = self.q_net(next_states_t)
    best_actions = online_next_q.argmax(dim=1, keepdim=True)
    next_q_values = self.target_net(next_states_t).gather(1, best_actions).squeeze(1)
    target_q_values = rewards_t + self.gamma * next_q_values * (1 - dones_t)
```

**理论练习答案**

当A_t > 0时，损失函数鼓励增大r_t(θ)（增加选择该动作的概率），但r_t(θ)不能超过1+ε。当A_t < 0时，损失函数鼓励减小r_t(θ)（降低选择该动作的概率），但r_t(θ)不能低于1-ε。Clip函数的角色是"安全阀"：防止策略在单个更新步骤中变化过大（超过±ε的幅度），从而避免灾难性的策略退化。这个设计本质上是用一阶的clip操作替代了TRPO中复杂的二阶置信域约束，以极低的计算代价获得了类似的稳定性保证。

---

*本章完 | 下一章：12-1 视觉Transformer与机器人感知*
