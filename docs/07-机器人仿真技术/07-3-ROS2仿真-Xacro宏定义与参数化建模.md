# 07-3 ROS2仿真-Xacro宏定义与参数化建模

> **前置课程**：07-2 URDF机器人建模
> **后续课程**：07-4 Gazebo仿真环境搭建

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在ROS2机器人仿真中，Xacro是一个强大的URDF预处理工具。它允许我们使用变量、宏和条件语句来创建可配置、可复用的机器人模型。本节将深入讲解Xacro的核心概念，通过实战案例帮助你掌握参数化建模的技巧，从而能够创建更加灵活和专业的机器人模型。

---

## 1. Xacro概述

Xacro（XML Macro）是ROS2中用于处理URDF文件的宏语言工具。它在URDF的基础上添加了变量定义、宏定义、条件渲染等高级特性，大大简化了复杂机器人模型的创建和维护工作。

### 1.1 什么是Xacro

Xacro是一种XML宏语言，它允许我们在URDF文件中使用编程式的语法来定义机器人模型。原始的URDF文件是静态的，每一次修改都需要手动编辑XML结构。而Xacro文件（通常使用`.xacro`作为后缀）可以包含变量、表达式和宏，使得模型更加灵活和可配置。

```xml
<!-- 原始URDF：每次修改尺寸都需要手动替换 -->
<link name="base_link">
  <visual>
    <geometry>
      <box size="0.5 0.3 0.1"/>
    </geometry>
  </visual>
</link>

<!-- Xacro：使用变量定义，随时可修改 -->
<xacro:property name="base_width" value="0.3"/>
<xacro:property name="base_length" value="0.5"/>
<xacro:property name="base_height" value="0.1"/>

<link name="base_link">
  <visual>
    <geometry>
      <box size="${base_length} ${base_width} ${base_height}"/>
    </geometry>
  </visual>
</link>
```

Xacro的核心价值在于**参数化**和**模块化**。通过参数化，我们可以轻松调整机器人的尺寸、关节位置等参数；通过模块化，我们可以将常用的机器人组件封装成可复用的宏定义。

### 1.2 工作原理

Xacro的工作流程包括三个主要步骤：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  robot.xacro │ ──▶ │  xacro工具  │ ──▶ │ robot.urdf  │ ──▶ │  Gazebo/RViz │
│  (源文件)    │     │  (预处理)    │     │  (生成文件) │     │   (渲染)     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**第一步**：编写Xacro文件，定义变量、宏和条件逻辑

**第二步**：使用`xacro`命令将Xacro文件转换为标准URDF

**第三步**：将生成的URDF文件加载到RViz或Gazebo中进行可视化

```bash
# 基本转换命令
xacro model.xacro > model.urdf

# 指定输出文件
xacro -o output.urdf input.xacro

# 在ROS2中直接使用xacro文件
ros2 launch robot_bringup robot.launch.py
```

### 1.3 Xacro与URDF的关系

Xacro并不是URDF的替代品，而是URDF的扩展和补充。理解这一点非常重要：

| 特性 | URDF | Xacro |
|------|------|-------|
| 文件格式 | 纯XML | XML + 宏语法 |
| 变量支持 | ❌ 不支持 | ✅ 支持 |
| 宏支持 | ❌ 不支持 | ✅ 支持 |
| 条件渲染 | ❌ 不支持 | ✅ 支持 |
| 文件包含 | ❌ 不支持 | ✅ 支持 |
| RViz直接加载 | ✅ 支持 | ❌ 需要转换 |
| Gazebo直接加载 | ✅ 支持 | ❌ 需要转换 |

Xacro文件不能被RViz或Gazebo直接识别，必须先转换为标准的URDF文件。在ROS2中，通常在launch文件中自动完成这个转换过程。

---

## 2. 变量与参数定义

变量是Xacro最基础的功能，它允许我们定义可重用的数值，使模型参数的修改变得简单高效。

### 2.1 属性定义

使用`<xacro:property>`标签定义属性（变量）。属性具有命名空间，可以在整个Xacro文件中使用：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 定义属性 -->
  <xacro:property name="wheel_radius" value="0.05"/>
  <xacro:property name="wheel_width" value="0.02"/>
  <xacro:property name="base_length" value="0.4"/>
  <xacro:property name="base_width" value="0.3"/>
  <xacro:property name="base_height" value="0.05"/>
  
  <!-- 使用属性 -->
  <link name="base_link">
    <visual>
      <geometry>
        <box size="${base_length} ${base_width} ${base_height}"/>
      </geometry>
    </visual>
  </link>
  
</robot>
```

### 2.2 数学表达式

Xacro支持在`${}`语法中使用Python风格的数学表达式：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <xacro:property name="pi" value="3.14159"/>
  <xacro:property name="radius" value="0.1"/>
  
  <!-- 简单计算 -->
  <xacro:property name="circumference" value="${2 * pi * radius}"/>
  
  <!-- 复杂表达式 -->
  <xacro:property name="wheel_diameter" value="${radius * 2}"/>
  <xacro:property name="half_width" value="${wheel_width / 2}"/>
  
  <!-- 使用数学函数 -->
  <xacro:property name="sin_30" value="${math.sin(math.radians(30))}"/>
  <xacro:property name="cos_60" value="${math.cos(math.radians(60))}"/>
  
  <!-- 在XML中使用表达式 -->
  <link name="wheel">
    <visual>
      <geometry>
        <cylinder length="${wheel_width}" radius="${radius}"/>
      </geometry>
      <origin rpy="${pi/2} 0 0"/>
    </visual>
  </link>
  
</robot>
```

