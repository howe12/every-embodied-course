# 14-4 RLHF 与人类反馈强化学习

**版本**: V1.0  
**作者**: Wendy | **课程系列**: ROS2机器人仿真与应用实践  
**适用对象**: 具备强化学习基础，希望理解并实现人类反馈强化学习的学员  
**前置知识**: 强化学习基础概念（策略梯度、PPO）、深度学习基础（神经网络、损失函数）

---

## 一、课程概述

传统的强化学习需要精心设计奖励函数，但这一要求在很多实际场景中难以满足：让机器人学会写作、对话或创作艺术，奖励信号该如何定义？人类反馈强化学习（Reinforcement Learning from Human Feedback，简称RLHF）提供了一种革命性的解决方案——用人类偏好代替精确奖励函数来指导智能体学习。

RLHF由OpenAI、DeepMind和Anthropic等机构在近年大力推广，是GPT-4、Claude、InstructGPT等大语言模型对齐（Alignment）的核心技术。它的核心思想是：不要求人类给出精确的奖励数值，只需要在两个候选输出之间选择更好的那个。这种"比大小"式的反馈远比精确打分容易获取，也更能捕捉人类的隐性偏好和价值观。

学完本章后，你将理解RLHF的三阶段训练流程（监督微调→奖励模型→PPO强化学习），掌握Bradley-Terry偏好模型的理论基础，并能在Python中实现完整的RLHF训练pipeline。

---

## 二、章节设计

本章分为三个核心模块，遵循"概念→原理→实现→实践"的递进逻辑：

**模块一：RLHF基础理论**  
从"为什么需要人类反馈"这一问题出发，介绍RLHF的发展历程，详解三阶段训练框架的每一步。

**模块二：核心技术详解**  
深入讲解奖励模型的设计与训练（Bradley-Terry模型）、PPO强化学习在RLHF中的特殊用法（KL散度约束），以及训练稳定性的关键技巧。

**模块三：代码实战**  
从零实现奖励模型、PPO训练循环，最终串联成完整的RLHF pipeline，并在文本生成任务上验证效果。

---

## 三、理论内容

### 3.1 RLHF概述

#### 3.1.1 什么是人类反馈强化学习

RLHF（Reinforcement Learning from Human Feedback，即人类反馈强化学习）是一种将人类偏好融入强化学习的技术框架。与传统RL依赖精确奖励函数不同，RLHF通过学习一个人类偏好模型（Reward Model）来替代手工设计的奖励函数。

RLHF的核心管线分为三个阶段：

1. **监督微调（SFT）**：在大规模预训练模型基础上，用高质量人工标注数据进行监督学习，获得一个具备基础能力的模型。
2. **奖励模型训练（RM）**：收集人类对成对输出的偏好数据，训练一个奖励模型来预测人类偏好。
3. **PPO强化学习**：使用奖励模型提供的信号，通过强化学习（通常是PPO算法）进一步优化策略模型。

整个流程中，最关键的创新是**不需要精确奖励**——人类只需要表达"我更喜欢A而不是B"，奖励模型就能学会如何评分。

#### 3.1.2 为什么需要人类反馈

传统强化学习面临的核心困难是**奖励设计（Reward Engineering）**：对于复杂任务（如写作质量、对话流畅性），精确奖励函数往往极难设计——我们很难用数学公式精确描述什么是"好的对话"。

即便我们能设计出奖励函数，也常常遇到**奖励黑客（Reward Hacking）**问题：智能体发现奖励函数的漏洞，通过非预期的手段获取高奖励，而实际任务性能却很差。典型的例子是游戏AI学会"卡bug"来得分，而非真正掌握游戏策略。

人类反馈则可以解决这些问题：

- **表达主观偏好**：人类可以自然地判断"这段回复更有帮助"，无需定义精确的奖励函数。
- **避免奖励黑客**：人类的判断基于整体质量，难以被单一维度的指标欺骗。
- **处理开放域任务**：对于没有明确正确答案的任务，人类反馈是唯一可行的指导信号。

#### 3.1.3 RLHF的发展历程

RLHF的发展历程可追溯至早期研究：

| 年份 | 工作 | 贡献 |
|------|------|------|
| 2017 | "Deep Reinforcement Learning from Human Preferences" (Christiano et al.) | 首次提出用人类偏好替代精确奖励的框架 |
| 2020 | InstructGPT / GPT-3 | 展示了RLHF在大语言模型对齐中的巨大威力 |
| 2022 | Constitutional AI (Anthropic) | 提出用AI反馈替代部分人类反馈（RLAIF） |
| 2022 | ChatGPT (OpenAI) | RLHF成为对话AI的核心技术 |
| 2023 | Llama 2 (Meta) | 开源模型中大规模应用RLHF |

值得注意的是，2022年Anthropic提出的**Constitutional AI（宪法AI）**在RLHF基础上更进一步：使用一组人类编写的"宪法原则"（如"不要提供有害信息"），让AI自我批评并修正输出，从而大幅减少对人类标注的依赖。

### 3.2 RLHF三阶段

#### 3.2.1 监督微调（Supervised Fine-Tuning, SFT）

SFT阶段的目标是将预训练模型（如GPT、LLaMA）转变为具备基础任务能力的模型。预训练模型的长项是预测"下一个token"，但这与"生成有帮助的回复"并不一致——预训练模型不知道什么是有帮助的，它只是在模仿训练文本的分布。

SFT通过监督学习解决这个问题：

$$\mathcal{L}_{\text{SFT}} = -\mathbb{E}_{(x,y)\sim D_{\text{SFT}}} \left[ \sum_{t=1}^{T} \log \pi_\theta(y_t \mid x, y_{<t}) \right]$$

其中 $x$ 是输入提示（Prompt），$y$ 是人工标注的高质量回复，$\pi_\theta$ 是模型策略。SFT让模型学会：给定一个用户问题，生成什么样的回复更可能得到人类认可。

SFT阶段的数据质量至关重要。典型做法是：由人类标注员针对多样化的提示写出高质量回复，覆盖各种任务类型（问答、写作、代码、对话等）。数据量通常在万到十万级别。

