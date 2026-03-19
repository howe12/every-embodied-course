# 07-2 ROS2仿真-Gazebo仿真平台与ROS2集成

> **前置课程**：07-1 ROS2仿真-机器人URDF建模规范
> **后续课程**：07-3 ROS2仿真-Xacro宏定义与参数化建模

**作者**：霍海杰 | **联系方式**：howe12@126.com

> **前置说明**：Gazebo是机器人领域最流行的仿真平台之一，它提供了高质量的物理仿真和灵活的3D环境构建能力。本节将深入讲解Gazebo仿真平台的核心概念、ROS2与Gazebo的集成方法、仿真世界建模技术，以及如何将机器人模型放入仿真环境中运行。通过本节学习，你将掌握使用Gazebo进行机器人仿真的完整流程。

---

## 1. Gazebo概述

Gazebo是一款开源的3D机器人仿真软件，由Open Source Robotics Foundation（OSRF）开发维护。它能够模拟复杂的室内外环境，支持多种机器人模型，并提供逼真的物理反馈。Gazebo广泛应用于机器人算法开发、控制系统测试、产品原型验证等领域。

### 1.1 Gazebo的核心特性

Gazebo具有以下几个核心特性，使其成为机器人仿真的首选工具：

**高保真物理引擎**：Gazebo集成了多个物理引擎，包括ODE（默认）、Bullet、Simbody和DART，能够精确模拟刚体动力学、碰撞检测、关节约束等物理现象。对于大多数机器人仿真需求，ODE引擎已经足够使用；对于需要更高精度的人形机器人或柔性物体仿真，可以选择Simbody或DART引擎。

**丰富的传感器模型**：Gazebo提供了多种传感器的仿真模型，包括激光雷达、深度相机、IMU、GPS、触觉传感器等。这些传感器模型能够生成与真实硬件相似的数据格式，可以无缝对接到ROS系统中。

**灵活的环境构建**：Gazebo提供了直观的GUI界面和强大的SDF（Simulation Description Format）格式，允许用户创建从简单室内环境到复杂室外场景的各种仿真世界。

**分布式仿真支持**：Gazebo支持通过网络进行分布式仿真，多个计算节点可以协同工作，模拟大规模的机器人系统或复杂的交通场景。

### 1.2 Gazebo与ROS的集成历史

Gazebo与ROS之间有着深厚的历史渊源。从ROS诞生之初，就开始了与Gazebo的集成工作。经历了两个主要阶段：

**ros_gz桥接阶段**：在ROS1时期，ros_gz包提供了ROS与Gazebo之间的通信桥接。开发者需要分别安装ROS和Gazebo，通过ros_gz话题转换实现数据交互。这种方式虽然可行，但配置过程较为繁琐，且两个系统之间的版本兼容性常常带来麻烦。

**ignition gazebo阶段（现为Gazebo Sim）**：随着ROS2的发展，Gazebo也进行了重大升级。Ignition Gazebo（现更名为Gazebo Sim）从架构上更好地支持了ROS2。ros_gz桥接功能得到了显著增强，支持更丰富的数据类型和更高效的通信。同时，gazebo_ros_pkgs包提供了原生的ROS2接口，使得在Gazebo中仿真ROS2机器人变得更加直观。

当前推荐使用Gazebo Sim（又称Fortress、Humble等版本）与ROS2 Humble或更高版本配合使用，以获得最佳的开发体验。

### 1.3 Gazebo界面介绍

启动Gazebo后，你会看到以下主要界面区域：

```
┌─────────────────────────────────────────────────────────────┐
│  菜单栏：File | Edit | View | | Window | Help              │
├──────────┬──────────────────────────────────┬───────────────┤
│          │                                  │               │
│  物体    │                                  │   属性面板    │
│  列表    │        3D视窗                   │   (Properties)│
│          │                                  │               │
│ (World)  │                                  │  - Pose       │
│          │                                  │  - Geometry   │
│          │                                  │  - Material   │
│          │                                  │  - Physics    │
├──────────┴──────────────────────────────────┴───────────────┤
│  底部工具栏：播放 | 暂停 | 步进 | 时间显示 | 物理引擎选择    │
└─────────────────────────────────────────────────────────────┘
```

- **3D视窗**：显示仿真世界的实时渲染效果，支持视角的平移、旋转和缩放
- **物体列表**：显示当前仿真世界中的所有模型对象
- **属性面板**：显示选中物体的详细参数，可进行实时修改
- **底部工具栏**：控制仿真的播放、暂停和单步执行

---

## 2. ROS2-Gazebo集成

