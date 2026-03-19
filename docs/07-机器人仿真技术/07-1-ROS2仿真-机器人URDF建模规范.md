# 07-1 ROS2仿真-机器人URDF建模规范

> **前置课程**：06-4 多传感器数据融合
> **后续课程**：07-2 ROS2仿真-Gazebo仿真平台与ROS2集成

**作者**：霍海杰 | **联系方式**：howe12@126.com

> **前置说明**：URDF（Unified Robot Description Format）是ROS中用于描述机器人模型的标准格式。本节将深入讲解URDF的XML语法、link与joint的概念、机器人建模的完整流程，以及如何使用xacro简化建模工作。通过本节的学习，你将掌握为任何机器人创建URDF模型的能力，为后续的仿真和实际部署打下基础。

---

## 1. URDF概述

URDF（Unified Robot Description Format，统一机器人描述格式）是一种基于XML的机器人描述文件格式。它能够完整地描述机器人的物理结构，包括连杆（link）的形状、尺寸、颜色、惯性参数，以及关节（joint）的类型、位置、轴向等。URDF不仅是机器人可视化的基础，也是运动学仿真、碰撞检测、导航规划等功能的底层依赖。

### 1.1 URDF的核心作用

URDF在ROS机器人开发中扮演着至关重要的角色。首先，它是**机器人可视化**的基础：RViz等工具通过解析URDF文件来渲染机器人的三维模型，让我们能够在虚拟环境中直观地看到机器人的结构。其次，URDF是**仿真引擎**的输入：Gazebo等仿真软件需要准确的URDF模型来模拟机器人的物理行为，包括重力、碰撞、摩擦等。再次，URDF定义了**坐标系变换**：通过joint和link的层级关系，ROS能够维护完整的坐标系树（TF树），这是定位、导航等功能的基石。最后，URDF是**运动学建模**的基础：机械臂的逆运动求解、路径规划等都需要准确的连杆参数。

### 1.2 URDF文件结构

一个完整的URDF文件通常包含以下主要部分：`robot`根元素是整个文件的容器；`link`元素用于描述机器人的各个刚体部分（如基座、连杆、末端执行器等）；`joint`元素用于描述link之间的连接关系（如旋转关节、移动关节等）；`material`元素用于定义视觉属性（如颜色、纹理等）；`transmission`元素用于描述驱动配置（将joint与 actuator 关联）；`gazebo`元素用于包含Gazebo仿真特定的参数。

```xml
<?xml version="1.0"?>
<robot name="my_robot">
    
    <!-- 全局material定义 -->
    <material name="blue">
        <color rgba="0.0 0.0 0.8 1.0"/>
    </material>
    
    <!-- Link定义 -->
    <link name="base_link">
        <visual>
            <geometry>
                <cylinder length="0.1" radius="0.2"/>
            </geometry>
            <material name="blue"/>
        </visual>
        <collision>
            <geometry>
                <cylinder length="0.1" radius="0.2"/>
            </geometry>
        </collision>
        <inertial>
            <mass value="1.0"/>
            <inertia ixx="0.001" ixy="0.0" ixz="0.0"
                     iyy="0.001" iyz="0.0" izz="0.001"/>
        </inertial>
    </link>
    
    <!-- Joint定义 -->
    <joint name="base_to_wheel" type="continuous">
        <parent link="base_link"/>
        <child link="wheel_link"/>
        <origin xyz="0.1 0.0 0.0" rpy="0 1.57 0"/>
        <axis xyz="0 0 1"/>
    </joint>
    
    <!-- 传动系统定义 -->
    <transmission name="wheel_trans">
        <type>transmission_interface/SimpleTransmission</type>
        <joint name="base_to_wheel">
            <hardwareInterface>EffortJointInterface</hardwareInterface>
        </joint>
        <actuator name="wheel_motor">
            <hardwareInterface>EffortJointInterface</hardwareInterface>
            <mechanicalReduction>1</mechanicalReduction>
        </actuator>
    </transmission>
    
    <!-- Gazebo仿真配置 -->
    <gazebo reference="base_link">
        <material>Gazebo/Blue</material>
        <turnGravityOff>false</turnGravityOff>
    </gazebo>
    
</robot>
```

