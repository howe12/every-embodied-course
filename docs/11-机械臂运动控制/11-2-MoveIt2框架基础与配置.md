# 11-2 MoveIt2框架基础与配置

> **前置课程**：05-4 机械臂运动学基础与建模
> **后续课程**：05-6 MoveIt2运动规划与控制编程

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：MoveIt2是ROS2中功能最强大的机器人运动规划框架，它整合了运动学、碰撞检测、轨迹生成等多个模块，为机械臂、移动机械手等提供了完整的运动控制解决方案。本节将深入讲解MoveIt2的核心概念、架构设计、配置方法以及快速入门指南，帮助你建立起对MoveIt2的全面认识。

---

## 1. MoveIt2概述

MoveIt2是ROS2生态系统中专门用于机器人运动规划的框架，它不仅提供了强大的运动规划算法，还包含了完整的机械臂控制工具链。从简单的点对点运动到复杂的连续轨迹执行，MoveIt2都能提供可靠的解决方案。

### 1.1 什么是MoveIt2

MoveIt2是MoveIt在ROS2中的重新设计版本，完全适配了ROS2的架构和DDS通信机制。它不仅仅是一个规划器，而是一个完整的**运动控制框架**，集成了以下核心功能：

- **运动规划（Motion Planning）**：基于采样或优化的规划算法
- **运动学（Kinematics）**：正逆运动学求解
- **碰撞检测（Collision Detection）**：实时碰撞检测与规避
- **轨迹处理（Trajectory Processing）**：轨迹平滑与时间参数化
- **控制器接口（Controller Interface）**：与底层硬件的无缝集成

### 1.2 MoveIt2的应用场景

MoveIt2广泛应用于以下场景：

| 应用场景 | 描述 | 示例 |
|----------|------|------|
| 机械臂抓取 | 目标物抓取、放置操作 | 工业分拣、服务机器人 |
| 运动复制 | 演示轨迹复现 | 示教编程 |
| 碰撞规避 | 复杂环境中的安全运动 | 人机协作 |
| 末端精细操作 | 精细定位与调整 | 精密装配、手术机器人 |
| 移动操作 | 移动平台+机械臂协调 | 移动抓取机器人 |

### 1.3 MoveIt2 vs MoveIt（ROS1）

MoveIt2相对于ROS1版本的MoveIt有重大改进：

| 特性 | MoveIt（ROS1） | MoveIt2（ROS2） |
|------|----------------|-----------------|
| 通信框架 | roscpp/rospy | rclcpp/rclpy |
| 中间件 | ROS Master | DDS |
| 实时性能 | 非实时 | 支持实时（需配置） |
| 生命周期管理 | 无 | 节点生命周期管理 |
| QoS配置 | 不支持 | 丰富QoS支持 |
| 并行规划 | 基础 | 改进的并行规划 |

---

## 2. 核心概念

理解MoveIt2的核心概念对于正确使用框架至关重要。本节将详细介绍各个关键组件及其作用。

### 2.1 Planning Scene（规划场景）

规划场景是MoveIt2中用于表示机器人工作环境的抽象概念，它包含：

- **机器人模型**：URDF/SRDF描述的机器人几何和运动学信息
- **机器人状态**：当前关节位置、末端执行器位姿
- **障碍物**：静态和动态障碍物
- **附加物体**：夹爪抓取的物体

```
┌─────────────────────────────────────────┐
│           Planning Scene                │
│  ┌─────────┐    ┌─────────┐            │
│  │ 机器人  │    │ 障碍物  │            │
│  │ Model   │    │Obstacles│            │
│  └─────────┘    └─────────┘            │
│  ┌─────────┐    ┌─────────┐            │
│  │ 附加物体│    │ 碰撞检测│            │
│  │Attached │    │Collision│            │
│  └─────────┘    └─────────┘            │
└─────────────────────────────────────────┘
```

### 2.2 Planning Group（规划组）

规划组是MoveIt2中组织机器人关节的核心概念。一个机器人可以有多个规划组：

- **机械臂组（Arm Group）**：所有参与运动的关节集合
- **夹爪组（Gripper Group）**：末端执行器的开合关节
- **整个机器人（Whole Robot）**：所有关节的集合

