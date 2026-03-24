# 09-9-X RDK-X5 边缘计算加速

## 课程说明

本课程介绍如何在 RDK-X5 开发板上利用 BPU（Bio-inspired Processing Unit）架构实现边缘神经网络推理加速，涵盖模型优化、BPU 部署、ROS2 节点开发及性能调优全流程。

**前置知识**：Linux 基础、Python 基础、ROS2 基础概念、神经网络入门。

---

## 1. 边缘计算概述

### 1.1 什么是边缘计算

边缘计算（Edge Computing）是指在靠近数据源（终端设备）的位置完成计算任务，而不是将数据全部上传至远程云服务器处理。

```
┌─────────────┐     网络延迟高      ┌─────────────┐
│   云服务器   │ ←───────────────── │  终端设备   │
│  (远程计算)  │                    │ (数据采集)  │
└─────────────┘                    └─────────────┘

┌─────────────┐     网络延迟低      ┌─────────────┐
│   RDK-X5    │ ←───────────────── │  终端设备   │
│ (本地边缘)  │                    │ (数据采集)  │
└─────────────┘                    └─────────────┘
```

### 1.2 边缘计算 vs 云端计算

| 对比维度 | 边缘计算 | 云端计算 |
|---------|---------|---------|
| 延迟 | 毫秒级（<10ms） | 百毫秒~秒级 |
| 带宽 | 低带宽需求 | 高带宽依赖 |
| 隐私 | 数据本地处理，隐私好 | 数据上传，存在泄露风险 |
| 可靠性 | 离线可用 | 依赖网络连接 |
| 成本 | 一次性硬件投入 | 按需付费 |
| 能耗 | 端侧芯片 TDP 低 | 数据中心 TDP 高 |

### 1.3 边缘计算在机器人中的应用场景

| 场景 | 计算内容 | 实时性要求 |
|-----|---------|-----------|
| 目标检测与避障 | 图像分类/检测/分割 | 高（<50ms） |
| 语义 SLAM | 场景理解、地图构建 | 中（<100ms） |
| 语音唤醒 | 关键词检测 | 高（<200ms） |
| 姿态估计 | 人体关键点检测 | 高（<30ms） |
| 决策规划 | 路径规划、强化学习 | 中（<500ms） |

### 1.4 RDK-X5 边缘计算定位

RDK-X5 是地平线机器人开发板，定位为**高性能边缘 AI 推理平台**：

- 内置 BPU（伯努利架构）专用 AI 加速器
- 支持 INT8/FP16 混合精度推理
- 典型功耗 5~15W，适合移动机器人
- 可本地运行 YOLO、ResNet、UNet 等主流模型

---

## 2. RDK-X5 算力概述

### 2.1 BPU 架构详解

BPU（Bio-inspired Processing Unit）是地平线自研的专用 AI 推理芯片架构，全称**伯努利架构**。

**BPU 核心特性**：

```
BPU 架构组成
├── 多个 BPU Core（推理计算核心）
│   ├── 矩阵乘单元（MAC Array）
│   ├── 激活函数单元（ReLU/Sigmoid/Tanh）
│   └── 池化单元（MaxPool/AvgPool）
├── DMA 控制器（数据搬运）
├── DDR 带宽管理（共享内存访问）
└── 异构调度器（与 CPU 协同）
```

**BPU vs CPU 计算对比**：

```python
# CPU 执行矩阵乘法（逐元素计算）
for i in range(N):
    for j in range(M):
        for k in range(K):
            C[i][j] += A[i][k] * B[k][j]  # O(N*M*K) 次访存

# BPU 执行矩阵乘法（硬件并行）
# MAC Array 一次完成整个矩阵乘法，硬件级流水
```

### 2.2 CPU + BPU 异构计算

RDK-X5 采用 **ARM Cortex-A 系列 CPU + BPU 加速器** 异构架构：

```
┌─────────────────────────────────┐
│        RDK-X5 SoC               │
│  ┌───────────┐  ┌───────────┐  │
│  │  CPU      │  │   BPU     │  │
│  │ Cortex-A  │  │  伯努利    │  │
│  │  (4核)   │  │ (加速器)   │  │
│  └─────┬─────┘  └─────┬─────┘  │
│        │              │        │
│        └──────┬───────┘        │
│               ↓                │
│         DDR 内存                │
└─────────────────────────────────┘
```

**分工原则**：
- CPU 负责：数据预处理、后处理、业务逻辑、ROS 通信
- BPU 负责：神经网络推理（矩阵乘、卷积等计算密集型任务）

### 2.3 算力对比（TOPS）

| 平台 | TOPS（INT8） | 适用场景 |
|-----|-------------|---------|
| Raspberry Pi 4 | ~0.1 TOPS | 轻量模型演示 |
| Jetson Nano | ~0.5 TOPS | 入门级 AI |
| RDK-X5 | **8~16 TOPS** | 高性能边缘推理 |
| Jetson AGX Xavier | ~32 TOPS | 高端边缘计算 |
| 云服务器 A100 | ~312 TOPS | 云端大模型 |

> RDK-X5 的 TOPS 数值因 BPU 利用率、模型结构不同而有所差异，实际测量请参考第 6 节性能测试方法。

### 2.4 内存与带宽

```bash
# 查看 RDK-X5 内存信息（板子上执行）
free -h

# 输出示例：
#               total        used        free      shared  buff/cache   available
# Mem:           3.7Gi       1.2Gi       2.5Gi       200Mi    400Mi        2.3Gi
# Swap:          2.0Gi       0.0Ki       2.0Gi

# 查看 DDR 带宽（地平线工具）
hrtimer_eval --help
```

**带宽注意事项**：
- BPU 推理性能受 DDR 带宽限制，高分辨率输入会显著降低吞吐量
- 建议批量处理（batch）以充分利用带宽
- 模型过大（>100MB）可能超出板载内存

---

## 3. 边缘计算优化策略

### 3.1 模型量化（FP32 → FP16 → INT8）

量化是用低精度数据类型表示模型参数，减少计算量和内存占用。

```
精度路径：
FP32（32位浮点）→ FP16（16位浮点）→ INT8（8位整数）

文件大小变化（以 ResNet50 为例）：
FP32: ~98 MB
FP16: ~49 MB
INT8: ~25 MB
```

**量化方法对比**：

| 方法 | 描述 | 精度损失 | 速度提升 |
|-----|------|---------|---------|
| 训练后量化（PTQ）| 直接量化预训练模型 | 中等 | 高 |
| 量化感知训练（QAT）| 训练时模拟量化 | 低 | 高 |
| 动态量化 | 推理时动态确定 scale | 低 | 中 |

**RDK-X5 量化实战**（使用地平线工具链）：