### 2.3 全局与局部属性

属性可以在不同作用域中定义，产生不同的效果：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 全局属性：整个文件可见 -->
  <xacro:property name="robot_name" value="my_robot"/>
  <xacro:property name="material_color" value="blue"/>
  
  <!-- 定义轮子宏 -->
  <xacro:macro name="wheel_link" params="prefix">
    <!-- 局部属性：仅在此宏内可见 -->
    <xacro:property name="wheel_radius" value="0.05"/>
    <xacro:property name="wheel_width" value="0.03"/>
    
    <link name="${prefix}_wheel">
      <visual>
        <geometry>
          <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
        </geometry>
        <material name="${material_color}"/>  <!-- 引用全局属性 -->
      </visual>
    </link>
  </xacro:macro>
  
  <!-- 调用宏 -->
  <xacro:wheel_link prefix="front_left"/>
  <xacro:wheel_link prefix="front_right"/>
  
</robot>
```

### 2.4 属性默认值

使用`${variable:-default}`语法为属性指定默认值，这在参数未定义时非常有用：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 如果未定义pi，使用默认值 -->
  <xacro:property name="pi" value="${3.14159}"/>
  
  <!-- 定义带默认值的安全参数 -->
  <xacro:property name="laser_offset" value="${laser_offset:-0.1}"/>
  <xacro:property name="camera_fov" value="${camera_fov:-1.047}"/>  <!-- 默认60度 -->
  
</robot>
```

---

## 3. 宏定义（Macro）

宏是Xacro最强大的功能之一，它允许我们定义可复用的XML代码块，大幅减少重复代码。

### 3.1 基本宏定义

使用`<xacro:macro>`标签定义宏，使用`<xacro:macro_name>`调用宏：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 定义轮子宏 -->
  <xacro:macro name="wheel" params="name radius width *origin">
    <link name="${name}">
      <visual>
        <geometry>
          <cylinder length="${width}" radius="${radius}"/>
        </geometry>
        <material name="gray">
          <color rgba="0.5 0.5 0.5 1.0"/>
        </material>
      </visual>
      <collision>
        <geometry>
          <cylinder length="${width}" radius="${radius}"/>
        </geometry>
      </collision>
    </link>
    
    <!-- 使用xacro:insert_block插入内容 -->
    <joint name="${name}_joint" type="continuous">
      <parent link="base_link"/>
      <child link="${name}"/>
      <xacro:insert_block name="origin"/>
      <axis xyz="0 1 0"/>
    </joint>
  </xacro:macro>
  
  <!-- 调用宏 -->
  <xacro:wheel name="front_left_wheel" radius="0.05" width="0.03">
    <origin xyz="${0.2} ${0.15} 0" rpy="0 0 0"/>
  </xacro:wheel>
  
  <xacro:wheel name="front_right_wheel" radius="0.05" width="0.03">
    <origin xyz="${0.2} ${-0.15} 0" rpy="0 0 0"/>
  </xacro:wheel>
  
</robot>
```

### 3.2 参数类型

Xacro宏支持三种类型的参数：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 普通参数：字符串或数值 -->
  <xacro:macro name="box_link" params="name size">
    <link name="${name}">
      <visual>
        <geometry>
          <box size="${size}"/>
        </geometry>
      </visual>
    </link>
  </xacro:macro>
  
  <!-- 块参数：允许嵌入XML内容 -->
  <xacro:macro name="sensor_mount" params="name *origin **axis">
    <link name="${name}"/>
    <joint name="${name}_joint" type="fixed">
      <parent link="base_link"/>
      <child link="${name}"/>
      <xacro:insert_block name="origin"/>
      <xacro:insert_block name="axis"/>
    </joint>
  </xacro:macro>
  
  <!-- 调用示例 -->
  <xacro:box_link name="body" size="0.5 0.3 0.1"/>
  
  <xacro:sensor_mount name="laser">
    <origin xyz="0.3 0 0.1" rpy="0 0 0"/>
    <axis xyz="0 0 1"/>
  </xacro:sensor_mount>
  
</robot>
```

### 3.3 默认参数值

从Xacro 1.14.0版本开始，支持默认参数值：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 带默认值的参数 -->
  <xacro:macro name="motor" params="name type:=servo *origin">
    <link name="${name}">
      <visual>
        <geometry>
          <xacro:if value="${type == 'servo'}">
            <cylinder length="0.04" radius="0.02"/>
          </xacro:if>
          <xacro:if value="${type == 'stepper'}">
            <box size="0.04 0.04 0.06"/>
          </xacro:if>
        </geometry>
      </visual>
    </link>
    <joint name="${name}_joint" type="revolute">
      <xacro:insert_block name="origin"/>
      <limit lower="-3.14" upper="3.14" effort="10" velocity="5"/>
    </joint>
  </xacro:macro>
  
  <!-- 使用默认值 -->
  <xacro:motor name="motor1" origin="xyz 0.1 0 0"/>
  
  <!-- 覆盖默认值 -->
  <xacro:motor name="motor2" type="stepper" origin="xyz 0.2 0 0"/>
  
