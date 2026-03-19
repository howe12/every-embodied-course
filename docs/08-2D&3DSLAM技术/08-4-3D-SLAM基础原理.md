# 08-4 3D SLAM基础原理

> **前置课程**：08-3 2D SLAM真实硬件实战
> **后续课程**：08-5 3D SLAM仿真实战

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：3D SLAM是移动机器人领域的重要技术，它在二维SLAM的基础上增加了高度信息，使机器人能够感知三维环境结构。本节将深入讲解3D SLAM的基础原理，包括3D点云处理、体素滤波、特征提取、位姿估计、回环检测等核心概念，并介绍LOAM、LIO-SAM等经典算法。

---

## 1. 3D SLAM概述

### 1.1 什么是3D SLAM

**3D SLAM**是在三维空间中进行同步定位与地图构建的技术。与2D SLAM相比，3D SLAM能够获取环境的深度信息，构建包含高度信息的三维地图，使机器人在复杂三维环境中具有更强的感知和导航能力。

3D SLAM的重要性体现在多个方面。首先，三维地图包含更丰富的环境信息，能够支持更复杂的任务，如无人机飞行规划、机械臂抓取、复杂地形导航等。其次，三维感知能够帮助机器人更好地理解环境结构，区分地面、墙壁、障碍物等不同元素。最后，随着多线激光雷达和深度相机的普及，3D SLAM技术正在变得越来越重要。

### 1.2 3D SLAM与2D SLAM的区别

3D SLAM与2D SLAM在多个方面存在显著差异：

| 特性 | 2D SLAM | 3D SLAM |
|------|---------|----------|
| 地图维度 | 二维平面 | 三维空间 |
| 传感器 | 单线激光雷达 | 多线激光雷达、深度相机 |
| 数据量 | 较小 | 较大 |
| 计算复杂度 | 较低 | 较高 |
| 位姿估计 | 2D位姿(x,y,θ) | 6D位姿(x,y,z,r,p,y) |
| 应用场景 | 室内平面导航 | 无人机、室外导航 |

2D SLAM假设机器人在二维平面内运动，地图是一个平面栅格。3D SLAM则需要处理完整的三维空间，位姿估计需要6个自由度（位置xyz + 姿态roll/pitch/yaw）。

### 1.3 3D SLAM的基本框架

一个完整的3D SLAM系统通常包含以下核心模块：

```
┌─────────────────────────────────────────────────────────────────┐
│                        3D SLAM 系统框架                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │   3D传感器    │───▶│   点云处理    │───▶│   特征提取    │    │
│  │ (激光/深度)   │    │  (滤波/降采样) │    │  (边缘/平面)  │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│                                                      │         │
│                              ┌──────────────┐         │         │
│                              │   位姿估计    │◀────────┤         │
│                              │  (里程计/优化)│         │         │
│                              └──────────────┘         │         │
│                                   │                   │         │
│                              ┌──────────────┐         │         │
│                              │   回环检测    │◀────────┤         │
│                              │  (scan-context)│        │         │
│                              └──────────────┘         │         │
│                                   │                   │         │
│                                   ▼                   │         │
│                              ┌──────────────┐         │         │
│                              │   后端优化    │◀────────┘         │
│                              │   (因子图)    │                   │
│                              └──────────────┘                   │
│                                   │                             │
│                                   ▼                             │
│                              ┌──────────────┐                   │
│                              │   3D地图输出  │                   │
│                              │  (点云/网格)  │                   │
│                              └──────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**传感器数据层**：负责采集3D环境信息，包括多线激光雷达点云、深度相机图像、IMU数据等。

**点云处理层**：对原始点云进行预处理，包括体素滤波降采样、去噪处理等。

**特征提取层**：从处理后的点云中提取特征信息，包括边缘特征（特征点）和平面特征（平面点）。

**前端里程计层**：基于特征匹配进行实时位姿估计，提供高频的局部定位结果。

**回环检测层**：检测机器人是否回到了之前访问过的位置，用于消除累积误差。

**后端优化层**：基于因子图优化，对全局位姿进行联合优化，构建一致的3D地图。

---

## 2. 3D点云处理

3D点云是3D SLAM的核心数据形式，原始点云通常包含数十万甚至数百万个点，数据量庞大且存在噪声。本节介绍点云的基本处理方法。

### 2.1 点云数据结构

在ROS2中，3D点云通常使用`sensor_msgs/PointCloud2`消息类型传输：

```yaml
# sensor_msgs/msg/PointCloud2.msg
Header header                    # 时间戳和坐标系
uint32 height                    # 点云高度（用于组织结构）
uint32 width                     # 点云宽度
PointField[] fields             # 点字段描述
bool is_bigendian               # 字节序
bool is_dense                   # 是否稠密
```

PointField定义了点云中每个点的数据结构：

```yaml
# PointField定义示例
- name: x
  offset: 0
  datatype: 7  # FLOAT32
  count: 1
