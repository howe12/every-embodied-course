# 09-5-X Nav2 on RDK-X5 实机部署

> **前置课程**：[09-5 仿真导航全流程实战（Gazebo+Nav2）](../09-AMCL定位导航技术/09-5-仿真导航全流程实战（Gazebo+Nav2）.md)
> **前置课程**：[09-4 ROS2导航栈架构与核心模块](../09-AMCL定位导航技术/09-4-ROS2导航栈架构与核心模块.md)
> **对应课程**：09-5 导航实战（RDK-X5 实机部署）

---

## 目录

1. [Nav2 概述与架构](#1-nav2-概述与架构)
2. [硬件系统集成](#2-硬件系统集成)
3. [Nav2 环境搭建](#3-nav2-环境搭建)
4. [地图构建（SLAM）](#4-地图构建slam)
5. [Nav2 配置与调参](#5-nav2-配置与调参)
6. [实机导航启动](#6-实机导航启动)
7. [ROS2 导航节点封装](#7-ros2-导航节点封装)
8. [部署与验证](#8-部署与验证)
9. [常见问题排查](#9-常见问题排查)
10. [练习题](#练习题)
11. [答案](#答案)

---

## 1. Nav2 概述与架构

### 1.1 ROS Navigation Stack vs Nav2

ROS（Robot Operating System）早期使用 **navigation stack**（Groovy 及以前版本）进行移动机器人导航。随着 ROS1 到 ROS2 的演进，原有导航栈已无法适配 ROS2 的新特性，于是 **Nav2**（Navigation2）应运而生，成为 ROS2 官方推荐的导航框架。

| 特性 | ROS Navigation Stack（ROS1） | Nav2（ROS2） |
|------|------------------------------|--------------|
| 框架版本 | ROS1（Groovy~Noetic） | ROS2（Humble/Iron/Jazzy） |
| 生命周期管理 | 无 | 行为树（BT）驱动，支持插件化 |
| 恢复策略 | 固定 3 种 | 可配置行为树，灵活扩展 |
| 参数服务器 | XML 参数 | YAML + ROS2 参数 |
| TF 变换 | tf/tf2 | tf2（统一变换库） |
| 插件系统 | 无 | 全模块插件化（Planner/Controller/Costmap） |
| 多机器人支持 | 有限 | 原生多机器人场景 |
| 状态机 | 简单状态机 | 行为树（Behavior Tree） |

```
┌──────────────────────────────────────────────────────┐
│                  Nav2 整体架构                         │
│                                                      │
│  ┌────────────┐   ┌────────────┐   ┌──────────────┐ │
│  │   RVIZ2    │   │  Nav2 App  │   │  外部指令     │ │
│  │  (可视化)   │   │ (API调用)   │   │ (Python/ROS2)│ │
│  └─────┬──────┘   └─────┬──────┘   └──────┬───────┘ │
│        │                │                  │         │
│        └────────────────┼──────────────────┘         │
│                         ▼                            │
│              ┌──────────────────┐                    │
│              │   Nav2 BT Server  │                   │
│              │   (行为树控制器)   │                   │
│              └────────┬─────────┘                    │
│      ┌────────────────┼────────────────┐             │
│      ▼                ▼                ▼             │
│  ┌────────┐     ┌──────────┐    ┌──────────┐       │
│  │Planner │     │Controller│    │ Recovery  │       │
│  │(全局路径)│    │(局部路径) │    │(恢复行为)  │       │
│  └────────┘     └──────────┘    └──────────┘       │
│      │                │                │             │
│      └────────────────┼────────────────┘             │
│                       ▼                               │
│              ┌──────────────────┐                    │
│              │     Costmap      │                    │
│              │   (代价地图)      │                    │
│              └──────────────────┘                    │
│                       │                              │
│              ┌────────┴────────┐                    │
│              │    传感器数据     │                    │
│              │激光雷达/IMU/编码器│                    │
│              └─────────────────┘                     │
└──────────────────────────────────────────────────────┘
```

### 1.2 Nav2 核心模块

Nav2 的核心组件包括 **行为树服务器**、**规划器**、**控制器** 和 **恢复器**：

| 模块 | 功能 | 典型插件 |
|------|------|---------|
| **Planner**（全局规划器） | 在代价地图上计算从当前位置到目标点的全局路径 | NavFn、DWB、Smac Planner |
| **Controller**（局部控制器） | 跟踪全局路径，输出速度指令 | DWB、Teb、MPPI |
| **Recovery**（恢复器） | 碰撞、卡住时执行恢复行为（后退、旋转） | BackUp、Spin、Wait |
| **Behavior Tree**（行为树） | 编排 Planner/Controller/Recovery 的执行逻辑 | XML 配置 |
| **Lifecycle Manager** | 管理所有导航节点的生命周期（Config→Active→Inactive） | 节点启动/停止 |

### 1.3 RDK-X5 部署 Nav2 的优势

| 优势 | 说明 |
|------|------|
| **异构计算** | RDK-X5 集成 BPU（AI 加速器），可同时处理 AI 感知 + 导航规划 |
| **低功耗** | 相比 x86 工控机，RDK-X5 功耗更低，适合嵌入式部署 |
| **原生 ROS2 支持** | 地平线 BSP 基于 Ubuntu 22.04，可直接安装 ROS2 Humble |
| **MIPI/摄像头接口** | 内置 MIPI 接口，支持视觉 SLAM（VSLAM）与导航融合 |
| **实时性能** | 5 TOPS@INT8 算力，足够处理 10Hz 以上的路径规划循环 |
| **体积小巧** | 适合中小型移动机器人（AMR、服务机器人） |

---

## 2. 硬件系统集成

### 2.1 系统连接拓扑

```
┌──────────────────────────────────────────────────────────┐
│                      RDK-X5 开发板                        │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │   激光雷达    │   │   IMU 模块   │   │  电机编码器   │ │
│  │  (UART/USB)  │   │   (I2C/SPI)  │   │  (ABI/PWM)   │ │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘ │
│         │                  │                  │          │
│         └──────────────────┼──────────────────┘          │
│                            ▼                             │
│                   ┌──────────────┐                       │
│                   │  传感器融合   │                        │
│                   │ (robot_localization)│                 │
│                   └────────┬─────┘                       │
│                            │                              │
│         ┌──────────────────┼──────────────────┐         │
│         ▼                  ▼                  ▼         │
│  ┌────────────┐     ┌────────────┐    ┌────────────┐    │
│  │   Nav2     │     │   Costmap  │    │   AMCL     │    │
│  │  Planner   │     │  (局部/全局)│    │ (定位)     │    │
│  └────────────┘     └────────────┘    └────────────┘    │
│                            │                              │
│                            ▼                              │
│                   ┌──────────────┐                       │
│                   │  底盘控制器   │                        │
│                   │ (Motor Driver)│                       │
│                   └──────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

### 2.2 激光雷达连接与驱动安装

#### 硬件连接

| 激光雷达型号 | 接口 | 连接方式 | 话题 |
|-------------|------|---------|------|
| 思岚 A1/A2 | UART | USB 转 TTL | `/scan` |
| Lowa M1/M2 | UART | USB 转 TTL | `/scan` |
| 速腾 RS-LiDAR | Ethernet | 直接网线 | `/scan` |
| 思岚 S1 | USB | Micro USB | `/scan` |

> **注意**：RDK-X5 的 USB 口为 Type-A 接口（USB3.0），思岚 A1 附带 USB 线可直接连接。

#### 驱动安装（思岚 A1 为例）

```bash
# 在 RDK-X5 上创建工作空间
mkdir -p ~/robot_ws/src
cd ~/robot_ws

# 克隆思岚 A1 驱动（rplidar_ros）
git clone https://github.com/Slamtec/rplidar_ros.git src/rplidar_ros

# 检查依赖
rosdep install --from-paths src --ignore-src -r -y

# 编译
source /opt/ros/humble/setup.bash
colcon build --packages-select rplidar_ros

# 编译完成后 source
source install/setup.bash

# 查看话题（激光雷达连接后运行）
ros2 topic list | grep scan
```

#### 启动激光雷达

```bash
# 启动思岚 A1（USB 设备通常为 /dev/ttyUSB0）
ros2 launch rplidar_ros rplidar.launch.py

# 查看激光数据
ros2 topic echo /scan

# rviz2 可视化
ros2 run rviz2 rviz2
# 在 rviz2 中：Add → By topic → /scan → LaserScan
```

#### udev 规则（确保 USB 设备权限）

```bash
# 查看雷达连接的 USB 端口
ls -l /dev/ttyUSB*

# 创建 udev 规则（确保普通用户可访问）
sudo bash -c 'cat > /etc/udev/rules.d/99-rplidar.rules << EOF
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", MODE:="0666", GROUP:="dialout", SYMLINK+="rplidar"
EOF'

# 重新加载 udev 规则
sudo udevadm control --reload-rules
sudo udevadm trigger

# 将当前用户加入 dialout 组
sudo usermod -aG dialout $USER
# 需要重新登录或执行: newgrp dialout
```

### 2.3 电机编码器数据接入

#### 编码器接口说明

| 接口类型 | 说明 | RDK-X5 连接方式 |
|---------|------|----------------|
| AB 相编码器 |  quadrature 脉冲输出 | GPIO + 外部中断，或专用编码器接口 |
| PWM 输出 | 速度/方向信号 | GPIO PWM |
| UART 串口 | 编码器自带 MCU 输出 | USB 转 UART 或板载 UART |
| CAN 总线 | 高速实时总线 | MCP2515 CAN 模块 |

#### 差速轮编码器接入示例

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/robot_bringup/robot_bringup/encoder_reader.py
# 编码器数据读取节点 - 差速轮机器人

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import RPi.GPIO as GPIO
import time

class EncoderReader(Node):
    """
    编码器读取节点
    通过 GPIO 读取左右轮 AB 相编码器，计算轮速并发布
    """
    def __init__(self):
        super().__init__('encoder_reader')
        
        # 参数声明
        self.declare_parameter('ticks_per_meter', 4000)  # 每米编码器脉冲数（根据实际型号调整）
        self.declare_parameter('wheel_separation', 0.4) # 左右轮中心间距（米）
        self.declare_parameter('gpio_left_a', 23)       # 左轮编码器 A 相 GPIO
        self.declare_parameter('gpio_left_b', 24)       # 左轮编码器 B 相 GPIO
        self.declare_parameter('gpio_right_a', 17)       # 右轮编码器 A 相 GPIO
        self.declare_parameter('gpio_right_b', 18)       # 右轮编码器 B 相 GPIO
        
        self.ticks_per_meter = self.get_parameter('ticks_per_meter').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        
        # 编码器计数
        self.left_ticks = 0
        self.right_ticks = 0
        self.last_left_ticks = 0
        self.last_right_ticks = 0
        self.last_time = self.get_clock().now()
        
        # GPIO 初始化（RDK-X5 使用树莓派兼容 GPIO）
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            gpio_left_a = self.get_parameter('gpio_left_a').value
            gpio_left_b = self.get_parameter('gpio_left_b').value
            gpio_right_a = self.get_parameter('gpio_right_a').value
            gpio_right_b = self.get_parameter('gpio_right_b').value
            
            # 设置编码器 GPIO 引脚为输入，启用上拉/下拉
            for gpio in [gpio_left_a, gpio_left_b, gpio_right_a, gpio_right_b]:
                GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.add_event_detect(gpio, GPIO.BOTH, callback=self.encoder_callback)
            
            self.get_logger().info('编码器 GPIO 初始化完成')
        except Exception as e:
            self.get_logger().warn(f'GPIO 初始化失败（可能不在树莓派平台）: {e}')
        
        # 发布左右轮速度
        self.left_vel_pub = self.create_publisher(Float64, '/left_wheel_vel', 10)
        self.right_vel_pub = self.create_publisher(Float64, '/right_wheel_vel', 10)
        
        # 定时器计算速度（10Hz）
        self.timer = self.create_timer(0.1, self.calculate_velocity)
    
    def encoder_callback(self, channel):
        """编码器中断回调 - 计数"""
        # 根据 A/B 相相位判断方向
        # 这里简化处理，实际需要根据具体 GPIO 通道判断左右轮
        pass  # 实际实现需要记录每个 GPIO 的状态变化
    
    def calculate_velocity(self):
        """计算轮速（米/秒）"""
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        
        if dt <= 0:
            return
        
        # 计算增量
        left_delta = self.left_ticks - self.last_left_ticks
        right_delta = self.right_ticks - self.last_right_ticks
        
        # 转换为米/秒
        left_vel = (left_delta / self.ticks_per_meter) / dt
        right_vel = (right_delta / self.ticks_per_meter) / dt
        
        # 发布速度
        self.left_vel_pub.publish(Float64(data=left_vel))
        self.right_vel_pub.publish(Float64(data=right_vel))
        
        # 更新状态
        self.last_left_ticks = self.left_ticks
        self.last_right_ticks = self.right_ticks
        self.last_time = current_time


def main(args=None):
    rclpy.init(args=args)
    node = EncoderReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 2.4 IMU 数据接入

#### 常见 IMU 模块选型

| 型号 | 接口 | 协议 | 特点 |
|------|------|------|------|
| MPU6050 | I2C | I2C | 6 轴，便宜，入门首选 |
| MPU9250 | I2C/SPI | I2C/SPI | 9 轴，包含磁力计 |
| BMI088 | SPI/I2C | SPI/I2C | 工业级，高稳定性 |
| CH110 | UART | UART | 高精度，GPS+IMU 融合 |

#### IMU 驱动安装（以 MPU6050 为例）

```bash
# 安装 ROS2 IMU 驱动
sudo apt-get install -y ros-humble-imu-tools

# 克隆 MPU6050 驱动
cd ~/robot_ws/src
git clone https://github.com/ros-drivers/imu_drivers.git
cd imu_drivers
git checkout humble

# 编译
cd ~/robot_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select imu_tools

# source 并启动
source install/setup.bash
ros2 launch imu_tools mpu6050.launch.py
```

#### IMU 数据验证

```bash
# 查看 IMU 话题
ros2 topic list | grep imu

# 查看 IMU 原始数据
ros2 topic echo /imu

# IMU 标定（水平静止放置，运行 5 分钟）
ros2 run imu_calib do_calibrate
# 标定后修改 ~/.ros/imu_calib.yaml
```

### 2.5 底盘控制接口

#### 底盘控制节点

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/robot_bringup/robot_bringup/chassis_driver.py
# 底盘控制节点 - 将 Nav2 的 /cmd_vel 转换为电机控制信号

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import math

class ChassisDriver(Node):
    """
    底盘驱动节点
    订阅 Nav2 发布的 /cmd_vel（机器人坐标系速度）
    转换为左右轮速度后通过 UART/CAN 发送给电机驱动板
    """
    def __init__(self):
        super().__init__('chassis_driver')
        
        # 参数声明
        self.declare_parameter('wheel_separation', 0.4)  # 左右轮间距（米）
        self.declare_parameter('wheel_radius', 0.05)     # 轮子半径（米）
        self.declare_parameter('uart_port', '/dev/ttyUSB1')  # 电机驱动板串口
        
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.uart_port = self.get_parameter('uart_port').value
        
        # 订阅 Nav2 的速度指令
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # 串口初始化（示例，实际使用 pySerial）
        try:
            import serial
            self.serial_port = serial.Serial(
                self.uart_port,
                115200,
                timeout=0.1
            )
            self.get_logger().info(f'串口 {self.uart_port} 打开成功')
        except Exception as e:
            self.get_logger().warn(f'串口打开失败: {e}')
            self.serial_port = None
        
        self.get_logger().info('底盘驱动节点初始化完成')
    
    def cmd_vel_callback(self, msg: Twist):
        """
        处理 Nav2 发来的速度指令
        将 (v_x, v_theta) 转换为左右轮速度
        """
        v_x = msg.linear.x       # 前进方向线速度（m/s）
        v_theta = msg.angular.z # 绕 z 轴角速度（rad/s）
        
        # 运动学模型：差速轮机器人
        # v_left  = v_x - (wheel_separation / 2) * v_theta
        # v_right = v_x + (wheel_separation / 2) * v_theta
        v_left = v_x - (self.wheel_separation / 2.0) * v_theta
        v_right = v_x + (self.wheel_separation / 2.0) * v_theta
        
        # 转换为轮子转速（RPM）
        left_rpm = (v_left / (2 * math.pi * self.wheel_radius)) * 60.0
        right_rpm = (v_right / (2 * math.pi * self.wheel_radius)) * 60.0
        
        # 通过串口发送电机控制指令
        self.send_motor_command(left_rpm, right_rpm)
        
        self.get_logger().debug(
            f'左轮: {v_left:.3f}m/s({left_rpm:.1f}RPM), '
            f'右轮: {v_right:.3f}m/s({right_rpm:.1f}RPM)'
        )
    
    def send_motor_command(self, left_rpm: float, right_rpm: float):
        """通过串口发送电机控制指令"""
        if self.serial_port is None:
            return
        
        try:
            # 协议格式（示例）：$M,<left_rpm_int>,<right_rpm_int>\n
            cmd = f"$M,{int(left_rpm)},{int(right_rpm)}\n"
            self.serial_port.write(cmd.encode('utf-8'))
        except Exception as e:
            self.get_logger().error(f'串口发送失败: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = ChassisDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 3. Nav2 环境搭建

### 3.1 ROS2 Humble 安装

```bash
# RDK-X5 默认已安装 ROS2 Humble（BSP 镜像）
# 如果需要重新安装，执行以下步骤：

# 1. 设置 locale
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8

# 2. 添加 ROS2 apt 源
sudo apt install -y software-properties-common
sudo add-apt-repository universe
sudo apt install -y curl
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
sudo sh -c 'echo "deb [arch=$(dpkg --print-architecture)] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" > /etc/apt/sources.list.d/ros2.list'

# 3. 安装 ROS2 Humble
sudo apt update
sudo apt install -y ros-humble-desktop
# 或 ros-humble-base（无 GUI 工具，适合嵌入式）

# 4. 安装常用工具
sudo apt install -y \
    python3-rosdep \
    python3-rosinstall \
    python3-rosinstall-generator \
    build-essential \
    git \
    vim

# 5. 初始化 rosdep
sudo rosdep init
rosdep update

# 6. 创建工作空间
mkdir -p ~/robot_ws/src
cd ~/robot_ws
source /opt/ros/humble/setup.bash
```

### 3.2 Nav2 功能包安装

```bash
# 方法一：通过 apt 安装（推荐生产环境）
sudo apt install -y \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-nav2-gazebo \
    ros-humble-slam-toolbox \
    ros-humble-map-server \
    ros-humble-amcl \
    ros-humble-robot-localization \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher

# 方法二：源码编译（需要最新特性）
cd ~/robot_ws/src
git clone https://github.com/ros-planning/navigation2.git -b humble
git clone https://github.com/SteveMacenski/navigation2_bringup.git -b humble
git clone https://github.com/ira-lombok/robot_localization.git -b humble

# 安装 navigation2 依赖
cd ~/robot_ws
rosdep install --from-paths src --ignore-src -r -y

# 编译（RDK-X5 多核编译）
source /opt/ros/humble/setup.bash
colcon build --packages-select navigation2 nav2_bringup robot_localization slam_toolbox
```

### 3.3 工作空间目录结构

```
~/robot_ws/
├── src/
│   ├── navigation2/              # Nav2 核心（官方包）
│   ├── navigation2_bringup/      # Nav2 启动示例
│   ├── robot_localization/       # 传感器融合
│   ├── slam_toolbox/             # SLAM 建图
│   ├── rplidar_ros/              # 激光雷达驱动
│   ├── imu_drivers/              # IMU 驱动
│   └── rdk_deploy/               # ★ 自定义部署包
│       ├── robot_bringup/        # 机器人启动包
│       │   ├── launch/
│       │   │   ├── robot_bringup.launch.py
│       │   │   └── nav2_bringup.launch.py
│       │   ├── config/
│       │   │   ├── nav2_params.yaml
│       │   │   ├── slam_params.yaml
│       │   │   └── ekf.yaml
│       │   └── robot_bringup/
│       │       ├── __init__.py
│       │       ├── chassis_driver.py
│       │       └── encoder_reader.py
│       └── maps/                  # 地图文件
│           ├── my_map.pgm
│           └── my_map.yaml
├── install/
├── build/
└── log/
```

---

## 4. 地图构建（SLAM）

### 4.1 SLAM Toolbox 使用

```bash
# 启动 SLAM Toolbox 进行实时建图
# 前提：激光雷达驱动已安装并正常发布 /scan 话题

ros2 launch slam_toolbox online_async_launch.py \
   :=$(pwd)/params_mapper.yaml \
    sensor_frame:=base_scan \
    use_sim_time:=false
```

### 4.2 SLAM 参数配置文件

```yaml
# ~/robot_ws/src/rdk_deploy/robot_bringup/config/slam_params.yaml
# SLAM Toolbox 参数配置

slam_toolbox:
  ros__parameters:
    # 坐标系
    map_frame: map
    odom_frame: odom
    base_frame: base_link
    scan_topic: /scan
    
    # 地图分辨率（米/像素）
    resolution: 0.05
    
    # 地图尺寸（像素）
    map_size: 2048
    
    # 激光雷达参数
    max_range: 25.0          # 最大扫描距离（米）
    min_range: 0.2           # 最小扫描距离（米）
    
    # 定位模式
    mode: mapping            # mapping | localization
    
    # 扫描匹配参数
    transform_timeout: 0.2
    tf_buffer_duration: 30.
    
    # 地图更新频率
    map_update_interval: 1.0 # 秒
    
    # ICP 相关
    icp_match_epsilon: 0.01
    icp_correction_timeout: 0.1
```

### 4.3 建图启动 Launch 文件

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/robot_bringup/launch/slam_bringup.launch.py
# SLAM 建图启动文件

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """生成 SLAM 建图 Launch 描述"""
    
    # 获取包路径
    pkg_share = get_package_share_directory('robot_bringup')
    
    # 参数文件
    slam_params_file = os.path.join(pkg_share, 'config', 'slam_params.yaml')
    
    # 节点列表
    ld = LaunchDescription([
        # SLAM Toolbox 节点
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params_file],
            remappings=[
                ('/scan', '/scan'),      # 激光雷达话题
            ]
        ),
        
        # 机器人状态发布器
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{
                'robot_description': '',  # 从 xacro/urdf 加载
                'use_sim_time': False,
            }]
        ),
        
        # rviz2（可视化）
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(pkg_share, 'rviz', 'slam.rviz')],
        ),
    ])
    
    return ld
```

### 4.4 地图保存

```bash
# 在建图过程中或完成后，使用 map_saver 保存地图
# 默认保存到当前目录

ros2 run nav2_map_server map_saver_cli \
    -f ~/robot_ws/src/rdk_deploy/maps/my_map

# 参数说明：
# -f: 输出文件名前缀（不包含扩展名）
# 保存后生成：
#   ~/robot_ws/src/rdk_deploy/maps/my_map.pgm   # 地图图像
#   ~/robot_ws/src/rdk_deploy/maps/my_map.yaml  # 地图元数据

# 查看地图文件
cat ~/robot_ws/src/rdk_deploy/maps/my_map.yaml
```

地图元数据文件内容示例：

```yaml
# ~/robot_ws/src/rdk_deploy/maps/my_map.yaml
image: ./my_map.pgm
mode: trinary
resolution: 0.05        # 0.05 米/像素
origin: [-10.0, -10.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

### 4.5 建图后的地图编辑

```bash
# 使用 GIMP 或 ImageMagick 编辑 PGM 地图
# 例如去除噪点、填充空洞

# 安装 ImageMagick
sudo apt install -y imagemagick

# 查看地图信息
identify ~/robot_ws/src/rdk_deploy/maps/my_map.pgm

# 调整对比度
convert ~/robot_ws/src/rdk_deploy/maps/my_map.pgm -normalize ~/robot_ws/src/rdk_deploy/maps/my_map_fixed.pgm
```

---

## 5. Nav2 配置与调参

### 5.1 Nav2 参数文件概述

Nav2 的配置主要分为以下几个部分：

| 配置文件 | 内容 |
|---------|------|
| `nav2_params.yaml` | Nav2 核心参数（planner/controller/recovery/costmap/amcl） |
| `bt_navigator.yaml` | 行为树配置 |
| `ekf.yaml` | 扩展卡尔曼滤波（传感器融合） |

### 5.2 代价地图（Costmap）配置

```yaml
# ~/robot_ws/src/rdk_deploy/robot_bringup/config/nav2_params.yaml
# Nav2 核心参数文件

amcl:
  ros__parameters:
    use_sim_time: false
    alpha1: 0.2          # 里程计旋转噪声
    alpha2: 0.2          # 里程计平移噪声
    alpha3: 0.2          # 里程计旋转+平移噪声
    alpha4: 0.2          # 里程计平移+旋转噪声
    alpha5: 0.1          # 传感器噪声
    base_frame_id: base_link
    beam_skip_distance: 0.5
    beam_skip_error_threshold: 0.9
    beam_skip_threshold: 0.3
    global_frame_id: map
    lambda_short: 0.1
    laser_likelihood_max_dist: 2.0
    laser_max_range: 25.0
    laser_min_range: -1.0
    laser_model_type: likelihood_field
    max_beams: 30
    max_particles: 2000
    min_particles: 500
    odom_frame_id: odom
    pf_err: 0.1
    pf_z: 0.1
    recovery_alpha_fast: 0.0
    recovery_alpha_slow: 0.0
    resample_interval: 1
    robot_model_type: differential_drive
    scan_topic: /scan
    set_initial_pose: false
    theta_deviation: 0.2
    x_deviation: 0.2
    y_deviation: 0.2
    z_hit: 0.5
    z_max: 0.05
    z_rand: 0.5
    z_short: 0.05

# 全局代价地图
global_costmap:
  global_costmap:
    ros__parameters:
      use_sim_time: false
      robot_radius: 0.22           # 机器人半径（米）
      resolution: 0.05
      track_unknown_space: true
      plugins: ['static_layer', 'obstacle_layer', 'inflation_layer']
      
      # 静态地图层
      obstacle_layer:
        observer: 'costmap_observer'
        range: 3.0
      static_layer:
        plugin: 'nav2_costmap_2d::StaticLayer'
        map_subscribe_transient_local: true
      
      # 障碍物层
      obstacle_layer:
        plugin: 'nav2_costmap_2d::ObstacleLayer'
        enabled: true
        observation_sources: ['scan']
        scan:
          sensor: 'sensor_msgs::LaserScan'
          data_type: 'LaserScan'
          topic: '/scan'
          marking: true
          clearing: true
          max_obstacle_height: 2.0
          min_obstacle_height: 0.0
      
      # 膨胀层（障碍物缓冲）
      inflation_layer:
        plugin: 'nav2_costmap_2d::InflationLayer'
        enabled: true
        inflation_radius: 0.55     # 膨胀半径（米），机器人能避障的安全距离
        cost_scaling_factor: 1.0    # 代价缩放因子，越大障碍物影响范围越小

# 局部代价地图
local_costmap:
  local_costmap:
    ros__parameters:
      use_sim_time: false
      robot_radius: 0.22
      resolution: 0.05
      plugins: ['obstacle_layer', 'inflation_layer']
      obstacle_layer:
        plugin: 'nav2_costmap_2d::ObstacleLayer'
        enabled: true
        observation_sources: ['scan']
        scan:
          sensor: 'sensor_msgs::LaserScan'
          data_type: 'LaserScan'
          topic: '/scan'
          marking: true
          clearing: true
      inflation_layer:
        plugin: 'nav2_costmap_2d::InflationLayer'
        enabled: true
        inflation_radius: 0.35
        cost_scaling_factor: 1.0
      width: 6           # 局部地图宽度（米）
      height: 6         # 局部地图高度（米）
```

### 5.3 规划器（Planner）配置

```yaml
# 在 nav2_params.yaml 中继续添加

planner_server:
  ros__parameters:
    use_sim_time: false
    planner_plugins: ['GridBased']
    
    GridBased:
      plugin: 'nav2_smac_planner/SmacPlanner2D'
      # 采样分辨率
      downsample_costmap: 1
      downsampling_factor: 1
      
      # 地图范围
      motion_model_for_search: "DUALSEARCH"
      
      # 启发函数
      tolerance: 0.5                    # 目标点容差（米）
     heuristic_rasterize_size: 500
      allow_primitive_replanning: true
      
      # 搜索参数
      max_iterations: 100000
      max_on_approach_iterations: 1000
      terminal_checking_delay: 0.5
      
      # 代价权重
      neutral_cost: 50
      cost_factor: 3.0
```

### 5.4 控制器（Controller）配置

```yaml
# 在 nav2_params.yaml 中继续添加

controller_server:
  ros__parameters:
    use_sim_time: false
    controller_plugins: ['FollowPath']
    
    # DWB 局部控制器配置
    FollowPath:
      plugin: 'd      # DWB 局部控制器配置
      FollowPath:
        plugin: 'nav2_dwb_controller/DwbLocalPlanner'
        
        # 速度限制
        max_speed: 0.26          # 最大线速度（m/s）
        min_speed: 0.0
        
        # 加速度限制
        max_accel: 2.5
        max_decel: 2.5
        
        # 角度速度限制
        max_angular_vel: 1.5
        min_angular_vel: -1.5
        
        # 预测时间（局部规划的前向时间）
        time_ lookahead: 1.0
        
        # 关键参数
        vx_sample: 20
        vtheta_sample: 20
        
        # 评分函数权重
        scale: 1.0
        swar m_dist: 0.5
        
        # 局部路径搜索范围
        sim_time: 1.5
        linear_granularity: 0.05
        angular_granularity: 0.025
        
        # 代价函数权重
        path_dist_bias: 32.0   # 路径跟随权重
        goal_dist_bias: 24.0  # 目标接近权重
        occdist_scale: 1.0    # 障碍物避让权重

### 5.5 恢复器（Recovery）配置

```yaml
# 在 nav2_params.yaml 中继续添加

recoveries_server:
  ros__parameters:
    use_sim_time: false
    costmap_topic: local_costmap/costmap
    particle_topic: particle_cloud
    
    # 恢复行为列表（按顺序尝试）
    recoveries: [
      'spin',           # 原地旋转 360°
      'backup',         # 后退 0.3 米
      'wait'            # 等待
    ]
    
    # Spin 参数
    spin:
      plugin: 'nav2_recoveries/Spin'
      max_rotational_vel: 1.0
      min_rotational_vel: -1.0
      rotational_acc_lim: 2.0
    
    # Backup 参数
    backup:
      plugin: 'nav2_recoveries/BackUp'
      max_backup_dist: 0.3   # 后退距离（米）
      max_backup_speed: 0.2  # 后退速度（m/s）
```

### 5.6 AMCL 定位配置

```yaml
# AMCL 启动参数（见 nav2_params.yaml 中的 amcl 部分）
# 关键参数说明：

# robot_radius: 机器人碰撞半径，用于障碍物检测
# laser_max_range: 激光雷达最大范围
# min_particles / max_particles: 粒子数量范围
#   - 初始值应设大（如 2000）以快速收敛
#   - 稳定后可减小（如 500）以降低计算量
# alpha1~alpha5: 运动模型噪声参数
#   - alpha1: 旋转噪声（旋转的额外噪声）
#   - alpha2: 平移噪声（平移的额外噪声）
#   - alpha3: 旋转-平移耦合噪声
#   - alpha4: 平移-旋转耦合噪声
#   - alpha5: 传感器噪声

# 实际调参建议：
# 如果机器人打滑严重 → 增大 alpha1, alpha2
# 如果定位跳变 → 增大 min_particles
# 如果定位收敛慢 → 减小 initial_pose 的协方差
```

---

## 6. 实机导航启动

### 6.1 Nav2 bringup 启动文件

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/robot_bringup/launch/nav2_bringup.launch.py
# Nav2 导航启动文件

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """生成 Nav2 导航启动描述"""
    
    pkg_share = get_package_share_directory('robot_bringup')
    
    # 启动参数
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    autostart = LaunchConfiguration('autostart', default='true')
    
    # 导航参数文件
    nav2_params_file = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    map_file = os.path.join(pkg_share, 'maps', 'my_map.yaml')
    
    ld = LaunchDescription([
        # 声明启动参数
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='使用仿真时间'
        ),
        DeclareLaunchArgument(
            'autostart',
            default_value='true',
            description='自动启动 Nav2 生命周期节点'
        ),
        
        # ========== 地图服务器 ==========
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[{
                'yaml_filename': map_file,
                'use_sim_time': use_sim_time,
            }],
            remappings=[('/tf', '/tf'), ('/tf_static', '/tf_static')],
        ),
        
        # ========== AMCL 定位 ==========
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[nav2_params_file],
            remappings=[('/scan', '/scan')],
        ),
        
        # ========== Lifecycle Manager ==========
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager',
            output='screen',
            parameters=[{
                'autostart': autostart,
                'node_names': [
                    'map_server',
                    'amcl',
                    'controller_server',
                    'planner_server',
                    'recoveries_server',
                    'bt_navigator',
                ],
                'use_sim_time': use_sim_time,
            }],
        ),
        
        # ========== 全局规划器 ==========
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[nav2_params_file],
        ),
        
        # ========== 局部控制器 ==========
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[nav2_params_file],
            remappings=[
                ('/cmd_vel', '/cmd_vel'),
            ],
        ),
        
        # ========== 恢复行为 ==========
        Node(
            package='nav2_recoveries',
            executable='recoveries_node',
            name='recoveries_server',
            output='screen',
            parameters=[nav2_params_file],
        ),
        
        # ========== 行为树导航 ==========
        Node(
            package='nav2_behavior_tree',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[nav2_params_file],
        ),
    ])
    
    return ld
```

### 6.2 完整机器人启动 Launch

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/robot_bringup/launch/robot_bringup.launch.py
# 完整机器人启动文件 - 整合所有传感器和导航

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    """生成完整机器人启动描述"""
    
    pkg_share = get_package_share_directory('robot_bringup')
    
    # 延迟启动导航（等待传感器就绪）
    nav2_bringup = TimerAction(
        period=5.0,  # 等待 5 秒后启动
        actions=[
            Node(
                package='robot_bringup',
                executable='nav2_bringup',
                name='nav2_bringup',
                output='screen',
                parameters=[{
                    'use_sim_time': False,
                    'autostart': True,
                }],
            )
        ]
    )
    
    ld = LaunchDescription([
        # ========== 激光雷达 ==========
        Node(
            package='rplidar_ros',
            executable='rplidar_composition',
            name='rplidar',
            output='screen',
            parameters=[{
                'serial_port': '/dev/rplidar',
                'serial_baudrate': 115200,
                'frame_id': 'base_scan',
                'angle_compensate': True,
                'scan_mode': 'Standard',
            }],
        ),
        
        # ========== IMU ==========
        Node(
            package='imu_tools',
            executable='imu_filter_node',
            name='imu_filter',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'publish_topic': True,
                ' orientations': True,
                'angular_velocity': True,
                'linear_acceleration': True,
            }],
            remappings=[
                ('/imu/data_raw', '/imu/data_raw'),
            ],
        ),
        
        # ========== 编码器节点 ==========
        Node(
            package='robot_bringup',
            executable='encoder_reader',
            name='encoder_reader',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'ticks_per_meter': 4000,
                'wheel_separation': 0.4,
            }],
        ),
        
        # ========== 底盘驱动 ==========
        Node(
            package='robot_bringup',
            executable='chassis_driver',
            name='chassis_driver',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'wheel_separation': 0.4,
                'wheel_radius': 0.05,
                'uart_port': '/dev/ttyUSB1',
            }],
        ),
        
        # ========== 传感器融合（EKF） ==========
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node_odom',
            output='screen',
            parameters=[os.path.join(pkg_share, 'config', 'ekf.yaml')],
            remappings=[
                ('/odom', '/odom'),
                ('/imu/data', '/imu/data'),
            ],
        ),
        
        # ========== Nav2 导航（延迟启动） ==========
        nav2_bringup,
    ])
    
    return ld
```

### 6.3 启动导航系统

```bash
# 1. Source 工作空间
cd ~/robot_ws
source /opt/ros/humble/setup.bash
source install/setup.bash

# 2. 启动完整机器人系统
ros2 launch robot_bringup robot_bringup.launch.py

# 3. 在另一终端中启动 rviz2 可视化
ros2 run rviz2 rviz2 -d ~/robot_ws/src/rdk_deploy/robot_bringup/rviz/nav2_default.rviz

# 4. 查看所有话题
ros2 topic list

# 5. 查看节点图
ros2 run rqt_graph rqt_graph
```

### 6.4 发送导航目标点

#### 方法一：rviz2 手动导航

1. 在 rviz2 中添加 `Navigation2` 插件
2. 点击 `2D Pose Estimate` 设置机器人初始位置（拖动）
3. 点击 `2D Nav Goal` 设置目标点（拖动方向）

#### 方法二：命令行发送目标

```bash
# 设置初始位置（2D Pose Estimate）
ros2 topic pub /initialpose geometry_msgs/PoseWithCovarianceStamped \
    "{header: {stamp: {sec: 0}, frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}"

# 发送导航目标点
ros2 topic pub /goal_pose geometry_msgs/PoseStamped \
    "{header: {stamp: {sec: 0}, frame_id: 'map'}, pose: {position: {x: 5.0, y: 3.0, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.707, w: 0.707}}}"
```

#### 方法三：Python API 发送目标

```python
#!/usr/bin/env python3
# ~/robot_ws/src/rdk_deploy/robot_bringup/robot_bringup/nav2_goal_sender.py
# 使用 Python 发送 Nav2 导航目标点

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, NavigationTask
import math

class Nav2GoalSender(Node):
    """
    Nav2 导航目标点发送节点
    支持多点顺序导航、取消任务、查询状态
    """
    def __init__(self):
        super().__init__('nav2_goal_sender')
        
        # 初始化 Nav2 导航客户端
        self.nav = BasicNavigator()
        
        self.get_logger().info('Nav2 目标发送节点已初始化')
    
    def set_initial_pose(self, x: float, y: float, theta: float = 0.0):
        """
        设置机器人初始位置
        @param x: X 坐标（米）
        @param y: Y 坐标（米）
        @param theta: 偏航角（弧度）
        """
        initial_pose = PoseStamped()
        initial_pose.header.stamp = self.nav.get_clock().now().to_msg()
        initial_pose.header.frame_id = 'map'
        initial_pose.pose.position.x = x
        initial_pose.pose.position.y = y
        initial_pose.pose.position.z = 0.0
        
        # 四元数转换
        q = self._euler_to_quaternion(0.0, 0.0, theta)
        initial_pose.pose.orientation.x = q[0]
        initial_pose.pose.orientation.y = q[1]
        initial_pose.pose.orientation.z = q[2]
        initial_pose.pose.orientation.w = q[3]
        
        self.nav.setInitialPose(initial_pose)
        self.get_logger().info(f'初始位置已设置: ({x}, {y}, {theta})')
    
    def send_goal(self, x: float, y: float, theta: float = 0.0) -> bool:
        """
        发送导航目标点
        @param x: 目标 X 坐标（米）
        @param y: 目标 Y 坐标（米）
        @param theta: 目标朝向（弧度）
        @return: 是否成功开始导航
        """
        goal_pose = PoseStamped()
        goal_pose.header.stamp = self.nav.get_clock().now().to_msg()
        goal_pose.header.frame_id = 'map'
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.position.z = 0.0
        
        q = self._euler_to_quaternion(0.0, 0.0, theta)
        goal_pose.pose.orientation.x = q[0]
        goal_pose.pose.orientation.y = q[1]
        goal_pose.pose.orientation.z = q[2]
        goal_pose.pose.orientation.w = q[3]
        
        self.get_logger().info(f'发送目标点: ({x}, {y}, {theta})')
        
        # 等待导航完成（阻塞）
        result = self.nav.goToPose(goal_pose)
        
        return result
    
    def wait_for_navigation(self, timeout_sec: float = 300.0) -> bool:
        """
        等待导航完成
        @param timeout_sec: 超时时间（秒）
        @return: 是否成功到达目标
        """
        self.get_logger().info('等待导航完成...')
        
        i = 0
        while not self.nav.isTaskComplete():
            i += 1
            feedback = self.nav.getFeedback()
            if feedback:
                self.get_logger().debug(
                    f'剩余距离: {feedback.distance_remaining:.2f} 米'
                )
            
            if i > timeout_sec * 10:  # 10Hz 采样
                self.nav.cancelTask()
                self.get_logger().error('导航超时已取消')
                return False
            
            # 简单延时（实际使用 Timer）
            import time
            time.sleep(0.1)
        
        result = self.nav.getResult()
        self.get_logger().info(f'导航结果: {result}')
        
        return result == NavigationTask.SUCCEEDED
    
    def cancel_goal(self):
        """取消当前导航任务"""
        self.nav.cancelTask()
        self.get_logger().info('导航任务已取消')
    
    @staticmethod
    def _euler_to_quaternion(roll: float, pitch: float, yaw: float):
        """欧拉角转四元数"""
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        
        return [x, y, z, w]


def main():
    rclpy.init()
    
    nav_sender = Nav2GoalSender()
    
    # 等待 Nav2 完全启动
    nav_sender.nav.waitUntilNav2Active()
    
    # 示例：设置初始位置
    nav_sender.set_initial_pose(x=0.0, y=0.0, theta=0.0)
    
    # 示例：顺序导航到多个点
    waypoints = [
        (2.0, 0.0, 0.0),
        (4.0, 2.0, 1.57),
        (0.0, 0.0, 3.14),
    ]
    
    for i, (x, y, theta) in enumerate(waypoints):
        print(f'\n=== 前往第 {i+1} 个目标点: ({x}, {y}) ===')
        success = nav_sender.send_goal(x, y, theta)
        
        if success:
            arrived = nav_sender.wait_for_navigation(timeout_sec=120.0)
            print(f'第 {i+1} 个目标点: {"到达" if arrived else "失败"}')
        else:
            print(f'第 {i+1} 个目标点: 发送失败')
    
    # 取消导航
    # nav_sender.cancel_goal()
    
    nav_sender.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 7. ROS2 导航节点封装

### 7.1 扩展卡尔曼滤波配置

```yaml
# ~/robot_ws/src/rdk_deploy/robot_bringup/config/ekf.yaml
# 传感器融合配置 - 融合里程计和 IMU

ekf_filter_node_odom:
  ros__parameters:
    use_sim_time: false
    
    # 传感器频率
    sensor_timeout: 0.1
    
    # 里程计配置
    odom0: /odom
    odom0_config: [
      false, false, false,  # x, y, z 位置（里程计不直接给出位置）
      false, false, false,  # roll, pitch, yaw（里程计不给出姿态）
      true, true, true,   # vx, vy, vz 速度
      false, false, true   # vroll, vpitch, vyaw 角速度
    ]
    odom0_differential: false
    odom0_queue_size: 10
    
    # IMU 配置
    imu0: /imu/data
    imu0_config: [
      false, false, false,  # x, y, z 位置
      true, true, true,    # roll, pitch, yaw（使用 IMU 姿态）
      false, false, false,  # vx, vy, vz 速度
      true, true, true    # vroll, vpitch, vyaw 角速度
    ]
    imu0_differential: false
    imu0_queue_size: 10
    
    # 输出配置
    publish_tf: true
    publish_acceleration: false
    
    # 过程噪声（越大越信任传感器，越小越平滑）
    process_noise_covariance: [
      0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0.05, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0.03, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0.03, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0.025, 0, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0.025, 0, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0.04, 0, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0.01, 0, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.01, 0, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.01, 0, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.015, 0, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.015, 0,
      0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.015
    ]
```

### 7.2 CMakeLists.txt 配置

```cmake
# ~/robot_ws/src/rdk_deploy/robot_bringup/CMakeLists.txt

cmake_minimum_required(VERSION 3.8)
project(robot_bringup)

# 检查 C++ 标准
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# 编译选项
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find ROS2 依赖
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy_required_cmake)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav2_msgs REQUIRED)
find_package(nav2_simple_commander)
find_package(sensor_msgs REQUIRED)

# 安装 Python 模块
ament_python_install_package(${PROJECT_NAME})

# 安装 Python 可执行文件
install(PROGRAMS
  robot_bringup/chassis_driver.py
  robot_bringup/encoder_reader.py
  robot_bringup/nav2_goal_sender.py
  DESTINATION lib/${PROJECT_NAME}
)

# 安装 Launch 文件
install(DIRECTORY
  launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# 安装参数文件
install(DIRECTORY
  config/
  DESTINATION share/${PROJECT_NAME}/config
)

# 安装地图文件
install(DIRECTORY
  maps/
  DESTINATION share/${PROJECT_NAME}/maps
)

# 安装 rviz 配置
install(DIRECTORY
  rviz/
  DESTINATION share/${PROJECT_NAME}/rviz
)

ament_package()
```

### 7.3 package.xml 配置

```xml
<?xml version="1.0"?>
<!-- ~/robot_ws/src/rdk_deploy/robot_bringup/package.xml -->
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>robot_bringup</name>
  <version>1.0.0</version>
  <description>机器人导航启动包 - RDK-X5 实机部署</description>
  <maintainer email="your@email.com">Your Name</maintainer>
  <license>Apache-2.0</license>
  
  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>ament_cmake_python</buildtool_depend>
  
  <depend>rclcpp</depend>
  <depend>rclpy</depend>
  <depend>geometry_msgs</depend>
  <depend>nav2_msgs</depend>
  <depend>nav2_simple_commander</depend>
  <depend>nav2_bringup</depend>
  <depend>nav2_controller</depend>
  <depend>nav2_planner</depend>
  <depend>nav2_amcl</depend>
  <depend>robot_localization</depend>
  <depend>sensor_msgs</depend>
  <depend>std_msgs</depend>
  
  <exec_depend>python3-serial</exec_depend>
  <exec_depend>python3-rpi.gpio</exec_depend>
  
  <test_depend>ament_lint_auto</test_depend>
  <test_depend>ament_lint_common</test_depend>
  
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
```

---

## 8. 部署与验证

### 8.1 文件目录规划

所有部署文件统一放置在 `~/robot_ws/src/rdk_deploy/` 目录下：

```
~/robot_ws/src/rdk_deploy/
├── robot_bringup/              # 主启动包
│   ├── launch/
│   │   ├── robot_bringup.launch.py      # 完整启动
│   │   ├── nav2_bringup.launch.py        # Nav2 导航
│   │   └── slam_bringup.launch.py       # SLAM 建图
│   ├── config/
│   │   ├── nav2_params.yaml    # Nav2 核心参数
│   │   ├── slam_params.yaml    # SLAM 参数
│   │   └── ekf.yaml            # 传感器融合
│   ├── maps/
│   │   ├── my_map.pgm
│   │   └── my_map.yaml
│   ├── rviz/
│   │   ├── nav2_default.rviz
│   │   └── slam.rviz
│   ├── robot_bringup/
│   │   ├── chassis_driver.py   # 底盘驱动
│   │   ├── encoder_reader.py   # 编码器读取
│   │   └── nav2_goal_sender.py # 导航目标发送
│   ├── CMakeLists.txt
│   └── package.xml
└── scripts/                     # 辅助脚本
    ├── deploy_to_rdk.sh         # 部署脚本
    └── systemd_service.sh       # 开机自启脚本
```

### 8.2 rsync/SSH 部署

```bash
#!/bin/bash
# ~/robot_ws/src/rdk_deploy/scripts/deploy_to_rdk.sh
# 将代码部署到 RDK-X5 开发板

# RDK-X5 开发板 IP（根据实际修改）
RDK_HOST="192.168.1.101"
RDK_USER="root"
RDK_PORT="22"

# 源码目录（主机）
LOCAL_SRC="~/robot_ws/src/rdk_deploy"
# 目标目录（RDK-X5）
REMOTE_DEST="/root/robot_ws/src/rdk_deploy"

echo "=== 部署到 RDK-X5 (${RDK_HOST}) ==="

# 方式一：rsync 同步（推荐，只同步差异）
rsync -avz --progress \
    -e "ssh -p ${RDK_PORT}" \
    --exclude '*.pyc' \
    --exclude '__pycache__' \
    --exclude 'install' \
    --exclude 'build' \
    --exclude 'log' \
    "${LOCAL_SRC}/" \
    "${RDK_USER}@${RDK_HOST}:${REMOTE_DEST}/"

# 方式二：scp 完整复制
# scp -r -P ${RDK_PORT} ~/robot_ws/src/rdk_deploy ${RDK_USER}@${RDK_HOST}:/root/robot_ws/src/

echo "=== 部署完成 ==="
echo "在 RDK-X5 上执行以下命令编译："
echo "  cd ~/robot_ws"
echo "  source /opt/ros/humble/setup.bash"
echo "  colcon build --packages-select robot_bringup"
echo "  source install/setup.bash"
```

### 8.3 systemd 开机自启

```bash
#!/bin/bash
# ~/robot_ws/src/rdk_deploy/scripts/systemd_service.sh
# 创建 systemd 服务，实现开机自启

SERVICE_NAME="robot-nav"
SERVICE_USER="root"
WORK_DIR="/root/robot_ws"
LAUNCH_FILE="robot_bringup/launch/robot_bringup.launch.py"

# 创建 systemd 服务文件
sudo bash -c "cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Robot Navigation System
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${WORK_DIR}
Environment=\"ROS_DOMAIN_ID=42\"
ExecStart=/bin/bash -c 'source /opt/ros/humble/setup.bash && source ${WORK_DIR}/install/setup.bash && ros2 launch ${LAUNCH_FILE}'
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"

# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

# 启动/停止/状态查看
sudo systemctl start ${SERVICE_NAME}
sudo systemctl stop ${SERVICE_NAME}
sudo systemctl status ${SERVICE_NAME}

# 查看日志
journalctl -u ${SERVICE_NAME} -f
```

### 8.4 导航性能评估

```bash
# 1. 查看导航状态
ros2 action list
ros2 action info /navigate_to_pose

# 2. 实时监控导航延迟
ros2 topic hz /navigate_to_pose/_action/status

# 3. 测量导航成功率
# 使用 nav2_tests 或自定义脚本统计

# 4. 查看规划路径质量
ros2 run nav2_util execute_service /compute_path_to_pose

# 5. 性能指标
# - 规划时间（planning_time）：应 < 1 秒
# - 控制频率（control frequency）：应稳定在 10Hz+
# - 恢复次数（recovery count）：正常应 < 3 次
# - 到达精度（goal tolerance）：应 < 0.3 米
```

---

## 9. 常见问题排查

### 9.1 激光雷达相关

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| `/scan` 话题无数据 | USB 权限不足 | 添加 udev 规则，检查 `/dev/ttyUSB*` |
| 激光数据跳变 | 雷达转速不稳 | 检查供电（USB 供电不足用外接电源） |
| 地图扭曲/变形 | 激光帧率低或 TF 不正确 | 检查 `/scan` 频率，确保 base_link → laser frame 正确 |

```bash
# 排查激光雷达
ls -l /dev/rplidar  # 检查设备节点
ros2 topic hz /scan  # 查看话题频率（应为 5-10Hz）
ros2 run rqt_graph rqt_graph  # 查看节点连接
```

### 9.2 定位相关

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 机器人位置跳变 | AMCL 粒子数过少或噪声参数过大 | 增加 `min_particles`，减小 `alpha*` |
| 定位收敛慢 | 初始位置不准确 | 使用 rviz2 `2D Pose Estimate` 重新标定 |
| 长期漂移 | 里程计累积误差 | 检查编码器，安装 IMU 融合 |

```bash
# 查看 AMCL 粒子分布
ros2 topic echo /particle_cloud --once

# 重置 AMCL
ros2 service call /reset_localization std_srvs/srv/Empty
```

### 9.3 导航执行相关

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 机器人不动 | `/cmd_vel` 未到达底盘 | 检查底盘驱动节点是否正常 |
| 机器人绕圈 | 控制器参数不当 | 调低 `path_dist_bias`，调高 `vx_sample` |
| 无法通过窄门 | inflation_radius 过大 | 减小 `inflation_layer.inflation_radius` |
| 卡在障碍物边 | costmap 膨胀不够 | 增大 `inflation_radius` |

```bash
# 排查控制器
ros2 topic echo /cmd_vel  # 查看速度指令
ros2 run rqt_reconfigure rqt_reconfigure  # 动态调参

# 查看代价地图
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=${MAP_FILE}
```

### 9.4 网络通信

```bash
# 确保主机和 RDK-X5 在同一网段
# 设置 ROS_DOMAIN_ID（避免多机器人干扰）
export ROS_DOMAIN_ID=42

# 测试网络连通性
ping 192.168.1.101

# 测试 ROS2 话题通信
# 主机端：
ros2 topic list
# RDK-X5 端：
ros2 topic list
# 两边话题应一致
```

---

## 练习题

### 基础题

**1. Nav2 与 ROS Navigation Stack 的核心区别是什么？**

**2. 在 RDK-X5 上部署 Nav2，需要安装哪些 ROS2 功能包？请列出至少 5 个。**

**3. 请说明差速轮机器人的运动学模型，并写出左右轮速度与机器人线速度/角速度的关系式。**

**4. 代价地图（Costmap）的膨胀层（Inflation Layer）的作用是什么？`inflation_radius` 参数过大或过小会有什么影响？**

**5. AMCL 定位中，`alpha1` ~ `alpha5` 参数分别代表什么噪声？**

### 进阶题

**6. 请编写一个 launch 文件，同时启动激光雷达、底盘驱动、IMU 融合和 Nav2 导航系统。**

**7. 假设机器人在导航过程中经常卡在障碍物边缘，请分析可能的原因，并给出至少 3 条调参建议。**

**8. 请说明如何通过 `robot_localization` 包实现 IMU 和里程计的传感器融合，并解释 `odom0_config` 和 `imu0_config` 中每个布尔值的含义。**

**9. 在 SLAM 建图时，地图出现明显扭曲变形，请列出排查步骤。**

### 实战题

**10. 编写 Python 脚本，实现以下功能：**
- 连接
 Nav2 后自动按顺序导航到 3 个预设目标点，并打印每个目标点的到达结果。

**11.（选做）使用 systemd 在 RDK-X5 上配置 Nav2 开机自启，并验证服务状态。**

---

## 答案

### 基础题答案

**1. Nav2 与 ROS Navigation Stack 的核心区别**

| 区别点 | ROS Navigation Stack | Nav2 |
|--------|---------------------|------|
| 框架 | 简单状态机 | 行为树（Behavior Tree）驱动 |
| 扩展性 | 插件少 | 全模块插件化（Planner/Controller/Costmap） |
| 恢复策略 | 固定 3 种 | 可配置行为树，灵活扩展 |
| 生命周期 | 无 | Lifecycle Manager 管理节点状态 |
| ROS 版本 | ROS1 | ROS2 Humble/Iron/Jazzy |
| 多机器人 | 不支持 | 原生支持 |

**2. ROS2 功能包**

```bash
sudo apt install -y \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-nav2-bringup \
    ros-humble-slam-toolbox \
    ros-humble-map-server \
    ros-humble-amcl \
    ros-humble-robot-localization \
    ros-humble-robot-state-publisher \
    ros-humble-joint-state-publisher \
    ros-humble-nav2-controller \
    ros-humble-nav2-planner \
    ros-humble-nav2-recoveries
```

**3. 差速轮运动学模型**

```
v_left  = v_x - (d / 2) × ω
v_right = v_x + (d / 2) × ω
```

其中 `v_x` 为机器人前进线速度（m/s），`ω` 为绕 z 轴角速度（rad/s），`d` 为左右轮中心间距（米）。

反解：
```
v_x  = (v_left + v_right) / 2
ω    = (v_right - v_left) / d
```

**4. 膨胀层（Inflation Layer）作用**

在代价地图中，将每个障碍物单元的代价值向外扩散，形成一个安全缓冲区。

- `inflation_radius` 过**大**：机器人离障碍物很远就开始绕行，导航路径保守，可能无法通过狭窄通道
- `inflation_radius` 过**小**：机器人距离障碍物很近才避障，容易发生碰撞或卡住

**5. AMCL alpha 参数含义**

| 参数 | 含义 |
|------|------|
| `alpha1` | 里程计旋转噪声（旋转时产生的额外角度误差） |
| `alpha2` | 里程计平移噪声（平移时产生的额外位置误差） |
| `alpha3` | 里程计旋转-平移耦合噪声 |
| `alpha4` | 里程计平移-旋转耦合噪声 |
| `alpha5` | 传感器（激光）噪声 |

### 进阶题答案

**6. Launch 文件示例**

```python
#!/usr/bin/env python3
# robot_full_bringup.launch.py

from launch import LaunchDescription
from launch_ros.actions import Node, TimerAction

def generate_launch_description():
    return LaunchDescription([
        # 激光雷达
        Node(package='rplidar_ros', executable='rplidar_composition', name='rplidar'),
        
        # 底盘驱动
        Node(package='robot_bringup', executable='chassis_driver', name='chassis_driver'),
        
        # 编码器
        Node(package='robot_bringup', executable='encoder_reader', name='encoder_reader'),
        
        # IMU 融合（延迟 3 秒启动）
        TimerAction(period=3.0, actions=[
            Node(package='robot_localization', executable='ekf_node', name='ekf_filter_node'),
        ]),
        
        # Nav2 导航（延迟 5 秒启动）
        TimerAction(period=5.0, actions=[
            Node(package='robot_bringup', executable='nav2_bringup', name='nav2_bringup'),
        ]),
    ])
```

**7. 卡在障碍物边缘的调参建议**

| 方向 | 建议参数调整 |
|------|-------------|
| 膨胀层 | 增大 `inflation_layer.inflation_radius`（如 0.35 → 0.55） |
| 控制器 | 减小 `path_dist_bias`（降低路径紧贴度权重） |
| 控制器 | 增大 `min_obstacle_dist`（如果 DWB 支持） |
| 代价地图 | 增大 `cost_scaling_factor`（使膨胀区域过渡更平滑） |
| 局部地图 | 增大局部地图 `inflation_radius` |
| 恢复行为 | 添加 `wait` 恢复行为（让机器人等待后重新规划） |

**8. robot_localization 传感器融合**

`ekf.yaml` 中的配置项含义（以 `odom0_config` 为例，布尔数组顺序为 `[x, y, z, roll, pitch, yaw, vx, vy, vz, vroll, vpitch, vyaw]`）：

- `true` 表示使用该数据，`false` 表示不使用
- 对于里程计：通常使用速度项 `[false,false,false, false,false,false, true,true,true, false,false,true]`（vx, vy, vz, vyaw）
- 对于 IMU：通常使用姿态和角速度 `[false,false,false, true,true,true, false,false,false, true,true,true]`

融合效果：EKF 综合里程计的累积位移和 IMU 的瞬时姿态，提供更稳定的 `odom → base_link` 变换。

**9. 地图扭曲变形排查步骤**

1. **检查激光雷达**：确保 `/scan` 话题数据稳定，频率正常（5-10Hz）
2. **检查 TF 变换**：`base_link` → `base_scan` 的静态 TF 是否正确（距离和角度）
3. **检查传感器同步**：激光数据时间戳与里程计时间戳是否同步
4. **检查编码器**：里程计输出是否平滑，无突变
5. **调整 SLAM 参数**：减小 `max_iterations`，增大 `transform_timeout`
6. **降低机器人移动速度**：SLAM 时匀速缓慢移动效果更好

### 实战题答案

**10. Python 多点导航脚本**

```python
#!/usr/bin/env python3
# nav2_multi_goal.py - 顺序导航到多个目标点

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, NavigationTask
import math

def euler_to_quaternion(roll, pitch, yaw):
    """欧拉角转四元数"""
    cy, sy = math.cos(yaw/2), math.sin(yaw/2)
    cp, sp = math.cos(pitch/2), math.sin(pitch/2)
    cr, sr = math.cos(roll/2), math.sin(roll/2)
    return [sr*cp*cy - cr*sp*sy,  # x
            cr*sp*cy + sr*cp*sy,  # y
            cr*cp*sy - sr*sp*cy,  # z
            cr*cp*cy + sr*sp*sy]  # w

def make_pose(nav, x, y, yaw):
    """创建 PoseStamped 目标"""
    pose = PoseStamped()
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.header.frame_id = 'map'
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = 0.0
    q = euler_to_quaternion(0.0, 0.0, yaw)
    pose.pose.orientation.x, pose.pose.orientation.y = q[0], q[1]
    pose.pose.orientation.z, pose.pose.orientation.w = q[2], q[3]
    return pose

def main():
    rclpy.init()
    nav = BasicNavigator()
    
    # 等待 Nav2 就绪
    nav.waitUntilNav2Active()
    print('[INFO] Nav2 已就绪')
    
    # 设置初始位置
    nav.setInitialPose(make_pose(nav, 0.0, 0.0, 0.0))
    
    # 多点列表
    goals = [
        (2.0, 0.0, 0.0),
        (4.0, 2.0, 1.57),
        (0.0, 0.0, 3.14),
    ]
    
    for i, (x, y, yaw) in enumerate(goals):
        print(f'\n=== 前往目标 {i+1}: ({x}, {y}) ===')
        nav.goToPose(make_pose(nav, x, y, yaw))
        
        # 轮询等待
        while not nav.isTaskComplete():
            feedback = nav.getFeedback()
            if feedback:
                print(f'  剩余距离: {feedback.distance_remaining:.2f}m', end='\r')
        
        result = nav.getResult()
        status = '✓ 到达' if result == NavigationTask.SUCCEEDED else '✗ 失败'
        print(f'\n目标 {i+1}: {status}')
    
    print('\n[INFO] 全部任务完成')
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

**11. systemd 开机自启**

```bash
# 创建服务文件
sudo nano /etc/systemd/system/robot-nav.service

# 内容：
# [Unit]
# Description=Robot Navigation Service
# After=network.target
# [Service]
# Type=simple
# ExecStart=/bin/bash -c 'source /opt/ros/humble/setup.bash && source ~/robot_ws/install/setup.bash && ros2 launch robot_bringup robot_bringup.launch.py'
# Restart=on-failure
# [Install]
# WantedBy=multi-user.target

# 启用并启动
sudo systemctl daemon-reload
sudo systemctl enable robot-nav
sudo systemctl start robot-nav
sudo systemctl status robot-nav
```

---

## 参考资料

- [Nav2 官方文档](https://navigation.ros.org/)
- [d-robotics.github.io/rdk_doc](https://d-robotics.github.io/rdk_doc/) - 地平线 RDK-X5 官方文档
- [ROS2 Humble 安装指南](https://docs.ros.org/en/humble/Installation.html)
- [SLAM Toolbox 文档](https://github.com/SteveMacenski/slam_toolbox)
- [robot_localization 文档](http://docs.ros.org/en/noetic/api/robot_localization/html/index.html)
- [Nav2 参数调优指南](https://navigation.ros.org/tutorials/docs/tuning_nav2_params.html)

---

> **Last updated**: 2026-03-24
> **Maintainer**: every-embodied-course team
