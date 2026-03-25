# 15-4 LfdDB 数据集与实践

> **前置课程**：15-1 模仿学习、15-3 GAIL 生成对抗模仿学习
> **后续课程**：15-5 模仿学习项目实战

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：模仿学习的效果高度依赖于演示数据的质量与规模。本节聚焦于 LfdDB（Leveraged Fusion demonstration Database）——一个专为机器人示教学习设计的演示数据集。我们将深入讲解 LfdDB 的数据结构设计、数据采集流程、数据增强策略，以及如何将 LfdDB 与 PyTorch 深度集成，完成从原始数据到训练管线的全流程实践。

---

## 1. LfdDB 概述

### 1.1 什么是 LfdDB

LfdDB（Leveraged Fusion demonstration Database）是一个专为**机器人模仿学习**设计的标准化演示数据库。它整合了多传感器、多任务、多形态机器人的示教数据，提供统一的数据格式与丰富的元信息，支持行为克隆、DAgger、GAIL 等多种模仿学习算法的训练与评估。

LfdDB 的核心设计理念是**"一次采集，多处复用"**——同一条演示轨迹可以同时用于监督学习、强化学习奖励设计、逆向强化学习等不同任务，最大化数据价值。

### 1.2 数据集设计目的

| 设计目标 | 具体实现 |
|---------|---------|
| **统一数据格式** | 定义标准化的状态-动作-轨迹结构，兼容多种机器人平台 |
| **多模态感知融合** | 同步记录 RGB 图像、深度图、力矩、关节角度等多模态信号 |
| **任务多样性** | 覆盖抓取、放置、装配、导航等多种机器人操作任务 |
| **高质量标注** | 提供动作标签、任务描述、成功率等丰富的元数据 |
| **高效读取** | 支持流式加载与内存映射，避免全量加载造成的内存瓶颈 |

### 1.3 数据规模与覆盖

| 维度 | 规模 |
|------|------|
| **总轨迹数** | 5,000+ 条 |
| **任务类型** | 15+ 类（抓取、放置、推拭、装配、导航等） |
| **机器人平台** | 5+ 种（UR5、Franka、Panda、Baxter、TurtleBot） |
| **传感器通道** | RGB、Depth、Force、Torque、Joint State、Action |
| **单条轨迹长度** | 100~2,000 步 |
| **数据总量** | ~50 GB（含原始传感器数据） |

---

## 2. 数据格式

### 2.1 状态-动作对

LfdDB 中的每条记录称为一个**状态-动作对（State-Action Pair）**，定义为：

$$
\mathcal{D}_{sa} = \{(s_i, a_i)\}_{i=1}^N
$$

其中：

- **状态 $s_i$**：包含机器人本体感知与环境感知两部分
- **动作 $a_i$**：可以是末端位置增量、关节角增量、力控制指令等

**状态 $s_i$ 的结构**：

```python
state = {
    "joint_positions":     np.ndarray,  # 关节角度 (D_j,)
    "joint_velocities":   np.ndarray,  # 关节速度 (D_j,)
    "end_effector_pose":  np.ndarray,  # 末端位姿 (7,) = (x,y,z,qx,qy,qz,qw)
    "wrench":             np.ndarray,  # 力矩 (6,) = (fx,fy,fz,tx,ty,tz)
    "rgb_image":          np.ndarray,  # RGB图像 (H,W,3)
    "depth_image":        np.ndarray,  # 深度图 (H,W)
    "timestamp":          float,        # 时间戳（秒）
}
```

**动作 $a_i$ 的结构**：

```python
action = {
    "type":           str,   # "joint_delta" | "ee_delta" | "torque"
    "values":         np.ndarray,  # 动作值
    "gripper_action": float,  # 夹爪开合程度 [0, 1]
}
```

### 2.2 轨迹数据结构

一条完整的**演示轨迹（Trajectory）** 由多个状态-动作对按时间顺序排列组成：

```python
class Trajectory:
    """LfdDB 中的一条完整演示轨迹"""
    def __init__(self):
        self.traj_id: str                    # 轨迹唯一标识
        self.task_name: str                  # 任务名称
        self.robot_type: str                 # 机器人型号
        self.success: bool                   # 任务是否成功完成
        self.num_steps: int                  # 轨迹步数
        self.states: List[State]             # 状态序列
        self.actions: List[Action]            # 动作序列
        self.metadata: TrajectoryMetadata     # 元数据
```

**轨迹元数据（TrajectoryMetadata）**：

```python
class TrajectoryMetadata:
    """轨迹的附加描述信息"""
    experimenter: str      # 采集人员
    date: str              # 采集日期 "YYYY-MM-DD"
    duration: float        # 轨迹总时长（秒）
    task_description: str  # 任务自然语言描述
    success: bool          # 任务是否成功
    failure_reason: str    # 失败原因（若失败）
    environment: str       # 实验环境描述
    tags: List[str]        # 自定义标签，如 ["peg-in-hole", "precision"]
```

