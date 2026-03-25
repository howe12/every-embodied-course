# 18-3 Franka Kitchen 环境

> **前置课程**：18-2 CALVIN 基准
> **后续课程**：18-4 RLBench 基准

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：上一节我们深入探讨了 CALVIN Benchmark 的长时序语言条件机器人操控评测体系。CALVIN 的场景聚焦于桌面操控，任务相对简单。本节我们将目光移向更复杂的家庭场景——**Franka Kitchen 环境**，这是目前最具代表性的**厨房多任务仿真基准**之一。与 CALVIN 不同，Franka Kitchen 的核心挑战在于：**机器人在一个逼真的厨房场景中，需要依次完成开门、开抽屉、移动物体等多个操作，且任务之间存在严格的状态依赖关系**。这个环境在模仿学习和机器人控制领域被广泛使用，是检验长时序操作能力的重要试金石。

---

## 1. Franka Kitchen 概述

### 1.1 Franka Panda 机械臂

**Franka Panda** 是由德国 **Franka Emika** 公司生产的**协作机器人手臂**（Cobot），因其高精度、高灵敏度和开放的接口设计，在机器人研究领域极为流行。

**Franka Panda 硬件规格**：

| 参数 | 规格 |
|------|------|
| **自由度（DOF）** | 7 个关节（7-DOF） |
| **末端负载** | 3 kg |
| **工作半径** | 855 mm |
| **重复定位精度** | ±0.1 mm |
| **重量** | 18 kg |
| **控制频率** | 1 kHz（原生） |
| **通信接口** | TCP/IP, ROS, FCI（Franka Control Interface） |
| **末端执行器** | 双指夹爪（Panda Gripper） |

**为什么选择 Franka Panda 作为仿真基准？**

| 优势 | 说明 |
|------|------|
| **7-DOF 仿生设计** | 与人类手臂自由度相同，逆运动学解算自然，适合操作任务 |
| **高灵敏度** | 内置关节力矩传感器，可实现力控和柔顺操作 |
| **开源研究接口** | 提供 FCI 开放接口，可直接读取和写入关节命令 |
| **广泛使用** | 研究社区积累大量基于 Franka 的算法和数据 |
| **Mujoco 原生支持** | Mujoco 物理引擎对 Franka 模型有完善的支持 |

**Franka Panda 关节结构**：

```
        关节7（腕部旋转）
             ↑
        关节6（腕部俯仰）
             ↑
        关节5（肘部）
             ↑
   关节4 ←┼→ 关节3（肩部侧摆）
             ↑
   关节2（肩部俯仰）
             ↑
        关节1（底座旋转）
             ↓
         [基座]
```

**7 个关节的协调控制**是 Franka Panda 执行精细操作的关键。每个关节都有独立的力矩传感器，使得机器人能够实现"力感知"——即在接触物体时自动调节力度，这是实现柔顺操作（如抽屉拉动、门把手旋转）的重要基础。

### 1.2 厨房仿真环境

**Franka Kitchen** 是基于 **Mujoco** 物理引擎构建的**厨房操控仿真环境**，专门用于评估机器人在厨房场景中执行**多步操作任务**的能力。