- name: y
  offset: 4
  datatype: 7
  count: 1
- name: z
  offset: 8
  datatype: 7
  count: 1
- name: intensity
  offset: 12
  datatype: 7
  count: 1
```

### 2.2 使用PCL处理点云

**Point Cloud Library (PCL)** 是处理点云的主流C++库，ROS2提供了pcl_ros功能包进行集成。

**安装PCL**：

```bash
# Ubuntu安装
sudo apt-get install libpcl-dev
sudo apt-get install ros-humble-pcl-*
```

**基本点云操作示例**：

```python
# Python中使用pypcl（需安装）
import pcl
import numpy as np

# 从点云创建PCL对象
def create_pcl_point_cloud(points):
    """从numpy数组创建PCL点云"""
    cloud = pcl.PointCloud()
    cloud.from_array(points.astype(np.float32))
    return cloud

# 体素滤波
def voxel_filter(cloud, leaf_size=0.1):
    """体素滤波降采样"""
    vox = cloud.make_voxel_grid_filter()
    vox.set_leaf_size(leaf_size, leaf_size, leaf_size)
    return vox.filter()

# 统计离群点移除
def remove_outliers(cloud, mean_k=50, std_threshold=1.0):
    """统计离群点移除"""
    sor = cloud.make_statistical_outlier_filter()
    sor.set_mean_k(mean_k)
    sor.set_std_deviation_mul_thresh(std_threshold)
    return sor.filter()

# 平面分割（RANSAC）
def segment_plane(cloud, max_distance=0.01):
    """分割平面（地面）"""
    seg = cloud.make_segmenter()
    seg.set_model_type(pcl.SACMODEL_PLANE)
    seg.set_method_type(pcl.SAC_RANSAC)
    seg.set_distance_threshold(max_distance)
    indices, model = seg.segment()
    return indices, model
```

### 2.3 点云坐标变换

3D SLAM中经常需要进行点云坐标变换，将点云从传感器坐标系转换到世界坐标系：

```python
import numpy as np
from scipy.spatial.transform import Rotation as R

def transform_point_cloud(points, translation, quaternion):
    """
    对点云进行刚体变换
    
    参数:
        points: Nx3 numpy数组
        translation: [x, y, z] 平移向量
        quaternion: [x, y, z, w] 四元数
    
    返回:
        变换后的点云
    """
    # 创建旋转矩阵
    rot = R.from_quat(quaternion)
    rotation_matrix = rot.as_matrix()
    
    # 应用变换: p' = R * p + t
    transformed = (rotation_matrix @ points.T).T + np.array(translation)
    
    return transformed

# 示例
points = np.random.randn(1000, 3)  # 1000个3D点
translation = [1.0, 2.0, 0.5]
quaternion = [0, 0, 0, 1]  # 无旋转

transformed_points = transform_point_cloud(points, translation, quaternion)
print(f"原始点云形状: {points.shape}")
print(f"变换后点云形状: {transformed_points.shape}")
```

---

## 3. 体素滤波

**体素滤波（Voxel Filter）**是3D SLAM中最重要的点云降采样方法，它将空间划分为均匀的体素网格，每个体素只保留一个代表点。

### 3.1 体素滤波原理

体素滤波的核心思想是将空间划分为相同大小的立方体（体素），然后对每个体素内的点进行压缩：

```
原始点云                          体素滤波后
                                  
    *                               
   * *          *                   *
  *   *        * *        *        * *
 *     *      *   *      * *      *   *
*       *    *     *    *   *    *     *
   * *        * *        *        *
     *          *          *        *
```

每个立方体代表一个体素，体素内的点用其质心或中心点代替。

### 3.2 体素滤波公式

体素滤波的几何定义如下：

设体素大小为 $d$，点云中任意点 $p_i = (x_i, y_i, z_i)$，则该点所属体素的索引为：

$$
\text{index}_x = \left\lfloor \frac{x_i - x_{\min}}{d} \right\rfloor
$$

$$
\text{index}_y = \left\lfloor \frac{y_i - y_{\min}}{d} \right\rfloor
$$

$$
\text{index}_z = \left\lfloor \frac{z_i - z_{\min}}{d} \right\rfloor
$$

体素内所有点的质心计算：

$$
p_{\text{centroid}} = \frac{1}{N} \sum_{i=1}^{N} p_i
$$

其中 $N$ 是该体素内点的数量。

### 3.3 体素滤波实现

```python
import numpy as np

