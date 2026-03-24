# 10-20-X VLM-on-RDK-X5 端侧部署

!!! info "课程概述"
    本课程介绍如何在 RDK-X5 开发板上部署视觉语言模型（VLM），实现图像理解、问答、描述生成等能力。涵盖模型准备、环境配置、推理部署、ROS2 集成全流程。

---

## 1. VLM 端侧部署概述

### 1.1 什么是端侧 VLM 部署

视觉语言模型（Vision-Language Model，VLM）是同时理解和处理图像与文本的多模态模型。端侧部署指将预训练好的 VLM 模型部署到本地硬件设备（如 RDK-X5）上运行，而非依赖云端 API。

### 1.2 端侧部署的优势

| 优势 | 说明 |
|------|------|
| **低延迟** | 本地推理无需网络往返，响应时间可控制在毫秒级 |
| **隐私保护** | 图像和文本数据不离开设备，适合安防、家庭等场景 |
| **离线运行** | 不依赖互联网，适用于户外、野外机器人作业 |
| **成本降低** | 无需支付云端 API 调用费用 |

### 1.3 RDK-X5 BPU 对 VLM 的支持

RDK-X5 搭载地平线 BPU（Brain Processing Unit）异构计算架构，对 VLM 的支持情况如下：

- **BPU 加速**：支持 INT8/FP16 量化模型的 BPU 加速推理
- **内存限制**：受限于端侧设备内存，建议使用 7B 参数以下的模型或量化版本
- **模型格式**：地平线提供专属模型转换工具链，支持 ONNX/OpenMMLab 格式
- **典型性能**：INT8 量化后 7B 模型推理延迟约 2-5 秒/图（取决于图像尺寸）

### 1.4 常见端侧 VLM 模型

| 模型 | 参数量 | 特点 | 适合场景 |
|------|--------|------|----------|
| **LLaVA-1.5** | 7B / 13B | 开源成熟，生态丰富 | 通用图像理解 |
| **Qwen-VL** | 7B / 9B | 阿里出品，中文支持好 | 中文机器人交互 |
| **MiniGPT-4** | 7B | 轻量高效 | 边缘设备优先 |
| **InternVL2** | 6B / 26B | 多模态能力强 | 高精度感知任务 |

> **推荐入门**：初学者建议从 **Qwen-VL2** 或 **LLaVA-1.5-7B** INT8 量化版本开始。

---

## 2. VLM 模型准备

### 2.1 主流开源 VLM 模型对比

```bash
# 模型下载目录（后续转换时使用）
mkdir -p /userdata/models/vlm
ls -la /userdata/models/vlm/
```

### 2.2 模型格式转换（以 LLaVA 为例）

地平线 AI 工具链要求将 PyTorch 模型转换为专用格式。以下以 LLaVA-1.5-7B 为例：

#### 2.2.1 安装模型转换依赖

```bash
# 在具备 GPU 的开发机器上执行（非 RDK-X5）
pip install transformers torch accelerate bitsandbytes \
    gguf petastorm onnx onnxruntime  # 转换依赖
```

#### 2.2.2 下载原始模型

```bash
# 从 HuggingFace 下载 LLaVA-1.5-7B 模型权重
# 方式一：使用 git lfs 克隆完整模型仓库（约 13GB）
cd /userdata/models/vlm
git lfs install
git clone https://huggingface.co/llava-hf/llava-1.5-7b-hf

# 方式二：使用 huggingface-cli 下载（需登录）
huggingface-cli download \
    --local-dir /userdata/models/vlm/llava-1.5-7b-hf \
    --local-dir-use-symlinks False \
    llava-hf/llava-1.5-7b-hf
```

#### 2.2.3 导出为 ONNX 格式（图像编码器 + 语言解码器）

```python
# /userdata/models/vlm/export_onnx.py
"""
将 LLaVA 模型导出为 ONNX 格式，供地平线工具链进一步转换
"""
import torch
from transformers import AutoModelForVision2Seq, AutoProcessor
import onnx

# 指定模型路径（从 HuggingFace 下载后的本地路径）
MODEL_PATH = "/userdata/models/vlm/llava-1.5-7b-hf"
OUTPUT_DIR = "/userdata/models/vlm/onnx"

# 加载模型和处理器
processor = AutoProcessor.from_pretrained(MODEL_PATH)
model = AutoModelForVision2Seq.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.float16,  # 使用半精度减少导出体积
    device_map="cpu",            # 导出时放在 CPU
)

# ---------- 导出视觉编码器（Vision Encoder）----------
vision_tower = model.vision_tower
vision_tower.eval()

# 构造虚拟输入（图像 token 数量根据模型配置）
dummy_pixel_values = torch.randn(
    1, 3, 336, 336  # LLaVA 1.5 默认输入分辨率 336x336
).half()

torch.onnx.export(
    vision_tower,
    (dummy_pixel_values,),
    f"{OUTPUT_DIR}/vision_encoder.onnx",
    input_names=["pixel_values"],
    output_names=["image_features"],
    dynamic_axes={
        "pixel_values": {0: "batch"},
        "image_features": {0: "batch"}
    },
    opset_version=14,
)
print(f"[OK] 视觉编码器已导出: {OUTPUT_DIR}/vision_encoder.onnx")

# ---------- 导出语言解码器（Language Decoder）----------
# 由于语言解码器较大，通常采用量化导出或直接使用地平线 runtime 加载
# 此处示例导出为简化版 ONNX（实际部署建议使用地平线专用 runtime）
language_model = model.language_model
language_model.eval()

# 虚拟输入：image_features + text tokens
batch_size = 1
seq_len = 128
dummy_input_ids = torch.randint(0, 32000, (batch_size, seq_len))
dummy_image_features = torch.randn(batch_size, 576, 1024).half()  # 576=image_tokens, 1024=hidden

torch.onnx.export(
    language_model,
    (dummy_input_ids, dummy_image_features),
    f"{OUTPUT_DIR}/language_decoder.onnx",
    input_names=["input_ids", "image_features"],
    output_names=["logits"],
    dynamic_axes={
        "input_ids": {0: "batch", 1: "seq"},
        "image_features": {0: "batch"},
        "logits": {0: "batch", 1: "seq"}
    },
    opset_version=14,
)
print(f"[OK] 语言解码器已导出: {OUTPUT_DIR}/language_decoder.onnx")

# ---------- 导出图像预处理（Preprocessing）----------
print("[OK] 导出完成！请使用地平线转换工具进一步优化模型")
```