ROS2与Gazebo的集成是通过ros_gz桥接包和gazebo_ros_pkgs实现的。本节将详细介绍安装配置方法和核心集成概念。

### 2.1 安装配置

在ROS2 Humble及以上版本中，安装Gazebo仿真环境非常简单：

```bash
# 安装Gazebo Sim（Fortress版本）
sudo apt install ros-humble-gazebo-ros-pkgs

# 安装额外的Gazebo插件
sudo apt install ros-humble-gazebo-ros2-control
sudo apt install ros-humble-gazebo-ros2-pid

# 验证安装
ros2 pkg list | grep gazebo
```

安装完成后，可以通过以下命令启动一个空的Gazebo世界：

```bash
# 启动Gazebo（使用默认的Fortress版本）
ros2 launch gazebo_ros gazebo.launch.py
```

或者使用更简洁的命令：

```bash
# 使用ign命令启动
ign gazebo
```

### 2.2 ros_gz桥接原理

ros_gz是连接ROS2与Gazebo的核心桥梁，它实现了以下功能：

**话题桥接**：将Gazebo中的仿真数据发布到ROS2话题，同时将ROS2的控制指令传递给Gazebo。典型的桥接包括：
- 激光雷达数据：/scan → /laser_scan
- 图像数据：/camera/image_raw → /image_raw
- 关节状态：/joint_states → /joint_states
- 关节控制：/joint_trajectory → /joint_commands

**服务桥接**：提供ROS2客户端调用Gazebo服务的能力，如模型Spawn、物理参数调整等。

**TF转换**：协调Gazebo内部坐标系与ROS2坐标系系统之间的转换。

ros_gz桥接的启动方式通常在一个launch文件中配置：

```python
# gazebo_ros_launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 启动Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([
                    FindPackageShare('gazebo_ros'),
                    'launch',
                    'gazebo.launch.py'
                ])
            ])
        ),
        
        # 启动ros_gz桥接节点
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='scan_bridge',
            arguments=['/scan@sensor_msgs/msg/LaserScan@ignition.msgs.LaserScan'],
            output='screen'
        ),
        
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='image_bridge',
            arguments=['/camera/image_raw@sensor_msgs/msg/Image@ignition.msgs.Image'],
            output='screen'
        ),
        
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='cmd_vel_bridge',
            arguments=['/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist'],
            output='screen'
        ),
    ])
```

### 2.3 gazebo_ros_pkgs

gazebo_ros_pkgs是ROS2官方提供的Gazebo集成包集合，包含了多个关键功能包：

| 功能包 | 功能描述 |
|--------|----------|
| gazebo_ros | 核心功能，提供ROS2与Gazebo的基础集成 |
| gazebo_ros_control | 集成ros2_control框架，支持关节控制器 |
| gazebo_ros_diff_drive | 差速驱动插件 |
| gazebo_ros_joint_state_publisher | 关节状态发布插件 |
| gazebo_ros_skid_steering | 滑移转向驱动插件 |

这些功能包通过SDF插件的形式与Gazebo交互。在URDF/XACRO文件中，可以通过`<gazebo>`标签引用这些插件。

---

## 3. 仿真世界建模

仿真世界（World）是Gazebo中用于描述仿真环境的核心概念。一个完整的世界文件包含了所有物理对象、传感器、光照、地面等元素。

### 3.1 SDF格式基础

SDF（Simulation Description Format）是Gazebo用于描述仿真世界的XML格式。与URDF相比，SDF支持更丰富的物理特性描述，包括：

- 多个物理引擎的支持
- 嵌套模型（nested models）
- 粒子系统
- 海面、焦散等特效
- 传感器噪声模型

一个简单的SDF世界文件结构如下：

```xml
<?xml version="1.0" ?>
<sdf version="1.10">
  <world name="robot_world">
    
    <!-- 物理引擎配置 -->
    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>
    
    <!-- 光照设置 -->
    <scene>
      <ambient>0.4 0.4 0.4 1</ambient>
      <shadows>true</shadows>
      <grid>true</grid>
    </scene>
    
    <!-- 光源 -->
    <light type="directional" name="sun">
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <cast_shadows>true</cast_shadows>
      <attenuation>
        <range>1000</range>
        <constant>0.9</constant>
        <linear>0.01</linear>
        <quadratic>0.001</quadratic>
      </attenuation>
    </light>
    
    <!-- 地面 -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <pose>0 0 0 0 0 0</pose>
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
          <surface>
            <friction>
              <ode>
                <mu>1.0</mu>
                <mu2>1.0</mu2>
              </ode>
            </friction>
          </surface>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>100 100</size>
            </plane>
          </geometry>
          <material>
            <ambient>0.5 0.5 0.5 1</ambient>
            <diffuse>0.5 0.5 0.5 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
    <!-- 障碍物 -->
    <model name="box_obstacle">
      <pose>2 0 0.5 0 0 0</pose>
      <link name="link">
        <pose>0 0 0 0 0 0</pose>
        <collision name="collision">
          <geometry>
            <box>
              <size>1 1 1</size>
            </box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box>
              <size>1 1 1</size>
            </box>
          </geometry>
          <material>
            <diffuse>1 0 0 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
  </world>
</sdf>
```

