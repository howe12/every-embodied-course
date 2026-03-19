# 07-6 MuJoCo仿真

> **前置课程**：07-5 Isaac Sim环境部署
> **后续课程**：待定

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：MuJoCo（Multi-Joint Dynamics with Contact）是一款专业的机器人仿真引擎，以其精确的物理仿真和高效的计算性能著称。相比Gazebo，MuJoCo提供了更真实的物理接触建模能力和更快的仿真速度。本节将详细介绍MuJoCo的安装部署、XML模型定义、ROS2集成以及机器人仿真实例，帮助你掌握这款强大的仿真工具。

---

## 1. MuJoCo概述

MuJoCo是由DeepMind开发的一款开源物理引擎，专门为机器人学、强化学习和生物力学研究设计。与其他仿真引擎相比，MuJoCo具有以下几个显著优势。

### 1.1 核心特性

**精确的物理仿真**：MuJoCo采用基于优化的求解器，能够精确处理多关节动力学和复杂接触力。其核心求解器基于稀疏坐标松弛（sparse coordinate relaxation）和主动集（active set）算法，可以在保证精度的同时实现实时仿真。

**统一的接触模型**：MuJoCo使用统一的弹性接触模型，通过阻尼弹簧系统模拟所有类型的接触。这种方法避免了传统仿真器中不同接触类型需要不同处理的问题，使得接触力计算更加一致和可预测。

**高效的计算性能**：MuJoCo的计算效率很高，能够在普通硬件上实现数千帧每秒的仿真速度。这对于需要大量样本的强化学习训练尤为重要。

**开源免费**：MuJoCo自2021年被DeepMind收购后开源，目前免费提供给学术和商业使用，降低了研究门槛。

### 1.2 应用场景

MuJoCo广泛应用于以下领域：

| 领域 | 应用说明 |
|------|----------|
| 机器人控制 | 双足行走、manipulation、无人机控制 |
| 强化学习 | 策略训练、Sim-to-Real迁移 |
| 生物力学 | 人体运动分析、动物行为研究 |
| 运动规划 | 碰撞检测、运动优化 |

### 1.3 与Gazebo的对比

| 特性 | MuJoCo | Gazebo |
|------|--------|--------|
| 物理精度 | 高 | 中 |
| 计算速度 | 快 | 慢 |
| 接触模型 | 统一弹性模型 | 多模型混合 |
| ROS集成 | 通过mujoco_ros_pkgs | 原生支持 |
| 可视化 | 内置查看器 | 依赖Gazebo GUI |
| 传感器噪声 | 可配置 | 插件化 |

---

## 2. 安装部署

MuJoCo的安装相对简单，可以通过二进制包或源码编译两种方式获取。下面分别介绍在Linux系统上的安装步骤。

### 2.1 通过apt安装（推荐）

```bash
# 安装MuJoCo
sudo apt install libmujoco-py python3-mujoco

# 验证安装
python3 -c "import mujoco; print(mujoco.__version__)"
```

### 2.2 通过pip安装

```bash
# 安装mujoco-py（Python绑定）
pip install mujoco

# 验证安装
python3 -c "import mujoco; print('MuJoCo installed successfully')"
```

### 2.3 安装MuJoCo环境变量

MuJoCo需要设置环境变量指向其数据目录：

```bash
# 写入~/.bashrc
echo 'export MUJOCO_DATA=/usr/share/mujoco/mujoco_py/mujoco_data' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/share/mujoco/mujoco_py/mujoco_v210_linux' >> ~/.bashrc

# 重新加载
source ~/.bashrc
```

### 2.4 安装mujoco_ros_pkgs（ROS2集成）

ROS2与MuJoCo的集成通过`mujoco_ros_pkgs`包实现：

```bash
# 创建ROS2工作空间
mkdir -p ~/ros2_mujoco/src
cd ~/ros2_mujoco

# 克隆mujoco_ros_pkgs
git clone https://github.com/mujoco-ros/mujoco_ros_pkg.git src/mujoco_ros_pkg

# 安装依赖
rosdep install --from-paths src --ignore-src -r -y

# 编译
colcon build --symlink-install

# 设置环境
source install/setup.bash
```

### 2.5 安装MuJoCo Viewer（可视化）

MuJoCo自带了3D查看器，也可以使用更现代的`mujoco-viewer`：

