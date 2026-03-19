# 08-3 2D SLAM真实硬件实战

> **前置课程**：08-2 2D SLAM仿真实战
> **后续课程**：08-4 3D SLAM技术概述

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：本节将带领大家将SLAM技术从仿真环境迁移到真实硬件平台。我们将详细介绍硬件平台的选型与搭建、ROS2驱动配置、SLAM算法部署以及地图构建的完整实操流程。通过本节课程，你将掌握在真实机器人上运行2D SLAM系统的全部技能。

---

## 1. 硬件平台搭建

在真实机器人上运行2D SLAM系统，需要精心选择和配置硬件平台。本节将介绍主流的机器人硬件方案，包括传感器选型、计算平台和机器人底盘。

### 1.1 典型硬件架构

一个完整的2D SLAM机器人系统通常包含以下组件：

```
┌─────────────────────────────────────────────────────────────┐
│                      机器人系统架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  激光雷达   │    │   轮式里程计  │    │    IMU     │     │
│  │ RPLIDAR A1  │    │   电机编码器  │    │   MPU6050  │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                 │                 │             │
│         ▼                 ▼                 ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   传感器融合层                        │   │
│  │              (Robot Localization)                   │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    SLAM层                            │   │
│  │           (Gmapping / Cartographer)                  │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   导航层                              │   │
│  │     (Navigation2 / MoveBase)                        │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                            │                                │
│                            ▼                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   运动控制   │    │   路径规划   │    │  障碍物检测  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   计算平台                            │   │
│  │         (Jetson Nano / Raspberry Pi 4)              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 激光雷达选型

激光雷达是2D SLAM的核心传感器，其性能直接影响SLAM效果。以下是主流单线激光雷达的对比：

| 型号 | 测距范围 | 角度分辨率 | 扫描频率 | 精度 | 价格区间 | 适用场景 |
|------|----------|------------|----------|------|----------|----------|
| RPLIDAR A1 | 0.15-12m | 1° | 5.5Hz | ±1cm | ¥300-400 | 入门级、教育 |
| RPLIDAR A2 | 0.15-16m | 0.9° | 10Hz | ±1cm | ¥600-800 | 实验室、DIY |
| RPLIDAR S1 | 0.05-40m | 0.5° | 10Hz | ±2cm | ¥1500-2000 | 室内大场景 |
| YDLIDAR X4 | 0.1-10m | 0.5° | 5-8Hz | ±2cm | ¥200-300 | 入门级、性价比 |

**推荐配置**：对于学习和实验室使用，推荐使用**RPLIDAR A2**或**YDLIDAR X4**，两者都具有良好的性价比和ROS2原生支持。

### 1.3 计算平台选型

计算平台需要运行ROS2、SLAM算法和导航堆栈，对CPU和内存有一定要求：

| 平台 | CPU | 内存 | 功耗 | 特点 | 推荐场景 |
|------|-----|------|------|------|----------|
| Raspberry Pi 4 | 4x Cortex-A72 | 4-8GB | 5-7W | 成本低、社区活跃 | 学习、轻量级 |
| Jetson Nano | 4x Cortex-A57 | 4GB | 5-10W | GPU加速、AI支持 | 视觉SLAM |
| Jetson Orin Nano | 6x ARM Cortex-A78AE | 4-8GB | 7-15W | 强GPU、AI性能 | 复杂AI应用 |
| Intel NUC | i3/i5/i7 | 8-32GB | 15-28W | x86架构、性能强 | 实验室研究 |

**推荐配置**：对于2D SLAM应用，**Raspberry Pi 4 (4GB)** 或 **Jetson Nano** 足以满足需求。如果需要运行更复杂的算法或视觉SLAM，推荐使用**Jetson Orin Nano**。

### 1.4 机器人底盘

机器人底盘需要提供运动学和里程计信息。常见的方案包括：

**成熟产品**：

| 型号 | 尺寸 | 驱动方式 | 载重 | 特点 |
|------|------|----------|------|------|
| TurtleBot3 Burger | 138x178x150mm | 差速 | 5kg | 开源、ROS原生支持 |
| 履带底盘 | 可定制 | 履带 | 10-50kg | 越障能力强 |
| 麦克纳姆轮底盘 | 可定制 | 麦克纳姆轮 | 10-30kg | 全向移动 |

**DIY方案**：

对于动手能力强的学习者，可以使用以下方案DIY底盘：
- 两轮差速方案：使用直流减速电机+轮子
- 阿克曼转向方案：使用舵机+直流电机
- 四轮驱动方案：使用4个TT电机或带编码器的电机

### 1.5 硬件连接示意图

典型的硬件连接方式如下：

```
                    ┌──────────────────┐
                    │   12V/5V 电源    │
                    └────────┬─────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌────────────┐   ┌────────────┐   ┌────────────┐
    │  激光雷达  │   │  计算平台   │   │  电机驱动  │
    │  (UART/    │   │  (USB/     │   │  (PWM/     │
    │   USB)     │   │   网口)    │   │   CAN)     │
    └──────┬─────┘   └──────┬─────┘   └──────┬─────┘
           │                 │                 │
           │    USB/RS485    │        ┌────────┘
           │                 │        │
           │                 │        ▼
           │                 │  ┌────────────┐
           │                 │  │   直流电机  │
           │                 │  │ + 编码器   │
           │                 │  └────────────┘
           │                 │
           │                 │  ┌────────────┐
           │                 │  │   IMU模块   │
           └─────────────────┤  │ (I2C/SPI)  │
                             │  └────────────┘
                             │
