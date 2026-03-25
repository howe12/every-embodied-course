# 19-5 RoboTurk 数据集

> **前置课程**：15-模仿学习基础、19-4 RH20T 数据集
> **后续课程**：19-6 MIMIC数据集

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在上一节课程中，我们详细介绍了 RH20T 遥操作数据集的采集系统、数据格式和实战方法。本节我们将学习另一个极具影响力的机器人数据集——**RoboTurk**。RoboTurk 是由斯坦福大学机器人研究中心发布的众包机器人遥操作数据集，其创新性地采用**智能手机作为遥操作终端**，利用众包平台大规模收集机器人演示数据。这一设计极大地降低了数据采集的成本和门槛，为机器人模仿学习研究提供了前所未有的数据规模。通过本节学习，你将全面理解 RoboTurk 的众包采集范式、数据结构设计，并掌握基于该数据集的代码实战技能。

---

## 1. RoboTurk 概述

### 1.1 什么是 RoboTurk

RoboTurk 是斯坦福大学机器人研究中心（Stanford AI Lab）于 2018 年发布的大规模机器人遥操作数据集，由 Ajay Mandlekar、Yuke Zhu 等研究者开发。该数据集的核心创新在于**采用智能手机作为遥操作终端**，通过众包平台（Amazon Mechanical Turk）招募大量非专业用户远程控制机器人执行操作任务。

RoboTurk 的设计哲学是：**让每个人都能成为机器人数据的贡献者**。传统的遥操作数据集需要专业操作员在实验室环境下使用昂贵的设备（如 Phantom Omni）采集数据，成本高、规模有限。而 RoboTurk 通过将智能手机与机器人控制系统连接，使普通用户只需一部手机就能远程操控机器人，大幅降低了参与门槛。

RoboTurk 的主要特点：
- **零硬件依赖**：用户使用智能手机即可参与数据采集，无需专业设备
- **众包范式**：通过 Amazon Mechanical Turk 平台众包，突破实验室限制
- **大规模数据**：单日可采集数千条演示，规模远超传统方法
- **真实人类多样性**：操作来自全球各地的真实用户，动作风格多样

### 1.2 数据规模

RoboTurk 在发布时创下了遥操作数据集的规模纪录：

| 指标 | 数值 |
|------|------|
| 演示片段（Episodes） | 14,000+ 条 |
| 总时长 | 50,000+ 秒（约 14 小时） |
| 任务类型 | 8 种操作任务 |
| 采集平台 | Amazon Mechanical Turk |
| 遥操作设备 | 智能手机（iOS/Android） |
| 相机视角 | 1 个主视角 RGB 相机 |
| 机器人类型 | WidowX 机械臂 |
| 参与者数量 | 1,000+ 人 |

这一数据规模在当时是同类遥操作数据集的 **10 倍以上**，为模仿学习研究提供了前所未有的数据支持。

### 1.3 任务覆盖

RoboTurk 涵盖 8 种核心操作任务，涵盖了机器人操作的基本技能：

| 任务名称 | 描述 | 难度 |
|---------|------|------|
| 抓取放置（Pick & Place） | 抓取物体并放置到目标区域 | ⭐ |
| 推物体（Push） | 推动物体沿指定方向移动 | ⭐ |
| 倾倒（Pour） | 倾斜容器使物体倒入另一容器 | ⭐⭐ |
| 搅拌（Stir） | 使用工具搅拌容器内物质 | ⭐⭐ |
| 开门（Door Open） | 操作门把手打开门 | ⭐⭐ |
| 抽屉操作（Drawer） | 拉开或推上抽屉 | ⭐⭐ |
| 物体排序（Sort） | 将物体按类别放入不同区域 | ⭐⭐⭐ |
| 叠放（Stack） | 将物体堆叠在一起 | ⭐⭐⭐ |

这些任务涵盖了从简单到复杂的操作技能，能够有效评估机器人的操作泛化能力。

---

## 2. 数据采集系统

### 2.1 众包平台

RoboTurk 的数据采集基于 **Amazon Mechanical Turk（MTurk）** 众包平台。MTurk 是亚马逊提供的在线众包市场，允许研究者发布"Human Intelligence Tasks"（HITs），由全球各地的 worker 完成并获取报酬。

RoboTurk 的众包流程：

```
┌─────────────────────────────────────────────────────────┐
│                     研究团队                              │
│  1. 设计任务（定义操作任务、目标物体、评价标准）            │
│  2. 开发移动端遥操作 APP                                  │
│  3. 在 MTurk 发布 HITs（每个 HIT = 一个完整任务演示）       │
└─────────────────┬───────────────────────────────────────┘
                  │ 发布任务
                  ▼
┌─────────────────────────────────────────────────────────┐
│                  Amazon MTurk                           │
│  4. Worker 领取任务，下载遥操作 APP                      │
│  5. Worker 使用手机实时控制机器人                         │
│  6. 录制完成后上传数据，获得报酬                          │
└─────────────────┬───────────────────────────────────────┘
                  │ 数据汇总
                  ▼
┌─────────────────────────────────────────────────────────┐
│                  数据后处理                              │
│  7. 质量筛选（过滤低质量演示）                            │
│  8. 格式标准化（统一为 HDF5 格式）                        │
│  9. 标注完善（补充任务标签、成功与否等）                    │
└─────────────────────────────────────────────────────────┘
```

**报酬设计**：每个成功的任务演示报酬约为 **$2-5 美元**，根据任务难度和完成质量浮动。研究团队设置了基础报酬 + 绩效奖金的机制，激励 worker 提交高质量的演示数据。

### 2.2 智能手机遥操作

RoboTurk 的核心技术创新是**将智能手机作为遥操作终端**。研究团队开发了专用的移动端 APP，实现了以下功能：

**运动控制**：
- 手机陀螺仪控制末端执行器姿态（倾斜手机 → 机械臂移动）
- 手机加速度计捕捉细微运动
- 触屏按钮控制夹爪开闭

**视频流传输**：
- 机器人端相机通过 ROS 节点发布视频流
- 手机端 APP 接收并显示实时视频
- 视频延迟控制在 100ms 以内，保证操作手感

**指令编码**：
- 手机的陀螺仪数据（roll, pitch, yaw）编码为控制指令
- 每帧指令包含末端位置增量和夹爪状态
- 指令通过 WiFi 发送到机器人控制端

```
手机端 APP                    机器人控制端
┌──────────────┐            ┌──────────────────┐
│  陀螺仪/加速度 │ ──WiFi──▶ │  指令解析器       │
│              │            │  ↓               │
│  触屏控制     │            │  机器人控制器     │
│              │            │  ↓               │
│  视频显示     │ ◀──WiFi── │  相机视频流       │
└──────────────┘            └──────────────────┘
```

这种设计的优势在于：
- **零硬件成本**：无需购买昂贵的力反馈设备
- **人人可参与**：全球数十亿智能手机用户都可成为数据贡献者
- **真实多样性**：不同用户的操作风格带来丰富的动作多样性

### 2.3 质量控制

众包数据的质量参差不齐，RoboTurk 设计了多层次的质量控制机制：

**1. 实时反馈系统**
- APP 实时显示任务完成状态（如物体是否到达目标区域）
- Worker 可看到自己的操作效果，及时调整策略
- 成功率实时显示，激励高质量操作

**2. 自动质量筛选**
- 设定最低成功率阈值（如 30%），低于阈值的数据自动丢弃
- 检测异常轨迹（如关节角度突变、轨迹过于简单）
- 过滤采集时间过短或过长的异常数据

**3. 人工审核机制**
- 随机抽样进行人工审核
- 审核维度：任务完成度、动作自然性、数据完整性
- 质量评分低于阈值的 worker 被禁止继续参与

**4. Worker 信誉系统**
- 建立 worker 信誉档案，记录历史数据质量
- 高信誉 worker 获得更高报酬和优先任务权
- 连续低质量 worker 被永久封禁

通过以上机制，RoboTurk 最终保留了约 **70-80%** 的原始采集数据，在规模和质量之间取得了平衡。

---

## 3. 数据格式

### 3.1 轨迹数据

