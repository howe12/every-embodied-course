# 08-6 3D SLAM真实硬件实战

> **前置课程**：08-5 3D SLAM仿真实战（RTAB-Map）
> **后续课程**：08-7 自主导航与避障

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：真实硬件环境下的3D SLAM是将仿真技术落地应用的关键步骤。本节将详细介绍3D激光雷达的选型与硬件连接、ROS2驱动配置、RTAB-Map在真实硬件上的部署方法，以及完整的3D地图构建实操流程。通过本节学习，读者将掌握将仿真环境中的3D SLAM技术迁移到真实机器人平台的能力。

---

## 1. 硬件平台概述

在真实硬件上实现3D SLAM，首先需要选择合适的传感器平台。本节以**3D激光雷达**为核心传感器，配合IMU和轮式里程计，构建完整的SLAM系统。

### 1.1 3D激光雷达选型

3D激光雷达能够获取环境的三维点云数据，是实现3D SLAM的核心传感器。根据扫描方式和性能指标，3D激光雷达主要分为以下几类：

| 类型 | 代表产品 | 扫描方式 | 测距精度 | 视场角 | 特点 |
|------|----------|----------|----------|--------|------|
| 机械旋转式 | Velodyne Puck | 360°旋转 | ±2cm | 360°×30° | 精度高，体积大，价格贵 |
| 固态式 | Livox Mid-40 | 固态扫描 | ±2cm | 38.4°×38.4° | 成本低，盲区小 |
| 混合固态 | Robosense RS-LiDAR-16 | 360°旋转 | ±2cm | 360°×30° | 性价比较高 |

对于学习和实验场景，推荐使用**Livox系列固态激光雷达**或**Robosense 16线激光雷达**。这两款产品性价比较高，且有完善的ROS2驱动支持。

```
┌─────────────────────────────────────────────────────────────────┐
│                     3D SLAM 硬件系统架构                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    ┌──────────────┐         ┌──────────────┐                   │
│    │  3D激光雷达   │────────▶│   边缘计算单元  │                   │
│    │ (Livox/RS)   │  PointCloud2 │ (Jetson/PC)  │                   │
│    └──────────────┘         └──────┬───────┘                   │
│                                     │                            │
│    ┌──────────────┐                 │                            │
│    │   IMU模块    │────────────────┤                            │
│    │ (BMI088)    │    Imu         │                            │
│    └──────────────┘                 │                            │
│                                     │                            │
│    ┌──────────────┐                 ▼                            │
│    │  轮式里程计   │────────▶  ┌──────────────┐                   │
│    │ (编码器)     │  Odometry │  RTAB-Map    │                   │
│    └──────────────┘           └──────┬───────┘                   │
│                                     │                            │
│                                     ▼                            │
│                              ┌──────────────┐                    │
│                              │  3D点云地图   │                    │
│                              └──────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 推荐硬件配置

以下是推荐的学习和实验硬件配置：

```bash
# 推荐硬件清单
- 边缘计算单元: NVIDIA Jetson Orin Nano / Jetson Xavier NX
- 3D激光雷达: Livox Mid-360 或 Robosense RS-Bpearl
- IMU模块: BMI088 或 CH110
- 机器人底盘: 差速轮式底盘（带编码器）
- 电源: 12V 5A 锂电池
```

对于预算有限的用户，可以先使用**Livox Mid-40**（单台约1500元）进行学习，其体积小巧、性能稳定，非常适合实验室环境。

---

## 2. ROS2驱动配置

3D激光雷达需要安装对应的ROS2驱动才能正常工作。本节以**Livox激光雷达**和**Robosense激光雷达**为例，详细讲解驱动配置方法。

### 2.1 Livox激光雷达驱动安装

Livox提供了官方的ROS2驱动包，支持Mid-40、Mid-70、Horizon等型号。

**安装步骤**：

```bash
# 1. 创建ROS2工作空间
mkdir -p ~/ros2_lidar_ws/src
cd ~/ros2_lidar_ws

# 2. 下载Livox ROS2驱动
cd src
git clone https://github.com/Livox-SDK/livox_ros2_driver.git

# 3. 安装依赖
cd ..
rosdep install --from-paths src --ignore-src -r -y