```bash
# 步骤 1：准备校准数据集（至少 100 张图片）
mkdir -p ~/robot_ws/calibration_data
# 将图片放入此目录，命名如 img_0001.jpg, img_0002.jpg ...

# 步骤 2：编写校准脚本 calibrate.py
cat > ~/robot_ws/calibration.py << 'EOF'
"""模型校准脚本 - 生成量化参数"""
import os
import numpy as np

def calibrate_model(model_path, calibration_dir, output_path):
    """
    使用校准数据集生成量化参数

    参数:
        model_path: 原始浮点模型路径 (.onnx)
        calibration_dir: 校准图片目录
        output_path: 输出量化模型路径
    """
    import glob

    # 加载校准图片
    calibration_images = sorted(glob.glob(os.path.join(calibration_dir, "*.jpg")))
    print(f"找到 {len(calibration_images)} 张校准图片")

    # 模拟校准过程（实际使用地平线工具链）
    # 1. 收集每层激活值的 min/max
    # 2. 计算每层 scale 和 zero_point
    # 3. 生成量化表

    print("校准完成！")
    return {"status": "calibrated"}

if __name__ == "__main__":
    calibrate_model(
        model_path="/userdata/models/resnet50_fp32.onnx",
        calibration_dir="/userdata/calibration_data",
        output_path="/userdata/models/resnet50_int8.onnx"
    )
EOF

# 步骤 3：运行校准（板子上执行）
python3 ~/robot_ws/calibration.py

# 步骤 4：转换为 RDK-X5 可用模型（.hbm 格式）
# 使用地平线模型转换工具（详情见第 4 节）
```

### 3.2 模型剪枝

剪枝通过移除不重要的神经元/通道来减少计算量：

```python
"""
简单通道剪枝示例（结构化剪枝）
剪掉贡献小的卷积核
"""

def prune_channel(weights, prune_ratio):
    """
    对卷积权重进行通道级别剪枝

    参数:
        weights: 卷积核权重 [out_channels, in_channels, H, W]
        prune_ratio: 剪枝比例（如 0.3 表示剪掉 30% 的通道）

    返回:
        pruned_weights: 剪枝后的权重
        mask: 保留通道的掩码
    """
    # 计算每个输出通道的重要性（L1 范数）
    importance = np.abs(weights).sum(axis=(1, 2, 3))  # shape: [out_channels]

    # 确定剪枝阈值
    threshold = np.percentile(importance, prune_ratio * 100)

    # 生成掩码（重要性高于阈值的保留）
    mask = importance > threshold

    print(f"剪枝比例: {prune_ratio:.1%}")
    print(f"原始通道数: {weights.shape[0]}, 保留通道数: {mask.sum()}")

    return weights[mask], mask

# 示例：对 YOLO 最后一层卷积剪枝 30%
# yolo_weights = np.load("/userdata/models/yolo_last_conv.npy")
# pruned_weights, mask = prune_channel(yolo_weights, prune_ratio=0.3)
```

### 3.3 知识蒸馏

知识蒸馏用大模型（教师模型）指导小模型（学生模型）训练：

```python
"""
知识蒸馏训练脚本
"""

class DistillationLoss:
    """
    蒸馏损失 = 软标签损失 + 硬标签损失

    软标签来自教师模型的 logits
    硬标签来自真实标注
    """

    def __init__(self, temperature=4.0, alpha=0.7):
        """
        参数:
            temperature: 蒸馏温度，越高软标签越平滑
            alpha: 软标签损失权重，1-alpha 为硬标签权重
        """
        self.temperature = temperature
        self.alpha = alpha

    def compute(self, student_logits, teacher_logits, labels):
        """
        计算蒸馏损失

        参数:
            student_logits: 学生模型输出 [batch, num_classes]
            teacher_logits: 教师模型输出 [batch, num_classes]
            labels: 真实标签 [batch]
        """
        import torch.nn.functional as F

        # 1. 软标签损失（KL 散度）
        soft_student = F.log_softmax(student_logits / self.temperature, dim=1)
        soft_teacher = F.softmax(teacher_logits / self.temperature, dim=1)
        distill_loss = F.kl_div(soft_student, soft_teacher, reduction='batchmean')
        distill_loss = distill_loss * (self.temperature ** 2)  # 温度补偿

        # 2. 硬标签损失（交叉熵）
        hard_loss = F.cross_entropy(student_logits, labels)

        # 3. 加权组合
        total_loss = self.alpha * distill_loss + (1 - self.alpha) * hard_loss

        return total_loss, distill_loss.item(), hard_loss.item()


def train_student(student_model, teacher_model, train_loader, epochs=50):
    """蒸馏训练主流程"""
    criterion = DistillationLoss(temperature=4.0, alpha=0.7)
    optimizer = torch.optim.Adam(student_model.parameters(), lr=1e-3)

    for epoch in range(epochs):
        for batch_idx, (images, labels) in enumerate(train_loader):
            # 前向传播
            student_logits = student_model(images)
            with torch.no_grad():
                teacher_logits = teacher_model(images)

            # 计算损失
            loss, soft_loss, hard_loss = criterion.compute(
                student_logits, teacher_logits, labels
            )

            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            if batch_idx % 100 == 0:
                print(f"Epoch {epoch} | Loss: {loss:.4f} | "
                      f"软损失: {soft_loss:.4f} | 硬损失: {hard_loss:.4f}")
```

### 3.4 计算图优化

使用 ONNX Runtime 或地平线优化工具对计算图进行优化：

```bash
# 1. 使用 ONNX Runtime 优化（PC 上执行）
python3 << 'EOF'
"""ONNX 模型图优化"""
import onnx
from onnxruntime.transformers import optimizer

# 加载模型
model = onnx.load("/userdata/models/resnet50.onnx")

# 应用图优化（消除冗余操作、融合算子等）
optimized_model = optimizer.get_optimized_model(model)

# 保存优化后模型
onnx.save(optimized_model, "/userdata/models/resnet50_optimized.onnx")
print("模型优化完成！")
EOF

# 2. 常用图优化手段
# - 算子融合（Conv+BN → Conv, Conv+ReLU → Conv）
# - 常量折叠
# - 冗余节点消除
# - 维度推断
```

---

## 4. BPU 加速实战

### 4.1 BPU 算子支持

RDK-X5 BPU 支持以下主流神经网络算子：

| 类别 | 支持的算子 |
|-----|-----------|
| 卷积 | Conv, ConvTranspose, DepthwiseConv |
| 池化 | MaxPool, AvgPool, GlobalAvgPool |
| 激活 | ReLU, Sigmoid, Tanh, LeakyReLU, PReLU |
| 归一化 | BatchNorm, InstanceNorm, LayerNorm |
| 线性层 | MatMul, Gemm, Dense (FC) |
| 形状操作 | Reshape, Transpose, Concat, Split |
| Resize | Resize (nearest, bilinear) |
| 检测头 | YOLO Head, RetinaNet Head 等 |

> **注意**：并非所有自定义算子都支持。如果模型包含 BPU 不支持的算子，需要用等价算子替换或回退到 CPU 执行。

### 4.2 模型转换与验证

地平线提供 `hb_model` 工具链将 ONNX/TFLite 模型转换为 RDK-X5 可用的 `.hbm` 格式：

