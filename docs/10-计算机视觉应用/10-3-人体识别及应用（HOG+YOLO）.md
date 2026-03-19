# 10-3 人体识别及应用（HOG + YOLO）

> **前置课程**：10-2 图像特征提取与匹配
> **后续课程**：10-4 目标跟踪与多目标跟踪

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：人体识别是计算机视觉中的核心任务之一，广泛应用于机器人避障、智能监控、人机交互等领域。本课程将介绍两种经典的人体检测方法：基于HOG（Histogram of Oriented Gradients）特征的传统方法，以及基于YOLO（You Only Look Once）深度学习方法。通过ROS2集成实战，你将掌握如何在机器人系统中实现实时人体检测与跟踪。

---

## 1. HOG特征提取

### 1.1 原理概述

**HOG（方向梯度直方图）** 是一种用于物体检测的特征描述符，由Dalal和Triggs在2005年提出。其核心思想是：通过统计图像局部区域的梯度方向分布来描述物体的形状和外观。

HOG特征具有以下优点：
- 对光照变化具有较好的鲁棒性
- 能够捕捉图像的边缘和形状信息
- 计算效率较高，适合实时应用

### 1.2 数学原理

给定一幅图像 $I(x,y)$，其梯度计算公式为：

$$G_x(x,y) = I(x+1,y) - I(x-1,y)$$

$$G_y(x,y) = I(x,y+1) - I(x,y-1)$$

梯度幅值和方向为：

$$G(x,y) = \sqrt{G_x(x,y)^2 + G_y(x,y)^2}$$

$$\theta(x,y) = \arctan\left(\frac{G_y(x,y)}{G_x(x,y)}\right)$$

HOG特征的提取过程如下：

1. **图像预处理**：将图像转换为灰度图，并进行归一化处理
2. **计算梯度**：对每个像素计算梯度幅值和方向
3. **划分单元格（Cells）**：将图像划分为若干个小的单元格（如 8×8 像素）
4. **构建直方图**：在每个单元格内，根据梯度方向统计直方图
5. **块归一化（Block Normalization）**：将若干个单元格组合成块（如 2×2 单元格），对块内特征进行归一化
6. **特征向量拼接**：将所有块的特征向量连接起来形成最终的HOG特征

```
┌─────────────────────────────────────────┐
│              输入图像                     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           计算梯度 (Gx, Gy)              │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      划分单元格 (8×8 pixels)            │
│  ┌────┬────┬────┬────┐                 │
│  │cell│cell│cell│cell│                 │
│  ├────┼────┼────┼────┤                 │
│  │cell│cell│cell│cell│                 │
│  └────┴────┴────┴────┘                 │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      每个单元格统计9bins直方图          │
│  [0°,20°,40°,60°,80°,100°,120°,140°,160°]│
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      块归一化 (2×2 cells)               │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         HOG 特征向量                     │
└─────────────────────────────────────────┘
```

### 1.3 OpenCV实现

使用OpenCV的`HOGDescriptor`可以方便地提取HOG特征：

```python
import cv2
import numpy as np

def extract_hog_features(image, cell_size=(8, 8), block_size=(2, 2), bins=9):
    """
    提取HOG特征
    
    参数:
        image: 输入图像 (灰度图)
        cell_size: 单元格大小
        block_size: 块大小 (单元格数量)
        bins: 方向直方图的bin数量
    
    返回:
        hog_features: HOG特征向量
        hog_image: HOG特征可视化图像
    """
    # 创建HOG描述符
    win_size = (64, 128)  # 检测窗口大小
    block_stride = (cell_size[0] * block_size[0], 
                    cell_size[1] * block_size[1])
    block_size_px = (block_size[0] * cell_size[0], 
                     block_size[1] * cell_size[1])
    
    hog = cv2.HOGDescriptor(win_size, block_size_px, 
                           block_stride, cell_size, bins)
    
    # 提取特征
    features = hog.compute(image)
    
    # 可视化HOG特征
    hog_image = np.zeros((128, 64), dtype=np.uint8)
    
    return features, hog_image

# 示例用法
image = cv2.imread('person.jpg', cv2.IMREAD_GRAYSCALE)
image = cv2.resize(image, (64, 128))
features, hog_vis = extract_hog_features(image)
print(f"HOG特征维度: {features.shape}")
```