</robot>
```

### 3.4 宏的嵌套与递归

宏可以相互调用，实现复杂的模块化设计：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 基础轮子宏 -->
  <xacro:macro name="wheel" params="name radius width">
    <link name="${name}">
      <visual>
        <geometry>
          <cylinder length="${width}" radius="${radius}"/>
        </geometry>
        <material name="black"/>
      </visual>
    </link>
  </xacro:macro>
  
  <!-- 轮腿组件宏（包含轮子和关节） -->
  <xacro:macro name="wheel_leg" params="name x y radius width">
    <xacro:wheel name="${name}_wheel" radius="${radius}" width="${width}"/>
    <joint name="${name}_joint" type="continuous">
      <parent link="base_link"/>
      <child link="${name}_wheel"/>
      <origin xyz="${x} ${y} ${-0.03}" rpy="${pi/2} 0 0"/>
      <axis xyz="0 1 0"/>
    </joint>
  </xacro:macro>
  
  <!-- 四轮底盘宏 -->
  <xacro:macro name="four_wheel_base" params="wheel_radius wheel_width">
    <xacro:wheel_leg name="front_left" x="0.15" y="0.1" 
                    radius="${wheel_radius}" width="${wheel_width}"/>
    <xacro:wheel_leg name="front_right" x="0.15" y="-0.1" 
                    radius="${wheel_radius}" width="${wheel_width}"/>
    <xacro:wheel_leg name="back_left" x="-0.15" y="0.1" 
                    radius="${wheel_radius}" width="${wheel_width}"/>
    <xacro:wheel_leg name="back_right" x="-0.15" y="-0.1" 
                    radius="${wheel_radius}" width="${wheel_width}"/>
  </xacro:macro>
  
  <!-- 调用四轮底盘宏 -->
  <xacro:four_wheel_base wheel_radius="0.05" wheel_width="0.03"/>
  
</robot>
```

---

## 4. 条件渲染

条件渲染允许根据参数值动态生成不同的XML结构，这是创建可配置机器人的关键技术。

### 4.1 if条件语句

使用`<xacro:if>`标签实现条件渲染：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <xacro:property name="use_gpu" value="true"/>
  <xacro:property name="sim_mode" value="true"/>
  
  <!-- 简单的条件判断 -->
  <xacro:if value="${use_gpu}">
    <link name="gpu_link">
      <visual>
        <box size="0.05 0.05 0.01"/>
        <material name="green"/>
      </visual>
    </link>
  </xacro:if>
  
  <xacro:if value="${not use_gpu}">
    <link name="cpu_link">
      <visual>
        <box size="0.08 0.08 0.02"/>
        <material name="red"/>
      </visual>
    </link>
  </xacro:if>
  
  <!-- 使用elif（通过嵌套if实现） -->
  <xacro:if value="${sim_mode}">
    <gazebo reference="base_link">
      <material>Gazebo/Blue</material>
    </gazebo>
  </xacro:if>
  <xacro:if value="${not sim_mode}">
    <gazebo reference="base_link">
      <material>Gazebo/Grey</material>
    </gazebo>
  </xacro:if>
  
</robot>
```

### 4.2 unless条件语句

`unless`是`if`的相反条件，当值为false时执行：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <xacro:property name="debug" value="false"/>
  
  <!-- if：条件为true时执行 -->
  <xacro:if value="${debug}">
    <link name="debug_led">
      <visual>
        <sphere radius="0.01"/>
        <material name="yellow"/>
      </visual>
    </link>
  </xacro:if>
  
  <!-- unless：条件为false时执行 -->
  <xacro:unless value="${debug}">
    <link name="production_led">
      <visual>
        <sphere radius="0.005"/>
        <material name="green"/>
      </visual>
    </link>
  </xacro:unless>
  
</robot>
```

### 4.3 多条件选择

使用字典或列表实现多条件选择：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <xacro:property name="robot_type" value="diff_drive"/>
  
  <!-- 差速驱动配置 -->
  <xacro:if value="${robot_type == 'diff_drive'}">
    <xacro:property name="wheel_count" value="2"/>
    <xacro:property name="wheel_separation" value="0.3"/>
  </xacro:if>
  
  <!-- 阿克曼配置 -->
  <xacro:if value="${robot_type == 'ackermann'}">
    <xacro:property name="wheel_count" value="4"/>
    <xacro:property name="wheel_separation" value="0.25"/>
  </xacro:if>
  
  <!-- 麦克纳姆轮配置 -->
  <xacro:if value="${robot_type == 'mecanum'}">
    <xacro:property name="wheel_count" value="4"/>
    <xacro:property name="wheel_separation" value="0.35"/>
  </xacro:if>
  
  <!-- 使用配置值 -->
  <link name="base">
    <visual>
      <geometry>
        <box size="${0.4} ${wheel_separation + 0.1} 0.1"/>
      </geometry>
    </visual>
  </link>
  