```bash
# ========== 环境准备（PC 上执行）==========
# 安装地平线模型转换工具（Docker 环境）
docker pull registry.cn-hangzhou.aliyuncs.com/hobot/horizonai_model_converter

# 进入 Docker 环境
docker run -it --rm \
  -v $(pwd):/workspace \
  registry.cn-hangzhou.aliyuncs.com/hobot/horizonai_model_converter:latest \
  /bin/bash

# ========== 模型转换流程 ==========
# 目录结构
mkdir -p ~/robot_ws/model_convert
# 放置文件：
#   ~/robot_ws/model_convert/model.onnx          # 原始 ONNX 模型
#   ~/robot_ws/model_convert/calibration_data/  # 校准数据（100+张图片）

cd ~/robot_ws/model_convert

# 编写转换配置文件 build.ini
cat > build.ini << 'EOF'
[basic]
model_file = model.onnx
input_name = images
input_shape = 1,3,640,640
output_name = output
output_dir = output_hbm
log_level = info

[quantization]
calibration_data_dir = calibration_data
calibration_data_type = float32
quantization_type = int

[advanced]
compile_mode = latency  # latency（低延迟）或 throughput（高吞吐）
debug = false
EOF

# 运行模型转换
hb_model -config build.ini

# 转换成功后，输出目录包含：
# output_hbm/
#   ├── model.hbm          # 可在 RDK-X5 上运行的模型文件
#   ├── model.onnx         # 转换后的 ONNX（带 BPU 算子）
#   └── compile_log.txt    # 编译日志
```

**转换失败常见问题排查**：

```bash
# 问题 1：BPU 不支持某算子
# 解决：查看日志中 unsupported_ops，替换为等价算子

# 问题 2：输入shape不匹配
# 解决：确认模型实际输入shape，修改 input_shape 参数

# 问题 3：模型版本不兼容
# 解决：使用地平线提供的模型转换工具链最新版本
```

### 4.3 推理性能测试

在 RDK-X5 开发板上执行性能测试：

```bash
# 1. 查看模型文件
ls -lh /userdata/models/
# 输出示例：
# -rw-r--r-- 1 root root  25M Mar 24 10:00 model.hbm

# 2. 使用地平线推理基准工具测试
cat > /userdata/benchmark.py << 'EOF'
"""RDK-X5 BPU 推理性能测试脚本"""
import time
import numpy as np

def benchmark_inference(model_path, input_shape, num_runs=100, warmup=10):
    """
    测试 BPU 推理性能

    参数:
        model_path: .hbm 模型路径
        input_shape: 输入张量形状 (N, C, H, W)
        num_runs: 正式测试次数
        warmup: 预热次数

    返回:
        平均延迟(ms)、标准差、吞吐量(FPS)
    """
    # 模拟加载模型（实际使用地平线 AI 工具链 API）
    print(f"加载模型: {model_path}")

    # 模拟创建推理会话
    # session = BPUModel(model_path)  # 实际用法

    # 生成随机输入数据
    dummy_input = np.random.randn(*input_shape).astype(np.float32)

    print(f"输入形状: {input_shape}")
    print(f"预热次数: {warmup}, 正式测试: {num_runs}")

    # 预热
    for _ in range(warmup):
        # _ = session.run(dummy_input)  # 实际用法
        time.sleep(0.001)

    # 正式测试
    latencies = []
    for i in range(num_runs):
        start = time.perf_counter()
        # _ = session.run(dummy_input)  # 实际用法
        time.sleep(0.005)  # 模拟推理时间（实际删除）
        latency = (time.perf_counter() - start) * 1000  # 转换为 ms
        latencies.append(latency)

        if (i + 1) % 20 == 0:
            print(f"  进度: {i+1}/{num_runs}")

    # 计算统计指标
    avg_latency = np.mean(latencies)
    std_latency = np.std(latencies)
    min_latency = np.min(latencies)
    max_latency = np.max(latencies)
    fps = 1000.0 / avg_latency  # 吞吐量

    # 打印结果
    print("\n" + "="*50)
    print("BPU 推理性能测试结果")
    print("="*50)
    print(f"  平均延迟: {avg_latency:.2f} ms")
    print(f"  标准差:   {std_latency:.2f} ms")
    print(f"  最小延迟: {min_latency:.2f} ms")
    print(f"  最大延迟: {max_latency:.2f} ms")
    print(f"  吞吐量:   {fps:.1f} FPS")
    print("="*50)

    return {
        "avg_latency_ms": avg_latency,
        "std_ms": std_latency,
        "min_ms": min_latency,
        "max_ms": max_latency,
        "fps": fps
    }


if __name__ == "__main__":
    result = benchmark_inference(
        model_path="/userdata/models/yolov5s.hbm",
        input_shape=(1, 3, 640, 640),
        num_runs=100,
        warmup=10
    )
EOF

# 运行测试
python3 /userdata/benchmark.py
```

### 4.4 瓶颈分析

使用 `htop` / `atop` 分析 CPU 占用，使用地平线工具分析 BPU 利用率：

```bash
# 1. 查看 CPU 占用（按 q 退出）
htop

# 2. 查看进程级 CPU/内存占用
top -p $(pgrep -f python3)

# 3. 分析推理瓶颈类型
# 瓶颈类型：
# - CPU-bound: 预处理/后处理过慢，BPU 空闲等待
# - BPU-bound: BPU 计算饱和，CPU 空闲
# - Memory-bound: DDR 带宽不足
# - IO-bound: 数据读取过慢

# 4. 定位瓶颈的简单方法
cat > /userdata/bottleneck_check.py << 'EOF'
"""简单瓶颈分析"""
import time
import numpy as np

def profile_inference_pipeline():
    """
    分析推理流水线各阶段耗时
    """
    num_runs = 50

    preprocess_times = []
    inference_times = []
    postprocess_times = []

    for _ in range(num_runs):
        # 阶段 1：预处理（resize、normalize、letterbox）
        t0 = time.perf_counter()
        dummy_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        # 模拟 resize + normalize
        dummy_input = np.random.randn(1, 3, 640, 640).astype(np.float32)
        preprocess_times.append((time.perf_counter() - t0) * 1000)

        # 阶段 2：BPU 推理
        t1 = time.perf_counter()
        # 实际推理: results = bpu_session.run(dummy_input)
        time.sleep(0.008)  # 模拟 8ms 推理
        inference_times.append((time.perf_counter() - t1) * 1000)

        # 阶段 3：后处理（NMS、坐标转换）
        t2 = time.perf_counter()
        # 模拟后处理
        dummy_boxes = np.random.randn(100, 6)
        postprocess_times.append((time.perf_counter() - t2) * 1000)

    total = np.sum([preprocess_times, inference_times, postprocess_times], axis=0)

    print("推理流水线耗时分析（50次平均）")
    print(f"  预处理: {np.mean(preprocess_times):.2f} ms ({np.mean(preprocess_times)/np.mean(total)*100:.1f}%)")
    print(f"  BPU推理: {np.mean(inference_times):.2f} ms ({np.mean(inference_times)/np.mean(total)*100:.1f}%)")
    print(f"  后处理: {np.mean(postprocess_times):.2f} ms ({np.mean(postprocess_times)/np.mean(total)*100:.1f}%)")
    print(f"  总延迟: {np.mean(total):.2f} ms")

if __name__ == "__main__":
    profile_inference_pipeline()
EOF

python3 /userdata/bottleneck_check.py
```