### 2.3 元数据定义

LfdDB 使用 **YAML** 文件定义数据集级别的元信息，便于索引与检索：

```yaml
# dataset_meta.yaml
dataset_name: LfdDB-v1.0
version: "1.0"
total_trajectories: 5234
total_size_gb: 48.6
robots:
  - name: UR5
    count: 1800
  - name: Franka
    count: 2100
  - name: Panda
    count: 1334
tasks:
  - name: pick_and_place
    traj_count: 1200
  - name: peg_in_hole
    traj_count: 800
  - name: door_open
    traj_count: 600
  - name: drawer_open
    traj_count: 700
  # ... 更多任务
sensor_config:
  rgb_resolution: [640, 480]
  depth_resolution: [640, 480]
  joint_dim: 7
  frequency: 30  # Hz
```

---

## 3. 数据采集

### 3.1 人类演示采集

LfdDB 支持多种**人类示范采集**方式，以适应不同机器人和任务需求：

| 采集方式 | 设备 | 适用场景 | 精度 |
|---------|------|---------|------|
| **遥操作（Teleoperation）** | 示教器、SpaceMouse、手柄 | 精细操作任务 | 高 |
| **动觉示教（Kinesthetic）** | 直接拖动机器人 | 简单轨迹示教 | 中 |
| **VR/AR 遥操作** | Oculus、HoloLens | 远程示教 | 高 |
| **动作捕捉** | OptiTrack、VICON | 人体运动映射 | 高 |
| **视觉示教** | 单目/双目相机 + 手势识别 | 无接触示教 | 中低 |

**遥操作采集流程**：

```
1. 校准：机器人与遥操作设备手柄坐标系标定
2. 示教：操作员通过手柄控制机器人执行任务
3. 录制：同步记录所有传感器数据与动作指令
4. 标注：后处理添加任务标签与成功/失败标记
5. 清洗：剔除异常片段（如碰撞、超限、数据丢失）
```

### 3.2 传感器配置

LfdDB 推荐的**标准传感器配置**如下：

```python
# 标准传感器配置
SENSOR_CONFIG = {
    # 视觉感知
    "rgb_camera": {
        "resolution": (640, 480),
        "fps": 30,
        "encoding": "bgr8",
        "topic": "/camera/rgb/image_raw",
    },
    "depth_camera": {
        "resolution": (640, 480),
        "fps": 30,
        "encoding": "32FC1",
        "topic": "/camera/depth/image_raw",
    },
    
    # 关节状态
    "joint_states": {
        "topic": "/joint_states",
        "fields": ["position", "velocity", "effort"],
    },
    
    # 力觉感知
    "ft_sensor": {
        "topic": "/ft_sensor/raw",
        "bias_removed": True,
        "rate_limiter_hz": 100,
    },
    
    # 末端感知
    "ee_pose": {
        "topic": "/robot/ee_pose",
        "frame": "tool0",
    },
}

def configure_sensors(robot_type: str) -> dict:
    """根据机器人类型返回适配的传感器配置"""
    configs = {
        "UR5": {"joint_dim": 6, "has_ft_sensor": True, "has_wrist_camera": True},
        "Franka": {"joint_dim": 7, "has_ft_sensor": True, "has_wrist_camera": True},
        "Panda": {"joint_dim": 7, "has_ft_sensor": True, "has_wrist_camera": False},
        "Baxter": {"joint_dim": 7, "has_ft_sensor": False, "has_wrist_camera": False},
    }
    return configs.get(robot_type, configs["UR5"])
```

### 3.3 数据清洗

采集的原始数据需要经过**多级清洗**才能入库：

```python
import numpy as np

class DataCleaner:
    """LfdDB 数据清洗工具"""
    
    def __init__(self):
        self.joint_limits = {
            "UR5": (-np.pi, np.pi),
            "Franka": (-2.9, 2.9),
            "Panda": (-2.9, 2.9),
        }
    
    def remove_outliers(self, trajectory) -> bool:
        """剔除异常轨迹：关节超限、动作突变、数据缺失"""
        for step in range(len(trajectory.states)):
            # 检查关节超限
            joint_pos = trajectory.states[step].joint_positions
            if np.any(np.abs(joint_pos) > np.pi * 1.1):  # 允许10%过载
                trajectory.failure_reason = "joint_limit_exceeded"
                return False
            
            # 检查动作突变（速度不应超过物理限制）
            if step > 0:
                vel = trajectory.states[step].joint_velocities
                if np.any(np.abs(vel) > 5.0):  # 5 rad/s 阈值
                    trajectory.failure_reason = "velocity_surge"
                    return False
        
        return True
    
    def interpolate_missing(self, trajectory) -> None:
        """对短暂的数据缺失进行插值修补"""
        for i, state in enumerate(trajectory.states):
            if state is None:
                # 线性插值
                prev_state = trajectory.states[i - 1]
                next_state = trajectory.states[i + 1]
                trajectory.states[i] = self._linear_interpolate(prev_state, next_state)
    
    def normalize_timestamps(self, trajectory) -> None:
        """将时间戳归一化为从0开始"""
        start_ts = trajectory.states[0].timestamp
        for state in trajectory.states:
            state.timestamp -= start_ts
    
    def validate_trajectory(self, trajectory) -> bool:
        """综合验证轨迹有效性"""
        checks = [
            ("长度", len(trajectory.states) > 10),
            ("状态完整性", all(s is not None for s in trajectory.states)),
            ("动作对齐", len(trajectory.actions) == len(trajectory.states)),
            ("传感器数据", all(s.rgb_image is not None for s in trajectory.states)),
        ]
        return all(check[1] for check in checks)
```

