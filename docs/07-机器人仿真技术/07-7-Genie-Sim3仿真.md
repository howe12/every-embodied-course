# 07-7 Genie-Sim3仿真

> **前置课程**：07-6 MuJoCo仿真
> **后续课程**：待定

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：Genie-Sim3是一款功能强大的机器人仿真平台，专注于为具身智能研究提供高保真度的仿真环境。它结合了物理引擎渲染与实时控制能力，支持多种机器人模型的快速部署和测试。本节将详细介绍Genie-Sim3的核心特性、安装部署、场景配置、机器人控制方法以及与ROS2的深度集成，帮助你快速掌握这款仿真工具。

---

## 1. Genie-Sim3概述

Genie-Sim3是新一代机器人仿真平台，专为具身智能和机器人学研究设计。与传统仿真器相比，Genie-Sim3在渲染质量、物理精度和实时性能方面具有显著优势。

### 1.1 核心特性

**高保真渲染引擎**：Genie-Sim3采用现代渲染技术，支持基于物理的渲染（PBR）、光线追踪和实时全局光照，能够生成接近真实世界的视觉输出。这对于需要视觉感知的机器人训练任务尤为重要。

**实时物理仿真**：平台内置高性能物理引擎，支持刚体动力学、柔性体仿真和复杂接触力建模。物理仿真与渲染帧率解耦，确保在复杂场景下仍能保持稳定的仿真精度。

**多机器人支持**：Genie-Sim3支持同时仿真多个异构机器人，每个机器人可以拥有不同的控制接口和传感器配置。这一特性使得多机器人协作和对抗性场景的研究成为可能。

**丰富的传感器模型**：平台提供多种传感器的物理仿真模型，包括RGB相机、深度相机、激光雷达、IMU、触觉传感器等。所有传感器都经过校准，可以输出与真实硬件相近的数据。

**Python API优先**：Genie-Sim3采用Python作为主要编程接口，提供简洁易用的API。这种设计使得研究者和工程师能够快速迭代实验，而无需深入了解底层实现细节。

### 1.2 应用场景

| 领域 | 应用说明 |
|------|----------|
| 具身智能 | 视觉语言动作模型训练、Sim-to-Real迁移 |
| 机器人控制 | manipulation、抓取、 locomotion |
| 强化学习 | 策略训练、奖励函数设计 |
| 人机交互 | 语音交互、动作识别 |
| 自动驾驶 | 车载传感器仿真、决策规划 |

### 1.3 与其他仿真器的对比

| 特性 | Genie-Sim3 | MuJoCo | Gazebo | Isaac Sim |
|------|-------------|--------|--------|-----------|
| 渲染质量 | 高（光线追踪） | 低 | 中 | 高 |
| 物理精度 | 高 | 很高 | 中 | 高 |
| 实时性能 | 优秀 | 优秀 | 一般 | 优秀 |
| ROS集成 | 原生支持 | 需要桥接 | 原生支持 | 原生支持 |
| 易用性 | 高 | 中 | 低 | 中 |
| 传感器丰富度 | 高 | 中 | 高 | 高 |

---

## 2. 部署安装

Genie-Sim3支持多种安装方式，包括Docker容器、本地安装和云端部署。本节将详细介绍本地安装和Docker部署两种主要方式。

### 2.1 系统要求

在开始安装之前，请确保你的系统满足以下要求：

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 20.04+ | Ubuntu 22.04+ |
| CPU | 4核 | 8核+ |
| 内存 | 8GB | 16GB+ |
| 显卡 | GTX 1060+ | RTX 3060+ |
| 存储 | 20GB SSD | 50GB SSD |
| CUDA | 11.0+ | 11.8+ |

### 2.2 通过Docker安装（推荐）

Docker方式安装最为简便，可以避免依赖冲突：

```bash
# 安装Docker（如果未安装）
sudo apt update
sudo apt install -y docker.io docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 拉取Genie-Sim3镜像
docker pull geniesim/genie-sim3:latest

# 运行容器
docker run -it --gpus all \
    --name genie-sim3 \
    -v ~/genie_sim3_workspace:/workspace \
    -p 8080:8080 \
    -p 50051:50051 \
    geniesim/genie-sim3:latest

# 如果需要持久化容器
docker run -d --gpus all \
    --name genie-sim3 \
    -v ~/genie_sim3_workspace:/workspace \
    -p 8080:8080 \
    -p 50051:50051 \
    geniesim/genie-sim3:latest
```