```bash
# 执行导出脚本
mkdir -p /userdata/models/vlm/onnx
python /userdata/models/vlm/export_onnx.py

# 确认导出文件
ls -lh /userdata/models/vlm/onnx/
# 输出示例：
# vision_encoder.onnx   (~50MB)
# language_decoder.onnx (~800MB)
```

### 2.3 模型量化（INT8）

端侧部署强烈建议使用量化模型，以降低内存占用和推理延迟：

```bash
# 安装量化工具
pip install optimum-quanto onnxruntime-gpu

# 使用 optimum-quanto 对 ONNX 模型进行 INT8 量化
python3 << 'EOF'
from optimum.quanto import quantize, qint8
from onnxruntime.transformers import onnx_exporter
import onnx

# 加载视觉编码器
model = onnx.load("/userdata/models/vlm/onnx/vision_encoder.onnx")

# INT8 动态量化（激活值 int8，权重 int8）
quantize(model, weights=qint8)

# 保存量化后模型
onnx.save(model, "/userdata/models/vlm/onnx/vision_encoder_int8.onnx")
print("[OK] 视觉编码器 INT8 量化完成")

# 同样量化语言解码器
model_llm = onnx.load("/userdata/models/vlm/onnx/language_decoder.onnx")
quantize(model_llm, weights=qint8)
onnx.save(model_llm, "/userdata/models/vlm/onnx/language_decoder_int8.onnx")
print("[OK] 语言解码器 INT8 量化完成")
EOF
```

### 2.4 模型文件放置

```bash
# 在 RDK-X5 开发板上整理模型文件结构
mkdir -p /userdata/models/vlm/
tree /userdata/models/vlm/

# 推荐的文件结构如下：
# /userdata/models/vlm/
# ├── llava-1.5-7b-hf/          # 原始 HuggingFace 格式（可选）
# ├── onnx/                     # ONNX 格式模型
# │   ├── vision_encoder.onnx
# │   ├── vision_encoder_int8.onnx
# │   ├── language_decoder.onnx
# │   └── language_decoder_int8.onnx
# └── config.json               # 模型配置文件
```

---

## 3. 环境搭建

### 3.1 Python 环境配置

```bash
# 在 RDK-X5 开发板上操作
# 创建独立的 Python 虚拟环境（推荐 Python 3.8-3.10）
python3 -m venv /userdata/venv/vlm_env
source /userdata/venv/vlm_env/bin/activate

# 升级 pip
pip install --upgrade pip setuptools wheel
```

### 3.2 地平线 AI 工具链

地平线官方提供完整的端侧部署工具链，包括模型转换、runtime 部署等：

```bash
# 添加地平线 Python 源（若使用地平线提供的 pip 仓库）
# 注意：以下为示意，实际请参考 d-robotics.github.io/rdk_doc 官方文档
# pip install horizon_plugin_pytorch horizon_nn

# 验证地平线工具链安装
python3 -c "import horizon_nn; print('horizon_nn version:', horizon_nn.__version__)"
```

### 3.3 依赖安装

```bash
# 安装 VLM 推理核心依赖
pip install \
    torch==2.1.0 \
    transformers==4.36.0 \
    accelerate==0.25.0 \
    pillow==10.1.0 \
    numpy==1.24.3 \
    opencv-python==4.8.1.78 \
    onnxruntime==1.16.3

# 安装 ROS2 相关依赖（如果尚未安装）
pip install rclpy sensor_msgs geometry_msgs cv_bridge
```

### 3.4 推理框架安装

```bash
# 安装地平线 BPU Runtime（必选）
# 具体安装命令请参考地平线官方文档：
# https://d-robotics.github.io/rdk_doc/
# 以下为示意
pip install horizon_pytorch horizon_nn

# 验证 BPU 可用性
python3 << 'EOF'
try:
    import horizon_nn
    print("[OK] 地平线 horizon_nn 安装成功")
except ImportError as e:
    print(f"[WARN] horizon_nn 未安装: {e}")
    print(">>> 请参考官方文档安装 BPU Runtime")
EOF
```

---

## 4. VLM 推理部署

### 4.1 模型加载