---

## 4. 数据增强

### 4.1 数据增广方法

数据增强是提升模仿学习泛化能力的关键手段。LfdDB 支持以下**多层级数据增广**策略：

| 增广层级 | 方法 | 效果 |
|---------|------|------|
| **状态空间** | 随机噪声、状态扰动、数据平衡 | 增加状态覆盖，防止过拟合 |
| **动作空间** | 噪声注入、动作平滑 | 提高策略鲁棒性 |
| **视觉空间** | 图像增强（颜色、对比度、遮挡） | 增强视觉泛化能力 |
| **时序空间** | 轨迹切片、时序插值 | 增加有效样本量 |

### 4.2 噪声注入

向状态和动作中注入噪声是模仿学习中最常用的增强手段：

```python
import numpy as np

class NoiseInjector:
    """向状态-动作对注入噪声以增强数据多样性"""
    
    def __init__(self, state_noise_std: float = 0.01, action_noise_std: float = 0.02):
        self.state_noise_std = state_noise_std    # 状态噪声标准差
        self.action_noise_std = action_noise_std  # 动作噪声标准差
    
    def add_state_noise(self, state: np.ndarray, 
                        noise_type: str = "gaussian") -> np.ndarray:
        """
        向状态添加噪声
        
        Args:
            state: 原始状态 (D,)
            noise_type: "gaussian" | "uniform" | "salt_pepper"
        
        Returns:
            加噪后的状态
        """
        D = state.shape[0]
        if noise_type == "gaussian":
            noise = np.random.randn(D) * self.state_noise_std
        elif noise_type == "uniform":
            noise = np.random.uniform(-self.state_noise_std, 
                                        self.state_noise_std, D)
        else:  # salt_pepper
            noise = np.zeros(D)
            prob = 0.05
            salt_mask = np.random.rand(D) < prob
            pepper_mask = np.random.rand(D) < prob
            noise[salt_mask] = self.state_noise_std * 3
            noise[pepper_mask] = -self.state_noise_std * 3
        
        return state + noise
    
    def add_action_noise(self, action: np.ndarray,
                         noise_scale: float = 0.1) -> np.ndarray:
        """
        向动作添加噪声，保持动作分布特性
        
        Args:
            action: 原始动作 (D_a,)
            noise_scale: 噪声相对于动作幅值的比例
        
        Returns:
            加噪后的动作
        """
        noise_std = np.abs(action).mean() * noise_scale * self.action_noise_std
        noise = np.random.randn(*action.shape) * noise_std
        noisy_action = action + noise
        
        # 限制动作在合理范围内（防止物理不可行动作）
        return np.clip(noisy_action, -3.0, 3.0)
    
    def augment_trajectory(self, trajectory, noise_prob: float = 0.3):
        """
        对整条轨迹进行噪声增强
        
        Args:
            trajectory: Trajectory 对象
            noise_prob: 每个状态-动作对被增强的概率
        """
        for i in range(len(trajectory.states)):
            if np.random.rand() < noise_prob:
                # 仅对部分数据加噪，避免全部退化
                trajectory.states[i].joint_positions = \
                    self.add_state_noise(trajectory.states[i].joint_positions)
                
                if trajectory.actions[i].type == "joint_delta":
                    trajectory.actions[i].values = \
                        self.add_action_noise(trajectory.actions[i].values)
```

### 4.3 轨迹平滑

采集的示教轨迹往往包含人为抖动，直接用于训练会导致策略学习到抖动的动作。**轨迹平滑**是预处理中不可或缺的步骤：