```xml
<!-- SRDF中的规划组定义示例 -->
<group name="panda_arm">
    <chain base_link="panda_link0" tip_link="panda_link8" />
</group>

<group name="panda_hand">
    <link name="panda_link8" />
    <joint name="panda_finger_joint1" />
    <joint name="panda_finger_joint2" />
</group>

<group name="panda_whole">
    <group ref="panda_arm" />
    <group ref="panda_hand" />
</group>
```

### 2.3 RobotModel（机器人模型）

RobotModel是MoveIt2的核心数据结构，它封装了：

- **运动学模型**：关节连接关系、连杆参数
- **几何模型**：网格、碰撞体
- **状态信息**：当前关节值、速度、加速度

```python
# 加载机器人模型
from moveit.core import RobotModel
from moveit.core.robot_model import RobotModel

robot_model_loader = RobotModelLoader("robot_description")
robot_model = robot_model_loader.getModel()
```

### 2.4 MotionPlanRequest（运动规划请求）

运动规划请求包含规划所需的所有信息：

| 参数 | 说明 |
|------|------|
| group_name | 规划组名称 |
| goal_constraints | 目标约束（位置、方向） |
| path_constraints | 路径约束（方向、位姿限制） |
| workspace_parameters | 工作空间边界 |
| planning_time | 最大规划时间 |
| num_planning_attempts | 规划尝试次数 |

### 2.5 Planning Pipeline（规划管道）

规划管道是MoveIt2的规划执行流程，包含多个阶段：

```
MotionPlanRequest
       │
       ▼
┌─────────────────┐
│  规划请求验证   │ ← 验证请求合法性
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  运动学求解器   │ ← IK求解
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  规划器插件    │ ← OMPL/STOMP/CHOMP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  轨迹后处理    │ ← 平滑、时间参数化
└────────┬────────┘
         │
         ▼
   MotionPlanResult
```

---

## 3. 系统架构

MoveIt2采用模块化设计，各个组件之间通过清晰的接口进行交互。

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                          MoveIt2 架构                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    用户接口层 (User Interfaces)                │  │
│  │   MoveIt! Setup Assistant │ RViz │ Python/C++ API │ MoveIt    │  │
│  └─────────────────────────────┬─────────────────────────────────┘  │
│                                │                                     │
│  ┌─────────────────────────────┴─────────────────────────────────┐  │
│  │                    核心功能层 (Core Functionality)             │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │  │
│  │  │  运动规划 │ │ 运动学   │ │ 碰撞检测 │ │   轨迹处理      │   │  │
│  │  │Planning  │ │Kinematics│ │Collision │ │Trajectory Proc. │   │  │
│  │  └─────┬────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘   │  │
│  │        │           │           │                 │              │  │
│  │  ┌─────┴───────────┴───────────┴─────────────────┴─────────┐   │  │
│  │  │              Planning Scene Monitor                      │   │  │
│  │  └───────────────────────────┬─────────────────────────────┘   │  │
│  └──────────────────────────────┼───────────────────────────────┘  │
│                                 │                                    │
│  ┌──────────────────────────────┼───────────────────────────────┐   │
│  │                    硬件抽象层 (Hardware Interface)          │   │
│  │         ┌──────────────┐  ┌──────────────┐                   │   │
│  │         │ ros2_control│  │   控制器    │                   │   │
│  │         │  Driver     │  │  Controllers │                   │   │
│  │         └──────────────┘  └──────────────┘                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件详解

**MoveGroup**：最常用的接口节点，提供action和service接口

- 订阅`/joint_states`获取当前机器人状态
- 提供`/plan` action用于运动规划
- 提供`/execute` action用于轨迹执行
- 管理planning scene

**MoveitCpp**：轻量级C++编程接口

- 直接嵌入到用户程序中
- 不需要启动额外节点
- 更高的灵活性

**Planning Scene Manager**：

- 维护机器人工作空间状态
- 管理障碍物信息
- 提供碰撞检测服务

** kinematics_solver**：运动学求解器

- 默认使用KDL（基于KDL的IK）
- 支持KDL、TF2、KDL等
- 可插拔设计

### 3.3 与ros2_control集成

MoveIt2与ros2_control深度集成，实现了对真实硬件的控制：