RoboTurk 的轨迹数据以 **HDF5 格式**存储，包含丰富的状态和动作信息。

**数据结构**：

```python
{
    "observations": {
        # 图像观测（每隔 N 帧采样一次）
        "images": {
            "primary": b"<binary_rgb_data>",  # 主视角 RGB 图像（base64 编码）
        },
        
        # 机器人状态
        "robot_state": {
            "joint_positions": [0.1, -0.3, 0.8, 0.5, -0.2, 0.3],  # 6 个关节角度（弧度）
            "joint_velocities": [0.02, -0.01, 0.03, 0.01, -0.02, 0.01],  # 关节速度
            "ee_pose": [0.3, 0.2, 0.15, 0.0, 0.0, 0.707, 0.707],  # 末端位姿 (x,y,z,qx,qy,qz,qw)
            "gripper_state": 1.0,  # 夹爪状态（0=开，1=闭合，连续值）
        },
    },
    
    # 动作序列
    "actions": {
        "world_vector": [0.01, -0.005, 0.0],  # 末端位置增量（米）
        "rotation_delta": [0.0, 0.0, 0.01],   # 末端姿态增量（弧度）
        "gripper_closedness_action": 1.0,      # 夹爪控制（0~1）
    },
    
    # 元数据
    "metadata": {
        "episode_id": "roboTurk_00001",
        "task_name": "pick_place",
        "task_type": "manipulation",
        "worker_id": "A2XXXXX",               # MTurk Worker ID（匿名化）
        "success": True,                      # 是否成功完成任务
        "success_metric": 0.95,               # 成功指标（0~1，物体到目标位置的比例）
        "duration": 8.3,                      # 持续时间（秒）
        "num_steps": 249,                     # 总步数
        "timestamp": "2018-06-15T14:30:00",  # 采集时间戳
        "device": "iPhone_X",                 # 设备类型
        "language_instruction": "Pick the red block and place it in the blue box",  # 语言指令
    }
}
```

### 3.2 视频数据

视频数据以**图像序列**形式存储，而非连续视频文件。这种设计有以下优势：

- **按需加载**：训练时只需加载需要的帧，无需解码整个视频
- **可变帧率**：可以根据任务调整采样频率
- **便于预处理**：每帧图像独立处理，支持数据增强

**图像格式**：
- 分辨率：640 × 480 像素
- 编码格式：JPEG（压缩存储，节省空间）
- 帧率：约 10-15 Hz（受限于网络传输带宽）

**图像张量形状**（加载后）：
$$
\text{image\_shape} = (H, W, C) = (480, 640, 3)
$$

### 3.3 HDF5 存储结构

RoboTurk 使用 HDF5（Hierarchical Data Format version 5）作为数据容器，这是科学数据存储的标准格式：

```
roboTurk_dataset.hdf5
├── /episodes/
│   ├── episode_00001/
│   │   ├── observations/
│   │   │   ├── images/
│   │   │   │   └── primary        # (num_steps, 480, 640, 3) uint8
│   │   │   └── robot_state/
│   │   │       ├── joint_positions    # (num_steps, 6) float32
│   │   │       ├── joint_velocities   # (num_steps, 6) float32
│   │   │       ├── ee_pose            # (num_steps, 7) float32
│   │   │       └── gripper_state      # (num_steps, 1) float32
│   │   ├── actions/
│   │   │   ├── world_vector           # (num_steps, 3) float32
│   │   │   ├── rotation_delta         # (num_steps, 3) float32
│   │   │   └── gripper_closedness_action  # (num_steps, 1) float32
│   │   └── metadata/
│   │       ├── task_name              # string
│   │       ├── success                # bool
│   │       └── ...
│   ├── episode_00002/
│   └── ...
└── /dataset_info/
    ├── task_list              # 所有任务名称列表
    ├── statistics             # 数据集统计信息
    └── normalization_params   # 归一化参数（均值、标准差）
```

使用 HDF5 的优势：
- **支持大文件**：可存储数十 GB 的数据集
- **随机访问**：无需加载整个文件即可访问部分数据
- **跨平台**：支持 Python、C++、MATLAB 等多语言
- **压缩支持**：内置压缩算法，节省存储空间

---

## 4. 任务类型详解

### 4.1 基础操作任务

基础操作任务是 RoboTurk 数据集的主体，占总数据的约 60%：

**抓取放置（Pick & Place）**
- 任务描述：将指定物体从起始位置抓取并放置到目标区域
- 评价指标：物体最终位置与目标区域的距离
- 技术难点：精确抓取、放置位置的准确性

**推物体（Push）**
- 任务描述：使用夹爪或末端推动物体沿指定路径移动
- 评价指标：物体移动距离和方向准确性
- 技术难点：力的控制、摩擦力建模

**倾倒（Pour）**
- 任务描述：抓取容器，将其中物体（或模拟液体）倒入另一容器
- 评价指标：目标容器接收到的物质量
- 技术难点：重力和倾倒角度控制

### 4.2 中级操作任务

中级任务占总数据的约 30%：

**搅拌（Stir）**
- 任务描述：使用工具在容器内做圆周搅拌动作
- 评价指标：搅拌均匀度（可通过颜色变化等指标衡量）
- 技术难点：连续轨迹控制、工具与容器的接触

**开门（Door Open）**
- 任务描述：操作门把手并推开或关闭门
- 评价指标：门打开的角度
- 技术难点：理解门把手的机械结构、力的感知

**抽屉操作（Drawer）**
- 任务描述：拉开抽屉取物或推上抽屉
- 评价指标：抽屉开合程度
- 技术难点：拉力的控制、抽屉滑轨的物理特性

### 4.3 高级操作任务

高级任务占总数据的约 10%：

**物体排序（Sort）**
- 任务描述：将多个不同类别的物体分别放入对应区域
- 评价指标：分类准确率
- 技术难点：多物体识别、序列规划

**叠放（Stack）**
- 任务描述：将多个物体按顺序堆叠成指定形状
- 评价指标：堆叠稳定性和位置准确性
- 技术难点：精确放置、平衡控制

---

## 5. 使用方法

### 5.1 数据获取

RoboTurk 数据集可通过以下方式获取：

**官方网站（Stanford AI Lab）**

```bash
# 访问 https://h2r.github.io/rob Turk/
# 注册账号并申请下载权限

# 下载数据集（约 25GB）
wget https://download.rob turk.stanford.edu/rob Turk_dataset.tar.gz
tar -xzf roboTurk_dataset.tar.gz
```

**GitHub 仓库（附带工具）**

```bash
# 克隆官方 GitHub 仓库
git clone https://github.com/StanfordVL/rob Turk.git
cd rob Turk

# 安装依赖
pip install -r requirements.txt

# 下载数据集
python scripts/download_dataset.py --task pick_place --output ./data/
```

**按任务选择性下载**

```python
import requests
import os

def download_task_dataset(task_name, output_dir):
    """
    下载指定任务的数据
    
    参数:
        task_name: 任务名称（如 "pick_place", "push", "pour"）
        output_dir: 输出目录
    """
    base_url = "https://download.rob turk.stanford.edu/"
    file_name = f"rob Turk_{task_name}.tar.gz"
    url = base_url + file_name
    
    output_path = os.path.join(output_dir, file_name)
    
    print(f"下载任务: {task_name}")
    print(f"URL: {url}")
    
    # 使用 curl 下载（大文件支持断点续传）
    os.system(f"curl -L -C - -o {output_path} {url}")
    
    # 解压
    import tarfile
    with tarfile.open(output_path, 'r:gz') as tar:
        tar.extractall(output_dir)
    
    print(f"解压完成: {output_dir}/{task_name}")
```

### 5.2 预处理

RoboTurk 数据需要预处理后才能用于深度学习训练：