```python
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter

class TrajectorySmoother:
    """轨迹平滑处理，减小采集噪声"""
    
    def __init__(self, method: str = "gaussian"):
        self.method = method  # "gaussian" | "savgol" | "moving_avg"
    
    def smooth_joint_positions(self, positions: np.ndarray, 
                                window: int = 5) -> np.ndarray:
        """
        对关节位置序列进行平滑
        
        Args:
            positions: 原始关节位置 (T, D_j)
            window: 平滑窗口大小
        
        Returns:
            平滑后的关节位置 (T, D_j)
        """
        T, D = positions.shape
        smoothed = np.zeros_like(positions)
        
        for d in range(D):
            if self.method == "gaussian":
                # 高斯滤波，sigma越大越平滑
                smoothed[:, d] = gaussian_filter1d(positions[:, d], sigma=window//2)
            elif self.method == "savgol":
                # Savitzky-Golay 滤波，保持边缘同时平滑
                if window > D:
                    window = D if D % 2 == 1 else D - 1
                smoothed[:, d] = savgol_filter(positions[:, d], window, 3)
            elif self.method == "moving_avg":
                # 移动平均
                kernel = np.ones(window) / window
                smoothed[:, d] = np.convolve(positions[:, d], kernel, mode='same')
        
        return smoothed
    
    def smooth_actions(self, actions: np.ndarray) -> np.ndarray:
        """
        对动作序列进行平滑，避免动作突变
        
        Args:
            actions: 原始动作序列 (T, D_a)
        
        Returns:
            平滑后的动作序列
        """
        # 高斯滤波
        sigma = 2.0
        smoothed = gaussian_filter1d(actions, sigma=sigma, axis=0)
        return smoothed
    
    def smooth_full_trajectory(self, trajectory) -> None:
        """对整条轨迹进行全方位平滑"""
        # 提取所有关节位置 (T, D_j)
        all_joints = np.array([s.joint_positions for s in trajectory.states])
        # 提取所有末端位置 (T, 3)
        all_ee = np.array([s.end_effector_pose[:3] for s in trajectory.states])
        # 提取所有动作
        all_actions = np.array([a.values for a in trajectory.actions])
        
        # 平滑
        smoothed_joints = self.smooth_joint_positions(all_joints)
        smoothed_ee = self.smooth_joint_positions(all_ee)
        smoothed_actions = self.smooth_actions(all_actions)
        
        # 回填
        for i, state in enumerate(trajectory.states):
            state.joint_positions = smoothed_joints[i]
            state.end_effector_pose[:3] = smoothed_ee[i]
        
        for i, action in enumerate(trajectory.actions):
            action.values = smoothed_actions[i]
```

---

## 5. 与深度学习框架集成

### 5.1 PyTorch Dataset

将 LfdDB 封装为 `torch.utils.data.Dataset`，实现与 PyTorch 训练管线的无缝对接：

```python
import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from typing import Tuple, Optional, List

class LfdDBDataset(Dataset):
    """
    LfdDB PyTorch Dataset 实现
    
    支持状态/动作的在线变换、缓存与多进程加载
    """
    
    def __init__(self, 
                 data_root: str,
                 trajectories: List[Trajectory],
                 state_keys: List[str] = None,
                 action_dim: int = 7,
                 transform=None,
                 normalize: bool = True):
        """
        Args:
            data_root: LfdDB 数据根目录
            trajectories: Trajectory 对象列表
            state_keys: 要使用的状态字段列表（None 表示全部使用）
            action_dim: 动作维度
            transform: 可选的在线变换函数
            normalize: 是否对状态/动作进行标准化
        """
        self.data_root = data_root
        self.trajectories = trajectories
        self.state_keys = state_keys or ["joint_positions", "end_effector_pose"]
        self.action_dim = action_dim
        self.transform = transform
        self.normalize = normalize
        
        # 构建索引表：(traj_idx, step_idx) -> 全局索引
        self.index_map = []
        for traj_idx, traj in enumerate(trajectories):
            for step_idx in range(len(traj.states)):
                self.index_map.append((traj_idx, step_idx))
        
        # 计算归一化参数（从所有轨迹统计）
        if normalize:
            self._compute_normalization_params()
    
    def _compute_normalization_params(self):
        """统计所有状态/动作的均值与标准差，用于归一化"""
        all_states = []
        all_actions = []
        
        for traj in self.trajectories:
            for state in traj.states:
                state_vec = self._flatten_state(state)
                all_states.append(state_vec)
            for action in traj.actions:
                all_actions.append(action.values)
        
        all_states = np.array(all_states)
        all_actions = np.array(all_actions)
        
        # 计算均值和标准差（防止除零）
        self.state_mean = all_states.mean(axis=0)
        self.state_std = all_states.std(axis=0) + 1e-8
        self.action_mean = all_actions.mean(axis=0)
        self.action_std = all_actions.std(axis=0) + 1e-8
    
    def _flatten_state(self, state: State) -> np.ndarray:
        """将状态对象展平为向量"""
        parts = []
        for key in self.state_keys:
            val = getattr(state, key)
            if isinstance(val, np.ndarray):
                parts.append(val.flatten())
        return np.concatenate(parts)
    
    def __len__(self) -> int:
        return len(self.index_map)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """返回单个状态-动作对"""
        traj_idx, step_idx = self.index_map[idx]
        traj = self.trajectories[traj_idx]
        
        state = traj.states[step_idx]
        action = traj.actions[step_idx]
        
        # 展平并转为张量
        state_vec = self._flatten_state(state)
        action_vec = action.values
        
        # 归一化
        if self.normalize:
            state_vec = (state_vec - self.state_mean) / self.state_std
            action_vec = (action_vec - self.action_mean) / self.action_std
        
        # 在线变换
        if self.transform:
            state_vec, action_vec = self.transform(state_vec, action_vec)
        
        return (
            torch.FloatTensor(state_vec),
            torch.FloatTensor(action_vec)
        )
```

