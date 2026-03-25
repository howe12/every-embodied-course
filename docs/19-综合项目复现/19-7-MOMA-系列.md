# 19-7 MOMA 系列

> **前置课程**：15-模仿学习基础、19-4 RH20T 数据集、19-6 MIMIC 数据集
> **后续课程**：19-8 MOMA 实战

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在前几节课程中，我们分别介绍了日常操作数据集（RH20T、RoboTurk）和手术机器人数据集（MIMIC）。这些数据集主要关注**固定基座**机械臂的操作任务。本节我们将进入**移动操作**领域，学习具身智能中一个极具挑战性的方向——**移动机械臂操作**（Mobile Manipulation）。我们将深入研究 **MOMA**（Multi-Operation Mobile Manipulator）系列数据集，这是目前最具影响力的移动操作数据集之一，涵盖了移动机械臂在家庭、企业、工厂等多种场景下的操作任务。MOMA 系列为家庭服务机器人、物流机器人、工业协作机器人的模仿学习和强化学习研究提供了重要的数据支撑。通过本节学习，你将全面理解 MOMA 的数据集设计理念、数据格式、使用方法，并掌握基于该数据集的代码实战技能。

---

## 1. MOMA 概述

### 1.1 什么是 MOMA

MOMA（Multi-Operation Mobile Manipulator，多操作移动机械臂）是一个专注于**移动机械臂操作**的大规模机器人数据集系列。与传统固定基座机械臂不同，移动机械臂由一个可自主移动的**底盘**（Mobile Base）和一个多自由度**机械臂**组成，能够在更大范围内执行操作任务。

MOMA 系列包含多个子数据集：

| 数据集 | 侧重点 | 发布机构 |
|--------|--------|---------|
| MOMA-Supervised | 移动操作模仿学习数据 | 斯坦福大学 |
| MOMA-Challenge | 移动操作竞赛任务 | ICRA/RSS 等学术会议 |
| MOMA-Large | 超大规模移动操作数据 | 多机构联合 |
| MOMA-Industry | 工业场景移动操作 | 西门子/ABB 联合实验室 |

MOMA 的核心研究问题是：**如何在移动平台上实现精确、鲁棒的机械臂操作？** 这一问题的难点在于：

1. **运动学耦合**：底盘移动会影响机械臂的基坐标系，进而影响末端执行器的定位精度
2. **双目定位问题**：底盘移动时，相机的视角持续变化，需要持续重新定位
3. **任务规划复杂**：移动操作任务通常需要在导航和操作之间进行协调规划
4. **环境交互多样性**：移动机器人需要同时处理地面平整度、障碍物规避、人机协作等挑战

### 1.2 数据规模

MOMA-Large 是目前最大的移动操作数据集之一：

| 指标 | 数值 |
|------|------|
| 总时长 | 1,000,000+ 秒（约 280 小时） |
| 演示片段（Episodes） | 80,000+ 条 |
| 任务类型 | 200+ 种移动操作任务 |
| 机器人平台 | Fetch / PR2 / Stretch / Unitree 机械臂 |
| 场景数量 | 50+ 个不同室内场景 |
| 传感器通道 | 15+ 通道（RGB-D、激光雷达、关节角、底盘里程计等） |
| 标注类型 | 任务描述、动作序列、场景物体、成功与否 |

### 1.3 与其他数据集的核心区别

MOMA 与之前介绍的 RH20T、RoboTurk、MIMIC 在**机器人构型**和**任务类型**上有本质区别：

| 维度 | RH20T | RoboTurk | MIMIC | MOMA |
|------|-------|----------|-------|------|
| 基座类型 | 固定基座 | 固定基座 | 固定基座（手术台旁） | **移动基座** |
| 操作范围 | 工作空间（约 1m³） | 工作空间（约 1m³） | 手术器械范围 | **整个室内空间** |
| 任务层次 | 单一操作 | 单一操作 | 手术操作 | **导航 + 操作** |
| 传感器重点 | 多视角 RGB-D | 单目相机 | 双目立体视觉 | **RGB-D + 激光雷达** |
| 主要应用 | 家庭操作 | 众包演示 | 医疗手术 | **家庭服务 / 物流** |