### 3.2 创建室内环境

创建室内仿真环境需要考虑以下几个方面：

**地面与墙面**：室内环境通常需要一个封闭的空间。可以使用SDF的模型库，也可以手动创建墙面模型：

```xml
<!-- 室内房间模型 -->
<model name="room">
  <!-- 地面 -->
  <link name="floor">
    <pose>0 0 0 0 0 0</pose>
    <collision name="floor_collision">
      <geometry>
        <box>
          <size>10 8 0.1</size>
        </box>
      </geometry>
    </collision>
    <visual name="floor_visual">
      <geometry>
        <box>
          <size>10 8 0.1</size>
        </box>
      </geometry>
      <material>
        <diffuse>0.6 0.6 0.6 1</diffuse>
      </material>
    </visual>
  </link>
  
  <!-- 墙壁（简化表示） -->
  <link name="wall_north">
    <pose>0 4 1 0 0 0</pose>
    <collision name="wall_north_collision">
      <geometry>
        <box>
          <size>10 0.1 2</size>
        </box>
      </geometry>
    </collision>
    <visual name="wall_north_visual">
      <geometry>
        <box>
          <size>10 0.1 2</size>
        </box>
      </geometry>
      <material>
        <diffuse>0.8 0.8 0.8 1</diffuse>
      </material>
    </visual>
  </link>
  
  <!-- 其他墙壁类似... -->
</model>
```

**室内装饰**：为了使仿真更加真实，可以添加桌子、椅子、柜子等家具模型。Gazebo提供了模型数据库（Model Database），可以直接引用其中的模型：

```xml
<!-- 引用Gazebo模型库的模型 -->
<world>
  <!-- 从模型库加载桌子 -->
  <include>
    <uri>https://fuel.ignitionfuel.org/1.0/OpenRobotics/models/Table</uri>
    <name>table</name>
    <pose>2 2 0 0 0 1.57</pose>
  </include>
</world>
```

### 3.3 创建室外环境

室外环境仿真需要考虑更大的尺度范围和更复杂的地形：

**地形创建**：Gazebo支持通过高度图（Heightmap）创建起伏的地形：

```xml
<model name="terrain">
  <link name="terrain_link">
    <gravity>true</gravity>
    <collision name="terrain_collision">
      <geometry>
        <heightmap>
          <uri>file://media/heightmap/terrain.png</uri>
          <size>50 50 2</size>
          <pos>0 0 0</pos>
        </heightmap>
      </geometry>
    </collision>
    <visual name="terrain_visual">
      <geometry>
        <heightmap>
          <texture>
            <size>10</size>
            <diffuse>textures/terrain/dirt_diffuse.png</diffuse>
            <normal>textures/terrain/dirt_normal.png</normal>
          </texture>
          <uri>file://media/heightmap/terrain.png</uri>
          <size>50 50 2</size>
          <pos>0 0 0</pos>
        </heightmap>
      </geometry>
    </visual>
  </link>
</model>
```

**天空与环境**：使用`<sky>`和`<ambient>`元素设置户外光照：

```xml
<scene>
  <sky>
    <clouds>
      <speed>4</speed>
      <humidity>50</humidity>
      <mean_size>0.5</mean_size>
    </clouds>
  </sky>
  <ambient>0.5 0.5 0.5 1</ambient>
  <background>0.5 0.7 1 1</background>
</scene>
```

---

## 4. 机器人放入仿真环境

将机器人模型放入Gazebo仿真环境中运行，需要完成以下几个关键步骤：模型准备、插件配置、launch文件编写。

### 4.1 机器人模型准备

首先，确保你的机器人模型已经是URDF/XACRO格式，并且包含必要的Gazebo标签。如果没有，请参考上一节课程（07-1）的内容。

一个完整的Gazebo可加载机器人URDF应该包含：

