# 09-3 AMCL真实硬件实战

> **前置课程**：09-2 AMCL仿真实战与参数调优
> **后续课程**：10-1 导航堆栈概述

**作者**：霍海杰 | **联系方式**：howe12@126.com

> **前置说明**：在前两节课程中，我们已经学习了AMCL的原理和仿真环境中的配置方法。本节将把目光投向真实硬件平台，详细讲解如何在实际的机器人上配置传感器驱动、加载地图、部署AMCL定位系统，并进行真实的定位实操。通过本节的学习，你将具备将AMCL从仿真环境迁移到真实机器人的能力。

---

## 1. 真实硬件平台概述

真实机器人平台与仿真环境有本质区别：传感器存在噪声、机械结构有误差、环境不可控。本节以典型的ROS2移动机器人为例，讲解硬件平台的组成和选型要点。

### 1.1 典型硬件平台组成

一个用于AMCL定位的完整机器人系统通常包含以下硬件组件：

| 组件 | 功能 | 选型要点 |
|------|------|----------|
| **计算平台** | 运行ROS2和定位算法 | Jetson Nano/Orin、树莓派、x86工控机 |
| **激光雷达** | 环境感知、障碍物检测 | 思岚A1/A2/A3、镭神C16、YDLIDAR |
| **IMU** | 姿态测量、运动辅助 | MPU6050、BMI088、CH110 |
| **电机编码器** | 里程计数据 | 光电编码器、磁编码器 |
| **运动控制器** | 电机驱动 | Arduino、STM32、电机驱动板 |
| **电源系统** | 供电 | 锂电池、稳压模块 |

```
┌─────────────────────────────────────────────────────────────────┐
│                      典型ROS2机器人硬件架构                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐                                            │
│   │   计算平台    │  Jetson Nano / x86工控机                    │
│   │  (ROS2主机)  │                                            │
│   └──────┬───────┘                                            │
│          │                                                    │
│   ┌──────┴───────┐    ┌──────────────┐    ┌──────────────┐   │
│   │  传感器接口   │◀──▶│   激光雷达   │    │     IMU      │   │
│   │  (USB/UART)  │    │  /scan话题   │    │  /imu话题    │   │
│   └──────┬───────┘    └──────────────┘    └──────────────┘   │
│          │                                                    │
│   ┌──────┴───────┐    ┌──────────────┐    ┌──────────────┐   │
│   │  运动控制器   │◀──▶│   左电机     │    │    右电机    │   │
│   │  /cmd_vel    │    │  编码器数据  │    │  编码器数据  │   │
│   └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 常见机器人平台推荐

对于学习AMCL定位，推荐以下几种常见的机器人平台：

**入门级**：
- TurtleBot4：内置ROS2支持，开箱即用
- ROS2经典教材推荐平台，社区资源丰富

**进阶级**：
- 自建两轮差速机器人：成本可控，定制性强
- 思岚ROS机器人平台：工业级品质

**研究级**：
- ClearPath Husky：全向移动，户外可用
- Boston Dynamics Spot：高性能，但成本较高

### 1.3 硬件连接要点

在连接硬件时，需要注意以下要点：

1. **激光雷达**：通常通过USB连接，发布`/scan`话题
2. **IMU**：通过I2C或USB连接，发布`/imu`话题
3. **编码器**：通过UART或GPIO连接，由运动控制器发布`/odom`话题
4. **运动控制器**：订阅`/cmd_vel`话题，输出电机PWM控制

---

## 2. ROS2驱动配置

ROS2驱动的正确配置是AMCL定位的前提。本节详细讲解各类传感器驱动的安装和配置方法。

### 2.1 激光雷达驱动

以思岚A1激光雷达为例，介绍ROS2驱动的安装和配置：

```bash
# 安装思岚A1雷达驱动
cd ~/ros2_ws/src
git clone https://github.com/Slamtec/sllidar_ros2.git
cd sllidar_ros2
git checkout humble