# 4. 编译功能包
colcon build --packages-select livox_ros2_driver
source install/setup.bash
```

**驱动参数配置**：

```bash
# 创建驱动配置文件
mkdir -p ~/ros2_lidar_ws/src/livox_ros2_driver/config
cat > ~/ros2_lidar_ws/src/livox_ros2_driver/config/livox_lidar.yaml << 'EOF'
livox_lidar:
  ros__parameters:
    # 激光雷达IP配置
    ip: 192.168.1.1xx        # 根据实际雷达型号修改
    cmd_port: 56000          # 命令端口
    push_port: 56001         # 数据推送端口
    sub_port: 56002         # 订阅端口
    
    # 发布话题配置
    publish_point_cloud: true
    publish_topic: "/livox/lidar"
    
    # 数据格式
    point_cloud_format: 2    # 0: xyz, 1: xyzirt, 2: xyzirtcb
    coordinate_type: 1       # 0: camera, 1: cartesian
    
    # 帧ID
    frame_id: "livox_frame"
EOF
```

**启动驱动**：

```bash
# 终端1：启动Livox驱动
cd ~/ros2_lidar_ws
source install/setup.bash
ros2 launch livox_ros2_driver livox_lidar_launch.py

# 终端2：查看点云话题
ros2 topic list
ros2 topic hz /livox/lidar
```

### 2.2 Robosense激光雷达驱动安装

Robosense RS系列激光雷达使用`rs_driver`作为ROS2驱动。

```bash
# 1. 安装rs_driver依赖
cd ~/ros2_lidar_ws/src
git clone https://github.com/RoboSense-LiDAR/rs_driver.git

# 2. 安装PCL（如果未安装）
sudo apt-get install libpcl-dev

# 3. 编译驱动
cd ~/ros2_lidar_ws
colcon build --packages-select rs_driver
source install/setup.bash
```

**启动Robosense雷达**：

```bash
# RS-Bpearl雷达启动命令
ros2 launch rs_driver rs_lidar_launch.py driver_params_file:=/path/to/params.yaml
```

### 2.3 雷达话题数据格式

3D激光雷达发布的数据类型为`sensor_msgs/PointCloud2`，这是ROS2中标准的点云消息格式：

```yaml
# sensor_msgs/PointCloud2 消息结构
Header header              # 时间戳和帧ID
uint32 height              # 点云高度（用于有序点云）
uint32 width               # 点云宽度
PointField[] fields        # 点云字段（x, y, z, intensity, timestamp等）
bool is_bigendian         # 字节序
uint32 point_step         # 每个点的字节数
uint32 row_step           # 每行的字节数
uint8[] data              # 点云数据
bool is_dense             # 是否为稠密点云
```

```bash
# 查看点云话题信息
ros2 topic info /livox/lidar -v

# 查看点云数据
ros2 topic echo /livox/lidar --flow-style
```

---

## 3. RTAB-Map部署

在真实硬件上部署RTAB-Map，需要完成传感器数据对齐、参数配置和启动文件编写等工作。

### 3.1 安装RTAB-Map ROS2功能包

```bash
# 安装RTAB-Map ROS2版本
sudo apt-get update
sudo apt-get install ros-humble-rtabmap-ros

# 验证安装
ros2 pkg list | grep rtabmap
```

### 3.2 传感器坐标系配置

3D SLAM要求各传感器的坐标系正确对齐。使用**TF2**工具管理坐标系变换：

```bash
# 查看当前TF树
ros2 run tf2_ros tf2_echo /base_footprint /livox_frame
ros2 run rqt_tf_tree rqt_tf_tree
```

**坐标系配置说明**：

| 坐标系 | 说明 |
|--------|------|
| `base_footprint` | 机器人底部基坐标系 |
| `base_link` | 机器人本体坐标系 |
| `livox_frame` | 激光雷达坐标系 |
| `imu_link` | IMU传感器坐标系 |
| `odom` | 里程计坐标系 |

**静态TF发布**：

```python
# /home/nx_ros/ros2_ws/src/robot_bringup/robot_bringup/static_tf_publisher.py
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster
from geometry_msgs.msg import TransformStamped

class StaticTFPublisher(Node):
    def __init__(self):
        super().__init__('static_tf_publisher')
        self.broadcaster = StaticTransformBroadcaster(self)
        
        # 发布激光雷达相对于base_link的TF
        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = 'base_link'
        t.child_frame_id = 'livox_frame'
        
        # 雷达安装在机器人前方0.3米，高度0.1米
        t.transform.translation.x = 0.3
        t.transform.translation.y = 0.0
        t.transform.translation.z = 0.1
        
        # 无旋转
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0
        
        self.broadcaster.sendTransform(t)
        self.get_logger().info('Static TF published')