```python
import h5py
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Optional

class RoboTurkPreprocessor:
    """
    RoboTurk 数据预处理器
    
    功能：
    - 加载 HDF5 格式数据
    - 数据清洗和过滤
    - 格式转换为 NumPy
    - 归一化处理
    """
    
    def __init__(self, data_root: str):
        """
        初始化预处理器
        
        参数:
            data_root: 数据根目录（包含 .hdf5 文件）
        """
        self.data_root = Path(data_root)
        self.hdf5_files = list(self.data_root.glob("*.hdf5"))
        
        print(f"找到 {len(self.hdf5_files)} 个 HDF5 文件")
    
    def load_episode(self, hdf5_path: str, episode_name: str) -> Dict:
        """
        加载单个 episode
        
        参数:
            hdf5_path: HDF5 文件路径
            episode_name: episode 名称（如 "episode_00001"）
        
        返回:
            包含观测和动作的字典
        """
        with h5py.File(hdf5_path, 'r') as f:
            ep_group = f[f"episodes/{episode_name}"]
            
            # 加载观测数据
            observations = {
                "images": {
                    "primary": ep_group["observations/images/primary"][:]
                },
                "robot_state": {
                    "joint_positions": ep_group["observations/robot_state/joint_positions"][:],
                    "joint_velocities": ep_group["observations/robot_state/joint_velocities"][:],
                    "ee_pose": ep_group["observations/robot_state/ee_pose"][:],
                    "gripper_state": ep_group["observations/robot_state/gripper_state"][:]
                }
            }
            
            # 加载动作数据
            actions = {
                "world_vector": ep_group["actions/world_vector"][:],
                "rotation_delta": ep_group["actions/rotation_delta"][:],
                "gripper_closedness_action": ep_group["actions/gripper_closedness_action"][:]
            }
            
            # 加载元数据
            metadata = {}
            for key in ep_group["metadata"].keys():
                value = ep_group[f"metadata/{key}"][()]
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                metadata[key] = value
        
        return {
            "observations": observations,
            "actions": actions,
            "metadata": metadata
        }
    
    def filter_by_success(self, min_success_rate: float = 0.5) -> List[str]:
        """
        根据成功率过滤 episode
        
        参数:
            min_success_rate: 最低成功率阈值
        
        返回:
            过滤后的 episode 名称列表
        """
        valid_episodes = []
        
        for hdf5_path in self.hdf5_files:
            with h5py.File(hdf5_path, 'r') as f:
                if "episodes" not in f:
                    continue
                
                for ep_name in f["episodes"].keys():
                    try:
                        success_metric = float(
                            f[f"episodes/{ep_name}/metadata/success_metric"][()]
                        )
                        if success_metric >= min_success_rate:
                            valid_episodes.append((str(hdf5_path), ep_name))
                    except:
                        continue
        
        print(f"成功率 ≥ {min_success_rate} 的 episode: {len(valid_episodes)}")
        return valid_episodes
    
    def convert_to_numpy(
        self,
        episode_list: List[tuple],
        output_dir: str,
        downsample_ratio: int = 1
    ):
        """
        将 HDF5 格式转换为 NumPy 格式
        
        参数:
            episode_list: episode 列表 [(hdf5_path, ep_name), ...]
            output_dir: 输出目录
            downsample_ratio: 下采样比例（如 2 表示每 2 帧取 1 帧）
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for hdf5_path, ep_name in episode_list:
            data = self.load_episode(hdf5_path, ep_name)
            
            # 下采样
            observations = data["observations"]
            actions = data["actions"]
            metadata = data["metadata"]
            
            obs_images = observations["images"]["primary"][::downsample_ratio]
            joint_pos = observations["robot_state"]["joint_positions"][::downsample_ratio]
            ee_pose = observations["robot_state"]["ee_pose"][::downsample_ratio]
            gripper = observations["robot_state"]["gripper_state"][::downsample_ratio]
            
            world_vec = actions["world_vector"][::downsample_ratio]
            rot_delta = actions["rotation_delta"][::downsample_ratio]
            gripper_action = actions["gripper_closedness_action"][::downsample_ratio].reshape(-1, 1)
            
            # 拼接动作向量（7 维：3 位置增量 + 3 姿态增量 + 1 夹爪）
            action_vector = np.concatenate([
                world_vec, rot_delta, gripper_action
            ], axis=1)
            
            # 保存为 npz
            output_file = output_dir / f"{metadata['episode_id']}.npz"
            np.savez_compressed(
                output_file,
                images=obs_images,            # (T, H, W, 3) uint8
                joint_positions=joint_pos,    # (T, 6) float32
                ee_pose=ee_pose,              # (T, 7) float32
                gripper_state=gripper,        # (T, 1) float32
                actions=action_vector,        # (T, 7) float32
                task_name=metadata.get("task_name", "unknown"),
                success=metadata.get("success", False),
                success_metric=metadata.get("success_metric", 0.0)
            )
            
            print(f"转换完成: {output_file.name}")
    
    def compute_normalization_stats(self, episode_list: List[tuple]) -> Dict:
        """
        计算数据集的归一化参数（均值和标准差）
        
        用于训练时的数据标准化
        """
        all_states = []
        all_actions = []
        
        for hdf5_path, ep_name in episode_list:
            data = self.load_episode(hdf5_path, ep_name)
            
            # 拼接状态向量
            joint_pos = data["observations"]["robot_state"]["joint_positions"]
            ee_pose = data["observations"]["robot_state"]["ee_pose"]
            gripper = data["observations"]["robot_state"]["gripper_state"]
            
            state = np.concatenate([joint_pos, ee_pose, gripper], axis=1)
            all_states.append(state)
            
            # 动作向量
            world_vec = data["actions"]["world_vector"]
            rot_delta = data["actions"]["rotation_delta"]
            gripper_action = data["actions"]["gripper_closedness_action"].reshape(-1, 1)
            action = np.concatenate([world_vec, rot_delta, gripper_action], axis=1)
            all_actions.append(action.astype(np.float32))
        
        all_states = np.concatenate(all_states, axis=0).astype(np.float32)
        all_actions = np.concatenate(all_actions, axis=0).astype(np.float32)
        
        stats = {
            "state_mean": all_states.mean(axis=0),
            "state_std": all_states.std(axis=0) + 1e-7,
            "action_mean": all_actions.mean(axis=0),
            "action_std": all_actions.std(axis=0) + 1e-7,
        }
        
        print(f"状态维度: {all_states.shape[1]}")
        print(f"动作维度: {all_actions.shape[1]}")
        print(f"状态均值范围: [{stats['state_mean'].min():.3f}, {stats['state_mean'].max():.3f}]")
        print(f"动作均值范围: [{stats['action_mean'].min():.3f}, {stats['action_mean'].max():.3f}]")
        
        return stats
```

### 5.3 训练集成

RoboTurk 数据集可以与多种模仿学习框架集成：

**与 RoboTurk 原生训练代码集成**：

```python
# RoboTurk 官方提供的训练框架示例
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# 使用 RoboTurk 数据训练行为克隆策略
def train_bc_policy_rob Turk(data_root, tasks, epochs=100, batch_size=32):
    """
    基于 RoboTurk 数据训练行为克隆策略
    
    参数:
        data_root: 数据目录
        tasks: 任务列表
        epochs: 训练轮数
        batch_size: 批次大小
    """
    from rob Turk_dataset import RoboTurkDataset
    from policy import BehavioralCloningPolicy
    
    # 创建数据集
    dataset = RoboTurkDataset(
        data_root=data_root,
        tasks=tasks,
        image_size=(224, 224),
        normalize_actions=True
    )
    
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True
    )
    
    # 创建策略网络（简单的 CNN + MLP）
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    policy = BehavioralCloningPolicy(
        image_dim=(224, 224, 3),
        state_dim=16,
        action_dim=7,
        hidden_dim=256
    ).to(device)
    
    optimizer = torch.optim.Adam(policy.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    
    # 训练循环
    for epoch in range(epochs):
        total_loss = 0.0
        num_batches = 0
        
        for batch in dataloader:
            images = batch["images"].to(device)      # (B, T, H, W, 3)
            states = batch["states"].to(device)    # (B, T, state_dim)
            actions = batch["actions"].to(device)  # (B, T, action_dim)
            
            # 取最后一帧的观测和动作作为监督目标
            image_input = images[:, -1]              # (B, H, W, 3)
            state_input = states[:, -1]              # (B, state_dim)
            action_target = actions[:, -1]           # (B, action_dim)
            
            # 前向传播
            pred_action = policy(image_input, state_input)
            
            # 计算损失
            loss = loss_fn(pred_action, action_target)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
    
    # 保存模型
    torch.save(policy.state_dict(), "rob Turk_bc_policy.pth")
    print("模型已保存: roboTurk_bc_policy.pth")
    
    return policy
```

