# 17-2 CLIPORT 算法解析

> **前置课程**：17-1 VLN基础介绍
> **后续课程**：17-3 VLN 视觉语言导航

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：CLIPORT 是视觉-语言-动作（VLA）领域的重要模型，它将 CLIP 的语义理解能力与 Transporter Networks 的空间变换机制巧妙结合，实现了"语义+空间"双驱动的机器人操控。本节将深入解析 CLIPORT 的设计动机、模型架构、训练方法和代码实现，帮助你理解如何用视觉-语言预训练模型赋能机器人操控任务。

---

## 1. CLIPORT 概述

### 1.1 背景——语义理解与空间推理的双重挑战

在机器人操控任务中，智能体面临两个核心挑战：

1. **语义理解**：理解"把红色的积木放到蓝色的盒子旁边"这样的语言指令，并识别对应的物体
2. **空间推理**：精确定位"哪里是红色积木"、"蓝色盒子旁边是哪里"，执行精确的抓取和放置动作

传统方法通常将这两个问题分开处理：先用检测模型识别物体，再用手工设计的规则计算动作目标。然而，这种分离式方法存在明显缺陷：
- 需要大量针对特定任务的标注数据
- 难以泛化到新物体、新场景
- 语义和空间信息分离处理，信息利用不充分

**CLIPORT** 的核心思想是：让语义理解和空间推理在同一个模型中协同工作。CLIP 提供强大的语义先验，Transporter Networks 提供精确的空间操作能力，两者结合，诞生了 CLIPORT。

### 1.2 CLIPORT 是什么？

**CLIPORT**（CLIP + Transporter）是一个视觉-语言-动作（VLA）模型，专门用于机器人桌面操控任务（pick-and-place）。它的设计哲学是：

> **"语义即空间，空间即语义"**

即：CLIP 的语义特征不仅用于"理解"语言，还直接参与空间动作的预测；Transporter Networks 的空间变换机制不仅用于定位，还同时编码了语义信息。

从论文标题 *"`CLIPORT: What Else Does the Robot Need to Know?`"* 可以看出，作者在问一个深刻的问题：除了 CLIP 已经知道的语义知识之外，机器人还需要什么？答案是——**精确的空间操作能力**，而这正是 Transporter Networks 所提供的。

### 1.3 Transporter Networks 基础

理解 CLIPORT 之前，需要先理解 **Transporter Networks**。这是 2020 年由 Zachary et al. 提出的一个用于机器人操控的框架，其核心思想是：

**把"在哪里抓"和"放在哪里"问题，转化为"在哪里复制特征，在哪里粘贴特征"的问题**

具体来说，Transporter Networks 不直接预测坐标点，而是预测两个特征图（feature map）之间的空间变换：

$$
\mathcal{T} = \text{Transporter}(I, \theta)
$$

其中 $I$ 是输入图像，$\theta$ 是网络参数，$\mathcal{T}$ 是一个二维空间变换场（spatial transformation field）。

**工作原理**：

1. **编码器**：将输入图像 $I$ 编码为特征图 $F$
2. **解码器（Keypoint Decoder）**：从 $F$ 预测一组关键点（keypoints）
3. **空间查询（Query）**：以关键点为中心提取局部特征
4. **空间变换（Transport）**：将提取的特征"搬运"到目标位置附近
5. **动作输出**：基于变换后的特征图，预测最终的动作参数（抓取位姿、放置位姿）

**为什么叫 Transporter（搬运工）？**

因为它的核心操作是"从源区域复制特征，粘贴到目标区域"。这个"搬运"操作本身，就是一种隐式的空间推理——模型在学习"哪里的特征应该去哪里"。

### 1.4 端到端设计

CLIPORT 继承了 Transporter Networks 的端到端设计，但将视觉编码器从普通 CNN 替换为 **CLIP 视觉编码器**，并新增了 **语言分支**。这意味着：

- 输入：图像 + 语言指令 → 输出：动作（抓取位姿 + 放置位姿）
- 整个 pipeline 可以端到端梯度训练
- 语言指令的语义信息可以影响每一个空间操作决策

---

## 2. CLIPORT 架构

### 2.1 整体架构

CLIPORT 的整体架构可以概括为"两条路径、一个融合、两个输出"：

```
输入：RGB图像 + 语言指令
    ↓                    ↓
视觉编码器（CLIP）    语言编码器（CLIP Text）
    ↓                    ↓
视觉特征图 F_v     语言特征向量 f_l
    ↓                    ↓
    ===== 交叉融合 =====
    ↓                    ↓
    空间动作头（Action Head）
    ↓                    ↓
输出：抓取位姿 (pick) + 放置位姿 (place)
```

### 2.2 视觉编码器（CLIP）

CLIPORT 的视觉编码器使用的是 **CLIP（Contrastive Language-Image Pre-training）** 的预训练视觉编码器。CLIP 由 OpenAI 在 2021 年提出，其核心是通过对比学习，让图像和文本在统一的向量空间中表示。

**CLIP 的核心思想**：

给定一批图文对 $(I_i, T_i)$，CLIP 训练一个视觉编码器 $E_v$ 和一个文本编码器 $E_t$，使得配对的图像-文本对在特征空间中距离更近，不配对的距离更远：

$$\mathcal{L} = -\log \frac{\exp(\text{sim}(E_v(I_i), E_t(T_i)) / \tau)}{\sum_j \exp(\text{sim}(E_v(I_i), E_t(T_j)) / \tau)}$$

其中 $\text{sim}(\cdot, \cdot)$ 是余弦相似度，$\tau$ 是温度参数。

**CLIPORT 中 CLIP 的作用**：

CLIP 为 CLIPORT 提供了两个关键能力：