```
MoveIt2                    ros2_control                   硬件
    │                           │                            │
    │──── Plan Request ────────▶│                            │
    │                           │                            │
    │◀─── Trajectory ───────────│                            │
    │                           │                            │
    │──── Execute Trajectory ──▶│                            │
    │                           │──── Joint Commands ────────▶│
    │                           │◀─── Joint States ──────────│
    │                           │                            │
```

**Controller Manager**管理多个控制器：

- **JointTrajectoryController**：关节轨迹跟踪
- **JointGroupPositionController**：位置组控制
- **GripperActionController**：夹爪控制

---

## 4. 安装与配置

本节将详细介绍MoveIt2的安装方法和基本配置步骤。

### 4.1 安装MoveIt2

**从二进制包安装（推荐）**：

```bash
# Ubuntu 22.04 (Jammy)
sudo apt update
sudo apt install ros-humble-moveit*

# 检查安装
ros2 pkg list | grep moveit
```

**从源码编译（开发版本）**：

```bash
# 创建工作空间
mkdir -p ~/moveit2_ws/src
cd ~/moveit2_ws

# 拉取源码
git clone https://github.com/ros-planning/moveit2.git src/moveit2 --branch humble
git clone https://github.com/ros-planning/moveit_resources.git src/moveit_resources --branch humble

# 安装依赖
sudo apt install python3-colcon-common-extensions
rosdep install --from-paths src --ignore-src -r -y

# 编译
colcon build --mixins release -t src src/moveit2
source install/setup.bash
```

### 4.2 验证安装

```bash
# 启动MoveIt2配置好的演示
ros2 launch moveit_resources_panda_moveit_config demo.launch.py

# 或使用MoveIt2的RViz插件
ros2 launch moveit2_rviz rviz.launch.py
```

### 4.3 快速配置新机器人

使用MoveIt2配置助手可以快速为新机器人生成配置文件：

```bash
# 启动配置助手
ros2 run moveit_setup_assistant setup_assistant
```

**配置步骤**：

1. **加载URDF**：选择机器人的URDF文件
2. **生成SRDF**：自动生成或手动编辑SRDF
3. **配置规划组**：定义关节组和规划组
4. **配置机器人姿态**：定义初始状态和目标姿态
5. **配置夹爪**：如有末端执行器
6. **配置3D感知**：选择传感器
7. **生成配置文件**：输出到功能包

---

## 5. MoveIt2配置详解

理解MoveIt2的配置文件结构对于定制化使用至关重要。

### 5.1 配置文件结构

```
robot_moveit_config/
├── config/
│   ├── kinematics.yaml          # 运动学配置
│   ├── joint_limits.yaml        # 关节限位
│   ├── planning_pipeline.yaml  # 规划管道
│   ├── ompl_planning.yaml      # OMPL规划器
│   ├── moveit_controllers.yaml # 控制器配置
│   └── sensor_manager.yaml     # 传感器配置
├── launch/
│   ├── robot_state_publisher.launch.py
│   ├── move_group.launch.py
│   └── demo.launch.py
├── urdf/
│   └── robot.urdf.xacro
├── srdf/
│   └── robot.srdf
└── package.xml
```

### 5.2 运动学配置（kinematics.yaml）

```yaml
robot_name:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.05
  kinematics_solver_attempts: 3
```

**运动学求解器选项**：

| 求解器 | 插件 | 特点 |
|--------|------|------|
| KDL | kdl_kinematics_plugin | 默认，通用性强 |
| TF2 | tf2_kinematics_plugin | 实时性好 |
| LMA | lma_kinematics_plugin | 支持冗余机械臂 |
| IKFast | ikfast_kinematics_plugin | 速度最快 |

### 5.3 关节限位（joint_limits.yaml）

```yaml
joint_limits:
  panda_joint1:
    has_position_limits: true
    min_position: -2.8973
    max_position: 2.8973
    has_velocity_limits: true
    max_velocity: 2.1750
    has_acceleration_limits: true
    max_acceleration: 15.0
    has_jerk_limits: true
    max_jerk: 1000.0
```

### 5.4 规划管道配置（planning_pipeline.yaml）