#### 3.2.2 奖励模型训练（Reward Modeling）

在SFT之后，我们有了一个"还算不错"的模型，但它的能力边界受限于人工标注的数量和质量。奖励模型阶段的目标是训练一个能够**预测人类偏好**的模型，从而可以规模化地评估任意输出的质量。

**成对偏好数据收集**：让同一个提示（Prompt）通过当前模型生成多个候选回复（如A和B），然后请人类标注员选择"哪个更好"。数据形如三元组：$(\text{prompt}, \text{response}_A, \text{response}_B)$，标注结果为"更喜欢A"或"更喜欢B"。

**奖励模型结构**：奖励模型通常是一个在SFT模型基础上改造的神经网络——将SFT模型的最后一个线性层替换为一个标量输出层（输出一个实数作为"奖励"）。输入相同提示和回复，输出一个奖励分数。

奖励模型的训练目标我们将在3.3节Bradley-Terry模型中详细介绍。训练完成后，奖励模型可以泛化到任意未见过的（prompt, response）对，给出人类可能给出的评分。

#### 3.2.3 PPO强化学习

获得奖励模型后，就可以进入强化学习阶段——使用奖励模型提供的信号，通过强化学习进一步优化策略模型。

这一阶段通常使用**PPO（Proximal Policy Optimization）**算法，原因在于PPO的裁剪机制能很好地控制策略更新的幅度，防止模型在优化过程中"跑偏"。

RLHF中的PPO与标准PPO有一个关键区别：**KL散度约束**。我们希望优化后的模型不要太偏离SFT模型——因为奖励模型虽然能评分，但它的偏好不一定完全正确，如果放任优化，模型可能"走火入魔"生成语法正确但内容荒谬的文本。

因此，RLHF-PPO的目标函数为：

$$\mathcal{L}_{\text{RLHF}} = \mathbb{E}_{x\sim D, y\sim\pi_\theta(\cdot|x)} \left[ r_\phi(x, y) - \beta \cdot \text{KL}(\pi_\theta(y|x) \| \pi_{\text{SFT}}(y|x)) \right]$$

其中 $r_\phi(x, y)$ 是奖励模型对输出 $y$ 的评分，$\beta$ 是KL惩罚系数，$\pi_{\text{SFT}}$ 是SFT阶段的参考模型。KL项确保策略不会过度偏离SFT，从而保持语言模型的基础能力。

### 3.3 奖励模型

#### 3.3.1 奖励模型设计

奖励模型的核心任务是：对于给定的输入（prompt）和输出（response），预测一个代表人类偏好程度的分数。

典型的奖励模型架构是**在Transformer语言模型顶部添加一个奖励头**：

- 基础网络：与SFT模型相同的Transformer（如LLaMA、GPT-2）
- 输入：[CLS] prompt [SEP] response [EOS]
- 输出：池化层（如取[CLS] token的表示）→ 线性层 → 标量奖励 $r$

这个设计使得奖励模型能够同时利用：
1. **prompt信息**：理解任务背景和约束
2. **response信息**：评估回复质量

奖励模型通常复用SFT模型的预训练权重作为初始化，这大幅加速了训练并提高了泛化能力。

#### 3.3.2 人类偏好收集

偏好数据的收集是RLHF中成本最高的环节，需要精心设计标注流程：

**标注任务设计**：标注员面对的是一个（prompt, response_A, response_B）三元组，需要判断哪个回复更好。有时还需要标注"好多少"（偏好强度），这可以用于训练带权重的偏好模型（如Bradley-Terry模型的扩展）。

**质量控制**：
- **交叉标注**：同一对样本由多个标注员独立标注，计算一致性指标
- **标注指南**：详细说明标注标准，确保标注员之间的判断一致性
- **争议样本复审**：对争议较大的样本进行专家复审

**数据规模**：InstructGPT使用的偏好数据约为数万个样本。虽然听起来不多，但这些数据需要覆盖足够多样的任务类型和回复风格，因此标注成本仍然很高。

#### 3.3.3 Bradley-Terry模型

Bradley-Terry模型是偏好建模的理论基石，源自统计学中用于分析竞技比赛和主观评分的经典模型。

假设给定一个prompt和两个候选回复A和B。Bradley-Terry模型假设人类选择A而非B的概率由下式给出：

$$P(A \succ B) = \frac{exp(r_A)}{exp(r_A) + exp(r_B)} = \frac{1}{1 + exp(r_B - r_A)}$$

其中 $r_A$ 和 $r_B$ 分别是回复A和回复B的潜在"真实"奖励（隐变量），$P(A \succ B)$ 是人类偏好A的实际概率。

如果我们用神经网络 $r_\phi(\text{prompt}, \text{response})$ 来逼近这个潜在奖励，那么训练奖励模型等价于拟合下面的对数似然：

$$\mathcal{L}_{\text{RM}} = -\mathbb{E}_{(\text{prompt}, y_A, y_B, \text{pref}) \sim D} \left[ \log \sigma \left( r_\phi(\text{prompt}, y_{\text{pref}}) - r_\phi(\text{prompt}, y_{\text{rejected}}) \right) \right]$$

其中 $\text{pref} \in \{A, B\}$ 表示人类偏好的回复，$\sigma$ 是sigmoid函数。这个损失函数的含义是：如果人类偏好A，那么我们希望 $r_\phi(\text{prompt}, A) > r_\phi(\text{prompt}, B)$，即让差值的sigmoid值接近1（对数似然接近0）。

直觉上理解：这个损失函数是一个**二元交叉熵损失**，将偏好问题转化为"A的奖励是否高于B"的二分类问题。

### 3.4 PPO算法

#### 3.4.1 PPO核心思想

PPO（Proximal Policy Optimization，近端策略优化）由OpenAI于2017年提出，是当前最流行的强化学习算法之一。PPO的核心设计哲学是：**小步快跑，避免大步跃迁**。