```bash
# 安装mujoco-viewer
pip install mujoco-viewer

# 使用示例
python3 -c "
import mujoco
import mujoco.viewer

model = mujoco.load_model('/usr/share/mujoco/mujoco200/model/humanoid.xml')
data = mujoco.MjData(model)
with mujoco.viewer.launch_passive(model, data) as viewer:
    for _ in range(1000):
        mujoco.mj_step(model, data)
        viewer.sync()
"
```

---

## 3. XML模型定义

MuJoCo使用XML格式的模型文件（`.xml`）来描述物理世界、机器人和环境。本节详细介绍XML模型的结构和常用元素。

### 3.1 基本结构

一个完整的MuJoCo模型文件包含以下几个主要部分：

```xml
<mujoco model="robot_model">
    <!-- 编译器配置 -->
    <compiler/>
    
    <!-- 全局选项 -->
    <option/>
    
    <!-- 纹理和网格 -->
    <asset/>
    
    <!-- 世界环境 -->
    <worldbody>
        <!-- 地面 -->
        <!-- 光源 -->
        <!-- 摄像机 -->
    </worldbody>
    
    <!-- 关节驱动 -->
    <actuator/>
    
    <!-- 接触参数 -->
    <contact/>
    
    <!-- 传感器 -->
    <sensor/>
    
    <!-- 绳索和约束 -->
    <tendon/>
    <equality/>
</mujoco>
```

### 3.2 刚体定义

刚体（Body）是MuJoCo模型的基本组成单元，每个刚体可以包含几何形状、惯性参数和子刚体：

```xml
<!-- 世界body -->
<worldbody>
    <!-- 地面 -->
    <geom type="plane" size="10 10 0.1" rgba="0.5 0.5 0.5 1"/>
    
    <!-- 机器人基座 -->
    <body name="base" pos="0 0 0.5">
        <!-- 惯性参数 -->
        <inertial pos="0 0 0" mass="10" diaginertia="0.1 0.1 0.1"/>
        
        <!-- 可视化几何 -->
        <geom type="cylinder" size="0.2 0.05" rgba="1 0 0 1"/>
        
        <!-- 子刚体：关节连接 -->
        <body name="link1" pos="0 0 0.1">
            <inertial pos="0 0 0" mass="2" diaginertia="0.01 0.01 0.01"/>
            <joint name="joint1" type="hinge" axis="0 1 0" damping="0.5"/>
            <geom type="box" size="0.05 0.05 0.1" rgba="0 1 0 1"/>
        </body>
    </body>
</worldbody>
```

### 3.3 关节类型

MuJoCo支持多种关节类型：

| 类型 | 说明 | 自由度 |
|------|------|--------|
| `free` | 自由关节（6DOF） | 6 |
| `ball` | 球关节（3DOF） | 3 |
| `hinge` | 铰链关节（1DOF旋转） | 1 |
| `slide` | 滑动关节（1DOF平移） | 1 |
| `planar` | 平面关节（2DOF） | 2 |
| `fixed` | 固定关节（0DOF） | 0 |

**铰链关节示例**：

```xml
<!-- 旋转关节 -->
<joint name="shoulder_joint" type="hinge" 
       pos="0 0 0" axis="0 0 1" 
       range="-3.14 3.14" 
       damping="0.1" frictionloss="0.01"/>

<!-- 带电机驱动的关节 -->
<joint name="elbow_joint" type="hinge" 
       pos="0 0.2 0" axis="1 0 0" 
       range="-2.5 2.5" 
       damping="0.2" frictionloss="0.02"
       actuator="motor1"/>
```

**滑动关节示例**：

```xml
<!-- 线性关节 -->
<joint name="prismatic_joint" type="slide" 
       pos="0 0 0" axis="0 1 0" 
       range="-0.5 0.5" 
       damping="0.3"/>
```

### 3.4 驱动器定义

驱动器（Actuator）用于控制关节运动：

```xml
<!-- 简单电机 -->
<actuator>
    <!-- 位置控制电机 -->
    <motor name="shoulder_motor" joint="shoulder_joint" 
           ctrllimited="true" ctrlrange="-100 100" 
           gear="100"/>
    
    <!-- 速度控制电机 -->
    <velocity name="elbow_velocity" joint="elbow_joint" 
              ctrllimited="true" ctrlrange="-10 10" 
              gear="50"/>
    
    <!-- 液压缸 -->
    <cylinder name="linear_actuator" joint="prismatic_joint" 
              ctrllimited="true" ctrlrange="-50 50" 
              gear="200"/>
</actuator>
```