```

---

## 2. ROS2驱动配置

完成硬件平台搭建后，需要配置相应的ROS2驱动。本节将详细介绍各类传感器的驱动安装和配置方法。

### 2.1 激光雷达驱动配置

#### 2.1.1 RPLIDAR驱动安装

RPLIDAR是思岚科技推出的低成本激光雷达，ROS2有官方支持包。

**安装步骤**：

```bash
# 创建ROS2工作空间
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws

# 克隆RPLIDAR驱动
git clone https://github.com/Slamtec/rplidar_ros.git src/rplidar_ros

# 编译驱动
source /opt/ros/humble/setup.bash
colcon build --packages-select rplidar_ros

# 刷新环境
source install/setup.bash
```

**启动驱动**：

```bash
# 启动RPLIDAR A1/A2
ros2 launch rplidar_ros rplidar_a1.launch.py

# 或者使用命令行方式
ros2 run rplidar_ros rplidar.launch.py
```

**验证数据**：

```bash
# 查看话题
ros2 topic list

# 应该看到 /scan 话题

# 查看激光雷达数据
ros2 topic echo /scan
```

#### 2.1.2 YDLIDAR驱动安装

YDLIDAR是EAI公司推出的激光雷达，性价比高。

**安装步骤**：

```bash
cd ~/ros2_ws/src

# 克隆YDLIDAR驱动
git clone https://github.com/YDLIDAR/ydlidar_ros2.git src/ydlidar_ros2

# 编译
colcon build --packages-select ydlidar_ros2_driver

# 刷新环境
source ~/ros2_ws/install/setup.bash
```

**配置YDLIDAR X4**：

```bash
# 创建启动文件配置
mkdir -p ~/robot_config/launch
```

```yaml
# ~/robot_config/launch/ydlidar_x4.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ydlidar_ros2_driver',
            executable='ydlidar_ros2_driver',
            name='ydlidar_driver',
            output='screen',
            parameters=[{
                'port': '/dev/ttyUSB0',
                'baudrate': 115200,
                'frame_id': 'laser_link',
                'angle_min': -180.0,
                'angle_max': 180.0,
                'range_min': 0.1,
                'range_max': 10.0,
                'scan_frequency': 5.0,
            }]
        ),
    ])
```

**启动YDLIDAR**：

```bash
# 给予串口权限
sudo chmod 777 /dev/ttyUSB0