**论文**：[Learning Surgical Skills from Simulated and Demonstrated Robot Manipulation](https://arxiv.org/abs/2110.11792)（相关早期工作）
**相关资源**：`https://github.com/AGentin/franka_kitchen`（社区维护版本）

**核心定位**：Franka Kitchen 的场景是一个**真实厨房的 Mujoco 仿真模型**，包含橱柜、水槽、炉灶、微波炉、抽屉等多种可交互物体。机器人（Franka Panda）在场景中执行操作，每个操作都会改变物体的状态（如门打开、抽屉关闭）。

**Franka Kitchen 场景布局**：

```
┌──────────────────────────────────────────────────────────┐
│                      厨房场景                             │
│                                                          │
│   ┌─────────┐    ┌──────┐    ┌─────────┐    ┌────────┐   │
│   │ 上柜1   │    │微波炉│    │ 上柜2   │    │  炉灶  │   │
│   └─────────┘    └──────┘    └─────────┘    └────────┘   │
│                                                          │
│   ┌─────────┐    ┌──────────┐    ┌─────────┐              │
│   │ 下柜门1 │    │  水槽    │    │ 下柜门2 │              │
│   │ (可开)  │    │          │    │ (可开)  │              │
│   └─────────┘    └──────────┘    └─────────┘              │
│                                                          │
│   ┌─────────────────────┐    ┌──────────────────────┐   │
│   │     抽屉1 (可拉)    │    │     抽屉2 (可拉)     │   │
│   └─────────────────────┘    └──────────────────────┘   │
│                                                          │
│                    [Franka Panda 机械臂]                 │
│                         ↑                                │
│                       桌面                                │
└──────────────────────────────────────────────────────────┘
```

**与 CALVIN 的本质区别**：

| 维度 | CALVIN | Franka Kitchen |
|------|--------|---------------|
| **场景复杂度** | 简单桌面场景 | 真实厨房环境，多物体 |
| **机械臂** | 桌面机械臂（4-6 DOF） | Franka Panda（7 DOF） |
| **交互物体** | 积木、球、盒子 | 橱柜门、抽屉、炉灶、微波炉 |
| **任务依赖** | 语言序列组合 | 严格状态依赖（需先开门才能拿东西） |
| **观测类型** | RGB-D + 状态 | Mujoco 仿真状态（物体位置、关节角度） |
| **主要用途** | 语言条件 VLA 评测 | 模仿学习、任务规划评测 |

### 1.3 任务场景设计

Franka Kitchen 的任务场景设计围绕**厨房常见操作**展开，每个操作都对应一个**物体的状态变化**。

**核心操作类型**：

| 操作 | 英文 | 状态变化 | 示例 |
|------|------|---------|------|
| **打开柜门** | Open Cabinet | 角度 0° → 90° | 打开左侧下柜门 |
| **关闭柜门** | Close Cabinet | 角度 90° → 0° | 关闭右侧下柜门 |
| **拉开抽屉** | Open Drawer | 位置 0 → 0.3m | 拉出抽屉1 |
| **关闭抽屉** | Close Drawer | 位置 0.3m → 0 | 推回抽屉2 |
| **转动炉灶开关** | Toggle Burner | 开/关 切换 | 打开炉灶 |
| **操作微波炉** | Operate Microwave | 门开/关 + 时间设置 | 打开微波炉门 |

**多步任务链示例**：

> "打开左侧柜门，从柜子里拿出杯子，然后关闭柜门"

这个任务链包含 **3 个步骤**，且存在严格的状态依赖：
1. 必须先打开柜门才能伸手进去（状态依赖）
2. 必须在柜门打开状态下才能取物（空间约束）
3. 取物后关闭柜门是最终目标状态（目标约束）

**场景难度分级**：

| 难度 | 描述 | 示例任务 |
|------|------|---------|
| **L1 单步操作** | 单一操作，无依赖 | "打开抽屉1" |
| **L2 两步操作** | 两个操作，有依赖 | "打开柜门 → 关闭抽屉" |
| **L3 三步操作** | 三个操作链 | "打开柜门 → 拉抽屉 → 关炉灶" |
| **L4 复杂组合** | 四步及以上组合 | 多物体、长序列、多约束 |

---

## 2. 环境配置

### 2.1 Mujoco 仿真引擎

**Mujoco**（Multi-Joint Dynamics with Contact）是 DeepMind 开源的**通用物理仿真引擎**，专注于机器人仿真和强化学习。Franka Kitchen 正是基于 Mujoco 构建的。

**Mujoco 的核心优势**：

| 优势 | 说明 |
|------|------|
| **高精度物理** | 精确的关节动力学和接触力计算 |
| **高效的约束求解** | 针对关节限位、接触约束的专用求解器 |
| **XML 模型格式** | 基于 MJCF（Mujoco Native Format）定义模型 |
| **可视化渲染** | 内置 viewer，支持实时交互 |
| **Python API** | 通过 `mujoco-py` 或 `mujoco` 包提供 Python 接口 |

**安装 Mujoco 及 Franka Kitchen 环境**：

```python
# 安装 Mujoco Python 包
pip install mujoco
pip install mujoco-py      # 旧版接口（已停止维护，推荐用 mujoco）

# 克隆 Franka Kitchen 仓库
# 注意：官方仓库可能已停止维护，以下为社区维护版本
# 实际使用时请参照最新 fork 版本
import subprocess

# 克隆仓库
subprocess.run([
    "git", "clone",
    "https://github.com/AGentin/franka_kitchen.git",
    "/tmp/franka_kitchen"
], check=True)

print("✓ Franka Kitchen 仓库克隆完成")
```

### 2.2 模型文件

Franka Kitchen 的模型文件采用 **Mujoco MJCF** 格式（XML），定义了场景中所有物体的几何结构、物理属性和约束关系。

**MJCF 模型文件结构**：

```xml
<!-- Franka Kitchen 场景模型（概念示例） -->
<!-- 完整文件请参照仓库中的 kitchen.xml -->

<mujoco model="kitchen">
    <!-- 1. 编译器设置 -->
    <compiler angle="radian" meshdir="meshes/"/>

    <!-- 2. 默认关节设置 -->
    <default>
        <joint damping="0.1" stiffness="1.0"/>
        <geom friction="0.5" solimp="0.9 0.9 0.01"/>
    </default>

    <!-- 3. 物体（worldbody）定义 -->
    <worldbody>
        <!-- 地面 -->
        <geom name="floor" type="plane" size="5 5 0.1"/>

        <!-- Franka Panda 机械臂 -->
        <body name="panda" pos="0 0 0">
            <!-- 各关节定义 -->
            <joint name="panda_joint1" type="hinge" axis="0 0 1" .../>
            <body name="link1"> ... </body>
            <!-- 末端执行器（夹爪） -->
            <geom name="gripper" type="box" .../>
        </body>

        <!-- 厨房家具 -->
        <!-- 柜门1 -->
        <body name="cabinet_door_1" pos="1.5 0 0.5">
            <joint name="cabinet_door_1_joint" type="hinge" axis="0 1 0"/>
            <geom name="cabinet_door_1_geom" type="box" size="0.4 0.05 0.4"/>
        </body>

        <!-- 抽屉1 -->
        <body name="drawer_1" pos="1.0 0 0.3">
            <joint name="drawer_1_joint" type="slide" axis="1 0 0"/>
            <geom name="drawer_1_geom" type="box" size="0.3 0.2 0.1"/>
        </body>

        <!-- 炉灶 -->
        <body name="burner" pos="2.0 0 0.4">
            <joint name="burner_joint" type="hinge" axis="0 0 1"/>
            <geom name="burner_geom" type="cylinder" .../>
        </body>

        <!-- 微波炉 -->
        <body name="microwave" pos="2.5 0 0.5">
            <joint name="microwave_door_joint" type="hinge" axis="0 1 0"/>
            <geom name="microwave_geom" type="box" .../>
        </body>
    </worldbody>

    <!-- 4. 物理属性 -->
    <option timestep="0.002" iterations="50"/>
</mujoco>
```

**模型关键元素说明**：

| 元素 | 说明 |
|------|------|
| `<joint>` | 关节定义，`type="hinge"` 为旋转关节，`type="slide"` 为滑动关节 |
| `axis` | 关节运动轴向，如 `axis="0 1 0"` 表示绕 Y 轴旋转 |
| `<geom>` | 几何形状定义（box、cylinder、mesh 等） |
| `friction` | 摩擦系数，影响物体滑动和夹爪抓取 |
| `damping` | 关节阻尼，影响运动响应速度 |

### 2.3 参数设置

**Mujoco 仿真参数配置**：

```python
"""
Mujoco 仿真参数配置
"""
import mujoco
import numpy as np


def create_kitchen_model(xml_path="/tmp/franka_kitchen/kitchen.xml"):
    """
    加载 Franka Kitchen 场景模型

    Args:
        xml_path: MJCF XML 文件路径

    Returns:
        model: Mujoco 模型对象
    """
    # 加载 MJCF XML 模型
    model = mujoco.MjModel.from_xml_path(xml_path)

    print("=" * 50)
    print("Franka Kitchen 模型信息")
    print("=" * 50)
    print(f"模型名称: {model.name}")
    print(f"关节数量: {model.njnt}")
    print(f"物体（body）数量: {model.nbody}")
    print(f"约束数量: {model.neq}")
    print(f"仿真步长: {model.opt.timestep:.4f} 秒")

    return model


def configure_simulation(model):
    """
    配置仿真器参数

    Args:
        model: Mujoco 模型对象

    Returns:
        data: Mujoco 数据对象（包含仿真状态）
    """
    # 创建仿真数据对象
    data = mujoco.MjData(model)

    # 配置仿真选项
    # 这些参数影响仿真精度和稳定性
    sim_config = {
        'timestep': model.opt.timestep,           # 仿真步长（秒）
        'iterations': model.opt.iterations,       # 约束求解迭代次数
        'tolerance': model.opt.tolerance,         # 约束求解收敛容差
        'ls_iterations': model.opt.ls_iterations, # 线搜索迭代次数
        'noslip_iterations': model.opt.noslip_iterations,  # 防滑迭代次数
        'mpr_iterations': model.opt.mpr_iterations,       # MPR 求解器迭代次数
    }

    print("\n仿真配置:")
    for key, val in sim_config.items():
        print(f"  {key}: {val}")

    return data


def set_initial_state(data, joint_positions):
    """
    设置机器人初始关节角度

    Args:
        data: Mujoco 数据对象
        joint_positions: 关节角度数组（弧度）

    Returns:
        data: 配置后的数据对象
    """
    # Franka Panda 有 7 个关节
    # joint_positions 应为长度为 7 的数组
    if len(joint_positions) != 7:
        raise ValueError(f"期望 7 个关节角度，实际得到 {len(joint_positions)} 个")

    # 设置各关节位置
    data.qpos[:7] = joint_positions

    # 前向动力学计算（更新所有派生状态）
    mujoco.mj_step(data, nstep=1)

    print(f"\n✓ 初始状态设置完成")
    print(f"  关节角度: {[f'{j:.3f}' for j in joint_positions]}")

    return data
```

**仿真步长与精度**：

Mujoco 的 `timestep` 参数控制仿真精度与速度的权衡：

| 步长 | 精度 | 实时性 | 适用场景 |
|------|------|--------|---------|
| 0.001s（1ms） | 最高 | 慢（需1000步/秒） | 高精度控制研究 |
| 0.002s（2ms） | 中等 | 适中 | 默认推荐值 |
| 0.005s（5ms） | 较低 | 快（200步/秒） | 快速训练 |

**Franka Panda 关节限位**：

```python
"""
Franka Panda 关节限位
"""
# Franka Panda 各关节的运动范围（单位：弧度）
panda_joint_limits = {
    'joint_1': (-2.8973, 2.8973),    # 基座旋转
    'joint_2': (-1.7628, 1.7628),    # 肩部俯仰
    'joint_3': (-2.8973, 2.8973),    # 肩部侧摆
    'joint_4': (-3.0718, -0.0698),   # 肘部俯仰（注意负值范围）
    'joint_5': (-2.8973, 2.8973),    # 腕部侧摆
    'joint_6': (-0.0175, 3.7525),    # 腕部俯仰
    'joint_7': (-2.8973, 2.8973),    # 腕部旋转
}

print("Franka Panda 关节限位（弧度）:")
for joint, (low, high) in panda_joint_limits.items():
    range_deg = (high - low) * 180 / np.pi
    print(f"  {joint}: [{low:+.4f}, {high:+.4f}] ≈ {range_deg:.1f}°")
```

---

## 3. 任务定义

### 3.1 开关门操作

**柜门操作**是 Franka Kitchen 中最基础的任务类型之一。柜门通过**旋转关节**连接在柜体上，关节角度从 0°（关闭）到 90°（完全打开）。

**开门任务定义**：

```python
"""
开门任务
"""
class OpenCabinetTask:
    """
    打开指定柜门任务
    """

    def __init__(self, cabinet_name, target_angle=np.pi/2):
        """
        Args:
            cabinet_name: 柜门名称（如 'cabinet_door_1'）
            target_angle: 目标打开角度（弧度），默认 90°
        """
        self.cabinet_name = cabinet_name
        self.target_angle = target_angle  # 90度 = 完全打开
        self.joint_id = None

    def get_state(self, data):
        """获取当前柜门角度"""
        # 通过 Mujoco 的 qpos 数组获取关节位置
        # joint_id 需要通过模型查找
        current_angle = data.qpos[self.joint_id] if self.joint_id else 0
        return current_angle

    def check_success(self, data):
        """检查任务是否成功"""
        current_angle = self.get_state(data)
        # 成功条件：当前角度达到目标角度的 90% 以上
        success = current_angle >= 0.9 * self.target_angle
        return success

    def get_reward(self, data):
        """
        reward shaping: 给予逐步引导奖励
        奖励与当前角度占目标角度的比例成正比
        """
        current_angle = self.get_state(data)
        progress = np.clip(current_angle / self.target_angle, 0, 1)
        # 奖励 = 进度比例，最大为 1.0
        reward = progress
        return reward


# 示例：创建开门任务
open_cabinet_task = OpenCabinetTask(
    cabinet_name='cabinet_door_1',
    target_angle=np.pi / 2  # 90度
)
print(f"开门任务: {open_cabinet_task.cabinet_name}")
print(f"目标角度: {open_cabinet_task.target_angle:.2f} rad ({open_cabinet_task.target_angle * 180 / np.pi:.1f}°)")
```

**关门任务定义**：

关门是开门的逆操作，目标角度为 0°。但在物理仿真中，由于摩擦和阻尼的存在，关门任务往往比开门更困难——柜门可能在目标位置附近震荡。

```python
"""
关门任务（带阻尼震荡处理）
"""
class CloseCabinetTask:
    """
    关闭指定柜门任务
    关门比开门更难：需要精确控制以避免震荡
    """

    def __init__(self, cabinet_name, target_angle=0.0, tolerance=0.05):
        """
        Args:
            cabinet_name: 柜门名称
            target_angle: 目标角度（弧度），默认 0 = 关闭
            tolerance: 容差（弧度），角度在 target ± tolerance 内视为成功
        """
        self.cabinet_name = cabinet_name
        self.target_angle = target_angle
        self.tolerance = tolerance

    def check_success(self, data):
        """检查关门是否成功（带容差判断）"""
        current_angle = data.qpos[self.joint_id]
        # 必须满足两个条件：
        # 1. 角度接近目标
        # 2. 角速度足够小（避免在目标位置震荡）
        angle_ok = abs(current_angle - self.target_angle) < self.tolerance
        velocity_ok = abs(data.qvel[self.joint_id]) < 0.1  # rad/s
        return angle_ok and velocity_ok
```

### 3.2 抽屉操作

**抽屉操作**是 Franka Kitchen 中的另一类核心任务。与柜门不同，抽屉通过**滑动关节**（slide joint）实现线性运动。

**抽屉关节运动示意**：

```
    柜体
┌──────────┐
│          │
│  ┌────┐  │
│  │抽屉│──┼──→ 沿 X 轴滑动
│  └────┘  │
│          │
└──────────┘
     ↑
   joint: type="slide", axis="1 0 0"
```

**抽屉操作任务定义**：

```python
"""
抽屉操作任务
"""
class DrawerTask:
    """
    抽屉操作任务（拉开或关闭）
    """

    def __init__(self, drawer_name, target_position, tolerance=0.02):
        """
        Args:
            drawer_name: 抽屉名称（如 'drawer_1'）
            target_position: 目标位置（米），如 0.3 表示完全拉出
            tolerance: 容差（米）
        """
        self.drawer_name = drawer_name
        self.target_position = target_position
        self.tolerance = tolerance
        self.joint_id = None

    def get_position(self, data):
        """获取当前抽屉位置（沿滑动轴的距离）"""
        return data.qpos[self.joint_id] if self.joint_id else 0

    def check_success(self, data):
        """检查抽屉是否到达目标位置"""
        current_pos = self.get_position(data)
        return abs(current_pos - self.target_position) < self.tolerance

    def get_reward(self, data):
        """奖励塑形：距离奖励 + 成功奖励"""
        current_pos = self.get_position(data)
        distance = abs(current_pos - self.target_position)
        # 距离奖励：越接近目标，奖励越高
        distance_reward = 1.0 - (distance / self.target_position) if self.target_position > 0 else 1.0
        # 成功奖励
        success_reward = 10.0 if self.check_success(data) else 0.0
        return distance_reward + success_reward


# 示例：拉出抽屉任务
open_drawer_task = DrawerTask(
    drawer_name='drawer_1',
    target_position=0.3,  # 拉出 0.3 米
    tolerance=0.02        # 2cm 容差
)
print(f"抽屉任务: {open_drawer_task.drawer_name}")
print(f"目标位置: {open_drawer_task.target_position:.3f} m")
```

### 3.3 物体移动

物体移动是更具挑战性的任务，需要机器人先**抓取**物体，再**搬运**到目标位置，最后**释放**。

**物体移动任务分解**：

| 子步骤 | 操作 | 技术挑战 |
|--------|------|---------|
| **1. 接近** | 移动夹爪到物体上方 | 视觉定位、运动规划 |
| **2. 抓取** | 闭合夹爪，包裹物体 | 抓取姿态选择、力控 |
| **3. 抬起** | 垂直提升物体 | 负载稳定性、夹爪保持 |
| **4. 搬运** | 水平移动到目标上方 | 轨迹平滑、避障 |
| **5. 放置** | 下放并释放物体 | 位置精度、释放时机 |
| **6. 撤离** | 夹爪离开物体区域 | 安全撤离 |

```python
"""
物体移动任务
"""
class MoveObjectTask:
    """
    物体抓取并移动到目标位置任务
    """

    def __init__(self, object_name, target_position, grasp_offset=0.05):
        """
        Args:
            object_name: 物体名称
            target_position: 目标放置位置 [x, y, z]（米）
            grasp_offset: 抓取时夹爪与物体的偏移量
        """
        self.object_name = object_name
        self.target_position = np.array(target_position)
        self.grasp_offset = grasp_offset
        self.object_id = None

        # 任务阶段
        self.phase = 'approach'  # 'approach' | 'grasp' | 'lift' | 'transport' | 'place' | 'done'
        self.grasp_success = False

    def get_object_position(self, data):
        """获取物体当前世界坐标"""
        # Mujoco 中通过 geom 或 body 获取物体位置
        # 这里简化表示
        return data.body(self.object_name).xpos if self.object_id else np.zeros(3)

    def get_reward(self, data):
        """分层奖励函数"""
        object_pos = self.get_object_position(data)
        target_pos = self.target_position
        distance_to_target = np.linalg.norm(object_pos - target_pos)

        if self.phase == 'approach':
            # 接近阶段：奖励与目标距离成比例
            return 1.0 - min(distance_to_target, 1.0)

        elif self.phase == 'grasp':
            # 抓取阶段：夹爪已接触物体
            return 2.0 if self.grasp_success else 1.0

        elif self.phase == 'lift':
            # 抬起阶段：物体高度应增加
            lift_height = object_pos[2]
            return 1.0 + lift_height * 10

        elif self.phase == 'transport':
            # 搬运阶段：靠近目标位置
            progress = 1.0 - (distance_to_target / 0.5)  # 假设初始距离 < 0.5m
            return 2.0 + np.clip(progress, 0, 1)

        elif self.phase == 'place':
            # 放置阶段：距离目标足够近
            if distance_to_target < 0.05:
                self.phase = 'done'
                return 10.0  # 成功奖励
            return 1.0

        else:  # 'done'
            return 10.0

    def check_success(self, data):
        """检查任务是否成功"""
        object_pos = self.get_object_position(data)
        distance = np.linalg.norm(object_pos - self.target_position)
        # 成功条件：物体中心距离目标位置 < 5cm
        return distance < 0.05 and self.phase == 'done'
```

### 3.4 组合任务

**组合任务**是 Franka Kitchen 的核心评测形式。组合任务由多个原子操作按特定顺序组成，只有当**所有步骤都成功**时，任务才算完成。

**组合任务示例**：

```python
"""
组合任务定义
"""
class KitchenCompositeTask:
    """
    Franka Kitchen 组合任务
    由多个原子操作按顺序组成
    """

    def __init__(self, name, subtasks):
        """
        Args:
            name: 任务名称
            subtasks: 子任务列表，每个元素为任务对象
        """
        self.name = name
        self.subtasks = subtasks
        self.current_subtask_idx = 0

    def get_current_subtask(self):
        """获取当前执行的子任务"""
        if self.current_subtask_idx < len(self.subtasks):
            return self.subtasks[self.current_subtask_idx]
        return None

    def advance_subtask(self):
        """推进到下一个子任务"""
        self.current_subtask_idx += 1
        print(f"  → 进入子任务 {self.current_subtask_idx + 1}: {self.get_current_subtask().__class__.__name__}")

    def step(self, data):
        """
        执行一步组合任务
        返回：(reward, done, info)
        """
        current_task = self.get_current_subtask()

        if current_task is None:
            # 所有子任务完成
            return 10.0, True, {'success': True, 'completed_subtasks': len(self.subtasks)}

        # 执行当前子任务
        reward = current_task.get_reward(data)
        success = current_task.check_success(data)

        if success:
            self.advance_subtask()

        return reward, False, {'current_subtask': current_task.__class__.__name__, 'success': success}

    def check_overall_success(self):
        """检查所有子任务是否完成"""
        return self.current_subtask_idx >= len(self.subtasks)


# 示例：创建"打开柜门 → 拉抽屉 → 关闭柜门"组合任务
composite_task = KitchenCompositeTask(
    name="Kitchen_Mission_1",
    subtasks=[
        OpenCabinetTask(cabinet_name='cabinet_door_1', target_angle=np.pi/2),
        DrawerTask(drawer_name='drawer_1', target_position=0.3),
        CloseCabinetTask(cabinet_name='cabinet_door_1', target_angle=0.0),
    ]
)

print(f"组合任务: {composite_task.name}")
print(f"子任务数量: {len(composite_task.subtasks)}")
for i, task in enumerate(composite_task.subtasks):
    print(f"  {i+1}. {task.__class__.__name__}")
```

**状态依赖关系**：

组合任务中的子任务往往存在**状态依赖**，这增加了任务规划和执行的复杂度：

| 依赖类型 | 示例 | 约束 |
|---------|------|------|
| **物理依赖** | 必须先打开柜门才能拿取内部物体 | 物体在关闭时不可达 |
| **空间依赖** | 拉抽屉时夹爪必须在抽屉前方 | 位置约束 |
| **时序依赖** | 必须在开门后一定时间内完成取物 | 时间窗口 |
| **状态依赖** | 关闭抽屉前必须先推入抽屉 | 抽屉必须先完全拉出才能关闭 |

---

## 4. 观测与动作

### 4.1 关节空间

**关节空间控制**是最直接的控制方式，直接指定每个关节的目标角度或关节速度。

**Franka Panda 关节空间描述**：

| 关节 | 名称 | 类型 | 控制模式 | 典型值范围 |
|------|------|------|---------|-----------|
| 0 | joint_1 | 旋转 | 位置/力矩 | [-2.9, 2.9] rad |
| 1 | joint_2 | 旋转 | 位置/力矩 | [-1.8, 1.8] rad |
| 2 | joint_3 | 旋转 | 位置/力矩 | [-2.9, 2.9] rad |
| 3 | joint_4 | 旋转 | 位置/力矩 | [-3.1, -0.07] rad |
| 4 | joint_5 | 旋转 | 位置/力矩 | [-2.9, 2.9] rad |
| 5 | joint_6 | 旋转 | 位置/力矩 | [-0.02, 3.75] rad |
| 6 | joint_7 | 旋转 | 位置/力矩 | [-2.9, 2.9] rad |

**关节空间观测**：

```python
"""
关节空间观测
"""
def get_joint_observation(data):
    """
    获取关节空间观测

    Returns:
        joint_obs: 关节观测字典，包含：
            - qpos: 各关节位置（弧度）
            - qvel: 各关节速度（弧度/秒）
            - qtorqe: 各关节力矩（Nm）
    """
    joint_obs = {
        'qpos': data.qpos[:7].copy(),    # 关节位置
        'qvel': data.qvel[:7].copy(),    # 关节速度
        'qtorque': data.qfrc_actuator[:7].copy(),  # 关节力矩
    }
    return joint_obs


def print_joint_state(data):
    """打印当前关节状态"""
    joint_obs = get_joint_observation(data)

    print("\n" + "=" * 60)
    print("Franka Panda 关节状态")
    print("=" * 60)
    print(f"{'关节':<10} {'位置(rad)':>15} {'速度(rad/s)':>15} {'力矩(Nm)':>15}")
    print("-" * 60)

    for i in range(7):
        print(
            f"joint_{i+1:<3} "
            f"{joint_obs['qpos'][i]:>15.4f} "
            f"{joint_obs['qvel'][i]:>15.4f} "
            f"{joint_obs['qtorque'][i]:>15.4f}"
        )
    print("=" * 60)
```

**关节空间动作**：

```python
"""
关节空间动作接口
"""
def compute_joint_position_control(data, target_positions, kp=1.0, ki=0.0, kd=0.1):
    """
    计算关节位置控制力矩
    使用 PD 控制器

    Args:
        data: Mujoco 数据对象
        target_positions: 目标关节位置（弧度），长度为 7
        kp: 比例增益
        ki: 积分增益
        kd: 微分增益

    Returns:
        torques: 关节控制力矩（Nm）
    """
    # 当前状态
    current_q = data.qpos[:7]
    current_qd = data.qvel[:7]

    # 位置误差
    error = target_positions - current_q

    # 累积误差（用于积分项）
    # 实际中需要维护误差积分状态
    # error_integral += error * dt

    # PD 控制力矩
    torques = kp * error - kd * current_qd

    # Franka Panda 关节力矩限制
    max_torque = 87.0  # Nm（关节1-4）, 12.0 Nm（关节5-7）
    torques = np.clip(torques,
                      np.array([-87, -87, -87, -87, -12, -12, -12]),
                      np.array([87, 87, 87, 87, 12, 12, 12]))

    return torques
```

### 4.2 任务空间

**任务空间控制**直接控制末端执行器（夹爪）的位置和姿态，更符合人类的操作直觉。

**任务空间描述**：

末端执行器的状态由**位置**（3维）和**姿态**（3维，用欧拉角或四元数表示）组成，共 6 维：

$$
\mathbf{x} = [x, y, z, \phi, \theta, \psi]^T
$$

**末端执行器观测**：

```python
"""
任务空间（末端执行器）观测
"""
import numpy as np


def get_end_effector_observation(data):
    """
    获取末端执行器（夹爪）观测

    Returns:
        ee_obs: 末端执行器观测字典
            - position: 位置 [x, y, z]（米）
            - orientation: 姿态（欧拉角 [roll, pitch, yaw]，弧度）
            - linear_velocity: 线速度 [vx, vy, vz]（米/秒）
            - angular_velocity: 角速度 [wx, wy, wz]（弧度/秒）
    """
    # 末端执行器的位置（世界坐标系）
    # Franka Panda 的末端执行器 body 名称通常为 'right_hand'
    ee_pos = data.body('right_hand').xpos.copy()  # [x, y, z]

    # 末端执行器的姿态（世界坐标系，用四元数表示）
    ee_quat = data.body('right_hand').xquat.copy()  # [w, x, y, z]

    # 转换为欧拉角（ZYX 顺序，即 yaw-pitch-roll）
    ee_euler = np.zeros(3)
    ee_euler[0] = np.arctan2(2*(ee_quat[0]*ee_quat[1] + ee_quat[2]*ee_quat[3]),
                              1 - 2*(ee_quat[1]**2 + ee_quat[2]**2))  # roll
    ee_euler[1] = np.arcsin(2*(ee_quat[0]*ee_quat[2] - ee_quat[3]*ee_quat[1]))  # pitch
    ee_euler[2] = np.arctan2(2*(ee_quat[0]*ee_quat[3] + ee_quat[1]*ee_quat[2]),
                              1 - 2*(ee_quat[2]**2 + ee_quat[3]**2))  # yaw

    # 末端执行器线速度和角速度
    ee_vel = data.body('right_hand').cvel.copy()  # [vx, vy, vz, wx, wy, wz]

    ee_obs = {
        'position': ee_pos,               # [x, y, z] 世界坐标
        'orientation': ee_euler,           # [roll, pitch, yaw] 欧拉角
        'quaternion': ee_quat,             # [w, x, y, z] 四元数
        'linear_velocity': ee_vel[:3],     # [vx, vy, vz] 米/秒
        'angular_velocity': ee_vel[3:],    # [wx, wy, wz] 弧度/秒
    }

    return ee_obs


def print_ee_state(data):
    """打印末端执行器状态"""
    ee_obs = get_end_effector_observation(data)

    print("\n" + "=" * 60)
    print("末端执行器状态")
    print("=" * 60)
    print(f"位置 (m):     [{ee_obs['position'][0]:.4f}, {ee_obs['position'][1]:.4f}, {ee_obs['position'][2]:.4f}]")
    print(f"姿态 (deg):    [{ee_obs['orientation'][0]*180/np.pi:.2f}, "
          f"{ee_obs['orientation'][1]*180/np.pi:.2f}, "
          f"{ee_obs['orientation'][2]*180/np.pi:.2f}]")
    print(f"线速度 (m/s): [{ee_obs['linear_velocity'][0]:.4f}, {ee_obs['linear_velocity'][1]:.4f}, {ee_obs['linear_velocity'][2]:.4f}]")
    print(f"角速度 (rad/s): [{ee_obs['angular_velocity'][0]:.4f}, {ee_obs['angular_velocity'][1]:.4f}, {ee_obs['angular_velocity'][2]:.4f}]")
    print("=" * 60)
### 4.3 视觉输入

Franka Kitchen 环境提供**相机视角渲染**，可获取 RGB 图像和深度图像作为视觉观测。

**相机配置**：

| 相机 | 位置 | 视角 | 用途 |
|------|------|------|------|
| **前向相机** | 场景正前方 | 宽视角 | 物体定位、目标识别 |
| **腕部相机** | 夹爪附近 | 窄视角 | 精细抓取、接近检测 |
| **顶视相机** | 场景上方 | 俯视图 | 整体布局感知 |

**视觉观测获取**：

```python
"""
视觉观测获取
"""
import mujoco
import numpy as np


def render_rgb_image(model, data, camera_name='front'):
    """
    渲染 RGB 图像

    Args:
        model: Mujoco 模型对象
        data: Mujoco 数据对象
        camera_name: 相机名称（需在 XML 中定义）

    Returns:
        rgb_image: RGB 图像数组，shape=(height, width, 3)，dtype=uint8
    """
    # 获取相机 ID
    camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)

    # 创建渲染器
    renderer = mujoco.Renderer(model, height=480, width=640)

    # 渲染当前帧
    renderer.update_scene(data, camera=camera_id)
    rgb_image = renderer.render()

    return rgb_image