```python
# /userdata/robot_ws/src/rdk_deploy/vlm_deploy/vlm_inference.py
"""
VLM 推理模块 - 模型加载与图像理解
"""

import os
import time
import json
import numpy as np
from PIL import Image
from typing import List, Tuple, Optional

# ====================== 配置区 ======================
# 模型文件路径（根据实际转换后的文件调整）
MODEL_DIR = "/userdata/models/vlm/onnx"
VISION_ENCODER_PATH = os.path.join(MODEL_DIR, "vision_encoder_int8.onnx")
LANGUAGE_DECODER_PATH = os.path.join(MODEL_DIR, "language_decoder_int8.onnx")

# 图像预处理参数（LLaVA 1.5 默认配置）
IMAGE_SIZE = 336       # 输入图像分辨率
MEAN = [0.48145466, 0.4578275, 0.40821073]  # ImageNet 均值
STD = [0.26862954, 0.26130258, 0.27577711]   # ImageNet 标准差


class VLMInference:
    """视觉语言模型推理类"""

    def __init__(self):
        """初始化：加载 ONNX 模型"""
        try:
            # 优先尝试地平线 BPU Runtime
            import horizon_nn as hnn
            self.use_horizon = True
            print("[INFO] 使用地平线 BPU 加速推理")

            # 加载视觉编码器到 BPU
            self.vision_session = hnn.load(
                VISION_ENCODER_PATH,
                device=hnn.HORIZONN,
            )
            # 加载语言解码器（通常在 CPU/NPU 执行）
            self.llm_session = hnn.load(
                LANGUAGE_DECODER_PATH,
                device=hnn.HORIZONN,
            )

        except ImportError:
            # Fallback: 使用 ONNX Runtime
            self.use_horizon = False
            print("[WARN] 地平线 runtime 未安装，使用 ONNX Runtime")
            import onnxruntime as ort

            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )

            self.vision_session = ort.InferenceSession(
                VISION_ENCODER_PATH, sess_options
            )
            self.llm_session = ort.InferenceSession(
                LANGUAGE_DECODER_PATH, sess_options
            )

        print("[OK] VLM 模型加载完成")

    # ==================== 图像预处理 ====================
    @staticmethod
    def preprocess_image(image: Image.Image) -> np.ndarray:
        """
        图像预处理：resize + normalize + 通道转换

        Args:
            image: PIL Image 对象

        Returns:
            预处理后的 numpy 数组，形状 (3, H, W)，已归一化到 [0,1]
        """
        # 1. Resize 到模型输入尺寸
        image = image.resize((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)

        # 2. 转为 numpy 数组 (H, W, C)，并归一化到 [0, 1]
        img_np = np.array(image).astype(np.float32) / 255.0

        # 3. 通道转换 (H, W, C) -> (C, H, W)
        img_np = img_np.transpose(2, 0, 1)

        # 4. 标准化（减均值、除标准差）
        # broadcast: (C, H, W) - (3, 1, 1)
        mean = np.array(MEAN)[:, None, None]
        std = np.array(STD)[:, None, None]
        img_np = (img_np - mean) / std

        # 5. 转换为半精度（节省内存和加速）
        img_np = img_np.astype(np.float16)

        # 6. 添加 batch 维度
        img_np = np.expand_dims(img_np, axis=0)  # (1, 3, H, W)

        return img_np

    # ==================== 视觉特征提取 ====================
    def extract_vision_features(self, pixel_values: np.ndarray) -> np.ndarray:
        """
        使用视觉编码器提取图像特征

        Args:
            pixel_values: 预处理后的图像张量 (1, 3, 336, 336)

        Returns:
            图像特征向量，用于后续语言解码
        """
        if self.use_horizon:
            # 地平线 runtime 接口
            outputs = self.vision_session.inference(
                {"pixel_values": pixel_values}
            )
            # 返回第一个输出
            image_features = outputs[0]
        else:
            # ONNX Runtime 接口
            outputs = self.vision_session.run(
                None,
                {"pixel_values": pixel_values}
            )
            image_features = outputs[0]

        return image_features

    # ==================== 文本处理 ====================
    @staticmethod
    def encode_text(text: str, tokenizer) -> np.ndarray:
        """
        将文本编码为 token IDs

        Args:
            text: 输入文本
            tokenizer: 分词器

        Returns:
            token IDs 数组
        """
        # 使用 transformers 的 tokenizer
        inputs = tokenizer(
            text,
            return_tensors="np",
            padding=True,
            truncation=True,
            max_length=128,
        )
        return inputs["input_ids"]

    # ==================== 推理调用 ====================
    def inference(
        self,
        image: Image.Image,
        prompt: str,
        tokenizer,
        max_new_tokens: int = 128,
    ) -> str:
        """
        端到端推理：图像 + 文本 → 文本回答

        Args:
            image: PIL Image 对象
            prompt: 输入提示词（如 "描述这张图片"）
            tokenizer: 分词器
            max_new_tokens: 最大生成的 token 数量

        Returns:
            模型生成的文本回答
        """
        t_start = time.time()

        # Step 1: 图像预处理
        pixel_values = self.preprocess_image(image)

        # Step 2: 提取视觉特征
        image_features = self.extract_vision_features(pixel_values)

        # Step 3: 文本编码
        input_ids = self.encode_text(prompt, tokenizer)

        # Step 4: 语言模型推理（自回归生成）
        generated_ids = self._generate(
            input_ids, image_features, tokenizer, max_new_tokens
        )

        # Step 5: 解码为文本
        response = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

        t_end = time.time()
        print(f"[VLM] 推理耗时: {t_end - t_start:.2f}s")

        return response

    def _generate(
        self,
        input_ids: np.ndarray,
        image_features: np.ndarray,
        tokenizer,
        max_new_tokens: int,
    ) -> List[List[int]]:
        """简化版自回归生成（实际部署建议使用 fastergenerate）"""
        generated = input_ids.tolist()
        past_key_values = None

        for _ in range(max_new_tokens):
            if self.use_horizon:
                outputs = self.llm_session.inference({
                    "input_ids": np.array(generated[:, -1:]),
                    "image_features": image_features,
                })
            else:
                outputs = self.llm_session.run(
                    None,
                    {
                        "input_ids": np.array(generated[:, -1:]),
                        "image_features": image_features,
                    }
                )

            logits = outputs[0][0, -1, :]
            next_token_id = int(np.argmax(logits))

            if next_token_id == tokenizer.eos_token_id:
                break

            generated[0].append(next_token_id)

        return generated


# ====================== 测试代码 ======================
if __name__ == "__main__":
    from transformers import AutoTokenizer

    # 加载分词器（使用 HuggingFace 模型对应的 tokenizer）
    tokenizer = AutoTokenizer.from_pretrained(
        "/userdata/models/vlm/llava-1.5-7b-hf",
        trust_remote_code=True,
    )

    # 初始化推理引擎
    vlm = VLMInference()

    # 读取测试图像
    test_image = Image.open("/userdata/test_images/robot_cam.jpg")

    # 图像描述
    prompt = "请描述这张图片"
    response = vlm.inference(test_image, prompt, tokenizer)
    print(f"描述结果: {response}")

    # 图像问答
    prompt = "图中有什么物体？"
    response = vlm.inference(test_image, prompt, tokenizer)
    print(f"问答结果: {response}")
```

### 4.2 性能测试

