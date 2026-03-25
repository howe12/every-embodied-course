# 19-6 MIMIC数据集

> **前置课程**：15-模仿学习基础、19-4 RH20T 数据集、19-5 RoboTurk 数据集
> **后续课程**：19-7 MOMA 系列

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在前几节课程中，我们分别介绍了遥操作采集的 RH20T 数据集和众包模式的 RoboTurk 数据集。本节我们将进入**医疗机器人**领域，学习具身智能中一个极具社会价值的应用方向——**手术机器人**。我们将深入研究 **MIMIC**（Multi-modal Motor-Instrument Interface for Computer-assisted Surgery）数据集，这是目前最具影响力的手术机器人遥操作数据集之一，采集自达芬奇（Da Vinci）手术系统执行的各类手术。MIMIC 数据集为手术技能评估、手术流程分析和机器人辅助手术的模仿学习研究提供了宝贵的临床数据。通过本节学习，你将全面理解 MIMIC 的数据采集系统、数据格式设计、任务类型，并掌握基于该数据集的代码实战技能。

---

## 1. MIMIC 概述

### 1.1 什么是 MIMIC

MIMIC（Multi-modal Motor-Instrument Interface for Computer-assisted Surgery，多模态运动仪器接口计算机辅助手术系统）是由约翰斯·霍普金斯大学（Johns Hopkins University）、Intuitive Surgical 公司（达芬奇手术机器人制造商）以及多家国际研究机构联合发布的**大规模手术机器人遥操作数据集**。该数据集于 2020 年正式对外发布，旨在为手术机器人研究社区提供标准化、高质量的临床手术数据。

MIMIC 的核心定位是为以下研究提供数据支撑：
- **手术技能评估**：客观量化外科医生的操作水平
- **手术流程建模**：理解手术各阶段的时序特征和操作模式
- **手术机器人模仿学习**：训练机器人从专家演示中学习手术技能
- **自动化手术**：最终实现手术机器人的部分自动化操作

MIMIC 与此前介绍的 RH20T、RoboTurk 的核心区别在于其**医疗场景的真实性和复杂性**——数据来自真实的临床手术环境（或高保真模拟），操作对象是模拟组织或真实组织，任务目标涉及精细的切割、缝合、解剖等医学操作。

### 1.2 数据规模

MIMIC 数据集在发布时是**最大的手术机器人遥操作数据集**：

| 指标 | 数值 |
|------|------|
| 手术演示片段（Episodes） | 5,000+ 条 |
| 总时长 | 180,000+ 秒（约 50 小时） |
| 手术类型 | 15+ 种外科手术 |
| 外科医生数量 | 100+ 名（匿名化） |
| 手术机器人平台 | Da Vinci Research Kit (dVRK) |
| 传感器通道 | 20+ 通道（Kinematics、Video、Tool、Event 等） |
| 视频分辨率 | 1920 × 1080 @ 30Hz |
| 标注类型 | 手术相位、器械类型、事件标注 |

### 1.3 手术类型覆盖

MIMIC 涵盖多种外科手术类型，按难度从低到高排列：

| 手术类型 | 英文名称 | 难度 | 主要操作 |
|---------|---------|------|---------|
| 抓取与放置 | Peg Transfer | ⭐ | 转移手术针、夹取组织 |
| 丝绸转移 | Silk Suture Transfer | ⭐ | 精细夹取与放置 |
| 穿针引线 | Needle Passing | ⭐⭐ | 缝合练习、针的精确操控 |
| 环切术 | Ring Roller | ⭐⭐ | 环形结构的旋转操作 |
| 解剖分离 | Tissue Dissection | ⭐⭐⭐ | 组织剥离与切割 |
| 缝合 | Suture Manipulation | ⭐⭐⭐ | 缝合打结、组织连接 |
| 结扎 | Ligature | ⭐⭐⭐ | 血管结扎操作 |
| 抓取与回缩 | Grasp Retraction | ⭐⭐⭐ | 组织牵拉与暴露 |
| 切割 | Cutting | ⭐⭐⭐⭐ | 精确切割组织 |
| 吻合 | Anastomosis | ⭐⭐⭐⭐ | 管道连接手术 |

---

## 2. 数据采集系统

### 2.1 Da Vinci 手术系统

MIMIC 数据集的核心采集平台是 **Da Vinci Research Kit（dVRK）**——这是一款由约翰斯·霍普金斯大学基于达芬奇（Da Vinci）手术系统开发的开源研究平台。

达芬奇手术系统是 Intuitive Surgical 公司生产的商用手术机器人，是目前全球应用最广泛的手术机器人系统之一。它由三个主要组件构成：

- **外科医生控制台（Surgeon Console）**：提供 3D 高清立体视觉、力反馈手柄和主操作手，外科医生通过它远程控制机械臂
- **手术床旁机械臂（Patient Side Manipulators）**：4 条可独立操控的机械臂，配备 EndoWrist 灵巧器械（夹爪、针持、剪刀等）
- **视觉系统（Vision System）**：双目立体相机，提供 1080p 高清视频和近红外照明

dVRK 是专门为机器人手术研究设计的开源平台：
- **完整的主从控制**：主端发送运动指令，从端精确执行
- **开源固件**：研究团队可以访问底层控制代码进行二次开发
- **精确的运动映射**：主端手柄运动可配置比例映射到末端执行器运动
- **可替换末端工具**：支持多种 EndoWrist 器械的快速更换

### 2.2 日志记录系统

MIMIC 的数据采集依赖于 dVRK 平台内置的**高精度日志记录系统**，该系统以统一时钟源为基准，同步记录所有传感器数据：

| 通道类型 | 采样率 | 数据内容 | 用途 |
|---------|--------|---------|------|
| 主端关节角 | 100 Hz | 2 个主手的 6 自由度关节角 | 反映外科医生操作意图 |
| 从端关节角 | 100 Hz | 2 个从端机械臂的 6 自由度关节角 | 反映机器人实际执行状态 |
| 末端执行器位姿 | 100 Hz | 末端位置（xyz）+ 姿态（四元数） | 计算器械在患者体内的精确位置 |
| 夹爪开闭状态 | 100 Hz | 夹爪开度（0~1 连续值） | 判断当前操作类型 |
| 双目立体视频 | 30 Hz | 左/右相机图像（1080p） | 提供手术视野的视觉输入 |
| 事件标记 | 手动触发 | 手术相位切换、器械更换等事件 | 用于相位识别任务 |
| 力和力矩 | 50 Hz | 末端执行器感受的接触力（3 轴） | 反映组织交互的力学特性 |