MOMA 的数据采集更为复杂——不仅需要记录机械臂的关节角度和末端位姿，还需要同步记录底盘的里程计数据、激光雷达扫描、导航目标点等移动平台特有的信息。

---

## 2. MOMA-Challenge

### 2.1 竞赛任务定义

MOMA-Challenge 是 ICRA 和 RSS 等学术会议举办的年度移动操作竞赛，旨在评估机器人在**真实家庭环境**中的移动操作能力。

**核心任务类型**：

**任务一：移动抓取（Mobile Grasping）**
- 机器人接收自然语言指令（如"把桌子上的红色方块拿给我"）
- 机器人需要自主导航到目标位置
- 识别并抓取指定物体
- 移动到用户位置并交付物体

**任务二：物体归置（Object Rearrangement）**
- 将指定物体从当前位置移动到目标位置
- 可能涉及开门、绕过障碍物等子任务
- 需要理解物体间的空间关系

**任务三：场景重建（Scene Rearrangement）**
- 根据参考图像恢复场景布局
- 多个物体需要按特定规则摆放
- 涉及精细操作和长距离移动

**任务四：人机交接（Human-Robot Handover）**
- 从人类手中接收或交付物体
- 需要理解人类的意图和手势
- 安全的力控制策略

### 2.2 评估标准

MOMA-Challenge 采用多维度评估体系：

| 指标 | 描述 | 权重 |
|------|------|------|
| 任务成功率（Success Rate） | 是否成功完成任务 | 40% |
| 执行时间（Execution Time） | 从指令到完成的总时间 | 20% |
| 路径效率（Path Efficiency） | 实际路径与最优路径的比值 | 15% |
| 操作精度（Manipulation Precision） | 物体放置精度、夹爪对齐度 | 15% |
| 安全性（Safety） | 碰撞次数、力限幅违规次数 | 10% |

**综合评分公式**：

$$
S_{total} = 0.4 \cdot S_{success} + 0.2 \cdot \frac{T_{max} - T_{actual}}{T_{max}} + 0.15 \cdot \frac{L_{optimal}}{L_{actual}} + 0.15 \cdot P_{manip} + 0.1 \cdot S_{safety}
$$

其中：
- $S_{success} \in \{0, 1\}$ 为任务是否成功
- $T_{actual}$ 为实际执行时间，$T_{max}$ 为允许最大时间
- $L_{actual}$ 为实际路径长度，$L_{optimal}$ 为最短路径长度
- $P_{manip} \in [0, 1]$ 为操作精度评分
- $S_{safety} \in [0, 1]$ 为安全性评分（基于碰撞检测）

### 2.3 基线方法

MOMA-Challenge 提供了多个基线方法供参赛者参考：

**基线一：分层策略（Hierarchical Policy）**

```python
class HierarchicalMobileManipulationPolicy:
    """
    分层移动操作策略
    
    架构：
    - 高层策略：负责导航目标规划（基于语言指令）
    - 中层策略：负责导航控制（基于激光雷达和里程计）
    - 低层策略：负责机械臂操作控制（基于视觉和触觉）
    """
    
    def __init__(self):
        self.high_level_policy = load_high_level_model()  # 语言 -> 导航目标
        self.mid_level_policy = load_nav_model()           # 感知 -> 底盘控制
        self.low_level_policy = load_arm_model()           # 视觉 -> 机械臂控制
    
    def step(self, observation):
        """
        执行一步策略
        
        参数:
            observation: 观测（语言指令、RGB-D图像、激光雷达扫描、关节状态等）
        
        返回:
            action: 动作（底盘速度 + 机械臂关节增量）
        """
        # 高层：解析指令，确定目标物体和目标位置
        nav_goal = self.high_level_policy.predict_goal(observation["language"])
        
        # 中层：根据激光雷达避障，执行导航到目标附近
        if not self._is_near_target(observation["base_pose"], nav_goal):
            base_action = self.mid_level_policy.navigate(
                lidar_scan=observation["lidar"],
                current_pose=observation["base_pose"],
                target_pose=nav_goal
            )
            return {"base_velocity": base_action, "arm_action": np.zeros(7)}
        
        # 低层：执行机械臂操作
        arm_action = self.low_level_policy.manipulate(
            rgb_image=observation["rgb"],
            depth_image=observation["depth"],
            ee_pose=observation["end_effector_pose"],
            target_object=observation.get("target_object")
        )
        
        return {"base_velocity": np.zeros(2), "arm_action": arm_action}
```