### 3.5 接触参数

MuJoCo使用统一的接触模型，相关参数在`<contact>`元素中定义：

```xml
<contact>
    <!-- 全局接触参数 -->
    <global friction="1.0 0.005 0.0001" 
            restitution="0.1" 
            precision="1e-6"/>
    
    <!-- 特定geom的接触参数 -->
    <!-- 通过geom的condim和friction属性设置 -->
</contact>
```

**geom级别的接触设置**：

```xml
<geom type="box" size="0.1 0.1 0.1" 
      friction="1.5 0.01 0.0001" 
      restitution="0.2" 
      condim="4"/>
```

其中`condim`表示接触维度：
- 1：法向力
- 3：法向力+切向力
- 4：法向力+两个切向力+扭矩

### 3.6 传感器定义

MuJoCo支持丰富的传感器类型：

```xml
<sensor>
    <!-- 关节位置传感器 -->
    <jointpos name="joint1_pos" joint="joint1"/>
    
    <!-- 关节速度传感器 -->
    <jointvel name="joint1_vel" joint="joint1"/>
    
    <!-- 关节扭矩传感器 -->
    <jointactuatorfrc name="joint1_act" joint="joint1"/>
    
    <!-- 加速度计 -->
    <accelerometer name="imu_acc" 
                   site="imu_site" 
                   noise="0.01"/>
    
    <!-- 陀螺仪 -->
    <gyro name="imu_gyro" 
          site="imu_site" 
          noise="0.001"/>
    
    <!-- 力传感器 -->
    <force name="contact_force" 
           site="force_sensor_site"/>
    
    <!-- 触觉传感器 -->
    <touch name="touch_sensor" 
           geom="gripper_contact"/>
</sensor>
```

### 3.7 完整模型示例：二自由度机械臂

下面是一个完整的二自由度机械臂模型：

```xml
<mujoco model="2dof_arm">
    <!-- 编译器配置 -->
    <compiler angle="radian" 
              meshdir="meshes" 
              autolimits="true"/>
    
    <!-- 全局选项 -->
    <option timestep="0.002" 
            iterations="100" 
            solver="Newton" 
            gravity="0 0 -9.81"/>
    
    <!-- 资产定义 -->
    <asset>
        <mesh file="link.stl"/>
        <texture type="2d" file="texture.png" 
                 name="tex"/>
    </asset>
    
    <!-- 世界 -->
    <worldbody>
        <!-- 灯光 -->
        <light diffuse=".5 .5 .5" 
               pos="0 0 3" 
               dir="0 0 -1"/>
        
        <!-- 地面 -->
        <geom type="plane" 
              size="2 2 0.1" 
              rgba="0.3 0.3 0.3 1"/>
        
        <!-- 基座 -->
        <body name="base" pos="0 0 0.3">
            <inertial pos="0 0 0" 
                      mass="5" 
                      diaginertia="0.1 0.1 0.1"/>
            <geom type="cylinder" 
                  size="0.15 0.1" 
                  rgba="0.5 0.5 0.5 1"/>
            
            <!-- 连杆1 -->
            <body name="link1" pos="0 0 0.1">
                <inertial pos="0 0.15 0" 
                          mass="2" 
                          diaginertia="0.01 0.05 0.01"/>
                <joint name="joint1" 
                       type="hinge" 
                       axis="0 1 0" 
                       pos="0 0 0" 
                       range="-3.14 3.14" 
                       damping="0.1"/>
                <geom type="box" 
                      size="0.05 0.15 0.05" 
                      pos="0 0.15 0" 
                      rgba="1 0 0 1"/>
                
                <!-- 连杆2 -->
                <body name="link2" pos="0 0.3 0">
                    <inertial pos="0 0.1 0" 
                              mass="1" 
                              diaginertia="0.005 0.02 0.005"/>
                    <joint name="joint2" 
                           type="hinge" 
                           axis="0 1 0" 
                           pos="0 0 0" 
                           range="-3.14 3.14" 
                           damping="0.1"/>
                    <geom type="box" 
                          size="0.04 0.1 0.04" 
                          pos="0 0.1 0" 
                          rgba="0 1 0 1"/>
                    
                    <!-- 末端执行器 -->
                    <body name="ee" pos="0 0.2 0">
                        <geom type="sphere" 
                              size="0.03" 
                              rgba="0 0 1 1"/>
                    </body>
                </body>
            </body>
        </body>
    </worldbody>
    
    <!-- 驱动器 -->
    <actuator>
        <motor name="motor1" 
               joint="joint1" 
               ctrllimited="true" 
               ctrlrange="-50 50" 
               gear="100"/>
        <motor name="motor2" 
               joint="joint2" 
               ctrllimited="true" 
               ctrlrange="-30 30" 
               gear="80"/>
    </actuator>
    
    <!-- 传感器 -->
    <sensor>
        <jointpos name="q1" joint="joint1"/>
        <jointpos name="q2" joint="joint2"/>
        <jointvel name="dq1" joint="joint1"/>
        <jointvel name="dq2" joint="joint2"/>
    </sensor>
</mujoco>
```

