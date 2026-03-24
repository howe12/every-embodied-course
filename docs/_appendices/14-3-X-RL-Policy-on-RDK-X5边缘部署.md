# 14-3-X RL Policy on RDK-X5 边缘部署

> **前置课程**：[14-3 机器人强化学习训练实战](./14-3-RL训练实战.md)  
> **硬件平台**：RDK-X5（地平线旭日 X5）  
> **软件环境**：ROS2 Humble + Python 3.10 + 地平线 AI 工具链  
> **模型格式**：PyTorch (.pt) → ONNX (.onnx) → Horizon BPU (.hb)  

---

## 目录

1. [RL Policy 端侧部署概述](#1-rl-policy-端侧部署概述)
2. [RL Policy 训练与模型导出](#2-rl-policy-训练与模型导出)
3. [RDK-X5 环境配置](#3-rdk-x5-环境配置)
4. [ONNX 模型导出详解](#4-onnx-模型导出详解)
5. [模型量化与 HB 模型转换](#5-模型量化与-hb-模型转换)
6. [ROS2 RL 控制节点开发](#6-ros2-rl-控制节点开发)
7. [实机部署案例](#7-实机部署案例)
8. [部署与验证](#8-部署与验证)
9. [练习题](#9-练习题)
10. [答案](#10-答案)

---

## 1. RL Policy 端侧部署概述

### 1.1 什么是 Policy（策略网络）

Policy（策略网络）是强化学习（Reinforcement Learning, RL）的核心组件，它定义了智能体（机器人）在给定状态下选择动作的映射关系。

```
状态 s → Policy(s) → 动作 a
```

- **确定性策略（Deterministic Policy）**：给定状态输出单一动作 `a = π(s)`
- **随机性策略（Stochastic Policy）**：给定状态输出动作分布 `a ~ π(·|s)`，适合需要探索的场景

### 1.2 RL Policy 的表示形式

| 网络架构 | 适用场景 | 输入 | 输出 |
|----------|----------|------|------|
| **MLP**（多层感知机） | 低维状态空间（关节角度、速度等） | 传感器数值向量 | 动作向量 |
| **CNN**（卷积神经网络） | 图像输入（相机、深度图） | H×W×C 图像 | 动作/特征向量 |
| **Transformer** | 多模态融合、序列决策 | 多传感器时序数据 | 动作序列 |

### 1.3 机器人控制中的 RL Policy

RL Policy 在机器人领域有广泛应用：

| 应用场景 | 输入状态 | 输出动作 |
|----------|----------|----------|
| 移动机器人导航 | 激光雷达 + 里程计 | 线速度 + 角速度 |
| 机械臂操作 | 视觉图像 + 关节角度 | 关节力矩/位置 |
| 四足机器人步态 | IMU + 足端触觉 | 各关节角度 |
| 无人机控制 | GPS + IMU + 图像 | 姿态控制量 |

### 1.4 边缘部署 RL 的意义

| 优势 | 说明 |
|------|------|
| 低延迟 | 端侧推理 < 10ms，避免网络往返 50-100ms |
| 高可靠 | 无需网络连接，本地自主决策 |
| 隐私安全 | 数据不离机器人，不上传云端 |
| 能耗优化 | 专用 BPU 芯片比 GPU 功耗降低 10x |
| 实时控制 | 100Hz 以上控制频率，满足实时性要求 |

---

## 2. RL Policy 训练与模型导出

### 2.1 常见 RL 算法

| 算法 | 类型 | 适用场景 | 特点 |
|------|------|----------|------|
| **PPO**（Proximal Policy Optimization） | on-policy | 连续动作控制 | 稳定、高效、广泛应用 |
| **SAC**（Soft Actor-Critic） | off-policy | 连续动作控制 | 最大熵探索，适合稀疏奖励 |
| **TD3**（Twin Delayed DDPG） | off-policy | 连续动作控制 | 解决 DDPG 过估计问题 |

本课程以 **PPO** 为例，使用 Stable-Baselines3 框架训练。

### 2.2 安装训练依赖

```bash
# 在训练服务器（PC/云端）上执行
pip install torch torchvision
pip install stable-baselines3 shimmy gymnasium
pip install onnx onnxruntime onnxsim
```

### 2.3 Policy 训练代码

```python
"""
RL Policy 训练脚本 - 使用 Stable-Baselines3 PPO
文件路径: ~/rl_train/train_ppo.py
"""
import os
import gymnasium as gym
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

def make_env():
    """创建单个环境（以 Pendulum 为例，实际替换为机器人环境）"""
    env = gym.make("Pendulum-v1")
    return env

# 向量化环境配置
n_envs = 4  # 并行环境数量
env = DummyVecEnv([make_env for _ in range(n_envs)])
env = VecNormalize(env, norm_obs=True, norm_reward=True)

# PPO 模型配置
model = PPO(
    policy="MlpPolicy",          # 多层感知机策略网络
    env=env,
    learning_rate=3e-4,          # 学习率
    n_steps=2048,                # 每次更新收集的步数
    batch_size=64,               # 小批量大小
    n_epochs=10,                 # 每次更新的 epoch 数
    gamma=0.99,                  # 折扣因子
    gae_lambda=0.95,             # GAE 参数
    clip_range=0.2,              # PPO 裁剪范围
    ent_coef=0.01,               # 熵系数（促进探索）
    verbose=1,
    tensorboard_log="./ppo_tensorboard/"
)

# 开始训练
print("开始训练 PPO Policy...")
model.learn(
    total_timesteps=500_000,
    callback=EvalCallback(env, best_model_save_path="./logs_best/"),
    progress_bar=True
)

# 保存模型
model_save_path = "/userdata/models/ppo_policy.pt"
os.makedirs(os.path.dirname(model_save_path), exist_ok=True)
model.save(model_save_path)
print(f"模型已保存至: {model_save_path}")

# 保存环境归一化参数（部署时需要）
env.save("/userdata/models/vecnormalize_env.pkl")
print("环境归一化参数已保存")
```

### 2.4 运行训练

```bash
mkdir -p ~/rl_train && cd ~/rl_train
python train_ppo.py
```

---

## 3. RDK-X5 环境配置

### 3.1 系统要求

- RDK-X5 开发板（地平线旭日 X5 芯片）
- 烧录好 Ubuntu 22.04 系统镜像
- 网络连接（PC 与 RDK-X5 同一局域网）

### 3.2 Python 环境配置

```bash
# 通过 SSH 登录 RDK-X5
ssh root@<RDK-X5-IP>

# 配置 conda 环境
conda create -n rdk_rl python=3.10 -y
conda activate rdk_rl

# 安装基础依赖
pip install numpy opencv-python scipy onnxruntime
```

### 3.3 ROS2 Humble 安装

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ros-humble-ros-base ros-humble-control-msgs
sudo apt install -y ros-humble-sensor-msgs ros-humble-geometry-msgs
pip install rosdep && rosdep init
```

### 3.4 地平线 AI 工具链安装

> **重要**：地平线工具链在 **训练服务器（PC）** 上运行，用于模型转换；RDK-X5 只运行推理 runtime。

#### 训练服务器（PC）安装工具链

```bash
# 下载地址: https://developer.horizon.ai/ (d-robotics.github.io/rdk_doc)

# 安装依赖
sudo apt install -y python3-pyqt5 pyqt5-dev-tools

# 安装 hbdk（模型转换工具，版本根据下载调整）
pip install hbdk-4.30.3-cp38-cp38-linux_x86_64.whl

# 安装 horizon_mmlab（模型部署工具）
pip install horizon_mmlab-1.1.5-py3.8-linux-x86_64.whl

# 验证安装
hbdk --version
horizon_tool --version
```

#### RDK-X5 安装推理 runtime

```bash
# 在 RDK-X5 上安装 BPU runtime
pip install rknnpool-2.0.0-cp310-cp310-linux_aarch64.whl
pip install horizon_npu-6.4.6-py3.10-linux_aarch64.whl
```

### 3.5 网络连接与文件传输

```bash
# 测试网络连接
ping <RDK-X5-IP>

# 通过 rsync 传输文件
rsync -avz --progress /userdata/models/ root@<RDK-X5-IP>:/userdata/models/
```

---

## 4. ONNX 模型导出详解

### 4.1 为什么导出为 ONNX

```
PyTorch (.pt) → ONNX (.onnx) → HB 模型 (.hb)
                    ↓
         跨平台、跨框架的中间表示
         可被地平线工具链进一步优化
```

### 4.2 Policy 网络定义

```python
"""
Policy 网络定义（与训练时保持一致）
文件路径: ~/rl_train/model_def.py
"""
import torch
import torch.nn as nn


class MLPPolicy(nn.Module):
    """多层感知机策略网络"""
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super(MLPPolicy, self).__init__()
        self.state_dim = state_dim
        self.action_dim = action_dim

        # 策略网络主体
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
        )
        self.mean_layer = nn.Linear(hidden_dim // 2, action_dim)
        self.log_std = nn.Parameter(torch.zeros(action_dim))

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """前向传播（推理时使用，返回确定性动作）"""
        x = self.net(state)
        mean = self.mean_layer(x)
        return torch.tanh(mean)
```

### 4.3 ONNX 模型导出脚本

```python
"""
ONNX 模型导出脚本
文件路径: ~/rl_train/export_onnx.py
"""
import torch
import os
import sys
sys.path.insert(0, os.path.expanduser("~/rl_train"))


def export_policy_to_onnx(
    model_path: str = "/userdata/models/ppo_policy.pt",
    output_path: str = "/userdata/models/ppo_policy.onnx",
    state_dim: int = 3,
    action_dim: int = 1,
):
    """将 PyTorch Policy 模型导出为 ONNX 格式"""
    print(f"加载模型: {model_path}")
    model = torch.load(model_path, map_location="cpu")
    policy = model.policy  # PPO 模型的 policy 属性包含网络结构

    # 构造示例输入（批量大小=1 用于推理）
    example_input = torch.zeros(1, state_dim, dtype=torch.float32)

    # 动态轴设置（支持变长输入）
    dynamic_axes = {
        "state": {0: "batch_size"},
        "action": {0: "batch_size"}
    }

    print(f"导出 ONNX 模型: {output_path}")
    torch.onnx.export(
        policy,
        example_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["state"],
        output_names=["action"],
        dynamic_axes=dynamic_axes,
        verbose=False
    )

    # 验证 ONNX 模型
    print("验证 ONNX 模型...")
    import onnx
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)
    print(f"ONNX 模型大小: {os.path.getsize(output_path) / 1024 / 1024:.2f} MB")
    print(f"导出成功: {output_path}")

    # 简化 ONNX 模型（可选）
    print("简化 ONNX 模型...")
    import onnxsim
    simplified_model, check = onnxsim.simplify(output_path)
    if check:
        import onnx
        simplified_path = output_path.replace(".onnx", "_simplified.onnx")
        onnx.save(simplified_model, simplified_path)
        print(f"简化模型已保存: {simplified_path}")
        return simplified_path
    return output_path


if __name__ == "__main__":
    export_policy_to_onnx(
        model_path="/userdata/models/ppo_policy.pt",
        output_path="/userdata/models/ppo_policy.onnx",
        state_dim=3,
        action_dim=1
    )
```

### 4.4 运行 ONNX 导出

```bash
cd ~/rl_train
python export_onnx.py
```

### 4.5 ONNX 推理性能测试

```python
"""
ONNX 推理测试脚本
文件路径: ~/rl_train/test_onnx.py
"""
import onnxruntime as ort
import numpy as np
import time


def test_onnx_inference(onnx_path: str, n_tests: int = 10):
    """测试 ONNX 模型推理"""
    providers = [
        ("CUDAExecutionProvider", {"device_id": 0}),
        "CPUExecutionProvider"
    ]
    session = ort.InferenceSession(onnx_path, providers=providers)

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    print(f"输入名称: {input_name}, 输出名称: {output_name}")

    for i in range(n_tests):
        state = np.random.randn(1, 3).astype(np.float32)
        action = session.run([output_name], {input_name: state})[0]
        print(f"  Test {i+1}: action_shape={action.shape}")
        assert np.all(action >= -1.0) and np.all(action <= 1.0), "动作超出范围!"

    print("ONNX 推理测试通过!")

    # 性能基准测试
    n_warmup, n_runs = 10, 100
    state = np.random.randn(1, 3).astype(np.float32)
    for _ in range(n_warmup):
        _ = session.run([output_name], {input_name: state})

    start = time.time()
    for _ in range(n_runs):
        _ = session.run([output_name], {input_name: state})
    elapsed = time.time() - start

    print(f"\n推理延迟: {elapsed/n_runs*1000:.2f} ms/次")
    print(f"吞吐量: {n_runs/elapsed:.1f} 次/秒")


if __name__ == "__main__":
    test_onnx_inference("/userdata/models/ppo_policy.onnx")
```

---

## 5. 模型量化与 HB 模型转换

### 5.1 为什么需要量化

| 量化模式 | 模型体积 | 精度损失 | 推理速度 |
|----------|----------|----------|----------|
| FP32 | 原始大小 | 无 | 基准 |
| FP16 | 减少 2x | 极小 | 提升 2x |
| INT8 | 减少 4x | 较小 | 提升 2-4x |

### 5.2 生成量化校准数据

```python
"""
生成量化校准数据
文件路径: ~/rl_train/gen_calib_data.py
"""
import numpy as np
import pickle
import os

n_samples = 200
state_dim = 3

calib_data = []
for i in range(n_samples):
    state = np.random.uniform(-1, 1, size=(1, state_dim)).astype(np.float32)
    calib_data.append(state)

os.makedirs("/home/user/rdk_deploy/calibration_data", exist_ok=True)
with open("/home/user/rdk_deploy/calibration_data/calib_data.pkl", "wb") as f:
    pickle.dump(calib_data, f)

print(f"已生成 {n_samples} 个校准样本")
```

```bash
python ~/rl_train/gen_calib_data.py
```

### 5.3 ONNX → HB 模型转换

```bash
# 在训练服务器（PC）上执行

# 进入工具链环境
source /opt/horizon/toolchain/setup.bash

# 创建转换工作目录
mkdir -p ~/rdk_deploy/hb_convert
cd ~/rdk_deploy/hb_convert

# 复制 ONNX 模型
cp /userdata/models/ppo_policy.onnx ./

# FP16 量化转换（推荐）
hbdk-onnx2hb \
    --input ppo_policy.onnx \
    --output ppo_policy.hb \
    --input-name state \
    --output-name action \
    --model-format onnx \
    --march bernoulli_v2 \
    --quantize-mode fp16 \
    --calibration-data ./calibration_data/calib_data.pkl

# INT8 量化（压缩率更高）
hbdk-onnx2hb \
    --input ppo_policy.onnx \
    --output ppo_policy_int8.hb \
    --input-name state \
    --output-name action \
    --model-format onnx \
    --march bernoulli_v2 \
    --quantize-mode int8 \
    --calibration-data ./calibration_data/calib_data.pkl

# 查看生成的文件
ls -lh *.hb
```

> **参数说明**：
> - `--march bernoulli_v2`：RDK-X5（BPU 架构代号）
> - `--quantize-mode fp16/int8`：量化模式
> - `--calibration-data`：校准数据集路径

### 5.4 HB 模型信息查看

```python
"""
查看 HB 模型信息
文件路径: ~/rl_train/hb_model_info.py
"""
try:
    import hbdk as hbrt

    model = hbrt.Model.load("/userdata/models/ppo_policy.hb")
    print(f"模型名称: {model.name}")
    print(f"输入数量: {model.num_inputs}")
    print(f"输出数量: {model.num_outputs}")

    for i in range(model.num_inputs):
        inp = model.get_input(i)
        print(f"  输入 {i}: name={inp.name}, shape={inp.shape}, dtype={inp.dtype}")

    for i in range(model.num_outputs):
        out = model.get_output(i)
        print(f"  输出 {i}: name={out.name}, shape={out.shape}, dtype={out.dtype}")
except ImportError:
    print("[跳过] hbdk 未安装，跳过 HB 模型信息查看")
```

---

## 6. ROS2 RL 控制节点开发

### 6.1 创建 ROS2 工作空间

```bash
# 在 RDK-X5 上执行
mkdir -p ~/robot_ws/src
cd ~/robot_ws
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash

# 创建 RL 控制包
cd ~/robot_ws/src
ros2 pkg create rdk_rl_control --dependencies rclpy sensor_msgs geometry_msgs std_msgs
```

### 6.2 RL 控制节点主代码

```python
"""
ROS2 RL Policy 控制节点
文件路径: ~/robot_ws/src/rdk_rl_control/rdk_rl_control/rl_control_node.py
"""
import rclpy
from rclpy.node import Node
import numpy as np
import json
import os
import pickle

# 尝试导入 BPU 推理库
try:
    import hbdk as hbrt
    HBPU_AVAILABLE = True
except ImportError:
    HBPU_AVAILABLE = False
    print("[警告] 未检测到 hbdk，将使用 ONNX Runtime（CPU 推理）")

import onnxruntime as ort


class RLControlNode(Node):
    """
    RL Policy 控制节点
    订阅传感器话题 → 状态预处理 → Policy 推理 → 发布控制指令
    """

    def __init__(self):
        super().__init__('rl_control_node')

        # 参数配置
        self.declare_parameter('model_path', '/userdata/models/ppo_policy.hb')
        self.declare_parameter('onnx_fallback', '/userdata/models/ppo_policy.onnx')
        self.declare_parameter('normalize_path', '/userdata/models/vecnormalize_env.pkl')
        self.declare_parameter('state_dim', 3)
        self.declare_parameter('action_dim', 1)
        self.declare_parameter('control_freq', 20.0)
        self.declare_parameter('action_min', -1.0)
        self.declare_parameter('action_max', 1.0)

        self.model_path = self.get_parameter('model_path').value
        self.onnx_fallback = self.get_parameter('onnx_fallback').value
        self.normalize_path = self.get_parameter('normalize_path').value
        self.state_dim = self.get_parameter('state_dim').value
        self.action_dim = self.get_parameter('action_dim').value
        self.control_freq = self.get_parameter('control_freq').value
        self.action_min = self.get_parameter('action_min').value
        self.action_max = self.get_parameter('action_max').value

        self._load_model()
        self._load_normalizer()
        self._setup_publishers()
        self._setup_subscribers()

        self.latest_state = None
        self.state_received = False
        control_period = 1.0 / self.control_freq
        self.timer = self.create_timer(control_period, self._control_callback)

        self.get_logger().info(f'RL 控制节点已启动，控制频率: {self.control_freq} Hz')
        self.get_logger().info(f'模型路径: {self.model_path}')

    def _load_model(self):
        """加载 Policy 模型（BPU 优先，回退到 ONNX CPU）"""
        if HBPU_AVAILABLE and os.path.exists(self.model_path):
            self.get_logger().info('使用 BPU 加速推理')
            self.model = hbrt.Model.load(self.model_path)
            self.inference_func = self._inference_bpu
        elif os.path.exists(self.onnx_fallback):
            self.get_logger().warn('BPU 不可用，使用 ONNX Runtime（CPU）')
            providers = ['CPUExecutionProvider']
            self.session = ort.InferenceSession(self.onnx_fallback, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            self.inference_func = self._inference_onnx
        else:
            raise FileNotFoundError(f'未找到模型文件')

    def _load_normalizer(self):
        """加载环境归一化参数"""
        self.normalizer = None
        if os.path.exists(self.normalize_path):
            try:
                with open(self.normalize_path, 'rb') as f:
                    self.normalizer = pickle.load(f)
                self.get_logger().info('已加载环境归一化参数')
            except Exception as e:
                self.get_logger().warn(f'归一化参数加载失败: {e}')

    def _inference_bpu(self, state: np.ndarray) -> np.ndarray:
        """BPU 推理"""
        inputs = {self.model.get_input(0).name: state}
        outputs = self.model.forward(inputs)
        return outputs[self.model.get_output(0).name]

    def _inference_onnx(self, state: np.ndarray) -> np.ndarray:
        """ONNX Runtime 推理（CPU）"""
        outputs = self.session.run([self.output_name], {self.input_name: state})
        return outputs[0]

    def _setup_publishers(self):
        """设置发布者"""
        from geometry_msgs.msg import Vector3Stamped
        from std_msgs.msg import String

        self.action_pub = self.create_publisher(Vector3Stamped, '/rl/action', 10)
        self.diag_pub = self.create_publisher(String, '/rl/diagnostics', 5)

    def _setup_subscribers(self):
        """设置订阅者"""
        from sensor_msgs.msg import JointState
        self.state_sub = self.create_subscription(
            JointState, '/robot/joint_states', self._state_callback, 10)

    def _state_callback(self, msg):
        """将传感器数据转换为 Policy 输入格式"""
        positions = np.array(msg.position, dtype=np.float32)
        velocities = np.array(msg.velocity, dtype=np.float32)
        state = np.concatenate([positions, velocities])

        if self.normalizer is not None:
            state = self.normalizer.normalize(state)

        self.latest_state = state.reshape(1, -1).astype(np.float32)
        self.state_received = True

    def _control_callback(self):
        """控制定时器回调（固定频率调用）"""
        if not self.state_received or self.latest_state is None:
            return
        try:
            action = self.inference_func(self.latest_state)
            action = self._postprocess_action(action)
            self._publish_action(action)
            self._publish_diagnostics(action)
        except Exception as e:
            self.get_logger().error(f'推理出错: {e}')

    def _postprocess_action(self, action: np.ndarray) -> np.ndarray:
        """动作后处理：范围裁剪、安全检查"""
        action = action.flatten()
        action = np.clip(action, self.action_min, self.action_max)
        return action

    def _publish_action(self, action: np.ndarray):
        """发布控制指令"""
        from geometry_msgs.msg import Vector3Stamped
        msg = Vector3Stamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'rl_policy'
        if len(action) >= 1:
            msg.vector.x = float(action[0])
        if len(action) >= 2:
            msg.vector.y = float(action[1])
        if len(action) >= 3:
            msg.vector.z = float(action[2])
        self.action_pub.publish(msg)

    def _publish_diagnostics(self, action: np.ndarray):
        """发布诊断信息"""
        from std_msgs.msg import String
        msg = String()
        diag = {
            'timestamp': self.get_clock().now().nanoseconds,
            'action': action.tolist(),
            'inference_mode': 'BPU' if HBPU_AVAILABLE else 'CPU'
        }
        msg.data = json.dumps(diag)
        self.diag_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RLControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 6.3 启动文件

```python
"""
启动文件: ~/robot_ws/src/rdk_rl_control/rdk_rl_control/launch/rl_control.launch.py
"""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rdk_rl_control',
            executable='rl_control_node',
            name='rl_control_node',
            output='screen',
            parameters=[{
                'model_path': '/userdata/models/ppo_policy.hb',
                'onnx_fallback': '/userdata/models/ppo_policy.onnx',
                'normalize_path': '/userdata/models/vecnormalize_env.pkl',
                'state_dim': 3,
                'action_dim': 1,
                'control_freq': 20.0,
                'action_min': -1.0,
                'action_max': 1.0,
            }]
        ),
    ])
```

### 6.4 编译与运行

```bash
# 编译工作空间
cd ~/robot_ws
colcon build --packages-select rdk_rl_control
source install/setup.bash

# 启动 RL 控制节点
ros2 launch rdk_rl_control rl_control.launch.py
```

---

## 7. 实机部署案例

### 7.1 案例一：移动机器人导航 Policy

```python
"""
移动机器人导航 Policy 状态处理
文件路径: ~/robot_ws/src/rdk_rl_nav/rdk_rl_nav/nav_policy.py
"""
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import PoseStamped


class NavPolicy(Node):
    """
    导航 Policy 节点
    输入: 激光雷达数据 + 目标位置
    输出: 线速度 + 角速度
    """
    def __init__(self):
        super().__init__('nav_policy')
        self.declare_parameter('laser_points', 360)
        self.declare_parameter('goal_size', 3)

        self.laser_points = self.get_parameter('laser_points').value
        self.goal_size = self.get_parameter('goal_size').value
        self.laser_data = None
        self.goal_data = None

        self.laser_sub = self.create_subscription(
            LaserScan, '/scan', self._laser_callback, 10)
        self.goal_sub = self.create_subscription(
            PoseStamped, '/goal_pose', self._goal_callback, 10)

    def _laser_callback(self, msg: LaserScan):
        """处理激光雷达数据"""
        ranges = np.array(msg.ranges, dtype=np.float32)
        ranges = np.clip(ranges, 0, msg.range_max)
        ranges = ranges / msg.range_max  # 归一化到 [0, 1]
        self.laser_data = ranges

    def _goal_callback(self, msg: PoseStamped):
        """处理目标位置"""
        x = msg.pose.position.x
        y = msg.pose.position.y
        theta = 2 * np.arctan2(msg.pose.orientation.z, msg.pose.orientation.w)
        self.goal_data = np.array([x, y, theta], dtype=np.float32)

    def get_state(self) -> np.ndarray:
        """构造 Policy 输入状态向量"""
        if self.laser_data is None or self.goal_data is None:
            return None
        state = np.concatenate([self.laser_data, self.goal_data])
        return state.reshape(1, -1).astype(np.float32)
```

### 7.2 案例二：四足机器人步态 Policy

```python
"""
四足机器人步态 Policy 状态处理
文件路径: ~/robot_ws/src/rdk_rl_quadruped/rdk_rl_quadruped/gait_policy.py
"""
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, JointState


class QuadrupedGaitPolicy(Node):
    """
    四足机器人步态 Policy 节点
    输入: IMU 数据 + 关节角度/速度
    输出: 12 个关节目标角度（每条腿 3 个关节）
    """
    def __init__(self):
        super().__init__('quadruped_gait_policy')
        self.declare_parameter('num_legs', 4)
        self.declare_parameter('joints_per_leg', 3)

        self.num_legs = self.get_parameter('num_legs').value
        self.joints_per_leg = self.get_parameter('joints_per_leg').value
        self.imu_data = None
        self.joint_data = None

        self.imu_sub = self.create_subscription(
            Imu, '/imu/data', self._imu_callback, 10)
        self.joint_sub = self.create_subscription(
            JointState, '/robot/joint_states', self._joint_callback, 10)

    def _imu_callback(self, msg: Imu):
        """处理 IMU 数据（角速度 + 线加速度）"""
        angular = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z
        ], dtype=np.float32)
        linear = np.array([
            msg.linear_acceleration.x,
            msg.linear_acceleration.y,
            msg.linear_acceleration.z
        ], dtype=np.float32)
        self.imu_data = np.concatenate([angular, linear])  # 6 维

    def _joint_callback(self, msg: JointState):
        """处理关节状态（位置 + 速度）"""
        n_joints = self.num_legs * self.joints_per_leg
        positions = np.array(msg.position[:n_joints], dtype=np.float32)
        velocities = np.array(msg.velocity[:n_joints], dtype=np.float32)
        self.joint_data = np.concatenate([positions, velocities])  # 24 维

    def get_state(self) -> np.ndarray:
        """构造 Policy 输入状态向量: [IMU 6维, 关节 24维] = 30维"""
        if self.imu_data is None or self.joint_data is None:
            return None
        state = np.concatenate([self.imu_data, self.joint_data])
        return state.reshape(1, -1).astype(np.float32)
```

---

## 8. 部署与验证

### 8.1 文件放置路径

| 用途 | PC 端路径 | RDK-X5 端路径 |
|------|-----------|---------------|
| RL Policy 模型 | `/userdata/models/` | `/userdata/models/` |
| 归一化参数 | `/userdata/models/` | `/userdata/models/` |
| ROS2 工作空间 | `~/robot_ws/src/rdk_deploy/` | `~/robot_ws/src/rdk_deploy/` |
| 校准数据 | `~/rdk_deploy/calibration_data/` | （仅 PC 端） |

### 8.2 文件部署命令

```bash
# PC 端：将模型文件同步到 RDK-X5
rsync -avz --progress \
    /userdata/models/ \
    root@<RDK-X5-IP>:/userdata/models/

# PC 端：将 ROS2 包同步到 RDK-X5
rsync -avz --progress \
    ~/robot_ws/src/rdk_rl_control/ \
    root@<RDK-X5-IP>:~/robot_ws/src/rdk_rl_control/
```

### 8.3 推理延迟测试

```python
"""
RDK-X5 推理延迟测试脚本
文件路径: ~/robot_ws/src/rdk_rl_control/rdk_rl_control/latency_test.py
"""
import time
import numpy as np


def benchmark_inference(inference_func, state_shape=(1, 3), n_warmup=10, n_runs=200):
    """
    测试推理延迟
    Args:
        inference_func: 推理函数
        state_shape: 输入状态形状
        n_warmup: 预热次数
        n_runs: 正式测试次数
    """
    # 预热
    state = np.random.randn(*state_shape).astype(np.float32)
    for _ in range(n_warmup):
        _ = inference_func(state)

    # 计时测试
    latencies = []
    for _ in range(n_runs):
        state = np.random.randn(*state_shape).astype(np.float32)
        start = time.time()
        _ = inference_func(state)
        latencies.append((time.time() - start) * 1000)  # 转换为毫秒

    latencies = np.array(latencies)
    print(f"推理延迟统计 (共 {n_runs} 次):")
    print(f"  平均值: {np.mean(latencies):.2f} ms")
    print(f"  中位数: {np.median(latencies):.2f} ms")
    print(f"  P95:    {np.percentile(latencies, 95):.2f} ms")
    print(f"  P99:    {np.percentile(latencies, 99):.2f} ms")
    print(f"  最大值: {np.max(latencies):.2f} ms")
    return latencies
```

### 8.4 CPU vs BPU 对比实验

```bash
# 在 RDK-X5 上分别测试 CPU 和 BPU 推理延迟

# 1. 测试 ONNX Runtime（CPU）推理
python -c "
import onnxruntime as ort
import numpy as np
import time

session = ort.InferenceSession('/userdata/models/ppo_policy.onnx',
                                providers=['CPUExecutionProvider'])
input_name = session.get_inputs()[0].name
state = np.random.randn(1, 3).astype(np.float32)

# 预热
for _ in range(10):
    _ = session.run(None, {input_name: state})

# 测试
start = time.time()
for _ in range(100):
    _ = session.run(None, {input_name: state})
cpu_time = (time.time() - start) / 100 * 1000
print(f'CPU 推理延迟: {cpu_time:.2f}
ms')
print(f'CPU 推理延迟: {cpu_time:.2f} ms')
"
# 退出 RDK-X5 SSH，在 PC 端测试
# 下载模型到本地后测试 HB 模型
```

### 8.5 Policy 性能评估指标

| 指标 | 说明 | 达标标准 |
|------|------|----------|
| 推理延迟 | 单次推理耗时 | < 10ms（BPU）/ < 50ms（CPU） |
| 控制频率 | Policy 控制循环频率 | > 20Hz |
| 成功率 | 任务完成率 | > 80% |
| 动作平滑度 | 动作变化幅度 | < 阈值 |

### 8.6 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 模型加载失败 | 文件路径错误 | 检查 `/userdata/models/` 路径 |
| 推理超时 | BPU 未启动 | 检查 horizon_npu 安装 |
| 动作异常 | 归一化参数缺失 | 加载 `vecnormalize_env.pkl` |
| ROS2 话题无数据 | 订阅话题名错误 | 检查 `/robot/joint_states` |

---

## 9. 练习题

### 练习 1：ONNX 模型导出
**题目**：将一个 state_dim=11, action_dim=2 的 PPO 模型导出为 ONNX 格式，写出导出命令的关键参数设置。

<details>
<summary>点击查看答案</summary>

```python
example_input = torch.zeros(1, 11, dtype=torch.float32)
dynamic_axes = {"state": {0: "batch_size"}, "action": {0: "batch_size"}}

torch.onnx.export(
    policy,
    example_input,
    "ppo_policy.onnx",
    export_params=True,
    opset_version=14,
    input_names=["state"],
    output_names=["action"],
    dynamic_axes=dynamic_axes,
)
```
关键参数：`state_dim=11`, `action_dim=2`，`batch_size=1`。

</details>

### 练习 2：HB 模型转换
**题目**：使用 hbdk-onnx2hb 将 ONNX 模型转换为 RDK-X5 可用的 HB 模型，写出完整命令（假设校准数据在 `./calib/` 目录）。

<details>
<summary>点击查看答案</summary>

```bash
source /opt/horizon/toolchain/setup.bash
hbdk-onnx2hb \
    --input ppo_policy.onnx \
    --output ppo_policy.hb \
    --input-name state \
    --output-name action \
    --model-format onnx \
    --march bernoulli_v2 \
    --quantize-mode fp16 \
    --calibration-data ./calib/calib_data.pkl
```
关键点：`--march bernoulli_v2` 指定 RDK-X5 架构。

</details>

### 练习 3：ROS2 控制节点编写
**题目**：编写一个 ROS2 节点，订阅 `/sensor/state` 话题（类型 `Float32MultiArray`），每 50ms 调用 Policy 推理一次，并将动作发布到 `/robot/cmd_vel`。写出核心代码结构。

<details>
<summary>点击查看答案</summary>

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist

class RLNode(Node):
    def __init__(self):
        super().__init__('rl_node')
        self.sub = self.create_subscription(
            Float32MultiArray, '/sensor/state', self.callback, 10)
        self.pub = self.create_publisher(Twist, '/robot/cmd_vel', 10)
        self.timer = self.create_timer(0.05, self.control)  # 50ms
        self.latest_state = None
        # 加载模型...

    def callback(self, msg):
        import numpy as np
        self.latest_state = np.array(msg.data, dtype=np.float32).reshape(1, -1)

    def control(self):
        if self.latest_state is None:
            return
        action = self.inference(self.latest_state)
        # 发布动作...
```
核心：定时器控制频率、状态缓冲、推理调用。

</details>

### 练习 4：量化模式选择
**题目**：某机器人对推理延迟要求极高（< 5ms），但对动作精度有一定容忍度，应该选择哪种量化模式？为什么？

<details>
<summary>点击查看答案</summary>

**选择 INT8 量化**。

理由：
- INT8 量化模型体积减少 4x，内存带宽降低 4x
- BPU 对 INT8 有专用加速单元，推理速度比 FP16 再快 1.5-2x
- 配合 BPU 加速，单次推理可达到 < 5ms
- 代价是可能有轻微精度损失，但机器人控制场景通常可以接受

</details>

### 练习 5：端侧部署流程
**题目**：简述从 PyTorch 训练到 RDK-X5 边缘部署的完整流程（按顺序列出关键步骤）。

<details>
<summary>点击查看答案</summary>

1. **训练**：使用 Stable-Baselines3 在仿真环境训练 PPO 模型，保存 `.pt` 文件
2. **归一化**：保存 `VecNormalize` 环境参数（部署时状态预处理需要）
3. **ONNX 导出**：将 PyTorch 模型转换为 ONNX 格式（跨平台中间表示）
4. **校准数据**：采集 100-200 个代表性状态样本
5. **HB 转换**：使用 hbdk-onnx2hb 将 ONNX 转换为 HB 模型（量化）
6. **文件传输**：通过 rsync 将 HB 模型和归一化参数传到 RDK-X5
7. **ROS2 开发**：编写 RL 控制节点，订阅传感器话题、调用推理、发布控制指令
8. **编译运行**：colcon build 后 ros2 launch 启动节点
9. **验证测试**：测试推理延迟、控制频率、任务成功率

</details>

---

## 10. 答案

> 以上练习题答案均已在各题目下方以 `<details>` 折叠块形式给出。

### 补充说明

1. **模型导出时注意 input_names/output_names** 必须与 hbdk-onnx2hb 的 `--input-name`/`--output-name` 参数一致。
2. **归一化参数必须保留**，否则部署时状态分布不一致会导致 Policy 性能急剧下降。
3. **BPU 推理优先**，只有在 BPU 不可用时才回退到 CPU，避免推理延迟影响控制实时性。
4. **安全监控不可少**：在 `_postprocess_action` 中必须做动作范围裁剪，防止 Policy 输出破坏性动作。
5. **Sim2Real  gap**：仿真训练的 Policy 直接部署到真实机器人可能会有性能下降，需要 domain randomization 或在线微调。

---

*更多 RL 机器人部署内容，请参考 [d-robotics.github.io/rdk_doc](https://d-robotics.github.io/rdk_doc)*
