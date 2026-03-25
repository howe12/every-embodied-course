# 14-5 RLHF 与人类反馈强化学习

**版本**: V2.0  
**作者**: Wendy | **课程系列**: ROS2机器人仿真与应用实践  
**适用对象**: 具备强化学习基础，希望理解并实现人类反馈强化学习的学员  
**前置知识**: 强化学习基础概念（策略梯度、PPO）、深度学习基础（神经网络、损失函数）

---

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 14-5 |
| 课程名称 | RLHF 与人类反馈强化学习 |
| 所属模块 | 14-强化学习 (RL) |
| 难度等级 | ⭐⭐⭐⭐☆ |
| 预计学时 | 8小时 |
| 前置知识 | 强化学习基础（策略梯度、PPO）、深度学习基础 |

---

## 目录

1. [RLHF概述](#1-rlhf概述)
2. [Reward Model训练](#2-reward-model训练)
3. [PPO微调](#3-ppo微调)
4. [其他人类反馈方法](#4-其他人类反馈方法)
5. [具身智能应用](#5-具身智能应用)
6. [代码实战](#6-代码实战)
7. [练习题](#7-练习题)
8. [参考答案](#8-参考答案)

---

## 一、RLHF概述

### 1.1 什么是人类反馈强化学习

**RLHF（Reinforcement Learning from Human Feedback，即人类反馈强化学习）** 是一种将人类偏好融入强化学习的技术框架。与传统RL依赖精确奖励函数不同，RLHF通过学习一个**人类偏好模型（Reward Model）**来替代手工设计的奖励函数。

RLHF的核心管线分为三个阶段：

1. **监督微调（SFT）**：在大规模预训练模型基础上，用高质量人工标注数据进行监督学习，获得一个具备基础能力的模型。
2. **奖励模型训练（RM）**：收集人类对成对输出的偏好数据，训练一个奖励模型来预测人类偏好。
3. **PPO强化学习**：使用奖励模型提供的信号，通过强化学习（通常是PPO算法）进一步优化策略模型。

整个流程中，最关键的创新是**不需要精确奖励**——人类只需要表达"我更喜欢A而不是B"，奖励模型就能学会如何评分。

### 1.2 为什么需要人类反馈

传统强化学习面临的核心困难是**奖励设计（Reward Engineering）**：对于复杂任务（如写作质量、对话流畅性），精确奖励函数往往极难设计——我们很难用数学公式精确描述什么是"好的对话"。

即便我们能设计出奖励函数，也常常遇到**奖励黑客（Reward Hacking）**问题：智能体发现奖励函数的漏洞，通过非预期的手段获取高奖励，而实际任务性能却很差。典型的例子是游戏AI学会"卡bug"来得分，而非真正掌握游戏策略。

人类反馈则可以解决这些问题：

- **表达主观偏好**：人类可以自然地判断"这段回复更有帮助"，无需定义精确的奖励函数。
- **避免奖励黑客**：人类的判断基于整体质量，难以被单一维度的指标欺骗。
- **处理开放域任务**：对于没有明确正确答案的任务，人类反馈是唯一可行的指导信号。

### 1.3 RLHF的发展历程

RLHF的发展历程可追溯至早期研究：

| 年份 | 工作 | 贡献 |
|------|------|------|
| 2017 | "Deep Reinforcement Learning from Human Preferences" (Christiano et al.) | 首次提出用人类偏好替代精确奖励的框架 |
| 2020 | InstructGPT / GPT-3 | 展示了RLHF在大语言模型对齐中的巨大威力 |
| 2022 | Constitutional AI (Anthropic) | 提出用AI反馈替代部分人类反馈（RLAIF） |
| 2022 | ChatGPT (OpenAI) | RLHF成为对话AI的核心技术 |
| 2023 | Llama 2 (Meta) | 开源模型中大规模应用RLHF |

值得注意的是，2022年Anthropic提出的**Constitutional AI（宪法AI）**在RLHF基础上更进一步：使用一组人类编写的"宪法原则"（如"不要提供有害信息"），让AI自我批评并修正输出，从而大幅减少对人类标注的依赖。

### 1.4 人类反馈 vs 规则奖励

| 维度 | 规则奖励 | 人类反馈 |
|------|----------|----------|
| **设计成本** | 高（需要领域专家设计） | 中（需要标注员标注偏好） |
| **适用范围** | 任务明确、指标可量化 | 主观判断、开放域任务 |
| **奖励黑客风险** | 高（规则容易被钻空子） | 低（人类判断更全面） |
| **可扩展性** | 差（每新任务需重新设计） | 好（偏好模型可迁移） |
| **标注一致性** | N/A | 挑战（标注员间存在差异） |
| **典型应用** | 游戏、机器人控制 | 对话、写作、内容审核 |

---

## 二、Reward Model训练

### 2.1 人类偏好数据收集

偏好数据的收集是RLHF中成本最高的环节，需要精心设计标注流程：

**标注任务设计**：标注员面对的是一个（prompt, response_A, response_B）三元组，需要判断哪个回复更好。有时还需要标注"好多少"（偏好强度）。

**数据形如**：

```python
preference_data = [
    {
        "prompt": "解释一下量子计算",
        "response_a": "量子计算是一种使用量子力学原理进行信息处理的计算方式...",
        "response_b": "量子计算就是量子力学加计算机，没什么特别的。",
        "preference": "a"  # 标注员选择了response_a
    },
    # ...
]
```

**质量控制**：
- **交叉标注**：同一对样本由多个标注员独立标注，计算一致性指标
- **标注指南**：详细说明标注标准，确保标注员之间的判断一致性
- **争议样本复审**：对争议较大的样本进行专家复审

**数据规模**：InstructGPT使用的偏好数据约为数万个样本。虽然听起来不多，但这些数据需要覆盖足够多样的任务类型和回复风格。

### 2.2 Bradley-Terry模型

**Bradley-Terry模型**是偏好建模的理论基石，源自统计学中用于分析竞技比赛和主观评分的经典模型。

假设给定一个prompt和两个候选回复A和B。Bradley-Terry模型假设人类选择A而非B的概率由下式给出：

$$P(A \succ B) = \frac{exp(r_A)}{exp(r_A) + exp(r_B)} = \frac{1}{1 + exp(r_B - r_A)}$$

其中 $r_A$ 和 $r_B$ 分别是回复A和回复B的潜在"真实"奖励（隐变量），$P(A \succ B)$ 是人类偏好A的实际概率。

如果我们用神经网络 $r_\phi(\text{prompt}, \text{response})$ 来逼近这个潜在奖励，那么训练奖励模型等价于拟合下面的对数似然：

$$\mathcal{L}_{\text{RM}} = -\mathbb{E}_{(\text{prompt}, y_A, y_B, \text{pref}) \sim D} \left[ \log \sigma \left( r_\phi(\text{prompt}, y_{\text{pref}}) - r_\phi(\text{prompt}, y_{\text{rejected}}) \right) \right]$$

其中 $\text{pref} \in \{A, B\}$ 表示人类偏好的回复，$\sigma$ 是sigmoid函数。这个损失函数的含义是：如果人类偏好A，那么我们希望 $r_\phi(\text{prompt}, A) > r_\phi(\text{prompt}, B)$，即让差值的sigmoid值接近1（对数似然接近0）。

直觉上理解：这个损失函数是一个**二元交叉熵损失**，将偏好问题转化为"A的奖励是否高于B"的二分类问题。

### 2.3 Reward Model损失函数

奖励模型的训练目标是最大化人类偏好的似然。给定一批偏好数据，损失函数为：

$$\mathcal{L}_{\text{RM}} = -\sum_{i=1}^{N} \log \sigma \left( r_\phi(x_i, y_i^+) - r_\phi(x_i, y_i^-) \right)$$

其中：
- $x_i$ 是第 $i$ 个输入prompt
- $y_i^+$ 是被选中的回复（preferred）
- $y_i^-$ 是被拒绝的回复（rejected）
- $r_\phi(\cdot)$ 是奖励模型输出的标量分数

**关键实现细节**：
- 奖励模型通常在SFT模型基础上改造：将最后的线性层替换为一个输出标量的头
- 初始化时将奖励头权重初始化为零，使初始奖励接近零，便于后续学习
- 使用对比学习思想：同prompt的两个回复，奖励模型应给偏好回复更高分

### 2.4 奖励模型标定

奖励模型训练完成后，需要进行**标定（Calibration）**以确保奖励分数具有绝对意义：

**Z-scoring（InstructGPT方法）**：在PPO训练期间，对奖励进行归一化：

$$\hat{r}(x,y) = \frac{r(x,y) - \mu}{\sigma}$$

其中 $\mu$ 和 $\sigma$ 是奖励的均值和标准差（使用指数移动平均估计）。

**Pairwise Accuracy验证**：用测试集验证奖励模型的准确性，期望达到70-80%的偏好预测准确率。

---

## 三、PPO微调

### 3.1 PPO + Reward Model

获得奖励模型后，就可以进入强化学习阶段——使用奖励模型提供的信号，通过强化学习进一步优化策略模型。

这一阶段通常使用**PPO（Proximal Policy Optimization）**算法，原因在于PPO的裁剪机制能很好地控制策略更新的幅度，防止模型在优化过程中"跑偏"。

RLHF中的PPO与标准PPO有一个关键区别：**KL散度约束**。我们希望优化后的模型不要太偏离SFT模型——因为奖励模型虽然能评分，但它的偏好不一定完全正确，如果放任优化，模型可能"走火入魔"生成语法正确但内容荒谬的文本。

RLHF-PPO的目标函数为：

$$\mathcal{L}_{\text{RLHF}} = \mathbb{E}_{x\sim D, y\sim\pi_\theta(\cdot|x)} \left[ r_\phi(x, y) - \beta \cdot \text{KL}(\pi_\theta(y|x) \| \pi_{\text{SFT}}(y|x)) \right]$$

其中 $r_\phi(x, y)$ 是奖励模型对输出 $y$ 的评分，$\beta$ 是KL惩罚系数，$\pi_{\text{SFT}}$ 是SFT阶段的参考模型。

### 3.2 KL散度约束

**KL散度（Kullback-Leibler Divergence）**是衡量两个概率分布差异的度量：

$$\text{KL}(P \| Q) = \mathbb{E}_{x\sim P} \left[ \log \frac{P(x)}{Q(x)} \right]$$

在RLHF中，我们用它来衡量当前策略 $\pi_\theta$ 与参考策略 $\pi_{\text{SFT}}$ 之间的差异。KL惩罚项的作用是双重的：
- **防止语言崩坏**：如果完全自由优化奖励，语言模型可能生成语法奇怪但高奖励的文本
- **防止奖励黑客变体**：即便奖励模型给出高评分，如果与参考模型的分布差异过大，KL惩罚会将其拉回

实际工程中，$\beta$ 的取值需要权衡：过大（>0.1）会压制对奖励的优化；过小（<0.01）则KL约束失效。InstructGPT中 $\beta$ 取0.03左右。

### 3.3 策略更新稳定性

RLHF的训练稳定性是出了名的困难，以下是核心挑战和解决方案：

**挑战一：奖励模型过度自信**  
PPO阶段会出现"奖励黑客"现象。

**解决方案**：对奖励模型进行正则化；在PPO训练中对奖励进行归一化。

**挑战二：KL散度爆炸**  
训练初期PPO可能产生与参考模型差异极大的输出。

**解决方案**：使用**自适应KL目标**——当实际KL超过目标值时加大惩罚系数；设置KL的硬上限。

**挑战三：训练早期振荡**  
PPO在奖励模型信号过强时会产生剧烈振荡。

**解决方案**：使用**价值函数（Value Function）**估计回报；在PPO损失中添加**值函数损失**项。

### 3.4 PPOx模型训练流程

完整的RLHF-PPOx训练流程如下：

```
┌─────────────────────────────────────────────────────────────────┐
│                      RLHF PPOx 训练流程                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. [参考模型 π_ref] ← SFT模型（冻结，不更新）                    │
│                                                                 │
│  2. [采样] 从训练数据中采样一批prompts                            │
│         prompts → 当前策略模型 → 生成responses                   │
│                                                                 │
│  3. [评分] 使用Reward Model对每个response打分                     │
│         r = R_M(prompt, response)                               │
│                                                                 │
│  4. [KL计算] 计算每个response的KL散度                             │
│         KL = KL(π_θ || π_ref)                                   │
│                                                                 │
│  5. [优势计算] Advantage = r - β·KL（减去KL惩罚）                │
│                                                                 │
│  6. [PPO更新] 使用PPO裁剪目标更新策略模型                         │
│         L = min(ratio·A, clip(ratio, 1-ε, 1+ε)·A)               │
│                                                                 │
│  7. 重复步骤2-6直至收敛                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 四、其他人类反馈方法

### 4.1 RLAIF（AI反馈）

**RLAIF（Reinforcement Learning from AI Feedback）** 是Anthropic在Constitutional AI论文中提出的方法，旨在减少对人类标注的依赖。

**核心思想**：用AI（通常是更大的模型）替代人类进行偏好判断，从而规模化偏好数据的生成。

**RLAIF vs RLHF**：

| 维度 | RLHF | RLAIF |
|------|------|-------|
| 反馈来源 | 人类标注员 | AI模型（如Claude） |
| 标注成本 | 高（需要大量人工） | 低（可自动化） |
| 偏好质量 | 高（真实人类偏好） | 中（取决于评判模型能力） |
| 规模化潜力 | 有限（受人类标注速度限制） | 强（可并行生成） |

### 4.2 DPO（Direct Preference Optimization）

**DPO（Direct Preference Optimization，直接偏好优化）** 是斯坦福大学2023年提出的方法，直接在偏好数据上优化策略，**无需训练奖励模型，也无需使用PPO**。

**核心洞察**：DPO发现可以直接将RLHF的RL目标转化为一个**监督学习问题**，从而绕过了奖励模型训练和RL过程。

**DPO损失函数**：

$$\mathcal{L}_{\text{DPO}} = -\mathbb{E}_{(x, y^+, y^-) \sim D} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y^+|x)}{\pi_{\text{ref}}(y^+|x)} - \beta \log \frac{\pi_\theta(y^-|x)}{\pi_{\text{ref}}(y^-|x)} \right) \right]$$

其中 $\beta$ 是温度参数，控制偏离参考模型的程度。

**DPO vs PPO-RLHF**：

| 维度 | PPO-RLHF | DPO |
|------|---------|-----|
| 需要奖励模型 | 是 | 否 |
| 需要PPO训练 | 是 | 否 |
| 训练稳定性 | 中等 | 较高 |
| 样本效率 | 中等 | 较高（off-policy可用） |
| 超参数数量 | 多（学习率、PPO参数、KL系数等） | 少（主要是β） |

### 4.3 KTO（Kahneman-Tversky Optimization）

**KTO（Kahneman-Tversky Optimization）** 是基于行为经济学中的**Kahneman-Tversky前景理论**，由Farima等人2023年提出。

**核心思想**：人类对**损失**比等量**收益**更敏感（损失厌恶）。KTO利用这一洞察，对偏好数据和非偏好数据采用不对称的损失函数。

**KTO的优势**：
- **无需成对偏好数据**：只需要正负样本，不需要成对比较
- **更符合人类心理**：直接建模损失厌恶心理
- **训练更简单**：不需要Bradley-Terry模型假设

---

## 五、具身智能应用

### 5.1 机器人任务的人类偏好学习

RLHF的核心思想——用人类偏好替代精确奖励——在**具身智能（Embodied AI）**领域同样具有巨大价值。传统的机器人技能学习依赖手工设计的奖励函数，但很多复杂任务的奖励信号难以精确量化。

**机器人场景中的人类偏好应用**：

| 任务类型 | 传统奖励设计难点 | RLHF如何解决 |
|----------|-----------------|-------------|
| 折叠衣物 | "整齐"无法精确量化 | 人类直接判断哪次折叠更好 |
| 桌面整理 | 不同物品摆放有不同偏好 | 人类比较不同整理方案 |
| 社交机器人 | 对话风格无标准答案 | 人类偏好决定对话风格 |
| 人形机器人行走 | 步态美感难以定义 | 人类选择更自然的步态 |
| 协助手术 | 安全和效率需要权衡 | 外科医生偏好决定优先级 |

**机器人RLHF的数据收集**：

```python
robot_preference_data = [
    {
        "task": "将红色方块放入蓝色盒子",
        "trajectory_a": [state1, action1, state2, action2, ...],  # 轨迹A
        "trajectory_b": [state1, action1_prime, state2, action2_prime, ...],  # 轨迹B
        "preference": "a",  # 人类选择轨迹A
        "human_id": "annotator_001"
    },
    # ...
]
```

### 5.2 安全约束的RLHF

在机器人领域，**安全**是首要约束。RLHF可以通过人类偏好来注入安全约束，使机器人学会避开危险行为。

**安全RLHF的核心方法**：

**方法一：安全偏好数据增强**

在偏好数据收集时，刻意包含一些"看起来有效但有安全隐患"的样本，让奖励模型学会识别不安全行为：

```python
safety_preference_examples = [
    {
        "task": "将杯子从桌上拿起",
        "trajectory_safe": "缓慢靠近 → 轻握 → 提起",  # 安全的轨迹
        "trajectory_dangerous": "快速猛抓 → 杯子飞出",  # 危险但可能短期有效的轨迹
        "preference": "safe"
    },
    {
        "task": "在人旁边操作机械臂",
        "trajectory_aggressive": "大范围高速运动",  # 危险的轨迹
        "trajectory_conservative": "小范围低速运动",  # 安全的轨迹
        "preference": "conservative"
    }
]
```

**方法二：Constitutional AI for Robotics**

将安全原则编码为"宪法"，让机器人学会自我批评：

```python
robot_safety_constitution = [
    "1. 绝不向人类移动方向加速",
    "2. 检测到接触时应立即停止",
    "3. 不在人类视线盲区内操作",
    "4. 力量输出不超过安全阈值",
    "5. 未知环境应降低速度"
]
```

**方法三：带约束的RLHF目标函数**

将安全约束以**惩罚项**形式加入RL目标：

$$\mathcal{L}_{\text{SafeRLHF}} = \mathbb{E} \left[ r_\phi(x, y) - \beta \cdot \text{KL}(\pi_\theta \| \pi_{\text{SFT}}) - \lambda \cdot C(y) \right]$$

其中 $C(y)$ 是安全约束惩罚项，$\lambda$ 是安全约束权重。安全约束可以是：
- 碰撞检测：$C_{\text{collision}} = \mathbb{1}(\text{发生碰撞})$
- 力阈值：$C_{\text{force}} = \max(0, \|F\| - F_{\text{max}})$
- 距离约束：$C_{\text{distance}} = \max(0, d_{\min} - d_{\text{human}})$

---

## 六、代码实战

### 6.1 Reward Model训练示例

下面实现一个基于GPT-2的奖励模型：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer


class RewardModel(nn.Module):
    """
    奖励模型：将 (prompt, response) 映射为一个标量奖励分数
    基于预训练语言模型，在顶部添加一个奖励输出头
    """
    
    def __init__(self, model_name: str = "gpt2"):
        super().__init__()
        # 加载预训练语言模型作为基础网络
        self.model = AutoModel.from_pretrained(model_name)
        self.model_name = model_name
        
        # 获取隐藏层大小
        hidden_size = self.model.config.n_embd
        
        # 投影层：将模型输出映射为标量奖励
        self.reward_head = nn.Linear(hidden_size, 1, bias=False)
        
        # 初始化奖励头的权重为零（参考InstructGPT实践）
        nn.init.zeros_(self.reward_head.weight)
    
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor):
        """
        前向传播
        
        Args:
            input_ids: 输入token序列，shape: (batch_size, seq_len)
            attention_mask: 注意力掩码，shape: (batch_size, seq_len)
        
        Returns:
            rewards: 标量奖励分数，shape: (batch_size,)
        """
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        last_hidden_state = outputs.last_hidden_state  # (batch, seq_len, hidden)
        
        # 取序列最后一个有效token的隐藏状态作为句子表示
        sequence_lengths = attention_mask.long().sum(dim=1) - 1
        batch_indices = torch.arange(
            last_hidden_state.size(0), 
            device=last_hidden_state.device
        )
        pooled_hidden = last_hidden_state[batch_indices, sequence_lengths, :]
        
        # 通过奖励头得到标量分数
        rewards = self.reward_head(pooled_hidden).squeeze(-1)  # (batch,)
        return rewards


class BradleyTerryLoss(nn.Module):
    """
    Bradley-Terry 偏好损失函数
    训练奖励模型时使用：给定偏好对 (y_winner, y_loser)，最大化差值奖励
    """
    
    def __init__(self):
        super().__init__()
    
    def forward(self, r_winner: torch.Tensor, r_loser: torch.Tensor):
        """
        计算偏好损失
        
        Args:
            r_winner: 偏好回复的奖励分数，shape: (batch_size,)
            r_loser: 被拒绝回复的奖励分数，shape: (batch_size,)
        
        Returns:
            loss: 标量损失
        """
        # Bradley-Terry模型：P(A > B) = sigmoid(r_A - r_B)
        # 损失 = -log(P(偏好 > 被拒绝))
        diff = r_winner - r_loser  # shape: (batch,)
        loss = -torch.log(torch.sigmoid(diff)).mean()
        return loss


def train_reward_model(
    reward_model,
    preference_data,
    tokenizer,
    epochs: int = 3,
    lr: float = 1e-5,
    batch_size: int = 8,
    device: str = "cuda"
):
    """
    训练奖励模型
    """
    optimizer = torch.optim.AdamW(reward_model.parameters(), lr=lr)
    criterion = BradleyTerryLoss()
    reward_model.train()
    reward_model.to(device)
    
    dataset_size = len(preference_data)
    num_batches = dataset_size // batch_size
    
    for epoch in range(epochs):
        total_loss = 0.0
        indices = torch.randperm(dataset_size)
        
        for i in range(num_batches):
            batch_indices = indices[i * batch_size : (i + 1) * batch_size]
            
            prompts = [preference_data[idx]['prompt'] for idx in batch_indices]
            chosen_responses = [preference_data[idx]['chosen'] for idx in batch_indices]
            rejected_responses = [preference_data[idx]['rejected'] for idx in batch_indices]
            
            # 编码chosen和rejected responses
            chosen_texts = [
                p + tokenizer.eos_token + c 
                for p, c in zip(prompts, chosen_responses)
            ]
            rejected_texts = [
                p + tokenizer.eos_token + r 
                for p, r in zip(prompts, rejected_responses)
            ]
            
            chosen_enc = tokenizer(
                chosen_texts,
                truncation=True,
                max_length=512,
                padding='max_length',
                return_tensors='pt'
            )
            rejected_enc = tokenizer(
                rejected_texts,
                truncation=True,
                max_length=512,
                padding='max_length',
                return_tensors='pt'
            )
            
            chosen_ids = chosen_enc['input_ids'].to(device)
            chosen_mask = chosen_enc['attention_mask'].to(device)
            rejected_ids = rejected_enc['input_ids'].to(device)
            rejected_mask = rejected_enc['attention_mask'].to(device)
            
            # 前向传播：分别计算chosen和rejected的奖励
            r_chosen = reward_model(chosen_ids, chosen_mask)
            r_rejected = reward_model(rejected_ids, rejected_mask)
            
            # 计算Bradley-Terry损失
            loss = criterion(r_chosen, r_rejected)
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                reward_model.parameters(), 
                max_norm=1.0
            )
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / num_batches
        print(f"[Reward Model] Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
    
    return reward_model
```

### 6.2 DPO简化实现

DPO将RLHF的RL阶段转化为直接的监督学习，无需奖励模型和PPO：

```python
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer


class DPOTrainer:
    """
    DPO (Direct Preference Optimization) 训练器
    
    核心思想：直接优化策略模型使其偏好数据中preferred回复的概率高于rejected
    损失函数基于Bradley-Terry模型的隐式奖励差异
    """
    
    def __init__(
        self,
        policy_model,      # 当前策略模型（需要优化的模型）
        ref_model,         # 参考模型（SFT模型，不优化）
        beta: float = 0.1, # 温度参数，控制偏离参考模型的程度
        lr: float = 1e-6,
    ):
        self.policy_model = policy_model
        self.ref_model = ref_model
        self.beta = beta
        self.optimizer = torch.optim.AdamW(
            policy_model.parameters(), 
            lr=lr
        )
        
        # 冻结参考模型
        for param in ref_model.parameters():
            param.requires_grad = False
    
    def get_sequence_log_probs(self, model, input_ids, attention_mask, labels):
        """
        计算序列的log概率（对数似然）
        
        使用滑动窗口方式计算：对于每个token，
        log_prob[ t ] = log P(x_t | x_<t)
        最终返回序列平均log概率
        """
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        logits = outputs.logits  # (batch, seq_len, vocab_size)
        
        # 计算每个token的log概率
        # 移位：logits[:, :-1] 对应 labels[:, 1:]
        log_probs = F.log_softmax(logits, dim=-1)
        
        # 获取每个token位置对应label的log概率
        # labels是输入序列（因为是Causal LM）
        # 对于位置 t，我们用 logits[:, t-1] 来预测 label[:, t]
        # 即 labels[:, 1:] 对应 logits[:, :-1]
        
        # 有效位置（非padding）的mask
        valid_mask = attention_mask.float()
        
        # 计算序列的平均log概率
        # 对于每个样本，计算所有有效token位置log概率的平均
        per_token_logps = torch.gather(
            log_probs, 
            dim=2, 
            index=labels.unsqueeze(2)
        ).squeeze(2)  # (batch, seq_len)
        
        # 考虑有效token的mask
        seq_log_probs = (per_token_logps * valid_mask).sum(dim=-1) / valid_mask.sum(dim=-1)
        
        return seq_log_probs  # (batch,)
    
    def dpo_loss(
        self,
        policy_chosen_logps,    # 策略模型对chosen序列的log概率
        policy_rejected_logps,  # 策略模型对rejected序列的log概率
        ref_chosen_logps,       # 参考模型对chosen序列的log概率
        ref_rejected_logps,     # 参考模型对rejected序列的log概率
    ):
        """
        计算DPO损失
        
        DPO的核心洞察：使用隐式奖励 r(y) = β * (log πθ(y) - log πref(y))
        偏好概率 P(y+ > y-) = sigmoid(r(y+) - r(y-))
        """
        # 计算隐式奖励差异
        # 对于chosen：β * (log πθ(y+) - log πref(y+))
        chosen_rewards = self.beta * (policy_chosen_logps - ref_chosen_logps)
        # 对于rejected：β * (log πθ(y-) - log πref(y-))
        rejected_rewards = self.beta * (policy_rejected_logps - ref_rejected_logps)
        
        # 偏好概率 = sigmoid(奖励差异)
        # 我们希望 chosen_reward - rejected_reward 越大越好
        reward_diff = chosen_rewards - rejected_rewards
        
        # DPO损失 = -log(sigmoid(reward_diff)) 
        # 等价于最小化：sigmoid(reward_diff) 越小（即 reward_diff 越大）
        # 但实际使用 log-sigmoid 以保持数值稳定
        loss = -torch.log(torch.sigmoid(reward_diff)).mean()
        
        return loss
    
    def train_step(self, batch):
        """
        执行一次DPO训练步骤
        
        Args:
            batch: 包含以下键的字典
                - chosen_ids: 被选中的序列token ids
                - rejected_ids: 被拒绝的序列token ids
                - attention_mask: 注意力掩码
        """
        chosen_ids = batch['chosen_ids']
        rejected_ids = batch['rejected_ids']
        attention_mask = batch['attention_mask']
        
        # 计算策略模型和参考模型对chosen/rejected序列的log概率
        # 注意：labels = input_ids（因果语言模型）
        
        # 策略模型
        policy_chosen_logps = self.get_sequence_log_probs(
            self.policy_model, chosen_ids, attention_mask, chosen_ids
        )
        policy_rejected_logps = self.get_sequence_log_probs(
            self.policy_model, rejected_ids, attention_mask, rejected_ids
        )
        
        # 参考模型（不更新梯度）
        with torch.no_grad():
            ref_chosen_logps = self.get_sequence_log_probs(
                self.ref_model, chosen_ids, attention_mask, chosen_ids
            )
            ref_rejected_logps = self.get_sequence_log_probs(
                self.ref_model, rejected_ids, attention_mask, rejected_ids
            )
        
        # 计算DPO损失
        loss = self.dpo_loss(
            policy_chosen_logps,
            policy_rejected_logps,
            ref_chosen_logps,
            ref_rejected_logps
        )
        
        # 反向传播
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            self.policy_model.parameters(), 
            max_norm=1.0
        )
        self.optimizer.step()
        
        return {
            'loss': loss.item(),
            'reward_diff': (policy_chosen_logps - policy_rejected_logps).mean().item()
        }


def dpo_training_loop(
    policy_model,
    ref_model,
    preference_data,
    tokenizer,
    num_epochs=3,
    batch_size=4,
    beta=0.1,
    lr=1e-6
):
    """
    DPO训练循环
    
    Args:
        preference_data: 偏好数据列表
            [{'prompt': str, 'chosen': str, 'rejected': str}, ...]
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    dpo_trainer = DPOTrainer(
        policy_model=policy_model,
        ref_model=ref_model,
        beta=beta,
        lr=lr
    )
    
    policy_model.to(device)
    ref_model.to(device)
    
    for epoch in range(num_epochs):
        total_loss = 0.0
        indices = torch.randperm(len(preference_data))
        num_batches = len(preference_data) // batch_size
        
        for i in range(num_batches):
            batch_indices = indices[i * batch_size : (i + 1) * batch_size]
            batch_data = [preference_data[idx] for idx in batch_indices]
            
            # 构建batch
            # 格式：prompt + chosen/rejected response
            chosen_texts = [
                d['prompt'] + tokenizer.eos_token + d['chosen']
                for d in batch_data
            ]
            rejected_texts = [
                d['prompt'] + tokenizer.eos_token + d['rejected']
                for d in batch_data
            ]
            
            chosen_enc = tokenizer(
                chosen_texts,
                truncation=True,
                max_length=512,
                padding='max_length',
                return_tensors='pt'
            )
            rejected_enc = tokenizer(
                rejected_texts,
                truncation=True,
                max_length=512,
                padding='max_length',
                return_tensors='pt'
            )
            
            batch = {
                'chosen_ids': chosen_enc['input_ids'].to(device),
                'rejected_ids': rejected_enc['input_ids'].to(device),
                'attention_mask': chosen_enc['attention_mask'].to(device)
            }
            
            stats = dpo_trainer.train_step(batch)
            total_loss += stats['loss']
        
        avg_loss = total_loss / num_batches
        print(f"[DPO] Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
    
    return policy_model
```

### 6.3 人类反馈数据收集流程

```python
"""
人类反馈数据收集流程模拟
实际应用中需要部署专门的标注平台
"""


class HumanPreferenceCollector:
    """
    人类偏好数据收集器
    
    负责管理标注任务生成、标注结果收集、数据质量控制
    """
    
    def __init__(self, model, tokenizer, num_candidates: int = 2):
        self.model = model
        self.tokenizer = tokenizer
        self.num_candidates = num_candidates  # 每个prompt生成的候选回复数
    
    def generate_candidates(self, prompt: str, num_candidates: int = None):
        """
        使用当前模型为给定prompt生成多个候选回复
        
        使用不同温度和随机种子来增加多样性
        """
        if num_candidates is None:
            num_candidates = self.num_candidates
        
        candidates = []
        temperatures = [0.3, 0.5, 0.7, 0.9, 1.1]
        
        for i in range(num_candidates):
            temp = temperatures[i % len(temperatures)]
            
            encoded = self.tokenizer(
                prompt,
                return_tensors='pt',
                truncation=True,
                max_length=256
            ).to(self.model.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **encoded,
                    max_new_tokens=150,
                    do_sample=True,
                    temperature=temp,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            
            # 去掉prompt部分
            prompt_len = encoded['input_ids'].shape[1]
            response_ids = generated_ids[0][prompt_len:]
            response = self.tokenizer.decode(response_ids, skip_special_tokens=True)
            candidates.append(response)
        
        return candidates
    
    def create_preference_pair(self, prompt: str):
        """
        为一个prompt创建偏好对
        返回 (prompt, response_a, response_b) 供人类标注
        """
        candidates = self.generate_candidates(prompt, num_candidates=2)
        
        return {
            'prompt': prompt,
            'response_a': candidates[0],
            'response_b': candidates[1]
        }
    
    def batch_collect(self, prompts: list, verbose: bool = True):
        """
        批量收集偏好数据
        
        Args:
            prompts: prompt列表
            verbose: 是否打印进度
        
        Returns:
            preference_data: 偏好数据列表
        """
        preference_data = []
        
        for i, prompt in enumerate(prompts):
            pair = self.create_preference_pair(prompt)
            # 实际应用中，这里需要人类标注员判断哪个更好
            # 这里简化为模拟数据
            pair['preference'] = 'a' if i % 2 == 0 else 'b'
            preference_data.append(pair)
            
            if verbose and (i + 1) % 10 == 0:
                print(f"已收集 {i+1}/{len(prompts)} 个偏好样本")
        
        return preference_data


if __name__ == "__main__":
    """
    演示人类反馈数据收集流程
    """
    from transformers import AutoModelForCausalLM
    
    # 加载模型
    model_name = "gpt2"
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
    # 创建收集器
    collector = HumanPreferenceCollector(model, tokenizer, num_candidates=2)
    
    # 定义标注任务prompts
    task_prompts = [
        "什么是人工智能？",
        "如何学习Python编程？",
        "解释一下机器学习的基本原理",
    ]
    
    # 收集偏好数据
    preference_data = collector.batch_collect(task_prompts, verbose=True)
    
    print(f"\n收集完成！共 {len(preference_data)} 条偏好数据")
    print(f"示例数据：{preference_data[0]}")


---

## 七、练习题

### 7.1 选择题

**1. RLHF的三阶段训练流程顺序正确的是？**
- A. 奖励模型 → PPO → SFT
- B. SFT → PPO → 奖励模型
- C. SFT → 奖励模型 → PPO
- D. PPO → SFT → 奖励模型

**2. Bradley-Terry模型的核心作用是？**
- A. 生成多样化的回复
- B. 预测人类偏好的概率
- C. 优化语言模型的参数
- D. 实现策略梯度更新

**3. PPO算法中裁剪（Clipping）机制的作用是？**
- A. 加速模型收敛
- B. 限制策略更新的幅度
- C. 减少计算量
- D. 提高生成多样性

**4. KL散度约束在RLHF中的主要作用是？**
- A. 提高奖励分数
- B. 确保策略不会过度偏离SFT模型
- C. 加速PPO训练
- D. 减少人类标注数据需求

**5. DPO相比PPO-RLHF的核心优势是？**
- A. 需要更多训练数据
- B. 训练更稳定，无需奖励模型
- C. 只能用于对话任务
- D. 必须使用人类标注数据

**6. KTO方法的核心心理学基础是？**
- A. 期望效用理论
- B. 损失厌恶（Kahneman-Tversky前景理论）
- C. 强化学习原理
- D. 对比学习理论

### 7.2 简答题

**1. 简述RLHF相比传统强化学习的优势，以及它为什么特别适合用于训练大语言模型。**

**2. 请解释Bradley-Terry模型的数学公式，以及它如何用于训练奖励模型。**

**3. 在RLHF的PPO阶段，为什么要使用KL散度约束？如果不添加KL约束会发生什么问题？**

**4. 描述RLHF在机器人具身智能中的一个具体应用场景，并说明如何设计人类偏好数据收集流程。**

### 7.3 编程题

**1. 实现一个简化的Bradley-Terry损失函数**，给定两个奖励张量 `r_winner` 和 `r_loser`，计算偏好损失。

**2. 实现一个KL散度计算函数**，给定两个概率分布 `p` 和 `q`（张量形式），计算它们的KL散度。

**3. 修改DPO训练代码**，添加一个 `evaluate` 方法，在验证集上计算偏好准确率。

---

## 八、参考答案

### 8.1 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | C | RLHF的标准流程是：先SFT获得基础能力，再训练奖励模型学习人类偏好，最后用PPO基于奖励模型优化策略。 |
| 2 | B | Bradley-Terry模型用于建模人类在成对选项中的选择概率，从而训练奖励模型预测偏好。 |
| 3 | B | PPO裁剪机制通过限制重要性比率的更新范围，防止策略在单步更新中变化过大导致性能崩溃。 |
| 4 | B | KL散度约束确保优化后的策略不会过度偏离参考的SFT模型，防止语言能力退化和奖励黑客。 |
| 5 | B | DPO的核心优势是训练更稳定，直接优化策略无需训练奖励模型，简化了训练流程。 |
| 6 | B | KTO基于Kahneman-Tversky前景理论，利用人类对损失比收益更敏感的心理特征设计损失函数。 |

### 8.2 简答题答案

**1. RLHF相比传统强化学习的优势：**

传统RL需要精确的奖励函数，但很多任务（如对话、写作）难以定义精确奖励；而且即便定义了奖励，智能体容易发现奖励函数的漏洞进行"作弊"。RLHF通过人类偏好来指导学习，不需要精确奖励函数，人类判断更难被欺骗。

RLHF特别适合大语言模型的原因：
- **对齐需求**：预训练模型能力很强但可能生成有害或无用内容，RLHF可以将人类价值观注入模型
- **偏好难以形式化**：判断一段文本"是否有帮助"没有精确标准，人类反馈是唯一可行的信号
- **规模化潜力**：奖励模型学习偏好后可以规模化评估，无需持续人类介入

**2. Bradley-Terry模型解释：**

Bradley-Terry模型假设两个选项A和B的潜在"真实"奖励为 $r_A$ 和 $r_B$，人类选择A的概率为：

$$P(A \succ B) = \frac{exp(r_A)}{exp(r_A) + exp(r_B)} = \frac{1}{1 + exp(r_B - r_A)}$$

训练奖励模型时，我们用神经网络 $r_\phi(\text{prompt}, \text{response})$ 逼近潜在奖励。对于偏好数据 $(\text{prompt}, y_A, y_B, \text{pref=A})$，损失函数为：

$$\mathcal{L} = -\log \sigma(r_\phi(\text{prompt}, y_A) - r_\phi(\text{prompt}, y_B))$$

这本质上是让奖励模型对偏好回复的打分高于被拒绝回复，差值越大损失越小。

**3. KL散度约束的作用：**

KL散度衡量当前策略 $\pi_\theta$ 与参考策略 $\pi_{\text{SFT}}$ 的差异。RLHF目标函数中加入KL惩罚：

$$\mathcal{L}_{\text{RLHF}} = r_\phi(x, y) - \beta \cdot \text{KL}(\pi_\theta \| \pi_{\text{SFT}})$$

如果不加KL约束，会发生：
- **语言崩坏**：模型可能生成语法奇怪但高奖励的文本
- **奖励黑客泛化**：模型可能发现奖励模型的"漏洞"，生成看似高分但实际无意义的文本
- **能力退化**：完全自由优化可能损害预训练语言模型已学到的语言能力和知识

**4. 机器人具身智能应用场景：**

以"人形机器人步态学习"为例：

- **任务**：让机器人学会自然、节能的行走步态
- **难点**："自然"难以量化，不同人可能有不同偏好
- **RLHF方案**：
  1. 让机器人用不同策略生成多条行走轨迹
  2. 让人类标注员比较轨迹，选择更自然的
  3. 训练奖励模型学习人类对步态的偏好
  4. 用PPO在奖励模型指导下优化步态策略

数据收集流程：
- 使用动作捕捉系统记录不同步态的关节角度序列
- 将轨迹可视化供人类标注员评判
- 收集至少1000对偏好数据进行训练

### 8.3 编程题答案

**1. Bradley-Terry损失函数实现：**

```python
import torch
import torch.nn.functional as F

def bradley_terry_loss(r_winner: torch.Tensor, r_loser: torch.Tensor) -> torch.Tensor:
    """
    计算Bradley-Terry偏好损失
    
    Args:
        r_winner: 偏好回复的奖励分数，shape: (batch_size,)
        r_loser: 被拒绝回复的奖励分数，shape: (batch_size,)
    Returns:
        loss: 标量损失
    """
    diff = r_winner - r_loser
    loss = -torch.log(torch.sigmoid(diff)).mean()
    return loss
```

**2. KL散度计算函数实现：**

```python
import torch
import torch.nn.functional as F

def kl_divergence(p: torch.Tensor, q: torch.Tensor, reduction: str = 'batchmean') -> torch.Tensor:
    """
    计算KL(p || q)
    
    KL(p || q) = sum_x p(x) * log(p(x) / q(x))
    
    Args:
        p: 第一个概率分布（目标），shape: (batch, ...)
        q: 第二个概率分布（参考），shape与p相同
        reduction: 'none' | 'batchmean' | 'sum' | 'mean'
    Returns:
        kl: KL散度
    """
    # 确保p是概率分布（归一化）
    p = p / p.sum(dim=-1, keepdim=True)
    q = q / q.sum(dim=-1, keepdim=True)
    
    # PyTorch的kl_div输入是log-probabilities
    kl = F.kl_div(q.log(), p, reduction=reduction)
    return kl
```

**3. DPO评估方法实现：**

```python
def evaluate(self, val_data, batch_size=8):
    """
    在验证集上计算DPO模型的偏好准确率
    
    Args:
        val_data: 验证数据集 [{'prompt':, 'chosen':, 'rejected':, 'preference':}, ...]
        batch_size: 批大小
    
    Returns:
        accuracy: 偏好预测准确率
    """
    self.policy_model.eval()
    device = next(self.policy_model.parameters()).device
    
    correct = 0
    total = 0
    
    for i in range(0, len(val_data), batch_size):
        batch = val_data[i:i+batch_size]
        
        chosen_texts = [d['prompt'] + self.tokenizer.eos_token + d['chosen'] for d in batch]
        rejected_texts = [d['prompt'] + self.tokenizer.eos_token + d['rejected'] for d in batch]
        
        chosen_enc = self.tokenizer(chosen_texts, truncation=True, 
                                    max_length=512, padding='max_length', return_tensors='pt')
        rejected_enc = self.tokenizer(rejected_texts, truncation=True,
                                      max_length=512, padding='max_length', return_tensors='pt')
        
        chosen_ids = chosen_enc['input_ids'].to(device)
        rejected_ids = rejected_enc['input_ids'].to(device)
        mask = chosen_enc['attention_mask'].to(device)
        
        with torch.no_grad():
            # 计算隐式奖励差异
            chosen_logps = self.get_sequence_log_probs(
                self.policy_model, chosen_ids, mask, chosen_ids
            )
            rejected_logps = self.get_sequence_log_probs(
                self.policy_model, rejected_ids, mask, rejected_ids
            )
            ref_chosen_logps = self.get_sequence_log_probs(
                self.ref_model, chosen_ids, mask, chosen_ids
            )
            ref_rejected_logps = self.get_sequence_log_probs(
                self.ref_model, rejected_ids, mask, rejected_ids
            )
            
            # 计算reward差异
            chosen_rewards = self.beta * (chosen_logps - ref_chosen_logps)
            rejected_rewards = self.beta * (rejected_logps - ref_rejected_logps)
            reward_diff = chosen_rewards - rejected_rewards
        
        # 预测：reward_diff > 0 表示chosen优于rejected
        predictions = (reward_diff > 0).cpu().tolist()
        
        for pred, d in zip(predictions, batch):
            if (pred and d['preference'] == 'chosen') or \
               (not pred and d['preference'] == 'rejected'):
                correct += 1
            total += 1
    
    accuracy = correct / total if total > 0 else 0.0
    return accuracy
```

---

## 本章小结

| 知识点 | 内容 |
|--------|------|
| **RLHF概述** | 三阶段管线：SFT → 奖励模型 → PPO强化学习 |
| **Bradley-Terry模型** | 将人类偏好转化为概率模型，用于训练奖励模型 |
| **PPO + KL约束** | 在优化奖励的同时防止策略偏离SFT太远 |
| **RLAIF** | 用AI反馈替代部分人类反馈，降低标注成本 |
| **DPO** | 直接偏好优化，无需奖励模型和PPO |
| **KTO** | 基于损失厌恶心理的优化方法 |
| **具身智能应用** | 机器人任务的人类偏好学习与安全约束RLHF |

---

> **课程总结**：本节介绍了RLHF（人类反馈强化学习）这一革命性技术，涵盖了三阶段训练流程、Bradley-Terry偏好模型、PPO+KL微调、以及DPO、KTO等新型方法，并探讨了其在具身智能领域的应用。掌握这些内容后，你将理解大语言模型对齐的核心技术原理。

*本章完 | 下一章：[14-6 强化学习调参与优化](14-6-强化学习调参与优化.md)*