</robot>
```

### 4.4 条件与宏的结合

条件渲染与宏结合是创建可配置机器人的最佳实践：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 传感器配置参数 -->
  <xacro:property name="has_laser" value="true"/>
  <xacro:property name="has_camera" value="true"/>
  <xacro:property name="has_imu" value="false"/>
  
  <!-- 激光雷达传感器宏 -->
  <xacro:macro name="laser_scanner" params="name topic:=scan">
    <link name="${name}">
      <visual>
        <cylinder length="0.05" radius="0.04"/>
        <material name="blue"/>
      </visual>
      <collision>
        <cylinder length="0.05" radius="0.04"/>
      </collision>
    </link>
    <joint name="${name}_joint" type="fixed">
      <parent link="base_link"/>
      <child link="${name}"/>
      <origin xyz="0.15 0 0.05" rpy="0 0 0"/>
    </joint>
    <gazebo reference="${name}">
      <sensor type="ray" name="${name}">
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
        </ray>
        <plugin name="gazebo_ros_laser" filename="libgazebo_ros_ray_sensor.so">
          <ros>
            <namespace>/</namespace>
            <remapping>~/out:=${topic}</remapping>
          </ros>
          <output_type>sensor_msgs/LaserScan</output_type>
        </plugin>
      </sensor>
    </gazebo>
  </xacro:macro>
  
  <!-- 相机传感器宏 -->
  <xacro:macro name="camera" params="name topic:=image">
    <link name="${name}">
      <visual>
        <box size="0.03 0.08 0.03"/>
        <material name="black"/>
      </visual>
    </link>
    <joint name="${name}_joint" type="fixed">
      <parent link="base_link"/>
      <child link="${name}"/>
      <origin xyz="0.2 0 0.02" rpy="0 0 0"/>
    </joint>
    <gazebo reference="${name}">
      <sensor type="camera" name="${name}">
        <update_rate>30.0</update_rate>
        <camera name="head">
          <horizontal_fov>1.3962634</horizontal_fov>
          <image>
            <width>640</width>
            <height>480</height>
            <format>R8G8B8</format>
          </image>
          <clip>
            <near>0.02</near>
            <far>300</far>
          </clip>
        </camera>
        <plugin name="gazebo_ros_camera" filename="libgazebo_ros_camera.so">
          <ros>
            <namespace>/</namespace>
            <remapping>~/image_raw:=${topic}</remapping>
          </ros>
          <camera_name>${name}</camera_name>
          <frame_name>${name}_frame</frame_name>
        </plugin>
      </sensor>
    </gazebo>
  </xacro:macro>
  
  <!-- 根据配置条件性地添加传感器 -->
  <xacro:if value="${has_laser}">
    <xacro:laser_scanner name="laser" topic="/scan"/>
  </xacro:if>
  
  <xacro:if value="${has_camera}">
    <xacro:camera name="camera" topic="/camera/image"/>
  </xacro:if>
  
  <xacro:if value="${has_imu}">
    <!-- IMU传感器定义... -->
  </xacro:if>
  
</robot>
```

---

## 5. 文件包含与模块化

Xacro支持文件包含，这使得我们可以将机器人模型拆分成多个模块，便于团队协作和代码复用。

### 5.1 包含其他Xacro文件

使用`<xacro:include>`标签包含其他文件：

```xml
<?xml version="1.0"?>
<!-- main.xacro - 主文件 -->
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 包含公共定义 -->
  <xacro:include filename="common_properties.xacro"/>
  <xacro:include filename="materials.xacro"/>
  
  <!-- 包含机器人部件 -->
  <xacro:include filename="base.xacro"/>
  <xacro:include filename="wheels.xacro"/>
  <xacro:include filename="sensors.xacro"/>
  
  <!-- 主底盘链接 -->
  <link name="base_footprint"/>
  <link name="base_link"/>
  <joint name="base_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 0.05"/>
  </joint>
  
</robot>
```

```xml
<!-- common_properties.xacro - 公共属性 -->
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <xacro:property name="pi" value="3.14159"/>
  <xacro:property name="wheel_radius" value="0.05"/>
  <xacro:property name="wheel_width" value="0.03"/>
  
</robot>
```

```xml
<!-- materials.xacro - 材质定义 -->
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <material name="black">
    <color rgba="0.1 0.1 0.1 1.0"/>
  </material>
  <material name="white">
    <color rgba="0.9 0.9 0.9 1.0"/>
  </material>
  <material name="blue">
    <color rgba="0.2 0.2 0.8 1.0"/>
  </material>
  <material name="red">
    <color rgba="0.8 0.2 0.2 1.0"/>
  </material>
  
</robot>
```

### 5.2 命名空间

使用`ns`属性避免命名冲突：

```xml
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 使用命名空间 -->
  <xacro:include filename="sensors/laser.xacro" ns="laser"/>
  <xacro:include filename="sensors/camera.xacro" ns="camera"/>
  
  <!-- 调用带命名空间的宏 -->
  <xacro:laser:hokuyo name="front_laser"/>
  <xacro:camera:realsense name="front_camera"/>
  
</robot>
```