# 启动驱动
ros2 launch ~/robot_config/launch/ydlidar_x4.launch.py
```

### 2.2 轮式里程计配置

轮式里程计通过电机编码器计算机器人的位移和角度，是SLAM系统的重要输入。

#### 2.2.1 编码器原理

机器人底盘通常配备编码器，常见类型包括：

| 类型 | 特点 | 精度 |
|------|------|------|
| 光电编码器 | 非接触、精度高 | 较高 |
| 霍尔编码器 | 成本低、耐用 | 中等 |
| 磁编码器 | 抗干扰、寿命长 | 中等 |

**里程计计算公式**：

对于两轮差速机器人，里程计计算如下：

$$
\begin{aligned}
v &= \frac{v_r + v_l}{2} \\
\omega &= \frac{v_r - v_l}{L} \\
\Delta x &= v \cdot \Delta t \cdot \cos(\theta) \\
\Delta y &= v \cdot \Delta t \cdot \sin(\theta) \\
\Delta \theta &= \omega \cdot \Delta t
\end{aligned}
$$

其中：
- $v_r, v_l$ 为左右轮速度
- $L$ 为轮间距
- $\theta$ 为机器人航向角

#### 2.2.2 ROS2里程计发布

如果使用TurtleBot3等成熟底盘，里程计由底层控制器发布：

```bash
# TurtleBot3 启动
ros2 launch turtlebot3_bringup robot.launch.py
```

对于DIY底盘，需要创建里程计发布节点：

```python
# odometry_publisher.py
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf_transformations
import tf2_ros
import math

class OdometryPublisher(Node):
    def __init__(self):
        super().__init__('odometry_publisher')
        
        # 订阅电机编码器话题（或直接读取串口）
        # 这里假设收到的是编码器脉冲数
        from std_msgs.msg import Float32MultiArray
        self.subscription = self.create_subscription(
            Float32MultiArray,
            '/motor_encoders',
            self.encoder_callback,
            10
        )
        
        # 发布里程计
        self.odom_pub = self.create_publisher(Odometry, '/odom', 50)
        
        # TF广播器
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        # 状态变量
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_time = self.get_clock().now()
        
        # 机器人参数
        self.wheel_radius = 0.033  # 轮子半径（米）
        self.ticks_per_rev = 360   # 每转脉冲数
        self.wheel_base = 0.160    # 轮间距（米）
        
    def encoder_callback(self, msg):
        # 解析编码器数据
        left_ticks = msg.data[0]
        right_ticks = msg.data[1]
        
        # 计算时间间隔
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        
        if dt <= 0:
            return
        
        # 计算速度（需要根据齿轮比和轮子直径调整）
        left_vel = (left_ticks / self.ticks_per_rev) * 2 * math.pi * self.wheel_radius / dt
        right_vel = (right_ticks / self.ticks_per_rev) * 2 * math.pi * self.wheel_radius / dt
        
        # 计算里程计
        v = (left_vel + right_vel) / 2.0
        omega = (right_vel - left_vel) / self.wheel_base
        
        self.x += v * dt * math.cos(self.theta)
        self.y += v * dt * math.sin(self.theta)
        self.theta += omega * dt
        
        # 规范化角度到[-pi, pi]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        
        # 发布里程计消息
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        
        q = tf_transformations.quaternion_from_euler(0, 0, self.theta)
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        
        odom.twist.twist.linear.x = v
        odom.twist.twist.angular.z = omega
        
        self.odom_pub.publish(odom)
        
        # 广播TF
        t = TransformStamped()
        t.header.stamp = odom.header.stamp
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation = odom.pose.pose.orientation
        self.tf_broadcaster.sendTransform(t)
        
        self.last_time = current_time


def main(args=None):
    rclpy.init(args=args)
    node = OdometryPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 2.3 IMU传感器配置

IMU（惯性测量单元）提供角速度和加速度信息，可以与里程计融合提高定位精度。

#### 2.3.1 常见IMU模块