### 1.3 URDF建模流程

机器人URDF建模通常遵循以下流程：首先是**需求分析**，明确机器人的自由度数量、关节类型、传感器配置等；然后是**连杆设计**，确定每个link的形状、尺寸、惯性参数；接着是**关节配置**，定义joint的位置、类型、运动轴和限制；再是**可视化完善**，添加颜色、网格等视觉元素；之后是**物理参数**，填写collision和inertial标签；最后是**仿真适配**，添加Gazebo特有的配置。

在实际项目中，建议将URDF文件组织为以下结构：主URDF文件（`robot.urdf`）包含robot根元素和核心定义；xacro文件（`robot.xacro`）使用宏定义简化模型；配置文件（`robot.gazebo`）包含Gazebo仿真参数；launch文件（`display.launch`）用于启动RViz查看模型。

---

## 2. Link定义

Link是URDF中描述机器人刚体部分的基本元素。每个link可以包含三种类型的子元素：`visual`（视觉外观，用于RViz显示）、`collision`（碰撞几何，用于物理仿真和避障）、`inertial`（惯性参数，用于动力学计算）。

### 2.1 Visual（视觉外观）

visual元素定义了机器人在RViz等可视化工具中的外观。它包含几何形状和材质两部分。

```xml
<link name="base_link">
    <visual>
        <!-- 几何形状：支持box、cylinder、sphere、mesh -->
        <geometry>
            <cylinder length="0.05" radius="0.1"/>
        </geometry>
        
        <!-- 材质定义 -->
        <material name="white">
            <color rgba="1.0 1.0 1.0 1.0"/>
        </material>
        
        <!-- 视觉原点（可选） -->
        <origin xyz="0 0 0" rpy="0 0 0"/>
    </visual>
</link>
```

常用的几何形状有四种：**box（长方体）**使用三个尺寸参数（xyz）；**cylinder（圆柱体）**使用长度和半径参数；**sphere（球体）**使用半径参数；**mesh（网格）**使用外部STL或DAE文件，支持复杂的机器人模型。

```xml
<!-- 各种几何形状示例 -->
<geometry>
    <box size="0.1 0.1 0.05"/>  <!-- 长方体：长x宽x高 -->
</geometry>

<geometry>
    <cylinder length="0.1" radius="0.05"/>  <!-- 圆柱体：高度、半径 -->
</geometry>

<geometry>
    <sphere radius="0.05"/>  <!-- 球体：半径 -->
</geometry>

<geometry>
    <!-- 导入外部网格模型 -->
    <mesh filename="package://robot_description/meshes/base.stl" scale="0.001 0.001 0.001"/>
</geometry>
```

**颜色定义**使用RGBA四个分量，每个分量取值范围为0.0到1.0。例如，`<color rgba="1.0 0.0 0.0 1.0"/>`表示红色，完全不透明。

### 2.2 Collision（碰撞几何）

collision元素定义了用于碰撞检测的几何形状。为了提高计算效率，碰撞几何通常使用比视觉几何更简单的形状。

```xml
<link name="base_link">
    <collision>
        <!-- 碰撞几何通常使用简单形状以提高效率 -->
        <geometry>
            <cylinder length="0.05" radius="0.1"/>
        </geometry>
        <origin xyz="0 0 0" rpy="0 0 0"/>
    </collision>
</link>
```

### 2.3 Inertial（惯性参数）

inertial元素定义了link的质量和惯性张量。这些参数对于物理仿真和运动规划至关重要。

```xml
<link name="base_link">
    <inertial>
        <!-- 质量（单位：kg） -->
        <mass value="1.5"/>
        
        <!-- 惯性张量（单位：kg·m²） -->
        <inertia 
            ixx="0.001" ixy="0.0" ixz="0.0"
            iyy="0.001" iyz="0.0"
            izz="0.001"/>
            
        <!-- 惯性参考系的原点 -->
        <origin xyz="0 0 0"/>
    </inertial>
</link>
```

