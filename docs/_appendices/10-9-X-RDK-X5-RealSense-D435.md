# 10-9-X RDK-X5 RealSense D435 深度相机接入

> **前置课程**：10-9 点云与深度相机
> **对应课程**：10-9 点云与深度相机（RDK-X5 适配）

---

## 目录

1. [RealSense D435 概述](#1-realsense-d435-概述)
2. [硬件准备与连接](#2-硬件准备与连接)
3. [环境搭建](#3-环境搭建)
4. [设备连接与验证](#4-设备连接与验证)
5. [ROS2 驱动使用](#5-ros2-驱动使用)
6. [Python 图像处理实战](#6-python-图像处理实战)
7. [深度应用](#7-深度应用)
8. [部署与验证](#8-部署与验证)
9. [常见问题排查](#9-常见问题排查)
10. [练习题](#练习题)
11. [答案](#答案)

---

## 1. RealSense D435 概述

### 1.1 D435 产品线对比

Intel RealSense D400 系列包含多款深度相机，以下是常见型号的对比：

| 型号 | 深度分辨率 | 深度范围 | RGB分辨率 | 深度FOV | IMU | 典型场景 |
|------|-----------|---------|----------|---------|-----|---------|
| D415 | 1280×720 | 0.16~10m | 1920×1080 | 65°×40° | 否 | 近距离精细扫描 |
| **D435** | 1280×720 | 0.1~10m | 1920×1080 | 87°×58° | 否 | 机器人导航、避障 |
| **D435i** | 1280×720 | 0.1~10m | 1920×1080 | 87°×58° | **是** | 室内SLAM、VIO |

> **本课程以 D435 为例**，D435i 的使用方法几乎完全相同，区别在于 D435i 额外提供 IMU 数据（加速度计+陀螺仪）。

### 1.2 深度测量原理

RealSense D435 采用 **主动红外立体视觉（Active IR Stereo Vision）** 原理：

```
┌──────────────────────────────────────────────────────────────┐
│                    RealSense D435 深度测量原理                │
│                                                              │
│   左侧红外相机          红外投射器         右侧红外相机        │
│   (IR Camera L)    ──(IR Projector)──>  (IR Camera R)       │
│        │                                   │                │
│        │<───── 视差 (Disparity) ──────────>|                │
│        │                                   │                │
│        └──────────────► 深度图 ◄───────────┘                │
│                                                              │
│   红外投射器：投射不可见的红外斑点图案，增强纹理，提升无纹理区域的深度精度      │
│   立体匹配  ：通过左右红外图像匹配计算视差，再转换为深度值             │
└──────────────────────────────────────────────────────────────┘
```

**深度计算公式**：

```
Z（深度）= f（焦距）× B（基线） / d（视差）
```

- `f`：红外相机的焦距（单位：像素）
- `B`：左右红外相机之间的物理距离（基线，约 55mm）
- `d`：匹配得到的视差值（单位：像素）
- `Z`：目标到相机的实际深度（单位：mm）

**视差与深度的关系**：视差越大，深度越近；视差越小，深度越远。

### 1.3 RGB-D 多模态输出

RealSense D435 同时输出多种数据流：

| 数据流 | 分辨率 | 帧率 | 说明 |
|--------|--------|------|------|
| 深度图（Depth） | 1280×720 / 848×480 | 最高 90fps | 每个像素保存深度值（mm） |
| 彩色图（Color） | 1920×1080 / 1280×720 | 最高 30fps | RGB彩色图像 |
| 红外左图（IR L） | 1280×720 | 最高 90fps | 左侧红外相机图像 |
| 红外右图（IR R） | 1280×720 | 最高 90fps | 右侧红外相机图像 |
| 点云（Point Cloud） | 1280×720 | 最高 90fps | 3D点坐标 |

### 1.4 RDK-X5 USB 接口要求

RealSense D435 需要 **USB 3.0** 接口才能达到最佳性能：

| USB 版本 | 深度帧率 | 彩色帧率 | 说明 |
|----------|---------|---------|------|
| USB 2.0 | 最高 30fps | 最高 15fps | 可用但性能受限 |
| **USB 3.0** | 最高 90fps | 最高 30fps | **推荐** |

> **注意**：RDK-X5 开发板的 USB 3.0 接口标识为蓝色（USB 3.0），请务必将 D435 连接至蓝色 USB 接口。

---

## 2. 硬件准备与连接

### 2.1 硬件清单

| 物品 | 说明 |
|------|------|
| RDK-X5 开发板 | 地平线 RDK-X5（BSP 5.10+ 系统） |
| Intel RealSense D435 或 D435i | 深度相机 |
| USB 3.0 数据线 | Type-A to Type-C，长度建议 ≤3m |
| 12V 电源适配器 | RDK-X5 供电要求 ≥12V/2A |
| HDMI 显示器 | 用于查看预览效果 |
| PC（用于 SSH） | 与 RDK-X5 同一局域网 |

### 2.2 硬件连接

> ⚠️ **警告**：连接 RealSense D435 前，请确保使用 **USB 3.0 数据线**！USB 2.0 线无法保证深度相机的正常工作！

**连接步骤**：

**Step 1：确认 USB 接口**

找到 RDK-X5 开发板上标识为 **蓝色** 的 USB 3.0 接口（通常标注为 USB 3.0 或 SS）。

**Step 2：连接相机**

```bash
# 将 RealSense D435 的 USB Type-C 接口连接到 RDK-X5 的 USB 3.0 蓝色接口
# 确认连接牢固，避免松动
```

**Step 3：检查指示灯**

D435 正面有一个 LED 指示灯：
- 正常工作时：LED 亮起（白色或绿色）
- 供电不足时：LED 闪烁或暗淡
- 未识别时：LED 不亮

---

## 3. 环境搭建

### 3.1 系统依赖安装

首先更新系统软件包：

```bash
# SSH 登录 RDK-X5
ssh root@<RDK-X5-IP>

# 更新软件包列表
apt update

# 安装 RealSense SDK 依赖
apt install -y \
    libudev-dev \
    libgtk-3-dev \
    libglfw3-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    libusb-1.0-0-dev \
    pkg-config \
    python3-pip \
    cmake \
    git
```

### 3.2 安装 Intel RealSense SDK（librealsense）

RealSense SDK（ librealsense）是访问 RealSense 相机的核心库，ROS2 驱动依赖于此库。

**方法一：编译安装（推荐）**

```bash
# 切换到工作目录
cd /home/root/

# 克隆 RealSense SDK 源码（版本 v2.54.1，稳定版）
git clone https://github.com/IntelRealSense/librealsense.git
cd librealsense

# 切换到稳定版本
git checkout v2.54.1

# 创建编译目录
mkdir build && cd build

# 配置 CMake（开启 ROS 桥接和 Python 支持）
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=ON \
    -DBUILD_GRAPHICAL_EXAMPLES=OFF \
    -DBUILD_PYTHON_BINDINGS=ON \
    -DBUILD_WITH_CUDA=OFF \
    -DFORCE_RSUSB_BACKEND=ON

# 编译（使用多核加速）
make -j$(nproc)

# 安装
make install

# 刷新动态链接库缓存
ldconfig
```

**方法二：使用 apt 安装（快速）**

```bash
# 添加 Intel RealSense SDK apt 源
apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3F7D
echo "deb https://librealsense.intel.com/Debian/apt-repo focal main" > /etc/apt/sources.list.d/intel-realsense.list

# 更新并安装
apt update
apt install -y librealsense2 librealsense2-dev librealsense2-utils

# 安装 Python 绑定
pip3 install pyrealsense2
```

> **注意**：编译安装耗时约 30~60 分钟（取决于网络和编译核数），但可以获得最新功能和最佳性能。apt 安装更快但版本可能较旧。

### 3.3 安装 ROS2 RealSense 驱动

ROS2 的 realsense2_camera 驱动将 RealSense 数据发布为 ROS2 话题。

```bash
# 切换到 ROS2 工作空间
source /opt/hobot/ros2/setup.bash   # 根据实际 ROS2 环境source
cd ~/robot_ws/

# 克隆 realsense-ros 驱动（galactic 分支对应 ROS2 Galactic）
git clone -b ros2 https://github.com/IntelRealSense/realsense-ros.git src/realsense-ros

# 安装依赖
cd ~/robot_ws
rosdep install --from-paths src --ignore-src -r -y

# 编译
source /opt/hobot/ros2/setup.bash
colcon build --packages-select realsense2_camera realsense2_description --cmake-args -DCMAKE_BUILD_TYPE=Release

# 刷新环境
source install/setup.bash
```

### 3.4 配置 udev 规则

Linux 系统需要 udev 规则才能以普通用户身份访问 USB 设备：

```bash
# 复制 udev 规则文件
cp /usr/lib/librealsense2/udev/rules.d/99-realsense-libusb.rules /etc/udev/rules.d/99-realsense-libusb.rules

# 重载 udev 规则
udevadm control --reload-rules
udevadm trigger

# 将当前用户加入 video 组（免密访问）
usermod -aG video root
```

> **说明**：99-realsense-libusb.rules 规则文件允许非 root 用户访问 RealSense USB 设备，无需每次 sudo。

---

## 4. 设备连接与验证

### 4.1 检查 USB 连接

```bash
# 查看 USB 设备列表，确认 RealSense 被识别
lsusb | grep -i intel

# 预期输出类似：
# Bus 002 Device 003: ID 8086:0b07 Intel Corp. RealSense D435
```

### 4.2 使用 rs-enumerate-devices 检测设备

```bash
# 列出所有连接的 RealSense 设备
rs-enumerate-devices

# 预期输出（部分）：
# Device Serial Number: 123622270247
# Device Name: Intel RealSense D435
# Device Product ID: 0x0B07
# Firmware Version: 5.12.11.100
# Depth Sensor:
#   Depth Resolution: 1280x720
#   Depth FPS: 30, 60, 90
# Color Sensor:
#   Color Resolution: 1920x1080
#   Color FPS: 30
```

### 4.3 预览深度图与彩色图

**使用 librealsense 官方工具预览**：

```bash
# 预览 RGB + Depth（实时窗口）
rs-preview

# 或使用 realsense-viewer（图形界面）
realsense-viewer
```

> **说明**：`rs-preview` 和 `realsense-viewer` 会在终端打开一个实时预览窗口，显示深度图和彩色图。RDK-X5 若无图形界面，可跳过此步。

**使用 ROS2 工具预览**：

```bash
# 启动 realsense2_camera 节点（默认参数）
source /opt/hobot/ros2/setup.bash
source ~/robot_ws/install/setup.bash

ros2 launch realsense2_camera rs_launch.py

# 在 PC 上（同一网络）使用 rviz2 查看
rviz2

# 在 rviz2 中添加 Image 和 PointCloud 话题查看
```

---

## 5. ROS2 驱动使用

### 5.1 realsense2_camera 节点配置

`realsense2_camera` 是 ROS2 中访问 RealSense 相机的核心节点，提供多种数据话题。

**基本启动命令**：

```bash
# 启动 realsense2_camera 节点（发布深度图 + 彩色图 + 点云）
source ~/robot_ws/install/setup.bash
ros2 launch realsense2_camera rs_launch.py
```

**带参数的启动（推荐）**：

```bash
# 以更高分辨率和帧率启动
ros2 launch realsense2_camera rs_launch.py \
    depth_module.profile:=1280x720x90 \
    rgb_camera.profile:=1920x1080x30 \
    enable_pointcloud:=true \
    pointcloud_texture_opt:=1920x1080 \
    pointcloud_texture_stream:=RS2_STREAM_COLOR
```

### 5.2 话题列表

启动 realsense2_camera 后，可通过以下命令查看所有发布的话题：

```bash
# 列出所有话题
ros2 topic list

# 列出带类型的消息
ros2 topic list -t
```

**常用话题说明**：

| 话题名称 | 消息类型 | 说明 |
|---------|---------|------|
| `/camera/depth/image_rect_raw` | `sensor_msgs/Image` | 原始深度图（mm为单位） |
| `/camera/color/image_raw` | `sensor_msgs/Image` | 原始彩色图 |
| `/camera/infra1/image_rect_raw` | `sensor_msgs/Image` | 左侧红外图像 |
| `/camera/infra2/image_rect_raw` | `sensor_msgs/Image` | 右侧红外图像 |
| `/camera/depth/camera_info` | `sensor_msgs/CameraInfo` | 深度相机内参 |
| `/camera/color/camera_info` | `sensor_msgs/CameraInfo` | 彩色相机内参 |
| `/camera/points` | `sensor_msgs/PointCloud2` | 点云数据 |
| `/camera/extrinsics/depth_to_color` | `realsense2_camera_msgs/Extrinsics` | 深度到彩色的外参 |

### 5.3 相机内参获取

相机内参（焦距、主点、畸变系数）对于深度到RGB对齐和3D测量至关重要。

**通过 ROS2 话题获取内参**：

```bash
# 查看深度相机内参
ros2 topic echo /camera/depth/camera_info

# 预期输出：
# header:
#   stamp:
#     sec: 1712
#     nanosec: 123456789
#   frame_id: camera_depth_optical_frame
# height: 720
# width: 1280
# distortion_model: "plumb_bob"
# D: [0.0, 0.0, 0.0, 0.0, 0.0]
# K: [633.456, 0.0, 635.234, 0.0, 633.456, 360.512, 0.0, 0.0, 1.0]
# R: [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
# P: [633.456, 0.0, 635.234, 0.0, 0.0, 633.456, 360.512, 0.0, 0.0, 0.0, 1.0, 0.0]
```

**内参解读**：

- `K[0]` = `fx` = 633.456（深度图 x 方向焦距，单位像素）
- `K[2]` = `cx` = 635.234（深度图 x 方向主点）
- `K[4]` = `fy` = 633.456（深度图 y 方向焦距）
- `K[5]` = `cy` = 360.512（深度图 y 方向主点）

### 5.4 launch 启动文件

创建一个自定义 launch 文件，方便管理和复用配置：

**文件路径**：`~/robot_ws/src/rdk_deploy/launch/rs_d435_launch.py`

```python
#!/usr/bin/env python3
"""
RealSense D435 启动配置
功能：启动 realsense2_camera 节点，发布深度图、彩色图、点云
"""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """生成 launch 描述"""
    return LaunchDescription([
        # realsense2_camera 节点
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='realsense2_camera',
            output='screen',
            parameters=[{
                # 深度模块配置
                'depth_module.profile': '1280x720x90',  # 深度分辨率和帧率
                'enable_depth': True,                    # 启用深度

                # RGB 相机配置
                'rgb_camera.profile': '1920x1080x30',  # 彩色分辨率和帧率
                'enable_color': True,                   # 启用彩色

                # 红外相机配置
                'enable_infra1': True,                  # 启用左红外
                'enable_infra2': True,                  # 启用右红外
                'infra_rgb': False,                      # 红外图不使用彩色映射

                # 点云配置
                'enable_pointcloud': True,              # 启用点云输出
                'pointcloud_texture_opt': '1920x1080',  # 点云纹理分辨率
                'pointcloud_texture_stream': 'RS2_STREAM_COLOR',  # 使用彩色作为纹理

                # 滤波配置（可选）
                'spatial_filter.magnitude': 2,          # 空间滤波强度
                'spatial_filter.alpha': 0.5,
                'spatial_filter.delta': 20,
                'temporal_filter.alpha': 0.4,            # 时域滤波（减少抖动）

                # 激光器功率配置
                'depth_module.emitter_enabled': 1,      # 启用红外投射器（1=On, 0=Off）

                # 坐标框架
                'camera_namespace': 'camera',
                'camera_name': 'd435',
                'base_frame_id': 'camera_link',         # 相机基坐标系
                'depth_frame_id': 'camera_depth_optical_frame',
                'color_frame_id': 'camera_color_optical_frame',

                # 同步配置
                'sync_groups': 'color',
            }]
        ),
    ])
```

**使用方法**：

```bash
# 启动自定义 launch 文件
source ~/robot_ws/install/setup.bash
ros2 launch rdk_deploy rs_d435_launch.py
```

---

## 6. Python 图像处理实战

### 6.1 安装 pyrealsense2

pyrealsense2 是 RealSense SDK 的 Python 接口，用于直接访问相机数据：

```bash
# 安装 pyrealsense2（如果尚未安装）
pip3 install pyrealsense2 opencv-python numpy
```

### 6.2 读取深度图与彩色图

**文件路径**：`~/robot_ws/src/rdk_deploy/scripts/rs_read_stream.py`

```python
#!/usr/bin/env python3
"""
RealSense D435 读取深度图与彩色图
功能：从 RealSense D435 读取并保存深度图和彩色图
"""
import pyrealsense2 as rs  # RealSense SDK Python 接口
import cv2  # OpenCV 用于图像处理和显示
import numpy as np  # NumPy 用于数值计算
import os

def read_streams():
    """
    读取 RealSense D435 的深度图和彩色图
    并通过 OpenCV 窗口实时显示
    """
    # ========== 1. 配置 RealSense 管道 ==========
    pipeline = rs.pipeline()

    # 创建配置对象，用于指定启用的数据流
    config = rs.config()

    # 启用深度流：1280x720 分辨率，90fps
    # rs.format.z16 表示 16 位深度值（单位 mm）
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 90)

    # 启用彩色流：1920x1080 分辨率，30fps
    # rs.format.rgb8 表示 8 位 RGB 格式
    config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 30)

    # ========== 2. 启动管道 ==========
    # 启动后 RealSense 开始采集数据
    profile = pipeline.start(config)
    print("RealSense D435 已启动，按 'q' 键退出...")

    # ========== 3. 创建对齐对象 ==========
    # 深度图和彩色图分辨率不同，需要对齐后才能叠加
    # rs.align(rs.stream.color) 表示将深度图对齐到彩色图
    align = rs.align(rs.stream.color)

    try:
        frame_count = 0
        save_dir = "/home/root/rs_captures"
        os.makedirs(save_dir, exist_ok=True)

        while True:
            # ========== 4. 获取一帧数据 ==========
            # wait_for_frames() 阻塞等待直到收到完整的一帧
            frames = pipeline.wait_for_frames()

            # 将深度图对齐到彩色图坐标系统
            aligned_frames = align.process(frames)

            # 分离对齐后的深度图和彩色图
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            # 检查帧是否有效（可能因 USB 带宽不足丢失）
            if not depth_frame or not color_frame:
                continue

            frame_count += 1

            # ========== 5. 转换为 NumPy 数组（OpenCV 格式） ==========
            # 深度图：16位整数，单通道（单位 mm）
            depth_image = np.asanyarray(depth_frame.get_data())

            # 彩色图：8位整数，三通道 RGB
            color_image = np.asanyarray(color_frame.get_data())

            # OpenCV 显示格式为 BGR，需要转换 RGB -> BGR
            color_image_bgr = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)

            # ========== 6. 应用颜色映射到深度图（可视化） ==========
            # 深度图是单通道 16 位，直接显示为灰度看不清
            # 使用 COLORMAP_JET 将深度值映射为彩色（近=红，远=蓝）
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),  # 缩放深度值到 0-255
                cv2.COLORMAP_JET
            )

            # ========== 7. 显示图像 ==========
            # 彩色图
            cv2.namedWindow('Color Image', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('Color Image', color_image_bgr)

            # 深度图（伪彩色）
            cv2.namedWindow('Depth Image', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('Depth Image', depth_colormap)

            # 每隔 30 帧保存一次图像
            if frame_count % 30 == 0:
                color_path = os.path.join(save_dir, f"color_{frame_count}.jpg")
                depth_path = os.path.join(save_dir, f"depth_{frame_count}.png")
                cv2.imwrite(color_path, color_image_bgr)
                cv2.imwrite(depth_path, depth_image)
                print(f"已保存: {color_path}, {depth_path}")

            # 按 'q' 退出
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    finally:
        # ========== 8. 停止管道，释放资源 ==========
        pipeline.stop()
        cv2.destroyAllWindows()
        print("RealSense D435 已关闭")

if __name__ == "__main__":
    read_streams()
```

**运行方式**：

```bash
# 赋予执行权限
chmod +x ~/robot_ws/src/rdk_deploy/scripts/rs_read_stream.py

# 运行脚本
python3 ~/robot_ws/src/rdk_deploy/scripts/rs_read_stream.py
```

### 6.3 深度与 RGB 对齐

深度图和彩色图的像素坐标不同，需要对齐后才能进行像素级融合。

**文件路径**：`~/robot_ws/src/rdk_deploy/scripts/rs_align_depth_color.py`

```python
#!/usr/bin/env python3
"""
RealSense D435 深度图与彩色图对齐
功能：将深度图对齐到彩色图坐标系，实现像素级融合
"""
import pyrealsense2 as rs
import cv2
import numpy as np

def align_depth_to_color():
    """
    将深度图对齐到彩色图
    对齐后，深度图上每个像素都对应彩色图上同一个像素的深度值
    """
    # ========== 1. 启动管道 ==========
    pipeline = rs.pipeline()
    config = rs.config()

    # 启用深度和彩色流
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 90)
    config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 30)

    profile = pipeline.start(config)
    print("深度-彩色对齐已启动，按 'q' 键退出...")

    # ========== 2. 获取深度到彩色的外参矩阵 ==========
    # 外参描述了两个相机之间的旋转和平移关系
    depth_stream = profile.get_stream(rs.stream.depth)
    color_stream = profile.get_stream(rs.stream.color)

    # extrinsics 表示从深度相机到彩色相机的坐标变换
    extrinsics = depth_stream.get_extrinsics_to(color_stream)

    print(f"深度到彩色的旋转矩阵:\n{np.array(extrinsics.rotation).reshape(3, 3)}")
    print(f"深度到彩色的平移向量: {extrinsics.translation}")

    # ========== 3. 创建对齐对象 ==========
    align = rs.align(rs.stream.color)

    try:
        while True:
            frames = pipeline.wait_for_frames()

            # 对齐：让深度图每个像素对应彩色图坐标
            aligned_frames = align.process(frames)

            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            # ========== 4. 提取对齐后的深度值 ==========
            # 获取对齐后的深度图数据
            depth_image = np.asanyarray(depth_frame.get_data())

            # 获取彩色图
            color_image = np.asanyarray(color_frame.get_data())
            color_image_bgr = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)

            # ========== 5. 深度图叠加到彩色图（验证对齐效果） ==========
            # 将深度图缩放到可视范围
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET
            )

            # 并排显示彩色图、对齐后的深度图、叠加效果
            combined = np.hstack([
                color_image_bgr,
                depth_colormap
            ])

            # 叠加：半透明混合
            overlay = color_image_bgr.copy()
            mask = depth_image > 0  # 有效深度区域（非0值）
            overlay[mask] = cv2.addWeighted(
                color_image_bgr, 0.7,   # 原始彩色图权重 70%
                depth_colormap, 0.3,    # 深度图权重 30%
                gamma=0
            )[mask]

            cv2.namedWindow('Aligned Depth + Color Overlay', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('Aligned Depth + Color Overlay', overlay)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    align_depth_to_color()
```

### 6.4 点云生成（使用 PCL）

将深度图转换为 3D 点云，用于机器人导航、物体检测等应用。

**文件路径**：`~/robot_ws/src/rdk_deploy/scripts/rs_generate_pcl.py`

```python
#!/usr/bin/env python3
"""
RealSense D435 点云生成
功能：从深度图生成 3D 点云，并保存为 PCD 文件
"""
import pyrealsense2 as rs
import numpy as np
import open3d as o3d  # Open3D 用于点云处理

def generate_pointcloud():
    """
    生成 RealSense D435 的 3D 点云
    """
    # ========== 1. 启动管道 ==========
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 90)
    config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 30)

    profile = pipeline.start(config)
    print("点云生成已启动，按 'q' 键退出...")

    # ========== 2. 获取相机内参 ==========
    # 深度相机的内参（焦距、主点）
    depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
    depth_intrinsics = depth_profile.get_intrinsics()

    print(f"深度相机内参:")
    print(f"  分辨率: {depth_intrinsics.width} x {depth_intrinsics.height}")
    print(f"  焦距 fx={depth_intrinsics.fx}, fy={depth_intrinsics.fy}")
    print(f"  主点 cx={depth_intrinsics.ppx}, cy={depth_intrinsics.ppy}")
    print(f"  畸变模型: {depth_intrinsics.model}")

    # 彩色相机内参
    color_profile = rs.video_stream_profile(profile.get_stream(rs.stream.color))
    color_intrinsics = color_profile.get_intrinsics()

    # ========== 3. 创建对齐对象 ==========
    align = rs.align(rs.stream.color)

    frame_count = 0
    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)

            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            frame_count += 1

            # ========== 4. 深度图转点云（手动计算） ==========
            depth_image = np.asanyarray(depth_frame.get_data())

            # 获取彩色图
            color_image = np.asanyarray(color_frame.get_data())

            # 有效深度掩码（深度值 > 0 表示有效）
            depth_mask = depth_image > 0

            # 遍历每个像素，计算 3D 坐标
            h, w = depth_image.shape
            points = []
            colors = []

            for y in range(h):
                for x in range(w):
                    if not depth_mask[y, x]:
                        continue  # 跳过无效深度

                    # 获取深度值（单位：mm）
                    d = depth_image[y, x] / 1000.0  # 转换为米

                    # 从像素坐标反投影到 3D 相机坐标系
                    # deproject_pixel_to_point 将 2D 像素 + 深度 -> 3D 点
                    point = rs.rs2_deproject_pixel_to_point(
                        depth_intrinsics,   # 相机内参
                        [x, y],             # 像素坐标
                        d                   # 深度值（米）
                    )
                    points.append(point)

                    # 获取该像素对应的彩色值（需要对齐后才是对的）
                    if x < color_image.shape[1] and y < color_image.shape[0]:
                        colors.append(color_image[y, x] / 255.0)  # 归一化到 0-1

            points = np.array(points)
            colors = np.array(colors)

            print(f"第 {frame_count} 帧: 有效点 {len(points)} 个")

            # ========== 5. 使用 Open3D 创建点云对象 ==========
            pcd = o3d.geometry.PointCloud()

            # 设置点云坐标（Open3D 使用 np.float64）
            pcd.points = o3d.utility.Vector3dVector(points)

            # 设置点云颜色
            if len(colors) > 0:
                pcd.colors = o3d.utility.Vector3dVector(colors)

            # 下采样（减少点数，加速显示）
            pcd = pcd.voxel_down_sample(voxel_size=0.01)

            # ========== 6. 保存点云为 PCD 文件 ==========
            if frame_count % 30 == 0:
                pcd_path = f"/home/root/rs_captures/pcd_{frame_count}.pcd"
                o3d.io.write_point_cloud(pcd_path, pcd)
                print(f"点云已保存: {pcd_path}")

            # ========== 7. 可视化点云 ==========
            # Open3D 可视化（非必须，用于调试）
            # o3d.visualization.draw_geometries([pcd])

            if frame_count >= 100:  # 处理 100 帧后退出
                break

    finally:
        pipeline.stop()
        print("点云生成已结束")

if __name__ == "__main__":
    generate_pointcloud()
```

> **依赖安装**：`pip3 install open3d`

---

## 7. 深度应用

### 7.1 深度测距

通过深度图获取指定像素的深度值，计算目标物体到相机的距离。

**文件路径**：`~/robot_ws/src/rdk_deploy/scripts/rs_depth_ranging.py`

```python
#!/usr/bin/env python3
"""
RealSense D435 深度测距
功能：点击图像上的任意点，获取该点的 3D 坐标和距离
"""
import pyrealsense2 as rs
import cv2
import numpy as np

def mouse_callback(event, x, y, flags, param):
    """
    鼠标点击回调函数
    当用户在图像上点击时，保存点击坐标
    """
    if event == cv2.EVENT_LBUTTONDOWN:
        param[0] = (x, y)  # param[0] 是共享状态变量

def depth_ranging():
    """
    实时深度测距
    用户点击图像上的某点，程序输出该点到相机的距离
    """
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 90)
    config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 30)

    profile = pipeline.start(config)
    print("深度测距已启动，点击图像查看距离，按 'q' 键退出...")

    # 创建对齐对象（深度对齐到彩色）
    align = rs.align(rs.stream.color)

    # 获取深度相机内参（用于坐标转换）
    depth_profile = rs.video_stream_profile(profile.get_stream(rs.stream.depth))
    depth_intrinsics = depth_profile.get_intrinsics()

    # 共享状态：鼠标点击的像素坐标
    click_pos = [None]

    # 创建窗口并注册鼠标回调
    window_name = "Depth Ranging - Click to Measure"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback, click_pos)

    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)

            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            if not depth_frame or not color_frame:
                continue

            depth_image = np.asanyarray(depth_frame.get_data())
            color_image = np.asanyarray(color_frame.get_data())
            color_image_bgr = cv2.cvtColor(color_image, cv2.COLOR_RGB2BGR)

            # 如果有鼠标点击，执行测距
            if click_pos[0] is not None:
                x, y = click_pos[0]

                # 获取该点的深度值（单位：mm）
                distance_mm = depth_frame.get_distance(x, y)
                distance_m = distance_mm / 1000.0  # 转换为米

                # 反投影到 3D 坐标系
                point_                distance_m = distance_mm / 1000.0  # 转换为米

                # 反投影到 3D 坐标系（得到相机坐标系下的 xyz）
                point_3d = rs.rs2_deproject_pixel_to_point(
                    depth_intrinsics, [x, y], distance_mm
                )

                # 在图像上标注点击位置和距离
                text = f"Distance: {distance_m:.3f} m"
                cv2.circle(color_image_bgr, (x, y), 5, (0, 255, 0), 2)
                cv2.putText(color_image_bgr, text, (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                print(f"像素坐标: ({x}, {y}) | 3D坐标: {point_3d} | 距离: {distance_m:.3f} m")

                click_pos[0] = None  # 重置点击状态

            # 应用颜色映射到深度图
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET
            )

            cv2.imshow(window_name, color_image_bgr)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    depth_ranging()
```

### 7.2 障碍物检测与避障

基于深度图的前方障碍物检测，是机器人自主导航的基础。

**文件路径**：`~/robot_ws/src/rdk_deploy/scripts/rs_obstacle_detection.py`

```python
#!/usr/bin/env python3
"""
RealSense D435 障碍物检测
功能：基于深度图检测前方障碍物，判断是否需要停止或转向
"""
import pyrealsense2 as rs
import cv2
import numpy as np

def detect_obstacles():
    """
    实时障碍物检测
    将深度图分为多个区域，计算每个区域的平均深度
    如果某区域深度值小于阈值，说明该方向有障碍物
    """
    pipeline = rs.pipeline()
    config = rs.config()

    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 90)

    profile = pipeline.start(config)
    print("障碍物检测已启动，按 'q' 键退出...")

    align = rs.align(rs.stream.depth)

    # 障碍物检测参数
    DISTANCE_THRESHOLD = 0.5   # 障碍物距离阈值（米），小于此值认为有障碍物
    WARNING_THRESHOLD = 1.0     # 警告距离（米）

    # 深度图像中心区域（感兴趣区域）
    h, w = 720, 1280
    center_roi = (h // 4, h * 3 // 4, w // 4, w * 3 // 4)  # 上、下、左、右

    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()

            if not depth_frame:
                continue

            depth_image = np.asanyarray(depth_frame.get_data())

            # 提取中心 ROI 区域
            y1, y2, x1, x2 = center_roi
            roi_depth = depth_image[y1:y2, x1:x2].astype(np.float32) / 1000.0  # 转为米

            # 将 ROI 分为 3x3 区域
            regions = {
                'left': roi_depth[:, :x2//3 - x1],
                'center': roi_depth[:, x2//3 - x1:2*x2//3 - x1],
                'right': roi_depth[:, 2*x2//3 - x1:],
            }

            # 计算每个区域的平均深度
            avg_distances = {}
            for name, region in regions.items():
                valid = region[region > 0]  # 过滤无效深度（值为0）
                if len(valid) > 0:
                    avg_distances[name] = np.mean(valid)
                else:
                    avg_distances[name] = float('inf')

            # 判断障碍物方向
            obstacles = []
            for name, dist in avg_distances.items():
                if dist < DISTANCE_THRESHOLD:
                    obstacles.append(name)
                    print(f"⚠️ 障碍物检测 [{name}]: {dist:.3f} m")
                elif dist < WARNING_THRESHOLD:
                    print(f"⚡ 警告 [{name}]: {dist:.3f} m")

            # 深度图可视化（带障碍物标注）
            depth_colormap = cv2.applyColorMap(
                cv2.convertScaleAbs(depth_image, alpha=0.03),
                cv2.COLORMAP_JET
            )

            # 在深度图上标注区域
            colors = {'left': (255, 0, 0), 'center': (0, 255, 0), 'right': (0, 0, 255)}
            region_x = [x1, x1 + (x2-x1)//3, x1 + 2*(x2-x1)//3, x2]

            for i, (name, dist) in enumerate(avg_distances.items()):
                # 画区域分割线
                cv2.line(depth_colormap, (region_x[i], y1), (region_x[i], y2), (255,255,255), 1)
                # 标注区域名称和距离
                text = f"{name}: {dist:.2f}m"
                cx = (region_x[i] + region_x[i+1]) // 2
                cv2.putText(depth_colormap, text, (cx - 30, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[name], 1)

                # 如果有障碍物，在区域上叠加红色警告框
                if name in obstacles:
                    cv2.rectangle(depth_colormap,
                                   (region_x[i], y1), (region_x[i+1], y2),
                                   (0, 0, 255), 3)

            cv2.namedWindow('Obstacle Detection', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('Obstacle Detection', depth_colormap)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_obstacles()
```

> **应用场景**：此障碍物检测结果可接入机器人运动控制，当 `center` 区域检测到障碍物时，机器人应立即停止并选择绕行。

---

## 8. 部署与验证

### 8.1 文件放置路径

本课程所有代码文件统一放置在 `~/robot_ws/src/rdk_deploy/` 目录下：

```bash
# 创建目录结构
mkdir -p ~/robot_ws/src/rdk_deploy/{launch,scripts}

# 查看目录结构
tree ~/robot_ws/src/rdk_deploy/
```

**目录结构**：

```
~/robot_ws/src/rdk_deploy/
├── launch/
│   └── rs_d435_launch.py          # realsense2_camera 启动文件
├── scripts/
│   ├── rs_read_stream.py          # 读取深度图与彩色图
│   ├── rs_align_depth_color.py     # 深度与 RGB 对齐
│   ├── rs_generate_pcl.py          # 点云生成
│   ├── rs_depth_ranging.py         # 深度测距
│   └── rs_obstacle_detection.py    # 障碍物检测
└── README.md
```

### 8.2 从 PC 部署到 RDK-X5

```bash
# 在 PC 上，使用 rsync 将文件同步到 RDK-X5
rsync -avz --progress \
    ~/robot_ws/src/rdk_deploy/ \
    root@<RDK-X5-IP>:/home/root/robot_ws/src/rdk_deploy/

# 或者使用 scp
scp -r ~/robot_ws/src/rdk_deploy/scripts/rs_*.py root@<RDK-X5-IP>:/home/root/robot_ws/src/rdk_deploy/scripts/
```

### 8.3 开机自启配置

将 realsense2_camera 配置为开机自启动服务：

**Step 1：创建 systemd 服务文件**

```bash
# 在 RDK-X5 上创建 systemd 服务文件
cat > /etc/systemd/system/realsense2-camera.service << 'EOF'
[Unit]
Description=Intel RealSense D435 Camera Driver
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/root
Environment="LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH"
ExecStart=/bin/bash -c "source /opt/hobot/ros2/setup.bash && source /home/root/robot_ws/install/setup.bash && ros2 launch realsense2_camera rs_launch.py"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

**Step 2：启用并启动服务**

```bash
# 重载 systemd 配置
systemctl daemon-reload

# 启用开机自启
systemctl enable realsense2-camera

# 立即启动服务
systemctl start realsense2-camera

# 查看服务状态
systemctl status realsense2-camera
```

### 8.4 rviz2 点云可视化

在 PC 上通过 ROS2 主题查看 RDK-X5 上的点云：

**Step 1：PC 配置 ROS2 环境**

```bash
# 在 PC 上设置 ROS2 环境变量，连接到 RDK-X5
export ROS_DOMAIN_ID=42
export ROS2_LIVeliness=9
export ROS2_REMOTE_HOST=<RDK-X5-IP>

# 使用 FastDDS discovery server 加速发现
export FASTRTPS_DEFAULT_PROFILES_FILE=~/fastdds.xml
```

**Step 2：在 PC 上启动 rviz2**

```bash
# 在 PC 上启动 rviz2
rviz2

# 在 rviz2 中：
# 1. 添加 PointCloud2 显示 -> 设置话题 /camera/points
# 2. 设置 Fixed Frame 为 camera_link
# 3. 调整 Color Transform 为 RGB8
```

### 8.5 完整验证流程

```bash
# 1. 检查设备识别
lsusb | grep 8086

# 2. 检查 ROS2 话题
source ~/robot_ws/install/setup.bash
ros2 topic list | grep camera

# 3. 查看话题频率
ros2 topic hz /camera/depth/image_rect_raw
ros2 topic hz /camera/color/image_raw
ros2 topic hz /camera/points

# 4. 运行 Python 脚本验证
python3 ~/robot_ws/src/rdk_deploy/scripts/rs_read_stream.py
```

---

## 9. 常见问题排查

### Q1：RealSense D435 无法被识别（lsusb 看不到）

**可能原因**：
- USB 3.0 数据线未连接或线材不合格
- USB 接口供电不足
- udev 规则未正确配置

**排查步骤**：

```bash
# 检查 USB 连接
lsusb

# 查看 dmesg 日志中的 USB 错误
dmesg | grep -i usb
dmesg | grep -i realsense

# 重新加载 udev 规则
udevadm control --reload-rules
udevadm trigger

# 检查 USB 供电
cat /sys/bus/usb/devices/*/power/active_pole
```

**解决方案**：
- 使用原装或高品质 USB 3.0 数据线（长度 ≤ 3m）
- 尝试不同的 USB 3.0 接口
- 确保 RDK-X5 电源供电充足（12V/2A 以上）

### Q2：深度图全黑或全零

**可能原因**：
- 红外投射器未启用
- 镜头前方有遮挡
- 光照过强（阳光直射会干扰红外图案）

**排查步骤**：

```bash
# 检查深度流是否开启
rs-enumerate-devices

# 手动启用发射器（通过 librealsense）
python3 -c "import pyrealsense2 as rs; p = rs.pipeline(); c = rs.config(); c.enable_stream(rs.stream.depth); prof = p.start(c); dev = prof.get_device(); dev.first_depth_sensor().set_option(rs.option.emitter_enabled, 1); import time; time.sleep(2)"
```

### Q3：深度帧率低（低于预期）

**可能原因**：
- USB 2.0 连接（带宽不足）
- 分辨率设置过高
- USB 带宽被其他设备占用

**解决方案**：

```bash
# 降低分辨率和帧率
ros2 launch realsense2_camera rs_launch.py \
    depth_module.profile:=848x480x60 \
    rgb_camera.profile:=1280x720x30

# 断开其他 USB 设备
lsusb
```

### Q4：ROS2 驱动编译失败

**排查步骤**：

```bash
# 查看具体编译错误
cd ~/robot_ws
colcon build --packages-select realsense2_camera --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF 2>&1 | tail -50

# 确保依赖已安装
rosdep install --from-paths src --ignore-src -r -y
```

### Q5：pyrealsense2 导入失败（ImportError）

```bash
# 确认 pyrealsense2 安装
pip3 show pyrealsense2

# 重新安装
pip3 install --upgrade pyrealsense2

# 检查 Python 版本兼容性
python3 --version
```

---

## 练习题

### 练习 1：RealSense D435 深度测量原理理解

RealSense D435 采用主动红外立体视觉原理测量深度。请回答以下问题：

1. RealSense D435 的深度测量范围是多少？
2. 深度计算公式 `Z = f × B / d` 中，`f`、`B`、`d` 分别代表什么物理量？
3. 为什么红外投射器（IR Projector）对深度测量至关重要？
4. D435 和 D435i 的主要区别是什么？

### 练习 2：环境搭建

请按以下步骤完成 RealSense SDK 和 ROS2 驱动的安装：

1. 安装 librealsense2（选择 apt 或编译方式）
2. 安装 realsense2_camera ROS2 驱动
3. 配置 udev 规则
4. 验证设备连接（使用 rs-enumerate-devices）

### 练习 3：ROS2 话题查看

启动 realsense2_camera 节点后，执行以下操作：

1. 列出所有发布的话题
2. 查看深度图话题的消息频率
3. 查看彩色图话题的 CameraInfo 内参
4. 列出点云话题的消息类型

### 练习 4：深度图对齐

编写 Python 代码，实现：
1. 从 RealSense D435 同时读取深度图和彩色图
2. 将深度图对齐到彩色图坐标系
3. 在对齐后的彩色图上叠加伪彩色深度（半透明效果）
4. 将结果保存为图片

### 练习 5：障碍物检测

基于本课程的障碍物检测代码，实现以下改进：

1. 将检测区域从 3x3 扩展为 5x5（更精细的方向判断）
2. 增加一个"极近障碍"阈值（如 0.3m），触发紧急停止
3. 在彩色图上实时标注障碍物方向和距离
4. 将障碍物信息发布为 ROS2 话题 `/obstacle_warning`

---

## 答案

### 练习 1 答案

1. **深度测量范围**：0.1m ~ 10m（官方规格）

2. **公式参数说明**：
   - `f`：红外相机的焦距（单位：像素）
   - `B`：左右红外相机之间的物理距离（基线），D435 约 55mm
   - `d`：通过立体匹配得到的视差值（单位：像素）

3. **红外投射器的作用**：D435 投射不可见的红外斑点图案到场景表面，增强无纹理区域（如白墙）的特征，使得立体匹配算法能够找到对应点，从而获得准确的深度值。没有红外投射器，白墙等无纹理区域的深度测量会失败。

4. **D435 vs D435i**：D435i 在 D435 基础上集成了 IMU（加速度计 + 陀螺仪），可用于 VIO（视觉惯性里程计）和室内 SLAM 应用。D435i 的深度和 RGB 性能与 D435 完全相同。

### 练习 2 答案

```bash
# 1. 安装依赖
apt update && apt install -y libudev-dev libgtk-3-dev libglfw3-dev cmake git

# 2. 安装 librealsense（apt 方式）
apt-key adv --keyserver keyserver.ubuntu.com --recv-key F6E65AC044F831AC80A06380C8B3A55A6F3F7D
echo "deb https://librealsense.intel.com/Debian/apt-repo focal main" > /etc/apt/sources.list.d/intel-realsense.list
apt update && apt install -y librealsense2 librealsense2-utils
pip3 install pyrealsense2

# 3. 安装 realsense2_camera
cd ~/robot_ws
source /opt/hobot/ros2/setup.bash
git clone -b ros2 https://github.com/IntelRealSense/realsense-ros.git src/realsense-ros
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select realsense2_camera

# 4. 配置 udev
cp /usr/lib/librealsense2/udev/rules.d/99-realsense-libusb.rules /etc/udev/rules.d/
udevadm control --reload-rules && udevadm trigger

# 5. 验证设备
rs-enumerate-devices
```

### 练习 3 答案

```bash
# 启动相机
ros2 launch realsense2_camera rs_launch.py

# 新开终端执行：
source ~/robot_ws/install/setup.bash

# 1. 列出所有话题
ros2 topic list

# 2. 查看深度图频率
ros2 topic hz /camera/depth/image_rect_raw

# 3. 查看彩色图内参
ros2 topic echo /camera/color/camera_info

# 4. 查看点云消息类型
ros2 topic info /camera/points
# 输出：Type: sensor_msgs/msg/PointCloud2
```

### 练习 4 答案

核心代码逻辑：

```python
import pyrealsense2 as rs
import cv2
import numpy as np

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 90)
config.enable_stream(rs.stream.color, 1920, 1080, rs.format.rgb8, 30)

profile = pipeline.start(config)
align = rs.align(rs.stream.color)

while True:
    frames = pipeline.wait_for_frames()
    aligned = align.process(frames)
    depth = np.asanyarray(aligned.get_depth_frame().get_data())
    color = aligned.get_color_frame()
    color_data = cv2.cvtColor(np.asanyarray(color.get_data()), cv2.COLOR_RGB2BGR)

    # 深度伪彩色映射
    depth_color = cv2.applyColorMap(cv2.convertScaleAbs(depth, alpha=0.03), cv2.COLORMAP_JET)

    # 叠加效果
    overlay = cv2.addWeighted(color_data, 0.7, depth_color, 0.3, gamma=0)

    # 保存图片
    cv2.imwrite("overlay.jpg", overlay)
    cv2.imshow("Aligned Depth + Color", overlay)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

pipeline.stop()
```

### 练习 5 答案（要点）

```python
# 5x5 区域分割
h, w = depth_image.shape
grid_h, grid_w = h // 5, w // 5

obstacles = {}
for i in range(5):
    for j in range(5):
        region = depth_image[i*grid_h:(i+1)*grid_h, j*grid_w:(j+1)*grid_w]
        valid = region[region > 0]
        avg = np.mean(valid) / 1000.0 if len(valid) > 0 else float('inf')
        obstacles[f"row{i}_col{j}"] = avg

# 发布 ROS2 话题
from rclpy.node import Node
...
self.publisher = self.create_publisher(ObstacleMsg, '/obstacle_warning', 10)
...
msg = ObstacleMsg()
msg.header.stamp = self.get_clock().now().to_msg()
msg.danger = any(d < 0.3 for d in obstacles.values())
self.publisher.publish(msg)
```

---

*课程编写于 2026-03-24*