MIMIC 采用了**硬件时间戳同步**方案：所有传感器共享一个高精度时钟（微秒级精度），每帧数据都带有统一的时间戳标签，视频流与运动数据在采集时即完成对齐。

### 2.3 脱敏处理

MIMIC 数据集经过了严格的**隐私脱敏处理**：

**已脱敏的信息**：
- 外科医生身份：全部替换为匿名 ID（如 "Surgeon_001"）
- 患者信息：完全不包含，所有数据来自模拟组织或匿名化数据
- 医疗机构信息：已移除所有来源标识
- 日期时间：仅保留手术持续时长，去除具体日期

**保留用于研究的信息**：
- 操作技能水平：每条演示附带技能评分（由专家标注）
- 手术类型和难度等级
- 器械类型和规格
- 客观运动学指标（轨迹平滑度、操作时间等）

---

## 3. 数据格式

### 3.1 运动学数据

MIMIC 的运动学数据包含主端（master）和从端（slave）的完整运动信息。

**数据字段说明**：

```python
{
    "timestamp": 1609459200000,         # 时间戳（毫秒，从手术开始计时）
    
    # 主端运动学（外科医生控制台）
    "master_state": {
        "joint_positions": [0.1, -0.3, 0.5, 0.2, -0.1, 0.4],  # 6 个关节角度（弧度）
        "joint_velocities": [0.02, -0.01, 0.03, 0.01, -0.02, 0.01],  # 关节速度
        "cartesian_position": {           # 笛卡尔空间位置
            "translation": [0.1, -0.05, 0.02],  # x, y, z（米）
            "rotation": [0.0, 0.0, 0.0, 1.0]   # 四元数 (qx, qy, qz, qw)
        },
        "gripper_position": 0.5,          # 主手夹爪位置（0=全开，1=全闭）
    },
    
    # 从端运动学（患者侧机械臂）
    "slave_state": {
        "joint_positions": [-0.2, 0.5, -0.3, 0.8, 0.1, -0.4],  # 6 个关节角度
        "cartesian_position": {           # 末端执行器在患者坐标系下的位姿
            "translation": [0.05, -0.02, 0.15],  # x, y, z（米）
            "rotation": [0.1, -0.1, 0.05, 0.99]  # 四元数
        },
        "jaw_position": 0.3,              # 器械夹爪开度（0~1）
        "insertion_depth": 0.12,          # 插入深度（米）
    },
    
    # 交互力（估算值，基于电机电流推算）
    "interaction_force": {
        "force": [0.1, -0.05, 0.02],     # 3 轴力（N）
        "torque": [0.0, 0.0, 0.0]         # 3 轴力矩（Nm）
    }
}
```

**主-从运动映射关系**：

主端运动学数据记录的是外科医生在控制台的操作，而从端数据记录的是机器人的实际执行状态。二者之间的映射关系为：

$$
\mathbf{q}_{slave} = f(\mathbf{q}_{master})
$$

其中 $f$ 是达芬奇系统的主-从运动映射函数，包含运动缩放（通常为 3:1 或 5:1）、姿态映射和碰撞检测等环节。

### 3.2 视频数据

视频数据是 MIMIC 中信息密度最高的模态，以**左右双目立体视频**的形式存储。

| 参数 | 数值 |
|------|------|
| 分辨率 | 1920 × 1080 像素（Full HD） |
| 帧率 | 30 Hz |
| 编码格式 | H.264 / MJPEG |
| 立体方式 | 左/右相机水平排列，基线距离约 8.5 mm |

**立体视觉的优势**：
- **深度感知**：通过左右图像的视差可以恢复场景的三维结构
- **精确测量**：手术中器械与组织的距离可以直接从立体视觉中获取
- **遮挡处理**：某一视角被遮挡时，另一个视角可提供补充信息

### 3.3 手术相位标注

MIMIC 数据集包含丰富的**手术相位标注**（采用 JIGSAWS 标注规范）：

| 阶段编号 | 阶段名称 | 描述 |
|---------|---------|------|
| 0 | 空闲（Idle） | 等待、准备状态 |
| 1 | 伸手（Reaching） | 器械向目标移动 |
| 2 | 抓取（Grasping） | 夹取组织或器械 |
| 3 | 回缩（Retracting） | 将抓取的物体拉向相机 |
| 4 | 定向（Orientation） | 调整物体/器械的姿态 |
| 5 | 平移（Translating） | 物体在空间中的平移 |
| 6 | 释放（Releasing） | 松开夹爪放下物体 |
| 7 | 缝合（Suturing） | 进行缝合操作 |
| 8 | 切割（Cutting） | 进行切割操作 |

**相位标注格式**：

```python
{
    "phase_annotations": [
        {
            "phase_id": 0,
            "phase_name": "准备阶段",
            "start_time": 0.0,
            "end_time": 15.5,
            "gesture": "Idle",
            "instruments": ["Left Large Needle Driver", "Right Cadiere Forceps"],
            "difficulty": "easy",
            "skill_level": 3
        },
        {
            "phase_id": 1,
            "phase_name": "组织分离",
            "start_time": 15.5,
            "end_time": 45.2,
            "gesture": "Grasping",
            "instruments": ["Left Bipolar Forceps", "Right Cadiere Forceps"],
            "difficulty": "medium",
            "skill_level": 4
        }
    ],
    
    "gesture_labels": [
        {"frame": 0, "gesture": "Idle"},
        {"frame": 50, "gesture": "Reaching"},
        {"frame": 120, "gesture": "Grasping"},
        {"frame": 200, "gesture": "Retracting"},
        {"frame": 350, "gesture": "Releasing"},
        {"frame": 400, "gesture": "Idle"}
    ]
}
```

### 3.4 数据文件结构

```
mimic_dataset/
├── episode_00001/
│   ├── metadata.json                    # 元数据（手术类型、外科医生ID、技能评分等）
│   ├── kinematics/
│   │   ├── master_state.csv             # 主端运动学数据
│   │   ├── slave_state.csv              # 从端运动学数据
│   │   └── interaction_forces.csv        # 交互力数据
│   ├── video/
│   │   ├── left_camera/                 # 左相机图像序列（JPEG）
│   │   │   ├── frame_00000.jpg
│   │   │   └── ...
│   │   └── right_camera/                # 右相机图像序列（JPEG）
│   │       ├── frame_00000.jpg
│   │       └── ...
│   └── annotations/
│       ├── phases.json                  # 手术相位标注
│       ├── gestures.csv                 # 手势标注序列
│       └── events.json                  # 事件标记
├── episode_00002/
│   └── ...
└── dataset_statistics.json               # 数据集统计信息
```