---

## 4. ROS2集成

将MuJoCo与ROS2集成，可以利用ROS2丰富的工具链和通信机制。本节介绍如何通过`mujoco_ros_pkgs`包实现ROS2与MuJoCo的集成。

### 4.1 架构概述

MuJoCo与ROS2的集成架构如下：

```
┌─────────────────────────────────────────────────────┐
│                   ROS2 生态系统                      │
│   ┌──────────────┐  ┌──────────────┐               │
│   │  ros2_control │  │  ros2_robot  │               │
│   └──────┬───────┘  └──────┬───────┘               │
│          │                 │                        │
│          ▼                 ▼                        │
│   ┌────────────────────────────────┐                │
│   │      mujoco_ros_pkgs          │                │
│   │  ┌────────┐  ┌────────────┐   │                │
│   │  │ bridge │  │ mujoco_hw  │   │                │
│   │  └────────┘  └────────────┘   │                │
│   └────────────────────────────────┘                │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│              MuJoCo 物理引擎                        │
│   ┌──────────────┐  ┌──────────────┐               │
│   │  MjModel     │  │    MjData    │               │
│   │  (静态模型)  │  │  (运行时状态) │               │
│   └──────────────┘  └──────────────┘               │
└─────────────────────────────────────────────────────┘
```

### 4.2 MuJoCo ROS包概述

`mujoco_ros_pkgs`包含以下主要组件：

| 包 | 功能 |
|----|------|
| `mujoco_ros` | 核心ROS接口 |
| `mujoco_ros_control` | 与ros2_control集成 |
| `mujoco_ros_msgs` | 自定义消息类型 |

### 4.3 启动MuJoCo仿真

使用ROS2启动文件启动MuJoCo仿真：

```python
# launch/mujoco_sim.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # MuJoCo仿真节点
        Node(
            package='mujoco_ros',
            executable='mujoco_node',
            name='mujoco_sim',
            parameters=[{
                'model_path': 'package://my_robot_description/mujoco/robot.xml',
                'simulate_real_time': True,
                'publish_frequency': 50.0,
            }],
            output='screen'
        ),
        
        # ROS2控制器
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_trajectory_controller'],
            output='screen'
        ),
    ])
```

### 4.4 MuJoCo硬件接口

使用`ros2_control`与MuJoCo集成：

```xml
<!-- robot.ros2_control.xacro -->
<ros2_control name="mujoco_hardware" type="system">
    <hardware>
        <plugin>mujoco_ros_control/MujocoRos2ControlHardware</plugin>
        <param name="model_path">/path/to/model.xml</param>
    </hardware>
    
    <!-- 关节接口 -->
    <joint name="joint1">
        <command_interface>position</command_interface>
        <state_interface>position</state_interface>
        <state_interface>velocity</state_interface>
    </joint>
    
    <joint name="joint2">
        <command_interface>position</command_interface>
        <state_interface>position</state_interface>
        <state_interface>velocity</state_interface>
    </joint>
</ros2_control>
```

### 4.5 发布传感器数据到ROS2

以下代码演示如何将MuJoCo传感器数据发布到ROS2话题：