**基线二：端到端模仿学习（End-to-End IL）**

```python
class EndToEndMobileManipulationBC:
    """
    端到端移动操作行为克隆
    
    直接从多模态观测（图像 + 激光雷达 + 语言）预测完整动作
    优点：不需要手动设计中间表示
    缺点：需要大量数据训练
    """
    
    def __init__(self, state_dim=128, action_dim=9):
        """
        初始化网络
        
        参数:
            state_dim: 状态特征维度
            action_dim: 动作维度（2底盘速度 + 7关节增量）
        """
        import torch.nn as nn
        
        # 视觉编码器（处理 RGB 图像）
        self.vision_encoder = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64 * 26 * 26, state_dim),
            nn.ReLU()
        )
        
        # 激光雷达编码器
        self.lidar_encoder = nn.Sequential(
            nn.Linear(360, 128),  # 360束激光
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, state_dim)
        )
        
        # 语言编码器
        self.language_encoder = nn.Sequential(
            nn.Embedding(10000, 128),
            nn.GRU(input_size=128, hidden_size=64, batch_first=True),
        )
        
        # 融合 + 动作预测
        self.fusion = nn.Sequential(
            nn.Linear(state_dim * 3, state_dim),
            nn.ReLU()
        )
        
        self.action_head = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, action_dim),
            nn.Tanh()
        )
        
        # 动作尺度（可学习）
        self.action_scale = nn.Parameter(torch.ones(action_dim) * 0.5)
    
    def forward(self, rgb, lidar, language_tokens):
        """
        前向传播
        
        参数:
            rgb: RGB 图像张量 (B, 3, H, W)
            lidar: 激光雷达扫描 (B, 360)
            language_tokens: 语言 token (B, max_len)
        
        返回:
            action: 动作向量 (B, 9)
                   前2维：底盘速度 (vx, vw)
                   后7维：机械臂关节增量
        """
        import torch
        
        rgb_feat = self.vision_encoder(rgb)
        lidar_feat = self.lidar_encoder(lidar)
        
        # 语言特征：取 GRU 最后一个隐状态
        _, lang_hidden = self.language_encoder(language_tokens)
        lang_feat = lang_hidden.squeeze(0)
        
        # 融合多模态特征
        fused = self.fusion(torch.cat([rgb_feat, lidar_feat, lang_feat], dim=1))
        
        # 预测动作
        action = self.action_head(fused) * self.action_scale
        
        return action
```

---

## 3. MOMA-Large

### 3.1 数据规模

MOMA-Large 是 MOMA 系列中规模最大的子数据集，专门为训练**大规模移动操作策略**而设计：

| 指标 | 数值 |
|------|------|
| 总演示时长 | 1,000,000+ 秒 |
| Episode 总数 | 80,000+ 条 |
| 独立任务 | 200+ 种 |
| 机器人类型 | Fetch (55%)、PR2 (25%)、Stretch (20%) |
| 场景类型 | 家庭（60%）、办公室（25%）、工厂（15%） |
| 标注人员 | 500+ 名（众包 + 专业标注员） |

### 3.2 任务复杂度分层

MOMA-Large 将任务按复杂度分为四个层级：