# 编译驱动
cd ~/ros2_ws
colcon build --packages-select sllidar_ros2
source install/setup.bash
```

**启动雷达节点**：

```bash
# 启动雷达节点
ros2 launch sllidar_ros2 sllidar_a1_launch.py
```

或手动启动：

```bash
ros2 run sllidar_ros2 sllidar_node --ros-args \
    -p serial_port:=/dev/ttyUSB0 \
    -p serial_baudrate:115200 \
    -p frame_id:=laser_link \
    -p angle_compensate:=true \
    -p scan_mode:=Standard
```

**验证雷达话题**：

```bash
# 查看雷达话题
ros2 topic list | grep scan

# 查看雷达数据
ros2 topic echo /scan

# 查看雷达频率
ros2 topic hz /scan
```

典型输出应显示激光扫描数据，包含角度和距离信息：

```yaml
header:
  stamp: 1234567890.123
  frame_id: laser_link
angle_min: 0.0
angle_max: 6.283185
angle_increment: 0.017453
range_min: 0.15
range_max: 12.0
ranges: [1.23, 1.45, 1.67, ...]
intensities: [100.0, 105.0, 98.0, ...]
```

### 2.2 IMU驱动

以MPU6050 IMU为例，介绍ROS2驱动配置：

```bash
# 安装MPU6050 ROS2驱动
cd ~/ros2_ws/src
git clone https://github.com/ika-rwth-aachen/imu_complementary_filter.git
git clone https://github.com/ros-drivers/imu_drivers.git

# 编译
cd ~/ros2_ws
colcon build --packages-select imu_complementary_filter imu_tools
source install/setup.bash
```

**配置udev规则**（使IMU设备有固定名称）：

```bash
# 查看IMU设备
ls -l /dev/ttyUSB*

# 创建udev规则
sudo nano /etc/udev/rules.d/99-imu.rules
```

添加以下内容：

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", \
    SYMLINK+="imu_serial", MODE="0666"
```

**启动IMU节点**：

```bash
ros2 run imu_driver imu_driver --ros-args \
    -p device:=/dev/imu_serial \
    -p frame_id:=imu_link
```

或使用互补滤波器融合数据：

```bash
ros2 launch imu_complementary_filter complementary_filter.launch.py
```

### 2.3 里程计驱动

里程计是AMCL定位的重要输入，需要正确配置。以下是一个典型的里程计驱动结构：

```python
# odometry_driver.py - 里程计驱动示例
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf_transformations
import math

class OdometryDriver(Node):
    def __init__(self):
        super().__init__('odometry_driver')
        
        # 机器人参数
        self.wheel_radius = 0.05  # 轮子半径 (m)
        self.wheel_base = 0.3     # 轮距 (m)
        
        # 状态变量
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_left_ticks = 0
        self.last_right_ticks = 0
        
        # 发布者
        self.odom_pub = self.create_publisher(Odometry, '/odom', 50)
        self.tf_broadcaster = self.TransformBroadcaster(self)
        
        # 定时器
        self.timer = self.create_timer(0.05, self.update_odometry)
        
        self.get_logger().info('Odometry driver started')
        
    def update_odometry(self):
        # 读取编码器数据（需要根据实际硬件实现）
        left_ticks = self.read_left_encoder()
        right_ticks = self.read_right_encoder()
        
        # 计算差值
        delta_left = left_ticks - self.last_left_ticks
        delta_right = right_ticks - self.last_right_ticks
        
        self.last_left_ticks = left_ticks
        self.last_right_ticks = right_ticks
        
        # 转换为米
        delta_left_m = delta_left * self.ticks_to_meters
        delta_right_m = delta_right * self.ticks_to_meters
        
        # 计算运动
        delta_x = (delta_left_m + delta_right_m) / 2.0 * math.cos(self.theta)
        delta_y = (delta_left_m + delta_right_m) / 2.0 * math.sin(self.theta)
        delta_theta = (delta_right_m - delta_left_m) / self.wheel_base
        
        # 更新位置
        self.x += delta_x
        self.y += delta_y
        self.theta += delta_theta
        
        # 发布Odometry消息
        odom = Odometry()
        odom.header.stamp = self.get_clock().now().to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        
        q = tf_transformations.quaternion_from_euler(0, 0, self.theta)
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        
        odom.twist.twist.linear.x = (delta_left_m + delta_right_m) / 2.0 / 0.05
        odom.twist.twist.angular.z = delta_theta / 0.05
        
        self.odom_pub.publish(odom)
        
    def read_left_encoder(self):
        # 实现编码器读取
        return 0
        
    def read_right_encoder(self):
        # 实现编码器读取
        return 0
        
    @property
    def ticks_to_meters(self):
        return 2.0 * math.pi * self.wheel_radius / 360.0

def main(args=None):
    rclpy.init(args=args)
    node = OdometryDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 2.4 坐标系配置

正确配置TF坐标系是定位的关键。机器人需要配置的坐标系关系：

```
map (地图坐标系)
    │
    └── odom (里程计坐标系)
            │
            └── base_link (机器人基座)
                    │
                    ├── laser_link (激光雷达)
                    └── imu_link (IMU)