def render_depth_image(model, data, camera_name='front'):
    """
    渲染深度图像

    Args:
        model: Mujoco 模型对象
        data: Mujoco 数据对象
        camera_name: 相机名称

    Returns:
        depth_image: 深度图像数组，shape=(height, width, 1)，值域 [0, 1]
    """
    # 获取相机 ID
    camera_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, camera_name)

    # 创建渲染器
    renderer = mujoco.Renderer(model, height=480, width=640)

    # 渲染深度图
    renderer.update_scene(data, camera=camera_id)
    depth_image = renderer.render(depth=True)

    return depth_image


def get_visual_observation(model, data, camera_names=None):
    """
    获取完整视觉观测

    Args:
        model: Mujoco 模型对象
        data: Mujoco 数据对象
        camera_names: 相机名称列表，默认 ['front', 'wrist']

    Returns:
        visual_obs: 视觉观测字典
    """
    if camera_names is None:
        camera_names = ['front', 'wrist']

    visual_obs = {}

    for camera_name in camera_names:
        try:
            rgb = render_rgb_image(model, data, camera_name)
            depth = render_depth_image(model, data, camera_name)
            visual_obs[camera_name] = {
                'rgb': rgb,
                'depth': depth
            }
            print(f"  ✓ 相机 {camera_name}: RGB {rgb.shape}, Depth {depth.shape}")
        except Exception as e:
            print(f"  ✗ 相机 {camera_name} 不可用: {e}")

    return visual_obs