---

## 4. 任务类型详解

### 4.1 手术操作

手术操作是 MIMIC 数据集的核心任务，涵盖了外科手术中最常见的技能单元：

**抓取操作（Grasping）**
- 精确抓取手术器械或模拟组织
- 要求器械姿态与目标物体几何特征匹配
- 力反馈信息帮助判断抓取是否牢固

**切割操作（Cutting）**
- 使用超声刀或剪刀进行组织切割
- 需要沿预定路径精确控制刀具方向和深度
- 切割速度影响组织愈合效果

**缝合操作（Suturing）**
- 进行组织的精确缝合
- 包括穿针、引线、打结等子动作
- 是手术技能评估中最关键的指标之一

**解剖分离（Dissection）**
- 在不同组织层之间进行精确分离
- 需要识别组织边界并沿正确层面操作
- 避免对血管和神经的损伤

### 4.2 器械控制

MIMIC 数据集中包含了对手术器械的精细控制任务：

**主-从同步控制**
- 研究主端操作与从端执行的对应关系
- 分析运动缩放系数对操作精度的影响
- 评估系统的延迟和跟随误差

**夹爪力控制**
- 记录不同操作中夹爪的开闭模式
- 分析力反馈数据与操作质量的关系
- 研究自适应夹爪力控制策略

**多器械协同**
- 双手协调操作（左右机械臂同时工作）
- 器械之间的配合与避碰
- 工具更换的时序优化

### 4.3 相位识别

相位识别是 MIMIC 数据集的特色任务，旨在从传感器数据中自动识别当前所处的手术阶段：

**基于运动学的相位识别**
- 利用关节角度/速度序列判断手术阶段
- 不同的手术阶段具有不同的运动模式
- 可用于手术流程的实时监控

**基于视觉的相位识别**
- 利用手术视频识别当前操作类型
- 结合图像和运动学多模态信息
- 可实现手术进度的自动追踪

**预测性相位识别**
- 不仅识别当前阶段，还预测下一阶段
- 为手术机器人的自主决策提供依据
- 是实现手术自动化的关键技术

---

## 5. 使用方法

### 5.1 数据获取

MIMIC 数据集的获取需要经过正式的申请流程：

**申请流程**：

```
1. 访问 MIMIC 官方网站或 GitHub 仓库
   https://mimicdataset.github.io/
   https://github.com/StanfordVAL/MIMIC

2. 阅读数据使用协议（Data Use Agreement）
   - 承诺仅用于学术研究
   - 不得用于商业目的
   - 不得尝试反匿名化

3. 提交申请表格
   - 研究机构信息
   - 研究目的说明
   - 指导教师/负责人签字

4. 等待审批（约 2-4 周）

5. 获批后收到下载链接和凭证
```

**下载方式**：

```bash
# 方式一：使用 gdown 下载 Google Drive 文件
pip install gdown
gdown --fuzzy https://drive.google.com/file/d/XXXXX/view

# 方式二：使用 AWS S3（需 AWS 账号）
aws s3 sync s3://mimic-dataset/release/ ./mimic_data/

# 方式三：使用 wget/curl
wget https://mimicdataset.github.io/data/mimic_surgical.tar.gz

# 验证数据完整性
md5sum -c checksums.txt
```

### 5.2 预处理

MIMIC 数据需要经过系统性预处理才能用于深度学习训练：