### 5.2 DataLoader 配置

DataLoader 的配置直接影响训练效率与泛化效果：

```python
def create_dataloader(
    dataset: LfdDBDataset,
    batch_size: int = 64,
    shuffle: bool = True,
    num_workers: int = 4,
    pin_memory: bool = True,
    drop_last: bool = False,
    collate_fn=None,
) -> DataLoader:
    """
    创建 LfdDB 专用 DataLoader
    
    Args:
        dataset: LfdDBDataset 实例
        batch_size: 批大小
        shuffle: 是否打乱
        num_workers: 数据加载进程数
        pin_memory: 加速 GPU 传输
        drop_last: 丢弃最后不完整批次
        collate_fn: 自定义批处理函数
    
    Returns:
        DataLoader 实例
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        drop_last=drop_last,
        collate_fn=collate_fn,
        prefetch_factor=2 if num_workers > 0 else None,
    )
```

### 5.3 批处理

**批处理策略**对模仿学习训练效果有显著影响。LfdDB 支持多种批处理模式：

```python
class TrajectoryBatchSampler:
    """
    按轨迹分组的批采样器
    
    确保同一批次的样本来自不同轨迹，
    避免批次内数据冗余导致过拟合
    """
    
    def __init__(self, trajectories: List[Trajectory], 
                 batch_size: int, 
                 shuffle: bool = True):
        self.traj_lens = [len(traj) for traj in trajectories]
        self.batch_size = batch_size
        self.shuffle = shuffle
        
        # 计算每个轨迹应分配的批次数
        self.traj_batches = [
            max(1, length // batch_size) for length in self.traj_lens
        ]
    
    def __iter__(self):
        """生成批次索引列表"""
        indices = []
        for traj_idx, num_batches in enumerate(self.traj_batches):
            # 将每个轨迹均匀划分为 num_batches 个批次
            step_indices = np.array_split(
                np.arange(self.traj_lens[traj_idx]), 
                num_batches
            )
            for steps in step_indices:
                if len(steps) > 0:
                    indices.append((traj_idx, steps.tolist()))
        
        if self.shuffle:
            np.random.shuffle(indices)
        
        # 生成批次
        batch = []
        for traj_idx, steps in indices:
            batch.append((traj_idx, steps))
            if len(batch) == self.batch_size:
                yield batch
                batch = []
        
        if batch:
            yield batch  # 最后一个不完整批次
    
    def __len__(self):
        return sum(self.traj_batches)


def dynamic_batch_collate(batch: List[Tuple]) -> Tuple:
    """
    动态批次整理函数
    
    处理同一批次中轨迹长度不同的情况
    """
    states, actions = zip(*batch)
    
    # 状态填充到相同长度（用0填充）
    max_len = max(s.shape[0] for s in states)
    padded_states = []
    state_lens = []
    
    for s in states:
        if s.shape[0] < max_len:
            pad = torch.zeros(max_len - s.shape[0], s.shape[1])
            padded = torch.cat([s, pad], dim=0)
        else:
            padded = s
        padded_states.append(padded)
        state_lens.append(s.shape[0])
    
    return (
        torch.stack(padded_states),      # (B, T_max, D_s)
        torch.stack(actions),              # (B, D_a)
        torch.LongTensor(state_lens),      # (B,) 实际长度
    )
```

---

## 6. 代码实战

### 6.1 LfdDB 数据集加载

完整的数据集加载与预处理流程：

