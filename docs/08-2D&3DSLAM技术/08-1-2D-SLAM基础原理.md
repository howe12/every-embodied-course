# 08-1 2D SLAM基础原理

> **前置课程**：07-3 机器人运动控制
> **后续课程**：08-2 3D SLAM技术概述

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：同步定位与地图构建（SLAM）是移动机器人领域的核心技术，它使机器人能够在未知环境中同时估计自身位置并构建环境地图。本节将深入讲解2D SLAM的基础原理，包括地图表示方法、位姿估计、回环检测等核心概念，并介绍Gmapping、Hector、Cartographer等经典算法。

---

## 1. SLAM概述

### 1.1 什么是SLAM

**同步定位与地图构建（Simultaneous Localization and Mapping，SLAM）**是机器人自主导航的核心技术。SLAM解决的问题是：在未知环境中，机器人如何仅凭自身传感器感知的信息，同时完成两件事——确定自己在环境中的位置（定位），以及构建环境的地形图（建图）。

SLAM技术的重要性体现在以下几个方面。首先，它是机器人自主导航的前提——只有知道自己在哪（定位），才能规划路径到达目的地；只有知道环境什么样（建图），才能避开障碍物。其次，SLAM是实现真正无人干预机器人的关键技术，在扫地机器人、自动驾驶、无人机等领域都有广泛应用。最后，SLAM涉及传感器融合、概率估计、图优化等核心技术，是机器人学和相关专业的核心知识点。

### 1.2 SLAM的分类

根据应用场景和传感器类型的不同，SLAM可以分为多种类型：

**按维度分类**：

| 类型 | 描述 | 典型应用 |
|------|------|----------|
| 2D SLAM | 在二维平面内建图 | 扫地机器人、仓库AGV |
| 2.5D SLAM | 建图考虑高度信息 | 室内服务机器人 |
| 3D SLAM | 三维空间建图 | 自动驾驶、无人机 |

**按传感器分类**：

| 类型 | 描述 | 优缺点 |
|------|------|--------|
| 激光SLAM | 使用激光雷达 | 精度高，Outdoor能力弱 |
| 视觉SLAM | 使用相机 | 成本低，信息丰富，稳定性差 |
| 惯性SLAM | 使用IMU | 短期精度高，累积误差大 |
| 多传感器融合 | 组合多种传感器 | 精度高，复杂度高 |

**按建图方法分类**：

| 类型 | 描述 | 代表算法 |
|------|------|----------|
| 栅格地图 | 将环境划分为栅格 | Gmapping、Hector |
| 拓扑地图 | 用节点和边表示 | Tino、拓扑SLAM |
| 特征地图 | 用几何特征表示 | PTAM、ORB-SLAM |
| 点云地图 | 用3D点表示 | LOAM、LIO-SAM |

2D SLAM通常使用栅格地图（Occupancy Grid Map）表示环境，这也是本课程重点讲解的内容。

### 1.3 SLAM的基本框架

一个完整的2D SLAM系统通常包含以下几个核心模块：

**传感器数据**：负责采集环境信息和机器人运动数据，主要包括激光雷达点云、轮式里程计数据、IMU数据等。

**前端（Odometry/Frontend）**：负责计算机器人的相对运动，包括里程计估计和激光扫描匹配。前端需要实时处理传感器数据，提供高频的位姿估计。

**后端（Optimization/Backend）**：负责全局优化，包括位姿图优化和回环检测修正。后端通常运行在较低频率，但对精度至关重要。

**地图构建**：根据处理后的数据和优化结果，构建环境地图。在2D SLAM中，栅格地图是最常用的表示方法。

---

## 2. 传感器要求

2D SLAM系统对传感器有一定要求，不同传感器组合会影响SLAM系统的性能。本节详细介绍各类传感器的要求和特点。

### 2.1 激光雷达

**激光雷达（LiDAR）**是2D SLAM最常用的传感器，它通过发射激光束并接收反射信号来测量距离。激光雷达具有测距精度高、响应速度快的优点，是2D SLAM的首选传感器。

**技术参数**：