```python
# /userdata/robot_ws/src/rdk_deploy/vlm_deploy/benchmark.py
"""
VLM 推理性能基准测试
测量延迟、吞吐量、内存占用
"""

import time
import psutil
import os
from PIL import Image
import numpy as np

# 导入 VLM 推理模块
from vlm_inference import VLMInference


def measure_latency(vlm, image, prompt, tokenizer, runs: int = 10):
    """测量单次推理延迟"""
    latencies = []

    for i in range(runs):
        # 预热（第一次可能触发 JIT 编译）
        if i == 0:
            _ = vlm.inference(image, prompt, tokenizer, max_new_tokens=32)

        start = time.perf_counter()
        _ = vlm.inference(image, prompt, tokenizer, max_new_tokens=64)
        end = time.perf_counter()

        latencies.append(end - start)
        print(f"  Run {i+1}/{runs}: {latencies[-1]:.3f}s")

    avg_latency = np.mean(latencies)
    std_latency = np.std(latencies)
    throughput = 1.0 / avg_latency

    print(f"\n=== 延迟统计 ({runs} 次) ===")
    print(f"  平均延迟: {avg_latency:.3f}s ± {std_latency:.3f}s")
    print(f"  吞吐量:   {throughput:.2f} 图/秒")
    print(f"  最小延迟:  {np.min(latencies):.3f}s")
    print(f"  最大延迟:  {np.max(latencies):.3f}s")

    return avg_latency, throughput


def measure_memory():
    """测量当前进程内存占用"""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    mem_mb = mem_info.rss / 1024 / 1024
    print(f"\n=== 内存占用 ===")
    print(f"  RSS: {mem_mb:.1f} MB")
    return mem_mb


if __name__ == "__main__":
    from transformers import AutoTokenizer

    # 加载 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        "/userdata/models/vlm/llava-1.5-7b-hf",
        trust_remote_code=True,
    )

    # 初始化 VLM
    vlm = VLMInference()

    # 加载测试图像
    test_image = Image.open("/userdata/test_images/robot_cam.jpg")

    # 测量内存基线
    baseline_mem = measure_memory()

    # 性能测试
    prompt = "简要描述这张图片的内容"
    measure_memory()
    measure_latency(vlm, test_image, prompt, tokenizer, runs=5)
```

---

## 5. ROS2 VLM 节点

### 5.1 功能包结构

```bash
# 创建 ROS2 功能包（在 RDK-X5 或开发机上操作）
cd ~/robot_ws/src
ros2 pkg create --build-type ament_python rdk_vlm --dependencies \
    rclpy sensor_msgs std_msgs cv_bridge image_geometry opencv_python

# 查看生成的功能包结构
tree ~/robot_ws/src/rdk_vlm/
# rdk_vlm/
# ├── rdk_vlm/
# │   ├── __init__.py
# │   ├── vlm_node.py        # VLM 推理 ROS2 节点
# │   └── vlm_inference.py   # VLM 推理核心模块
# ├── resource/
# ├── test/
# ├── setup.py
# └── package.xml
```

### 5.2 VLM ROS2 节点实现

```python
# /home/nx_ros/robot_ws/src/rdk_vlm/rdk_vlm/vlm_node.py
"""
ROS2 VLM 节点 - 将 VLM 推理能力封装为 ROS2 节点
订阅摄像头图像，发布文本理解结果
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy

import sys
import os
import time
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from std_msgs.msg import String
from sensor_msgs.msg import Image as SensorImage
from cv_bridge import CvBridge

# 导入 VLM 推理模块（路径：rdk_vlm/vlm_inference.py）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from vlm_inference import VLMInference


class VLMNode(Node):
    """ROS2 VLM 视觉语言模型节点"""

    def __init__(self):
        super().__init__("vlm_node")

        # ==================== 参数声明 ====================
        # 推理参数
        self.declare_parameter("model_dir", "/userdata/models/vlm/onnx")
        self.declare_parameter("prompt", "请描述这张图片")
        self.declare_parameter("max_new_tokens", 128)
        self.declare_parameter("image_timeout_sec", 5.0)

        # 话题参数
        self.declare_parameter("image_topic", "/image_raw")
        self.declare_parameter("result_topic", "/vlm/result")

        self.model_dir = self.get_parameter("model_dir").value
        self.prompt = self.get_parameter("prompt").value
        self.max_new_tokens = self.get_parameter("max_new_tokens").value
        self.image_timeout_sec = self.get_parameter("image_timeout_sec").value
        self.image_topic = self.get_parameter("image_topic").value
        self.result_topic = self.get_parameter("result_topic").value

        # ==================== CV Bridge ====================
        self.bridge = CvBridge()

        # ==================== VLM 推理引擎 ====================
        self.get_logger().info("正在初始化 VLM 推理引擎...")
        self.vlm: Optional[VLMInference] = None
        self._init_vlm()

        # ==================== Tokenizer ====================
        self._init_tokenizer()

        # ==================== ROS2 发布者/订阅者 ====================
        # 文本结果发布者
        self.result_pub = self.create_publisher(
            String, self.result_topic, QoSProfile(depth=10)
        )

        # 图像订阅者（可靠传输，确保不丢帧）
        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.RELIABLE,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.image_sub = self.create_subscription(
            SensorImage,
            self.image_topic,
            self._image_callback,
            qos,
        )

        # 标志位：当前是否有待处理图像
        self.latest_image: Optional[SensorImage] = None
        self.is_processing = False

        # 图像定时器（控制推理频率，避免过载）
        self.timer = self.create_timer(0.5, self._process_timer_callback)

        self.get_logger().info(f"VLM 节点已就绪！订阅话题: {self.image_topic}")
        self.get_logger().info(f"默认提示词: {self.prompt}")

    def _init_vlm(self):
        """初始化 VLM 推理引擎"""
        try:
            from vlm_inference import VLMInference
            self.vlm = VLMInference()
            self.get_logger().info("[OK] VLM 推理引擎初始化完成")
        except Exception as e:
            self.get_logger().error(f"VLM 初始化失败: {e}")
            raise

    def _init_tokenizer(self):
        """初始化分词器"""
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_dir.replace("/onnx", ""),
                trust_remote_code=True,
            )
            self.get_logger().info("[OK] 分词器加载完成")
        except Exception as e:
            self.get_logger().error(f"分词器加载失败: {e}")
            raise

    # ==================== 图像回调 ====================
    def _image_callback(self, msg: SensorImage):
        """
        图像话题回调函数，缓存最新图像

        Args:
            msg: ROS2 图像消息
        """
        self.latest_image = msg
        # 可选：打印图像元信息
        # self.get_logger().debug(
        #     f"收到图像: {msg.width}x{msg.height} @ {msg.header.stamp.sec}.{msg.header.stamp.nanosec}"
        # )

    # ==================== 定时处理 ====================
    def _process_timer_callback(self):
        """定时器回调，批量处理最新图像"""
        # 如果正在处理或没有新图像，直接返回
        if self.is_processing or self.latest_image is None:
            return

        self.is_processing = True

        try:
            # 取出最新图像
            ros_image = self.latest_image
            self.latest_image = None  # 清空，允许接收下一帧

            # ROS Image -> OpenCV -> PIL Image
            cv_image = self.bridge.imgmsg_to_cv2(ros_image, desired_encoding="rgb8")
            pil_image = Image.fromarray(cv_image)

            # 执行 VLM 推理
            self.get_logger().debug("开始 VLM 推理...")
            t_start = time.time()

            response = self.vlm.inference(
                image=pil_image,
                prompt=self.prompt,
                tokenizer=self.tokenizer,
                max_new_tokens=self.max_new_tokens,
            )

            t_end = time.time()
            latency_ms = (t_end - t_start) * 1000

            # 发布结果
            result_msg = String()
            result_msg.data = response
            self.result_pub.publish(result_msg)

            # 日志输出
            self.get_logger().info(
                f"[VLM 推理完成] 延迟: {latency_ms:.0f}ms | 结果: {response[:80]}{'...' if len(response) > 80 else ''}"
            )

        except Exception as e:
            self.get_logger().error(f"推理过程出错: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.is_processing = False

    # ==================== 销毁节点 ====================
    def destroy_node(self):
        """清理资源"""
        self.get_logger().info("VLM 节点关闭中...")
        super().destroy_node()


# ====================== 入口函数 ======================
def main(args=None):
    rclpy.init(args=args)
    node = VLMNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("收到 Ctrl+C，退出节点")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
```