```python
import os
import pickle
import numpy as np
import torch
from torch.utils.data import DataLoader

# ===================== 1. 数据加载 =====================

def load_lfddb(data_path: str, task_filter: str = None) -> list:
    """
    从磁盘加载 LfdDB 数据集
    
    Args:
        data_path: 数据根目录
        task_filter: 可选的任务名称过滤（如 "pick_and_place"）
    
    Returns:
        Trajectory 对象列表
    """
    trajectories = []
    metadata_path = os.path.join(data_path, "dataset_meta.yaml")
    
    # 加载元数据
    import yaml
    with open(metadata_path, 'r') as f:
        meta = yaml.safe_load(f)
    
    print(f"加载数据集: {meta['dataset_name']}")
    print(f"总轨迹数: {meta['total_trajectories']}")
    
    # 遍历所有轨迹文件
    traj_dir = os.path.join(data_path, "trajectories")
    for traj_file in sorted(os.listdir(traj_dir)):
        if not traj_file.endswith(".pkl"):
            continue
        
        traj_path = os.path.join(traj_dir, traj_file)
        with open(traj_path, 'rb') as f:
            traj = pickle.load(f)
        
        # 任务过滤
        if task_filter and task_filter not in traj.task_name:
            continue
        
        trajectories.append(traj)
    
    print(f"已加载 {len(trajectories)} 条轨迹（过滤后）")
    return trajectories


# ===================== 2. 数据预处理 =====================

def preprocess_trajectories(trajectories: list, 
                              smooth: bool = True,
                              remove_outliers: bool = True) -> list:
    """
    批量预处理轨迹
    
    Args:
        trajectories: 原始轨迹列表
        smooth: 是否进行轨迹平滑
        remove_outliers: 是否移除异常轨迹
    
    Returns:
        处理后的轨迹列表
    """
    from data_cleaner import DataCleaner
    from trajectory_smoother import TrajectorySmoother
    
    cleaner = DataCleaner()
    smoother = TrajectorySmoother(method="gaussian")
    cleaned_trajs = []
    
    for traj in trajectories:
        # 异常检测
        if remove_outliers and not cleaner.validate_trajectory(traj):
            print(f"跳过异常轨迹: {traj.traj_id} - {traj.failure_reason}")
            continue
        
        # 平滑处理
        if smooth:
            smoother.smooth_full_trajectory(traj)
        
        # 时间戳归一化
        cleaner.normalize_timestamps(traj)
        
        cleaned_trajs.append(traj)
    
    print(f"预处理完成: {len(cleaned_trajs)}/{len(trajectories)} 条有效轨迹")
    return cleaned_trajs


# ===================== 3. 数据增强 =====================

def augment_dataset(trajectories: list, 
                    noise_prob: float = 0.3,
                    num_augmented: int = 3) -> list:
    """
    对数据集进行增强
    
    Args:
        trajectories: 原始轨迹列表
        noise_prob: 每条轨迹加噪的概率
        num_augmented: 每条原始轨迹生成的增强副本数量
    
    Returns:
        增强后的轨迹列表
    """
    from noise_injector import NoiseInjector
    import copy
    
    injector = NoiseInjector(state_noise_std=0.01, action_noise_std=0.02)
    augmented = []
    
    for traj in trajectories:
        # 保留原始轨迹
        augmented.append(traj)
        
        # 生成增强副本
        for _ in range(num_augmented):
            aug_traj = copy.deepcopy(traj)
            injector.augment_trajectory(aug_traj, noise_prob)
            aug_traj.traj_id = f"{traj.traj_id}_aug_{_}"
            augmented.append(aug_traj)
    
    print(f"数据增强完成: {len(augmented)} 条轨迹（原始 {len(trajectories)} + 增强 {len(augmented)-len(trajectories)}）")
    return augmented
```

### 6.2 训练集成示例

将 LfdDB 与行为克隆训练流程整合的完整示例：

```python
import torch
import torch.nn as nn
import torch.optim as optim

# ===================== 1. 定义策略网络 =====================

class ImitationPolicy(nn.Module):
    """
    模仿学习策略网络
    
    输入：状态向量
    输出：动作向量（连续控制）
    """
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 256):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Tanh()  # 动作输出归一化到 [-1, 1]
        )
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        Args:
            state: (B, state_dim) 或 (state_dim,)
        
        Returns:
            action: (B, action_dim) 或 (action_dim,)
        """
        return self.network(state)


# ===================== 2. 行为克隆训练 =====================

def train_behavior_cloning(dataset: LfdDBDataset,
                           policy: ImitationPolicy,
                           num_epochs: int = 100,
                           batch_size: int = 64,
                           lr: float = 1e-3,
                           device: str = "cuda" if torch.cuda.is_available() else "cpu"):
    """
    行为克隆训练主循环
    
    Args:
        dataset: LfdDBDataset 实例
        policy: 策略网络
        num_epochs: 训练轮数
        batch_size: 批大小
        lr: 学习率
        device: 计算设备
    """
    policy = policy.to(device)
    
    dataloader = create_dataloader(
        dataset, 
        batch_size=batch_size, 
        shuffle=True, 
        num_workers=4
    )
    
    optimizer = optim.Adam(policy.parameters(), lr=lr)
    criterion = nn.MSELoss()  # 均方误差损失
    
    print(f"开始训练，设备: {device}")
    print(f"数据集大小: {len(dataset)}, 批次数: {len(dataloader)}")
    
    for epoch in range(num_epochs):
        epoch_loss = 0.0
        num_batches = 0
        
        for batch_states, batch_actions in dataloader:
            # 移动到设备
            batch_states = batch_states.to(device)
            batch_actions = batch_actions.to(device)
            
            # 前向传播
            pred_actions = policy(batch_states)
            
            # 计算损失
            loss = criterion(pred_actions, batch_actions)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy.parameters(), max_norm=1.0)
            optimizer.step()
            
            epoch_loss += loss.item()
            num_batches += 1
        
        avg_loss = epoch_loss / num_batches
        print(f"Epoch {epoch+1:3d}/{num_epochs} | Loss: {avg_loss:.6f}")
    
    return policy


# ===================== 3. 主训练流程 =====================

def main():
    """完整训练流程示例"""
    
    # Step 1: 加载数据
    data_root = "./data/lfddb"
    trajectories = load_lfddb(data_root, task_filter="pick_and_place")
    
    # Step 2: 预处理
    trajectories = preprocess_trajectories(
        trajectories, smooth=True, remove_outliers=True
    )
    
    # Step 3: 数据增强
    trajectories = augment_dataset(trajectories, noise_prob=0.3, num_augmented=2)
    
    # Step 4: 构建 Dataset
    dataset = LfdDBDataset(
        data_root=data_root,
        trajectories=trajectories,
        state_keys=["joint_positions", "end_effector_pose"],
        normalize=True
    )
    
    # Step 5: 创建策略网络
    state_dim = dataset.state_mean.shape[0]
    action_dim = 7  # 假设7自由度机械臂
    policy = ImitationPolicy(state_dim=state_dim, action_dim=action_dim)
    
    # Step 6: 训练
    trained_policy = train_behavior_cloning(
        dataset=dataset,
        policy=policy,
        num_epochs=100,
        batch_size=64,
        lr=1e-3
    )
    
    # Step 7: 保存模型
    torch.save(trained_policy.state_dict(), "./checkpoints/bc_policy.pth")
    print("模型已保存至 ./checkpoints/bc_policy.pth")


if __name__ == "__main__":
    main()
```