---

## 6. 代码实战

### 6.1 数据加载器实现

下面实现一个完整的 RoboTurk 数据加载器，支持多任务和图像处理：

```python
import h5py
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2

class RoboTurkDataset(Dataset):
    """
    RoboTurk 数据集加载器
    
    支持：
    - 多任务加载
    - 图像预处理
    - 动作归一化
    - 数据下采样
    """
    
    def __init__(
        self,
        data_root: str,
        tasks: Optional[List[str]] = None,
        image_size: Tuple[int, int] = (224, 224),
        seq_length: int = 16,
        normalize_actions: bool = True,
        stats_path: Optional[str] = None,
        load_images: bool = True,
        downsample: int = 1
    ):
        """
        初始化数据集
        
        参数:
            data_root: 数据根目录（包含 .hdf5 文件）
            tasks: 任务列表，None 表示全部任务
            image_size: 图像 resize 大小
            seq_length: 序列长度
            normalize_actions: 是否归一化动作
            stats_path: 归一化参数文件路径
            load_images: 是否加载图像（False 可节省内存）
            downsample: 下采样步长
        """
        self.data_root = Path(data_root)
        self.tasks = tasks or []
        self.image_size = image_size
        self.seq_length = seq_length
        self.normalize_actions = normalize_actions
        self.load_images = load_images
        self.downsample = downsample
        
        # 收集所有 episode
        self.episodes: List[Dict] = []
        self._scan_episodes()
        
        # 加载或计算归一化参数
        if stats_path and Path(stats_path).exists():
            self._load_stats(stats_path)
        else:
            self._compute_stats()
    
    def _scan_episodes(self):
        """扫描所有有效的 episode"""
        hdf5_files = list(self.data_root.glob("*.hdf5"))
        
        for hdf5_path in hdf5_files:
            try:
                with h5py.File(hdf5_path, 'r') as f:
                    if "episodes" not in f:
                        continue
                    
                    for ep_name in f["episodes"].keys():
                        try:
                            meta = f[f"episodes/{ep_name}/metadata"]
                            
                            task_name = self._decode_bytes(
                                meta["task_name"][()]
                            )
                            
                            # 任务过滤
                            if self.tasks and task_name not in self.tasks:
                                continue
                            
                            success = bool(meta["success"][()])
                            success_metric = float(meta["success_metric"][()])
                            
                            self.episodes.append({
                                "hdf5_path": str(hdf5_path),
                                "ep_name": ep_name,
                                "task_name": task_name,
                                "success": success,
                                "success_metric": success_metric
                            })
                        except Exception:
                            continue
            except Exception as e:
                print(f"读取文件失败 {hdf5_path}: {e}")
                continue
        
        print(f"加载了 {len(self.episodes)} 个有效 episode")
    
    def _decode_bytes(self, value) -> str:
        """解码 bytes 类型的字符串"""
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return str(value)
    
    def _compute_stats(self):
        """计算归一化参数（从全部数据中采样）"""
        print("计算归一化参数...")
        
        # 采样一部分数据以节省时间
        sample_size = min(1000, len(self.episodes))
        sample_eps = np.random.choice(len(self.episodes), sample_size, replace=False)
        
        all_actions = []
        
        for idx in sample_eps:
            ep = self.episodes[idx]
            try:
                with h5py.File(ep["hdf5_path"], 'r') as f:
                    actions = f[f"episodes/{ep['ep_name']}/actions"]
                    
                    world_vec = actions["world_vector"][::self.downsample]
                    rot_delta = actions["rotation_delta"][::self.downsample]
                    gripper = actions["gripper_closedness_action"][::self.downsample][:, None]
                    
                    action = np.concatenate([world_vec, rot_delta, gripper], axis=1)
                    all_actions.append(action.astype(np.float32))
            except Exception:
                continue
        
        if all_actions:
            all_actions = np.concatenate(all_actions, axis=0)
            self.action_mean = torch.FloatTensor(all_actions.mean(axis=0))
            self.action_std = torch.FloatTensor(all_actions.std(axis=0) + 1e-7)
        else:
            self.action_mean = torch.zeros(7)
            self.action_std = torch.ones(7)
    
    def _load_stats(self, stats_path: str):
        """从文件加载归一化参数"""
        stats = np.load(stats_path)
        self.action_mean = torch.FloatTensor(stats["action_mean"])
        self.action_std = torch.FloatTensor(stats["action_std"])
    
    def __len__(self) -> int:
        return len(self.episodes)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        获取一个 episode 的数据
        
        返回:
            dict: 包含以下键的字典
                - images: 图像序列 (seq_len, H, W, 3)
                - states: 状态序列 (seq_len, state_dim)
                - actions: 动作序列 (seq_len, 7)
                - task_name: 任务名称
                - success: 是否成功
                - success_metric: 成功指标
        """
        ep = self.episodes[idx]
        
        with h5py.File(ep["hdf5_path"], 'r') as f:
            obs_group = f[f"episodes/{ep['ep_name']}/observations"]
            act_group = f[f"episodes/{ep['ep_name']}/actions"]
            
            # 加载图像
            if self.load_images:
                images = obs_group["images/primary"][::self.downsample]
                # 预处理图像：resize + 归一化
                processed_images = []
                for img_bytes in images:
                    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    img = cv2.resize(img, self.image_size)
                    # BGR -> RGB，归一化到 [0, 1]
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) / 255.0
                    processed_images.append(img)
                images = np.array(processed_images, dtype=np.float32)
            else:
                images = np.zeros((1, *self.image_size, 3), dtype=np.float32)
            
            # 加载关节状态
            joint_pos = obs_group["robot_state/joint_positions"][::self.downsample].astype(np.float32)
            ee_pose = obs_group["robot_state/ee_pose"][::self.downsample].astype(np.float32)
            gripper = obs_group["robot_state/gripper_state"][::self.downsample].astype(np.float32)
            
            # 拼接状态向量 (6 关节 + 7 末端 + 1 夹爪 = 14 维)
            states = np.concatenate([joint_pos, ee_pose, gripper], axis=1)
            
            # 加载动作
            world_vec = act_group["world_vector"][::self.downsample].astype(np.float32)
            rot_delta = act_group["rotation_delta"][::self.downsample].astype(np.float32)
            gripper_act = act_group["gripper_closedness_action"][::self.downsample][:, None].astype(np.float32)
            actions = np.concatenate([world_vec, rot_delta, gripper_act], axis=1)
        
        # 转换为 tensor
        images = torch.FloatTensor(images)
        states = torch.FloatTensor(states)
        actions = torch.FloatTensor(actions)
        
        # 归一化动作
        if self.normalize_actions:
            actions = (actions - self.action_mean) / self.action_std
        
        # 处理序列长度
        seq_len = min(len(actions), self.seq_length)
        images = images[:seq_len]
        states = states[:seq_len]
        actions = actions[:seq_len]
        
        return {
            "images": images,
            "states": states,
            "actions": actions,
            "task_name": ep["task_name"],
            "success": torch.tensor(ep["success"], dtype=torch.float),
            "success_metric": torch.tensor(ep["success_metric"], dtype=torch.float)
        }


def create_rob Turk_dataloader(
    data_root: str,
    tasks: Optional[List[str]] = None,
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 4
) -> DataLoader:
    """
    创建 RoboTurk 数据加载器
    
    参数:
        data_root: 数据根目录
        batch_size: 批次大小
        tasks: 任务列表
        shuffle: 是否打乱
        num_workers: 数据加载线程数
    
    返回:
        DataLoader 实例
    """
    dataset = RoboTurkDataset(
        data_root=data_root,
        tasks=tasks,
        normalize_actions=True,
        seq_length=16,
        image_size=(224, 224)
    )
    
    def collate_fn(batch):
        """
        自定义批次整理函数
        将不同长度的序列 padding 到相同长度
        """
        max_len = max(item["actions"].shape[0] for item in batch)
        
        padded_images = []
        padded_states = []
        padded_actions = []
        masks = []
        
        for item in batch:
            seq_len = item["actions"].shape[0]
            pad_len = max_len - seq_len
            
            if pad_len > 0:
                # Padding：用零填充
                image_pad = torch.zeros(pad_len, *item["images"].shape[1:])
                state_pad = torch.zeros(pad_len, item["states"].shape[1])
                action_pad = torch.zeros(pad_len, item["actions"].shape[1])
                
                images = torch.cat([item["images"], image_pad], dim=0)
                states = torch.cat([item["states"], state_pad], dim=0)
                actions = torch.cat([item["actions"], action_pad], dim=0)
                mask = torch.cat([torch.ones(seq_len), torch.zeros(pad_len)], dim=0)
            else:
                images = item["images"]
                states = item["states"]
                actions = item["actions"]
                mask = torch.ones(seq_len)
            
            padded_images.append(images)
            padded_states.append(states)
            padded_actions.append(actions)
            masks.append(mask)
        
        return {
            "images": torch.stack(padded_images),       # (batch, max_len, H, W, 3)
            "states": torch.stack(padded_states),       # (batch, max_len, state_dim)
            "actions": torch.stack(padded_actions),    # (batch, max_len, 7)
            "mask": torch.stack(masks),                # (batch, max_len)
            "task_names": [item["task_name"] for item in batch],
            "success": torch.stack([item["success"] for item in batch]),
            "success_metric": torch.stack([item["success_metric"] for item in batch])
        }
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=True
    )
```