```xml
<!-- robot.urdf.xacro -->
<?xml version="1.0" ?>
<robot name="my_robot" xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 包含Gazebo相关宏定义 -->
  <xacro:include filename="$(find gazebo_ros)/urdf/gazebo.urdf.xacro"/>
  
  <!-- 基础链接定义 -->
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="0.1" radius="0.2"/>
      </geometry>
      <material name="blue">
        <color rgba="0 0 0.8 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder length="0.1" radius="0.2"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="5.0"/>
      <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/>
    </inertial>
  </link>
  
  <!-- Gazebo物理属性扩展 -->
  <gazebo reference="base_link">
    <material>Gazebo/Blue</material>
    <mu1>0.2</mu1>
    <mu2>0.2</mu2>
  </gazebo>
  
  <!-- 关节定义 -->
  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="0 0.15 0" rpy="-1.5707 0 0"/>
    <axis xyz="0 0 1"/>
  </joint>
  
  <link name="left_wheel">
    <visual>
      <geometry>
        <cylinder length="0.05" radius="0.1"/>
      </geometry>
      <material name="black"/>
    </visual>
    <collision>
      <geometry>
        <cylinder length="0.05" radius="0.1"/>
      </geometry>
    </collision>
  </link>
  
  <gazebo reference="left_wheel">
    <material>Gazebo/Black</material>
  </gazebo>
  
  <!-- 右侧轮子类似... -->
  
</robot>
```

### 4.2 Gazebo插件配置

Gazebo通过插件实现与ROS的交互。对于差速驱动机器人，最常用的是`gazebo_ros_diff_drive`插件：

```xml
<!-- 在URDF中添加差速驱动插件 -->
<gazebo>
  <plugin filename="libgazebo_ros_diff_drive.so" name="gazebo_ros_diff_drive">
    
    <!-- 插件参数 -->
    <ros>
      <namespace>/my_robot</namespace>
      <remapping>cmd_vel:=cmd_vel</remapping>
      <remapping>odom:=odom</remapping>
    </ros>
    
    <!-- 车辆参数 -->
    <update_rate>50</update_rate>
    
    <!-- 车轮配置 -->
    <left_joint>left_wheel_joint</left_joint>
    <right_joint>right_wheel_joint</right_joint>
    <wheel_separation>0.3</wheel_separation>
    <wheel_diameter>0.2</wheel_diameter>
    
    <!-- 驱动参数 -->
    <max_wheel_torque>20</max_wheel_torque>
    <max_wheel_acceleration>1.0</max_wheel_acceleration>
    
    <!-- 命令输入 -->
    <command_topic>cmd_vel</command_topic>
    
    <!-- 发布TF和里程计 -->
    <publish_odom>true</publish_odom>
    <publish_odom_tf>true</publish_odom_tf>
    <publish_wheel_tf>true</publish_wheel_tf>
    
    <!-- 里程计参数 -->
    <odometry_topic>odom</odometry_topic>
    <odometry_frame>odom</odometry_frame>
    <robot_base_frame>base_link</robot_base_frame>
    
  </plugin>
</gazebo>
```

**关键参数说明**：

| 参数 | 说明 | 典型值 |
|------|------|--------|
| `update_rate` | 控制器更新频率 | 50Hz |
| `wheel_separation` | 左右轮中心距 | 0.3m |
| `wheel_diameter` | 车轮直径 | 0.2m |
| `max_wheel_torque` | 最大驱动扭矩 | 20Nm |
| `max_wheel_acceleration` | 最大加速度 | 1.0 m/s² |

对于需要发布激光雷达等传感器的机器人，还需要添加相应的传感器插件：

```xml
<!-- 激光雷达传感器插件 -->
<gazebo reference="laser_link">
  <sensor type="ray" name="rplidar">
    <pose>0 0 0 0 0 0</pose>
    <visualize>true</visualize>
    <update_rate>10</update_rate>
    <ray>
      <scan>
        <horizontal>
          <samples>360</samples>
          <resolution>1</resolution>
          <min_angle>-3.14159</min_angle>
          <max_angle>3.14159</max_angle>
        </horizontal>
      </scan>
      <range>
        <min>0.1</min>
        <max>10.0</max>
        <resolution>0.01</resolution>
      </range>
      <noise>
        <type>gaussian</type>
        <mean>0.0</mean>
        <stddev>0.01</stddev>
      </noise>
    </ray>
    <plugin filename="libgazebo_ros_ray_sensor.so" name="gazebo_ros_laser">
      <ros>
        <namespace>/my_robot</namespace>
        <remapping>~/out:=scan</remapping>
      </ros>
      <output_type>sensor_msgs/LaserScan</output_type>
    </plugin>
  </sensor>
</gazebo>
```