| 参数 | 说明 | 对SLAM的影响 |
|------|------|---------------|
| 测距范围 | 激光能探测的最远距离 | 影响建图范围 |
| 测距精度 | 距离测量误差 | 影响地图精度 |
| 角度分辨率 | 相邻激光束的角度差 | 影响角度精度 |
| 扫描频率 | 每秒完成的扫描次数 | 影响实时性 |
| 角分辨率 | 激光束的角度间隔 | 影响角向分辨率 |

**常见激光雷达类型**：

| 类型 | 代表产品 | 特点 |
|------|----------|------|
| 单线激光雷达 | RPLIDAR A1/S1 | 成本低，2D建图首选 |
| 多线激光雷达 | Velodyne HDL-32E | 3D扫描，昂贵 |
| 固态激光雷达 | Livox Mid-40 | 成本低，FOV大 |

**ROS2中的激光雷达消息**：

```yaml
# sensor_msgs/msg/LaserScan.msg
Header header                    # 时间戳和坐标系
float32 angle_min               # 扫描起始角度（弧度）
float32 angle_max               # 扫描结束角度（弧度）
float32 angle_increment         # 角度增量
float32 time_increment          # 时间增量
float32 scan_time               # 扫描时间间隔
float32 range_min               # 最小有效距离
float32 range_max               # 最大有效距离
float32[] ranges                # 距离数据数组
float32[] intensities            # 强度数据数组
```

**Python读取激光雷达数据示例**：

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class LaserReader(Node):
    def __init__(self):
        super().__init__('laser_reader')
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
    def scan_callback(self, msg):
        # 获取前方的距离
        front_index = len(msg.ranges) // 2
        front_distance = msg.ranges[front_index]
        
        self.get_logger().info(
            f'前方距离: {front_distance:.2f}m, '
            f'扫描角度范围: [{msg.angle_min:.2f}, {msg.angle_max:.2f}]'
        )

def main(args=None):
    rclpy.init(args=args)
    node = LaserReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 2.2 里程计

**里程计（Odometry）**通过分析电机编码器数据来估计机器人的运动。里程计提供相邻时刻之间的相对位姿变化，是SLAM系统中重要的运动先验信息。

**里程计类型**：

| 类型 | 数据来源 | 优点 | 缺点 |
|------|----------|------|------|
| 轮式里程计 | 电机编码器 | 长期稳定 | 轮子打滑累积误差 |
| 视觉里程计 | 相机图像 | 无累积误差 | 受光照影响 |
| 惯性里程计 | IMU | 短期精度高 | 快速漂移 |

**ROS2中的里程计消息**：

```yaml
# nav_msgs/msg/Odometry.msg
Header header
string child_frame_id
geometry_msgs/Pose pose          # 位置和朝向
geometry_msgs/Twist twist        # 线速度和角速度
```

**里程计消息中的协方差**：

```python
# 设置里程计协方差矩阵
odom_msg.pose.covariance = [
    0.01, 0, 0, 0, 0, 0,    # x 位置方差
    0, 0.01, 0, 0, 0, 0,    # y 位置方差
    0, 0, 0.01, 0, 0, 0,    # z 位置方差
    0, 0, 0, 0.1, 0, 0,     # x 轴旋转方差
    0, 0, 0, 0, 0.1, 0,     # y 轴旋转方差
    0, 0, 0, 0, 0, 0.1      # z 轴旋转方差
]
```

### 2.3 IMU惯性测量单元

**IMU（Inertial Measurement Unit）**惯性测量单元包含加速度计和陀螺仪，可以测量机器人当前的线加速度和角速度。IMU数据可用于位姿预测和传感器融合。

**ROS2中的IMU消息**：

```yaml
# sensor_msgs/msg/Imu.msg
Header header
geometry_msgs/Quaternion orientation         # 四元数姿态
float64[9] orientation_covariance            # 姿态协方差
geometry_msgs/Vector3 angular_velocity        # 角速度
float64[9] angular_velocity_covariance       # 角速度协方差
geometry_msgs/Vector3 linear_acceleration     # 线加速度
float64[9] linear_acceleration_covariance     # 线加速度协方差
```

**IMU数据读取示例**：

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import math

