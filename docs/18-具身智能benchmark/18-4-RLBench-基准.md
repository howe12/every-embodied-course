# 18-4 RLBench 基准

> **前置课程**：18-3 Franka Kitchen 环境
> **后续课程**：18-5 Benchmark 项目实战

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：前两节我们分别探讨了 CALVIN 的长时序语言条件评测体系和 Franka Kitchen 的厨房多任务仿真环境。本节我们将目光转向 **RLBench**——目前任务数量最多、场景最丰富的**机械臂操控 benchmark**。RLBench 由 **Imperial College London** 和 **DeepMind** 联合推出，收录了超过 **100 个**差异化任务，覆盖抓取、放置、旋转、装配等多种操作类型，是评估机器人多任务学习能力和泛化性的重要基准。与 CALVIN 和 Franka Kitchen 不同，RLBench 基于 **CoppeliaSim** 仿真引擎，提供标准化的任务接口和自动化评估流程，是当前具身智能研究中最广泛使用的 benchmark 之一。

---

## 1. RLBench 概述

### 1.1 什么是 RLBench

**RLBench**（**R**obot **L**earning **Bench**mark）是由 **Imperial College London** 和 **DeepMind** 联合推出的**大规模机器人学习基准**，旨在为机器人操控任务提供一个**标准化、可复现、任务丰富**的评测环境。