| 型号 | 接口 | 陀螺仪 | 加速度计 | 价格 |
|------|------|--------|----------|------|
| MPU6050 | I2C | ±250-2000°/s | ±2-16g | ¥15-30 |
| MPU9250 | I2C/SPI | ±250-2000°/s | ±2-16g | ¥40-60 |
| BMI088 | I2C/SPI | ±2000°/s | ±24g | ¥60-80 |

#### 2.3.2 ROS2 IMU驱动

**安装imu_tools**：

```bash
# 安装IMU ROS2包
sudo apt-get install ros-humble-imu-tools ros-humble-rviz-imu-plugin
```

**使用RTIMULib**：

```bash
# 安装RTIMULib
cd ~/ros2_ws/src
git clone https://github.com/rtabs/rtabs_ros2_imu.git

colcon build --packages-select rtabs_ros2_imu
source ~/ros2_ws/install/setup.bash
```

**启动IMU**：

```bash
# 启动MPU6050
ros2 run rtabs_ros2_imu mpu6050
```

### 2.4 传感器融合配置

使用robot_localization包融合里程计和IMU数据，提高定位精度。

**安装**：

```bash
sudo apt-get install ros-humble-robot-localization
```

**配置**：

```yaml
# robot_localization.yaml
/robot_localization:
  ros__parameters:
    frequency: 50
    sensor_timeout: 0.1
    two_d_mode: true
    
    # 使用里程计
    odom0: /diffbot/robot_controller/odom
    odom0_config: [true, true, false,
                  false, false, true,
                  false, false, false,
                  false, false, false,
                  false, false, false]
    odom0_differential: false
    
    # 使用IMU
    imu0: /imu/data
    imu0_config: [false, false, false,
                  false, false, true,
                  false, false, false,
                  false, false, true,
                  false, false, false]
    imu0_differential: false
    
    process_noise_covariance: [0.05, 0.05, 999999.0, 0.05, 0.05, 999999.0, 999999.0, 999999.0, 999999.0, 0.05, 0.05, 0.05, 999999.0, 999999.0, 999999.0]
```

**启动融合节点**：

```bash
ros2 run robot_localization ekf_node --ros-args --params-file robot_localization.yaml
```

---

## 3. SLAM算法部署

本节将介绍在真实硬件上部署SLAM算法的方法，重点讲解Gmapping和Cartographer的配置。

### 3.1 Gmapping部署

Gmapping是ROS2中最常用的2D SLAM算法之一，基于粒子滤波器实现。

#### 3.1.1 安装Gmapping

```bash
# 安装Gmapping
sudo apt-get install ros-humble-slam-gmapping

# 或从源码编译
cd ~/ros2_ws/src
git clone https://github.com/ros-perception/slam_gmapping.git

colcon build --packages-select gmapping
source ~/ros2_ws/install/setup.bash
```

#### 3.1.2 配置启动文件

```yaml
# slam_gmapping.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # 声明参数
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    return LaunchDescription([
        # 启动Gmapping节点
        Node(
            package='slam_gmapping',
            executable='slam_gmapping',
            name='slam_gmapping',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'base_frame': 'base_link',
                'odom_frame': 'odom',
                'map_frame': 'map',
                'maxUrange': 16.0,
                'maxRange': 20.0,
                'sigma': 0.05,
                'kernelSize': 1,
                'lstep': 0.05,
                'angularUpdate': 0.05,
                'linearUpdate': 0.05,
                'resampleThreshold': 0.5,
                'particles': 100,
                'xmin': -10.0,
                'ymin': -10.0,
                'xmax': 10.0,
                'ymax': 10.0,
                'delta': 0.05,
            }],
            remappings=[
                ('/scan', '/scan'),
                ('/map', '/map'),
            ]
        ),
    ])
```

#### 3.1.3 启动SLAM

```bash
# 启动Gmapping
ros2 launch your_package slam_gmapping.launch.py

# 或者使用参数方式
ros2 run slam_gmapping slam_gmapping --ros-args -p use_sim_time:=false
```