def voxel_filter(points, voxel_size):
    """
    实现体素滤波
    
    参数:
        points: Nx3 numpy数组
        voxel_size: 体素大小 [dx, dy, dz]
    
    返回:
        降采样后的点云和索引
    """
    # 计算体素索引
    min_coords = points.min(axis=0)
    voxel_indices = np.floor((points - min_coords) / voxel_size).astype(np.int32)
    
    # 唯一体素索引
    unique_voxels, inverse_indices = np.unique(
        voxel_indices, axis=0, return_inverse=True
    )
    
    # 计算每个体素的质心
    filtered_points = []
    for i in range(len(unique_voxels)):
        mask = inverse_indices == i
        centroid = points[mask].mean(axis=0)
        filtered_points.append(centroid)
    
    return np.array(filtered_points), inverse_indices

# 示例
np.random.seed(42)
original_points = np.random.randn(10000, 3) * 10
voxel_size = np.array([0.5, 0.5, 0.5])

filtered_points, indices = voxel_filter(original_points, voxel_size)
print(f"原始点数: {len(original_points)}")
print(f"滤波后点数: {len(filtered_points)}")
print(f"压缩比: {len(original_points)/len(filtered_points):.2f}x")
```

```python
# 使用Open3D库（更高效的实现）
import open3d as o3d

def voxel_filter_open3d(point_cloud, voxel_size=0.05):
    """使用Open3D进行体素滤波"""
    # 下采样（体素滤波）
    downpcd = point_cloud.voxel_down_sample(voxel_size)
    return downpcd

# 从numpy数组创建Open3D点云
def numpy_to_open3d(points):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    return pcd

# 使用示例
# points = np.random.randn(10000, 3)
# pcd = numpy_to_open3d(points)
# filtered = voxel_filter_open3d(pcd, voxel_size=0.1)
# filtered_points = np.asarray(filtered.points)
```

---

## 4. 特征提取

3D SLAM中的特征提取是从点云中提取具有显著性和可重复性的几何特征，用于后续的位姿估计。

### 4.1 边缘特征与平面特征

3D SLAM中最常用的特征分为两类：

**边缘特征（Edge Features）**：对应场景中的突变区域，如墙角、物体边缘等。边缘特征在点云中表现为曲率较大的点。

**平面特征（Planar Features）**：对应场景中的平滑区域，如地面、墙面等。平面特征在点云中表现为曲率较小的点。

### 4.2 曲率计算

曲率是区分边缘特征和平面特征的关键指标。对于点云中的每个点，通过其邻近点计算曲率：

设点 $p_i$ 的 $k$ 个最近邻为 $\{p_{i1}, p_{i2}, ..., p_{ik}\}$，构建局部协方差矩阵：

$$
C = \frac{1}{k} \sum_{j=1}^{k}(p_{ij} - \bar{p})(p_{ij} - \bar{p})^T
$$

其中 $\bar{p}$ 是邻域点的质心：

$$
\bar{p} = \frac{1}{k} \sum_{j=1}^{k} p_{ij}
$$

对协方差矩阵 $C$ 进行特征值分解，得到特征值 $\lambda_1 \geq \lambda_2 \geq \lambda_3 \geq 0$。曲率可以定义为：

$$
c = \frac{\lambda_3}{\lambda_1 + \lambda_2 + \lambda_3}
$$

- **曲率较大** ($\lambda_3$ 相对较大)：边缘特征
- **曲率较小** ($\lambda_3$ 相对较小)：平面特征

### 4.3 特征提取实现

```python
import numpy as np
from scipy.spatial import KDTree

def compute_curvature(points, k=10):
    """
    计算点云中每个点的曲率
    
    参数:
        points: Nx3 点云
        k: 邻域点数
    
    返回:
        curvatures: 每个点的曲率
    """
    n = len(points)
    curvatures = np.zeros(n)
    
    # 构建KD树
    tree = KDTree(points)
    
    for i in range(n):
        # 获取k个最近邻
        distances, indices = tree.query(points[i], k=k+1)
        # 排除自身
        neighbors = points[indices[1:]]
        
        if len(neighbors) < 3:
            curvatures[i] = 0
            continue
        
        # 计算质心
        centroid = neighbors.mean(axis=0)
        
        # 中心化
        centered = neighbors - centroid
        
        # 协方差矩阵
        cov = centered.T @ centered / len(neighbors)
        
        # 特征值分解
        eigenvalues = np.linalg.eigvalsh(cov)
        eigenvalues = np.sort(eigenvalues)[::-1]
        
        # 计算曲率
        lambda_sum = eigenvalues.sum()
        if lambda_sum > 1e-10:
            curvatures[i] = eigenvalues[2] / lambda_sum
    
    return curvatures

