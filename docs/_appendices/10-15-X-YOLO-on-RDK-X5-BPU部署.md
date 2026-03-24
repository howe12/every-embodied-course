# 10-15-X YOLO on RDK-X5 BPU部署

> **前置课程**：10-15 YOLO目标检测原理与安装使用
> **对应课程**：10-15 YOLO目标检测（RDK-X5 BPU加速部署）

---

## 目录

1. [BPU加速原理](#1-bpu加速原理)
2. [硬件准备与连接](#2-硬件准备与连接)
3. [YOLO模型准备](#3-yolo模型准备)
4. [环境搭建](#4-环境搭建)
5. [模型转换PT→ONNX→HB](#5-模型转换pt→onnx→hb)
6. [BPU推理部署](#6-bpu推理部署)
7. [ROS2 YOLO检测节点](#7-ros2-yolo检测节点)
8. [端到端实战](#8-端到端实战)
9. [部署与验证](#9-部署与验证)
10. [性能对比](#10-性能对比)
11. [常见问题排查](#11-常见问题排查)
12. [练习题](#练习题)
13. [答案](#答案)

---

## 1. BPU加速原理

### 1.1 什么是BPU

BPU（Backbone Processing Unit，地平线神经网络加速器）是地平线自主研发的高性能AI推理专用芯片，集成了专用深度学习加速单元，专门用于加速神经网络推理计算。与通用CPU/GPU不同，BPU针对深度学习算子进行了硬件级优化，能够实现极低的功耗和极高的推理效率。

RDK-X5开发板搭载的**地平线旭日X5（Sunrise X5）** 芯片内置BPU加速器，峰值算力达到**10 TOPS**（INT8），支持INT8/FP16混合精度推理，非常适合部署YOLO等实时目标检测模型。

### 1.2 BPU vs CPU/GPU 性能对比

| 指标 | CPU (ARM Cortex-A78) | GPU (Mali-G610) | BPU (地平线X5) |
|------|---------------------|-----------------|----------------|
| YOLOv8s 推理延迟 | ~150ms/帧 | ~30ms/帧 | **~5ms/帧** |
| 功耗 | ~5W | ~8W | **~2W** |
| 算力（INT8） | 0.1 TOPS | 1.0 TOPS | **10 TOPS** |
| 实时性（1080p） | ❌ 6-7 FPS | ⚠️ 30 FPS | ✅ **200+ FPS** |

> **结论**：在目标检测任务上，BPU的推理速度是GPU的**6倍以上**，功耗却只有GPU的**1/4**，是边缘部署的最佳选择。

### 1.3 地平线BPU架构特点

```
┌──────────────────────────────────────────────────────────────┐
│                     RDK-X5 系统架构                          │
│                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │   CPU核     │   │   BPU核     │   │   ISP/VIO   │       │
│  │ Cortex-A78  │   │  深度学习   │   │  图像处理   │       │
│  │   4x@2.2GHz │   │   加速器    │   │             │       │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘       │
│         │                 │                 │               │
│         └────────┬────────┴────────┬────────┘               │
│                  │                  │                        │
│            ┌─────▼─────────────────▼─────┐                   │
│            │      统一内存架构 (UMA)     │                   │
│            │    Shared Memory 4GB/8GB   │                   │
│            └────────────────────────────┘                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**核心优势**：
- **统一内存架构（UMA）**：CPU与BPU共享大内存，避免数据拷贝，提升推理效率
- **BPU编译工具链（hbdk）**：将ONNX/TFLite模型编译为硬件可执行的`.hb`文件
- **混合精度量化**：支持FP16/INT8，自动选择最优精度策略
- **算子融合**：Conv+BN+Act等常见算子自动融合，减少计算量

---

## 2. 硬件准备与连接

### 2.1 硬件清单

| 设备 | 数量 | 说明 |
|------|------|------|
| RDK-X5 开发板 | 1 | 搭载地平线旭日X5芯片 |
| MIPI 摄像头 | 1 | 支持IMX219/IMX477/OV5647 |
| USB 摄像头 | 1 | 备选方案 |
| TF 卡 | 1 | ≥32GB，用于存储模型 |
| 电源适配器 | 1 | 12V/2A |
| 网线/Wi-Fi | 1 | 用于网络连接 |

### 2.2 摄像头连接

**MIPI 摄像头连接**：

RDK-X5 提供 MIPI CSI 接口，位于开发板正面：

```
    ┌─────────────────────────────┐
    │      RDK-X5 开发板           │
    │                             │
    │   ┌───────────────────┐    │
    │   │   CAMERA FFC      │    │  ← 24pin FFC 接口
    │   │   (CAM0 / CAM1)   │    │
    │   └───────────────────┘    │
    │                             │
    │   [====] ← 屏幕接口         │
    └─────────────────────────────┘
```

**连接步骤**：
```bash
# 1. 关闭开发板电源
# 2. 将MIPI摄像头FFC排线金手指朝下插入CAM0接口
# 3. 确保排线完全插入且卡扣锁紧
# 4. 上电启动
```

### 2.3 开发板联网

```bash
# 通过网线连接，或使用Wi-Fi
# Wi-Fi 连接（串口终端）
nmcli device wifi list                    # 扫描Wi-Fi热点
nmcli device wifi connect <SSID> password <PASSWORD>  # 连接Wi-Fi

# 确认网络连通
ping -c 3 www.baidu.com
```

### 2.4 SSH远程登录

```bash
# RDK-X5 默认IP地址（查看路由器或串口终端）
# 默认用户名：root，默认密码：root

# 从PC端SSH登录
ssh root@<RDK-X5-IP>
# 例：ssh root@192.168.1.100

# 确认登录成功
whoami  # 应输出：root
```

---

## 3. YOLO模型准备

### 3.1 YOLO模型选择建议

| 模型 | 参数量 | mAP@val (COCO) | 推理延迟(BPU) | 适用场景 |
|------|--------|----------------|--------------|----------|
| YOLOv8n | 3.2M | 37.3% | ~3ms | 资源极度受限 |
| **YOLOv8s** | **11.2M** | **44.9%** | **~5ms** | **平衡之选** ✅ |
| YOLOv8m | 25.9M | 50.2% | ~8ms | 高精度需求 |
| YOLOv8l | 43.7M | 52.6% | ~12ms | 超高精度 |

> **推荐**：初学者从 **YOLOv8s** 开始，体验最佳性价比。

### 3.2 预训练模型下载

在PC端（不是RDK-X5）执行以下命令：

```bash
# 创建工作目录
mkdir -p ~/yolo_work && cd ~/yolo_work

# 方法1：使用pip安装ultralytics下载
pip install ultralytics -q
python -c "from ultralytics import YOLO; model = YOLO('yolov8s.pt'); print('下载完成')"

# 方法2：直接下载（推荐，速度快）
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt

# 确认文件
ls -lh yolov8s.pt
# 输出：yolov8s.pt (26.6 MB)
```

### 3.3 模型存放路径规范

```bash
# 在RDK-X5上创建标准目录结构
mkdir -p /userdata/models/        # 模型文件目录
mkdir -p /userdata/workspace/     # 代码工作目录
mkdir -p /userdata/datasets/      # 数据集目录

# 将PC端的模型复制到RDK-X5
# 方式1：SCP（从PC执行）
scp ~/yolo_work/yolov8s.pt root@<RDK-X5-IP>:/userdata/models/

# 方式2：rsync（推荐，支持断点续传）
rsync -avP ~/yolo_work/yolov8s.pt root@<RDK-X5-IP>:/userdata/models/
```

---

## 4. 环境搭建

### 4.1 地平线AI工具链概述

地平线提供的完整工具链包括：

| 工具 | 用途 |
|------|------|
| **hbdk** | BPU模型编译SDK（PC端运行） |
| **hb_model_convert** | 模型转换工具（PC端运行） |
| **horizon_nn** | 运行时推理SDK（RDK-X5端运行） |
| **hb_perf** | 性能分析工具 |
| **Docker 镜像** | 标准化编译环境（推荐） |

### 4.2 Docker环境安装（推荐）

地平线提供预配置的Docker镜像，避免手动配置依赖：

```bash
# 在PC端（不是RDK-X5）执行
# 1. 安装Docker
curl -fsSL https://get.docker.com | sh

# 2. 下载地平线Docker镜像（约15GB，需要较长时间）
docker pull horizon_docker/public/hobot-rdk-x5:1.2.1

# 3. 启动容器并进入
docker run -it --privileged \
    -v /home/$USER/yolo_work:/workspace \
    --name yolo_build \
    horizon_docker/public/hobot-rdk-x5:1.2.1 \
    /bin/bash

# 4. 以后重新进入容器
docker start -i yolo_build
```

### 4.3 PC端工具链验证

```bash
# 在Docker容器内验证
cd /workspace

# 验证hb_model_convert工具
which hb_model_convert
# 输出应类似：/usr/local/bin/hb_model_convert

# 验证Python版本和依赖
python3 --version
# 输出：Python 3.8.10 或更高

pip list | grep -E "onnx|numpy|opencv"
# 应显示：onnx, numpy, opencv-python 等
```

### 4.4 RDK-X5端Python环境

```bash
# 在RDK-X5上执行（通过SSH或串口）
# RDK-X5 自带Python环境，无需额外安装

python3 --version
# 输出：Python 3.8.10

# 安装运行时依赖
pip3 install numpy opencv-python-headless pillow

# 验证摄像头驱动
# MIPI摄像头自动识别
v4l2-ctl --list-devices | grep -i video
# 应显示：video0（CAM0）或 video1（CAM1）
```

### 4.5 ROS2 Humble 环境检查

```bash
# 在RDK-X5上执行
source /opt/ros/humble/setup.bash

# 检查ROS2环境
ros2 pkg list | grep -E "image_transport|cv_bridge"

# 如未安装，安装必要包
sudo apt update
sudo apt install -y ros-humble-image-transport ros-humble-cv-bridge ros-humble-vision-msgs
```

---

## 5. 模型转换PT→ONNX→HB

### 5.1 PT模型转ONNX

**为什么需要转换为ONNX？**
- `.pt` 是 PyTorch 专有格式，地平线工具链无法直接使用
- ONNX 是通用的中间表示格式，几乎所有AI框架都支持导出/导入

**转换脚本（PC端/Docker中执行）**：

```python
# ~/yolo_work/pt2onnx.py

import torch
from ultralytics import YOLO

def export_yolov8_to_onnx(model_path="yolov8s.pt", output_path="yolov8s.onnx"):
    """
    将YOLOv8模型从PyTorch格式转换为ONNX格式

    参数：
        model_path: 输入的.pt模型路径
        output_path: 输出的.onnx模型路径
    """
    # 加载PyTorch模型
    model = YOLO(model_path)

    # 设置模型为推理模式
    model.model.eval()

    # 创建动态ONNX模型（支持多种输入尺寸）
    dynamic_axes = {
        'images': {0: 'batch', 2: 'height', 3: 'width'},  # 动态batch和图像尺寸
        'output': {0: 'batch', 1: 'num_detections'}
    }

    # 执行导出（输入尺寸640x640，动态batch 1-16）
    success = model.export(
        format='onnx',
        imgsz=640,
        batch=1,
        dynamic_img_size=True,  # 启用动态图像尺寸
        simplify=True,          # 简化ONNX算子
        opset=12,               # ONNX算子集版本
    )

    print(f"✅ ONNX导出{'成功' if success else '失败'}")
    print(f"📁 输出文件：{output_path}")

    return output_path

if __name__ == "__main__":
    export_yolov8_to_onnx(
        model_path="/workspace/yolov8s.pt",
        output_path="/workspace/yolov8s.onnx"
    )
```

**执行转换**：

```bash
cd ~/yolo_work

python3 pt2onnx.py

# 验证ONNX文件生成
ls -lh yolov8s.onnx
# 输出示例：yolov8s.onnx (46.2 MB)

# 使用Netron可视化（可选）
# pip install netron
# netron yolov8s.onnx
```

### 5.2 ONNX模型验证

```python
# ~/yolo_work/verify_onnx.py

import onnx
import onnxruntime as ort
import numpy as np

def verify_onnx_model(onnx_path="yolov8s.onnx"):
    """
    验证ONNX模型的正确性和输入输出格式
    """
    # 加载模型
    model = onnx.load(onnx_path)

    # 检查模型格式是否合法
    onnx.checker.check_model(model)
    print("✅ ONNX模型格式检查通过")

    # 打印模型输入输出信息
    print("\n📋 模型输入输出信息：")
    for inp in model.graph.input:
        shape = [dim.dim_value if dim.dim_value > 0 else "动态"
                 for dim in inp.type.tensor_type.shape.dim]
        print(f"  输入：{inp.name}, 形状：{shape}")

    for out in model.graph.output:
        shape = [dim.dim_value if dim.dim_value > 0 else "动态"
                 for dim in out.type.tensor_type.shape.dim]
        print(f"  输出：{out.name}, 形状：{shape}")

    # 使用ONNX Runtime推理测试
    session = ort.InferenceSession(onnx_path)
    print("\n🔧 ONNX Runtime推理测试通过")

    # 随机输入测试
    input_name = session.get_inputs()[0].name
    dummy_input = np.random.randn(1, 3, 640, 640).astype(np.float32)
    output = session.run(None, {input_name: dummy_input})
    print(f"  推理输出shape：{[o.shape for o in output]}")

if __name__ == "__main__":
    verify_onnx_model("/workspace/yolov8s.onnx")
```

```bash
# 安装依赖
pip install onnx onnxruntime onnxoptimizer -q

# 执行验证
python3 verify_onnx.py
```

### 5.3 ONNX优化

```python
# ~/yolo_work/optimize_onnx.py

import onnx
from onnx import optimizer, shape_inference
import onnxoptimizer

def optimize_onnx(input_path="yolov8s.onnx", output_path="yolov8s_opt.onnx"):
    """
    优化ONNX模型：
    1. 消除冗余算子
    2. 融合连续卷积
    3. 简化形状推理
    """
    print(f"📥 加载模型：{input_path}")

    # 加载原始模型
    model = onnx.load(input_path)

    # 应用优化通道
    passes = [
        'eliminate_deadend',
        'eliminate_Identity',
        'eliminate_if_with_cond',
        'fuse_add_bias_into_conv',
        'fuse_consecutive_squeezes',
        'fuse_matmul_add_bias_into_gemm',
    ]

    optimized_model = onnxoptimizer.optimize(model, passes)
    print("✅ ONNX优化完成（算子融合、冗余消除）")

    # 形状推理（可选，有助于后续编译）
    try:
        optimized_model = shape_inference.infer_shapes(optimized_model)
        print("✅ 形状推理完成")
    except Exception as e:
        print(f"⚠️ 形状推理跳过：{e}")

    # 保存优化后的模型
    onnx.save(optimized_model, output_path)
    print(f"📁 保存优化模型：{output_path}")

    # 文件大小对比
    import os
    original_size = os.path.getsize(input_path) / 1024 / 1024
    optimized_size = os.path.getsize(output_path) / 1024 / 1024
    print(f"📊 模型大小：{original_size:.1f} MB → {optimized_size:.1f} MB")

if __name__ == "__main__":
    optimize_onnx(
        input_path="/workspace/yolov8s.onnx",
        output_path="/workspace/yolov8s_opt.onnx"
    )
```

### 5.4 ONNX转HB模型（核心步骤）

> ⚠️ **此步骤必须在PC端（Docker容器）中执行**，RDK-X5无法直接进行模型编译。

**YOLOv8后处理配置文件**：

```python
# ~/yolo_work/yolov8s_config.py
# YOLOv8模型转换配置

# 模型参数
MODEL_NAME = "yolov8s"                    # 模型名称（用于生成文件前缀）
ONNX_MODEL = "/workspace/yolov8s_opt.onnx" # 输入ONNX模型路径
OUTPUT_DIR = "/workspace/hb_model"          # 输出HB模型目录

# 输入图像配置
INPUT_WIDTH = 640                         # 输入宽度
INPUT_HEIGHT = 640                        # 输入高度
INPUT_CHANNEL = 3                         # 输入通道数（RGB）

# 预处理配置（与训练时一致）
NORM_MEAN = [0.0, 0.0, 0.0]              # 归一化均值
NORM_STD = [255.0, 255.0, 255.0]          # 归一化标准差（简单除以255）

# 推理配置
BPU_HW_BUDGET = 2000000                    # BPU算子数量预算（一般不改）
QUANTIZE_TYPE = "int8"                     # 量化类型：int8 或 fp16

# YOLOv8后处理参数（关键！）
NMS_THRESH = 0.45                         # NMS阈值
CONF_THRESH = 0.25                        # 置信度阈值
NUM_CLASSES = 80                          # COCO数据集类别数

# 输出配置
DEBUG = True                               # 开启调试输出
```

**执行模型转换**：

```bash
# 在Docker容器中执行
cd /workspace

# 创建输出目录
mkdir -p hb_model

# 执行转换（int8量化）
hb_model_convert \
    --model-name yolov8s \
    --onnx-model ./yolov8s_opt.onnx \
    --output-dir ./hb_model \
    --input-mean "0,0,0" \
    --input-std "255,255,255" \
    --output-mean "0,0,0" \
    --output-std "1,1,1" \
    --calibration-directory ./calib_images \
    --calibration-type int8 \
    --performance-mode high \
    --debug

# 如果有校准图片（可选，用于更精确的量化）
# hb_model_convert ... --calibration-images ./calib_images/ ...
```

> **说明**：
> - `--calibration-type int8`：使用INT8量化，性能最高，精度略有损失
> - `--calibration-type fp16`：使用FP16量化，性能较好，精度损失更小
> - `--performance-mode high`：优先性能模式

**转换成功输出示例**：

```
[INFO] Model converting...
[INFO] Start to compile model...
[INFO] Compile model success!
[INFO] Output model: ./hb_model/yolov8s_fp32.nb  # 编译后模型文件
[INFO] Model info:
  - Input shape: [1, 3, 640, 640]
  - Output shape: [1, 84, 8400]
[INFO] Compile time: 45.3s
```

### 5.5 HB模型文件说明

转换成功后，`hb_model` 目录包含以下文件：

```bash
ls -lh hb_model/
```

| 文件 | 说明 |
|------|------|
| `yolov8s.nb` | **核心模型文件**，运行时加载此文件 |
| `yolov8s_deploy.yaml` | 模型部署配置文件 |
| `yolov8s_input.yaml` | 输入预处理配置 |
| `yolov8s.log` | 转换日志 |

> ⚠️ **注意**：`.nb` 文件是地平线专有格式，只能在RDK-X5上运行，无法在PC端验证。

---

## 6. BPU推理部署

### 6.1 RDK-X5端运行时安装

```bash
# 在RDK-X5上执行
# 安装地平线推理运行时（已预装在官方镜像中）

pip3 install horizon-plugin-xxx horizon-ml -q

# 验证安装
python3 -c "import horizon_nn; print('horizon_nn 版本:', horizon_nn.__version__)"
```

### 6.2 BPU推理Python代码

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/rdk_deploy/bpu_inference.py
# BPU推理核心模块

import os
import time
import numpy as np
import cv2
from horizon_nn import horizon_nn

class BPUYOLO:
    """
    基于地平线BPU的YOLO目标检测推理类
    """

    def __init__(self, model_path="/userdata/models/yolov8s.nb",
                 conf_thresh=0.25, nms_thresh=0.45, num_classes=80):
        """
        初始化BPU推理引擎

        参数：
            model_path: HB模型文件路径（.nb格式）
            conf_thresh: 置信度阈值
            nms_thresh: NMS非极大值抑制阈值
            num_classes: 类别数量
        """
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh
        self.num_classes = num_classes

        # 初始化BPU推理引擎
        self.session = horizon_nn.init()
        self.model = self.session.load_model(model_path)
        print(f"✅ BPU模型加载成功：{model_path}")

        # 获取模型输入输出信息
        self.input_tensor = self.session.get_input_tensor(self.model)
        self.output_tensor = self.session.get_output_tensor(self.model)
        print(f"📋 模型输入shape：{self.input_tensor.shape}")
        print(f"📋 模型输出shape：{self.output_tensor.shape}")

    def preprocess(self, img, target_size=(640, 640)):
        """
        图像预处理：resize、归一化、BGR→RGB

        参数：
            img: 输入图像（BGR格式，来自OpenCV）
            target_size: 目标尺寸 (宽, 高)

        返回：
            normalized: 预处理后的图像数据
        """
        # 获取原始尺寸
        h, w = img.shape[:2]
        target_w, target_h = target_size

        # 计算缩放比例（保持宽高比，空白区域填充）
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)

        # resize图像
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # 创建640x640画布并填充灰色（保持宽高比）
        canvas = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
        pad_w = (target_w - new_w) // 2
        pad_h = (target_h - new_h) // 2
        canvas[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized

        # BGR→RGB转换
        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)

        # 归一化到[0,1]（根据转换时的配置，这里简单除以255）
        normalized = rgb.astype(np.float32) / 255.0

        # HWC→CHW格式
        transposed = np.transpose(normalized, (2, 0, 1))

        # 添加batch维度
        batched = np.expand_dims(transposed, axis=0)

        return batched, scale, (pad_w, pad_h)

    def postprocess(self, output, scale, pad, img_shape):
        """
        YOLO输出后处理：解析bbox、置信度、NMS

        参数：
            output: 模型原始输出
            scale: 预处理时的缩放比例
            pad: 预处理时的填充量
            img_shape: 原始图像尺寸

        返回：
            boxes: 检测框列表 [[x1,y1,x2,y2,score,class_id], ...]
        """
        # YOLOv8输出格式：[1, 84, 8400] → [batch, (4+num_classes), num_proposals]
        # 84 = 4(bbox) + 80(classes)

        predictions = output[0]  # 取batch=0

        # 分离bbox和类别置信度
        # 4个bbox参数 + 80个类别 = 84
        bbox_params = predictions[:4, :]      # [4, 8400]
        class_scores = predictions[4:, :]     # [80, 8400]

        # 获取每个proposal的最高置信度类别和分数
        class_ids = np.argmax(class_scores, axis=0)       # [8400]
        confidences = np.max(class_scores, axis=0)          # [8400]

        # 解析bbox（YOLOv8使用xywh格式，中心点+宽高）
        cx = bbox_params[0, :]
        cy = bbox_params[1, :]
        bw = bbox_params[2, :]
        bh = bbox_params[3, :]

        # 转换为xyxy格式（左上右下）
        x1 = cx - bw / 2
        y1 = cy - bh / 2
        x2 = cx + bw / 2
        y2 = cy + bh / 2

        # 反算到原始图像坐标（去除padding和缩放）
        pad_w, pad_h = pad
        scale_factor = 1.0 / scale

        x1 = (x1 - pad_w) * scale_factor
        y1 = (y1 - pad_h) * scale_factor
        x2 = (x2 - pad_w) * scale_factor
        y2 = (y2 - pad_h) * scale_factor

        # 裁剪到图像边界
        h, w = img_shape[:2]
        x1 = np.clip(x1, 0, w)
        y1 = np.clip(y1, 0, h)
        x2 = np.clip(x2, 0, w)
        y2 = np.clip(y2, 0, h)

        # 置信度过滤
        mask = confidences > self.conf_thresh
        x1 = x1[mask]
        y1 = y1[mask]
        x2 = x2[mask]
        y2 = y2[mask]
        confidences = confidences[mask]
        class_ids = class_ids[mask]

        # 执行NMS
        boxes = []
        for i in range(len(x1)):
            boxes.append([x1[i], y1[i], x2[i], y2[i], confidences[i], class_ids[i]])

        boxes = np.array(boxes, dtype=np.float32)

        if len(boxes) == 0:
            return boxes

        # NMS：按置信度排序
        indices = self._nms(boxes[:, :4], boxes[:, 4], boxes[:, 5],
                            self.nms_thresh)

        return boxes[indices]

    def _nms(self, boxes, scores, class_ids, nms_thresh):
        """
        非极大值抑制（NMS）

        参数：
            boxes: [N, 4] bbox坐标
            scores: [N] 置信度
            class_ids: [N] 类别ID
            nms_thresh: NMS阈值

        返回：
            keep_indices: 保留的索引
        """
        # 按类别分组处理
        unique_classes = np.unique(class_ids)
        keep_indices = []

        for cls in unique_classes:
            # 获取该类别的所有检测框
            mask = class_ids == cls
            cls_boxes = boxes[mask]
            cls_scores = scores[mask]

            # 按置信度排序
            order = cls_scores.argsort()[::-1]

            while len(order) > 0:
                # 保留置信度最高的框
                i = order[0]
                keep_indices.append(np.where(mask)[0][i])

                if len(order) == 1:
                    break

                # 计算IoU
                ious = self._compute_iou(cls_boxes[i], cls_boxes[order[1:]])

                # 删除IoU大于阈值的框
                keep_mask = ious <= nms_thresh
                order = order[1:][keep_mask]

        return np.array(keep_indices)

    def _compute_iou(self, box, boxes):
        """
        计算一个bbox与多个bbox的IoU

        参数：
            box: [4] 单个bbox [x1,y1,x2,y2]
            boxes: [N,4] 多个bbox

        返回：
            ious: [N] IoU值数组
        """
        # 计算交集区域
        x1 = np.maximum(box[0], boxes[:, 0])
        y1 = np.maximum(box[1], boxes[:, 1])
        x2 = np.minimum(box[2], boxes[:, 2])
        y2 = np.minimum(box[3], boxes[:, 3])

        inter_area = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)

        # 计算各自面积
        box_area = (box[2] - box[0]) * (box[3] - box[1])
        boxes_area = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

        # 计算并集面积
        union_area = box_area + boxes_area - inter_area

        # 计算IoU
        ious = inter_area / (union_area + 1e-6)

        return ious

    def infer(self, img):
        """
        执行推理

        参数：
            img: 输入图像（BGR格式）

        返回：
            boxes: 检测结果 [[x1,y1,x2,y2,score,class_id], ...]
        """
        # 预处理
        input_data, scale, pad = self.preprocess(img)

        # 设置输入
        self.session.set_input_tensor(self.model, 0, input_data)

        # 执行推理
        start_time = time.time()
        self.session.run(self.model)
        inference_time = time.time() - start_time

        # 获取输出
        output = self.session.get_output_tensor(self.model)

        # 后处理
        boxes = self.postprocess(output, scale, pad, img.shape)

        return boxes, inference_time

    def draw_boxes(self, img, boxes, class_names):
        """
        在图像上绘制检测框

        参数：
            img: 原始图像
            boxes: 检测结果
            class_names: 类别名称列表

        返回：
            annotated: 绘制了检测框的图像
        """
        annotated = img.copy()

        # 定义颜色（80个类别）
        COLORS = [(np.random.randint(0, 255),
                   np.random.randint(0, 255),
                   np.random.randint(0, 255)) for _ in range(80)]

        for box in boxes:
            x1, y1, x2, y2, score, class_id = box
            class_id = int(class_id)

            # 绘制框
            color = COLORS[class_id]
            cv2.rectangle(annotated, (int(x1), int(y1)),
                         (int(x2), int(y2)), color, 2)

            # 绘制标签
            label = f"{class_names[class_id]}: {score:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            label_y = int(y1) - 10 if int(y1) - 10 > label_size[1] else int(y1) + label_size[1]

            cv2.rectangle(annotated, (int(x1), label_y - label_size[1] - 4),
                         (int(x1) + label_size[0], label_y + 4), color, -1)
            cv2.putText(annotated, label, (int(x1), label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return annotated


# COCO数据集80类名称
COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
    'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book',
    'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
]
```

### 6.3 推理性能测试脚本

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/rdk_deploy/test_bpu_fps.py
# BPU推理性能测试

import os
import sys
import time
import numpy as np
import cv2

# 添加模块路径
sys.path.insert(0, '/home/nx_ros/robot_ws/src/rdk_deploy')
from bpu_inference import BPUYOLO

def test_bpu_performance(model_path="/userdata/models/yolov8s.nb",
                         test_images=100):
    """
    测试BPU推理性能

    参数：
        model_path: 模型文件路径
        test_images: 测试帧数
    """
    print("=" * 60)
    print("🔧 BPU YOLO 推理性能测试")
    print("=" * 60)

    # 初始化BPU推理器
    detector = BPUYOLO(model_path=model_path)

    # 生成测试图像（模拟摄像头输入）
    print(f"\n📊 生成 {test_images} 帧测试图像...")
    dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    # 预热（前10帧不计入统计）
    print("🔥 预热中（前10帧）...")
    for _ in range(10):
        _ = detector.infer(dummy_img)

    # 正式测试
    print(f"\n⏱️  开始测试 {test_images} 帧...")
    times = []

    for i in range(test_images):
        # 模拟不同尺寸输入
        h = np.random.choice([480, 640, 720, 1080])
        w = np.random.choice([640, 720, 1280, 1920])
        test_img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)

        _, inf_time = detector.infer(test_img)
        times.append(inf_time)

        if (i + 1) % 20 == 0:
            avg_time = np.mean(times)
            fps = 1.0 / avg_time if avg_time > 0 else 0
            print(f"  [{i+1}/{test_images}] 平均延迟: {avg_time*1000:.2f}ms, FPS: {fps:.1f}")

    # 统计结果
    times = np.array(times)
    print("\n" + "=" * 60)
    print("📊 性能统计结果")
    print("=" * 60)
    print(f"  总测试帧数：{test_images}")
    print(f"  平均延迟：{np.mean(times)*1000:.2f} ms")
    print(f"  最小延迟：{np.min(times)*1000:.2f} ms")
    print(f"  最大延迟：{np.max(times)*1000:.2f} ms")
    print(f"  延迟标准差：{np.std(times)*1000:.2f} ms")
    print(f"  推理 FPS：{1.0/np.mean(times):.1f}")
    print(f"  P50 延迟：{np.percentile(times, 50)*1000:.2f} ms")
    print(f"  P95 延迟：{np.percentile(times, 95)*1000:.2f} ms")
    print(f"  P99 延迟：{np.percentile(times, 99)*1000:.2f} ms")
    print("=" * 60)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='BPU YOLO性能测试')
    parser.add_argument('--model', type=str,
                       default='/userdata/models/yolov8s.nb',
                       help='模型文件路径')
    parser.add_argument('--frames', type=int, default=100,
                       help='测试帧数')
    args = parser.parse_args()

    test_bpu_performance(model_path=args.model, test_images=args.frames)
```

**执行性能测试**：

```bash
# 在RDK-X5上执行
cd /home/nx_ros/robot_ws/src/rdk_deploy

# 运行性能测试（100帧）
python3 test_bpu_fps.py --model /userdata/models/yolov8s.nb --frames 100

# 预期输出示例：
# ============================================================
# 🔧 BPU YOLO 推理性能测试
# ============================================================
# ✅ BPU模型加载成功：/userdata/models/yolov8s.nb
# 📊 生成 100 帧测试图像...
# ...
# 📊 性能统计结果
# ============================================================
#   总测试帧数：100
#   平均延迟：4.87 ms
#   推理 FPS：205.3
# ============================================================
```

---

## 7. ROS2 YOLO检测节点

### 7.1 功能包目录结构

```bash
# 在RDK-X5上创建功能包
cd /home/nx_ros/robot_ws/src
ros2 pkg create rdk_yolo --dependencies rclpy std_msgs sensor_msgs image_transport cv_bridge vision_msgs

# 查看创建结果
tree rdk_yolo/
# 输出：
rdk_yolo/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/
│   └── rdk_yolo
├── rdk_yolo/
│   ├── __init__.py
│   └── yolo_node.py    # YOLO检测节点
└── launch/
    └── yolo_launch.py  # 启动文件
```

### 7.2 ROS2 YOLO检测节点代码

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_yolo/rdk_yolo/yolo_node.py
# ROS2 YOLO目标检测节点

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
import cv2
import sys

# 导入BPU推理模块
sys.path.insert(0, '/home/nx_ros/robot_ws/src/rdk_deploy')
from bpu_inference import BPUYOLO, COCO_CLASSES


class YOLONode(Node):
    """
    ROS2 YOLO目标检测节点
    订阅图像话题，发布检测结果话题
    """

    def __init__(self):
        super().__init__('yolo_bpu_node')

        # 声明参数
        self.declare_parameter('model_path', '/userdata/models/yolov8s.nb')
        self.declare_parameter('conf_thresh', 0.25)
        self.declare_parameter('nms_thresh', 0.45)
        self.declare_parameter('input_topic', '/image_raw')
        self.declare_parameter('output_topic', '/yolo/detections')
        self.declare_parameter('show_image', True)

        # 获取参数
        model_path = self.get_parameter('model_path').value
        conf_thresh = self.get_parameter('conf_thresh').value
        nms_thresh = self.get_parameter('nms_thresh').value
        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        show_image = self.get_parameter('show_image').value

        # 初始化BPU检测器
        self.get_logger().info(f"🔧 初始化BPU YOLO检测器...")
        self.detector = BPUYOLO(
            model_path=model_path,
            conf_thresh=conf_thresh,
            nms_thresh=nms_thresh
        )

        # 初始化CV-Bridge
        self.bridge = CvBridge()

        # 统计变量
        self.frame_count = 0
        self.fps = 0.0
        self.last_time = self.get_clock().now()

        # 创建发布者
        self.detection_pub = self.create_publisher(
            Detection2DArray,
            output_topic,
            10
        )

        # 创建图像发布者（带检测框的可视化图像）
        self.image_pub = self.create_publisher(
            Image,
            '/yolo/image_detections',
            10
        )

        # 创建订阅者
        self.image_sub = self.create_subscription(
            Image,
            input_topic,
            self.image_callback,
            10
        )

        self.get_logger().info(f"✅ YOLO BPU节点启动成功！")
        self.get_logger().info(f"   订阅话题：{input_topic}")
        self.get_logger().info(f"   发布话题：{output_topic}")
        self.get_logger().info(f"   模型路径：{model_path}")

    def image_callback(self, msg):
        """
        图像回调函数：接收图像，执行检测，发布结果
        """
        try:
            # 将ROS2图像消息转换为OpenCV图像
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"图像转换失败: {e}")
            return

        # 执行BPU推理
        boxes, inf_time = self.detector.infer(cv_image)

        # 绘制检测框
        annotated_image = self.detector.draw_boxes(cv_image, boxes, COCO_CLASSES)

        # 计算FPS
        current_time = self.get_clock().now()
        elapsed = (current_time - self.last_time).nanoseconds / 1e9
        if elapsed > 0:
            self.fps = 1.0 / elapsed
        self.last_time = current_time

        # 在图像上显示FPS
        cv2.putText(annotated_image, f"FPS: {self.fps:.1f}",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.putText(annotated_image, f"Objects: {len(boxes)}",
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        # 发布可视化图像
        annotated_msg = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
        self.image_pub.publish(annotated_msg)

        # 构建ROS2检测消息
        detection_array = Detection2DArray()
        detection_array.header = msg.header
        detection_array.header.frame_id = "camera_frame"

        for box in boxes:
            detection = Detection2D()
            # 填充边界框信息
            bbox = BoundingBox2D()
            bbox.center.position.x = float((box[0] + box[2]) / 2)  # 中心x
            bbox.center.position.y = float((box[1] + box[3]) / 2)  # 中心y
            bbox.size_x = float(box[2] - box[0])                    # 宽度
            bbox.size_y = float(box[3] - box[1])                    # 高度
            detection.bbox = bbox

            # 填充置信度和类别
            detection.results[0].hypothesis.confidence = float(box[4])
            detection.results[0].hypothesis.class_id = COCO_CLASSES[int(box[5])]

            detection_array.detections.append(detection)

        # 发布检测结果
        self.detection_pub.publish(detection_array)

        # 日志输出（每30帧输出一次）
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            self.get_logger().info(
                f"检测帧数: {self.frame_count}, "
                f"FPS: {self.fps:.1f}, "
                f"推理时间: {inf_time*1000:.1f}ms, "
                f"检测目标: {len(boxes)}个"
            )

    def destroy_node(self):
        """节点销毁时释放资源"""
        self.get_logger().info("🛑 关闭YOLO BPU节点...")
        super().destroy_node()


def main(args=None):
    """节点入口函数"""
    rclpy.init(args=args)

    try:
        node = YOLONode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 7.3 启动文件

```python
# ~/robot_ws/src/rdk_yolo/launch/yolo_launch.py
# ROS2 YOLO检测节点启动文件

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    """
    生成启动描述

    用法：
        ros2 launch rdk_yolo yolo_launch.py

    参数：
        model_path: HB模型文件路径
        conf_thresh: 置信度阈值
        nms_thresh: NMS阈值
        input_topic: 输入图像话题
        output_topic: 输出检测结果话题
    """

    # 模型路径参数
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value='/userdata/models/yolov8s.nb',
        description='YOLO HB模型文件路径'
    )

    # 置信度阈值
    conf_thresh_arg = DeclareLaunchArgument(
        'conf_thresh',
        default_value='0.25',
        description='目标检测置信度阈值'
    )

    # NMS阈值
    nms_thresh_arg = DeclareLaunchArgument(
        'nms_thresh',
        default_value='0.45',
        description='NMS非极大值抑制阈值'
    )

    # 输入图像话题
    input_topic_arg = DeclareLaunchArgument(
        'input_topic',
        default_value='/image_raw',
        description='输入图像话题'
    )

    # YOLO检测节点
    yolo_node = Node(
        package='rdk_yolo',
        executable='yolo_node.py',
        name='yolo_bpu_node',
        output='screen',
        parameters=[{
            'model_path': LaunchConfiguration('model_path'),
            'conf_thresh': LaunchConfiguration('conf_thresh'),
            'nms_thresh': LaunchConfiguration('nms_thresh'),
            'input_topic': LaunchConfiguration('input_topic'),
            'show_image': True,
        }]
    )

    return LaunchDescription([
        model_path_arg,
        conf_thresh_arg,
        nms_thresh_arg,
        input_topic_arg,
        yolo_node,
    ])
```

### 7.4 setup.py配置

```python
# ~/robot_ws/src/rdk_yolo/setup.py

import os
from glob import glob
from setuptools import setup

package_name = 'rdk_yolo'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 包含launch文件
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_scripts=[
        # YOLO节点脚本（需要设为可执行）
    ],
    entry_points={
        'console_scripts': [
            'yolo_node = rdk_yolo.yolo_node:main',  # 节点入口点
        ],
    },
)
```

### 7.5 摄像头采集节点

如果使用MIPI摄像头，需要先启动摄像头驱动节点：

```bash
# 查看MIPI摄像头设备
v4l2-ctl --list-devices

# 启动摄像头驱动（ros2_v4l2_camera 或 hobot_xxx）
# 具体命令请参考 10-1-X-RDK-X5-MIPI摄像头接入.md

# 示例：使用ros2_v4l2_camera
ros2 launch ros2_v4l2_camera camera.launch.py \
    device:=/dev/video0 \
    image_size:=[640,480] \
    framerate:=30
```

---

## 8. 端到端实战

### 8.1 完整工作流

```
┌─────────────────────────────────────────────────────────────────┐
│                     端到端部署工作流                              │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   PC端       │    │   PC端       │    │   RDK-X5端   │      │
│  │  ① 下载.pt   │───▶│  ② 转ONNX    │───▶│  ④ 转HB     │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                              │                   │
│                                              ▼                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   RDK-X5端   │◀───│   网络传输    │◀───│  ③ 转HB     │      │
│  │  ⑤ BPU推理   │───▶│  ⑥ 发布结果  │    └──────────────┘      │
│  └──────────────┘    └──────────────┘                           │
│         │                  │                                    │
│         ▼                  ▼                                    │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │  图像采集     │    │  rqt_image   │                          │
│  │  (MIPI/USB)  │───▶│  _view 可视化 │                          │
│  └──────────────┘    └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 一键部署脚本

```bash
#!/bin/bash
# ~/robot_ws/deploy_yolo.sh
# YOLO on RDK-X5 一键部署脚本

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  YOLO on RDK-X5 BPU 一键部署脚本"
echo "=========================================="

# 配置区域
RDK_IP="192.168.1.100"          # RDK-X5 IP地址
MODEL_NAME="yolov8s"            # 模型名称
LOCAL_WORK="/home/$USER/yolo_work"  # PC端工作目录
REMOTE_MODEL="/userdata/models"     # RDK-X5模型目录
REMOTE_CODE="/home/nx_ros/robot_ws/src"  # RDK-X5代码目录

# 步骤1：本地构建ONNX模型
echo ""
echo "[1/6] 📦 构建ONNX模型..."
cd $LOCAL_WORK

if [ ! -f "${MODEL_NAME}.pt" ]; then
    echo "  下载YOLOv8模型..."
    wget -q https://github.com/ultralytics/assets/releases/download/v0.0.0/${MODEL_NAME}.pt
fi

if [ ! -f "${MODEL_NAME}.onnx" ]; then
    echo "  转换为ONNX..."
    python3 pt2onnx.py
fi

if [ ! -f "${MODEL_NAME}_opt.onnx" ]; then
    echo "  优化ONNX..."
    python3 optimize_onnx.py
fi

echo "  ✅ ONNX模型就绪"

# 步骤2：复制到Docker进行HB转换
echo ""
echo "[2/6] 🔄 Docker中转换为HB模型..."
docker start yolo_build 2>/dev/null || true
docker exec -it yolo_build bash -c "
    cd /workspace
    cp ${MODEL_NAME}_opt.onnx ./
    hb_model_convert \
        --model-name ${MODEL_NAME} \
        --onnx-model ./${MODEL_NAME}_opt.onnx \
        --output-dir ./hb_model \
        --input-mean '0,0,0' \
        --input-std '255,255,255' \
        --output-mean '0,0,0' \
        --output-std '1,1,1' \
        --calibration-type int8 \
        --performance-mode high
"

# 步骤3：同步HB模型到RDK-X5
echo ""
echo "[3/6] 📡 同步HB模型到RDK-X5..."
mkdir -p $REMOTE_MODEL
rsync -avP $LOCAL_WORK/hb_model/${MODEL_NAME}.nb \
    root@${RDK_IP}:${REMOTE_MODEL}/

echo "  ✅ HB模型同步完成"

# 步骤4：同步代码到RDK-X5
echo ""
echo "[4/6] 📡 同步Python代码到RDK-X5..."
rsync -avP --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pt' \
    --exclude='*.onnx' \
    $LOCAL_WORK/ \
    root@${RDK_IP}:${REMOTE_CODE}/

echo "  ✅ 代码同步完成"

# 步骤5：安装RDK-X5端依赖
echo ""
echo "[5/6] 🔧 RDK-X5安装依赖..."
ssh root@${RDK_IP} << 'ENDSSH'
    pip3 install -q numpy opencv-python-headless pillow horizon_nn
    cd /home/nx_ros/robot_ws
    colcon build --packages-select rdk_deploy rdk_yolo 2>/dev/null || true
ENDSSH

echo "  ✅ 依赖安装完成"

# 步骤6：验证部署
echo ""
echo "[6/6] ✅ 部署验证..."
ssh root@${RDK_IP} << 'ENDSSH'
    echo "  模型文件检查："
    ls -lh /userdata/models/${MODEL_NAME}.nb
    echo "  代码目录检查："
    ls -la /home/nx_ros/robot_ws/src/rdk_deploy/bpu_inference.py
ENDSSH

echo ""
echo "=========================================="
echo "  🎉 部署完成！"
echo "=========================================="
echo "  模型路径：${REMOTE_MODEL}/${MODEL_NAME}.nb"
echo "  代码路径：${REMOTE_CODE}"
echo ""
echo "  启动检测节点："
echo "  ssh root@${RDK_IP}"
echo "  cd /home/nx_ros/robot_ws"
echo "  source install/setup.bash"
echo "  ros2 run rdk_yolo yolo_node"
echo "=========================================="
```

```bash
# 赋予执行权限
chmod +x ~/robot_ws/deploy_yolo.sh

# 运行一键部署
~/robot_ws/deploy_yolo.sh
```

---

## 9. 部署与验证

### 9.1 文件放置路径规范

```bash
# RDK-X5 标准目录结构
/userdata/                           # 用户数据分区（持久化存储）
├── models/                          # 模型文件目录
│   ├── yolov8s.nb                  # HB模型文件
│   ├── yolov8s_deploy.yaml         # 部署配置
│   └── coco_classes.txt            # 类别名称文件
├── workspace/                      # 工作目录
│   └── test_images/                # 测试图片
└── datasets/                      # 数据集目录

/home/nx_ros/robot_ws/src/         # ROS2工作空间
├── rdk_deploy/                    # BPU推理通用模块
│   ├── __init__.py
│   ├── bpu_inference.py           # 核心推理类
│   └── test_bpu_fps.py            # 性能测试脚本
└── rdk_yolo/                      # YOLO检测功能包
    ├── rdk_yolo/
    │   ├── __init__.py
    │   └── yolo_node.py           # ROS2节点
    ├── launch/
    │   └── yolo_launch.py         # 启动文件
    └── package.xml
```

### 9.2 手动部署（rsync方式）

```bash
# 从PC端执行

# 1. 传输HB模型文件
rsync -avP ~/yolo_work/hb_model/yolov8s.nb \
    root@192.168.1.100:/userdata/models/

# 2. 传输推理代码
rsync -avP ~/robot_ws/src/rdk_deploy/ \
    root@192.168.1.100:/home/nx_ros/robot_ws/src/

# 3. 传输ROS2功能包
rsync -avP ~/robot_ws/src/rdk_yolo/ \
    root@192.168.1.100:/home/nx_ros/robot_ws/src/

# 4. 在RDK-X5上编译
ssh root@192.168.1.100
cd /home/nx_ros/robot_ws
colcon build --packages-select rdk_deploy rdk_yolo
source install/setup.bash
```

### 9.3 systemd开机自启服务

```ini
# /etc/systemd/system/rdk-yolo.service
# RDK-X5 YOLO检测系统服务（开机自启）

[Unit]
Description=RDK-X5 YOLO BPU Detection Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/nx_ros/robot_ws
ExecStart=/usr/bin/python3 /home/nx_ros/robot_ws/src/rdk_yolo/rdk_yolo/yolo_node.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# 环境变量
Environment="LD_LIBRARY_PATH=/opt/horizon/lib:$LD_LIBRARY_PATH"
Environment="PYTHONPATH=/home/nx_ros/robot_ws/src/rdk_deploy:$PYTHONPATH"

[Install]
WantedBy=multi-user.target
```

**配置开机自启**：

```bash
# 在RDK-X5上执行
# 1. 复制服务文件
sudo cp /path/to/rdk-yolo.service /etc/systemd/system/

# 2. 重新加载systemd配置
sudo systemctl daemon-reload

# 3. 启用服务（开机自启）
sudo systemctl enable rdk-yolo

# 4. 立即启动服务
sudo systemctl start rdk-yolo

# 5. 查看服务状态
sudo systemctl status rdk-yolo

# 6. 查看日志
journalctl -u rdk-yolo -f
```

### 9.4 rqt_image_view验证

```bash
# 在RDK-X5上启动检测节点（新终端）
ssh root@192.168.1.100
cd /home/nx_ros/robot_ws
source install/setup.bash

# 启动YOLO检测节点
ros2 run rdk_yolo yolo_node

# 新开一个终端，启动rqt_image_view
# 注意：需要配置DISPLAY（如果使用SSH X11转发）
rqt_image_view

# 或使用David终图形界面
# 选择话题：/yolo/image_detections
```

**通过RViz2验证**：

```bash
# 在RDK-X5上
rviz2

# 添加 Image 面板
# 选择话题 /yolo/image_detections
# 即可看到带检测框的图像
```

### 9.5 性能验证命令

```bash
# 测试BPU推理FPS
python3 /home/nx_ros/robot_ws/src/rdk_deploy/test_bpu_fps.py \
    --model /userdata/models/yolov8s.nb \
    --frames 200

# 查看ROS2话题列表
ros2 topic list

# 查看YOLO检测结果话题
ros2 topic echo /yolo/detections

# 查看图像发布话题
ros2 topic hz /yolo/image_detections
```

---

## 10. 性能对比

### 10.1 CPU vs GPU vs BPU 对比测试

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/benchmark_compare.py
# 不同硬件平台性能对比测试

import time
import numpy as np
import cv2

def benchmark_cpu(model_path, test_frames=100):
    """
    使用CPU推理（OpenCV DNN）
    """
    print("\n" + "="*50)
    print("🖥️  CPU (OpenCV DNN) 推理测试")
    print("="*50)

    # 加载ONNX模型（使用OpenCV DNN）
    net = cv2.dnn.readNetFromONNX(model_path.replace('.nb', '.onnx'))
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

    # 生成测试图像
    dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    blob = cv2.dnn.blobFromImage(dummy_img, 1/255.0, (640, 640))

    # 预热
    for _ in range(10):
        net.forward()

    # 测试
    times = []
    for _ in range(test_frames):
        start = time.time()
        net.forward()
        times.append(time.time() - start)

    times = np.array(times)
    print(f"  平均延迟：{np.mean(times)*1000:.1f} ms")
    print(f"  FPS：{1.0/np.mean(times):.1f}")
    print(f"  P95延迟：{np.percentile(times, 95)*1000:.1f} ms")
    return np.mean(times)


def benchmark_gpu(model_path, test_frames=100):
    """
    使用GPU推理（OpenCV DNN CUDA）
    """
    print("\n" + "="*50)
    print("🖥️  GPU (OpenCV DNN CUDA) 推理测试")
    print("="*50)

    try:
        net = cv2.dnn.readNetFromONNX(model_path.replace('.nb', '.onnx'))
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)

        dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        blob = cv2.dnn.blobFromImage(dummy_img, 1/255.0, (640, 640))

        # 预热
        for _ in range(10):
            net.forward()

        times = []
        for _ in range(test_frames):
            start = time.time()
            net.forward()
            times.append(time.time() - start)

        times = np.array(times)
        print(f"  平均延迟：{np.mean(times)*1000:.1f} ms")
        print(f"  FPS：{1.0/np.mean(times):.1f}")
        print(f"  P95延迟：{np.percentile(times, 95)*1000:.1f} ms")
        return np.mean(times)
    except Exception as e:
        print(f"  GPU不可用，跳过：{e}")
        return None


def benchmark_bpu(model_path, test_frames=100):
    """
    使用BPU推理（地平线加速器）
    """
    print("\n" + "="*50)
    print("🚀 BPU (地平线X5) 推理测试")
    print("="*50)

    sys.path.insert(0, '/home/nx_ros/robot_ws/src/rdk_deploy')
    from bpu_inference import BPUYOLO

    detector = BPUYOLO(model_path=model_path)

    dummy_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    # 预热
    for _ in range(10):
        detector.infer(dummy_img)

    times = []
    for _ in range(test_frames):
        _, inf_time = detector.infer(dummy_img)
        times.append(inf_time)

    times = np.array(times)
    print(f"  平均延迟：{np.mean(times)*1000:.1f} ms")
    print(f"  FPS：{1.0/np.mean(times):.1f}")
    print(f"  P95延迟：{np.percentile(times, 95)*1000:.1f} ms")
    return np.mean(times)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='/userdata/models/yolov8s.nb')
    parser.add_argument('--frames', type=int, default=100)
    args = parser.parse_args()

    print("\n" + "#"*60)
    print("#  YOLO推理平台性能对比测试")
    print("#"*60)

    cpu_time = benchmark_cpu(args.model, args.frames)
    gpu_time = benchmark_gpu(args.model, args.frames)
    bpu_time = benchmark_bpu(args.model, args.frames)

    print("\n" + "="*60)
    print("📊 性能对比汇总")
    print("="*60)
    print(f"{'平台':<15} {'平均延迟':<15} {'FPS':<15} {'加速比':<15}")
    print("-"*60)
    if cpu_time:
        print(f"{'CPU':<15} {cpu_time*1000:.1f}ms{'':<8} {1/cpu_time:.1f}{'':<10} {'1.0x':<15}")
    if gpu_time:
        speedup = cpu_time / gpu_time if cpu_time else 0
        print(f"{'GPU':<15} {gpu_time*1000:.1f}ms{'':<8} {1/gpu_time:.1f}{'':<10} {speedup:.1f}x{'':<13}")
    if bpu_time:
        speedup = cpu_time / bpu_time if cpu_time else 0
        print(f"{'BPU':<15} {bpu_time*1000:.1f}ms{'':<8} {1/bpu_time:.1f}{'':<10} {speedup:.1f}x{'':<13}")
    print("="*60)


if __name__ == "__main__":
    main()
```

**性能对比预期结果**：

```
================================================================
📊 性能对比汇总
================================================================
平台            平均延迟          FPS             加速比
------------------------------------------------------------
CPU            150.2ms          6.7             1.0x
GPU            28.5ms           35.1            5.3x
BPU            4.8ms            208.3           31.3x
================================================================
```

> **结论**：BPU的推理速度是CPU的 **31倍**，是GPU的 **6倍**，性能优势极为显著。

### 10.2 量化精度对比

| 量化类型 | 模型大小 | 推理延迟 | mAP@COCO | 精度损失 |
|---------|---------|---------|----------|---------|
| FP32（原始） | 46.6 MB | ~8ms | 44.9% | - |
| FP16（半精度） | 23.3 MB | ~5ms | 44.7% | -0.2% |
| INT8（量化） | 11.6 MB | **~4ms** | 44.3% | -0.6% |

> **推荐**：生产环境使用 **INT8量化**，精度损失极小（<1%），但推理速度提升近一倍。

---

## 11. 常见问题排查

### Q1: HB模型转换失败，提示"算子不支持"

**问题描述**：
```
[ERROR] Unsupported operator: ScatterND
```

**解决方案**：
1. 使用较新版本的hb_model_convert工具
2. 检查ONNX模型是否包含不兼容的算子
3. 尝试简化模型（减少后处理复杂度）

```bash
# 检查ONNX算子
python3 -c "
import onnx
m = onnx.load('model.onnx')
for n in m.graph.node:
    print(n.op_type)
" | sort | uniq -c | sort -rn
```

### Q2: BPU推理加载模型失败

**问题描述**：
```
RuntimeError: load model failed: file not found or permission denied
```

**解决方案**：
1. 检查文件路径是否正确
2. 检查文件权限
```bash
ls -la /userdata/models/yolov8s.nb
# 确保有读权限：chmod 644 /userdata/models/yolov8s.nb
```

### Q3: 图像预处理后检测结果全为空

**问题描述**：推理正常但没有检测结果

**解决方案**：
1. 检查预处理参数是否与模型转换时一致
2. 确认输入图像格式（BGR vs RGB）
3. 检查置信度阈值是否过高

```python
# 调试：打印预处理后的数据统计
print(f"输入数据范围：{input_data.min():.3f} ~ {input_data.max():.3f}")
print(f"输入数据形状：{input_data.shape}")
```

### Q4: ROS2节点订阅图像无响应

**问题描述**：YOLO节点启动成功但没有检测结果输出

**解决方案**：
1. 确认图像话题是否正确发布
```bash
# 检查可用话题
ros2 topic list

# 查看图像话题是否在发布
ros2 topic hz /image_raw
```

2. 检查节点日志是否有错误
```bash
ros2 run rdk_yolo yolo_node --ros-args --log-level debug
```

### Q5: 模型转换时内存不足

**问题描述**：
```
RuntimeError: Cannot allocate memory
```

**解决方案**：
1. 减少ONNX模型的batch size
2. 使用更小的输入分辨率
3. 在Docker中限制并发进程数

```bash
# 在Docker中限制内存
docker run --memory=8g ...
```

---

## 练习题

### 练习1：模型转换流程（填空题）

1. YOLOv8模型的标准导出格式是 ______，地平线BPU需要的模型格式是 ______。
2. 模型转换工具 `hb_model_convert` 应该在 ______（PC端/RDK-X5端）运行。
3. INT8量化相比FP32，推理速度约提升 ______ 倍，精度损失约 ______%。
4. YOLOv8的输出张量形状为 [1, 84, 8400]，其中84 = ______（bbox参数） + ______（类别数）。

### 练习2：代码补全题

请补全以下BPU推理代码中的后处理函数：

```python
def postprocess(self, output, scale, pad, img_shape):
    """YOLO输出后处理"""
    predictions = output[0]

    # 分离bbox和类别
    bbox_params = predictions[:4, :]
    class_scores = predictions[4:, :]

    # 获取最高置信度类别
    class_ids = np.argmax(________, axis=0)  # 补全1
    confidences = np.max(________, axis=0)   # 补全2

    # bbox解码（YOLOv8 xywh → xyxy）
    cx, cy = bbox_params[0, :], bbox_params[1, :]
    bw, bh = bbox_params[2, :], bbox_params[3, :]

    x1 = cx - bw / 2
    y1 = ________                           # 补全3
    x2 = cx + bw / 2
    y2 = ________                           # 补全4

    # 反算到原图坐标
    scale_factor = ________                  # 补全5
    x1 = (x1 - pad[0]) * scale_factor
    ...
```

### 练习3：实践题

**目标**：将自定义训练的YOLO模型部署到RDK-X5

**要求**：
1. 使用自己的数据集训练一个YOLOv8模型（可使用Roboflow导出）
2. 将.pt模型转换为.hb模型
3. 修改BPUYOLO类中的 `num_classes` 参数
4. 部署到RDK-X5并验证检测效果

**评分标准**：
- ✅ 模型转换成功（30分）
- ✅ 代码修改正确（30分）
- ✅ RDK-X5推理正常（20分）
- ✅ 检测结果正确（20分）

### 练习4：简答题

1. **BPU的工作原理是什么？** 为什么它比CPU/GPU更适合深度学习推理？
2. **模型量化的目的是什么？** INT8和FP16量化各有什么优缺点？
3. **YOLOv8的后处理包括哪些步骤？** 为什么后处理不能放在BPU上执行？
4. **在ROS2机器人中使用BPU加速时，需要注意哪些实时性问题？**

---

## 答案

### 练习1：填空题答案

1. **ONNX**，**NB/HB**（.nb文件）
2. **PC端**（在Docker容器中）
3. **约2倍**，**<1%**
4. **4**（4个边界框参数：cx, cy, w, h），**80**（COCO 80类）

### 练习2：代码补全答案

```python
# 补全1：沿类别维度找最大值索引
class_ids = np.argmax(class_scores, axis=0)

# 补全2：获取最大置信度值
confidences = np.max(class_scores, axis=0)

# 补全3：y1 = cy - bh/2
y1 = cy - bh / 2

# 补全4：y2 = cy + bh/2
y2 = cy + bh / 2

# 补全5：scale_factor = 1.0 / scale
scale_factor = 1.0 / scale
```

### 练习3：实践题答案要点

```bash
# 步骤1：导出自定义模型
python3 pt2onnx.py --model custom_model.pt --classes 10

# 步骤2：优化ONNX
python3 optimize_onnx.py --input custom_model.onnx --output custom_model_opt.onnx

# 步骤3：转换为HB
hb_model_convert \
    --model-name custom_model \
    --onnx-model custom_model_opt.onnx \
    --output-dir ./hb_model \
    --calibration-type int8

# 步骤4：修改推理类
# 在BPUYOLO.__init__中设置 num_classes=你的类别数

# 步骤5：部署到RDK-X5
rsync -avP custom_model.nb root@192.168.1.100:/userdata/models/
```

### 练习4：简答题答案要点

**1. BPU的工作原理**

BPU（Backbone Processing Unit）是专为神经网络设计的AI加速器：
- **硬件级算子支持**：内置卷积、池化、激活等常用算子的硬件电路
- **数据流优化**：脉动阵列架构，数据流过处理单元无需反复访问内存
- **低功耗设计**：专用电路而非通用计算，功耗远低于GPU
- **统一内存架构**：CPU与BPU共享大内存，避免数据传输瓶颈

**2. 模型量化目的**

- **目的**：用更低精度的数值（INT8/FP16）代替FP32，减少计算量和内存占用
- **INT8优点**：推理速度快2-4倍，模型体积小4倍，适合边缘部署
- **INT8缺点**：精度损失略大，需要校准数据
- **FP16优点**：精度损失极小，速度提升明显
- **FP16缺点**：速度提升不如INT8，模型体积减少2倍

**3. YOLOv8后处理步骤**

- 提取bbox参数和类别分数
- 置信度阈值过滤
- **NMS（非极大值抑制）**：按类别过滤重叠框
- 坐标反算到原图

**后处理不能放在BPU的原因**：
- NMS需要动态比较操作（排序、IoU计算），硬件不支持或效率极低
- 类别数动态可变，不适合硬件固化
- BPU只负责计算密集型的前向推理，数据处理类操作由CPU完成更高效

**4. ROS2实时性注意事项**

- 图像订阅使用**image_transport**压缩传输，减少带宽
- BPU推理放在独立线程，避免阻塞ROS主循环
- 设置合适的QoS策略（History: Keep Last, Depth: 1）
- 避免在回调函数中执行耗时操作，推理异步进行
- 使用`rclpy.spin_once`或`timer`控制检测频率

---

## 相关资料

- [地平线RDK-X5官方文档](https://d-robotics.github.io/rdk_doc)
- [地平线AI工具链文档](https://developer.horizon.ai/)
- [YOLOv8官方仓库](https://github.com/ultralytics/ultralytics)
- [ONNX Runtime文档](https://onnxruntime.ai/)
- [ROS2 Humble官方文档](https://docs.ros.org/en/humble/)

---

> **维护记录**：
> - 2026-03-24：初始编写完成（课程10-15-X）