1. **零样本语义泛化**：CLIP 在 4 亿图文对的大规模数据上预训练过，能够识别大量视觉概念。即使是新物体，只要能通过语言描述，CLIPORT 就能理解
2. **语言-视觉统一表示**：语言指令和视觉图像被编码到同一个特征空间，交叉融合更自然

### 2.3 动作预测头（Action Head）

CLIPORT 的动作预测头继承了 Transporter Networks 的设计，但做了关键改进。

#### 2.3.1 隐式 Affordance Map

CLIPORT 的核心是预测两张 **affordance map**（可供性地图）：

| Map | 含义 | 作用 |
|-----|------|------|
| **Pick Affordance** | 每个像素作为"抓取点"的得分 | 指示"从哪里抓" |
| **Place Affordance** | 每个像素作为"放置点"的得分 | 指示"放到哪里" |

两张 map 的尺寸与输入图像相同（通常是 224×224 或 320×320），每个像素的值代表在该位置执行动作的"适合度"。

**数学表达**：

$$M_{pick} = \text{Head}_{pick}(F_{fused})$$
$$M_{place} = \text{Head}_{place}(F_{fused})$$

其中 $F_{fused}$ 是融合后的特征图。

#### 2.3.2 抓取和放置解耦

CLIPORT 的一个重要设计决策是：**抓取（pick）和放置（place）的预测是解耦的**。

具体来说：
- **Pick Head**：预测抓取位置的概率分布 $P_{pick}(x, y)$
- **Place Head**：预测放置位置的概率分布 $P_{place}(x, y | x_{pick})$

这意味着：
- 放置位置的预测以抓取位置为条件（因为需要先抓住物体，才能谈放置）
- 但两者共享 $F_{fused}$ 的语义特征，因此语义信息可以同时指导抓取和放置决策

#### 2.3.3 动作输出

从 affordance map 到实际机器人动作，需要一步转换：

```python
# 从 affordance map 提取最终动作（伪代码）
def get_action(affordance_map, num_samples=16, temperature=1.0):
    """
    从 affordance map 中采样候选位置
    affordance_map: H x W 的热力图
    """
    # 1. 使用 softmax 将 map 转为概率分布
    prob = softmax(affordance_map / temperature)
    
    # 2. 采样 num_samples 个候选点
    indices = np.random.choice(
        H * W, size=num_samples, p=prob.flatten(), replace=False
    )
    
    # 3. 取概率最高的点作为最终决策
    best_idx = indices[0]
    y, x = best_idx // W, best_idx % W
    
    return (x, y)  # 返回像素坐标
```

**为什么需要采样而不是直接取最大值？**

因为在训练时，我们希望损失函数能看到整个分布（软目标），而不仅仅是最大值点；在推理时，通过采样可以增加动作的多样性。

### 2.4 空间变换机制

这是 CLIPORT 相对于原始 Transporter Networks 的核心改进所在。

#### 2.4.1 语言引导的空间查询

在 Transporter Networks 中，空间查询（query）是随机初始化的可学习向量。而在 CLIPORT 中，空间查询由**语言特征**引导：

$$Q = \text{MLP}(f_l)$$

其中 $f_l$ 是 CLIP 文本编码器输出的语言特征向量，MLP 是一个多层感知机，将语言特征投影为空间查询向量。

这个设计让语言指令**主动引导**了空间注意力的分布：
- "拿起红色的积木" → 语言特征驱动注意力集中在红色物体区域
- "放到蓝色盒子旁边" → 语言特征驱动注意力集中在蓝色盒子附近

#### 2.4.2 跨模态注意力

CLIPORT 的特征融合通过一个**跨模态注意力层**实现：

$$F_{fused} = \text{CrossAttention}(Q=K_{视觉}, K=\text{LN}(F_v), V=\text{LN}(F_v))$$

其中：
- $Q$（Query）来自语言特征 $f_l$ 的投影
- $K, V$（Key, Value）来自 CLIP 视觉编码器的特征 $F_v$
- LN 是层归一化

这个设计让语言特征"查询"视觉特征，生成语义条件化的空间特征图。

#### 2.4.3 残差连接

为了保留原始视觉特征的细粒度空间信息，CLIPORT 在融合后保留了残差连接：

$$F_{out} = F_{fused} + F_v$$

这确保了高层的语义信息和低层的空间细节不会在融合过程中丢失。

---

## 3. 训练方法

### 3.1 模仿学习（Imitation Learning）

CLIPORT 的训练核心是**行为克隆（Behavior Cloning）**——让模型模仿专家演示来学习策略。

**训练数据**：

训练数据是一组轨迹演示 $\mathcal{D} = \{(\text{image}_t, \text{language}_t, \text{action}_t)\}$，其中：
- $\text{image}_t$：第 $t$ 步的 RGB 图像
- $\text{language}_t$：描述当前任务的语言指令（如"把红色的方块放到左边"）
- $\text{action}_t = (x_{pick}, y_{pick}, x_{place}, y_{place})$：专家标注的抓取和放置位置（像素坐标）

**损失函数**：

CLIPORT 使用负对数似然损失（NLL）作为主要损失：

$$\mathcal{L} = -\sum_{(x_p, y_p) \in \mathcal{D}_{pick}} \log P_{pick}(x_p, y_p) - \sum_{(x_{pl}, y_{pl}) \in \mathcal{D}_{place}} \log P_{place}(x_{pl}, y_{pl} | x_p, y_p)$$

其中 $P_{pick}$ 和 $P_{place}$ 是模型预测的概率分布（从 affordance map 经 softmax 得到）。

**通俗理解**：让模型对专家标注的位置给予高概率，对其他位置给予低概率。

### 3.2 语义增强（Semantic Augmentation）