### 1.4 行人检测器

OpenCV提供了预训练的HOG行人检测器：

```python
import cv2
import numpy as np

def detect_persons_hog(image):
    """
    使用HOG+SVM检测行人
    
    参数:
        image: 输入图像 (BGR格式)
    
    返回:
        boxes: 检测到的行人边界框列表
    """
    # 创建HOG描述符并加载预训练模型
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    # 检测行人
    # 参数: 图像, 步长, Padding, 阈值, 膨胀系数
    boxes, weights = hog.detectMultiScale(
        image,
        winStride=(8, 8),
        padding=(32, 32),
        scale=1.05,
        hitThreshold=0
    )
    
    # 绘制检测框
    for (x, y, w, h) in boxes:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    return image, boxes

# 示例用法
image = cv2.imread('test_image.jpg')
result_image, boxes = detect_persons_hog(image.copy())
print(f"检测到 {len(boxes)} 个行人")
cv2.imwrite('hog_detection_result.jpg', result_image)
```

---

## 2. YOLO目标检测

### 2.1 YOLO原理概述

**YOLO（You Only Look Once）** 是Joseph Redmon等人于2015年提出的实时目标检测算法。与传统的两阶段检测器（如R-CNN系列）不同，YOLO将目标检测问题作为回归问题来解决，在单次前向传播中同时预测边界框和类别概率。

YOLO系列的主要优点：
- **速度快**：单阶段检测，适合实时应用
- **背景误检率低**：利用全局上下文信息
- **泛化能力强**：学习到目标的通用特征

### 2.2 YOLO网络结构

以YOLOv5为例，网络结构分为三个部分：

1. **Backbone（骨干网络）**：CSPDarknet53，负责特征提取
2. **Neck（颈部网络）**：PANet，负责特征融合
3. **Head（头部网络）**：检测头，负责预测边界框和类别

```
┌─────────────────────────────────────────────────────┐
│                   输入图像 (640×640)                │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              Backbone: CSPDarknet53                │
│  ├── Focus层 (下采样)                               │
│  ├── CBS层 (Conv+BatchNorm+SiLU)                  │
│  ├── C3层 (Cross Stage Partial)                    │
│  └── SPPF (Spatial Pyramid Pooling - Fast)        │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                  Neck: PANet                        │
│  ├── Upsample (上采样)                              │
│  └── Concat (特征融合)                              │
└─────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────────────────────────────────────────────┐
│                  Head: 检测头                       │
│  ├── P3 (80×80) - 检测小目标                        │
│   ├── P4 (40×40) - 检测中目标                       │
│   └── P5 (20×20) - 检测大目标                       │
└─────────────────────────────────────────────────────┘
```

### 2.3 YOLO推理原理

YOLO将输入图像划分为 $S \times S$ 的网格，每个网格负责预测：

- **B个边界框** $(x, y, w, h)$ 和置信度 $C$
- **C个类别概率** $P(Class_i | Object)$

每个边界框的预测包含：
- $(x, y)$：边界框中心相对于网格左上角的偏移
- $(w, h)$：边界框宽高（相对于输入图像的比例）
- $confidence$：边界框包含目标的置信度

最终置信度为：

$$Score = P(Object) \times IoU_{pred}^{truth}$$

### 2.4 使用Ultralytics库

Ultralytics提供了简洁易用的YOLO接口：