```yaml
planning_plugin: ompl_interface/OMPLPlanner
request_adapters: >-
  default_planner_request_adapters/AddTimeOptimalParameterization
  default_planner_request_adapters/FixWorkspaceBounds
  default_planner_request_adapters/FixStartStateBounds
  default_planner_request_adapters/FixStartStateCollision
  default_planner_request_adapters/ResolveConstraintFrames
  default_planner_request_adapters/FilterConstraintTrajectories

start_state_max_bounds_error: 0.1
```

### 5.5 OMPL规划器配置

OMPL提供了多种规划算法，每种适用于不同场景：

| 规划算法 | 适用场景 | 特点 |
|----------|----------|------|
| RRT* | 通用 | 渐近最优 |
| RRTConnect | 快速路径 | 速度快，非最优 |
| PRM | 多查询 | 预处理后查询快 |
| PRM* | 高维空间 | 渐近最优 |
| BIT* | 有障碍物 | 知情搜索 |
| CForest | 并行规划 | 多线程加速 |

```yaml
planner_configs:
  RRTstarkConfigDefault:
    range: 0.0
    goal_bias: 0.05
    max_iterations: 10000
    max_goalsamples: 10000
    type: geometric::RRTstar

  RRTConnectkConfigDefault:
    range: 0.0
    max_iterations: 10000
    type: geometric::RRTConnect

  PRMstarkConfigDefault:
    max_nodes: 100000
    max_iterations: 10000
    max_goalsamples: 10000
    type: geometric::PRMstar
```

---

## 6. 快速入门示例

本节将通过一个完整的示例，展示如何使用Python API进行MoveIt2编程。

### 6.1 Panda机械臂配置

Panda是Franka Emika的机械臂，MoveIt2提供了完整的配置包：

```bash
# 安装Panda演示包
sudo apt install ros-humble-moveit-resources-panda-moveit-config

# 查看包位置
ros2 pkg list | grep panda
```

### 6.2 Python编程接口

