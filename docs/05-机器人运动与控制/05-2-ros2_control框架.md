# 05-2 ros2_control框架应用

> **前置课程**：05-1 移动底盘运动学模型
> **后续课程**：05-3 里程计计算

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在掌握了移动底盘的运动学模型后，我们现在来学习ROS2中最重要的机器人控制框架——ros2_control。ros2_control是ROS2官方提供的标准化控制框架，它将硬件抽象与控制算法解耦，让我们能够用统一的方式控制各种不同的机器人硬件。本节课将详细讲解ros2_control的架构，并通过实战示例展示如何为仿真机器人配置ros2_control。

---

## 1. ros2_control框架架构

ros2_control是ROS2的机器人控制框架，提供了标准化的接口来集成硬件和控制器。其核心设计理念是**硬件抽象**——将控制算法与具体硬件实现分离。

### 1.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        ros2_control 架构                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│   │  Controller  │     │  Controller  │     │  Controller  │   │
│   │  Manager     │     │  (PID)       │     │  (DiffDrive) │   │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘   │
│          │                    │                    │            │
│          └────────────────────┼────────────────────┘            │
│                               │                                  │
│                    ┌──────────┴──────────┐                     │
│                    │   Controller        │                     │
│                    │   Manager           │                     │
│                    │   (加载/卸载/切换)    │                     │
│                    └──────────┬──────────┘                     │
│                               │                                  │
│          ┌────────────────────┼────────────────────┐            │
│          │                    │                    │            │
│   ┌──────┴───────┐     ┌──────┴───────┐     ┌──────┴───────┐   │
│   │ Hardware     │     │ Hardware     │     │ Hardware     │   │
│   │ Interface    │     │ Interface    │     │ Interface    │   │
│   │ (关节位置)    │     │ (关节速度)    │     │ (力/力矩)     │   │
│   └──────┬───────┘     └──────┬───────┘     └──────┬───────┘   │
│          │                    │                    │            │
│   ┌──────┴───────┐     ┌──────┴───────┐     ┌──────┴───────┐   │
│   │  电机驱动    │     │  编码器      │     │  力传感器    │   │
│   └──────────────┘     └──────────────┘     └──────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件

ros2_control框架主要由三个核心组件构成：

| 组件 | 描述 | 职责 |
|------|------|------|
| **Controller Manager** | 控制器管理器 | 负责加载、卸载、切换控制器，维护控制器生命周期 |
| **Hardware Interface** | 硬件接口 | 抽象硬件操作，提供标准化的命令/状态接口 |
| **Controller** | 控制器 | 实现具体控制算法，如PID、轨迹跟踪等 |

### 1.3 数据流

```
用户指令 → Controller → Hardware Interface → 实际硬件
                ↑                              │
                └──── 状态反馈 (传感器) ←───────┘
```

---

## 2. 核心组件详解

### 2.1 硬件接口类型

ros2_control支持多种硬件接口类型，适用于不同的控制场景：

| 接口类型 | 命令类型 | 适用场景 | 示例 |
|----------|----------|----------|------|
| **Position Joint Interface** | `std_msgs/Float64` | 位置控制 | 机械臂关节定位 |
| **Velocity Joint Interface** | `std_msgs/Float64` | 速度控制 | 轮子速度控制 |
| **Effort Joint Interface** | `std_msgs/Float64` | 力控 | 柔顺控制、夹爪 |
| ** ** Gripper** | - | 夹爪控制 | 物体抓取 |

### 2.2 常用控制器

ros2_control提供了丰富的预置控制器：

#### (1) diff_drive_controller（差速驱动控制器）

专门用于差分驱动移动机器人的控制器：

- **输入**：cmd_vel (geometry_msgs/Twist)
- **输出**：左右轮速度命令
- **功能**：将上层导航的线性/角速度转换为左右轮速度

```yaml
# 参数说明
diff_drive_controller:
  ros__parameters:
    base_frame_id: base_link
    left_wheel_names: [left_wheel_joint]
    right_wheel_names: [right_wheel_joint]
    wheel_separation: 0.287
    wheel_radius: 0.033
    
    # 速度限制
    max_velocity: 1.0
    min_velocity: -1.0
    
    # 发布频率
    publish_rate: 50
    
    # 里程计框架
    odom_frame_id: odom
    enable_odom_tf: true
```

