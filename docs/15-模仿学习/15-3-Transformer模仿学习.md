# 15-3 Transformer模仿学习

**版本**: V2.0  
**作者**: Wendy | **课程系列**: ROS2机器人仿真与应用实践  
**适用对象**: 具备强化学习基础，熟悉深度学习与 PyTorch 的学员  
**前置知识**: 强化学习基础（MDP、策略梯度）、深度学习基础（Transformer、注意力机制、PyTorch）

---

## 一、课程概述

传统强化学习以马尔可夫决策过程（MDP）为框架，假设策略仅依赖当前状态做出决策。然而，真实的机器人任务中，智能体往往需要基于**观测历史**（多帧图像、关节角度序列、触觉反馈序列）进行决策，历史信息对于理解当前场景至关重要。例如，物体被遮挡时的轨迹预测、机械臂操作中的力反馈序列分析、人体姿态跟踪等场景，单独依赖当前帧几乎不可能做出正确决策。

**Transformer**（由 Vaswani 等人于 2017 年提出）最初用于自然语言处理，其核心优势在于通过**自注意力机制（Self-Attention）**建模任意距离的依赖关系。将 Transformer 引入序列决策问题，正是看中了这一特性——将状态、动作、奖励等视为"序列 token"，用注意力机制建模它们之间的远程依赖，从而在观测历史建模上取得突破性进展。

本课程系统讲解 Transformer 在模仿学习中的应用：从 **Decision Transformer（DT）** 的序列建模思想，到 **Trajectory Transformer（TT）** 的轨迹联合建模，再到 **ACT（Action Chunking Transformer）** 的动作分块与时序一致性优化，以及 **GATO、RT-1/RT-2** 等多任务多模态大模型。最后通过 Decision Transformer 的 PyTorch 简化实现，帮助读者从代码层面理解这一范式的核心设计。

学完本章后，你将理解 Transformer 处理序列决策的动机与优势，掌握 Decision Transformer、Trajectory Transformer 的数学原理与网络设计，深入理解 ACT 的动作分块与时序一致性机制，了解 GATO、RT-1/RT-2 等多模态大模型在机器人领域的应用，并能够实现简化版 Decision Transformer。

---

## 二、章节设计

**模块一：Transformer 在 RL 中的应用**  
理解为什么用 Transformer 处理序列决策，掌握 Attention 机制在策略学习中的作用，理解观测历史建模的核心意义。

**模块二：Decision Transformer**  
掌握 DT 的序列 token 化设计、回报-to-Go（Rtg）机制、因果掩码的注意力计算，理解 DT 相比传统 RL 的根本差异，掌握简化版 DT 的 PyTorch 实现。

**模块三：Trajectory Transformer**  
理解 TT 将整个轨迹联合建模为序列的思想，掌握基于 Beam Search 的动作解码，理解 TT 在长程任务中的优势。

**模块四：ACT（Action Chunking Transformer）**  
掌握动作分块机制、时序一致性设计，理解斯坦福 ALOHA 项目与 ACT 的关系，掌握 ACT 在双臂操作任务中的应用。

**模块五：其他 Transformer IL 方法**  
了解 GATO 的多任务 Agent 设计、RT-1/RT-2 的视觉-语言-动作模型思想，了解主要开源实现与资源。

---

## 三、理论内容

### 3.1 Transformer 在强化学习中的应用

#### 3.1.1 为什么用 Transformer 处理序列决策

传统 RL 算法（如 DQN、PPO、SAC）的策略网络结构通常是简单的多层感知机（MLP）或卷积神经网络（CNN），输入为当前状态 $s_t$，输出为动作 $a_t$ 或 Q 值。这类方法的隐含假设是：**决策仅依赖当前状态**，即满足马尔可夫性 $p(a_t | s_t, s_{t-1}, ..., s_0) = p(a_t | s_t)$。

然而，许多实际任务违反这一假设：

| 场景 | 问题描述 | 马尔可夫性违反原因 |
|------|---------|------------------|
| **视觉遮挡** | 目标被障碍物遮挡，单帧无法看到 | 需要历史帧推断目标运动 |
| **多模态行为** | 同一状态可对应多种合理动作 | 需要历史上下文消歧 |
| **接触任务** | 力反馈需在时序上理解（插拔、拧螺丝） | 接触力有物理延迟，需序列感知 |
| **长程规划** | 机械臂抓取需预判物体运动趋势 | 单帧无法推断运动方向 |
| **人体跟踪** | 关节角度历史反映运动意图 | 速度/加速度需从序列估计 |

**Transformer 的核心优势**：

1. **全局感受野**：Self-Attention 让每个 token 与序列中所有其他 token 直接交互，不受距离限制
2. **并行计算**：相比 RNN/LSTM，Transformer 可并行处理序列所有位置
3. **可解释性**：注意力权重直观反映不同历史时刻对当前决策的贡献
4. **多模态融合**：不同模态（图像、关节角度、触觉）可统一为 token 序列

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$

其中 $Q$（Query）、$K$（Key）、$V$（Value）均由输入序列线性投影得到，$\sqrt{d_k}$ 用于缩放防止点积过大。

#### 3.1.2 Attention 机制在策略学习中的作用

在 RL 场景中，Attention 机制的核心作用是**动态选择与当前决策最相关的历史信息**。

**观测历史建模**：

将历史观测序列 $\mathbf{o}_{1:t} = (o_1, o_2, ..., o_t)$ 编码为 token 序列，通过多层注意力模块让网络自动学习哪些历史帧对当前决策最重要：

```python
# 伪代码：观测历史注意力
class HistoryAttention(nn.Module):
    """
    历史注意力层：为每个历史时刻分配注意力权重
    当前决策 query: 当前状态编码
    历史 key/value: 历史状态编码
    """
    def __init__(self, embed_dim, num_heads=4):
        self.attention = nn.MultiheadAttention(embed_dim, num_heads)
        self.norm = nn.LayerNorm(embed_dim)
    
    def forward(self, current_state, history_states):
        """
        Args:
            current_state: 当前状态 (embed_dim,) 或 (1, embed_dim)
            history_states: 历史状态序列 (seq_len, embed_dim)
        Returns:
            注意力加权后的历史特征 (embed_dim,)
        """
        # 当前状态作为 query，历史状态作为 key/value
        attn_out, attn_weights = self.attention(
            query=current_state.unsqueeze(0),  # (1, embed_dim)
            key=history_states,                 # (seq_len, embed_dim)
            value=history_states
        )
        return attn_out.squeeze(0), attn_weights  # 第二个返回值可解释注意力分布
```

**注意力权重的实际意义**：

在机器人操作任务中，训练完成后的注意力权重往往显示出有意义的模式：
- 物体被遮挡时，网络对遮挡前的最后一帧赋予高注意力
- 接触任务中，网络对接触瞬间及其后的触觉序列赋予高注意力
- 多阶段任务中，网络对当前阶段开始帧赋予高注意力

这使得 Transformer 策略网络相比 MLP 具有更好的**可解释性**。

#### 3.1.3 观测历史建模框架

将观测历史建模为序列输入 Transformer，需要解决三个核心问题：

**1. Token 化（Tokenization）**：

| 模态 | Token 化方式 | 示例 |
|------|------------|------|
| 图像 | 预训练视觉编码器（ResNet/ViT） | $o_t^{\text{img}} \rightarrow v_t \in \mathbb{R}^d$ |
| 关节角度 | 直接线性投影 | $o_t^{\text{joint}} \in \mathbb{R}^{N_{\text{joint}}}$ |
| 触觉 | 线性投影 + 归一化 | $o_t^{\text{tactile}} \in \mathbb{R}^{N_{\text{sensor}}}$ |
| 动作 | 动作空间嵌入 | $a_t \in \mathbb{R}^{N_{\text{action}}}$ |
| 奖励/回报 | 回报-to-Go 标量嵌入 | $r_t^{\text{rtg}} \in \mathbb{R}^1 \rightarrow e_t \in \mathbb{R}^d$ |