在策略优化中，如果一步更新过大，策略可能会"崩溃"——从良好性能跌落到很差。PPO通过在目标函数中引入裁剪（Clipping）机制，限制每次策略更新的幅度，从而兼顾样本效率和训练稳定性。

RLHF采用PPO的原因在于：
1. **适合大规模语言模型**：PPO是on-policy算法（虽然RLHF通过重要性采样做了近似off-policy处理），与语言模型的生成过程兼容性好。
2. **可控制的更新幅度**：KL散度约束 + PPO裁剪双重保险，确保策略不会剧烈偏离。
3. **成熟的工程实现**：OpenAI、DeepMind等已验证了PPO在大规模模型上的可行性。

#### 3.4.2 裁剪损失函数

标准PPO的裁剪目标函数定义为：

$$\mathcal{L}^{\text{CLIP}}(\theta) = \mathbb{E}_t \left[ \min \left( \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)} \hat{A}_t,\; \text{clip}\left(\frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)}, 1-\epsilon, 1+\epsilon\right) \hat{A}_t \right) \right]$$

其中：
- $\frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{\text{old}}}(a_t|s_t)}$ 是**重要性比率**（Probability Ratio），衡量新策略与旧策略在动作选择上的差异
- $\hat{A}_t$ 是优势函数（Advantage）的估计
- $\text{clip}(x, 1-\epsilon, 1+\epsilon)$ 将比率裁剪到 $[1-\epsilon, 1+\epsilon]$ 区间
- $\epsilon$ 是超参数，通常取 $0.1$ 或 $0.2$

裁剪的物理含义是：当重要性比率超出 $[1-\epsilon, 1+\epsilon]$ 范围时，就不再鼓励进一步增大或减小选择该动作的概率——即"到此为止，不要再优化了"。这防止了策略在单个更新步骤中变化过大。

#### 3.4.3 KL散度约束

KL散度（Kullback-Leibler Divergence）是衡量两个概率分布差异的度量。在RLHF中，KL散度约束是连接强化学习优化与语言模型能力的桥梁。

两个分布 $P$ 和 $Q$ 之间的KL散度定义为：

$$\text{KL}(P \| Q) = \mathbb{E}_{x\sim P} \left[ \log \frac{P(x)}{Q(x)} \right] = \sum_x P(x) \log \frac{P(x)}{Q(x)}$$

在RLHF中，我们用它来衡量当前策略 $\pi_\theta$ 与参考策略（通常是SFT模型）$\pi_{\text{SFT}}$ 之间的差异：

$$\text{KL}(\pi_\theta \| \pi_{\text{SFT}}) = \sum_y \pi_\theta(y|x) \log \frac{\pi_\theta(y|x)}{\pi_{\text{SFT}}(y|x)}$$

KL惩罚项的作用是双重的：
- **防止语言崩坏**：如果完全自由优化奖励，语言模型可能生成语法奇怪但高奖励的文本。KL约束强制模型保持语言能力。
- **防止奖励黑客变体**：即便奖励模型给出高评分，如果与参考模型的分布差异过大，KL惩罚会将其拉回。

实际工程中，$\beta$ 的取值需要权衡：过大（>0.1）会压制对奖励的优化，模型几乎不学习；过小（<0.01）则KL约束失效。InstructGPT中 $\beta$ 取0.03左右，这是一个经过大量实验验证的数值。

### 3.5 RLHF实践

#### 3.5.1 数据收集策略

高效的人类反馈数据收集是RLHF成功的关键。以下是实践中常用的策略：

**采样多样性**：为获得有信息量的偏好数据，不能只让模型生成一种回复。常用方法：
- 使用模型在不同温度下生成多个候选回复
- 使用不同的checkpoint（如训练早期、中期、晚期的模型）生成回复
- 使用不同的采样策略（如top-k、top-p）

**优先选择争议样本**：在多个模型生成的候选对中，优先选择那些**评估不确定性高**的样本让人类标注——如果两个回复差异明显，人类判断没有信息量；但如果两个回复质量接近，标注结果能最有效地训练奖励模型。

**渐进式数据收集**：InstructGPT的实践表明，不必一次性收集所有数据。可以先训练一个初步版本，用它生成新的候选回复，再请人类标注，形成数据收集→训练→新数据收集的迭代循环。

#### 3.5.2 训练稳定性

RLHF的训练稳定性是出了名的困难，以下是核心挑战和解决方案：

**挑战一：奖励模型过度自信**  
如果奖励模型在某些（prompt, response）对上训练得过于极端（奖励分数极高或极低），PPO阶段会出现"奖励黑客"现象——模型发现某些特定模式能稳定获得高奖励。

**解决方案**：对奖励模型进行正则化；在PPO训练中对奖励进行归一化（减均值、除标准差）；在奖励函数中添加KL项的直接惩罚。

**挑战二：KL散度爆炸**  
训练初期PPO可能产生与参考模型差异极大的输出，导致KL项爆炸式增长。

**解决方案**：使用**自适应KL目标**——当实际KL超过目标值时加大惩罚系数；设置KL的硬上限，超出则拒绝更新。

**挑战三：训练早期振荡**  
PPO在奖励模型信号过强时会产生剧烈振荡。

**解决方案**：使用**价值函数（Value Function）**估计回报，降低优势函数的方差；在PPO损失中添加**值函数损失（Value Loss）**项；对奖励进行打折和归一化处理。

#### 3.5.3 常见问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 模型输出变得冗长/重复 | 奖励模型偏向长回复 | 在奖励中添加长度惩罚；对偏好数据进行长度归一化 |
| 奖励黑客：模型"作弊" | 奖励模型泛化不足 | 增强奖励模型训练数据多样性；添加KL硬约束 |
| KL散度无法控制 | β系数不合适或PPO学习率过高 | 调整β；使用自适应KL目标；降低学习率 |
| 训练崩溃（NaN） | 奖励值范围过大 | 对奖励进行裁剪；梯度裁剪（Gradient Clipping） |
| 语言能力退化 | KL惩罚过强 | 降低β；延长SFT阶段训练时间 |
| 偏好数据标注不一致 | 标注员理解差异 | 详细标注指南；交叉标注；一致性审查 |