对于简单几何形状，可以手动计算惯性参数。例如，质量为$m$、半径为$r$、高度为$h$的圆柱体，其主惯性矩计算公式为：

$$I_{xx} = I_{yy} = \frac{1}{12}m(3r^2 + h^2)$$

$$I_{zz} = \frac{1}{2}mr^2$$

---

## 3. Joint定义

Joint定义了机器人各link之间的连接关系和运动方式。URDF支持多种关节类型，每种类型都有不同的运动特性和参数要求。

### 3.1 Joint类型

URDF定义了六种基本的joint类型：

| 类型 | 描述 | 自由度 | 适用场景 |
|------|------|--------|----------|
| `revolute` | 旋转关节 | 1 | 有角度限制的旋转（机械臂关节） |
| `continuous` | 连续旋转关节 | 1 | 无角度限制的旋转（轮子） |
| `prismatic` | 移动关节 | 1 | 直线运动（滑轨、活塞） |
| `fixed` | 固定关节 | 0 | 刚性连接（不可运动） |
| `floating` | 浮动关节 | 6 | 完整6DOF运动 |
| `planar` | 平面关节 | 3 | 平面内运动 |

**旋转关节（revolute）**：绕固定轴旋转，有角度限制。

```xml
<joint name="arm_joint" type="revolute">
    <parent link="base_link"/>
    <child link="arm_link_1"/>
    <origin xyz="0 0 0.1" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
    <limit lower="-3.14" upper="3.14" effort="10.0" velocity="2.0"/>
    <dynamics damping="0.7" friction="0.5"/>
</joint>
```

**连续旋转关节（continuous）**：无限制旋转，适用于轮子等持续旋转的部件。

```xml
<joint name="wheel_joint" type="continuous">
    <parent link="base_link"/>
    <child link="wheel_link"/>
    <origin xyz="0.1 0.0 -0.05" rpy="0 1.57 0"/>
    <axis xyz="0 0 1"/>
    <dynamics damping="0.2" friction="0.1"/>
</joint>
```

**移动关节（prismatic）**：沿直线运动。

```xml
<joint name="slider_joint" type="prismatic">
    <parent link="base_link"/>
    <child link="slider_link"/>
    <origin xyz="0 0 0"/>
    <axis xyz="1 0 0"/>
    <limit lower="0.0" upper="0.5" effort="100.0" velocity="0.5"/>
</joint>
```

**固定关节（fixed）**：刚性连接，不可运动。

```xml
<joint name="sensor_mount" type="fixed">
    <parent link="base_link"/>
    <child link="camera_link"/>
    <origin xyz="0.1 0.0 0.2" rpy="0 0 0"/>
</joint>
```

### 3.2 Joint参数详解

每个joint包含以下关键参数：

- **parent link**：父连杆，关节连接的主体
- **child link**：子连杆，关节连接的从属部分
- **origin**：变换矩阵，定义child相对于parent的位置和姿态
- **axis**：旋转轴（revolute/continuous）或运动方向（prismatic）
- **limit**：运动限制，包括lower、upper、effort、velocity
- **dynamics**：动力学参数，包括damping（阻尼）和friction（摩擦力）

**origin参数的数学含义**：origin定义了从parent坐标系到child坐标系的变换。它包含两个部分：xyz（位置偏移，单位：米）和rpy（欧拉角旋转，单位：弧度）。

**axis参数的数学含义**：axis定义了旋转或移动的方向，使用单位向量表示。

```xml
<!-- 各种axis示例 -->
<axis xyz="0 0 1"/>   <!-- 绕/沿Z轴 -->
<axis xyz="1 0 0"/>   <!-- 绕/沿X轴 -->
<axis xyz="0 1 0"/>   <!-- 绕/沿Y轴 -->
```

---

## 4. 机器人建模实战：差速轮式机器人