```python
#!/usr/bin/env python3
"""
Panda机械臂运动规划示例
功能：演示如何使用MoveIt2 Python API进行基本运动规划
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, PoseStamped
from moveit.core import RobotModel, PlanningSceneInterface
from moveit.core.planning_interface import (
    MoveGroupInterface,
    PlanningComponentInterface,
)
from moveit_configs_utils import MoveItConfigsBuilder


class PandaMotionPlanner(Node):
    def __init__(self):
        super().__init__('panda_motion_planner')
        
        # 加载MoveIt配置
        moveit_config = (
            MoveItConfigsBuilder("panda", package="panda_moveit_config")
            .robot_description(file_path="config/panda.urdf.xacro")
            .srdf(file_path="config/panda.srdf")
            .planning_scene_monitor(
                publish_robot_description=True,
                publish_robot_state_description=True,
            )
            .trajectory_execution(file_path="config/moveit_controllers.yaml")
            .planning_pipelines(
                pipelines=["ompl", "chomp"],
                default_planning_pipeline="ompl",
            )
            .build()
        )
        
        # 创建规划组接口
        self.move_group = MoveGroupInterface(
            self, "panda_arm", moveit_config.robot_description, 
            moveit_config.robot_description_semantic, 
            moveit_config.planning_scene_monitor
        )
        
        # 配置规划参数
        self.move_group.set_planning_time(5.0)
        self.move_group.set_num_planning_attempts(10)
        self.move_group.set_max_velocity_scaling_factor(0.5)
        self.move_group.set_max_acceleration_scaling_factor(0.5)
        
        self.get_logger().info("Panda motion planner initialized")
    
    def plan_to_pose(self, target_pose):
        """规划到目标位姿"""
        # 设置目标位姿
        self.move_group.set_pose_target(target_pose, end_effector_link="panda_link8")
        
        # 执行规划
        plan_result = self.move_group.plan()
        
        if plan_result:
            self.get_logger().info("Planning succeeded!")
            return plan_result.trajectory
        else:
            self.get_logger().error("Planning failed!")
            return None
    
    def plan_to_joint_state(self, joint_positions):
        """规划到指定关节角度"""
        # 设置目标关节位置
        self.move_group.set_joint_value_target(joint_positions)
        
        # 执行规划
        plan_result = self.move_group.plan()
        
        if plan_result:
            self.get_logger().info("Planning succeeded!")
            return plan_result.trajectory
        else:
            self.get_logger().error("Planning failed!")
            return None
    
    def execute_trajectory(self, trajectory):
        """执行规划好的轨迹"""
        result = self.move_group.execute(trajectory, wait=True)
        if result == MoveGroupInterface.ExecuteTrajectoryResult.SUCCESS:
            self.get_logger().info("Execution succeeded!")
        else:
            self.get_logger().error("Execution failed!")
    
    def get_current_pose(self):
        """获取当前末端执行器位姿"""
        current_pose = self.move_group.get_current_pose(end_effector_link="panda_link8")
        return current_pose.pose
    
    def get_current_joint_values(self):
        """获取当前关节角度"""
        return self.move_group.get_current_joint_values()


def main(args=None):
    rclpy.init(args=args)
    
    planner = PandaMotionPlanner()
    
    # 示例1：规划到目标位姿
    target_pose = Pose()
    target_pose.position.x = 0.4
    target_pose.position.y = 0.0
    target_pose.position.z = 0.6
    target_pose.orientation.x = 0.0
    target_pose.orientation.y = 1.0
    target_pose.orientation.z = 0.0
    target_pose.orientation.w = 0.0
    
    trajectory = planner.plan_to_pose(target_pose)
    
    if trajectory:
        planner.execute_trajectory(trajectory)
    
    # 示例2：规划到指定关节位置
    # panda机械臂的初始位置
    joint_positions = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
    trajectory = planner.plan_to_joint_state(joint_positions)
    
    if trajectory:
        planner.execute_trajectory(trajectory)
    
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 6.3 C++编程接口

```cpp
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit/robot_model_loader/robot_model_loader.h>
#include <moveit/robot_state/robot_state.h>

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions node_options;
  node_options.automatically_declare_parameters_from_overrides(true);

  rclcpp::ExecutorOptions options;
  auto executor = std::make_shared<rclcpp::executors::MultiThreadedExecutor>(options);
  rclcpp::Node::SharedPtr node = rclcpp::Node::make_shared("panda_motion_planner", node_options);
  executor->add_node(node);

  // 创建MoveGroup接口
  static const std::string PLANNING_GROUP = "panda_arm";
  moveit::planning_interface::MoveGroupInterface move_group(node, PLANNING_GROUP);

  // 配置规划参数
  move_group.setPlanningTime(5.0);
  move_group.setMaxVelocityScalingFactor(0.5);
  move_group.setMaxAccelerationScalingFactor(0.5);

  // 获取当前状态
  auto current_state = move_group.getCurrentState();
  
  // 规划到目标位姿
  geometry_msgs::msg::Pose target_pose;
  target_pose.position.x = 0.4;
  target_pose.position.y = 0.0;
  target_pose.position.z = 0.6;
  target_pose.orientation.x = 0.0;
  target_pose.orientation.y = 1.0;
  target_pose.orientation.z = 0.0;
  target_pose.orientation.w = 0.0;

  move_group.setPoseTarget(target_pose);

  // 执行规划
  moveit::planning_interface::MoveGroupInterface::Plan plan;
  bool success = move_group.plan(plan);

  if (success) {
    RCLCPP_INFO(node->get_logger(), "Planning succeeded!");
    move_group.execute(plan.trajectory);
  } else {
    RCLCPP_ERROR(node->get_logger(), "Planning failed!");
  }

  rclcpp::shutdown();
  return 0;
}
```

### 6.4 运行示例

```bash
# 启动Panda机械臂demo
ros2 launch panda_moveit_config demo.launch.py

# 在另一个终端运行Python示例
ros2 run panda_examples motion_planner_example

# 或使用C++示例
ros2 run panda_examples_cpp motion_planner_cpp_example
```

---

## 7. Planning Scene应用

规划场景（Planning Scene）是MoveIt2中管理环境信息的核心组件，本节将详细介绍其使用方法。

### 7.1 创建PlanningSceneInterface

```python
from moveit.core.planning_scene_interface import PlanningSceneInterface

# 创建规划场景接口
planning_scene = PlanningSceneInterface()
```

### 7.2 添加障碍物

```python
# 添加一个box障碍物
box_pose = PoseStamped()
box_pose.header.frame_id = "panda_link0"
box_pose.pose.position.x = 0.5
box_pose.pose.position.y = 0.0
box_pose.pose.position.z = 0.5
box_pose.pose.orientation.w = 1.0

