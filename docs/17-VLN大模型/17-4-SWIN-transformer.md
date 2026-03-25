# 17-4 SWIN Transformer

> **前置课程**：17-3 VLN视觉语言导航
> **后续课程**：17-5 VLN数据集与评估

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：本节我们将深入探讨 SWIN Transformer（Shifted Windows Transformer）。SWIN Transformer 是近年来在计算机视觉领域取得重大突破的层级式视觉Transformer架构，其核心创新——移位窗口注意力机制——使其在图像分类、目标检测、语义分割等任务上超越了传统的CNN和早期ViT模型。在VLN（视觉语言导航）任务中，SWIN Transformer 常被用作视觉编码器，为智能体提供多尺度、高质量的视觉特征，对提升导航决策的准确性具有关键作用。

---

## 1. SWIN Transformer 概述

### 1.1 层级式 Transformer 设计

在传统的 Vision Transformer（ViT）中，输入图像被划分为固定大小的 Patch（如 16×16），所有 Patch 之间通过全局自注意力机制进行交互。这种设计虽然简单直接，但存在两个显著问题：

- **计算复杂度高**：全局自注意力的复杂度为 $O(N^2)$，其中 $N$ 是 Patch 的数量。当图像分辨率较高时，计算开销急剧增长。
- **缺乏多尺度建模能力**：ViT 在整个网络中维持单一尺度的特征表示，难以有效捕捉不同尺度的物体结构。

**SWIN Transformer** 提出了**层级式（Hierarchical）** 设计，核心思想借鉴了卷积神经网络（CNN）的多尺度金子塔结构：

| 层级 | 特征图尺寸 | 感受野 | 适用任务 |
|------|-----------|--------|----------|
| Stage 1 | $H/4 \times W/4$ | 局部 | 细节纹理 |
| Stage 2 | $H/8 \times W/8$ | 稍大 | 小物体 |
| Stage 3 | $H/16 \times W/16$ | 中等 | 物体结构 |
| Stage 4 | $H/32 \times W/32$ | 全局 | 场景语义 |

通过**逐层降采样**，SWIN 在深层获得较大的感受野，在浅层保留细粒度信息，实现了 CNN 金字塔式的多尺度建模能力，同时保留了 Transformer 的全局建模优势。

### 1.2 移位窗口机制

SWIN 的核心创新在于**移位窗口注意力（Shifted Window Attention）**。在每个 Stage 内，输入被划分为多个不重叠的窗口（Window），注意力计算只在同一窗口内进行，而非全局：

```
标准窗口划分（非移位）:
┌─────┬─────┬─────┬─────┐
│ W0  │ W1  │ W2  │ W3  │
├─────┼─────┼─────┼─────┤
│ W4  │ W5  │ W6  │ W7  │
├─────┼─────┼─────┼─────┤
│ W8  │ W9  │ W10 │ W11 │
├─────┼─────┼─────┼─────┤
│ W12 │ W13 │ W14 │ W15 │
└─────┴─────┴─────┴─────┘

移位窗口划分（Shifted）:
┌─────┼─────┬─────┼─────┐
│     │ W1' │     │ W3' │
├─────┼─────┼─────┼─────┤
│ W4' │     │ W6' │     │
├─────┼─────┼─────┼─────┤
│     │ W9' │     │ W11'│
├─────┼─────┼─────┼─────┤
│ W12'│     │ W14'│     │
└─────┴─────┴─────┴─────┘
```

**为什么需要移位？**

如果不移位，每个窗口之间没有信息交互，导致窗口间语义割裂。SWIN 在连续的 Transformer Block 之间交替使用**常规窗口划分**和**移位窗口划分**：

- **Block 1（W-MSA）**：使用常规窗口划分，每个窗口内独立做自注意力
- **Block 2（SW-MSA）**：窗口整体偏移半个窗口大小，使窗口边界重新对齐，从而实现跨窗口的信息传递

移位后，相邻窗口的 Patch 会被划分到同一个窗口中，从而建立跨窗口的连接。经过多层堆叠后，信息可以在整个特征图上流动。

### 1.3 与 ViT 的核心区别

| 特性 | ViT | SWIN Transformer |
|------|-----|------------------|
| 注意力范围 | 全局注意力 $O(N^2)$ | 窗口内注意力 $O(N)$ |
| 特征金字塔 | 无，单尺度 | 有，多尺度层级 |
| 计算效率 | 低（高分辨率图像） | 高，窗口划分控制复杂度 |
| 归纳偏置 | 少，需要更多数据 | 多，窗口局部性先验 |
| 适合任务 | 分类（粗粒度） | 检测/分割/导航（细粒度） |

---

## 2. 核心架构

### 2.1 分层特征图

SWIN Transformer 的分层特征图通过 **Patch Merging（Patch合并）** 操作实现。流程如下：

**输入**：原始图像 $H \times W \times 3$

**Stage 1**：
1. **Patch Partition**：将图像划分为 $4 \times 4$ 的 Patch，每个 Patch 被展平为 $4 \times 4 \times 3 = 48$ 维向量
2. **Linear Embedding**：通过线性层映射到 $C$ 维（如 96）
3. **SWIN Block**：进行窗口注意力计算
4. 输出特征图尺寸：$\frac{H}{4} \times \frac{W}{4} \times C$