#### (2) joint_state_controller（关节状态控制器）

发布关节状态信息：

- **输入**：读取硬件接口状态
- **输出**：sensor_msgs/JointState

```yaml
joint_state_controller:
  ros__parameters:
    publish_rate: 50
```

#### (3) joint_trajectory_controller（关节轨迹控制器）

用于机械臂等关节型机器人的轨迹跟踪：

- **输入**：trajectory_msgs/JointTrajectory
- **输出**：位置/速度/力命令

---

## 3. 配置流程

为机器人配置ros2_control需要完成三个步骤：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. 实现硬件接口  │ → │  2. 编写YAML配置 │ → │  3. 编写启动文件 │
│     (C++)       │    │   (.yaml)       │    │   (.launch.py)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3.1 步骤一：实现硬件接口

硬件接口需要继承 `hardware_interface::RobotHardware` 基类，实现以下方法：

- `on_init()` - 初始化
- `on_configure()` - 配置阶段
- `on_activate()` - 激活
- `on_deactivate()` - 停用
- `read()` - 读取传感器数据
- `write()` - 发送控制命令

#### C++ 示例：模拟底盘硬件接口

```cpp
// include/diff_drive_botHardware.hpp
#ifndef DIFF_DRIVE_BOT_HARDWARE_HPP
#define DIFF_DRIVE_BOT_HARDWARE_HPP

#include <hardware_interface/robot_hardware_interface.hpp>
#include <hardware_interface/joint_state_interface.hpp>
#include <hardware_interface/joint_command_interface.hpp>
#include <ros/ros.h>
#include <geometry_msgs/Twist.h>

namespace diff_drive_bot
{

class DiffDriveBotHardware : public hardware_interface::RobotHardware
{
public:
  DiffDriveBotHardware();

  // RobotHardware 接口
  int init() override;
  int on_configure() override;
  int on_activate() override;
  int on_deactivate() override;
  int read() override;
  int write() override;

private:
  // 初始化ROS接口
  void initROS();

  // 关节名称
  std::vector<std::string> left_wheel_names_;
  std::vector<std::string> right_wheel_names_;
  
  // 状态与命令
  std::vector<double> joint_position_;
  std::vector<double> joint_velocity_;
  std::vector<double> joint_effort_;
  std::vector<double> joint_velocity_command_;
  
  // 硬件接口
  hardware_interface::JointStateInterface joint_state_interface_;
  hardware_interface::VelocityJointInterface velocity_joint_interface_;
  
  // ROS节点
  ros::NodeHandle nh_;
  ros::Publisher cmd_vel_pub_;
  
  // 模拟参数
  double wheel_separation_;
  double wheel_radius_;
};

}  // namespace diff_drive_bot

#endif
```