| 层级 | 名称 | 示例任务 | 导航距离 | 操作复杂度 |
|------|------|---------|---------|-----------|
| L1 | 近距离操作 | 抓取桌上物体、开关抽屉 | < 2m | 单臂末端操作 |
| L2 | 中距离移动 | 移动到另一房间取物、多步操作 | 2-10m | 臂+夹爪协同 |
| L3 | 远距离导航+操作 | 整个房子的整理任务 | > 10m | 多物体、长时序 |
| L4 | 开放域任务 | 根据语言描述自由探索并完成任务 | 任意 | 需要推理规划 |

**任务复杂度分布**：

```python
# MOMA-Large 任务复杂度分布
task_distribution = {
    "L1_近距离操作": 0.25,   # 25%
    "L2_中距离移动": 0.35,   # 35%
    "L3_远距离导航操作": 0.30,  # 30%
    "L4_开放域任务": 0.10    # 10%
}

# 平均 Episode 长度分布
episode_stats = {
    "L1": {"mean_duration": 25, "std": 8, "min": 10, "max": 60},
    "L2": {"mean_duration": 60, "std": 20, "min": 30, "max": 150},
    "L3": {"mean_duration": 180, "std": 60, "min": 90, "max": 600},
    "L4": {"mean_duration": 300, "std": 120, "min": 120, "max": 1200}
}
```

### 3.3 场景多样性

MOMA-Large 覆盖了 50+ 个真实室内场景，按场景类型分布：

| 场景类别 | 子类别 | Episode 占比 |
|---------|--------|------------|
| 家庭场景 | 客厅、卧室、厨房、卫生间、阳台 | 60% |
| 办公室场景 | 工位、会议室、走廊、休息室 | 25% |
| 工业场景 | 仓库、生产线、装配区 | 15% |

---

## 4. 数据格式

### 4.1 轨迹格式

MOMA 的轨迹数据包含移动平台和机械臂的完整状态信息：

```python
{
    "timestamp": 1609459200000,      # 时间戳（毫秒）
    
    # 底盘状态（移动平台）
    "base_state": {
        "position": [1.5, 2.3],       # 底盘在地图中的 (x, y) 位置（米）
        "orientation": 1.57,           # 朝向角（弧度，逆时针为正）
        "velocity": [0.1, 0.02],      # 底盘速度 (vx, vw)，线速度+角速度
        "lidar_scan": [0.5, 0.6, ...],  # 360度激光雷达扫描（360个距离值，米）
        "camera_pose": [1.5, 2.3, 0.0, 0.0, 0.0, 0.707, 0.707]  # 相机位置+四元数
    },
    
    # 机械臂状态
    "arm_state": {
        "joint_positions": [0.1, -0.3, 0.8, 1.2, -0.5, 0.3, 0.0],  # 7个关节角度（弧度）
        "joint_velocities": [0.02, -0.01, 0.05, 0.01, -0.02, 0.01, 0.0],  # 关节速度
        "end_effector_pose": {          # 末端执行器位姿（基坐标系下）
            "position": [0.3, -0.1, 0.8],  # x, y, z（米）
            "orientation": [0.0, 0.0, 0.0, 1.0]  # 四元数 (qx, qy, qz, qw)
        },
        "gripper_state": 0.0           # 夹爪开度（0=全开，1=全闭）
    },
    
    # 视觉观测
    "observation": {
        "rgb_image": "base64_encoded_jpeg...",  # RGB 图像（Base64 编码）
        "depth_image": "base64_encoded_png...",  # 深度图像（Base64 编码）
        "camera_intrinsics": [525.0, 525.0, 319.5, 239.5],  # fx, fy, cx, cy
        "object_detections": [       # 目标检测结果
            {"class": "cup", "bbox": [120, 80, 200, 180], "confidence": 0.92, "depth": 0.45}
        ]
    },
    
    # 动作
    "action": {
        "base_velocity": [0.05, 0.0],   # 底盘速度 (vx, vw)
        "arm_delta": [0.01, -0.005, 0.02, 0.0, -0.01, 0.005, 0.0],  # 7个关节增量
        "gripper_action": 0.0          # 夹爪目标开度
    }
}
```