```python
import json
import numpy as np
import pandas as pd
import cv2
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from scipy.interpolate import interp1d

class MIMICPreprocessor:
    """
    MIMIC 数据预处理器
    
    功能：
    - 加载多模态数据（运动学、视频、标注）
    - 运动学数据清洗和重采样
    - 视频数据解码和预处理
    - 归一化处理
    """
    
    def __init__(self, data_root: str):
        """初始化预处理器"""
        self.data_root = Path(data_root)
        self.sample_rate = 100  # 运动学采样率（Hz）
        self.video_rate = 30    # 视频帧率（Hz）
    
    def load_kinematics(self, episode_path: Path) -> Dict[str, np.ndarray]:
        """
        加载运动学数据
        
        参数:
            episode_path: episode 目录路径
        
        返回:
            包含主端和从端运动数据的字典
        """
        # 加载主端数据
        master_file = episode_path / "kinematics" / "master_state.csv"
        master_df = pd.read_csv(master_file)
        
        # 加载从端数据
        slave_file = episode_path / "kinematics" / "slave_state.csv"
        slave_df = pd.read_csv(slave_file)
        
        # 解析关节角度序列（6个关节）
        master_joints = master_df[[f"joint_{i}" for i in range(6)]].values
        slave_joints = slave_df[[f"joint_{i}" for i in range(6)]].values
        
        # 解析末端位姿（位置 + 四元数，共7维）
        master_pose = master_df[["ee_x", "ee_y", "ee_z", "ee_qx", "ee_qy", "ee_qz", "ee_qw"]].values
        slave_pose = slave_df[["ee_x", "ee_y", "ee_z", "ee_qx", "ee_qy", "ee_qz", "ee_qw"]].values
        
        # 解析夹爪状态
        master_gripper = master_df["gripper_position"].values
        slave_jaw = slave_df["jaw_position"].values
        
        # 加载交互力
        force_file = episode_path / "kinematics" / "interaction_forces.csv"
        force_df = pd.read_csv(force_file)
        forces = force_df[["fx", "fy", "fz"]].values
        torques = force_df[["tx", "ty", "tz"]].values
        
        # 提取时间戳
        timestamps = master_df["timestamp"].values
        
        return {
            "timestamps": timestamps,
            "master_joints": master_joints.astype(np.float32),
            "slave_joints": slave_joints.astype(np.float32),
            "master_pose": master_pose.astype(np.float32),
            "slave_pose": slave_pose.astype(np.float32),
            "master_gripper": master_gripper.astype(np.float32),
            "slave_jaw": slave_jaw.astype(np.float32),
            "forces": forces.astype(np.float32),
            "torques": torques.astype(np.float32)
        }
    
    def load_annotations(self, episode_path: Path) -> Dict:
        """
        加载相位和手势标注
        
        参数:
            episode_path: episode 目录路径
        
        返回:
            标注字典
        """
        # 加载相位标注
        phase_file = episode_path / "annotations" / "phases.json"
        with open(phase_file, 'r') as f:
            phases = json.load(f)
        
        # 加载手势标注
        gesture_file = episode_path / "annotations" / "gestures.csv"
        gesture_df = pd.read_csv(gesture_file)
        gestures = gesture_df[["frame", "gesture"]].values
        
        # 加载事件标记
        event_file = episode_path / "annotations" / "events.json"
        with open(event_file, 'r') as f:
            events = json.load(f)
        
        return {
            "phases": phases,
            "gestures": gestures,
            "events": events
        }
    
    def resample_to_uniform_rate(
        self, 
        data: np.ndarray, 
        original_rate: float, 
        target_rate: float
    ) -> np.ndarray:
        """
        将数据重采样到目标采样率
        
        参数:
            data: 原始数据 (T, D)
            original_rate: 原始采样率（Hz）
            target_rate: 目标采样率（Hz）
        
        返回:
            重采样后的数据
        """
        T, D = data.shape
        original_time = np.arange(T) / original_rate
        target_time = np.arange(int(T * target_rate / original_rate)) / target_rate
        
        resampled = np.zeros((len(target_time), D))
        
        for d in range(D):
            interp_func = interp1d(
                original_time, data[:, d], 
                kind='linear', fill_value='extrapolate'
            )
            resampled[:, d] = interp_func(target_time)
        
        return resampled
    
    def preprocess_kinematics(self, kinematics: Dict) -> Dict:
        """
        预处理运动学数据
        
        包括：
        - 重采样到统一采样率（10 Hz）
        - 去除异常值
        - 计算派生量（速度、加速度）
        """
        target_rate = 10.0  # 重采样到 10 Hz（便于与视频对齐）
        
        processed = {}
        for key, value in kinematics.items():
            if isinstance(value, np.ndarray) and value.ndim == 1:
                processed[key] = self.resample_to_uniform_rate(
                    value.reshape(-1, 1), self.sample_rate, target_rate
                ).flatten()
            elif isinstance(value, np.ndarray) and value.ndim == 2:
                processed[key] = self.resample_to_uniform_rate(
                    value, self.sample_rate, target_rate
                )
        
        # 计算末端执行器速度
        slave_pose_pos = processed["slave_pose"][:, :3]  # 只取位置
        velocities = np.diff(slave_pose_pos, axis=0) * target_rate
        velocities = np.vstack([velocities, velocities[-1]])  # 补齐最后一帧
        processed["slave_velocity"] = velocities
        
        # 计算夹爪开闭速度
        jaw_diff = np.diff(processed["slave_jaw"])
        jaw_diff = np.hstack([jaw_diff, jaw_diff[-1]])
        processed["jaw_velocity"] = jaw_diff * target_rate
        
        return processed
    
    def compute_normalization_stats(self, episodes: List[Path]) -> Dict:
        """
        计算数据集的归一化参数
        
        从多个 episode 中采样，计算均值和标准差
        """
        all_master_joints = []
        all_slave_joints = []
        all_actions = []
        
        sample_size = min(50, len(episodes))
        sampled_eps = np.random.choice(len(episodes), sample_size, replace=False)
        
        for idx in sampled_eps:
            try:
                kinematics = self.load_kinematics(episodes[idx])
                kinematics = self.preprocess_kinematics(kinematics)
                
                # 主端动作 = 主端位置增量
                master_delta = np.diff(kinematics["master_pose"][:, :3], axis=0)
                master_delta = np.vstack([master_delta, master_delta[-1]])
                
                all_master_joints.append(kinematics["master_joints"])
                all_slave_joints.append(kinematics["slave_joints"])
                all_actions.append(master_delta)
            except Exception:
                continue
        
        if all_master_joints:
            all_master_joints = np.concatenate(all_master_joints, axis=0)
            all_slave_joints = np.concatenate(all_slave_joints, axis=0)
            all_actions = np.concatenate(all_actions, axis=0)
            
            stats = {
                "master_joints_mean": all_master_joints.mean(axis=0),
                "master_joints_std": all_master_joints.std(axis=0) + 1e-7,
                "slave_joints_mean": all_slave_joints.mean(axis=0),
                "slave_joints_std": all_slave_joints.std(axis=0) + 1e-7,
                "actions_mean": all_actions.mean(axis=0),
                "actions_std": all_actions.std(axis=0) + 1e-7,
            }
            return stats
        
        return None
```

### 5.3 伦理审批

使用 MIMIC 数据集进行研究需要遵守严格的伦理规范：

**IRB 审批要求**：

- **纯算法研究**（如相位识别、动作预测）：通常需要 IRB 豁免，因为数据已完全匿名化
- **涉及人类受试者的研究**：需要完整的 IRB 审批流程
- **临床应用研究**：需要更严格的审批和监管

**数据使用协议（DUA）主要条款**：