### 3.2 Cartographer部署

Cartographer是Google开发的SLAM算法，支持2D和3D SLAM，精度高且支持实时回环检测。

#### 3.2.1 安装Cartographer

```bash
# 安装Cartographer
sudo apt-get install ros-humble-cartographer
sudo apt-get install ros-humble-cartographer-ros

# 或从源码编译（推荐）
cd ~/ros2_ws/src
git clone https://github.com/ros2/cartographer.git
git clone https://github.com/ros2/cartographer_ros.git

source /opt/ros/humble/setup.bash
colcon build --packages-select cartographer_ros
```

#### 3.2.2 配置Cartographer

```lua
-- cartographer.lua
include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "base_link",
  odom_frame = "odom",
  provide_odom_frame = true,
  use_odometry = true,
  use_laser_scan = true,
  use_multi_echo_laser_scan = false,
  num_point_clouds = 0,
}

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER_2D.min_range = 0.3
TRAJECTORY_BUILDER_2D.max_range = 30.0
TRAJECTORY_BUILDER_2D.missing_data_ray_height = 1.0
TRAJECTORY_BUILDER_2D.use_imu_data = true
TRAJECTORY_BUILDER_2D.use_odometry = true

return options
```

#### 3.2.3 配置Cartographer节点

```yaml
# cartographer.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer',
            output='screen',
            parameters=[{'use_sim_time': False}],
            arguments=[
                '-configuration_directory', '/path/to/config',
                '-configuration_basename', 'cartographer.lua'
            ],
            remappings=[
                ('scan', '/scan'),
                ('odom', '/odom'),
            ]
        ),
        
        # 启动OccupancyGridNode用于地图可视化
        Node(
            package='cartographer_ros',
            executable='occupancy_grid_node',
            name='occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
        ),
    ])
```

#### 3.2.4 运行Cartographer

```bash
# 启动Cartographer
ros2 launch cartographer_ros cartographer.launch.py \
    configuration_directory:=/path/to/config \
    configuration_basename:=cartographer.lua
```

---

## 4. 地图构建实操

本节将带领大家完成完整的地图构建实操流程，包括启动各个组件、遥控机器人构建地图以及保存地图。

### 4.1 完整启动流程

#### 4.1.1 创建启动脚本

为了简化操作，创建一个一键启动脚本：

```yaml
# ~/robot_slam/launch/full_slam.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    return LaunchDescription([
        # 1. 启动激光雷达驱动
        Node(
            package='ydlidar_ros2_driver',
            executable='ydlidar_ros2_driver',
            name='ydlidar_driver',
            output='screen',
            parameters=[{
                'port': '/dev/ttyUSB0',
                'baudrate': 115200,
                'frame_id': 'laser_link',
            }]
        ),
        
        # 2. 启动里程计/底盘驱动
        Node(
            package='turtlebot3_bringup',
            executable='robot.launch.py',
            name='turtlebot3_robot',
            output='screen',
        ),
        
        # 3. 启动IMU
        Node(
            package='mpu6050_driver',
            executable='mpu6050',
            name='mpu6050',
            output='screen',
        ),
        
        # 4. 启动传感器融合
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_localization',
            output='screen',
            parameters=['/path/to/robot_localization.yaml'],
        ),
        
        # 5. 启动SLAM算法 (Gmapping或Cartographer)
        Node(
            package='slam_gmapping',
            executable='slam_gmapping',
            name='slam_gmapping',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'base_frame': 'base_link',
                'odom_frame': 'odom',
                'map_frame': 'map',
                'maxUrange': 16.0,
                'delta': 0.05,
            }],
        ),
    ])
```

#### 4.1.2 启动命令

```bash
# 终端1: 启动完整SLAM系统
cd ~/robot_slam
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch launch/full_slam.launch.py

# 终端2: 启动键盘遥控
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 终端3: 启动RViz可视化
ros2 launch slam_toolbox online_sync_launch.py
# 或
rviz2 -d /path/to/slam.rviz
```