### 5.3 launch 启动文件

```xml
<!-- /home/nx_ros/robot_ws/src/rdk_vlm/launch/vlm.launch.py -->
"""
VLM 节点启动文件
用法: ros2 launch rdk_vlm vlm.launch.py
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """生成 launch 描述"""

    # ==================== 启动参数 ====================
    model_dir_arg = DeclareLaunchArgument(
        "model_dir",
        default_value="/userdata/models/vlm/onnx",
        description="VLM 模型目录路径",
    )

    image_topic_arg = DeclareLaunchArgument(
        "image_topic",
        default_value="/image_raw",
        description="摄像头图像话题",
    )

    prompt_arg = DeclareLaunchArgument(
        "prompt",
        default_value="请描述这张图片",
        description="VLM 推理提示词",
    )

    max_tokens_arg = DeclareLaunchArgument(
        "max_new_tokens",
        default_value="128",
        description="最大生成的 token 数",
    )

    # ==================== VLM 节点 ====================
    vlm_node = Node(
        package="rdk_vlm",
        executable="vlm_node",
        name="vlm_node",
        output="screen",          # 输出打印到屏幕
        emulate_tty=True,
        parameters=[
            {
                # 模型目录（会自动替换 DeclareLaunchArgument 的默认值）
                "model_dir": LaunchConfiguration("model_dir"),
                "image_topic": LaunchConfiguration("image_topic"),
                "prompt": LaunchConfiguration("prompt"),
                "max_new_tokens": LaunchConfiguration("max_new_tokens"),
            }
        ],
        # 节点启动顺序：等待 image_transport 等依赖
        # 依赖话题自动发现，无需额外配置
    )

    # ==================== 组合描述 ====================
    return LaunchDescription(
        [
            model_dir_arg,
            image_topic_arg,
            prompt_arg,
            max_tokens_arg,
            vlm_node,
        ]
    )
```

### 5.4 修改 setup.py

```python
# /home/nx_ros/robot_ws/src/rdk_vlm/setup.py
# 在原有 setup.py 中添加以下内容：

from setuptools import setup
import os
from glob import glob

package_name = "rdk_vlm"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        # 添加 launch 文件
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        (
            "share/" + package_name + "/launch",
            glob("launch/*.launch.py"),
        ),
    ],
    # ... 其他原有内容保持不变
    entry_points={
        "console_scripts": [
            # 添加 vlm_node 入口点
            "vlm_node = rdk_vlm.vlm_node:main",
        ],
    },
)
```

### 5.5 编译和运行

```bash
# 编译功能包（从 RDK-X5 或交叉编译后拷贝到板子）
cd ~/robot_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select rdk_vlm

# 激活工作空间
source install/setup.bash

# 运行 VLM 节点（默认参数）
ros2 launch rdk_vlm vlm.launch.py

# 指定参数运行（图像问答模式）
ros2 launch rdk_vlm vlm.launch.py \
    prompt:="图中有哪些物体？请列出" \
    max_new_tokens:=64

# 查看节点状态
ros2 node list
# 输出: /vlm_node

# 查看发布的话题
ros2 topic list | grep vlm
# 输出:
# /vlm/result   # VLM 文本结果

# 直接订阅结果话题
ros2 topic echo /vlm/result
```

---

## 6. 端到端实战

### 6.1 图像问答（Image QA）

```python
# /home/nx_ros/robot_ws/src/rdk_deploy/examples/vlm_qa.py
"""
图像问答示例 - 机器人自主感知的核心能力
"""

import sys
import os
from PIL import Image

# 将 vlm_inference.py 所在目录加入路径
sys.path.insert(0, "/home/nx_ros/robot_ws/src/rdk_deploy/vlm_deploy")
from vlm_inference import VLMInference
from transformers import AutoTokenizer


def image_qa(vlm: VLMInference, image_path: str, question: str, tokenizer):
    """
    图像问答函数

    Args:
        vlm: VLM 推理引擎实例
        image_path: 图像文件路径
        question: 提问内容
        tokenizer: 分词器

    Returns:
        回答文本
    """
    # 加载图像
    image = Image.open(image_path).convert("RGB")

    # 构造提示词（不同模型格式略有差异）
    prompt = f"用户问题: {question}\n请根据图片回答："

    # 执行推理
    answer = vlm.inference(image, prompt, tokenizer, max_new_tokens=128)

    return answer


if __name__ == "__main__":
    # 初始化
    tokenizer = AutoTokenizer.from_pretrained(
        "/userdata/models/vlm/llava-1.5-7b-hf",
        trust_remote_code=True,
    )
    vlm = VLMInference()

    # 示例图像（替换为实际图像路径）
    test_images = [
        "/userdata/test_images/kitchen.jpg",
        "/userdata/test_images/office.jpg",
        "/userdata/test_images/outdoor.jpg",
    ]

    # 预设问题列表
    questions = [
        "图中有什么物体？",
        "描述一下这个场景",
        "图中是否有危险物品？",
        "估计一下这个房间的面积",
    ]

    for img_path in test_images:
        if not os.path.exists(img_path):
            print(f"[SKIP] 图像不存在: {img_path}")
            continue

        print(f"\n{'='*60}")
        print(f"图像: {img_path}")

        for question in questions:
            
            answer = image_qa(vlm, img_path, question, tokenizer)
            print(f"  Q: {question}")
            print(f"  A: {answer}\n")


# ====================== 完整示例 ======================
if __name__ == "__main__":
    # 单元测试：运行所有预设问答
    print("[INFO] 启动 VLM 图像问答测试\n")
    image_qa_demo()
            
            answer = image_qa(vlm, img_path, question, tokenizer)
            print(f"  Q: {question}")
            print(f"  A: {answer}\n")


# ====================== 完整示例 ======================
if __name__ == "__main__":
    # 单元测试：运行所有预设问答
    print("[INFO] 启动 VLM 图像问答测试\n")
    image_qa_demo()
(vlm, img_path, question, tokenizer)
### 6.2 图像描述生成（Image Captioning）

```python
# /home/nx_ros/robot_ws/src/rdk_deploy/examples/vlm_caption.py
"""
图像描述生成（Image Captioning）示例
"""

