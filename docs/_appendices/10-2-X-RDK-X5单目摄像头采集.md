# 10-2-X RDK-X5 单目摄像头采集

## 课程说明

本课程介绍在 RDK-X5 开发板上进行单目摄像头图像采集的方法，涵盖 USB 摄像头和 MIPI 摄像头两种接入方式，以及 v4l2 原始采集、ROS2 集成、Python OpenCV 开发三条技术路径。

**前置知识**：Linux 基础命令、ROS2 基本概念  
**硬件环境**：RDK-X5（Ubuntu 22.04）、USB 摄像头 或 MIPI 摄像头模块  
**预计学时**：2 小时

---

## 1. 单目摄像头概述

### 1.1 USB 摄像头 vs MIPI 摄像头

| 对比项 | USB 摄像头 | MIPI 摄像头 |
|--------|-----------|-------------|
| 接口类型 | USB 2.0/3.0 | MIPI CSI-2 |
| 分辨率 | 通常最高 1080p | 可达 4K 及以上 |
| 延迟 | 相对较高 | 低延迟，适合实时视觉 |
| 安装方式 | 即插即用，热插拔 | 需固定安装，连接器扣合 |
| 驱动方式 | V4L2 通用驱动 | 需要内核 DTS 配置或 ISP 驱动 |
| 适用场景 | 入门测试、桌面机器人 | 量产产品、高速视觉 |

### 1.2 单目视觉应用场景

- **目标检测与识别**：单张图像输入，输出目标类别和位置
- **图像分类**：如垃圾分类、缺陷检测
- **视觉里程计**：单目 SLAM 中的图像特征提取
- **人脸识别与考勤**：配合深度学习模型实现身份核验
- **自动导航辅助**：结合其他传感器做避障或车道线检测

### 1.3 RDK-X5 视频输入接口

RDK-X5 开发板提供以下视频输入接口：

- **USB 摄像头接口**：任意兼容 UVC 的 USB 摄像头，插入即用
- **MIPI CSI-2 接口**：支持 2-lane 或 4-lane MIPI 摄像头模块，需要在设备树中配置对应 sensor 驱动