```
1. 使用范围
   - 仅用于非商业性学术研究
   - 不得向第三方转让数据
   - 不得尝试识别外科医生或患者身份

2. 引用要求
   - 发表论文时必须正确引用 MIMIC 数据集论文

3. 数据安全
   - 数据存储在安全设施中
   - 访问需要权限控制
   - 不得在公共服务器存储数据

4. 成果共享
   - 欢迎提交代码和改进到官方仓库
   - 训练模型权重可选择性共享
## 6. 代码实战

### 6.1 数据加载器实现

下面实现一个完整的 MIMIC 数据加载器：

```python
import json
import numpy as np
import torch
import pandas as pd
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class MIMICDataset(Dataset):
    """
    MIMIC 数据集加载器
    
    支持：
    - 多模态数据加载（运动学 + 视频）
    - 手术相位过滤
    - 数据归一化
    - 序列采样
    """
    
    # 手术相位 ID 映射（JIGSAWS 标准）
    PHASE_MAP = {
        "Idle": 0, "Reaching": 1, "Grasping": 2, "Retracting": 3,
        "Orientation": 4, "Translating": 5, "Releasing": 6,
        "Suturing": 7, "Cutting": 8
    }
    
    def __init__(
        self,
        data_root: str,
        phases: Optional[List[str]] = None,
        tasks: Optional[List[str]] = None,
        seq_length: int = 16,
        image_size: Tuple[int, int] = (224, 224),
        load_video: bool = False,
        normalize: bool = True,
        stats_path: Optional[str] = None,
        camera: str = "left_camera"
    ):
        self.data_root = Path(data_root)
        self.phases = phases
        self.tasks = tasks
        self.seq_length = seq_length
        self.image_size = image_size
        self.load_video = load_video
        self.normalize = normalize
        self.camera = camera
        
        self.episodes: List[Dict] = []
        self._scan_episodes()
        
        if stats_path and Path(stats_path).exists():
            self._load_stats(stats_path)
        else:
            self._compute_stats()
    
    def _scan_episodes(self):
        """扫描所有有效的 episode 并按条件过滤"""
        for ep_dir in sorted(self.data_root.iterdir()):
            if not ep_dir.name.startswith("episode_"):
                continue
            
            meta_file = ep_dir / "metadata.json"
            if not meta_file.exists():
                continue
            
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            
            task_name = meta.get("task_name", "unknown")
            if self.tasks and task_name not in self.tasks:
                continue
            
            if self.phases:
                phase_file = ep_dir / "annotations" / "phases.json"
                if phase_file.exists():
                    with open(phase_file, 'r') as f:
                        phases = json.load(f)
                    phase_names = set(p["phase_name"] for p in phases)
                    if not any(p in phase_names for p in self.phases):
                        continue
            
            self.episodes.append({
                "path": ep_dir,
                "meta": meta,
                "task_name": task_name,
                "surgeon_id": meta.get("surgeon_id", "unknown"),
                "skill_level": meta.get("skill_level", 0),
                "difficulty": meta.get("difficulty", "unknown")
            })
        
        print(f"加载了 {len(self.episodes)} 个有效 episode")
    
    def _load_stats(self, stats_path: str):
        """从文件加载归一化参数"""
        stats = np.load(stats_path)
        self.state_mean = torch.FloatTensor(stats["state_mean"])
        self.state_std = torch.FloatTensor(stats["state_std"])
        self.action_mean = torch.FloatTensor(stats["action_mean"])
        self.action_std = torch.FloatTensor(stats["action_std"])
    
    def _compute_stats(self):
        """计算归一化参数（从全部数据中采样）"""
        print("计算归一化参数...")
        
        sample_size = min(100, len(self.episodes))
        sampled_eps = np.random.choice(len(self.episodes), sample_size, replace=False)
        
        all_states = []
        all_actions = []
        
        for idx in sampled_eps:
            try:
                ep = self.episodes[idx]
                kinematics = self._load_kinematics(ep["path"])
                
                state = np.concatenate([
                    kinematics["slave_joints"],
                    kinematics["slave_pose"][:, :3],
                    kinematics["slave_jaw"].reshape(-1, 1)
                ], axis=1).astype(np.float32)
                
                action = np.diff(kinematics["master_pose"][:, :3], axis=0)
                action = np.vstack([action, action[-1]])
                
                all_states.append(state)
                all_actions.append(action.astype(np.float32))
            except Exception:
                continue
        
        if all_states and all_actions:
            all_states = np.concatenate(all_states, axis=0)
            all_actions = np.concatenate(all_actions, axis=0)
            
            self.state_mean = torch.FloatTensor(all_states.mean(axis=0))
            self.state_std = torch.FloatTensor(all_states.std(axis=0) + 1e-7)
            self.action_mean = torch.FloatTensor(all_actions.mean(axis=0))
            self.action_std = torch.FloatTensor(all_actions.std(axis=0) + 1e-7)
        else:
            self.state_mean = torch.zeros(10)
            self.state_std = torch.ones(10)
            self.action_mean = torch.zeros(3)
            self.action_std = torch.ones(3)
    
    def _load_kinematics(self, ep_path: Path) -> Dict:
        """加载单个 episode 的运动学数据"""
        master_df = pd.read_csv(ep_path / "kinematics" / "master_state.csv")
        slave_df = pd.read_csv(ep_path / "kinematics" / "slave_state.csv")
        
        master_joints = master_df[[f"joint_{i}" for i in range(6)]].values
        slave_joints = slave_df[[f"joint_{i}" for i in range(6)]].values
        master_pose = master_df[["ee_x", "ee_y", "ee_z", "ee_qx", "ee_qy", "ee_qz", "ee_qw"]].values
        slave_pose = slave_df[["ee_x", "ee_y", "ee_z", "ee_qx", "ee_qy", "ee_qz", "ee_qw"]].values
        master_gripper = master_df["gripper_position"].values
        slave_jaw = slave_df["jaw_position"].values
        
        return {
            "master_joints": master_joints.astype(np.float32),
            "slave_joints": slave_joints.astype(np.float32),
            "master_pose": master_pose.astype(np.float32),
            "slave_pose": slave_pose.astype(np.float32),
            "master_gripper": master_gripper.astype(np.float32),
            "slave_jaw": slave_jaw.astype(np.float32)
        }
    
    def _load_annotations(self, ep_path: Path) -> Dict:
        """加载单个 episode 的标注数据"""
        phase_file = ep_path / "annotations" / "phases.json"
        phases = json.load(open(phase_file)) if phase_file.exists() else []
        
        gesture_file = ep_path / "annotations" / "gestures.csv"
        if gesture_file.exists():
            gesture_df = pd.read_csv(gesture_file)
            gestures = gesture_df[["frame", "gesture"]].values
        else:
            gestures = np.zeros((0, 2))
        
        return {"phases": phases, "gestures": gestures}
    
    def __len__(self) -> int:
        return len(self.episodes)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """获取一个 episode 的数据"""
        ep = self.episodes[idx]
        
        kinematics = self._load_kinematics(ep["path"])
        annotations = self._load_annotations(ep["path"])
        
        # 构建状态向量：6关节 + 3末端位置 + 1夹爪 = 10维
        state = np.concatenate([
            kinematics["slave_joints"],
            kinematics["slave_pose"][:, :3],
            kinematics["slave_jaw"].reshape(-1, 1)
        ], axis=1).astype(np.float32)
        
        # 动作 = 主端位置增量
        action = np.diff(kinematics["master_pose"][:, :3], axis=0)
        action = np.vstack([action, action[-1]]).astype(np.float32)
        
        state = torch.FloatTensor(state)
        action = torch.FloatTensor(action)
        
        if self.normalize:
            state = (state - self.state_mean) / self.state_std
            action = (action - self.action_mean) / self.action_std
        
        seq_len = min(len(action), self.seq_length)
        state = state[:seq_len]
        action = action[:seq_len]
        
        if annotations["gestures"].size > 0:
            phase_name = annotations["gestures"][0, 1]
            phase_label = self.PHASE_MAP.get(phase_name, 0)
        else:
            phase_label = 0
        
        return {
            "states": state,
            "actions": action,
            "task_name": ep["task_name"],
            "skill_level": torch.tensor(ep["skill_level"], dtype=torch.float),
            "phase_label": torch.tensor(phase_label, dtype=torch.long),
            "surgeon_id": ep["surgeon_id"],
            "difficulty": ep["difficulty"]
        }