---

## 四、代码实战

### 4.1 奖励模型实现

下面实现一个基于LLaMA的奖励模型，核心是将语言模型的输出映射为一个标量奖励分数。

```python
import torch
import torch.nn as nn
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
        # 投影层：将模型输出映射为标量奖励
        # 对于GPT-2，使用最后一个隐藏状态的第一个token（类似[CLS]）作为表示
        hidden_size = self.model.config.n_embd
        self.reward_head = nn.Linear(hidden_size, 1, bias=False)
        
        # 初始化奖励头的权重为零（参考InstructGPT实践）
        # 这样初始化时奖励模型输出接近零，便于后续学习
        nn.init.zeros_(self.reward_head.weight)
    
    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor = None):
        """
        前向传播
        Args:
            input_ids: 输入token序列，shape: (batch_size, seq_len)
            attention_mask: 注意力掩码，shape: (batch_size, seq_len)
        Returns:
            rewards: 标量奖励分数，shape: (batch_size,)
        """
        # 获取模型最后一层的隐藏状态
        outputs = self.model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True
        )
        # 取最后一个token的隐藏状态作为句子表示
        last_hidden_state = outputs.last_hidden_state  # (batch, seq_len, hidden)
        # 取序列最后一个有效token（通常对应[SEP]或[EOS]位置）
        # 这里用attention_mask找到最后一个有效位置
        sequence_lengths = attention_mask.long().sum(dim=1) - 1  # 最后一个位置是padding
        batch_indices = torch.arange(last_hidden_state.size(0), device=last_hidden_state.device)
        # gather获取每个样本最后一个有效token的隐藏状态
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
        # 等价于对数损失：-log(sigmoid(r_winner - r_loser))
        diff = r_winner - r_loser  # shape: (batch,)
        loss = -torch.log(torch.sigmoid(diff)).mean()
        return loss


def train_reward_model(
    reward_model,
    preference_data,
    tokenizer,
    epochs: int = 3,
    lr: float = 1e-5,
    batch_size: int = 8
):
    """
    训练奖励模型
    
    Args:
        reward_model: RewardModel实例
        preference_data: 偏好数据集，格式为：
            [{'prompt': str, 'chosen': str, 'rejected': str}, ...]
        tokenizer: 分词器
        epochs: 训练轮数
        lr: 学习率
        batch_size: 批大小
    """
    optimizer = torch.optim.AdamW(reward_model.parameters(), lr=lr)
    criterion = BradleyTerryLoss()
    reward_model.train()
    
    dataset_size = len(preference_data)
    num_batches = dataset_size // batch_size
    
    for epoch in range(epochs):
        total_loss = 0.0
        indices = torch.randperm(dataset_size)  # 打乱数据
        
        for i in range(num_batches):
            batch_indices = indices[i * batch_size : (i + 1) * batch_size]
            
            # 获取当前batch的prompt和response
            prompts = [preference_data[idx]['prompt'] for idx in batch_indices]
            chosen_responses = [preference_data[idx]['chosen'] for idx in batch_indices]
            rejected_responses = [preference_data[idx]['rejected'] for idx in batch_indices]
            
            # 编码chosen和rejected responses
            chosen_encodings = tokenizer(
                [p + tokenizer.sep_token + c for p, c in zip(prompts, chosen_responses)],
                truncation=True,
                max_length=512,
                padding='max_length',
                return_tensors='pt'
            )
            rejected_encodings = tokenizer(
                [p + tokenizer.sep_token + r for p, r in zip(prompts, rejected_responses)],
                truncation=True,
                max_length=512,
                padding='max_length',
                return_tensors='pt'
            )
            
            # 前向传播：分别计算chosen和rejected的奖励
            r_chosen = reward_model(
                chosen_encodings['input_ids'],
                chosen_encodings['attention_mask']
            )
            r_rejected = reward_model(
                rejected_encodings['input_ids'],
                rejected_encodings['attention_mask']
            )
            
            # 计算Bradley-Terry损失
            loss = criterion(r_chosen, r_rejected)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(reward_model.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_loss = total_loss / num_batches
        print(f"Epoch {epoch+1}/{epochs}, Average Loss: {avg_loss:.4f}")
    
    return reward_model
```

### 4.2 PPO训练循环