planning_scene.add_box("obstacle_box", box_pose, size=(0.1, 0.1, 0.1))

# 添加一个球体障碍物
sphere_pose = PoseStamped()
sphere_pose.header.frame_id = "panda_link0"
sphere_pose.pose.position.x = 0.3
sphere_pose.pose.position.y = 0.2
sphere_pose.pose.position.z = 0.3

planning_scene.add_sphere("obstacle_sphere", sphere_pose, radius=0.05)

# 添加mesh障碍物
mesh_pose = PoseStamped()
mesh_pose.header.frame_id = "panda_link0"
mesh_pose.pose.position.x = 0.4
mesh_pose.pose.position.y = -0.2
mesh_pose.pose.position.z = 0.3

planning_scene.attach_mesh("table_mesh", mesh_pose, filename="package://panda_description/meshes/collision/table.stl")
```

### 7.3 管理附加物体

```python
# 将物体附加到机器人末端
object_pose = PoseStamped()
object_pose.header.frame_id = "panda_link8"  # 末端执行器
object_pose.pose.position.x = 0.0
object_pose.pose.position.y = 0.0
object_pose.pose.position.z = 0.05
object_pose.pose.orientation.w = 1.0

planning_scene.attach_object(" grasped_object", object_pose, "panda_link8")

# 解除附加
planning_scene.remove_attached_object("grasped_object", "panda_link8")
```

### 7.4 碰撞检测

```python
# 检查当前状态是否有碰撞
robot_state = move_group.get_current_state()
collision_result = planning_scene.check_collision(robot_state)

if collision_result.collision:
    print(f"Collision detected with: {collision_result.contacts}")
else:
    print("No collision")
```

---

## 8. 进阶配置

### 8.1 碰撞检测配置

```yaml
# collision_common.yaml
collision_detector: FCL
padding:
  default_padding: 0.01
  link_padding:
    panda_link1: 0.005
    panda_link2: 0.005
scaling:
  robot_scale: 1.0
  link_scale:
    panda_link3: 0.9
```

### 8.2 轨迹后处理配置

```yaml
# trajectory_processing.yaml
time_optimal_parameterization:
  type: time_optimal_trajectory_generation/TimeOptimalTrajectoryGeneration
  tolerance: 0.05
  min_step_size: 0.01
  max_step_size: 0.1

iterative_spline_parameterization:
  type: iterative_spline/IterativeSplineParameterization
  criteria: 0.0
```

### 8.3 约束规划

```python
# 位置约束
position_constraint = moveit_msgs.msg.PositionConstraint()
position_constraint.header.frame_id = "panda_link0"
position_constraint.link_name = "panda_link8"
position_constraint.constraint_region.primitives.append(
    create_box([0.05, 0.05, 0.05], [0.5, 0.0, 0.5])
)

# 方向约束
orientation_constraint = moveit_msgs.msg.OrientationConstraint()
orientation_constraint.header.frame_id = "panda_link0"
orientation_constraint.link_name = "panda_link8"
orientation_constraint.orientation.w = 1.0
orientation_constraint.absolute_x_axis_tolerance = 0.1
orientation_constraint.absolute_y_axis_tolerance = 0.1
orientation_constraint.absolute_z_axis_tolerance = 3.14

# 应用约束
constraints = moveit_msgs.msg.Constraints()
constraints.position_constraints.append(position_constraint)
constraints.orientation_constraints.append(orientation_constraint)