class ImuReader(Node):
    def __init__(self):
        super().__init__('imu_reader')
        self.subscription = self.create_subscription(
            Imu,
            '/imu',
            self.imu_callback,
            10
        )
        
    def imu_callback(self, msg):
        # 从四元数提取偏航角（yaw）
        q = msg.orientation
        siny_cosp = 2 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1 - 2 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        self.get_logger().info(
            f'偏航角: {math.degrees(yaw):.1f}°, '
            f'角速度Z: {msg.angular_velocity.z:.2f} rad/s'
        )

def main(args=None):
    rclpy.init(args=args)
    node = ImuReader()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 2.4 传感器配置建议

对于一个性能良好的2D SLAM系统，建议的传感器配置如下：

| 传感器 | 推荐规格 | 作用 |
|--------|----------|------|
| 激光雷达 | 单线，≥5Hz，180°FOV | 核心环境感知 |
| 轮式里程计 | 精度≥100脉冲/转 | 运动估计 |
| IMU（可选） | 6轴，≥50Hz | 运动预测 |

在实际应用中，需要注意传感器之间的同步问题。建议使用硬件触发或时间同步机制，确保各传感器数据的时间戳一致。

---

## 3. 2D SLAM原理

本节深入讲解2D SLAM的核心原理，包括地图表示方法、位姿估计技术和回环检测机制。

### 3.1 地图表示

2D SLAM最常用的地图表示方法是**栅格地图（Occupancy Grid Map）**。栅格地图将环境划分为均匀的网格，每个格子记录该位置是否被占用。

**栅格地图原理**：

栅格地图将2D空间划分为均匀的网格，每个格子可以处于三种状态：空闲（Free）、占用（Occupied）或未知（Unknown）。通常使用0-100的数值表示，0表示完全空闲，100表示完全占用，50或-1表示未知。

**占用概率计算**：

设 $P(s)$ 为格子 $s$ 被占用的概率，使用**对数odds**表示：

$$l(s) = \log\frac{P(s)}{1-P(s)}$$

更新公式为：

$$l_{t}(s) = l_{t-1}(s) + \log\frac{P(z_t|s)}{1-P(z_t|s)} - l_0$$

其中 $z_t$ 是 $t$ 时刻的观测，$l_0$ 是先验的log-odds。

使用log-odds表示的好处是加法运算比概率乘法更高效，且数值更稳定。

**ROS2中的栅格地图消息**：

```yaml
# nav_msgs/msg/OccupancyGrid.msg
Header header
MapMetaData info           # 地图元数据
int8[] data               # 占用数据（0-100）

# MapMetaData
time map_load_time         # 地图加载时间
float32 resolution         # 栅格分辨率（米）
uint32 width               # 地图宽度（栅格数）
uint32 height              # 地图高度（栅格数）
geometry_msgs/Pose origin  # 地图原点位姿
```

**Python创建栅格地图**：

```python
import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid, MapMetaData
from geometry_msgs.msg import Pose
import math

class MapPublisher(Node):
    def __init__(self):
        super().__init__('map_publisher')
        self.publisher = self.create_publisher(OccupancyGrid, '/map', 10)
        self.timer = self.create_timer(1.0, self.publish_map)
        
        # 地图参数
        self.width = 100
        self.height = 100
        self.resolution = 0.05  # 5cm
        
    def publish_map(self):
        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        
        # 地图元数据
        msg.info.resolution = self.resolution
        msg.info.width = self.width
        msg.info.height = self.height
        
        # 地图原点
        msg.info.origin.position.x = -self.width * self.resolution / 2
        msg.info.origin.position.y = -self.height * self.resolution / 2
        msg.info.origin.position.z = 0.0
        msg.info.origin.orientation.w = 1.0
        
        # 初始化为未知（-1 或 50）
        msg.data = [50] * (self.width * self.height)
        
        self.publisher.publish(msg)
        self.get_logger().info('Map published')

def main(args=None):
    rclpy.init(args=args)
    node = MapPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 3.2 位姿估计

位姿估计是SLAM的核心问题之一，包括**里程计估计**和**扫描匹配**两种主要方法。

#### 3.2.1 里程计估计

里程计估计使用机器人运动模型来预测位姿变化。最常用的是**里程计运动模型**：

**里程计更新公式**：

设机器人在时刻 $t-1$ 的位姿为 $\mathbf{x}_{t-1} = [x, y, \theta]^T$，里程计测量为 $\mathbf{u}_t = [\Delta x, \Delta y, \Delta\theta]^T$，则预测的位姿为：

$$
\begin{bmatrix} x' \\ y' \\ \theta' \end{bmatrix} = 
\begin{bmatrix} x + \Delta x \cos\theta - \Delta y \sin\theta \\ y + \Delta x \sin\theta + \Delta y \cos\theta \\ \theta + \Delta\theta \end{bmatrix}
$$

**里程计实现示例**：

```python
import math