本节我们将通过一个完整的差速轮式机器人建模示例，来实践URDF的各个方面。该机器人包含一个方形底座、两个驱动轮和一个万向轮。

### 4.1 机器人结构分析

差速轮式机器人是最常见的移动机器人类型之一。其结构特点是：两个驱动轮分布在机器人底座两侧，通过差速实现转向；一个或多个万向轮用于支撑和平衡。

### 4.2 创建URDF文件

首先创建功能包和URDF文件：

```bash
mkdir -p ~/ros2_ws/src/my_robot_description/urdf
mkdir -p ~/ros2_ws/src/my_robot_description/meshes
mkdir -p ~/ros2_ws/src/my_robot_description/launch
```

```xml
<!-- ~/ros2_ws/src/my_robot_description/urdf/diff_robot.urdf -->
<?xml version="1.0"?>
<robot name="diff_robot">
    
    <!-- 全局材质定义 -->
    <material name="blue">
        <color rgba="0.0 0.0 0.8 1.0"/>
    </material>
    <material name="black">
        <color rgba="0.1 0.1 0.1 1.0"/>
    </material>
    <material name="white">
        <color rgba="0.9 0.9 0.9 1.0"/>
    </material>
    
    <!-- ==================== base_link (机器人底座) ==================== -->
    <link name="base_link">
        <visual>
            <geometry>
                <box size="0.4 0.2 0.1"/>
            </geometry>
            <material name="blue"/>
        </visual>
        <collision>
            <geometry>
                <box size="0.4 0.2 0.1"/>
            </geometry>
        </collision>
        <inertial>
            <mass value="2.0"/>
            <inertia ixx="0.01" ixy="0.0" ixz="0.0"
                     iyy="0.02" iyz="0.0" izz="0.02"/>
        </inertial>
    </link>
    
    <!-- ==================== 左轮 ==================== -->
    <link name="left_wheel">
        <visual>
            <geometry>
                <cylinder length="0.04" radius="0.08"/>
            </geometry>
            <material name="black"/>
            <origin rpy="1.57 0 0"/>
        </visual>
        <collision>
            <geometry>
                <cylinder length="0.04" radius="0.08"/>
            </geometry>
            <origin rpy="1.57 0 0"/>
        </collision>
        <inertial>
            <mass value="0.5"/>
            <inertia ixx="0.0002" ixy="0.0" ixz="0.0"
                     iyy="0.0002" iyz="0.0" izz="0.0003"/>
        </inertial>
    </link>
    
    <!-- ==================== 右轮 ==================== -->
    <link name="right_wheel">
        <visual>
            <geometry>
                <cylinder length="0.04" radius="0.08"/>
            </geometry>
            <material name="black"/>
            <origin rpy="1.57 0 0"/>
        </visual>
        <collision>
            <geometry>
                <cylinder length="0.04" radius="0.08"/>
            </geometry>
            <origin rpy="1.57 0 0"/>
        </collision>
        <inertial>
            <mass value="0.5"/>
            <inertia ixx="0.0002" ixy="0.0" ixz="0.0"
                     iyy="0.0002" iyz="0.0" izz="0.0003"/>
        </inertial>
    </link>
    
    <!-- ==================== 万向轮（caster） ==================== -->
    <link name="caster_wheel">
        <visual>
            <geometry>
                <sphere radius="0.02"/>
            </geometry>
            <material name="white"/>
        </visual>
        <collision>
            <geometry>
                <sphere radius="0.02"/>
            </geometry>
        </collision>
        <inertial>
            <mass value="0.1"/>
            <inertia ixx="0.00001" ixy="0.0" ixz="0.0"
                     iyy="0.00001" iyz="0.0" izz="0.00001"/>
        </inertial>
    </link>
    
    <!-- ==================== 左轮关节 ==================== -->
    <joint name="left_wheel_joint" type="continuous">
        <parent link="base_link"/>
        <child link="left_wheel"/>
        <origin xyz="-0.05 0.12 -0.05" rpy="0 0 0"/>
        <axis xyz="0 1 0"/>
        <dynamics damping="0.2" friction="0.1"/>
    </joint>
    
    <!-- ==================== 右轮关节 ==================== -->
    <joint name="right_wheel_joint" type="continuous">
        <parent link="base_link"/>
        <child link="right_wheel"/>
        <origin xyz="-0.05 -0.12 -0.05" rpy="0 0 0"/>
        <axis xyz="0 1 0"/>
        <dynamics damping="0.2" friction="0.1"/>
    </joint>
    
    <!-- ==================== 万向轮关节 ==================== -->
    <joint name="caster_joint" type="fixed">
        <parent link="base_link"/>
        <child link="caster_wheel"/>
        <origin xyz="0.15 0.0 -0.05" rpy="0 0 0"/>
    </joint>
    
</robot>
```