```cpp
// src/diff_drive_bot_hardware.cpp
#include "diff_drive_botHardware.hpp"
#include <pluginlib/class_list_macros.hpp>

namespace diff_drive_bot
{

DiffDriveBotHardware::DiffDriveBotHardware()
  : nh_("~")
{
}

// 注册硬件插件
PLUGINLIB_EXPORT_CLASS(diff_drive_bot::DiffDriveBotHardware,
                       hardware_interface::RobotHardware)

int DiffDriveBotHardware::init()
{
  // 1. 获取关节名称参数
  nh_.param<std::vector<std::string>>("left_wheel_names", 
                                        left_wheel_names_, 
                                        {"left_wheel_joint"});
  nh_.param<std::vector<std::string>>("right_wheel_names", 
                                        right_wheel_names_, 
                                        {"right_wheel_joint"});
  
  // 2. 获取机器人参数
  nh_.param<double>("wheel_separation", wheel_separation_, 0.287);
  nh_.param<double>("wheel_radius", wheel_radius_, 0.033);
  
  // 3. 初始化关节状态数组
  size_t num_joints = left_wheel_names_.size() + right_wheel_names_.size();
  joint_position_.resize(num_joints, 0.0);
  joint_velocity_.resize(num_joints, 0.0);
  joint_effort_.resize(num_joints, 0.0);
  joint_velocity_command_.resize(num_joints, 0.0);
  
  // 4. 注册接口
  // 注册关节状态接口
  for (size_t i = 0; i < left_wheel_names_.size(); ++i)
  {
    hardware_interface::JointStateHandle state_handle(
      left_wheel_names_[i], &joint_position_[i], 
      &joint_velocity_[i], &joint_effort_[i]);
    joint_state_interface_.registerHandle(state_handle);
  }
  for (size_t i = 0; i < right_wheel_names_.size(); ++i)
  {
    hardware_interface::JointStateHandle state_handle(
      right_wheel_names_[i], &joint_position_[left_wheel_names_.size() + i], 
      &joint_velocity_[left_wheel_names_.size() + i], 
      &joint_effort_[left_wheel_names_.size() + i]);
    joint_state_interface_.registerHandle(state_handle);
  }
  registerInterface(&joint_state_interface_);
  
  // 注册速度命令接口
  for (size_t i = 0; i < left_wheel_names_.size(); ++i)
  {
    hardware_interface::JointHandle cmd_handle(
      joint_state_interface_.getHandle(left_wheel_names_[i]),
      &joint_velocity_command_[i]);
    velocity_joint_interface_.registerHandle(cmd_handle);
  }
  for (size_t i = 0; i < right_wheel_names_.size(); ++i)
  {
    hardware_interface::JointHandle cmd_handle(
      joint_state_interface_.getHandle(right_wheel_names_[i]),
      &joint_velocity_command_[left_wheel_names_.size() + i]);
    velocity_joint_interface_.registerHandle(cmd_handle);
  }
  registerInterface(&velocity_joint_interface_);
  
  return 0;
}

int DiffDriveBotHardware::on_configure()
{
  initROS();
  return 0;
}

int DiffDriveBotHardware::on_activate()
{
  // 重置命令
  std::fill(joint_velocity_command_.begin(), 
            joint_velocity_command_.end(), 0.0);
  return 0;
}

int DiffDriveBotHardware::on_deactivate()
{
  return 0;
}

int DiffDriveBotHardware::read()
{
  // 在仿真中，这里可以从Gazebo读取实际位置
  // 或者使用运动学模型模拟
  
  // 示例：从命令积分计算位置（仿真用）
  static ros::Time last_time = ros::Time::now();
  ros::Time current_time = ros::Time::now();
  double dt = (current_time - last_time).toSec();
  last_time = current_time;
  
  // 简单积分（实际应使用更精确的模型）
  for (size_t i = 0; i < joint_position_.size(); ++i)
  {
    joint_position_[i] += joint_velocity_[i] * dt;
  }
  
  return 0;
}

int DiffDriveBotHardware::write()
{
  // 在仿真中，这里将速度命令发送到Gazebo
  // 或者直接应用运动学模型
  
  // 计算左右轮平均速度
  double v_left = joint_velocity_command_[0];
  double v_right = joint_velocity_command_[1];
  
  // 计算机器人运动
  double v = (v_right + v_left) / 2.0;
  double omega = (v_right - v_left) / wheel_separation_;
  
  // 更新速度（仿真用）
  joint_velocity_[0] = v_left;
  joint_velocity_[1] = v_right;
  
  // 发布cmd_vel（如果有上层导航）
  // geometry_msgs::Twist cmd;
  // cmd.linear.x = v;
  // cmd.angular.z = omega;
  // cmd_vel_pub_.publish(cmd);
  
  return 0;
}

void DiffDriveBotHardware::initROS()
{
  cmd_vel_pub_ = nh_.advertise<geometry_msgs::Twist>("/cmd_vel", 1);
}

}  // namespace diff_drive_bot
```

#### plugin.xml 配置