```python
#!/usr/bin/env python3
# mujoco_ros_bridge.py

import rclpy
from rclpy.node import Node
import mujoco
from sensor_msgs.msg import JointState

class MuJoCoRosBridge(Node):
    def __init__(self, model_path):
        super().__init__('mujoco_ros_bridge')
        
        # 加载模型
        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)
        
        # ROS2发布者
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)
        
        # 定时器
        self.timer = self.create_timer(0.01, self.publish_callback)
        
        # 关节名称
        self.joint_names = ['joint1', 'joint2']
        
    def publish_callback(self):
        # 仿真一步
        mujoco.mj_step(self.model, self.data)
        
        # 发布关节状态
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        
        # 从MuJoCo获取关节位置和速度
        for i, name in enumerate(self.joint_names):
            joint_id = mujoco.mj_name2id(self.model, 
                                          mujoco.mjtObj.mjOBJ_JOINT, 
                                          name)
            if joint_id >= 0:
                msg.position.append(self.data.qpos[joint_id])
                msg.velocity.append(self.data.qvel[joint_id])
        
        self.joint_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    
    model_path = '/path/to/your/model.xml'
    node = MuJoCoRosBridge(model_path)
    
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

### 4.6 订阅ROS2控制命令

以下代码演示如何订阅ROS2控制命令并应用到MuJoCo：

```python
#!/usr/bin/env python3
# mujoco_controller.py

import rclpy
from rclpy.node import Node
import mujoco
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class MuJoCoController(Node):
    def __init__(self, model_path):
        super().__init__('mujoco_controller')
        
        # 加载模型
        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)
        
        # 目标关节位置
        self.target_positions = {}
        
        # 订阅控制命令
        self.sub = self.create_subscription(
            JointTrajectory,
            '/joint_trajectory_commands',
            self.trajectory_callback,
            10
        )
        
        # 定时器
        self.timer = self.create_timer(0.002, self.control_callback)
        
    def trajectory_callback(self, msg):
        if msg.points:
            # 获取目标位置
            point = msg.points[0]
            for i, name in enumerate(msg.joint_names):
                if i < len(point.positions):
                    self.target_positions[name] = point.positions[i]
    
    def control_callback(self):
        # 仿真一步
        mujoco.mj_step(self.model, self.data)
        
        # 应用PD控制
        for joint_name, target_pos in self.target_positions.items():
            joint_id = mujoco.mj_name2id(self.model, 
                                          mujoco.mjtObj.mjOBJ_JOINT, 
                                          joint_name)
            if joint_id >= 0:
                # 简单的P控制
                kp = 100.0  # 比例增益
                current_pos = self.data.qpos[joint_id]
                error = target_pos - current_pos
                
                # 应用控制力
                if hasattr(self.data, 'ctrl'):
                    self.data.ctrl[joint_id] = kp * error

def main(args=None):
    rclpy.init(args=args)
    
    model_path = '/path/to/your/model.xml'
    node = MuJoCoController(model_path)
    
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

---

## 5. 机器人仿真示例

本节通过两个完整的示例，展示如何使用MuJoCo进行机器人仿真。

### 5.1 示例1：倒立摆控制

倒立摆是控制理论中的经典问题，下面展示如何在MuJoCo中建模并控制倒立摆。

**模型定义（cartpole.xml）**：

```xml
<mujoco model="cartpole">
    <option timestep="0.001" solver="Newton" iterations="20"/>
    
    <worldbody>
        <!-- 地面 -->
        <geom type="plane" size="2 2 0.1" rgba="0.3 0.3 0.3 1"/>
        
        <!-- 轨道 -->
        <body name="cart" pos="0 0 0.2">
            <inertial pos="0 0 0" mass="1" diaginertia="0.01 0.01 0.01"/>
            <joint name="slide" type="slide" axis="1 0 0" range="-1 1"/>
            <geom type="box" size="0.1 0.05 0.03" rgba="1 0 0 1"/>
            
            <!-- 摆杆 -->
            <body name="pole" pos="0 0 0">
                <inertial pos="0 0.3 0" mass="0.1" diaginertia="0.001 0.01 0.001"/>
                <joint name="hinge" type="hinge" axis="0 0 1" range="-3.14 3.14"/>
                <geom type="capsule" fromto="0 0 0 0 0.6 0" 
                      size="0.02" rgba="0 1 0 1"/>
            </body>
        </body>
    </worldbody>
    
    <actuator>
        <motor name="cart_motor" joint="slide" 
               ctrllimited="true" ctrlrange="-20 20" gear="10"/>
    </actuator>
</mujoco>
```

**PD控制器（cartpole_control.py）**：