### 4.3 在RViz中查看模型

创建launch文件来启动RViz并显示机器人模型：

```xml
<!-- ~/ros2_ws/src/my_robot_description/launch/display.launch -->
<launch>
    <arg name="model" default="$(find my_robot_description)/urdf/diff_robot.urdf"/>
    <arg name="gui" default="true"/>
    
    <param name="robot_description" command="cat $(arg model)"/>
    
    <group if="$(arg gui)">
        <node name="joint_state_publisher_gui" 
              pkg="joint_state_publisher_gui" 
              type="joint_state_publisher_gui"/>
    </group>
    
    <node name="robot_state_publisher" 
          pkg="robot_state_publisher" 
          type="robot_state_publisher"/>
    
    <node name="rviz" 
          pkg="rviz2" 
          type="rviz2" 
          required="true"/>
</launch>
```

### 4.4 运行查看

```bash
# 编译功能包
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select my_robot_description
source install/setup.bash

# 启动RViz查看模型
ros2 launch my_robot_description display.launch
```

在RViz中，左侧"Displays"面板的"Global Options"中设置"Fixed Frame"为"base_link"，然后添加"RobotModel"显示项，即可看到机器人模型。

---

## 5. Xacro简化建模

随着机器人模型变得越来越复杂，URDF文件会变得冗长难以维护。Xacro（XML Macro）是URDF的扩展，提供了宏定义、变量、条件包含等功能，可以大幅简化机器人建模工作。

### 5.1 Xacro基本语法

Xacro文件使用`.xacro`扩展名，需要在URDF基础上添加xacro命名空间声明：

```xml
<robot name="my_robot" xmlns:xacro="http://ros.org/wiki/xacro">
    <!-- Xacro内容 -->
</robot>
```

**变量定义与使用**：使用xacro:property定义变量：

```xml
<!-- 定义变量 -->
<xacro:property name="wheel_radius" value="0.08"/>
<xacro:property name="base_length" value="0.4"/>
<xacro:property name="base_width" value="0.2"/>
<xacro:property name="PI" value="3.14159"/>

<!-- 使用变量 -->
<geometry>
    <box size="${base_length} ${base_width} 0.1"/>
</geometry>
```

**数学表达式**：Xacro支持基本的数学运算：

```xml
<!-- 支持的运算符：+ - * / -->
<origin xyz="${wheel_radius * 2} 0 0"/>
<cylinder radius="${wheel_radius}" length="${base_width/5}"/>
```

### 5.2 宏定义（Macro）

Xacro允许定义可重用的代码块（宏）：

```xml
<!-- 定义轮子宏 -->
<xacro:macro name="wheel" params="name prefix *origin">
    <link name="${name}_${prefix}_wheel">
        <visual>
            <geometry>
                <cylinder length="0.04" radius="0.08"/>
            </geometry>
            <material name="black"/>
            <origin rpy="1.57 0 0"/>
        </visual>
        <collision>
            <geometry>
                <cylinder length="0.04" radius="0.08"/>
            </geometry>
            <origin rpy="1.57 0 0"/>
        </collision>
        <inertial>
            <mass value="0.5"/>
            <inertia ixx="0.0002" ixy="0.0" ixz="0.0"
                     iyy="0.0002" iyz="0.0" izz="0.0003"/>
        </inertial>
    </link>
    
    <joint name="${name}_${prefix}_wheel_joint" type="continuous">
        <parent link="${name}_base_link"/>
        <child link="${name}_${prefix}_wheel"/>
        <xacro:insert_block name="origin"/>
        <axis xyz="0 1 0"/>
    </joint>
</xacro:macro>

<!-- 调用宏 -->
<xacro:wheel name="diff" prefix="left">
    <origin xyz="-0.05 0.12 -0.05" rpy="0 0 0"/>
</xacro:wheel>

<xacro:wheel name="diff" prefix="right">
    <origin xyz="-0.05 -0.12 -0.05" rpy="0 0 0"/>
</xacro:wheel>
```