def extract_features(points, num_features=100, k=10):
    """
    提取边缘特征和平面特征
    
    参数:
        points: Nx3 点云
        num_features: 每类特征数量
        k: 邻域点数
    
    返回:
        edge_points: 边缘特征点
        planar_points: 平面特征点
    """
    # 计算曲率
    curvatures = compute_curvature(points, k)
    
    # 根据曲率排序
    edge_indices = np.argsort(curvatures)[-num_features:]
    planar_indices = np.argsort(curvatures)[:num_features]
    
    edge_points = points[edge_indices]
    planar_points = points[planar_indices]
    
    return edge_points, planar_points, curvatures

# 示例
np.random.seed(42)
# 创建一个包含平面和边缘的简单场景
plane_points = np.random.randn(500, 3) * 0.1 + np.array([0, 0, 0])
edge_points = np.random.randn(100, 3) * 0.05 + np.array([1, 0, 0])
all_points = np.vstack([plane_points, edge_points])

edge, planar, curv = extract_features(all_points, num_features=20)
print(f"提取边缘特征: {len(edge)} 点")
print(f"提取平面特征: {len(planar)} 点")
```

### 4.4 LOAM特征提取

LOAM（Laser Odometry and Mapping）算法使用更精细的特征提取策略：

```python
def loam_feature_extraction(points, scan_id, curvature_threshold=0.5):
    """
    LOAM风格的特征提取
    
    参数:
        points: 激光扫描点云
        scan_id: 扫描线ID
        curvature_threshold: 曲率阈值
    
    返回:
        edge_points: 边缘特征
        planar_points: 平面特征
        less_sharp_points: 不那么尖锐的点
        less_flat_points: 不那么平坦的点
    """
    n = len(points)
    curvatures = compute_curvature(points, k=5)
    
    edge_points = []
    planar_points = []
    less_sharp_points = []
    less_flat_points = []
    
    for i in range(n):
        c = curvatures[i]
        
        # 跳过遮挡区域的点
        if scan_id[i] != scan_id[i-1] or scan_id[i] != scan_id[i+1]:
            continue
        
        # 边缘特征 (曲率大)
        if c > curvature_threshold:
            edge_points.append(points[i])
        elif c > 0.1 * curvature_threshold:
            less_sharp_points.append(points[i])
        
        # 平面特征 (曲率小)
        if c < 0.001:
            planar_points.append(points[i])
        elif c < 0.1:
            less_flat_points.append(points[i])
    
    return np.array(edge_points), np.array(planar_points), \
           np.array(less_sharp_points), np.array(less_flat_points)
```

---

## 5. 位姿估计

**位姿估计**是3D SLAM的核心问题，目标是从连续帧点云中估计机器人位姿的变化。

### 5.1 点到点ICP

**迭代最近点（Iterative Closest Point, ICP）**是最经典的点云配准算法。给定两个点云，ICP通过迭代优化找到最优的刚性变换：

$$
T^* = \arg\min_T \sum_{i=1}^{N} \|p_i - T(q_i)\|^2
$$

其中 $p_i$ 是源点云中的点，$q_i$ 是目标点云中的对应点，$T$ 是刚性变换（旋转+平移）。

```python
import numpy as np
from scipy.spatial import KDTree

def icp(source, target, max_iterations=50, tolerance=1e-5):
    """
    点到点ICP算法
    
    参数:
        source: 源点云 Nx3
        target: 目标点云 Mx3
        max_iterations: 最大迭代次数
        tolerance: 收敛阈值
    
    返回:
        transformation: [R|t] 4x4变换矩阵
        distances: 对应点距离
    """
    # 初始化
    src = source.copy()
    prev_error = float('inf')
    
    # 构建目标点云KD树
    target_tree = KDTree(target)
    
    for i in range(max_iterations):
        # 步骤1: 找最近邻
        distances, indices = target_tree.query(src)
        
        # 步骤2: 计算变换
        # 计算质心
        src_centroid = src.mean(axis=0)
        tgt_centroid = target[indices].mean(axis=0)
        
        # 中心化
        src_centered = src - src_centroid
        tgt_centered = target[indices] - tgt_centroid
        
        # 计算H
        H = src_centered.T @ tgt_centered
        
        # SVD分解
        U, S, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        
        # 检测反射
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        
        t = tgt_centroid - R @ src_centroid
        
        # 步骤3: 应用变换
        src = (R @ src.T).T + t
        
        # 步骤4: 检查收敛
        mean_error = np.mean(distances)
        if abs(prev_error - mean_error) < tolerance:
            break
        prev_error = mean_error
    
    # 构建变换矩阵
    transformation = np.eye(4)
    transformation[:3, :3] = R
    transformation[:3, 3] = t
    
    return transformation, distances