### 2.3 本地安装

如果你需要更深入的控制，可以选择本地安装：

```bash
# 创建工作目录
mkdir -p ~/genie_sim3
cd ~/genie_sim3

# 安装依赖
sudo apt update
sudo apt install -y \
    python3.10 \
    python3-pip \
    python3-venv \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

# 克隆Genie-Sim3仓库
git clone https://github.com/GenieSim/genie-sim3.git

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4 验证安装

安装完成后，可以通过以下命令验证：

```bash
# 进入虚拟环境
source venv/bin/activate

# 运行验证脚本
python -c "import genie_sim3; print('Genie-Sim3 version:', genie_sim3.__version__)"

# 或使用CLI验证
genie-sim3 --version
```

---

## 3. 场景配置

Genie-Sim3的场景通过配置文件定义，支持JSON和YAML两种格式。本节将介绍场景的基本结构、环境配置和物体放置方法。

### 3.1 场景文件结构

Genie-Sim3的场景文件采用层次化结构：

```yaml
# scenes/simple_scene.yaml
version: "3.0"

# 场景元数据
metadata:
  name: "Simple Robot Scene"
  description: "Basic scene with robot and objects"
  author: "Your Name"

# 渲染设置
rendering:
  width: 1920
  height: 1080
  fps: 60
  enable_shadow: true
  enable_ambient_occlusion: true
  enable_raytracing: false

# 物理设置
physics:
  gravity: [0, 0, -9.81]
  timestep: 0.001
  substeps: 10
  solver_iterations: 50

# 环境设置
environment:
  skybox: "studio HDRI"
  ambient_light: [0.3, 0.3, 0.3]
  directional_light:
    direction: [-1, -1, -1]
    intensity: 1.0
    color: [1.0, 1.0, 1.0]

# 地面设置
ground:
  plane:
    normal: [0, 0, 1]
    friction: 0.8
    restitution: 0.1
  material:
    texture: "textures/wood_floor.png"
    roughness: 0.5
    metallic: 0.0
```

### 3.2 机器人模型配置

机器人通过模型配置加载：

```yaml
# 配置机器人
robots:
  - name: "robot_panda"
    type: "panda"
    urdf: "robots/panda.urdf"
    base_position: [0, 0, 0]
    base_orientation: [0, 0, 0, 1]  # quaternion
    
    # 初始关节位置
    initial_joint_positions:
      panda_joint1: 0.0
      panda_joint2: 0.785
      panda_joint3: 0.0
      panda_joint4: -2.356
      panda_joint5: 0.0
      panda_joint6: 1.571
      panda_joint7: 0.785
      
    # 末端执行器配置
    end_effector:
      name: "gripper"
      type: "panda_gripper"
      
    # 传感器配置
    sensors:
      - type: "camera"
        name: "wrist_camera"
        frame: "panda_8"
        resolution: [640, 480]
        fov: 90
        
      - type: "force_torque"
        name: "ft_sensor"
        frame: "panda_8"
```

### 3.3 物体和障碍物

场景中可以添加各种物体：

```yaml
# 添加物体
objects:
  # 立方体
  - name: "cube_1"
    type: "box"
    size: [0.05, 0.05, 0.05]
    mass: 0.1
    position: [0.3, 0.0, 0.5]
    orientation: [0, 0, 0, 1]
    material:
      color: [1.0, 0.0, 0.0]
      roughness: 0.4
      
  # 球体
  - name: "ball_1"
    type: "sphere"
    radius: 0.03
    mass: 0.05
    position: [0.4, 0.1, 0.5]
    material:
      color: [0.0, 1.0, 0.0]
      
  # 圆柱体
  - name: "cylinder_1"
    type: "cylinder"
    radius: 0.04
    height: 0.1
    mass: 0.2
    position: [0.35, -0.1, 0.5]
    
  # 从URDF加载复杂物体
  - name: "table"
    type: "urdf"
    urdf: "objects/table.urdf"
    position: [0.5, 0.0, 0.0]
    static: true