### 5.3 使用Xacro重构机器人模型

使用Xacro重构后的差速机器人模型：

```xml
<!-- ~/ros2_ws/src/my_robot_description/urdf/diff_robot.xacro -->
<?xml version="1.0"?>
<robot name="diff_robot" xmlns:xacro="http://ros.org/wiki/xacro">
    
    <!-- ==================== 常量定义 ==================== -->
    <xacro:property name="PI" value="3.14159"/>
    
    <!-- 底座参数 -->
    <xacro:property name="base_length" value="0.4"/>
    <xacro:property name="base_width" value="0.2"/>
    <xacro:property name="base_height" value="0.1"/>
    <xacro:property name="base_mass" value="2.0"/>
    
    <!-- 轮子参数 -->
    <xacro:property name="wheel_radius" value="0.08"/>
    <xacro:property name="wheel_width" value="0.04"/>
    <xacro:property name="wheel_mass" value="0.5"/>
    <xacro:property name="wheel_offset_x" value="-0.05"/>
    <xacro:property name="wheel_offset_y" value="0.12"/>
    <xacro:property name="wheel_offset_z" value="-0.05"/>
    
    <!-- 万向轮参数 -->
    <xacro:property name="caster_radius" value="0.02"/>
    <xacro:property name="caster_mass" value="0.1"/>
    <xacro:property name="caster_offset_x" value="0.15"/>
    <xacro:property name="caster_offset_z" value="-0.05"/>
    
    <!-- ==================== 材质定义 ==================== -->
    <material name="blue">
        <color rgba="0.0 0.0 0.8 1.0"/>
    </material>
    <material name="black">
        <color rgba="0.1 0.1 0.1 1.0"/>
    </material>
    <material name="white">
        <color rgba="0.9 0.9 0.9 1.0"/>
    </material>
    
    <!-- ==================== 轮子宏 ==================== -->
    <xacro:macro name="wheel" params="prefix">
        <link name="${prefix}_wheel">
            <visual>
                <geometry>
                    <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
                </geometry>
                <material name="black"/>
                <origin rpy="${PI/2} 0 0"/>
            </visual>
            <collision>
                <geometry>
                    <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
                </geometry>
                <origin rpy="${PI/2} 0 0"/>
            </collision>
            <inertial>
                <mass value="${wheel_mass}"/>
                <inertia ixx="${wheel_mass * wheel_radius * wheel_radius / 2}" 
                         ixy="0" ixz="0"
                         iyy="${wheel_mass * wheel_radius * wheel_radius / 2}" 
                         iyz="0"
                         izz="${wheel_mass * wheel_radius * wheel_radius}"/>
            </inertial>
        </link>
        
        <joint name="${prefix}_wheel_joint" type="continuous">
            <parent link="base_link"/>
            <child link="${prefix}_wheel"/>
            <origin xyz="${wheel_offset_x} ${wheel_offset_y * (1 if prefix == 'left' else -1)} ${wheel_offset_z}" 
                    rpy="0 0 0"/>
            <axis xyz="0 1 0"/>
            <dynamics damping="0.2" friction="0.1"/>
        </joint>
    </xacro:macro>
    
    <!-- ==================== 万向轮宏 ==================== -->
    <xacro:macro name="caster" params="prefix">
        <link name="${prefix}_wheel">
            <visual>
                <geometry>
                    <sphere radius="${caster_radius}"/>
                </geometry>
                <material name="white"/>
            </visual>
            <collision>
                <geometry>
                    <sphere radius="${caster_radius}"/>
                </geometry>
            </collision>
            <inertial>
                <mass value="${caster_mass}"/>
                <inertia ixx="${2/5 * caster_mass * caster_radius * caster_radius}" 
                         ixy="0" ixz="0"
                         iyy="${2/5 * caster_mass * caster_radius * caster_radius}" 
                         iyz="0"
                         izz="${2/5 * caster_mass * caster_radius * caster_radius}"/>
            </inertial>
        </link>
        
        <joint name="${prefix}_wheel_joint" type="fixed">
            <parent link="base_link"/>
            <child link="${prefix}_wheel"/>
            <origin xyz="${caster_offset_x} 0 ${caster_offset_z}" rpy="0 0 0"/>
        </joint>
    </xacro:macro>
    
    <!-- ==================== 底座Link ==================== -->
    <link name="base_link">
        <visual>
            <geometry>
                <box size="${base_length} ${base_width} ${base_height}"/>
            </geometry>
            <material name="blue"/>
        </visual>
        <collision>
            <geometry>
                <box size="${base_length} ${base_width} ${base_height}"/>
            </geometry>
        </collision>
        <inertial>
            <mass value="${base_mass}"/>
            <inertia ixx="${base_mass * (base_width * base_width + base_height * base_height) / 12}" 
                     ixy="0" ixz="0"
                     iyy="${base_mass * (base_length * base_length + base_height * base_height) / 12}" 
                     iyz="0"
                     izz="${base_mass * (base_length * base_length + base_width * base_width) / 12}"/>
        </inertial>
    </link>
    
    <!-- ==================== 调用宏 ==================== -->
    <xacro:wheel prefix="left"/>
    <xacro:wheel prefix="right"/>
    <xacro:caster prefix="caster"/>
    
</robot>
```