# 示例
np.random.seed(42)
# 创建两个有重叠的点云
theta = np.pi / 6
R_gt = np.array([
    [np.cos(theta), -np.sin(theta), 0],
    [np.sin(theta), np.cos(theta), 0],
    [0, 0, 1]
])
t_gt = np.array([1.0, 0.5, 0.0])

target = np.random.randn(500, 3) * 2
source = (R_gt @ target.T).T + t_gt + np.random.randn(500, 3) * 0.1

# 运行ICP
T_result, distances = icp(source, target)
print(f"ICP估计的旋转:\n{T_result[:3, :3]}")
print(f"ICP估计的平移:\n{T_result[:3, 3]}")
print(f"真实旋转:\n{R_gt}")
print(f"真实平移:\n{t_gt}")
```

### 5.2 点到平面ICP

相比点到点ICP，**点到平面ICP**利用平面法向量信息，通常收敛更快：

```python
def icp_point_to_plane(source, target, normals, max_iterations=30):
    """
    点到平面ICP算法
    
    参数:
        source: 源点云
        target: 目标点云
        normals: 目标点云的法向量
    """
    src = source.copy()
    
    for i in range(max_iterations):
        # 找最近邻
        tree = KDTree(target)
        distances, indices = tree.query(src)
        
        # 构建线性系统
        # 对于点到平面: (R*p + t - q) · n = 0
        A = np.zeros((len(src), 6))
        b = np.zeros(len(src))
        
        for j in range(len(src)):
            p = src[j]
            q = target[indices[j]]
            n = normals[indices[j]]
            
            # 构建方程: [p]_× * R + I * t = n
            A[j, :3] = np.cross(p, n)
            A[j, 3:] = n
            b[j] = np.dot(q - p, n)
        
        # 求解最小二乘
        x, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
        
        # 提取旋转和平移
        delta_R = np.eye(3)
        delta_R[:] = np.array([
            [1, -x[2], x[1]],
            [x[2], 1, -x[0]],
            [-x[1], x[0], 1]
        ])
        
        delta_t = x[3:]
        
        # 更新
        src = (delta_R @ src.T).T + delta_t
    
    return src, distances
```

### 5.3 基于特征的位姿估计

LOAM等算法使用特征匹配进行位姿估计，效率更高：

```python
def feature_based_pose_estimation(
    source_edge, target_edge,
    source_planar, target_planar,
    K_edge=5, K_planar=3
):
    """
    基于特征的位姿估计
    
    参数:
        source_edge/target_edge: 边缘特征
        source_planar/target_planar: 平面特征
        K_edge: 边缘特征对应邻居数
        K_planar: 平面特征对应邻居数
    
    返回:
        T: 4x4 变换矩阵
    """
    # 边缘特征匹配（点到线）
    tree_edge = KDTree(target_edge)
    edge_distances, edge_indices = tree_edge.query(source_edge)
    
    # 平面特征匹配（点到面）
    tree_planar = KDTree(target_planar)
    planar_distances, planar_indices = tree_planar.query(source_planar)
    
    # 组合优化问题
    # 这里简化处理，使用所有特征
    all_source = np.vstack([source_edge, source_planar])
    all_target_indices = np.hstack([edge_indices, planar_indices])
    all_target = np.vstack([target_edge, target_planar])[all_target_indices]
    
    # 使用SVD求解
    T, _ = icp(all_source, all_target, max_iterations=20)
    
    return T
```

---

## 6. 回环检测

**回环检测（Loop Closure Detection）**是3D SLAM中消除累积误差的关键技术。当机器人回到之前访问过的位置时，检测到回环并进行全局优化，可以显著提升地图一致性。

### 6.1 回环检测问题

在长时间的SLAM运行中，位姿估计的误差会累积，导致地图出现"漂移"。回环检测通过检测重复访问的位置，提供额外的约束来修正累积误差。

```
        ┌─────────┐
        │   回环   │
        │    ↻    │
        ▼         │
   ───────────▶   │
   │              │
   │ 累积误差     │ 优化后
   ▼              │
   ───────────▶   │
        │         │
        ▼         ▼
   ─────────── ─────────
   优化前          优化后