### 4.3 Launch文件编写

现在创建一个完整的launch文件来启动Gazebo仿真环境并加载机器人：

```python
# my_robot_gazebo.launch.py
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # 获取功能包路径
    pkg_name = 'my_robot_description'
    pkg_gazebo = get_package_share_directory('gazebo_ros')
    
    # 机器人URDF文件路径
    urdf_file = os.path.join(
        get_package_share_directory(pkg_name),
        'urdf',
        'robot.urdf.xacro'
    )
    
    # Gazebo世界文件路径（可选）
    world_file = os.path.join(
        get_package_share_directory(pkg_name),
        'worlds',
        'empty.world'
    )
    
    return LaunchDescription([
        # 声明参数
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock time'
        ),
        
        # 启动Gazebo
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo, 'launch', 'gazebo.launch.py')
            ),
            launch_arguments={
                'world': world_file,
                'verbose': 'false',
            }.items()
        ),
        
        # Spawn机器人模型到Gazebo
        Node(
            package='gazebo_ros',
            executable='spawn_entity.py',
            arguments=[
                '-entity', 'my_robot',
                '-file', urdf_file,
                '-x', '0', '-y', '0', '-z', '0.1',
                '-Y', '0'
            ],
            output='screen'
        ),
        
        # 启动机器人状态发布节点
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'use_sim_time': True,
                'robot_description': open(urdf_file).read()
            }],
            output='screen'
        ),
        
        # 启动关节状态发布器
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[{
                'use_sim_time': True
            }],
            output='screen'
        ),
    ])
```

### 4.4 运行仿真

完成以上配置后，可以按照以下步骤运行仿真：

```bash
# 1. 编译功能包
cd ~/ros2_ws
colcon build --packages-select my_robot_description my_robot_gazebo
source install/setup.bash

# 2. 启动仿真
ros2 launch my_robot_gazebo my_robot_gazebo.launch.py

# 3. 在另一个终端启动键盘控制
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/my_robot/cmd_vel

# 4. 查看话题列表
ros2 topic list

# 5. 查看机器人里程计
ros2 topic echo /my_robot/odom

# 6. 在rviz2中可视化
ros2 launch rviz2 rviz2.launch.py
```

### 4.5 使用ros2_control进行仿真控制

除了使用Gazebo原生插件，ROS2生态中的`ros2_control`框架也提供了与Gazebo的集成。这种方式的优势是可以统一使用ros2_control的控制器配置：

**在URDF中添加ros2_control相关配置**：

```xml
<!-- robot.ros2_control.xacro -->
<robot name="my_robot" xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- ros2_control硬件接口 -->
  <xacro:macro name="diff_drive_control_params" params="namespace">
    <ros2_control name="GazeboSystem" type="system">
      <hardware>
        <plugin>gazebo_ros2_control/GazeboSystem</plugin>
      </hardware>
      
      <!-- 关节配置 -->
      <joint name="left_wheel_joint">
        <command_interface>velocity</command_interface>
        <state_interface>position</state_interface>
        <state_interface>velocity</state_interface>
      </joint>
      <joint name="right_wheel_joint">
        <command_interface>velocity</command_interface>
        <state_interface>position</state_interface>
        <state_interface>velocity</state_interface>
      </joint>
    </ros2_control>
  </xacro:macro>
  
  <!-- 调用宏 -->
  <xacro:diff_drive_control_params namespace=""/>
  
  <!-- Gazebo ros2_control插件 -->
  <gazebo>
    <plugin filename="libgazebo_ros2_control.so" name="gazebo_ros2_control">
      <ros>
        <namespace>/my_robot</namespace>
      </ros>
      <parameters>$(find my_robot_bringup)/config/robot_controllers.yaml</parameters>
    </plugin>
  </gazebo>
  
</robot>
```

**创建控制器配置文件**：

```yaml
# robot_controllers.yaml
controller_manager:
  ros__parameters:
    update_rate: 50
    
    diff_drive_controller:
      type: diff_drive_controller/DiffDriveController

diff_drive_controller:
  ros__parameters:
    left_wheel_names: ["left_wheel_joint"]
    right_wheel_names: ["right_wheel_joint"]
    wheel_separation: 0.3
    wheel_radius: 0.1
    
    publish_rate: 50
    base_frame_id: base_link
    odom_frame_id: odom
    
    use_stamped_velocity: false
    
    # 速度限制
    max_velocity: 1.0
    min_velocity: -1.0
    max_acceleration: 2.0
    max_deceleration: 2.0

joint_state_broadcaster:
  type: joint_state_broadcaster/JointStateBroadcaster
```