```

---

## 5. 数据集

### 5.1 人类演示数据

Franka Kitchen 环境配套的**人类演示数据集**是模仿学习研究的重要资源。演示数据通常通过**远程操控**（teleoperation）或**VR 示教**等方式采集。

**数据采集方式**：

| 方式 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **6-DOF 遥控手柄** | 使用游戏手柄控制机器人 | 操作简单 | 精度较低 |
| **VR 示教** | 使用 VR 手柄记录人手动作 | 自然直观 | 设备昂贵 |
| **动捕手套** | 通过数据手套记录关节角度 | 精度高 | 设备复杂 |
| **直接示教** | 人工引导机械臂移动 | 最直观 | 仅限物理机器人 |

**数据集规模**：

| 数据集 | 轨迹数 | 任务数 | 演示/任务 | 采集者 |
|--------|--------|--------|-----------|--------|
| **Franka Kitchen Demo（社区版）** | ~500 | 30+ | 10-20 | 社区贡献 |
| **MT-ACT** | 8,735 | 87 | 100+ | 斯坦福等 |
| **Bridge Dataset** | 7,216 | 52 | ~140 | UC Berkeley |

### 5.2 轨迹格式

Franka Kitchen 的轨迹数据以 **NumPy .npz 格式**存储，包含每次演示的完整状态-动作序列。

**轨迹数据结构**：

```python
"""
轨迹数据格式
"""
import numpy as np
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class TrajectoryStep:
    """
    单步轨迹数据
    """
    # 观测
    joint_positions: np.ndarray      # 关节位置 (7,)
    joint_velocities: np.ndarray    # 关节速度 (7,)
    joint_torques: np.ndarray       # 关节力矩 (7,)
    ee_position: np.ndarray          # 末端位置 (3,)
    ee_orientation: np.ndarray       # 末端姿态 (4,) 四元数
    object_states: np.ndarray        # 物体状态（各关节角度/位置）

    # 动作
    action: np.ndarray               # 动作向量 (7,) - 关节位置增量或笛卡尔增量

    # 元信息
    reward: float                    # 奖励值
    task_name: str                   # 当前任务名称
    subtask_index: int               # 子任务索引


