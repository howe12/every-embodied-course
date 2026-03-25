# 13-1 大模型技术概述（基础概念与Transformer架构）

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 13-1 |
| 课程名称 | 大模型技术概述（基础概念与Transformer架构） |
| 所属模块 | 13-大模型技术与应用 |
| 难度等级 | ⭐⭐⭐☆☆ |
| 预计学时 | 4小时 |
| 前置知识 | Python基础、线性代数基础、神经网络基础 |

---

## 目录

1. [大模型（LLM）定义与发展历程](#1-大模型llm定义与发展历程)
2. [Transformer 架构详解](#2-transformer-架构详解)
3. [预训练与微调](#3-预训练与微调)
4. [主流大模型介绍](#4-主流大模型介绍)
5. [代码实战：实现Transformer与注意力机制](#5-代码实战实现transformer与注意力机制)
6. [练习题](#6-练习题)
7. [参考答案](#7-参考答案)

---

## 1. 大模型（LLM）定义与发展历程

### 1.1 什么是大语言模型

**大语言模型**（Large Language Model，LLM）是一类基于深度学习的自然语言处理模型，通过在大规模文本语料上进行预训练，学习语言的统计规律和语义表示，能够完成文本生成、问答、翻译、摘要等多种语言任务。

LLM的核心特征：

- **大规模参数**：通常拥有数十亿到数千亿个参数
- **大规模预训练**：在海量文本数据上进行无监督学习
- **涌现能力**：表现出小模型不具备的复杂推理能力
- **通用性**：通过少量示例或提示即可适配多种任务

### 1.2 语言模型基础

语言模型（Language Model）的核心任务是计算一个句子出现的概率：

$$P(w_1, w_2, ..., w_n) = \prod_{i=1}^{n} P(w_i | w_1, w_2, ..., w_{i-1})$$

即根据前文预测下一个词的概率。

**N-gram模型**是统计语言模型的基础，通过滑动窗口限制上下文长度：

$$P(w_i | w_1, ..., w_{i-1}) \approx P(w_i | w_{i-n+1}, ..., w_{i-1})$$

### 1.3 LLM发展历程

| 时代 | 时间 | 技术特点 | 代表模型 |
|------|------|----------|----------|
| 统计NLP | 1990s-2010s | N-gram、语言模型 | GPT-1、BERT前身 |
| 深度学习NLP | 2012-2017 | Word2Vec、Seq2Seq、Attention | Word2Vec、GRU/LSTM |
| 预训练语言模型 | 2018-2020 | 预训练+微调范式 | GPT-2、BERT、RoBERTa、T5 |
| 大模型时代 | 2020-至今 | 规模化、涌现能力 | GPT-3/4、PaLM、LLaMA、ChatGLM |
| 多模态融合 | 2023-至今 | 文本+图像+语音统一 | GPT-4V、Gemini、GPT-4o |

### 1.4 参数规模演进

LLM的参数规模经历了爆炸式增长：

| 模型 | 参数量 | 发布时间 | 关键能力 |
|------|--------|----------|----------|
| GPT-1 | 1.17亿 | 2018 | 预训练+微调范式开创 |
| GPT-2 | 15亿 | 2019 | 零样本任务迁移 |
| GPT-3 | 1750亿 | 2020 | 上下文学习（ICL）、思维链 |
| GPT-3.5 | 1750亿 | 2022 | 指令微调、对话优化 |
| GPT-4 | 未公开 | 2023 | 多模态、长上下文、安全性 |
| LLaMA-1 | 7B-65B | 2023 | 开源基础模型 |
| LLaMA-2 | 7B-70B | 2023 | 开放权重、对话优化 |
| LLaMA-3 | 8B-70B | 2024 | 指令微调、长上下文 |
| Claude-3 | 超大规模 | 2024 | 安全对话、多模态 |

### 1.5 涌现能力（Emergent Capabilities）

**涌现能力**是指大模型在参数规模超过某个临界点后，突然展现出小模型完全不具备的能力。

典型涌现能力：

- **上下文学习**（In-Context Learning）：从提示中的少量示例学习新任务，无需参数更新
- **思维链推理**（Chain-of-Thought）：进行多步推理，展示中间步骤
- **复杂代码生成**：编写完整项目级代码
- **多步数学推理**：解决竞赛数学题

```python
# 上下文学习示例
prompt = """
示例1: 输入 "2+2"，输出 "4"
示例2: 输入 "5+3"，输出 "8"
示例3: 输入 "7+9"，输出
"""
# 模型会输出 "16"，无需任何训练
```

### 1.6 缩放定律（Scaling Law）

研究表明，模型性能随参数规模近似服从幂律分布：

$$L(N) \approx \left(\frac{N_0}{N}\right)^{\alpha}$$

其中 $L$ 是损失，$N$ 是参数量，$N_0$ 和 $\alpha$ 是常数。

**Chinchilla缩放定律**指出，在相同的计算预算下，模型的参数量和数据量应该大致同比增长：

$$N_{optimal} \approx 1.53 \times C^{0.49}$$

$$D_{optimal} \approx 1.47 \times C^{0.51}$$

```
性能
  │
  │                           ╭──────── GPT-4
  │                      ╭────│
  │                 ╭────│    │  涌现区域
  │            ╭────│    │    │
  │       ╭────│    │    │    │
  │  ─────│    │    │    │    │
  └──────────────────────────────────→ 参数量
       7B      13B     70B     175B
```

---

## 2. Transformer 架构详解

### 2.1 注意力机制（Self-Attention）

自注意力是Transformer的核心，它允许序列中任意位置直接交互，摆脱了RNN的距离依赖问题。

**注意力分数计算**：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

其中：
- $Q$（Query）：查询向量，表示当前位置想要关注什么
- $K$（Key）：键向量，表示每个位置的特征
- $V$（Value）：值向量，包含实际的信息内容
- $d_k$：键向量的维度，用于缩放

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class SelfAttention(nn.Module):
    """
    自注意力机制实现
    核心公式: Attention(Q,K,V) = softmax(QK^T / sqrt(d_k)) * V
    """
    def __init__(self, embed_dim, num_heads):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        assert self.head_dim * num_heads == embed_dim, \
            "embed_dim必须能被num_heads整除"
        
        # Q、K、V 线性变换，将输入投影到Q、K、V空间
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        # 输出投影，将多头结果合并回原始维度
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
    def forward(self, x, mask=None):
        """
        参数:
            x: [batch, seq_len, embed_dim] 输入张量
            mask: [batch, seq_len, seq_len] 可选注意力掩码
        返回:
            output: [batch, seq_len, embed_dim] 注意力输出
            attention_weights: [batch, num_heads, seq_len, seq_len] 注意力权重
        """
        batch_size, seq_len, _ = x.shape
        
        # 线性投影得到Q、K、V
        Q = self.q_proj(x)  # [batch, seq_len, embed_dim]
        K = self.k_proj(x)
        V = self.v_proj(x)
        
        # 重塑为多头形式 [batch, num_heads, seq_len, head_dim]
        # 便于并行计算多个注意力头
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算注意力分数: Q @ K^T / sqrt(d_k)
        # 除以sqrt(d_k)防止点积过大导致softmax梯度消失
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # 应用掩码（如果有）- 将不可见位置设为负无穷
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))
        
        # Softmax归一化得到注意力权重
        attention_weights = F.softmax(scores, dim=-1)
        
        # 加权求和: 注意力权重 @ V
        context = torch.matmul(attention_weights, V)  # [batch, num_heads, seq_len, head_dim]
        
        # 合并多头 [batch, seq_len, embed_dim]
        context = context.transpose(1, 2).contiguous()
        context = context.view(batch_size, seq_len, self.embed_dim)
        
        output = self.out_proj(context)
        return output, attention_weights


# 使用示例
batch_size = 2
seq_len = 10
embed_dim = 64
num_heads = 8

attention = SelfAttention(embed_dim, num_heads)
x = torch.randn(batch_size, seq_len, embed_dim)

output, weights = attention(x)
print(f"输出形状: {output.shape}")      # [2, 10, 64]
print(f"注意力权重形状: {weights.shape}")  # [2, 8, 10, 10]
```

### 2.2 多头注意力（Multi-Head Attention）

多头注意力将输入分成多个头并行计算，捕捉不同子空间的特征：

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$

其中 $\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$

```python
class MultiHeadAttention(nn.Module):
    """
    多头注意力模块
    多个注意力头并行计算，捕捉不同子空间的特征
    """
    def __init__(self, embed_dim, num_heads, dropout=0.1):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # 一次性计算Q、K、V（更高效）
        self.qkv_proj = nn.Linear(embed_dim, embed_dim * 3)
        self.out_proj = nn.Linear(embed_dim, embed_dim)

        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.head_dim)

    def forward(self, x, attention_mask=None):
        """
        参数:
            x: [batch, seq_len, embed_dim] 输入
            attention_mask: 注意力掩码
        返回:
            output: [batch, seq_len, embed_dim]
            attn_weights: [batch, num_heads, seq_len, seq_len]
        """
        batch_size, seq_len, embed_dim = x.shape

        # 一次性计算Q、K、V [batch, seq_len, 3*embed_dim]
        qkv = self.qkv_proj(x)
        # 重塑为多头格式 [batch, seq_len, 3, num_heads, head_dim]
        qkv = qkv.reshape(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        # 调整维度顺序 [3, batch, num_heads, seq_len, head_dim]
        qkv = qkv.permute(2, 0, 3, 1, 4)

        Q, K, V = qkv[0], qkv[1], qkv[2]

        # 计算注意力分数
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale

        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask == 0, float("-inf"))

        # 归一化
        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # 加权求和
        context = torch.matmul(attn_weights, V)
        # 合并多头: [batch, num_heads, seq_len, head_dim] -> [batch, seq_len, embed_dim]
        context = context.transpose(1, 2).reshape(batch_size, seq_len, embed_dim)

        output = self.out_proj(context)
        return output, attn_weights
```

### 2.3 位置编码（Positional Encoding）

Transformer本身不包含序列顺序信息，需要通过位置编码添加。

```python
class PositionalEncoding(nn.Module):
    """
    位置编码
    使用正弦/余弦函数为序列中的每个位置添加唯一的位置信息
    """
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        
        # 创建位置编码矩阵 [max_len, d_model]
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        # 计算除数项，用于生成不同频率的正弦/余弦
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        
        # 偶数维度使用sin，奇数维度使用cos
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        # 添加批次维度 [1, max_len, d_model]
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)  # 不被优化，但会随模型保存
        
    def forward(self, x):
        """
        参数:
            x: [batch, seq_len, d_model] 输入张量
        返回:
            添加了位置编码的张量
        """
        x = x + self.pe[:, :x.size(1), :]
        return x


class RotaryPositionalEncoding(nn.Module):
    """
    旋转位置编码（RoPE）
    LLaMA、GLM等模型使用的一种高效位置编码
    """
    def __init__(self, dim, base=10000):
        super().__init__()
        self.dim = dim
        self.base = base
        # 预计算频率
        inv_freq = 1.0 / (base ** (torch.arange(0, dim, 2).float() / dim))
        self.register_buffer('inv_freq', inv_freq)
        
    def forward(self, x, seq_len):
        """
        生成旋转矩阵
        """
        t = torch.arange(seq_len, device=x.device).type_as(self.inv_freq)
        # 外积得到频率矩阵 [seq_len, dim//2]
        freqs = torch.outer(t, self.inv_freq)
        # 拼接sin和cos [seq_len, dim]
        emb = torch.cat((freqs.sin(), freqs.cos()), dim=-1)
        return emb
```

### 2.4 前馈神经网络（FFN）

每个Transformer层还包含一个前馈神经网络：

$$\text{FFN}(x) = \max(0, xW_1 + b_1)W_2 + b_2$$

```python
class FeedForward(nn.Module):
    """
    前馈神经网络模块
    采用"升维-激活-降维"的设计，增强模型表达能力
    """
    def __init__(self, embed_dim, feedforward_dim, dropout=0.1):
        super().__init__()
        # 升维：embed_dim -> feedforward_dim（通常是4倍）
        self.fc1 = nn.Linear(embed_dim, feedforward_dim)
        self.fc2 = nn.Linear(feedforward_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)
        # GELU激活函数：比ReLU更平滑，GPT-2/LLaMA等常用
        self.activation = nn.GELU()

    def forward(self, x):
        """
        参数:
            x: [batch, seq_len, embed_dim]
        返回:
            [batch, seq_len, embed_dim]
        """
        x = self.fc1(x)          # 升维
        x = self.activation(x)   # 激活
        x = self.dropout(x)
        x = self.fc2(x)          # 降维
        return x
```

### 2.5 残差连接与层归一化

Transformer使用**残差连接**和**层归一化**来稳定训练：

```python
class TransformerLayer(nn.Module):
    """
    单个Transformer编码器层
    包含：多头注意力 + 残差连接 + 层归一化 + FFN + 残差连接 + 层归一化
    """
    def __init__(self, embed_dim, num_heads, feedforward_dim, dropout=0.1):
        super().__init__()

        # 多头自注意力
        self.self_attn = MultiHeadAttention(embed_dim, num_heads, dropout)
        # 第一个归一化层（注意力之后）
        self.norm1 = nn.LayerNorm(embed_dim)

        # 前馈网络
        self.ffn = FeedForward(embed_dim, feedforward_dim, dropout)
        # 第二个归一化层（FFN之后）
        self.norm2 = nn.LayerNorm(embed_dim)

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, attention_mask=None):
        """
        前向传播
        """
        # 自注意力 + 第一个残差连接
        attn_output, attn_weights = self.self_attn(x, attention_mask)
        x = x + self.dropout(attn_output)  # 残差连接
        x = self.norm1(x)

        # 前馈网络 + 第二个残差连接
        ffn_output = self.ffn(x)
        x = x + ffn_output  # 残差连接
        x = self.norm2(x)

        return x, attn_weights
```

### 2.6 完整Transformer编码器

```python
class TransformerEncoder(nn.Module):
    """
    完整Transformer编码器
    由词嵌入、多层Transformer层堆叠而成
    """
    def __init__(self, vocab_size, embed_dim, num_heads, num_layers,
                 feedforward_dim, dropout=0.1, max_seq_len=512):
        super().__init__()

        # 词嵌入层
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        # 位置编码
        self.position_embedding = PositionalEncoding(embed_dim, max_seq_len)

        # 多层Transformer编码器堆叠
        self.layers = nn.ModuleList([
            TransformerLayer(embed_dim, num_heads, feedforward_dim, dropout)
            for _ in range(num_layers)
        ])

        # 最终归一化层
        self.norm = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, attention_mask=None):
        """
        参数:
            x: [batch, seq_len] 词索引
            attention_mask: 注意力掩码
        返回:
            output: [batch, seq_len, embed_dim] 编码后的隐藏状态
            all_attn_weights: 所有层的注意力权重列表
        """
        # 词嵌入 + 位置编码
        x = self.token_embedding(x)
        x = self.position_embedding(x)
        x = self.dropout(x)

        # 逐层处理
        all_attn_weights = []
        for layer in self.layers:
            x, attn_weights = layer(x, attention_mask)
            all_attn_weights.append(attn_weights)

        # 最终归一化
        x = self.norm(x)

        return x, all_attn_weights


# 完整模型示例
vocab_size = 50000
embed_dim = 512
num_heads = 8
num_layers = 6
feedforward_dim = 2048

encoder = TransformerEncoder(
    vocab_size, embed_dim, num_heads, num_layers, feedforward_dim
)

# 模拟输入
batch_size = 2
seq_len = 32
x = torch.randint(0, vocab_size, (batch_size, seq_len))

output, attn_weights = encoder(x)
print(f"编码器输出形状: {output.shape}")  # [2, 32, 512]
print(f"层数: {len(attn_weights)}")      # 6
```

### 2.7 Encoder vs Decoder vs Encoder-Decoder

| 架构类型 | 结构特点 | 代表模型 | 适用任务 |
|----------|----------|----------|----------|
| **Encoder-only** | 双向注意力，只编码 | BERT、RoBERTa | 理解任务：分类、NER、问答 |
| **Decoder-only** | 单向（因果）注意力，自回归生成 | GPT、LLaMA | 生成任务：对话、写作、代码 |
| **Encoder-Decoder** | 编码器+解码器，交叉注意力 | T5、BART | 序列到序列：翻译、摘要、问答 |

```python
class TransformerDecoderLayer(nn.Module):
    """
    Transformer解码器层（用于自回归生成，如GPT）
    与编码器层的区别：
    1. 使用因果掩码（Causal Mask）防止看到未来位置
    2. 可选的交叉注意力层（用于条件生成）
    """
    def __init__(self, embed_dim, num_heads, feedforward_dim, dropout=0.1):
        super().__init__()

        # 掩码自注意力（只能看到之前的位置）
        self.self_attn = MultiHeadAttention(embed_dim, num_heads, dropout)
        self.norm1 = nn.LayerNorm(embed_dim)

        # 交叉注意力（用于接收编码器输出，如翻译任务）
        self.cross_attn = MultiHeadAttention(embed_dim, num_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)

        # 前馈网络
        self.ffn = FeedForward(embed_dim, feedforward_dim, dropout)
        self.norm3 = nn.LayerNorm(embed_dim)

        self.dropout = nn.Dropout(dropout)

    def forward(self, x, encoder_output=None, self_mask=None, cross_mask=None):
        """
        参数:
            x: 解码器输入
            encoder_output: 编码器输出（用于交叉注意力）
            self_mask: 解码器自注意力掩码（因果掩码）
            cross_mask: 交叉注意力掩码
        """
        # 掩码自注意力
        attn_out, _ = self.self_attn(x, self_mask)
        x = self.norm1(x + self.dropout(attn_out))

        # 交叉注意力（如果有编码器输出）
        if encoder_output is not None:
            cross_out, _ = self.cross_attn(x, cross_mask)
            x = self.norm2(x + self.dropout(cross_out))

        # 前馈网络
        ffn_out = self.ffn(x)
        x = self.norm3(x + ffn_out)

        return x


def create_causal_mask(seq_len):
    """
    创建因果掩码，确保每个位置只能看到之前的词
    这是GPT等自回归模型的关键组件
    """
    # 创建下三角矩阵（对角线及以下为1，表示可见）
    mask = torch.tril(torch.ones(seq_len, seq_len))
    return mask
```

### 2.8 Transformer架构图示

```
输入序列: [Token1, Token2, Token3, ..., TokenN]
    │
    ▼
┌─────────────────────────────────────────┐
│           Token Embedding + Pos         │
│         [batch, seq, embed_dim]          │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│         Transformer Layer × N           │
│  ┌─────────────────────────────────┐     │
│  │  Multi-Head Self-Attention      │     │
│  │  + Residual Connection          │     │
│  │  + Layer Normalization          │     │
│  └─────────────────────────────────┘     │
│  ┌─────────────────────────────────┐     │
│  │  Feed-Forward Network          │     │
│  │  + Residual Connection          │     │
│  │  + Layer Normalization          │     │
│  └─────────────────────────────────┘     │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│              Layer Norm                  │
└─────────────────────────────────────────┘
    │
    ▼
输出序列: [hidden1, hidden2, ..., hiddenN]
```

---

## 3. 预训练与微调

### 3.1 预训练任务

预训练是大模型学习语言知识的核心阶段，主要任务包括：

| 预训练任务 | 描述 | 适用模型 |
|------------|------|----------|
| **MLM**（Masked Language Modeling） | 掩码语言模型，预测被掩码的词 | BERT |
| **NSP**（Next Sentence Prediction） | 预测句子对是否连续 | BERT |
| **Next Token Prediction** | 因果语言模型，预测下一个词 | GPT、LLaMA |
| **Span Corruption** | 掩码一段连续文本 | T5、BART |

```python
class PretrainingTasks:
    """
    预训练任务实现
    """
    
    @staticmethod
    def masked_language_modeling(tokens, mask_token_id, vocab_size, mask_prob=0.15):
        """
        MLM任务实现（BERT风格）
        
        参数:
            tokens: 输入token序列
            mask_token_id: 掩码token的ID
            vocab_size: 词表大小
            mask_prob: 掩码概率（通常15%）
        返回:
            masked_tokens: 处理后的序列
            labels: 需要预测的标签（-100表示不需要预测）
        """
        labels = tokens.clone()
        probability_matrix = torch.full(labels.shape, mask_prob)
        
        # 不对特殊token进行掩码
        special_tokens_mask = (tokens == 0) | (tokens == 1) | (tokens == 2)
        probability_matrix.masked_fill_(special_tokens_mask, value=0.0)
        
        # 随机选择要掩码的位置
        masked_indices = torch.bernoulli(probability_matrix).bool()
        labels[~masked_indices] = -100  # 不需要预测的位置设为-100
        
        # 80%替换为[MASK]，10%替换为随机词，10%保持不变
        indices_replaced = torch.bernoulli(torch.full(labels.shape, 0.8)).bool() & masked_indices
        tokens[indices_replaced] = mask_token_id
        
        indices_random = torch.bernoulli(torch.full(labels.shape, 0.5)).bool() & masked_indices & ~indices_replaced
        random_words = torch.randint(vocab_size, tokens.shape, dtype=torch.long)
        tokens[indices_random] = random_words[indices_random]
        
        return tokens, labels
    
    @staticmethod
    def next_token_prediction(tokens):
        """
        因果语言模型任务（GPT风格）
        预测下一个token，标签是输入右移一位
        """
        input_tokens = tokens[:-1]  # 输入：除最后一个外的所有token
        labels = tokens[1:]          # 标签：除第一个外的所有token
        return input_tokens, labels
```

### 3.2 微调方法

微调是将预训练模型适配到特定任务的技术：

| 方法 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **Full Fine-tuning** | 更新所有参数 | 效果最好 | 资源消耗大 |
| **LoRA** | 低秩适配器 | 高效、参数量小 | 效果略逊 |
| **Prefix Tuning** | 添加可学习前缀 | 参数效率高 | 需要精心设计 |
| **Adapter** | 添加适配层 | 模块化、可插拔 | 增加推理延迟 |

```python
class LoRALayer(nn.Module):
    """
    LoRA（Low-Rank Adaptation）实现
    核心思想：用两个低秩矩阵的乘积替代原权重更新
    ΔW = BA，其中B∈R^{d×r}，A∈R^{r×k}，r远小于d和k
    """
    def __init__(self, original_layer, rank=4, alpha=1.0):
        super().__init__()
        self.original_layer = original_layer
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # 获取原权重维度
        d_in, d_out = original_layer.weight.shape
        
        # LoRA的两个低秩矩阵
        self.lora_A = nn.Parameter(torch.randn(d_in, rank))
        self.lora_B = nn.Parameter(torch.zeros(rank, d_out))
        
        # 冻结原始权重
        for param in self.original_layer.parameters():
            param.requires_grad = False
            
        # 初始化A（使用随机正交初始化）
        nn.init.normal_(self.lora_A, std=1.0 / rank)
        
    def forward(self, x):
        """
        前向传播：原权重 + LoRA调整
        """
        # 原始输出
        original_output = self.original_layer(x)
        # LoRA调整：x @ A @ B * scaling
        lora_output = x @ self.lora_A @ self.lora_B * self.scaling
        return original_output + lora_output


class LoRAConfig:
    """
    LoRA配置类
    """
    def __init__(
        self,
        model_name_or_path,
        rank=4,
        alpha=1.0,
        target_modules=None,
        lora_dropout=0.05,
        bias="none"
    ):
        self.model_name_or_path = model_name_or_path
        self.rank = rank
        self.alpha = alpha
        self.target_modules = target_modules or ["q_proj", "v_proj", "k_proj", "o_proj"]
        self.lora_dropout = lora_dropout
        self.bias = bias


def apply_lora_to_model(model, config):
    """
    为模型应用LoRA
    """
    from PEFT import get_peft_model, LoraConfig as PeftLoraConfig
    
    peft_config = PeftLoraConfig(
        task_type="CAUSAL_LM",
        r=config.rank,
        lora_alpha=config.alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules
    )
    
    return get_peft_model(model, peft_config)
```

### 3.3 提示工程（Prompt Engineering）

提示工程是优化大模型输出的关键技术：

```python
class PromptTemplates:
    """
    常用提示模板
    """
    
    # 零样本提示
    ZERO_SHOT = """请回答以下问题：
问题：{question}
答案："""
    
    # 少样本提示（Few-shot）
    FEW_SHOT = """请完成下面的类比推理：

示例1:
输入：皇帝 - 皇后 = 男人 - [?]
输出：女人

示例2:
输入：国王 - 王国 = 父亲 - [?]
输出：孩子

现在请完成：
输入：{input}
输出："""
    
    # 思维链提示（Chain-of-Thought）
    COT = """请逐步推理以下问题：

问题：{problem}

让我们一步步思考：
1. """
    
    # 系统提示 + 用户提示
    @staticmethod
    def build_chat_prompt(system_prompt, user_message):
        """构建对话格式提示"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    
    @staticmethod
    def build_robot_command_prompt():
        """构建机器人命令理解提示"""
        return """你是一个机器人命令理解专家。
分析用户的命令，提取：
1. intent: 意图（navigation/pick/place/follow/stop/greet）
2. target: 目标（位置或物体）
3. constraints: 约束条件

以JSON格式输出：
{"intent": "...", "target": "...", "constraints": "..."}"""


class PromptEngineer:
    """
    提示工程师类
    """
    def __init__(self, llm_model):
        self.llm = llm_model
        
    def zero_shot(self, question):
        """零样本推理"""
        prompt = PromptTemplates.ZERO_SHOT.format(question=question)
        return self.llm.generate(prompt)
    
    def few_shot(self, examples, input_text):
        """少样本推理"""
        # 构建示例部分
        example_text = "\n".join([
            f"输入：{ex['input']}\n输出：{ex['output']}"
            for ex in examples
        ])
        prompt = f"{example_text}\n\n现在请完成：\n输入：{input_text}\n输出："
        return self.llm.generate(prompt)
    
    def chain_of_thought(self, problem):
        """思维链推理"""
        prompt = PromptTemplates.COT.format(problem=problem)
        return self.llm.generate(prompt)
```

---

## 4. 主流大模型介绍

### 4.1 GPT系列（OpenAI）

| 模型 | 参数量 | 发布时间 | 关键能力 |
|------|--------|----------|----------|
| GPT-1 | 1.17亿 | 2018 | 预训练+微调开创 |
| GPT-2 | 15亿 | 2019 | 零样本迁移 |
| GPT-3 | 1750亿 | 2020 | 上下文学习、思维链 |
| GPT-4 | 未公开 | 2023 | 多模态、长上下文、安全性 |
| GPT-4o | 未公开 | 2024 | 实时多模态交互 |

```python
# OpenAI API调用示例
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "你是一个机器人助手"},
        {"role": "user", "content": "请解释什么是Transformer架构"}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

### 4.2 LLaMA系列（Meta）

LLaMA是Meta开源的基础语言模型，掀起了开源大模型浪潮：

| 模型 | 参数量 | 上下文 | 特点 |
|------|--------|--------|------|
| LLaMA-1 | 7B/13B/33B/65B | 2K | 首个开源基础模型 |
| LLaMA-2 | 7B/13B/70B | 4K | 开放权重、对话优化 |
| LLaMA-3 | 8B/70B | 8K | 指令微调、最新预训练 |

**LLaMA-3的技术特点**：
- 使用超过15T tokens的公开数据预训练
- 优化了训练效率，使用数据并行+模型并行
- 支持多种量化版本，便于部署

### 4.3 Claude系列（Anthropic）

Claude由Anthropic开发，以安全性著称：

| 模型 | 特点 |
|------|------|
| Claude-1 | 早期版本 |
| Claude-2 | 长上下文、安全优化 |
| Claude-3 | 多模态、性能卓越 |

```python
# Anthropic Claude API调用示例（通过OpenAI兼容接口）
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key",
    base_url="https://api.anthropic.com/v1"
)

response = client.chat.completions.create(
    model="claude-3-opus-20240229",
    messages=[
        {"role": "user", "content": "你好，请介绍一下自己"}
    ],
    max_tokens=500
)

print(response.choices[0].message.content)
```

### 4.4 其他主流开源模型

| 模型 | 机构 | 参数规模 | 特点 |
|------|------|----------|------|
| **ChatGLM** | 智谱AI | 6B-130B | 中文优化、开源对话 |
| **Qwen** | 阿里云 | 7B-72B | 中文强大、开源生态 |
| **DeepSeek** | 深度求索 | 7B-67B | 推理能力强、开源 |
| **Mistral** | Mistral AI | 7B | 高效率、结构化稀疏 |
| **Baichuan** | 百川智能 | 7B-13B | 中文对话、商业友好 |

### 4.5 开源模型 vs 闭源模型

| 方面 | 开源模型 | 闭源模型 |
|------|----------|----------|
| **代表** | LLaMA、ChatGLM、Qwen | GPT-4、Claude-3 |
| **成本** | 免费（本地部署） | 按token付费 |
| **隐私** | 数据不离开本地 | 数据发送至云端 |
| **定制性** | 可自由微调 | 有限定制 |
| **性能** | 越来越好，但仍有一定差距 | 通常最优 |
| **部署** | 需要GPU资源 | 直接API调用 |

### 4.6 模型选择指南

```
┌─────────────────────────────────────────────────────────┐
│                    模型选择决策树                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  需要商用? ──是──→ 检查LICENSE ──→ 可商用 ✓               │
│      │                                                    │
│      否                                                    │
│      │                                                    │
│  需要中文? ──是──→ Qwen-2 / ChatGLM-4                    │
│      │                                                    │
│      否                                                    │
│      │                                                    │
│  需要推理能力? ──是──→ DeepSeek-V2 / Claude              │
│      │                                                    │
│      否                                                    │
│      │                                                    │
│  需要轻量部署? ──是──→ LLaMA-3-8B / Mistral-7B-Q4       │
│      │                                                    │
│      否                                                    │
│      │                                                    │
│  → GPT-4 / Claude-3 (最高精度)                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4.7 主流大模型对比

| 模型 | 机构 | 参数量级 | 开源 | 中文能力 | 适用场景 |
|------|------|----------|------|----------|----------|
| GPT-4 | OpenAI | 超大规模 | ❌ | ⭐⭐⭐⭐⭐ | 通用、高精度 |
| GPT-3.5 | OpenAI | 175B | ❌ | ⭐⭐⭐⭐ | 对话、代码 |
| Claude-3 | Anthropic | 超大规模 | ❌ | ⭐⭐⭐⭐⭐ | 安全对话、分析 |
| LLaMA-3 | Meta | 8B-70B | ✅ | ⭐⭐⭐ | 基础模型、研发 |
| ChatGLM-4 | 智谱AI | 6B-130B | ✅ | ⭐⭐⭐⭐⭐ | 中文对话 |
| Qwen-2 | 阿里云 | 0.5B-72B | ✅ | ⭐⭐⭐⭐⭐ | 通用、中文 |
| DeepSeek-V2 | 深度求索 | 21B-236B | ✅ | ⭐⭐⭐⭐ | 推理、代码 |
| Mistral-7B | Mistral AI | 7B | ✅ | ⭐⭐⭐ | 高效推理 |

---

## 5. 代码实战：实现Transformer与注意力机制

### 5.1 环境准备

```bash
# 创建虚拟环境
python3 -m venv ~/llm_venv
source ~/llm_venv/bin/activate

# 安装PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu

# 安装transformers
pip install transformers accelerate sentencepiece protobuf
```

### 5.2 实现简化的Transformer编码器

```python
#!/usr/bin/env python3
# examples/transformer_encoder_demo.py
"""
简化Transformer编码器实现
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class PositionalEncoding(nn.Module):
    """位置编码：为序列添加位置信息"""
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1), :]
        return x