```

### 3.4 加载场景

使用Python API加载场景：

```python
import genie_sim3 as gs

# 初始化仿真环境
sim = gs.Simulation()

# 加载场景配置
sim.load_scene("scenes/simple_scene.yaml")

# 或使用代码创建场景
sim.create_scene(
    name="my_scene",
    rendering={"width": 1280, "height": 720},
    physics={"timestep": 0.001}
)

# 添加地面
sim.add_ground(
    friction=0.8,
    restitution=0.1
)

# 添加光源
sim.add_light(
    light_type="directional",
    direction=[-1, -1, -1],
    intensity=1.0
)

print("Scene loaded successfully!")
```

---

## 4. 机器人控制

Genie-Sim3提供多种机器人控制方式，从底层的关节位置/速度控制到高层的任务空间控制。本节将详细介绍各种控制方法。

### 4.1 关节位置控制

最基本的控制方式是直接设置关节目标位置：

```python
import genie_sim3 as gs
import numpy as np

# 初始化并加载场景
sim = gs.Simulation()
sim.load_scene("scenes/robot_scene.yaml")

# 获取机器人
robot = sim.get_robot("robot_panda")

# 关节位置控制
def move_to_joint_positions(positions, duration=2.0):
    """
    将机器人移动到指定的关节位置
    
    Args:
        positions: 7个关节的目标位置（弧度）
        duration: 移动持续时间（秒）
    """
    robot.set_joint_position_targets(positions)
    
    # 仿真循环
    dt = sim.get_timestep()
    t = 0
    while t < duration:
        sim.step()
        t += dt
        
        # 打印当前关节位置
        current = robot.get_joint_positions()
        print(f"Joint positions: {current}")

# 示例：移动到抓取姿态
target_positions = [0.0, 0.5, 0.0, -1.5, 0.0, 1.0, 0.5]
move_to_joint_positions(target_positions)
```

### 4.2 关节速度控制

对于连续运动控制，可以使用速度控制模式：

```python
# 关节速度控制
def move_with_joint_velocities(velocities, duration=3.0):
    """
    以指定关节速度移动机器人
    
    Args:
        velocities: 7个关节的速度（弧度/秒）
        duration: 运行时间（秒）
    """
    robot.set_joint_velocity_mode()
    robot.set_joint_velocity_targets(velocities)
    
    dt = sim.get_timestep()
    t = 0
    while t < duration:
        sim.step()
        t += dt
        
        # 检查是否到达位置限制
        positions = robot.get_joint_positions()
        
        # 简单停止条件
        if np.any(np.abs(positions) > np.pi):
            robot.set_joint_velocity_targets([0] * 7)
            break

# 示例：正弦波运动
import math
t = 0
dt = 0.001
while t < 10.0:
    # 生成正弦波速度
    v1 = 0.3 * math.sin(t * 2)
    v2 = 0.2 * math.sin(t * 3)
    velocities = [v1, v2, 0.1, -0.1, 0.05, 0.1, 0.05]
    
    robot.set_joint_velocity_targets(velocities)
    sim.step()
    t += dt
```

### 4.3 力/力矩控制

对于需要柔顺控制的场景，可以使用力控制：

```python
# 柔顺控制示例
def compliant_move(target_position, stiffness=100.0, damping=10.0):
    """
    使用阻抗控制移动到目标位置
    
    Args:
        target_position: 目标末端位置 [x, y, z]
        stiffness: 刚度系数
        damping: 阻尼系数
    """
    robot.set_joint_impedance_mode()
    
    dt = sim.get_timestep()
    max_iterations = 5000
    
    for i in range(max_iterations):
        # 获取当前末端位置
        current_pose = robot.get_end_effector_pose()
        current_pos = current_pose[:3]
        
        # 计算位置误差
        error = np.array(target_position) - current_pos
        
        # PD控制器计算力
        velocity = robot.get_end_effector_linear_velocity()
        force = stiffness * error - damping * velocity
        
        # 发送力命令
        robot.set_joint_effort_forces(force)
        
        sim.step()
        
        # 检查是否接近目标
        if np.linalg.norm(error) < 0.001:
            print(f"Reached target in {i} iterations")
            break