class OdometryEstimator:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
    def update(self, delta_x, delta_y, delta_theta):
        """更新里程计估计"""
        # 更新角度
        self.theta += delta_theta
        
        # 归一化角度到 [-π, π]
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
        
        # 更新位置（考虑当前角度）
        self.x += delta_x * math.cos(self.theta) - delta_y * math.sin(self.theta)
        self.y += delta_x * math.sin(self.theta) + delta_y * math.cos(self.theta)
        
        return (self.x, self.y, self.theta)
    
    def get_pose(self):
        """获取当前位姿"""
        return (self.x, self.y, self.theta)
```

#### 3.2.2 扫描匹配

扫描匹配（Scan Matching）是利用激光数据估计机器人位姿的方法。最经典的算法是**迭代最近点（ICP）**及其变体。

**ICP算法原理**：

给定两个点集 $P$ 和 $Q$，寻找最优的旋转矩阵 $\mathbf{R}$ 和平移向量 $\mathbf{t}$，使得：

$$\mathbf{Q} = \mathbf{R}\mathbf{P} + \mathbf{t}$$

**扫描匹配实现（简化版）**：

```python
import numpy as np
import math

def scan_match_icp(reference_scan, current_scan, initial_pose):
    """
    简化的ICP扫描匹配
    
    Args:
        reference_scan: 参考扫描点 numpy array (N x 2)
        current_scan: 当前扫描点 numpy array (M x 2)
        initial_pose: 初始猜测 (x, y, theta)
        
    Returns:
        (x, y, theta): 最优位姿
    """
    x, y, theta = initial_pose
    
    for iteration in range(20):
        # 1. 使用当前位姿变换当前扫描点
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        rotation = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
        transformed = np.dot(current_scan, rotation.T) + np.array([x, y])
        
        # 2. 找到对应点（简化：最近邻）
        matched = []
        for p in transformed:
            distances = np.linalg.norm(reference_scan - p, axis=1)
            min_idx = np.argmin(distances)
            if distances[min_idx] < 1.0:  # 距离阈值
                matched.append((p, reference_scan[min_idx]))
        
        if len(matched) < 3:
            break
            
        # 3. 计算变换
        src = np.array([m[0] for m in matched])
        dst = np.array([m[1] for m in matched])
        
        center_src = src.mean(axis=0)
        center_dst = dst.mean(axis=0)
        
        src_centered = src - center_src
        dst_centered = dst - center_dst
        
        # SVD求解旋转
        H = np.dot(src_centered.T, dst_centered)
        U, S, Vt = np.linalg.svd(H)
        R = np.dot(Vt.T, U.T)
        
        # 检测反射
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = np.dot(Vt.T, U.T)
        
        t = center_dst - np.dot(R, center_src)
        
        # 4. 更新位姿
        dx, dy = t
        dtheta = math.atan2(R[1, 0], R[0, 0])
        
        x += dx
        y += dy
        theta += dtheta
        
        # 检查收敛
        if abs(dx) < 0.001 and abs(dy) < 0.001 and abs(dtheta) < 0.001:
            break
    
    return (x, y, theta)