import sys
sys.path.insert(0, "/home/nx_ros/robot_ws/src/rdk_deploy/vlm_deploy")
from vlm_inference import VLMInference
from transformers import AutoTokenizer
from PIL import Image


def generate_caption(vlm: VLMInference, image_path: str, tokenizer, style: str = "简短"):
    """
    生成图像描述

    Args:
        vlm: VLM 推理引擎
        image_path: 图像路径
        tokenizer: 分词器
        style: 描述风格（简短/详细/技术）

    Returns:
        图像描述文本
    """
    image = Image.open(image_path).convert("RGB")

    # 根据风格选择不同的提示词
    if style == "简短":
        prompt = "请用一句话简要描述这张图片。"
    elif style == "详细":
        prompt = "请详细描述这张图片，包括场景、物体、颜色、动作等细节。"
    else:  # 技术风格
        prompt = "以机器人感知视角描述这张图片，重点关注可操作信息。"

    caption = vlm.inference(image, prompt, tokenizer, max_new_tokens=200)
    return caption


def batch_caption(vlm, image_dir: str, tokenizer, output_file: str = None):
    """
    批量图像描述

    Args:
        vlm: VLM 推理引擎
        image_dir: 图像目录路径
        tokenizer: 分词器
        output_file: 可选，结果保存路径
    """
    import os
    results = []

    image_exts = (".jpg", ".jpeg", ".png", ".bmp")
    image_files = [
        f for f in os.listdir(image_dir)
        if f.lower().endswith(image_exts)
    ]

    print(f"[INFO] 发现 {len(image_files)} 张图像，开始批量描述...")

    for i, img_file in enumerate(sorted(image_files)):
        img_path = os.path.join(image_dir, img_file)
        caption = generate_caption(vlm, img_path, tokenizer, style="详细")

        results.append({"file": img_file, "caption": caption})
        print(f"  [{i+1}/{len(image_files)}] {img_file}: {caption[:60]}...")

    # 保存结果
    if output_file:
        import json
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"[OK] 结果已保存到: {output_file}")

    return results


if __name__ == "__main__":
    tokenizer = AutoTokenizer.from_pretrained(
        "/userdata/models/vlm/llava-1.5-7b-hf",
        trust_remote_code=True,
    )
    vlm = VLMInference()

    # 单张图像描述
    caption = generate_caption(
        vlm,
        "/userdata/test_images/demo.jpg",
        tokenizer,
        style="详细",
    )
    print(f"图像描述: {caption}")

    # 批量描述（取消注释即可使用）
    # batch_caption(vlm, "/userdata/test_images/", tokenizer,
    #                output_file="/userdata/output/captions.json")
```

### 6.3 机器人感知应用示例

```python
# /home/nx_ros/robot_ws/src/rdk_deploy/examples/robot_perception.py
"""
机器人感知应用 - 综合 VLM + 机器人决策示例
场景：机器人通过摄像头感知环境，做出导航/抓取/告警决策
"""

import sys
sys.path.insert(0, "/home/nx_ros/robot_ws/src/rdk_deploy/vlm_deploy")
from vlm_inference import VLMInference
from transformers import AutoTokenizer


class RobotPerception:
    """机器人感知类 - 基于 VLM 的环境理解"""

    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            "/userdata/models/vlm/llava-1.5-7b-hf",
            trust_remote_code=True,
        )
        self.vlm = VLMInference()

    def analyze_scene(self, image_path: str) -> dict:
        """
        综合场景分析

        Returns:
            dict: 包含场景描述、物体列表、安全评估的字典
        """
        from PIL import Image

        image = Image.open(image_path).convert("RGB")

        # 并行提问（串行执行，实际可并发优化）
        descriptions = [
            ("场景描述", "简要描述当前场景"),
            ("物体清单", "列出图中所有可见物体"),
            ("安全评估", "图中是否有危险物品或安全隐患？"),
            ("导航建议", "如果要在这个场景中行走，你有什么建议？"),
        ]

        results = {}
        for key, question in descriptions:
            prompt = f"图片分析问题: {question}"
            answer = self.vlm.inference(image, prompt, self.tokenizer, max_new_tokens=80)
            results[key] = answer

        return results

    def decide_action(self, scene_analysis: dict) -> str:
        """
        基于场景分析做出简单决策

        Args:
            scene_analysis: 场景分析结果字典

        Returns:
            建议的机器人动作
        """
        # 简单规则：检测关键词决定动作
        text = str(scene_analysis).lower()

        if any(kw in text for kw in ["危险", "危险物品", "障碍", "阻止"]):
            return "STOP - 检测到危险，停止移动"
        elif any(kw in text for kw in ["门", "通道", "畅通"]):
            return "FORWARD - 通道畅通，继续前进"
        elif any(kw in text for kw in ["目标物体", "抓取", "拿起"]):
            return "GRASP - 发现目标，执行抓取"
        elif any(kw in text for kw in ["楼梯", "台阶", "高差"]):
            return "ASCEND - 检测台阶，开始攀爬"
        else:
            return "EXPLORE - 继续探索环境"


if __name__ == "__main__":
    robot = RobotPerception()

    # 模拟机器人感知流程
    test_image = "/userdata/test_images/robot_cam.jpg"

    print("[机器人感知系统] 启动环境分析...")
    analysis = robot.analyze_scene(test_image)

    print("\n=== 场景分析结果 ===")
    for key, value in analysis.items():
        print(f"\n【{key}】")
        print(f"  {value}")

    action = robot.decide_action(analysis)
    print(f"\n=== 机器人动作决策 ===")
    print(f"  -> {action}")