```

### 6.2 基于扫描上下文的回环检测

**Scan Context**是一种流行的点云回环检测方法，它将3D点云转换为2D描述子：

```python
import numpy as np

def compute_scan_context(points, num_rings=20, num_sectors=60, max_height=10.0):
    """
    计算Scan Context描述子
    
    参数:
        points: 点云 Nx3 [x, y, z]
        num_rings: 环的数量
        num_sectors: 扇区的数量
        max_height: 最大高度
    
    返回:
        scan_context: 2D描述子
    """
    # 将点云从3D投影到2D
    # 使用极坐标
    
    # 过滤地面点以下的部分
    points = points[points[:, 2] > 0]
    
    # 计算极坐标
    r = np.sqrt(points[:, 0]**2 + points[:, 1]**2)
    theta = np.arctan2(points[:, 1], points[:, 0])
    
    # 环和扇区索引
    ring_indices = np.clip((r / max_height * num_rings).astype(int), 0, num_rings-1)
    sector_indices = np.clip(((theta + np.pi) / (2*np.pi) * num_sectors).astype(int), 0, num_sectors-1)
    
    # 构建Scan Context
    scan_context = np.zeros((num_rings, num_sectors))
    
    for i in range(len(points)):
        ring = ring_indices[i]
        sector = sector_indices[i]
        z = points[i, 2]
        scan_context[ring, sector] = max(scan_context[ring, sector], z)
    
    return scan_context

def compute_scan_context_distance(ctx1, ctx2):
    """
    计算两个Scan Context的距离
    
    使用列方向的循环移位来找最优匹配
    """
    num_sectors = ctx1.shape[1]
    min_distance = float('inf')
    best_shift = 0
    
    for shift in range(num_sectors):
        # 循环移位
        shifted = np.roll(ctx2, shift, axis=1)
        # 计算距离
        distance = np.sum(np.abs(ctx1 - shifted)) / (ctx1.shape[0] * ctx1.shape[1])
        
        if distance < min_distance:
            min_distance = distance
            best_shift = shift
    
    return min_distance, best_shift

# 示例
np.random.seed(42)
# 模拟两个位置的点云
points1 = np.random.randn(500, 3)
points1[:, 2] = np.abs(points1[:, 2])  # 都在地面上

# 模拟机器人移动后回到原点
R = np.eye(3)
t = np.array([0.1, 0.1, 0])
points2 = (R @ points1.T).T + t

# 计算Scan Context
ctx1 = compute_scan_context(points1)
ctx2 = compute_scan_context(points2)

# 计算相似度
distance, shift = compute_scan_context_distance(ctx1, ctx2)
print(f"Scan Context距离: {distance:.4f}")
print(f"最优移位: {shift}")
```

### 6.3 基于词袋的回环检测

**词袋模型（Bag of Words）**是另一种常用的回环检测方法：

```python
class BoWLoopDetector:
    def __init__(self, vocabulary_path=None):
        self.vocabulary = {}
        self.history = []
        self.features_history = []
        
    def train_vocabulary(self, features_list, num_clusters=100):
        """
        使用K-Means训练词汇表
        """
        from sklearn.cluster import KMeans
        
        # 合并所有特征
        all_features = np.vstack(features_list)
        
        # K-Means聚类
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        kmeans.fit(all_features)
        
        self.vocabulary['centers'] = kmeans.cluster_centers_
        self.vocabulary['kmeans'] = kmeans
        
    def compute_bow(self, features):
        """计算词袋向量"""
        if len(features) == 0:
            return np.zeros(len(self.vocabulary['centers']))
        
        # 分配到最近的词
        words = self.vocabulary['kmeans'].predict(features)
        
        # 统计词频
        bow = np.bincount(words, minlength=len(self.vocabulary['centers']))
        
        # TF-IDF加权（简化版本）
        bow = bow.astype(float)
        bow = bow / (np.linalg.norm(bow) + 1e-10)
        
        return bow
    
    def detect_loop(self, features, threshold=0.5):
        """
        检测回环
        
        返回:
            loop_index: 回环候选的索引，-1表示未检测到
            score: 相似度得分
        """
        # 计算当前帧的词袋
        bow = self.compute_bow(features)
        
        # 与历史帧比较
        best_score = 0
        best_idx = -1
        
        # 只比较一定时间间隔之前的帧
        min_interval = 30
        
        for i in range(len(self.history) - min_interval):
            hist_bow = self.history[i]
            
            # 余弦相似度
            score = np.dot(bow, hist_bow) / (np.linalg.norm(bow) * np.linalg.norm(hist_bow) + 1e-10)
            
            if score > best_score:
                best_score = score
                best_idx = i
        
        if best_score > threshold:
            return best_idx, best_score
        
        # 保存到历史
        self.history.append(bow)
        self.features_history.append(features)
        
        return -1, 0.0