def main(args=None):
    rclpy.init(args=args)
    node = StaticTFPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 3.3 RTAB-Map启动参数配置

RTAB-Map有众多参数需要根据实际硬件配置进行调整：

```bash
# 创建RTAB-Map配置文件
mkdir -p ~/ros2_slam/config
cat > ~/ros2_slam/config/rtabmap_params.yaml << 'EOF'
rtabmap:
  ros__parameters:
    # 基础参数
    frame_id: "base_link"
    odom_frame_id: "odom"
    map_frame_id: "map"
    
    # 里程计配置
    odom_sensor: 2           # 0: only visual, 1: only IMU, 2: IMU+Visual
    
    # 传感器话题配置
    scan_topic: "/livox/lidar"
    odom_topic: "/diff_drive_controller/odom"
    imu_topic: "/imu/data"
    
    # RTAB-Map算法参数
    queue_size: 100
    max_keypoints: 1000
    max_depth: 5.0          # 最大深度（米）
    min_depth: 0.1         # 最小深度（米）
    
    # 回环检测参数
    loop_closure_threshold: 0.25
    loop_closure_optimizer: 7
    
    # 内存管理
    working_memory: 1000
    images_history: 100
    
    # 点云滤波
    voxel_size: 0.05        # 体素滤波大小（米）
    
    # 发布配置
    publish_tf: true
    publish_map_odom_transform: true
    publish_debug_image: false
EOF
```

---

## 4. 3D地图构建实操

本节将通过完整的实操流程，演示如何在真实硬件上使用RTAB-Map构建3D地图。

### 4.1 系统启动脚本

创建一个完整的启动脚本，整合所有节点：

```bash
# /home/nx_ros/ros2_ws/src/robot_slam/launch/robot_slam.launch.py
#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 获取配置参数
    pkg_share = get_package_share_directory('robot_slam')
    config_file = os.path.join(pkg_share, 'config', 'rtabmap_params.yaml')
    
    return LaunchDescription([
        # 1. 静态TF发布（雷达与IMU安装位置）
        Node(
            package='robot_bringup',
            executable='static_tf_publisher',
            name='static_tf_publisher',
            output='screen'
        ),
        
        # 2. Livox激光雷达驱动
        Node(
            package='livox_ros2_driver',
            executable='livox_lidar_node',
            name='livox_lidar_node',
            output='screen',
            parameters=[{
                'publish_point_cloud': True,
                'point_cloud_format': 2,
                'frame_id': 'livox_frame'
            }]
        ),
        
        # 3. IMU滤波器（如果需要）
        Node(
            package='imu_filter',
            executable='imu_filter_node',
            name='imu_filter',
            output='screen',
            parameters=[{
                'use_mag': False,
                'publish_tf': True,
                'world_frame': 'enu'
            }]
        ),
        
        # 4. RTAB-Map SLAM节点
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            output='screen',
            parameters=[config_file],
            remappings=[
                ('scan', '/livox/lidar'),
                ('odom', '/diff_drive_controller/odom'),
                ('imu', '/imu/data')
            ]
        ),
        
        # 5. 地图可视化（可选）
        Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            name='rtabmap_viz',
            output='screen'
        )
    ])
```

### 4.2 启动3D SLAM系统

```bash
# 终端1：启动机器人基础节点（底盘驱动、传感器等）
cd ~/ros2_ws
source install/setup.bash
ros2 launch robot_bringup robot_minimal.launch.py

# 终端2：启动3D SLAM系统
cd ~/ros2_ws
source install/setup.bash
ros2 launch robot_slam robot_slam.launch.py
```

### 4.3 实时地图构建

启动系统后，控制机器人在环境中移动：

```bash
# 终端3：启动键盘控制节点
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 输入控制命令：
# i - 前进
# j - 左转
# k - 停止
# l - 右转
# , - 后退
```

在SLAM运行过程中，RTAB-Map会：

1. **实时里程计估计**：根据IMU和轮式里程计数据计算机器人位姿
2. **点云处理**：对激光雷达数据进行滤波和特征提取
3. **回环检测**：当检测到之前访问过的区域时，消除累积误差
4. **地图优化**：使用图优化方法调整所有关键帧位姿

### 4.4 地图保存与加载

完成地图构建后，需要保存地图供后续使用：