```python
from ultralytics import YOLO
import cv2

def detect_persons_yolo(image_path, model_path='yolov8n.pt'):
    """
    使用YOLOv8检测行人
    
    参数:
        image_path: 输入图像路径
        model_path: 模型权重路径
    
    返回:
        result_image: 绘制了检测结果的图像
        detections: 检测结果列表
    """
    # 加载模型
    model = YOLO(model_path)
    
    # 读取图像
    image = cv2.imread(image_path)
    
    # 执行推理
    results = model(image, verbose=False)
    
    # 提取人物检测结果 (COCO数据集中person类别ID为0)
    detections = []
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # 获取类别ID
            class_id = int(box.cls[0])
            if class_id == 0:  # person类
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                detections.append({
                    'bbox': [x1, y1, x2, y2],
                    'confidence': confidence
                })
                # 绘制边界框
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f'Person: {confidence:.2f}'
                cv2.putText(image, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return image, detections

# 示例用法
result, detections = detect_persons_yolo('test_image.jpg', 'yolov8n.pt')
print(f"检测到 {len(detections)} 个人")
cv2.imwrite('yolo_detection_result.jpg', result)
```

### 2.5 模型选择

YOLO有多个版本和尺寸可选，精度和速度权衡如下：

| 模型 | 参数量 | mAP@0.5 | 速度 (FPS) | 适用场景 |
|------|--------|---------|------------|----------|
| YOLOv8n | 3.2M | 52.7% | 300 | 轻量级部署 |
| YOLOv8s | 11.2M | 56.8% | 220 | 边缘设备 |
| YOLOv8m | 26.2M | 64.0% | 100 | 通用场景 |
| YOLOv8l | 68.2M | 67.2% | 60 | 高精度 |
| YOLOv8x | 258.0M | 69.7% | 30 | 最高精度 |

```python
# 根据场景选择模型
def get_model(choice='n'):
    """
    获取不同尺寸的YOLOv8模型
    
    参数:
        choice: 模型尺寸 ('n', 's', 'm', 'l', 'x')
    
    返回:
        model: YOLO模型
    """
    model_map = {
        'n': 'yolov8n.pt',
        's': 'yolov8s.pt', 
        'm': 'yolov8m.pt',
        'l': 'yolov8l.pt',
        'x': 'yolov8x.pt'
    }
    return YOLO(model_map.get(choice, 'yolov8n.pt'))
```

---

## 3. ROS2集成

### 3.1 功能包创建

首先创建ROS2功能包用于人体检测：

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python person_detection --dependencies rclpy sensor_msgs std_msgs cv_bridge image_transport
```

### 3.2 自定义消息定义

创建用于发布检测结果的消息类型：

```yaml
# person_detection/msg/PersonDetection.msg
# 人体检测结果消息