```

### 3.3 回环检测

**回环检测（Loop Closure Detection）**是SLAM中解决累积误差的关键技术。当机器人返回之前访问过的位置时，检测到回环并修正位姿图，可以消除累积漂移。

**回环检测方法**：

| 方法 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 基于里程计 | 检测是否接近历史位置 | 简单 | 误差大时失效 |
| 基于外观 | 比较扫描/图像相似度 | 准确 | 计算量大 |
| 基于词袋 | 将扫描转为词袋向量 | 高效 | 需要训练 |

**词袋模型（Bag of Words）实现**：

```python
import numpy as np
from collections import defaultdict

class BowDetector:
    """基于词袋模型的回环检测"""
    
    def __init__(self, vocabulary_size=100):
        self.vocabulary_size = vocabulary_size
        self.vocabulary = []  # 视觉词
        self.descriptors_history = []  # 历史描述子
        
    def extract_features(self, scan):
        """从激光扫描中提取特征（简化版：使用极坐标采样点）"""
        # 将极坐标点转为笛卡尔坐标
        features = []
        for i, r in enumerate(scan.ranges):
            if scan.range_min < r < scan.range_max:
                angle = scan.angle_min + i * scan.angle_increment
                x = r * np.cos(angle)
                y = r * np.sin(angle)
                features.append([x, y])
        return np.array(features) if features else np.array([]).reshape(0, 2)
    
    def compute_descriptor(self, features):
        """计算简化的描述子"""
        if len(features) < 5:
            return np.zeros(self.vocabulary_size)
        
        # 简化为直方图描述子
        hist, _ = np.histogram(features[:, 1], bins=self.vocabulary_size)
        return hist / (np.linalg.norm(hist) + 1e-6)
    
    def detect_loop(self, current_descriptor, history_size=100):
        """检测回环"""
        if len(self.descriptors_history) < history_size:
            return None
            
        # 获取历史窗口
        history = self.descriptors_history[-history_size:-10]  # 排除最近10帧
        
        # 计算相似度
        similarities = []
        for i, desc in enumerate(history):
            sim = np.dot(current_descriptor, desc)
            similarities.append((i, sim))
        
        # 找到最高相似度
        best_match = max(similarities, key=lambda x: x[1])
        
        # 阈值判断
        if best_match[1] > 0.8:  # 相似度阈值
            return len(self.descriptors_history) - history_size + best_match[0]
        
        return None
    
    def add_descriptor(self, descriptor):
        """添加新的描述子到历史"""
        self.descriptors_history.append(descriptor)
```

---

## 4. 经典算法

本节介绍三种经典的2D SLAM算法：Gmapping、Hector和Cartographer。这些算法在ROS/ROS2中有广泛的应用。

### 4.1 Gmapping

**Gmapping**是基于粒子滤波的2D SLAM算法，它使用RBPF（Rao-Blackwellized Particle Filter）框架，将定位和建图分离。

**算法特点**：

| 特性 | 说明 |
|------|------|
| 方法 | 粒子滤波 |
| 地图类型 | 栅格地图 |
| 优点 | 实现简单，可处理非线性 |
| 缺点 | 粒子数多时计算量大 |

**算法原理**：

Gmapping使用粒子滤波器维护多个可能的机器人位姿，每个粒子携带一个地图副本。权重的更新依赖于观测 likelihood：

$$w_t^{(i)} = w_{t-1}^{(i)} \cdot p(z_t | x_t^{(i)}, m_{t-1}^{(i)})$$

其中 $w_t^{(i)}$ 是粒子 $i$ 的权重，$z_t$ 是观测，$x_t^{(i)}$ 是粒子位姿，$m_{t-1}^{(i)}$ 是对应的地图。

**ROS2中使用Gmapping**：

```bash
# 安装gmapping
sudo apt install ros-humble-slam-toolbox

# 启动gmapping
ros2 launch slam_toolbox online_sync_launch.py
```

**参数配置**：

```yaml
# slam.yaml
slam_toolbox:
  ros__parameters:
    # 地图参数
    resolution: 0.05              # 地图分辨率
    map_size: 2048                # 地图尺寸
    
    # 激光参数
    max_laser_range: 10.0          # 最大激光范围
    laser_thresholds: 0.1         # 激光阈值
    
    # 粒子参数
    num_particles: 50             # 粒子数
    min_particles: 20              # 最少粒子数
    max_particles: 200            # 最多粒子数
    
    # 里程计参数
    odom_frame: odom              # 里程计坐标系
    map_frame: map                # 地图坐标系