> 参考资料：[地平线 RDK-X5 官方文档](https://developer.d-robotics.cc/rdk_doc/RDK-X5/latest)

---

## 2. 环境准备

### 2.1 系统环境确认

```bash
# 登录 RDK-X5（假设 IP 为 192.168.1.101）
ssh ubuntu@192.168.1.101

# 查看 Ubuntu 版本
cat /etc/os-release
# 预期输出包含：Ubuntu 22.04.3 LTS

# 查看内核版本
uname -r
```

### 2.2 摄像头设备识别

#### USB 摄像头识别

```bash
# 列出所有 USB 设备，找到摄像头
lsusb

# 查看详细 USB 设备信息（以 Logitech C920 为例）
lsusb -d 046d:0825
# 预期输出：Bus 001 Device 003: ID 046d:0825 Logitech, Inc. HD Webcam C920

# 查看 /dev 目录下的视频设备
ls -la /dev/video*
# 预期输出：/dev/video0, /dev/video1 等
```

#### v4l2 设备查询

```bash
# 安装 v4l-utils（如未安装）
sudo apt update
sudo apt install -y v4l-utils

# 查看所有可用视频设备及支持的格式
v4l2-ctl --list-devices
# 预期输出类似：
# HD Webcam: HD Webcam (usb-xhci-hcd-1.2):
#         /dev/video0

# 查看指定摄像头的所有可用格式和分辨率
v4l2-ctl -d /dev/video0 --list-formats-ext
# 预期输出包含：MJPG, YUYV 格式及各种分辨率组合
```

#### MIPI 摄像头识别（如已连接）

```bash
# 查看系统检测到的摄像头子设备
v4l2-ctl --list-devices

# 查看摄像头节点详情
v4l2-ctl -d /dev/video0 --all

# 查看摄像头支持的帧率和分辨率
v4l2-ctl -d /dev/video0 --get-fmt-video
```

### 2.3 依赖安装

```bash
# 更新软件源
sudo apt update

# 安装 OpenCV（Python 绑定）
sudo apt install -y python3-opencv

# 安装 ROS2 图像相关包（如使用 ROS2 Humble）
sudo apt install -y ros-humble-v4l2-camera ros-humble-image-transport-plugins ros-humble-cv-bridge

# 验证 OpenCV 安装成功
python3 -c "import cv2; print('OpenCV 版本:', cv2.__version__)"
```

---

## 3. v4l2 图像采集

### 3.1 v4l2 核心 API 介绍

v4l2（Video4Linux2）是 Linux 下摄像头编程的标准接口。核心操作流程如下：

| 步骤 | API 函数 | 说明 |
|------|---------|------|
| 1 | `open()` | 打开设备文件，如 `/dev/video0` |
| 2 | `ioctl(fd, VIDIOC_QUERYCAP, &cap)` | 查询设备能力 |
| 3 | `ioctl(fd, VIDIOC_S_FMT, &fmt)` | 设置图像格式（分辨率、像素格式） |
| 4 | `ioctl(fd, VIDIOC_REQBUFS, &req)` | 请求缓冲区 |
| 5 | `ioctl(fd, VIDIOC_QBUF, &buf)` | 将缓冲区放入队列 |
| 6 | `ioctl(fd, VIDIOC_STREAMON, &type)` | 启动视频流 |
| 7 | `read()` / `ioctl(fd, VIDIOC_DQBUF, &buf)` | 读取图像数据 |
| 8 | `ioctl(fd, VIDIOC_STREAMOFF, &type)` | 停止视频流 |
| 9 | `close()` | 关闭设备 |

### 3.2 摄像头参数配置

```bash
# 查看当前格式配置
v4l2-ctl -d /dev/video0 --get-fmt-video
# 预期输出：Pixel Format: 'YUYV'，Width/Height: 640/480

# 设置分辨率为 1280x720
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1280,height=720,pixelformat=YUYV

# 设置帧率为 30fps
v4l2-ctl -d /dev/video0 --set-parm=30

# 查看所有支持的像素格式
v4l2-ctl -d /dev/video0 --list-formats
```

### 3.3 采集测试命令

```bash
# 使用 v4l2-ctl 抓取单帧图像保存为 PPM 格式
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=YUYV
v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=1 --stream-to=capture.ppm

# 使用 ffmpeg 录制 5 秒视频
ffmpeg -f v4l2 -device /dev/video0 -input_format yuyv422 -video_size 640x480 \
       -i /dev/video0 -t 5 output.avi

# 安装并使用 cheese（图形化摄像头工具）测试
sudo apt install -y cheese
cheese  # 弹出窗口显示摄像头画面
```

### 3.4 简单 v4l2 采集 C 代码

将以下代码保存为 `v4l2_capture.c`，编译后可直接运行：

**文件路径**：`~/robot_ws/src/rdk_deploy/v4l2_capture.c`

```c
/*
 * v4l2 图像采集示例程序
 * 编译命令：gcc v4l2_capture.c -o v4l2_capture -Wall
 * 运行命令：./v4l2_capture /dev/video0
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>

#define CLEAR(x) memset(&(x), 0, sizeof(x))

// 摄像头缓冲区结构体
struct buffer {
    void   *start;    // 缓冲区起始地址
    size_t  length;   // 缓冲区长度
};

// 全局变量
static int              fd = -1;         // 设备文件描述符
static struct buffer   *buffers;         // 缓冲区数组
static unsigned int     n_buffers;       // 缓冲区数量

// 打开摄像头设备
static int open_device(const char *dev_name)
{
    // O_RDWR：读写模式，O_NONBLOCK：非阻塞模式（读取时无数据立即返回）
    fd = open(dev_name, O_RDWR | O_NONBLOCK, 0);
    if (fd == -1) {
        fprintf(stderr, "错误：无法打开设备 %s，%s\n", dev_name, strerror(errno));
        return -1;
    }
    printf("成功打开设备：%s\n", dev_name);
    return 0;
}

// 查询设备能力
static int query_capability(void)
{
    struct v4l2_capability cap;
    // VIDIOC_QUERYCAP：获取设备基本信息（驱动名称、设备名称、支持的模式等）
    if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == -1) {
        perror("错误：ioctl(VIDIOC_QUERYCAP) 失败");
        return -1;
    }

    // 检查是否支持视频捕获（V4L2_CAP_VIDEO_CAPTURE）
    // 和流模式（V4L2_CAP_STREAMING）
    printf("设备能力信息：\n");
    printf("  驱动名称：%s\n", cap.driver);
    printf("  设备名称：%s\n", cap.card);
    printf("  支持视频捕获：%s\n",
           (cap.capabilities & V4L2_CAP_VIDEO_CAPTURE) ? "是" : "否");
    printf("  支持流模式：%s\n",
           (cap.capabilities & V4L2_CAP_STREAMING) ? "是" : "否");

    if (!(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE)) {
        fprintf(stderr, "错误：设备不支持视频捕获！\n");
        return -1;
    }
    return 0;
}

// 设置视频格式（分辨率和像素格式）
static int set_format(int width, int height, int pixelformat)
{
    struct v4l2_format fmt;
    CLEAR(fmt);
    fmt.type                = V4L2_BUF_TYPE_VIDEO_CAPTURE;  // 视频捕获类型
    fmt.fmt.pix.width        = width;                         // 图像宽度
    fmt.fmt.pix.height       = height;                        // 图像高度
    fmt.fmt.pix.pixelformat  = pixelformat;                  // 像素格式（如 V4L2_PIX_FMT_YUYV）
    fmt.fmt.pix.field        = V4L2_FIELD_ANY;                // 场模式（任意）

    // VIDIOC_S_FMT：设置视频格式
    if (ioctl(fd, VIDIOC_S_FMT, &fmt) == -1) {
        perror("错误：ioctl(VIDIOC_S_FMT) 失败");
        return -1;
    }

    // 确认实际设置的格式（驱动可能调整了参数）
    printf("设置视频格式：%dx%d，像素格式：%c%c%c%c\n",
           fmt.fmt.pix.width, fmt.fmt.pix.height,
           (pixelformat >> 0) & 0xFF,
           (pixelformat >> 8) & 0xFF,
           (pixelformat >> 16) & 0xFF,
           (pixelformat >> 24) & 0xFF);

    // 验证宽度和高度是否设置成功
    if (fmt.fmt.pix.width != (unsigned int)width ||
        fmt.fmt.pix.height != (unsigned int)height) {
        fprintf(stderr, "警告：实际分辨率 %dx%d 与请求 %dx%d 不匹配\n",
                fmt.fmt.pix.width, fmt.fmt.pix.height, width, height);
    }
    return 0;
}

// 请求并分配缓冲区
static int request_buffers(void)
{
    struct v4l2_requestbuffers req;
    CLEAR(req);
    req.count  = 4;                       // 请求 4 个缓冲区
    req.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    req.memory = V4L2_MEMORY_MMAP;        // 内存映射模式（效率高）

    // VIDIOC_REQBUFS：请求缓冲区
    if (ioctl(fd, VIDIOC_REQBUFS, &req) == -1) {
        perror("错误：ioctl(VIDIOC_REQBUFS) 失败");
        return -1;
    }

    n_buffers = req.count;
    printf("已请求 %u 个缓冲区\n", n_buffers);

    // 分配缓冲区数组内存
    buffers = calloc(n_buffers, sizeof(*buffers));
    if (!buffers) {
        fprintf(stderr, "错误：内存分配失败\n");
        return -1;
    }

    // 为每个缓冲区映射设备内存
    for (unsigned int i = 0; i < n_buffers; ++i) {
        struct v4l2_buffer buf;
        CLEAR(buf);
        buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        buf.index  = i;

        // VIDIOC_QUERYBUF：查询缓冲区信息（获取长度和偏移量）
        if (ioctl(fd, VIDIOC_QUERYBUF, &buf) == -1) {
            perror("错误：ioctl(VIDIOC_QUERYBUF) 失败");
            return -1;
        }

        // mmap：将设备内存映射到用户空间，start 指向图像数据
        buffers[i].length = buf.length;
        buffers[i].start  = mmap(NULL, buf.length,
                                   PROT_READ | PROT_WRITE,   // 可读可写
                                   MAP_SHARED,                // 共享模式
                                   fd, buf.m.offset);
        if (buffers[i].start == MAP_FAILED) {
            perror("错误：mmap 失败");
            return -1;
        }
        printf("  缓冲区 %u：偏移 0x%08x，大小 %u 字节\n",
               i, buf.m.offset, buf.length);
    }
    return 0;
}

// 将所有缓冲区放入采集队列
static int enqueue_buffers(void)
{
    for (unsigned int i = 0; i < n_buffers; ++i) {
        struct v4l2_buffer buf;
        CLEAR(buf);
        buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        buf.index  = i;

        // VIDIOC_QBUF：将缓冲区放入输入队列，等待填充数据
        if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
            perror("错误：ioctl(VIDIOC_QBUF) 失败");
            return -1;
        }
    }
    return 0;
}

// 启动视频流
static int start_streaming(void)
{
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    // VIDIOC_STREAMON：开启视频流，开始采集
    if (ioctl(fd, VIDIOC_STREAMON, &type) == -1) {
        perror("错误：ioctl(VIDIOC_STREAMON) 失败");
        return -1;
    }
    printf("视频流已启动\n");
    return 0;
}

// 采集一帧图像
static int capture_frame(void)
{
    struct v4l2_buffer buf;
    fd_set fds;
    struct timeval tv;
    int ret;

    // 初始化文件描述符集合
    FD_ZERO(&fds);
    FD_SET(fd, &fds);

    // 设置超时：2 秒
    tv.tv_sec  = 2;
    tv.tv_usec = 0;

    // select：等待数据可读或超时
    ret = select(fd + 1, &fds, NULL, NULL, &tv);
    if (ret == -1) {
        perror("错误：select 失败");
        return -1;
    } else if (ret == 0) {
        fprintf(stderr, "错误：等待帧数据超时（2秒内无数据）\n");
        return -1;
    }

    CLEAR(buf);
    buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;

    // VIDIOC_DQBUF：从输出队列取出已填充数据的缓冲区
    if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
        perror("错误：ioctl(VIDIOC_DQBUF) 失败");
        return -1;
    }

    printf("成功采集一帧：缓冲区索引=%u，大小=%u 字节\n",
           buf.index, buf.bytesused);

    // 此时 buffers[buf.index].start 包含图像数据
    // 可以在这里处理图像数据，例如保存为文件

    // 将缓冲区重新放入输入队列
    if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
        perror("错误：ioctl(VIDIOC_QBUF) 重新入队失败");
        return -1;
    }

    return 0;
}

// 停止视频流
static int stop_streaming(void)
{
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    // VIDIOC_STREAMOFF：停止视频流
    if (ioctl(fd, VIDIOC_STREAMOFF, &type) == -1) {
        perror("错误：ioctl(VIDIOC_STREAMOFF) 失败");
        return -1;
    }
    printf("视频流已停止\n");
    return 0;
}

// 关闭设备并释放资源
static void close_device(void)
{
    // 解除内存映射
    for (unsigned int i = 0; i < n_buffers; ++i) {
        if (buffers[i].start != MAP_FAILED && buffers[i].start != NULL) {
            munmap(buffers[i].start, buffers[i].length);
        }
    }
    free(buffers);

    // 关闭设备文件
    if (fd != -1) {
        close(fd);
        printf("设备已关闭\n");
    }
}

// 主函数
int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "用法：%s <设备节点>\n", argv[0]);
        fprintf(stderr, "示例：%s /dev/video0\n", argv[0]);
        return 1;
    }

    const char *dev_name = argv[1];

    // 逐步执行初始化流程
    if (open_device(dev_name) == -1) return 1;
    if (query_capability() == -1)    return 1;
    if (set_format(640, 480, V4L2_PIX_FMT_YUYV) == -1) return 1;
    if (request_buffers() == -1)     return 1;
    if (enqueue_buffers() == -1)     return 1;
    if (start_streaming() == -1)     return 1;

    // 连续采集 5 帧
    printf("\n开始采集 5 帧图像...\n");
    for (int i = 0; i < 5; i++) {
        printf("--- 帧 %d ---\n", i + 1);
        if (capture_frame() == -1) break;
    }

    // 清理
    stop_streaming();
    close_device();
    return 0;
}
```

**编译并运行**：

```bash
# 在 ~/robot_ws/src/rdk_deploy/ 目录下
gcc v4l2_capture.c -o v4l2_capture -Wall

# 运行（假设摄像头在 /dev/video0）
./v4l2_capture /dev/video0

# 预期输出：
# 成功打开设备：/dev/video0
# 设备能力信息：
#   驱动名称：uvcvideo
#   设备名称：HD Webcam
#   支持视频捕获：是
#   支持流模式：是
# 设置视频格式：640x480，像素格式：YUYV
# 已请求 4 个缓冲区
# 视频流已启动
# 成功采集一帧：缓冲区索引=0，大小=614400 字节
```

---

## 4. ROS2 图像采集

### 4.1 v4l2_camera 节点使用

ROS2 提供了开箱即用的 `v4l2_camera` 包，可以将 V4L2 设备直接发布为 ROS2 图像话题。

```bash
# 安装 v4l2_camera 包
sudo apt install -y ros-humble-v4l2-camera

# 手动启动摄像头节点（分辨率为 640x480，30fps）
ros2 run v4l2_camera v4l2_camera_node --ros-args \
    -p video_device:=/dev/video0 \
    -p image_size:="[640,480]" \
    -p pixel_format:=YUYV \
    -p framerate:=30.0
```

### 4.2 image_transport 图像压缩

`image_transport` 是 ROS2 中图像传输的增强框架，支持多种压缩格式（H264、H265、JPEG、PNG 等）：

```bash
# 安装图像传输插件
sudo apt install -y ros-humble-image-transport-plugins

# 查看图像话题列表
ros2 topic list | grep image
# 预期输出：
# /camera/image_raw        （原始图像）
# /camera/image_raw/compressed  （JPEG 压缩）
# /camera/image_raw/theora   （Theora 视频压缩，已废弃）

# 查看原始图像话题信息
ros2 topic info /camera/image_raw
```

### 4.3 launch 启动文件编写

**文件路径**：`~/robot_ws/src/rdk_deploy/rdk_deploy/launch/camera.launch.py`

```python
"""
摄像头启动 launch 文件
用法：ros2 launch rdk_deploy camera.launch.py
"""

import launch
from launch_ros.actions import Node


def generate_launch_description():
    """生成 launch 描述，启动摄像头节点"""

    # 定义 v4l2_camera 节点参数
    # video_device：摄像头设备节点路径
    # image_size：图像分辨率 [宽度, 高度]
    # pixel_format：像素格式，YUYV 需要额外转换；MJPG 效率更高
    # framerate：帧率
    # camera_frame_id：图像消息的坐标系名称
    camera_node = Node(
        package='v4l2_camera',          # ROS2 包名
        executable='v4l2_camera_node', # 可执行节点名
        name='v4l2_camera',             # 节点名称
        namespace='camera',             # 命名空间，话题前缀
        parameters=[{
            'video_device': '/dev/video0',       # 摄像头设备路径
            'image_size': [640, 480],            # 分辨率 640x480
            'pixel_format': 'YUYV',              # YUYV 格式（需 cv_bridge 转换）
            # 如摄像头支持 MJPG，设为 'MJPG' 可减少 CPU 占用
            # 'pixel_format': 'MJPG',
            'framerate': 30.0,                   # 30 fps
            'camera_frame_id': 'camera_link',    # 相机坐标系 ID
            'camera_name': 'hd_webcam',          # 相机名称（用于 tf2 前缀）
        }],
        output='screen',               # 输出到屏幕（便于调试）
        emulate_tty=True,              # 模拟 TTY（支持颜色输出）
    )

    return launch.LaunchDescription([
        camera_node
    ])
```

**启动摄像头**：

```bash
# 方式一：使用 launch 文件启动
ros2 launch rdk_deploy camera.launch.py

# 方式二：直接运行包（如果已编译为独立包）
ros2 run v4l2_camera v4l2_camera_node \
    --ros-args -p video_device:=/dev/video0 -p image_size:="[640,480]"
```

### 4.4 独立 ROS2 包创建与编译

如果想把 launch 文件和节点编译为独立 ROS2 包：

```bash
# 创建工作空间结构
mkdir -p ~/robot_ws/src/rdk_deploy/rdk_deploy/launch
mkdir -p ~/robot_ws/src/rdk_deploy/scripts

# 编写 package.xml（包清单）
cat > ~/robot_ws/src/rdk_deploy/package.xml << 'EOF'
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd"
            schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>rdk_deploy</name>
  <version>1.0.0</version>
  <description>RDK-X5 部署工具包</description>
  <maintainer email="ubuntu@localhost">ubuntu</maintainer>
  <license>MIT</license>

  <buildtool_depend>ament_python</buildtool_depend>
  <exec_depend>v4l2_camera</exec_depend>
  <exec_depend>launch_ros</exec_depend>
  <exec_depend>cv_bridge</exec_depend>
  <exec_depend>image_transport</exec_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
EOF

# 编写 setup.py
cat > ~/robot_ws/src/rdk_deploy/setup.py << 'EOF'
from setuptools import setup

package_name = 'rdk_deploy'
setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name + '/launch',
         ['rdk_deploy/launch/camera.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    description='RDK-X5 deployment utilities',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_publisher = scripts.camera_publisher:main',
        ],
    },
)
EOF

# 复制 launch 文件
cp camera.launch.py ~/robot_ws/src/rdk_deploy/rdk_deploy/launch/

# 编译
cd ~/robot_ws
colcon build --packages-select rdk_deploy
source install/setup.bash

# 启动
ros2 launch rdk_deploy camera.launch.py
```

---

## 5. Python OpenCV 采集

### 5.1 OpenCV VideoCapture 读取

Python OpenCV 提供了简洁的 `cv2.VideoCapture` 接口，无需关心 v4l2 底层细节：

```python
import cv2

# 打开摄像头（0 表示第一个摄像头，/dev/video0）
# 传入视频文件路径也可读取视频
cap = cv2.VideoCapture(0)

# 检查摄像头是否成功打开
if not cap.isOpened():
    print("错误：无法打开摄像头")
    exit(1)

# 设置分辨率（部分摄像头可能不响应，取决于驱动支持）
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # 宽度 640
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # 高度 480

# 设置帧率
cap.set(cv2.CAP_PROP_FPS, 30)

# 查询实际参数
actual_width  = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
actual_fps    = cap.get(cv2.CAP_PROP_FPS)
print(f"实际分辨率：{actual_width}x{actual_height}")
print(f"实际帧率：{actual_fps}")

# 读取一帧（ret 为是否成功，frame 为图像数组，格式为 BGR）
ret, frame = cap.read()
if ret:
    print(f"读取成功，图像尺寸：{frame.shape}")
else:
    print("读取失败")

# 释放资源
cap.release()
```

### 5.2 图像格式转换（BGR → RGB）

OpenCV 默认使用 **BGR** 格式，而多数图像处理库（PIL、matplotlib、深度学习框架）使用 **RGB** 格式，需要手动转换：

```python
import cv2

cap = cv2.VideoCapture(0)
ret, frame = cap.read()
cap.release()

if ret:
    # BGR → RGB（用于深度学习模型输入）
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # RGB → BGR（用于 OpenCV 显示或编码）
    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    # 灰度图转换
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # HSV 颜色空间（用于颜色检测）
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    print(f"原始 BGR 形状：{frame.shape}")
    print(f"RGB 形状：{frame_rgb.shape}")
    print(f"灰度图形状：{gray.shape}")
```

### 5.3 ROS2 图像消息发布

将 OpenCV 采集的图像发布为 ROS2 `sensor_msgs/Image` 消息：

**文件路径**：`~/robot_ws/src/rdk_deploy/scripts/camera_publisher.py`

```python
#!/usr/bin/env python3
"""
OpenCV 摄像头图像发布节点
将 USB 摄像头采集的图像通过 ROS2 话题发布

订阅话题：无需订阅
发布话题：/camera/image_raw (sensor_msgs/Image)
"""

import rclpy
from rclpy.node import Node
import cv2
from cv_bridge import CvBridge          # OpenCV ↔ ROS 图像消息格式转换工具
from sensor_msgs.msg import Image      # ROS2 标准图像消息


class CameraPublisher(Node):
    """摄像头发布节点类"""

    def __init__(self):
        super().__init__('camera_publisher')

        # 声明参数（可在 launch 或命令行覆盖）
        self.declare_parameter('video_device', '/dev/video0')
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('framerate', 30.0)

        # 读取参数值
        video_device  = self.get_parameter('video_device').value
        frame_width   = self.get_parameter('frame_width').value
        frame_height  = self.get_parameter('frame_height').value
        framerate     = self.get_parameter('framerate').value

        # 初始化 OpenCV 视频捕获
        self.cap = cv2.VideoCapture(video_device)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开摄像头：{video_device}")

        # 设置摄像头分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.cap.set(cv2.CAP_PROP_FPS,          framerate)

        # 实际分辨率
        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.get_logger().info(
            f"摄像头已打开，分辨率：{actual_w}x{actual_h}，帧率：{framerate}fps")

        # 初始化 CvBridge（用于 OpenCV ↔ ROS Image 消息互相转换）
        # BGR8：OpenCV 的 3 通道 8 位 BGR 图像编码格式
        self.bridge = CvBridge()

        # 创建发布者（队列大小 10）
        self.publisher = self.create_publisher(
            Image,
            'image_raw',      # 话题名称
            10
        )

        # 创建定时器，按帧率周期发布
        # timer_period = 1/帧率（秒）
        timer_period = 1.0 / framerate
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.frame_count = 0  # 帧计数器（用于日志）

    def timer_callback(self):
        """
        定时器回调函数，每帧执行一次
        从摄像头读取图像并发布为 ROS2 消息
        """
        # 读取一帧（BGR 格式）
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn("摄像头读取失败，跳过本帧")
            return

        self.frame_count += 1

        # 将 OpenCV BGR 图像转换为 ROS2 Image 消息
        # "bgr8" 表示 3 通道 8 位 BGR 格式，是 ROS 中最常用的图像编码
        try:
            image_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"CvBridge 转换失败：{e}")
            return

        # 设置图像消息头（包含时间戳和坐标系）
        # stamp：时间戳（ROS2 使用 builtin_interfaces/Time）
        image_msg.header.stamp = self.get_clock().now().to_msg()
        # frame_id：坐标系 ID，用于 tf2 坐标变换
        image_msg.header.frame_id = "camera_link"

        # 发布图像消息
        self.publisher.publish(image_msg)

        # 每 30 帧打印一次日志（避免刷屏）
        if self.frame_count % 30 == 0:
            self.get_logger().info(
                f"已发布 {self.frame_count} 帧，尺寸：{frame.shape[1]}x{frame.shape[0]}")

    def destroy_node(self):
        """节点销毁时释放摄像头资源"""
        self.cap.release()
        super().destroy_node()


def main(args=None):
    """入口函数"""
    rclpy.init(args=args)  # 初始化 ROS2 客户端库
    try:
        node = CameraPublisher()
        rclpy.spin(node)     # 进入事件循环，保持节点运行
    except RuntimeError as e:
        print(f"启动失败：{e}")
    finally:
        if rclpy.ok():
            rclpy.shutdown()  # 关闭 ROS2 客户端库


if __name__ == '__main__':
    main()
```

**添加可执行权限并运行**：

```bash
# 添加可执行权限
chmod +x ~/robot_ws/src/rdk_deploy/scripts/camera_publisher.py

# 运行节点（需要先 source 工作空间）
source ~/robot_ws/install/setup.bash
ros2 run rdk_deploy camera_publisher

# 或指定参数运行
ros2 run rdk_deploy camera_publisher --ros-args \
    -p video_device:=/dev/video0 \
    -p frame_width:=1280 \
    -p frame_height:=720 \
    -p framerate:=30.0
```

---

## 6. 图像预处理

### 6.1 图像缩放、裁剪

```python
import cv2
import numpy as np

# 假设 frame 是从摄像头读取的 BGR 图像 (H, W, C)
# 原始尺寸示例：[480, 640, 3]

# ===== 图像缩放 =====
# cv2.resize(src, dsize, fx, fy, interpolation)
# dsize：目标尺寸 (宽度, 高度)
# fx, fy：缩放因子（当 dsize=None 时生效）
# interpolation：插值方法

# 按固定尺寸缩放
resized = cv2.resize(frame, (320, 240))  # 缩小到 320x240

# 按比例缩放（宽高各缩小一半）
resized_half = cv2.resize(frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

# 放大两倍（使用 INTER_LINEAR，效率高）
resized_big = cv2.resize(frame, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_LINEAR)

print(f"原始形状：{frame.shape}")        # (480, 640, 3)
print(f"缩小后：{resized.shape}")         # (240, 320, 3)

# ===== 图像裁剪 =====
# NumPy 数组直接切片：[行_start:行_end, 列_start:列_end]
# 注意：行对应高度（Y），列对应宽度（X）

# 裁剪中心区域（从第 100 行到第 380 行，第 160 列到第 480 列）
cropped = frame[100:380, 160:480]

# 裁剪左半边
left_half = frame[:, :320]

# 裁left_half = frame[:, :320]

# 裁剪右半边
right_half = frame[:, 320:]

print(f"裁剪后形状：{cropped.shape}")  # (280, 320, 3)
```

### 6.2 颜色空间转换

```python
import cv2
import numpy as np

# 假设 frame 是 BGR 图像
# BGR → RGB（用于显示或 PIL 输入）
rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

# BGR → 灰度图
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

# BGR → HSV（用于颜色检测）
# H: 0-180（色调），S: 0-255（饱和度），V: 0-255（明度）
hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# 灰度图 → BGR（用于与彩色图合并或 ROS 发布）
gray_to_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

# 示例：检测红色物体
lower_red = np.array([0, 120, 70])    # 红色下限（H:0-10, S:高, V:高）
upper_red = np.array([10, 255, 255])  # 红色上限
mask = cv2.inRange(hsv, lower_red, upper_red)  # 生成掩码
result = cv2.bitwise_and(frame, frame, mask=mask)  # 应用掩码

print(f"HSV 形状：{hsv.shape}")   # (H, W, 3)
print(f"灰度图形状：{gray.shape}") # (H, W)
```

### 6.3 图像翻转与旋转

```python
import cv2

# 假设 frame 是 BGR 图像

# ===== 翻转 =====
# flipCode：0=垂直翻转（上下），1=水平翻转（左右），-1=两者皆翻转
flipped_vertical   = cv2.flip(frame, 0)  # 上下翻转
flipped_horizontal = cv2.flip(frame, 1)  # 左右翻转
flipped_both       = cv2.flip(frame, -1) # 180 度旋转

# ===== 旋转 =====
# getRotationMatrix2D(center, angle, scale)
# center：旋转中心（图像宽高的一半）
# angle：旋转角度（正值为逆时针）
# scale：缩放因子（1.0 表示不缩放）
h, w = frame.shape[:2]
center = (w / 2, h / 2)

# 旋转 90 度（需要配合 transpose 和 flip）
# 旋转 90 度顺时针
rotated_90_cw = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
# 旋转 90 度逆时针
rotated_90_ccw = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
# 旋转 180 度
rotated_180 = cv2.rotate(frame, cv2.ROTATE_180)

# 任意角度旋转
angle = 45
scale = 1.0
M = cv2.getRotationMatrix2D(center, angle, scale)
rotated = cv2.warpAffine(frame, M, (w, h))  # 应用仿射变换

# ===== 平移 =====
# M 是 2x3 变换矩阵，tx/ty 为平移量
tx, ty = 50, -30  # x 方向平移 50 像素，y 方向平移 -30 像素
M = np.float32([[1, 0, tx], [0, 1, ty]])
translated = cv2.warpAffine(frame, M, (w, h))

print(f"原尺寸：{frame.shape[:2]}")
print(f"旋转后尺寸：{rotated.shape[:2]}")
```

---

## 7. 部署与验证

### 7.1 文件放置路径

```
~/robot_ws/src/rdk_deploy/
├── package.xml                # ROS2 包清单
├── setup.py                   # Python 包配置
├── v4l2_capture.c             # C 语言 v4l2 采集程序
├── scripts/
│   └── camera_publisher.py    # Python OpenCV 采集发布节点
└── rdk_deploy/
    └── launch/
        └── camera.launch.py   # ROS2 launch 启动文件
```

### 7.2 rsync/SSH 部署命令

```bash
# 从宿主机将代码同步到 RDK-X5
# -avz：归档模式、显示详情、gzip 压缩
# --exclude：排除不需同步的文件
rsync -avz --exclude='*.pyc' --exclude='__pycache__' \
      --exclude='build' --exclude='install' --exclude='log' \
      ~/robot_ws/src/rdk_deploy/ \
      ubuntu@192.168.1.101:~/robot_ws/src/rdk_deploy/

# 在 RDK-X5 上编译工作空间
ssh ubuntu@192.168.1.101 "cd ~/robot_ws && colcon build --packages-select rdk_deploy"

# SSH 远程执行单个命令
ssh ubuntu@192.168.1.101 "source ~/robot_ws/install/setup.bash && ros2 launch rdk_deploy camera.launch.py"
```

### 7.3 systemd 服务配置（开机自启）

将摄像头节点配置为 systemd 服务，实现开机自启：

```bash
# 在 RDK-X5 上创建 systemd 服务文件
sudo nano /etc/systemd/system/camera.service
```

```ini
[Unit]
Description=RDK-X5 Camera Publisher Service
After=network.target  # 网络就绪后再启动

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/robot_ws
ExecStart=/usr/bin/bash -c "source /home/ubuntu/robot_ws/install/setup.bash && ros2 launch rdk_deploy camera.launch.py"
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启用服务（开机自启）
sudo systemctl enable camera

# 启动服务（立即启动）
sudo systemctl start camera

# 查看服务状态
sudo systemctl status camera

# 查看日志
journalctl -u camera -f
```

### 7.4 rqt_image_view 验证

```bash
# 在有图形界面的机器上（或者通过 X11 转发）启动图像查看器
# RDK-X5 通常没有显示器，建议在 PC 端运行
rqt_image_view

# 或使用 ros2 run 方式
ros2 run rqt_image_view rqt_image_view

# 通过 SSH X11 转发（需要 PC 端安装 X server，如 XQuartz 或 VcXsrv）
# 在 Mac/Linux PC 端执行：
ssh -X ubuntu@192.168.1.101 "source ~/robot_ws/install/setup.bash && rqt_image_view"

# 查看 ROS2 话题列表（确认图像话题存在）
ros2 topic list | grep image
# 预期输出：
# /camera/image_raw
# /camera/image_raw/compressed

# 查看话题带宽占用
ros2 topic hz /camera/image_raw
# 预期输出类似：average rate: 30.003

# 查看话题带宽（字节/秒）
ros2 topic bw /camera/image_raw
```

---

## 8. 练习题

### 练习 1：摄像头设备识别

使用命令行工具完成以下操作：

1. 列出系统所有 USB 设备，找到摄像头的厂商 ID 和产品 ID
2. 使用 `v4l2-ctl` 查看 `/dev/video0` 支持的所有像素格式和分辨率组合
3. 使用 `v4l2-ctl` 将摄像头设置为 1280x720 分辨率、YUYV 格式、30fps，并抓取一帧保存为 PPM 文件

**预期结果**：能够独立完成摄像头设备识别，并成功配置参数采集图像。

---

### 练习 2：编写 v4l2 采集程序

参考 3.4 节的 C 代码，实现以下扩展功能：

1. 添加命令行参数解析，支持传入分辨率、像素格式、采集帧数
2. 将采集的 YUYV 格式图像保存为 JPEG 文件（使用 libjpeg）
3. 采集指定帧数后自动退出程序

**提示**：
- 使用 `getopt_long()` 解析命令行参数
- YUYV 转 JPEG 可使用 `cjpeg` 工具或 libjpeg 库

---

### 练习 3：ROS2 图像话题发布

参考 5.3 节的 Python 代码，实现以下功能：

1. 发布两个话题：`/camera/raw`（原始图像）和 `/camera/resized`（缩放后图像，分辨率 320x240）
2. 添加参数 `enable_flip`，支持水平翻转（flip_code=1）
3. 添加 ROS2 参数服务器支持，可在运行时用 `ros2 param set` 动态调整参数

---

### 练习 4：颜色物体跟踪

综合运用本课程知识，实现一个简单的颜色物体跟踪节点：

1. 使用 HSV 颜色空间检测指定颜色的物体（参考 6.2 节）
2. 计算检测到的物体中心点坐标
3. 将中心点坐标发布为 `geometry_msgs/Point` 话题
4. 将检测结果（带边框的图像）发布为 `/camera/detection` 话题

**选做**：添加 PID 控制算法，根据物体中心点偏差控制 TurtleBot3 机器人移动，使物体保持在图像中心。

---

### 练习 5：ROS2 launch 文件配置

编写一个完整的 launch 文件，实现：

1. 启动 `v4l2_camera` 节点，分辨率 640x480，30fps
2. 启动 `camera_publisher` 节点（自研 Python 节点）
3. 启动 `rqt_image_view` 节点用于图像显示
4. 使用 `DeclareLaunchArgument` 声明所有可配置参数（video_device、frame_width 等）
5. 添加 `LogInfo` 打印启动信息

---

## 9. 答案

### 答案 1：摄像头设备识别

```bash
# 1. 列出 USB 设备，找到摄像头
lsusb
# 输出示例：Bus 001 Device 003: ID 046d:0825 Logitech, Inc. HD Webcam C920
# 厂商 ID：046d，产品 ID：0825

# 2. 查看支持的格式和分辨率
v4l2-ctl -d /dev/video0 --list-formats-ext

# 3. 设置参数并抓取单帧
v4l2-ctl -d /dev/video0 --set-fmt-video=width=1280,height=720,pixelformat=YUYV
v4l2-ctl -d /dev/video0 --set-parm=30
v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=1 --stream-to=capture.ppm

# 确认文件已保存
ls -lh capture.ppm
```

---

### 答案 2：v4l2 采集程序扩展

以下为扩展版本的关键修改部分（`getopt` 参数解析和 JPEG 保存）：

```c
// 参数解析结构体
struct {
    int width;
    int height;
    int pixelformat;
    int frames;
    const char *output;
} opts = {
    .width = 640,
    .height = 480,
    .pixelformat = V4L2_PIX_FMT_YUYV,
    .frames = 5,
    .output = "output.ppm"
};

// 解析命令行参数
int c;
static struct option long_options[] = {
    {"width",   required_argument, 0, 'w'},
    {"height",  required_argument, 0, 'h'},
    {"format",  required_argument, 0, 'f'},
    {"frames",  required_argument, 0, 'n'},
    {"output",  required_argument, 0, 'o'},
    {0, 0, 0, 0}
};
while ((c = getopt_long(argc, argv, "w:h:f:n:o:", long_options, NULL)) != -1) {
    switch (c) {
        case 'w': opts.width    = atoi(optarg); break;
        case 'h': opts.height   = atoi(optarg); break;
        case 'n': opts.frames   = atoi(optarg); break;
        case 'o': opts.output   = optarg;       break;
        case 'f':
            if (strcmp(optarg, "YUYV") == 0)
                opts.pixelformat = V4L2_PIX_FMT_YUYV;
            else if (strcmp(optarg, "MJPG") == 0)
                opts.pixelformat = V4L2_PIX_FMT_MJPEG;
            break;
    }
}
```

---

### 答案 3：ROS2 双话题发布

**文件路径**：`~/robot_ws/src/rdk_deploy/scripts/camera_multi_publisher.py`

```python
#!/usr/bin/env python3
"""双话题图像发布节点（原始图 + 缩放图）"""

import rclpy
from rclpy.node import Node
import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image


class CameraMultiPublisher(Node):
    def __init__(self):
        super().__init__('camera_multi_publisher')

        # 参数声明
        self.declare_parameter('video_device', '/dev/video0')
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('framerate', 30.0)
        self.declare_parameter('resize_width', 320)
        self.declare_parameter('resize_height', 240)
        self.declare_parameter('enable_flip', False)

        # 读取参数
        video_device  = self.get_parameter('video_device').value
        frame_width   = self.get_parameter('frame_width').value
        frame_height  = self.get_parameter('frame_height').value
        framerate     = self.get_parameter('framerate').value
        self.resize_w = self.get_parameter('resize_width').value
        self.resize_h = self.get_parameter('resize_height').value
        self.enable_flip = self.get_parameter('enable_flip').value

        # 初始化摄像头
        self.cap = cv2.VideoCapture(video_device)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开摄像头：{video_device}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  frame_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.cap.set(cv2.CAP_PROP_FPS,          framerate)

        self.bridge = CvBridge()

        # 创建两个发布者
        self.pub_raw    = self.create_publisher(Image, 'raw',    10)
        self.pub_resized = self.create_publisher(Image, 'resized', 10)

        timer_period = 1.0 / framerate
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # 翻转处理
        if self.enable_flip:
            frame = cv2.flip(frame, 1)  # 水平翻转

        # 发布原始图像
        raw_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        raw_msg.header.stamp = self.get_clock().now().to_msg()
        raw_msg.header.frame_id = "camera_link"
        self.pub_raw.publish(raw_msg)

        # 缩放并发布
        resized = cv2.resize(frame, (self.resize_w, self.resize_h))
        resized_msg = self.bridge.cv2_to_imgmsg(resized, encoding="bgr8")
        resized_msg.header.stamp = self.get_clock().now().to_msg()
        resized_msg.header.frame_id = "camera_link"
        self.pub_resized.publish(resized_msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        rclpy.spin(CameraMultiPublisher())
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**运行时动态调参**：

```bash
# 运行时启用水平翻转
ros2 param set /camera_multi_publisher enable_flip true

# 修改缩放分辨率
ros2 param set /camera_multi_publisher resize_width 640
ros2 param set /camera_multi_publisher resize_height 480
```

---

### 答案 4：颜色物体跟踪（简化版）

```python
#!/usr/bin/env python3
"""
简单颜色物体跟踪节点
检测指定颜色的物体，发布中心点坐标和带检测框的图像
"""

import rclpy
from rclpy.node import Node
import cv2
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point


class ColorTracker(Node):
    def __init__(self):
        super().__init__('color_tracker')

        # 可通过参数配置待检测颜色
        self.declare_parameter('video_device', '/dev/video0')
        self.declare_parameter('target_color', 'red')  # red/green/blue
        self.declare_parameter('hsv_lower', [0, 120, 70])
        self.declare_parameter('hsv_upper', [10, 255, 255])

        video_device  = self.get_parameter('video_device').value
        self.lower = np.array(self.get_parameter('hsv_lower').value)
        self.upper = np.array(self.get_parameter('hsv_upper').value)

        self.cap = cv2.VideoCapture(video_device)
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开摄像头")

        self.bridge = CvBridge()

        # 发布检测结果图像
        self.image_pub = self.create_publisher(Image, 'detection', 10)
        # 发布物体中心点
        self.point_pub = self.create_publisher(Point, 'target_point', 10)

        self.timer = self.create_timer(1/30.0, self.timer_callback)

    def timer_callback(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # BGR → HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 创建掩码，提取目标颜色区域
        mask = cv2.inRange(hsv, self.lower, self.upper)

        # 形态学处理：去噪
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 找到轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)

        center_x, center_y = -1, -1  # 默认值：未检测到

        if contours:
            # 找最大轮廓
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            if area > 500:  # 过滤小噪点
                x, y, w, h = cv2.boundingRect(largest)
                # 画矩形框
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                # 计算中心点
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

        # 发布图像
        det_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        det_msg.header.stamp = self.get_clock().now().to_msg()
        det_msg.header.frame_id = "camera_link"
        self.image_pub.publish(det_msg)

        # 发布中心点
        point = Point()
        point.x = float(center_x)
        point.y = float(center_y)
        point.z = 0.0
        self.point_pub.publish(point)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    try:
        rclpy.spin(ColorTracker())
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

### 答案 5：ROS2 launch 文件

```python
"""完整摄像头 launch 文件"""
import launch
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # 声明 launch 参数（可从命令行或上级 launch 传入）
    declare_video_device = DeclareLaunchArgument(
        'video_device', default_value='/dev/video0',
        description='摄像头设备路径')
    declare_width = DeclareLaunchArgument(
        'frame_width', default_value='640',
        description='图像宽度')
    declare_height = DeclareLaunchArgument(
        'frame_height', default_value='480',
        description='图像高度')
    declare_framerate = DeclareLaunchArgument(
        'framerate', default_value='30.0',
        description='帧率')

    # 获取参数值
    video_device = LaunchConfiguration('video_device')
    frame_width  = LaunchConfiguration('frame_width')
    frame_height = LaunchConfiguration('frame_height')
    framerate    = LaunchConfiguration('framerate')

    return LaunchDescription([
        # 打印启动信息
        LogInfo(msg=['启动摄像头节点，设备：', video_device,
                     '，分辨率：', frame_width, 'x', frame_height]),

        declare_video_device,
        declare_width,
        declare_height,
        declare_framerate,

        # v4l2_camera 节点
        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            name='v4l2_camera',
            namespace='camera',
            parameters=[{
                'video_device': video_device,
                'image_size': [640, 480],
                'pixel_format': 'YUYV',
                'framerate': 30.0,
                'camera_frame_id': 'camera_link',
            }],
            output='screen',
        ),

        # 自研 Python 节点
        Node(
            package='rdk_deploy',
            executable='camera_publisher',
            name='camera_publisher',
            namespace='camera',
            parameters=[{
                'video_device': video_device,
                'frame_width': 640,
                'frame_height': 480,
                'framerate': 30.0,
            }],
            output='screen',
        ),
    ])
```

**运行带参数的 launch**：

```bash
ros2 launch rdk_deploy camera_full.launch.py \
    video_device:=/dev/video0 \
    frame_width:=1280 \
    frame_height:=720 \
    framerate:=30.0
```

---

## 10. 常见问题排查

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| `lsusb` 找不到摄像头 | USB 连接不良或摄像头未供电 | 重新插拔 USB，或检查 USB 口供电 |
| `v4l2-ctl` 报错 "Not such device" | 设备节点名错误 | `ls -la /dev/video*` 确认正确节点 |
| `cv2.VideoCapture(0)` 返回 False | 设备被占用或权限不足 | `sudo chmod 666 /dev/video0`，或检查是否被其他程序占用 |
| 图像发绿/发红 | YUYV 格式未正确转换 | 使用 `cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YUYV)` 转换 |
| 采集帧率低 | YUYV 格式数据量大 | 切换到 MJPG 格式，或降低分辨率 |
| ROS2 话题无数据 | 节点未正确启动 | `ros2 topic echo /camera/image_raw` 检查是否有数据 |
| systemd 服务启动失败 | 环境变量未加载 | 在 service 文件中使用完整路径 source setup.bash |

---

## 下一步

完成本课程后，你可以继续学习：

- **10-2-Y：RDK-X5 双目摄像头采集** — 双目视觉深度测量基础
- **10-3-A：ROS2 标定工具使用** — 单目/双目摄像头内参标定
- **课程 7 系列** — 深度学习目标检测实战（YOLOv8）

---

*参考文档*：[地平线 RDK-X5 官方文档](https://developer.d-robotics.cc/rdk_doc/RDK-X5/latest) | [ROS2 v4l2_camera Wiki](https://index.ros.org/p/v4l2_camera/)