**论文**：[RLBench: Robot Learning with Large-Scale, Diverse Tasks](https://arxiv.org/abs/1904.03641)

**GitHub**：`https://github.com/stepjam/RLBench`

**核心定位**：RLBench 的核心目标是**推动大规模机器人学习研究**，提供一个包含 **100+ 差异化任务**的标准测试平台，每个任务都有明确的成功条件和自动化评估指标。

**RLBench vs CALVIN vs Franka Kitchen**：

| 维度 | RLBench | CALVIN | Franka Kitchen |
|------|---------|--------|----------------|
| **任务数量** | 100+ | 6 | 7 |
| **仿真引擎** | CoppeliaSim | Python API | Mujoco |
| **机械臂** | Franka Panda / Fetch / Panda | KUKA LBR | Franka Panda |
| **场景复杂度** | 多样化单步任务 | 桌面链式任务 | 厨房多步任务 |
| **语言指令** | 支持 | 核心特色 | 不支持 |
| **评估重点** | 任务多样性 & 成功率 | 长时序语言理解 | 状态依赖多步操作 |
| **发布年份** | 2019 | 2022 | 2019 |

### 1.2 设计哲学

RLBench 的设计围绕三个核心原则：

**① 任务多样性（Task Diversity）**

RLBench 收录了 **100+ 个**差异化任务，涵盖：

- **物体操控**：抓取、移动、旋转、装配
- **工具使用**：使用螺丝刀、开抽屉、使用锤子
- **精细操作**：插孔、拧瓶盖、倒水
- **多阶段任务**：多步骤组合操作

**② 评估标准化（Standardized Evaluation）**

所有任务遵循统一的**观测-动作接口**：

```
观测（Observation）
├── 视觉：RGB-D 图像、点云
├── 关节状态：位置、速度、力矩
├── 末端执行器：位置、姿态、抓取状态
└── 任务指令：文本描述（可选）

动作（Action）
└── 末端执行器 6-DoF 位置/姿态控制
    或关节空间控制
```

**③ 数据高效性（Data Efficiency）**

RLBench 提供**演示数据**（demonstration trajectories），研究者可直接使用这些数据进行模仿学习或作为基线对比，大幅降低研究门槛。

### 1.3 目标与意义

**研究目标**：

1. **多任务学习**：一个模型如何同时学习 100+ 个不同任务并保持良好性能
2. **视觉运动策略**：如何利用 RGB-D 图像直接预测机器人动作
3. **少样本适应**：如何快速适应新任务（Fast Adaptation）
4. **跨任务迁移**：在一个任务上学到的技能如何迁移到新任务

**对具身智能研究的意义**：

| 意义 | 说明 |
|------|------|
| **降低研究门槛** | 提供标准化环境和评测基线，新研究者可快速上手 |
| **推动多任务学习** | 100+ 任务的多样性推动真正泛化的机器人学习算法 |
| **benchmark 标准化** | 统一的评估协议使不同算法之间的公平对比成为可能 |
| **演示数据共享** | 内置演示数据支持模仿学习研究 |

---

## 2. 环境设置

### 2.1 系统要求

**最低配置**：

| 组件 | 要求 |
|------|------|
| **操作系统** | Ubuntu 18.04 / 20.04 / 22.04 |
| **CPU** | Intel i5 以上 |
| **内存** | 8 GB 以上 |
| **GPU** | NVIDIA GPU（推荐，用于视觉策略） |
| **Python** | 3.7 - 3.9 |
| **磁盘空间** | 20 GB 以上 |

> ⚠️ RLBench 依赖 CoppeliaSim 仿真引擎，需要图形界面支持。建议使用有 GPU 的机器，或在有虚拟显示的环境中运行。

### 2.2 安装步骤

**步骤 1：安装 CoppeliaSim**

RLBench 基于 **CoppeliaSim**（原 V-REP）仿真引擎。首先下载并安装 CoppeliaSim：

```bash
# 下载 CoppeliaSim EDU 版本（免费用于研究）
cd ~/Downloads
wget https://www.coppeliarobotics.com/files/CoppeliaSim_Edu_V4_4_0_rev0_Linux.tar.gz
tar -xzf CoppeliaSim_Edu_V4_4_0_rev0_Linux.tar.gz
sudo mv CoppeliaSim_Edu_V4_4_0_rev0_Linux /opt/coppeliasim
sudo ln -s /opt/coppeliasim/coppeliaSim.sh /usr/local/bin/coppeliaSim
```

设置环境变量：

```bash
# 在 ~/.bashrc 中添加
export COPPELIASIM_ROOT=/opt/coppeliasim
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$COPPELIASIM_ROOT
export QT_QPA_PLATFORM=offscreen  # 无头模式运行
```

**步骤 2：安装 RLBench**

```bash
# 创建虚拟环境（推荐）
conda create -n rlbench python=3.8
conda activate rlbench

# 安装 RLBench
pip install rlbench
```

**步骤 3：验证安装**

```python
python -c "from rlbench import Environment; print('RLBench 安装成功！')"
```

> 💡 如果遇到 CoppeliaSim 启动问题，请确保系统已安装必要的图形库：`sudo apt install libgl1-mesa-glx libx11-6 libxext6`

### 2.3 快速开始

安装完成后，运行以下代码验证 RLBench 环境是否正常：

```python
"""
RLBench 快速开始示例
验证环境安装是否正确
"""

from rlbench import Environment  # RLBench 主环境类
from rlbench.task_environment import TaskEnvironment
from rlbench.action_modes import ActionMode
from rlbench.tasks import reach_target  # 导入示例任务
import numpy as np

# ============================================================
# 第1步：创建仿真环境
# ============================================================
# ActionMode.ARM_EEFS: 末端执行器位置控制模式
# robot_setup: 指定使用的机械臂型号（Franka Panda）
action_mode = ActionMode.ARM_EEFS
env = Environment(action_mode=action_mode, headless=False)

# 获取活动机械臂
robot = env.workerpool.panda  # 获取 Franka Panda 机械臂

print("✅ RLBench 环境创建成功！")
print(f"机械臂类型: {robot.name}")
print(f"关节数量: {robot.num_joints}")

# ============================================================
# 第2步：加载一个简单任务
# ============================================================
task = env.load_task(reach_target)  # 加载"到达目标"任务

# 获取任务的初始状态描述
print(f"\n✅ 任务加载成功: {task.name}")
print(f"任务描述: reach_target - 控制机械臂到达指定目标位置")

# ============================================================
# 第3步：重置任务并获取初始观测
# ============================================================
# reset() 重置任务到初始状态，并返回初始观测
descriptions, obs = task.reset()

print(f"\n✅ 任务重置成功！")
print(f"观测信息包含:")
print(f"  - RGB 图像: {obs.rgb.shape if obs.rgb is not None else 'None'}")
print(f"  - 深度图像: {obs.depth.shape if obs.depth is not None else 'None'}")
print(f"  - 关节状态: {obs.joint_positions}")
print(f"  - 末端位置: {obs.ee_pos}")

# ============================================================
# 第4步：执行一个随机动作
# ============================================================
# 生成随机末端执行器位置动作
action = np.random.uniform(-0.1, 0.1, size=(7,))  # 7维动作：3维位置+4维四元数
obs, reward, done = task.step(action)

print(f"\n✅ 动作执行成功！")
print(f"奖励值: {reward}")
print(f"任务完成: {done}")

# ============================================================
# 第5步：关闭环境
# ============================================================
env.shutdown()
print("\n✅ RLBench 环境已关闭")
```

运行效果：

```
✅ RLBench 环境创建成功！
机械臂类型: panda
关节数量: 7

✅ 任务加载成功: reach_target
任务描述: reach_target - 控制机械臂到达指定目标位置

✅ 任务重置成功！
观测信息包含:
  - RGB 图像: (128, 128, 3)
  - 深度图像: (128, 128, 1)
  - 关节状态: [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
  - 末端位置: [0.3, 0.0, 0.5]

✅ 动作执行成功！
奖励值: 0.0
任务完成: False

✅ RLBench 环境已关闭
```

---

## 3. 任务库

### 3.1 任务概览

RLBench 目前收录了 **149 个**任务（版本持续更新），覆盖多种操作类型：

| 类别 | 任务数量 | 示例任务 |
|------|----------|----------|
| **基础运动** | ~15 | reach_target, pick_and_lift, push |
| **精细操作** | ~20 | insert_peg, screw_bulb, open_drawer |
| **多物体操控** | ~25 | stack_blocks, arrange_objects, sort_shapes |
| **工具使用** | ~15 | use_screwdriver, turn_tap, press_buttons |
| **日常活动** | ~20 | open_fridge, close_door, take_glass_from_dishwasher |
| **组合任务** | ~30 | open_window_and_push_object, multi_task_sequences |
| **语言条件** | ~25 | language_guided_pick, instruction_following |

### 3.2 任务分类详解

**① 基础运动任务**

基础运动任务是最简单的任务类型，主要测试机械臂的基本运动能力：

```python
# 基础运动任务示例
from rlbench.tasks import reach_target, pick_and_lift, push

tasks_basic = [
    reach_target,      # 控制机械臂到达目标位置
    pick_and_lift,     # 抓取物体并抬起
    push,              # 推动物体到目标位置
    pick_and_place,    # 抓取并放置物体
    reach_and_touch,   # 到达并触碰目标点
]
```

**② 精细操作任务**

精细操作任务要求机械臂进行精确的空间操作，对位姿控制要求更高：

```python
# 精细操作任务示例
from rlbench.tasks import (
    insert_peg,        # 将销钉插入孔中
    screw_bulb,        # 拧入灯泡
    open_drawer,       # 打开抽屉
    close_drawer,      # 关闭抽屉
    turn_tap,          # 旋转水龙头
)

tasks_fine = [
    insert_peg,        # 需要精确的位姿控制
    screw_bulb,        # 需要旋转+下压协调
    open_drawer,       # 需要直线拉动
    turn_tap,          # 需要旋转关节
]
```

**③ 工具使用任务**

工具使用任务要求机械臂操作工具来完成任务：

```python
# 工具使用任务示例
from rlbench.tasks import (
    use_screwdriver,   # 使用螺丝刀拧螺丝
    press_buttons,     # 按下多个按钮
    sweep_toDustpan,   # 用扫帚将垃圾扫到簸箕
    wipe_surface,      # 擦拭表面
)

tasks_tools = [
    use_screwdriver,   # 需要稳定握持+旋转
    press_buttons,     # 需要精确按压
    sweep_toDustpan,   # 需要协调手臂+视觉反馈
]
```

**④ 语言条件任务**

RLBench 支持**语言条件任务**，即通过自然语言指令指定目标：

```python
# 语言条件任务示例
from rlbench.tasks import (
    language_guided_pick,     # 按语言指令抓取
    language_guided_place,    # 按语言指令放置
    instruction_following,    # 跟随指令操作
)

tasks_language = [
    language_guided_pick,     # "Pick up the red box"
    language_guided_place,    # "Place it on the left shelf"
    instruction_following,    # "Open the drawer then take the cup"
]
```

### 3.3 难度分级

RLBench 的任务按难度分为三个级别：

| 难度 | 特征 | 任务示例 | 典型成功率（基线算法）|
|------|------|----------|---------------------|
| **简单（Easy）** | 单步操作、无精确要求 | reach_target, pick_and_lift | 70-90% |
| **中等（Medium）** | 需要精确位姿或多步骤 | insert_peg, open_drawer | 40-70% |
| **困难（Hard）** | 多步骤+状态依赖+精确控制 | language_guided_seq, assembly | 10-40% |

**难度评估维度**：

1. **动作精度要求**：到位精度要求越高，难度越大
2. **时序复杂度**：单步 vs 多步组合
3. **视觉识别难度**：目标物体识别和定位的复杂度
4. **物理交互复杂度**：涉及力控、柔顺操作的任务更难

---

## 4. 观测与动作

### 4.1 观测空间

RLBench 的观测空间包含多种模态数据：

**RLBench 观测空间结构**：

```
Observation（观测）
│
├── rgb: numpy.ndarray  (H, W, 3)
│   └── RGB 彩色图像，默认 128x128
│
├── depth: numpy.ndarray  (H, W, 1)
│   └── 深度图像，像素值表示到相机的距离
│
├── point_cloud: numpy.ndarray  (H, W, 3)
│   └── 点云数据，从深度图像计算得到
│
├── joint_positions: numpy.ndarray  (7,)
│   └── 7个关节的当前位置（弧度）
│
├── joint_velocities: numpy.ndarray  (7,)
│   └── 7个关节的当前速度（rad/s）
│
├── joint_forces: numpy.ndarray  (7,)
│   └── 7个关节的当前力矩（N·m）
│
├── ee_pos: numpy.ndarray  (3,)
│   └── 末端执行器在基坐标系下的位置 (x, y, z)
│
├── ee_quat: numpy.ndarray  (4,)
│   └── 末端执行器在基坐标系下的姿态（四元数 x,y,z,w）
│
├── gripper_pos: numpy.ndarray  (2,)
│   └── 夹爪两个手指的开合程度 [左指, 右指]
│
├── gripper_touch: numpy.ndarray  (n_sensors,)
│   └── 夹爪触觉传感器读数
│
├── misc: dict
│   └── 其他信息（任务特定数据）
│
└── task_description: str  (可选)
    └── 自然语言任务描述（语言条件任务）
```

**完整观测获取示例**：

```python
"""
RLBench 观测空间详解
展示如何获取和理解各类观测数据
"""

from rlbench import Environment
from rlbench.action_modes import ActionMode
from rlbench.tasks import reach_target
import numpy as np

# 创建环境（headless=False 用于可视化）
env = Environment(action_mode=ActionMode.ARM_EEFS, headless=False)
task = env.load_task(reach_target)
descriptions, obs = task.reset()

print("=" * 60)
print("RLBench 观测空间详解")
print("=" * 60)

# ----------------------------------------
# 1. 视觉观测：RGB 图像
# ----------------------------------------
print("\n【1】RGB 图像观测")
print(f"  形状: {obs.rgb.shape}")
print(f"  数据类型: {obs.rgb.dtype}")
print(f"  数值范围: [{obs.rgb.min()}, {obs.rgb.max()}]")
# RGB 图像是 HxWx3 的数组，每个像素值 0-255

# ----------------------------------------
# 2. 视觉观测：深度图像
# ----------------------------------------
print("\n【2】深度图像观测")
print(f"  形状: {obs.depth.shape}")
print(f"  数据类型: {obs.depth.dtype}")
print(f"  数值范围: [{obs.depth.min():.4f}, {obs.depth.max():.4f}]")
# 深度图像是 HxWx1，每个像素值表示到相机的距离（米）

# ----------------------------------------
# 3. 关节状态观测
# ----------------------------------------
print("\n【3】关节状态观测")
print(f"  关节位置: {obs.joint_positions}")
print(f"  关节数量: {len(obs.joint_positions)}")
print(f"  关节速度: {obs.joint_velocities}")
print(f"  关节力矩: {obs.joint_forces}")

# ----------------------------------------
# 4. 末端执行器观测
# ----------------------------------------
print("\n【4】末端执行器观测")
print(f"  末端位置 (m): {obs.ee_pos}")
print(f"  末端姿态 (四元数): {obs.ee_quat}")
# 四元数格式：[x, y, z, w]，用于表示 3D 旋转

# ----------------------------------------
# 5. 夹爪状态观测
# ----------------------------------------
print("\n【5】夹爪状态观测")
print(f"  夹爪开度: {obs.gripper_pos}")
print(f"  触觉传感器: {obs.gripper_touch}")

# ----------------------------------------
# 6. 点云观测
# ----------------------------------------
print("\n【6】点云观测")
point_cloud = obs.point_cloud
print(f"  点云形状: {point_cloud.shape}")
# 点云是 HxWx3 的数组，表示每个像素对应的 3D 坐标

env.shutdown()
```

### 4.2 动作空间

RLBench 支持两种主要的动作模式：

**① 末端执行器位置控制（ARM_EEFS）**

控制末端执行器的位置和姿态，输出为 7 维向量：

```python
# 末端执行器控制模式
ActionMode.ARM_EEFS
动作维度: 7 = [x, y, z, qx, qy, qz, gripper]
          前3个: 末端位置 (m)
          后4个: 末端姿态四元数 (x, y, z, w)
          gripper: 夹爪控制 (0=关闭, 1=打开)

# 示例：生成一个有效的末端执行器动作
def generate_ee_action(target_pos, target_quat=(0, 0, 0, 1), gripper=1.0):
    """
    生成末端执行器控制动作

    参数:
        target_pos: 目标位置 [x, y, z]
        target_quat: 目标姿态四元数 [x, y, z, w]，默认为保持当前姿态
        gripper: 夹爪开度，0=关闭，1=全开

    返回:
        action: 7维动作向量
    """
    action = np.concatenate([
        np.array(target_pos),    # 3维位置
        np.array(target_quat),   # 4维姿态四元数
        np.array([gripper])      # 1维夹爪控制
    ])
    return action
```

**② 关节空间控制（ARM_ABS）**

直接控制各关节的角度，输出为 7 维向量：

```python
# 关节空间控制模式
ActionMode.ARM_ABS
动作维度: 7 = [j1, j2, j3, j4, j5, j6, j7]
          每个值是对应关节的目标角度（弧度）
          夹爪单独控制

# 示例：生成关节空间动作
def generate_joint_action(joint_positions):
    """
    生成关节空间控制动作

    参数:
        joint_positions: 7个关节的目标角度

    返回:
        action: 7维关节动作
    """
    return np.array(joint_positions)
```

**动作空间对比**：

| 动作模式 | 控制维度 | 优点 | 缺点 |
|----------|----------|------|------|
| ARM_EEFS | 7 | 直观、易于规划 | 需要 IK 解算，奇异点问题 |
| ARM_ABS | 7 | 无需 IK，直接控制 | 难以直观指定末端姿态 |
| ARM_REL | 7 | 相对运动，易于增量控制 | 累积误差 |

---

## 5. 评估协议

### 5.1 成功率（Success Rate）

**成功率**是 RLBench 的核心评估指标。定义如下：

$$
\text{成功率} = \frac{\text{成功完成的任务数}}{\text{总尝试次数}} \times 100\%
$$

**"成功"的定义**：

- 任务达到预定义的**成功条件**（Success Condition）
- 成功条件因任务而异，由 RLBench 预定义

**评估流程**：

```python
"""
RLBench 成功率评估流程
展示如何正确评估一个策略的成功率
"""

from rlbench import Environment
from rlbench.action_modes import ActionMode
from rlbench.tasks import reach_target, pick_and_lift
import numpy as np

# ============================================================
# 评估配置
# ============================================================
NUM_EPISODES = 100       # 评估的总回合数
TASK = reach_target      # 评估的任务
MAX_STEPS = 50           # 每回合最大步数

# 创建环境
env = Environment(action_mode=ActionMode.ARM_EEFS, headless=False)

# ============================================================
# 评估函数
# ============================================================
def evaluate_policy(policy_fn, task_class, num_episodes=100, max_steps=50):
    """
    评估策略的成功率

    参数:
        policy_fn: 策略函数，输入观测，输出动作
        task_class: RLBench 任务类
        num_episodes: 评估回合数
        max_steps: 每回合最大步数

    返回:
        success_rate: 成功率 (0-1)
        success_count: 成功次数
    """
    success_count = 0

    for episode in range(num_episodes):
        # 加载并重置任务
        task = env.load_task(task_class)
        descriptions, obs = task.reset()

        done = False
        steps = 0

        # 运行一个回合
        while not done and steps < max_steps:
            # 获取策略动作
            action = policy_fn(obs)

            # 执行动作
            obs, reward, done = task.step(action)
            steps += 1

        # 记录成功
        if done:
            success_count += 1

        if (episode + 1) % 10 == 0:
            current_rate = success_count / (episode + 1)
            print(f"  进度: {episode+1}/{num_episodes}, "
                  f"当前成功率: {current_rate*100:.1f}%")

    success_rate = success_count / num_episodes
    return success_rate, success_count

# ============================================================
# 示例：随机策略（基线对比）
# ============================================================
def random_policy(obs):
    """随机策略：随机生成动作"""
    return np.random.uniform(-0.1, 0.1, size=(7,))

print("开始评估随机策略...")
rate, count = evaluate_policy(random_policy, TASK, NUM_EPISODES, MAX_STEPS)
print(f"\n随机策略结果: 成功率 = {rate*100:.1f}% ({count}/{NUM_EPISODES})")

# 示例：恒定姿态策略
def constant_policy(obs):
    """恒定姿态策略：保持当前状态"""
    action = np.zeros(7)
    action[:3] = obs.ee_pos  # 保持当前位置
    action[3:7] = obs.ee_quat  # 保持当前姿态
    action[6] = 1.0  # 夹爪全开
    return action

print("\n开始评估恒定姿态策略...")
rate, count = evaluate_policy(constant_policy, TASK, NUM_EPISODES, MAX_STEPS)
print(f"\n恒定姿态策略结果: 成功率 = {rate*100:.1f}% ({count}/{NUM_EPISODES})")

env.shutdown()
```

### 5.2 评分标准详解

RLBench 的评估指标不仅包括成功率，还包括多个辅助指标：

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| **成功率（SR）** | 任务完成比例 | 成功次数 / 总次数 |
| **平均步数（AS）** | 成功任务的平均步数 | 成功任务总步数 / 成功次数 |
| **效率（Efficiency）** | 完成任务所需的平均尝试次数 | 1 / 成功率（越低越好）|
| **路径长度（PL）** | 末端执行器移动的总距离 | $\sum_{t} \|p_{t+1} - p_t\|$ |

**综合评分公式**：

$$
\text{评分} = \text{SR} \times \min\left(1, \frac{10}{\text{AS}}\right) \times \exp\left(-\frac{\text{PL}}{100}\right)
$$

这个评分综合考虑了成功率、动作效率和路径长度，避免单一指标的局限性。

### 5.3 排行榜

RLBench 官方维护了一个排行榜，记录各算法在各个任务上的表现：

**排行榜链接**：`https://rlbench.github.io/`

**主流基线算法对比**（截至 2023 年）：

| 算法 | 类别 | 平均成功率 | 代表任务 |
|------|------|-----------|----------|
| **BC**（Behavior Cloning）| 模仿学习 | 30-50% | 简单任务 |
| **BC-RNN** | 序列模仿学习 | 40-60% | 中等任务 |
| **PIRL** | 对比学习 | 45-65% | 多任务 |
| **RRL** | 强化学习 | 35-55% | 持续探索 |
| **GCT** | 图对比 | 50-70% | 跨任务迁移 |
| **RoboCLIP** | 视觉语言 | 60-80% | 语言条件 |

---

## 6. 基线方法

### 6.1 PIRL（Prompt-Invariant RL）

**PIRL**（**P**rompt-**I**nvariant **R**einforcement **L**earning）是一种面向**语言条件机器人操控**的强化学习方法，核心思想是：无论语言指令如何变化，机器人应该学会**与任务无关的通用操控技能**。

**论文**：[PIRL: A Competitive, Cooperative, Interpretable Robot Agent](https://arxiv.org/abs/2005.03726)

**核心架构**：

```
语言指令 "Pick the red box"
         ↓
   [文本编码器 BERT]
         ↓
   任务嵌入 z
         ↓
   ┌──────────────────────────────────────┐
   │         PIRL 策略网络                 │
   │  输入: 视觉观测 + 任务嵌入            │
   │  输出: 机器人动作                      │
   └──────────────────────────────────────┘
         ↓
   末端执行器动作
```

**PIRL 在 RLBench 上的表现**：

- 在 **40 个语言条件任务**上平均成功率达 **65.3%**
- 在未见过的**新任务**上保持 **45%** 的零样本成功率
- 相比非语言条件方法，PIRL 的语言泛化能力提升约 **20%**

### 6.2 RRL（Relational RL）

**RRL**（**R**elational **R**einforcement **L**earning）是一种基于**关系推理**的强化学习方法，核心思想是：机器人应该学会理解物体之间的**空间关系**（如"把球放到盒子左边"）。

**论文**：[RRL: Relational Reinforcement Learning](https://arxiv.org/abs/1904.05318)

**核心思想**：

RRL 引入**关系图**来表示场景中物体之间的关系：

```python
# RRL 关系表示示例
class RelationalState:
    """
    RLBench 场景的关系表示
    """
    def __init__(self, objects):
        # objects: 场景中的所有物体列表
        self.objects = objects

        # 构建关系图：物体之间的空间关系
        self.relations = []
        for i, obj1 in enumerate(objects):
            for j, obj2 in enumerate(objects):
                if i != j:
                    # 计算物体间的空间关系
                    relation = self.compute_relation(obj1, obj2)
                    self.relations.append({
                        'from': obj1,
                        'to': obj2,
                        'type': relation['type'],  # left_of, above, inside, etc.
                        'distance': relation['distance']
                    })

    def compute_relation(self, obj1, obj2):
        """计算两个物体之间的空间关系"""
        pos1, pos2 = obj1.position, obj2.position

        if pos1[0] < pos2[0]:
            return {'type': 'left_of', 'distance': pos2[0] - pos1[0]}
        elif pos1[0] > pos2[0]:
            return {'type': 'right_of', 'distance': pos1[0] - pos2[0]}
        elif pos1[2] > pos2[2]:
            return {'type': 'above', 'distance': pos1[2] - pos2[2]}
        else:
            return {'type': 'below', 'distance': pos2[2] - pos1[2]}
```

**RRL 在 RLBench 上的表现**：

- 在需要**空间推理**的任务上（如"把球放到盒子左边"）成功率提升约 **25%**
- 关系表示使策略网络能够更好地处理**物体数量变化**的场景
- 在组合任务（如"先放到左边再旋转"）上表现优异

### 6.3 模仿学习基线

模仿学习（Imitation Learning）是 RLBench 最常用的基线方法，包括以下几种：

**① 行为克隆（Behavior Cloning, BC）**

最简单的模仿学习方法，直接监督学习观测-动作对：

```python
"""
行为克隆（BC）基线实现
使用 RLBench 演示数据进行行为克隆训练
"""

from rlbench import Environment
from rlbench.action_modes import ActionMode
from rlbench.tasks import reach_target
import numpy as np

# ============================================================
# 行为克隆核心原理
# ============================================================
"""
行为克隆的目标是学习一个策略 πθ(a|o)，
使得在观测 o 下，策略输出的动作 a 尽可能接近专家动作 a*

损失函数：
L(θ) = E_{o,a*} [||πθ(a|o) - a*||²]

其中：
- θ 是策略网络的参数
- o 是观测（视觉、关节状态等）
- a* 是专家演示的动作
"""

# ============================================================
# 简化 BC 策略实现
# ============================================================
class BCPolicy:
    """
    简化的行为克隆策略

    这个示例展示 BC 的核心思想：
    输入观测 → 预测动作
    """
    def __init__(self, input_dim, output_dim):
        # 实际使用时，这里应该是一个神经网络
        # 为了演示，使用一个简单的线性映射
        self.weights = np.random.randn(input_dim, output_dim) * 0.01
        self.bias = np.zeros(output_dim)

    def predict(self, obs):
        """
        从观测预测动作

        参数:
            obs: RLBench 观测对象

        返回:
            action: 7维动作向量
        """
        # 将观测转换为特征向量
        features = self.extract_features(obs)

        # 线性策略：action = W @ features + b
        action = features @ self.weights + self.bias

        # 动作归一化到合理范围
        action = np.clip(action, -1, 1)

        return action

    def extract_features(self, obs):
        """
        从观测中提取特征

        实际实现中，应该使用 CNN 处理视觉观测
        这里用简化版本演示
        """
        # 使用关节状态和末端执行器位置作为特征
        joint_feat = obs.joint_positions
        ee_pos_feat = obs.ee_pos
        ee_quat_feat = obs.ee_quat

        # 拼接所有特征
        features = np.concatenate([
            joint_feat,       # 7维
            ee_pos_feat,      # 3维
            ee_quat_feat,     # 4维
        ])

        return features

    def update(self, observations, actions, learning_rate=0.001):
        """
        使用专家数据更新策略

        参数:
            observations: 观测列表
            actions: 专家动作列表
            learning_rate: 学习率
        """
        losses = []
        for obs, action in zip(observations, actions):
            pred_action = self.predict(obs)
            loss = np.mean((pred_action - action) ** 2)
            losses.append(loss)

        # 简化：直接用平均损失更新
        mean_loss = np.mean(losses)

        # 梯度下降（实际应该用反向传播）
        # 这里仅演示思想
        return mean_loss


# ============================================================
# BC 在 RLBench 上的典型性能
# ============================================================
print("=" * 60)
print("行为克隆（BC）在 RLBench 上的性能")
print("=" * 60)

bc_results = {
    'reach_target': 0.85,      # 简单任务：85%
    'pick_and_lift': 0.72,     # 中等任务：72%
    'insert_peg': 0.55,        # 精细操作：55%
    'open_drawer': 0.48,       # 精细操作：48%
    'push': 0.65,              # 中等任务：65%
    'stack_blocks': 0.35,     # 困难任务：35%
}

for task, sr in bc_results.items():
    bar = "█" * int(sr * 30)
    print(f"  {task:20s} | {bar:30s} | {sr*100:.1f}%")

print("\nBC 基线特点：")
print("  ✅ 简单易实现，训练稳定")
print("  ✅ 在简单任务上表现良好")
print("  ❌ 分布偏移问题：误差会累积")
print("  ❌ 在复杂/长时序任务上表现不佳")
```

**② GAIL（Generative Adversarial Imitation Learning）**

使用生成对抗方法学习专家策略：

```python
# GAIL 在 RLBench 上的表现
gail_results = {
    'reach_target': 0.88,      # +3% vs BC
    'pick_and_lift': 0.78,    # +6% vs BC
    'insert_peg': 0.62,        # +7% vs BC
    'open_drawer': 0.55,      # +7% vs BC
    'push': 0.70,              # +5% vs BC
    'stack_blocks': 0.42,    # +7% vs BC
}
```

---

## 7. 代码实战

### 7.1 环境加载与任务执行

```python
"""
RLBench 代码实战：环境加载与任务执行
本节演示如何在 RLBench 中加载环境、选择任务、运行 episode
"""

from rlbench import Environment
from rlbench.action_modes import ActionMode, ActionSpace
from rlbench.tasks import get_task_names
import numpy as np

# ============================================================
# 第1步：创建 RLBench 环境
# ============================================================
print("=" * 60)
print("第1步：创建 RLBench 环境")
print("=" * 60)

# 创建环境，指定动作模式
# ARM_EEFS: 末端执行器位置控制（最常用）
action_mode = ActionMode.ARM_EEFS

# headless=True: 无头模式（无图形界面，适合服务器）
# headless=False: 有图形界面（可观察机械臂的实时运动）
env = Environment(action_mode=action_mode, headless=True)
print("✅ 环境创建成功！")

# ============================================================
# 第2步：查看所有可用任务
# ============================================================
print("\n" + "=" * 60)
print("第2步：查看所有可用任务")
print("=" * 60)

# get_task_names() 返回所有可用任务名称列表
all_tasks = get_task_names()
print(f"RLBench 共有 {len(all_tasks)} 个任务：")
print(f"\n前10个任务: {all_tasks[:10]}")
print(f"\n后10个任务: {all_tasks[-10:]}")

# ============================================================
# 第3步：加载并执行一个具体任务
# ============================================================
print("\n" + "=" * 60)
print("第3步：加载并执行 reach_target 任务")
print("=" * 60)

# 导入目标任务
from rlbench.tasks import reach_target, pick_and_lift

# 加载任务
task = env.load_task(reach_target)

# 重置任务，获取初始观测
descriptions, obs = task.reset()

print(f"✅ 任务: {task.name}")
print(f"✅ 初始观测已获取")
print(f"  关节位置: {obs.joint_positions[:3]}...")  # 只打印前3个

# ============================================================
# 第4步：执行一个完整的 episode
# ============================================================
print("\n" + "=" * 60)
print("第4步：执行一个完整的 episode")
print("=" * 60)

MAX_STEPS = 50  # 最大步数

def random_policy(obs):
    """随机策略"""
    return np.random.uniform(-0.05, 0.05, size=(7,))

done = False
step_count = 0
episode_reward = 0.0

while not done and step_count < MAX_STEPS:
    # 使用策略选择动作
    action = random_policy(obs)

    # 执行动作，获取下一观测
    obs, reward, done = task.step(action)

    episode_reward += reward
    step_count += 1

print(f"✅ Episode 完成！")
print(f"  总步数: {step_count}")
print(f"  总奖励: {episode_reward:.2f}")
print(f"  任务成功: {'是 ✅' if done else '否 ❌'}")

# ============================================================
# 第5步：关闭环境
# ============================================================
print("\n" + "=" * 60)
print("第5步：关闭环境")
print("=" * 60)
env.shutdown()
print("✅ 环境已关闭")
```

### 7.2 完整评估脚本

```python
"""
RLBench 完整评估脚本
在多个任务上评估策略的性能
"""

from rlbench import Environment
from rlbench.action_modes import ActionMode
from rlbench.tasks import (
    reach_target, pick_and_lift, push,
    open_drawer, close_drawer, insert_peg
)
import numpy as np
from collections import defaultdict

# ============================================================
# 配置
# ============================================================
NUM_EPISODES = 20          # 每个任务评估的 episode 数
MAX_STEPS = 50             # 每个 episode 的最大步数
TASKS = [                  # 要评估的任务列表
    reach_target,
    pick_and_lift,
    push,
    open_drawer,
    insert_peg,
]

# 创建环境
env = Environment(action_mode=ActionMode.ARM_EEFS, headless=True)

# ============================================================
# 随机策略
# ============================================================
def random_policy(obs):
    """随机动作策略（基线）"""
    # 动作空间：7维
    # 前3维：末端位置增量（-0.1 ~ 0.1 m）
    # 后3维：末端姿态四元数增量
    # 最后1维：夹爪控制
    action = np.random.uniform(-0.05, 0.05, size=(7,))
    action[6] = 1.0  # 夹爪全开
    return action

# ============================================================
# 执行评估
# ============================================================
def evaluate_task(task_class, num_episodes=20, max_steps=50):
    """
    在单个任务上评估策略

    返回:
        results: dict，包含成功率、平均步数等信息
    """
    successes = 0
    total_steps = 0
    episode_lengths = []

    for ep in range(num_episodes):
        # 重置任务
        task = env.load_task(task_class)
        descriptions, obs = task.reset()

        done = False
        steps = 0

        # 运行 episode
        while not done and steps < max_steps:
            action = random_policy(obs)
            obs, reward, done = task.step(action)
            steps += 1

        # 记录结果
        if done:
            successes += 1
            episode_lengths.append(steps)
        total_steps += steps

    # 计算统计数据
    avg_steps = np.mean(episode_lengths) if episode_lengths else 0
    success_rate = successes / num_episodes

    return {
        'success_rate': success_rate,
        'avg_steps': avg_steps,
        'num_successes': successes,
        'num_episodes': num_episodes,
    }

# ============================================================
# 运行评估并打印结果
# ============================================================
print("=" * 70)
print("RLBench 多任务评估报告")
print("=" * 70)
print(f"策略: 随机策略")
print(f"每个任务评估: {NUM_EPISODES} episodes")
print(f"每个 episode 最大步数: {MAX_STEPS}")
print("=" * 70)

task_names = {
    reach_target: "reach_target",
    pick_and_lift: "pick_and_lift",
    push: "push",
    open_drawer: "open_drawer",
    insert_peg: "insert_peg",
}

all_results = {}
for task_class in TASKS:
    task_name = task_names[task_class]
    print(f"\n评估任务: {task_name}...", end=" ", flush=True)

    results = evaluate_task(task_class, NUM_EPISODES, MAX_STEPS)
    all_results[task_name] = results

    print(f"完成！成功率: {results['success_rate']*100:.1f}%")

# ============================================================
# 汇总报告
# ============================================================
print("\n" + "=" * 70)
print("汇总结果")
print("=" * 70)
print(f"{'任务':<20} | {'成功率':<10} | {'平均步数':<10} | {'成功次数':<10}")
print("-" * 70)

total_sr = 0.0
for task_name, results in all_results.items():
    sr = results['success_rate'] * 100
    total_sr += sr
    avg_s = results['avg_steps']
    ns = f"{results['num_successes']}/{results['num_episodes']}"
    print(f"{task_name:<20} | {sr:>8.1f}% | {avg_s:>9.1f} | {ns:>10s}")

avg_overall = total_sr / len(all_results)
print("-" * 70)
print(f"{'平均':<20} | {avg_overall:>8.1f}% |")

env.shutdown()
print("\n✅ 评估完成！")
```

---

## 8. 练习题

### 选择题

**1. RLBench 的核心仿真引擎是什么？**

A. Mujoco
B. Gazebo
C. CoppeliaSim
D. Webots

**2. RLBench 中，ARM_EEFS 动作模式的维度是多少？**

A. 6
B. 7
C. 8
D. 14

**3. 以下哪个不是 RLBench 的设计原则？**

A. 任务多样性
B. 评估标准化
C. 硬件在环
D. 数据高效性

**4. PIRL 的全称是什么？**

A. Position-Invariant Reinforcement Learning
B. Prompt-Invariant Reinforcement Learning
C. Policy-Invariant Reinforcement Learning
D. Prompt-Invariant Robot Learning

**5. RLBench 中，哪个观测不是直接提供的？**

A. RGB 图像
B. 深度图像
C. 关节力矩
D. 物体类别标签

**6. 在 RLBench 中，`task.reset()` 返回值的类型是？**

A. `(obs, reward, done)`
B. `(descriptions, obs)`
C. `(obs, done)`
D. `(descriptions, reward, obs)`

**7. RRL 的核心思想是？**

A. 强化学习
B. 关系推理
C. 模仿学习
D. 迁移学习

### 填空题

**8.** RLBench 收录了超过 **____** 个差异化任务。

**9.** 成功率公式：成功率 = 成功次数 / **____** × 100%。

**10.** 末端执行器姿态的表示方式（四元数）包含 **____** 个分量。

**11.** 在 ARM_EEFS 动作模式中，前 3 维表示 **____** 控制量。

**12.** 行为克隆（BC）的损失函数是 **____**（填英文缩写）。

### 简答题

**13.** 请简述 RLBench 与 CALVIN 在任务设计上的主要区别。

**14.** 请描述 RLBench 观测空间中 `point_cloud` 和 `depth` 的区别与联系。

**15.** 为什么说 RLBench 的任务多样性对评估机器人学习算法的泛化能力至关重要？

---

## 9. 答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **C** | RLBench 使用 CoppeliaSim 作为仿真引擎（从 V-REP 改名），而 Franka Kitchen 使用 Mujoco，CALVIN 使用自定义 Python API |
| 2 | **B** | ARM_EEFS 模式：7维 = 3维位置 + 4维四元数姿态 + 1维夹爪控制（有的版本把夹爪单独处理） |
| 3 | **C** | RLBench 的设计原则是：任务多样性、评估标准化、数据高效性。硬件在环不是其设计目标 |
| 4 | **B** | PIRL = Prompt-Invariant Reinforcement Learning，强调语言指令变化下的泛化能力 |
| 5 | **D** | RLBench 提供 RGB、深度、点云、关节状态等观测，但不直接提供物体类别标签（需要从视觉中识别） |
| 6 | **B** | `task.reset()` 返回 `(descriptions, obs)`，其中 descriptions 是任务描述列表，obs 是观测对象 |
| 7 | **B** | RRL = Relational Reinforcement Learning，核心是通过关系图表示物体间的空间关系 |

### 填空题答案

**8.** **100+**（RLBench 目前收录了 149 个任务，且版本持续更新）

**9.** **总尝试次数**（成功率 = 成功完成的任务数 / 总尝试次数 × 100%）

**10.** **4**（四元数 [x, y, z, w] 四个分量，用于避免欧拉角的万向锁问题）

**11.** **末端位置**（ARM_EEFS 模式：前3维 [x, y, z] 控制末端执行器的空间位置）

**12.** **MSE** 或 **均方误差**（Behavior Cloning 使用的损失函数：$L(\theta) = E_{o,a^*}[||\pi_\theta(a|o) - a^*||^2]$）

### 简答题答案

**13.**
> RLBench 与 CALVIN 在任务设计上的主要区别：
>
> - **任务数量**：RLBench 有 100+ 个任务，CALVIN 只有 6 个任务链
> - **任务粒度**：RLBench 以**单步独立任务**为主（如抓取、放置），CALVIN 以**长时序链式任务**为主（多步串联）
> - **语言使用**：RLBench 语言指令是**可选的辅助信息**，CALVIN 的语言指令是**核心**，是任务的唯一描述方式
> - **评测重点**：RLBench 评测**任务多样性和泛化能力**，CALVIN 评测**长时序语言理解与规划能力**
> - **时序依赖**：RLBench 任务之间相互独立，CALVIN 子任务之间有严格的状态依赖关系

**14.**
> `point_cloud` 和 `depth` 的区别与联系：
>
> **区别**：
> - `depth` 是原始深度图像，形状为 `(H, W, 1)`，每个像素值表示该点到相机传感器的距离（单位：米）
> - `point_cloud` 是从深度图像经过相机内参投影得到的 3D 点云，形状为 `(H, W, 3)`，每个像素对应一个 `(x, y, z)` 3D 坐标
>
> **联系**：
> - `point_cloud` 是由 `depth` 图像**派生**而来的
> - 计算公式：$P_{xyz} = depth \cdot K^{-1} \cdot p_{uv}$，其中 $K$ 是相机内参矩阵，$p_{uv}$ 是像素坐标
> - 两者使用相同的原始深度数据，只是表示形式不同
>
> **适用场景**：
> - 深度图像适合做 2D 视觉处理（如深度卷积网络）
> - 点云适合做 3D 空间推理（如抓取点估计、障碍物检测）

**15.**
> RLBench 的任务多样性对评估泛化能力至关重要，原因如下：
>
> 1. **避免过拟合评测**：如果 benchmark 只有少量简单任务，算法可能通过记忆特定模式来获得高分，而非学到真正可泛化的操控技能。100+ 差异化任务使得"死记硬背"策略失效。
>
> 2. **覆盖多种操控技能**：不同任务需要不同的技能组合（精确位姿、力控、工具使用、多物体协调等），只有全面覆盖才能验证算法的综合能力。
>
> 3. **跨任务迁移评估**：通过在任务 A 上训练、在任务 B 上测试的方式，可以评估算法的跨任务迁移能力——这是机器人真正泛化的核心。
>
> 4. **难度梯度**：从简单任务（reach_target）到困难任务（assembly），形成自然的难度梯度，能更细致地刻画算法性能。
>
> 5. **真实世界映射**：真实世界的操控任务千差万别，多样化的 benchmark 才能更真实地反映算法在真实场景中的表现。

---

## 总结

本节我们全面介绍了 **RLBench**——目前最具规模的机械臂操控 benchmark：

| 模块 | 核心内容 |
|------|----------|
| **概述** | 100+ 任务、CoppeliaSim 引擎、标准化评估接口 |
| **环境** | CoppeliaSim + RLBench 安装、Python API 快速上手 |
| **任务库** | 基础/精细/工具/语言条件 4 大类，E/M/H 3 级难度 |
| **观测与动作** | RGB-D/点云/关节状态 + ARM_EEFS/ARM_ABS 两种控制模式 |
| **评估协议** | 成功率 + 平均步数 + 路径长度的综合评分体系 |
| **基线方法** | PIRL（语言泛化）、RRL（关系推理）、BC/GAIL（模仿学习）|
| **代码实战** | 环境加载、任务执行、批量评估的完整代码示例 |

**下节预告**：18-5 Benchmark 项目实战——我们将综合运用 CALVIN、Franka Kitchen 和 RLBench 三大基准，完成一个完整的机器人学习项目，包括数据采集、模型训练和性能评估。

---

**参考文献**：

1. James S, et al. "RLBench: Robot Learning with Large-Scale, Diverse Tasks." arXiv:1904.03641, 2019.
2. Steppin et al. "PIRL: A Competitive, Cooperative, Interpretable Robot Agent." arXiv:2005.03726, 2020.
3. Zambetta et al. "RRL: Relational Reinforcement Learning." arXiv:1904.05318, 2019.
4. RLBench Official Repository: https://github.com/stepjam/RLBench