下面实现RLHF中的PPO训练循环，这是三阶段中最复杂的部分。

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class PPOTrainer:
    """
    PPO训练器，用于RLHF的强化学习阶段
    核心思想：通过KL约束确保策略不会过度偏离参考模型
    """
    
    def __init__(
        self,
        policy_model,          # 当前策略模型（需要优化的模型）
        ref_model,             # 参考模型（SFT模型，不优化）
        reward_model,          # 奖励模型（用于评分）
        tokenizer,             # 分词器
        kl_coef: float = 0.03, # KL惩罚系数 beta
        clip_eps: float = 0.2, # PPO裁剪参数 epsilon
        gamma: float = 1.0,    # 折扣因子
        lambd: float = 0.95,   # GAE参数
        learning_rate: float = 1e-5,
    ):
        self.policy_model = policy_model
        self.ref_model = ref_model
        self.reward_model = reward_model
        self.tokenizer = tokenizer
        self.kl_coef = kl_coef
        self.clip_eps = clip_eps
        self.gamma = gamma
        self.lambd = lambd
        
        # 优化器：只优化策略模型
        self.optimizer = torch.optim.AdamW(
            policy_model.parameters(), 
            lr=learning_rate
        )
    
    def generate_responses(self, prompts, max_new_tokens=100, temperature=0.7):
        """
        使用当前策略模型生成回复
        """
        self.policy_model.eval()
        all_responses = []
        
        for prompt in prompts:
            encoded = self.tokenizer(
                prompt,
                return_tensors='pt',
                truncation=True,
                max_length=256
            ).to(self.policy_model.device)
            
            with torch.no_grad():
                generated_ids = self.policy_model.generate(
                    **encoded,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=temperature,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            
            # 去掉prompt部分，只保留生成的回复
            prompt_len = encoded['input_ids'].shape[1]
            response_ids = generated_ids[0][prompt_len:]
            response = self.tokenizer.decode(response_ids, skip_special_tokens=True)
            all_responses.append(response)
        
        return all_responses
    
    def compute_rewards(self, prompts, responses):
        """
        使用奖励模型计算每个样本的奖励
        """
        self.reward_model.eval()
        rewards = []
        
        for prompt, response in zip(prompts, responses):
            # 将prompt和response拼接后编码
            text = prompt + self.tokenizer.sep_token + response
            encoded = self.tokenizer(
                text,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            ).to(self.policy_model.device)
            
            with torch.no_grad():
                r = self.reward_model(
                    encoded['input_ids'],
                    encoded['attention_mask']
                )
            rewards.append(r.item())
        
        return torch.tensor(rewards, device=self.policy_model.device)
    
    def compute_kl_penalty(self, input_ids, attention_mask):
        """
        计算KL散度惩罚项
        
        KL(π_policy || π_ref) = sum_y π_policy(y|x) * log(π_policy(y|x) / π_ref(y|x))
        """
        # 策略模型输出
        policy_logits = self.policy_model(input_ids, attention_mask=attention_mask).logits
        
        # 参考模型输出（不更新梯度）
        with torch.no_grad():
            ref_logits = self.ref_model(input_ids, attention_mask=attention_mask).logits
        
        # 计算log概率
        policy_log_probs = F.log_softmax(policy_logits, dim=-1)
        ref_log_probs = F.log_softmax(ref_logits, dim=-1)
        
        # KL散度 = sum p * (log(p) - log(q))
        kl_div = torch.exp(ref_log_probs) * (policy_log_probs - ref_log_probs)
        # 对vocab维度求和，对序列维度求平均
        kl_per_token = kl_div.sum(dim=-1)  # (batch, seq_len)
        
        # 只考虑有效token位置（忽略padding）
        valid_mask = attention_mask.float()
        kl_penalty = (kl_per_token * valid_mask).sum(dim=-1) / valid_mask.sum(dim=-1)
        
        return kl_penalty  # (batch,)
    
    def gae_advantages(self, rewards, gamma=1.0, lambd=0.95):
        """
        计算GAE(Generalized Advantage Estimation)优势估计
        
        GAE公式：
        A_t = sum_{l=0}^{T-t-1} (gamma * lambda)^l * delta_{t+l}
        其中 delta_t = r_t + gamma * V(s_{t+1}) - V(s_t)
        """
        T = len(rewards)
        advantages = np.zeros(T)
        last_gae = 0
        
        # 使用奖励的移动平均作为价值基线
        baseline = rewards.mean().item()
        
        # 反向计算GAE
        for t in reversed(range(T)):
            if t == T - 1:
                next_value = 0  # 终止状态
            else:
                next_value = rewards[t + 1].item()
            
            delta = rewards[t].item() + gamma * next_value - baseline
            last_gae = delta + gamma * lambd * last_gae
            advantages[t] = last_gae
        
        return torch.tensor(advantages, dtype=torch.float32, device=rewards.device)
    
    def train_step(self, prompts, responses, old_log_probs):
        """
        执行一次PPO训练步骤
        
        Args:
            prompts: 输入提示列表
            responses: 生成的回复列表
            old_log_probs: 旧策略的log概率，用于重要性采样
        
        Returns:
            stats: 训练统计信息字典
        """
        # 1. 编码prompt+response
        texts = [p + self.tokenizer.sep_token + r for p, r in zip(prompts, responses)]
        encodings = self.tokenizer(
            texts,
            truncation=True,
            max_length=512,
            padding='max_length',
            return_tensors='pt'
        )
        input_ids = encodings['input_ids'].to(self.policy_model.device)
        attention_mask = encodings['attention_mask'].to(self.policy_model.device)
        
        # 2. 计算奖励
        rewards = self.compute_rewards(prompts, responses)
        
        # 3. 计算KL惩罚
        kl_penalty = self.compute_kl_penalty(input_ids, attention_mask)
        
        # 4. 计算GAE优势
        advantages = self.gae_advantages(rewards, self.gamma, self.lambd)
        
        # 5. 获取当前策略的log概率
        self.policy_model.train()
        logits = self.policy_model(input_ids, attention_mask=attention_mask).logits
        log_probs = F.log_softmax(logits, dim=-1)
        
        # 计算序列平均log概率（用于重要性采样）
        valid_mask = attention_mask.float()
        seq_log_probs = (log_probs * valid_mask.unsqueeze(-1)).sum(dim=-2) / valid_mask.sum(dim=-1, keepdim=True)
        seq_log_probs = seq_log_probs.squeeze(-1)  # (batch,)
        
        # 6. 计算PPO裁剪损失
        # 重要性比率
        ratio = torch.exp(seq_log_probs - old_log_probs.to(seq_log_probs.device))
        
        # 裁剪
        clipped_ratio = torch.clamp(ratio, 1 - self.clip_eps, 1 + self.clip_eps)
        
        # 优势函数
        advantages_expanded = advantages.unsqueeze(-1).expand_as(ratio)
        
        # PPO裁剪目标
        surr1 = ratio * advantages_expanded
        surr2 = clipped_ratio * advantages_expanded
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # 7. KL惩罚项
        kl_loss = kl_penalty.mean()
        
        # 8. 总损失 = PPO损失 + beta * KL损失
        # 注意：KL项在RLHF目标中是从奖励中减去的，这里合并到损失中
        total_loss = policy_loss + self.kl_coef * kl_loss
        
        # 9. 反向传播
        self.optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_model.parameters(), max_norm=1.0)
        self.optimizer.step()
        
        return {
            'total_loss': total_loss.item(),
            'policy_loss': policy_loss.item(),
            'kl_loss': kl_loss.item(),
            'mean_reward': rewards.mean().item(),
            'mean_kl': kl_penalty.mean().item()
        }