CLIPORT 的一个重要训练技巧是**语义增强**。由于 CLIP 本身具有强大的语义泛化能力，CLIPORT 在训练时会随机替换语言指令中的物体名称，以增加数据多样性：

```python
# 原始训练样本
{"image": img, "language": "pick the red block", "action": (100, 120, 200, 180)}

# 语义增强后的样本（图像和动作不变，仅改变语言描述）
{"image": img, "language": "pick the yellow block", "action": (100, 120, 200, 180)}
{"image": img, "language": "pick the green object", "action": (100, 120, 200, 180)}
```

**关键点**：
- 图像和动作保持不变
- 仅改变语言指令的表述
- 利用 CLIP 的语义理解能力，让模型学会"不依赖特定词汇"的泛化

### 3.3 数据集

CLIPORT 的实验主要在以下数据集上进行：

#### （1）Language-table 数据集

这是 CLIPORT 论文提出的一个桌面操控数据集，包含：
- **真实环境**：在真实桌面上用真实物体采集的数据
- **仿真环境**：用 Blender 渲染的合成图像
- **任务类型**：推（push）、抓取（grasp）两类动作
- **语言指令**：简单的自然语言描述（如"把绿色方块推到左边"）

#### （2）RLBench 数据集

CLIPORT 也在 **RLBench** 上进行了评估，这是一个标准化的机器人 benchmark，包含 100 个预定义任务。

### 3.4 训练配置

| 配置项 | 值 |
|--------|-----|
| 视觉编码器 | CLIP ViT-B/32 |
| 语言编码器 | CLIP Text Transformer |
| 图像分辨率 | 224×224 |
| 优化器 | AdamW |
| 学习率 | 1e-4（CLIP编码器）/ 1e-3（随机初始化部分） |
| Batch Size | 64 |
| 训练 epoch | 100 |
| 温度参数 | 1.0（用于 softmax 归一化） |

**重要技巧**：CLIP 编码器的学习率通常是随机初始化部分的 **1/10**，这是因为 CLIP 预训练权重已经包含了非常丰富的语义信息，过高的学习率会破坏这些表征。

---

## 4. 能力表现

### 4.1 语义泛化

CLIPORT 最显著的能力是**零样本语义泛化**——它能够处理训练集中从未出现过的物体类别和语言描述。

**实验结果**：

在 Language-table 数据集上，CLIPORT 对新物体的泛化实验：

| 条件 | 成功率 |
|------|--------|
| seen objects（见过） | 95% |
| unseen objects, seen colors（新物体，旧颜色） | 89% |
| unseen objects, unseen colors（新物体，新颜色） | 76% |

**分析**：
- 即使是完全新的物体和颜色组合，CLIPORT 仍能保持较高成功率
- CLIP 的预训练知识在其中起到了关键作用——模型能理解"红色"、"方块"这些概念的视觉特征

### 4.2 空间推理

CLIPORT 的空间推理能力继承了 Transporter Networks 的精确性：

| 任务 | 精度 |
|------|------|
| 抓取位置误差 | < 2cm |
| 放置位置误差 | < 3cm |
| 旋转角度误差 | < 15° |

**这意味着**：CLIPORT 不仅能理解"抓什么"、"放哪里"，还能精确到像素级别地定位目标位置。

### 4.3 效率分析

CLIPORT 的推理效率较高，适合实时控制：

| 指标 | 值 |
|------|-----|
| 推理速度 | ~10 FPS（单卡 RTX 2080Ti） |
| 模型参数量 | ~151M（基于 CLIP ViT-B/32） |
| 内存占用 | ~2GB |

**对比**：相比需要额外检测网络的 Pipeline 方法，CLIPORT 的端到端设计避免了重复的特征提取，效率更高。

---

## 5. 与其他模型对比

### 5.1 FLAT

**FLAT**（Fast Language-Assisted Manipulation Transformer）是另一个视觉-语言-动作模型，与 CLIPORT 有不同的设计理念。

| 维度 | CLIPORT | FLAT |
|------|---------|------|
| **基础架构** | CLIP + Transporter | Transformer（Perceiver IO） |
| **动作表示** | Affordance Map（热力图） | 离散动作 token |
| **空间推理** | 隐式（通过热力图） | 显式（通过 attention） |
| **语义泛化** | 强（CLIP 预训练） | 中等（需微调） |
| **推理速度** | 快（~10 FPS） | 慢（~2-3 FPS） |
| **适用任务** | 桌面操控（push/grasp） | 多种操控任务 |

**核心区别**：FLAT 使用离散的 action token 输出动作，而 CLIPORT 使用连续的热力图。这让 CLIPORT 在空间精度上更有优势，而 FLAT 在动作多样性上可能更灵活。

### 5.2 CLIP on Wheels

**CLIP on Wheels**（CoW）是一个基于 CLIP 的 VLN/VLA 模型系列，专门用于**轮式移动机器人**的导航任务。

| 维度 | CLIPORT | CLIP on Wheels |
|------|---------|----------------|
| **任务类型** | 桌面操控（pick-place） | 室内导航 |
| **动作空间** | 连续像素坐标 | 离散导航动作 |
| **环境** | 桌面/仿真 | 房间/建筑 |
| **关键能力** | 精确空间操作 | 大范围语义导航 |
| **模型规模** | ~151M | ~151M-400M |

**互补性**：CLIPORT 擅长"精细操作"，CLIP on Wheels 擅长"粗略导航"。两者可以组合使用——用 CLIP on Wheels 做导航，用 CLIPORT 做最终的物体操控。

### 5.3 优劣势分析

#### CLIPORT 的优势