```

### 4.2 Hector

**Hector**是一种基于扫描匹配的SLAM算法，它使用高斯-牛顿法进行实时扫描对齐，不需要里程计数据。

**算法特点**：

| 特性 | 说明 |
|------|------|
| 方法 | 扫描匹配（高斯-牛顿） |
| 地图类型 | 栅格地图 |
| 优点 | 精度高，无需里程计 |
| 缺点 | 对快速移动敏感 |

**算法原理**：

Hector使用高斯-牛顿优化求解最优位姿，最小化残差函数：

$$E(\xi) = \sum_{i=1}^{n}[1 - M(S_i(\xi))]^2$$

其中 $\xi = (x, y, \theta)$ 是机器人位姿，$S_i$ 是将第 $i$ 个激光点变换到地图坐标的函数，$M$ 是地图的占用概率。

**ROS2中使用Hector**：

```bash
# 安装hector
sudo apt install ros-humble-hector-slam

# 启动hector
ros2 launch hector_slam_launch tutorial.launch.py
```

### 4.3 Cartographer

**Cartographer**是Google开发的SLAM算法，以其优秀的建图效果和实时性能著称。它采用**子图（Submap）**概念和**位姿图优化**。

**算法特点**：

| 特性 | 说明 |
|------|------|
| 方法 | 子图 + 扫描匹配 + 位姿图优化 |
| 地图类型 | 概率栅格 + 子图 |
| 优点 | 精度高，支持大规模建图 |
| 缺点 | 计算资源需求高 |

**算法核心概念**：

Cartographer将地图划分为多个子图（Submap），每个子图由有限数量的激光扫描构成。局部SLAM负责将新的扫描匹配到当前子图，产生高频的位姿估计；全局SLAM通过回环检测优化所有子图的位姿，消除累积误差。

**ROS2中使用Cartographer**：

```bash
# 安装cartographer
sudo apt install ros-humble-cartographer ros-humble-cartographer-ros

# 启动cartographer
ros2 launch cartographer_slam cartographer.launch.py
```

**参数配置**：

```lua
-- cartographer.lua
include "map_builder.lua"
include "trajectory_builder.lua"

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER_2D.min_range = 0.3
TRAJECTORY_BUILDER_2D.max_range = 8.0
TRAJECTORY_BUILDER_2D.missing_data_ray_height = 1.0
TRAJECTORY_BUILDER_2D.use_imu_data = true
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

-- 回环检测参数
POSE_GRAPH.optimize_every_n_nodes = 90
POSE_GRAPH.constraint_builder.sampling_ratio = 0.3
```

**三种算法对比**：

| 特性 | Gmapping | Hector | Cartographer |
|------|----------|--------|--------------|
| 方法 | 粒子滤波 | 扫描匹配 | 子图+图优化 |
| 里程计需求 | 需要 | 不需要 | 需要 |
| 精度 | 中 | 高 | 高 |
| 计算量 | 中 | 小 | 大 |
| 回环检测 | 无 | 无 | 有 |
| 适用场景 | 小型环境 | 无里程计场景 | 大规模建图 |

---

## 练习题

### 选择题

1. SLAM技术的核心目的是什么？
   - A) 只定位机器人位置
   - B) 只构建环境地图
   - C) 同时定位和建图
   - D) 规划机器人路径

   **答案：C**。SLAM（同步定位与地图构建）的核心目标是在未知环境中同时估计机器人位置并构建环境地图。

2. 在2D SLAM中，栅格地图的每个格子通常表示什么？
   - A) 机器人的速度
   - B. 位置的占用概率
   - C) 传感器的精度
   - D) 机器人的朝向

   **答案：B**。栅格地图（Occupancy Grid Map）将环境划分为网格，每个格子记录该位置被占用的概率。

3. 哪种2D SLAM算法不需要里程计数据？
   - A) Gmapping
   - B) Cartographer
   - C) Hector
   - D) 以上都需要

   **答案：C**。Hector SLAM基于纯扫描匹配，不需要里程计数据，适合没有里程计的无人机等平台。

4. 回环检测的主要作用是什么？
   - A) 提高扫描匹配速度
   - B) 消除累积误差
   - C) 增加粒子数量
   - D) 减少激光数据量

   **答案：B**。回环检测通过识别机器人返回曾经访问过的位置，修正位姿图以消除累积漂移误差。

### 实践题

5. 编写一个Python程序，实现简单的激光数据读取和距离计算功能。

   **参考答案**：

```python
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math