### 6.2 轨迹可视化

下面实现 RoboTurk 数据的可视化功能：

```python
import h5py
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from typing import List, Dict, Optional
import cv2

def visualize_rob Turk_episode(
    hdf5_path: str,
    ep_name: str,
    save_dir: Optional[str] = None
):
    """
    可视化单个 episode 的数据
    
    参数:
        hdf5_path: HDF5 文件路径
        ep_name: episode 名称
        save_dir: 保存目录，None 则不保存
    """
    with h5py.File(hdf5_path, 'r') as f:
        ep_group = f[f"episodes/{ep_name}"]
        
        # 加载数据
        obs = ep_group["observations"]
        act = ep_group["actions"]
        
        # 末端执行器位置
        ee_poses = obs["robot_state/ee_pose"][:]
        positions = ee_poses[:, :3]  # x, y, z
        
        # 关节角度
        joint_pos = obs["robot_state/joint_positions"][:]
        
        # 夹爪状态
        gripper = obs["robot_state/gripper_state"][:]
        
        # 动作
        world_vec = act["world_vector"][:]
        gripper_act = act["gripper_closedness_action"][:]
        
        # 元数据
        meta = ep_group["metadata"]
        task_name = meta["task_name"][()].decode() if isinstance(meta["task_name"][()], bytes) else meta["task_name"][()]
        success = bool(meta["success"][()])
        success_metric = float(meta["success_metric"][()])
    
    # 创建可视化
    fig = plt.figure(figsize=(15, 10))
    
    # 1. 3D 末端轨迹
    ax1 = fig.add_subplot(221, projection='3d')
    colors = ['green' if g > 0.5 else 'red' for g in gripper]
    ax1.scatter(positions[:, 0], positions[:, 1], positions[:, 2], 
                c=colors, s=5, alpha=0.6)
    ax1.plot(positions[:, 0], positions[:, 1], positions[:, 2], 
             'b-', alpha=0.3, linewidth=1)
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_zlabel('Z (m)')
    ax1.set_title(f'末端执行器 3D 轨迹\n任务: {task_name}, 成功: {success}, 指标: {success_metric:.2f}')
    
    # 2. 位置随时间变化
    ax2 = fig.add_subplot(222)
    time = np.arange(len(positions)) / 15.0  # 约 15Hz
    ax2.plot(time, positions[:, 0], label='X', alpha=0.8)
    ax2.plot(time, positions[:, 1], label='Y', alpha=0.8)
    ax2.plot(time, positions[:, 2], label='Z', alpha=0.8)
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('位置 (m)')
    ax2.set_title('末端执行器位置随时间变化')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 关节角度
    ax3 = fig.add_subplot(223)
    for j in range(min(6, joint_pos.shape[1])):
        ax3.plot(time, joint_pos[:, j], label=f'J{j+1}', alpha=0.7)
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('关节角度 (rad)')
    ax3.set_title('关节角度随时间变化')
    ax3.legend(fontsize=6, ncol=3)
    ax3.grid(True, alpha=0.3)
    
    # 4. 动作分量
    ax4 = fig.add_subplot(224)
    ax4.plot(time, world_vec[:, 0], label='dx', alpha=0.8)
    ax4.plot(time, world_vec[:, 1], label='dy', alpha=0.8)
    ax4.plot(time, world_vec[:, 2], label='dz', alpha=0.8)
    ax4_twin = ax4.twinx()
    ax4_twin.plot(time, gripper_act, label='gripper', color='purple', alpha=0.8)
    ax4.set_xlabel('时间 (s)')
    ax4.set_ylabel('位置增量 (m)')
    ax4_twin.set_ylabel('夹爪控制')
    ax4.set_title('动作分量随时间变化')
    ax4.legend(loc='upper left')
    ax4_twin.legend(loc='upper right')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_dir:
        save_path = Path(save_dir) / f"{ep_name}.png"
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
    
    plt.show()
    plt.close()


def visualize_dataset_statistics(data_root: str):
    """
    绘制数据集统计信息
    
    包括：任务分布、成功率和轨迹长度分布
    """
    data_root = Path(data_root)
    hdf5_files = list(data_root.glob("*.hdf5"))
    
    # 收集统计信息
    task_counts = {}
    success_counts = {}
    trajectory_lengths = []
    success_metrics = []
    
    for hdf5_path in hdf5_files:
        try:
            with h5py.File(hdf5_path, 'r') as f:
                if "episodes" not in f:
                    continue
                
                for ep_name in f["episodes"].keys():
                    try:
                        meta = f[f"episodes/{ep_name}/metadata"]
                        task = meta["task_name"][()].decode() if isinstance(meta["task_name"][()], bytes) else meta["task_name"][()]
                        success = bool(meta["success"][()])
                        sm = float(meta["success_metric"][()])
                        
                        task_counts[task] = task_counts.get(task, 0) + 1
                        success_counts[task] = success_counts.get(task, 0) + (1 if success else 0)
                        trajectory_lengths.append(int(meta["num_steps"][()]))
                        success_metrics.append(sm)
                    except Exception:
                        continue
        except Exception:
            continue
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. 任务分布
    tasks = list(task_counts.keys())
    counts = list(task_counts.values())
    axes[0, 0].barh(tasks, counts)
    axes[0, 0].set_xlabel('Episode 数量')
    axes[0, 0].set_title('各任务 Episode 数量')
    
    # 2. 任务成功率
    success_rates = [success_counts[t] / task_counts[t] for t in tasks]
    axes[0, 1].barh(tasks, success_rates)
    axes[0, 1].set_xlabel('成功率')
    axes[0, 1].set_title('各任务成功率')
    axes[0, 1].set_xlim(0, 1)
    
    # 3. 轨迹长度分布
    axes[1, 0].hist(trajectory_lengths, bins=30, edgecolor='black', alpha=0.7)
    axes[1, 0].set_xlabel('轨迹长度（帧）')
    axes[1, 0].set_ylabel('Episode 数量')
    axes[1, 0].set_title(f'轨迹长度分布\n均值: {np.mean(trajectory_lengths):.0f}')
    axes[1, 0].axvline(np.mean(trajectory_lengths), color='r', linestyle='--')
    
    # 4. 成功指标分布
    axes[1, 1].hist(success_metrics, bins=30, edgecolor='black', alpha=0.7)
    axes[1, 1].set_xlabel('成功指标')
    axes[1, 1].set_ylabel('Episode 数量')
    axes[1, 1].set_title(f'成功指标分布\n均值: {np.mean(success_metrics):.2f}')
    axes[1, 1].axvline(np.mean(success_metrics), color='r', linestyle='--')
    
    plt.tight_layout()
    plt.savefig(data_root / 'roboTurk_statistics.png', dpi=150)
    print(f"统计图已保存: {data_root / 'roboTurk_statistics.png'}")
    plt.show()
    plt.close()


def visualize_image_frames(hdf5_path: str, ep_name: str, frame_indices: List[int]):
    """
    可视化指定帧的图像
    
    参数:
        hdf5_path: HDF5 文件路径
        ep_name: episode 名称
        frame_indices: 要可视化的帧索引列表
    """
    with h5py.File(hdf5_path, 'r') as f:
        images_raw = f[f"episodes/{ep_name}/observations/images/primary"][:]
    
    n_frames = len(frame_indices)
    fig, axes = plt.subplots(1, n_frames, figsize=(4 * n_frames, 4))
    
    if n_frames == 1:
        axes = [axes]
    
    for ax, idx in zip(axes, frame_indices):
        if idx >= len(images_raw):
            print(f"帧索引 {idx} 超出范围（共 {len(images_raw)} 帧）")
            continue
        
        img_bytes = images_raw[idx]
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        ax.imshow(img)
        ax.set_title(f'帧 {idx}')
        ax.axis('off')
    
    plt.tight_layout()
    plt.show()
```