1. **强大的语义泛化**：得益于 CLIP 的预训练，CLIPORT 可以处理从未见过的物体
2. **端到端训练**：不需要额外的检测、分割网络，简化了部署
3. **精确的空间操作**：继承了 Transporter Networks 的高精度定位能力
4. **语言引导的注意力**：语言指令能够直接引导空间注意力的分布

#### CLIPORT 的劣势

1. **任务类型受限**：主要针对桌面操控的 push/grasp 任务，不适合复杂的多步骤任务
2. **需要演示数据**：依赖专家演示数据进行行为克隆，数据收集成本较高
3. **空间范围有限**：affordance map 是像素级的，空间操作范围受输入图像视野限制
4. **缺乏动作序列建模**：每次只输出一个动作（抓取或放置），不直接支持多步骤规划

#### CLIPORT 的改进方向

- **多步骤扩展**：结合分层规划，让 CLIPORT 能够执行复杂任务序列
- **强化学习增强**：通过 RL 弥补模仿学习的分布偏移问题
- **3D 表示增强**：将 2D affordance map 扩展到 3D，提升空间操作精度

---

## 6. 代码实战

### 6.1 CLIPORT 核心实现

以下代码实现了 CLIPORT 的核心架构，包括视觉编码器、语言编码器、跨模态注意力和动作头：

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import clip  # OpenAI CLIP