```python
#!/usr/bin/env python3
import mujoco
import mujoco.viewer
import numpy as np

# 加载模型
model = mujoco.MjModel.from_xml_path('cartpole.xml')
data = mujoco.MjData(model)

# PD控制器参数
kp = 50.0  # 位置增益
kd = 10.0  # 速度增益

# 运行仿真
with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running():
        # 获取状态
        cart_pos = data.qpos[0]
        cart_vel = data.qvel[0]
        pole_angle = data.qpos[1]
        pole_vel = data.qvel[1]
        
        # 计算控制力
        # 目标：保持pole_angle接近0
        force = kp * (-pole_angle) + kd * (-pole_vel)
        
        # 限制控制力
        force = np.clip(force, -20, 20)
        
        # 应用控制力
        data.ctrl[0] = force
        
        # 仿真一步
        mujoco.mj_step(model, data)
        
        # 同步查看器
        viewer.sync()
```

**运行仿真**：

```bash
python3 cartpole_control.py
```

### 5.2 示例2：四足机器人仿真

下面展示一个简化的四足机器人模型及其控制。

**模型定义（quadruped.xml）**：

```xml
<mujoco model="quadruped">
    <compiler angle="degree" autolimits="true"/>
    <option timestep="0.002" solver="Newton" iterations="50"/>
    
    <worldbody>
        <light diffuse=".5 .5 .5" pos="0 0 3" dir="0 0 -1"/>
        <geom type="plane" size="5 5 0.1" rgba="0.3 0.3 0.3 1"/>
        
        <!-- 躯干 -->
        <body name="torso" pos="0 0 0.4">
            <inertial pos="0 0 0" mass="5" diaginertia="0.1 0.2 0.1"/>
            <geom type="box" size="0.3 0.15 0.08" rgba="0.5 0.5 0.5 1"/>
            
            <!-- 腿部（4条） -->
            <!-- 前左腿 -->
            <body name="FL_hip" pos="0.2 0.1 0">
                <joint name="FL_hip_joint" type="hinge" axis="1 0 0" 
                       range="-45 45" damping="0.5"/>
                <inertial pos="0 0.05 0" mass="0.5" diaginertia="0.001 0.005 0.001"/>
                <geom type="capsule" fromto="0 0 0 0 0.1 0" size="0.02" rgba="1 0 0 1"/>
                
                <body name="FL_knee" pos="0 0.1 0">
                    <joint name="FL_knee_joint" type="hinge" axis="1 0 0" 
                           range="-90 0" damping="0.5"/>
                    <inertial pos="0 0.1 0" mass="0.3" diaginertia="0.001 0.005 0.001"/>
                    <geom type="capsule" fromto="0 0 0 0 0.2 0" size="0.015" rgba="1 0.3 0 1"/>
                </body>
            </body>
            
            <!-- 前右腿 -->
            <body name="FR_hip" pos="0.2 -0.1 0">
                <joint name="FR_hip_joint" type="hinge" axis="1 0 0" 
                       range="-45 45" damping="0.5"/>
                <inertial pos="0 0.05 0" mass="0.5" diaginertia="0.001 0.005 0.001"/>
                <geom type="capsule" fromto="0 0 0 0 0.1 0" size="0.02" rgba="0 0 1 1"/>
                
                <body name="FR_knee" pos="0 0.1 0">
                    <joint name="FR_knee_joint" type="hinge" axis="1 0 0" 
                           range="-90 0" damping="0.5"/>
                    <inertial pos="0 0.1 0" mass="0.3" diaginertia="0.001 0.005 0.001"/>
                    <geom type="capsule" fromto="0 0 0 0 0.2 0" size="0.015" rgba="0 0.3 1 1"/>
                </body>
            </body>
            
            <!-- 后左腿 -->
            <body name="BL_hip" pos="-0.2 0.1 0">
                <joint name="BL_hip_joint" type="hinge" axis="1 0 0" 
                       range="-45 45" damping="0.5"/>
                <inertial pos="0 0.05 0" mass="0.5" diaginertia="0.001 0.005 0.001"/>
                <geom type="capsule" fromto="0 0 0 0 0.1 0" size="0.02" rgba="1 0 0 1"/>
                
                <body name="BL_knee" pos="0 0.1 0">
                    <joint name="BL_knee_joint" type="hinge" axis="1 0 0" 
                           range="-90 0" damping="0.5"/>
                    <inertial pos="0 0.1 0" mass="0.3" diaginertia="0.001 0.005 0.001"/>
                    <geom type="capsule" fromto="0 0 0 0 0.2 0" size="0.015" rgba="1 0.3 0 1"/>
                </body>
            </body>
            
            <!-- 后右腿 -->
            <body name="BR_hip" pos="-0.2 -0.1 0">
                <joint name="BR_hip_joint" type="hinge" axis="1 0 0" 
                       range="-45 45" damping="0.5"/>
                <inertial pos="0 0.05 0" mass="0.5" diaginertia="0.001 0.005 0.001"/>
                <geom type="capsule" fromto="0 0 0 0 0.1 0" size="0.02" rgba="0 0 1 1"/>
                
                <body name="BR_knee" pos="0 0.1 0">
                    <joint name="BR_knee_joint" type="hinge" axis="1 0 0" 
                           range="-90 0" damping="0.5"/>
                    <inertial pos="0 0.1 0" mass="0.3" diaginertia="0.001 0.005 0.001"/>
                    <geom type="capsule" fromto="0 0 0 0 0.2 0" size="0.015" rgba="0 0.3 1 1"/>
                </body>
            </body>
        </body>
    </worldbody>
    
    <actuator>
        <motor name="FL_hip_motor" joint="FL_hip_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
        <motor name="FL_knee_motor" joint="FL_knee_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
        <motor name="FR_hip_motor" joint="FR_hip_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
        <motor name="FR_knee_motor" joint="FR_knee_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
        <motor name="BL_hip_motor" joint="BL_hip_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
        <motor name="BL_knee_motor" joint="BL_knee_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
        <motor name="BR_hip_motor" joint="BR_hip_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
        <motor name="BR_knee_motor" joint="BR_knee_joint" ctrllimited="true" ctrlrange="-5 5" gear="20"/>
    </actuator>
</mujoco>
```