def run_ppo_training(
    ppo_trainer,
    prompts,
    num_episodes: int = 100,
    ppo_epochs: int = 4,
    num_rollouts: int = 32,
):
    """
    运行完整的PPO训练循环
    
    Args:
        ppo_trainer: PPOTrainer实例
        prompts: 训练用的提示列表
        num_episodes: 训练轮数
        ppo_epochs: 每批数据上PPO更新的轮数
        num_rollouts: 每次收集的样本数量
    """
    training_stats = []
    
    for episode in range(num_episodes):
        # 1. 采样一批prompts
        sample_indices = np.random.choice(len(prompts), min(num_rollouts, len(prompts)), replace=False)
        batch_prompts = [prompts[i] for i in sample_indices]
        
        # 2. 使用当前策略生成回复
        responses = ppo_trainer.generate_responses(batch_prompts)
        
        # 3. 计算old_log_probs（在更新前获取）
        old_log_probs_list = []
        ppo_trainer.policy_model.eval()
        with torch.no_grad():
            for prompt, response in zip(batch_prompts, responses):
                text = prompt + ppo_trainer.tokenizer.sep_token + response
                encoded = ppo_trainer.tokenizer(
                    text,
                    truncation=True,
                    max_length=512,
                    return_tensors='pt'
                ).to(ppo_trainer.policy_model.device)
                
                logits = ppo_trainer.policy_model(**encoded).logits
                log_probs = F.log_softmax(logits, dim=-1)
                valid_mask = encoded['attention_mask'].float()
                seq_log_probs = (log_probs * valid_mask.unsqueeze(-1)).sum(dim=-2) / valid_mask.sum(dim=-1)
                old_log_probs_list.append(seq_log_probs.mean().item())
        
        old_log_probs = torch.tensor(old_log_probs_list)
        
        # 4. 执行多轮PPO更新
        for _ in range(ppo_epochs):
            stats = ppo_trainer.train_step(batch_prompts, responses, old_log_probs)
        
        training_stats.append(stats)
        
        # 每10个episode打印一次统计信息
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean([s['mean_reward'] for s in training_stats[-10:]])
            avg_kl = np.mean([s['mean_kl'] for s in training_stats[-10:]])
            print(f"Episode {episode+1}/{num_episodes} | "
                  f"Avg Reward: {avg_reward:.3f} | "
                  f"Avg KL: {avg_kl:.5f}")
    
    return training_stats
```

### 4.3 RLHF完整Pipeline

下面将三个阶段串联起来，实现一个完整的RLHF训练流程：

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

class RLHFPipeline:
    """
    完整的RLHF训练流程
    包含三个阶段：SFT监督微调 -> 奖励模型训练 -> PPO强化学习
    """
    
    def __init__(self, model_name: str = "gpt2"):
        self.model_name = model_name
        print(f"Initializing RLHF Pipeline with model: {model_name}")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 初始化SFT模型
        self.sft_model = AutoModelForCausalLM.from_pretrained(model_name)
        self.ref_model = AutoModelForCausalLM.from_pretrained(model_name)
        # 冻结参考模型（SFT模型不参与优化）
        self.ref_model.eval()
        for param in self.ref_model.parameters():
            param.requires_grad = False
    
    def stage1_sft(self, sft_data, epochs=3, lr=2e-5, batch_size=4):
        """
        阶段1：监督微调（Supervised Fine-Tuning）
        
        使用高质量人工标注数据对预训练模型进行监督学习
        数据格式：[(prompt, response), ...]
        """
        self.sft_model.train()
        optimizer = torch.optim.AdamW(self.sft_model.parameters(), lr=lr)
        
        dataset_size = len(sft_data)
        num_batches = dataset_size // batch_size
        
        for epoch in range(epochs):
            total_loss = 0.0
            indices = torch.randperm(dataset_size)
            
            for i in range(num_batches):
                batch_indices = indices[i * batch_size : (i + 1) * batch_size]
                batch_prompts = [sft_data[idx][0] for idx in batch_indices]
                batch_responses = [sft_data[idx][1] for idx in batch_indices]
                
                # 编码prompt和response（用EOS连接）
                texts = [p + self.tokenizer.eos_token + r for p, r in zip(batch_prompts, batch_responses)]
                encodings = self.tokenizer(
                    texts,
                    truncation=True,
                    max_length=512,
                    padding='max_length',
                    return_tensors='pt'
                )
                
                # 前向传播（使用label=input_ids计算语言模型损失）
                outputs = self.sft_model(
                    input_ids=encodings['input_ids'],
                    attention_mask=encodings['attention_mask'],
                    labels=encodings['input_ids']
                )
                loss = outputs.loss
                
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.sft_model.parameters(), max_norm=1.0)
                optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / num_batches
            print(f"[SFT] Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.4f}")
        
        # 更新参考模型为当前SFT模型
        self.ref_model.load_state_dict(self.sft_model.state_dict())
        return self.sft_model
    
    def stage2_reward_model(self, preference_data, epochs=3, lr=1e-5, batch_size=8):
        """
        阶段2：训练奖励模型
        
        使用偏好数据训练一个能预测人类偏好的奖励模型
        preference_data格式：[{prompt, chosen, rejected}, ...]
        """
        from .reward_model import RewardModel, train_reward_model
        
        # 初始化奖励模型（基于SFT模型）
        self.reward_model = RewardModel(model_name=self.model_name)
        self.reward_model.to(self.sft_model.device)
        
        # 训练奖励模型
        self.reward_model = train_reward_model(
            self.reward_model,
            preference_data,
            self.tokenizer,
            epochs=epochs,
            lr=lr,
            batch_size=batch_size
        )
        return self.reward_model
    
    def stage3_ppo(self, prompts, num_episodes=100, ppo_epochs=4, num_rollouts=32):
        """
        阶段3：PPO强化学习优化
        
        使用奖励模型提供的信号，通过PPO算法优化策略模型
        """
        from .ppo_trainer import PPOTrainer, run_ppo_training
        
        # 初始化PPO训练器
        ppo_trainer = PPOTrainer(
            policy_model=self.sft_model,
            ref_model=self.ref_model,
            reward_model=self.reward_model,
            tokenizer=self.tokenizer,
            kl_coef=0.03,
            clip_eps=0.2,
            learning_rate=1e-5
        )
        
        # 运行PPO训练
        stats = run_ppo_training(
            ppo_trainer=ppo_trainer,
            prompts=prompts,
            num_episodes=num_episodes,
            ppo_epochs=ppo_epochs,
            num_rollouts=num_rollouts
        )
        return stats
    
    def train(self, sft_data, preference_data, prompts, 
               sft_epochs=3, rm_epochs=3, ppo_episodes=100):
        """
        完整的RLHF训练流程
        
        Args:
            sft_data: SFT训练数据 [(prompt, response), ...]
            preference_data: 偏好数据 [{prompt, chosen, rejected}, ...]
            prompts: PPO阶段使用的提示列表
            sft_epochs: SFT训练轮数
            rm_epochs: 奖励模型训练轮数
            ppo_episodes: PPO训练轮数
        """
        print("=" * 60)
        print("Stage 1: Supervised Fine-Tuning (SFT)")
        print("=" * 60)
        self.stage1_sft(sft_data, epochs=sft_epochs)
        
        print("\n" + "=" * 60)
        print("Stage 2: Reward Model Training")
        print("=" * 60)
        self.stage2_reward_model(preference_data, epochs=rm_epochs)
        
        print("\n" + "=" * 60)
        print("Stage 3: PPO Reinforcement Learning")
        print("=" * 60)
        ppo_stats = self.stage3_ppo(prompts, num_episodes=ppo_episodes)
        
        print("\n" + "=" * 60)
        print("RLHF Training Complete!")
        print("=" * 60)
        return ppo_stats
    
    def generate(self, prompt, max_new_tokens=100, temperature=0.7):
        """
        使用训练好的模型生成回复
        """
        self.sft_model.eval()
        encoded = self.tokenizer(prompt, return_tensors='pt').to(self.sft_model.device)
        
        with torch.no_grad():
            generated_ids = self.sft_model.generate(
                **encoded,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=0.9
            )
        
        response = self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        return response


def demo():
    """
    演示RLHF完整训练流程（使用小规模数据）
    """
    # 初始化pipeline
    pipeline = RLHFPipeline(model_name="gpt2")
    
    # 准备数据（实际应用中需要真实的人类标注数据）
    sft_data = [
        ("什么是机器人？", "机器人是一种能够自主执行任务的机械或虚拟智能体。"),
        ("解释一下强化学习", "强化学习是一种通过与环境交互来学习最优策略的机器学习方法。"),
        ("Python是什么？", "Python是一种高级编程语言，以简洁易读著称。"),
    ]
    
    preference_data = [
        {"prompt": "什么是人工智能？", "chosen": "人工智能是计算机科学的一个分支，致力于创造智能机器。", "rejected": "AI就是AI啊。"},
        {"prompt": "如何学习编程？", "chosen": "学习编程建议从Python开始，多动手实践。", "rejected": "不学。"},
    ]
    
    prompts = [
        "什么是深度学习？",
        "解释一下神经网络",
        "机器学习和人工智能有什么区别？",
    ]
    
    # 执行完整训练（简化版本，跳过实际耗时的训练）
    print("Running RLHF demo (training skipped for demo)...")
    response = pipeline.generate("解释一下大语言模型")
    print(f"Generated response: {response}")


if __name__ == "__main__":
    demo()
```