### 6.3 训练示例

下面实现基于 RoboTurk 的完整行为克隆训练：

```python
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from typing import List, Optional
import json

class RoboTurkBCPolicy(nn.Module):
    """
    基于 RoboTurk 的行为克隆策略网络
    
    输入：图像 (H, W, 3) + 状态向量 (state_dim,)
    输出：动作向量 (7,)
    """
    
    def __init__(
        self,
        image_size: tuple = (224, 224),
        state_dim: int = 14,
        action_dim: int = 7,
        hidden_dim: int = 256
    ):
        super().__init__()
        
        # 图像编码器（轻量 CNN）
        self.image_encoder = nn.Sequential(
            # 输入: (B, 3, 224, 224)
            nn.Conv2d(3, 32, kernel_size=7, stride=2, padding=3),  # 112x112
            nn.ReLU(),
            nn.MaxPool2d(2),                                        # 56x56
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),  # 28x28
            nn.ReLU(),
            nn.MaxPool2d(2),                                        # 14x14
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1), # 7x7
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),                          # 1x1
            nn.Flatten(),
            nn.Linear(128, hidden_dim),
            nn.ReLU()
        )
        
        # 状态编码器（MLP）
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # 融合 + 动作预测
        self.fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU()
        )
        
        # 动作预测头
        self.action_head = nn.Linear(hidden_dim // 2, action_dim)
        
        # 动作尺度参数（可学习）
        self.register_parameter(
            'action_scale', 
            nn.Parameter(torch.ones(action_dim) * 0.5)
        )
        self.register_parameter(
            'action_bias', 
            nn.Parameter(torch.zeros(action_dim))
        )
    
    def forward(
        self, 
        image: torch.Tensor, 
        state: torch.Tensor
    ) -> torch.Tensor:
        """
        前向传播
        
        参数:
            image: 图像张量 (B, H, W, 3) 或 (B, 3, H, W)
            state: 状态张量 (B, state_dim)
        
        返回:
            action: 动作张量 (B, action_dim)
        """
        # 确保图像格式为 (B, C, H, W)
        if image.dim() == 4 and image.shape[-1] == 3:
            image = image.permute(0, 3, 1, 2)
        
        # 图像编码
        img_feat = self.image_encoder(image)  # (B, hidden_dim)
        
        # 状态编码
        state_feat = self.state_encoder(state)  # (B, hidden_dim)
        
        # 融合
        fused = torch.cat([img_feat, state_feat], dim=1)  # (B, hidden_dim*2)
        fused = self.fusion(fused)  # (B, hidden_dim//2)
        
        # 动作预测
        action = self.action_head(fused)  # (B, action_dim)
        action = action * torch.tanh(self.action_scale) + self.action_bias
        
        return action


def train_rob Turk_bc(
    data_root: str,
    tasks: Optional[List[str]] = None,
    epochs: int = 100,
    batch_size: int = 32,
    lr: float = 1e-3,
    save_path: str = "roboTurk_bc_policy.pth",
    stats_path: str = "normalization_stats.npz"
):
    """
    训练 RoboTurk 行为克隆策略
    
    参数:
        data_root: 数据目录
        tasks: 训练任务列表
        epochs: 训练轮数
        batch_size: 批次大小
        lr: 学习率
        save_path: 模型保存路径
        stats_path: 归一化参数保存路径
    """
    from roboTurk_dataset import RoboTurkDataset, create_rob Turk_dataloader
    
    # 创
    # 创建数据集和 DataLoader
    print("初始化数据集...")
    dataset = RoboTurkDataset(
        data_root=data_root,
        tasks=tasks,
        image_size=(224, 224),
        seq_length=16,
        normalize_actions=True
    )
    
    dataloader = create_rob Turk_dataloader(
        data_root=data_root,
        tasks=tasks,
        batch_size=batch_size,
        shuffle=True
    )
    
    # 保存归一化参数
    stats = {
        "action_mean": dataset.action_mean.numpy(),
        "action_std": dataset.action_std.numpy()
    }
    np.savez(stats_path, **stats)
    print(f"归一化参数已保存: {stats_path}")
    
    # 创建模型
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    
    policy = RoboTurkBCPolicy(
        image_size=(224, 224),
        state_dim=14,
        action_dim=7,
        hidden_dim=256
    ).to(device)
    
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    
    # 训练循环
    print(f"开始训练，共 {epochs} 个 epochs...")
    best_loss = float('inf')
    
    for epoch in range(epochs):
        policy.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch in dataloader:
            images = batch["images"].to(device)       # (B, T, H, W, 3)
            states = batch["states"].to(device)      # (B, T, state_dim)
            actions = batch["actions"].to(device)   # (B, T, 7)
            mask = batch["mask"].to(device)          # (B, T)
            
            # 取最后一帧作为观测和动作目标（行为克隆标准做法）
            image_input = images[:, -1]              # (B, H, W, 3)
            state_input = states[:, -1]             # (B, state_dim)
            action_target = actions[:, -1]          # (B, 7)
            
            # 前向传播
            pred_action = policy(image_input, state_input)
            
            # 计算损失
            loss = loss_fn(pred_action, action_target)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        
        marker = " *" if avg_loss < best_loss else ""
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(policy.state_dict(), save_path)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}{marker}")
    
    print(f"\n训练完成！最佳损失: {best_loss:.6f}")
    print(f"模型已保存: {save_path}")
    
    return policy


# ============ 使用示例 ============

if __name__ == "__main__":
    # 训练指定任务的策略
    policy = train_rob Turk_bc(
        data_root="./roboTurk_processed",
        tasks=["pick_place", "push"],
        epochs=100,
        lr=1e-3,
        batch_size=32,
        save_path="roboTurk_bc_policy.pth"
    )
```

---

## 7. 练习题

### 选择题

1. **RoboTurk 数据集使用的遥操作设备是？**
   - A. Phantom Omni 力反馈设备
   - B. 游戏手柄
   - C. 智能手机
   - D. VR 头显控制器

2. **RoboTurk 数据采集的众包平台是？**
   - A. Amazon Mechanical Turk
   - B. 微信小程序
   - C. Upwork
   - D. Fiverr

3. **RoboTurk 数据集使用什么格式存储数据？**
   - A. ROS Bag
   - B. HDF5
   - C. JSON
   - D. NumPy .npz

4. **RoboTurk 中动作向量是多少维？**
   - A. 3 维
   - B. 6 维
   - C. 7 维
   - D. 14 维

5. **RoboTurk 的智能手机遥操作中，手机的什么传感器用于控制机械臂运动？**
   - A. GPS
   - B. 摄像头
   - C. 陀螺仪
   - D. 麦克风

### 填空题

6. **RoboTurk 将手机倾斜角度映射为机械臂末端执行器的 ________ 。**

7. **RoboTurk 数据集中，最终保留了约 ________% 的原始采集数据（质量和规模平衡）。**

8. **RoboTurk 使用 ________ 格式存储图像序列，而非连续视频文件。**