**trot步态控制器（quadruped_trot.py）**：

```python
#!/usr/bin/env python3
import mujoco
import mujoco.viewer
import numpy as np
import time

# 加载模型
model = mujoco.MjModel.from_xml_path('quadruped.xml')
data = mujoco.MjData(model)

# 关节索引映射
joint_names = [
    'FL_hip_joint', 'FL_knee_joint',
    'FR_hip_joint', 'FR_knee_joint',
    'BL_hip_joint', 'BL_knee_joint',
    'BR_hip_joint', 'BR_knee_joint'
]

joint_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name) 
             for name in joint_names]

# 步态参数
cycle_time = 0.4  # 步态周期（秒）
step_height = 0.1  # 抬腿高度

def get_phase(t):
    """获取步态相位"""
    return (t % cycle_time) / cycle_time

def compute_trot_gait(t):
    """计算trot步态的目标关节角度"""
    phase = get_phase(t)
    
    # trot步态：对角腿同步
    # FL+BR 站立, FR+BL 摆动
    if phase < 0.5:
        # 站立相
        hip_angle = 0.0
        knee_angle = 0.0
    else:
        # 摆动相 - 使用正弦曲线生成平滑过渡
        swing_phase = (phase - 0.5) * 2 * np.pi
        hip_angle = 0.3 * np.sin(swing, knee_angle = 0.0
    
    # 分配给各腿
    # FL和BR站立，FR和BL摆动
    targets = [0.0] * 8
    targets[0] = hip_angle   # FL_hip
    targets[1] = knee_angle  # FL_knee
    targets[4] = hip_angle   # BL_hip
    targets[5] = knee_angle  # BL_knee
    # FR和BR在对侧相位
    
    return targets

def pd_control(targets):
    """PD控制器"""
    kp = 50.0
    kd = 5.0
    
    for i, joint_id in enumerate(joint_ids):
        if joint_id >= 0:
            current_pos = data.qpos[joint_id]
            current_vel = data.qvel[joint_id]
            error = targets[i] - current_pos
            data.ctrl[i] = kp * error + kd * (-current_vel)

# 运行仿真
start_time = time.time()
with mujoco.viewer.launch_passive(model, data) as viewer:
    while viewer.is_running():
        t = time.time() - start_time
        
        # 计算目标关节角度
        targets = compute_trot_gait(t)
        
        # 应用PD控制
        pd_control(targets)
        
        # 仿真一步
        mujoco.mj_step(model, data)
        
        # 同步查看器
        viewer.sync()
```

运行四足机器人仿真：

```bash
python3 quadruped_trot.py
```

---

## 练习题

### 选择题

1. MuJoCo使用什么格式定义物理模型？
   - A) YAML格式
   - B) XML格式
   - C) JSON格式
   - D) PROTOBUF格式
   
   **答案：B**。MuJoCo使用XML格式的模型文件（`.xml`）来描述物理世界、机器人和环境。