```xml
<!-- diff_drive_bot_hardware/plugin.xml -->
<library path="diff_drive_bot_hardware">
  <class name="diff_drive_bot/DiffDriveBotHardware" 
         type="diff_drive_bot::DiffDriveBotHardware"
         base_class_type="hardware_interface::RobotHardware">
    <description>
      Differential Drive Bot Hardware Interface for Simulation
    </description>
  </class>
</library>
```

#### CMakeLists.txt

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.8)
project(diff_drive_bot_hardware)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 寻找依赖
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_ros REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)

# 创建库
add_library(diff_drive_bot_hardware SHARED
  src/diff_drive_bot_hardware.cpp
)

# 添加依赖
ament_target_dependencies(diff_drive_bot_hardware
  "hardware_interface"
  "ament_cmake_ros"
  "geometry_messages"
)

# 注册插件
pluginlib_export_plugin_description_file(hardware_interface 
  plugins/diff_drive_bot_hardware.xml)

# 安装
install(TARGETS diff_drive_bot_hardware
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(plugins DIRECTORY plugins/
  DESTINATION share/${PROJECT_NAME}/plugins
)

ament_package()
```

### 3.2 步骤二：编写YAML配置文件

控制器配置文件定义了所有控制器的参数：

```yaml
# config/diff_drive_controllers.yaml

controller_manager:
  ros__parameters:
    update_rate: 50  # Hz
    
    # 控制器列表
    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController
    
    joint_state_broadcaster:
      type: joint_state_controller/JointStateController

# 差速驱动控制器配置
diff_drive_controller:
  ros__parameters:
    # 机器人基础参数
    base_frame_id: base_link
    odom_frame_id: odom
    
    # 轮子配置
    left_wheel_names: [left_wheel_joint]
    right_wheel_names: [right_wheel_joint]
    wheel_separation: 0.287  # 米
    wheel_radius: 0.033     # 米
    
    # 速度限制
    max_velocity: 1.0  # m/s
    min_velocity: -1.0  # m/s
    max_acceleration: 2.0  # m/s²
    
    # 发布配置
    publish_rate: 50  # Hz
    
    # 里程计与TF
    enable_odom_tf: true
    
    # PID参数 (可选，用于底层速度控制)
    velocity_rolling_window_size: 10

# 关节状态广播器配置
joint_state_broadcaster:
  ros__parameters:
    publish_rate: 50
```

### 3.3 步骤三：编写启动文件

```python
# launch/diff_drive.launch.py
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 获取包路径
    pkg_name = 'diff_drive_bot_hardware'
    pkg_share = get_package_share_directory(pkg_name)
    
    # 控制器配置文件
    controller_config = os.path.join(
        pkg_share, 'config', 'diff_drive_controllers.yaml'
    )
    
    # 机器人描述文件
    robot_description = os.path.join(
        pkg_share, 'description', 'robot.urdf.xacro'
    )
    
    # 启动参数
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    
    return LaunchDescription([
        # 声明参数
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock time'
        ),
        
        # 1. 启动robot_state_publisher发布机器人描述
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
            output='screen'
        ),
        
        # 2. 启动ros2_control节点（加载硬件接口）
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[controller_config],
            output='screen',
            remappings=[
                ('/diff_drive_controller/cmd_vel', '/cmd_vel'),
                ('/diff_drive_controller/odom', '/odom'),
            ]
        ),
        
        # 3. 加载并激活diff_drive_controller
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['diff_drive_controller'],
            output='screen'
        ),
        
        # 4. 加载并激活joint_state_broadcaster
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster'],
            output='screen'
        ),
    ])
```

---

## 4. 实战：为仿真机器人配置ros2_control

本节将展示完整的配置流程，使用Gazebo仿真环境。

### 4.1 创建工作空间

```bash
# 创建工作空间
mkdir -p ~/ws_ros2_control/src
cd ~/ws_ros2_control

# 初始化
source /opt/ros/humble/setup.bash
ros2 pkg create diff_drive_bot --dependencies \
    hardware_interface geometry_msgs \
    ros2_controllers diff_drive_controller