---

## 五、练习题

### 5.1 选择题

1. **RLHF的三阶段训练流程顺序正确的是？**
   - A. 奖励模型 → PPO → SFT
   - B. SFT → PPO → 奖励模型
   - C. SFT → 奖励模型 → PPO
   - D. PPO → SFT → 奖励模型

2. **Bradley-Terry模型的核心作用是？**
   - A. 生成多样化的回复
   - B. 预测人类偏好的概率
   - C. 优化语言模型的参数
   - D. 实现策略梯度更新

3. **PPO算法中裁剪（Clipping）机制的作用是？**
   - A. 加速模型收敛
   - B. 限制策略更新的幅度
   - C. 减少计算量
   - D. 提高生成多样性

4. **KL散度约束在RLHF中的主要作用是？**
   - A. 提高奖励分数
   - B. 确保策略不会过度偏离SFT模型
   - C. 加速PPO训练
   - D. 减少人类标注数据需求

5. **以下哪个不是RLHF面临的常见问题？**
   - A. 奖励黑客（Reward Hacking）
   - B. KL散度爆炸
   - C. 语言能力退化
   - D. 模型过拟合训练数据

### 5.2 简答题

1. **简述RLHF相比传统强化学习的优势，以及它为什么特别适合用于训练大语言模型。**

2. **请解释Bradley-Terry模型的数学公式，以及它如何用于训练奖励模型。**

3. **在RLHF的PPO阶段，为什么要使用KL散度约束？如果不添加KL约束会发生什么问题？**

4. **假设你正在训练一个对话AI，请描述你将如何设计数据收集策略来获取高质量的偏好数据。**

### 5.3 编程题

1. **实现一个简化的Bradley-Terry损失函数**，给定两个奖励张量 `r_winner` 和 `r_loser`，计算偏好损失。

2. **实现一个KL散度计算函数**，给定两个概率分布 `p` 和 `q`（张量形式），计算它们的KL散度。

3. **修改RLHFPipeline代码**，添加一个 `stage2_rm_with_baseline` 方法，使用带基准线的奖励模型训练方法（参考InstructGPT的做法）。

---

## 六、答案