**启动ros2_control**：

```python
# my_robot_ros2_control.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # 加载控制器
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=[
                'diff_drive_controller',
                'joint_state_broadcaster',
                '--controller-manager-timeout', '30'
            ],
            output='screen'
        ),
    ])
```

---

## 5. 实战：创建完整机器人仿真环境

本节我们将创建一个完整的机器人仿真项目，包括机器人模型、仿真环境和控制脚本。

### 5.1 项目结构

```
my_robot_sim/
├── my_robot_description/
│   ├── urdf/
│   │   ├── robot.urdf.xacro
│   │   └── macros.xacro
│   ├── meshes/
│   │   └── robot.dae
│   ├── config/
│   │   └── robot_controllers.yaml
│   ├── worlds/
│   │   └── office.world
│   └── launch/
│       └── robot_description.launch.py
├── my_robot_gazebo/
│   └── launch/
│       └── simulation.launch.py
└── my_robot_control/
    ├── launch/
    │   └── teleop.launch.py
    └── setup.py
```

### 5.2 创建URDF模型

```xml
<!-- my_robot_description/urdf/robot.urdf.xacro -->
<?xml version="1.0" ?>
<robot name="diff_robot" xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 参数定义 -->
  <xacro:property name="PI" value="3.1415926535897931"/>
  <xacro:property name="base_radius" value="0.15"/>
  <xacro:property name="base_height" value="0.1"/>
  <xacro:property name="wheel_radius" value="0.05"/>
  <xacro:property name="wheel_width" value="0.04"/>
  <xacro:property name="wheel_separation" value="0.22"/>
  
  <!-- 包含Gazebo宏 -->
  <xacro:include filename="$(find gazebo_ros)/urdf/gazebo.urdf.xacro"/>
  
  <!-- 机器人底座 -->
  <link name="base_link">
    <visual>
      <geometry>
        <cylinder length="${base_height}" radius="${base_radius}"/>
      </geometry>
      <material name="blue">
        <color rgba="0.2 0.4 0.8 1"/>
      </material>
    </visual>
    <collision>
      <geometry>
        <cylinder length="${base_height}" radius="${base_radius}"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="3.0"/>
      <inertia ixx="0.015" ixy="0" ixz="0" iyy="0.015" iyz="0" izz="0.025"/>
    </inertial>
  </link>
  
  <gazebo reference="base_link">
    <material>Gazebo/Blue</material>
  </gazebo>
  
  <!-- 左轮 -->
  <link name="left_wheel">
    <visual>
      <geometry>
        <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
      </geometry>
      <origin rpy="${PI/2} 0 0"/>
      <material name="black"/>
    </visual>
    <collision>
      <geometry>
        <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
      </geometry>
      <origin rpy="${PI/2} 0 0"/>
    </collision>
    <inertial>
      <mass value="0.2"/>
      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>
    </inertial>
  </link>
  
  <gazebo reference="left_wheel">
    <material>Gazebo/Black</material>
  </gazebo>
  
  <!-- 右轮 -->
  <link name="right_wheel">
    <visual>
      <geometry>
        <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
      </geometry>
      <origin rpy="${PI/2} 0 0"/>
      <material name="black"/>
    </visual>
    <collision>
      <geometry>
        <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
      </geometry>
      <origin rpy="${PI/2} 0 0"/>
    </collision>
    <inertial>
      <mass value="0.2"/>
      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>
    </inertial>
  </link>
  
  <gazebo reference="right_wheel">
    <material>Gazebo/Black</material>
  </gazebo>
  
  <!-- 左侧腿轮（caster） -->
  <link name="left_caster">
    <visual>
      <geometry>
        <sphere radius="0.02"/>
      </geometry>
      <material name="gray"/>
    </visual>
    <collision>
      <geometry>
        <sphere radius="0.02"/>
      </geometry>
    </collision>
  </link>
  
  <!-- 右侧腿轮（caster） -->
  <link name="right_caster">
    <visual>
      <geometry>
        <sphere radius="0.02"/>
      </geometry>
      <material name="gray"/>
    </visual>
    <collision>
      <geometry>
        <sphere radius="0.02"/>
      </geometry>
    </collision>
  </link>
  
  <!-- 关节定义 -->
  <joint name="left_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="left_wheel"/>
    <origin xyz="0 ${wheel_separation/2} 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <dynamics damping="0.05"/>
  </joint>
  
  <joint name="right_wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="right_wheel"/>
    <origin xyz="0 -${wheel_separation/2} 0" rpy="0 0 0"/>
    <axis xyz="0 1 0"/>
    <dynamics damping="0.05"/>
  </joint>
  
  <joint name="left_caster_joint" type="fixed">
    <parent link="base_link"/>
    <child link="left_caster"/>
    <origin xyz="0.1 0.1 -0.05" rpy="0 0 0"/>
  </joint>
  
  <joint name="right_caster_joint" type="fixed">
    <parent link="base_link"/>
    <child link="right_caster"/>
    <origin xyz="0.1 -0.1 -0.05" rpy="0 0 0"/>
  </joint>
  
  <!-- Gazebo差速驱动插件 -->
  <gazebo>
    <plugin filename="libgazebo_ros_diff_drive.so" name="gazebo_ros_diff_drive">
      <ros>
        <namespace>/</namespace>
        <remapping>cmd_vel:=cmd_vel</remapping>
        <remapping>odom:=odom</remapping>
      </ros>
      <update_rate>50</update_rate>
      <left_joint>left_wheel_joint</left_joint>
      <right_joint>right_wheel_joint</right_joint>
      <wheel_separation>${wheel_separation}</wheel_separation>
      <wheel_diameter>${wheel_radius*2}</wheel_diameter>
      <max_wheel_torque>10</max_wheel_torque>
      <max_wheel_acceleration>1.0</max_wheel_acceleration>
      <command_topic>cmd_vel</command_topic>
      <publish_odom>true</publish_odom>
      <publish_odom_tf>true</publish_odom_tf>
      <publish_wheel_tf>true</publish_wheel_tf>
      <odometry_topic>odom</odometry_topic>
      <odometry_frame>odom</odometry_frame>
      <robot_base_frame>base_link</robot_base_frame>
    </plugin>
  </gazebo>
  
  <!-- 关节状态发布插件 -->
  <gazebo>
    <plugin filename="libgazebo_ros_joint_state_publisher.so" name="gazebo_ros_joint_state_publisher">
      <ros>
        <namespace>/</namespace>
        <remapping>~/out:=joint_states</remapping>
      </ros>
      <update_rate>50</update_rate>
    </plugin>
  </gazebo>
  
</robot>
```