### 4.2 地图构建技巧

#### 4.2.1 遥控操作规范

在构建地图时，遥控机器人需要注意以下几点：

1. **缓慢移动**：保持低速移动（<0.3m/s），确保激光雷达数据稳定
2. **避免快速旋转**：快速旋转会导致地图匹配失败
3. **覆盖整个区域**：需要让机器人遍历整个需要建图的空间
4. **闭合回环**：让机器人经过已建图区域，帮助SLAM算法进行回环检测
5. **避免障碍物**：保持与障碍物的安全距离

#### 4.2.2 典型地图构建轨迹

```
                    ┌──────────────────┐
                    │                  │
                    │    ┌─────────┐   │
                    │    │         │   │
        ───────────▶│    │         │   │
        │           │    │         │   │
        │           │    └────┬────┘   │
        │           │         │        │
        │           │    ┌────┴────┐   │
        │           │    │         │   │
        │           │    │         │   │
        │           │    └─────────┘   │
        │           │                  │
        │           │                  │
        ▼           └──────────────────┘
        
建议路径：沿墙边走→S形遍历→闭合回环
```

### 4.3 地图保存

#### 4.3.1 保存地图

地图构建完成后，需要保存地图文件：

```bash
# 方法1: 使用map_saver
ros2 run nav2_map_server map_saver -f ~/maps/my_map

# 这会生成两个文件:
# ~/maps/my_map.yaml   - 地图元数据
# ~/maps/my_map.pgm   - 地图图像
```

#### 4.3.2 地图格式说明

**YAML文件**：

```yaml
# my_map.yaml
image: my_map.pgm
resolution: 0.050000
origin: [-10.000000, -10.000000, 0.000000]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
```

参数说明：
- `image`: 地图图像文件路径
- `resolution`: 地图分辨率（米/像素）
- `origin`: 地图原点坐标
- `occupied_thresh`: 占用阈值（>65%认为占用）
- `free_thresh`: 空闲阈值（<19.6%认为空闲）

### 4.4 地图加载与使用

#### 4.4.1 加载已有地图

```bash
# 启动地图服务器
ros2 run nav2_map_server map_server \
    --ros-args -p yaml_filename:=/path/to/map.yaml
```

#### 4.4.2 完整导航启动

```bash
# 启动导航2
ros2 launch nav2_bringup navigation_launch.py \
    map:=/path/to/map.yaml
```

---

## 5. 实战：完整SLAM系统搭建

本节将整合前面所学内容，搭建一个完整的2D SLAM系统。

### 5.1 系统配置

**硬件清单**：

| 组件 | 型号 | 数量 | 备注 |
|------|------|------|------|
| 计算平台 | Jetson Nano 4GB | 1 | 运行ROS2 |
| 激光雷达 | YDLIDAR X4 | 1 | 10m测距 |
| 底盘 | TurtleBot3 Burger | 1 | 差速驱动 |
| IMU | MPU6050 | 1 | 内置TB3 |
| 电源 | 12V 5000mAh | 1 | 锂电池 |

**软件环境**：
- Ubuntu 20.04 (Jetson版)
- ROS2 Humble
- SLAM: Gmapping + Cartographer

### 5.2 快速启动脚本

```bash
#!/bin/bash
# robot_slam_start.sh

# 1. 检查环境
echo "=== 检查ROS2环境 ==="
source /opt/ros/humble/setup.bash

# 2. 设置串口权限
echo "=== 设置串口权限 ==="
sudo chmod 777 /dev/ttyUSB0 2>/dev/null

# 3. 加载环境变量
source ~/ros2_ws/install/setup.bash
source ~/robot_ws/install/setup.bash

# 4. 启动机器人
echo "=== 启动机器人 ==="
ros2 launch turtlebot3_bringup robot.launch.py &

sleep 3

# 5. 启动激光雷达
echo "=== 启动激光雷达 ==="
ros2 launch ydlidar_ros2_driver ydlidar.launch.py &

sleep 2

# 6. 启动SLAM
echo "=== 启动SLAM ==="
ros2 launch slam_gmapping online_launch.py &

sleep 2

# 7. 启动RViz
echo "=== 启动RViz ==="
rviz2 -d ~/robot_ws/src/robot_slam/config/slam.rviz &

echo "=== 启动完成 ==="
echo "使用以下命令遥控机器人："
echo "ros2 run teleop_twist_keyboard teleop_twist_keyboard"
echo ""
echo "使用以下命令保存地图："
echo "ros2 run nav2_map_server map_saver -f ~/maps/my_map"
```