---

## 7. 练习题

### 7.1 选择题

1. **LfdDB 的核心设计理念是什么？**
   - A. 收集最多的数据
   - B. 一次采集，多处复用
   - C. 只存储图像数据
   - D. 仅支持单一机器人平台

2. **在 LfdDB 中，一条轨迹的状态-动作对用哪个符号表示？**
   - A. $\mathcal{D} = \{s_i, a_i\}$
   - B. $\mathcal{D}_{sa} = \{(s_i, a_i)\}_{i=1}^N$
   - C. $\mathcal{D} = \sum_{i=1}^N s_i + a_i$
   - D. $\mathcal{D} = [s_1, a_1, s_2, a_2, ...]$

3. **轨迹平滑中，高斯滤波的 sigma 参数越大，平滑效果如何？**
   - A. 越弱
   - B. 越强
   - C. 无影响
   - D. 先强后弱

4. **在 PyTorch DataLoader 中，`pin_memory=True` 的主要作用是什么？**
   - A. 防止数据丢失
   - B. 加速 CPU 到 GPU 的数据传输
   - C. 增加数据批次大小
   - D. 启用数据增强

5. **数据增强时，为什么不应对所有数据都注入噪声？**
   - A. 噪声注入太慢
   - B. 保留部分原始数据有助于防止策略退化
   - C. 噪声注入会改变数据格式
   - D. 原始数据不需要保留

### 7.2 简答题