**动作空间定义**：

MOMA 的动作空间是 10 维向量：

$$
\mathbf{a}_t = [v_x, v_\omega, \Delta q_1, \Delta q_2, \Delta q_3, \Delta q_4, \Delta q_5, \Delta q_6, \Delta q_7, g]^T
$$

其中：
- $v_x \in [-0.5, 0.5]$ m/s：底盘线速度
- $v_\omega \in [-1.0, 1.0]$ rad/s：底盘角速度
- $\Delta q_i \in [-0.1, 0.1]$ rad：第 $i$ 个关节的角度增量
- $g \in [0, 1]$：夹爪目标开度

### 4.2 场景描述格式

MOMA 每个 episode 都附带了详细的场景描述：

```python
scene_annotation = {
    "scene_id": "home_living_room_01",
    "scene_type": "home",
    "sub_type": "living_room",
    "floor_plan": {
        "bounds": {"x_min": 0, "x_max": 8.5, "y_min": 0, "y_max": 6.0},
        "walls": [[...], [...]],  # 墙壁多边形
        "doors": [{"position": [...], "orientation": [...], "width": 0.9}, ...],
        "windows": [...]
    },
    "furniture": [
        {"type": "sofa", "position": [...], "size": [2.0, 0.8, 0.9], "orientation": 0.0},
        {"type": "coffee_table", "position": [...], "size": [1.2, 0.6, 0.45], "orientation": 0.0},
    ],
    "object_of_interest": [
        {"name": "red_cube", "category": "cube", "initial_pose": [...], "target_pose": [...]},
        {"name": "cup", "category": "cup", "initial_pose": [...], "target_pose": [...]}
    ],
    "navigation_goals": [
        {"name": "sofa_area", "position": [2.0, 3.0], "orientation": 0.0},
        {"name": "kitchen_entrance", "position": [7.5, 3.0], "orientation": 1.57}
    ]
}
```

### 4.3 任务规范格式

```python
task_spec = {
    "task_id": "moma_task_00042",
    "task_name": "mobile_pick_and_place",
    
    # 任务类型
    "task_type": {
        "primary": "pick_and_place",
        "secondary": ["navigation", "grasping", "reorientation"],
        "hierarchy_level": "L2"
    },
    
    # 初始状态
    "initial_state": {
        "robot_pose": {"position": [0.5, 0.5], "orientation": 0.0},
        "arm_config": [0.0] * 7,
        "gripper_state": 0.0,
    },
    
    # 目标状态
    "goal_state": {
        "target_object_pose": {...},
        "success_conditions": [
            {"type": "object_at_position", "object": "cup", "position": [2.0, 1.0, 0.8], "tolerance": 0.05},
            {"type": "gripper_open", "tolerance": 0.1}
        ]
    },
    
    # 难度参数
    "difficulty": {
        "level": "medium",
        "num_obstacles": 3,
        "navigation_distance": 5.2,
        "requires_reorientation": True,
        "time_limit": 120.0
    }
}
```

---

## 5. 使用方法

### 5.1 环境配置

MOMA 数据集支持多种使用方式，以下是推荐的环境配置：

```bash
# 方式一：使用 pip 安装（MOMA-Supervised 已发布到 PyPI）
pip install moma-dataset

# 方式二：从源码安装（获取最新功能）
git clone https://github.com/moma-dataset/moma.git
cd moma
pip install -e .

# 方式三：使用 Docker（推荐，避免依赖冲突）
docker pull momadataset/moma-env:latest
docker run -it --gpus all -v /path/to/moma_data:/data momadataset/moma-env:latest

# 验证安装
python -c "from moma_dataset import MOMA; print('MOMA 安装成功')"
```

**数据集下载**：