### 5.4 Xacro转换为URDF

使用xacro命令将xacro文件转换为URDF：

```bash
# 查看生成的URDF
xacro /path/to/robot.xacro

# 保存为URDF文件
xacro /path/to/robot.xacro > /path/to/robot.urdf

# 在launch文件中直接使用xacro
<param name="robot_description" command="xacro $(find my_robot_description)/urdf/diff_robot.xacro"/>
```

修改后的launch文件：

```xml
<launch>
    <arg name="model" default="$(find my_robot_description)/urdf/diff_robot.xacro"/>
    <arg name="gui" default="true"/>
    
    <!-- 使用xacro解析器 -->
    <param name="robot_description" 
           command="xacro $(arg model)"/>
    
    <group if="$(arg gui)">
        <node name="joint_state_publisher_gui" 
              pkg="joint_state_publisher_gui" 
              type="joint_state_publisher_gui"/>
    </group>
    
    <node name="robot_state_publisher" 
          pkg="robot_state_publisher" 
          type="robot_state_publisher"/>
    
    <node name="rviz" 
          pkg="rviz2" 
          type="rviz2" 
          required="true"/>
</launch>
```

---

## 练习题

### 选择题

1. URDF中用于描述机器人刚体部分的基本元素是什么？
   - A) joint
   - B) link
   - C) robot
   - D) material
   
   **答案：B**。Link是URDF中描述机器人刚体部分的基本元素，包括visual、collision和inertial三个子元素。

2. 下列哪个joint类型适用于驱动轮？
   - A) revolute
   - B) continuous
   - C) prismatic
   - D) fixed
   
   **答案：B**。连续旋转关节（continuous）适用于需要无限旋转的部件，如驱动轮。

3. Xacro文件中用于定义变量的标签是：
   - A) xacro:macro
   - B) xacro:property
   - C) xacro:variable
   - D) xacro:define
   
   **答案：B**。使用xacro:property标签定义变量，使用${variable_name}语法引用变量。

### 实践题