**2. 位置编码（Positional Encoding）**：

Transformer 本身对序列顺序不敏感（Permutation Invariant），需要额外注入位置信息。在 RL 中，位置编码有两种常用方式：
- **绝对位置编码**：类似 NLP，为序列中每个时间步分配固定位置向量
- **相对位置编码**：编码 token 之间的相对时间差，更适合变长轨迹

**3. 序列构建策略**：

```
策略输入序列构建（以 Decision Transformer 为例）：

时间步:    t-K      t-K+1    ...    t-1      t
输入:    [o_t-K,  a_t-K,  R_t-K,  o_t-K+1, a_t-K+1, R_t-K+1, ..., o_t]
          ↓        ↓       ↓        ↓         ↓        ↓              ↓
Token:   E_o     E_a     E_R      E_o      E_a     E_R      E_o(预测目标)

其中 R_t = 回报-to-Go（从当前时刻到轨迹结束的累积折扣回报）
```

---

### 3.2 Decision Transformer

#### 3.2.1 Decision Transformer 核心思想

**Decision Transformer（DT）** 由 Chen 等人于 2021 年在论文《Decision Transformer: Reinforcement Learning via Sequence Modeling》中提出，是将 Transformer 应用于 RL 的里程碑工作。

**核心洞察**：将 RL 问题重新定义为**序列建模**问题——不再通过环境交互最大化累积奖励，而是让 Transformer 根据历史轨迹序列（状态、动作、回报-to-Go）**自回归地预测下一步最优动作**。

**传统 RL vs DT 的对比**：

| 维度 | 传统 RL（PPO/DQN/SAC） | Decision Transformer |
|------|----------------------|---------------------|
| **建模方式** | 交互式策略优化 | 序列到序列的监督学习 |
| **优化目标** | $\max_\pi \mathbb{E}[\sum_t r_t]$ | $\max_\theta \sum_t \log \pi_\theta(a_t | \tau_{1:t})$ |
| **训练方式** | 环境交互 + 梯度更新 | 监督学习（MSE/CE 损失） |
| **序列依赖** | 仅当前状态 $s_t$ | 完整历史 $\tau_{1:t}$ |
| **探索机制** | ε-greedy、熵正则化等 | 无需显式探索（离线数据驱动） |
| **长程信用分配** | 通过 TD 误差逐层传播 | Attention 全局建模一步到位 |
| **离线数据利用** | DQN 经验回放（简单） | 整个轨迹序列联合建模 |

DT 最大的创新在于**彻底放弃在线交互**，完全依赖离线数据集（专家轨迹）进行监督学习，这使得它天然适合模仿学习场景。

#### 3.2.2 回报-to-Go（Rtg）机制

DT 引入了一个关键设计：**回报-to-Go**（Return-to-Go，记作 $R_t$），定义为从当前时刻 $t$ 到轨迹结束 $T$ 的累积折扣回报：