```

**创建静态TF发布节点**：

```bash
# 启动静态TF发布
ros2 run tf2_ros static_transform_publisher \
    x y z yaw pitch roll \
    base_link laser_link
```

例如，如果激光雷达在机器人前方0.1米处：

```bash
ros2 run tf2_ros static_transform_publisher \
    0.1 0.0 0.2 0 0 0 \
    base_link laser_link
```

**验证坐标系**：

```bash
# 查看TF树
ros2 run tf2_tools view_frames

# 监听TF变换
ros2 run tf2_ros tf2_echo base_link laser_link

# 检查坐标系是否正确
ros2 topic echo /tf_static
```

---

## 3. 地图加载

AMCL定位需要预先构建好的地图。本节介绍地图的加载方法和格式转换。

### 3.1 地图格式

ROS2导航使用两种常见的地图格式：

**OccupancyGrid地图（2D栅格地图）**：
- `nav_msgs/OccupancyGrid`消息格式
- 包含元数据和栅格数据
- 用于导航和定位

**YAML配置文件**：

```yaml
# map.yaml
image: map.pgm
resolution: 0.05
origin: [0.0, 0.0, 0.0]
occupied_thresh: 0.65
free_thresh: 0.196
negate: 0
```

### 3.2 加载地图

使用`map_server`加载地图：

```bash
# 安装map_server
sudo apt install ros-humble-nav2-map-server

# 启动map_server加载地图
ros2 run nav2_map_server map_server \
    --ros-args -p yaml_filename:=/path/to/map.yaml
```

或使用launch文件：

```python
# map_server_launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            parameters=[{
                'yaml_filename': '/home/nx_ros/ros2_ws/maps/my_map.yaml',
                'topic': 'map',
                'frame_id': 'map'
            }]
        )
    ])
```

### 3.3 地图服务

map_server提供两个服务：

**获取地图**（`/map服务`）：

```bash
# 调用map服务
ros2 service call /map nav_msgs/srv/GetMap
```

**更改地图**（`/map服务`）：

```bash
ros2 service call /clear_unknown_cells nav_msgs/srv/ClearEntireMap
```

### 3.4 地图可视化

使用rviz2可视化地图：

```bash
ros2 run rviz2 rviz2 -d $(ros2 pkg share nav2_map_server)/rviz/map_server_example.rviz
```

或在rviz2中添加：
- `Map`类型显示项
- 话题选择`/map`
- 坐标系选择`map`

---

## 4. AMCL部署

本节详细介绍如何在真实机器人上启动和配置AMCL定位系统。

### 4.1 AMCL节点启动

使用nav2包中的AMCL启动：

```bash
# 安装AMCL
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup
```

**基础启动**：

```bash
ros2 launch nav2_bringup localization_launch.py \
    map:=/path/to/map.yaml \
    params_file:=/path/to/params.yaml
```

### 4.2 AMCL参数配置

创建AMCL参数文件：

```yaml
# amcl_params.yaml
amcl:
  ros__parameters:
    # 坐标系设置
    odom_frame_id: "odom"
    base_frame_id: "base_link"
    global_frame_id: "map"
    
    # 频率设置
    update_min_a: 0.1
    update_min_d: 0.1
    odom_dt_factor: 10.0
    
    # 粒子数设置
    initial_pose_x: 0.0
    initial_pose_y: 0.0
    initial_pose_a: 0.0
    initial_cov_xx: 0.5
    initial_cov_yy: 0.5
    initial_cov_aa: 0.5
    max_particles: 5000
    min_particles: 500
    
    # 模型参数
    laser_model_type: "likelihood_field"
    laser_min_range: 0.15
    laser_max_range: 12.0
    laser_max_beams: 30
    
    # 里程计模型参数
    odom_model_type: "diff-corrected"
    odom_alpha1: 0.2
    odom_alpha2: 0.2
    odom_alpha3: 0.2
    odom_alpha4: 0.2
    odom_alpha5: 0.01
    
    # 重采样参数
    resample_interval: 1
    transform_tolerance: 0.1