### 5.3 模块化设计最佳实践

推荐的文件结构：

```
robot_description/
├── CMakeLists.txt
├── package.xml
├── xacro/
│   ├── main.xacro              # 主入口
│   ├── robot.xacro             # 机器人主模型
│   ├── properties/
│   │   └── constants.xacro     # 常量定义
│   ├── materials.xacro         # 材质定义
│   ├── base/
│   │   ├── base.xacro          # 底盘
│   │   └── motors.xacro        # 电机
│   ├── wheels/
│   │   ├── wheel.xacro         # 轮子宏
│   │   └── diff_wheels.xacro   # 差速轮配置
│   └── sensors/
│       ├── laser.xacro         # 激光雷达
│       ├── camera.xacro        # 相机
│       └── imu.xacro           # IMU
└── config/
    └── robot.yaml              # 参数配置
```

---

## 6. 实战：创建可配置的差速机器人模型

本节我们将创建一个完整的、可配置的差速机器人模型，综合运用Xacro的各种特性。

### 6.1 项目结构

首先创建功能包结构：

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake diff_robot_description
mkdir -p diff_robot_description/xacro
mkdir -p diff_robot_description/urdf
mkdir -p diff_robot_description/launch
```

### 6.2 创建配置文件

```xml
<!-- xacro/config/robot_config.xacro -->
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- ==================== 基础参数 ==================== -->
  <xacro:property name="pi" value="3.14159"/>
  
  <!-- 机器人名称 -->
  <xacro:property name="robot_name" value="diff_robot"/>
  
  <!-- ==================== 底盘参数 ==================== -->
  <xacro:property name="base_length" value="0.4"/>
  <xacro:property name="base_width" value="0.3"/>
  <xacro:property name="base_height" value="0.05"/>
  <xacro:property name="base_mass" value="2.0"/>
  
  <!-- ==================== 轮子参数 ==================== -->
  <xacro:property name="wheel_radius" value="0.05"/>
  <xacro:property name="wheel_width" value="0.03"/>
  <xacro:property name="wheel_mass" value="0.2"/>
  <xacro:property name="wheel_separation" value="0.25"/>
  <xacro:property name="wheel_offset_x" value="0.1"/>
  
  <!-- ==================== 传感器参数 ==================== -->
  <xacro:property name="has_laser" value="true"/>
  <xacro:property name="has_camera" value="false"/>
  <xacro:property name="laser_height" value="0.08"/>
  <xacro:property name="laser_offset" value="0.15"/>
  
  <!-- ==================== 颜色配置 ==================== -->
  <xacro:property name="base_color" value="0.2 0.2 0.8 1.0"/>
  <xacro:property name="wheel_color" value="0.1 0.1 0.1 1.0"/>
  
</robot>
```

### 6.3 创建轮子宏

```xml
<!-- xacro/wheel.xacro -->
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 轮子宏定义 -->
  <xacro:macro name="wheel" params="name suffix x_offset y_offset">
    <link name="${name}_${suffix}">
      <visual>
        <origin rpy="${pi/2} 0 0"/>
        <geometry>
          <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
        </geometry>
        <material name="wheel_color"/>
      </visual>
      <collision>
        <origin rpy="${pi/2} 0 0"/>
        <geometry>
          <cylinder length="${wheel_width}" radius="${wheel_radius}"/>
        </geometry>
      </collision>
      <inertial>
        <origin rpy="${pi/2} 0 0"/>
        <mass value="${wheel_mass}"/>
        <inertia
          ixx="${wheel_mass * (3*wheel_radius*wheel_radius + wheel_width*wheel_width) / 12}"
          ixy="0" ixz="0"
          iyy="${wheel_mass * wheel_radius*wheel_radius / 2}"
          iyz="0"
          izz="${wheel_mass * (3*wheel_radius*wheel_radius + wheel_width*wheel_width) / 12}"/>
      </inertial>
    </link>
    
    <!-- 轮子关节 -->
    <joint name="${name}_${suffix}_joint" type="continuous">
      <parent link="${name}_link"/>
      <child link="${name}_${suffix}"/>
      <origin xyz="${x_offset} ${y_offset} 0" rpy="0 0 0"/>
      <axis xyz="0 1 0"/>
      <dynamics damping="0.05" friction="0.1"/>
    </joint>
    
    <!-- Gazebo物理属性 -->
    <gazebo reference="${name}_${suffix}">
      <mu1>1.0</mu1>
      <mu2>1.0</mu2>
      <kp>1000000.0</kp>
      <kd>100.0</kd>
      <material>Gazebo/Black</material>
    </gazebo>
  </xacro:macro>
  
  <!-- 四轮差速底盘宏 -->
  <xacro:macro name="diff_wheels" params="name">
    <xacro:wheel name="${name}" suffix="front_left" 
                x_offset="${wheel_offset_x}" y_offset="${wheel_separation/2}"/>
    <xacro:wheel name="${name}" suffix="front_right" 
                x_offset="${wheel_offset_x}" y_offset="${-wheel_separation/2}"/>
    <xacro:wheel name="${name}" suffix="back_left" 
                x_offset="${-wheel_offset_x}" y_offset="${wheel_separation/2}"/>
    <xacro:wheel name="${name}" suffix="back_right" 
                x_offset="${-wheel_offset_x}" y_offset="${-wheel_separation/2}"/>
  </xacro:macro>
  