move_group.set_path_constraints(constraints)
```

---

## 练习题

### 选择题

1. MoveIt2中的Planning Group是什么？
   - A) 一个具体的规划算法
   - B) 一组参与运动规划的关节集合
   - C) 一个碰撞检测器
   - D) 一个轨迹执行器
   
   **答案：B**。Planning Group是规划组，用于组织参与运动规划的关节集合。

2. 下列哪个不是MoveIt2的核心组件？
   - A) MoveGroup
   - B) PlanningScene
   - C) MoveItCpp
   - D) Nav2
   
   **答案：D**。Nav2是导航框架，不是MoveIt2的核心组件。

3. OMPL中的RRT*算法特点是什么？
   - A) 速度最快但非最优
   - B) 渐近最优
   - C) 只能用于无障碍环境
   - D) 需要大量预处理
   
   **答案：B**。RRT*具有渐近最优特性，规划迭代次数足够多时能得到最优解。

### 实践题

4. 配置一个简单的两关节机械臂的MoveIt2环境。
   
   **提示**：
   - 创建URDF定义两个旋转关节
   - 使用MoveIt!Setup Assistant生成配置文件
   - 验证配置是否正确

5. 编写Python程序，实现以下功能：
   - 将一个box障碍物添加到规划场景
   - 规划一条避开障碍物的轨迹
   - 执行轨迹
   
   **参考答案**：
   
   ```python
   import rclpy
   from rclpy.node import Node
   from geometry_msgs.msg import Pose, PoseStamped
   from moveit.core import RobotModel
   from moveit.core.planning_interface import MoveGroupInterface
   from moveit_configs_utils import MoveItConfigsBuilder
   
   class ObstaclePlanner(Node):
       def __init__(self):
           super().__init__('obstacle_planner')
           
           moveit_config = (
               MoveItConfigsBuilder("panda", package="panda_moveit_config")
               .robot_description(file_path="config/panda.urdf.xacro")
               .srdf(file_path="config/panda.srdf")
               .planning_scene_monitor(publish_robot_description=True)
               .build()
           )
           
           self.move_group = MoveGroupInterface(
               self, "panda_arm", moveit_config.robot_description,
               moveit_config.robot_description_semantic,
               moveit_config.planning_scene_monitor
           )
           
           # 添加障碍物
           self.add_obstacles()
       
       def add_obstacles(self):
           from moveit.core.planning_scene_interface import PlanningSceneInterface
           scene = PlanningSceneInterface()
           
           box_pose = PoseStamped()
           box_pose.header.frame_id = "panda_link0"
           box_pose.pose.position.x = 0.25
           box_pose.pose.position.y = 0.0
           box_pose.pose.position.z = 0.5
           box_pose.pose.orientation.w = 1.0
           
           scene.add_box("obstacle", box_pose, size=(0.1, 0.1, 0.2))
   
       def plan_around_obstacle(self):
           # 设置目标（绕过障碍物）
           target = Pose()
           target.position.x = 0.3
           target.position.y = 0.2
           target.position.z = 0.5
           target.orientation.w = 1.0
           
           self.move_group.set_pose_target(target)
           result = self.move_group.plan()
           
           if result:
               self.move_group.execute(result.trajectory)
   
   def main(args=None):
       rclpy.init(args=args)
       planner = ObstaclePlanner()
       planner.plan_around_obstacle()
       rclpy.shutdown()
   ```

---

## 本章小结

本章我们对MoveIt2进行了全面的介绍。首先了解了MoveIt2是什么以及它相对于ROS1版本的改进，然后深入学习了核心概念，包括规划场景、规划组、机器人模型等。系统架构部分展示了MoveIt2的模块化设计以及与ros2_control的集成方式。安装配置章节提供了完整的安装指南和配置文件说明。快速入门示例展示了Python和C++两种编程接口的基本用法。最后，我们学习了规划场景的管理和碰撞检测功能。

MoveIt2是ROS2生态中不可或缺的运动控制框架，掌握它将为后续学习机械臂控制、机器人抓取等高级应用打下坚实基础。

---

## 参考资料

### 官方文档

1. MoveIt2官方文档：<https://moveit.ros.org/>
2. MoveIt2 GitHub：<https://github.com/ros-planning/moveit2>
3. MoveIt2 Tutorials：<https://moveit.picknik.ai/>

### 机器人模型

4. Panda MoveIt Config：<https://github.com/ros-planning/moveit_resources/tree/main/panda_moveit_config>
5. URDF文档：<https://wiki.ros.org/urdf/XML>

### 规划算法

6. OMPL文档：<https://ompl.kavrakilab.org/>
7. KDL文档：<https://www.orocos.org/kdl>

---

## 下节预告

下一节我们将学习 **05-6 MoveIt2运动规划与控制编程**，深入探讨运动规划的详细过程、多种规划算法的使用、以及如何编写复杂的机器人控制程序。内容包括：自定义规划请求、轨迹后处理优化、控制器配置与执行、以及完整的机械臂抓取应用案例。

---

*本章学习完成！MoveIt2是机器人运动控制的核心框架，建议在真实机器人或仿真环境中多加练习，加深理解。*