class MultiHeadAttention(nn.Module):
    """多头注意力机制"""
    def __init__(self, embed_dim, num_heads, dropout=0.1):
        super().__init__()
        assert embed_dim % num_heads == 0
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        self.qkv_proj = nn.Linear(embed_dim, embed_dim * 3)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.head_dim)

    def forward(self, x, attention_mask=None):
        batch_size, seq_len, embed_dim = x.shape

        # 一次性计算Q、K、V
        qkv = self.qkv_proj(x)
        qkv = qkv.reshape(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # [3, batch, num_heads, seq_len, head_dim]

        Q, K, V = qkv[0], qkv[1], qkv[2]

        # 计算注意力分数
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale

        if attention_mask is not None:
            scores = scores.masked_fill(attention_mask == 0, float("-inf"))

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # 加权求和
        context = torch.matmul(attn_weights, V)
        context = context.transpose(1, 2).reshape(batch_size, seq_len, embed_dim)

        output = self.out_proj(context)
        return output, attn_weights


class FeedForward(nn.Module):
    """前馈神经网络"""
    def __init__(self, embed_dim, feedforward_dim, dropout=0.1):
        super().__init__()
        self.fc1 = nn.Linear(embed_dim, feedforward_dim)
        self.fc2 = nn.Linear(feedforward_dim, embed_dim)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

    def forward(self, x):
        x = self.fc1(x)
        x = self.activation(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x


class TransformerEncoderLayer(nn.Module):
    """单个Transformer编码器层"""
    def __init__(self, embed_dim, num_heads, feedforward_dim, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(embed_dim, num_heads, dropout)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.ffn = FeedForward(embed_dim, feedforward_dim, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, attention_mask=None):
        # 自注意力 + 残差连接
        attn_out, _ = self.self_attn(x, attention_mask)
        x = x + self.dropout(attn_out)
        x = self.norm1(x)

        # FFN + 残差连接
        ffn_out = self.ffn(x)
        x = x + ffn_out
        x = self.norm2(x)

        return x


class TransformerEncoder(nn.Module):
    """完整Transformer编码器"""
    def __init__(self, vocab_size, embed_dim, num_heads, num_layers,
                 feedforward_dim, dropout=0.1, max_seq_len=512):
        super().__init__()
        self.token_embedding = nn.Embedding(vocab_size, embed_dim)
        self.position_embedding = PositionalEncoding(embed_dim, max_seq_len)
        self.layers = nn.ModuleList([
            TransformerEncoderLayer(embed_dim, num_heads, feedforward_dim, dropout)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, attention_mask=None):
        x = self.token_embedding(x)
        x = self.position_embedding(x)
        x = self.dropout(x)

        for layer in self.layers:
            x = layer(x, attention_mask)

        x = self.norm(x)
        return x


def demo_transformer_encoder():
    """演示Transformer编码器"""
    # 配置
    VOCAB_SIZE = 10000
    EMBED_DIM = 128
    NUM_HEADS = 4
    NUM_LAYERS = 2
    FEEDFORWARD_DIM = 512
    SEQ_LEN = 20

    # 创建模型
    encoder = TransformerEncoder(
        vocab_size=VOCAB_SIZE,
        embed_dim=EMBED_DIM,
        num_heads=NUM_HEADS,
        num_layers=NUM_LAYERS,
        feedforward_dim=FEEDFORWARD_DIM
    )

    # 模拟输入：batch=2, seq_len=20
    x = torch.randint(0, VOCAB_SIZE, (2, SEQ_LEN))

    # 前向传播
    output = encoder(x)
    print(f"输入形状: {x.shape}")          # [2, 20]
    print(f"输出形状: {output.shape}")     # [2, 20, 128]

    # 统计参数量
    total_params = sum(p.numel() for p in encoder.parameters())
    print(f"总参数量: {total_params:,}")


if __name__ == "__main__":
    demo_transformer_encoder()
```

### 5.3 实现多头注意力机制

```python
#!/usr/bin/env python3
# examples/multihead_attention_demo.py
"""
多头注意力机制详细实现与可视化
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import matplotlib.pyplot as plt
import numpy as np


class MultiHeadAttention(nn.Module):
    """
    多头注意力机制
    核心公式: MultiHead(Q,K,V) = Concat(head_1,...,head_h) W^O
    其中 head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
    """
    def __init__(self, embed_dim, num_heads, dropout=0.1):
        super().__init__()
        assert embed_dim % num_heads == 0, "embed_dim必须能被num_heads整除"
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        
        # 四个线性投影矩阵
        self.W_q = nn.Linear(embed_dim, embed_dim)
        self.W_k = nn.Linear(embed_dim, embed_dim)
        self.W_v = nn.Linear(embed_dim, embed_dim)
        self.W_o = nn.Linear(embed_dim, embed_dim)
        
        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.head_dim)
        
    def forward(self, query, key, value, mask=None):
        """
        参数:
            query: [batch, seq_len, embed_dim] 查询
            key: [batch, seq_len, embed_dim] 键
            value: [batch, seq_len, embed_dim] 值
            mask: [batch, seq_len, seq_len] 注意力掩码
        返回:
            output: [batch, seq_len, embed_dim] 注意力输出
            attention_weights: [batch, num_heads, seq_len, seq_len] 注意力权重
        """
        batch_size = query.size(0)
        
        # 线性投影
        Q = self.W_q(query)
        K = self.W_k(key)
        V = self.W_v(value)
        
        # 分头: [batch, seq_len, num_heads, head_dim] -> [batch, num_heads, seq_len, head_dim]
        Q = Q.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # 计算注意力分数: Q @ K^T / sqrt(d_k)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        
        # 应用掩码
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))
        
        # 归一化
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # 加权求和
        context = torch.matmul(attention_weights, V)
        
        # 合并多头: [batch, num_heads, seq_len, head_dim] -> [batch, seq_len, embed_dim]
        context = context.transpose(1, 2).contiguous()
        context = context.view(batch_size, -1, self.embed_dim)
        
        # 输出投影
        output = self.W_o(context)
        
        return output, attention_weights


def visualize_attention(attention_weights, tokens, save_path="attention.png"):
    """
    可视化注意力权重
    
    参数:
        attention_weights: [num_heads, seq_len, seq_len] 注意力权重
        tokens: token列表
        save_path: 保存路径
    """
    num_heads = attention_weights.shape[0]
    seq_len = attention_weights.shape[1]
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    for head_idx in range(min(num_heads, 8)):
        ax = axes[head_idx]
        weights = attention_weights[head_idx].cpu().detach().numpy()
        
        im = ax.imshow(weights, cmap='viridis', aspect='auto')
        ax.set_xticks(range(seq_len))
        ax.set_yticks(range(seq_len))
        ax.set_xticklabels(tokens, rotation=45, fontsize=8)
        ax.set_yticklabels(tokens, fontsize=8)
        ax.set_title(f'Head {head_idx + 1}', fontsize=10)
        plt.colorbar(im, ax=ax)
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"注意力可视化已保存到: {save_path}")


def demo_attention():
    """演示多头注意力"""
    # 配置
    batch_size = 1
    seq_len = 8
    embed_dim = 64
    num_heads = 4
    
    # 示例序列（机器人指令）
    tokens = ["机器人", "去", "厨", "房", "拿", "水", "杯", "[PAD]"]
    
    # 创建注意力层
    attention = MultiHeadAttention(embed_dim, num_heads)
    
    # 模拟输入
    x = torch.randn(batch_size, seq_len, embed_dim)
    
    # 前向传播
    output, weights = attention(x, x, x)
    
    print(f"输入形状: {x.shape}")            # [1, 8, 64]
    print(f"输出形状: {output.shape}")        # [1, 8, 64]
    print(f"注意力权重形状: {weights.shape}")  # [1, 4, 8, 8]
    
    # 分析注意力分布
    avg_weights = weights[0].mean(dim=0)  # [8, 8] 平均所有头
    print(f"\n平均注意力权重（最后一层）:")
    print(avg_weights.shape)
    
    # 可视化
    visualize_attention(weights[0], tokens)
    
    # 分析每个头关注的内容
    print("\n各头关注的token（最大注意力位置）:")
    for head_idx in range(num_heads):
        max_pos = weights[0, head_idx].sum(dim=-1).argmax().item()
        print(f"  Head {head_idx + 1}: 主要关注位置 {max_pos} ({tokens[max_pos]})")


if __name__ == "__main__":
    demo_attention()
```

### 5.4 使用transformers库加载预训练模型

```python
#!/usr/bin/env python3
# examples/transformers_hf_demo.py
"""
使用Hugging Face Transformers库加载预训练模型
"""

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModel,
    pipeline
)
import warnings
warnings.filterwarnings('ignore')


class HuggingFaceLLM:
    """
    Hugging Face大语言模型封装类
    支持本地模型和在线模型
    """
    def __init__(self, model_name, device=None):
        """
        初始化LLM
        
        参数:
            model_name: HuggingFace模型名称或本地路径
            device: 运行设备 ('cuda'/'cpu')
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        
        print(f"[INFO] 设备: {self.device}")
        print(f"[INFO] 加载模型: {model_name}")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            trust_remote_code=True
        )
        
        self.model.eval()
        print("[INFO] 模型加载完成")
    
    def generate(self, prompt, max_new_tokens=256, temperature=0.7,
                 top_p=0.9, top_k=50, do_sample=True):
        """
        生成文本
        
        参数:
            prompt: 输入提示
            max_new_tokens: 最大生成token数
            temperature: 采样温度（越高越随机）
            top_p: Nucleus采样阈值
            top_k: Top-K采样数量
            do_sample: 是否采样
        返回:
            str: 生成的文本
        """
        # 构建输入消息
        messages = [{"role": "user", "content": prompt}]
        
        # 应用聊天模板（如果有）
        if hasattr(self.tokenizer, 'apply_chat_template'):
            input_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            input_text = prompt
        
        # 分词
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        
        # 移至设备
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id
            )
        
        # 解码（去掉输入prompt部分）
        generated_text = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return generated_text
    
    def chat(self, messages):
        """
        对话模式
        
        参数:
            messages: 消息列表 [{"role": "user", "content": "..."}]
        返回:
            str: 助手回复
        """
        if hasattr(self.tokenizer, 'apply_chat_template'):
            input_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            input_text = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        
        inputs = self.tokenizer(
            input_text,
            return_tensors="pt",
            padding=True,
            truncation=True
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        
        return response


def demo_pipeline():
    """
    使用Pipeline简化推理
    适合快速体验不同模型
    """
    print("\n" + "="*50)
    print("Pipeline模式演示")
    print("="*50)
    
    # 创建文本生成pipeline
    # 使用Qwen-2.5-7B-Instruct（支持中文，效果好）
    generator = pipeline(
        "text-generation",
        model="Qwen/Qwen2.5-7B-Instruct",
        device=0 if torch.cuda.is_available() else -1,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    
    # 生成文本
    prompt = """请用Python写一个快速排序算法"""
    
    results = generator(
        prompt,
        max_new_tokens=256,
        temperature=0.7,
        do_sample=True,
        top_p=0.9
    )
    
    print(f"\n问题: {prompt}")
    print(f"\n生成结果:\n{results[0]['generated_text']}")


def demo_chat():
    """
    对话模式演示
    """
    print("\n" + "="*50)
    print("对话模式演示")
    print("="*50)
    
    # 初始化（使用支持中文的模型）
    try:
        llm = HuggingFaceLLM("Qwen/Qwen2.5-7B-Instruct")
        
        # 对话
        messages = [
            {"role": "system", "content": "你是一个机器人助手，简洁回复。"},
            {"role": "user", "content": "你好，请介绍一下Transformer架构"}
        ]
        
        response = llm.chat(messages)
        print(f"\n用户: 你好，请介绍一下Transformer架构")
        print(f"助手: {response}")
        
    except Exception as e:
        print(f"模型加载失败（可能需要网络下载）: {e}")
        print("提示：请确保网络连接，或使用已下载的本地模型")


def demo_local_model():
    """
    本地模型演示
    需要提前下载模型
    """
    print("\n" + "="*50)
    print("本地模型演示")
    print("="*50)
    
    # 本地模型路径示例
    local_model_path = "./models/llama-3-8b"
    
    try:
        llm = HuggingFaceLLM(local_model_path)
        response = llm.generate("请解释什么是大语言模型")
        print(f"\n生成结果: {response}")
    except Exception as e:
        print(f"本地模型加载失败: {e}")
        print("提示：请先下载模型到本地目录")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--pipeline":
            demo_pipeline()
        elif sys.argv[1] == "--chat":
            demo_chat()
        elif sys.argv[1] == "--local":
            demo_local_model()
        else:
            print("用法: python transformers_hf_demo.py [--pipeline|--chat|--local]")
    else:
        print("="*50)
        print("Hugging Face Transformers 使用演示")
        print("="*50)
        print("\n可用模式:")
        print("  1. Pipeline模式: python transformers_hf_demo.py --pipeline")
        print("  2. 对话模式: python transformers_hf_demo.py --chat")
        print("  3. 本地模型: python transformers_hf_demo.py --local")
        print("\n默认运行Pipeline模式演示...")
        demo_pipeline()
```

---

## 6. 练习题

### 基础题

**1. 选择题**

1.1 Transformer架构中，注意力机制的核心公式是：
- A. $y = Wx + b$
- B. $\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$
- C. $y = \max(0, Wx + b)$
- D. $y = \sigma(Wx + b)$

1.2 以下哪个不是大语言模型的特点：
- A. 大规模参数
- B. 大规模预训练
- C. 需要针对每个任务微调
- D. 涌现能力

1.3 LLaMA模型是由哪家机构开发的：
- A. OpenAI
- B. Google
- C. Meta
- D. Microsoft

1.4 Transformer中的位置编码（Positional Encoding）作用是：
- A. 增加词表大小
- B. 为序列添加位置信息
- C. 实现注意力机制
- D. 压缩模型参数

1.5 以下哪种不是预训练任务：
- A. MLM（掩码语言模型）
- B. NSP（下一句预测）
- C. CNN（卷积神经网络）
- D. Next Token Prediction（下一个token预测）

**2. 简答题**

2.1 简述Transformer架构的核心组件及其作用。

2.2 解释什么是"涌现能力"，并举例说明。

2.3 比较GPT系列（Decoder-only）和BERT（Encoder-only）架构的差异。

2.4 说明自注意力机制相比RNN循环神经网络的优势。

**3. 编程题**

3.1 编写Python代码，实现一个简化的多头注意力机制。

3.2 使用transformers库加载一个中文对话模型（如Qwen-2.5-7B），并完成一次对话。

### 提高题

**4. 综合题**

4.1 设计一个基于LLM的具身智能机器人对话系统，包括：
   - 系统架构（文字描述）
   - 核心模块及功能
   - 对话流程设计

4.2 分析Chinchilla缩放定律的含义，并讨论这对大模型训练的意义。

4.3 解释LoRA微调的原理，并说明它相比全量微调的优势。

**5. 实战题**

5.1 实现一个简化的Transformer编码器，包括：
   - 词嵌入
   - 位置编码
   - 多层Transformer编码器
   - 输出层

5.2 比较GPT系列、LLaMA、ChatGLM、Qwen等主流大模型的优缺点，并针对机器人应用场景给出选型建议。

---

## 7. 参考答案

### 基础题答案

**1. 选择题**

1.1 **答案：B**
解析：注意力机制的核心公式是 $\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$，其他选项分别是线性层、ReLU激活和Sigmoid激活的公式。

1.2 **答案：C**
解析：LLM的核心特点之一是通用性，通过少量示例或提示即可适配新任务，无需像传统模型那样针对每个任务进行微调。

1.3 **答案：C**
解析：LLaMA（Large Language Model Meta AI）是由Meta（原Facebook）开发的开源语言模型。

1.4 **答案：B**
解析：Transformer本身不包含序列顺序信息，位置编码用于为序列中的每个位置添加唯一的位置信息，使模型能够区分不同位置的token。

1.5 **答案：C**
解析：CNN（卷积神经网络）不是预训练任务。MLM、NSP和Next Token Prediction都是大模型预训练阶段使用的训练目标。

**2. 简答题**

2.1 **Transformer核心组件**：

| 组件 | 作用 |
|------|------|
| 位置编码 | 为序列中的每个位置添加位置信息 |
| 多头注意力 | 并行计算多个注意力，捕捉不同子空间特征 |
| 前馈神经网络 | 对每个位置独立进行非线性变换 |
| 残差连接 | 缓解梯度消失，加速训练收敛 |
| 层归一化 | 稳定训练过程，加速收敛 |

2.2 **涌现能力**：
涌现能力是指当模型规模超过某个临界点后，突然具备小模型完全不具备的能力。例如：
- 上下文学习：无需参数更新，从示例中学习新任务
- 思维链推理：进行多步逻辑推理
- 复杂代码生成：编写完整项目级代码

2.3 **GPT vs BERT**：

| 方面 | GPT（Decoder-only） | BERT（Encoder-only） |
|------|-----|-----|
| 架构 | 单向（因果）注意力 | 双向注意力 |
| 训练目标 | 下一个词预测（自回归） | 掩码语言模型（MLM） |
| 适用任务 | 生成任务 | 理解任务 |
| 典型应用 | 对话、写作、代码生成 | 分类、NER、问答 |

2.4 **自注意力优势**：
- **并行计算**：摆脱序列依赖，训练速度大幅提升
- **长距离依赖**：任意位置直接交互，解决长序列依赖问题
- **可解释性**：注意力权重可视化，展示模型关注点

**3. 编程题答案**

3.1 **多头注意力实现**：
```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class MultiHeadAttention(nn.Module):
    """
    多头注意力机制实现
    """
    def __init__(self, embed_dim, num_heads, dropout=0.1):
        super().__init__()
        assert embed_dim % num_heads == 0

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # 四个线性变换
        self.W_q = nn.Linear(embed_dim, embed_dim)
        self.W_k = nn.Linear(embed_dim, embed_dim)
        self.W_v = nn.Linear(embed_dim, embed_dim)
        self.W_o = nn.Linear(embed_dim, embed_dim)

        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.head_dim)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        # 线性投影
        Q = self.W_q(query)
        K = self.W_k(key)
        V = self.W_v(value)

        # 分头
        Q = Q.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        K = K.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        V = V.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)

        # 注意力计算
        scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        if mask is not None:
            scores = scores.masked_fill(mask == 0, float("-inf"))

        attn_weights = F.softmax(scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # 加权求和
        context = torch.matmul(attn_weights, V)
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.embed_dim)

        output = self.W_o(context)
        return output, attn_weights


# 测试
attn = MultiHeadAttention(embed_dim=64, num_heads=8)
x = torch.randn(2, 10, 64)
output, weights = attn(x, x, x)
print(f"输出形状: {output.shape}")      # [2, 10, 64]
print(f"注意力权重形状: {weights.shape}")  # [2, 8, 10, 10]
```

### 提高题答案

**4. 综合题**

4.1 **LLM具身智能机器人对话系统设计**：

```
┌─────────────────────────────────────────────────────────────┐
│                    系统架构                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户输入 ──→ ASR语音识别 ──→ LLM理解 ──→ 任务规划           │
│                            │               │                 │
│                            ▼               ▼                 │
│                      意图识别      子任务分解                 │
│                            │               │                 │
│                            ▼               ▼                 │
│                      对话管理 ←────── 技能执行               │
│                            │                                │
│                            ▼                                │
│                      响应生成 ──→ TTS语音合成 ──→ 用户输出   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  核心模块:                                                   │
│  - ASR模块: 语音转文本（Whisper/FunASR）                    │
│  - LLM模块: 意图理解、对话生成（GPT-4/Qwen/ChatGLM）         │
│  - 任务规划: 将高层指令分解为机器人可执行步骤                  │
│  - 对话管理: 状态追踪、上下文维护                              │
│  - 技能执行: 调用机器人运动控制、导航、抓取等能力               │
│  - TTS模块: 文本转语音（VALL-E/Fish-Speech）                 │
└─────────────────────────────────────────────────────────────┘
```

4.2 **Chinchilla缩放定律意义**：

Chinchilla定律指出，在相同的计算预算下，模型的参数量和数据量应该大致同比增长：

$$N_{optimal} \approx 1.53 \times C^{0.49}$$

$$D_{optimal} \approx 1.47 \times C^{0.51}$$

**意义**：
1. **训练效率**：之前的GPT-3范式（数据量不变，增加参数）并非最优
2. **成本优化**：同等算力下，更小但数据更多的模型可能表现更好
3. **对GPT-4的推测**：可能使用了比175B参数更小的模型，但用了更多训练数据
4. **实践指导**：确定模型规模时，应同时考虑参数量和数据量

4.3 **LoRA微调原理与优势**：

**原理**：LoRA（Low-Rank Adaptation）用两个低秩矩阵的乘积替代原权重更新：

$$\Delta W = BA$$

其中 $B \in \mathbb{R}^{d \times r}$，$A \in \mathbb{R}^{r \times k}$，$r \ll \min(d, k)$

前向传播时：
$$h = Wx + \frac{\alpha}{r} BAx$$

**优势**：
- **参数量小**：只需训练A和B两个矩阵，参数量从 $d \times k$ 降到 $d \times r + r \times k$
- **显存高效**：冻结原权重，只更新低秩矩阵，大幅降低GPU显存需求
- **可插拔**：不同任务训练不同的LoRA权重，推理时动态加载
- **效果好**：在多种任务上接近全量微调的效果

**5. 实战题答案**

5.1 **简化Transformer编码器**：
（参见代码实战5.2节，已包含完整的TransformerEncoder实现）

5.2 **主流大模型对比与机器人应用选型**：

| 应用场景 | 推荐模型 | 理由 |
|----------|----------|------|
| 家庭服务机器人 | Qwen-2.5 / ChatGLM-4 | 中文能力强，开源可商用 |
| 工业检测机器人 | GPT-4 / Claude-3 | 精度高，多模态 |
| 边缘部署 | LLaMA-3-8B-Q4 / Mistral-7B-Q4 | 体积小，量化后可部署 |
| 对话助手 | Claude-3.5 / GPT-4o | 对话自然，安全 |
| 代码生成 | GPT-4 / DeepSeek-V2 | 编程能力强 |

---

## 总结

本课程学习了LLM与大模型的基础知识，包括：

1. **LLM概述**：发展历史、语言模型基础、涌现能力、缩放定律
2. **Transformer架构**：自注意力、多头注意力、位置编码、前馈网络、残差连接
3. **预训练与微调**：MLM、NSP、Next Token Prediction、LoRA、Prefix Tuning
4. **主流大模型**：GPT系列、LLaMA、Claude、ChatGLM、Qwen、DeepSeek等
5. **代码实战**：从零实现Transformer编码器、多头注意力、transformers库使用

---

**下一步学习：**
- [13-2 Prompt Engineering](../13-2-Prompt-Engineering/13-2-Prompt-Engineering.md)
- [13-3 LangChain 框架](../13-3-LangChain-框架/13-3-LangChain-框架.md)

---

*本课程由 Every Emodied Course 项目组编写 - 2026*
```