</robot>
```

### 6.4 创建激光雷达宏

```xml
<!-- xacro/sensors/laser_scanner.xacro -->
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 激光雷达传感器宏 -->
  <xacro:macro name="laser_scanner" params="name parent:=base_link">
    <link name="${name}_link">
      <visual>
        <origin xyz="0 0 ${laser_height/2}" rpy="0 0 0"/>
        <geometry>
          <cylinder length="${laser_height}" radius="0.04"/>
        </geometry>
        <material name="blue"/>
      </visual>
      <collision>
        <origin xyz="0 0 ${laser_height/2}" rpy="0 0 0"/>
        <geometry>
          <cylinder length="${laser_height}" radius="0.04"/>
        </geometry>
      </collision>
      <inertial>
        <mass value="0.1"/>
        <inertia
          ixx="0.0001" ixy="0" ixz="0"
          iyy="0.0001" iyz="0"
          izz="0.0001"/>
      </inertial>
    </link>
    
    <joint name="${name}_joint" type="fixed">
      <parent link="${parent}"/>
      <child link="${name}_link"/>
      <origin xyz="${laser_offset} 0 ${base_height/2 + laser_height/2}" rpy="0 0 0"/>
    </joint>
    
    <!-- Gazebo仿真配置 -->
    <gazebo reference="${name}_link">
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
        <plugin name="gazebo_ros_laser" filename="libgazebo_ros_ray_sensor.so">
          <ros>
            <namespace>/</namespace>
            <remapping>~/out:=scan</remapping>
          </ros>
          <output_type>sensor_msgs/LaserScan</output_type>
        </plugin>
      </sensor>
    </gazebo>
  </xacro:macro>
  
</robot>
```

### 6.5 创建主机器人模型文件

```xml
<!-- xacro/robot.xacro -->
<?xml version="1.0"?>
<robot xmlns:xacro="http://www.ros.org/wiki/xacro">
  
  <!-- 包含配置文件 -->
  <xacro:include filename="config/robot_config.xacro"/>
  <xacro:include filename="wheel.xacro"/>
  <xacro:include filename="sensors/laser_scanner.xacro"/>
  
  <!-- 基础底座连接 -->
  <link name="base_footprint">
    <inertial>
      <mass value="0.01"/>
      <origin xyz="0 0 0"/>
      <inertia ixx="0.0001" ixy="0" ixz="0" iyy="0.0001" iyz="0" izz="0.0001"/>
    </inertial>
  </link>
  
  <!-- 主底座链接 -->
  <link name="base_link">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="${base_length} ${base_width} ${base_height}"/>
      </geometry>
      <material name="base_color"/>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <box size="${base_length} ${base_width} ${base_height}"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="${base_mass}"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia
        ixx="${base_mass * (base_width*base_width + base_height*base_height) / 12}"
        ixy="0" ixz="0"
        iyy="${base_mass * (base_length*base_length + base_height*base_height) / 12}"
        iyz="0"
        izz="${base_mass * (base_length*base_length + base_width*base_width) / 12}"/>
    </inertial>
  </link>
  
  <!-- 底座关节 -->
  <joint name="base_joint" type="fixed">
    <parent link="base_footprint"/>
    <child link="base_link"/>
    <origin xyz="0 0 ${wheel_radius}" rpy="0 0 0"/>
  </joint>
  
  <!-- 添加轮子 -->
  <xacro:diff_wheels name="base"/>
  
  <!-- 根据配置添加传感器 -->
  <xacro:if value="${has_laser}">
    <xacro:laser_scanner name="laser" parent="base_link"/>
  </xacro:if>
  
  <!-- Gazebo控制器配置 -->
  <gazebo>
    <plugin filename="libgazebo_ros_diff_drive.so" name="gazebo_ros_diff_drive">
      <ros>
        <namespace>/</namespace>
        <remapping>~/cmd_vel:=cmd_vel</remapping>
        <remapping>~/odom:=odom</remapping>
      </ros>
      
      <!-- 机器人参数 -->
      <update_rate>50</update_rate>
      
      <!-- 驱动配置 -->
      <left_joint>base_back_left_joint</left_joint>
      <right_joint>base_back_right_joint</right_joint>
      <wheel_separation>${wheel_separation}</wheel_separation>
      <wheel_diameter>${wheel_radius * 2}</wheel_diameter>
      
      <!-- 动力学参数 -->
      <max_wheel_torque>20</max_wheel_torque>
      <max_wheel_acceleration>1.0</max_wheel_acceleration>
      
      <!-- 里程计配置 -->
      <odometry_frame>odom</odometry_frame>
      <robot_base_frame>base_footprint</robot_base_frame>
      
      <!-- 发布里程计 -->
      <publish_odom>true</publish_odom>
      <publish_odom_tf>true</publish_odom_tf>
      <publish_wheel_tf>true</publish_wheel_tf>
    </plugin>
  </gazebo>
  
</robot>
```

### 6.6 创建Launch文件

```python
# launch/robot.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os
from pathlib import Path