1. 简述 LfdDB 数据集中 `1. 简述 LfdDB 数据集中 `State` 对象包含哪些主要字段，并说明各字段的数据类型与物理意义。

2. 为什么在数据预处理中要进行轨迹平滑？列举两种平滑方法并说明其特点。

3. 解释 PyTorch DataLoader 中 `num_workers` 参数的作用，以及设置过大可能带来的问题。

4. 在数据增强中，噪声注入的 `noise_prob` 参数为什么通常设置为 0.3 而不是 1.0？

### 7.3 编程题

1. 编写一个函数 `compute_trajectory_stats(trajectories)`，统计给定轨迹列表的：
   - 总步数、平均轨迹长度
   - 成功率
   - 各任务类型的轨迹数量

2. 基于 `LfdDBDataset`，编写一个带**在线数据增强**的数据集类 `AugmentedLfdDBDataset`，在 `__getitem__` 中实时进行随机噪声注入和状态归一化。

3. 实现一个简单的 `Evaluator` 类，接收训练好的策略网络与验证数据集，计算策略在验证集上的均方根误差（RMSE）与任务成功率。

---

## 8. 答案

### 8.1 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | LfdDB 核心设计理念是"一次采集，多处复用"，同一条轨迹可服务于监督学习、强化学习、IRL 等多种任务，最大化数据价值。 |
| 2 | **B** | 标准的状态-动作对集合记作 $\mathcal{D}_{sa} = \{(s_i, a_i)\}_{i=1}^N$，表示 $N$ 个配对样本的集合。 |
| 3 | **B** | 高斯滤波中 sigma 越大，高斯核越宽，平滑效果越强，但可能导致细节丢失。 |
| 4 | **B** | `pin_memory=True` 将数据锁定在页锁定内存中，CPU→GPU 传输时无需额外拷贝，显著加速数据传输。 |
| 5 | **B** | 保留部分原始数据作为参照，可防止噪声过度注入导致策略学习到模糊甚至错误的映射关系。 |

### 8.2 简答题答案

**1. State 对象主要字段：**

```python
state = {
    "joint_positions":     np.ndarray,  # (D_j,) 关节角度（弧度）
    "joint_velocities":   np.ndarray,  # (D_j,) 关节角速度（弧度/秒）
    "end_effector_pose":  np.ndarray,  # (7,) 末端位姿 [x,y,z,qx,qy,qz,qw]
    "wrench":             np.ndarray,  # (6,) 力/力矩 [fx,fy,fz,tx,ty,tz]
    "rgb_image":          np.ndarray,  # (H,W,3) RGB图像
    "depth_image":        np.ndarray,  # (H,W) 深度图
    "timestamp":          float,        # 时间戳（秒）
}
```

**2. 轨迹平滑的原因与常用方法：**

人类示教中不可避免地包含手部抖动和动作过度修正，直接使用会导致策略学习到抖动动作，平滑可有效减少高频噪声。两种常用方法：

| 方法 | 原理 | 特点 |
|------|------|------|
| **高斯滤波** | 加权平均，权重服从高斯分布 | 平滑效果好，但会模糊边缘 |
| **Savitzky-Golay 滤波** | 用多项式拟合局部窗口数据 | 保持边缘和峰谷，适合变加速运动 |

**3. `num_workers` 的作用与风险：**

`num_workers` 控制 DataLoader 使用多少个子进程并行加载数据。适当增大可加速数据读取，但过大会导致：进程创建开销超过数据加载收益、内存竞争、调试困难。建议从 4 开始调参，结合 `prefetch_factor` 优化。

**4. `noise_prob` 设为 0.3 的原因：**

设为 1.0 意味着所有样本都被噪声注入，策略在训练时只见过加噪数据，原分布信息被完全覆盖。设为 0.3 使得部分样本保持原始高质量信号，让策略在两种分布上都能学习，提升鲁棒性与泛化能力。

### 8.3 编程题答案

**编程题 1：轨迹统计**

```python
def compute_trajectory_stats(trajectories):
    """统计轨迹数据集的各项指标"""
    total_steps = sum(len(traj.states) for traj in trajectories)
    avg_len = total_steps / len(trajectories)
    success_count = sum(1 for traj in trajectories if traj.success)
    success_rate = success_count / len(trajectories)
    
    # 任务类型统计
    task_counts = {}
    for traj in trajectories:
        task_counts[traj.task_name] = task_counts.get(traj.task_name, 0) + 1
    
    print(f"总轨迹数: {len(trajectories)}")
    print(f"总步数: {total_steps}")
    print(f"平均轨迹长度: {avg_len:.1f}")
    print(f"成功率: {success_rate:.2%}")
    print(f"任务分布: {task_counts}")
    
    return {
        "total_trajectories": len(trajectories),
        "total_steps": total_steps,
        "avg_length": avg_len,
        "success_rate": success_rate,
        "task_counts": task_counts,
    }
```

**编程题 2：在线增强数据集**

```python
class AugmentedLfdDBDataset(LfdDBDataset):
    """支持在线数据增强的 LfdDB Dataset"""
    
    def __init__(self, *args, 
                 noise_prob: float = 0.3,
                 noise_std: float = 0.01,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.noise_prob = noise_prob
        self.noise_std = noise_std
    
    def __getitem__(self, idx):
        state_vec, action_vec = super().__getitem__(idx)
        
        # 在线噪声注入（以一定概率）
        if np.random.rand() < self.noise_prob:
            noise = torch.randn_like(state_vec) * self.noise_std
            state_vec = state_vec + noise
        
        return state_vec, action_vec
```

**编程题 3：Evaluator 类**

```python
class Evaluator:
    """策略评估器，计算验证集上的性能指标"""
    
    def __init__(self, policy: nn.Module, device: str = "cpu"):
        self.policy = policy.to(device)
        self.device = device
    
    def compute_rmse(self, dataloader) -> float:
        """计算均方根误差"""
        self.policy.eval()
        total_mse = 0.0
        num_samples = 0
        
        with torch.no_grad():
            for states, actions in dataloader:
                states = states.to(self.device)
                actions = actions.to(self.device)
                
                pred_actions = self.policy(states)
                mse = ((pred_actions - actions) ** 2).mean().item()
                total_mse += mse * len(states)
                num_samples += len(states)
        
        rmse = np.sqrt(total_mse / num_samples)
        return rmse
    
    def evaluate_success_rate(self, trajectories: list, env, num_episodes: int = 100) -> float:
        """在仿真环境中评估任务成功率"""
        success = 0
        for _ in range(num_episodes):
            traj = np.random.choice(trajectories)
            obs = env.reset()
            
            for step in range(len(traj.states)):
                state = torch.FloatTensor(traj.states[step].joint_positions).to(self.device)
                with torch.no_grad():
                    action = self.policy(state.unsqueeze(0)).cpu().numpy()[0]
                obs, reward, done, info = env.step(action)
                if done:
                    break
            
            success += int(info.get("success", False))
        
        return success / num_episodes
```