```

### 4.2 实现硬件接口

按照上一节的代码示例，实现自定义硬件接口。对于Gazebo仿真，可以使用 `gazebo_ros2_control` 包提供的默认接口：

```yaml
# config/gazebo_controllers.yaml
gazebo_ros2_control:
  ros__parameters:
    update_rate: 50
    
    diff_drive:
      type: diff_drive_controller/DiffDriveController
    
    joint_state:
      type: joint_state_controller/JointStateController

diff_drive:
  ros__parameters:
    base_frame_id: base_footprint
    odom_frame_id: odom
    enable_odom_tf: true
    
    left_wheel_names: [left_wheel_joint]
    right_wheel_names: [right_wheel_joint]
    
    wheel_separation: 0.287
    wheel_radius: 0.033
    
    max_velocity: 1.0
    min_velocity: -1.0
    max_acceleration: 2.0
    
    publish_rate: 50
    
joint_state:
  ros__parameters:
    publish_rate: 50
```

### 4.3 启动仿真并测试

#### 启动命令

```bash
# 1. 启动Gazebo仿真
ros2 launch gazebo_ros gazebo.launch.py world:=empty.world

# 2. 加载机器人模型（带ros2_control插件）
ros2 launch diff_drive_bot gazebo.launch.py

# 3. 查看已加载的控制器
ros2 control list_controllers
```

#### 查看控制器状态

```bash
# 查看所有控制器
ros2 control list_controllers

# 输出示例:
# diff_drive_controller[diff_drive_controller/DiffDriveController] active
# joint_state_broadcaster[joint_state_controller/JointStateController] active
```

### 4.4 通过话题控制机器人运动

ros2_control提供标准化的ROS2接口进行控制：

#### (1) 使用cmd_vel话题（推荐）

```bash
# 前进 0.5 m/s
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

# 旋转 0.5 rad/s
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.5}}"

# 停止
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
```

#### (2) 使用rqt工具

```bash
# 启动rqt
rqt

#  Plugins → Topics → Message Publisher
#  选择 /cmd_vel 话题，配置 Twist 消息
```

#### (3) 使用teleop_twist_keyboard

```bash
# 安装
sudo apt install ros-humble-teleop-twist-keyboard

# 运行
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### 4.5 验证里程计输出

```bash
# 订阅里程计话题
ros2 topic echo /odom

# 输出示例:
# header:
#   stamp:
#     sec: 1234
#     nanosec: 567890000
#   frame_id: odom
# child_frame_id: base_footprint
# pose:
#   pose:
#     position:
#       x: 1.234
#       y: 0.567
#       z: 0.0
#     orientation:
#       x: 0.0
#       y: 0.0
#       z: 0.123
#       w: 0.992
# twist:
#   twist:
#     linear:
#       x: 0.5
#       y: 0.0
#       z: 0.0
#     angular:
#       x: 0.0
#       y: 0.0
#       z: 0.0
```

---

## 5. 调试与故障排除

### 5.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 控制器无法加载 | 硬件接口未注册 | 检查plugin.xml配置 |
| 机器人不动 | 关节名称不匹配 | 核对URDF和YAML中的joint名称 |
| 里程计漂移 | 仿真时间问题 | 确认use_sim_time参数 |
| 控制器状态为unconfigured | 配置文件错误 | 检查YAML语法和参数名 |

### 5.2 调试命令

```bash
# 1. 查看控制器管理器日志
ros2 param list /controller_manager

# 2. 查看硬件接口状态
ros2 control list_hardware_interfaces

# 3. 测试控制器加载
ros2 controller load_diff_drive_controller
ros2 controller configure diff_drive_controller
ros2 controller activate diff_drive_controller

# 4. 查看控制命令
ros2 topic hz /diff_drive_controller/cmd_vel
ros2 topic echo /diff_drive_controller/cmd_vel

# 5. 使用rqt_reconfigure动态调整参数
ros2 run rqt_reconfigure rqt_reconfigure
```

---

## 6. 进阶话题

### 6.1 多控制器切换

ros2_control支持运行时切换控制器：

```bash
# 停用当前控制器
ros2 controller deactivate diff_drive_controller

# 加载新控制器（如手动模式）
ros2 controller load controller_manager manual_velocity_controller
ros2 controller configure manual_velocity_controller
ros2 controller activate manual_velocity_controller
```

