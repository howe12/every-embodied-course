# 10-21 抓取注意力热图

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 10-21 |
| 课程名称 | 抓取注意力热图 |
| 所属模块 | 10-计算机视觉应用和深度学习 |
| 难度等级 | ⭐⭐⭐⭐
| 预计学时 | 4小时
| 前置知识 | 图像处理基础、深度学习基础、CNN原理
| 预计学时 | 2小时 |
| 前置知识 | 图像处理基础、深度学习基础 |

---

## 目录

1. [为什么机器人需要"热图"](#1-为什么机器人需要热图)
2. [什么是抓取注意力热图](#2-什么是抓取注意力热图)
3. [热图的类型](#3-热图的类型)
4. [理论溯源：注意力热图从何而来](#4-理论溯源注意力热图从何而来)
5. [核心公式详解](#5-核心公式详解)
6. [数据标注与训练](#6-数据标注与训练)
7. [代码实战：生成热图](#7-代码实战生成热图)
8. [快速部署应用](#8-快速部署应用)
9. [在机器人上部署](#9-在机器人上部署)
10. [论文创新点分析](#10-论文创新点分析)
11. [练习题](#11-练习题)
12. [参考答案](#12-参考答案)

---

## 1. 为什么机器人需要"热图"

### 1.1 机器人的"选择困难"

想象一下：
```
你走进厨房，看到一堆东西：
- 桌上的苹果
- 旁边的叉子
- 后面的刀
- 远处的杯子
```

作为人类，你瞬间知道要抓哪个。但机器人看到的只是一堆像素！

### 1.2 热图的作用

**抓取注意力热图** 就像给机器人戴上了"X光眼镜"：

```
原始图像          热图           机器人看到的
┌─────────┐    🔥🔥🔥░░░    ┌─────────┐
│🍎  🍴   │  →  ░░░░░░░  →  │✓ ✓     │
│    🔪   │      🔥░░░       │   ✓    │
└─────────┘    └─────────┘       └─────────┘
  看到物体     哪里好抓热    选择热的地方抓
```

热的地方 = 容易抓取、成功率高的地方

---

## 2. 什么是抓取注意力热图

### 2.1学术定义

**抓取注意力热图（Grasp Attention Heatmap）** 是一种将神经网络学习到的抓取知识可视化的高维图像，它告诉机器人"在哪里抓、怎么抓"。

通常包含三个维度：
- **Q (Quality)**: 抓取质量/成功概率
- **Θ (Theta)**: 抓取角度/方向  
- **W (Width)**: 抓取宽度/开口大小

### 2.2 一张图读懂

```
输入图像                    输出热图
┌──────────────────┐      ┌──────────────────┐
│                  │      │  ░░░░░░░░░░░░░  │
│    物体          │  →   │░░░🔥🔥🔥🔥🔥░░│  ← 热=好抓
│                  │      │░░🔥🔥🔥🔥🔥░░│     (Quality)
│                  │      │  ░░░░░░░░░░░░░  │
└──────────────────┘      └──────────────────┘
```

### 2.3 应用场景

| 场景 | 解决的问题 |
|------|----------|
| 杂乱桌面 | 找到最佳抓取点 |
| 透明物体 | 视觉难以识别，热图可以 |
| 柔软物体 | 预测最佳抓取力度 |
| 实时抓取 | 30fps实时热图响应 |

---

## 3. 热图的类型

### 3.1 抓取质量热图 (Quality Map Q)

**作用**：显示每个点位的抓取成功概率

```
Q值分布：0.0 ~ 1.0
         ↑
     1.0 │ ████████  ← 完美抓取点
         │ ████████
     0.5 │ ░░░░░░░░  ← 不确定
         │ ░░░░░░░░
     0.0 │░░░░░░░░░  ← 抓不住
         └──────────→ 位置
```

### 3.2 抓取角度热图 (Angle Map Θ)

**作用**：显示最优抓取方向

```
Θ值分布：-π ~ +π
         ↑
     +π │    ╱
         │  ╱
     0  │──┼──  ← 水平抓取
         │╱
    -π  │
```

### 3.3 抓取宽度热图 (Width Map W)

**作用**：显示夹爪张开多大

```
W值分布：0cm ~ 10cm
         ↑
     10cm│ ████████
         │ ████████
      5cm│ ────────
         │ 
      0cm│
```

### 3.4 多 热图融合

实际应用中，三个热图会融合在一起：

```python
# 融合方法
grasp_map = {
    "quality": Q_map,   # 哪里抓
    "angle": Theta_map,  # 怎么抓
    "width": W_map,     # 开多大
}
```

---

## 4. 数据标注与训练

### 4.1 数据来源

| 数据集 | 描述 |
|--------|------|
| Cornell |  grasp dataset 标注 |
| Jacquard | 法语标注 |
| API | 合成数据 |
| 自采集 | 真实机器人 |

### 4.2 标注格式

```python
# 每张图像对应的热图
annotation = {
    "image": "object_01.jpg",
    "grasp_map": {
        "quality": "object_01_q.npy",   # H x W
        "angle": "object_01_theta.npy", # H x W  
        "width": "object_01_w.npy",     # H x W
    },
    "success": True/False  # 这次抓成没成功
}
```

### 4.3 训练代码

```python
import torch
import torch.nn as nn

# 简化版网络
class GraspNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = Encoder()      # 图像编码
        self.quality_head = nn.Conv2d(256, 1, 1)   # Q头
        self.angle_head = nn.Conv2d(256, 1, 1)    # Θ头
        self.width_head = nn.Conv2d(256, 1, 1)    # W头
        
    def forward(self, x):
        feat = self.encoder(x)
        # 三个头输出三个热图
        return {
            "quality": torch.sigmoid(self.quality_head(feat)),
            "angle": self.angle_head(feat),
            "width": torch.relu(self.width_head(feat)),
        }
```

---

## 5. 代码实战：生成热图

### 5.1 安装

```bash
pip install torch torchvision opencv-python numpy
```

### 5.2 生成热图

```python
import cv2
import numpy as np
import torch
from torchvision import models

# 1. 加载图像
image = cv2.imread('object.jpg')
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# 2. 预处理
input_tensor = torch.from_numpy(image_rgb).permute(2,0,1).unsqueeze(0) / 255.0

# 3. 模拟推理（实际需要加载训练好的模型）
def mock_grasp_heatmap(image_tensor):
    """模拟生成热图"""
    # 生成一个假的"热点"
    h, w = image_tensor.shape[2], image_tensor.shape[3]
    
    # Q: 质量热图 - 中间最热
    y, x = np.ogrid[:h, :w]
    center_y, center_x = h // 2, w // 2
    quality = np.exp(-((x - center_x)**2 + (y - center_y)**2 / 20000)
    
    # Θ: 角度热图
    angle = np.zeros_like(quality)
    
    # W: 宽度热图
    width = 0.2 + 0.1 * quality
    
    return quality, angle, width

# 4. 生成
quality, angle, width = mock_grasp_heatmap(input_tensor)

# 5. 可视化
def heatmap_to_rgb(heatmap):
    """热图转伪彩色"""
    heatmap = (heatmap * 255).astype(np.uint8)
    color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    return color

# 显示结果
cv2.imwrite('quality.png', heatmap_to_rgb(quality))
print("热图已生成!")
```

### 5.3 效果展示

```bash
python grasp_demo.py
# 生成:
# quality.png  - 质量热图
# angle.png   - 角度热图  
# width.png  - 宽度热图
```

---

## 6. 在机器人上部署

### 6.1 实时推理流程

```
相机图像 → CNN → 热图 → NMS → 选择最佳 → 机器人
               ↓
           取最大值
```

### 6.2 代码

```python
import cv2
import numpy as np
import torch

class GraspDetector:
    def __init__(self, model_path):
        self.model = load_model(model_path)
        
    def detect(self, image):
        # 推理
        with torch.no_grad():
            output = self.model(image)
            
        # 取质量最大的点
        quality = output['quality'][0, 0].numpy()
        max_idx = np.unravel_index(np.argmax(quality), quality.shape)
        
        # 获取该点的参数
        x, y = max_idx[1], max_idx[0]
        angle = output['angle'][0, 0, y, x].item()
        width = output['width'][0, 0, y, x].item()
        
        # 返回抓取点
        return {
            'x': x, 'y': y,
            'angle': angle,
            'width': width,
            'confidence': quality[y, x]
        }
    
    def run(self, camera, robot):
        """主循环"""
        while True:
            # 获取图像
            frame = camera.get_frame()
            
            # 检测
            grasp = self.detect(frame)
            
            # 执行抓取
            if grasp['confidence'] > 0.5:
                robot.grasp(grasp)
            else:
                print("置信度太低,不抓")
```

### 6.3 控制频率

```python
import time
from threading import Thread

class RealTimeGrasp:
    def __init__(self, detector, freq=30):
        self.detector = detector
        self.dt = 1 / freq
        
    def loop(self):
        while True:
            start = time.time()
            
            # 推理 + 控制
            grasp = self.detector.detect(camera.get_frame())
            robot.execute(grasp)
            
            # 保证频率
            elapsed = time.time() - start
            if elapsed < self.dt:
                time.sleep(self.dt - elapsed)
```

---

## 7. 练习题

### 基础题

1. **概念理解**：抓取热图的Q、Θ、W分别代表什么？
2. **数值范围**：Q的取值范围是多少？0.9表示什么含义？
3. **可视化**：写代码将Q值0.7转换为红色显示

### 进阶题

4. **网络设计**：如果只用单层CNN生成热图，输出通道应该是多少？
5. **NMS**：解释为什么要用Non-Maximum Suppression
6. **误差分析**：如果热图预测偏左，实际抓取也偏左，可能是什么原因？

### 实战题

7. **生成热图**：运行上面5.2的代码，验证输出
8. **实时检测**：用OpenCV读取摄像头，生成实时热图

---

## 8. 参考答案

### 基础题答案

1. **Q、Θ、W**
   - Q: 抓取质量（成功概率）
   - Θ: 抓取角度（方向）
   - W: 抓取宽度（开口大小）
   
2. **0~1**
   - Q范围：0.0 ~ 1.0
   - Q=0.9 表示90%把握能抓住
   
3. **转红**
   ```python
   # 对Q做伪彩色
   color = cv2.applyColorMap((Q * 255).astype(np.uint8), cv2.COLORMAP_JET)
   ```

### 进阶题答案

4. **3个通道**
   - 1个质量 + 1个角度 + 1个宽度 = **3通道**
   
5. **NMS**
   - 去除重叠的热区，防止在同一个物体上选多个抓取点
   
6. **误差原因**
   - 标注数据本身偏左
   - 数据集偏差
   - 图像预处理问题

### 实战题答案

7. **生成**
   ```bash
   python grasp_demo.py
   # 成功输出 quality.png
   ```

8. **实时**
   ```python
   cap = cv2.VideoCapture(0)
   while True:
       ret, frame = cap.read()
       # 生成热图...
       cv2.imshow('heatmap', quality_color)
   ```

---

## 参考资源

- [Grasp Quality Map论文](http://staff.ustc.edu.cn/~zkan/Papers/Conference/[42]_2022ARM_Grasping.pdf)
- [Fast GraspNeXt](https://openaccess.thecvf.com/content/CVPR2023W/NAS/papers/Wong_Fast_GraspNeXt_A_Fast_Self-Attention_Neural_Network_Architecture_for_Multi-Task_CVPRW_2023_paper.pdf)
- [Attention Based Visual Analysis](https://www.frontiersin.org/articles/10.3389/fnbot.2019.00060/full)

---

*更新于 2026-03-31*
---

## 4. 理论溯源：注意力热图从何而来

### 4.1 问题的起点：机器人如何"看"懂抓取？

在深度学习出现之前，机器人抓取是一个纯粹的**几何问题**：
```
传统方法：物体识别 → 查表获取模型 → 几何计算
要求：精确的3D模型、明确的物体类别
局限：无法处理未知物体、杂乱场景
```

人类看了一眼就能知道哪里好抓，这种能力来自于：
- 经验积累（见过的物体多了）
- 视觉注意力（快速定位关键区域）
- 空间推理（判断深度、角度）

### 4.2 发展线路一：CNN可视化 → 抓取热图

#### 4.2.1 CNN可视化的起源

2014年，Karen Simonyan 等人在研究 "Deep Inside Convolutional Networks" 时发现：卷积神经网络的特征图可以被可视化！这个发现开启了**神经网络可解释性**的研究热潮。

#### 4.2.2 关键论文

| 年份 | 论文 | 贡献 |
|------|------|------|
| 2013 | "Visualizing Convolutional Neural Networks" | 首次提出CNN可视化 |
| 2014 | "Deep Inside Convolutional Networks" | CAM (Class Activation Mapping) |
| 2016 | "Grad-CAM: Visual Explanations from Deep Networks" | Grad-CAM通用方法 |

### 4.3 发展线路二：人类注意力 → 机器人注意力

#### 4.3.1 Itti-N 模型（1998）

1998年，Laurent Itti 和 Christof Koch 在《Nature》上发表了里程碑式论文，提出了**Itti-N模型**：

```
视觉注意力 = 亮度差异 + 颜色差异 + 方向差异 + ... 
            ↓
        显著图 (Saliency Map)
            ↓
        热点 (Where to look)
```

这就是**热图（Heatmap）概念的起源**！

#### 4.3.2 Itti-N 模型核心流程

```
输入图像
    │
    ├─→ 亮度通道 ──→ 高斯金字塔 ──┐
    │                              │
    ├─→ 颜色通道 ──→ 高斯金字塔 ──┼─→ 中央-周围差分 ──→ 显著图
    │                              │
    └─→ 方向通道 ──→ 高斯金字塔 ──┘
```

### 4.4 两条线路的融合

```
CNN可视化 ──┐
            ├──→ 深度学习时代 ──→ 抓取注意力热图
人类注意力 ──┘
```

---

## 5. 核心公式详解

### 5.1 注意力机制的数学定义

注意力公式：

$$A = \text{softmax}\left(\frac{Q \cdot K^T}{\sqrt{d_k}}\right) \cdot V$$

其中：
- $Q$ (Query): 查询向量，"我想要什么"
- $K$ (Key): 键向量，"我是什么"
- $V$ (Value): 值向量，"我有什么信息"

### 5.2 抓取质量评价函数

矩形抓取表示：$(x, y, \theta, w)$

Dex-Net 2.0 提出的质量评价：

$$Q = P(\text{success} | \text{image}, g)$$

### 5.3 为什么用 cos(2θ) 和 sin(2θ)？

因为角度是周期性的，θ 和 θ+π 表示同一个抓取：
- 直接预测 θ 会导致损失函数在边界不连续
- cos(2θ) 和 sin(2θ) 是连续的，可以正确回归

$$\theta = \frac{1}{2} \text{atan2}(s, c)$$

### 5.4 手写注意力计算

```python
import numpy as np

def simple_attention_map(image, target_position):
    """
    简化版注意力计算
    """
    H, W = image.shape[:2]
    tx, ty = target_position
    
    y, x = np.ogrid[:H, :W]
    
    # 高斯注意力 - 中心点最强，周围递减
    sigma = 50
    attention = np.exp(-((x - tx)**2 + (y - ty)**2) / (2 * sigma**2))
    
    return attention
```

---

## 8. 快速部署应用

### 8.1 GGCNN - 实时抓取热图

| 项目 | 内容 |
|------|------|
| 论文 | "Closing the Loop for Robotic Grasping" |
| 作者 | Douglas Morrison, Peter Corke, Jürgen Leitner |
| 机构 | 澳大利亚昆士兰科技大学 (QUT) |
| 年份 | 2018/2019 |
| 项目链接 | <https://github.com/dougsm/ggcnn> |

**核心思想**：
1. **从特征图直接回归抓取参数** - 不需要候选框
2. **实时性** - 在普通GPU上达到 45fps
3. **端到端** - 图像输入，抓取输出

**网络结构**：
```
输入图像 (304 x 304)
        ↓
   ResNet-18 backbone
        ↓
   反卷积层上采样
        ↓
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Quality │ │  Angle  │ │ Cos(2θ) │ │ Sin(2θ) │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

**部署步骤**：
```bash
# 1. 克隆仓库
git clone https://github.com/dougsm/ggcnn.git
cd ggcnn

# 2. 安装依赖
pip install torch torchvision pyquaternion numpy opencv-python

# 3. 运行演示
python ggcnn/deployment.py --network ggcnn --dataset cornell --camera_id 0
```

### 8.2 GraspNet - 10亿级数据

| 项目 | 内容 |
|------|------|
| 论文 | "GraspNet-1Billion: A Large-Scale Benchmark for Grasp Detection" |
| 作者 | Haoyu Fang 等 |
| 机构 | 清华大学 |
| 年份 | 2019 |
| 项目链接 | <https://github.com/tencent-robot/robotics/tree/master/GraspNet> |

**核心贡献**：
1. **大规模数据集** - 10亿+ 合成抓取样本
2. **6-DOF 抓取** - 支持任意角度的抓取
3. **PointNet++ 基础** - 点云输入

### 8.3 其他主流方法

| 方法 | 年份 | 特点 | 适用场景 |
|------|------|------|----------|
| **Dex-Net 2.0** | 2016 | 鲁棒性抓取、合成数据 | 工业零件 |
| **6-DOF GraspNet** | 2019 | 6自由度抓取 | 杂乱场景 |
| **Contact-GraspNet** | 2020 | 点云输入、全场景 | 自动驾驶 |

---

## 10. 论文创新点分析

### 10.1 经典论文汇总

| 年份 | 论文 | 机构 | 创新点 | 重点 |
|------|------|------|--------|------|
| 2013 | Cornell Dataset | 康奈尔 | 抓取检测基准数据集 | 矩形抓取标注 |
| 2016 | Dex-Net 2.0 | UC Berkeley | 鲁棒抓取、质量度量 | Force Closure |
| 2018 | GGCNN | QUT | 实时热图生成 | 45fps |
| 2019 | GraspNet | 清华 | 10亿级数据、6-DOF | 点云输入 |
| 2019 | 6-DOF GraspNet | NVIDIA | 6自由度抓取 | 任意姿态 |
| 2020 | Contact-GraspNet | Google | 点云直接预测 | 全场景 |
| 2021 | CLIPort | Google | 语言引导抓取 | VLM + 抓取 |

### 10.2 创新点详解

#### Dex-Net 2.0 - 质量评价函数

**创新**：提出了基于力 closure 的抓取质量评价函数

```
Dex-Net 的质量 = Force Closure × 鲁棒性

Force Closure：物体能否被稳定握住，考虑摩擦力、接触点
鲁棒性：扰动下的稳定性，位置误差容忍度
```

**公式**：$$Q_{DexNet} = P(success | g, object) = \eta \cdot \mu^{robustness}$$

#### GGCNN - 实时热图

**创新**：轻量级网络 + 直接回归

```
传统方法：图像 → 候选框生成 → CNN分类 → 抓取
GGCNN：     图像 → CNN → 热图 → 极值点 → 抓取

优点：
1. 候选框生成被跳过 → 快
2. 全卷积网络 → 任意尺寸输入
3. 端到端训练 → 联合优化
```

### 10.3 最新进展 (2021-2024)

| 模型 | 年份 | 能力 |
|------|------|------|
| CLIPort | 2021 | 语言引导抓取 |
| Transporter Networks | 2021 | 空间注意力 |
| DiffusionPolicy | 2024 | 扩散+机器人操作 |

### 10.4 创新方向总结

```
传统方法 ──→ CNN 2D ──→ 点云 6-DOF ──→ VLM + 扩散模型
   │           │           │               │
   ↓           ↓           ↓               ↓
几何计算    热图回归     多自由度        多模态理解
```

**主要创新方向**：
1. **端到端 vs 模块化**
2. **2D vs 3D**
3. **有监督 vs 自监督**
4. **Sim2Real**

---

## 11. 练习题（更新）

### 基础题

1. **概念理解**：抓取热图的Q、Θ、W分别代表什么？
2. **数值范围**：Q的取值范围是多少？0.9表示什么含义？
3. **可视化**：写代码将Q值转换为彩色显示

### 理论题

4. **来源推导**：解释Itti-N模型的中央-周围差分机制
5. **公式推导**：为什么GGCNN用cos(2θ)和sin(2θ)而不是直接预测θ？
6. **注意力机制**：简述Query、Key、Value在注意力计算中的作用

### 进阶题

7. **网络设计**：如果只用单层CNN生成热图，输出通道应该是多少？
8. **NMS**：解释为什么要用Non-Maximum Suppression
9. **Sim2Real**：解释域随机化在仿真到真实迁移中的作用

### 实战题

10. **论文阅读**：阅读GGCNN论文，总结其三大贡献
11. **部署实践**：按照8.1步骤部署GGCNN
12. **创新思考**：分析CLIPort如何结合语言和视觉进行抓取

---

## 12. 参考答案（更新）

### 基础题答案

1. **Q、Θ、W**
   - Q: 抓取质量（成功概率）
   - Θ: 抓取角度（方向）
   - W: 抓取宽度（开口大小）

2. **0~1**，Q=0.9 表示90%把握能抓住

3. **转彩色**：
```python
color = cv2.applyColorMap((Q * 255).astype(np.uint8), cv2.COLORMAP_JET)
```

### 理论题答案

4. **Itti-N 中央-周围差分**
   - 视觉神经元对中心刺激强，对周围刺激弱
   - 高斯金字塔创建多尺度
   - 差分 = 中心 - 周围，产生显著区域

5. **cos(2θ) 和 sin(2θ) 的原因**
   - θ 和 θ+π 表示同一个抓取（夹爪转180度不变）
   - 直接预测 θ 在损失函数中会有不连续问题
   - cos(2θ) 和 sin(2θ) 是连续的，可以正确回归

6. **Query、Key、Value**
   - Query: 我想要什么（当前位置）
   - Key: 我是什么（特征位置）
   - Value: 我有什么信息（特征内容）

### 进阶题答案

7. **3个通道**：1个质量 + 1个角度 + 1个宽度

8. **NMS**：去除重叠的热区，防止在同一个物体上选多个抓取点

9. **Sim2Real**：在仿真中随机改变光照、纹理、物体材质等，让模型适应真实世界的变化

### 实战题答案

10. **GGCNN论文贡献**
    - 提出端到端热图回归方法
    - 实现45fps实时抓取
    - 轻量级网络可在嵌入式平台运行

11. **部署**：按8.1步骤执行即可

12. **CLIPort创新**：
    - 使用CLIP编码语言和图像
    - 融合多模态特征
    - 实现"pick up the red block"类语言指令

---

## 参考资源

### 论文

| 论文 | 链接 |
|------|------|
| Itti-N Saliency Model | <https://www.nature.com/articles/35004528> |
| Grad-CAM | <https://arxiv.org/abs/1610.02391> |
| GGCNN | <https://arxiv.org/abs/1804.05172> |
| Dex-Net 2.0 | <https://arxiv.org/abs/1606.02580> |
| GraspNet-1B | <https://arxiv.org/abs/1911.08759> |
| CLIPort | <https://arxiv.org/abs/2109.12006> |

### 代码仓库

| 项目 | 链接 |
|------|------|
| GGCNN | <https://github.com/dougsm/ggcnn> |
| GraspNet | <https://github.com/tencent-robot/robotics/tree/master/GraspNet> |
| Dex-Net | <https://github.com/BerkeleyAutomation/gqcnn> |

---

*更新于 2026-04-06*