def create_mimic_dataloader(
    data_root: str,
    phases: Optional[List[str]] = None,
    tasks: Optional[List[str]] = None,
    batch_size: int = 32,
    shuffle: bool = True,
    num_workers: int = 4,
    seq_length: int = 16
) -> DataLoader:
    """创建 MIMIC 数据加载器"""
    dataset = MIMICDataset(
        data_root=data_root,
        phases=phases,
        tasks=tasks,
        normalize=True,
        seq_length=seq_length
    )
    
    def collate_fn(batch):
        """自定义批次整理函数"""
        max_len = max(item["actions"].shape[0] for item in batch)
        
        padded_states = []
        padded_actions = []
        masks = []
        
        for item in batch:
            seq_len = item["actions"].shape[0]
            pad_len = max_len - seq_len
            
            if pad_len > 0:
                state_pad = torch.zeros(pad_len, item["states"].shape[1])
                action_pad = torch.zeros(pad_len, item["actions"].shape[1])
                mask = torch.cat([torch.ones(seq_len), torch.zeros(pad_len)], dim=0)
                states = torch.cat([item["states"], state_pad], dim=0)
                actions = torch.cat([item["actions"], action_pad], dim=0)
            else:
                states = item["states"]
                actions = item["actions"]
                mask = torch.ones(seq_len)
            
            padded_states.append(states)
            padded_actions.append(actions)
            masks.append(mask)
        
        return {
            "states": torch.stack(padded_states),
            "actions": torch.stack(padded_actions),
            "mask": torch.stack(masks),
            "task_names": [item["task_name"] for item in batch],
            "skill_levels": torch.stack([item["skill_level"] for item in batch]),
            "phase_labels": torch.stack([item["phase_label"] for item in batch])
        }
    
    return DataLoader(
        dataset, batch_size=batch_size, shuffle=shuffle,
        num_workers=num_workers, collate_fn=collate_fn, pin_memory=True
    )
```

### 6.2 轨迹可视化

```python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from typing import List, Dict, Optional

def visualize_mimic_trajectory(kinematics: Dict, save_path: Optional[str] = None):
    """
    可视化单个手术演示轨迹
    
    参数:
        kinematics: 运动学数据字典
        save_path: 保存路径（PNG），None 则不保存
    """
    slave_pos = kinematics["slave_pose"][:, :3]  # (T, 3)
    jaw = kinematics["slave_jaw"]
    
    fig = plt.figure(figsize=(14, 5))
    
    # 3D 末端轨迹
    ax1 = fig.add_subplot(131, projection='3d')
    colors = ['green' if j > 0.5 else 'red' for j in jaw]
    ax1.scatter(slave_pos[:, 0], slave_pos[:, 1], slave_pos[:, 2], c=colors, s=5, alpha=0.6)
    ax1.plot(slave_pos[:, 0], slave_pos[:, 1], slave_pos[:, 2], 'b-', alpha=0.3, linewidth=1)
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_zlabel('Z (m)')
    ax1.set_title('末端执行器 3D 轨迹\n绿=夹爪闭合，红=夹爪张开')
    
    # 位置随时间变化
    ax2 = fig.add_subplot(132)
    time = np.arange(len(slave_pos)) / 10.0
    ax2.plot(time, slave_pos[:, 0], label='X', alpha=0.8)
    ax2.plot(time, slave_pos[:, 1], label='Y', alpha=0.8)
    ax2.plot(time, slave_pos[:, 2], label='Z', alpha=0.8)
    ax2.set_xlabel('时间 (s)')
    ax2.set_ylabel('位置 (m)')
    ax2.set_title('末端执行器位置随时间变化')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 夹爪状态
    ax3 = fig.add_subplot(133)
    ax3.plot(time, jaw, 'g-', linewidth=2)
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('夹爪开度')
    ax3.set_title('夹爪开闭状态随时间变化')
    ax3.set_ylim(-0.05, 1.05)
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"轨迹图已保存: {save_path}")
    plt.show()
    plt.close()


def plot_dataset_statistics(episodes: List[Dict]):
    """绘制数据集统计信息"""
    task_counts = {}
    skill_levels = []
    difficulty_counts = {}
    
    for ep in episodes:
        task = ep.get("task_name", "unknown")
        task_counts[task] = task_counts.get(task, 0) + 1
        
        skill = ep.get("skill_level", 0)
        if skill > 0:
            skill_levels.append(skill)
        
        diff = ep.get("difficulty", "unknown")
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    tasks = list(task_counts.keys())
    axes[0].barh(tasks, list(task_counts.values()))
    axes[0].set_xlabel('Episode 数量')
    axes[0].set_title('各任务 Episode 数量')
    
    if skill_levels:
        axes[1].hist(skill_levels, bins=range(1, 7), edgecolor='black', alpha=0.7)
        axes[1].set_xlabel('技能评分')
        axes[1].set_ylabel('Episode 数量')
        axes[1].set_title(f'技能水平分布\n均值: {np.mean(skill_levels):.2f}')
        axes[1].set_xticks(range(1, 6))
    
    if difficulty_counts:
        axes[2].bar(list(difficulty_counts.keys()), list(difficulty_counts.values()))
        axes[2].set_xlabel('难度等级')
        axes[2].set_ylabel('Episode 数量')
        axes[2].set_title('难度等级分布')
    
    plt.tight_layout()
    plt.savefig('mimic_statistics.png', dpi=150)
    print("统计图已保存: mimic_statistics.png")
    plt.close()