```bash
# 安装 huggingface_hub（数据托管在 Hugging Face）
pip install huggingface_hub

# 下载 MOMA-Supervised（推荐新手从这里开始）
python -c "
from huggingface_hub import hf_hub_download
# 下载完整数据集（约 100GB）
path = hf_hub_download(
    repo_id='moma-dataset/moma-supervised',
    filename='moma_supervised_full.tar.gz'
)
print(f'下载路径: {path}')
"

# 选择性下载（节省时间和存储）
python scripts/download_moma.py \
    --tasks mobile_pick_place \
    --robot_type fetch \
    --split train \
    --max_episodes 5000
```

### 5.2 任务执行

MOMA 数据集可以在多种仿真环境中使用：

```bash
# 方式一：使用 Habitat-Sim（推荐用于导航任务）
pip install habitat-sim

# 方式二：使用 PyBullet（推荐用于操作任务）
pip install pybullet

# 方式三：使用 Isaac Gym（高性能 GPU 仿真）
# 需要 NVIDIA 许可证

# 方式四：使用 Gazebo + ROS（高保真仿真）
# 需要 ROS Noetic/ Galactic 环境
```

**在 PyBullet 中加载 MOMA 场景**：

```python
import pybullet as p
import pybullet_data
import numpy as np

def setup_pybullet_env(moma_dataset_path):
    """
    设置 PyBullet 环境并加载 MOMA 场景
    
    参数:
        moma_dataset_path: MOMA 数据集根目录
    """
    # 连接 PyBullet 物理引擎（GUI 模式）
    client_id = p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    
    # 设置光照
    p.configureDebugVisualizer(p.CV_ENABLE_SHADOWS, 1)
    p.setGravity(0, 0, -9.81)
    
    # 加载地面
    p.loadURDF("plane.urdf")
    
    # 加载 Fetch 机器人（如果可用）
    robot_id = p.loadURDF("fetch_description/robots/fetch.urdf", [0, 0, 0])
    
    # 设置相机视角
    p.resetDebugVisualizerCamera(
        cameraDistance=2.0,
        cameraYaw=45,
        cameraPitch=-30,
        cameraTargetPosition=[0, 0, 0.5]
    )
    
    return client_id, robot_id

def execute_moma_episode(robot_id, episode_data):
    """
    执行一个 MOMA Episode 的演示回放
    
    参数:
        robot_id: 机器人 URDF ID
        episode_data: MOMA episode 数据
    """
    p.setRealTimeSimulation(True)
    
    for step_data in episode_data.trajectory:
        # 设置底盘目标速度
        base_vel = step_data["action"]["base_velocity"]
        
        # 获取底盘关节索引（通常是 base 的轮子关节）
        # 这里用 JOINT_CONTROL 模拟速度控制
        base_joint_indices = [0, 1]  # 视机器人型号而定
        
        for i, joint_idx in enumerate(base_joint_indices):
            if i < len(base_vel):
                p.setJointMotorControl2(
                    bodyUniqueId=robot_id,
                    jointIndex=joint_idx,
                    controlMode=p.VELOCITY_CONTROL,
                    targetVelocity=base_vel[i]
                )
        
        # 设置机械臂关节目标位置
        arm_delta = step_data["action"]["arm_delta"]
        
        # 获取当前机械臂关节状态
        num_joints = p.getNumJoints(robot_id)
        arm_start_idx = 2  # 通常前两个关节是底盘，后面才是机械臂
        
        for i in range(7):  # 7 个机械臂关节
            joint_idx = arm_start_idx + i
            current_pos = p.getJointState(robot_id, joint_idx)[0]
            target_pos = current_pos + arm_delta[i]
            
            p.setJointMotorControl2(
                bodyUniqueId=robot_id,
                jointIndex=joint_idx,
                controlMode=p.POSITION_CONTROL,
                targetPosition=target_pos,
                maxVelocity=0.5
            )
        
        # 步进仿真
        p.stepSimulation()
    
    print("Episode 执行完成")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        data_path = "./moma_supervised"
    
    client, robot = setup_pybullet_env(data_path)
    print(f"PyBullet 环境已启动，client_id={client}, robot_id={robot}")
```

### 5.3 结果提交

MOMA-Challenge 竞赛的结果提交通常通过在线平台进行：