@dataclass
class Trajectory:
    """
    一条完整演示轨迹
    """
    task_name: str                   # 任务名称
    steps: List[TrajectoryStep]      # 轨迹步骤列表
    total_reward: float              # 总奖励
    success: bool                    # 是否成功完成

    @property
    def length(self):
        """轨迹长度（步数）"""
        return len(self.steps)

    def get_observations(self):
        """获取所有观测"""
        obs = {
            'joint_positions': [],
            'joint_velocities': [],
            'ee_position': [],
            'object_states': []
        }
        for step in self.steps:
            obs['joint_positions'].append(step.joint_positions)
            obs['joint_velocities'].append(step.joint_velocities)
            obs['ee_position'].append(step.ee_position)
            obs['object_states'].append(step.object_states)
        return {k: np.array(v) for k, v in obs.items()}

    def get_actions(self):
        """获取所有动作"""
        return np.array([step.action for step in self.steps])


def load_trajectory(npz_path: str) -> Trajectory:
    """
    从 npz 文件加载轨迹

    Args:
        npz_path: .npz 文件路径

    Returns:
        trajectory: Trajectory 对象
    """
    data = np.load(npz_path)

    # npz 文件中的字段（示例）
    required_keys = [
        'observations/joint_positions',
        'observations/joint_velocities',
        'observations/ee_position',
        'actions',
        'rewards',
        'task_name'
    ]

    steps = []
    n_steps = len(data['actions'])

    for i in range(n_steps):
        step = TrajectoryStep(
            joint_positions=data['observations/joint_positions'][i],
            joint_velocities=data['observations/joint_velocities'][i],
            joint_torques=data.get('observations/joint_torques', np.zeros(7))[i],
            ee_position=data['observations/ee_position'][i],
            ee_orientation=data.get('observations/ee_orientation', np.zeros(4))[i],
            object_states=data.get('observations/object_states', np.zeros(10))[i],
            action=data['actions'][i],
            reward=data.get('rewards', np.zeros(n_steps))[i],
            task_name=str(data.get('task_name', 'unknown')),
            subtask_index=data.get('subtask_indices', np.zeros(n_steps))[i]
        )
        steps.append(step)

    trajectory = Trajectory(
        task_name=str(data.get('task_name', 'unknown')),
        steps=steps,
        total_reward=sum(s.reward for s in steps),
        success=data.get('success', False)
    )

    return trajectory


# 示例：加载并分析轨迹
print("=" * 60)
print("Franka Kitchen 轨迹格式示例")
print("=" * 60)

# 假设已有轨迹数据
sample_trajectory_info = {
    '任务': 'open_cabinet_and_drawer',
    '总步数': 250,
    '成功标志': True,
    '每步数据结构': {
        '观测': '关节位置(7) + 关节速度(7) + 末端位置(3) + 物体状态(10)',
        '动作': '关节位置增量(7)',
        '奖励': '标量'
    },
    '文件大小估算': '~5 KB/条轨迹（未压缩）'
}

for key, val in sample_trajectory_info.items():
    print(f"  {key}: {val}")
```

### 5.3 数据规模

**Franka Kitchen 数据集规模与任务复杂度**：

| 任务类型 | 难度 | 推荐演示数 | 轨迹总步数 | 适用算法 |
|---------|------|-----------|-----------|---------|
| 单步开门 | L1 | 20-50 | 5k-10k | 行为克隆（BC） |
| 两步组合 | L2 | 50-100 | 20k-50k | BC + RNN |
| 三步组合 | L3 | 100-200 | 50k-100k | BC + Attention / GAIL |
| 复杂长序列 | L4 | 200-500+ | 100k+ | RRL / Diffusion Policy |

**数据效率关键指标**：

```python
"""
数据效率分析
"""
import numpy as np


def compute_data_efficiency(n_demos, success_rate, task_complexity):
    """
    计算数据效率指标

    Args:
        n_demos: 演示数量
        success_rate: 评测成功率
        task_complexity: 任务复杂度（子任务数量）

    Returns:
        efficiency_metrics: 效率指标字典
    """
    # 每条演示的期望成功次数
    expected_successes = n_demos * success_rate

    # 达到 80% 成功率所需的估计演示数（线性外推）
    if success_rate > 0:
        demos_for_80 = int(0.8 * n_demos / success_rate)
    else:
        demos_for_80 = float('inf')

    # 复杂度调整系数（长序列任务需要更多数据）
    complexity_factor = task_complexity / 1.0  # 基准为单步任务

    metrics = {
        'n_demos': n_demos,
        'success_rate': success_rate,
        'expected_successes': expected_successes,
        'demos_for_80pct': demos_for_80,
        'complexity_adjusted_demos': int(n_demos * complexity_factor),
        'steps_per_demo': 200,  # 假设每条轨迹 200 步
        'total_training_steps': n_demos * 200
    }

    return metrics


# 示例：分析不同数据规模下的效率
for n_demos in [50, 100, 200, 500]:
    for sr in [0.3, 0.5, 0.7]:
        metrics = compute_data_efficiency(n_demos, sr, task_complexity=3)
        print(f"演示数={n_demos:>4}, SR={sr:.1%} → "
              f"期望成功={metrics['expected_successes']:>5.1f}, "
              f"达到80%需={metrics['demos_for_80pct']:>5}")
        print()
```

---

## 6. 代码实战

### 6.1 环境加载

```python
"""
Franka Kitchen 环境加载与初始化
"""
import mujoco
import numpy as np


def load_kitchen_environment(xml_path="kitchen.xml"):
    """
    加载 Franka Kitchen 仿真环境

    Args:
        xml_path: MJCF XML 模型文件路径

    Returns:
        model: Mujoco 模型对象
        data: Mujoco 数据对象
    """
    try:
        # 尝试加载用户指定路径
        model = mujoco.MjModel.from_xml_path(xml_path)
        print(f"✓ 成功加载模型: {xml_path}")
    except FileNotFoundError:
        print(f"✗ 文件未找到: {xml_path}，使用内置厨房模型")
        # 使用 Franka Kitchen 内置 MJCF 字符串
        # 简化版模型，实际请用完整 XML
        kitchen_xml = """
        <mujoco model="kitchen">
            <compiler angle="radian"/>
            <option timestep="0.002"/>

            <worldbody>
                <!-- 地面 -->
                <geom name="floor" type="plane" size="5 5 0.1" rgba="0.8 0.8 0.8 1"/>

                <!-- Franka Panda（简化模型） -->
                <body name="panda" pos="0 0 0">
                    <!-- 底座 -->
                    <geom name="panda_base" type="cylinder" size="0.1 0.1" pos="0 0 0.05"/>
                    <!-- 关节（简化串联结构） -->
                    <joint name="joint1" type="hinge" axis="0 0 1" range="-2.9 2.9"/>
                    <body name="link1" pos="0 0 0.3">
                        <geom name="link1_geom" type="cylinder" size="0.05 0.15"/>
                        <joint name="joint2" type="hinge" axis="0 1 0" range="-1.8 1.8"/>
                        <body name="link2" pos="0 0 0.3">
                            <geom name="link2_geom" type="cylinder" size="0.04 0.12"/>
                            <joint name="joint3" type="hinge" axis="0 1 0" range="-2.9 2.9"/>
                            <body name="link3" pos="0 0 0.3">
                                <geom name="link3_geom" type="cylinder" size="0.04 0.12"/>
                                <joint name="joint4" type="hinge" axis="0 1 0" range="-3.1 -0.07"/>
                                <body name="link4" pos="0 0 0.3">
                                    <geom name="link4_geom" type="cylinder" size="0.03 0.1"/>
                                    <joint name="joint5" type="hinge" axis="0 0 1" range="-2.9 2.9"/>
                                    <body name="right_hand" pos="0 0 0.2">
                                        <geom name="gripper" type="box" size="0.03 0.04 0.02"/>
                                    </body>
                                </body>
                            </body>
                        </body>
                    </body>
                </body>

                <!-- 柜门（可旋转） -->
                <body name="cabinet_door" pos="1.0 0 0.5">
                    <joint name="cabinet_hinge" type="hinge" axis="0 1 0" range="0 1.57"/>
                    <geom name="cabinet_door_geom" type="box" size="0.4 0.02 0.4" rgba="0.6 0.4 0.2 1"/>
                </body>

                <!-- 抽屉（可滑动） -->
                <body name="drawer" pos="1.0 0 0.3">
                    <joint name="drawer_slide" type="slide" axis="1 0 0" range="0 0.3"/>
                    <geom name="drawer_geom" type="box" size="0.3 0.2 0.1" rgba="0.7 0.5 0.3 1"/>
                </body>
            </worldbody>
        </mujoco>
        """
        model = mujoco.MjModel.from_xml_string(kitchen_xml)

    # 创建仿真数据
    data = mujoco.MjData(model)

    # 打印环境信息
    print_environment_info(model, data)

    return model, data