def generate_launch_description():
    # 获取功能包路径
    pkg_name = 'diff_robot_description'
    pkg_share = FindPackageShare(pkg_name).find(pkg_name)
    
    # Xacro文件路径
    default_model_path = os.path.join(pkg_share, 'xacro', 'robot.xacro')
    
    # 声明模型参数
    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=default_model_path,
        description='机器人模型文件路径'
    )
    
    # 声明是否使用仿真时间参数
    use_sim_time_arg = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='是否使用仿真时间'
    )
    
    # 机器人状态发布节点
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'robot_description': LaunchConfiguration('model')
        }],
        output='screen'
    )
    
    return LaunchDescription([
        model_arg,
        use_sim_time_arg,
        robot_state_publisher
    ])
```

### 6.7 测试模型

```bash
# 编译功能包
cd ~/ros2_ws
colcon build --packages-select diff_robot_description
source install/setup.bash

# 转换为URDF查看
xacro ~/ros2_ws/install/diff_robot_description/share/diff_robot_description/xacro/robot.xacro > /tmp/robot.urdf
check_urdf /tmp/robot.urdf

# 启动RViz查看
ros2 launch diff_robot_description robot.launch.py

# 在RViz中:
# 1. 添加RobotModel显示
# 2. 设置Fixed Frame为base_footprint
# 3. 查看机器人模型
```

---

## 练习题

### 选择题

1. Xacro文件可以直接被RViz或Gazebo加载吗？
   - A) 可以直接加载
   - B) 需要先转换为URDF
   - C) 只能被Gazebo加载
   - D) 只能被RViz加载
   
   **答案：B**。Xacro文件需要先使用xacro工具转换为标准的URDF文件，才能被RViz或Gazebo加载使用。

2. 以下哪个标签用于定义Xacro中的变量？
   - `<xacro:define>`
   - `<xacro:variable>`
   - `<xacro:property>`
   - `<xacro:const>`
   
   **答案：C**。使用`<xacro:property>`标签定义属性（变量），这是Xacro中最基本的变量定义方式。

3. 在Xacro宏中，哪个标签用于插入调用时传入的XML块内容？
   - `<xacro:insert>`
   - `<xacro:insert_block>`
   - `<xacro:content>`
   - `<xacro:block>`
   
   **答案：B**。使用`<xacro:insert_block>`标签插入通过`*`参数传入的XML块内容。

4. 条件渲染使用什么标签？
   - `<xacro:condition>`
   - `<xacro:if>`和`<xacro:unless>`
   - `<xacro:switch>`
   - `<xacro:case>`
   
   **答案：B**。Xacro使用`<xacro:if>`和`<xacro:unless>`标签进行条件渲染，实现根据参数值动态生成不同的XML结构。

### 实践题

5. 创建一个Xacro文件，定义一个可配置的方形连杆（link）宏，要求参数包括：名称、尺寸、颜色、材质名称。
   
   **参考答案**：
   
   ```xml
   <?xml version="1.0"?>
   <robot xmlns:xacro="http://www.ros.org/wiki/xacro">
     
     <xacro:macro name="box_link" params="name size color material_name">
       <link name="${name}">
         <visual>
           <geometry>
             <box size="${size}"/>
           </geometry>
           <material name="${material_name}">
             <color rgba="${color}"/>
           </material>
         </visual>
         <collision>
           <geometry>
             <box size="${size}"/>
           </geometry>
         </collision>
         <inertial>
           <mass value="1.0"/>
           <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/>
         </inertial>
       </link>
     </xacro:macro>
     
     <!-- 调用示例 -->
     <xacro:box_link name="arm_link1" size="0.1 0.05 0.03" 
                    color="0.8 0.2 0.2 1.0" material_name="red_material"/>
   </robot>
   ```

6. 修改上面的方杆宏，添加条件判断，使得当`has_inertia`参数为false时不生成惯性数据。
   
   **参考答案**：
   
   ```xml
   <?xml version="1.0"?>
   <robot xmlns:xacro="http://www.ros.org/wiki/xacro">
     
     <xacro:macro name="box_link" params="name size color material_name has_inertia:=true">
       <link name="${name}">
         <visual>
           <geometry>
             <box size="${size}"/>
           </geometry>
           <material name="${material_name}">
             <color rgba="${color}"/>
           </material>
         </visual>
         <collision>
           <geometry>
             <box size="${size}"/>
           </geometry>
         </collision>
         
         <!-- 条件生成惯性数据 -->
         <xacro:if value="${has_inertia}">
           <inertial>
             <mass value="1.0"/>
             <inertia ixx="0.01" ixy="0" ixz="0" iyy="0.01" iyz="0" izz="0.01"/>
           </inertial>
         </xacro:if>
       </link>
     </xacro:macro>
     
     <!-- 使用默认值（包含惯性） -->
     <xacro:box_link name="arm_link1" size="0.1 0.05 0.03" 
                    color="0.8 0.2 0.2 1.0" material_name="red_material"/>
     
     <!-- 禁用惯性（用于纯视觉显示） -->
     <xacro:box_link name="decorative_link" size="0.05 0.05 0.01" 
                    color="0.5 0.5 0.5 1.0" material_name="gray" has_inertia="false"/>
   </robot>
   ```

7. 创建一个完整的机器人模型，包含：底座（圆柱）、两个轮子（圆柱）、可选的激光雷达传感器。使用Xacro实现，通过参数控制是否安装激光雷达。
   
   **参考答案**：
   
   ```xml
   <?xml version="1.0"?>
   <robot xmlns:xacro="http://www.ros.org/wiki/xacro">
     
     <!-- 配置参数 -->
     <xacro:property name="has_laser" value="true"/>
     <xacro:property name="pi" value="3.14159"/>
     
     <!-- 底座参数 -->
     <xacro:property name="base_radius" value="0.15"/>
     <xacro:property name="base_height" value="0.05"/>
     
     <!-- 轮子参数 -->
     <xacro:property name="wheel_radius" value="0.05"/>
     <xacro:property name="wheel_width" value="0.03"/>
     <xacro:property name="wheel_separation" value="0.2"/>
     
     <!-- 底座 -->
     <link name="base_link">
       <visual>
         <geometry>
           <cylinder radius="${base_radius}" length="${base_height}"/>
         </geometry>
         <material name="blue"/>
       </visual>
       <collision>
         <geometry>
           <cylinder radius="${base_radius}" length="${base_height}"/>
         </geometry>
       </collision>
     </link>
     
     <!-- 轮子宏 -->
     <xacro:macro name="wheel" params="suffix y_offset">
       <link name="wheel_${suffix}">
         <visual>
           <origin rpy="${pi/2} 0 0"/>
           <geometry>
             <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
           </geometry>
           <material name="black"/>
         </visual>
         <collision>
           <origin rpy="${pi/2} 0 0"/>
           <geometry>
             <cylinder radius="${wheel_radius}" length="${wheel_width}"/>
           </geometry>
         </collision>
       </link>
       <joint name="wheel_${suffix}_joint" type="continuous">
         <parent link="base_link"/>
         <child link="wheel_${suffix}"/>
         <origin xyz="0 ${y_offset} ${-base_height/2}" rpy="0 0 0"/>
         <axis xyz="0 1 0"/>
       </joint>
     </xacro:macro>
     
     <!-- 安装轮子 -->
     <xacro:wheel suffix="left" y_offset="${wheel_separation/2}"/>
     <xacro:wheel suffix="right" y_offset="${-wheel_separation/2}"/>
     
     <!-- 激光雷达宏 -->
     <xacro:macro name="laser" params="name parent">
       <link name="${name}">
         <visual>
           <cylinder radius="0.03" height="0.04"/>
           <material name="red"/>
         </visual>
       </link>
       <joint name="${name}_joint" type="fixed">
         <parent link="${parent}"/>
         <child link="${name}"/>
         <origin xyz="0 0 ${base_height/2 + 0.02}" rpy="0 0 0"/>
       </joint>
     </xacro:macro>
     
     <!-- 条件安装激光雷达 -->
     <xacro:if value="${has_laser}">
       <xacro:laser name="laser" parent="base_link"/>
     </xacro:if>
     
   </robot>
   ```

---

## 本章小结

本章我们全面学习了ROS2中Xacro的使用方法。Xacro作为URDF的扩展，提供了变量定义、数学表达式、宏定义、条件渲染和文件包含等强大功能。

**核心概念回顾**：
- **变量（property）**：使用`<xacro:property>`定义可重用的数值，支持Python风格的数学表达式
- **宏（macro）**：使用`<xacro:macro>`定义可复用的XML代码块，支持普通参数、块参数和默认参数值
- **条件渲染**：使用`<xacro:if>`和`<xacro:unless>`根据条件动态生成XML结构
- **文件包含**：使用`<xacro:include>`将模型拆分成多个模块，便于团队协作

通过本章的实战案例，你学会了如何创建一个可配置的差速机器人模型，包括底盘、轮子、传感器等组件。这些技能将帮助你在后续的Gazebo仿真中快速构建各种机器人模型。

---

## 参考资料

### ROS2官方文档

1. Xacro Documentation: <https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Using-Xacro.html>
2. URDF Documentation: <https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/URDF-Main.html>
3. Robot State Publisher: <https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Using-URDF-with-Robot-State-Publisher.html>

### Xacro进阶

4. Xacro in Gazebo: <https://gazebosim.org/docs/latest/urdf/>
5. Working with Plugins: <https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Using-Gazebo-Plugins-with-URDF.html>

### 示例代码

6. ROS2 Examples: <https://github.com/ros2/examples>
7. TurtleBot3 Description: <https://github.com/ROBOTIS-GIT/turtlebot3/tree/master/turtlebot3_description>

---

## 下节预告

下一节我们将学习**07-4 Gazebo仿真环境搭建**，了解如何在Gazebo中创建仿真环境、设置物理属性、添加障碍物等。配合本章学习的Xacro建模知识，你将能够创建完整的机器人仿真系统。

---

*本章学习完成！Xacro是ROS2机器人建模的核心工具，熟练掌握变量、宏和条件渲染，将大大提高你创建复杂机器人模型的效率。建议大家多加练习，尝试创建自己的机器人模型。*