### 6.2 自定义控制器

创建自定义控制器的步骤：

1. 继承 `controller_interface::ControllerBase`
2. 实现 `init()`, `update()`, `on_configure()`, `on_activate()`, `on_deactivate()`
3. 在 `plugin.xml` 中注册
4. 在 YAML 中配置

### 6.3 与MoveIt集成

```yaml
# MoveIt配置中的控制器配置
controllers:
  - name: diff_drive_controller
    action_ns: follow_velocity
    type: FollowVelocity
```

---

## 7. 练习题

### 练习1：硬件接口基础

**问题**：在ros2_control中，`read()` 和 `write()` 方法分别在什么时候被调用？它们的主要职责是什么？

<details>
<summary>查看答案</summary>

**答案**：

- `read()` 方法在每个控制周期开始时被调用，主要职责是从硬件（如编码器、传感器）读取状态数据（位置、速度、力矩等）
- `write()` 方法在控制周期结束时被调用，主要职责是将控制命令（如目标速度、目标位置）发送给执行器

它们的调用顺序：read() → 控制算法计算 → write()
</details>

### 练习2：差速驱动参数计算

**问题**：已知TurtleBot3的轮距L=0.287m，轮子半径r=0.033m。若要求机器人以0.2m/s的线速度前进，左右轮应该分别以多大的速度转动？

<details>
<summary>查看答案</summary>

**答案**：

根据差分驱动运动学公式：
- 机器人线速度 v = (v_R + v_L) / 2
- 机器人角速度 ω = (v_R - v_L) / L

当机器人直线前进时（ω=0），有 v_R = v_L = v

因此：v_R = v_L = 0.2 m/s

换算成角速度：ω_wheel = v / r = 0.2 / 0.033 ≈ 6.06 rad/s ≈ 57.9 RPM

</details>

### 练习3：YAML配置

**问题**：以下YAML配置中有一处错误，请指出并说明原因。

```yaml
diff_drive_controller:
  ros__parameters:
    left_wheel_names: [left_wheel_joint]  # 只有左轮
    wheel_separation: 0.287
    max_velocity: -1.0  # 负值速度限制
```

<details>
<summary>查看答案</summary>

**答案**：

问题：`max_velocity: -1.0` 是错误的

原因：
1. 速度限制应该是正值，表示允许的最大速度绝对值
2. `min_velocity` 才是负值，表示允许的最小（反向）速度
3. 正确配置应该是：
   ```yaml
   max_velocity: 1.0
   min_velocity: -1.0
   ```

另外，缺少 `right_wheel_names` 配置，这也可能导致控制器加载失败。

</details>

### 练习4：话题发布

**问题**：使用ros2 topic命令发布一个让机器人原地左转（角速度0.5rad/s）的Twist消息。

<details>
<summary>查看答案</summary>

**答案**：

```bash
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.5}}"
```

说明：
- linear.x = 0.0：表示没有直线运动
- angular.z = 0.5：表示绕Z轴（垂直方向）旋转，0.5 rad/s
- 在ROS坐标中，正的angular.z表示逆时针旋转（机器人左转）

</details>

---

## 8. 总结

本节课我们学习了ros2_control框架的核心概念和配置方法：

| 知识点 | 关键要点 |
|--------|----------|
| **架构** | Controller Manager → Hardware Interface → 实际硬件 |
| **接口类型** | Position、Velocity、Effort三大接口 |
| **常用控制器** | diff_drive_controller、joint_state_controller |
| **配置流程** | 实现硬件接口 → YAML配置 → 启动文件 |
| **控制方式** | 通过/cmd_vel话题发送Twist命令 |

ros2_control的标准化设计使得机器人控制代码具有良好的可移植性——同一套控制算法可以应用于仿真、真机或不同型号的机器人。

---

## 下节预告

**05-3 里程计计算** 将深入讲解：
- 里程计数据来源与计算方法
- 坐标系变换（odom → base_link）
- 误差分析与卡尔曼滤波
- 实际代码实现

---

*课程代码仓库：https://github.com/howe12/embodied-course*