```

---

## 7. 经典算法介绍

### 7.1 LOAM算法

**LOAM（Laser Odometry and Mapping）**是Zhang Ji等人在2014年提出的经典3D SLAM算法。它利用2D激光雷达进行3D建图，通过分离里程计和建图两个模块实现了高效实时的3D SLAM。

**核心思想**：
- 使用线扫描运动失真补偿
- 提取边缘特征和平面特征
- 使用两阶段优化（高频里程计 + 低频建图）

**算法框架**：

```python
# LOAM核心流程伪代码
class LOAM:
    def __init__(self):
        self.odometry = LaserOdometry()  # 高频里程计
        self.mapping = Mapping()         # 低频建图
        self.accumulated_cloud = None    # 累积点云
        
    def process_point_cloud(self, cloud, timestamp):
        """处理一帧点云"""
        # 1. 特征提取
        edge_points, planar_points = extract_features(cloud)
        
        # 2. 里程计估计（高频，10Hz）
        odometry_result = self.odometry.estimate(
            edge_points, planar_points
        )
        
        # 3. 累积点云
        self.accumulated_cloud = self.transform_point_cloud(
            cloud, odometry_result
        )
        
        # 4. 建图（低频，1Hz）
        if self.should_run_mapping():
            map_result = self.mapping.optimize(
                self.accumulated_cloud
            )
            return map_result
        
        return odometry_result
```

**LOAM的特点**：
- 只需要2D激光雷达（通过运动实现3D扫描）
- 实时性能好，在普通PC上可达10Hz
- 精度较高，适合室内环境
- 开源代码：https://github.com/laboshinl/loam_velodyne

### 7.2 LIO-SAM算法

**LIO-SAM（LIOSAM）**是Tixiao Shan等人在2020年提出的基于因子图的激光惯性SLAM系统。它在LOAM基础上集成了IMU、GPS等多种传感器，实现了更高精度和鲁棒性的3D SLAM。

**核心创新**：
- 因子图优化框架，支持多传感器融合
- 滑动窗口优化
- 紧耦合的IMU预积分

**算法框架**：

```
┌─────────────────────────────────────────────────────────┐
│                    LIO-SAM 系统框架                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐    ┌─────────────┐                   │
│  │   LiDAR点云  │    │    IMU数据   │                   │
│  └──────┬──────┘    └──────┬──────┘                   │
│         │                   │                          │
│         ▼                   ▼                          │
│  ┌─────────────────────────────────┐                   │
│  │     特征提取 (Feature Extraction)│                   │
│  └──────────────┬──────────────────┘                   │
│                 │                                        │
│                 ▼                                        │
│  ┌─────────────────────────────────┐                   │
│  │    IMU预积分 (IMU Preintegration) │                  │
│  └──────────────┬──────────────────┘                   │
│                 │                                        │
│                 ▼                                        │
│  ┌─────────────────────────────────┐                   │
│  │    里程计估计 (Odometry Estimation) │                │
│  └──────────────┬──────────────────┘                   │
│                 │                                        │
│                 ▼                                        │
│  ┌─────────────────────────────────┐                   │
│  │   因子图优化 (Factor Graph Optimization) │             │
│  │   ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐          │
│  │   │ GPS   │ │ Loop  │ │ IMU   │ │激光里程│          │
│  │   │因子   │ │ 因子   │ │ 因子   │ │ 因子   │          │
│  │   └───────┘ └───────┘ └───────┘ └───────┘          │
│  └──────────────┬──────────────────┘                   │
│
│                 │                                        │
│                 ▼                                        │
│  ┌─────────────────────────────────┐                   │
│  │   3D点云地图输出                 │                   │
│  └─────────────────────────────────┘                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**LIO-SAM的特点**：
- 支持多种传感器融合（激光雷达+IMU+GPS）
- 因子图优化，全局一致性更好
- 实时性能优秀
- 支持回环检测
- 开源代码：https://github.com/TixiaoShan/LIO-SAM

---

## 练习题

### 选择题

1. 3D SLAM与2D SLAM的主要区别是什么？
   - A) 3D SLAM使用更多的传感器
   - B) 3D SLAM估计6D位姿，2D SLAM估计3D位姿
   - C) 3D SLAM估计6D位姿(x,y,z,r,p,y)，2D SLAM估计3D位姿(x,y,θ)
   - D) 3D SLAM不需要回环检测
   
   **答案：C**。3D SLAM需要在三维空间中定位，位姿估计需要6个自由度，包括位置(x,y,z)和姿态(roll,pitch,yaw)；2D SLAM通常只需要3个自由度。