```

### 4.4 任务空间控制

更高级的控制是在任务空间（笛卡尔空间）直接控制末端执行器：

```python
# 任务空间位置控制
def move_to_pose(target_pose, duration=3.0):
    """
    移动末端执行器到指定位姿
    
    Args:
        target_pose: [x, y, z, qx, qy, qz, qw] 位置+四元数
        duration: 移动时间（秒）
    """
    robot.set_task_space_mode()
    robot.set_end_effector_pose_targets(target_pose)
    
    dt = sim.get_timestep()
    t = 0
    while t < duration:
        sim.step()
        t += dt
        
        # 监控进度
        current = robot.get_end_effector_pose()
        pos_error = np.linalg.norm(np.array(target_pose[:3]) - np.array(current[:3]))
        
        if pos_error < 0.001:
            print("Target reached!")
            break

# 示例：直线移动
start_pose = robot.get_end_effector_pose()
end_pose = start_pose[:3] + np.array([0.1, 0.1, 0.0])
end_pose = list(end_pose) + start_pose[3:]

move_to_pose(end_pose, duration=2.0)
```

### 4.5 夹爪控制

对于带夹爪的机器人，可以控制夹爪开合：

```python
# 夹爪控制
def control_gripper(action, width=None):
    """
    控制夹爪动作
    
    Args:
        action: "open", "close", 或 "set"
        width: 夹爪开合宽度（米），仅当action="set"时有效
    """
    if action == "open":
        robot.set_gripper_width(0.08)  # 完全打开
    elif action == "close":
        robot.set_gripper_width(0.0)    # 完全关闭
    elif action == "set" and width is not None:
        robot.set_gripper_width(width)
    
    # 等待夹爪稳定
    for _ in range(100):
        sim.step()

# 示例：抓取物体
# 移动到物体上方
move_to_pose([0.3, 0.0, 0.6, 0, 1, 0, 0])

# 下移
move_to_pose([0.3, 0.0, 0.55, 0, 1, 0, 0])

# 关闭夹爪
control_gripper("close")

# 抬起
move_to_pose([0.3, 0.0, 0.7, 0, 1, 0, 0])

# 移动到放置位置
move_to_pose([0.5, 0.0, 0.6, 0, 1, 0, 0])
move_to_pose([0.5, 0.0, 0.55, 0, 1, 0, 0])

# 打开夹爪
control_gripper("open")
```

---

## 5. ROS2集成

Genie-Sim3提供了完整的ROS2接口，支持通过话题、服务和动作与ROS2系统通信。本节将介绍如何配置ROS2集成和实现常见功能。

### 5.1 安装ROS2桥接包

首先需要安装Genie-Sim3的ROS2桥接包：

```bash
# 创建ROS2工作空间
mkdir -p ~/genie_sim3_ros2/src
cd ~/genie_sim3_ros2

# 克隆ROS2桥接包
git clone https://github.com/GenieSim/genie_sim3_ros2_bridge.git src/genie_sim3_ros2_bridge

# 安装依赖
cd src/genie_sim3_ros2_bridge
pip install -r requirements.txt

# 编译
cd ~/genie_sim3_ros2
source /opt/ros/humble/setup.bash
colcon build --packages-select genie_sim3_ros2_bridge

# 加载环境
source install/setup.bash
```

### 5.2 启动ROS2桥接

启动Genie-Sim3后，可以通过以下命令启动ROS2桥接：

```bash
# 方式1：启动默认配置
ros2 launch genie_sim3_ros2_bridge default.launch.py

# 方式2：自定义配置
ros2 launch genie_sim3_ros2_bridge genie_sim3_ros2_bridge.launch.py \
    robot_name:="panda_1" \
    namespace:="/genie_sim3"