```

### 4.3 启动脚本

创建一个完整的定位启动脚本：

```python
# localization_launch.py
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # 声明参数
    map_file = DeclareLaunchArgument(
        'map',
        default_value='/home/nx_ros/ros2_ws/maps/my_map.yaml',
        description='Path to map yaml file'
    )
    
    params_file = DeclareLaunchArgument(
        'params_file',
        default_value='/home/nx_ros/ros2_ws/config/amcl_params.yaml',
        description='Path to AMCL params file'
    )
    
    # 启动map_server
    map_server = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[{'yaml_filename': LaunchConfiguration('map')}]
    )
    
    # 启动AMCL
    amcl = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        parameters=[LaunchConfiguration('params_file')]
    )
    
    # 启动生命周期管理器
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager',
        parameters=[{
            'autostart': True,
            'node_names': ['map_server', 'amcl']
        }]
    )
    
    return LaunchDescription([
        map_file,
        params_file,
        map_server,
        amcl,
        lifecycle_manager
    ])
```

### 4.4 启动命令

按顺序启动各个组件：

```bash
# 终端1：启动传感器
ros2 launch robot_bringup sensors_launch.py

# 终端2：启动地图服务器
ros2 run nav2_map_server map_server --ros-args \
    -p yaml_filename:=/path/to/map.yaml

# 终端3：启动AMCL
ros2 run nav2_amcl amcl --ros-args \
    --params-file /path/to/amcl_params.yaml

# 终端4：启动rviz可视化
ros2 launch nav2_bringup rviz_launch.py
```

---

## 5. 定位实操

本节通过实际操作，讲解AMCL定位的调试和优化方法。

### 5.1 初始位姿设置

AMCL定位前，需要设置机器人的初始位姿：

**方法一：通过话题设置**：

```bash
# 发布初始位姿
ros2 topic pub /initialpose geometry_msgs/PoseWithCovarianceStamped \
"{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}"
```

**方法二：通过rviz设置**：

1. 在rviz2中点击`2D Pose Estimate`按钮
2. 在地图上点击机器人初始位置
3. 拖动箭头设置朝向

**方法三：通过参数设置**：

```yaml
# 在参数文件中设置
initial_pose_x: 1.0
initial_pose_y: 2.0
initial_pose_a: 1.57  # 90度
```

### 5.2 定位质量评估

观察以下指标评估定位质量：

**粒子分布**：

```bash
# 查看粒子云
ros2 topic echo /particlecloud
```

粒子应该聚集在一个小区域，表示定位准确。如果粒子分散在整个地图，说明定位失败。

**定位位姿**：

```bash
# 查看机器人当前位姿
ros2 topic echo /amcl_pose
```

**协方差**：

```bash
# 查看定位不确定性
ros2 topic echo /amcl_pose | grep covariance
```

协方差值越小，定位越准确。

### 5.3 定位问题诊断

常见定位问题和解决方法：

| 问题 | 原因 | 解决方法 |
|------|------|----------|
| 粒子发散 | 激光雷达噪声过大 | 调整laser_model参数 |
| 定位漂移 | 里程计误差积累 | 检查编码器校准 |
| 定位跳变 | TF坐标不准确 | 检查静态TF配置 |
| 收敛慢 | 初始位姿偏差大 | 手动设置初始位姿 |
| 撞墙 | 地图与实际不符 | 重新建图 |

### 5.4 实时调参

使用动态参数调整AMCL（需要安装`rqt_reconfigure`）：

```bash
# 安装动态参数工具
sudo apt install ros-humble-rqt-reconfigure