2. 体素滤波的主要目的是什么？
   - A) 增加点云密度
   - B. 降采样，减少计算量
   - C) 去除噪声
   - D) 分割地面
   
   **答案：B**。体素滤波通过将空间划分为体素网格，对每个体素只保留一个代表点（通常是质心），从而达到降采样、减少计算量的目的。

3. 在点云特征提取中，如何区分边缘特征和平面特征？
   - A) 边缘特征曲率大，平面特征曲率小
   - B) 边缘特征曲率小，平面特征曲率大
   - C) 边缘特征点云密度高，平面特征点云密度低
   - D) 无法区分
   
   **答案：A**。边缘特征对应场景中的突变区域，曲率较大；平面特征对应场景中的平滑区域，曲率较小。通过计算局部协方差矩阵的特征值可以估计曲率。

4. Scan Context回环检测方法的核心思想是什么？
   - A) 使用词袋模型
   - B) 将3D点云投影到2D极坐标网格
   - C) 使用ICP匹配
   - D) 使用深度学习
   
   **答案：B**。Scan Context将3D点云从极坐标视角投影到2D环-扇区网格，用每个网格单元的最大高度值作为描述子。

### 实践题

5. 实现一个简单的体素滤波函数，对输入的点云进行降采样。
   
   **参考答案**：
   
   ```python
   import numpy as np
   
   def voxel_filter(points, voxel_size):
       """
       实现体素滤波
       """
       # 计算体素索引
       min_coords = points.min(axis=0)
       voxel_indices = np.floor((points - min_coords) / voxel_size).astype(np.int32)
       
       # 唯一体素索引
       unique_voxels, inverse_indices = np.unique(
           voxel_indices, axis=0, return_inverse=True
       )
       
       # 计算每个体素的质心
       filtered_points = []
       for i in range(len(unique_voxels)):
           mask = inverse_indices == i
           centroid = points[mask].mean(axis=0)
           filtered_points.append(centroid)
       
       return np.array(filtered_points)
   
   # 测试
   points = np.random.randn(10000, 3) * 10
   filtered = voxel_filter(points, voxel_size=0.5)
   print(f"原始点数: {len(points)}, 滤波后: {len(filtered)}")
   ```

6. 实现点到点ICP算法的核心步骤。
   
   **提示**：
   - 构建KD树进行最近邻搜索
   - 使用SVD分解计算旋转和平移
   - 迭代直到收敛

---

## 本章小结

本章我们全面学习了3D SLAM的基础原理。在3D SLAM概述部分，我们了解了3D SLAM与2D SLAM的区别以及基本框架。在点云处理部分，我们学习了点云数据结构和PCL库的基本使用方法。在体素滤波部分，我们深入理解了体素滤波的原理并实现了相关代码。在特征提取部分，我们学习了如何通过曲率计算区分边缘特征和平面特征。在位姿估计部分，我们详细讲解了ICP算法的原理和实现。在回环检测部分，我们介绍了Scan Context和词袋模型两种方法。最后，我们介绍了LOAM和LIO-SAM两个经典算法。

3D SLAM是机器人感知领域的重要技术，掌握好这些基础原理，将为后续的3D SLAM实战课程打下坚实基础。

---

## 参考资料

### 经典论文

1. Zhang J, Singh S. LOAM: LiDAR Odometry and Mapping in Real-time[C]. Robotics: Science and Systems, 2014.

2. Shan T, Englot B. LIO-SAM: Tightly-coupled Lidar Inertial Odometry via Optimization and Factor Graph[C]. IEEE International Conference on Robotics and Automation (ICRA), 2021.

3. Kim G, Kim A. Scan Context: Egocentric Spatial Descriptor for Place Recognition within 3D Point Cloud Map[C]. IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS), 2018.

### 开源项目

4. LOAM Velodyne: https://github.com/laboshinl/loam_velodyne

5. LIO-SAM: https://github.com/TixiaoShan/LIO-SAM

6. A-LOAM: https://github.com/HoMingLab/aloam

### 学习资源

7. PCL官方文档: https://pointclouds.org/documentation/

8. Open3D文档: http://www.open3d.org/docs/release/

---

## 下节预告

下一节我们将学习**08-5 3D SLAM仿真实战**，在仿真环境中实践3D SLAM算法的配置和使用。

---

*本章学习完成！3D SLAM是现代机器人感知的重要技术，建议大家多加练习，熟练掌握点云处理和特征提取的方法。*