$$
R_t = \sum_{t'=t}^{T} \gamma^{t'-t} r_{t'}
$$

其中 $\gamma \in [0, 1]$ 为折扣因子。

**为什么需要 Rtg？**

在序列建模中，Transformer 需要知道"当前决策的目标是什么"。$R_t$ 本质上是给 Transformer 一个"未来预期的价值信号"——类似于给语言模型一个"写作主题提示"。Transformer 根据 $R_t$ 的大小决定当前应该采取激进还是保守的动作：

- **高 $R_t$（预期未来奖励高）**：继续保持当前策略，可能采取 ambitious 动作
- **低 $R_t$（预期未来奖励低）**：需要修正策略，采取 corrective 动作

```python
# Rtg 计算示例
def compute_rtg(rewards, gamma=0.997, device='cpu'):
    """
    从奖励序列计算回报-to-Go（Return-to-Go）
    R_t = r_t + gamma * R_{t+1}
    
    Args:
        rewards: 奖励序列 (trajectory_length,)
        gamma: 折扣因子
    Returns:
        rtg: 回报-to-Go 序列 (trajectory_length,)
    """
    rtg = []
    discounted_sum = 0.0
    # 从后向前累计（符合 R_t 定义）
    for r in reversed(rewards):
        discounted_sum = r + gamma * discounted_sum
        rtg.insert(0, discounted_sum)  # 头部插入，保持时间顺序
    return torch.tensor(rtg, dtype=torch.float32, device=device)

# 示例
rewards = [1.0, 1.0, 1.0, 0.0, 0.0]
gamma = 0.9
# R_5 = 0.0
# R_4 = 0.0 + 0.9*0.0 = 0.0
# R_3 = 0.0 + 0.9*0.0 = 0.0
# R_2 = 1.0 + 0.9*0.0 = 1.0
# R_1 = 1.0 + 0.9*1.0 = 1.9
# R_0 = 1.0 + 0.9*1.9 = 2.71
rtg = compute_rtg(rewards, gamma)
# rtg = [2.71, 1.9, 1.0, 0.0, 0.0]
```

**Rtg 在序列中的使用方式**：

DT 的输入序列按照 $[R_t, o_t, a_t, R_{t-1}, o_{t-1}, a_{t-1}, ...]$ 的顺序排列（从后往前），预测目标是对应的 $a_t$。这种排列方式使得在推理时，Transformer 可以从 $R_t^{\text{target}}$ 开始，自回归地预测一系列动作。

#### 3.2.3 Decision Transformer 架构

DT 的网络架构遵循标准的 GPT-style 因果 Transformer：

```
输入序列:  [R_t, o_t, a_t, R_{t-1}, o_{t-1}, a_{t-1}, ..., R_{t-K}, o_{t-K}, a_{t-K}]
             ↓      ↓    ↓      ↓        ↓        ↓              ↓        ↓        ↓
嵌入层:   E_R    E_o   E_a   E_R      E_o      E_a          E_R      E_o      E_a
             ↓      ↓    ↓      ↓        ↓        ↓              ↓        ↓        ↓
           + Pos Enc → 逐元素相加
             ↓
        多层因果 Transformer Block（Self-Attention + FFN）
             ↓
         线性预测头 → 输出 P(a_t | R_t, o_t, 历史)
```

**关键设计点**：

1. **三个独立的嵌入层**：$E_R, E_o, E_a$ 分别处理回报、观测、动作，参数不共享
2. **因果掩码（Causal Mask）**：确保 $a_t$ 只能 attend 到 $t$ 及之前的位置，防止信息泄漏
3. **线性动作预测头**：最后一层直接输出每个动作维度的均值（高斯策略）或分类 logits（离散动作）

```python
class DecisionTransformer(nn.Module):
    """
    Decision Transformer 简化实现
    输入：回报-to-Go、观测序列、动作序列的 token 序列
    输出：下一步动作的预测分布
    """
    def __init__(
        self,
        state_dim,        # 观测维度
        action_dim,       # 动作维度（连续动作取标量维度）
        hidden_dim=128,    # 嵌入维度
        max_length=30,    # 最大历史长度（K）
        num_layers=3,     # Transformer 层数
        num_heads=4,      # 注意力头数
        dropout=0.1
    ):
        super().__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.max_length = max_length
        
        # 三个独立嵌入层
        self.state_embed = nn.Linear(state_dim, hidden_dim)
        self.action_embed = nn.Linear(action_dim, hidden_dim)
        self.rtg_embed = nn.Linear(1, hidden_dim)  # Rtg 是标量 → 嵌入
        
        # 预测头（动作维度，用于预测 a_t）
        self.action_pred = nn.Linear(hidden_dim, action_dim)
        
        # 因果掩码的注意力层
        self.transformer = TransformerEncoder(
            TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=num_heads,
                dim_feedforward=hidden_dim * 4,
                dropout=dropout,
                activation='gelu',
                batch_first=True
            ),
            num_layers=num_layers
        )
        
        # 可学习的起始 token（用于无观测时的占位）
        self.start_token = nn.Parameter(torch.randn(1, 1, hidden_dim))
        
        # 位置编码（可学习参数）
        self.pos_embed = nn.Parameter(torch.randn(1, max_length * 3 + 1, hidden_dim))
    
    def forward(self, states, actions, rtgs, padding_mask=None):
        """
        前向传播（训练阶段）
        Args:
            states: 观测序列 (batch_size, seq_len, state_dim)
            actions: 动作序列 (batch_size, seq_len, action_dim)
            rtgs: 回报-to-Go 序列 (batch_size, seq_len, 1)
            padding_mask: 填充掩码 (batch_size, seq_len)，True=填充位置
        Returns:
            action_pred: 预测动作 logits/mu (batch_size, seq_len, action_dim)
        """
        batch_size, seq_len = states.shape[0], states.shape[1]
        
        # Token 嵌入
        state_emb = self.state_embed(states)                  # (B, L, H)
        action_emb = self.action_embed(actions)               # (B, L, H)
        rtg_emb = self.rtg_embed(rtgs)                        # (B, L, H)
        
        # 交替拼接：[R_t, o_t, a_t, R_{t-1}, ...]
        # 序列顺序：rtg, state, action, rtg, state, action, ...
        tokens = torch.zeros(batch_size, seq_len * 3, self.hidden_dim, 
                             device=states.device)
        tokens[:, 0::3, :] = rtg_emb    # 偶数位置：rtg
        tokens[:, 1::3, :] = state_emb  # 奇数位置：state
        tokens[:, 2::3, :] = action_emb
        
        # 添加起始 token（在序列最前面）
        start = self.start_token.expand(batch_size, -1, -1)  # (B, 1, H)
        tokens = torch.cat([start, tokens], dim=1)          # (B, L*3+1, H)
        
        # 添加位置编码
        tokens = tokens + self.pos_embed[:, :tokens.shape[1], :]
        
        # 因果掩码：每个位置只能 attend 到当前位置及之前
        seq_len_full = tokens.shape[1]
        causal_mask = torch.triu(
            torch.ones(seq_len_full, seq_len_full, device=tokens.device),
            diagonal=1
        ).bool()  # 上三角为 True（禁止 attend）
        
        # 通过 Transformer
        output = self.transformer(
            tokens,
            mask=causal_mask,
            src_key_padding_mask=padding_mask
        )  # (B, L*3+1, H)
        
        # 仅取出动作位置的预测（每隔3个位置，最后一个 action 位置）
        # start(0) + [rtg(0), state(0), action(0), rtg(1), ..., action(L-1)]
        # action 位置索引：3, 6, 9, ..., 3*L
        action_indices = list(range(3, 3 * seq_len + 1, 3))
        action_hidden = output[:, action_indices, :]  # (B, L, H)
        
        # 动作预测
        action_pred = self.action_pred(action_hidden)  # (B, L, action_dim)
        return action_pred
    
    def get_action(self, states, actions, rtgs):
        """
        推理阶段：获取单步动作预测
        仅预测最后一个时间步的动作
        """
        self.eval()
        with torch.no_grad():
            preds = self.forward(states, actions, rtgs)
            return preds[:, -1, :]  # (B, action_dim)
```

#### 3.2.4 DT vs 传统 RL 的核心差异

| 特性 | DQN / PPO（在线RL） | Decision Transformer（离线序列建模） |
|------|-------------------|-----------------------------------|
| **数据来源** | 在线环境交互 | 离线数据集（无需环境） |
| **优化目标** | 累积奖励期望最大化 | 轨迹序列的似然最大化 |
| **决策方式** | 单步策略 $\pi(a_t | s_t)$ | 序列条件预测 $\pi(a_t | R_t, \tau_{<t})$ |
| **信用分配** | TD 误差，传播慢 | Attention 全局建模一步到位 |
| **探索需求** | 必须探索（ε-greedy 等） | 无需探索（纯监督学习） |
| **训练稳定性** | 涉及价值函数估计、策略更新权衡 | 稳定（标准监督学习） |
| **长程依赖** | 需多层 TD 传播，容易梯度消失/爆炸 | Attention 全局建模，理论上无距离限制 |
| **样本效率** | 低（需大量环境交互） | 高（离线数据直接学习） |
| **泛化方式** | 隐式泛化（价值函数） | 显式条件（通过 Rtg 指定目标） |

**DT 的局限性**：

1. **自回归误差累积**：推理时预测的动作会影响下一步的观测，长序列仍有误差累积风险
2. **Rtg 条件敏感**：Rtg 的准确性直接影响策略表现，噪声 Rtg 会导致次优策略
3. **计算成本**：Transformer 的 $O(L^2)$ 复杂度在长轨迹上计算量大

---

### 3.3 Trajectory Transformer

#### 3.3.1 轨迹联合建模

**Trajectory Transformer（TT）** 由 Janner 等人于 2021 年在论文《Trajectory Transformer: Sequence Modeling for Robot Control》中提出，是 DT 的重要扩展。

**核心差异**：TT 不仅仅预测动作，而是将**整个轨迹（状态、动作、奖励）联合建模为自回归序列**，在推理时通过 **Beam Search** 解码出完整的轨迹 plan，再执行开环控制。

| 特性 | Decision Transformer | Trajectory Transformer |
|------|---------------------|----------------------|
| **预测目标** | 动作 $a_t$ | 状态 $s_{t+1}$、动作 $a_t$、奖励 $r_t$ |
| **决策方式** | 单步在线决策（每步预测 $a_t$） | 开环轨迹规划（一次解码完整轨迹） |
| **解码策略** | 自回归贪婪解码 | Beam Search |
| **输出结构** | $a_t$ | 完整的 $\tau = (s_0, a_0, r_0, s_1, a_1, r_1, ...)$ |

**TT 的序列建模方式**：

```
TT 输入/输出序列：
[s_0, a_0, r_0, s_1, a_1, r_1, ..., s_{T-1}, a_{T-1}, r_{T-1}, s_T]
  ↓       ↓     ↓     ↓       ↓     ↓              ↓
自回归预测：每步同时预测 (s_{t+1}, a_t, r_t)
```

TT 的目标函数是最大化整个轨迹的似然：
$$
\mathcal{L} = \sum_{t=0}^{T-1} \log p_\theta(s_{t+1}, a_t, r_t | s_{\leq t}, a_{<t}, r_{<t})
$$

**Beam Search 解码**：

推理时，TT 不执行单步决策，而是用 Beam Search 从分布 $p(s_{t+1}, a_t, r_t | \cdot)$ 中采样 $K$ 条候选轨迹，选取累积奖励最高的轨迹执行：

```python
def beam_search_trajectory(model, initial_state, beam_width=4, horizon=50):
    """
    Beam Search 解码：从 Trajectory Transformer 采样最优轨迹
    
    Args:
        model: Trajectory Transformer
        initial_state: 起始状态 s_0
        beam_width: Beam 宽度（候选轨迹数）
        horizon: 规划步数
    Returns:
        best_trajectory: 最优轨迹列表 [(s, a, r), ...]
    """
    beams = [{'states': [initial_state], 'actions': [], 'rewards': [], 'score': 0.0}]
    
    for step in range(horizon):
        all_candidates = []
        for beam in beams:
            # 准备解码输入
            seq_input = prepare_sequence(beam)  # 将已有轨迹转为 token 序列
            
            # 自回归解码一步
            with torch.no_grad():
                pred_dist = model(seq_input)  # 预测下一步 (s, a, r) 的分布
            
            # 从分布采样 top-k
            topk_actions = torch.topk(pred_dist['action'], beam_width, dim=-1)
            topk_rewards = torch.topk(pred_dist['reward'], beam_width, dim=-1)
            topk_next_states = torch.topk(pred_dist['next_state'], beam_width, dim=-1)
            
            for i in range(beam_width):
                candidate = {
                    'states': beam['states'] + [topk_next_states.indices[i]],
                    'actions': beam['actions'] + [topk_actions.indices[i]],
                    'rewards': beam['rewards'] + [topk_rewards.indices[i]],
                    'score': beam['score'] + topk_rewards.values[i].item()
                }
                all_candidates.append(candidate)
        
        # 选择 top beam_width 个候选
        beams = sorted(all_candidates, key=lambda x: x['score'], reverse=True)[:beam_width]
    
    # 返回最优轨迹
    return beams[0]
```

#### 3.3.2 长程任务中的优势

TT 在长程任务中相比 DT 具有以下优势：

1. **开环规划减少误差累积**：TT 一次规划完整轨迹，避免了 DT 逐步预测中误差逐步放大的问题
2. **全局优化**：Beam Search 可以考虑动作序列的全局效果（如"先抬起再平移最后放下"的完整抓取序列）
3. **奖励信号利用**：TT 联合建模奖励，解码时可以直接以累积奖励排序候选轨迹

---

### 3.4 ACT（Action Chunking Transformer）

#### 3.4.1 动作分块机制

**ACT（Action Chunking Transformer）** 由 Zhao 等人于 2023 年提出，是斯坦福 ALOHA 项目中的核心技术之一。ACT 的核心设计是**动作分块（Action Chunking）**——一次预测多个未来时刻的动作，而不是一次只预测一个动作。

**动机**：机器人的控制频率通常很高（100Hz 以上），而 Transformer 的推理速度相对较慢。如果每个控制周期都调用 Transformer，会导致控制频率严重不足。

**解决方案**：Transformer 每次输出 $T_{\text{chunk}}$ 个连续动作（一个 chunk），控制频率提升 $T_{\text{chunk}}$ 倍：

$$
a_t^{\text{chunk}} = (a_t, a_{t+1}, a_{t+2}, ..., a_{t+T_{\text{chunk}}-1})
$$

#### 3.4.2 时序一致性

ACT 的时序一致性设计确保了动作分块的质量：

**1. 平滑过渡（Temporal Smoothing）**：

当执行动作块时，相邻块之间可能存在动作突变（如 $a_{t+T_{\text{chunk}}-1}$ 与 $a_{t+T_{\text{chunk}}}$ 差距过大）。ACT 通过**指数移动平均（EMA）**或**余弦混合**实现平滑过渡：

```python
def apply_temporal_smoothing(chunk_current, chunk_previous, alpha=0.5):
    """
    相邻动作块的平滑过渡
    Args:
        chunk_current: 当前预测的动作块 (chunk_size, action_dim)
        chunk_previous: 上一时刻已执行的部分动作 (执行长度, action_dim)
        alpha: 平滑系数（越大越依赖历史）
    Returns:
        smoothed_chunk: 平滑后的动作块
    """
    executed_len = chunk_previous.shape[0]
    # 前 executed_len 个动作做平滑，后面的直接用
    smoothed = chunk_current.clone()
    if executed_len > 0:
        smoothed[:executed_len] = (
            alpha * chunk_previous + (1 - alpha) * chunk_current[:executed_len]
        )
    return smoothed
```

**2. 条件动作预测**：

ACT 的动作预测以当前观测和上一时刻执行的动作（而非预测的动作）为条件，确保实际执行的动作序列与预测一致：

$$
a_{t:t+T_{\text{chunk}}}^{\text{chunk}} = f_\theta(o_t, a_{t-1}^{\text{actual}})
$$

这保证了"执行闭环"——机器人实际做的动作才是下一步的条件，而非预测的动作（避免误差累积）。

#### 3.4.3 斯坦福 ALOHA 项目

**ALOHA**（Active Learning with Observation Anthropomorphic）是斯坦福大学双臂机器人操作研究项目，其核心成果包括：

| 成果 | 描述 |
|------|------|
| **ALOHA 硬件** | 低成本双臂机器人（2x WidowX + 夹爪），总成本约 2 万美元 |
| **ACT 算法** | Action Chunking Transformer，实现 50Hz 双臂控制 |
| **Mobile ALOHA** | 移动版 ALOHA，结合轮式基座，实现长程任务 |
| **UR3e 集成** | 工业机械臂版本的 ALOHA |

**ALOHA 的模仿学习 pipeline**：

```
数据收集（人类遥操作）:
    人类操作员 → 远程控制 ALOHA 双臂 → 记录 (o_t, a_t) 轨迹对
                          ↓
ACT 训练:
    (o_t, a_t) 序列 → Transformer → 预测动作块 a_{t:t+K}^{chunk}
                          ↓
推理执行（50Hz 闭环控制）:
    当前观测 o_t → ACT 推理 → 动作块预测 → 平滑执行
                          ↓
    实际执行 a_t → 作为下一时刻条件输入 → 继续推理
```

---

### 3.5 其他 Transformer IL 方法

#### 3.5.1 GATO（多任务 Agent）

**GATO**（Generalist Agent）由 DeepMind 于 2022 年提出，是一个**多任务多模态大模型**，可以在单一模型中处理文本、图像、机器人控制等多种任务。

**核心设计**：

| 组件 | 设计 |
|------|------|
| **Token 化** | 离散 token（文本/操作）用 GPT-2 tokenizer；连续值（图像/动作）用线性投影或离散化 |
| **序列拼接** | 不同任务的所有模态拼接到统一序列 |
| **Transformer** | 1.2B 参数 causal Transformer（类似 GPT） |
| **输出头** | 文本头（语言建模）、动作头（离散动作分类/连续回归） |
| **训练数据** | 来自不同任务的离线数据集（模拟器 + 真实机器人） |

**GATO 在 IL 中的意义**：GATO 证明了**多任务统一建模**的可行性——同一个 Transformer 可以同时学会雅达利游戏、图像描述、机器人操作，无需为每个任务设计专门的策略网络。

#### 3.5.2 RT-1 / RT-2

**RT-1**（Robot Transformer 1）和 **RT-2**（Robot Transformer 2）是 Google Robotics 的视觉-语言-动作（VLA）模型：

| 特性 | RT-1 | RT-2 |
|------|------|------|
| **架构** | FiLM-conditioned ResNet + TokenLearner + Transformer | RT-1 基础上 + 视觉-语言预训练（PaLM-E/ViT） |
| **动作空间** | 连续动作（末端执行器位置/旋转/夹爪） | 连续动作 + 离散动作 token |
| **训练数据** | 13 万条真实机器人演示 | RT-1 数据 + 互联网视觉-语言数据 |
| **泛化能力** | 简单场景泛化 | 显著提升泛化（继承视觉-语言预训练） |
| **核心创新** | 多任务模仿学习 baseline | 将 VLM 知识迁移到机器人控制 |

**RT-2 的核心洞察**：将机器人动作**离散化为 token**，与文本 token 一起用语言模型的 next-token prediction 方式预测——这使得 RT-2 可以利用互联网规模的视觉-语言预训练知识，直接泛化到未见过的物体和指令。

#### 3.5.3 开源实现

| 项目 | 框架 | 链接 | 主要内容 |
|------|------|------|---------|
| **decision-transformer** | PyTorch | `nicklashenyang/decision-transformer` | DT 原版简化实现，支持 Gymnasium |
| **TrajectoryTransformer** | PyTorch | `jannerm/trajectory-transformer` | TT 官方实现（牛津） |
| **ACT** | PyTorch | `StanfordALOHA/aloha` | ALOHA/ACT 官方实现 |
| **GATO** | PyTorch | `notmahi/gato` | 非官方 GATO 简化复现 |
| **RoboCat** | JAX | DeepMind 官方 | GATO 的机器人版本 |
| **RT-1/RT-2** | TF/TF-Agents | `google-research/robotics_transformer` | RT-1/2 官方实现 |

---

## 四、代码实战：Decision Transformer 简化实现

### 4.1 完整 PyTorch 实现

本节实现一个简化版 Decision Transformer，支持连续动作空间的 MuJoCo 环境（以 HalfCheetah-v4 为例）。

```python
"""
Decision Transformer 简化实现
课程：15-3 Transformer模仿学习
说明：基于 "Decision Transformer: Reinforcement Learning via Sequence Modeling"
     (Chen et al., 2021)

网络结构：
  输入: [R_t, o_t, a_t, R_{t-1}, o_{t-1}, a_{t-1}, ...]
  → 嵌入 → 因果 Transformer → 动作预测

训练损失: MSE(预测动作, 专家动作)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import TransformerEncoder, TransformerEncoderLayer
import numpy as np
from typing import List, Tuple, Optional


# ============================================================
# 1. 回报-to-Go（RTG）计算
# ============================================================

def compute_rtg(rewards: torch.Tensor, gamma: float = 0.997) -> torch.Tensor:
    """
    从奖励序列计算回报-to-Go
    R_t = r_t + gamma * R_{t+1}
    （从后向前累加，符合定义）
    
    Args:
        rewards: 奖励序列 (batch_size, trajectory_len)
        gamma: 折扣因子
    Returns:
        rtg: 回报-to-Go 序列 (batch_size, trajectory_len)，已标准化
    """
    trajectory_len = rewards.shape[1]
    rtg = torch.zeros_like(rewards)
    discounted_sum = torch.zeros(rewards.shape[0], device=rewards.device)
    
    # 从后向前遍历（T-1, T-2, ..., 0）
    for t in reversed(range(trajectory_len)):
        discounted_sum = rewards[:, t] + gamma * discounted_sum
        rtg[:, t] = discounted_sum
    
    # 标准化：减去均值除以标准差（有助于 Transformer 训练稳定）
    rtg = (rtg - rtg.mean(dim=1, keepdim=True)) / (rtg.std(dim=1, keepdim=True) + 1e-8)
    return rtg


# ============================================================
# 2. Decision Transformer 网络
# ============================================================

class DecisionTransformer(nn.Module):
    """
    Decision Transformer：基于 Transformer 的离线强化学习
    
    核心思想：将 RL 问题建模为序列建模问题
    - 输入：历史回报-to-Go、观测、动作 token 序列
    - 输出：下一步动作预测
    
    与传统 RL 的根本区别：
    1. 纯监督学习，无需环境交互（离线数据驱动）
    2. 使用因果 Transformer 建模长程历史依赖
    3. 通过条件化 Rtg 实现目标导向决策
    """
    
    def __init__(
        self,
        state_dim: int,             # 观测空间维度
        action_dim: int,             # 动作空间维度（连续动作为标量数量）
        hidden_dim: int = 128,       # 嵌入维度
        max_length: int = 30,        # 最大历史长度（K）
        num_layers: int = 3,         # Transformer 层数
        num_heads: int = 4,          # 注意力头数
        dropout: float = 0.1,
        action_scale: float = 1.0    # 动作
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim
        self.max_length = max_length
        self.action_scale = action_scale
        
        # -------- 嵌入层 --------
        # 观测嵌入：线性层（也可以替换为预训练视觉编码器）
        self.state_embed = nn.Linear(state_dim, hidden_dim)
        # 动作嵌入：与观测使用不同的嵌入层
        self.action_embed = nn.Linear(action_dim, hidden_dim)
        # Rtg 嵌入：标量 → 隐藏维度向量
        self.rtg_embed = nn.Linear(1, hidden_dim)
        
        # -------- Transformer 主体 --------
        # 因果注意力：每个位置只能 attend 到当前及之前的位置
        encoder_layer = TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=num_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            activation='gelu',
            batch_first=True,  # (batch, seq, dim) 格式
            norm_first=True    # Pre-LayerNorm（更稳定的训练）
        )
        self.transformer = TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # -------- 预测头 --------
        # 动作预测：输出每个动作维度的均值
        self.action_pred = nn.Linear(hidden_dim, action_dim)
        
        # -------- 可学习特殊 Token --------
        # 起始 token：在序列最前面，作为"等待填充"的位置
        self.start_token = nn.Parameter(torch.randn(1, 1, hidden_dim))
        
        # 可学习的位置编码（比固定 sin/cos 更灵活）
        self.pos_embed = nn.Parameter(
            torch.randn(1, (max_length + 1) * 3, hidden_dim)  # +1 for start token
        )
    
    def forward(
        self,
        states: torch.Tensor,      # (batch_size, seq_len, state_dim)
        actions: torch.Tensor,     # (batch_size, seq_len, action_dim)
        rtgs: torch.Tensor,         # (batch_size, seq_len, 1)
        padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        前向传播（训练阶段）
        
        Args:
            states: 观测序列，最后一个时间步是要预测动作的时间点
            actions: 动作序列（训练时为真实动作）
            rtgs: 回报-to-Go 序列（标准化后）
            padding_mask: 填充掩码，True = 填充位置（PyTorch 中这些位置不参与注意力计算）
        Returns:
            action_preds: 预测动作 (batch_size, seq_len, action_dim)
                          每个时间步对应输入序列中该时间步的动作预测
        """
        batch_size, seq_len = states.shape[0], states.shape[1]
        
        # ---- Token 嵌入 ----
        # 每个模态独立的嵌入层
        state_emb = self.state_embed(states)                  # (B, L, H)
        action_emb = self.action_embed(actions)              # (B, L, H)
        rtg_emb = self.rtg_embed(rtgs)                        # (B, L, H)
        
        # ---- 构建交替序列 ----
        # 序列顺序：[R_t, o_t, a_t, R_{t-1}, o_{t-1}, a_{t-1}, ...]
        # 即 [rtg, state, action] 三元组从后向前排列
        seq_len_total = seq_len * 3 + 1  # +1 for start token
        tokens = torch.zeros(
            batch_size, seq_len_total, self.hidden_dim,
            device=states.device, dtype=states.dtype
        )
        # R_t 位置索引：0, 3, 6, ...（0 is start token）
        tokens[:, 0::3, :] = rtg_emb     # 0,3,6,... → R_t
        tokens[:, 1::3, :] = state_emb   # 1,4,7,... → o_t
        tokens[:, 2::3, :] = action_emb  # 2,5,8,... → a_t
        
        # ---- 添加位置编码 ----
        # 截取实际序列长度对应的位置编码
        tokens = tokens + self.pos_embed[:, :seq_len_total, :]
        
        # ---- 因果掩码（重要！）----
        # 确保位置 i 只能 attend 到位置 ≤ i
        # torch.triu(..., diagonal=1) 生成上三角（不含对角线）
        causal_mask = torch.triu(
            torch.ones(seq_len_total, seq_len_total, device=tokens.device),
            diagonal=1
        ).bool()  # True = 阻止 attend
        
        # ---- Transformer 前向传播 ----
        output = self.transformer(
            tokens,
            mask=causal_mask,           # 强制因果注意
            src_key_padding_mask=padding_mask
        )  # (B, seq_len_total, H)
        
        # ---- 提取动作预测 ----
        # action 位置：2, 5, 8, ...（相对于 start=0）
        action_indices = list(range(2, seq_len * 3, 3))
        action_hidden = output[:, action_indices, :]  # (B, seq_len, H)
        
        # 动作预测输出
        action_preds = self.action_pred(action_hidden) * self.action_scale
        return action_preds
    
    def get_action(
        self,
        states: torch.Tensor,      # (batch_size, seq_len, state_dim)
        actions: torch.Tensor,       # (batch_size, seq_len, action_dim)
        rtgs: torch.Tensor            # (batch_size, seq_len, 1)
    ) -> torch.Tensor:
        """
        推理阶段：获取单步动作预测（仅预测最后一个时间步）
        
        Args:
            states: 当前历史观测序列 (B, K, state_dim)
            actions: 当前历史动作序列 (B, K, action_dim)
            rtgs: 当前历史 Rtg 序列 (B, K, 1)
        Returns:
            action: 预测动作 (B, action_dim)
        """
        self.eval()
        with torch.no_grad():
            preds = self.forward(states, actions, rtgs)
            # 返回序列中最后一个时间步的预测（即 t 时刻要执行的动作）
            return preds[:, -1, :]


# ============================================================
# 3. 训练循环
# ============================================================

def load_demonstrations(env_name: str = "HalfCheetah-v4", num_trajectories: int = 50):
    """
    加载专家演示数据（模拟的离线数据集）
    实际项目中应从文件或数据库加载真实人类演示
    
    这里用随机策略 + Gymnasium 环境生成模拟演示数据
    真实场景请使用 rlds tensorroute 或 d4rl 库加载真实离线数据
    """
    try:
        import gymnasium as gym
    except ImportError:
        import gym
    
    env = gym.make(env_name)
    
    trajectories = []
    for _ in range(num_trajectories):
        obs_list, action_list, reward_list = [], [], []
        obs, info = env.reset()
        done = False
        truncated = False
        total_reward = 0.0
        
        while not (done or truncated):
            action, = env.action_space.sample()  # 随机策略（真实场景替换为专家策略）
            
            obs_list.append(obs)
            action_list.append(action)
            
            obs, reward, done, truncated, info = env.step(action)
            reward_list.append(reward)
            total_reward += reward
        
        trajectories.append({
            'observations': np.array(obs_list),
            'actions': np.array(action_list),
            'rewards': np.array(reward_list),
            'total_reward': total_reward
        })
        
        print(f"  轨迹 {_}: 总奖励 = {total_reward:.2f}, 步数 = {len(reward_list)}")
    
    env.close()
    return trajectories


def prepare_batch(
    trajectories: List[dict],
    seq_len: int = 30,
    batch_size: int = 16,
    device: str = 'cpu'
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    从轨迹数据中随机采样批次用于训练
    
    Args:
        trajectories: 轨迹列表
        seq_len: 序列长度（每个样本的时间步数）
        batch_size: 批次大小
        device: 计算设备
    Returns:
        states, actions, rtgs, target_actions (均为 torch.Tensor)
    """
    states_all, actions_all, rtgs_all, targets_all = [], [], [], []
    
    for _ in range(batch_size):
        # 随机选择一个轨迹
        traj = trajectories[np.random.randint(len(trajectories))]
        obs = traj['observations']
        act = traj['actions']
        rew = traj['rewards']
        
        traj_len = len(obs)
        if traj_len < seq_len + 1:
            # 轨迹太短，跳过或填充
            continue
        
        # 随机选择起始位置
        start_idx = np.random.randint(0, traj_len - seq_len)
        end_idx = start_idx + seq_len
        
        # 切片
        obs_seq = obs[start_idx:end_idx]
        act_seq = act[start_idx:end_idx]
        rew_seq = rew[start_idx:end_idx]
        
        # 目标动作：整个序列的下一个动作（a_{t+1}）
        # 这是 DT 的训练目标——预测下一个动作
        target_act_seq = act[start_idx + 1:end_idx + 1]
        
        # 计算 Rtg（从当前时刻到轨迹结束的折扣回报）
        rew_tensor = torch.tensor(rew_seq, dtype=torch.float32).unsqueeze(0)
        rtg_seq = compute_rtg(rew_tensor).squeeze(0)  # (seq_len,)
        rtg_seq = rtg_seq.unsqueeze(-1)  # (seq_len, 1)
        
        states_all.append(obs_seq)
        actions_all.append(act_seq)
        rtgs_all.append(rtg_seq.numpy())
        targets_all.append(target_act_seq)
    
    # 转为 Tensor
    states = torch.tensor(np.array(states_all), dtype=torch.float32, device=device)
    actions = torch.tensor(np.array(actions_all), dtype=torch.float32, device=device)
    rtgs = torch.tensor(np.array(rtgs_all), dtype=torch.float32, device=device)
    target_actions = torch.tensor(np.array(targets_all), dtype=torch.float32, device=device)
    
    return states, actions, rtgs, target_actions


def train_decision_transformer(
    env_name: str = "HalfCheetah-v4",
    num_trajectories: int = 50,
    num_epochs: int = 50,
    batch_size: int = 16,
    seq_len: int = 30,
    lr: float = 1e-3,
    device: str = 'cpu',
    save_path: str = "decision_transformer.pt"
):
    """
    Decision Transformer 完整训练流程
    
    步骤：
    1. 加载/生成离线演示数据
    2. 创建模型和优化器
    3. 训练循环（监督学习）
    4. 保存模型
    """
    print(f"\n{'='*60}")
    print(f"Decision Transformer 训练")
    print(f"{'='*60}")
    print(f"环境: {env_name}")
    print(f"轨迹数: {num_trajectories}, 序列长度: {seq_len}, 批次: {batch_size}")
    print(f"{'='*60}\n")
    
    # ---- 1. 加载离线数据 ----
    print("📂 加载专家演示数据...")
    trajectories = load_demonstrations(env_name, num_trajectories)
    print(f"  加载完成，共 {len(trajectories)} 条轨迹\n")
    
    # ---- 2. 创建模型 ----
    # 获取环境维度和动作维度
    import gymnasium as gym
    temp_env = gym.make(env_name)
    state_dim = temp_env.observation_space.shape[0]
    action_dim = temp_env.action_space.shape[0]
    action_scale = float(temp_env.action_space.high[0])  # 用于缩放输出动作
    temp_env.close()
    
    print(f"状态维度: {state_dim}, 动作维度: {action_dim}, 动作范围: [-{action_scale}, {action_scale}]")
    
    model = DecisionTransformer(
        state_dim=state_dim,
        action_dim=action_dim,
        hidden_dim=128,
        max_length=seq_len,
        num_layers=3,
        num_heads=4,
        dropout=0.1,
        action_scale=action_scale
    ).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
    
    print(f"模型参数量: {sum(p.numel() for p in model.parameters()):,}")
    print(f"可训练参数: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}\n")
    
    # ---- 3. 训练循环 ----
    print("🚀 开始训练...")
    for epoch in range(num_epochs):
        # 准备批次数据
        states, actions, rtgs, target_actions = prepare_batch(
            trajectories, seq_len, batch_size, device
        )
        
        # 前向传播
        action_preds = model(states, actions, rtgs)  # (B, L, action_dim)
        
        # 计算 MSE 损失（预测动作 vs 目标动作）
        loss = F.mse_loss(action_preds, target_actions)
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        # 梯度裁剪，防止 Transformer 梯度爆炸
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        
        scheduler.step()
        
        # 日志输出
        if (epoch + 1) % 10 == 0 or epoch == 0:
            avg_reward = np.mean([t['total_reward'] for t in trajectories])
            print(
                f"  Epoch {epoch+1:3d}/{num_epochs} | "
                f"Loss: {loss.item():.4f} | "
                f"LR: {scheduler.get_last_lr()[0]:.6f} | "
                f"Avg Traj Reward: {avg_reward:.2f}"
            )
    
    # ---- 4. 保存模型 ----
    torch.save({
        'model_state_dict': model.state_dict(),
        'config': {
            'state_dim': state_dim,
            'action_dim': action_dim,
            'hidden_dim': model.hidden_dim,
            'max_length': model.max_length,
            'action_scale': action_scale
        }
    }, save_path)
    print(f"\n✅ 模型已保存至 {save_path}")
    
    return model


def evaluate_model(model, env_name: str = "HalfCheetah-v4", num_episodes: int = 5):
    """
    评估训练好的 Decision Transformer 策略
    """
    import gymnasium as gym
    
    device = next(model.parameters()).device
    model.eval()
    
    env = gym.make(env_name)
    eval_rewards = []
    
    print(f"\n🎮 评估 Decision Transformer ({num_episodes} 集)")
    print("-" * 40)
    
    for ep in range(num_episodes):
        obs, info = env.reset()
        done = False
        truncated = False
        total_reward = 0.0
        seq_len = model.max_length
        
        # 初始化历史序列缓冲
        obs_history = []
        act_history = []
        rew_history = []
        
        while not (done or truncated):
            obs_tensor = torch.tensor(obs, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)
            act_tensor = torch.zeros(1, 1, model.action_dim, device=device) if not act_history else \
                          torch.tensor(np.array(act_history[-1:]), dtype=torch.float32).unsqueeze(0).to(device)
            rtg_tensor = torch.zeros(1, 1, 1, device=device) if not rew_history else \
                          compute_rtg(torch.tensor(np.array(rew_history[-1:]), dtype=torch.float32).unsqueeze(0)).unsqueeze(0).to(device)
            
            # 填充历史到 seq_len（用零填充）
            if len(obs_history) < seq_len:
                pad_len = seq_len - len(obs_history)
                obs_pad = np.zeros((pad_len, obs.shape[0]))
                act_pad = np.zeros((pad_len, model.action_dim))
                rew_pad = np.zeros((pad_len,))
                
                obs_seq = np.concatenate([obs_pad, np.array(obs_history)])
                act_seq = np.concatenate([act_pad, np.array(act_history)])
                rew_seq = np.concatenate([rew_pad, np.array(rew_history)])
            else:
                obs_seq = np.array(obs_history[-seq_len:])
                act_seq = np.array(act_history[-seq_len:])
                rew_seq = np.array(rew_history[-seq_len:])
            
            obs_t = torch.tensor(obs_seq, dtype=torch.float32).unsqueeze(0).to(device)
            act_t = torch.tensor(act_seq, dtype=torch.float32).unsqueeze(0).to(device)
            rew_t = compute_rtg(torch.tensor(rew_seq, dtype=torch.float32).unsqueeze(0)).unsqueeze(0).to(device)
            
            # 获取动作
            action = model.get_action(obs_t, act_t, rew_t).cpu().numpy().flatten()
            
            # 执行动作
            obs, reward, done, truncated, info = env.step(action)
            
            obs_history.append(obs)
            act_history.append(action)
            rew_history.append(reward)
            total_reward += reward
        
        eval_rewards.append(total_reward)
        print(f"  Episode {ep+1}: 总奖励 = {total_reward:.2f}")
    
    env.close()
    mean_reward = np.mean(eval_rewards)
    std_reward = np.std(eval_rewards)
    print(f"\n  平均奖励: {mean_reward:.2f} ± {std_reward:.2f}")
    return mean_reward, std_reward


# ============================================================
# 4. 单步 vs 多步决策对比
# ============================================================

def compare_decision_modes():
    """
    对比实验：单步决策（MLP）vs 多步决策（DT）
    
    实验设计：
    - MLP: 用当前状态直接预测动作（传统 BC）
    - DT-K: 用过去 K 步历史预测动作（Decision Transformer）
    """
    print("\n" + "="*60)
    print("单步 vs 多步决策对比实验")
    print("="*60)
    
    import gymnasium as gym
    
    env_name = "HalfCheetah-v4"
    env = gym.make(env_name)
    state_dim = env.observation_space.shape[0]
    action_dim = env.action_space.shape[0]
    env.close()
    
    device = 'cpu'
    seq_len = 30
    
    # MLP 基线（单步决策）
    class MLPPolicy(nn.Module):
        """传统单步策略：pi(a_t | s_t)"""
        def __init__(self, state_dim, action_dim, hidden_dims=[256, 256]):
            super().__init__()
            layers = []
            prev = state_dim
            for h in hidden_dims:
                layers.extend([nn.Linear(prev, h), nn.ReLU()])
                prev = h
            layers.append(nn.Linear(prev, action_dim))
            self.net = nn.Sequential(*layers)
        
        def forward(self, state):
            return self.net(state)  # 输出无约束，需配合 tanh 使用
    
    mlp = MLPPolicy(state_dim, action_dim).to(device)
    dt = DecisionTransformer(state_dim, action_dim, hidden_dim=128, max_length=seq_len).to(device)
    
    print(f"\nMLP 参数量: {sum(p.numel() for p in mlp.parameters()):,}")
    print(f"DT 参数量: {sum(p.numel() for p in dt.parameters()):,}")
    
    print("\n" + "-"*50)
    print("单步 vs 多步决策的关键差异：")
    print("-"*50)
    
    differences = [
        ("输入", "仅当前状态 s_t", "历史序列 [s_{t-K}, a_{t-K}, R_{t-K}, ..., s_t]"),
        ("感受野", "局部（单帧）", "全局（K 步历史）"),
        ("遮挡处理", "无法处理", "通过历史帧推断"),
        ("计算量", "O(1)", "O(K^2) 注意力"),
        ("内存", "小（MLP）", "大（存储 K 步历史）"),
        ("训练", "快速收敛", "需要更长的轨迹数据"),
    ]
    
    print(f"{'维度':<12} {'单步 (MLP)':<25} {'多步 (DT)':<25}")
    print("-"*62)
    for dim, single, multi in differences:
        print(f"{dim:<12} {single:<25} {multi:<25}")
    
    print("\n结论：")
    print("  • 单步决策（MLP）：计算高效，适合完全可观测、马尔可夫的任务")
    print("  • 多步决策（DT）：建模能力强，适合部分可观测、历史敏感的任务")
    print("  • 实际机器人任务往往是后者——视觉遮挡、力反馈序列、姿态跟踪等")
    
    return mlp, dt


# ============================================================
# 5. 主函数入口
# ============================================================

if __name__ == "__main__":
    print("\n" + "🎯"*30)
    print("Decision Transformer 演示")
    print("🎯"*30)
    
    # ① 对比单步 vs 多步决策
    compare_decision_modes()
    
    # ② 完整训练（可选，取消注释运行）
    # print("\n准备训练 Decision Transformer...")
    # train_decision_transformer(
    #     env_name="HalfCheetah-v4",
    #     num_trajectories=30,   # 演示用小数据，正式训练需更多
    #     num_epochs=50,
    #     batch_size=16,
    #     seq_len=20,
    #     lr=3e-4,
    #     device='cuda' if torch.cuda.is_available() else 'cpu',
    #     save_path="decision_transformer_halfcheetah.pt"
    # )
    
    print("\n✅ 演示完成！")
    print("\n📌 关键代码说明：")
    print("  1. compute_rtg(): 计算回报-to-Go，用于条件化 Transformer")
    print("  2. DecisionTransformer: 核心网络，使用因果注意力和三元组序列")
    print("  3. prepare_batch(): 从离线轨迹中采样训练批次")
    print("  4. train_decision_transformer(): 完整训练循环")
    print("  5. compare_decision_modes(): 单步 vs 多步对比实验")

---

## 五、练习题

### 选择题

**1. [单选]** Decision Transformer（DT）与传统强化学习方法（PPO/DQN）的根本区别在于？

A. DT 使用注意力机制，PPO 使用策略梯度  
B. DT 通过监督学习离线训练，PPO 通过环境交互在线优化  
C. DT 只能处理离散动作，PPO 可以处理连续动作  
D. DT 不需要奖励函数，PPO 需要奖励函数引导  

**答案：B  
解析：** DT 的核心创新是**将 RL 问题重新建模为序列建模问题**，完全依赖离线演示数据进行监督学习（预测下一个动作），不需要与环境交互或优化累积奖励。选项 A 不准确（两者都可以结合注意力机制）；选项 C 不准确（DT 可以处理连续或离散动作）；选项 D 不准确（DT 仍然需要奖励序列计算 Rtg，但不需要奖励函数进行优化）。

---

**2. [单选]** 在 Decision Transformer 中，回报-to-Go（Rtg）的定义是？

A. $R_t = \sum_{t'=0}^{t} \gamma^{t'} r_{t'}$（从开始到当前的所有折扣奖励之和）  
B. $R_t = r_t$（即时奖励）  
C. $R_t = \sum_{t'=t}^{T} \gamma^{t'-t} r_{t'}$（从当前到轨迹结束的折扣奖励之和）  
D. $R_t = \mathbb{E}[\sum_{t'=0}^{\infty} \gamma^{t'} r_{t'}]$（无限时域期望）  

**答案：C  
解析：** Rtg（Return-to-Go）字面意思是"尚待获取的回报"，即从当前时刻 $t$ 到轨迹结束 $T$ 的折扣累积奖励 $R_t = \sum_{t'=t}^{T} \gamma^{t'-t} r_{t'}$。选项 A 是累积奖励（从 0 到 t），不是 DT 中的 Rtg。Rtg 是 Transformer 的条件输入，用来告知模型"预期还有多少回报可以争取"。

---

**3. [单选]** ACT（Action Chunking Transformer）引入"动作分块"机制的主要目的是？

A. 提高动作预测的精度  
B. 解决 Transformer 推理速度慢导致控制频率不足的问题  
C. 减少模型参数，降低计算成本  
D. 增强策略的泛化能力  

**答案：B  
解析：** 机器人的控制频率通常很高（100Hz+），而 Transformer 的推理速度相对较慢。ACT 的核心解决方案是**一次预测多个未来时刻的动作（T 个时间步构成一个 chunk）**，将控制频率提升 T 倍。动作分块并不直接提高单步精度（选项 A）、也不主要为了减少参数量（选项 C）或泛化（选项 D）。

---

**4. [单选]** Trajectory Transformer（TT）与 Decision Transformer（DT）的核心区别是？

A. TT 使用 LSTM，DT 使用 Transformer  
B. TT 联合预测状态、动作和奖励，DT 仅预测动作  
C. TT 只能处理文本序列，DT 只能处理机器人任务  
D. TT 必须在线训练，DT 可以离线训练  

**答案：B  
解析：** TT 将**整个轨迹（状态、动作、奖励）联合建模为序列**，同时预测下一个状态 $s_{t+1}$、动作 $a_t$ 和奖励 $r_t$，并在推理时用 Beam Search 解码完整轨迹计划。DT 仅预测动作 $a_t$。其他选项均描述错误。

---

### 简答题

**5. [简答]** 解释为什么在 Decision Transformer 中需要使用因果掩码（Causal Mask），以及如果不使用会造成什么后果？

**参考答案：**

因果掩码（Causal Mask）是 Decision Transformer 实现**自回归预测**的关键机制，确保在预测当前时间步 $t$ 的动作时，模型只能看到 $t$ 及之前的历史信息，而不能"窥视"未来的状态和动作。

**为什么需要因果掩码：**

1. **防止信息泄漏**：如果模型在预测 $a_t$ 时能看到 $a_{t+1}, s_{t+1}$ 等未来信息，它就不需要真正学习决策逻辑——直接"复制"未来动作即可
2. **与推理方式一致**：在线推理时，模型在 $t$ 时刻只有历史信息可用。因果掩码保证了训练与推理的条件完全一致
3. **实现自回归生成**：类似于语言模型中预测下一个词时只能看前面的词

**后果（不使用因果掩码）：**

- **训练时**：模型直接看到目标动作 $a_t$，损失急剧下降，但这是虚假的"学习"——模型没有学到决策能力
- **推理时崩溃**：实际部署时没有未来信息可用，模型性能大幅下降
- **过拟合风险**：模型记忆未来的输入输出对，无法泛化到真实决策场景

**实现方式**：
```python
# 因果掩码：上三角为 True（阻止 attend）
causal_mask = torch.triu(
    torch.ones(seq_len, seq_len), diagonal=1
).bool()
```

---

**6. [简答]** 说明 Decision Transformer 中 Rtg 条件化的作用，并解释为什么说 DT 实现了"目标导向"的决策。

**参考答案：**

**Rtg 条件化的核心作用：**

Rtg（Return-to-Go）$R_t$ 告诉 Transformer "从现在开始预期还能获得多少累积回报"。这是一个动态的条件信号，它的作用机制是：

1. **高 Rtg（如 $R_t = 100$）→ 告诉模型还有大量回报可以争取 → 应采取 ambitious（激进）的策略  
2. **低 Rtg（如 $R_t = -10$）→ 告诉模型预期回报已经很低 → 应采取 corrective（修正性）的策略，避免更大的损失

**为什么说 DT 实现了"目标导向"决策：**

在传统 RL 中，策略 $\pi(a_t | s_t)$ 由状态唯一决定，策略的目标隐含在奖励函数设计中（由环境决定）。

在 DT 中，策略变为 $\pi(a_t | R_t, \tau_{<t})$，同样的状态 $s_t$ 下，不同的 $R_t$ 会导向完全不同的动作——这相当于**显式地将目标作为条件输入传给模型**。

| 场景 | 高 $R_t$ 时的动作 | 低 $R_t$ 时的动作 |
|------|-----------------|-----------------|
| 机器人抓取 | 继续接近目标 | 放慢速度，修正位置 |
| 自动驾驶 | 保持高速行驶 | 减速，注意安全 |
| 游戏 | 继续进攻 | 保守策略，减少失误 |

这与人类决策非常相似——当目标明确且时间充裕时，我们会更激进；当发现目标难以达成时，我们会调整策略甚至放弃。

---

**7. [简答]** 比较 Decision Transformer、Trajectory Transformer 和 ACT 三种方法在决策方式上的差异，并分析各适用场景。

**参考答案：**

| 方法 | 决策方式 | 解码方式 | 适用场景 | 优缺点 |
|------|---------|---------|---------|--------|
| **Decision Transformer** | 单步在线决策 | 贪婪/随机采样 | 需要实时响应的任务（机械臂控制、机器人导航） | 实时性好，但有误差累积 |
| **Trajectory Transformer** | 开环轨迹规划 | Beam Search | 长程规划任务（多阶段操作、长距离导航） | 避免误差累积，但开环执行有风险 |
| **ACT** | 动作块在线决策 | 贪婪 + 时序平滑 | 高频控制场景（双臂操作、精细运动控制） | 兼顾频率与平滑性，50Hz 控制 |

**详细说明：**

**Decision Transformer**：每步用当前历史序列预测下一个动作，闭环执行。优势是实时性好（每步只推理一次），劣势是长序列中误差会累积。

**Trajectory Transformer**：一次性规划完整轨迹（通过 Beam Search 从 $p(s,a,r)$ 联合分布中采样多条轨迹，选取最优），然后开环执行。优势是全局优化（考虑动作序列的整体效果），劣势是开环执行在环境变化时无法自适应。

**ACT**：每次推理预测 $K$ 个动作（一个 chunk），执行部分后继续推理下一块。核心解决的是 Transformer 推理延迟与机器人高频控制之间的矛盾。通过动作块 + 平滑过渡，在保证控制频率的同时维持了序列建模的优势。

**适用场景总结**：
- **实时短程任务**：DT（如单步抓取、简单导航）
- **长程多阶段任务**：TT（如"打开冰箱→取出食物→关上冰箱"的完整操作流程）
- **高频精细操作**：ACT（如双臂协同装配、精细力控操作）