def print_environment_info(model, data):
    """打印环境基本信息"""
    print("\n" + "=" * 50)
    print("Franka Kitchen 环境信息")
    print("=" * 50)
    print(f"模型名称: {model.name}")
    print(f"物体数量: {model.nbody}")
    print(f"关节数量: {model.njnt}")
    print(f"自由度数量: {model.nq}")  # generalized coordinates
    print(f"仿真步长: {model.opt.timestep * 1000:.2f} ms")
    print("=" * 50)


def run_environment_demo():
    """环境演示：创建环境并运行几步仿真"""
    print("\n" + "=" * 60)
    print("Franka Kitchen 环境演示")
    print("=" * 60)

    # 加载环境
    model, data = load_kitchen_environment()

    # 重置仿真
    mujoco.mj_resetData(model, data)

    # 设置 Franka Panda 初始姿态（准备姿态）
    # 7 个关节的目标角度
    init_joint_positions = np.array([0.0, -0.79, 0.0, -2.36, 0.0, 1.57, 0.79])
    data.qpos[:7] = init_joint_positions
    mujoco.mj_step(model, data)

    print("\n初始状态:")
    print(f"  关节位置: {[f'{j:.3f}' for j in data.qpos[:7]]}")
    print(f"  仿真时间: {data.time:.3f} s")

    # 运行仿真循环
    print("\n运行仿真循环 (100 步)...")
    for step in range(100):
        mujoco.mj_step(model, data)

        if step % 20 == 0:
            print(f"  步 {step:>3}: time={data.time:.3f}s, "
                  f"qpos[0]={data.qpos[0]:.3f}")

    print(f"\n✓ 仿真完成，总步数={step+1}, 时间={data.time:.3f}s")

    return model, data


if __name__ == "__main__":
    run_environment_demo()
```

### 6.2 任务执行

```python
"""
Franka Kitchen 任务执行示例
"""
import mujoco
import numpy as np


class FrankaKitchenSimulator:
    """
    Franka Kitchen 仿真器封装
    提供高层任务执行接口
    """

    def __init__(self, model, data):
        self.model = model
        self.data = data

        # 查找关节 ID
        self.joint_ids = {}
        for i in range(model.njnt):
            joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
            if joint_name:
                self.joint_ids[joint_name] = i

        print(f"✓ FrankaKitchenSimulator 初始化完成")
        print(f"  关节列表: {list(self.joint_ids.keys())}")

    def get_state(self):
        """获取完整环境状态"""
        return {
            'time': self.data.time,
            'qpos': self.data.qpos.copy(),
            'qvel': self.data.qvel.copy(),
            'joint_positions': self.data.qpos[:7].copy(),
            'ee_position': self.data.body('right_hand').xpos.copy() if 'right_hand' in [
                mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_BODY, i)
                for i in range(self.model.nbody)] else self.data.qpos[:3].copy(),
        }

    def set_joint_positions(self, positions, duration=0.5, steps=None):
        """
        设置目标关节位置并执行（开环控制）

        Args:
            positions: 目标关节位置（弧度），长度 7
            duration: 执行时长（秒）
            steps: 仿真步数（如果指定，忽略 duration）
        """
        if steps is None:
            steps = int(duration / self.model.opt.timestep)

        # 线性插值到目标位置
        start_positions = self.data.qpos[:7].copy()
        for step in range(steps):
            alpha = (step + 1) / steps
            target = start_positions * (1 - alpha) + positions * alpha
            self.data.ctrl[:7] = target
            mujoco.mj_step(self.model, self.data)

    def open_cabinet_door(self, door_name='cabinet_door', duration=1.0):
        """
        打开柜门

        Args:
            door_name: 柜门名称
            duration: 执行时长（秒）
        """
        if door_name not in self.joint_ids:
            print(f"✗ 找不到柜门: {door_name}")
            return False

        joint_id = self.joint_ids[door_name]
        start_angle = self.data.qpos[joint_id]
        target_angle = np.pi / 2  # 90 度

        print(f"\n打开柜门: {door_name}")
        print(f"  起始角度: {start_angle:.3f} rad")
        print(f"  目标角度: {target_angle:.3f} rad")

        steps = int(duration / self.model.opt.timestep)
        for step in range(steps):
            alpha = (step + 1) / steps
            # 缓动函数（平滑加速减速）
            alpha = alpha * alpha * (3 - 2 * alpha)  # smoothstep
            self.data.qpos[joint_id] = start_angle + (target_angle - start_angle) * alpha
            mujoco.mj_step(self.model, self.data)

        print(f"  完成角度: {self.data.qpos[joint_id]:.3f} rad")
        return True

    def pull_drawer(self, drawer_name='drawer', distance=0.3, duration=1.0):
        """
        拉出抽屉

        Args:
            drawer_name: 抽屉名称
            distance: 拉出距离（米）
            duration: 执行时长（秒）
        """
        if drawer_name not in self.joint_ids:
            print(f"✗ 找不到抽屉: {drawer_name}")
            return False

        joint_id = self.joint_ids[drawer_name]
        start_pos = self.data.qpos[joint_id]
        target_pos = start_pos + distance

        print(f"\n拉出抽屉: {drawer_name}")
        print(f"  起始位置: {start_pos:.3f} m")
        print(f"  目标位置: {target_pos:.3f} m")

        steps = int(duration / self.model.opt.timestep)
        for step in range(steps):
            alpha = (step + 1) / steps
            alpha = alpha * alpha * (3 - 2 * alpha)
            self.data.qpos[joint_id] = start_pos + (target_pos - start_pos) * alpha
            mujoco.mj_step(self.model, self.data)

        print(f"  完成位置: {self.data.qpos[joint_id]:.3f} m")
        return True

    def execute_composite_task(self, task_sequence):
        """
        执行组合任务

        Args:
            task_sequence: 任务序列，每个元素为 (task_type, task_params) 元组

        Returns:
            results: 执行结果字典
        """
        results = {
            'total_tasks': len(task_sequence),
            'completed': 0,
            'failed': 0,
            'task_results': []
        }

        print("\n" + "=" * 60)
        print(f"执行组合任务（共 {len(task_sequence)} 个子任务）")
        print("=" * 60)

        for i, (task_type, params) in enumerate(task_sequence):
            print(f"\n[{i+1}/{len(task_sequence)}] 执行: {task_type}")

            try:
                if task_type == 'open_cabinet':
                    success = self.open_cabinet_door(**params)
                elif task_type == 'pull_drawer':
                    success = self.pull_drawer(**params)
                else:
                    print(f"  ✗ 未知任务类型: {task_type}")
                    success = False

                results['task_results'].append({'task': task_type, 'success': success})
                if success:
                    results['completed'] += 1
                    print(f"  ✓ 子任务完成")
                else:
                    results['failed'] += 1
                    print(f"  ✗ 子任务失败")

            except Exception as e:
                results['task_results'].append({'task': task_type, 'success': False, 'error': str(e)})
                results['failed'] += 1
                print(f"  ✗ 子任务异常: {e}")

        print("\n" + "=" * 60)
        print(f"组合任务完成: {results['completed']}/{results['total_tasks']} 成功")
        print("=" * 60)

        return results


def run_task_execution():
    """运行任务执行演示"""
    import mujoco

    # 创建简化模型
    kitchen_xml = """
    <mujoco model="kitchen">
        <compiler angle="radian"/>
        <option timestep="0.002"/>
        <worldbody>
            <geom name="floor" type="plane" size="5 5 0.1"/>
            <body name="cabinet_door" pos="1.0 0 0.5">
                <joint name="cabinet_door" type="hinge" axis="0 1 0" range="0 1.57"/>
                <geom name="cabinet_door_geom" type="box" size="0.4 0.02 0.4" rgba="0.6 0.4 0.2 1"/>
            </body>
            <body name="drawer" pos="1.0 0 0.3">
                <joint name="drawer" type="slide" axis="1 0 0" range="0 0.3"/>
                <geom name="drawer_geom" type="box" size="0.3 0.2 0.1" rgba="0.7 0.5 0.3 1"/>
            </body>
        </worldbody>
    </mujoco>
    """

    model = mujoco.MjModel.from_xml_string(kitchen_xml)
    data = mujoco.MjData(model)

    # 创建仿真器
    sim = FrankaKitchenSimulator(model, data)

    # 定义任务序列：开门 → 拉抽屉
    task_sequence = [
        ('open_cabinet', {'door_name': 'cabinet_door', 'duration': 1.0}),
        ('pull_drawer', {'drawer_name': 'drawer', 'distance': 0.3, 'duration': 1.0}),
    ]

    # 执行组合任务
    results = sim.execute_composite_task(task_sequence)

    return results


if __name__ == "__main__":
    run_task_execution()
```

### 6.3 数据采集

```python
"""
Franka Kitchen 数据采集
用于模仿学习训练数据收集
"""
import mujoco
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple
import json
import time


@dataclass
class DataCollectionConfig:
    """数据采集配置"""
    task_name: str                      # 任务名称
    output_dir: str = "./data"          # 输出目录
    max_steps_per_traj: int = 500       # 每条轨迹最大步数
    target_num_demos: int = 50          # 目标采集数量
    save_frequency: int = 10            # 每采集多少条保存一次
    include_images: bool = False        # 是否包含图像（增大存储）
    include_force: bool = True          # 是否包含力矩数据