9. **RoboTurk 动作向量的前 3 维表示 ________，第 7 维表示 ________ 。**

10. **HDF5 格式的优势包括支持大文件、________ 和跨平台。**

### 简答题

11. **比较 RoboTurk 与 RH20T 的数据采集方式，指出各自的优势和局限性。**

12. **RoboTurk 如何保证众包数据的质量？列出至少 3 种质量控制机制。**

13. **说明 RoboTurk 数据集中 `success_metric` 字段的含义及其用途。**

14. **为什么 RoboTurk 选择将图像数据存储为 JPEG 字节序列而非连续视频文件？**

15. **简述 HDF5 格式在 RoboTurk 数据存储中的优势。**

### 编程题

16. **编写代码实现按 `success_metric` 阈值过滤 RoboTurk episode**：
    - 输入：`data_root`、`min_success` 阈值
    - 输出：过滤后的 episode 列表及其统计信息

17. **基于 RoboTurk 数据集，实现一个数据增强函数**：
    - 对图像添加随机亮度/对比度变化
    - 对动作添加高斯噪声扰动

18. **编写一个完整的训练脚本，从加载数据到保存模型**：
    - 使用 CNN 编码图像，MLP 编码状态
    - 支持断点续训
    - 记录训练 loss 曲线

---

## 8. 练习题答案

### 选择题

1. **答案：C**
   - RoboTurk 的核心创新是使用智能手机作为遥操作终端，操作员通过手机陀螺仪控制机械臂运动

2. **答案：A**
   - RoboTurk 通过 Amazon Mechanical Turk（MTurk）众包平台发布任务，招募全球用户参与数据采集

3. **答案：B**
   - RoboTurk 使用 HDF5（Hierarchical Data Format version 5）格式存储数据，适合大规模科学数据

4. **答案：C**
   - RoboTurk 动作向量为 7 维：3 维末端位置增量 + 3 维姿态增量 + 1 维夹爪控制

5. **答案：C**
   - 手机陀螺仪捕捉倾斜角度（roll, pitch, yaw），映射为机械臂末端执行器的运动指令

### 填空题

6. **答案：位置增量（或运动指令）**
   - 手机陀螺仪的倾斜角度被编码为机械臂末端执行器的位置增量指令

7. **答案：70-80%**
   - 通过多层次质量控制机制，RoboTurk 最终保留了约 70-80% 的原始采集数据

8. **答案：JPEG 字节序列**
   - 每帧图像单独压缩为 JPEG 格式存储，按需加载，支持数据增强

9. **答案：末端位置增量 和 夹爪控制**
   - 前 3 维 (world_vector) 是末端执行器在 x/y/z 方向的位置增量
   - 第 7 维 (gripper_closedness_action) 是夹爪的开闭控制信号

10. **答案：随机访问**
    - HDF5 支持随机访问，无需加载整个文件即可访问部分数据

### 简答题

11. **RoboTurk vs RH20T 对比**：

| 维度 | RoboTurk | RH20T |
|------|----------|-------|
| 遥操作设备 | 智能手机 | Phantom Omni 力反馈设备 |
| 采集方式 | 众包（MTurk） | 实验室专业操作员 |
| 数据规模 | 14,000+ episodes | 11,000+ episodes |
| 操作员数量 | 1,000+ 人 | 数十人 |
| 动作多样性 | 高（来自不同人） | 较低（专业操作员风格相似）|
| 数据质量 | 参差不齐（需质量控制） | 较高且一致 |
| 硬件成本 | 几乎为零 | 较高（力反馈设备）|
| 适用场景 | 大规模预训练 | 精细控制任务 |

12. **RoboTurk 质量控制机制**：
    - **实时反馈系统**：APP 实时显示任务完成状态，worker 可及时调整
    - **自动质量筛选**：设定最低成功率阈值，过滤异常轨迹
    - **人工审核机制**：随机抽样进行人工审核评分
    - **Worker 信誉系统**：记录历史质量，限制低质量 worker 参与

13. **`success_metric` 的含义与用途**：
    - **含义**：表示任务完成的程度，是一个 0~1 之间的连续值
    - **计算方式**：例如抓取放置任务中，衡量物体最终位置与目标区域的接近程度
    - **用途**：精细化评估（不只是成功/失败二值）、质量过滤、训练加权

14. **JPEG 字节序列存储的优势**：
    - **按需加载**：训练时只需加载需要的帧，无需解码整个视频
    - **支持预处理**：每帧独立，可灵活应用数据增强
    - **可变帧率**：可根据任务调整采样频率
    - **节省空间**：JPEG 压缩率高，比未压缩视频节省大量存储

15. **HDF5 格式优势**：
    - **支持大文件**：可存储数十 GB 的数据集
    - **随机访问**：可直接读取特定 episode 或字段，无需扫描全文件
    - **跨平台**：Python、C++、MATLAB 等多语言支持
    - **层次结构**：原生支持嵌套的群组和数据集结构
    - **内置压缩**：支持多种压缩算法

### 编程题答案

16. **按 `success_metric` 过滤**：

```python
import h5py
from pathlib import Path
from typing import List, Tuple

def filter_by_success_metric(
    data_root: str,
    min_success: float = 0.5
) -> List[dict]:
    """
    按 success_metric 阈值过滤 episode
    
    参数:
        data_root: 数据根目录
        min_success: 最低成功指标阈值
    
    返回:
        过滤后的 episode 信息列表
    """
    data_root = Path(data_root)
    hdf5_files = list(data_root.glob("*.hdf5"))
    
    filtered_eps = []
    all_metrics = []
    
    for hdf5_path in hdf5_files:
        try:
            with h5py.File(hdf5_path, 'r') as f:
                if "episodes" not in f:
                    continue
                
                for ep_name in f["episodes"].keys():
                    try:
                        meta = f[f"episodes/{ep_name}/metadata"]
                        
                        task_name = meta["task_name"][()]
                        if isinstance(task_name, bytes):
                            task_name = task_name.decode('utf-8')
                        
                        success = bool(meta["success"][()])
                        success_metric = float(meta["success_metric"][()])
                        
                        all_metrics.append(success_metric)
                        
                        if success_metric >= min_success:
                            filtered_eps.append({
                                "hdf5_path": str(hdf5_path),
                                "ep_name": ep_name,
                                "task_name": task_name,
                                "success": success,
                                "success_metric": success_metric
                            })
                    except Exception:
                        continue
        except Exception:
            continue
    
    # 统计信息
    if all_metrics:
        print(f"=== 过滤统计 ===")
        print(f"最低阈值: {min_success}")
        print(f"总 episode 数: {len(all_metrics)}")
        print(f"通过阈值: {len(filtered_eps)} ({100*len(filtered_eps)/len(all_metrics):.1f}%)")
        print(f"成功指标范围: [{min(all_metrics):.3f}, {max(all_metrics):.3f}]")
        print(f"成功指标均值: {sum(all_metrics)/len(all_metrics):.3f}")
    
    return filtered_eps

# 测试
if __name__ == "__main__":
    results = filter_by_success_metric(
        data_root="./roboTurk_raw",
        min_success=0.5
    )
    print(f"\n过滤后共 {len(results)} 个 episode")
    for ep in results[:5]:
        print(f"  {ep['ep_name']}: {ep['task_name']}, metric={ep['success_metric']:.2f}")
```

17. **数据增强函数**：