std_msgs/Header header           # 时间戳和帧ID
int32[] bounding_box_x1          # 左上角x坐标数组
int32[] bounding_box_y1          # 左上角y坐标数组  
int32[] bounding_box_x2          # 右下角x坐标数组
int32[] bounding_box_y2          # 右下角y坐标数组
float32[] confidences            # 置信度数组
int32[] class_ids                # 类别ID数组
int32 count                      # 检测到的人数
```

### 3.3 HOG人体检测节点

```python
# person_detection/person_detection/hog_detector.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class HOGDetector(Node):
    """
    基于HOG的行人检测节点
    订阅图像话题，发布检测结果
    """
    
    def __init__(self):
        super().__init__('hog_detector')
        
        # 参数声明
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('output_topic', '/person_detection/hog')
        self.declare_parameter('display', True)
        
        image_topic = self.get_parameter('image_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.display = self.get_parameter('display').value
        
        # 初始化HOG检测器
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # 订阅图像
        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )
        
        # 发布检测结果图像
        self.image_pub = self.create_publisher(
            Image,
            output_topic,
            10
        )
        
        # 性能统计
        self.detection_count = 0
        self.total_time = 0.0
        
        self.get_logger().info(f'HOG Detector started, subscribing to {image_topic}')
    
    def image_callback(self, msg):
        """图像回调函数"""
        try:
            # ROS图像转OpenCV图像
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # 开始计时
            import time
            start_time = time.time()
            
            # 行人检测
            boxes = self.detect_persons(cv_image)
            
            # 统计时间
            elapsed = time.time() - start_time
            self.total_time += elapsed
            self.detection_count += 1
            
            avg_time = self.total_time / self.detection_count
            self.get_logger().debug(
                f'Detected {len(boxes)} persons in {elapsed*1000:.1f}ms '
                f'(avg: {avg_time*1000:.1f}ms)'
            )
            
            # 绘制结果
            if self.display:
                result_image = self.draw_results(cv_image, boxes)
            else:
                result_image = cv_image
            
            # 发布结果图像
            result_msg = self.bridge.cv2_to_imgmsg(result_image, 'bgr8')
            result_msg.header = msg.header
            self.image_pub.publish(result_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error processing image: {e}')
    
    def detect_persons(self, image):
        """
        使用HOG检测行人
        
        参数:
            image: OpenCV图像 (BGR)
        
        返回:
            boxes: 检测框列表 [(x, y, w, h), ...]
        """
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 检测行人
        boxes, _ = self.hog.detectMultiScale(
            gray,
            winStride=(8, 8),
            padding=(32, 32),
            scale=1.05
        )
        
        return boxes
    
    def draw_results(self, image, boxes):
        """绘制检测结果"""
        result = image.copy()
        
        for (x, y, w, h) in boxes:
            # 绘制边界框
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # 添加标签
            label = f'Person'
            cv2.putText(result, label, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # 添加统计信息
        info = f'HOG: {len(boxes)} detected'
        cv2.putText(result, info, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return result


def main(args=None):
    rclpy.init(args=args)
    node = HOGDetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 3.4 YOLO人体检测节点

```python
# person_detection/person_detection/yolo_detector.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

class YOLODetector(Node):
    """
    基于YOLOv8的行人检测节点
    """
    
    def __init__(self):
        super().__init__('yolo_detector')
        
        # 参数声明
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('output_topic', '/person_detection/yolo')
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('display', True)
        
        image_topic = self.get_parameter('image_topic').value
        output_topic = self.get_parameter('output_topic').value
        model_path = self.get_parameter('model_path').value
        self.confidence = self.get_parameter('confidence_threshold').value
        self.display = self.get_parameter('display').value
        
        # 加载YOLO模型
        self.get_logger().info(f'Loading YOLO model: {model_path}')
        self.model = YOLO(model_path)
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # 订阅图像
        self.image_sub = self.create_subscription(
            Image,
            image_topic,
            self.image_callback,
            10
        )
        
        # 发布检测结果
        self.image_pub = self.create_publisher(
            Image,
            output_topic,
            10
        )
        
        self.get_logger().info(f'YOLO Detector started')
    
    def image_callback(self, msg):
        """图像回调"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # YOLO推理
            results = self.model(cv_image, verbose=False, 
                                conf=self.confidence)
            
            # 提取人物检测结果
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    if class_id == 0:  # person
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        detections.append({
                            'bbox': [x1, y1, x2, y2],
                            'confidence': conf
                        })
            
            self.get_logger().debug(f'YOLO: {len(detections)} detected')
            
            # 绘制结果
            if self.display:
                result_image = self.draw_results(cv_image.copy(), detections)
            else:
                result_image = cv_image
            
            # 发布
            result_msg = self.bridge.cv2_to_imgmsg(result_image, 'bgr8')
            result_msg.header = msg.header
            self.image_pub.publish(result_msg)
            
        except Exception as e:
            self.get_logger().error(f'Error: {e}')
    
    def draw_results(self, image, detections):
        """绘制检测结果"""
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f'Person: {conf:.2f}'
            cv2.putText(image, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        info = f'YOLO: {len(detections)} detected'
        cv2.putText(image, info, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return image


def main(args=None):
    rclpy.init(args=args)
    node = YOLODetector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 3.5 启动文件

创建launch文件方便启动：

```python
# person_detection/launch/person_detection.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    """生成启动描述"""
    
    # HOG检测器节点
    hog_detector = Node(
        package='person_detection',
        executable='hog_detector',
        name='hog_detector',
        parameters=[{
            'image_topic': '/camera/image_raw',
            'output_topic': '/person_detection/hog',
            'display': True
        }],
        output='screen'
    )
    
    # YOLO检测器节点
    yolo_detector = Node(
        package='person_detection',
        executable='yolo_detector',
        name='yolo_detector',
        parameters=[{
            'image_topic': '/camera/image_raw',
            'output_topic': '/person_detection/yolo',
            'model_path': 'yolov8n.pt',
            'confidence_threshold': 0.5,
            'display': True
        }],
        output='screen'
    )
    
    return LaunchDescription([
        hog_detector,
        yolo_detector
    ])
```

---

## 4. 人体跟踪应用

### 4.1 跟踪算法概述

在检测到人体后，我们需要对不同的人进行跟踪，以实现持续监控或行为分析。常用的跟踪算法包括：

- **SORT (Simple Online and Realtime Tracking)**：基于卡尔曼滤波和匈牙利算法
- **DeepSORT**：结合深度学习特征的跟踪算法
- **ByteTrack**：基于字节Tracklet关联的跟踪算法

### 4.2 简单人体跟踪实现

```python
# person_detection/person_detection/person_tracker.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
from scipy.optimize import linear_sum_assignment
import numpy as np
import cv2

class PersonTracker(Node):
    """
    简单人体跟踪器
    结合YOLO检测和匈牙利算法进行多目标跟踪
    """
    
    def __init__(self):
        super().__init__('person_tracker')
        
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('model_path', 'yolov8n.pt')
        
        self.model = YOLO(self.get_parameter('model_path').value)
        self.bridge = CvBridge()
        
        # 跟踪参数
        self.max_age = 30      # 最大丢失帧数
        self.min_hits = 3      # 最小命中次数
        self.iou_threshold = 0.3  # IOU匹配阈值
        
        # 跟踪状态
        self.next_id = 0
        self.tracks = {}  # {track_id: {'bbox': [...], 'age': 0, 'hits': 0}}
        
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.callback, 10)
        self.image_pub = self.create_publisher(Image, '/person_tracking/result', 10)
        
        self.get_logger().info('Person tracker started')
    
    def callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        
        # 检测
        results = self.model(cv_image, verbose=False)
        detections = self.extract_detections(results)
        
        # 更新跟踪
        self.update_tracks(detections)
        
        # 绘制结果
        result_image = self.draw_tracks(cv_image)
        
        # 发布
        result_msg = self.bridge.cv2_to_imgmsg(result_image, 'bgr8')
        result_msg.header = msg.header
        self.image_pub.publish(result_msg)
    
    def extract_detections(self, results):
        """提取人物检测"""
        detections = []
        for result in results:
            for box in result.boxes:
                if int(box.cls[0]) == 0:  # person
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    detections.append({
                        'bbox': [x1, y1, x2, y2],
                        'confidence': conf,
                        'center': [(x1+x2)/2, (y1+y2)/2]
                    })
        return detections
    
    def update_tracks(self, detections):
        """更新跟踪状态"""
        if not self.tracks:
            # 初始化跟踪
            for det in detections:
                self.tracks[self.next_id] = {
                    'bbox': det['bbox'],
                    'age': 0,
                    'hits': 1,
                    'conf': det['confidence']
                }
                self.next_id += 1
            return
        
        if not detections:
            # 无检测，更新年龄
            for tid in list(self.tracks.keys()):
                self.tracks[tid]['age'] += 1
            self.remove_old_tracks()
            return
        
        # 计算IOU矩阵
        iou_matrix = self.compute_iou_matrix(detections)
        
        # 匈牙利匹配
        row_ind, col_ind = linear_sum_assignment(-iou_matrix)
        
        matched_detections = set()
        matched_tracks = set()
        
        for r, c in zip(row_ind, col_ind):
            if iou_matrix[r, c] > self.iou_threshold:
                tid = list(self.tracks.keys())[r % len(self.tracks)]
                self.tracks[tid] = {
                    'bbox': detections[c]['bbox'],
                    'age': 0,
                    'hits': self.tracks[tid]['hits'] + 1,
                    'conf': detections[c]['confidence']
                }
                matched_detections.add(c)
                matched_tracks.add(tid)
        
        # 新增跟踪
        for i, det in enumerate(detections):
            if i not in matched_detections:
                self.tracks[self.next_id] = {
                    'bbox': det['bbox'],
                    'age': 0,
                    'hits': 1,
                    'conf': det['confidence']
                }
                self.next_id += 1
        
        # 更新未匹配跟踪的年龄
        for tid in self.tracks:
            if tid not in matched_tracks:
                self.tracks[tid]['age'] += 1
        
        self.remove_old_tracks()
    
    def compute_iou_matrix(self, detections):
        """计算IOU矩阵"""
        n = len(self.tracks)
        m = len(detections)
        iou_matrix = np.zeros((n, m))
        
        track_bboxes = list(self.tracks[t]['bbox'] for t in self.tracks)
        det_bboxes = [d['bbox'] for d in detections]
        
        for i, tb in enumerate(track_bboxes):
            for j, db in enumerate(det_bboxes):
                iou_matrix[i, j] = self.compute_iou(tb, db)
        
        return iou_matrix
    
    def compute_iou(self, bbox1, bbox2):
        """计算两个边界框的IOU"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        union_area = box1_area + box2_area - inter_area
        
        return inter_area / union_area if union_area > 0 else 0
    
    def remove_old_tracks(self):
        """移除丢失太久的跟踪"""
        to_remove = []
        for tid, track in self.tracks.items():
            if track['age'] > self.max_age:
                to_remove.append(tid)
        for tid in to_remove:
            del self.tracks[tid]
    
    def draw_tracks(self, image):
        """绘制跟踪结果"""
        result = image.copy()
        
        for tid, track in self.tracks.items():
            if track['hits'] < self.min_hits:
                continue
            
            x1, y1, x2, y2 = track['bbox']
            
            # 颜色基于ID
            color = ((tid * 50) % 255, (tid * 100) % 255, (tid * 150) % 255)
            
            cv2.rectangle(result, (x1, y1), (x2, y2), color, 2)
            label = f'ID:{tid} Conf:{track["conf"]:.2f}'
            cv2.putText(result, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        info = f'Tracking: {len([t for t in self.tracks.values() if t["hits"] >= self.min_hits])} persons'
        cv2.putText(result, info, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return result


def main(args=None):
    rclpy.init(args=args)
    node = PersonTracker()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

---

## 5. 实战：机器人人体避障

### 5.1 系统架构

将人体检测与机器人控制结合，实现智能避障：

```
┌──────────────┐    /camera/image_raw    ┌──────────────────┐
│   相机节点    │ ─────────────────────▶ │   人体检测节点    │
└──────────────┘                          └────────┬─────────┘
                                                   │
                                                   ▼
                                         ┌──────────────────┐
                                         │  控制决策节点     │
                                         │  (避障逻辑)      │
                                         └────────┬─────────┘
                                                  │
                        ┌─────────────────────────┼─────────────────────────┐
                        │                         │                         │
                        ▼                         ▼                         ▼
              ┌──────────────────┐    ┌──────────────────┐       ┌──────────────────┐
              │  /cmd_vel (停止) │    │  /cmd_vel (直行) │       │  /cmd_vel (转向) │
              └──────────────────┘    └──────────────────┘       └──────────────────┘
```

### 5.2 避障控制节点

```python
# person_detection/person_detection/collision_avoider.py
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

class CollisionAvoider(Node):
    """
    基于人体检测的避障控制器
    检测到人体时停止机器人，人离开后恢复移动
    """
    
    def __init__(self):
        super().__init__('collision_avoider')
        
        # 参数
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('min_distance', 1.5)  # 最小安全距离 (米)
        self.declare_parameter('max_speed', 0.3)     # 最大速度 m/s
        
        self.min_distance = self.get_parameter('min_distance').value
        self.max_speed = self.get_parameter('max_speed').value
        
        # 加载YOLO
        self.model = YOLO('yolov8n.pt')
        self.bridge = CvBridge()
        
        # 订阅图像
        self.image_sub = self.create_subscription(
            Image, 
            self.get_parameter('image_topic').value,
            self.callback,
            10
        )
        
        # 发布速度指令
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 状态
        self.person_detected = False
        self.detection_count = 0
        self.confidence_threshold = 0.6
        self.current_min_distance = float('inf')
        
        # 定时器用于发布速度
        self.timer = self.create_timer(0.1, self.publish_cmd_vel)
        
        self.get_logger().info('Collision avoider started')
    
    def callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # 检测人体
            results = self.model(cv_image, verbose=False, 
                                conf=self.confidence_threshold)
            
            # 计算最近人体距离
            min_dist = float('inf')
            person_found = False
            
            for result in results:
                for box in result.boxes:
                    if int(box.cls[0]) == 0:  # person
                        person_found = True
                        # 根据边界框高度估算距离
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        height_pixels = y2 - y1
                        
                        # 简单距离估算
                        distance = self.estimate_distance(height_pixels)
                        
                        if distance < min_dist:
                            min_dist = distance
            
            # 更新状态 (连续3帧检测到才确认)
            if person_found:
                self.detection_count += 1
            else:
                self.detection_count = 0
            
            self.person_detected = self.detection_count >= 3
            self.current_min_distance = min_dist if person_found else float('inf')
            
        except Exception as e:
            self.get_logger().error(f'Error: {e}')
    
    def estimate_distance(self, height_pixels):
        """
        根据边界框高度估算距离
        假设人体高度约1.7米
        """
        known_height = 1.7  # 米
        focal_length = 500  # 像素 (需根据相机标定调整)
        
        if height_pixels > 0:
            distance = known_height * focal_length / height_pixels
            return distance
        return float('inf')
    
    def publish_cmd_vel(self):
        """发布速度指令"""
        cmd = Twist()
        
        if self.person_detected and self.current_min_distance < self.min_distance:
            # 检测到人体且距离过近，停止
            cmd.linear.x = 0.0
            cmd.angular.z = 0.0
            status = "STOP - Person detected!"
        else:
            # 正常前进
            cmd.linear.x = self.max_speed
            cmd.angular.z = 0.0
            status = "MOVING"
        
        self.cmd_vel_pub.publish(cmd)
        self.get_logger().debug(status)


def main(args=None):
    rclpy.init(args=args)
    node = CollisionAvoider()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 5.3 运行系统

```bash
# 编译功能包
cd ~/ros2_ws
colcon build --packages-select person_detection
source install/setup.bash

# 终端1：启动相机（如果使用USB相机）
ros2 run v4l2_camera v4l2_camera_node

# 终端2：启动YOLO检测器
ros2 run person_detection yolo_detector

# 终端3：启动避障控制器
ros2 run person_detection collision_avoider

# 终端4：查看检测结果
ros2 run rqt_image_view rqt_image_view
# 选择 /person_detection/yolo 话题查看结果
```

---

## 练习题

### 选择题

1. HOG特征提取过程中，每个单元格（Cell）的直方图 bins 数量通常是？
   - A) 3
   - B) 6
   - C) 9
   - D) 12
   
   **答案：C**。HOG特征通常使用9个方向bins，即把0°-180°（或0°-360°）均匀分成9个区间。

2. YOLO目标检测算法属于以下哪一类？
   - A) 两阶段检测器（如R-CNN）
   - B) 单阶段检测器（如YOLO、SSD）
   C) 特征金字塔网络
   - D) 语义分割网络
   
   **答案：B**。YOLO是典型的单阶段（One-Stage）目标检测算法，在单次前向传播中完成检测。

3. 在COCO数据集的80类目标中，person（人物）类别的ID是多少？
   - A) 1
   - B) 0
   - C) 15
   - D) 50
   
   **答案：B**。在COCO数据集中，person类别的ID为0。

4. 匈牙利算法在多目标跟踪中主要用于？
   - A) 特征提取
   - B) 数据关联（匹配检测框和跟踪ID）
   - C) 目标分类
   - D) 图像增强
   
   **答案：B**。匈牙利算法用于解决数据关联问题，将检测框与已有的跟踪轨迹进行最优匹配。

### 实践题

5. 创建一个ROS2节点，使用HOG检测器检测图像中的人物，并统计检测耗时。
   
   **参考答案**：
   
   ```python
   import rclpy
   from rclpy.node import Node
   from sensor_msgs.msg import Image
   from cv_bridge import CvBridge
   import cv2
   import time

   class HOGStats(Node):
       def __init__(self):
           super().__init__('hog_stats')
           self.bridge = CvBridge()
           self.hog = cv2.HOGDescriptor()
           self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
           
           self.sub = self.create_subscription(Image, '/camera/image_raw', self.callback, 10)
           self.times = []
           
       def callback(self, msg):
           img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
           gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
           
           start = time.time()
           boxes, _ = self.hog.detectMultiScale(gray, winStride=(8,8), padding=(32,32), scale=1.05)
           elapsed = time.time() - start
           
           self.times.append(elapsed)
           avg = sum(self.times) / len(self.times) if self.times else 0
           
           self.get_logger().info(f'Detected: {len(boxes)}, Time: {elapsed*1000:.1f}ms, Avg: {avg*1000:.1f}ms')

   def main(args=None):
       rclpy.init(args=args)
       rclpy.spin(HOGStats())
       rclpy.shutdown()
   ```

6. 修改YOLO检测器代码，添加对多个类别的检测（不仅限于人物），并发布检测结果到新话题。
   
   **提示**：
   - 移除person类别的过滤条件
   - 创建自定义消息或使用标准消息发布所有检测结果
   - 在draw_results中添加类别名称显示

---

## 本章小结

本章我们全面学习了人体识别与应用的两种核心技术：

1. **HOG特征提取**：详细介绍了HOG的数学原理，包括梯度计算、单元格划分、直方图统计和块归一化等步骤。HOG+SVM是传统的行人检测方案，计算效率高但精度有限。

2. **YOLO目标检测**：深入学习了YOLO的网络结构和推理原理。YOLO作为单阶段检测器，在速度和精度之间取得了很好的平衡。通过Ultralytics库，可以快速实现高性能的人体检测。

3. **ROS2集成**：通过创建HOG和YOLO检测节点，掌握了将视觉算法集成到ROS2系统中的方法。话题通信机制使得检测结果可以方便地传递给其他节点。

4. **人体跟踪**：实现了基于IOU匹配和匈牙利算法的简单多目标跟踪器，为后续的复杂跟踪算法奠定了基础。

5. **实战应用**：通过机器人人体避障案例，展示了如何将检测结果转化为机器人控制指令，实现智能避障功能。

---

## 参考资料

### HOG相关

1. Dalal & Triggs原始论文: https://ieeexplore.ieee.org/document/1561014
2. OpenCV HOG文档: https://docs.opencv.org/4.x/d5/d33/structcv_1_1HOGDescriptor.html

### YOLO相关

3. YOLO系列发展史: https://pjreddie.com/darknet/yolo/
4. Ultralytics YOLO文档: https://docs.ultralytics.com/
5. YOLOv8 GitHub: https://github.com/ultralytics/ultralytics

### ROS2相关

6. rclpy文档: https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Python-Publisher-And-Subscriber.html
7. cv_bridge文档: https://docs.ros.org/en/humble/p/rclpy api

---

## 下节预告

下一节我们将学习**10-4 目标跟踪与多目标跟踪**，深入探讨SORT、DeepSORT等经典跟踪算法，以及如何处理遮挡、ID切换等复杂场景。

---

*本章学习完成！建议大家动手实践HOG和YOLO的对比实验，体会传统方法与深度学习方法各自的优缺点。*