```bash
# 方式1：使用rtabmap数据库保存
# 在另一个终端执行
ros2 service call /rtabmap/save_map rtabmap_interfaces/srv/SaveMap "{
  path: '/home/nx_ros/ros2_ws/maps/my_3d_map.db',
  format: 'db'  # 'db' for database, 'png' for 2D occupancy grid
}"

# 方式2：保存点云地图
ros2 service call /rtabmap/export_point_cloud rtabmap_interfaces/srv/ExportPointCloud "{
  path: '/home/nx_ros/ros2_ws/maps/pointcloud.pcd',
  format: 'pcd'
}"
```

**地图加载**：

```bash
# 创建地图加载启动文件
cat > ~/ros2_ws/src/robot_slam/launch/robot_navigation.launch.py << 'EOF'
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='rtabmap_slam',
            executable='rtabmap',
            name='rtabmap',
            parameters=[{
                'database_path': '/home/nx_ros/ros2_ws/maps/my_3d_map.db',
                'ubilinux_screen': False,
                'subscribe_depth': True,
                'subscribe_rgb': False,
                'subscribe_scan': True
            }],
            remappings=[
                ('scan', '/livox/lidar'),
                ('odom', '/diff_drive_controller/odom')
            ]
        )
    ])
EOF
```

### 4.5 地图质量评估

构建完3D地图后，可以使用以下指标评估地图质量：

| 指标 | 说明 | 评估方法 |
|------|------|----------|
| 地图完整性 | 是否覆盖所有区域 | 人工检查或区域覆盖率计算 |
| 点云密度 | 单位面积的点云数量 | 使用PCL统计 |
| 回环质量 | 回环闭合的准确性 | 检查重复区域的点云对齐 |
| 全局一致性 | 地图无明显变形 | 观察长走廊等特征 |

```bash
# 使用PCL查看器检查点云
pcl_viewer /home/nx_ros/ros2_ws/maps/pointcloud.pcd

# 使用rviz2查看3D地图
rviz2 -d ~/ros2_ws/src/robot_slam/config/rtabmap.rviz
```

---

## 5. 常见问题与解决

### 5.1 雷达数据问题

**问题1：点云数据丢失或延迟**

```bash
# 检查雷达连接状态
ros2 topic hz /livox/lidar

# 如果频率过低，检查网络配置
# 确保雷达和计算单元在同一局域网
# 推荐使用千兆以太网
```

**问题2：点云噪声过大**

```yaml
# 在rtabmap参数中添加点云滤波
ros__parameters:
  point_cloud_filtering: true
  max_keypoints: 500
  min_keypoints: 50
```

### 5.2 SLAM精度问题

**问题1：里程计漂移过大**

```yaml
# 调整里程计权重
ros__parameters:
  odom_weight: 1.0
  loop_closure_weight: 10.0
  scan相关性_threshold: 0.5
```

**问题2：回环检测失败**

```yaml
# 调整回环检测参数
ros__parameters:
  loop_closure_threshold: 0.15  # 降低阈值
  loop_closure_optimizer: 7
  max_keypoints: 2000           # 增加特征点数量
```

### 5.3 实时性问题

**问题：SLAM运行卡顿**

```bash
# 1. 降低点云分辨率
# 在雷达驱动中设置lower_resolution

# 2. 减少RTAB-Map处理频率
ros__parameters:
  pub_keyframe_strategy: 2  # 只在有明显运动时发布

# 3. 使用GPU加速（如有）
# 安装CUDA版本的PCL
sudo apt-get install libcuda1.11.0
```

---

## 练习题

### 选择题

1. 在3D SLAM系统中，以下哪个传感器是必需的？
   - A) RGB-D相机
   - B) 3D激光雷达
   - C) 超声波传感器
   - D) 激光测距仪
   
   **答案：B**。3D激光雷达是实现3D SLAM的核心传感器，能够直接获取环境的三维点云数据。

2. Livox固态激光雷达相比机械旋转式雷达的优势是什么？
   - A) 测距精度更高
   - B) 视场角更大
   - C) 成本更低、无机械磨损
   - D) 防护等级更高
   
   **答案：C**。固态激光雷达没有机械旋转部件，成本较低且使用寿命更长。

3. RTAB-Map的回环检测主要依靠什么技术？
   - A) GPS定位
   - B) 词袋模型（Bag-of-Words）
   - C) 卡尔曼滤波
   - D) 神经网络
   
   **答案：B**。RTAB-Map使用基于外观的词袋模型进行回环检测，能够在不需要先验位姿的情况下检测回环。