2. 下列哪个关节类型用于旋转关节？
   - A) `slide`
   - B) `hinge`
   - C) `ball`
   - D) `fixed`
   
   **答案：B**。`hinge`是铰链关节，用于1DOF旋转运动。

3. MuJoCo的哪个特性使其特别适合强化学习研究？
   - A) 丰富的3D可视化
   - B) 高效的计算性能
   - C) 完善的ROS集成
   - D) 开放的API接口
   
   **答案：B**。MuJoCo的高效计算性能使其能够实现数千帧每秒的仿真速度，非常适合需要大量样本的强化学习训练。

### 实践题

4. 创建一个单摆（pendulum）模型，并编写PD控制器使其保持垂直平衡。
   
   **参考答案**：
   
   模型文件（pendulum.xml）：
   
   ```xml
   <mujoco model="pendulum">
       <option timestep="0.001"/>
       <worldbody>
           <body name="pivot" pos="0 0 0.5">
               <joint name="hinge" type="hinge" axis="0 0 1"/>
               <inertial pos="0 0.3 0" mass="1" diaginertia="0.01 0.1 0.01"/>
               <geom type="capsule" fromto="0 0 0 0 0.6 0" size="0.02"/>
           </body>
       </worldbody>
       <actuator>
           <motor name="torque" joint="hinge" ctrllimited="true" ctrlrange="-10 10"/>
       </actuator>
   </mujoco>
   ```
   
   控制器代码：
   
   ```python
   import mujoco
   import mujoco.viewer
   import numpy as np
   
   model = mujoco.MjModel.from_xml_path('pendulum.xml')
   data = mujoco.MjData(model)
   
   kp = 100.0  # 比例增益
   kd = 10.0   # 微分增益
   
   with mujoco.viewer.launch_passive(model, data) as viewer:
       while viewer.is_running():
           # 获取当前角度和角速度
           angle = data.qpos[0]
           angular_vel = data.qvel[0]
           
           # PD控制：目标角度为0（垂直）
           torque = kp * (-angle) + kd * (-angular_vel)
           torque = np.clip(torque, -10, 10)
           
           data.ctrl[0] = torque
           mujoco.mj_step(model, data)
           viewer.sync()
   ```

5. 修改四足机器人模型，添加一个躯干自由度，使其能够在前后方向上倾斜。
   
   **提示**：
   - 在torso和worldbody之间添加一个slide或hinge关节
   - 添加对应的驱动器和控制器
   - 调整控制器的目标位置以实现前后倾斜

---

## 本章小结

本章我们全面学习了MuJoCo仿真引擎。从概述部分，我们了解到MuJoCo是由DeepMind开发的开源物理引擎，以其精确的物理仿真和高效的性能著称，特别适合机器人控制和强化学习研究。安装部署部分，我们掌握了在Linux系统上安装MuJoCo以及ROS2集成包的方法。XML模型定义部分，我们详细学习了MuJoCo模型的结构，包括刚体定义、关节类型、驱动器、接触参数和传感器等核心元素。ROS2集成部分，我们介绍了如何通过mujoco_ros_pkgs实现ROS2与MuJoCo的通信。最后，通过倒立摆和四足机器人两个完整的仿真实例，我们将理论知识应用于实践。

MuJoCo作为一款专业的机器人仿真引擎，相比Gazebo具有更高的计算效率和更精确的物理仿真能力。掌握MuJoCo将为你的机器人研究和开发提供强有力的工具支持。

---

## 参考资料

### MuJoCo官方文档

1. MuJoCo Documentation: <https://mujoco.readthedocs.io/en/latest/>
2. MuJoCo Python Binding: <https://github.com/google-deepmind/mujoco/tree/main/python>
3. MuJoCo XML Reference: <https://mujoco.readthedocs.io/en/latest/XMLreference.html>

### ROS2集成

4. mujoco_ros_pkgs: <https://github.com/mujoco-ros/mujoco_ros_pkg>
5. mujoco_ros_control: <https://github.com/mujoco-ros/mujoco_ros_control>

### 学习资源

6. MuJoCo Tutorial: <https://github.com/deepmind/mujoco/blob/main/README.md>
7. DeepMind Control Suite: <https://github.com/deepmind/dm_control>

---

## 下节预告

后续课程将介绍更多机器人仿真技术，包括Webots仿真平台、PyBullet物理引擎等内容，帮助你全面掌握机器人仿真技术。

---

*本章学习完成！MuJoCo是机器人仿真领域的重要工具，建议大家动手实践，体会精确物理仿真的魅力。*