```

### 6.3 训练示例

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
from pathlib import Path

class MIMICBCPolicy(nn.Module):
    """
    基于 MIMIC 的行为克隆策略网络
    
    输入：手术机器人状态（关节角 + 末端位置 + 夹爪）
    输出：主端控制指令（末端位置增量）
    """
    
    def __init__(self, state_dim: int = 10, action_dim: int = 3, hidden_dim: int = 256):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Tanh()
        )
        
        self.action_scale = nn.Parameter(torch.ones(action_dim) * 0.05)
        self.action_bias = nn.Parameter(torch.zeros(action_dim))
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        action = self.network(state)
        return action * self.action_scale + self.action_bias


def train_mimic_bc(
    data_root: str,
    tasks: list = None,
    epochs: int = 50,
    lr: float = 1e-3,
    batch_size: int = 64,
    save_path: str = "mimic_bc_policy.pth"
):
    """
    训练 MIMIC 行为克隆策略
    
    参数:
        data_root: 数据目录
        tasks: 训练任务列表
        epochs: 训练轮数
        lr: 学习率
        batch_size: 批次大小
        save_path: 模型保存路径
    """
    from mimic_dataset import MIMICDataset, create_mimic_dataloader
    
    print("初始化数据集...")
    dataloader = create_mimic_dataloader(
        data_root=data_root,
        tasks=tasks,
        batch_size=batch_size,
        shuffle=True,
        seq_length=16
    )
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"使用设备: {device}")
    
    policy = MIMICBCPolicy(state_dim=10, action_dim=3, hidden_dim=256).to(device)
    optimizer = torch.optim.Adam(policy.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    
    print(f"开始训练，共 {epochs} 个 epochs...")
    best_loss = float('inf')
    
    for epoch in range(epochs):
        policy.train()
        total_loss = 0.0
        num_batches = 0
        
        for batch in dataloader:
            states = batch["states"].to(device)
            actions = batch["actions"].to(device)
            
            # 取最后一帧作为行为克隆的目标
            state_input = states[:, -1, :]
            action_target = actions[:, -1, :]
            
            pred_action = policy(state_input)
            loss = loss_fn(pred_action, action_target)
            
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), max_norm=1.0)
            optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(policy.state_dict(), save_path)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}{'*' if avg_loss < best_loss else ''}")
    
    print(f"\n训练完成！最佳损失: {best_loss:.6f}")
    print(f"模型已保存: {save_path}")
    
    return policy


class PhaseClassifier(nn.Module):
    """
    手术相位分类器
    
    输入：运动学序列
    输出：相位类别概率
    """
    
    def __init__(self, state_dim: int = 10, num_classes: int = 9, hidden_dim: int = 128):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=state_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, num_classes)
        )
    
    def forward(self, states: torch.Tensor, mask: torch.Tensor = None) -> torch.Tensor:
        """前向传播"""
        lstm_out, (h_n, c_n) = self.lstm(states)
        hidden = torch.cat([h_n[-2], h_n[-1]], dim=1)
        logits = self.classifier(hidden)
        return logits


if __name__ == "__main__":
    DATA_ROOT = "./mimic_processed"
    
    # 训练行为克隆策略
    print("=" * 50)
    print("训练行为克隆策略")
    print("=" * 50)
    policy = train_mimic_bc(
        data_root=DATA_ROOT,
        tasks=["suturing", "cutting"],
        epochs=50,
        lr=1e-3,
        batch_size=64
    )
```

---

## 7. 练习题

### 选择题

1. **MIMIC 数据集采集使用的手术机器人平台是？**
   - A. KUKA 机械臂
   - B. UR 协作机器人
   - C. Da Vinci Research Kit (dVRK)
   - D. WidowX 机械臂

2. **MIMIC 数据集中，主端运动学数据的采样率是？**
   - A. 10 Hz
   - B. 30 Hz
   - C. 50 Hz
   - D. 100 Hz

3. **MIMIC 运动学数据中，从端状态不包含以下哪个字段？**
   - A. joint_positions
   - B. cartesian_position
   - C. master_gripper
   - D. jaw_position

4. **MIMIC 采用的手术相位标注体系是？**
   - A. ROS 标准
   - B. JIGSAWS 标准
   - C. ROS-I 标准
   - D. IEC 标准

5. **MIMIC 数据集中的视频数据是以下哪种格式？**
   - A. 连续 MP4 视频
   - B. 左右双目立体图像序列（JPEG）
   - C. 单目 RGB-D 视频
   - D. 深度图序列

### 填空题

6. **MIMIC 动作向量的前 3 维表示 ________，是从端执行器的 ________ 。**

7. **dVRK 平台的主-从运动映射函数中，通常包含 ________ 系数，用于调整操作精度。**

8. **MIMIC 数据集中，外科医生身份全部替换为匿名 ID，这体现了数据的 ________ 处理。**

9. **MIMIC 数据集的文件组织中，`slave_state.csv` 存储的是 ________ 端运动学数据。**

10. **行为克隆策略网络的输入是 ________，输出是 ________（以 MIMIC 为例）。**

### 简答题

11. **简述 Da Vinci 手术系统的三个主要组件及其功能。**

12. **MIMIC 数据集相比 RH20T 和 RoboTurk，在数据采集和应用场景上有什么主要区别？**

13. **说明 MIMIC 中主端-从端运动映射关系及其意义。**

14. **为什么 MIMIC 要采用硬件时间戳同步机制？这对手术机器人研究有什么帮助？**

15. **简述手术相位识别任务的定义及其在手术自动化中的意义。**

### 编程题

16. **编写代码实现按外科医生技能等级过滤 MIMIC episode**：
    - 输入：episode 列表、最低技能等级
    - 输出：过滤后的 episode 列表
    - 要求：技能等级必须大于等于阈值

17. **基于 MIMIC 数据集，实现一个简单的数据增强函数**：
    - 对状态添加高斯噪声（均值为 0，标准差为 0.01）
    - 对动作添加高斯噪声（均值为 0，标准差为 0.005）

18. **实现一个手术技能评估函数**：
    - 输入：一段手术演示的运动学数据
    - 计算以下指标：操作时间、轨迹总长度、夹爪切换次数、轨迹平滑度
    - 输出：综合技能评分（0-100）

---

## 8. 练习题答案

### 选择题

1. **答案：C**
   - MIMIC 数据集使用 Da Vinci Research Kit（dVRK）作为采集平台

2. **答案：D**
   - 主端运动学数据的采样率为 100 Hz

3. **答案：C**
   - `master_gripper` 是主端字段，从端状态包含 `joint_positions`、`cartesian_position` 和 `jaw_position`

4. **答案：B**
   - MIMIC 采用 JIGSAWS（JHU Instrumented Surgical Training Tools）标准手术相位标注体系

5. **答案：B**
   - MIMIC 提供左右双目立体图像序列（JPEG 格式）

### 填空题

6. **答案：末端位置增量、笛卡尔空间**
   - 前 3 维是末端执行器在笛卡尔空间的位置增量（dx, dy, dz）

7. **答案：运动缩放**
   - 通常为 3:1 或 5:1

8. **答案：脱敏（或匿名化）**