### 5.3 调试与优化

#### 5.3.1 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 激光雷达无数据 | 串口权限、波特率 | 检查/dev/ttyUSB0权限 |
| 里程计漂移 | 编码器精度、轮子打滑 | 检查轮胎、检查编码器 |
| 地图错位 | 运动太快、回环检测失败 | 减慢速度、手动闭合回环 |
| 定位丢失 | 传感器噪声、参数不当 | 调整SLAM参数 |

#### 5.3.2 参数调优

**Gmapping参数调整**：

```yaml
# 推荐参数配置
slam_gmapping:
  ros__parameters:
    # 粒子数：环境大时增加
    particles: 100
    
    # 更新间隔：越小越精确但更慢
    linearUpdate: 0.1
    angularUpdate: 0.05
    
    # 扫描匹配参数
    lstep: 0.05
    astep: 0.05
    srr: 0.1
    srt: 0.1
    str: 0.1
    stt: 0.1
    
    # 地图范围
    xmin: -20.0
    ymin: -20.0
    xmax: 20.0
    ymax: 20.0
```

**Cartographer参数调整**：

```lua
-- 推荐参数配置
TRAJECTORY_BUILDER_2D.min_range = 0.3
TRAJECTORY_BUILDER_2D.max_range = 20.0
TRAJECTORY_BUILDER_2D.missing_data_ray_height = 1.0
TRAJECTORY_BUILDER_2D.use_imu_data = true
TRAJECTORY_BUILDER_2D.use_odometry = true

-- 运动滤波器
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_diff = 0.1
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_diff = 0.1
```

---

## 练习题

### 选择题

1. 在2D SLAM系统中，以下哪个传感器不是必需的？
   - A) 激光雷达
   - B) IMU
   - C) 轮式里程计
   - D) 相机
   
   **答案：D**。相机是视觉SLAM的核心传感器，但对于2D激光SLAM不是必需的。激光雷达、里程计和IMU是2D SLAM的常用传感器组合。

2. RPLIDAR A2的扫描频率是多少？
   - A) 5.5Hz
   - B) 8Hz
   - C) 10Hz
   - D) 15Hz
   
   **答案：C**。RPLIDAR A2的扫描频率为10Hz，角度分辨率为0.9°。

3. Gmapping算法基于什么原理实现？
   - A) 图优化
   - B) 粒子滤波
   - C) 卡尔曼滤波
   - D) 深度学习
   
   **答案：B**。Gmapping基于RBPF（Rao-Blackwellized Particle Filter）粒子滤波算法实现。

4. 在ROS2中，激光雷达数据发布在哪个话题上？
   - A) /lidar_scan
   - B) /laser_scan
   - C) /scan
   - D) /range_scan
   
   **答案：C**。ROS2中激光雷达数据默认发布在`/scan`话题上，使用`sensor_msgs/LaserScan`消息类型。

5. 保存地图使用的命令是？
   - A) ros2 run map_server map_saver
   - B) ros2 run nav2_map_server map_saver
   - C) ros2 run slam_toolbox map_saver
   - D) ros2 run cartographer map_saver
   
   **答案：B**。在ROS2 Humble中，保存地图使用`nav2_map_server`包中的`map_saver`节点。

### 实践题

6. 配置YDLIDAR X4激光雷达驱动，并验证数据输出。
   