---

## 5. ROS2 边缘计算节点

### 5.1 图像订阅 → BPU 推理 → 结果发布

完整 ROS2 节点，实现图像输入 → BPU 推理 → 检测结果发布：

```bash
# 创建功能包
cd ~/robot_ws/src
ros2 pkg create rdk_inference --dependencies rclpy sensor_msgs std_msgs std_msgs_py vision_msgs

# 创建节点文件
cat > ~/robot_ws/src/rdk_inference/rdk_inference_node.py << 'EOF'
#!/usr/bin/env python3
"""
RDK-X5 BPU 推理 ROS2 节点
订阅图像话题，执行目标检测，发布检测结果

作者: Course Author
日期: 2026-03-24
"""

import rclpy
from rclpy.node import Node
import numpy as np
import cv2
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D
from geometry_msgs.msg import Pose2D
from cv_bridge import CvBridge


class BPUInferenceNode(Node):
    """RDK-X5 BPU 推理节点"""

    def __init__(self):
        super().__init__('bpu_inference_node')

        # ========== 参数声明 ==========
        self.declare_parameter('model_path', '/userdata/models/yolov5s.hbm')
        self.declare_parameter('input_topic', '/image_raw')
        self.declare_parameter('output_topic', '/detections')
        self.declare_parameter('conf_threshold', 0.5)
        self.declare_parameter('nms_threshold', 0.45)
        self.declare_parameter('input_size', 640)

        self.model_path = self.get_parameter('model_path').value
        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.nms_threshold = self.get_parameter('nms_threshold').value
        self.input_size = self.get_parameter('input_size').value

        # ========== 初始化 BPU 模型 ==========
        self.get_logger().info(f'加载模型: {self.model_path}')
        # 实际加载（伪代码）
        # self.bpu_model = BPUModel(self.model_path)
        self.get_logger().info('BPU 模型加载完成')

        # ========== 初始化 ROS 组件 ==========
        self.bridge = CvBridge()

        # 图像订阅者（使用压缩图像传输节省带宽）
        self.image_sub = self.create_subscription(
            Image,
            self.input_topic,
            self.image_callback,
            10  # queue_size
        )

        # 检测结果发布者
        self.detection_pub = self.create_publisher(
            Detection2DArray,
            self.output_topic,
            10
        )

        # 调试用图像发布（标注了检测框）
        self.debug_pub = self.create_publisher(
            Image,
            '/detections/debug_image',
            10
        )

        # 统计信息
        self.frame_count = 0
        self.fps_timer = self.create_timer(1.0, self.publish_fps)

        self.get_logger().info(f'推理节点启动！')
        self.get_logger().info(f'  输入话题: {self.input_topic}')
        self.get_logger().info(f'  输出话题: {self.output_topic}')
        self.get_logger().info(f'  置信度阈值: {self.conf_threshold}')

    def image_callback(self, img_msg: Image):
        """
        图像回调函数

        流程:
        1. 接收图像消息
        2. 图像预处理（resize、归一化）
        3. BPU 推理
        4. 后处理（NMS、坐标转换）
        5. 发布结果
        """
        self.frame_count += 1

        try:
            # ===== 步骤 1：图像解码 =====
            cv_image = self.bridge.imgmsg_to_cv2(img_msg, desired_encoding='bgr8')
            original_h, original_w = cv_image.shape[:2]

            # ===== 步骤 2：预处理（Letterbox resize）=====
            input_tensor = self.preprocess_letterbox(cv_image)

            # ===== 步骤 3：BPU 推理 =====
            # 实际推理：raw_output = self.bpu_model.run(input_tensor)
            raw_output = self.mock_inference(input_tensor)  # 模拟输出

            # ===== 步骤 4：后处理 =====
            detections = self.postprocess(
                raw_output,
                original_size=(original_w, original_h),
                input_size=(self.input_size, self.input_size)
            )

            # ===== 步骤 5：发布检测结果 =====
            detection_msg = self.build_detection_msg(detections, img_msg.header)
            self.detection_pub.publish(detection_msg)

            # ===== 步骤 6：发布调试图像 =====
            debug_image = self.draw_detections(cv_image, detections)
            debug_msg = self.bridge.cv2_to_imgmsg(debug_image, encoding='bgr8')
            debug_msg.header = img_msg.header
            self.debug_pub.publish(debug_msg)

        except Exception as e:
            self.get_logger().error(f'推理失败: {str(e)}')

    def preprocess_letterbox(self, image):
        """
        Letterbox 预处理：保持宽高比 resize 到目标尺寸

        参数:
            image: BGR 图像，shape (H, W, 3)
        返回:
            letterboxed: 处理后图像 (1, 3, H, W)
        """
        h, w = image.shape[:2]
        target_size = self.input_size

        # 计算缩放比例
        scale = min(target_size / h, target_size / w)
        new_h, new_w = int(h * scale), int(w * scale)

        # resize 图像
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # 创建画布并填充（letterbox）
        letterboxed = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
        top = (target_size - new_h) // 2
        left = (target_size - new_w) // 2
        letterboxed[top:top+new_h, left:left+new_w] = resized

        # BGR -> RGB
        letterboxed = letterboxed[:, :, ::-1]

        # HWC -> NCHW，归一化到 [0, 1]
        input_tensor = letterboxed.transpose(2, 0, 1).astype(np.float32) / 255.0
        input_tensor = np.expand_dims(input_tensor, axis=0)  # 添加 batch 维

        self.pad = (left, top, scale)
        return input_tensor

    def mock_inference(self, input_tensor):
        """
        模拟 BPU 推理输出
        实际使用时替换为真实推理调用
        """
        # 模拟 YOLO 输出格式 [batch, num_boxes, 5+num_classes]
        num_boxes = 25200  # YOLOv5 80x80 + 40x40 + 20x20
        num_classes = 80
        output = np.random.randn(1, num_boxes, 5 + num_classes).astype(np.float32)
        # 前5列: [x, y, w, h, obj_confidence]
        output[:, :, 4] = np.random.rand(1, num_boxes) * 0.3  # 随机置信度
        return output

    def postprocess(self, raw_output, original_size, input_size):
        """
        后处理：从模型输出提取检测框
        """
        left_pad, top_pad, scale = self.pad
        orig_w, orig_h = original_size

        detections = []
        output = raw_output[0]  # [num_boxes, 5+num_classes]

        for i, box in enumerate(output):
            obj_conf = float(box[4])
            if obj_conf < self.conf_threshold:
                continue

            # 提取类别概率
            class_scores = box[5:]
            class_id = int(np.argmax(class_scores))
            class_conf = float(class_scores[class_id])
            final_conf = obj_conf * class_conf

            if final_conf < self.conf_threshold:
                continue

            # 解析边界框（中心点 + 宽高）
            cx, cy, w, h = box[:4]

            # 反向 letterbox 变换
            cx = (cx - left_pad) / scale
            cy = (cy - top_pad) / scale
            w = w / scale
            h = h / scale

            # 转换为 x1, y1, w, h 格式（像素坐标）
            x1 = max(0, cx - w / 2)
            y1 = max(0, cy - h / 2)
            x2 = min(orig_w, cx + w / 2)
            y2 = min(orig_h, cy + h / 2)

            detections.append({
                'class_id': class_id,
                'confidence': final_conf,
                'bbox': [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
            })

        # 简单 NMS
        detections = self.nms(detections)
        return detections

    def nms(self, detections):
        """非极大值抑制（NMS）"""
        if not detections:
            return []

        # 按置信度排序
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)

        keep = []
        while detections:
            best = detections.pop(0)
            keep.append(best)

            detections = [
                d for d in detections
                if d['class_id'] != best['class_id'] or
                   self.box_iou(d['bbox'], best['bbox']) < self.nms_threshold
            ]

        return keep

    def box_iou(self, box_a, box_b):
        """计算两个框的 IOU"""
        x1_a, y1_a, w_a, h_a = box_a
        x1_b, y1_b, w_b, h_b = box_b

        x2_a, y2_a = x1_a + w_a, y1_a + h_a
        x2_b, y2_b = x1_b + w_b, y1_b + h_b

        # 交集区域
        x1_inter = max(x1_a, x1_b)
        y1_inter = max(y1_a, y1_b)
        x2_inter = min(x2_a, x2_b)
        y2_inter = min(y2_a, y2_b)

        inter_area = max(0, x2_inter - x1_inter) * max(0, y2_inter - y1_inter)

        # 并集区域
        area_a = w_a * h_a
        area_b = w_b * h_b
        union_area = area_a + area_b - inter_area

        return inter_area / union_area if union_area > 0 else 0

    def build_detection_msg(self, detections, header):
        """构建 Detection2DArray 消息"""
        msg = Detection2DArray()
        msg.header = header

        for det in detections:
            det_msg = Detection2D()
            det_msg.results[0].hypothesis.class_id = str(det['class_id'])
            det_msg.results[0].hypothesis.score = det['confidence']

            # 填充边界框
            det_msg.bbox.center.position.x = float(det['bbox'][0])
            det_msg.bbox.center.position.y = float(det['bbox'][1])
            det_msg.bbox.size_x = float(det['bbox'][2])
            det_msg.bbox.size_y = float(det['bbox'][3])

            msg.detections.append(det_msg)

        return msg

    def draw_detections(self, image, detections):
        """在图像上绘制检测框"""
        output = image.copy()

        # COCO 类别名称（部分示例）
        class_names = [
            'person', 'bicycle', 'car', 'motorbike', 'aeroplane', 'bus', 'train',
            'truck', 'boat', 'traffic light', 'fire hydrant', 'stop sign',
            'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep',
            'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella'
        ]

        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

        for det in detections:
            x, y, w, h = det['bbox']
            class_id = det['class_id']
            conf = det['confidence']

            color = colors[class_id % len(colors)]

            # 绘制边界框
            cv2.rectangle(output, (x, y), (x + w, y + h), color, 2)

            # 绘制标签
            label = f"{class_names[class_id] if class_id < len(class_names) else str(class_id)}: {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(output, (x, y - label_size[1] - 4), (x + label_size[0], y), color, -1)
            cv2.putText(output, label, (x, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return output

    def publish_fps(self):
        """每秒发布帧率统计"""
        self.get_logger().info(f'FPS: {self.frame_count}')
        self.frame_count = 0


def main(args=None):
    rclpy.init(args=args)
    node = BPUInferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
EOF

# 3. 添加 launch 启动文件
mkdir -p ~/robot_ws/src/rdk_inference/launch
cat > ~/robot_ws/src/rdk_inference/launch/bpu_inference_launch.py << 'EOF'
"""RDK-X5 BPU 推理节点启动文件"""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rdk_inference',
            executable='bpu_inference_node',
            name='bpu_inference_node',
            parameters=[{
                'model_path': '/userdata/models/yolov5s.hbm',
                'input_topic': '/image_raw',
                'output_topic': '/detections',
                'conf_threshold': 0.5,
                'nms_threshold': 0.45,
                'input_size': 640,
            }],
            remappings=[
                ('/image_raw', '/camera/image_raw'),  # 按需修改
            ],
            output='screen',
        ),
    ])
EOF

# 4. 编译和运行
cd ~/robot_ws
colcon build --packages-select rdk_inference
source install/setup.bash

# 运行推理节点
ros2 launch rdk_inference bpu_inference_launch.py
```