```python
import numpy as np
import cv2
from typing import Tuple

def augment_image(
    image: np.ndarray,
    brightness_range: Tuple[float, float] = (0.8, 1.2),
    contrast_range: Tuple[float, float] = (0.8, 1.2)
) -> np.ndarray:
    """
    对图像进行随机亮度/对比度增强
    
    参数:
        image: 输入图像 (H, W, 3)，值域 [0, 1]
        brightness_range: 亮度缩放范围
        contrast_range: 对比度缩放范围
    
    返回:
        增强后的图像
    """
    # 随机亮度调整
    brightness = np.random.uniform(*brightness_range)
    image = np.clip(image * brightness, 0, 1)
    
    # 随机对比度调整
    contrast = np.random.uniform(*contrast_range)
    mean = image.mean()
    image = np.clip((image - mean) * contrast + mean, 0, 1)
    
    return image.astype(np.float32)


def augment_action(
    action: np.ndarray,
    noise_std: float = 0.02,
    action_bounds: Tuple[np.ndarray, np.ndarray] = None
) -> np.ndarray:
    """
    对动作添加高斯噪声扰动
    
    参数:
        action: 动作向量 (7,) 或 (T, 7)
        noise_std: 噪声标准差
        action_bounds: (min, max) 边界，None 表示不限制
    
    返回:
        增强后的动作
    """
    # 构建逐维度噪声标准差（夹爪噪声更小）
    if action.ndim == 1:
        stds = np.array([noise_std] * 3 + [noise_std] * 3 + [noise_std * 0.5])
        noise = np.random.normal(0, stds)
    else:
        T = action.shape[0]
        stds = np.array([noise_std] * 3 + [noise_std] * 3 + [noise_std * 0.5])
        noise = np.random.normal(0, stds, size=(T, 7))
    
    action_aug = action + noise
    
    # 限制在合法范围内
    if action_bounds is not None:
        action_min, action_max = action_bounds
        action_aug = np.clip(action_aug, action_min, action_max)
    
    return action_aug.astype(np.float32)


def batch_augment(
    images: np.ndarray,
    actions: np.ndarray,
    num_augmentations: int = 5
) -> Tuple[np.ndarray, np.ndarray]:
    """
    批量数据增强
    
    参数:
        images: 图像数组 (T, H, W, 3)
        actions: 动作数组 (T, 7)
        num_augmentations: 每个样本增强次数
    
    返回:
        (增强图像, 增强动作) 元组
    """
    augmented_images = [images]
    augmented_actions = [actions]
    
    for _ in range(num_augmentations):
        # 图像增强
        aug_images = np.array([
            augment_image(img) for img in images
        ])
        
        # 动作增强（动作范围限制）
        action_min = np.array([-0.1, -0.1, -0.1, -0.05, -0.05, -0.05, 0.0])
        action_max = np.array([0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 1.0])
        
        aug_actions = augment_action(
            actions,
            noise_std=0.02,
            action_bounds=(action_min, action_max)
        )
        
        augmented_images.append(aug_images)
        augmented_actions.append(aug_actions)
    
    return np.concatenate(augmented_images, axis=0), np.concatenate(augmented_actions, axis=0)
```

18. **完整训练脚本（含断点续训）**：

```python
import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List, Optional
import json

# ============ 策略网络定义 ============

class RoboTurkBCPolicy(nn.Module):
    """行为克隆策略网络"""
    
    def __init__(self, state_dim=14, action_dim=7, hidden_dim=256):
        super().__init__()
        
        # 图像编码器（简化版：直接用状态，不处理图像）
        self.state_encoder = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        
        # 动作预测头
        self.action_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Tanh()
        )
        
        # 可学习动作尺度
        self.action_scale = nn.Parameter(torch.ones(action_dim) * 0.5)
        self.action_bias = nn.Parameter(torch.zeros(action_dim))
    
    def forward(self, state):
        feat = self.state_encoder(state)
        action = self.action_head(feat)
        return action * self.action_scale + self.action_bias


# ============ 数据加载 ============

def load_rob Turk_numpy(data_root):
    """加载 NumPy 格式的 RoboTurk 数据"""
    data_root = Path(data_root)
    
    all_states = []
    all_actions = []
    
    for npz_file in data_root.glob("*.npz"):
        data = np.load(npz_file)
        all_states.append(data["states"])
        all_actions.append(data["actions"])
    
    states = torch.FloatTensor(np.concatenate(all_states, axis=0))
    actions = torch.FloatTensor(np.concatenate(all_actions, axis=0))
    
    return states, actions


# ============ 训练函数 ============

def train_with_resume(
    data_root: str,
    save_path: str = "roboTurk_bc.pth",
    epochs: int = 100,
    lr: float = 1e-3,
    batch_size: int = 256
):
    """
    带断点续训的 RoboTurk BC 训练
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    print("加载数据...")
    states, actions = load_rob Turk_numpy(data_root)
    print(f"数据规模: states={states.shape}, actions={actions.shape}")
    
    # 计算归一化参数
    action_mean = actions.mean(dim=0)
    action_std = actions.std(dim=0) + 1e-7
    normalized_actions = (actions - action_mean) / action_std
    
    # 创建 DataLoader
    dataset = torch.utils.data.TensorDataset(states, normalized_actions)
    dataloader = torch.utils.data.DataLoader(
        dataset, batch_size=batch_size, shuffle=True, num_workers=4
    )
    
    # 创建模型
    policy = RoboTurkBCPolicy().to(device)
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    
    # 断点续训
    start_epoch = 0
    best_loss = float('inf')
    losses = []
    save_path = Path(save_path)
    
    if save_path.exists():
        print(f"检测到已有模型: {save_path}")
        checkpoint = torch.load(save_path, map_location=device)
        policy.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_loss = checkpoint.get('best_loss', float('inf'))
        losses = checkpoint.get('losses', [])
        print(f"从 epoch {start_epoch} 继续训练")
    
    print(f"使用设备: {device}")
    print(f"开始训练，从 epoch {start_epoch} 到 {epochs}...")
    
    for epoch in range(start_epoch, epochs):
        policy.train()
        epoch_loss = 0.0
        num_batches = 0
        
        for batch_states, batch_actions in dataloader:
            batch_states = batch_states.to(device)
            batch_actions = batch_actions.to(device)
            
            pred_actions = policy(batch_states)
            loss = loss_fn(pred_actions, batch_actions)
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), max_norm=1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
        
        avg_loss = epoch_loss / num_batches
        losses.append(avg_loss)
        
        marker = ""
        if avg_loss < best_loss:
            best_loss = avg_loss
            marker = " *"
            torch.save({
                'epoch': epoch,
                'model_state_dict': policy.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_loss': best_loss,
                'losses': losses,
                'action_mean': action_mean,
                'action_std': action_std
            }, save_path)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}{marker}")
    
    # 绘制 loss 曲线
    plt.figure(figsize=(10, 5))
    plt.plot(losses)
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title(f'RoboTurk BC Training (Best: {best_loss:.6f})')
    plt.grid(True)
    plt.savefig('training_loss.png', dpi=150)
    print("Loss 曲线已保存: training_loss.png")
    
    print(f"\n训练完成！最佳损失: {best_loss:.6f}")
    print(f"模型保存: {save_path}")


if __name__ == "__main__":
    train_with_resume(
        data_root="./roboTurk_processed",
        save_path="roboTurk_bc.pth",
        epochs=100,
        lr=1e-3,
        batch_size=256
    )
```

---

## 本章小结

本节课程系统介绍了 RoboTurk 众包机器人遥操作数据集：

1. **数据集概述**：RoboTurk 是斯坦福大学发布的大规模众包遥操作数据集，包含 14,000+ 条演示、8 种操作任务，创新性地使用智能手机作为遥操作终端

2. **数据采集系统**：通过 Amazon Mechanical Turk 众包平台招募用户，利用手机陀螺仪控制机械臂，设计了多层次质量控制机制（实时反馈、自动筛选、人工审核、信誉系统）

3. **数据格式**：使用 HDF5 格式存储，包含图像序列（压缩 JPEG）、机器人状态（关节、末端、夹爪）和动作向量（7 维），支持随机访问和高效存储

4. **任务类型**：覆盖基础操作（抓取、放置、推）、中级操作（搅拌、开门）和高级操作（排序、叠放）三大难度级别

5. **使用方法**：支持官方网站和 GitHub 下载，预处理后可转换为 NumPy 或 RLDS 格式，与主流模仿学习框架集成

6. **代码实战**：实现了完整的数据加载器（HDF5 读取、图像处理、归一化）、轨迹可视化工具（3D 轨迹、关节曲线、统计图表）和行为克隆训练脚本（断点续训、loss 记录）

---

**相关资源**：

- RoboTurk 官网：https://h2r.github.io/rob Turk/
- GitHub 仓库：https://github.com/StanfordVL/rob Turk
- HDF5 Python API：https://docs.h5py.org/
- Amazon Mechanical Turk：https://www.mturk.com/
