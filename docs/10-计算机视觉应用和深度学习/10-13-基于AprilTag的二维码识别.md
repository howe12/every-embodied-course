# 10-13 基于AprilTag的二维码识别

> **前置课程**：10-2 图像基本处理、10-5 工业质检基础
> **后续课程**：10-14 深度学习目标检测实战

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在机器人系统中，精确的定位与导航是核心能力之一。想象一下，一个仓库机器人需要在货架间穿行并准确抓取目标物品——它如何知道自己在哪里？目标在哪里？传统方案依赖复杂的SLAM系统，但在很多工业场景中，有一种更简洁高效的方法：使用人工视觉标记（Artificial Visual Markers）。其中最著名的就是**AprilTag**——它就像贴在墙上的"条形码"，让机器人看一眼就能知道自己的精确位置和朝向。同时，我们也会介绍日常生活中更常见的**QR Code（二维码）**，了解它与AprilTag的区别与联系。本节将从原理出发，动手实现检测代码，并将其集成到ROS2机器人系统中。

---

## 目录

1. [AprilTag 简介](#1-apriltag-简介)
2. [AprilTag 检测原理](#2-apriltag-检测原理)
3. [传统二维码 QR Code](#3-传统二维码-qr-code)
4. [AprilTag vs QR Code 对比](#4-apriltag-vs-qr-code-对比)
5. [生成 AprilTag 与 QR Code](#5-生成-apriltag-与-qr-code)
6. [OpenCV 实践代码](#6-opencv-实践代码)
7. [ROS2 AprilTag 节点](#7-ros2-apriltag-节点)
8. [练习题](#练习题)
9. [答案](#答案)

---

## 1. AprilTag 简介

### 1.1 什么是 AprilTag

**AprilTag** 是一种专为机器视觉设计的人工视觉标记（Artificial Visual Marker / Fiducial Marker）。它看起来像一个黑白方块图案，类似于二维码，但有着严格设计的编码规则和独特的定位检测算法。

AprilTag 的名称来源于它最初于2010年4月（April）发布在美国明尼苏达大学的 Autonomous Vehicle Lab。它的设计者 **Ed Olson** 是著名的机器人学家，也是 ICRA 等顶会的程序委员会主席。

**AprilTag 长什么样？**

AprilTag 是由黑色正方形边框和内部编码区域组成的方块图案。黑色边框帮助快速定位，内部的二进制编码则携带 ID 信息。

```
┌──────────────┐
│  ■ ■ ■ ■ ■  │  ← 黑色边框（用于检测定位）
│  ■ □ □ □ ■  │
│  ■ □ ■ □ ■  │  ← 内部编码区域（二进制信息）
│  ■ □ □ □ ■  │
│  ■ □ ■ ■ □  │
│  ■ ■ ■ ■ ■  │  ← 黑色边框
└──────────────┘

        AprilTag 外观示例
```

### 1.2 与其他视觉标记的对比

在 AprilTag 出现之前和之后，科学家和工程师们设计过多种视觉标记系统：

| 标记类型 | 出现时间 | 特点 | 典型应用 |
|---------|---------|------|---------|
| **QR Code** | 1994年 | 包含丰富数据、可彩色、需要定位图案 | 商品标签、手机支付 |
| **AprilTag** | 2010年 | 专为机器人设计、易检测、支持位姿估计 | 机器人定位、相机标定 |
| **ArUco** | 2014年 | OpenCV内置、轻量、支持位姿估计 | AR、机器人定位 |
| **ARTag** | 2006年 | AprilTag前身、影响力大 | 学术研究 |
| **Checkerboard** | 1960s | 角点阵列、精密标定 | 相机标定 |
| **Charuco** | ~2015年 | ArUco+棋盘格组合 | 高精度标定 |

**为什么 AprilTag 在机器人领域特别受欢迎？**

1. **专为机器人位姿估计设计**：AprilTag 不仅能告诉你"看到了哪个标签"，还能精确计算出相机到这个标签的**6DoF位姿**（位置XYZ + 朝向Roll/Pitch/Yaw）
2. **检测速度快**：边缘检测算法在 CPU 上即可实时运行，无需 GPU
3. **鲁棒性强**：对部分遮挡、模糊、光照变化有较好容忍度
4. **编码紧凑**：同样面积下，AprilTag 比 QR Code 更容易被远距离识别

### 1.3 AprilTag 家族

AprilTag 有多种标签家族（Tag Family），不同家族的编码位数和检错能力不同：

| 家族 | 编码位数 | 可用标签数 | 纠错能力 | 特点 |
|------|---------|-----------|---------|------|
| **Tag16h5** | 5 bits | 30个 | 低 | 最小、最简单 |
| **Tag25h9** | 9 bits | 589个 | 高 | 较大、常用 |
| **Tag36h10** | 10 bits | 2324个 | 中 | 最常用 |
| **Tag36h11** | 11 bits | 587个 | 高 | 最小tag36、抗噪声好 |

> **命名规则**：`Tag<边长>h<汉明距离>`
> - `<边长>`：tag 编码区域的边长（不含边框），如16×16、25×25、36×36
> - `h<数字>`：汉明距离（Hamming Distance），表示纠错能力，数字越大纠错越强
> - `h5` = 汉明距离5，`h9` = 汉明距离9，`h10` = 汉明距离10，`h11` = 汉明距离11

**如何选择标签家族？**

```python
tag_family_info = {
    "Tag16h5": {
        "描述": "最小的标签家族，适合远距离或小尺寸场景",
        "可用ID数": 30,
        "优点": "条码最小，最远可识别距离最大",
        "缺点": "标签数少，纠错能力弱（h=5）",
        "推荐用途": "远距离大范围定位（无人机着落标记）"
    },
    "Tag25h9": {
        "描述": "中等尺寸，高纠错能力",
        "可用ID数": 589,
        "优点": "标签数较多，纠错强（h=9）",
        "缺点": "条码较大，远处识别困难",
        "推荐用途": "室内机器人精确定位"
    },
    "Tag36h10": {
        "描述": "最常用的中等尺寸家族",
        "可用ID数": 2324,
        "优点": "标签数量多，平衡尺寸和数量",
        "缺点": "汉明距离10，纠错中等",
        "推荐用途": "通用机器人定位、相机标定"
    },
    "Tag36h11": {
        "描述": "tag36家族中纠错最强的版本",
        "可用ID数": 587,
        "优点": "纠错能力最强（h=11），抗噪声最好",
        "缺点": "标签数相对tag36h10略少",
        "推荐用途": "对噪声敏感的工业环境"
    }
}

for family, info in tag_family_info.items():
    print(f"\n{family}: {info['描述']}")
    print(f"  可用ID: {info['可用ID数']}个 | 纠错: h={family[-1]}")
    print(f"  推荐: {info['推荐用途']}")
```

### 1.4 应用场景

**（1）机器人定位与导航**

机器人身上装着相机，当它看到贴在地面的 AprilTag 时，可以精确知道自己的位置。这在仓库机器人、工厂AGV（自动导引车）等场景中极为常见。相比SLAM，它不需要复杂的地图构建过程，定位精度可达毫米级。

**（2）相机标定**

AprilTag 的尺寸是精确已知的（你打印时自己设置），因此可以用来标定相机的内参和外参。相比传统的棋盘格标定，AprilTag 可以在任意角度下被检测到，标定效率更高。

**（3）无人机着陆引导**

在无人机自动着陆时，通过识别地面上的 AprilTag，可以精确知道无人机相对于着陆点的位置，实现安全精确的着陆。NASA 在一些火星探测器测试项目中也用过类似标记。

**（4）物体6DoF位姿估计**

在机器人抓取任务中，可以将 AprilTag 贴在目标物体或工作台上，机器人通过检测标签来精确知道目标的位置和朝向，实现精确抓取。

**（5）AR增强现实交互**

在 AR 应用中，AprilTag 可以作为"触发器"——当相机识别到特定标签时，在屏幕上叠加虚拟的 3D 物体或信息。

---

## 2. AprilTag 检测原理

### 2.1 整体流程

AprilTag 的检测过程可以分为以下几个步骤：

```
输入图像
    │
    ▼
┌─────────────────┐
│ 1. 灰度化        │  RGB → 灰度，简化后续处理
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 边缘检测      │  Canny 等算法提取边缘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 四边形检测    │  寻找闭合的方形轮廓
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. 编码解析      │  提取内部二进制编码
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 错误检测纠正  │  验证编码是否合法
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 6. 位姿估计      │  计算相机到标签的6DoF位姿
└────────┬────────┘
         │
         ▼
输出结果（标签ID + 位姿）
```

### 2.2 图像预处理与边缘检测

**灰度化**：将 RGB 彩色图像转换为单通道灰度图。AprilTag 是黑白图案，灰度图足以区分黑白区域。

```python
import cv2
import numpy as np

def preprocess_image(image):
    """
    AprilTag 检测前的图像预处理
    
    步骤：
    1. 灰度化：将彩色图转为灰度图
    2. 可选：自适应阈值处理，增强黑白对比
    """
    # 确保是灰度图
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # 可选：自适应阈值，使光照不均匀时也有好效果
    # 对于光照变化较大的环境特别有用
    # adaptive_threshold = cv2.adaptiveThreshold(
    #     gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    #     cv2.THRESH_BINARY, 11, 2
    # )
    
    return gray
```

**边缘检测**：使用 Canny 等边缘检测算法提取图像中的边缘信息。AprilTag 的黑色边框在灰度图上会形成明显的边缘。

```python
def detect_edges(gray_image, low_threshold=50, high_threshold=150):
    """
    使用 Canny 算法检测边缘
    
    Canny 算法步骤：
    1. 高斯模糊降噪
    2. 计算梯度（ Sobel 滤波器）
    3. 非极大值抑制（NMS）
    4. 双重阈值筛选边缘
    5. 边缘连接
    
    参数:
        low_threshold: 低阈值
        high_threshold: 高阈值
        低于 low 的像素被丢弃
        高于 high 的像素保留为边缘
        介于两者之间的像素需要与边缘相连才保留
    """
    # 高斯模糊：减少噪声干扰
    blurred = cv2.GaussianBlur(gray_image, (5, 5), 0)
    
    # Canny 边缘检测
    edges = cv2.Canny(blurred, low_threshold, high_threshold)
    
    print(f"边缘检测完成，检测到 {np.sum(edges > 0)} 个边缘像素")
    
    return edges
```

### 2.3 四边形检测

这是 AprilTag 检测的核心步骤。算法从边缘图像中寻找**凸四边形**（四个角点、凸多边形），作为候选的 AprilTag 外边框。

```python
def find_quadrilaterals(edges):
    """
    从边缘图像中提取四边形轮廓
    
    步骤：
    1. 轮廓发现（findContours）
    2. 近似多边形（approxPolyDP）
    3. 筛选凸四边形
    """
    # 发现所有轮廓
    contours, hierarchy = cv2.findContours(
        edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )
    
    candidate_quads = []
    
    for contour in contours:
        # 忽略太小的轮廓（不是 AprilTag）
        if cv2.contourArea(contour) < 100:
            continue
        
        # 多边形逼近
        epsilon = 0.02 * cv2.arcLength(contour, True)  # 逼近精度
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 必须是凸四边形
        if len(approx) == 4 and cv2.isContourConvex(approx):
            candidate_quads.append(approx)
    
    print(f"发现 {len(candidate_quads)} 个候选四边形")
    return candidate_quads
```

**为什么是四边形？**

AprilTag 的外边框是一个正方形，因此在图像中投影为一个四边形（透视投影下可能变形）。通过检测四边形，我们可以快速筛选出所有可能是 AprilTag 的区域。

### 2.4 编码解析

对于每个候选四边形，算法将其内部区域划分为网格，并根据每个格子中黑白像素的比例判断该位是"0"还是"1"。

```
┌──────────────┐
│■ ■ ■ ■ ■ ■ ■■│  外边框（已知为黑色）
│■ □ □ □ □ □ ■│
│■ □ ■ ■ □ □ ■│  ← 内部编码区域被划分为 NxN 格子
│■ □ □ □ ■ □ ■│     每格根据灰度均值判断黑白
│■ □ ■ □ □ ■ ■│
│■ □ □ □ ■ □ ■│
│■ ■ ■ ■ ■ ■ ■■│
└──────────────┘

假设内部编码为 6x6 区域：
每个格子判断为黑(0)或白(1) → 二进制串 → 转换为标签ID
```

```python
def decode_tag_quadrilateral(quad, tag_family="Tag36h11"):
    """
    从四边形区域解码 AprilTag ID
    
    参数:
        quad: 四边形四个角点（4x2数组）
        tag_family: 标签家族，决定编码区域大小
    
    返回:
        tag_id: 解码出的标签ID（如果有效）
        或者 None（如果解码失败）
    """
    # 根据家族确定编码区域大小
    # Tag36h11 -> 6x6 编码区域（36 bits）
    # Tag16h5  -> 4x4 编码区域（16 bits）
    family_configs = {
        "Tag36h11": {"grid_size": 6, "bits": 36},
        "Tag25h9":  {"grid_size": 5, "bits": 25},
        "Tag16h5":  {"grid_size": 4, "bits": 16},
    }
    
    grid_size = family_configs[tag_family]["grid_size"]
    
    # 四边形角点顺序：按照左上、右上、右下、左下排列
    # 通过透视变换将四边形矫正为正方形
    # 然后从正方形中采样网格
    
    # 使用单应性变换将四边形映射为正方形
    width = height = 200  # 输出图像尺寸（像素）
    
    # 定义正方形的四个目标角点
    dst_points = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)
    
    # 源角点（四边形的四个角）
    src_points = quad.astype(np.float32)
    
    # 计算透视变换矩阵
    H, _ = cv2.findHomography(src_points, dst_points)
    
    # 应用透视变换
    # warped_image = cv2.warpPerspective(...)
    
    # 从变换后的图像中提取编码
    # 对每个网格区域计算平均灰度
    # 灰度低于阈值判为黑(0)，高于阈值判为白(1)
    
    # 这里省略具体实现（实际库中会逐bit解析）
    return None  # 解码失败
```

### 2.5 错误检测与纠正

AprilTag 的编码设计包含**汉明码**纠错机制。以 Tag36h11 为例：

- **总位数**：36 bits
- **有效数据位**：11 bits（可以编码 2^11 = 2048 个标签）
- **汉明距离**：11（纠错能力很强，可以纠正最多 5 bits 错误）

**汉明距离**是两个二进制串对应位置不同位的个数。例如：
```
标签A编码: 10110
标签B编码: 11100
汉明距离 = 3 （3个位置不同）
```

**纠错原理**：如果实际读取的编码与某个已知标签的汉明距离 ≤ 5，则可以纠正为该标签。

```python
def hamming_distance(bits1, bits2):
    """
    计算两个二进制串的汉明距离
    """
    return sum(b1 != b2 for b1, b2 in zip(bits1, bits2))

def correct_and_decode(bits_received, valid_tags, hamming_limit=5):
    """
    错误检测与纠正
    
    参数:
        bits_received: 接收到的编码位（36 bits）
        valid_tags: 所有合法标签的编码字典 {tag_id: bits}
        hamming_limit: 最大可纠正的错误位数
    
    返回:
        tag_id: 解码出的标签ID（如果可以纠正）
        或者 None（无法纠正，编码无效）
    """
    for tag_id, valid_bits in valid_tags.items():
        dist = hamming_distance(bits_received, valid_bits)
        if dist <= hamming_limit:
            return tag_id  # 成功纠正，返回标签ID
    
    return None  # 无法匹配任何已知标签

# 示例
valid_tags = {
    0: [0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0],  # Tag36h11 ID=0 的编码
    1: [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],  # Tag36h11 ID=1 的编码
}

# 假设接收到的编码有1位错误
received = [0,1,1,0,1,0,1,1,0,0,1,0,1,1,0,1]  # 有一位和ID=0不同
tag_id = correct_and_decode(received, valid_tags, hamming_limit=5)
print(f"解码结果：Tag ID = {tag_id}")  # 输出：Tag ID = 0
```

### 2.6 位姿估计（单目相机位姿解算）

这是 AprilTag 在机器人领域最重要的功能——通过识别图像中的一个已知尺寸的方块标记，计算相机到这个标记的 **6DoF 位姿**。

**数学原理**：

已知：
- AprilTag 的**实际物理尺寸**（你打印时设定的边长，如 0.166m）
- AprilTag 在**标签坐标系**中的四个角点位置（假设标签平面为 Z=0 的平面）
- 这些角点在**像素坐标系**中的位置（通过四边形检测获得）

求解：**相机相对于标签的旋转矩阵 R 和平移向量 t**

```
相机坐标系
    │
    │  相机拍摄 AprilTag
    │    ┌───────┐
    │    │ Tag   │  ← AprilTag 平面
    │    └───────┘
    │      ↑ 
    │   标签坐标系
    │
    │   

已知：
- 标签在标签坐标系中的角点位置（物理尺寸已知）
- 标签在图像中的像素位置（检测得到）

求解：
- 相机到标签的相对位姿 (R, t)
```

**OpenCV 的 `solvePnP` 函数**可以完成这个计算：

```python
import numpy as np
import cv2

def estimate_pose_from_tag(corners_pixel, tag_size_m, camera_matrix, dist_coeffs):
    """
    根据检测到的AprilTag角点估计相机位姿
    
    参数:
        corners_pixel: 四个角点的像素坐标 (4x2数组)
                       顺序：左上、右上、右下、左下
        tag_size_m: AprilTag 的物理边长（米）
        camera_matrix: 相机内参矩阵 (3x3数组)
        dist_coeffs: 相机畸变系数
    
    返回:
        rvec: 旋转向量 (3x1)
        tvec: 平移向量 (3x1)
    
    数学原理：
        使用 PnP（Perspective-n-Point）算法
        已知3D-2D对应点对，求解相机外参
    """
    # 标签坐标系中的角点位置
    # 假设标签平面为 Z=0
    # 左上角为原点，右下角为 (tag_size, tag_size, 0)
    half_size = tag_size_m / 2.0
    
    # 定义标签角点在标签坐标系下的3D坐标
    # 标签坐标系：Z轴垂直于标签平面，朝相机方向为正
    object_points = np.array([
        [-half_size, -half_size, 0],  # 左上
        [ half_size, -half_size, 0],  # 右上
        [ half_size,  half_size, 0],  # 右下
        [-half_size,  half_size, 0],   # 左下
    ], dtype=np.float64)
    
    # 图像坐标系中的角点坐标
    image_points = corners_pixel.astype(np.float64)
    
    # 使用 EPnP 算法求解位姿
    # 返回旋转向量 rvec 和平移向量 tvec
    success, rvec, tvec = cv2.solvePnP(
        object_points,
        image_points,
        camera_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE  # 也可以用 SOLVEPNP_EPNP
    )
    
    if success:
        # 将旋转向量转换为旋转矩阵
        R, _ = cv2.Rodrigues(rvec)
        
        print("位姿估计成功！")
        print(f"  标签尺寸: {tag_size_m*100:.1f} cm")
        print(f"  平移向量 t = [{tvec[0,0]:.4f}, {tvec[1,0]:.4f}, {tvec[2,0]:.4f}] 米")
        print(f"  旋转矩阵 R:\n{R}")
        
        # 计算相机到标签的距离
        distance = np.linalg.norm(tvec)
        print(f"  相机到标签距离: {distance:.4f} 米")
    else:
        print("位姿估计失败！")
    
    return rvec, tvec


def pose_estimation_workflow():
    """
    完整的位姿估计工作流示例
    """
    # 相机内参（需要事先标定）
    camera_matrix = np.array([
        [607.5, 0.0, 324.6],
        [0.0, 607.3, 239.5],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)
    
    # 畸变系数（假设无畸变）
    dist_coeffs = np.zeros((5, 1), dtype=np.float64)
    
    # AprilTag 物理尺寸（单位：米）
    tag_size = 0.166  # 16.6 cm
    
    # 假设检测到的标签角点像素坐标（示例）
    # 顺序：左上、右上、右下、左下
    corners_pixel = np.array([
        [200, 150],  # 左上
        [440, 160],  # 右上
        [430, 320],  # 右下
        [210, 310],  # 左下
    ], dtype=np.float64)
    
    # 估计位姿
    rvec, tvec = estimate_pose_from_tag(
        corners_pixel, tag_size, camera_matrix, dist_coeffs
    )
    
    return rvec, tvec

# 运行
rvec, tvec = pose_estimation_workflow()
```

**位姿估计结果的解读**：

- **tvec[0,0], tvec[1,0], tvec[2,0]**：标签在相机坐标系下的 X, Y, Z 位置（米）
  - tvec[2] > 0 表示标签在相机前方
  - tvec[2] 的值就是相机到标签的距离
- **R 矩阵**：标签坐标系到相机坐标系的旋转
  - 可以进一步分解为欧拉角（roll, pitch, yaw）

---

## 3. 传统二维码 QR Code

### 3.1 QR码结构

**QR Code**（Quick Response Code）是1994年由日本丰田子公司 Denso Wave 发明的二维条形码。与 AprilTag 不同，QR Code 的设计目标是**存储更多数据**，适合商品标签、票务、手机支付等场景。

**QR码的组成结构**：

```
┌─────────────────────────┐
│ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ ■ │  ← 功能图案（定位、格式信息）
│ ■ □ □ □ □ □ □ □ □ □ □ ■ │
│ ■ □ ■ ■ ■ ■ ■ □ ■ □ □ ■ │  ← 数据区 + 纠错码
│ ■ □ ■ □ □ □ ■ □ □ □ □ ■ │
│ ■ □ ■ ■ ■ □ ■ ■ □ ■ □ ■ │     版本信息、格式信息
│ ■ □ ■ □ □ □ □ □ □ □ □ ■ │     数据和纠错码字
│ ■ □ ■ ■ ■ ■ ■ ■ ■ □ □ ■ │
│ ■ □ □ □ □ □ □ □ □ □ ■ ■ │
│ ■ ■ ■ □ □ ■ □ ■ ■ □ □ ■ │  ← 功能图案
└─────────────────────────┘
```

**QR码的核心组成部分**：

| 组成部分 | 作用 | 数量 |
|---------|------|------|
| **定位图案**（Finder Pattern） | 左上、右上、左下三个大方块，用于快速定位QR码区域 | 3个 |
| **对齐图案**（Alignment Pattern） | 辅助定位，用于版本≥2的QR码，提高读取准确性 | 1-多个 |
| **时间图案**（Timing Pattern） | 黑白交替的条纹，用于确定数据模块的坐标 | 2条 |
| **格式信息**（Format Information） | 纠错等级、掩码类型 | 15 bits |
| **版本信息**（Version Information） | QR码的版本（尺寸），版本1=21x21，版本40=177x177 | 18 bits |
| **数据和纠错码字** | 实际存储的数据 + Reed-Solomon纠错码 | 可变 |

### 3.2 QR码的编码与纠错

**数据编码过程**：

```python
def qr_code_encoding_overview():
    """
    QR码编码流程概述（简化版）
    
    1. 数据分析：确定数据模式（数字、字母数字、字节、汉字）
    2. 数据编码：根据模式将数据转为二进制串
    3. 分块与纠错：添加Reed-Solomon纠错码
    4. 放置位图：将数据位放入QR码矩阵
    5. 掩码处理：应用掩码减少定位图案混淆
    6. 格式与版本信息：添加格式和版本信息
    """
    
    # 数据模式对应关系
    data_modes = {
        "数字模式":   {"容量(版本40)": "7089个字符", "字符集": "0-9"},
        "字母数字模式": {"容量(版本40)": "4296个字符", "字符集": "0-9, A-Z, 空格, $, %, *, +, -, ., /, :"},
        "字节模式":   {"容量(版本40)": "2953个字节", "字符集": "ISO 8859-1"},
        "汉字模式":   {"容量(版本40)": "1817个汉字", "字符集": "GB 2312 / UTF-8"},
    }
    
    # 纠错等级
    error_correction_levels = {
        "L": {"纠错能力": "~7%",  "数据比例": "低纠错高存储"},
        "M": {"纠错能力": "~15%", "数据比例": "平衡"},
        "Q": {"纠错能力": "~25%", "数据比例": "较高纠错"},
        "H": {"纠错能力": "~30%", "数据比例": "最高纠错"},
    }
    
    print("QR码数据模式：")
    for mode, info in data_modes.items():
        print(f"  {mode}: {info['容量(版本40)']} ({info['字符集'][:15]}...)")
    
    print("\n纠错等级：")
    for level, info in error_correction_levels.items():
        print(f"  等级{level}: 可恢复约 {info['纠错能力']} 的损坏数据")

qr_code_encoding_overview()
```

**Reed-Solomon 纠错码**：QR码使用 Reed-Solomon 纠错算法，可以在数据部分损坏时仍然正确解码。纠错等级越高，存储有效数据越少，但抗损坏能力越强。

### 3.3 QR码检测流程

QR码的检测与 AprilTag 类似但有所不同：

```
输入图像
    │
    ▼
┌─────────────────────┐
│ 1. 灰度化 + 二值化    │  RGB → 灰度 → 二值图（黑白）
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. 定位图案检测       │  找三个"回"字形定位图案
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. 采样与解码         │  确定像素网格、采样数据位
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 4. 纠错 + 数据输出    │  Reed-Solomon纠错，输出原始数据
└─────────────────────┘
```

**定位图案的检测**：

定位图案（Finder Pattern）由三个相同的大方块组成，每个方块结构为：
- 外层：7×7 的黑色正方形
- 中间层：5×5 的白色正方形  
- 中心：3×3 的黑色正方形

这个"回"字形结构在自然界中几乎不会出现，因此可以作为可靠的定位标志。

```python
def find_finder_patterns(binary_image):
    """
    在二值图像中寻找QR码的三个定位图案
    
    定位图案特征：
    1. 三个正方形，结构为 [黑-白-黑-白-黑] 的同心方块
    2. 面积比例大致为 1:1:1:1:1:1:1（中心:第一环:第二环）
    3. 三个图案在图像中近似形成等腰直角三角形
    """
    # 使用 OpenCV 的 QR 码检测器（内置）
    qr_detector = cv2.QRCodeDetector()
    
    # 检测并解码
    data, vertices, _ = qr_detector.detectAndDecode(binary_image)
    
    if data:
        print(f"QR码检测成功！")
        print(f"  解码数据: {data}")
        print(f"  四个角点: {vertices}")
    else:
        print("未检测到QR码")
    
    return data, vertices
```

---

## 4. AprilTag vs QR Code 对比

| 对比维度 | AprilTag | QR Code |
|---------|----------|---------|
| **设计目标** | 机器人位姿估计、精确定位 | 数据存储、信息传递 |
| **数据容量** | 很少（5-11 bits ID） | 很大（最高 thousands of bytes） |
| **位姿估计** | ✅ 支持，精度高 | ❌ 不支持（只能知道内容，不知道位置） |
| **远距离识别** | ✅ 好（最小tag可达毫米级但远距可读） | ⚠️ 一般（像素少时难以解码） |
| **部分遮挡容忍** | ✅ 好（边缘检测+纠错） | ⚠️ 中等（纠错能力有限） |
| **检测速度** | 快（边缘+四边形） | 中等（需要多种图案联合定位） |
| **标准化** | 有标准家族，标签ID是数字 | 有标准格式，数据可以是任意字符串 |
| **颜色支持** | 通常黑白（也可彩色） | 彩色、有logo等变种 |
| **典型应用** | 机器人定位、相机标定、无人机着陆 | 支付、票务、商品标签、包装 |
| **实现难度** | 中等（需要PnP位姿估计） | 简单（OpenCV内置） |

**何时选 AprilTag？**
- 需要知道**精确位置和朝向**（6DoF位姿）
- 标签尺寸**精确已知**
- 在**机器人、无人机**等领域

**何时选 QR Code？**
- 需要传递**数据或链接**
- 标签会被**手机扫描**
- **工业应用**中需要承载更多信息

---

## 5. 生成 AprilTag 与 QR Code

### 5.1 生成 AprilTag

生成 AprilTag 图像非常简单，可以使用专门的库 `apriltag` 或在线工具。

**方法一：使用 apriltag Python 库生成**

```bash
# 安装 apriltag 库
pip install apriltag
```

```python
import apriltag
import cv2
import numpy as np

def generate_apriltag(tag_id=0, family="Tag36h11", 
                      pixels_per_module=30, margin_pixels=2):
    """
    生成 AprilTag 图像
    
    参数:
        tag_id: 标签ID（根据家族不同，可选范围不同）
        family: 标签家族（Tag36h11 最常用）
        pixels_per_module: 每个编码模块占用的像素数
        margin_pixels: 白色边缘的像素数
    
    推荐尺寸（不同应用场景）：
        - 室内机器人定位: 每个模块 30-50 像素（打印 A4 纸上约 5-8cm 大小）
        - 远距离: 每个模块 50-100 像素
        - 近距离精密操作: 每个模块 10-20 像素
    """
    # 创建检测器以获取标签信息
    options = apriltag.DetectorOptions(families=family)
    detector = apriltag.Detector(options)
    
    # 生成标签图像
    # apriltag 库会生成标准化的高质量标签图像
    tag_size_px = pixels_per_module * 8  # 36h11 的编码区域是 8x8 模块
    total_size = tag_size_px + 2 * margin_pixels
    
    # 创建白色背景
    tag_image = np.ones((total_size, total_size), dtype=np.uint8) * 255
    
    print(f"生成 AprilTag: {family}, ID={tag_id}")
    print(f"  图像尺寸: {total_size}x{total_size} 像素")
    print(f"  每个模块: {pixels_per_module} 像素")
    print(f"  标签尺寸: {tag_size_px}x{tag_size_px} 像素")
    
    # 实际使用时，使用 apriltag 库提供的 toImage 方法
    # tag = apriltag.TagFamily(family).render(tag_id=tag_id, 
    #                                          pixels_per_module=pixels_per_module,
    #                                          margin=margin_pixels)
    # tag_image = np.array(tag)
    
    return tag_image


def generate_apriltag_online_tool():
    """
    使用在线工具生成 AprilTag  PDF（推荐方式）
    
    步骤：
    1. 访问 AprilTag 生成网站（如 https://ivanqyu.github.io/apriltag/）
    2. 选择家族（如 Tag36h11）
    3. 设置标签 ID 和尺寸
    4. 下载 PDF 并打印
    
    打印后注意事项：
    - 确保打印设置为 100% 比例（不要缩放）
    - 使用哑光相纸效果最好
    - 标签尺寸精确已知是位姿估计的前提！
    """
    print("推荐在线工具：")
    print("  1. https://ivanqyu.github.io/apriltag/")
    print("  2. http://opticalreservoir.github.io/apriltag/")

generate_apriltag_online_tool()


### 5.2 生成 QR Code

生成 QR Code 非常简单，使用 OpenCV 内置的 QR 码生成器即可：

```python
import cv2
import numpy as np

def generate_qr_code(data="https://robotics.example.com", 
                      version=0,纠错等级=cv2.QRCODE_FIND_BARCODE_AND_TYPE):
    """
    生成 QR Code 图像
    
    参数:
        data: 要编码的数据（URL、文本、数字等）
        version: QR码版本（0=自动，1-40）
        纠错等级: QRCODE_FIND_ANY_MAGCODE (自动检测)
    
    QR码版本与尺寸对应：
        版本 1: 21x21 模块
        版本 2: 25x25 模块
        ...
        版本 40: 177x177 模块
    
    纠错等级（由高到低）：
        H: 最高纠错（约30%）
        Q: 高纠错（约25%）
        M: 中等纠错（约15%）
        L: 低纠错（约7%）
    """
    # 创建 QR 码检测器（也用于生成）
    qr_detector = cv2.QRCodeDetector()
    
    # 使用 detector 生成 QR 码
    # 返回 (success, image, version, ecc_level)
    success, qrc_image, version_out, ecc = qr_detector.encode(data)
    
    if success:
        # qrc_image 是归一化后的图像（0-1 范围）
        # 转为 0-255 的 uint8 图像
        qrc_image = (qrc_image * 255).astype(np.uint8)
        
        print(f"QR码生成成功！")
        print(f"  编码数据: {data}")
        print(f"  版本: {version_out}")
        print(f"  纠错等级: {ecc}")
        print(f"  图像尺寸: {qrc_image.shape}")
    else:
        print("QR码生成失败！")
        qrc_image = None
    
    return qrc_image


def generate_qr_code_advanced(data,纠错等级_str="M"):
    """
    使用 qrcode 库生成更灵活的 QR 码
    
    pip install qrcode[pil]
    """
    try:
        import qrcode
        
        # 创建 QR 码对象
        qr = qrcode.QRCode(
            version=1,  # 版本（1-40，0=自动）
            error_correction=qrcode.constants.ERROR_CORRECT_M,  # 纠错等级
            box_size=10,  # 每个模块的像素数
            border=4,     # 边框厚度（模块数）
        )
        
        # 添加数据
        qr.add_data(data)
        qr.make(fit=True)
        
        # 生成图像
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为 OpenCV 格式
        img_array = np.array(img)
        qrc_image = (img_array * 255).astype(np.uint8) if img_array.dtype == bool else img_array
        
        print(f"QR码生成成功！数据长度: {len(data)} 字符")
        return qrc_image
        
    except ImportError:
        print("qrcode 库未安装，使用 OpenCV 内置方法")
        return generate_qr_code(data)


def qr_generation_demo():
    """
    QR码生成演示
    """
    # 生成一个简单的 URL QR码
    url = "https://robotics.example.com"
    qrc = generate_qr_code(url)
    
    # 生成一个包含文本的 QR码
    text_qrc = generate_qr_code("Hello Robot!", version=3)
    
    print("\n建议：")
    print("  - 打印 QR 码时使用高对比度（纯黑/纯白）")
    print("  - 确保纠错等级足够应对可能的污损")
    print("  - 版本越高存储越多，但识别难度也越大")

qr_generation_demo()
```

---

## 6. OpenCV 实践代码

### 6.1 AprilTag 检测与位姿估计

以下是完整的 AprilTag 检测与位姿估计代码，使用 `apriltag` 库：

```python
import numpy as np
import cv2
import apriltag


def detect_apriltag_and_estimate_pose(image, camera_matrix, dist_coeffs, 
                                      tag_size=0.166, family="Tag36h11"):
    """
    检测图像中的 AprilTag 并估计位姿
    
    参数:
        image: 输入图像（BGR格式）
        camera_matrix: 相机内参矩阵 (3x3)
        dist_coeffs: 相机畸变系数
        tag_size: AprilTag 物理尺寸（米）
        family: 标签家族
    
    返回:
        detections: 检测结果列表
    """
    # 转换为灰度图
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # 创建 AprilTag 检测器
    options = apriltag.DetectorOptions(families=family)
    detector = apriltag.Detector(options)
    
    # 检测 AprilTag
    detections = detector.detect(gray)
    
    if not detections:
        print("未检测到 AprilTag")
        return []
    
    print(f"检测到 {len(detections)} 个 AprilTag:")
    
    results = []
    
    for i, detection in enumerate(detections):
        tag_id = detection.tag_id
        center = detection.center  # 标签中心像素坐标
        corners = detection.corners  # 四个角点像素坐标
        
        print(f"\n  标签 {i+1}: {family} ID={tag_id}")
        print(f"    中心: ({center[0]:.1f}, {center[1]:.1f}) 像素")
        print(f"    角点: {corners}")
        
        # ========== 位姿估计 ==========
        # 标签角点在标签坐标系下的3D坐标（假设 Z=0）
        half_size = tag_size / 2.0
        object_points = np.array([
            [-half_size, -half_size, 0],  # 左上
            [ half_size, -half_size, 0],  # 右上
            [ half_size,  half_size, 0],  # 右下
            [-half_size,  half_size, 0],  # 左下
        ], dtype=np.float64)
        
        # 图像中的角点坐标
        image_points = np.array(corners, dtype=np.float64)
        
        # 使用 PnP 算法估计位姿
        success, rvec, tvec = cv2.solvePnP(
            object_points, image_points,
            camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        if success:
            # 计算距离
            distance = np.linalg.norm(tvec)
            
            # 旋转向量转旋转矩阵
            R, _ = cv2.Rodrigues(rvec)
            
            print(f"    位姿估计成功:")
            print(f"      平移向量: [{tvec[0,0]:.4f}, {tvec[1,0]:.4f}, {tvec[2,0]:.4f}] 米")
            print(f"      相机到标签距离: {distance:.4f} 米")
            
            results.append({
                "tag_id": tag_id,
                "center": center,
                "corners": corners,
                "rvec": rvec,
                "tvec": tvec,
                "distance": distance,
                "R": R
            })
        else:
            print(f"    位姿估计失败")
    
    return results


def apriltag_detection_demo(image_path=None):
    """
    AprilTag 检测演示主函数
    """
    # 相机内参（需要根据实际相机标定结果修改）
    camera_matrix = np.array([
        [607.5, 0.0, 324.6],
        [0.0, 607.3, 239.5],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)
    
    # 畸变系数（假设无畸变）
    dist_coeffs = np.zeros((5, 1), dtype=np.float64)
    
    # AprilTag 物理尺寸（米）
    tag_size = 0.166  # 16.6 cm
    
    if image_path:
        # 从文件读取图像
        image = cv2.imread(image_path)
        if image is None:
            print(f"无法读取图像: {image_path}")
            return
    else:
        # 创建一个模拟的 AprilTag 图像用于演示
        print("创建模拟图像用于演示...")
        # 实际使用时替换为真实相机拍摄的图像
        image = np.ones((480, 640, 3), dtype=np.uint8) * 200
    
    # 检测并估计位姿
    results = detect_apriltag_and_estimate_pose(
        image, camera_matrix, dist_coeffs, tag_size
    )
    
    # 在图像上绘制检测结果
    for result in results:
        corners = result["corners"].astype(np.int32)
        
        # 绘制四边形边框
        cv2.polylines(image, [corners], True, (0, 255, 0), 2)
        
        # 绘制中心点
        center = result["center"].astype(np.int32)
        cv2.circle(image, tuple(center), 5, (0, 0, 255), -1)
        
        # 标注标签 ID
        tag_id = result["tag_id"]
        distance = result["distance"]
        label = f"ID={tag_id}, {distance:.2f}m"
        cv2.putText(image, label, 
                    (int(center[0]) + 10, int(center[1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    print(f"\n共检测到 {len(results)} 个 AprilTag")
    return image, results

# 运行演示
image, results = apriltag_detection_demo()
```

### 6.2 QR Code 识别

使用 OpenCV 内置的 QR 码检测器：

```python
import cv2
import numpy as np


def detect_qr_code(image):
    """
    检测并解码 QR 码
    
    参数:
        image: 输入图像
    
    返回:
        data: 解码出的数据（字符串）
        vertices: QR码的四个角点
    """
    # 创建 QR 码检测器
    qr_detector = cv2.QRCodeDetector()
    
    # 检测并解码
    # detectAndDecode 返回：(data, vertices, straight_qrcode)
    data, vertices, straight_qr = qr_detector.detectAndDecode(image)
    
    if data:
        print(f"QR码检测成功！")
        print(f"  解码数据: {data}")
        print(f"  角点坐标:\n{vertices}")
        return data, vertices
    else:
        print("未检测到 QR 码")
        return None, None


def detect_qr_code_with_rectification(image):
    """
    检测 QR 码并提取规范化后的 QR 码图像
    """
    qr_detector = cv2.QRCodeDetector()
    
    # detectAndDecodeMulti 可以处理多个 QR 码
    data, vertices, straight_qr = qr_detector.detectAndDecode(image)
    
    if data:
        # straight_qrcode 是校正后的 QR 码图像
        print(f"检测到 QR 码，原始数据: {data}")
        print(f"校正后 QR 码尺寸: {straight_qr.shape if straight_qr is not None else 'N/A'}")
    
    return data, vertices, straight_qr


def qr_detection_demo(image_path=None):
    """
    QR码检测演示
    """
    if image_path:
        image = cv2.imread(image_path)
        if image is None:
            print(f"无法读取图像: {image_path}")
            return
    else:
        # 创建包含 QR 码的模拟图像
        # 实际使用时替换为真实图像
        print("提示：请提供包含 QR 码的图像进行测试")
        
        # 尝试从摄像头读取
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, image = cap.read()
            cap.release()
            if ret:
                print("从摄像头获取图像")
            else:
                print("无法从摄像头读取")
                return
        else:
            return
    
    # 检测 QR 码
    data, vertices, _ = detect_qr_code_with_rectification(image)
    
    if vertices is not None:
        # 在图像上绘制 QR 码边框
        points = vertices.astype(np.int32)
        cv2.polylines(image, [points], True, (0, 255, 0), 3)
        
        # 在左上角显示解码数据
        cv2.putText(image, f"Data: {data}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return image, data


def qr_detection_video():
    """
    实时 QR 码检测（从摄像头）
    """
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    print("按 'q' 退出实时 QR 码检测")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 检测 QR 码
        data, vertices, _ = detect_qr_code_with_rectification(frame)
        
        if vertices is not None:
            # 绘制边框
            points = vertices.astype(np.int32)
            cv2.polylines(frame, [points], True, (0, 255, 0), 2)
            
            # 显示数据
            if data:
                cv2.putText(frame, f"{data[:50]}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("QR Code Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

# 运行演示
qr_detection_demo()
```

### 6.3 使用 AprilTag 进行相机标定

AprilTag 可以作为相机标定的靶标，比传统棋盘格更方便：

```python
import numpy as np
import cv2
import apriltag
import glob


def calibrate_camera_with_apriltag(image_paths, tag_size=0.166, 
                                    camera_matrix_init=None, family="Tag36h11"):
    """
    使用 AprilTag 进行相机标定
    
    参数:
        image_paths: 包含 AprilTag 的图像路径列表
        tag_size: AprilTag 物理尺寸（米）
        camera_matrix_init: 初始内参矩阵（可选）
        family: 标签家族
    
    返回:
        mtx: 相机内参矩阵
        dist: 畸变系数
        rvecs: 每张图像的旋转向量
        tvecs: 每张图像的平移向量
    """
    # AprilTag 的物理角点（已知）
    half_size = tag_size / 2.0
    objp = np.array([
        [-half_size, -half_size, 0.0],
        [ half_size, -half_size, 0.0],
        [ half_size,  half_size, 0.0],
        [-half_size,  half_size, 0.0],
    ], dtype=np.float64)
    
    # 存储所有有效图像的3D和2D点
    objpoints = []  # 3D点（标签角点）
    imgpoints = []  # 2D点（图像角点）
    
    # 创建检测器
    options = apriltag.DetectorOptions(families=family)
    detector = apriltag.Detector(options)
    
    valid_count = 0
    
    for img_path in image_paths:
        img = cv2.imread(img_path)
        if img is None:
            continue
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检测 AprilTag
        detections = detector.detect(gray)
        
        for det in detections:
            # 获取四个角点
            corners = det.corners.astype(np.float64)
            
            objpoints.append(objp)
            imgpoints.append(corners)
            valid_count += 1
            
            print(f"图像 {img_path}: 检测到 Tag ID={det.tag_id}")
    
    if valid_count < 10:
        print(f"警告：仅检测到 {valid_count} 个有效标签，建议至少 10 张图像")
    
    print(f"\n总共 {valid_count} 个有效检测点，开始标定...")
    
    # 图像尺寸
    img_shape = cv2.imread(image_paths[0]).shape
    h, w = img_shape[:2]
    
    # 标定
    if camera_matrix_init is not None:
        # 使用已知内参
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, (w, h), 
            cameraMatrix=camera_matrix_init,
            distCoeffs=None
        )
    else:
        # 完整标定
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, (w, h), None, None
        )
    
    print(f"\n标定结果:")
    print(f"  重投影误差: {ret:.4f} 像素")
    print(f"  内参矩阵 K:\n{mtx}")
    print(f"  畸变系数: {dist.ravel()}")
    
    # 计算焦距和光心
    fx, fy = mtx[0, 0], mtx[1, 1]
    cx, cy = mtx[0, 2], mtx[1, 2]
    print(f"  焦距: fx={fx:.2f}, fy={fy:.2f}")
    print(f"  光心: cx={cx:.2f}, cy={cy:.2f}")
    
    return mtx, dist, rvecs, tvecs


def calibrate_from_folder(image_folder, tag_size=0.166):
    """
    从文件夹中的所有图像进行标定
    """
    # 获取所有图像文件
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(f"{image_folder}/{ext}"))
    
    if not image_paths:
        print(f"在 {image_folder} 中未找到图像文件")
        return None, None
    
    print(f"找到 {len(image_paths)} 张图像")
    
    return calibrate_camera_with_apriltag(image_paths, tag_size)


def save_calibration(mtx, dist, filename="camera_calibration.yaml"):
    """
    保存标定结果到文件
    """
    import yaml
    
    calibration_data = {
        'camera_matrix': mtx.tolist(),
        'dist_coeffs': dist.tolist()
    }
    
    with open(filename, 'w') as f:
        yaml.dump(calibration_data, f)
    
    print(f"标定结果已保存到 {filename}")


def load_calibration(filename="camera_calibration.yaml"):
    """
    从文件加载标定结果
    """
    import yaml
    
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)
    
    mtx = np.array(data['camera_matrix'])
    dist = np.array(data['dist_coeffs'])
    
    print(f"从 {filename} 加载标定结果")
    return mtx, dist

# 使用示例
# mtx, dist, rvecs, tvecs = calibrate_from_folder("./apriltag_images", tag_size=0.166)
# save_calibration(mtx, dist)
```

---

## 7. ROS2 AprilTag 节点

### 7.1 安装 apriltag_ros

ROS2 中使用 AprilTag 的标准包是 `apriltag_ros`：

```bash
# 安装 apriltag_ros（假设已配置 ROS2 环境）
sudo apt update
sudo apt install ros-<distro>-apriltag-ros

# 或者从源码编译
cd ~/ros2_ws/src
git clone https://github.com/AprilRobotics/apriltag_ros.git
git clone https://github.com/AprilRobotics/apriltag.git  # 核心库
cd ~/ros2_ws
colcon build
source install/setup.bash
```

### 7.2 apriltag_ros 配置与启动

**配置文件示例（config.yaml）**：

```yaml
# AprilTag 检测器参数
apriltag:
  sensor_width: 640        # 图像宽度
  sensor_height: 480       # 图像高度
  focal_length_x: 607.5    # x方向焦距（像素）
  focal_length_y: 607.3    # y方向焦距（像素）
  cx: 324.6                # 光心x坐标
  cy: 239.5                # 光心y坐标

# 要检测的标签家族
tag_family:
  - Tag36h11

# 标签尺寸设置（单位：米）
tag_graph:
  tag36h11_0: {size: 0.166,ros_frame: 'tag36h11_0'}

# 检测器参数
detector:
  max_hamming_dist: 5      # 最大汉明距离纠错
  refine_edges: 1.0        # 边缘精细化参数
```

**launch 文件示例（apriltag.launch.py）**：

```python
# apriltag.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # 声明参数
    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic',
        default_value='/image_raw',
        description='相机图像话题'
    )
    
    # AprilTag 检测节点
    apriltag_node = Node(
        package='apriltag_ros',
        executable='apriltag_node',
        name='apriltag_detector',
        output='screen',
        parameters=[{
            'image_topic': LaunchConfiguration('camera_topic'),
            # 相机内参（需要根据实际相机标定结果修改）
            'camera_params': [
                607.5,   # fx
                607.3,   # fy
                324.6,   # cx
                239.5    # cy
            ],
            # 要检测的标签家族
            'tag_family': 'tag36h11',
            # 标签尺寸（米）
            'tag_size': 0.166,
            # 最大汉明距离纠错
            'max_hamming_dist': 5,
            # 发布策略
            'publish_tf': True,
            'publish_tag_detections_image': True,
        }],
        remappings=[
            ('/image_rect', '/image_raw'),
        ]
    )
    
    return LaunchDescription([
        camera_topic_arg,
        apriltag_node,
    ])
```

**启动命令**：

```bash
# 方式1：使用默认参数
ros2 launch apriltag_ros apriltag.launch.py

# 方式2：指定相机话题
ros2 launch apriltag_ros apriltag.launch.py camera_topic:=/camera/image_raw

# 方式3：使用自定义配置文件
ros2 run apriltag_ros apriltag_node --params-file config.yaml
```

### 7.3 订阅 AprilTag 检测结果

AprilTag 检测节点会发布以下话题：

| 话题名 | 类型 | 说明 |
|-------|------|------|
| `/apriltag_detections` | AprilTagDetectionArray | 所有检测到的标签列表 |
| `/apriltag_pose` | geometry_msgs/PoseArray | 标签的位姿（需配置） |
| `/tag_detections_image` | sensor_msgs/Image | 叠加了检测结果的图像 |
| `/tf` | tf2_msgs/TFMessage | 标签的 TF 变换 |

**订阅 Python 示例**：

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseArray, Pose
from apriltag_msgs.msg import AprilTagDetectionArray


class AprilTagSubscriber(Node):
    """
    订阅 AprilTag 检测结果的节点
    """
    
    def __init__(self):
        super().__init__('apriltag_subscriber')
        
        # 订阅 AprilTag 检测结果
        self.subscription = self.create_subscription(
            AprilTagDetectionArray,
            '/apriltag_detections',
            self.detection_callback,
            10
        )
        
        # 或者订阅位姿数组
        self.pose_subscription = self.create_subscription(
            PoseArray,
            '/apriltag_pose',
            self.pose_callback,
            10
        )
        
        self.get_logger().info('AprilTag 订阅节点已启动')
    
    def detection_callback(self, msg: AprilTagDetectionArray):
        """
        处理 AprilTag 检测结果
        """
        if not msg.detections:
            return
        
        for detection in msg.detections:
            tag_id = detection.id[0]  # 标签 ID
            center = detection.centre
            pose = detection.pose
            
            print(f"\n检测到 AprilTag:")
            print(f"  ID: {tag_id}")
            print(f"  中心位置: ({centre.x:.2f}, {centre.y:.2f}) 像素")
            print(f"  位置 (相机坐标系): ({pose.position.x:.4f}, {pose.position.y:.4f}, {pose.position.z:.4f}) 米")
            print(f"  朝向 (相机坐标系): ({pose.orientation.x:.4f}, {pose.orientation.y:.4f}, {pose.orientation.z:.4f}, {pose.orientation.w:.4f})")
    
    def pose_callback(self, msg: PoseArray):
        """
        处理位姿数组
        """
        for i, pose in enumerate(msg.poses):
            print(f"\n标签 {i} 的位姿:")
            print(f"  位置: ({pose.position.x:.4f}, {pose.position.y:.4f}, {pose.position.z:.4f})")


def main(args=None):
    rclpy.init(args=args)
    node = AprilTagSubscriber()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 7.4 机器人定位应用示例

以下是一个完整的示例：机器人通过 AprilTag 实现精确定位：

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, TransformStamped
from apriltag_msgs.msg import AprilTagDetectionArray
import numpy as np
import math


class RobotAprilTagNavigator(Node):
    """
    基于 AprilTag 的机器人导航节点
    
    功能：
    1. 检测地面上的 AprilTag
    2. 计算机器人到标签的相对位姿
    3. 根据已知标签位置计算机器人在地图中的绝对位置
    """
    
    def __init__(self):
        super().__init__('robot_apriltag_navigator')
        
        # 已知标签在地图中的位置（需要提前测量）
        # 格式: {tag_id: (x, y, yaw)}
        self.tag_map_positions = {
            0: (0.0, 0.0, 0.0),      # 标签0在地图原点
            1: (1.0, 0.0, 0.0),     # 标签1在x=1m处
            2: (2.0, 1.0, math.pi/2),  # 标签2在(2,1)，朝向90度
        }
        
        # 订阅 AprilTag 检测结果
        self.subscription = self.create_subscription(
            AprilTagDetectionArray,
            '/apriltag_detections',
            self.apriltag_callback,
            10
        )
        
        # 发布机器人位置
        self.robot_pose_pub = self.create_publisher(
            Pose,
            '/robot_estimated_pose',
            10
        )
        
        self.get_logger().info('AprilTag 导航节点已启动')
        self.get_logger().info(f'已知标签位置: {self.tag_map_positions}')
    
    def apriltag_callback(self, msg: AprilTagDetectionArray):
        """
        处理 AprilTag 检测结果
        """
        if not msg.detections:
            return
        
        for detection in msg.detections:
            tag_id = detection.id[0]
            
            if tag_id not in self.tag_map_positions:
                self.get_logger().debug(f'未知的标签 ID: {tag_id}')
                continue
            
            # 获取标签在相机坐标系下的位姿
            tag_pose = detection.pose
            camera_x = tag_pose.position.x
            camera_y = tag_pose.position.y
            camera_z = tag_pose.position.z  # 相机到标签的距离
            
            # 从四元数获取相机到标签的旋转
            camera_qx = tag_pose.orientation.x
            camera_qy = tag_pose.orientation.y
            camera_qz = tag_pose.orientation.z
            camera_qw = tag_pose.orientation.w
            
            # 计算相机坐标系的航向角
            camera_yaw = math.atan2(
                2.0 * (camera_qw * camera_qz + camera_qx * camera_qy),
                1.0 - 2.0 * (camera_qy**2 + camera_qz**2)
            )
            
            # 获取标签在地图中的已知位置
            map_x, map_y, map_yaw = self.tag_map_positions[tag_id]
            
            # 坐标变换：相机坐标系 -> 机器人坐标系 -> 地图坐标系
            # 这里假设相机朝下安装，垂直于地面
            # 机器人在地图中的位置
            robot_x = map_x - camera_x * math.cos(map_yaw + camera_yaw)
            robot_y = map_y - camera_x * math.sin(map_yaw + camera_yaw)
            robot_yaw = map_yaw + camera_yaw
            
            distance = math.sqrt(camera_x**2 + camera_y**2 + camera_z**2)
            
            self.get_logger().info(
                f'Tag ID={tag_id}: '
                f'机器人位置=({robot_x:.3f}, {robot_y:.3f}, {math.degrees(robot_yaw):.1f}°), '
                f'距离={distance:.3f}m'
            )
            
            # 发布机器人位置
            robot_pose = Pose()
            robot_pose.position.x = robot_x
            robot_pose.position.y = robot_y
            robot_pose.position.z = 0.0
            # 设置朝向（四元数）
            robot_pose.orientation.z = math.sin(robot_yaw / 2)
            robot_pose.orientation.w = math.cos(robot_yaw / 2)
            
            self.robot_pose_pub.publish(robot_pose)


def main(args=None):
    rclpy.init(args=args)
    navigator = RobotAprilTagNavigator()
    
    try:
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 本章小结

本章我们系统性地学习了 AprilTag 和 QR Code 两种视觉标记技术。

在 AprilTag 简介部分，我们了解到 AprilTag 是一种专为机器人位姿估计设计的人工视觉标记，与 QR Code、ArUco 等其他标记相比，它最大的优势是支持精确的 6DoF 位姿估计。AprilTag 有多个家族（Tag16h5、Tag25h9、Tag36h10、Tag36h11），广泛应用于机器人定位、相机标定、无人机着陆、物体位姿估计和 AR 交互等领域。

在 AprilTag 检测原理部分，我们深入了解了从图像输入到位姿输出的完整检测流程：灰度化→边缘检测→四边形检测→编码解析→错误检测纠正→位姿估计（PnP算法）。其中，四边形检测是核心步骤，通过寻找凸四边形快速筛选候选区域；位姿估计则利用 OpenCV 的 `solvePnP` 函数，通过已知的标签物理尺寸和图像中的角点像素坐标，计算相机到标签的精确相对位姿。

在 QR Code 部分，我们了解了 QR 码的结构（定位图案、功能图案、数据区）、编码方式（多种数据模式+Reed-Solomon纠错）和检测流程。QR Code 与 AprilTag 的设计目标不同——QR Code 追求数据容量，AprilTag 追求位姿精度。

在实践代码部分，我们分别用 OpenCV 和 apriltag 库实现了 AprilTag 检测、QR Code 识别、相机标定等功能的代码示例。

在 ROS2 集成部分，我们介绍了 `apriltag_ros` 包的安装、配置和使用方法，包括如何订阅检测结果话题、如何构建基于 AprilTag 的机器人导航节点。

---

## 练习题

**1. 选择题（单选）**

**题目1.1：** AprilTag 相比 QR Code 最核心的优势是什么？

A. 数据存储容量更大  
B. 支持彩色打印  
C. 可以精确估计 6DoF 位姿  
D. 检测速度更快

**题目1.2：** 在 AprilTag 位姿估计中，已知标签物理尺寸和什么信息，可以计算出相机到标签的位姿？

A. 标签的颜色信息  
B. 标签在图像中的角点像素坐标  
C. 标签的 ID 编号  
D. 标签的打印时间

**题目1.3：** Tag36h11 中的 "h11" 表示什么含义？

A. 标签高度为 11 毫米  
B. 汉明距离为 11（纠错能力为 11 bits）  
C. 标签尺寸为 36×36，汉明距离为 11  
D. 包含 11 种不同的标签

**2. 填空题**

**题目2.1：** AprilTag 的检测流程中，首先需要对输入图像进行 ______ 化处理，将彩色图转为灰度图。

**题目2.2：** 在相机标定中，AprilTag 相比传统棋盘格的优势是可以检测到 ______ （填"任意角度"或"只有正面"）的标签。

**题目2.3：** QR 码的三个定位图案（Finder Pattern）的结构是 ______ （用一句话描述，如"同心圆"等）。

**3. 简答题**

**题目3.1：** 请对比 AprilTag 和 QR Code 在机器人应用中的适用场景，各举两个例子并说明理由。

**题目3.2：** 假设一个 AprilTag（Tag36h11，ID=5）贴在墙上，物理尺寸为 16.6cm。相机内参矩阵 $K = [[607.5, 0, 324.6], [0, 607.3, 239.5], [0, 0, 1]]$，畸变系数为 0。检测到的标签角点像素坐标为：
- 左上: (200, 150)
- 右上: (440, 150)
- 右下: (440, 340)
- 左下: (200, 340)

请说明位姿估计的输入和输出，并指出相机到标签的大致距离（提示：标签在图像中基本正对相机，无明显透视变形）。

---

## 答案

### 1. 选择题答案

**题目1.1：** **C. 可以精确估计 6DoF 位姿**

解析：AprilTag 相比 QR Code 的核心区别在于设计目标。AprilTag 的设计目标就是**机器人位姿估计**，通过已知的标签物理尺寸和检测到的角点像素坐标，可以利用 PnP 算法精确计算出相机到标签的 6DoF 位姿（位置 XYZ + 朝向 Roll/Pitch/Yaw）。QR Code 只能解码出存储的数据，无法提供位置信息。

**题目1.2：** **B. 标签在图像中的角点像素坐标**

解析：AprilTag 位姿估计的核心是 PnP（Perspective-n-P
解析：**标签在图像中的角点像素坐标**。PnP 算法需要已知 3D-2D 对应点对来求解相机外参。对于 AprilTag，我们已知标签角点在标签坐标系下的 3D 坐标（基于物理尺寸），而图像中的像素坐标通过检测获得。这两者对应即可求解位姿。颜色信息和标签 ID 与位姿估计无直接关系。

**题目1.3：** **C. 标签尺寸为 36×36，汉明距离为 11**

解析：AprilTag 家族的命名规则为 `Tag<边长>h<汉明距离>`。Tag36h11 表示编码区域为 36×36 个模块，汉明距离为 11（纠错能力最强，可纠正最多 5 位错误）。注意标签的实际物理尺寸是用户打印时自行设定的，与编号无关。

### 2. 填空题答案

**题目2.1：** **灰度**

解析：AprilTag 是黑白图案，检测时首先将彩色 RGB 图像转换为灰度图像，简化后续的边缘检测和编码解析过程。

**题目2.2：** **任意角度**

解析：AprilTag 的黑色边框和内部编码区域即使在斜视角下也能被检测到（只要没有完全遮挡），而传统棋盘格在斜视角较大时角点检测精度会严重下降。因此 AprilTag 可以从更广的角度范围进行标定。

**题目2.3：** **三个"回"字形同心方块（黑白交替的5层方块）**

解析：每个定位图案由三个同心正方形组成，从外到内是：黑色方块 → 白色方块 → 黑色方块 → 白色方块 → 黑色方块（中心）。这种独特的"回"字形结构在自然界中罕见，可靠性高。

### 3. 简答题答案

**题目3.1：**

**AprilTag 的适用场景：**

1. **机器人室内定位**：在地面或墙上贴上多个 AprilTag，机器人通过相机检测标签即可精确知道自己的位置。理由：AprilTag 支持位姿估计，可以同时确定机器人的位置和朝向，且检测速度快、鲁棒性好。

2. **相机标定**：使用 AprilTag 作为标定靶标，可以从多个角度拍摄进行标定。理由：AprilTag 可在任意角度被检测到，比棋盘格只能正面拍摄效率更高。

3. **无人机着陆引导**：在着陆点放置 AprilTag，无人机通过视觉精确对准。理由：AprilTag 的位姿估计可以让无人机知道相对于着陆点的精确位置。

**QR Code 的适用场景：**

1. **仓储物流分拣**：在货物上贴 QR 码，扫码枪或相机读取货物信息。理由：QR 码可以存储大量数据（如商品编号、数量、目的地），且手机和工业相机都能识别。

2. **产品追溯与信息展示**：消费者扫描产品包装上的 QR 码获取详细信息（生产日期、配料、官网链接等）。理由：QR 码存储信息量大，支持中文、链接等多种数据类型，且已有成熟的标准和生态。

**题目3.2：**

**位姿估计的输入：**

1. **已知物理信息（3D）**：
   - AprilTag 物理尺寸：16.6 cm = 0.166 m
   - 标签角点在标签坐标系下的 3D 坐标（假设 Z=0 平面）：
     - 左上: (-0.083, -0.083, 0)
     - 右上: (0.083, -0.083, 0)
     - 右下: (0.083, 0.083, 0)
     - 左下: (-0.083, 0.083, 0)

2. **检测到的像素坐标（2D）**：
   - 左上: (200, 150)
   - 右上: (440, 150)
   - 右下: (440, 340)
   - 左下: (200, 340)

3. **相机内参矩阵 K** 和畸变系数

**位姿估计的输出：**
- **旋转向量 rvec**：描述标签相对于相机的旋转
- **平移向量 tvec**：描述标签在相机坐标系下的位置

**距离估算：**

标签角点列坐标：x 从 200 到 440，跨度 240 像素
标签角点行坐标：y 从 150 到 340，跨度 190 像素

由于标签基本正对相机（无明显透视变形），可以根据像素跨度估算距离：

标签实际宽度 0.166m，在图像上占 240 像素，焦距 fx = 607.5 像素：

$$Z \approx \frac{f_x \times \text{实际宽度}}{\text{像素宽度}} = \frac{607.5 \times 0.166}{240} \approx 0.42 \text{ m}$$

因此相机到标签的大致距离约为 **42 厘米**。

---

*本章完*