### 5.2 多模型串行/并行

一个 BPU 只能同时运行一个模型实例，但可以通过时间片轮转实现多模型串行，或启动多个 BPU 进程实现并行。

**串行模式（Pipeline）**：

```python
"""
多模型串行推理 Pipeline
模型A处理完 -> 模型B处理 -> 结果输出
适合检测+分类等有依赖关系的任务
"""

class SerialPipeline:
    """串行多模型推理管道"""

    def __init__(self, model_a_path, model_b_path):
        # 加载两个模型
        # self.model_a = BPUModel(model_a_path)  # 如目标检测
        # self.model_b = BPUModel(model_b_path)  # 如目标分类
        print("串行 Pipeline 初始化完成")

    def process(self, image):
        """
        串行处理流程:
        1. 模型A检测 -> 得到 ROI 区域
        2. 模型B分类 -> 对每个 ROI 分类
        3. 合并结果
        """
        # 步骤 1：检测
        # detections = self.model_a.run(image)
        detections = [{"roi": [100, 100, 200, 200], "class_id": 2}]

        # 步骤 2：对每个检测结果进行细分类
        results = []
        for det in detections:
            roi = det["roi"]
            roi_crop = image[roi[1]:roi[3], roi[0]:roi[2]]
            # 细分类
            # class_id, conf = self.model_b.run(roi_crop)
            class_id, conf = 10, 0.95  # 模拟
            results.append({
                "detection": det,
                "fine_class": class_id,
                "confidence": conf
            })

        return results


# 并行模式（Multi-Process）
# 适合相互独立的多模型任务
# 每个进程独立加载模型，避免 BPU 竞争

import multiprocessing as mp

def model_worker(model_path, input_queue, output_queue):
    """模型推理进程（Worker）"""
    # 在子进程中加载模型
    # model = BPUModel(model_path)
    print(f"Worker 启动，加载模型: {model_path}")

    while True:
        item = input_queue.get()
        if item is None:  # 终止信号
            break

        frame_id, image = item
        # results = model.run(image)
        results = [{"class": 0, "conf": 0.9}]
        output_queue.put((frame_id, results))

    print(f"Worker 退出: {model_path}")
```