# 启动动态参数配置
ros2 run rqt_reconfigure rqt_reconfigure
```

可以实时调整的参数：
- `min_particles` / `max_particles`：粒子数量
- `laser_z_hit` / `laser_z_rand`：激光模型参数
- `odom_alpha1` ~ `odom_alpha5`：里程计模型参数

### 5.5 完整实操流程

以下是完整的定位实操流程：

```bash
# 步骤1：检查传感器
# 确保激光雷达和里程计正常工作

# 查看激光雷达数据
ros2 topic echo /scan | head -20

# 查看里程计数据
ros2 topic echo /odom | head -20

# 步骤2：启动地图服务器
ros2 run nav2_map_server map_server \
    --ros-args -p yaml_filename:=/path/to/map.yaml

# 步骤3：启动AMCL
ros2 run nav2_amcl amcl --ros-args \
    --params-file /path/to/amcl_params.yaml

# 步骤4：设置初始位姿
ros2 topic pub /initialpose geometry_msgs/PoseWithCovarianceStamped \
"{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}}}" -1

# 步骤5：启动机器人运动
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 步骤6：在rviz中观察
# 添加Map显示/map
# 添加PoseArray显示/particlecloud
# 添加Pose显示/amcl_pose
# 添加RobotModel显示机器人模型
```

---

## 6. 真实环境注意事项

在真实硬件上运行AMCL时，需要注意以下事项：

### 6.1 传感器校准

**激光雷达校准**：
- 确保雷达水平安装
- 检查雷达原点偏移
- 清洁雷达镜头

**里程计校准**：
- 测量准确的轮距
- 校准轮子半径
- 消除左右轮不对称误差

### 6.2 环境因素

真实环境中的挑战：
- 光照变化影响视觉传感器
- 地面不平整影响定位
- 动态障碍物干扰
- 人员走动影响激光数据

### 6.3 安全措施

运行定位系统时的安全建议：
- 设置速度限制
- 保持急停开关可用
- 在开阔区域测试
- 监控电池电量

---

## 练习题

### 选择题

1. 在ROS2中，哪个话题是AMCL定位的必要输入之一？
   - A) /cmd_vel
   - B) /scan
   - C) /camera/image
   - D) /battery_state
   
   **答案：B**。激光雷达数据`/scan`是AMCL定位的核心输入，用于观测匹配。

2. 思岚A1激光雷达的默认波特率是多少？
   - 9600
   - 115200
   - 256000
   - 460800
   
   **答案：B**。思岚A1默认使用115200波特率。

3. AMCL定位需要以下哪些坐标系关系？
   - A) map → odom → base_link
   - B) base_link → odom → map
   - C) odom → base_link → laser_link
   - D) A和C都正确
   
   **答案：A**。正确的TF坐标系关系是map→odom→base_link→laser_link。

4. 在真实机器人上，如果发现定位粒子发散，应该首先检查什么？
   - A) 地图文件是否正确
   - B) 激光雷达数据质量
   - C) 电池电量
   - D) 运动控制器
   
   **答案：B**。粒子发散通常是因为激光雷达噪声过大或数据异常。

5. 设置AMCL初始位姿的方法不包括哪种？
   - A) 通过/initialpose话题发布
   - B) 在rviz中使用2D Pose Estimate
   - C) 在参数文件中设置
   - D) 通过/cmd_vel话题设置
   
   **答案：D**。/cmd_vel是速度控制话题，不能用于设置位姿。

### 实践题

6. 假设你有一个思岚A2激光雷达，USB接口为/dev/ttyUSB0，请编写启动雷达的完整launch文件。
   
   **参考答案**：
   
   ```python
   # lidar_launch.py
   from launch import LaunchDescription
   from launch_ros.actions import Node
   
   def generate_launch_description():
       return LaunchDescription([
           Node(
               package='sllidar_ros2',
               executable='sllidar_node',
               name='sllidar_node',
               parameters=[{
                   'serial_port': '/dev/ttyUSB0',
                   'serial_baudrate': 115200,
                   'frame_id': 'laser_link',
                   'angle_compensate': True,
                   'scan_mode': 'Standard'
               }],
               output='screen'
           )
       ])
   ```

7. 创建一个完整的定位启动launch文件，包含map_server、AMCL和lifecycle_manager。
   
   **参考答案**：
   
   ```python
   # localization_launch.py
   from launch import LaunchDescription
   from launch.actions import DeclareLaunchArgument
   from launch.substitutions import LaunchConfiguration
   from launch_ros.actions import Node
   
   def generate_launch_description():
       map_file_arg = DeclareLaunchArgument(
           'map_file',
           default_value='/home/nx_ros/ros2_ws/maps/my_map.yaml',
           description='Path to map YAML file'
       )
       
       params_file_arg = DeclareLaunchArgument(
           'params_file',
           default_value='/home/nx_ros/ros2_ws/config/amcl_params.yaml',
           description='Path to AMCL parameters file'
       )
       
       map_server = Node(
           package='nav2_map_server',
           executable='map_server',
           name='map_server',
           parameters=[{
               'yaml_filename': LaunchConfiguration('map_file'),
               'topic': 'map',
               'frame_id': 'map'
           }]
       )
       
       amcl = Node(
           package='nav2_amcl',
           executable='amcl',
           name='amcl',
           parameters=[LaunchConfiguration('params_file')]
       )
       
       lifecycle_manager = Node(
           package='nav2_lifecycle_manager',
           executable='lifecycle_manager',
           name='lifecycle_manager',
           parameters=[{
               'autostart': True,
               'node_names': ['map_server', 'amcl']
           }]
       )
       
       return LaunchDescription([
           map_file_arg,
           params_file_arg,
           map_server,
           amcl,
           lifecycle_manager
       ])
   ```

8. 如果发现AMCL定位粒子过度发散，请列出至少3个可能的原因及相应的解决方法。
   
   **参考答案**：
   
   | 可能原因 | 解决方法 |
   |----------|----------|
   | 激光雷达噪声过大 | 清洁雷达、检查电源供应、调整laser_z_rand参数 |
   | 地图与实际环境不符 | 重新使用SLAM构建地图 |
   | 里程计误差过大 | 检查轮子编码器、校准轮距和轮子半径 |
   | 激光雷达安装不稳定 | 固定雷达、检查安装角度 |
   | 环境中动态障碍物过多 | 在稳定环境中测试、适当增大laser_max_range |

---

## 本章小结

本章我们系统学习了AMCL在真实硬件平台上的部署和实操方法。

**硬件平台部分**：我们了解了典型ROS2机器人的硬件组成，包括计算平台、激光雷达、IMU、编码器等组件，以及它们之间的连接关系。

**驱动配置部分**：我们详细讲解了激光雷达、IMU和里程计驱动的安装和配置方法，以及TF坐标系的正确设置。

**地图加载部分**：我们学习了地图格式和map_server的使用方法。

**AMCL部署部分**：我们掌握了AMCL参数配置和启动脚本的编写。

**定位实操部分**：我们通过实际演示，学习了初始位姿设置、定位质量评估、问题诊断和实时调参的方法。

通过本节的学习，你应该能够将AMCL定位系统从仿真环境迁移到真实机器人上，并能够处理常见的定位问题。

---

## 参考资料

### ROS2官方文档

1. Navigation2 Documentation: <https://navigation.ros.org/>
2. AMCL: <https://navigation.ros.org/tutorials/docs/navigation2_with_slam.html>
3. TF2 Documentation: <https://docs.ros.org/en/humble/Tutorials/Tf2/Introduction-To-Tf2.html>

### 激光雷达驱动

4. Slamtec sllidar_ros2: <https://github.com/Slamtec/sllidar_ros2>
5. YDLIDAR ROS2 Driver: <https://github.com/YDLIDAR/ydlidar_ros2_driver>

### IMU驱动

6. imu_drivers: <https://github.com/ros-drivers/imu_drivers>
7. imu_complementary_filter: <https://github.com/ika-rwth-aachen/imu_complementary_filter>

---

## 下节预告

下一节我们将学习**10-1 导航堆栈概述**，了解ROS2导航系统的整体架构，包括全局规划器、局部规划器、控制器等组件的协同工作原理。

---

*本章学习完成！真实硬件上的AMCL定位是一个系统工程，需要仔细调试各个组件。希望大家多动手实践，逐步掌握真实机器人定位的技术。*