class FrankaKitchenDataCollector:
    """
    Franka Kitchen 数据采集器
    记录每个时间步的观测和动作
    """

    def __init__(self, model, data, config: DataCollectionConfig):
        self.model = model
        self.data = data
        self.config = config

        # 轨迹缓冲区
        self.current_traj = {
            'observations': [],
            'actions': [],
            'rewards': [],
            'dones': [],
            'infos': []
        }

        # 所有轨迹列表
        self.all_trajectories = []

        # 统计信息
        self.stats = {
            'total_steps': 0,
            'total_trajectories': 0,
            'successful_trajectories': 0
        }

        # 关节 ID 映射
        self.joint_ids = {}
        for i in range(model.njnt):
            name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
            if name:
                self.joint_ids[name] = i

        print(f"✓ 数据采集器初始化完成")
        print(f"  任务: {config.task_name}")
        print(f"  目标演示数: {config.target_num_demos}")
        print(f"  最大步数/轨迹: {config.max_steps_per_traj}")

    def reset_trajectory(self):
        """重置当前轨迹缓冲区"""
        self.current_traj = {
            'observations': [],
            'actions': [],
            'rewards': [],
            'dones': [],
            'infos': []
        }

    def collect_step(self, action: np.ndarray, reward: float = 0.0,
                     info: Dict = None, done: bool = False):
        """
        记录单步数据

        Args:
            action: 动作向量
            reward: 奖励值
            info: 额外信息字典
            done: 是否结束
        """
        # 采集观测
        observation = self._collect_observation()

        # 存入缓冲区
        self.current_traj['observations'].append(observation)
        self.current_traj['actions'].append(action.copy())
        self.current_traj['rewards'].append(reward)
        self.current_traj['dones'].append(done)
        self.current_traj['infos'].append(info or {})

        self.stats['total_steps'] += 1

    def _collect_observation(self) -> Dict:
        """采集当前观测"""
        obs = {
            # 时间
            'time': self.data.time,

            # 关节状态（7 维）
            'joint_positions': self.data.qpos[:7].copy(),
            'joint_velocities': self.data.qvel[:7].copy(),

            # 力矩数据
            'joint_torques': self.data.qfrc_actuator[:7].copy() if self.config.include_force else np.zeros(7),

            # 末端执行器（尝试获取）
            'ee_position': np.zeros(3),
            'ee_orientation': np.zeros(4),
        }

        # 尝试获取末端执行器信息
        try:
            obs['ee_position'] = self.data.body('right_hand').xpos.copy()
            obs['ee_orientation'] = self.data.body('right_hand').xquat.copy()
        except Exception:
            pass

        # 采集场景中可交互物体的状态
        obs['interactive_objects'] = self._get_object_states()

        return obs

    def _get_object_states(self) -> Dict[str, float]:
        """获取场景中可交互物体的状态"""
        object_states = {}

        for obj_name in ['cabinet_door', 'drawer']:
            if obj_name in self.joint_ids:
                joint_id = self.joint_ids[obj_name]
                object_states[obj_name] = float(self.data.qpos[joint_id])

        return object_states

    def finish_trajectory(self, success: bool = False):
        """
        结束当前轨迹采集

        Args:
            success: 轨迹是否成功完成
        """
        traj_data = {
            'task_name': self.config.task_name,
            'success': success,
            'num_steps': len(self.current_traj['observations']),
            'total_reward': sum(self.current_traj['rewards']),

            # 转换为 numpy 数组
            'observations': {
                'joint_positions': np.array([o['joint_positions'] for o in self.current_traj['observations']]),
                'joint_velocities': np.array([o['joint_velocities'] for o in self.current_traj['observations']]),
                'joint_torques': np.array([o['joint_torques'] for o in self.current_traj['observations']]),
                'ee_position': np.array([o['ee_position'] for o in self.current_traj['observations']]),
                'time': np.array([o['time'] for o in self.current_traj['observations']]),
            },
            'actions': np.array(self.current_traj['actions']),
            'rewards': np.array(self.current_traj['rewards']),
            'infos': self.current_traj['infos']
        }

        self.all_trajectories.append(traj_data)
        self.stats['total_trajectories'] += 1
        if success:
            self.stats['successful_trajectories'] += 1

        print(f"  轨迹 {self.stats['total_trajectories']} 完成: "
              f"步数={traj_data['num_steps']}, "
              f"奖励={traj_data['total_reward']:.2f}, "
              f"成功={success}")

        # 清空当前轨迹缓冲区
        self.reset_trajectory()

        # 定期保存
        if self.stats['total_trajectories'] % self.config.save_frequency == 0:
            self.save_data()

    def save_data(self, filepath: str = None):
        """
        保存采集的数据到磁盘

        Args:
            filepath: 保存路径（可选）
        """
        import os

        if filepath is None:
            filepath = os.path.join(
                self.config.output_dir,
                f"{self.config.task_name}_trajectories.npz"
            )

        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

        # 准备保存的数据
        save_data = {
            'task_name': self.config.task_name,
            'num_trajectories': len(self.all_trajectories),
            'total_steps': self.stats['total_steps'],
            'success_rate': self.stats['successful_trajectories'] / max(1, len(self.all_trajectories)),
            'trajectories': self.all_trajectories
        }

        # 使用 np.savez 保存
        # 注意：大型数据建议使用 HDF5
        np.savez(filepath, **save_data)

        print(f"\n✓ 数据已保存: {filepath}")
        print(f"  轨迹数: {save_data['num_trajectories']}")
        print(f"  总步数: {save_data['total_steps']}")
        print(f"  成功率: {save_data['success_rate']:.2%}")

        return filepath

    def print_stats(self):
        """打印采集统计"""
        print("\n" + "=" * 50)
        print("数据采集统计")
        print("=" * 50)
        print(f"总步数: {self.stats['total_steps']}")
        print(f"总轨迹数: {self.stats['total_trajectories']}")
        print(f"成功轨迹数: {self.stats['successful_trajectories']}")
        print(f"成功率: {self.stats['successful_trajectories'] / max(1, self.stats['total_trajectories']):.2%}")
        print("=" * 50)


def demonstrate_data_collection():
    """数据采集演示"""
    print("\n" + "=" * 60)
    print("Franka Kitchen 数据采集演示")
    print("=" * 60)

    # 创建模型（简化版）
    kitchen_xml = """
    <mujoco model="kitchen">
        <compiler angle="radian"/>
        <option timestep="0.002"/>
        <worldbody>
            <geom name="floor" type="plane" size="5 5 0.1"/>
            <body name="cabinet_door" pos="1.0 0 0.5">
                <joint name="cabinet_door" type="hinge" axis="0 1 0" range="0 1.57"/>
                <geom name="cabinet_door_geom" type="box" size="0.4 0.02 0.4"/>
            </body>
            <body name="drawer" pos="1.0 0 0.3">
                <joint name="drawer" type="slide" axis="1 0 0" range="0 0.3"/>
                <geom name="drawer_geom" type="box" size="0.3 0.2 0.1"/>
            </body>
        </worldbody>
    </mujoco>
    """

    model = mujoco.MjModel.from_xml_string(kitchen_xml)
    data = mujoco.MjData(model)

    # 配置数据采集
    config = DataCollectionConfig(
        task_name="open_cabinet_and_drawer",
        output_dir="/tmp/franka_kitchen_data",
        target_num_demos=5,
        max_steps_per_traj=300
    )

    # 创建采集器
    collector = FrankaKitchenDataCollector(model, data, config)

    # 模拟采集 5 条轨迹
    print("\n开始模拟数据采集（5 条轨迹）...")

    for traj_idx in range(5):
        mujoco.mj_resetData(model, data)
        collector.reset_trajectory()

        print(f"\n--- 轨迹 {traj_idx + 1} ---")

        # 模拟：开环执行任务 + 添加随机动作
        for step in range(config.max_steps_per_traj):
            # 模拟动作（实际从策略或人类获取）
            action = np.random.randn(7) * 0.1

            # 执行一步
            mujoco.mj_step(model, data)

            # 模拟奖励（实际根据任务计算）
            reward = -0.01  # 每步小惩罚

            # 模拟成功判断
            done = (step >= config.max_steps_per_traj - 1)

            # 记录数据
            collector.collect_step(action, reward, done=done)

        # 结束轨迹
        success = (np.random.rand() < 0.7)  # 模拟 70% 成功率
        collector.finish_trajectory(success)

    # 打印统计并保存
    collector.print_stats()

    # 保存最终数据
    collector.save_data()


if __name__ == "__main__":
    demonstrate_data_collection()

---

## 7. 练习题

### 选择题

**1. Franka Panda 机械臂的自由度（DOF）是多少？**
- A. 4 DOF
- B. 6 DOF
- C. 7 DOF
- D. 8 DOF

**2. Franka Kitchen 环境使用哪种物理仿真引擎？**
- A. PyBullet
- B. Drake
- C. Mujoco
- D. Gazebo

**3. 在 Franka Kitchen 中，抽屉操作对应的关节类型是？**
- A. hinge（旋转关节）
- B. slide（滑动关节）
- C. ball（球形关节）
- D. free（自由关节）

**4. 下列哪种观测不属于 Franka Kitchen 的关节空间观测？**
- A. qpos（关节位置）
- B. qvel（关节速度）
- C. rgb（相机图像）
- D. qfrc_actuator（关节力矩）

**5. Franka Panda 的腕部关节（joint_4）的运动范围特点是什么？**
- A. 对称范围，如 [-2.9, 2.9]
- B. 非对称范围，主要是负值 [-3.07, -0.07]
- C. 固定角度，不可动
- D. 范围最大，超过 ±3.0 弧度