```bash
# 方式一：使用官方 CLI 提交
pip install moma-challenge

# 配置 API 密钥（从竞赛官网获取）
moma-challenge configure --api-key YOUR_API_KEY

# 本地验证结果格式
moma-challenge validate --submission-dir ./results/

# 提交到竞赛服务器
moma-challenge submit \
    --submission-dir ./results/ \
    --competition moma-challenge-2024 \
    --split test
```

**提交格式要求**：

```python
submission_format = {
    "team_name": "MyAwesomeTeam",
    "method_name": "HierarchicalPolicy + BC",
    "submission_type": "policy_weights",  # 或 "docker_image"
    
    # 策略模型信息
    "model_info": {
        "architecture": "HierarchicalPolicy",
        "num_parameters": 12500000,
        "training_data": "MOMA-Large",
        "training_steps": 50000,
        "hardware": "NVIDIA RTX 3090"
    },
    
    # 任务结果（每个测试任务一行）
    "results": [
        {
            "task_id": "test_00001",
            "success": True,
            "execution_time": 45.2,
            "path_length": 8.5,
            "collision_count": 0,
        }
    ],
    
    # 代码仓库（可选）
    "code_repository": "https://github.com/myteam/moma-solution"
}
```

---

## 6. 代码实战

### 6.1 数据加载器实现

下面实现一个完整的 MOMA 数据加载器：