**Stage 2 ~ Stage 4**：
- **Patch Merging**：每进入下一个 Stage，将相邻 $2 \times 2$ 的 Patch 拼接，得到 $4C$ 维向量
- 经线性层降维到 $2C$，特征图尺寸减半
- 输出分辨率逐层降低，通道数逐层翻倍

最终得到类似 CNN 的金子塔特征：
$$\frac{H}{4}\times\frac{W}{4} \xrightarrow{\text{Stage 1}} \frac{H}{8}\times\frac{W}{8} \xrightarrow{\text{Stage 2}} \frac{H}{16}\times\frac{W}{16} \xrightarrow{\text{Stage 3}} \frac{H}{32}\times\frac{W}{32}$$

### 2.2 Shifted Window Attention 数学表达

标准窗口自注意力（W-MSA）在窗口内计算：

$$\text{Attention}(Q, K, V) = \text{Softmax}\left(\frac{QK^T}{\sqrt{d}}\right)V$$

其中 $Q, K, V \in \mathbb{R}^{M^2 \times d}$，$M$ 是窗口大小（默认 $M=7$）。

移位窗口注意力（SW-MSA）在窗口偏移后计算。设偏移量为 $\lfloor M/2 \rfloor$，则窗口划分起点从 $(0,0)$ 变为 $(\lfloor M/2 \rfloor, \lfloor M/2 \rfloor)$。

为了高效实现偏移窗口，SWIN 引入**循环移位（Cyclic Shift）** 机制：将特征图在空间维度上循环平移，使偏移后的窗口拼接仍然对齐为规则的窗口网格，从而可以复用高效的标准窗口注意力实现。

### 2.3 Patch Merging

Patch Merging 是实现层级降采样的关键：

```python
# 伪代码示意
def patch_merging(x):
    # x shape: [B, H, W, C]
    # 将相邻 2x2 patch 在空间维度拼接
    x = x.reshape(B, H//2, 2, W//2, 2, C)  # [B, H/2, 2, W/2, 2, C]
    x = x.permute(0, 1, 3, 2, 4, 5)          # [B, H/2, W/2, 2, 2, C]
    x = x.reshape(B, H//2, W//2, 4*C)      # [B, H/2, W/2, 4C]
    x = linear(4*C, 2*C)                   # 降维
    return x
```

通过 Patch Merging，特征图尺寸逐层减半，通道数逐层翻倍（×2），总计算量被有效控制。

---

## 3. SWIN 在 VLN 中的应用

### 3.1 视觉特征提取

在 VLN 任务中，SWIN Transformer 通常作为**视觉编码器**使用：

```
VLN视觉编码流程:
原始RGB图像 → SWIN-T/S/B → 多尺度视觉特征 → 与语言特征融合
```

相比 ResNet，SWIN 能提供：
- **更强的全局建模能力**：移位窗口注意力使不同区域的视觉信息有效交互
- **多尺度特征**：适合识别室内场景中不同大小的物体（桌子、杯子、门）
- **与语言模型更好的对齐**：层级特征金字塔与语言指令中的多粒度描述（如"走过大桌子"）更易对齐

### 3.2 多尺度特征在导航中的作用

VLN 导航中，智能体需要同时理解：

| 尺度 | 示例 | 对应特征层 |
|------|------|-----------|
| 全局场景 | "你现在在客厅" | Stage 3/4（低分辨率、高语义） |
| 中等物体 | "绕过沙发" | Stage 2（中等尺度） |
| 细小物体 | "拿起桌上的水杯" | Stage 1（高分辨率、细节纹理） |

SWIN 的金子塔结构天然支持这种多尺度需求，可以从不同 Stage 提取不同层级的特征，喂给后续的动作预测头或轨迹规划模块。

### 3.3 场景理解

室内VLN场景通常包含：
- **空间布局**：房间形状、家具摆放
- **地标物体**：沙发、茶几、书架
- **可通行区域**：门、走廊

SWIN 的层级特征能够：
1. **深层特征**捕获场景级语义（房间类型、空间关系）
2. **浅层特征**保留精确的几何纹理信息（门把手、边缘）
3. 通过多尺度融合，实现对导航指令的精确执行

---

## 4. 变体与改进

### 4.1 SWIN-B / SWIN-S / SWIN-T

SWIN Transformer 提供了三个规模的变体：

| 模型 | 通道数 $C$ | Block 数 | 参数量 | 适用场景 |
|------|-----------|---------|--------|----------|
| **SWIN-T** | 96 | $[2, 2, 6, 2]$ | 28M | 实时/嵌入式 |
| **SWIN-S** | 96 | $[2, 2, 18, 2]$ | 50M | 平衡性能 |
| **SWIN-B** | 128 | $[2, 2, 18, 2]$ | 88M | 高精度任务 |

### 4.2 SWIN-V2

SWIN-V2 针对初代 SWIN 进行了以下改进：

- **Log-spaced continuous position bias（对数空间连续位置偏置）**：解决高分辨率下位置偏置难以学习的问题
- **更强的训练策略**：包括大规模数据集预训练、更长的训练周期
- **更高的输入分辨率**：支持 $384 \times 384$ 或更高分辨率输入

### 4.3 针对 VLN 的优化

在实际VLN应用中，通常会对SWIN做以下定制：

- **特征插值**：将多尺度特征上采样到统一分辨率进行拼接
- **跨模态融合层**：在SWIN输出后接Cross-Attention层与语言特征交互
- **动作预测头**：在特征后接MLP或Transformer Decoder输出动作 logits