### 5.3 创建Gazebo世界文件

```xml
<!-- my_robot_description/worlds/office.world -->
<?xml version="1.0" ?>
<sdf version="1.10">
  <world name="office_world">
    
    <!-- 物理引擎 -->
    <physics type="ode">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
      <real_time_update_rate>1000</real_time_update_rate>
    </physics>
    
    <!-- 场景设置 -->
    <scene>
      <ambient>0.5 0.5 0.5 1</ambient>
      <shadows>true</shadows>
      <grid>true</grid>
    </scene>
    
    <!-- 灯光 -->
    <light type="directional" name="sun">
      <pose>0 0 10 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <cast_shadows>true</cast_shadows>
    </light>
    
    <!-- 地面 -->
    <model name="ground_plane">
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>20 20</size>
            </plane>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <plane>
              <normal>0 0 1</normal>
              <size>20 20</size>
            </plane>
          </geometry>
          <material>
            <diffuse>0.5 0.5 0.5 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
    <!-- 障碍物：桌子 -->
    <model name="table">
      <pose>2 2 0 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <box>
              <size>1 0.6 0.75</size>
            </box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box>
              <size>1 0.6 0.75</size>
            </box>
          </geometry>
          <material>
            <diffuse>0.6 0.4 0.2 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
    <!-- 障碍物：椅子 -->
    <model name="chair">
      <pose>2 2.8 0 0 0 0</pose>
      <static>true</static>
      <link name="link">
        <collision name="collision">
          <geometry>
            <box>
              <size>0.5 0.5 1</size>
            </box>
          </geometry>
        </collision>
        <visual name="visual">
          <geometry>
            <box>
              <size>0.5 0.5 1</size>
            </box>
          </geometry>
          <material>
            <diffuse>0.3 0.3 0.3 1</diffuse>
          </material>
        </visual>
      </link>
    </model>
    
  </world>
</sdf>
```

### 5.4 运行完整仿真