### 5.3 实时性保障（QoS）

ROS2 的 QoS（Quality of Service）策略对实时性至关重要：

```python
# ========== QoS 配置示例 ==========

# 实时性关键话题使用 Best Effort + Keep Last
# 适合高速传感器数据（如摄像头）
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy

# 图像话题推荐配置
qos_image = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,  # 允许丢帧，确保实时性
    durability=DurabilityPolicy.VOLATILE,        # 不保留历史数据
    history=HistoryPolicy.KEEP_LAST,              # 只保留最新一帧
    depth=1                                        # 队列深度
)

# 控制命令使用 Reliable + Transient Local
# 确保命令不丢失
qos_cmd = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
    history=HistoryPolicy.KEEP_ALL,
)

# 订阅图像话题（带 QoS）
self.image_sub = self.create_subscription(
    Image,
    '/image_raw',
    self.image_callback,
    qos_profile=qos_image
)

# 发布检测结果（带 QoS）
self.detection_pub = self.create_publisher(
    Detection2DArray,
    '/detections',
    qos_profile=qos_cmd
)
```

### 5.4 负载均衡

当有多个推理任务时，需要合理分配 BPU 计算资源：

```bash
# 方案 1：进程级隔离（推荐）
# 每个模型独占一个进程，进程间通过 ROS 话题传递数据
# 进程 1: detector_node (模型 A)
# 进程 2: classifier_node (模型 B)

# 方案 2：线程池调度
# 适合 CPU-bound 任务（预处理/后处理）
cat > /userdata/thread_pool_inference.py << 'EOF'
"""线程池实现 CPU 任务负载均衡"""
import concurrent.futures
import time
import numpy as np

def preprocess(image):
    """CPU 预处理任务"""
    time.sleep(0.003)  # 模拟 3ms 预处理
    return np.random.randn(1, 3, 640, 640).astype(np.float32)

def postprocess(output):
    """CPU 后处理任务"""
    time.sleep(0.002)  # 模拟 2ms 后处理
    return [{"class": 0, "conf": 0.9}]

def inference_task(image):
    """
    单帧完整推理流程（预处理 + BPU + 后处理）
    """
    # 1. CPU 预处理
    input_tensor = preprocess(image)

    # 2. BPU 推理（实际调用）
    # results = bpu_model.run(input_tensor)
    time.sleep(0.008)  # 模拟 8ms BPU 推理

    # 3. CPU 后处理
    final_results = postprocess(None)

    return final_results

# 使用线程池并行处理多帧
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    images = [np.random.randint(0, 255, (480, 640, 3)) for _ in range(10)]

    start = time.perf_counter()
    futures = [executor.submit(inference_task, img) for img in images]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]
    elapsed = time.perf_counter() - start

    print(f"处理 10 帧耗时: {elapsed*1000:.1f} ms")
    print(f"平均每帧: {elapsed*100:.1f} ms")
EOF
```

---

## 6. 应用案例

### 6.1 实时目标检测加速

完整的目标检测推理方案，以 YOLOv5s 为例：

```bash
# 文件放置路径
# /userdata/models/
#   ├── yolov5s.onnx          # 原始浮点模型
#   ├── yolov5s_int8.onnx     # 量化后模型
#   └── yolov5s.hbm           # RDK-X5 可执行模型

# 端到端延迟分解（640x640 输入）
# 预处理:  ~3 ms（resize + normalize）
# BPU推理: ~5 ms（INT8）
# 后处理:  ~2 ms（NMS）
# 总延迟:  ~10 ms（理论 100 FPS）
```

### 6.2 语义分割加速

使用 DeepLabV3/UNet 进行实时分割：

```python
"""
语义分割推理节点
输入: 图像 (H, W, 3)
输出: 分割掩码 (H, W) 每个像素对应一个类别 ID
"""

class SegmentationNode(Node):
    def __init__(self):
        super().__init__('segmentation_node')
        self.declare_parameter('model_path', '/userdata/models/deeplabv3.hbm')
        self.declare_parameter('num_classes', 21)
        self.declare_parameter('input_size', 513)  # DeepLabV3 常用 513x513

        # 订阅和发布
        self.image_sub = self.create_subscription(
            Image, '/image_raw', self.callback, 10
        )
        self.mask_pub = self.create_publisher(
            Image, '/segmentation/mask', 10
        )
        self.overlay_pub = self.create_publisher(
            Image, '/segmentation/overlay', 10
        )

    def callback(self, img_msg):
        cv_image = self.bridge.imgmsg_to_cv2(img_msg, desired_encoding='bgr8')

        # 预处理（参考 DeepLabV3 的缩小倍数）
        input_tensor = self.preprocess(cv_image)  # shape: (1, 3, 513, 513)

        # BPU 推理
        # output = self.bpu_model.run(input_tensor)  # shape: (1, 21, 513, 513)
        output = np.random.randn(1, 21, 513, 513).astype(np.float32)

        # 后处理：Argmax 获取每个像素的类别
        mask = np.argmax(output[0], axis=0)  # shape: (513, 513)

        # 上采样到原始尺寸
        mask_resized = cv2.resize(mask, (cv_image.shape[1], cv_image.shape[0]),
                                   interpolation=cv2.INTER_NEAREST)

        # 发布分割掩码
        mask_msg = self.bridge.cv2_to_imgmsg(mask_resized.astype(np.uint8), encoding='mono8')
        self.mask_pub.publish(mask_msg)

        # 发布彩色叠加图
        color_map = self.get_color_map(21)  # 21 类别的调色板
        overlay = color_map[mask_resized]
        overlay_msg = self.bridge.cv2_to_imgmsg(overlay, encoding='bgr8')
        self.overlay_pub.publish(overlay_msg)

    def get_color_map(self, num_classes):
        """生成调色板"""
        import numpy as np
        color_map = np.zeros((num_classes, 3), dtype=np.uint8)
        for i in range(num_classes):
            color_map[i] = [
                (i * 50) % 256,
                (i * 100) % 256,
                (i * 150) % 256,
            ]
        return color_map
```

### 6.3 姿态估计加速

人体关键点检测（以 OpenPose 简化版为例）：