```

---

## 7. 部署与验证

### 7.1 文件放置路径

```bash
# 推荐在 RDK-X5 开发板上建立如下目录结构
# /home/nx_ros/robot_ws/src/rdk_deploy/
# ├── vlm_deploy/               # VLM 核心推理模块
# │   ├── __init__.py
# │   ├── vlm_inference.py     # VLM 推理类（主模块）
# │   ├── benchmark.py         # 性能测试脚本
# │   └── requirements.txt     # Python 依赖
# ├── examples/                 # 示例代码
# │   ├── vlm_qa.py
# │   ├── vlm_caption.py
# │   └── robot_perception.py
# ├── models/                   # 模型文件（符号链接到 /userdata/models/vlm/）
# │   └── vlm -> /userdata/models/vlm/onnx
# └── scripts/                  # 辅助脚本
#     ├── download_model.sh     # 模型下载脚本
#     └── test_camera.sh        # 摄像头测试脚本

# 创建目录结构
mkdir -p ~/robot_ws/src/rdk_deploy/{vlm_deploy,examples,models,scripts}

# 建立模型目录符号链接（避免大文件重复存储）
ln -sf /userdata/models/vlm/onnx ~/robot_ws/src/rdk_deploy/models/vlm

# 查看最终结构
tree ~/robot_ws/src/rdk_deploy/
```

### 7.2 rsync/SSH 部署

```bash
# ==================== 从开发机推送到 RDK-X5 ====================
# 在开发机上执行（假设 RDK-X5 IP 为 192.168.1.101）

# 推送代码（增量同步）
rsync -avz --progress \
    ~/robot_ws/src/rdk_deploy/ \
    nx@192.168.1.101:/home/nx/robot_ws/src/rdk_deploy/

# 推送模型文件（如模型在开发机上）
rsync -avz --progress \
    /userdata/models/vlm/onnx/ \
    nx@192.168.1.101:/userdata/models/vlm/onnx/

# ==================== 在 RDK-X5 开发板上验证 ====================
# SSH 登录到 RDK-X5
ssh nx@192.168.1.101

# 验证文件完整性
ls -lh ~/robot_ws/src/rdk_deploy/vlm_deploy/vlm_inference.py
sha256sum ~/robot_ws/src/rdk_deploy/models/vlm/vision_encoder_int8.onnx

# 验证 Python 环境
source /userdata/venv/vlm_env/bin/activate
python3 -c "import torch, transformers, onnxruntime; print('依赖 OK')"
```

### 7.3 性能评估

```bash
# ==================== 延迟测试 ====================
# 在 RDK-X5 开发板上运行性能基准测试
cd ~/robot_ws/src/rdk_deploy/vlm_deploy
source /userdata/venv/vlm_env/bin/activate

python3 benchmark.py

# 预期输出示例：
# Run 1/5: 2.341s
# Run 2/5: 2.215s
# Run 3/5: 2.198s
# Run 4/5: 2.289s
# Run 5/5: 2.201s
#
# === 延迟统计 (5 次) ===
#   平均延迟: 2.249s ± 0.055s
#   吞吐量:   0.44 图/秒
#   最小延迟:  2.198s
#   最大延迟:  2.341s
```

### 7.4 内存与发热管理

```bash
# ==================== 内存监控 ====================
# 实时监控 VLM 进程的内存占用
watch -n 1 'ps aux | grep vlm_node | grep -v grep'

# 查看系统内存总览
free -h

# ==================== CPU/温度监控 ====================
# 查看 BPU 温度（RDK-X5 特定命令，请参考官方文档）
# 方式一：地平线工具
hrut_tempinfo

# 方式二：sysfs
cat /sys/class/thermal/thermal_zone0/temp
# 输出示例：45000 = 45°C

# 查看 CPU 使用率
top -bn1 | head -20

# ==================== 发热控制建议 ====================
# 1. 避免连续高频推理，设置推理间隔（如定时器 0.5s 以上）
# 2. 模型量化（INT8）可显著降低功耗和发热
# 3. 必要时加散热片或风扇（RDK-X5 官方配件）
# 4. 设置 CPU 限频（不推荐，影响性能）
cpufreq-set -g powersave  # 慎用
```

### 7.5 完整部署检查清单

```bash
# 在 RDK-X5 开发板上逐项检查

echo "===== VLM 端侧部署检查清单 ====="

echo -n "[1] Python 环境: "
source /userdata/venv/vlm_env/bin/activate && python3 --version

echo -n "[2] 依赖包: "
python3 -c "import torch, transformers, onnxruntime; print('OK')"

echo -n "[3] 模型文件: "
ls -lh /userdata/models/vlm/onnx/vision_encoder_int8.onnx

echo -n "[4] VLM 推理测试: "
python3 -c \
    "import sys; sys.path.insert(0, '/home/nx_ros/robot_ws/src/rdk_deploy/vlm_deploy'); \
    from vlm_inference import VLMInference; print('OK')"

echo -n "[5] ROS2 环境: "
source /opt/ros/humble/setup.bash && ros2 topic list | head -3

echo -n "[6] 摄像头驱动: "
v4l2-ctl --list-devices 2>/dev/null | head -5 || echo "请检查摄像头连接"