---

## 5. 代码实战

### 5.1 SWIN 模型实现

以下是一个简化版的 SWIN-T 模型实现，帮助你理解其核心结构：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class WindowAttention(nn.Module):
    """
    窗口注意力机制
    在不重叠的窗口内计算自注意力，支持常规窗口和移位窗口两种模式
    """
    def __init__(self, dim, num_heads, window_size=7, shift_size=0):
        super().__init__()
        self.dim = dim                    # 输入通道数
        self.num_heads = num_heads        # 注意力头数量
        self.head_dim = dim // num_heads  # 每个头的维度
        self.window_size = window_size    # 窗口大小（默认7x7）
        self.shift_size = shift_size       # 移位量（0表示不移位）
        
        # 相对位置偏置参数，用于编码像素间的相对位置关系
        self.relative_position_bias = nn.Parameter(
            torch.zeros(2 * window_size - 1, 2 * window_size - 1)
        )
        
        # QKV 三个线性变换层，将输入映射为Query、Key、Value
        self.qkv = nn.Linear(dim, dim * 3)
        # 输出投影层
        self.proj = nn.Linear(dim, dim)
        
        # 注册相对位置偏置的索引表，用于快速查询
        self._init_relative_position_index()
    
    def _init_relative_position_index(self):
        """初始化相对位置索引，用于构建相对位置偏置矩阵"""
        # 生成窗口内所有像素的坐标
        coords_h = torch.arange(self.window_size)
        coords_w = torch.arange(self.window_size)
        coords = torch.stack(torch.meshgrid(coords_h, coords_w, indexing='ij'))  # [2, M, M]
        # 展平坐标并计算相对位置
        coords_flat = coords.flatten(1)  # [2, M*M]
        relative_coords = coords_flat[:, :, None] - coords_flat[:, None, :]  # [2, M*M, M*M]
        # 转换到正值索引范围 [0, 2M-2]
        relative_coords = relative_coords.permute(1, 2, 0)  # [M*M, M*M, 2]
        relative_coords[:, :, 0] += self.window_size - 1
        relative_coords[:, :, 1] += self.window_size - 1
        relative_coords[:, :, 0] *= 2 * self.window_size - 1
        relative_position_index = relative_coords.sum(-1)  # [M*M, M*M]
        self.register_buffer("relative_position_index", relative_position_index)
    
    def forward(self, x):
        """
        前向传播
        x: [B, H, W, C] 输入特征图
        """
        B, H, W, C = x.shape
        
        # 如果启用了窗口移位，对特征图进行循环移位
        if self.shift_size > 0:
            # 循环移位：将右下角移动到左上角
            x = torch.roll(x, shifts=(-self.shift_size, -self.shift_size), dims=(1, 2))
        
        # 将空间维度展平为窗口序列，形状变为 [B, num_windows, M*M, C]
        num_windows = (H // self.window_size) * (W // self.window_size)
        x = x.view(B, H // self.window_size, self.window_size, 
                   W // self.window_size, self.window_size, C)
        x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
        x = x.view(B * num_windows, self.window_size * self.window_size, C)
        
        # QKV 投影
        qkv = self.qkv(x).reshape(B * num_windows, -1, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # [3, B*num_windows, num_heads, M*M, head_dim]
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        # 计算注意力分数
        scale = math.sqrt(self.head_dim)
        attn = (q @ k.transpose(-2, -1)) / scale  # [B*num_windows, num_heads, M*M, M*M]
        
        # 添加相对位置偏置
        relative_position_bias = self.relative_position_bias[
            self.relative_position_index.view(-1)
        ].view(self.window_size * self.window_size, self.window_size * self.window_size, -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous()
        attn = attn + relative_position_bias.unsqueeze(0)
        
        # Softmax归一化
        attn = F.softmax(attn, dim=-1)
        
        # 注意力加权求和
        x = (attn @ v).transpose(1, 2).reshape(B * num_windows, self.window_size * self.window_size, C)
        
        # 输出投影
        x = self.proj(x)
        
        # 恢复空间维度 [B, H, W, C]
        x = x.view(B, H // self.window_size, W // self.window_size, self.window_size, self.window_size, C)
        x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
        x = x.view(B, H, W, C)
        
        # 如果启用了移位，需要将特征图移回原位置（逆移位）
        if self.shift_size > 0:
            x = torch.roll(x, shifts=(self.shift_size, self.shift_size), dims=(1, 2))
        
        return x


class SwinTransformerBlock(nn.Module):
    """
    SWIN Transformer 块
    由一个常规窗口注意力（W-MSA）和一个移位窗口注意力（SW-MSA）组成
    移位机制使不同窗口之间能够交换信息
    """
    def __init__(self, dim, num_heads, window_size=7, shift_size=0):
        super().__init__()
        self.dim = dim
        self.shift_size = shift_size
        
        # 归一化层
        self.norm1 = nn.LayerNorm(dim)
        # 窗口注意力层
        self.attn = WindowAttention(dim, num_heads, window_size, shift_size)
        # FFN：两层全连接 + GELU激活
        self.norm2 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Linear(dim * 4, dim)
        )
    
    def forward(self, x):
        # W-MSA / SW-MSA 残差连接
        x = x + self.attn(self.norm1(x))
        # FFN 残差连接
        x = x + self.ffn(self.norm2(x))
        return x


class PatchMerging(nn.Module):
    """
    Patch合并层，用于实现层级降采样
    将相邻的 2x2 patches 拼接，并降维
    """
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.norm = nn.LayerNorm(4 * in_dim)
        self.linear = nn.Linear(4 * in_dim, out_dim)
    
    def forward(self, x):
        """
        x: [B, H, W, C]
        输出: [B, H//2, W//2, 2C]
        """
        B, H, W, C = x.shape
        
        # 将 2x2 邻域内的patch拼接
        x = x.view(B, H // 2, 2, W // 2, 2, C)
        x = x.permute(0, 1, 3, 2, 4, 5).contiguous()  # [B, H/2, W/2, 2, 2, C]
        x = x.view(B, H // 2, W // 2, 4 * C)           # [B, H/2, W/2, 4C]
        
        # 归一化 + 线性降维
        x = self.norm(x)
        x = self.linear(x)  # [B, H/2, W/2, 2C]
        return x


class SwinTransformerStage(nn.Module):
    """
    SWIN Transformer 的一个阶段
    包含若干个 SwinTransformerBlock + 可选的 PatchMerging
    """
    def __init__(self, dim, num_heads, window_size, depth, downsample=False):
        super().__init__()
        self.blocks = nn.ModuleList([
            SwinTransformerBlock(
                dim=dim,
                num_heads=num_heads,
                window_size=window_size,
                # 奇数层使用移位窗口，偶数层使用常规窗口
                shift_size=0 if i % 2 == 0 else window_size // 2
            )
            for i in range(depth)
        ])
        
        # 是否在该阶段末尾进行降采样（Patch Merging）
        self.downsample = PatchMerging(dim, dim * 2) if downsample else nn.Identity()
    
    def forward(self, x):
        for block in self.blocks:
            x = block(x)
        x = self.downsample(x)
        return x


class SwinTransformerTiny(nn.Module):
    """
    SWIN-T (Tiny) 模型
    完整结构：Stage1 -> Stage2 -> Stage3 -> Stage4
    """
    def __init__(self, num_classes=1000, window_size=7):
        super().__init__()
        self.window_size = window_size
        
        # Stage 1: 输入通道3 -> 输出通道96，分辨率 H/4 x W/4
        self.stage1 = SwinTransformerStage(
            dim=96, num_heads=3, window_size=window_size, depth=2, downsample=True
        )
        # Stage 2: 输入通道192 -> 输出通道192，分辨率 H/8 x W/8
        self.stage2 = SwinTransformerStage(
            dim=192, num_heads=6, window_size=window_size, depth=2, downsample=True
        )
        # Stage 3: 输入通道384 -> 输出通道384，分辨率 H/16 x W/16
        self.stage3 = SwinTransformerStage(
            dim=384, num_heads=12, window_size=window_size, depth=6, downsample=True
        )
        # Stage 4: 输入通道768 -> 输出通道768，分辨率 H/32 x W/32
        self.stage4 = SwinTransformerStage(
            dim=768, num_heads=24, window_size=window_size, depth=2, downsample=False
        )
        
        # 分类头
        self.norm = nn.LayerNorm(768)
        self.head = nn.Linear(768, num_classes)
        
        # 权重初始化
        self._init_weights()
    
    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)
    
    def forward(self, x):
        """
        x: [B, 3, H, W]
        返回: [B, num_classes] 分类 logits
        """
        # 初始 Patch Embedding: 4x4 卷积将通道从3降至96
        x = nn.functional.conv2d(x, weight=torch.eye(96).unsqueeze(-1).unsqueeze(-1) * 0.06,
                                  bias=None, stride=4, padding=0)
        x = x.permute(0, 2, 3, 1)  # [B, H/4, W/4, 96]
        
        # 四个Stage的前向传播
        x = self.stage1(x)
        x = self.stage2(x)
        x = self.stage3(x)
        x = self.stage4(x)
        
        # 全局平均池化 + 分类头
        x = x.mean(dim=[1, 2])  # [B, 768]
        x = self.norm(x)
        x = self.head(x)
        return x


if __name__ == "__main__":
    # 测试模型前向传播
    model = SwinTransformerTiny(num_classes=1000)
    
    # 模拟输入：batch=2, 3通道, 224x224图像
    x = torch.randn(2, 3, 224, 224)
    output = model(x)
    print(f"输入尺寸: {x.shape}")
    print(f"输出尺寸: {output.shape}")  # [2, 1000]
    print("SWIN-T 模型创建成功！")
```

### 5.2 窗口注意力机制详解

下面我们单独展示窗口注意力的核心逻辑，更直观地理解移位机制：

```python
import torch
import torch.nn.functional as F


def window_attention_single_window(q, k, v, head_dim):
    """
    在单个窗口内计算注意力
    q, k, v: [num_tokens, num_heads, head_dim]
    """
    scale = torch.sqrt(torch.tensor(head_dim, dtype=q.dtype))
    # Q @ K^T / sqrt(d) -> [num_tokens, num_heads, num_tokens]
    attn = torch.matmul(q, k.transpose(-2, -1)) / scale
    attn = F.softmax(attn, dim=-1)
    # 注意力加权值
    out = torch.matmul(attn, v)  # [num_tokens, num_heads, head_dim]
    return out


def shifted_window_partition(x, window_size=7, shift_size=3):
    """
    将特征图划分为移位窗口（循环移位方式）
    x: [B, H, W, C]
    返回: [B * num_windows, window_size, window_size, C]
    """
    B, H, W, C = x.shape
    
    # 循环移位：将右下区域移到左上
    x = torch.roll(x, shifts=(-shift_size, -shift_size), dims=(1, 2))
    
    # 划分窗口
    x = x.view(B, H // window_size, window_size, W // window_size, window_size, C)
    x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
    x = x.view(B * (H // window_size) * (W // window_size), window_size, window_size, C)
    return x


def compute_window_attention_with_shift(feature, window_size=7):
    """
    演示带移位的窗口注意力计算流程
    feature: [B, H, W, C] 输入特征图
    """
    B, H, W, C = feature.shape
    shift_size = window_size // 2
    
    # ====== Step 1: 常规窗口注意力（W-MSA）======
    # 划分常规窗口
    h_windows = H // window_size
    w_windows = W // window_size
    feature_windowed = feature.view(B, h_windows, window_size, w_windows, window_size, C)
    feature_windowed = feature_windowed.permute(0, 1, 3, 2, 4, 5).contiguous()
    feature_windowed = feature_windowed.view(B * h_windows * w_windows, 
                                             window_size * window_size, C)
    
    # 模拟 QKV（实际应用中通过线性层得到）
    qkv = torch.randn(B * h_windows * w_windows, window_size * window_size, 3, C)
    qkv = qkv / torch.sqrt(torch.tensor(C))
    q, k, v = qkv[:, :, 0], qkv[:, :, 1], qkv[:, :, 2]
    
    # 窗口内注意力
    attn_w = torch.matmul(q, k.transpose(-2, -1))
    attn_w = F.softmax(attn_w, dim=-1)
    out_w = torch.matmul(attn_w, v)
    print(f"常规窗口注意力输出形状: {out_w.shape}")
    
    # ====== Step 2: 移位窗口注意力（SW-MSA）======
    # 循环移位
    feature_shifted = torch.roll(feature, shifts=(-shift_size, -shift_size), dims=(1, 2))
    feature_shifted = feature_shifted.view(B, h_windows, window_size, w_windows, window_size, C)
    feature_shifted = feature_shifted.permute(0, 1, 3, 2, 4, 5).contiguous()
    feature_shifted = feature_shifted.view(B * h_windows * w_windows,
                                            window_size * window_size, C)
    
    # 同样计算注意力
    qkv_s = torch.randn(B * h_windows * w_windows, window_size * window_size, 3, C)
    qkv_s = qkv_s / torch.sqrt(torch.tensor(C))
    q_s, k_s, v_s = qkv_s[:, :, 0], qkv_s[:, :, 1], qkv_s[:, :, 2]
    
    attn_s = torch.matmul(q_s, k_s.transpose(-2, -1))
    attn_s = F.softmax(attn_s, dim=-1)
    out_s = torch.matmul(attn_s, v_s)
    
    # 逆移位
    out_s = out_s.view(B, h_windows, w_windows, window_size, window_size, C)
    out_s = out_s.permute(0, 1, 3, 2, 4, 5).contiguous()
    out_s = out_s.view(B, H, W, C)
    out_s = torch.roll(out_s, shifts=(shift_size, shift_size), dims=(1, 2))
    
    print(f"移位窗口注意力输出形状: {out_s.shape}")
    return out_w, out_s


# 测试代码
if __name__ == "__main__":
    feature = torch.randn(2, 56, 56, 96)  # 模拟 Stage2 的特征图
    out_w, out_s = compute_window_attention_with_shift(feature, window_size=7, shift_size=3)
    print("窗口注意力机制测试通过！")
```

### 5.3 视觉特征提取示例（SWIN + VLN）

以下示例展示如何用 SWIN 提取多尺度视觉特征，用于 VLN 导航任务：

```python
import torch
import torch.nn as nn


class SWINVisualEncoder(nn.Module):
    """
    SWIN视觉编码器，用于VLN任务
    输出多尺度特征，支持与语言指令的跨模态融合
    """
    def __init__(self, model_name='swin_tiny'):
        super().__init__()
        
        # 使用 timm 库加载预训练的 SWIN 模型
        try:
            import timm
            self.backbone = timm.create_model(
                model_name,
                pretrained=True,
                features_only=True  # 获取多尺度特征
            )
            # 获取各阶段输出通道数
            self.feature_channels = self.backbone.feature_info.channels()
            print(f"SWIN 特征通道: {self.feature_channels}")
        except ImportError:
            print("timm 未安装，使用自定义 SWIN 模型")
            self.backbone = SwinTransformerTiny(num_classes=1000)
            self.feature_channels = [96, 192, 384, 768]
    
    def forward(self, x):
        """
        x: [B, 3, H, W] 输入RGB图像
        返回: 多尺度特征字典
        """
        # 多尺度特征列表
        features = self.backbone(x)  # 通过 timm 获取多层特征
        
        # 将各层特征统一调整到相同分辨率进行融合
        target_h, target_w = features[0].shape[2], features[0].shape[3]
        
        # 上采样低分辨率特征到最高分辨率
        resized_features = []
        for feat in features:
            if feat.shape[2:] != (target_h, target_w):
                feat = nn.functional.interpolate(
                    feat, size=(target_h, target_w), mode='bilinear', align_corners=False
                )
            resized_features.append(feat)
        
        # 通道维度拼接：融合多尺度信息
        fused = torch.cat(resized_features, dim=1)  # [B, C_total, H, W]
        
        # 降维到统一通道数（如 512），便于与语言特征对齐
        projected = nn.Conv2d(
            in_channels=fused.shape[1],
            out_channels=512,
            kernel_size=1
        )(fused)
        
        return {
            'multi_scale': resized_features,  # 各尺度特征列表
            'fused': projected,              # 融合后统一特征 [B, 512, H, W]
        }


class VLNCrossModalFusion(nn.Module):
    """
    跨模态融合模块：将SWIN视觉特征与语言特征融合
    用于VLN的动作预测
    """
    def __init__(self, vision_dim=512, lang_dim=768, hidden_dim=512):
        super().__init__()
        # 视觉投影：将视觉特征映射到共享语义空间
        self.vision_proj = nn.Linear(vision_dim, hidden_dim)
        # 语言投影：将语言特征映射到共享语义空间
        self.lang_proj = nn.Linear(lang_dim, hidden_dim)
        # 跨模态注意力：视觉查询语言
        self.cross_attn = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=8,
            dropout=0.1
        )
        # 输出层
        self.output_norm = nn.LayerNorm(hidden_dim)
        self.action_head = nn.Linear(hidden_dim, 4)  # 4个动作：前进/左转/右转/停止
    
    def forward(self, vision_feat, lang_feat):
        """
        vision_feat: [B, C, H, W] SWIN提取的视觉特征
        lang_feat: [B, L, lang_dim] 语言特征（如BERT输出）
        """
        B, C, H, W = vision_feat.shape
        
        # 空间维度展平：空间信息保留在序列中
        vision_feat = vision_feat.permute(0, 2, 3, 1)  # [B, H, W, C]
        vision_seq = vision_feat.reshape(B, H * W, C)  # [B, H*W, C]
        
        # 投影到统一维度
        vision_seq = self.vision_proj(vision_seq)  # [B, H*W, hidden_dim]
        lang_feat = self.lang_proj(lang_feat)        # [B, L, hidden_dim]
        
        # 跨模态注意力：语言指导视觉特征选择
        # encoder: 视觉序列，keys/values；decoder: 语言序列，queries
        fused, attn_weights = self.cross_attn(
            query=lang_feat,
            key=vision_seq,
            value=vision_seq
        )
        
        # 全局平均池化得到全局视觉-语言表征
        global_feat = fused.mean(dim=1)  # [B, hidden_dim]
        global_feat = self.output_norm(global_feat)
        
        # 动作预测
        action_logits = self.action_head(global_feat)  # [B, 4]
        return action_logits, attn_weights


if __name__ == "__main__":
    # 示例：SWIN视觉编码 + VLN跨模态融合
    encoder = SWINVisualEncoder(model_name='swin_tiny')
    
    # 模拟输入：batch=4, 3通道, 224x224图像
    images = torch.randn(4, 3, 224, 224)
    vision_out = encoder(images)
    print(f"融合视觉特征形状: {vision_out['fused'].shape}")
    
    # 模拟语言特征（假设来自BERT）
    lang_features = torch.randn(4, 20, 768)  # batch=4, 序列长度=20, BERT维度=768
    
    # 跨模态融合 + 动作预测
    vln_fusion = VLNCrossModalFusion(vision_dim=512, lang_dim=768, hidden_dim=512)
    action_logits, attn = vln_fusion(vision_out['fused'], lang_features)
    
    print(f"动作预测logits: {action_logits.shape}")  # [4, 4]
    print("VLN视觉-语言融合测试通过！")
```

---

## 6. 练习题

### 6.1 选择题

1. **SWIN Transformer 中，移位窗口（Shifted Window）机制的主要目的是？**
   
   A. 降低模型参数量
   
   B. 实现不同窗口之间的信息交互
   
   C. 加快推理速度
   
   D. 减少GPU显存占用


2. **在 SWIN 的金子塔结构中，随着层级的加深，特征图的分辨率如何变化？**
   
   A. 分辨率逐渐增大
   
   B. 分辨率逐渐减小（降采样）
   
   C. 分辨率保持不变
   
   D. 先减小后增大

3. **Patch Merging 操作的作用是？**
   
   A. 增加特征图分辨率
   
   B. 将相邻Patch拼接并降维，实现通道翻倍和分辨率减半
   
   C. 增加注意力感受野
   
   D. 实现跨模态融合

4. **SWIN-T 与 SWIN-B 的主要区别在于？**
   
   A. 注意力头数量不同
   
   B. Stage数量不同
   
   C. 通道数和Block堆叠深度不同
   
   D. 是否使用移位窗口

5. **SWIN Transformer 在 VLN 任务中的主要作用是？**
   
   A. 动作执行
   
   B. 视觉特征编码
   
   C. 语言理解
   
   D. 路径规划

### 6.2 简答题

1. **请描述 SWIN Transformer 的层级式设计相比 ViT 全局注意力的优势。**

2. **解释为什么需要交替使用 W-MSA 和 SW-MSA，不能只用 W-MSA 吗？**

3. **在 VLN 导航中，为什么 SWIN 的多尺度特征比单一尺度特征更有优势？**

4. **Patch Merging 如何实现通道数翻倍和分辨率减半？请用数学表达式描述。**

### 6.3 编程题

1. **实现一个简化的 Patch Partition 模块，将 $H \times W \times 3$ 的图像转换为 $[B, H/4, W/4, 48]$ 的 Patch 表示。**

2. **修改 `WindowAttention` 类，使其支持自定义的注意力头数量。**

3. **设计一个函数，输入 SWIN 的四层多尺度特征，输出通道拼接后的融合特征（所有特征上采样到第一层的分辨率）。**

---

## 7. 答案

### 7.1 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | 移位窗口使相邻窗口之间产生重叠区域，从而实现跨窗口的信息交互，避免窗口间语义割裂 |
| 2 | **B** | 随着Stage加深，Patch Merging 使分辨率逐层减半（如 $H/4 \rightarrow H/8 \rightarrow H/16 \rightarrow H/32$），通道数翻倍 |
| 3 | **B** | Patch Merging 将 $2\times2$ 邻域Patch拼接为 $4C$ 维向量，经线性层降维到 $2C$，实现降采样和通道扩展 |
| 4 | **C** | SWIN-T/S/B 的差异主要体现在通道数 $C$（96 vs 128）和每Stage的Block深度上 |
| 5 | **B** | SWIN在VLN中作为视觉编码器，提取多尺度视觉特征，与语言特征融合后进行导航决策 |

### 7.2 简答题答案

**1. SWIN 层级式设计相比 ViT 全局注意力的优势：**

- **计算效率**：窗口注意力复杂度为 $O(N)$ 而非 $O(N^2)$，高分辨率下优势显著
- **多尺度建模**：层级结构类似 CNN 金字塔，浅层保留细节，深层捕获语义
- **适合密集预测任务**：分类用全局特征，检测/分割/导航需要局部细节，SWIN 兼顾两者
- **更强的归纳偏置**：局部窗口提供了空间局部性的先验，减少对大规模数据的依赖

**2. 为什么需要交替使用 W-MSA 和 SW-MSA：**

仅使用 W-MSA 时，每个窗口内独立计算注意力，窗口之间没有任何信息交互，导致**窗口边界处的语义断裂**——窗口 A 左下角的 Patch 和窗口 B 右上角的相邻 Patch 完全不知道彼此的存在。

通过交替使用移位窗口（SW-MSA），窗口整体偏移半个窗口大小，原本不相邻的 Patch 被划入同一窗口，从而在下一个 Block 中建立跨窗口联系。经过多次交替堆叠，信息可以在整个特征图上有效传播。

**3. SWIN 多尺度特征在 VLN 中的优势：**

室内导航场景包含不同尺度的视觉元素：

| 层级 | 分辨率 | 适合感知 |
|------|--------|---------|
| Stage 1 | $H/4$ | 细小物体（杯子、遥控器） |
| Stage 2 | $H/8$ | 家具（椅子、桌子） |
| Stage 3 | $H/16$ | 房间结构（门、墙） |
| Stage 4 | $H/32$ | 场景语义（厨房vs卧室） |

单一尺度特征难以同时满足细粒度感知和全局语义理解的需求，多尺度融合可以让智能体在判断"绕过障碍物"的同时保持对"目标房间在哪里"的全局感知。

**4. Patch Merging 的数学表达：**

设输入特征为 $X \in \mathbb{R}^{H \times W \times C}$，Patch Merging 将其划分为 $\frac{H}{2} \times \frac{W}{2}$ 个 $2\times2$ 邻域，每个邻域拼接后得到：

$$X'_{i,j} = \text{Concat}(X_{2i,2j}, X_{2i+1,2j}, X_{2i,2j+1}, X_{2i+1,2j+1}) \in \mathbb{R}^{4C}$$

然后经线性层 $W \in \mathbb{R}^{4C \times 2C}$ 降维：

$$Y_{i,j} = W^T \cdot X'_{i,j} \in \mathbb{R}^{2C}$$

最终输出 $Y \in \mathbb{R}^{H/2 \times W/2 \times 2C}$，分辨率减半，通道数翻倍。

### 7.3 编程题答案

**编程题 1：Patch Partition 实现**

```python
import torch

def patch_partition(images, patch_size=4):
    """
    将图像划分为不重叠的Patch
    images: [B, 3, H, W] 原始RGB图像
    patch_size: 每个patch的边长（默认4）
    返回: [B, H/patch_size, W/patch_size, patch_size*patch_size*3]
    """
    B, C, H, W = images.shape
    
    # 展平每个patch: 将图像划分为 H/patch_size x W/patch_size 个patch
    # [B, C, H, W] -> [B, H/patch_size, patch_size, W/patch_size, patch_size, C]
    x = images.unfold(2, patch_size, patch_size)     # 在H维度上滑动窗口
    x = x.unfold(3, patch_size, patch_size)          # 在W维度上滑动窗口
    # x: [B, H/ps, W/ps, C, ps, ps]
    
    # 调整维度顺序并展平
    x = x.permute(0, 1, 3, 2, 4, 5)  # [B, H/ps, W/ps, ps, ps, C]
    patches = x.reshape(B, H // patch_size, W // patch_size, 
                        patch_size * patch_size * C)  # [B, H/4, W/4, 48]
    return patches


# 测试
if __name__ == "__main__":
    images = torch.randn(2, 3, 224, 224)
    patches = patch_partition(images, patch_size=4)
    print(f"输入: {images.shape} -> 输出: {patches.shape}")  # [2, 56, 56, 48]
```

**编程题 2：支持自定义注意力头数量**

```python
class WindowAttentionFlexibleHeads(nn.Module):
    """
    支持自定义注意力头数量的窗口注意力
    """
    def __init__(self, dim, num_heads=3, window_size=7, shift_size=0):
        super().__init__()
        assert dim % num_heads == 0, "dim 必须能被 num_heads 整除"
        self.dim = dim
        self.num_heads = num_heads
        self.head_dim = dim // num_heads
        self.window_size = window_size
        self.shift_size = shift_size
        
        # QKV 投影
        self.qkv = nn.Linear(dim, dim * 3)
        self.proj = nn.Linear(dim, dim)
        
        # 相对位置偏置（可学习）
        self.relative_position_bias = nn.Parameter(
            torch.zeros(2 * window_size - 1, 2 * window_size - 1)
        )
        self._init_relative_position_index()
    
    def _init_relative_position_index(self):
        coords_h = torch.arange(self.window_size)
        coords_w = torch.arange(self.window_size)
        coords = torch.stack(torch.meshgrid(coords_h, coords_w, indexing='ij'))
        coords_flat = coords.flatten(1)
        relative_coords = coords_flat[:, :, None] - coords_flat[:, None, :]
        relative_coords = relative_coords.permute(1, 2, 0)
        relative_coords[:, :, 0] += self.window_size - 1
        relative_coords[:, :, 1] += self.window_size - 1
        relative_coords[:, :, 0] *= 2 * self.window_size - 1
        relative_position_index = relative_coords.sum(-1)
        self.register_buffer("relative_position_index", relative_position_index)
    
    def forward(self, x):
        B, H, W, C = x.shape
        
        if self.shift_size > 0:
            x = torch.roll(x, shifts=(-self.shift_size, -self.shift_size), dims=(1, 2))
        
        num_windows = (H // self.window_size) * (W // self.window_size)
        x = x.view(B, H // self.window_size, self.window_size,
                   W // self.window_size, self.window_size, C)
        x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
        x = x.view(B * num_windows, self.window_size * self.window_size, C)
        
        qkv = self.qkv(x).reshape(B * num_windows, -1, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]
        
        scale = torch.sqrt(torch.tensor(self.head_dim, dtype=q.dtype))
        attn = (q @ k.transpose(-2, -1)) / scale
        
        relative_position_bias = self.relative_position_bias[
            self.relative_position_index.view(-1)
        ].view(self.window_size * self.window_size, self.window_size * self.window_size, -1)
        relative_position_bias = relative_position_bias.permute(2, 0, 1).contiguous()
        attn = attn + relative_position_bias.unsqueeze(0)
        
        attn = F.softmax(attn, dim=-1)
        x = (attn @ v).transpose(1, 2).reshape(B * num_windows, self.window_size * self.window_size, C)
        x = self.proj(x)
        
        x = x.view(B, H // self.window_size, W // self.window_size, self.window_size, self.window_size, C)
        x = x.permute(0, 1, 3, 2, 4, 5).contiguous()
        x = x.view(B, H, W, C)
        
        if self.shift_size > 0:
            x = torch.roll(x, shifts=(self.shift_size, self.shift_size), dims=(1, 2))
        return x
```

**编程题 3：多尺度特征融合**

```python
def fuse_multiscale_features(multi_scale_features):
    """
    将SWIN的多尺度特征上采样到统一分辨率并拼接
    multi_scale_features: list of [B, C_i, H_i, W_i]，从浅到深的特征列表
    返回: [B, C_total, H_0, W_0] 融合特征
    """
    # 以最浅层（最高分辨率）的特征为目标分辨率
    target_h, target_w = multi_scale_features[0].shape[2], multi_scale_features[0].shape[3]
    
    resized = []
    for feat in multi_scale_features:
        if feat.shape[2:] != (target_h, target_w):
            feat = nn.functional.interpolate(
                feat, size=(target_h, target_w), mode='bilinear', align_corners=False
            )
        resized.append(feat)
    
    # 在通道维度拼接
    fused = torch.cat(resized, dim=1)  # [B, C0+C1+C2+C3, H0, W0]
    return fused


# 测试
if __name__ == "__main__":
    # 模拟SWIN的4层多尺度特征
    f0 = torch.randn(2, 96, 56, 56)   # Stage1
    f1 = torch.randn(2, 192, 28, 28)  # Stage2
    f2 = torch.randn(2, 384, 14, 14)  # Stage3
    f3 = torch.randn(2, 768, 7, 7)    # Stage4
    
    multi_scale = [f0, f1, f2, f3]
    fused = fuse_multiscale_features(multi_scale)
    print(f"融合特征形状: {fused.shape}")  # [2, 1440, 56, 56]
```

---

> **小结**：本节我们系统学习了 SWIN Transformer 的核心设计——层级式结构、移位窗口注意力（SW-MSA）和 Patch Merging，并深入探讨了其在 VLN 视觉语言导航任务中的应用。SWIN 通过窗口划分将计算复杂度从 $O(N^2)$ 降至 $O(N)$，同时通过交替移位机制实现跨窗口信息交互，兼顾了局部建模效率和全局感受野。在 VLN 中，SWIN 的多尺度金子塔特征为智能体提供了从细节纹理到全局场景语义的完整视觉表征，是现代 VLN 系统视觉编码器的核心支柱。