```python
"""
姿态估计推理节点
输出 17 个 COCO 人体关键点坐标
"""

class PoseEstimationNode(Node):
    """人体姿态估计节点"""

    def __init__(self):
        super().__init__('pose_estimation_node')
        self.declare_parameter('model_path', '/userdata/models/pose_hrnet.hbm')
        self.keypoint_names = [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ]

        self.image_sub = self.create_subscription(Image, '/image_raw', self.callback, 10)
        self.pose_pub = self.create_publisher(Detection2DArray, '/pose/keypoints', 10)

    def callback(self, img_msg):
        cv_image = self.bridge.imgmsg_to_cv2(img_msg)

        # BPU 推理获取热力图
        # heatmaps = self.bpu_model.run(preprocessed_image)  # shape: (1, 17, H, W)
        heatmaps = np.random.randn(1, 17, 64, 48).astype(np.float32)

        # 从热力图提取关键点坐标
        keypoints = self.extract_keypoints(heatmaps)

        # 缩放到原图坐标
        scale_x = cv_image.shape[1] / 48
        scale_y = cv_image.shape[0] / 64
        keypoints[:, 0] *= scale_x
        keypoints[:, 1] *= scale_y

        # 发布结果
        pose_msg = self.build_pose_message(keypoints, img_msg.header)
        self.pose_pub.publish(pose_msg)

    def extract_keypoints(self, heatmaps):
        """
        从热力图提取关键点位置
        使用 NMS 找每个通道的最大值点
        """
        keypoints = []
        for c in range(heatmaps.shape[1]):
            hm = heatmaps[0, c]
            # 找到热力图最大值位置
            y, x = np.unravel_index(np.argmax(hm), hm.shape)
            confidence = float(hm[y, x])
            keypoints.append([x, y, confidence])
        return np.array(keypoints)

    def build_pose_message(self, keypoints, header):
        """构建姿态消息"""
        msg = Detection2DArray()
        msg.header = header
        # ... 填充关键点数据
        return msg
```

### 6.4 多任务并行

同时运行检测+分割+姿态估计：

```bash
# 多节点并行架构
# 每个节点独立订阅图像，独立推理，通过 topic 区分结果

# launch 文件：multi_task_launch.py
cat > ~/robot_ws/src/rdk_inference/launch/multi_task_launch.py << 'EOF'
"""多任务并行推理 Launch 文件"""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 目标检测节点
        Node(
            package='rdk_inference',
            executable='detection_node',
            name='detection',
            parameters=[{'model_path': '/userdata/models/yolov5s.hbm'}],
        ),
        # 语义分割节点
        Node(
            package='rdk_inference',
            executable='segmentation_node',
            name='segmentation',
            parameters=[{'model_path': '/userdata/models/deeplabv3.hbm'}],
        ),
        # 姿态估计节点
        Node(
            package='rdk_inference',
            executable='pose_node',
            name='pose',
            parameters=[{'model_path': '/userdata/models/pose_hrnet.hbm'}],
        ),
        # 图像分发节点（将一路图像分发给三个推理节点）
        Node(
            package='rdk_inference',
            executable='image_dispatcher',
            name='dispatcher',
        ),
    ])
EOF
```

---

## 7. 部署与性能评估

### 7.1 文件放置路径

RDK-X5 开发板上的标准目录结构：

```bash
# 模型文件存放路径（推荐）
/userdata/models/
├── yolov5s.hbm              # 目标检测模型
├── deeplabv3.hbm            # 分割模型
├── pose_hrnet.hbm           # 姿态估计模型
└── resnet50.hbm             # 分类模型

# ROS2 工作空间（代码部署）
~/robot_ws/
├── src/
│   └── rdk_inference/       # 推理功能包
│       ├── rdk_inference_node.py
│       ├── detection_node.py
│       ├── segmentation_node.py
│       ├── pose_node.py
│       └── launch/
│           └── multi_task_launch.py
├── models/                   # 校准数据、临时模型
├── calibration_data/
└── log/

# 校准数据存放
/userdata/calibration_data/
├── img_0001.jpg
├── img_0002.jpg
└── ...
```

### 7.2 rsync / SSH 部署

```bash
# 1. 从 PC 推送模型到 RDK-X5（PC 上执行）
# 确保 PC 和 RDK-X5 在同一网络

# 方法一：rsync（推荐，适合大文件）
rsync -avzP --progress \
  /path/to/yolov5s.hbm \
  ubuntu@192.168.1.100:/userdata/models/

# 参数说明：
# -a: 归档模式（保留权限、时间戳）
# -v: 显示详情
# -z: 压缩传输
# -P: 显示进度，断点续传

# 方法二：scp（简单场景）
scp /path/to/model.hbm ubuntu@192.168.1.100:/userdata/models/

# 2. 推送代码到 RDK-X5
rsync -avzP --progress \
  ~/robot_ws/src/rdk_inference/ \
  ubuntu@192.168.1.100:~/robot_ws/src/rdk_inference/

# 3. RDK-X5 端编译
# （在 RDK-X5 上执行）
cd ~/robot_ws
colcon build --packages-select rdk_inference
source install/setup.bash

# 4. 快速部署脚本（PC 上执行）
cat > ~/robot_ws/deploy.sh << 'EOF'
#!/bin/bash
# 部署脚本：将模型和代码同步到 RDK-X5

RDK_IP="192.168.1.100"
RDK_USER="ubuntu"
RDK_MODEL_DIR="/userdata/models"
RDK_WS_DIR="/home/ubuntu/robot_ws"

echo "=== 同步模型文件 ==="
rsync -avzP --progress \
  /path/to/models/*.hbm \
  ${RDK_USER}@${RDK_IP}:${RDK_MODEL_DIR}/

echo "=== 同步代码 ==="
rsync -avzP --progress \
  ~/robot_ws/src/rdk_inference/ \
  ${RDK_USER}@${RDK_IP}:${RDK_WS_DIR}/src/rdk_inference/

echo "=== 部署完成 ==="
EOF
chmod +x ~/robot_ws/deploy.sh
```

### 7.3 延迟测量方法

```python
"""
精确延迟测量工具
区分预处理、BPU推理、后处理各阶段耗时
"""

import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class LatencyMeasurer(Node):
    """推理延迟测量节点"""

    def __init__(self):
        super().__init__('latency_measurer')
        self.sub = self.create_subscription(Image, '/detections', self.callback, 10)
        self.timestamps = {}  # frame_id -> timestamp

        # 创建定时器，每秒打印统计
        self.timer = self.create_timer(1.0, self.report)

        # 统计变量
        self.latencies = []

    def callback(self, msg):
        """接收检测结果，计算端到端延迟"""
        # 从消息头获取原始时间戳
        if msg.header.stamp.sec == 0:
            return

        now = self.get_clock().now().to_msg()
        recv_time = now.sec + now.nanosec * 1e-9
        send_time = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

        latency = (recv_time - send_time) * 1000  # ms
        self.latencies.append(latency)

    def report(self):
        """每秒报告统计"""
        if not self.latencies:
            return

        import numpy as np
        latencies = np.array(self.latencies)
        self.latencies.clear()

        print(f"[延迟统计] "
              f"平均: {np.mean(latencies):.2f}ms | "
              f"最大: {np.max(latencies):.2f}ms | "
              f"P95: {np.percentile(latencies, 95):.2f}ms | "
              f"P99: {np.percentile(latencies, 99):.2f}ms")


# 使用 Python time 模块测量子阶段延迟
import time

def measure_stage_latency(stage_name, func, *args):
    """测量单个阶段的延迟"""
    start = time.perf_counter()
    result = func(*args)
    latency = (time.perf_counter() - start) * 1000
    print(f"  {stage_name}: {latency:.2f} ms")
    return result, latency
```