### 6.1 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | C | RLHF的标准流程是：先SFT获得基础能力，再训练奖励模型学习人类偏好，最后用PPO基于奖励模型优化策略。 |
| 2 | B | Bradley-Terry模型用于建模人类在成对选项中的选择概率，从而训练奖励模型预测偏好。 |
| 3 | B | PPO裁剪机制通过限制重要性比率的更新范围，防止策略在单步更新中变化过大导致性能崩溃。 |
| 4 | B | KL散度约束确保优化后的策略不会过度偏离参考的SFT模型，防止语言能力退化和奖励黑客。 |
| 5 | D | 模型过拟合训练数据是通用机器学习问题，不是RLHF特有的；前三个都是RLHF训练中的典型问题。 |

### 6.2 简答题答案

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
- **语言崩坏**：模型可能生成语法奇怪但高奖励的文本，因为奖励模型可能过度关注某些pattern
- **奖励黑客泛化**：模型可能发现奖励模型的"漏洞"，生成看似高分但实际无意义的文本
- **能力退化**：完全自由优化可能损害预训练语言模型已学到的语言能力和知识

**4. 对话AI的偏好数据收集策略：**

- **多样性采样**：使用不同温度、不同的模型checkpoint生成多个候选回复
- **任务覆盖**：覆盖多种对话类型（问答、闲聊、推理、写作等），确保奖励模型泛化
- **争议优先**：优先让人类标注员评估质量接近的候选对，因为差异明显的样本信息量少
- **渐进式收集**：先训练一个基础奖励模型，用它生成新的候选对，再进行下一轮标注
- **一致性控制**：使用交叉标注计算标注员一致性，争议大的样本进行专家复审

### 6.3 编程题答案

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
    # 计算奖励差值
    diff = r_winner - r_loser
    # P(A > B) = sigmoid(r_A - r_B)
    # 损失 = -log(P(偏好 > 被拒绝))
    loss = -F.logsigmoid(diff).mean()
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
        p: 第一个概率分布（目标），shape可以是任意的概率分布
        q: 第二个概率分布（参考），shape与p相同
        reduction: 'none' | 'batchmean' | 'sum' | 'mean'
    Returns:
        kl: KL散度
    """
    # 确保p是概率分布（归一化）
    p = p / p.sum(dim=-1, keepdim=True)
    q = q / q.sum(dim=-1, keepdim=True)
    
    # 计算KL散度: KL(p||q) = p * (log(p) - log(q))
    kl = F.kl_div(q.log(), p, reduction=reduction)
    return kl


# 更简洁的用法（推荐）：
# PyTorch内置了kl_div，注意输入是log-probabilities
# torch.nn.functional.kl_div(q.log(), p, reduction='batchmean')
```

**3. 带基准线的奖励模型训练（参考答案）：**

```python
def stage2_rm_with_baseline(self, preference_data, epochs=3, lr=1e-5, batch_size=8, baseline_type='exponential'):
    """
    带基准线的奖励模型训练
    
    baseline的作用是减少奖励的方差，使训练更稳定
    baseline = E[r]（所有奖励的期望）
    
    实际优化目标变为：r - baseline
    这样即使绝对奖励值很大，只要相对排序正确，梯度就是合理的
    """
    from .reward_model import RewardModel, train_reward_model
    
    self.reward_model = RewardModel(model_name=self.model_name)
    self.reward_model.to(self.sft_model.device)
    
    optimizer = torch.optim.AdamW(self.reward_model.parameters(), lr=lr)
    criterion = BradleyTerryLoss()
    self.reward_model.train()
    
    dataset_size = len(preference_data)
    
    # 维护一个移动平均的基准线
    baseline = 0.0
    baseline_decay = 0.99  # 基准线衰减系数
    
    for epoch in range(epochs):
        total_loss = 0.0
        indices = torch.randperm(dataset_size)
        num_batches = dataset_size // batch_size
        
        for i in range(num_batches):
            batch_indices = indices[i * batch_size : (i + 1) * batch_size]
            batch_data = [preference_data[idx] for idx in batch_indices]
            
            # 编码chosen和rejected
            chosen_texts = [d['prompt'] + self.tokenizer.sep_token + d['chosen'] 
                           for d in batch_data]
            rejected_texts = [d['prompt'] + self.tokenizer.sep_token + d['rejected'] 
                             for d in batch_data]
            
            chosen_enc = self.tokenizer(chosen_texts, truncation=True, 
                                        max_length=512, padding='max_length', return_tensors='pt')
            rejected_enc = self.tokenizer(rejected_texts, truncation=True,
                                           max_length=512, padding='max_length', return_tensors='pt')
            
            r_chosen = self.reward_model(chosen_enc['input_ids'], chosen_enc['attention_mask'])
            r_rejected = self.reward_model(rejected_enc['input_ids'], rejected_enc['attention_mask'])
            
            # 更新基准线（指数移动平均）
            all_rewards = torch.cat([r_chosen, r_rejected])
            baseline = baseline_decay * baseline + (1 - baseline_decay) * all_rewards.mean().item()
            
            # 减去基准线后再计算损失
            r_chosen_centered = r_chosen - baseline
            r_rejected_centered = r_rejected - baseline
            
            loss = criterion(r_chosen_centered, r_rejected_centered)
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.reward_model.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"[RM with Baseline] Epoch {epoch+1}/{epochs}, Loss: {total_loss/num_batches:.4f}, Baseline: {baseline:.4f}")
    
    return self.reward_model
```

---

## 七、总结

本章我们系统学习了RLHF（人类反馈强化学习）这一革命性技术：

**核心流程**：RLHF通过三阶段管线将人类偏好注入大语言模型——SFT建立基础能力，奖励模型学习人类偏好，PPO基于偏好信号优化策略。

**理论基础**：Bradley-Terry模型提供了偏好建模的统计框架，将"哪个更好"的主观判断转化为概率模型；PPO的裁剪机制和KL散度约束共同保证了训练稳定性。

**工程实践**：RLHF的成功依赖高质量的偏好数据收集、合理的超参数设置（如KL系数β）和训练稳定性技巧（梯度裁剪、奖励归一化等）。

RLHF不仅是训练有用AI的核心技术，其思想也深刻影响了AI alignment研究的走向——从纯人类反馈到Constitutional AI的AI自我改进，未来RLHF将继续演进，而理解其原理是参与这一领域的基础。