```python
import json
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import base64
import cv2

class MOMADataset(Dataset):
    """
    MOMA 数据集加载器
    
    支持：
    - 多机器人类型（Fetch、PR2、Stretch）
    - 多任务类型过滤
    - 多模态数据加载（RGB、Depth、Lidar、Kinematics）
    - 数据归一化
    """
    
    def __init__(
        self,
        data_root: str,
        split: str = "train",
        robot_type: Optional[List[str]] = None,
        task_types: Optional[List[str]] = None,
        difficulty_levels: Optional[List[str]] = None,
        seq_length: int = 32,
        image_size: Tuple[int, int] = (224, 224),
        load_images: bool = True,
        load_lidar: bool = True,
        normalize: bool = True
    ):
        """
        初始化数据集
        
        参数:
            data_root: 数据集根目录
            split: 数据集划分（train / val / test）
            robot_type: 机器人类型过滤列表
            task_types: 任务类型过滤列表
            difficulty_levels: 难度等级过滤列表
            seq_length: 序列长度
            image_size: 图像 resize 大小
            load_images: 是否加载图像
            load_lidar: 是否加载激光雷达数据
            normalize: 是否归一化
        """
        self.data_root = Path(data_root)
        self.split = split
        self.robot_type = robot_type
        self.task_types = task_types
        self.difficulty_levels = difficulty_levels
        self.seq_length = seq_length
        self.image_size = image_size
        self.load_images = load_images
        self.load_lidar = load_lidar
        self.normalize = normalize
        
        # 收集有效的 episodes
        self.episodes: List[Dict] = []
        self._scan_episodes()
        
        # 计算归一化参数
        if normalize:
            self._compute_normalization_params()
    
    def _scan_episodes(self):
        """扫描所有有效的 episodes 并按条件过滤"""
        split_root = self.data_root / self.split
        
        if not split_root.exists():
            print(f"警告：目录不存在 {split_root}")
            return
        
        # 遍历所有 episode 目录
        for ep_dir in sorted(split_root.iterdir()):
            if not ep_dir.name.startswith("episode_"):
                continue
            
            # 读取元数据
            meta_file = ep_dir / "metadata.json"
            if not meta_file.exists():
                continue
            
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            
            # 按机器人类型过滤
            if self.robot_type and meta.get("robot_type") not in self.robot_type:
                continue
            
            # 按任务类型过滤
            if self.task_types and meta.get("task_type", {}).get("primary") not in self.task_types:
                continue
            
            # 按难度等级过滤
            if self.difficulty_levels and meta.get("difficulty", {}).get("level") not in self.difficulty_levels:
                continue
            
            self.episodes.append({
                "path": ep_dir,
                "meta": meta,
                "task_name": meta.get("task_name", "unknown"),
                "robot_type": meta.get("robot_type", "unknown"),
                "success": meta.get("success", False),
                "difficulty": meta.get("difficulty", {}).get("level", "unknown")
            })
        
        print(f"加载了 {len(self.episodes)} 个有效 episode")
    
    def _compute_normalization_params(self):
        """计算归一化参数（从全部数据中采样）"""
        print("计算归一化参数...")
        
        sample_size = min(100, len(self.episodes))
        sampled_eps = np.random.choice(len(self.episodes), sample_size, replace=False)
        
        all_base_states = []
        all_arm_states = []
        all_actions = []
        
        for idx in sampled_eps:
            try:
                ep = self.episodes[idx]
                traj_file = ep["path"] / "trajectory.json"
                
                if not traj_file.exists():
                    continue
                
                with open(traj_file, 'r') as f:
                    trajectory = json.load(f)
                
                for frame in trajectory:
                    # 底盘状态：2D位置 + 朝向角 + 2个速度
                    base = frame.get("base_state", {})
                    base_pos = base.get("position", [0, 0])
                    base_yaw = base.get("orientation", 0)
                    base_vel = base.get("velocity", [0, 0])
                    base_state = base_pos + [base_yaw] + base_vel
                    
                    # 机械臂状态：7关节 + 3末端位置
                    arm = frame.get("arm_state", {})
                    arm_joints = arm.get("joint_positions", [0] * 7)
                    ee_pos = arm.get("end_effector_pose", {}).get("position", [0, 0, 0])
                    arm_state = arm_joints + ee_pos
                    
                    # 动作：2底盘 + 7关节 + 1夹爪
                    action_data = frame.get("action", {})
                    base_action = action_data.get("base_velocity", [0, 0])
                    arm_action = action_data.get("arm_delta", [0] * 7)
                    gripper_action = [action_data.get("gripper_action", 0)]
                    action = base_action + arm_action + gripper_action
                    
                    all_base_states.append(base_state)
                    all_arm_states.append(arm_state)
                    all_actions.append(action)
                    
            except Exception as e:
                continue
        
        if all_base_states and all_actions:
            all_base_states = np.array(all_base_states, dtype=np.float32)
            all_arm_states = np.array(all_arm_states, dtype=np.float32)
            all_actions = np.array(all_actions, dtype=np.float32)
            
            self.base_state_mean = torch.FloatTensor(all_base_states.mean(axis=0))
            self.base_state_std = torch.FloatTensor(all_base_states.std(axis=0) + 1e-7)
            self.arm_state_mean = torch.FloatTensor(all_arm_states.mean(axis=0))
            self.arm_state_std = torch.FloatTensor(all_arm_states.std(axis=0) + 1e-7)
            self.action_mean = torch.FloatTensor(all_actions.mean(axis=0))
            self.action_std = torch.FloatTensor(all_actions.std(axis=0) + 1e-7)
        else:
            # 默认值
            self.base_state_mean = torch.zeros(5)
            self.base_state_std = torch.ones(5)
            self.arm_state_mean = torch.zeros(10)
            self.arm_state_std = torch.ones(10)
            self.action_mean = torch.zeros(10)
            self.action_std = torch.ones(10)
    
    def _load_trajectory(self, ep_path: Path) -> List[Dict]:
        """加载单个 episode 的轨迹数据"""
        traj_file = ep_path / "trajectory.json"
        if not traj_file.exists():
            return []
        
        with open(traj_file, 'r') as f:
            trajectory = json.load(f)
        
        return trajectory
    
    def __len__(self) -> int:
        return len(self.episodes)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        获取一个 episode 的数据
        
        返回:
            dict: 包含以下键的字典
                - base_states: 底盘状态序列 (seq_len, 5)
                - arm_states: 机械臂状态序列 (seq_len, 10)
                - actions: 动作序列 (seq_len, 10)
                - task_name: 任务名称
                -