echo "===== 检查完成 ====="
```

---

## 8. 练习题

### 练习 1：模型选型判断

> 某机器人项目需要在 RDK-X5 上实现实时图像问答，要求：
> - 延迟 < 3 秒/图
> - 支持中文
> - 内存占用 < 4GB
>
> 请根据以下选项选择最适合的模型方案，并说明理由。
>
> A. LLaVA-1.5-13B 全精度（FP16）
> B. Qwen-VL-7B INT8 量化
> C. LLaVA-1.5-7B FP16
> D. MiniGPT-4 7B INT4 量化

---

### 练习 2：代码补全

> 补全以下 `VLMNode` 的图像回调函数，使其支持**多图批量推理**：
>
> ```python
> def _image_callback(self, msg: SensorImage):
>     # TODO: 将当前图像加入缓冲区
>     # TODO: 如果缓冲区未满（<3张），直接返回
>     # TODO: 如果缓冲区已满，执行批量推理
>     # TODO: 清空缓冲区
>     pass
> ```

---

### 练习 3：性能优化分析

> 某 VLM 部署项目测量发现：
> - 图像预处理：50ms
> - 视觉编码器推理：800ms
> - 语言解码器推理：1400ms
> - 文本后处理：10ms
>
> 请问：
> 1. 推理链路中最耗时的阶段是哪个？
> 2. 如果要将总延迟从 2260ms 降低到 1500ms 以内，可以采取哪些优化措施？

---

### 练习 4：ROS2 话题集成

> 现有 `/camera/image_raw` 话题发布 30fps 原始图像，VLM 推理需 2 秒/图。
>
> 请设计一个方案（伪代码或流程图），使 VLM 节点既能**不丢帧**又能**控制推理频率**，并说明：
> 1. QoS 配置如何设置
> 2. 缓冲区大小如何选择
> 3. 定时器间隔如何确定

---

## 9. 答案

### 答案 1：模型选型判断

**正确答案：B（Qwen-VL-7B INT8 量化）**

理由分析：

| 方案 | 中文支持 | 内存占用 | 推理延迟 | 是否满足要求 |
|------|----------|----------|----------|------------|
| A. LLaVA-13B FP16 | ❌ 弱 | ~26GB | >10s | ❌ 内存超标 |
| B. Qwen-VL-7B INT8 | ✅ 强 | ~3-4GB | ~2-3s | ✅ 全部满足 |
| C. LLaVA-7B FP16 | ❌ 弱 | ~14GB | ~4-6s | ❌ 内存/延迟 |
| D. MiniGPT-4 INT4 | ❌ 弱 | ~2GB | ~1-2s | ❌ 中文差 |

**Qwen-VL** 的优势：阿里自研，中文理解能力强；7B 参数量经 INT8 量化后内存约 3-4GB；推理延迟 2-3 秒/图，满足实时性要求。

---

### 答案 2：代码补全

```python
def _image_callback(self, msg: SensorImage):
    """
    图像回调：支持多图批量推理
    缓冲区满 3 张时，批量送入推理
    """
    from PIL import Image as PILImage
    from cv_bridge import CvBridge

    # TODO 1: 将当前图像加入缓冲区
    try:
        cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
        pil_image = PILImage.fromarray(cv_image)
        self.image_buffer.append(pil_image)
    except Exception as e:
        self.get_logger().warn(f"图像转换失败: {e}")
        return

    # TODO 2: 如果缓冲区未满（<3张），直接返回
    if len(self.image_buffer) < self.batch_size:
        return

    # TODO 3: 缓冲区已满，执行批量推理（取最新一张作为代表）
    # 注：实际批量推理需修改 VLMInference 支持批量输入
    latest_image = self.image_buffer[-1]
    self.get_logger().debug(f"批量推理: 取缓冲区最新图，共 {len(self.image_buffer)} 张")

    try:
        response = self.vlm.inference(
            latest_image, self.prompt, self.tokenizer, self.max_new_tokens
        )
        result_msg = String()
        result_msg.data = response
        self.result_pub.publish(result_msg)
    except Exception as e:
        self.get_logger().error(f"推理失败: {e}")

    # TODO 4: 清空缓冲区
    self.image_buffer.clear()
```

---

### 答案 3：性能优化分析

**1. 最耗时阶段：语言解码器推理（1400ms，占比 62%）**

> 这是 VLM 中 LLM 部分的固有瓶颈，自回归生成（逐 token 预测）无法并行。

**2. 优化措施：**

| 优化方向 | 具体方法 | 预期提升 |
|----------|----------|----------|
| **降低分辨率** | 将输入从 336x336 降至 224x224 | 视觉编码器 800ms -> ~400ms |
| **量化升级** | FP16 -> INT8 量化 | 整体延迟降低 30-40% |
| **Beam Search -> Greedy** | 改用贪婪解码（牺牲质量换速度） | 生成阶段加速 20-30% |
| **KV Cache** | 启用 Transformer 键值缓存 | 批量推理时效果显著 |
| **BPU 加速** | 确认视觉编码器在 BPU 上运行 | 视觉编码器再降 50%+ |
| **降低 max_tokens** | 将 max_new_tokens 从 128 降至 64 | 语言解码 1400ms -> ~700ms |

**综合优化后目标：** 400ms（视觉）+ 700ms（解码）= ~1100ms < 1500ms ✅

---

### 答案 4：ROS2 话题集成设计

```
摄像头（30fps） ---> [图像缓冲区] ---> [定时器 2s] ---> VLM 推理 ---> /vlm/result
                      (queue=1)           |
                      (丢弃旧帧)           |
                                         v
                              控制推理频率，避免积压
```

**设计说明：**

```python
# 1. QoS 配置
qos = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,   # 确保不丢关键帧
    history=QoSHistoryPolicy.KEEP_LAST,            # 只保留最新帧
    depth=1,                                       # 缓冲区仅 1，丢弃旧帧
)

# 2. 缓冲区选择：queue=1（最多 1 张图）
# - 30fps = 每 33ms 一帧；VLM 推理 2s
# - 2s 内最多积压 60 帧，depth=1 确保只处理最新帧
# - 避免内存溢出

# 3. 定时器间隔：>= 单次推理延迟（如 2.5s）
self.timer = self.create_timer(2.5, self._process_timer_callback)
# - 2.5s > 2s（推理时间），确保上一次推理完成后再处理下一帧
# - 吞吐量：0.4 图/秒

# 关键：图像回调中每次覆盖缓冲区最新帧（而非追加），
# 定时器每次只取 1 张最新图处理
```

---

## 📚 参考资料

1. [地平线 RDK X5 官方文档](https://d-robotics.github.io/rdk_doc/) - 模型转换工具链、Runtime API
2. [LLaVA 官方 GitHub](https://github.com/haotian-liu/LLaVA) - LLaVA 模型架构与权重
3. [Qwen-VL 官方文档](https://qwenlm.github.io/blog/qwen-vl/) - Qwen-VL 多模态模型
4. [ONNX Runtime 官方文档](https://onnxruntime.ai/) - ONNX 模型推理加速
5. [Horizon Open Platform](https://developer.horizon.ai/) - 地平线开发者平台

---

> ⏱️ **课程时长**：约 4 小时（理论 1.5h + 实践 2.5h）
> 🔧 **适合平台**：RDK-X5（已刷地平线 BPU 系统）
> 📦 **模型文件**：约 3-7GB（INT8 量化后）
