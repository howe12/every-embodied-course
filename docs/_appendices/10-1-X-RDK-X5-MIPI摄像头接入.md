# 10-1-X RDK-X5 MIPI摄像头接入

> **前置课程**：10-1 计算机视觉概述与视觉传感器
> **对应课程**：10-1 计算机视觉概述（RDK-X5 适配）

---

## 目录

1. [MIPI摄像头概述](#1-mipi摄像头概述)
2. [硬件准备与连接](#2-硬件准备与连接)
3. [环境搭建](#3-环境搭建)
4. [MIPI摄像头接入验证](#4-mipi摄像头接入验证)
5. [ROS2图像采集](#5-ros2图像采集)
6. [Python图像处理实战](#6-python图像处理实战)
7. [部署与验证](#7-部署与验证)
8. [常见问题排查](#8-常见问题排查)
9. [练习题](#练习题)
10. [答案](#答案)

---

## 1. MIPI摄像头概述

### 1.1 什么是MIPI CSI-2接口

MIPI CSI-2（Camera Serial Interface 2）是移动产业处理器接口联盟（MIPI Alliance）制定的相机串行接口标准，广泛应用于手机、汽车ADAS、嵌入式开发板等领域。相比于USB摄像头和以太网摄像头，MIPI CSI-2具有**低功耗、低延迟、高带宽**的优势，是嵌入式视觉系统的首选接口。

```
┌─────────────────────────────────────────────────────────┐
│                    MIPI CSI-2 数据传输                    │
│                                                         │
│   摄像头模组 ──CSI-2──> ISP/SoC ──> CPU/BPU处理         │
│                                                         │
│   特点：                                                  │
│   • 2/4 lane 高速串行（每lane最高 2.5Gbps）               │
│   • 低电压差分信号（LVDS/LP-MIPI）                       │
│   • 支持 RAW、YUV、RGB 多种格式                          │
│   • 即插即用（通过I2C配置寄存器）                         │
└─────────────────────────────────────────────────────────┘
```

### 1.2 RDK-X5摄像头接口说明

RDK-X5 开发板集成**双MIPI CSI接口**，支持同时接入两路摄像头，具体规格如下：

| 参数 | 规格 |
|------|------|
| 接口类型 | MIPI CSI-2（4 lane） |
| 接口数量 | 2个（CAM0 / CAM1） |
| 单lane速率 | 最高 2.5Gbps |
| 支持分辨率 | 最高 4K@30fps |
| 支持格式 | RAW12/10/8、YUV422 |
| 协议层 | D-PHY v1.2 |
| 配置接口 | I2C（0x36 地址，可配置） |

> **注意**：RDK-X5 的 MIPI 接口默认需要配置设备树（Device Tree）才能识别摄像头。出厂系统若未烧录对应驱动，需要手动配置。

### 1.3 常见MIPI摄像头模组选型

| 型号 | 分辨率 | 视场角 | 特点 | 典型应用 |
|------|--------|--------|------|---------|
| IMX415 | 4K (3864×2196) | 120° | 低照度好，星光级 | 监控、导航 |
| IMX258 | 4K (3840×2160) | 可调（替换镜头） | 焦距可换 | 通用视觉 |
| OV13855 | 1300万像素 | 可调 | 高分辨率 | 精细检测 |
| IMX477 | 1200万像素 | 可换C/CS口 | 高画质 | 工业检测 |
| GC4663 | 4K | 160° | 广角 | 全向感知 |

本课程以 **IMX415** 为例进行讲解，它是嵌入式视觉领域最常用的4K MIPI摄像头之一，性价比高，夜视效果出色。

---

## 2. 硬件准备与连接

### 2.1 硬件清单

| 物品 | 说明 |
|------|------|
| RDK-X5 开发板 | 地平线RDK-X5（BSP 5.10+ 系统） |
| MIPI摄像头模组 | IMX415 或其他兼容模组 |
| FPC软排线 | 30pin / 22pin（根据模组接口选择） |
| 12V 电源适配器 | RDK-X5 供电要求 ≥12V/2A |
| HDMI显示器 | 用于接屏幕查看预览效果 |
| 键鼠套装 | 调试用 |
| PC（用于SSH） | 与RDK-X5同一局域网 |

### 2.2 硬件连接步骤

> ⚠️ **警告**：RDK-X5 开发板需要在断电状态下连接摄像头！带电插拔可能损坏模组！

**Step 1：断电确认**

```bash
# 在PC上通过SSH连接RDK-X5，先执行关机
ssh root@<RDK-X5-IP>
shutdown -h now
# 等待开发板指示灯熄灭后，再进行硬件连接
```

**Step 2：连接摄像头FPC排线**

找到开发板上的 **CAM0** 接口（靠近板子边缘，标注为 CAM0）：

```
RDK-X5 开发板局部示意图

    ┌─────────────────────────────┐
    │  CAM0          CAM1         │  ← 摄像头接口
    │  [========]    [========]  │
    │  30pin FPC     30pin FPC    │
    └─────────────────────────────┘
```

1. 轻轻翻开CAM0接口的黑色固定夹（向上翻开约90°）
2. 将FPC排线**金属触点朝下**插入接口
3. 确认插到底后，将黑色固定夹向下压紧
4. 排线另一端连接到摄像头模组的FPC接口（注意正反面）

**Step 3：检查连接**

```bash
# 重新上电，登录系统
ssh root@<RDK-X5-IP>

# 检查系统日志中是否有摄像头相关的I2C设备
dmesg | grep -i "imx\|cam\|mipi\|i2c"
```

---

## 3. 环境搭建

### 3.1 BSP系统烧录

RDK-X5 需要烧录包含MIPI驱动支持的BSP镜像。地平线官方提供烧录工具 **hitool**，支持SD卡和EMMC两种烧录方式。

**下载官方BSP镜像：**

```bash
# 在PC上操作，下载最新的RDK-X5 BSP镜像
# 镜像下载地址：https://developer.horizon.cc/
# 选择 RDK-X5 → BSP镜像 → 最新版本（如 v1.0.6）

# 假设下载后镜像文件为：rdk_x5_bsp_v1.0.6.tar.gz
# 解压后得到镜像文件
tar -xzf rdk_x5_bsp_v1.0.6.tar.gz
cd rdk_x5_bsp_v1.0.6/
```

**烧录到SD卡：**

```bash
# 查看SD卡设备名称
lsblk

# 假设SD卡设备为 /dev/sdb，执行烧录
sudo bash烧录工具.sh --device=/dev/sdb --image=./output/rdk_x5_bsp.img

# 等待烧录完成（约10-15分钟）
# 烧录完成后，将SD卡插入RDK-X5，从SD卡启动
```

**烧录到EMMC（使用hitool）：**

```bash
# 1. 将RDK-X5设置为串口烧录模式（参考官方文档）
# 2. 使用USB线连接PC的USB-TYPEC烧录口
# 3. 运行烧录工具
python3 hitool.pyc --chip=rdk_x5 --烧录模式=emmc --image=./output/rdk_x5_bsp.img
```

### 3.2 驱动配置

RDK-X5 的MIPI摄像头驱动主要包含两部分：
1. **内核驱动**：内核中的 `sunxi-csi`、`imx415` 等驱动模块
2. **设备树配置**：指定哪个I2C地址、哪个CSI接口、使用哪个摄像头模组

**检查当前内核驱动：**

```bash
# SSH登录RDK-X5后执行
# 查看内核是否已加载MIPI相关驱动
lsmod | grep -E "csi|sunxi|imx|sensor"

# 预期输出（部分示例）：
# sunxi_csi            40960  0
# vin_io               16384  1 sunxi_csi
# imx415               16384  0
```

**手动加载驱动（如未自动加载）：**

```bash
# 加载CSI驱动
modprobe sunxi-csi

# 加载IMX415传感器驱动（根据实际模组选择）
modprobe imx415

# 确认驱动加载成功
dmesg | tail -20
```

### 3.3 设备树配置

设备树文件定义了硬件的连接关系。如果默认设备树未包含你的摄像头模组，需要修改/编译设备树。

**查看当前设备树配置：**

```bash
# RDK-X5 设备树文件通常位于 /boot 或 /extlinux/
ls /boot/dtb/horizon/hobot/
# 例如：horizon_x3_v0.dtb

# 查看当前启动使用的设备树
cat /boot/extlinux/extlinux.conf
```

**修改设备树（MIPI CAM0 使用IMX415）：**

```bash
# 编辑 extlinux.conf，添加摄像头配置参数
cat > /boot/extlinux/extlinux.conf << 'EOF'
# RDK-X5 启动配置
DEFAULT primary

LABEL primary
    LINUX /boot/zImage
    FDT /boot/dtb/horizon/horizon_x3_v0.dtb
    APPEND console=ttyS0,115200 root=/dev/mmcblk0p2 rootwait rw boot=live
    # 摄像头配置参数
    APPEND_MIPI_CAM0=imx415
EOF

# 同步配置到启动分区
sync
```

### 3.4 环境变量配置

**设置摄像头相关的环境变量：**

```bash
# 编辑 /etc/profile.d/ 下的配置文件
cat >> /etc/profile.d/rdk_camera.sh << 'EOF'
#!/bin/bash
# RDK-X5 MIPI摄像头环境变量配置

# 摄像头设备节点配置
export CAMERA_DEVICE="/dev/video0"
export CAMERA_FORMAT="YUYV"
export CAMERA_WIDTH=3840
export CAMERA_HEIGHT=2160

# V4L2缓冲队列数量
export V4L2_BUFFER_COUNT=4

# 是否启用ISP（图像信号处理）
export CAMERA_USE_ISP=1

echo "[RDK-CAM] Camera env loaded."
EOF

chmod +x /etc/profile.d/rdk_camera.sh
source /etc/profile.d/rdk_camera.sh
```

---

## 4. MIPI摄像头接入验证

### 4.1 设备节点识别

连接好摄像头并配置好驱动后，系统应该能够识别到摄像头设备。

**检查设备节点：**

```bash
# SSH登录RDK-X5
ssh root@<RDK-X5-IP>

# 查看 video 设备节点
ls -la /dev/video*

# 预期输出：
# crw-rw---- 1 root video  81,   0 Jan 15 10:30 /dev/video0
# crw-rw---- 1 root root  81,   1 Jan 15 10:30 /dev/video1
# crw-rw---- 1 root root  81,   2 Jan 15 10:30 /dev/video2

# /dev/video0 通常是MIPI摄像头的主设备节点
# /dev/video1 通常是ISP处理后的输出节点
```

**查看摄像头详细参数：**

```bash
# 安装 v4l2-utils（如果未预装）
apt update && apt install -y v4l-utils

# 列出所有V4L2设备
v4l2-ctl --list-devices

# 查看 /dev/video0 的详细参数
v4l2-ctl -d /dev/video0 --all

# 预期输出（示例）：
# Driver Info (not using libv4l2):
#     Driver name   : sunxi-csi
#     Card type     : sunxi_csi0
#     Bus info      : MIPI-CSI-0
#     Driver version: 5.10.0
#     Capabilities  : 0x84201000
#         Video Capture
#         Streaming
#         Extended Pix Format
#     Device Caps   : 0x04201000
#         Video Capture
#         Streaming
```

### 4.2 v4l2-utils 测试摄像头

**查看支持的数据格式：**

```bash
# 查询摄像头支持的像素格式和分辨率
v4l2-ctl -d /dev/video0 --list-formats-ext

# 预期输出（示例）：
# ioctl: VIDIOC_ENUM_FMT
#     Index       : 0
#     Type        : Video Capture
#     Pixel Format: 'YUYV' (YUYV 4:2:2)
#     Name        : YUYV 4:2:2
#         Size: Stepwise 64x64 - 3840x2160
#     Index       : 1
#     Type        : Video Capture
#     Pixel Format: 'MJPG' (Motion-JPEG)
#     Name        : Motion-JPEG
#         Size: Stepwise 64x64 - 3840x2160
```

**测试摄像头采集（YUYV格式）：**

```bash
# 设置摄像头参数：4K分辨率，YUYV格式
v4l2-ctl -d /dev/video0 --set-fmt-video=width=3840,height=2160,pixelformat=YUYV

# 采集一帧图像保存为文件
v4l2-ctl -d /dev/video0 --stream-mmap=3 --stream-count=1 --stream-to=/tmp/test_frame.raw

# 将原始YUYV数据转换为PNG（需要OpenCV）
python3 -c "
import cv2
import numpy as np
raw = np.fromfile('/tmp/test_frame.raw', dtype=np.uint8)
h, w = 2160, 3840
yuyv = raw.reshape(h, w, 2)
bgr = cv2.cvtColor(yuyv, cv2.COLOR_YUV2BGR_YUYV)
cv2.imwrite('/tmp/test_frame.png', bgr)
print('Image saved to /tmp/test_frame.png')
"
```

**测试摄像头预览（使用GStreamer）：**

```bash
# RDK-X5 通常预装了 GStreamer
# 检查GStreamer是否支持v4l2
gst-inspect-1.0 v4l2src || echo "需要安装: apt install gstreamer1.0-plugins-good"

# GStreamer预览MIPI摄像头
gst-launch-1.0 v4l2src device=/dev/video0 ! \
    "video/x-raw,format=YUY2,width=1920,height=1080,framerate=30/1" ! \
    videoconvert ! \
    ximagesink
```

### 4.3 预览功能验证

如果开发板连接了HDMI显示器，可以使用以下方式验证预览功能：

**方式1：GStreamer直接预览**

```bash
# 在RDK-X5的HDMI显示器上预览摄像头画面
export DISPLAY=:0

gst-launch-1.0 v4l2src device=/dev/video0 ! \
    "video/x-raw,format=YUY2,width=1280,height=720,framerate=30/1" ! \
    videoconvert ! \
    autovideosink
```

**方式2：使用Python + OpenCV预览**

```bash
# 安装必要的Python库
pip3 install opencv-python-headless

# 创建预览脚本
cat > /tmp/camera_preview.py << 'EOF'
#!/usr/bin/env python3
"""
RDK-X5 MIPI摄像头预览脚本
"""
import cv2
import sys

def main():
    # 打开摄像头设备，使用V4L2后端
    cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print("[错误] 无法打开摄像头设备 /dev/video0")
        sys.exit(1)
    
    # 设置摄像头参数（1080P）
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    print(f"[INFO] 摄像头打开成功，分辨率: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
    
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[警告] 无法读取帧")
                break
            frame_count += 1
            cv2.imshow("RDK-X5 MIPI Camera Preview", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print(f"[INFO] 共采集 {frame_count} 帧")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] 预览已关闭")

if __name__ == "__main__":
    main()
EOF

python3 /tmp/camera_preview.py
```

---

## 5. ROS2图像采集

### 5.1 工作空间创建

**创建ROS2工作空间：**

```bash
# 在RDK-X5上创建ROS2工作空间
mkdir -p ~/robot_ws/src
cd ~/robot_ws

# 初始化ROS2工作空间
source /opt/ros/humble/setup.bash
colcon build
source install/setup.bash

# 创建摄像头功能包
cd ~/robot_ws/src
ros2 pkg create rdk_camera --build-type ament_python --dependencies rclpy sensor_msgs std_msgs cv_bridge image_transport
```

### 5.2 image_pub 节点编写

```bash
# 创建节点目录
mkdir -p ~/robot_ws/src/rdk_camera/rdk_camera/nodes
touch ~/robot_ws/src/rdk_camera/rdk_camera/nodes/__init__.py
```

**`~/robot_ws/src/rdk_camera/rdk_camera/nodes/image_pub.py`：**

```python
#!/usr/bin/env python3
"""
RDK-X5 MIPI摄像头图像发布节点
功能：通过V4L2读取MIPI摄像头图像，发布到ROS2话题

订阅话题：无
发布话题：
    - /camera/image_raw (sensor_msgs/Image)  # 原始图像
    - /camera/image_raw/compressed (sensor_msgs/CompressedImage)  # JPEG压缩图像

作者：课程编写组
日期：2026-03-24
"""

import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge


class CameraPublisher(Node):
    """
    MIPI摄像头图像发布节点
    
    该节点从V4L2设备读取摄像头数据，转换为ROS2图像消息并发布。
    支持动态参数调整（分辨率、帧率、发布话题选择等）。
    """
    
    def __init__(self):
        super().__init__('camera_publisher')
        
        # ---------- 声明ROS2参数 ----------
        self.declare_parameter('device', '/dev/video0')          # 摄像头设备节点
        self.declare_parameter('width', 1920)                    # 图像宽度
        self.declare_parameter('height', 1080)                   # 图像高度
        self.declare_parameter('framerate', 30)                 # 帧率
        self.declare_parameter('pixel_format', 'YUYV')          # 像素格式
        self.declare_parameter('publish_compressed', True)      # 是否发布压缩图像
        self.declare_parameter('topic_name', 'camera/image_raw') # 发布话题名称
        
        # 获取参数值
        device = self.get_parameter('device').get_parameter_value().string_value
        self.width = self.get_parameter('width').get_parameter_value().integer_value
        self.height = self.get_parameter('height').get_parameter_value().integer_value
        self.framerate = self.get_parameter('framerate').get_parameter_value().integer_value
        self.pixel_format = self.get_parameter('pixel_format').get_parameter_value().string_value
        self.publish_compressed = self.get_parameter('publish_compressed').get_parameter_value().bool_value
        topic_name = self.get_parameter('topic_name').get_parameter_value().string_value
        
        # 初始化CV_Bridge（用于OpenCV与ROS图像消息之间的转换）
        self.bridge = CvBridge()
        
        # ---------- 打开摄像头 ----------
        self.get_logger().info(f'正在打开摄像头设备: {device}')
        self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        
        if not self.cap.isOpened():
            self.get_logger().error(f'无法打开摄像头设备: {device}')
            raise RuntimeError(f'Cannot open camera: {device}')
        
        # 配置摄像头参数
        fourcc_map = {
            'YUYV': cv2.VideoWriter_fourcc(*'YUYV'),
            'MJPG': cv2.VideoWriter_fourcc(*'MJPG'),
            'NV12': cv2.VideoWriter_fourcc(*'NV12'),
        }
        fourcc = fourcc_map.get(self.pixel_format, cv2.VideoWriter_fourcc(*'YUYV'))
        
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)    # 设置像素格式
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)   # 设置宽度
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height) # 设置高度
        self.cap.set(cv2.CAP_PROP_FPS, self.framerate)       # 设置帧率
        
        # 确认实际设置的参数
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        self.get_logger().info(f'摄像头配置完成: {actual_width}x{actual_height} @ {actual_fps}fps')
        self.get_logger().info(f'像素格式: {self.pixel_format}')
        
        # ---------- 创建ROS2发布者 ----------
        self.pub_image = self.create_publisher(Image, topic_name, 10)
        
        if self.publish_compressed:
            # 压缩图像发布者（sensor_msgs/CompressedImage）
            self.pub_compressed = self.create_publisher(
                CompressedImage, 
                topic_name + '/compressed', 
                10
            )
        
        # 启动定时器，控制发布频率
        timer_period = 1.0 / self.framerate
        self.timer = self.create_timer(timer_period, self.timer_callback)
        
        self.frame_count = 0
        self.get_logger().info(f'图像发布节点已启动，正在发布到话题: {topic_name}')
    
    def timer_callback(self):
        """
        定时器回调函数，每帧执行一次
        从摄像头读取图像并发布到ROS2话题
        """
        ret, frame = self.cap.read()
        
        if not ret:
            self.get_logger().warn('无法读取摄像头帧', throttle_duration_sec=5.0)
            return
        
        self.frame_count += 1
        
        try:
            # 将OpenCV的BGR图像转换为ROS2 Image消息并发布
            # encoding='bgr8' 表示输入是BGR 8位彩色图像
            ros_image = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
            ros_image.header.stamp = self.get_clock().now().to_msg()
            ros_image.header.frame_id = 'camera_link'  # 坐标系名称
            
            self.pub_image.publish(ros_image)
            
            # 如果启用压缩图像，发布JPEG压缩版本
            if self.publish_compressed:
                compressed_msg = CompressedImage()
                compressed_msg.header.stamp = ros_image.header.stamp
                compressed_msg.header.frame_id = 'camera_link'
                compressed_msg.format = 'jpeg'
                # cv2.imencode将图像压缩为JPEG格式，质量85
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                compressed_msg.data = buffer.tobytes()
                self.pub_compressed.publish(compressed_msg)
        
        except Exception as e:
            self.get_logger().error(f'图像转换失败: {str(e)}', throttle_duration_sec=5.0)
    
    def destroy_node(self):
        """节点销毁时释放资源"""
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
            self.get_logger().info('摄像头已关闭')
        super().destroy_node()


def main(args=None):
    """节点入口函数"""
    rclpy.init(args=args)
    
    try:
        camera_node = CameraPublisher()
        rclpy.spin(camera_node)
    except KeyboardInterrupt:
        print("\n[INFO] 接收到Ctrl+C，正在关闭节点...")
    except Exception as e:
        print(f"[ERROR] 节点运行出错: {e}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 5.3 launch 启动文件

```bash
mkdir -p ~/robot_ws/src/rdk_camera/rdk_camera/launch
```

**`~/robot_ws/src/rdk_camera/rdk_camera/launch/camera_publisher.launch.py`：**

```python
#!/usr/bin/env python3
"""
RDK-X5 MIPI摄像头发布节点 launch 启动文件

使用方法：
    ros2 launch rdk_camera camera_publisher.launch.py

参数说明：
    device: 摄像头设备节点路径
    width: 图像宽度
    height: 图像高度
    framerate: 帧率
    topic_name: 发布的话题名称
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """生成launch描述"""
    
    # 声明 launch 参数
    device_arg = DeclareLaunchArgument(
        'device',
        default_value='/dev/video0',
        description='摄像头设备节点路径'
    )
    
    width_arg = DeclareLaunchArgument(
        'width',
        default_value='1920',
        description='图像宽度'
    )
    
    height_arg = DeclareLaunchArgument(
        'height',
        default_value='1080',
        description='图像高度'
    )
    
    framerate_arg = DeclareLaunchArgument(
        'framerate',
        default_value='30',
        description='帧率'
    )
    
    topic_arg = DeclareLaunchArgument(
        'topic_name',
        default_value='camera/image_raw',
        description='发布的话题名称'
    )
    
    # 创建摄像头发布节点
    camera_node = Node(
        package='rdk_camera',           # 功能包名称
        executable='image_pub',         # 可执行文件名（对应 nodes/image_pub.py）
        name='camera_publisher',        # 节点名称
        output='screen',                # 输出到屏幕（调试用）
        parameters=[{
            'device': LaunchConfiguration('device'),
            'width': LaunchConfiguration('width'),
            'height': LaunchConfiguration('height'),
            'framerate': LaunchConfiguration('framerate'),
            'topic_name': LaunchConfiguration('topic_name'),
            'publish_compressed': True,
        }],
    )
    
    return LaunchDescription([
        device_arg,
        width_arg,
        height_arg,
        framerate_arg,
        topic_arg,
        camera_node,
    ])
```

### 5.4 功能包配置文件

**`package.xml`：**

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
    <name>rdk_camera</name>
    <version>1.0.0</version>
    <description>RDK-X5 MIPI摄像头ROS2采集功能包</description>
    
    <maintainer email="course@example.com">Course Team</maintainer>
    <license>Apache-2.0</license>
    
    <buildtool_depend>ament_python</buildtool_depend>
    <depend>rclpy</depend>
    <depend>sensor_msgs</depend>
    <depend>std_msgs</depend>
    <depend>cv_bridge</depend>
    <depend>image_transport</depend>
    <depend>opencv-python-headless</depend>
    
    <test_depend>python3-pytest</test_depend>
    <export></export>
</package>
```

**`setup.py`：**

```python
from setuptools import setup
import os
from glob import glob

package_name = 'rdk_camera'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 安装 launch 文件
        (os.path.join('share', package_name, 'launch'), 
         glob('rdk_camera/launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Course Team',
    maintainer_email='course@example.com',
    description='RDK-X5 MIPI摄像头ROS2采集功能包',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # 将 image_pub.py 注册为可执行节点
            'image_pub = rdk_camera.nodes.image_pub:main',
        ],
    },
)
```

### 5.5 编译与启动

**编译功能包：**

```bash
cd ~/robot_ws

# 首次编译需要安装依赖
rosdep install --from-paths src --ignore-src -r -y

# 编译功能包
colcon build --packages-select rdk_camera

# 编译成功后，加载环境变量
source install/setup.bash
```

**启动摄像头发布节点：**

```bash
# 方式1：使用默认参数启动
ros2 launch rdk_camera camera_publisher.launch.py

# 方式2：使用自定义参数启动（1080P@60fps）
ros2 launch rdk_camera camera_publisher.launch.py \
    width:=1920 height:=1080 framerate:=60

# 方式3：命令行方式启动
ros2 run rdk_camera image_pub --ros-args \
    -p device:=/dev/video0 \
    -p width:=1920 \
    -p height:=1080 \
    -p framerate:=30 \
    -p topic_name:=camera/image_raw
```

### 5.6 rqt_image_view 验证

**在PC端（或RDK-X5上）验证图像发布：**

```bash
# 设置ROS2环境变量
export ROS2_DOMAIN_ID=42

# 方法1：使用rqt_image_view图像可视化工具
# 在PC上运行（需要与RDK-X5处于同一网络）
rqt_image_view

# 在弹出的界面中选择话题：/camera/image_raw 或 /camera/image_raw/compressed

# 方法2：查看话题列表
ros2 topic list

# 预期输出应包含：
# /camera/image_raw
# /camera/image_raw/compressed

# 方法3：查看图像话题的详细信息
ros2 topic info /camera/image_raw

# 方法4：查看图像帧率
ros2 topic hz /camera/image_raw
```

---

## 6. Python图像处理实战

### 6.1 OpenCV读取MIPI摄像头

```bash
# 创建工作目录
mkdir -p ~/robot_ws/src/rdk_deploy/scripts
```

**`~/robot_ws/src/rdk_deploy/scripts/camera_read_basic.py` - OpenCV基础读取：**

```python
#!/usr/bin/env python3
"""
RDK-X5 MIPI摄像头 - OpenCV基础读取
使用OpenCV的V4L2驱动读取MIPI摄像头
"""

import cv2
import numpy as np
import sys

def main():
    # 使用V4L2后端打开摄像头
    # cv2.CAP_V4L2 指定使用 Video4Linux2 驱动
    cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print('[错误] 无法打开 /dev/video0')
        sys.exit(1)
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'YUYV'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # 读取一帧测试
    ret, frame = cap.read()
    if ret:
        print(f'[OK] 成功读取一帧，形状: {frame.shape}')
        # OpenCV读取的图像默认是 BGR 格式 (H, W, 3)
        print(f'     数据类型: {frame.dtype}, 高度: {frame.shape[0]}, 宽度: {frame.shape[1]}')
    else:
        print('[错误] 读取帧失败')
    
    cap.release()

if __name__ == '__main__':
    main()
```

### 6.2 图像基本处理

**`~/robot_ws/src/rdk_deploy/scripts/image_processing.py` - 图像处理实战：**

```python
#!/usr/bin/env python3
"""
RDK-X5 MIPI摄像头 - 图像处理实战
包含：灰度转换、边缘检测、模糊处理、颜色空间转换等基础操作
"""

import cv2
import numpy as np

def grayscale_demo(frame):
    """灰度图转换"""
    # 将BGR图像转换为灰度图
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return gray

def gaussian_blur_demo(frame, kernel_size=5):
    """高斯模糊 - 降噪处理"""
    # kernel_size 必须是奇数
    blur = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    return blur

def edge_detection_demo(frame):
    """边缘检测 - Canny算法"""
    # 转换为灰度图
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 使用Canny边缘检测
    # 参数：灰度图，低阈值，高阈值
    edges = cv2.Canny(gray, 50, 150)
    return edges

def hsv_color_filter_demo(frame):
    """HSV颜色空间过滤 - 提取特定颜色"""
    # 将BGR转换为HSV（色调、饱和度、亮度）
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # 定义红色的HSV范围（分两段，因为红色跨越0度和360度）
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])
    
    # 创建掩码，提取红色区域
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2
    
    # 将掩码应用到原图
    result = cv2.bitwise_and(frame, frame, mask=mask)
    return result, mask

def resize_demo(frame, target_width=640):
    """图像缩放 - 保持宽高比"""
    height, width = frame.shape[:2]
    ratio = target_width / width
    new_dim = (target_width, int(height * ratio))
    resized = cv2.resize(frame, new_dim, interpolation=cv2.INTER_AREA)
    return resized

def main():
    # 打开摄像头
    cap = cv2.VideoCapture('/dev/video0', cv2.CAP_V4L2)
    if not cap.isOpened():
        print('[错误] 无法打开摄像头')
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print('[INFO] 按键盘数字键切换处理效果：')
    print('       0 - 原始图像')
    print('       1 - 灰度图')
    print('       2 - 高斯模糊')
    print('       3 - 边缘检测')
    print('       4 - 颜色过滤（红色）')
    print('       q - 退出')
    
    mode = 0  # 当前处理模式
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 根据模式应用不同处理
            if mode == 0:
                display = frame
            elif mode == 1:
                display = grayscale_demo(frame)
            elif mode == 2:
                display = gaussian_blur_demo(frame)
            elif mode == 3:
                display = edge_detection_demo(frame)
            elif mode == 4:
                display, mask =
                display, mask = hsv_color_filter_demo(frame)
            
            # 缩放显示（如果太大）
            if display.shape[0] > 720:
                display = resize_demo(display, target_width=960)
            
            cv2.imshow('Image Processing Demo', display)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key >= ord('0') and key <= ord('4'):
                mode = key - ord('0')
                print(f'[INFO] 切换到模式 {mode}')
    
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
```

### 6.3 图像发布ROS2话题

**`~/robot_ws/src/rdk_deploy/scripts/image_publisher_standalone.py` - 独立的图像发布脚本：**

```python
#!/usr/bin/env python3
"""
RDK-X5 MIPI摄像头 - 图像发布ROS2话题
独立的Python脚本，不需要ROS2功能包即可运行
使用rclpyexecutor实现定时发布
"""

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge

class ImagePublisher(Node):
    """独立的图像发布节点"""
    
    def __init__(self):
        super().__init__('image_publisher_standalone')
        
        # 参数声明
        self.declare_parameter('device', '/dev/video0')
        self.declare_parameter('width', 1920)
        self.declare_parameter('height', 1080)
        self.declare_parameter('fps', 30)
        self.declare_parameter('topic', 'camera/compressed')
        
        device = self.get_parameter('device').value
        width = self.get_parameter('width').value
        height = self.get_parameter('height').value
        fps = self.get_parameter('fps').value
        topic = self.get_parameter('topic').value
        
        self.bridge = CvBridge()
        
        # 打开摄像头
        self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        
        if not self.cap.isOpened():
            raise RuntimeError(f'无法打开摄像头: {device}')
        
        self.get_logger().info(f'摄像头已打开: {width}x{height} @ {fps}fps')
        
        # 创建发布者
        self.pub = self.create_publisher(CompressedImage, topic, 10)
        
        # 定时器
        timer_period = 1.0 / fps
        self.timer = self.create_timer(timer_period, self.publish_image)
        
        self.frame_count = 0
    
    def publish_image(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        
        self.frame_count += 1
        
        # 压缩为JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        msg.format = 'jpeg'
        msg.data = buffer.tobytes()
        
        self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    try:
        node = ImagePublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
```

---

## 7. 部署与验证

### 7.1 文件放置路径

部署文件时，按照以下目录结构放置：

```
~/robot_ws/src/
├── rdk_camera/                    # ROS2功能包
│   ├── rdk_camera/
│   │   ├── nodes/
│   │   │   └── image_pub.py        # 图像发布节点
│   │   └── launch/
│   │       └── camera_publisher.launch.py  # launch文件
│   ├── package.xml
│   └── setup.py
│
└── rdk_deploy/                     # 部署脚本（非ROS2）
    └── scripts/
        ├── camera_read_basic.py    # 基础读取脚本
        └── image_processing.py     # 图像处理脚本
```

**在PC上同步文件到RDK-X5：**

```bash
# 使用rsync同步整个工作空间
rsync -avz --progress ~/robot_ws/ root@<RDK-X5-IP>:~/robot_ws/

# 排除build和log目录以加快同步速度
rsync -avz --progress --exclude='build/' --exclude='log/' \
    ~/robot_ws/ root@<RDK-X5-IP>:~/robot_ws/
```

### 7.2 SSH免密码登录配置

```bash
# 在PC上生成SSH密钥（如果还没有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 将公钥复制到RDK-X5
ssh-copy-id root@<RDK-X5-IP>

# 之后登录RDK-X5无需输入密码
ssh root@<RDK-X5-IP>
```

### 7.3 开机自启配置

**使用systemd服务实现开机自启：**

```bash
# 在RDK-X5上创建systemd服务文件
cat > /etc/systemd/system/rdk-camera.service << 'EOF'
[Unit]
Description=RDK-X5 MIPI Camera Publisher
After=network.target ros2.service
Wants=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/robot_ws
Environment="ROS_DOMAIN_ID=42"
ExecStart=/usr/bin/python3 /root/robot_ws/src/rdk_camera/rdk_camera/nodes/image_pub.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 重新加载systemd配置
systemctl daemon-reload

# 启用开机自启
systemctl enable rdk-camera.service

# 启动服务（立即启动，不需要等开机）
systemctl start rdk-camera.service

# 查看服务状态
systemctl status rdk-camera.service

# 查看日志
journalctl -u rdk-camera.service -f
```

### 7.4 部署验证清单

| 步骤 | 检查项 | 命令 |
|------|--------|------|
| 1 | 摄像头设备节点存在 | `ls -la /dev/video0` |
| 2 | V4L2驱动正常 | `v4l2-ctl -d /dev/video0 --all` |
| 3 | ROS2节点运行中 | `ros2 node list` |
| 4 | 图像话题发布正常 | `ros2 topic hz /camera/image_raw` |
| 5 | rqt_image_view可看到画面 | `rqt_image_view` |

---

## 8. 常见问题排查

### Q1: /dev/video0 设备节点不存在

**原因**：摄像头驱动未加载或设备树未配置。

**排查步骤**：

```bash
# 1. 检查内核驱动模块是否加载
lsmod | grep -E "csi|imx|sensor"

# 2. 如果未加载，手动加载
modprobe sunxi-csi
modprobe imx415  # 根据实际传感器型号

# 3. 检查设备树启动参数
cat /boot/extlinux/extlinux.conf

# 4. 检查I2C总线是否有传感器设备
i2cdetect -y 0
# IMX415通常在I2C地址 0x36

# 5. 检查内核日志中的摄像头相关错误
dmesg | grep -i cam
dmesg | grep -i mipi
dmesg | grep -i i2c
```

### Q2: 摄像头打开成功但读取不到图像

**原因**：分辨率/格式配置不正确，或者摄像头正在被其他进程占用。

**排查步骤**：

```bash
# 1. 先查询摄像头支持哪些格式和分辨率
v4l2-ctl -d /dev/video0 --list-formats-ext

# 2. 确认当前配置的格式
v4l2-ctl -d /dev/video0 --get-fmt-video

# 3. 尝试使用摄像头支持的标准分辨率
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1920,height=1080,pixelformat=YUYV

# 4. 检查是否有其他进程占用摄像头
lsof /dev/video0

# 5. 杀掉占用进程后重试
kill -9 <PID>
```

### Q3: 图像颜色异常（偏绿/偏紫/噪点多）

**原因**：MIPI摄像头输出RAW格式（如RAW8/RAW10/RAW12），未经ISP处理直接显示会出现颜色异常。

**解决方案**：

```bash
# 1. 确认是否需要ISP处理
# RAW格式的摄像头需要ISP进行去拜耳化（Demosaicing）、自动白平衡、伽马校正等处理

# 2. 配置使用ISP输出节点（/dev/video1 通常是ISP处理后的节点）
v4l2-ctl -d /dev/video1 --set-fmt-video=width=1920,height=1080,pixelformat=NV12

# 3. 或者使用GStreamer + ISP插件处理
gst-launch-1.0 v4l2src device=/dev/video0 ! \
    video/x-bayer,format=bggr,width=3840,height=2160 ! \
    bayer2rgb ! \
    videoconvert ! \
    autovideosink
```

### Q4: ROS2图像话题发布正常，但rqt_image_view看不到图像

**原因**：ROS2域ID不匹配，或者网络配置问题。

**排查步骤**：

```bash
# 1. 确认PC和RDK-X5的ROS_DOMAIN_ID一致
# 在PC上执行
export ROS_DOMAIN_ID=42
echo $ROS_DOMAIN_ID

# 在RDK-X5上执行
export ROS_DOMAIN_ID=42

# 2. 检查话题是否能被发现
# 在PC上执行（应能看到 /camera/image_raw）
ros2 topic list

# 3. 查看话题详情
ros2 topic info /camera/image_raw

# 4. 直接echo话题数据（看是否有数据流）
ros2 topic echo /camera/image_raw --once

# 5. 检查网络连通性
ping <RDK-X5-IP>
```

### Q5: 编译ROS2功能包报错（找不到cv_bridge）

**原因**：未安装cv_bridge或OpenCV Python绑定。

**解决方案**：

```bash
# 1. 安装ROS2相关的OpenCV包
apt update
apt install -y ros-humble-cv-bridge ros-humble-opencv-python

# 2. 如果编译仍然失败，检查CMakeLists.txt中是否正确声明了依赖
# 3. 重新source后再编译
source /opt/ros/humble/setup.bash
cd ~/robot_ws
colcon build --packages-select rdk_camera
```

### Q6: 帧率很低（低于10fps）

**原因**：分辨率设置过高，或者系统负载过大。

**解决方案**：

```bash
# 1. 降低分辨率测试
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1280,height=720,pixelformat=YUYV

# 2. 使用MJPEG格式（压缩率高，减少带宽）
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1920,height=1080,pixelformat=MJPG

# 3. 减少V4L2缓冲队列长度
v4l2-ctl -d /dev/video0 --set-buf-count=2

# 4. 检查CPU占用
top -bn1 | grep python3

# 5. 检查内存是否不足
free -h
```

---

## 练习题

### 练习1：选择题

1. RDK-X5 开发板支持的最大MIPI CSI lane数是？
   - A. 1 lane
   - B. 2 lane
   - C. 4 lane
   - D. 8 lane

2. MIPI CSI-2接口用于配置摄像头寄存器的是什么总线？
   - A. SPI
   - B. UART
   - C. I2C
   - D. GPIO

3. OpenCV默认读取V4L2摄像头时，图像的色彩格式是什么？
   - A. RGB
   - B. BGR
   - C. YUV
   - D. HSV

4. ROS2中，用于在OpenCV图像和sensor_msgs/Image之间转换的库叫什么？
   - A. OpenCV Bridge
   - B. CvBridge
   - C. ImageBridge
   - D. ROS2CV

5. V4L2中用于枚举设备支持格式的命令是？
   - A. v4l2-ctl --list-devices
   - B. v4l2-ctl --list-formats-ext
   - C. v4l2-ctl --get-fmt-video
   - D. v4l2-ctl --stream-all

### 练习2：简答题

1. 请简述MIPI CSI-2接口相比USB摄像头的主要优势。
2. 为什么MIPI摄像头有时候需要在设备树中进行配置？请说明设备树的作用。
3. 请说明 cv_bridge 在ROS2图像处理中的作用，并描述其基本使用方法。
4. 在ROS2系统中，如果要同时查看多个摄像头的话题发布帧率，应使用哪个命令？
5. 为什么使用IMX415等RAW格式摄像头时，画面可能出现颜色异常？应该如何解决？

### 练习3：编程题

1. 编写一个Python脚本，实现：每5秒钟保存一张摄像头图像到 `/tmp/capture/` 目录，文件名包含时间戳（如 `capture_20260324_143052.jpg`）。

2. 编写一个ROS2节点，订阅 `/camera/image_raw` 话题，并对每帧图像进行以下处理后重新发布到 `/camera/processed` 话题：
   - 将图像缩放到50%大小
   - 在图像右下角添加文字水印："RDK-X5 Camera"

3. 编写一个systemd服务单元文件，实现：开机自动启动ROS2摄像头发布节点，并在启动失败时自动重启（最多重启3次）。

---

## 答案

### 练习1：选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **C. 4 lane** | RDK-X5 的 MIPI CSI 接口支持最多 4 lane，每 lane 最高 2.5Gbps |
| 2 | **C. I2C** | MIPI摄像头通过I2C总线进行寄存器配置（通常地址0x36） |
| 3 | **B. BGR** | OpenCV读取V4L2摄像头后，默认得到BGR格式（注意不是RGB） |
| 4 | **B. CvBridge** | cv_bridge是ROS2中OpenCV与sensor_msgs/Image之间双向转换的标准库 |
| 5 | **B. v4l2-ctl --list-formats-ext** | 该命令列出摄像头支持的所有像素格式和分辨率组合 |

### 练习2：简答题答案

**1. MIPI CSI-2相比USB摄像头的主要优势：**

- **更低延迟**：CSI-2是相机直连SoC，无需USB协议栈的额外开销，延迟更低
- **更低功耗**：LVDS/LP-MIPI信号电平低，功耗远低于USB
- **更高带宽**：单lane最高2.5Gbps，4 lane可达10Gbps，轻松支持4K@60fps
- **更低成本**：接口简单，不需要USB PHY芯片
- **更适合嵌入式**：小巧的FPC排线，占用空间小，适合紧凑型产品

**2. 设备树的作用：**

设备树（Device Tree）是Linux内核描述硬件配置的数据结构。对于MIPI摄像头，设备树需要指定：
- 摄像头连接在哪个CSI控制器上（CSI0还是CSI1）
- 摄像头使用哪个I2C总线和I2C地址
- 摄像头模组的寄存器初始化序列（如分辨率、帧率等）
- 使用的具体传感器型号（如imx415）

如果没有正确的设备树配置，内核不知道摄像头连接在哪个接口、使用什么参数，从而无法加载对应的驱动。

**3. cv_bridge的作用和使用方法：**

`cv_bridge`是ROS2中连接OpenCV和ROS图像消息的标准桥接库。基本用法：

```python
from cv_bridge import CvBridge

bridge = CvBridge()

# OpenCV BGR图像 -> ROS Image消息（发送前）
ros_image = bridge.cv2_to_imgmsg(cv_image, encoding='bgr8')

# ROS Image消息 -> OpenCV BGR图像（接收后）
cv_image = bridge.imgmsg_to_cv2(ros_image, desired_encoding='bgr8')
```

支持的encoding包括：`bgr8`、`rgb8`、`mono8`、`uyvy`、`yuyv`等。

**4. 查看多话题帧率的命令：**

```bash
ros2 topic hz /camera/image_raw
```

如果要同时监控多个话题，可以使用 `ros2 topic hz` 多次调用或配合 `watch` 命令：

```bash
watch -n 1 "ros2 topic hz /camera/image_raw /camera/image_raw/compressed"
```

**5. RAW格式摄像头颜色异常的原理与解决：**

IMX415等传感器的感光元件本身只能感知亮度（灰度），色彩是通过在每个像素上放置不同颜色的拜耳滤镜（Bayer Filter）获得的。传感器输出的是RAW数据（Raw Bayer），每个像素只有一种原色的信息。

如果直接显示RAW数据，会出现以下问题：
- 只有单通道数据（Bayer pattern）
- 颜色信息不完整
- 需要ISP进行去拜耳化（Demosaicing）、白平衡、色彩校正等处理

解决方案：
1. 使用ISP处理后的输出节点（如 `/dev/video1`，通常经过ISP处理）
2. 配置GStreamer的bayer2rgb插件进行软件去拜耳化
3. 或者使用已经输出YUV/RGB格式的摄像头模组

---

*更新于 2026-03-24*