9. **答案：从（slave）**

10. **答案：手术机器人状态（10维）、主端控制指令（3维）**

### 简答题

11. **Da Vinci 手术系统的三个主要组件**：
    - **外科医生控制台**：提供 3D 高清立体视觉、力反馈手柄和主操作手
    - **手术床旁机械臂**：4 条可独立操控的机械臂，配备 EndoWrist 灵巧器械
    - **视觉系统**：双目立体相机提供 1080p 高清视频

12. **MIMIC vs RH20T/RoboTurk**：
    | 维度 | MIMIC | RH20T | RoboTurk |
    |------|-------|-------|----------|
    | 应用领域 | 医疗手术 | 日常操作 | 日常操作 |
    | 机器人平台 | Da Vinci (dVRK) | WidowX/KUKA | WidowX |
    | 操作对象 | 模拟组织/真实组织 | 积木、杯子等 | 积木、瓶子等 |
    | 操作精度要求 | 极高（亚毫米级） | 较高 | 较高 |

13. **主端-从端运动映射关系**：
    - 映射函数 $\\mathbf{q}_{slave} = f(\\mathbf{q}_{master})$ 包含运动缩放、姿态映射和安全约束
    - 研究这一关系可以评估系统的响应精度和延迟特性

14. **硬件时间戳同步的意义**：
    - 手术中的视觉信息和力学信息必须在时间上严格对应，才能准确建模专家操作策略
    - 精确的同步是进行手术流程分析、相位识别和多模态学习的基础

15. **手术相位识别的意义**：
    - 自动识别手术的当前阶段，是手术流程监控的基础
    - 为手术机器人的自主决策提供依据，是实现手术自动化的关键技术

### 编程题答案

16. **按技能等级过滤**：

```python
def filter_by_skill_level(episodes: list, min_skill: int) -> list:
    """按外科医生技能等级过滤 episode"""
    filtered = []
    
    for ep in episodes:
        skill_level = ep.get("skill_level", 0)
        if skill_level >= min_skill:
            filtered.append({
                "path": str(ep["path"]),
                "task_name": ep.get("task_name", "unknown"),
                "surgeon_id": ep.get("surgeon_id", "unknown"),
                "skill_level": skill_level
            })
    
    print(f"技能等级 >= {min_skill}: {len(filtered)} / {len(episodes)}")
    return filtered
```

17. **数据增强函数**：

```python
import numpy as np

def augment_trajectory(states, actions, state_std=0.01, action_std=0.005):
    """对 MIMIC 轨迹数据进行增强"""
    T, sd = states.shape
    _, ad = actions.shape
    
    state_noise = np.random.normal(0, state_std, size=(T, sd))
    action_noise = np.random.normal(0, action_std, size=(T, ad))
    
    states_aug = (states + state_noise).astype(np.float32)
    actions_aug = (actions + action_noise).astype(np.float32)
    
    return states_aug, actions_aug
```

18. **手术技能评估函数**：

```python
import numpy as np

def evaluate_surgical_skill(kinematics: dict) -> dict:
    """评估手术操作技能"""
    slave_pos = kinematics["slave_pose"][:, :3]
    jaw = kinematics["slave_jaw"]
    
    # 操作时间
    duration = len(slave_pos) / 10.0
    
    # 轨迹总长度
    diffs = np.diff(slave_pos, axis=0)
    total_length = np.linalg.norm(diffs, axis=1).sum()
    
    # 夹爪切换次数
    jaw_diff = np.abs(np.diff(jaw))
    num_switches = np.sum(jaw_diff > 0.2)
    
    # 轨迹平滑度
    velocities = np.diff(slave_pos, axis=0) * 10.0
    smoothness = np.linalg.norm(velocities, axis=1).std()
    
    # 综合评分（0-100）
    time_score = max(0, 1 - duration / 60) * 100
    length_score = min(total_length / 2.0, 1.0) * 100
    switch_score = max(0, 100 - abs(num_switches - 20) * 5)
    smoothness_score = max(0, 100 - smoothness * 100)
    
    composite = time_score * 0.2 + length_score * 0.2 + switch_score * 0.3 + smoothness_score * 0.3
    
    return {
        "duration_seconds": round(duration, 2),
        "total_length_m": round(total_length, 4),
        "gripper_switches": int(num_switches),
        "smoothness": round(smoothness, 4),
        "composite_score": round(composite, 1),
        "grade": "A" if composite >= 80 else "B" if composite >= 60 else "C" if composite >= 40 else "D"
    }
```

---

## 本章小结

本节课程系统介绍了 MIMIC 手术机器人遥操作数据集：

1. **数据集概述**：MIMIC 是约翰斯·霍普金斯大学等机构发布的最大规模手术机器人遥操作数据集，包含 5,000+ 条演示、15+ 种外科手术类型，涵盖从基础抓取到复杂缝合的全方位操作技能

2. **数据采集系统**：使用 Da Vinci Research Kit（dVRK）开源手术机器人平台，通过硬件时间戳同步机制记录主端（外科医生操作）和从端（机器人执行）的完整运动学数据，并经过严格的隐私脱敏处理

3. **数据格式**：包含 20+ 通道的多模态数据（主/从端运动学、双目立体视频、交互力、事件标注等），以 CSV 和 JSON 格式存储，采用 JIGSAWS 标准手术相位标注体系

4. **任务类型**：覆盖手术操作（抓取、切割、缝合、解剖）、器械控制（主-从同步、夹爪力控制、多器械协同）和相位识别（运动学、视觉、预测性）三大类

5. **使用方法**：需经过正式申请流程获取数据，预处理包括运动学重采样、归一化、异常值过滤等步骤，使用需遵守 IRB 和 DUA 伦理规范

6. **代码实战**：实现了完整的数据加载器（支持多模态、相位过滤、归一化）、轨迹可视化工具（3D 轨迹、时间序列、统计图表）和行为克隆训练脚本，以及基于 LSTM 的手术相位分类器

7. **练习题**：涵盖了 MIMIC 数据集的采集平台、数据格式、任务类型、预处理流程等核心知识点，通过选择题、填空题、简答题和编程题全面检验学习效果

---

**相关资源**：

- MIMIC 官网：https://mimicdataset.github.io/
- GitHub 仓库：https://github.com/StanfordVAL/MIMIC
- dVRK 项目主页：https://research.intersectionsystems.com/dvrk/
- JIGSAWS 数据集：http://cirl.csberkeleykeley.edu/jigsaws/