class LaserAnalyzer(Node):
    def __init__(self):
        super().__init__('laser_analyzer')
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
    def scan_callback(self, msg):
        # 1. 获取左右两侧的距离
        left_index = len(msg.ranges) - 1
        right_index = 0
        left_dist = msg.ranges[left_index] if left_index < len(msg.ranges) else float('inf')
        right_dist = msg.ranges[right_index] if right_index < len(msg.ranges) else float('inf')
        
        # 2. 计算前方的扇形区域最小距离
        front_angles = [-30, -15, 0, 15, 30]  # 度
        front_ranges = []
        for angle in front_angles:
            angle_rad = math.radians(angle)
            index = int((angle_rad - msg.angle_min) / msg.angle_increment)
            if 0 <= index < len(msg.ranges):
                r = msg.ranges[index]
                if msg.range_min < r < msg.range_max:
                    front_ranges.append(r)
        
        min_front = min(front_ranges) if front_ranges else float('inf')
        
        self.get_logger().info(
            f'左侧: {left_dist:.2f}m, 右侧: {right_dist:.2f}m, '
            f'前方最近: {min_front:.2f}m'
        )

def main(args=None):
    rclpy.init(args=args)
    node = LaserAnalyzer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

6. 简述Gmapping和Cartographer在算法原理上的主要区别。

   **参考答案**：
   
   - **Gmapping**：基于粒子滤波（RBPF），维护多个粒子表示可能的机器人位姿，每个粒子携带独立地图副本。计算量随粒子数增加而增大，适合小规模环境。
   
   - **Cartographer**：采用子图（Submap）概念，将地图划分为多个小区域。局部扫描匹配产生高频位姿估计，全局通过回环检测和位姿图优化消除累积误差。支持大规模建图，精度高但计算资源需求大。

---

## 本章小结

本章我们全面学习了2D SLAM的基础原理。SLAM概述部分，我们了解了SLAM的定义、分类和基本框架。传感器要求部分，我们详细介绍了激光雷达、里程计和IMU的作用和配置。2D SLAM原理部分，我们深入讲解了栅格地图表示、里程计估计、扫描匹配和回环检测等技术。经典算法部分，我们对比介绍了Gmapping、Hector和Cartographer三种主流算法。

2D SLAM是机器人自主导航的基础技术，掌握好这些原理对于后续学习3D SLAM和实际机器人开发都非常重要。

---

## 参考资料

### 经典论文

1. Grisetti, G., et al. "Improved techniques for grid mapping with Rao-Blackwellized particle filters." IEEE Transactions on Robotics (2007). - Gmapping原始论文

2. Kohlbrecher, S., et al. "A flexible and scalable SLAM system with full 3D motion estimation." IEEE International Conference on Robotics (2011). - Hector SLAM原始论文

3. Hess, W., et al. "Real-time loop closure in 2D LIDAR SLAM." IEEE International Conference on Robotics and Automation (2016). - Cartographer原始论文

### ROS/ROS2文档

4. ROS2 SLAM Toolbox: <https://github.com/SteveMacenski/slam_toolbox>

5. Hector SLAM: <https://github.com/tu-darmstadt-ros-pkg/hector_slam>

6. Cartographer: <https://github.com/cartographer-project/cartographer>

---

## 下节预告

下一节我们将学习**08-2 3D SLAM技术概述**，了解三维 SLAM 的基本原理和典型算法，包括LOAM、LIO-SAM等代表性算法。

---

*本章学习完成！2D SLAM是机器人定位导航的核心技术，建议大家结合实际机器人平台进行练习，加深对原理的理解。*