### 7.4 吞吐量测试

```bash
# 使用 ros2 topic hz 查看话题发布频率
ros2 topic hz /detections

# 使用 image_pipeline 测试摄像头 + 推理端到端吞吐
# 安装: sudo apt install ros-humble-image-pipeline

# 编写吞吐量测试脚本
cat > /userdata/throughput_test.py << 'EOF'
"""吞吐量测试：测量每秒处理的图片数量"""
import time
import numpy as np
from collections import deque


class ThroughputMeter:
    """滑动窗口吞吐量计"""

    def __init__(self, window_size=30):
        """
        参数:
            window_size: 统计窗口大小（帧数）
        """
        self.window_size = window_size
        self.timestamps = deque(maxlen=window_size)

    def record(self):
        """记录一次处理完成"""
        self.timestamps.append(time.perf_counter())

    def get_fps(self):
        """计算当前吞吐量（FPS）"""
        if len(self.timestamps) < 2:
            return 0.0

        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed == 0:
            return 0.0

        return (len(self.timestamps) - 1) / elapsed

    def report(self):
        """打印吞吐量报告"""
        fps = self.get_fps()
        print(f"吞吐量: {fps:.1f} FPS | "
              f"帧延迟: {1000/fps if fps > 0 else 0:.1f} ms/帧 | "
              f"窗口: {len(self.timestamps)} 帧")


# 模拟吞吐量测试
meter = ThroughputMeter(window_size=30)

print("开始吞吐量测试（30秒）...")
start_time = time.time()
frame_count = 0

while time.time() - start_time < 30:
    # 模拟推理时间（10ms/帧）
    time.sleep(0.010)
    meter.record()
    frame_count += 1

    if frame_count % 100 == 0:
        meter.report()

print(f"\n=== 最终结果 ===")
print(f"总处理帧数: {frame_count}")
print(f"总耗时: {time.time() - start_time:.1f} 秒")
print(f"平均 FPS: {frame_count / (time.time() - start_time):.1f}")
EOF

python3 /userdata/throughput_test.py
```

### 7.5 能耗评估

```bash
# 1. 使用 powertop 查看功耗（板子上执行）
sudo powertop

# 2. 使用 stress 测试功耗
sudo apt install stress
# 满载测试
stress --cpu 4 &
# 然后用 powertop 观察

# 3. 使用地平线工具查看 BPU 功耗
# 参考地平线官方文档的功耗管理章节

# 4. 估算电池续航
# 假设：RDK-X5 功耗 10W，电池容量 5000mAh @ 12V
# 电池能量 = 5000mAh * 12V = 60Wh
# 续航时间 = 60Wh / 10W = 6 小时
```

---

## 8. 练习题

### 选择题

1. **BPU 的全称是？**
   - A. Basic Processing Unit
   - B. Bio-inspired Processing Unit
   - C. Binary Processing Unit
   - D. Batch Processing Unit

2. **RDK-X5 的 BPU 适合运行以下哪种任务？**
   - A. 文件压缩
   - B. 数据库查询
   - C. 神经网络推理
   - D. 视频编码

3. **INT8 量化相比 FP32 精度，通常会带来多少精度损失？**
   - A. 1%~3%
   - B. 5%~10%
   - C. 20%~30%
   - D. 50%以上

4. **Letterbox resize 的主要目的是？**
   - A. 减少计算量
   - B. 保持宽高比
   - C. 增加图像对比度
   - D. 模糊背景

5. **ROS2 中适合高速图像传输的 QoS 配置是？**
   - A. RELIABLE + KEEP_ALL
   - B. BEST_EFFORT + KEEP_LAST
   - C. RELIABLE + KEEP_LAST
   - D. BEST_EFFORT + KEEP_ALL

### 简答题

6. **简述 CPU + BPU 异构计算中，CPU 和 BPU 的分工。**

7. **解释什么是 NMS（非极大值抑制）及其作用。**

8. **为什么 BPU 推理前需要进行预处理（resize、归一化）？**

9. **列出三种边缘计算优化策略，并简要说明。**

10. **设计一个多模型并行架构，说明如何协调多个模型的推理任务。**

---

## 9. 答案

### 选择题答案

| 题号 | 答案 | 解析 |
|-----|------|------|
| 1 | **B** | BPU = Bio-inspired Processing Unit，地平线自研架构 |
| 2 | **C** | BPU 专门加速神经网络推理，属于计算密集型任务 |
| 3 | **A** | 正确量化后 INT8 相比 FP32 精度损失通常在 1%~3% |
| 4 | **B** | Letterbox 通过添加灰边保持原始宽高比，避免目标变形 |
| 5 | **B** | BEST_EFFORT + KEEP_LAST 允许丢帧，确保实时性 |

### 简答题答案

6. **CPU + BPU 异构计算的分工：**
   - **CPU 职责**：数据预处理（resize、归一化）、推理后处理（NMS、坐标变换）、ROS 通信、业务逻辑、任务调度
   - **BPU 职责**：神经网络推理的计算密集型任务（卷积、矩阵乘法、激活函数等），硬件级并行加速

7. **NMS（非极大值抑制）的作用：**
   - 目标检测模型通常对同一目标产生多个重叠的检测框
   - NMS 按置信度排序，保留最高置信度的框，删除与它 IoU > 阈值的其他框
   - 作用：消除冗余检测框，输出唯一的检测结果

8. **BPU 推理前需要预处理的原因：**
   - BPU 推理需要固定输入尺寸（如 640x640），与模型训练时一致
   - 预处理包括：resize 到目标尺寸、归一化（除以 255）、HWC→NCHW 维度转换
   - 不预处理会导致推理结果错误或无法运行

9. **三种边缘计算优化策略：**
   - **模型量化**：将 FP32 参数转换为 INT8/FP16，减少计算量和内存占用，提升推理速度
   - **模型剪枝**：移除不重要的神经元/通道，减小模型体积和计算量
   - **知识蒸馏**：用大模型（教师）指导小模型（学生）训练，使学生模型在参数量少的情况下接近大模型精度

10. **多模型并行架构设计：**
    ```
    图像输入 → [图像分发器] → 进程A(检测) → 结果A
                              → 进程B(分割) → 结果B
                              → 进程C(姿态) → 结果C
    协调器 ← 汇总 → 结果融合 → 最终输出
    ```
    - 每个模型独占一个独立进程，避免 BPU 资源竞争
    - 使用 ROS2 Topic 进行进程间通信
    - 协调器节点负责聚合各模型结果，按时间戳对齐
    - 适合独立任务的并行推理

---

## 10. 参考资料

- [RDK-X5 官方文档](https://developer.d-robotics.cc/)
- [地平线 AI 工具链文档](https://developer.horizon.ai/)
- [ROS2 官方文档](https://docs.ros.org/)
- [YOLOv5 官方仓库](https://github.com/ultralytics/yolov5)
- [ONNX Runtime 优化文档](https://onnxruntime.ai/docs/)

---

*课程更新日期：2026-03-24*