```bash
# 编译功能包
cd ~/ros2_ws
colcon build --packages-select my_robot_description my_robot_gazebo
source install/setup.bash

# 启动仿真
ros2 launch my_robot_gazebo simulation.launch.py

# 启动键盘控制
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## 练习题

### 选择题

1. Gazebo仿真平台的核心特性不包括以下哪项？
   - A) 高保真物理引擎
   - B) 丰富的传感器模型
   - C) 实时操作系统
   - D) 灵活的环境构建
   
   **答案：C**。Gazebo是仿真平台，不是实时操作系统，它提供物理仿真和3D环境，但不直接提供实时操作系统的功能。

2. 在ROS2中，连接Gazebo与ROS2的核心桥接包是什么？
   - A) ros_bridge
   - B) ros_gz
   - C) gazebo_ros
   - D) ros_gazebo
   
   **答案：B**。ros_gz是连接ROS2与Gazebo的核心桥接包，用于话题、服务和TF的转换。

3. SDF格式主要用于描述什么内容？
   - A) 机器人URDF模型
   - B) 仿真世界环境
   - C) ROS2话题消息
   - D) 控制器配置
   
   **答案：B**。SDF（Simulation Description Format）是Gazebo用于描述仿真世界的XML格式。

4. gazebo_ros_diff_drive插件的主要作用是什么？
   - A) 发布激光雷达数据
   - B) 实现差速驱动控制
   - C) 发布关节状态
   - D) 渲染3D可视化
   
   **答案：B**。gazebo_ros_diff_drive插件用于实现差速驱动机器人的运动控制。

5. 在Gazebo中，`<static>true</static>`标签的作用是什么？
   - A) 物体可以移动
   - B) 物体固定不动
   - C) 物体具有弹性
   - D) 物体透明
   
   **答案：B**。当`<static>true</static>`时，物体将被固定，不会受到物理力影响，常用于地面、墙壁等静态物体。

### 实践题

6. 创建一个带有IMU传感器的机器人URDF模型，并在Gazebo中添加IMU传感器插件。
   
   **参考答案**：
   
   ```xml
   <!-- IMU传感器配置 -->
   <link name="imu_link">
     <origin xyz="0 0 0.05" rpy="0 0 0"/>
   </link>
   
   <joint name="imu_joint" type="fixed">
     <parent link="base_link"/>
     <child link="imu_link"/>
     <origin xyz="0 0 0.05" rpy="0 0 0"/>
   </joint>
   
   <gazebo reference="imu_link">
     <sensor type="imu" name="imu_sensor">
       <always_on>true</always_on>
       <update_rate>100</update_rate>
       <pose>0 0 0 0 0 0</pose>
       <plugin filename="libgazebo_ros_imu.so" name="gazebo_ros_imu">
         <ros>
           <namespace>/my_robot</namespace>
           <remapping>~/out:=imu</remapping>
         </ros>
         <frame_name>imu_link</frame_name>
       </plugin>
     </sensor>
   </gazebo>
   ```

7. 修改差速驱动机器人配置，使其使用ros2_control框架而不是Gazebo原生插件。
   
   **提示**：
   - 在URDF中添加`<ros2_control>`标签
   - 创建YAML配置文件定义控制器
   - 使用controller_manager加载控制器

---

## 本章小结

本章我们系统学习了ROS2与Gazebo仿真平台的集成技术。在Gazebo概述部分，我们了解了Gazebo的核心特性、与ROS的集成历史以及界面布局。在ROS2-Gazebo集成部分，我们详细讲解了ros_gz桥接的工作原理和gazebo_ros_pkgs的功能。在仿真世界建模部分，我们学习了SDF格式的基础知识以及创建室内外环境的方法。在机器人放入仿真环境部分，我们掌握了URDF模型准备、Gazebo插件配置和launch文件编写的完整流程。

通过本节学习，你应该能够：
- 理解Gazebo仿真平台的核心概念
- 掌握ROS2与Gazebo的集成方法
- 创建自定义的仿真世界环境
- 将机器人模型加载到Gazebo中进行仿真

---

## 参考资料

### Gazebo官方文档

1. Gazebo Official Website: <https://www.gazebosim.org/>
2. Gazebo Tutorials: <https://gazebosim.org/docs>
3. SDF Format Documentation: <https://sdformat.org/>

### ROS2与Gazebo集成

4. gazebo_ros_pkgs: <https://github.com/ros-simulation/gazebo_ros_pkgs>
5. ros_gz Documentation: <https://github.com/gazebosim/ros_gz>
6. ROS2 Control with Gazebo: <https://control.ros.org/master/doc/gazebo_ros2_control/index.html>

### Gazebo模型库

7. Fuel Model Database: <https://app.gazebosim.org/models>

---

## 下节预告

下一节我们将学习**07-3 ROS2仿真-Xacro宏定义与参数化建模**，了解如何使用Xacro编写可复用的机器人模型，提高URDF的可维护性和灵活性。

---

*本章学习完成！Gazebo是机器人仿真的重要工具，熟练掌握ROS2与Gazebo的集成将为后续的SLAM、导航等高级功能开发奠定坚实基础。*