class CLIPORT(nn.Module):
    """
    CLIPORT: CLIP + Transporter for vision-language manipulation
    
    核心思想：将 CLIP 的语义理解能力与 Transporter 的空间变换机制结合，
    实现端到端的视觉-语言-动作（VLA）控制。
    
    架构：
    1. 视觉编码器：CLIP Vision Transformer，提取视觉特征
    2. 语言编码器：CLIP Text Transformer，提取语言特征
    3. 跨模态融合：语言特征引导视觉特征的空间查询
    4. 动作头：预测抓取和放置的 affordance map
    """
    
    def __init__(
        self,
        clip_model_name="ViT-B/32",
        img_size=224,
        num_samples=16,
        temperature=1.0
    ):
        """
        初始化 CLIPORT 模型
        
        Args:
            clip_model_name: CLIP 模型名称，支持 "ViT-B/32", "ViT-B/16", "ViT-L/14"
            img_size: 输入图像分辨率
            num_samples: 从 affordance map 采样的候选点数量
            temperature: softmax 温度参数，控制分布的尖锐程度
        """
        super().__init__()
        
        # ---------- 1. CLIP 视觉编码器 ----------
        # 使用 CLIP 的预训练视觉编码器，将输入图像映射为视觉特征
        # 这些特征已经在大规模图文对数据上学习了丰富的语义表示
        self.clip_model, self.preprocess = clip.load(clip_model_name, jit=False)
        
        # 获取 CLIP 视觉特征维度（ViT-B/32 为 512，ViT-B/16 为 512，ViT-L/14 为 768）
        self.vision_dim = self.clip_model.visual.output_dim
        
        # ---------- 2. CLIP 语言编码器 ----------
        # 复用同一 CLIP 模型中的文本编码器
        # 将自然语言指令编码为语言特征向量
        self.text_encoder = self.clip_model.transformer
        
        # 获取 CLIP 文本特征维度
        self.text_dim = 512  # CLIP 默认文本维度
        
        # ---------- 3. 跨模态融合层 ----------
        # 语言特征投影为 Query，视觉特征作为 Key 和 Value
        # 通过交叉注意力机制实现语言对视觉的空间引导
        self.lang_projection = nn.Sequential(
            nn.Linear(self.text_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 512)
        )  # 将语言特征投影为空间查询向量
        
        # 视觉特征的投影（用于 K, V）
        self.visual_projection = nn.Sequential(
            nn.Linear(self.vision_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 512)
        )
        
        # 层归一化
        self.layer_norm = nn.LayerNorm(512)
        
        # ---------- 4. 动作预测头（Affordance Map） ----------
        # 两个独立的预测头：抓取头 + 放置头
        # 每个头输出一个 HxW 的热力图，表示每个像素作为动作目标的得分
        
        # 融合特征 -> 抓取 affordance map
        self.pick_head = nn.Sequential(
            nn.Conv2d(512, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(256, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 1, kernel_size=1)  # 输出 1 通道热力图
        )
        
        # 融合特征 -> 放置 affordance map
        self.place_head = nn.Sequential(
            nn.Conv2d(512, 256, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(256, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(128, 1, kernel_size=1)
        )
        
        # ---------- 5. 其他配置 ----------
        self.img_size = img_size
        self.num_samples = num_samples
        self.temperature = temperature
        
    def encode_visual(self, images):
        """
        使用 CLIP 视觉编码器提取图像特征
        
        Args:
            images: 输入图像 [B, C, H, W]，已归一化
            
        Returns:
            visual_features: 视觉特征 [B, N, D]，N 为 patch 数量
        """
        # clip.load 返回的模型直接调用 encode_image
        visual_features = self.clip_model.encode_image(images)
        # CLIP ViT 输出: [B, D]，扩展为 [B, 1, D] 方便后续处理
        return visual_features
    
    def encode_text(self, text_tokens):
        """
        使用 CLIP 文本编码器提取语言特征
        
        Args:
            text_tokens: 文本 token [B, L]
            
        Returns:
            text_features: 语言特征 [B, D]
        """
        # CLIP 文本编码
        text_features = self.clip_model.encode_text(text_tokens)
        return text_features.float()
    
    def cross_modal_attention(self, lang_features, visual_features):
        """
        跨模态注意力融合层
        
        核心思想：语言特征作为 Query，去"查询"视觉特征，
        生成语义条件化的空间特征图。
        
        数学表达：
        F_fused = softmax(Q @ K^T / sqrt(d)) @ V
        其中 Q 来自语言特征，K,V 来自视觉特征
        
        Args:
            lang_features: 语言特征 [B, D]
            visual_features: 视觉特征 [B, D]
            
        Returns:
            fused_features: 融合后特征 [B, D]
        """
        B = lang_features.shape[0]
        
        # 1. 投影语言特征为 Query
        Q = self.lang_projection(lang_features)  # [B, 512]
        Q = Q.unsqueeze(1)  # [B, 1, 512]
        
        # 2. 投影视觉特征为 Key 和 Value
        K = self.layer_norm(self.visual_projection(visual_features))  # [B, 512]
        V = self.visual_projection(visual_features)  # [B, 512]
        K = K.unsqueeze(1)  # [B, 1, 512]
        V = V.unsqueeze(1)  # [B, 1, 512]
        
        # 3. 缩放点积注意力
        scale = 512 ** 0.5
        attention_scores = torch.matmul(Q, K.transpose(-2, -1)) / scale  # [B, 1, 1]
        attention_weights = F.softmax(attention_scores, dim=-1)  # [B, 1, 1]
        
        # 4. 加权求和得到语言引导的视觉特征
        guided_visual = torch.matmul(attention_weights, V)  # [B, 1, 512]
        guided_visual = guided_visual.squeeze(1)  # [B, 512]
        
        # 5. 残差连接：融合特征 + 语言特征（保留语言语义）
        fused_features = guided_visual + lang_features  # [B, 512]
        
        return fused_features
    
    def spatial_reshape(self, features):
        """
        将 CLIP 的全局特征 reshape 为空间热力图
        CLIP 输出的是 [B, D] 全局特征，我们将其扩展为 [B, D, H, W] 的空间特征
        
        由于 CLIP 是全局特征，不含空间结构，这里通过学习一个可学习的空间先验
        来生成空间分布
        """
        B, D = features.shape
        
        # 使用可学习的卷积核，从全局特征生成空间热力图
        # 这里使用一个简化的方法：将全局特征作为偏置加到空间先验上
        spatial_bias = self.spatial_prior  # [1, D, H, W] 的可学习空间先验
        
        # 将全局特征扩展为 [B, D, 1, 1]
        global_expanded = features.unsqueeze(-1).unsqueeze(-1)  # [B, D, 1, 1]
        
        # 结合全局特征和空间先验
        combined = spatial_bias + global_expanded  # [B, D, H, W]
        return combined
    
    def predict_affordance(self, fused_features):
        """
        从融合特征预测 affordance map（可供性地图）
        
        affordance map 是一个 HxW 的热力图，每个像素值表示
        "在该位置执行动作的适合程度"
        
        Args:
            fused_features: 融合特征 [B, D]
            
        Returns:
            pick_map: 抓取 affordance map [B, H, W]
            place_map: 放置 affordance map [B, H, W]
        """
        B = fused_features.shape[0]
        
        # CLIP ViT-B/32 输入 224x224 图像，输出 7x7=49 个 patches
        H = W = 7
        
        # 将融合特征 reshape 为 spatial feature map [B, D, H, W]
        spatial_features = fused_features.unsqueeze(-1).unsqueeze(-1)  # [B, D, 1, 1]
        spatial_features = spatial_features.expand(-1, -1, H, W)  # [B, D, H, W]
        
        # 通过 1x1 卷积预测 affordance
        pick_map = self.pick_head(spatial_features)  # [B, 1, H, W]
        place_map = self.place_head(spatial_features)  # [B, 1, H, W]
        
        # 上采样到原始图像尺寸
        pick_map = F.interpolate(
            pick_map, 
            size=(self.img_size, self.img_size), 
            mode='bilinear', 
            align_corners=False
        )  # [B, 1, 224, 224]
        place_map = F.interpolate(
            place_map, 
            size=(self.img_size, self.img_size), 
            mode='bilinear', 
            align_corners=False
        )  # [B, 1, 224, 224]
        
        return pick_map.squeeze(1), place_map.squeeze(1)
    
    def forward(self, images, text_tokens):
        """
        CLIPORT 前向传播
        
        Args:
            images: 输入图像 [B, C, H, W]，已归一化
            text_tokens: 文本 token [B, L]
            
        Returns:
            pick_map: 抓取 affordance map [B, H, W]
            place_map: 放置 affordance map [B, H, W]
        """
        # 1. 提取视觉特征
        visual_features = self.encode_visual(images)  # [B, D]
        
        # 2. 提取语言特征
        text_features = self.encode_text(text_tokens)  # [B, D]
        
        # 3. 跨模态融合
        fused_features = self.cross_modal_attention(text_features, visual_features)
        
        # 4. 预测 affordance map
        pick_map, place_map = self.predict_affordance(fused_features)
        
        return pick_map, place_map
```

### 6.2 动作预测

以下是 CLIPORT 的动作预测函数，包括从 affordance map 采样和最终动作提取：

```python
def sample_action_from_affordance(affordance_map, num_samples=16, temperature=1.0):
    """
    从 affordance map 中采样动作位置
    
    这是 CLIPORT 的核心推理逻辑：
    affordance map 是一个热力图，值越高的位置越适合作为动作目标。
    我们通过 softmax 将热力图转为概率分布，然后采样。
    
    为什么需要采样而不是直接取最大值？
    - 训练时：采样让损失函数能看到整个分布（软目标），梯度更稳定
    - 推理时：采样增加动作多样性，可以生成多个候选动作
    
    Args:
        affordance_map: affordance map [H, W]，值可以是任意实数
        num_samples: 采样的候选点数量
        temperature: 温度参数，控制分布的尖锐程度
            - temperature → 0：分布变得非常尖锐，几乎只选最大值点
            - temperature → ∞：分布变得非常平坦，所有点概率接近
            
    Returns:
        action: 采样的动作坐标 (x, y)，其中 x,y 是归一化的 [0, 1]
    """
    H, W = affordance_map.shape
    
    # 1. 使用 softmax 将热力图转为概率分布
    # 公式：P(i,j) = exp(affordance[i,j] / T) / sum(exp(affordance / T))
    affordance_flat = affordance_map.flatten()
    prob = F.softmax(affordance_flat / temperature, dim=-1)
    
    # 2. 按概率分布采样 num_samples 个位置
    indices = torch.multinomial(prob, num_samples, replacement=False)
    
    # 3. 取概率最高的点（第一个样本）作为最终决策
    best_idx = indices[0]
    y_idx = best_idx // W
    x_idx = best_idx % W
    
    # 4. 归一化到 [0, 1]
    x = x_idx.float() / (W - 1)
    y = y_idx.float() / (H - 1)
    
    return torch.tensor([x, y])


def extract_robot_action(pick_map, place_map, robot_camera_matrix, img_size=224):
    """
    从 CLIPORT 的 affordance map 提取真实的机器人控制指令
    
    这一步将像素坐标映射为真实的机器人末端执行器位姿。
    需要知道相机的内外参数（针孔相机模型）。
    
    Args:
        pick_map: 抓取 affordance map [H, W]
        place_map: 放置 affordance map [H, W]
        robot_camera_matrix: 相机内外参矩阵 [3, 4] 或 [3, 3]
            - 包含相机的内参（焦距、主点）
            - 包含相机相对于机器人基座的位姿变换
        img_size: 原始图像尺寸
        
    Returns:
        pick_pose: 抓取位姿 [x, y, z, roll, pitch, yaw]（机器人坐标系）
        place_pose: 放置位姿 [x, y, z, roll, pitch, yaw]
    """
    # 1. 从 affordance map 采样动作位置（像素坐标，归一化）
    pick_px = sample_action_from_affordance(pick_map, num_samples=16)  # [0, 1]
    place_px = sample_action_from_affordance(place_map, num_samples=16)  # [0, 1]
    
    # 2. 反归一化到像素坐标
    pick_x_px = int(pick_px[0].item() * (img_size - 1))
    pick_y_px = int(pick_px[1].item() * (img_size - 1))
    place_x_px = int(place_px[0].item() * (img_size - 1))
    place_y_px = int(place_px[1].item() * (img_size - 1))
    
    # 3. 像素坐标 -> 相机坐标系 -> 机器人基座坐标系
    # 假设高度已知（对于桌面任务，物体高度可以通过启发式规则估计）
    
    def pixel_to_robot(u, v, depth=0.5):
        """
        将像素坐标 + 深度转换为机器人坐标系中的 3D 位置
        
        基于针孔相机模型：
        X_c = (u - cx) / fx * depth
        Y_c = (v - cy) / fy * depth
        Z_c = depth
        
        Args:
            u, v: 像素坐标
            depth: 深度（米），对于桌面任务通常是固定的
            
        Returns:
            robot_pos: [x, y, z]，机器人基座坐标系中的位置
        """
        # 相机内参（从相机矩阵中提取）
        fx = robot_camera_matrix[0, 0]
        fy = robot_camera_matrix[1, 1]
        cx = robot_camera_matrix[0, 2]
        cy = robot_camera_matrix[1, 2]
        
        # 像素到归一化相机坐标
        x_norm = (u - cx) / fx * depth
        y_norm = (v - cy) / fy * depth
        z_norm = depth
        
        # 相机坐标系 -> 机器人基座坐标系
        # 假设相机已经标定，robot_camera_matrix 包含相机的位姿变换
        camera_pos = torch.tensor([x_norm, y_norm, z_norm])
        
        # 使用旋转矩阵 R 和平移向量 t 进行坐标系变换
        if robot_camera_matrix.shape[0] == 3 and robot_camera_matrix.shape[1] == 4:
            R = robot_camera_matrix[:3, :3]
            t = robot_camera_matrix[:3, 3]
            robot_pos = R @ camera_pos + t
        else:
            robot_pos = camera_pos
        
        return robot_pos.numpy()
    
    # 抓取位姿（假设抓取高度为桌面高度 + 物体高度）
    pick_depth = 0.05  # 假设物体距离桌面 5cm
    pick_3d = pixel_to_robot(pick_x_px, pick_y_px, depth=pick_depth)
    pick_pose = {
        'position': pick_3d.tolist(),  # [x, y, z] 机器人基座坐标系
        'rotation': [0, 0, 0, 1],      # 四元数表示的旋转（默认朝下）
        'gripper_open': True            # 抓取时先张开夹爪
    }
    
    # 放置位    # 放置位姿
    place_depth = 0.05
    place_3d = pixel_to_robot(place_x_px, place_y_px, depth=place_depth)
    place_pose = {
        'position': place_3d.tolist(),
        'rotation': [0, 0, 0, 1],
        'gripper_open': False  # 放置时夹爪已闭合
    }
    
    return pick_pose, place_pose
```

### 6.3 导航控制

以下是 CLIPORT 与机器人控制系统集成的示例，展示如何将模型输出转换为实际控制指令：

```python
import numpy as np

class CLIPORTNavigationController:
    """
    CLIPORT 导航控制器
    
    将 CLIPORT 的 affordance map 输出转换为机器人的运动控制指令。
    该控制器负责：
    1. 模型推理
    2. 动作后处理（坐标变换、安全检查）
    3. 机器人执行
    
    适用场景：桌面操控任务，如"把红色方块放到左边"
    """
    
    def __init__(self, model, robot_interface, device='cuda'):
        """
        初始化导航控制器
        
        Args:
            model: CLIPORT 模型实例
            robot_interface: 机器人通信接口（如 ROS、MoveIt 等）
            device: 计算设备
        """
        self.model = model.to(device)
        self.model.eval()
        self.robot = robot_interface
        self.device = device
        
        # 机器人工作空间边界（单位：米）
        # 用于安全检查，防止执行越界动作
        self.workspace_bounds = {
            'x_min': 0.1, 'x_max': 0.6,
            'y_min': -0.3, 'y_max': 0.3,
            'z_min': 0.0, 'z_max': 0.5
        }
        
    def step(self, observation, instruction):
        """
        执行一步推理和控制
        
        Args:
            observation: 当前观测，包含 RGB 图像
            instruction: 自然语言指令，如 "pick the red block"
            
        Returns:
            action_result: 执行结果字典
        """
        # 1. 准备输入
        rgb_image = observation['rgb']  # [H, W, 3]
        rgb_tensor = self.preprocess_image(rgb_image)  # [1, 3, 224, 224]
        text_tokens = self.tokenize_instruction(instruction)  # [1, L]
        
        # 2. 模型推理
        with torch.no_grad():
            pick_map, place_map = self.model(
                rgb_tensor.to(self.device),
                text_tokens.to(self.device)
            )
        
        # 3. 提取动作（像素坐标）
        pick_action = sample_action_from_affordance(
            pick_map[0].cpu(), 
            num_samples=16, 
            temperature=1.0
        )
        place_action = sample_action_from_affordance(
            place_map[0].cpu(),
            num_samples=16,
            temperature=1.0
        )
        
        # 4. 坐标变换（像素 -> 机器人坐标）
        pick_3d = self.pixel_to_3d(pick_action, depth=0.05)
        place_3d = self.pixel_to_3d(place_action, depth=0.05)
        
        # 5. 安全检查
        if not self.is_safe(pick_3d) or not self.is_safe(place_3d):
            return {
                'success': False,
                'reason': 'Target position out of workspace bounds'
            }
        
        # 6. 发送给机器人执行
        self.robot.move_to(pick_3d, 'pick')
        self.robot.close_gripper()
        self.robot.move_to(place_3d, 'place')
        self.robot.open_gripper()
        
        return {
            'success': True,
            'pick_position': pick_3d,
            'place_position': place_3d,
            'instruction': instruction
        }
    
    def preprocess_image(self, rgb_image):
        """将 PIL Image 或 numpy 数组转为模型输入 tensor"""
        import PIL.Image
        if isinstance(rgb_image, np.ndarray):
            rgb_image = PIL.Image.fromarray(rgb_image)
        # 使用 CLIP 的预处理
        preprocess = self.model.preprocess
        input_tensor = preprocess(rgb_image).unsqueeze(0)
        return input_tensor
    
    def tokenize_instruction(self, instruction):
        """将自然语言指令 token 化"""
        text_tokens = clip.tokenize([instruction])
        return text_tokens
    
    def pixel_to_3d(self, pixel_action, depth=0.05):
        """
        将归一化像素坐标 + 深度转换为机器人 3D 坐标
        
        Args:
            pixel_action: [x_norm, y_norm]，归一化到 [0, 1]
            depth: 深度（米）
            
        Returns:
            pos_3d: [x, y, z]，单位米
        """
        img_size = 224  # CLIP 输入分辨率
        u = int(pixel_action[0].item() * (img_size - 1))
        v = int(pixel_action[1].item() * (img_size - 1))
        
        # 相机内参（需要标定，这里用默认值）
        fx = fy = 200.0  # 焦距（像素）
        cx = cy = 112.0  # 主点（图像中心）
        
        # 像素到相机坐标系
        x_c = (u - cx) / fx * depth
        y_c = (v - cy) / fy * depth
        z_c = depth
        
        # 相机外参：相机到机器人基座的变换（需要标定）
        # 这里假设相机朝下安装，Z 轴向上
        R_cam_to_robot = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])
        t_cam_to_robot = np.array([0.2, 0.0, 0.5])  # 相机安装在机器人基座上方 0.5m
        
        camera_pos = np.array([x_c, y_c, z_c])
        robot_pos = R_cam_to_robot @ camera_pos + t_cam_to_robot
        
        return robot_pos.tolist()
    
    def is_safe(self, pos_3d):
        """
        检查目标位置是否在工作空间内
        
        Args:
            pos_3d: [x, y, z] 机器人坐标系位置
            
        Returns:
            bool: 是否安全
        """
        x, y, z = pos_3d
        bounds = self.workspace_bounds
        return (
            bounds['x_min'] <= x <= bounds['x_max'] and
            bounds['y_min'] <= y <= bounds['y_max'] and
            bounds['z_min'] <= z <= bounds['z_max']
        )
```

---

## 7. 练习题

### 基础题

**1. CLIPORT 的全称是什么？它的两个核心组件分别来自哪里？**

<details>
<summary>点击查看答案</summary>

CLIPORT = **CLIP** + **Transporter**

- **CLIP**：来自 OpenAI 的预训练视觉-语言模型，提供语义理解能力
- **Transporter**：来自 Google Robotics 的空间变换网络，提供精确的空间操作能力

</details>

**2. 什么是 Affordance Map？CLIPORT 预测几张 Affordance Map？**

<details>
<summary>点击查看答案</summary>

Affordance Map（可供性地图）是一个与输入图像尺寸相同的热力图，每个像素的值表示"在该位置执行某个动作的适合程度"。

CLIPORT 预测**两张** Affordance Map：
- **Pick Affordance Map**：抓取位置的热力图
- **Place Affordance Map**：放置位置的热力图

</details>

**3. 为什么 CLIPORT 能实现零样本语义泛化？**

<details>
<summary>点击查看答案</summary>

CLIPORT 的零样本语义泛化能力来源于 **CLIP 的预训练**。CLIP 在 4 亿图文对的大规模数据上进行了对比学习预训练，学习了丰富的视觉-语义对应关系。

当 CLIPORT 遇到新物体时（如"一个从未见过的蓝色杯子"），CLIP 的视觉编码器已经学会了"蓝色"、"杯子"等概念的视觉表示，因此即使没有在该物体上训练过，CLIPORT 也能理解语言指令并识别对应物体。

</details>

**4. Transporter Networks 的核心思想是什么？**

<details>
<summary>点击查看答案</summary>

Transporter Networks 的核心思想是：**把动作预测问题转化为特征图的空间变换问题**。

它不直接预测坐标点，而是预测"从源区域复制特征，粘贴到目标区域"的空间变换。这个"搬运"操作本质上是在学习"哪里的特征应该去哪里"，从而实现隐式的空间推理。

</details>

### 进阶题

**1. CLIPORT 相比原始 Transporter Networks 做了哪些关键改进？**

<details>
<summary>点击查看答案</summary>

CLIPORT 对 Transporter Networks 的关键改进有：

1. **视觉编码器替换**：从普通 CNN（ResNet）替换为 CLIP 预训练的 Vision Transformer
2. **新增语言分支**：引入 CLIP 文本编码器，处理自然语言指令
3. **语言引导的空间查询**：空间查询向量不再随机初始化，而是由语言特征投影得到
4. **跨模态注意力融合**：通过交叉注意力机制，让语言特征引导视觉特征的空间分布

这些改进使 CLIPORT 能够处理开放词汇的语言指令，而不仅仅是固定类别的物体。

</details>

**2. 为什么 CLIPORT 的动作预测要使用 softmax + 采样，而不是直接取热力图最大值？**

<details>
<summary>点击查看答案</summary>

使用 softmax + 采样有以下几个原因：

1. **训练稳定性**：softmax 将热力图转为概率分布，采样让损失函数能看到整个分布而非仅一个点，梯度更稳定
2. **多样性探索**：推理时多次采样可以得到多个候选动作，增加策略的多样性
3. **温度控制**：通过调节 temperature 参数，可以控制分布的尖锐程度：
   - 高温度：更探索（分布平坦）
   - 低温度：更利用（分布尖锐）
4. **避免过拟合**：直接取最大值的策略在模仿学习中容易过拟合专家数据，采样可以缓解这个问题

</details>

**3. CLIPORT 的优劣势是什么？它适合哪些场景，不适合哪些场景？**

<details>
<summary>点击查看答案</summary>

**CLIPORT 的优势**：
- 强大的零样本语义泛化（CLIP 预训练）
- 精确的空间操作能力（Transporter 基础）
- 端到端训练，架构简洁
- 推理速度快（~10 FPS）

**CLIPORT 的劣势**：
- 主要针对桌面操控（push/grasp），不适合作业级任务
- 需要专家演示数据，收集成本高
- 每次只输出一个动作，不直接支持多步骤规划
- 空间范围受输入图像视野限制

**适合场景**：
- 桌面物体的抓取和放置
- 语言指令明确、操作简单的任务
- 需要零样本泛化到新物体的场景

**不适合场景**：
- 复杂多步骤任务（如"先拿起碗，再打开微波炉，再放入碗"）
- 大范围导航任务（需要结合 CLIP on Wheels 等模型）
- 需要精确力控的任务（如插孔、拧螺丝）

</details>

---

## 本章小结

| 概念 | 说明 |
|------|------|
| **CLIPORT** | CLIP + Transporter，语义+空间双驱动的 VLA 模型 |
| **Affordance Map** | 可供性地图，表示每个位置作为动作目标的适合程度 |
| **Transporter Networks** | 空间变换网络，核心是"复制特征到目标位置"的操作 |
| **跨模态注意力** | 语言特征作为 Query 查询视觉特征，实现语义引导的空间推理 |
| **语义增强** | 训练时随机替换语言描述，增加数据多样性和泛化能力 |
| **模仿学习** | 通过行为克隆，让模型模仿专家演示学习策略 |
| **FLAT** | 另一个 VLA 模型，使用离散 action token，动作表示与 CLIPORT 不同 |
| **CLIP on Wheels** | 基于 CLIP 的导航模型，适合大范围室内导航，与 CLIPORT 互补 |

---

## 参考资料

### 基础论文

1. Shridhar, M., et al. (2022). CLIPORT: What Else Does the Robot Need to Know? *CoRL 2022*. (CLIPORT 原始论文)

2. Zeng, A., et al. (2020). Transporter Networks: Rearranging the Visual World for Robotic Manipulation. *CoRL 2020*. (Transporter Networks 原始论文)

3. Radford, A., et al. (2021). Learning Transferable Visual Models From Natural Language Supervision. *ICML 2021*. (CLIP 原始论文)

### 进阶论文

4. Jiang, H., et al. (2022). CLIP on Wheels: Zero-Shot Object Goal Navigation with Language Descriptors. *arXiv*.

5. Liu, H., et al. (2022). FLAT: Fast Language-Assisted Manipulation Transformer. *IROS 2022*.

6. Huang, S., et al. (2023). Hierarchical CLIPORT: Extending CLIPORT for Multi-Step Manipulation. *ICRA 2023*.

### 综述论文

7. Cao, Y., et al. (2023). A Survey on Vision-Language Navigation. *arXiv:2303.15829*.

---

*下一节我们将学习"17-3 VLN 视觉语言导航"，深入了解 VLN 的前沿方法和最新研究进展，包括基于大语言模型的 VLN、零样本 VLN、以及 VLN 与具身智能的结合等内容。*