4. 创建一个两轮差速机器人模型，包含底座和两个轮子，使用xacro实现参数化。
   
   **参考答案**：
   
   ```xml
   <?xml version="1.0"?>
   <robot name="two_wheel_robot" xmlns:xacro="http://ros.org/wiki/xacro">
       <xacro:property name="PI" value="3.14159"/>
       <xacro:property name="base_size" value="0.3"/>
       <xacro:property name="wheel_radius" value="0.05"/>
       
       <material name="red"><color rgba="0.8 0.2 0.2 1.0"/></material>
       
       <!-- 底座 -->
       <link name="base_link">
           <visual>
               <geometry><box size="${base_size} ${base_size} 0.05"/></geometry>
               <material name="red"/>
           </visual>
           <collision>
               <geometry><box size="${base_size} ${base_size} 0.05"/></geometry>
           </collision>
           <inertial>
               <mass value="1.0"/>
               <inertia ixx="0.001" ixy="0" ixz="0" iyy="0.001" iyz="0" izz="0.001"/>
           </inertial>
       </link>
       
       <!-- 轮子宏 -->
       <xacro:macro name="wheel" params="prefix y_offset">
           <link name="${prefix}_wheel">
               <visual>
                   <geometry><cylinder length="0.02" radius="${wheel_radius}"/></geometry>
                   <material name="black"><color rgba="0.1 0.1 0.1 1.0"/></material>
                   <origin rpy="${PI/2} 0 0"/>
               </visual>
               <collision>
                   <geometry><cylinder length="0.02" radius="${wheel_radius}"/></geometry>
                   <origin rpy="${PI/2} 0 0"/>
               </collision>
               <inertial>
                   <mass value="0.2"/>
                   <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>
               </inertial>
           </link>
           <joint name="${prefix}_wheel_joint" type="continuous">
               <parent link="base_link"/>
               <child link="${prefix}_wheel"/>
               <origin xyz="0 ${y_offset} -0.025" rpy="0 0 0"/>
               <axis xyz="0 1 0"/>
           </joint>
       </xacro:macro>
       
       <!-- 调用轮子 -->
       <xacro:wheel prefix="left" y_offset="0.15"/>
       <xacro:wheel prefix="right" y_offset="-0.15"/>
   </robot>
   ```

5. 为差速机器人添加一个激光雷达传感器（固定安装在底座前端）。
   
   **提示**：
   - 创建一个新的link表示激光雷达
   - 使用fixed类型的joint将激光雷达连接到base_link
   - 参考origin参数设置安装位置

---

## 本章小结

本章我们全面学习了ROS2中URDF机器人建模规范。我们了解了URDF的核心作用和文件结构，掌握了link元素的三种子元素（visual、collision、inertial）的用法，以及joint元素的六种类型（revolute、continuous、prismatic、fixed、floating、planar）。通过差速轮式机器人的实战案例，我们将理论知识应用于实践，创建了一个完整的机器人模型。最后，我们学习了如何使用xacro简化URDF建模，通过变量和宏实现参数化和代码复用。

掌握URDF建模是进行机器人仿真的基础，为后续学习Gazebo仿真、导航和运动规划等高级内容打下坚实基础。

---

## 参考资料

### URDF官方文档

1. URDF Documentation: <https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/URDF-XML.html>
2. URDF in ROS2: <https://docs.ros.org/en/humble/Concepts/About-URDF.html>

### Xacro文档

3. Using Xacro: <https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Using-Xacro.html>

### 工具和验证

4. check_urdf工具: <https://github.com/ros/urdfdom/tree/master/urdf_parser>
5. urdf_viewer: <https://github.com/ros/urdf_parser_py>

---

## 下节预告

下一节我们将学习**07-2 ROS2仿真-Gazebo仿真平台与ROS2集成**，了解如何在Gazebo中进行机器人仿真，包括仿真环境搭建、机器人模型导入、传感器仿真等内容。

---

*本章学习完成！URDF建模是机器人仿真的基石，建议大家多加练习，熟练掌握link和joint的用法，为后续的仿真学习打下基础。*