### 实践题

4. 配置Livox激光雷达的ROS2驱动，并验证点云数据发布正常。
   
   **参考答案**：
   
   ```bash
   # 步骤1：安装驱动
   cd ~/ros2_ws/src
   git clone https://github.com/Livox-SDK/livox_ros2_driver.git
   cd ..
   colcon build --packages-select livox_ros2_driver
   
   # 步骤2：配置环境
   source install/setup.bash
   
   # 步骤3：启动驱动
   ros2 launch livox_ros2_driver livox_lidar_launch.py
   
   # 步骤4：验证数据
   # 新终端中执行
   ros2 topic list
   ros2 topic hz /livox/lidar
   ros2 run rqt_plot rqt_plot /livox/lidar/pointcloud/point[0]
   ```

5. 编写一个启动脚本，实现在真实硬件上启动完整的3D SLAM系统（包含雷达驱动、IMU、RTAB-Map）。
   
   **参考答案**：
   
   ```python
   # /home/nx_ros/ros2_ws/src/robot_slam/launch/robot_3d_slam.launch.py
   from launch import LaunchDescription
   from launch_ros.actions import Node
   
   def generate_launch_description():
       return LaunchDescription([
           # 静态TF发布
           Node(
               package='robot_bringup',
               executable='static_tf_publisher',
               name='static_tf'
           ),
           
           # Livox雷达驱动
           Node(
               package='livox_ros2_driver',
               executable='livox_lidar_node',
               name='livox_driver',
               parameters=[{
                   'publish_point_cloud': True,
                   'frame_id': 'livox_frame'
               }]
           ),
           
           # IMU滤波器
           Node(
               package='imu_filter',
               executable='imu_filter_node',
               name='imu_filter',
               parameters=[{
                   'use_mag': False,
                   'world_frame': 'enu'
               }]
           ),
           
           # RTAB-Map
           Node(
               package='rtabmap_slam',
               executable='rtabmap',
               name='rtabmap',
               parameters=[{
                   'frame_id': 'base_link',
                   'odom_frame_id': 'odom',
                   'scan_topic': '/livox/lidar',
                   'odom_topic': '/diff_drive_controller/odom',
                   'imu_topic': '/imu/data',
                   'max_keypoints': 1000,
                   'voxel_size': 0.05
               }],
               remappings=[
                   ('scan', '/livox/lidar'),
                   ('odom', '/diff_drive_controller/odom'),
                   ('imu', '/imu/data')
               ]
           ),
           
           # 可视化
           Node(
               package='rtabmap_viz',
               executable='rtabmap_viz',
               name='rtabmap_viz'
           )
       ])
   ```

---

## 本章小结

本章我们详细学习了3D SLAM在真实硬件上的部署和实操。硬件平台部分，我们了解了3D激光雷达的选型方法和推荐配置。ROS2驱动配置部分，我们分别讲解了Livox和Robosense激光雷达的驱动安装和参数配置。RTAB-Map部署部分，我们完成了传感器坐标系配置和参数文件的编写。3D地图构建实操部分，我们通过完整的启动脚本和操作流程，演示了如何构建、保存和评估3D地图。最后，我们还介绍了常见问题的解决方法。

真实硬件环境比仿真环境更加复杂，需要考虑传感器标定、网络延迟、计算资源等多方面因素。但只要掌握了本节的内容，你就具备了将3D SLAM技术应用到实际机器人项目中的能力。

---

## 参考资料

### 激光雷达驱动

1. Livox ROS2 Driver: <https://github.com/Livox-SDK/livox_ros2_driver>
2. Robosense rs_driver: <https://github.com/RoboSense-LiDAR/rs_driver>

### RTAB-Map官方文档

3. RTAB-Map GitHub: <https://github.com/introlab/rtabmap>
4. RTAB-Map ROS2: <https://github.com/introlab/rtabmap_ros>

### 硬件选型参考

5. Livox产品手册: <https://www.livoxtech.com/>
6. Robosense产品手册: <https://www.robosense.cn/>

---

## 下节预告

下一节我们将学习**08-7 自主导航与避障**，了解如何在已构建的3D地图基础上，实现机器人的自主导航和动态避障。我们将介绍导航堆栈的配置、路径规划算法以及实际部署方法。

---

*本章学习完成！3D SLAM真实硬件实战是将理论转化为应用的关键一步，建议大家多动手实验，逐步掌握在真实环境中部署SLAM系统的技能。*