```

### 5.3 发布的话题和服务

ROS2桥接后，Genie-Sim3会发布以下话题：

| 话题 | 消息类型 | 描述 |
|------|----------|------|
| `/genie_sim3/robot/joint_states` | sensor_msgs/JointState | 关节状态 |
| `/genie_sim3/robot/end_effector_pose` | geometry_msgs/PoseStamped | 末端位姿 |
| `/genie_sim3/robot/end_effector_twist` | geometry_msgs/TwistStamped | 末端速度 |
| `/genie_sim3/sensor/camera/image` | sensor_msgs/Image | RGB相机图像 |
| `/genie_sim3/sensor/depth/image` | sensor_msgs/Image | 深度图像 |
| `/genie_sim3/sensor/laser/scan` | sensor_msgs/LaserScan | 激光雷达数据 |
| `/genie_sim3/sensor/imu/data` | sensor_msgs/Imu | IMU数据 |

订阅的话题和服务：

| 话题/服务 | 类型 | 描述 |
|-----------|------|------|
| `/genie_sim3/robot/joint_command` | sensor_msgs/JointState | 关节命令 |
| `/genie_sim3/robot/end_effector_command` | geometry_msgs/PoseStamped | 末端命令 |
| `/genie_sim3/gripper/command` | std_msgs/Float64 | 夹爪命令 |
| `/genie_sim3/reset` | std_msgs/Empty | 重置仿真 |
| `/genie_sim3/pause` | std_msgs/Empty | 暂停仿真 |
| `/genie_sim3/resume` | std_msgs/Empty | 恢复仿真 |

### 5.4 订阅关节命令

在ROS2中控制Genie-Sim3中的机器人：

```python
#!/usr/bin/env python3
"""
ROS2节点：控制Genie-Sim3中的机器人
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from geometry_msgs.msg import PoseStamped
import genie_sim3 as gs


class GenieSim3Controller(Node):
    def __init__(self):
        super().__init__('genie_sim3_controller')
        
        # 初始化Genie-Sim3
        self.sim = gs.Simulation()
        self.sim.load_scene("scenes/robot_scene.yaml")
        self.robot = self.sim.get_robot("panda_1")
        
        # 订阅关节命令
        self.joint_cmd_sub = self.create_subscription(
            JointState,
            '/genie_sim3/robot/joint_command',
            self.joint_command_callback,
            10
        )
        
        # 订阅末端执行器命令
        self.ee_cmd_sub = self.create_subscription(
            PoseStamped,
            '/genie_sim3/robot/end_effector_command',
            self.ee_command_callback,
            10
        )
        
        # 发布关节状态
        self.joint_state_pub = self.create_publisher(
            JointState,
            '/genie_sim3/robot/joint_states',
            10
        )
        
        self.get_logger().info('Genie-Sim3 controller started')
        
    def joint_command_callback(self, msg):
        """处理关节命令"""
        # 设置关节位置目标
        if len(msg.position) == 7:
            self.robot.set_joint_position_targets(list(msg.position))
            
    def ee_command_callback(self, msg):
        """处理末端执行器命令"""
        pose = [
            msg.pose.position.x,
            msg.pose.position.y,
            msg.pose.position.z,
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w
        ]
        self.robot.set_end_effector_pose_targets(pose)
        
    def publish_joint_states(self):
        """发布关节状态"""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [f'panda_joint{i}' for i in range(1, 8)]
        msg.position = list(self.robot.get_joint_positions())
        msg.velocity = list(self.robot.get_joint_velocities())
        
        self.joint_state_pub.publish(msg)
        
    def run(self):
        """主循环"""
        while rclpy.ok():
            # 仿真一步
            self.sim.step()
            
            # 发布状态
            self.publish_joint_states()
            
            # 处理ROS2回调
            rclpy.spin_once(self, timeout_sec=0.001)


def main(args=None):
    rclpy.init(args=args)
    controller = GenieSim3Controller()
    controller.run()
    controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 5.5 同步仿真时间

确保ROS2时间与Genie-Sim3仿真时间同步：

```bash
# 启动时使用仿真时间
ros2 run genie_sim3_ros2_bridge bridge_node \
    --ros-args \
    -p use_sim_time:=true
```

---

## 练习题

### 选择题

1. Genie-Sim3仿真平台的核心优势不包括以下哪项？
   - A) 高保真渲染
   - B) 实时物理仿真
   - C) 仅支持单机器人
   - D) Python API优先
   
   **答案：C**。Genie-Sim3支持多机器人仿真，这是其核心特性之一。

2. 在Genie-Sim3中，控制机器人末端执行器移动到指定位置的方法是？
   - A) set_joint_position_targets
   - B) set_joint_velocity_targets
   - C) set_end_effector_pose_targets
   - D) set_gripper_width
   
   **答案：C**。set_end_effector_pose_targets用于任务空间控制，直接设置末端执行器的目标位姿。

3. Genie-Sim3通过什么方式与ROS2进行集成？
   - A) 原生支持
   - B) 需要桥接包
   - C) 不支持ROS2
   - D) 只能通过C++ API
   
   **答案：B**。Genie-Sim3通过ROS2桥接包与ROS2系统集成，发布和订阅相应的话题。

### 实践题

4. 创建一个Genie-Sim3场景，包含一个UR5机械臂和一个立方体，并实现机械臂抓取立方体的完整流程。
   
   **参考答案**：
   
   ```python
   import genie_sim3 as gs
   import numpy as np
   
   # 初始化仿真
   sim = gs.Simulation()
   sim.load_scene("scenes/ur5_grasp.yaml")
   
   # 获取机器人和物体
   robot = sim.get_robot("ur5")
   cube = sim.get_object("cube")
   
   # 获取立方体位置
   cube_pose = cube.get_pose()
   cube_pos = cube_pose[:3]
   
   # 1. 移动到抓取前位置
   pre_grasp = list(cube_pos + np.array([0, 0, 0.1])) + [0, 1, 0, 0]
   robot.set_task_space_mode()
   robot.set_end_effector_pose_targets(pre_grasp)
   
   for _ in range(200):
       sim.step()
   
   # 2. 下移接近物体
   grasp_pos = list(cube_pos) + [0, 1, 0, 0]
   robot.set_end_effector_pose_targets(grasp_pos)
   
   for _ in range(100):
       sim.step()
   
   # 3. 关闭夹爪
   robot.set_gripper_width(0.0)
   
   for _ in range(50):
       sim.step()
   
   # 4. 抬起
   robot.set_end_effector_pose_targets(pre_grasp)
   
   for _ in range(200):
       sim.step()
   
   print("Grasping task completed!")
   ```

5. 使用ROS2接口，实现一个通过键盘控制Genie-Sim3中机器人的节点。
   
   **提示**：
   - 订阅ROS2键盘话题（如 `/keyboard/keydown`）
   - 根据按键设置关节位置目标或末端位姿目标
   - 在主循环中同时执行仿真步进和ROS2回调处理

---

## 本章小结

本章我们全面学习了Genie-Sim3仿真平台。概述部分，我们了解了其高保真渲染、实时物理仿真、多机器人支持等核心特性。部署安装部分，我们掌握了Docker和本地两种安装方式。场景配置部分，我们学习了YAML配置文件结构和机器人、物体添加方法。机器人控制部分，我们深入研究了关节位置控制、速度控制、力控制、任务空间控制和夹爪控制等多种控制方式。ROS2集成部分，我们实现了通过ROS2话题控制机器人和发布传感器数据。最后，通过物体抓取任务的实战项目，我们将理论知识应用于实践。

Genie-Sim3作为新一代机器人仿真平台，特别适合具身智能研究和视觉语言动作模型的训练。掌握好这款工具，将为你的机器人研究和开发工作提供强大的支持。

---

## 参考资料

### 官方文档

1. Genie-Sim3 Official Docs: <https://docs.genie-sim3.com>
2. Python API Reference: <https://docs.genie-sim3.com/api/python>

### ROS2集成

3. genie_sim3_ros2_bridge: <https://github.com/GenieSim/genie_sim3_ros2_bridge>
4. ROS2 Humble Documentation: <https://docs.ros.org/en/humble/>

### 相关技术

5. MoveIt2 Documentation: <https://moveit.ros.org/>
6. Robot URDF Modeling: <https://wiki.ros.org/urdf>

---

## 下节预告

下一节我们将学习**07-8 仿真与真实机器人对接**，了解如何将仿真环境中开发的算法和控制器无缝迁移到真实机器人平台上，包括硬件接口配置、通信桥接和Sim-to-Real迁移技术。

---

*本章学习完成！Genie-Sim3为机器人仿真提供了新的可能性，建议大家多加练习，熟练掌握其场景配置和控制方法。*