### 简答题

**6. 解释为什么在 Franka Kitchen 中，组合任务（如"开门 → 拉抽屉 → 关门"）比单步任务（如"只开门"）更难完成，并说明这种难度来自哪些方面。**

**7. 说明 Franka Panda 的 7 个关节中，各关节的运动轴向和作用，并分析为什么 7-DOF 设计对执行厨房操作任务特别重要。**

**8. 对比关节空间控制和任务空间控制两种控制方式，分析它们在 Franka Kitchen 任务执行中的优缺点。**

**9. 设计一个 Franka Kitchen 的模仿学习数据采集流程，包括：采集方式选择、轨迹格式定义、质量控制方法、数据增强策略。**

---

## 8. 练习题答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **C** | Franka Panda 是 7 自由度协作机械臂，7 个关节均为旋转关节，构型与人类手臂相似。 |
| 2 | **C** | Franka Kitchen 环境基于 Mujoco 物理引擎构建，利用 MJCF XML 格式定义场景和机器人模型。 |
| 3 | **B** | 抽屉沿线性轨道滑动，对应 Mujoco 的 `type="slide"` 关节；而柜门沿轴旋转，对应 `type="hinge"`。 |
| 4 | **C** | `rgb` 图像属于视觉观测，而关节空间观测包含 `qpos`（位置）、`qvel`（速度）、`qfrc_actuator`（力矩）。视觉输入属于另一类观测。 |
| 5 | **B** | Franka Panda 的 joint_4（肘部）运动范围是非对称的 `[-3.0718, -0.0698]` 弧度，主要覆盖负角度区域，这与肘部关节的解剖学约束有关。 |

### 简答题答案

**6. 组合任务难度分析**

组合任务比单步任务更难完成，主要来自以下几个方面：

| 难度来源 | 说明 |
|---------|------|
| **误差累积** | 每一步操作都有误差，长序列的总体成功率是各步概率的乘积。若每步 80% 成功，3 步序列仅为 $0.8^3 = 51.2\%$ |
| **状态依赖** | 组合任务中后续任务依赖前期状态。例如必须先打开柜门，才能执行"从柜内取物"；若开门失败，后续步骤无法进行 |
| **动作衔接** | 各步骤之间的过渡动作需要平滑衔接，切换过早或过晚都会导致失败 |
| **规划复杂度** | 越长序列需要考虑的可能性越多，规划和决策空间指数增长 |
| **恢复困难** | 一旦某步失败，中间状态可能使后续步骤无法执行或需要额外恢复动作 |

在 Franka Kitchen 中，这种难度体现得尤为明显——例如"拉抽屉"任务只有在柜门已打开的状态下，夹爪才能无碰撞地接近抽屉把手。

---

**7. Franka Panda 7-DOF 关节设计与厨房操作的重要性**

**各关节运动轴向与作用**：

| 关节 | 轴向 | 主要作用 |
|------|------|---------|
| joint_1 | 绕 Z 轴（垂直） | 基座旋转，实现水平面 360° 旋转 |
| joint_2 | 绕 Y 轴（前后） | 肩部俯仰，控制手臂上下高度 |
| joint_3 | 绕 Y 轴 | 肩部侧摆，内收/外展 |
| joint_4 | 绕 Y 轴 | 肘部俯仰，最强力的关节 |
| joint_5 | 绕 Z 轴 | 腕部侧摆，调整末端姿态 |
| joint_6 | 绕 Y 轴 | 腕部俯仰 |
| joint_7 | 绕 Z 轴 | 腕部旋转（精细调整夹爪朝向） |

**7-DOF 对厨房操作的重要性**：

**1. 运动学冗余**：7 个自由度超过了完成空间定位所需的 6 个（3 位置 + 3 姿态），产生冗余度。这使得机器人在执行操作时可以通过多种关节配置达到同一末端位置，从而避开障碍物或优化关节角度。

**2. 关节限位避让**：冗余度允许机器人在某个关节接近限位时，通过重新分配各关节的运动来继续完成任务，这对于受限空间内的厨房操作至关重要。

**3. 灵活的任务空间执行**：做"拉抽屉"这样的任务时，7-DOF 可以让夹爪沿抽屉方向移动，同时保持合适的接触力——这在 6-DOF 机械臂上往往难以实现。

---

**8. 关节空间控制 vs 任务空间控制**

| 维度 | 关节空间控制 | 任务空间控制 |
|------|-------------|-------------|
| **控制量** | 目标关节角度/速度 | 末端执行器位置/姿态 |
| **维度** | 7 维 | 6 维（位置 3 + 姿态 3） |
| **直观性** | 低（需要理解各关节） | 高（直接反映操作意图） |
| **逆运动学** | 无需 IK（直接给定关节值） | 需要 IK 解算 |
| **避障能力** | 弱（需额外规划） | 可结合任务空间约束 |
| **力控精度** | 高（直接控制关节力矩） | 较低（需转换） |
| **轨迹平滑性** | 取决于关节插值方式 | 自然平滑（直线/圆弧） |
| **适用场景** | 精确姿态控制、力控任务 | 目标接近、抓取放置 |

**在 Franka Kitchen 中的应用建议**：

- **开门/拉抽屉**：使用任务空间控制，让夹爪沿目标方向（直线）运动
- **精细调整（如对准钥匙孔）**：切换到关节空间微调
- **力控操作（如擦拭台面）**：使用关节力矩控制模式

混合使用两种控制模式，结合运动基元（Motion Primitives）切换，是 Franka Kitchen 任务执行的常见策略。

---

**9. Franka Kitchen 模仿学习数据采集流程设计**

**采集方式选择**：

| 方式 | 推荐场景 | 工具 |
|------|---------|------|
| **VR 示教** | 精确演示、多样轨迹 | Oculus + Unity 或 Robocouch |
| **动捕手套** | 高精度关节角度采集 | xsens MVN 或诺亦腾 |
| **6-DOF 手柄** | 快速采集原型数据 | Xbox/PS 手柄 + 自定义映射 |
| **直接示教** | 仅限物理机器人 | 无额外设备 |

**推荐方案**：VR 示教（高质量）+ 6-DOF 手柄（快速补充）

**轨迹格式定义**：

```python
trajectory_format = {
    'task_name': str,                    # 任务名称
    'demonstrator_id': str,               # 演示者 ID
    'timestamp': float,                   # 采集时间戳
    'observations': {
        'joint_positions': np.ndarray,    # (T, 7) 关节位置
        'joint_velocities': np.ndarray,  # (T, 7) 关节速度
        'ee_position': np.ndarray,       # (T, 3) 末端位置
        'ee_orientation': np.ndarray,     # (T, 4) 末端四元数
        'object_states': np.ndarray,     # (T, N) N个物体状态
    },
    'actions': np.ndarray,                # (T, 7) 动作（关节增量或笛卡尔）
    'rewards': np.ndarray,                # (T,) 每步奖励
    'success': bool,                      # 是否成功完成
    'quality_score': float                # 轨迹质量评分 (1-5)
}
```

**质量控制方法**：

| 检查项 | 方法 | 处理 |
|--------|------|------|
| **任务完成** | 自动检测最终状态 | 失败轨迹单独标记或丢弃 |
| **轨迹平滑度** | 加速度阈值检测 | 平滑滤波或丢弃 |
| **动作幅度** | 异常大动作检测 | 人工复查 |
| **演示者一致性** | 多演示者轨迹对比 | 异常者复查 |
| **碰撞检测** | 仿真器接触力检测 | 碰撞段标记或丢弃 |

**数据增强策略**：

| 策略 | 方法 | 适用场景 |
|------|------|---------|
| **观测噪声注入** | 添加高斯噪声到关节传感器 | 提升策略鲁棒性 |
| **动作延迟模拟** | 随机延迟 1-3 步 | 真实机器人部署 |
| **初始状态扰动** | 在任务可行域内随机初始 | 提升泛化能力 |
| **时序增广** | 截断轨迹作为 BC 演示起点 | 加速早期学习 |
| **多模态融合** | 同一状态添加不同动作标签 | 解决多解性问题 |

---

## 本章小结

| 概念 | 要点 |
|------|------|
| **Franka Panda** | 7-DOF 协作机械臂，高精度、灵敏力控、开放接口 |
| **Mujoco** | DeepMind 开源物理仿真引擎，MJCF XML 定义场景 |
| **Franka Kitchen** | 基于 Mujoco 的厨房多任务仿真环境，评测长时序操作 |
| **柜门/抽屉操作** | 柜门=旋转关节（hinge），抽屉=滑动关节（slide） |
| **关节空间观测** | qpos（位置）、qvel（速度）、qfrc_actuator（力矩） |
| **任务空间观测** | 末端位置（3D）、姿态（四元数/欧拉角）、线速度、角速度 |
| **视觉输入** | RGB 图像 + 深度图像，通过相机渲染获取 |
| **轨迹格式** | NumPy npz，包含观测序列、动作序列、奖励序列 |
| **组合任务** | 多步操作链，存在状态依赖和误差累积 |
| **数据采集** | VR 示教/手柄采集 → 质量控制 → 格式标准化 → 保存 |

**延伸学习资源**：
- Franka Emika 官方文档: `https://frankaemika.github.io/`
- Mujoco 文档: `https://mujoco.readthedocs.io/`
- Franka Kitchen GitHub: `https://github.com/AGentin/franka_kitchen`
- Franka Panda MJCF 模型: `https://github.com/google-deepmind/mujoco Menagerie`
- MT-ACT 数据集: `https://arxiv.org/abs/2304.12205`
