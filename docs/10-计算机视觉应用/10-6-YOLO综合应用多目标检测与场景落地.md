# 10-6 YOLO综合应用：多目标检测与场景落地

> **前置课程**：10-5 图像分割及应用
> **后续课程**：课程完结

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：YOLO（You Only Look Once）是目前工业界最广泛使用的目标检测算法，以其速度快、精度高著称。本节将从YOLO系列发展讲起，深入剖析YOLOv8的核心架构，通过多目标检测实战、ROS2集成以及机器人应用场景，帮助你全面掌握YOLO在实际机器人系统中的落地方法。

---

## 1. YOLO系列发展

YOLO系列是目标检测领域的里程碑算法，从2016年首次提出至今，已经迭代了多个版本。理解YOLO的发展脉络，有助于更好地掌握其最新版本的设计理念。

### 1.1 从YOLOv1到YOLOv3：奠基时代

**YOLOv1（2016）** 由Joseph Redmon等人提出，首次将目标检测问题转化为单次回归问题。与当时的Faster R-CNN等两阶段检测器相比，YOLOv1实现了端到端的检测，速度达到45 FPS（帧每秒），但精度较低，尤其是对小目标的检测效果不佳。

YOLOv1的核心思想是将输入图像划分为$S \times S$的网格，每个网格负责预测中心点落在该网格内的目标。每个网格预测$B$个边界框和每个框的置信度，以及$C$个类别的条件概率。

**YOLOv2（2017）** 在v1基础上进行了多项改进：引入Batch Normalization加速收敛、使用高分辨率分类器、采用先验框（Anchor Boxes）机制、使用Darknet-19作为 backbone 等。v2在416×416输入下达到67 FPS，mAP（mean Average Precision）为76.8%。

**YOLOv3（2018）** 采用了更深的Darknet-53 backbone，并引入FPN（Feature Pyramid Network）实现多尺度检测。v3在小目标检测上有了显著提升，但中等和大型目标的检测略有下降。速度为35 FPS，AP为55.3%。

### 1.2 YOLOv4到YOLOv7：工程化时代

**YOLOv4（2020）** 由Alexey Bochkovskiy等人发布，集成了大量深度学习的 tricks，包括：
- **Backbone**：CSPDarknet53（Cross Stage Partial）
- **Neck**：SPP（Spatial Pyramid Pooling）+ PAN（Path Aggregation Network）
- **Bag of Freebies**：Mosaic数据增强、Label Smoothing、CIOU Loss等
- **Bag of Specials**：Mish激活函数、DIoU NMS等

v4在COCO数据集上达到43.5% AP，FPS达到65。

**YOLOv5（2020）** 由Ultralytics公司发布，采用PyTorch实现，工程化程度极高。v5提供了n/s/m/l/x五种尺度的模型，满足从边缘设备到高性能GPU的不同算力需求。v5的anchor-free版本进一步简化了训练流程。

**YOLOv6（2022）** 由美团发布，针对工业应用进行了优化，采用重参数化设计和高效的Neck和Backbone设计，在精度和速度上均有提升。

**YOLOv7（2022）** 在v4基础上进一步优化，提出了E-ELAN（Extended Efficient Layer Aggregation Network）和模型缩放技术，在COCO上达到56.8% AP。

### 1.3 YOLOv8：集大成者

**YOLOv8（2023）** 由Ultralytics发布，是YOLO系列的最新力作。它继承了v5工程化的优点，同时借鉴了v4/v7的先进技术，并进行了多项创新：

| 特性 | YOLOv8改进 |
|------|-----------|
| Backbone | CSPDarknet53 + C2f模块 |
| Neck | PAFPN（路径聚合FPN） |
| Head | Decoupled Head（解耦头） |
| Anchor | Anchor-Free设计 |
| 损失函数 | Distribution Focal Loss + CIoU |
| 数据增强 | Mosaic + MixUp + Copy-paste |
| 部署 | ONNX/TensorRT/LiteRT支持 |

YOLOv8的模型规模延续了v5的设计，提供n/s/m/l/x五种规模：

| 模型 | 参数量（M） | FLOPs（G） | AP（COCO） | FPS（V100） |
|------|-------------|------------|------------|-------------|
| YOLOv8n | 3.2 | 8.7 | 37.3 | 277 |
| YOLOv8s | 11.2 | 28.6 | 44.9 | 175 |
| YOLOv8m | 25.9 | 78.9 | 50.2 | 105 |
| YOLOv8l | 43.7 | 165.2 | 52.9 | 62 |
| YOLOv8x | 68.2 | 257.8 | 53.9 | 46 |

---

## 2. YOLOv8详解

YOLOv8的核心架构分为三个部分：**Backbone（骨干网络）**、**Neck（颈部网络）**和**Head（检测头）**。理解这三部分的设计原理，是掌握YOLOv8的关键。

### 2.1 Backbone：特征提取

YOLOv8的Backbone采用CSPDarknet53结构，主要由C2f模块构成。C2f（Cross Stage Partial with Fast）模块是YOLOv8的核心构建块，它在保持特征提取能力的同时大幅降低了计算量。

**C2f模块结构**：

```
C2f模块输入
     │
     ├──→ Conv(k=1, s=1) → BN → SiLU ──────────────────┐
     │                                                 │
     │    ┌─────────────────────────────────────────┐  │
     │    │                                         │  │
     ├──→ │  → Split → Conv → Concat → Conv → Concat│──┼──→ 输出
     │    │                                         │  │
     │    └─────────────────────────────────────────┘  │
     │                                                 │
     └──→ Conv(k=1, s=1) → BN → SiLU ──────────────────┘
```

C2f模块的核心思想是将特征图在通道维度上split为两部分：一部分经过多个卷积块处理，另一部分直接做残差连接，最后concat在一起。这种设计既保留了原始特征，又提取了深层语义。

**下采样模块**：YOLOv8使用步长为2的卷积实现下采样，配合C2f模块逐步降低特征图尺寸、增大通道数：

| 阶段 | 特征图尺寸 | 通道数 | C2f模块数 |
|------|-----------|--------|-----------|
| Stage 1 | H/2 × W/2 | 64 | 1 |
| Stage 2 | H/4 × W/4 | 128 | 1 |
| Stage 3 | H/8 × W/8 | 256 | 3 |
| Stage 4 | H/16 × W/16 | 512 | 6 |
| Stage 5 | H/32 × W/32 | 1024 | 6 |

### 2.2 Neck：特征融合

Neck部分采用PAFPN（Path Aggregation Feature Pyramid Network）结构，实现多尺度特征的融合。PAFPN在FPN的基础上增加了自底向上的路径，帮助低层特征获得更强的语义信息。

**Neck的工作流程**：

```
Backbone输出:
  P3 (H/8) ────────────────────────────────┐
  P4 (H/16) ────→ FPN → P4' ──→ PAN → P4'' │
  P5 (H/32) ────→ FPN → P5' ──→ PAN → P5'' │
                                             │
                                             ▼
输出多尺度特征: P3', P4'', P5'' (送入Head)
```

FPN自顶向下传递高层语义，PAN自底向上传递定位信息，两者结合使特征金字塔的每一层都兼具语义和细节。

### 2.3 Head：检测头

YOLOv8采用**解耦检测头（Decoupled Head）**，将分类和回归分支分开。这一设计在v5的耦合头基础上进行了重大改进，显著提升了检测精度。

**解耦头的结构**：

```
输入特征 (P3/P4/P5)
     │
     ├──→ Conv(k=3, s=1) → BN → SiLU ──┐
     │                                 │
     ├──→ Conv(k=3, s=1) → BN → SiLU ──┼──→ Concat ─→ Conv → 输出
     │                                 │              │
     └──→ Conv(k=3, s=1) → BN → SiLU ──┘              │
                                                     │
                              ┌───────────────────────┘
                              ▼
                      分类分支 + 回归分支 + IoU分支
```

- **分类分支**：预测每个anchor的类别概率
- **回归分支**：预测边界框的坐标偏移量（中心点xy + 长宽wh）
- **IoU分支**：预测边界框与GT的IoU分数（用于辅助分类）

**损失函数**：YOLOv8的损失函数由三部分组成：

$$\mathcal{L}_{total} = \mathcal{L}_{cls} + \mathcal{L}_{reg} + \mathcal{L}_{IoU}$$

其中：
- $\mathcal{L}_{cls}$：使用BCE（二进制交叉熵）或Distribution Focal Loss
- $\mathcal{L}_{reg}$：使用CIoU（Complete Intersection over Union）损失
- $\mathcal{L}_{IoU}$：使用BCELoss计算IoU预测损失

**CIoU Loss**的公式为：

$$\mathcal{L}_{CIoU} = 1 - IoU + \frac{\rho^2(b, b^{gt})}{c^2} + \alpha v$$

其中：
- $IoU$：预测框与GT框的交并比
- $\rho^2(b, b^{gt})$：两个框中心点的欧氏距离平方
- $c$：覆盖两个框的最小闭包框的对角线长度
- $\alpha$：权重参数
- $v$：长宽比一致性度量

### 2.4 Anchor-Free设计

YOLOv8采用anchor-free设计，摒弃了预定义的anchor boxes，每个位置直接预测目标的存在性和边界框参数。这种设计简化了模型，减少了超参数数量，提高了泛化能力。

对于每个位置$(x, y)$，YOLOv8直接预测：
- 相对于特征图网格的偏移量$(dx, dy)$
- 预测框的宽高$(dw, dh)$
- 目标的置信度$o$
- 各类别的概率

最终边界框计算为：

$$b_x = x + \sigma(d_x)$$
$$b_y = y + \sigma(d_y)$$
$$b_w = p_w \cdot e^{d_w}$$
$$b_h = p_h \cdot e^{d_h}$$

其中$\sigma$是sigmoid函数，$p_w, p_h$是基础尺寸。

---

## 3. 多目标检测实战

本节通过实际代码演示YOLOv8的多目标检测能力，包括图片检测、视频检测和摄像头实时检测。

### 3.1 环境配置

```bash
# 创建conda环境
conda create -n yolov8 python=3.10 -y
conda activate yolov8

# 安装ultralytics库
pip install ultralytics opencv-python pillow numpy

# 验证安装
python -c "from ultralytics import YOLO; print('YOLOv8 installed successfully')"
```

### 3.2 基础图片检测

```python
# detect_image.py - 图片目标检测
from ultralytics import YOLO
import cv2

# 加载预训练模型（n/s/m/l/x可选）
model = YOLO('yolov8n.pt')  # nano模型，速度最快

# 对单张图片进行检测
results = model('https://ultralytics.com/images/bus.jpg', save=True)

# 处理检测结果
for result in results:
    boxes = result.boxes  # 边界框结果
    
    # 遍历每个检测目标
    for box in boxes:
        # 获取边界框坐标 (xyxy格式)
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        
        # 获取置信度
        conf = box.conf[0].cpu().numpy()
        
        # 获取类别ID和名称
        cls_id = int(box.cls[0])
        cls_name = result.names[cls_id]
        
        # 绘制边界框
        cv2.rectangle(result.orig_img, 
                     (int(x1), int(y1)), 
                     (int(x2), int(y2)), 
                     (0, 255, 0), 2)
        
        # 添加标签
        label = f'{cls_name} {conf:.2f}'
        cv2.putText(result.orig_img, label, 
                   (int(x1), int(y1) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                   (0, 255, 0), 2)
        
        print(f'Detected: {cls_name} | Confidence: {conf:.4f} | '
              f'Box: [{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]')

# 保存结果
cv2.imwrite('result.jpg', result.orig_img)
print('Result saved to result.jpg')
```

### 3.3 视频目标检测

```python
# detect_video.py - 视频目标检测
from ultralytics import YOLO
import cv2

# 加载模型
model = YOLO('yolov8n.pt')

# 打开视频文件或摄像头
video_path = 0  # 0表示摄像头，也可以是视频文件路径
cap = cv2.VideoCapture(video_path)

# 获取视频信息
fps = int(cap.get(cv2.CAP_PROP_FPS))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# 创建视频写入器
output_path = 'output.mp4'
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

# 定义颜色映射（为不同类别分配不同颜色）
colors = {}
import numpy as np

def get_color(cls_id):
    if cls_id not in colors:
        colors[cls_id] = tuple(np.random.randint(0, 255, 3).tolist())
    return colors[cls_id]

# 统计信息
total_frames = 0
detection_history = []

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    total_frames += 1
    
    # 进行检测
    results = model(frame, conf=0.5, iou=0.45)
    
    # 当前帧的检测结果
    frame_detections = []
    
    for result in results:
        boxes = result.boxes
        
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            conf = box.conf[0].cpu().numpy()
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            
            # 获取颜色
            color = get_color(cls_id)
            
            # 绘制边界框
            cv2.rectangle(frame, 
                         (int(x1), int(y1)), 
                         (int(x2), int(y2)), 
                         color, 2)
            
            # 绘制标签背景
            label = f'{cls_name} {conf:.2f}'
            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(frame,
                         (int(x1), int(y1) - label_h - 10),
                         (int(x1) + label_w, int(y1)),
                         color, -1)
            
            # 绘制标签文字
            cv2.putText(frame, label,
                       (int(x1), int(y1) - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                       (255, 255, 255), 2)
            
            # 记录检测结果
            frame_detections.append({
                'class': cls_name,
                'confidence': float(conf),
                'bbox': [float(x1), float(y1), float(x2), float(y2)]
            })
    
    # 显示FPS
    cv2.putText(frame, f'FPS: {fps}', (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # 显示检测数量
    cv2.putText(frame, f'Detections: {len(frame_detections)}', 
               (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, 
               (0, 255, 0), 2)
    
    # 保存帧
    out.write(frame)
    
    # 实时显示
    cv2.imshow('YOLOv8 Detection', frame)
    
    # 按q退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    detection_history.append(frame_detections)

cap.release()
out.release()
cv2.destroyAllWindows()

print(f'Processed {total_frames} frames')
print(f'Total detections: {sum(len(d) for d in detection_history)}')
print(f'Video saved to {output_path}')
```

### 3.4 多目标追踪

YOLOv8内置了目标追踪功能，可以跨帧追踪同一目标：

```python
# track.py - 多目标追踪
from ultralytics import YOLO
import cv2

# 加载模型（使用track模式）
model = YOLO('yolov8n.pt')

# 启动追踪，persist=True保持追踪ID跨帧一致
results = model.track(source='video.mp4', 
                      conf=0.5, 
                      iou=0.45,
                      persist=True,
                      show=True)

# 获取追踪结果
for result in results:
    boxes = result.boxes
    
    if boxes.id is not None:  # 有追踪ID
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            track_id = int(box.id[0])  # 追踪ID
            cls_id = int(box.cls[0])
            cls_name = result.names[cls_id]
            conf = box.conf[0].cpu().numpy()
            
            # 绘制追踪框和ID
            cv2.rectangle(result.orig_img,
                         (int(x1), int(y1)),
                         (int(x2), int(y2)),
                         (0, 255, 0), 2)
            
            label = f'ID:{track_id} {cls_name}'
            cv2.putText(result.orig_img, label,
                       (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                       (0, 255, 0), 2)
            
            print(f'Track ID: {track_id} | Class: {cls_name} | '
                  f'Conf: {conf:.2f}')
```

### 3.5 自定义数据集训练

使用自己的数据集训练YOLOv8：

```python
# train.py - 自定义数据集训练
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolov8n.yaml')  # 从配置文件加载，或使用'yolov8n.pt'

# 开始训练
results = model.train(
    data='dataset.yaml',      # 数据集配置文件
    epochs=100,               # 训练轮数
    imgsz=640,                # 输入图片大小
    batch=16,                 # 批次大小
    device=0,                 # GPU设备，'cpu'使用CPU
    workers=8,                # 数据加载线程数
    patience=50,              # 早停耐心值
    save=True,                # 保存模型
    save_period=10,           # 每10轮保存一次
    project='runs/detect',    # 输出项目目录
    name='train',             # 实验名称
    exist_ok=True,            # 允许覆盖已有结果
    pretrained=True,          # 使用预训练权重
    optimizer='SGD',          # 优化器: SGD/Adam/AdamW
    lr0=0.01,                 # 初始学习率
    lrf=0.01,                 # 最终学习率 = lr0 * lrf
    momentum=0.937,           # SGD动量
    weight_decay=0.0005,      # 权重衰减
    warmup_epochs=3.0,        # 预热轮数
    warmup_momentum=0.8,      # 预热动量
    box=7.5,                  # 边界框损失权重
    cls=0.5,                  # 分类损失权重
    dfl=1.5,                  # DFL损失权重
    mosaic=1.0,               # Mosaic增强概率
    mixup=0.0,                # MixUp增强概率
    copy_paste=0.0,           # Copy-paste增强概率
)

# 打印训练结果
print(f'Best mAP: {results.results_dict["metrics/mAP50(B)"]:.4f}')
print(f'Final mAP: {results.results_dict["metrics/mAP50-95(B)"]:.4f}')
```

**dataset.yaml配置文件格式**：

```yaml
# dataset.yaml
path: ./datasets/custom_dataset  # 数据集根目录
train: images/train              # 训练集图片目录
val: images/val                  # 验证集图片目录

# 类别数量
nc: 5

# 类别名称
names:
  0: person
  1: car
  2: bicycle
  3: dog
  4: cat
```

---

## 4. ROS2集成

将YOLOv8集成到ROS2系统中，实现机器人实时目标检测。

### 4.1 功能包创建

```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python yolov8_ros --dependencies rclpy sensor_msgs cv_bridge std_msgs message_filters

# 创建目录结构
mkdir -p yolov8_ros/yolov8_ros
mkdir -p yolov8_ros/resource
mkdir -p yolov8_ros/test
```

### 4.2 YOLOv8检测节点

```python
# yolov8_ros/yolov8_ros/yolo_detector.py
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np

class YoloDetector(Node):
    """YOLOv8目标检测节点"""
    
    def __init__(self):
        super().__init__('yolo_detector')
        
        # 声明参数
        self.declare_parameter('model_name', 'yolov8n.pt')
        self.declare_parameter('conf_threshold', 0.5)
        self.declare_parameter('iou_threshold', 0.45)
        self.declare_parameter('device', 'cuda')  # cuda/cpu
        self.declare_parameter('enable_cuda', False)
        
        self.model_name = self.get_parameter('model_name').value
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.iou_threshold = self.get_parameter('iou_threshold').value
        self.device = self.get_parameter('device').value
        self.enable_cuda = self.get_parameter('enable_cuda').value
        
        # 加载模型
        self.get_logger().info(f'Loading model: {self.model_name}')
        self.model = YOLO(self.model_name)
        
        if self.enable_cuda:
            self.model.to('cuda')
            self.get_logger().info('Using CUDA GPU')
        else:
            self.model.to('cpu')
            self.get_logger().info('Using CPU')
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # QoS配置
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            depth=1
        )
        
        # 订阅图像话题
        self.image_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            qos_profile
        )
        
        # 发布检测结果
        self.detection_pub = self.create_publisher(
            Detection2DArray,
            '/yolo/detections',
            10
        )
        
        # 发布带检测框的图像
        self.result_image_pub = self.create_publisher(
            Image,
            '/yolo/result_image',
            10
        )
        
        # 统计信息
        self.frame_count = 0
        self.fps = 0.0
        self.last_time = self.get_clock().now()
        
        self.get_logger().info('YOLO detector node initialized')
    
    def image_callback(self, msg):
        """处理图像消息"""
        try:
            # ROS图像转OpenCV图像
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {e}')
            return
        
        # 运行YOLOv8检测
        results = self.model(cv_image, 
                             conf=self.conf_threshold, 
                             iou=self.iou_threshold,
                             verbose=False)
        
        # 发布检测结果
        self.publish_detections(results, msg.header)
        
        # 发布带检测框的图像
        self.publish_result_image(results[0].plot(), msg.header)
        
        # 更新FPS
        self.update_fps()
    
    def publish_detections(self, results, header):
        """发布检测结果到vision_msgs"""
        detection_array = Detection2DArray()
        detection_array.header = header
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # 创建检测消息
                detection = Detection2D()
                
                # 边界框
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                bbox = BoundingBox2D()
                bbox.center.position.x = (x1 + x2) / 2
                bbox.center.position.y = (y1 + y2) / 2
                bbox.size_x = x2 - x1
                bbox.size_y = y2 - y1
                detection.bbox = bbox
                
                # 置信度
                detection.confidence = float(box.conf[0].cpu().numpy())
                
                # 类别ID和名称
                cls_id = int(box.cls[0].cpu().numpy())
                detection.results.append({
                    'id': str(cls_id),
                    'score': detection.confidence
                })
                
                detection_array.detections.append(detection)
        
        self.detection_pub.publish(detection_array)
    
    def publish_result_image(self, annotated_image, header):
        """发布带检测框的图像"""
        try:
            ros_image = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
            ros_image.header = header
            self.result_image_pub.publish(ros_image)
        except Exception as e:
            self.get_logger().error(f'Failed to publish result image: {e}')
    
    def update_fps(self):
        """计算FPS"""
        self.frame_count += 1
        current_time = self.get_clock().now()
        elapsed = (current_time - self.last_time).nanoseconds / 1e9
        
        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_time = current_time
            self.get_logger().debug(f'FPS: {self.fps:.2f}')


def main(args=None):
    rclpy.init(args=args)
    node = YoloDetector()
    
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

### 4.3 目标追踪节点

```python
# yolov8_ros/yolov8_ros/yolo_tracker.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray, Detection2D, BoundingBox2D
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np

class YoloTracker(Node):
    """YOLOv8目标追踪与跟随节点"""
    
    def __init__(self):
        super().__init__('yolo_tracker')
        
        # 参数
        self.declare_parameter('model_name', 'yolov8n.pt')
        self.declare_parameter('track_class', 'person')  # 追踪类别
        self.declare_parameter('conf_threshold', 0.5)
        self.declare_parameter('enable_cuda', False)
        self.declare_parameter('follow_distance', 1.5)  # 跟随距离（米）
        self.declare_parameter('max_linear_vel', 0.5)  # 最大线速度
        self.declare_parameter('image_width', 640)
        
        self.track_class = self.get_parameter('track_class').value
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.enable_cuda = self.get_parameter('enable_cuda').value
        self.follow_distance = self.get_parameter('follow_distance').value
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.image_width = self.get_parameter('image_width').value
        
        # 加载模型
        self.get_logger().info(f'Loading model: yolov8n.pt')
        self.model = YOLO('yolov8n.pt')
        
        if self.enable_cuda:
            self.model.to('cuda')
        
        self.bridge = CvBridge()
        
        # 订阅图像
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 1)
        
        # 发布速度命令
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 发布追踪结果图像
        self.result_pub = self.create_publisher(Image, '/tracker/result', 10)
        
        # 当前追踪目标ID
        self.tracked_id = None
        
        self.get_logger().info(f'Tracking class: {self.track_class}')
    
    def image_callback(self, msg):
        """处理图像并追踪目标"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'Image convert error: {e}')
            return
        
        # 运行追踪
        results = self.model.track(cv_image, 
                                   conf=self.conf_threshold,
                                   persist=True,
                                   verbose=False)
        
        tracked_target = None
        
        for result in results:
            boxes = result.boxes
            
            if boxes.id is not None:
                for box in boxes:
                    track_id = int(box.id[0])
                    cls_id = int(box.cls[0])
                    cls_name = result.names[cls_id]
                    
                    if cls_name == self.track_class:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        
                        # 计算目标中心
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        
                        tracked_target = {
                            'id': track_id,
                            'class': cls_name,
                            'bbox': [x1, y1, x2, y2],
                            'center': [cx, cy],
                            'conf': conf
                        }
                        
                        # 更新追踪ID
                        self.tracked_id = track_id
                        break
        
        # 发布控制命令
        self.publish_cmd(tracked_target)
        
        # 发布结果图像
        if results[0].plot() is not None:
            result_img = self.bridge.cv2_to_imgmsg(
                results[0].plot(), encoding='bgr8')
            result_img.header = msg.header
            self.result_pub.publish(result_img)
    
    def publish_cmd(self, target):
        """发布速度控制命令"""
        twist = Twist()
        
        if target is None:
            # 没有追踪目标，停止
            self.cmd_pub.publish(twist)
            return
        
        cx, cy = target['center']
        
        # 计算偏离中心的程度
        center_x = self.image_width / 2
        offset_x = (cx - center_x) / center_x  # -1到1之间
        
        # 角度控制：目标偏离中心时旋转
        twist.angular.z = -offset_x * 1.0  # 比例控制
        
        # 距离控制：基于目标大小估算距离
        x1, y1, x2, y2 = target['bbox']
        target_width = x2 - x1
        expected_width = self.image_width * 0.3  # 期望的宽度比例
        
        # 如果目标太小（太远），前进；太大（太近），后退
        distance_ratio = target_width / expected_width
        
        if distance_ratio < 0.8:
            # 目标太远，前进
            twist.linear.x = min(
                self.max_linear_vel * (1 - distance_ratio),
                self.max_linear_vel
            )
        elif distance_ratio > 1.2:
            # 目标太近，后退
            twist.linear.x = -self.max_linear_vel * 0.3
        else:
            # 距离合适
            twist.linear.x = 0.0
        
        self.cmd_pub.publish(twist)
        
        self.get_logger().debug(
            f'Target: {target["class"]} ID:{target["id"]} | '
            f'Center: ({cx:.0f}, {cy:.0f}) | '
            f'Cmd: linear={twist.linear.x:.2f}, angular={twist.angular.z:.2f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = YoloTracker()
    
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

### 4.4 launch启动文件

```python
# yolov8_ros/launch/yolo_detector.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    """生成YOLO检测器启动描述"""
    
    # 模型参数
    model_name_arg = DeclareLaunchArgument(
        'model_name',
        default_value='yolov8n.pt',
        description='YOLOv8 model name (yolov8n.pt, yolov8s.pt, etc.)'
    )
    
    conf_threshold_arg = DeclareLaunchArgument(
        'conf_threshold',
        default_value='0.5',
        description='Confidence threshold'
    )
    
    iou_threshold_arg = DeclareLaunchArgument(
        'iou_threshold',
        default_value='0.45',
        description='IoU threshold for NMS'
    )
    
    enable_cuda_arg = DeclareLaunchArgument(
        'enable_cuda',
        default_value='false',
        description='Enable CUDA GPU acceleration'
    )
    
    # 检测器节点
    detector_node = Node(
        package='yolov8_ros',
        executable='yolo_detector',
        name='yolo_detector',
        output='screen',
        parameters=[{
            'model_name': LaunchConfiguration('model_name'),
            'conf_threshold': LaunchConfiguration('conf_threshold'),
            'iou_threshold': LaunchConfiguration('iou_threshold'),
            'enable_cuda': LaunchConfiguration('enable_cuda'),
        }]
    )
    
    # 追踪节点（可选）
    tracker_node = Node(
        package='yolov8_ros',
        executable='yolo_tracker',
        name='yolo_tracker',
        output='screen',
        parameters=[{
            'model_name': 'yolov8n.pt',
            'track_class': 'person',
            'conf_threshold': 0.5,
            'enable_cuda': LaunchConfiguration('enable_cuda'),
        }]
    )
    
    return LaunchDescription([
        model_name_arg,
        conf_threshold_arg,
        iou_threshold_arg,
        enable_cuda_arg,
        detector_node,
        tracker_node
    ])
```

### 4.5 运行系统

```bash
# 编译功能包
cd ~/ros2_ws
colcon build --packages-select yolov8_ros
source install/setup.bash

# 方式1：只启动检测器
ros2 launch yolov8_ros yolo_detector.launch.py

# 方式2：启动检测器+追踪器
ros2 launch yolov8_ros yolo_detector.launch.py enable_cuda:=true

# 方式3：使用自定义模型
ros2 launch yolov8_ros yolo_detector.launch.py model_name:=yolov8s.pt

# 查看话题
ros2 topic list
ros2 topic hz /yolo/detections

# 可视化检测结果（使用rviz2或image_view）
ros2 run rqt_imageview rqt_imageview /yolo/result_image
```

---

## 5. 机器人应用场景

YOLO在机器人领域有着广泛的应用，本节介绍几个典型的应用场景及其实现方法。

### 5.1 智能跟随

基于YOLO的人体检测和追踪，实现机器人的智能跟随功能：

```python
# smart_follower.py - 智能跟随节点
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np

class SmartFollower(Node):
    """基于YOLO的智能跟随节点"""
    
    def __init__(self):
        super().__init__('smart_follower')
        
        self.declare_parameter('person_class', 'person')
        self.declare_parameter('conf_threshold', 0.6)
        self.declare_parameter('follow_distance', 1.5)
        self.declare_parameter('max_linear_vel', 0.4)
        self.declare_parameter('max_angular_vel', 1.0)
        self.declare_parameter('image_width', 640)
        
        self.person_class = self.get_parameter('person_class').value
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.follow_distance = self.get_parameter('follow_distance').value
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.max_angular_vel = self.get_parameter('max_angular_vel').value
        self.image_width = self.get_parameter('image_width').value
        
        # 加载YOLOv8模型
        self.get_logger().info('Loading YOLOv8 model...')
        self.model = YOLO('yolov8n.pt')
        self.get_logger().info('Model loaded')
        
        self.bridge = CvBridge()
        
        # 订阅相机图像
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.callback, 1)
        
        # 发布速度命令
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # 追踪状态
        self.tracked_person_id = None
        self.lost_count = 0
        
        self.get_logger().info('Smart follower initialized')
    
    def callback(self, msg):
        """处理图像并进行跟随控制"""
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except:
            return
        
        # 运行检测和追踪
        results = self.model.track(frame, 
                                   conf=self.conf_threshold,
                                   persist=True,
                                   verbose=False)
        
        person_target = self.find_person(results)
        
        if person_target:
            self.lost_count = 0
            self.control_follow(person_target)
        else:
            self.lost_count += 1
            if self.lost_count > 30:  # 丢失超过30帧，停止
                self.stop_robot()
    
    def find_person(self, results):
        """从检测结果中寻找人体"""
        for result in results:
            boxes = result.boxes
            
            if boxes.id is None:
                continue
            
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                
                if cls_name == self.person_class:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    track_id = int(box.id[0])
                    
                    return {
                        'id': track_id,
                        'bbox': [x1, y1, x2, y2],
                        'center': [cx, cy]
                    }
        return None
    
    def control_follow(self, target):
        """计算并发布跟随控制命令"""
        twist = Twist()
        
        cx, cy = target['center']
        x1, y1, x2, y2 = target['bbox']
        
        # 角度控制：目标偏离中心时旋转
        center_x = self.image_width / 2
        offset_x = (cx - center_x) / center_x  # -1到1
        twist.angular.z = np.clip(-offset_x * 2.0, 
                                  -self.max_angular_vel, 
                                  self.max_angular_vel)
        
        # 距离控制：基于人体框大小估算
        person_height = y2 - y1
        expected_height = self.image_width * 0.6  # 期望高度比例
        
        distance_ratio = person_height / expected_height
        
        if distance_ratio < 0.7:  # 太远，前进
            speed = self.max_linear_vel * (0.7 - distance_ratio) * 2
            twist.linear.x = np.clip(speed, 0, self.max_linear_vel)
        elif distance_ratio > 1.0:  # 太近，后退
            twist.linear.x = -self.max_linear_vel * 0.3
        else:
            twist.linear.x = 0.0
        
        self.cmd_pub.publish(twist)
        
        self.get_logger().debug(
            f'Following ID:{target["id"]} | '
            f'Offset:{offset_x:.2f} | '
            f'Linear:{twist.linear.x:.2f} Angular:{twist.angular.z:.2f}'
        )
    
    def stop_robot(self):
        """停止机器人"""
        twist = Twist()
        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = SmartFollower()
    
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

### 5.2 安全避障

利用YOLO检测机器人前方的障碍物，实现主动避障：

```python
# obstacle_avoider.py - YOLO障碍物检测与避障
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
from ultralytics import YOLO
import numpy as np

class ObstacleAvoider(Node):
    """基于YOLO的障碍物检测与避障"""
    
    # 需要避开的类别（可自定义）
    OBSTACLE_CLASSES = ['chair', 'dining table', 'couch', 'potted plant', 
                        'bed', 'tv', 'laptop', 'bottle', 'cup']
    
    def __init__(self):
        super().__init__('obstacle_avoider')
        
        self.declare_parameter('conf_threshold', 0.5)
        self.declare_parameter('min_distance', 0.5)  # 最小安全距离（米）
        self.declare_parameter('max_linear_vel', 0.3)
        self.declare_parameter('image_width', 640)
        self.declare_parameter('image_height', 480)
        
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.min_distance = self.get_parameter('min_distance').value
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value
        
        # 加载模型
        self.model = YOLO('yolov8n.pt')
        self.bridge = CvBridge()
        
        # 订阅图像
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.callback, 1)
        
        # 发布速度
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.get_logger().info('Obstacle avoider initialized')
    
    def callback(self, msg):
        """检测障碍物并发布避障命令"""
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except:
            return
        
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        
        obstacles = self.find_obstacles(results)
        
        if obstacles:
            self.avoid_obstacles(obstacles)
        else:
            self.move_forward()
    
    def find_obstacles(self, results):
        """寻找障碍物"""
        obstacles = []
        
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                cls_name = result.names[cls_id]
                
                if cls_name in self.OBSTACLE_CLASSES:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = box.conf[0].cpu().numpy()
                    
                    # 计算位置：越靠近图像底部的物体越近
                    vertical_position = y2 / self.image_height
                    
                    obstacles.append({
                        'class': cls_name,
                        'bbox': [x1, y1, x2, y2],
                        'confidence': conf,
                        'proximity': vertical_position  # 越大越近
                    })
        
        # 按接近程度排序
        obstacles.sort(key=lambda x: x['proximity'], reverse=True)
        return obstacles
    
    def avoid_obstacles(self, obstacles):
        """避障逻辑"""
        twist = Twist()
        
        # 获取最近的障碍物
        nearest = obstacles[0]
        x1, y1, x2, y2 = nearest['bbox']
        
        # 判断障碍物位置
        center_x = (x1 + x2) / 2
        center_y = (y2 + y1) / 2
        
        # 计算障碍物相对于图像中心的偏移
        offset_x = (center_x - self.image_width / 2) / (self.image_width / 2)
        
        # 判断距离：图像下半部分且框较大表示距离近
        proximity = nearest['proximity']
        
        if proximity > 0.7:  # 非常近
            # 急停并转向
            twist.linear.x = -self.max_linear_vel * 0.5
            twist.angular.z = -np.sign(offset_x) * 1.5
            self.get_logger().warning(
                f'Very close obstacle: {nearest["class"]} - stopping and turning')
        elif proximity > 0.5:  # 中等距离
            # 减速并转向
            twist.linear.x = self.max_linear_vel * 0.3
            twist.angular.z = -offset_x * 1.0
            self.get_logger().info(
                f'Obstacle detected: {nearest["class"]} - turning')
        else:  # 较远
            # 正常速度，略微偏移
            twist.linear.x = self.max_linear_vel * 0.8
            twist.angular.z = -offset_x * 0.5
        
        self.cmd_pub.publish(twist)
    
    def move_forward(self):
        """正常前进"""
        twist = Twist()
        twist.linear.x = self.max_linear_vel
        twist.angular.z = 0.0
        self.cmd_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoider()
    
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

### 5.3 场景识别

利用YOLO进行场景识别，为机器人导航提供语义信息：

```python
# scene_recognizer.py - 场景识别节点
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO
from collections import Counter

class SceneRecognizer(Node):
    """基于YOLO的场景识别"""
    
    # 场景定义：类别组合对应场景
    SCENE_PATTERNS = {
        'living_room': ['couch', 'tv', 'remote', 'chair', 'book'],
        'kitchen': ['bowl', 'cup', 'bottle', 'fork', 'knife', 'spoon', 'sink'],
        'office': ['laptop', 'keyboard', 'mouse', 'monitor', 'book'],
        'bedroom': ['bed', 'pillow', 'lamp', 'book'],
        'outdoor': ['person', 'bicycle', 'car', 'dog', 'cat', 'tree']
    }
    
    def __init__(self):
        super().__init__('scene_recognizer')
        
        self.declare_parameter('conf_threshold', 0.4)
        self.declare_parameter('history_size', 10)  # 滑动窗口大小
        
        self.conf_threshold = self.get_parameter('conf_threshold').value
        self.history_size = self.get_parameter('history_size').value
        
        # 加载模型
        self.model = YOLO('yolov8n.pt')
        self.bridge = CvBridge()
        
        # 订阅图像
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.callback, 1)
        
        # 发布场景结果
        self.scene_pub = self.create_publisher(String, '/scene/recognized', 10)
        
        # 历史记录
        self.scene_history = []
        
        self.get_logger().info('Scene recognizer initialized')
    
    def callback(self, msg):
        """识别场景"""
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except:
            return
        
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        
        # 统计检测到的物体
        detected_objects = []
        for result in results:
            for box in result.boxes:
                cls_name = result.names[int(box.cls[0])]
                detected_objects.append(cls_name)
        
        # 识别场景
        scene = self.recognize_scene(detected_objects)
        
        # 更新历史并发布
        self.scene_history.append(scene)
        if len(self.scene_history) > self.history_size:
            self.scene_history.pop(0)
        
        # 发布最可能的场景
        final_scene = self.get_most_likely_scene()
        scene_msg = String()
        scene_msg.data = final_scene
        self.scene_pub.publish(scene_msg)
        
        self.get_logger().debug(f'Recognized scene: {final_scene}')
    
    def recognize_scene(self, objects):
        """根据检测到的物体识别场景"""
        object_set = set(objects)
        
        max_score = 0
        best_scene = 'unknown'
        
        for scene_name, scene_objects in self.SCENE_PATTERNS.items():
            # 计算匹配度
            matches = len(object_set.intersection(scene_objects))
            if matches > max_score:
                max_score = matches
                best_scene = scene_name
        
        return best_scene
    
    def get_most_likely_scene(self):
        """从历史记录中获取最可能的场景"""
        if not self.scene_history:
            return 'unknown'
        
        counter = Counter(self.scene_history)
        return counter.most_common(1)[0][0]


def main(args=None):
    rclpy.init(args=args)
    node = SceneRecognizer()
    
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

---

## 6. 练习题

### 选择题

1. YOLOv8相比YOLOv5的主要改进不包括以下哪项？
   - A) 采用解耦检测头（Decoupled Head）
   - B) 引入Anchor-Free设计
   - C) 使用更强的Backbone Darknet-104
   - D) 采用C2f模块替代C3模块

   **答案：C**。YOLOv8使用CSPDarknet53作为Backbone，与v5相同，并非Darknet-104。其他选项都是v8的改进。

2. 在YOLOv8的损失函数中，$\\mathcal{L}_{CIoU}$用于优化什么？
   - A) 分类精度
   - B) 边界框回归
   - C) 模型收敛速度
   - D) 数据增强效果

   **答案：B**。CIoU（Complete IoU）损失用于优化边界框的回归，直接影响定位精度。

3. 在ROS2中集成YOLOv8时，以下哪个话题类型最合适用于发布检测结果？
   - A) `sensor_msgs/Image`
   - B) `vision_msgs/Detection2DArray`
   - C) `std_msgs/String`
   - D) `geometry_msgs/Twist`

   **答案：B**。`vision_msgs/Detection2DArray`是专门用于发布目标检测结果的消息类型，包含边界框、置信度、类别等信息。

4. YOLOv8的Anchor-Free设计意味着什么？
   - A) 不需要任何边界框信息
   - B) 每个位置直接预测目标，无需预定义anchor
   - C) 不再使用NMS后处理
   - D) 只适用于特定类别检测

   **答案：B**。Anchor-Free设计摒弃了预定义的anchor boxes，模型直接预测每个位置的目标存在性和边界框参数，简化了模型并提高了泛化能力。

### 实践题

5. 编写一个ROS2节点，使用YOLOv8检测人体，并发布人体中心点在图像中的像素坐标到话题`/person/position`。

   **参考答案**：
   
   ```python
   import rclpy
   from rclpy.node import Node
   from sensor_msgs.msg import Image
   from geometry_msgs.msg import Point
   from cv_bridge import CvBridge
   from ultralytics import YOLO
   
   class PersonPositionPublisher(Node):
       def __init__(self):
           super().__init__('person_position_publisher')
           self.model = YOLO('yolov8n.pt')
           self.bridge = CvBridge()
           
           self.image_sub = self.create_subscription(
               Image, '/camera/image_raw', self.callback, 1)
           
           self.position_pub = self.create_publisher(Point, '/person/position', 10)
           
           self.get_logger().info('Person position publisher started')
       
       def callback(self, msg):
           try:
               frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
           except:
               return
           
           results = self.model(frame, verbose=False)
           
           for result in results:
               for box in result.boxes:
                   if result.names[int(box.cls[0])] == 'person':
                       x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                       cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                       
                       point = Point()
                       point.x = float(cx)
                       point.y = float(cy)
                       point.z = float(box.conf[0].cpu().numpy())
                       
                       self.position_pub.publish(point)
   
   def main(args=None):
       rclpy.init(args=args)
       node = PersonPositionPublisher()
       rclpy.spin(node)
       node.destroy_node()
       rclpy.shutdown()
   
   if __name__ == '__main__':
       main()
   ```

6. 修改YOLO追踪节点，实现对特定类别的多目标追踪，并在终端打印每个追踪目标的ID、类别和位置。

   **提示**：
   - 使用`model.track()`的`persist=True`参数保持追踪ID
   - 检查`boxes.id`是否为None来判断是否有追踪ID
   - 根据类别名称过滤感兴趣的目标

---

## 本章小结

本章系统学习了YOLO系列的发展历程和YOLOv8的核心技术：

1. **YOLO系列发展**：从YOLOv1的单次检测理念，到v4/v7的工程化改进，再到v8的集大成之作。
2. **YOLOv8架构**：Backbone的C2f模块、Neck的PAFPN特征融合、Head的解耦设计，以及Anchor-Free的创新。
3. **多目标检测实战**：图片检测、视频检测、目标追踪和自定义数据集训练的完整流程。
4. **ROS2集成**：YOLOv8检测节点、追踪节点和launch文件的完整实现。
5. **机器人应用场景**：智能跟随、安全避障和场景识别三个典型应用。
6. **练习题**：选择题和实践题帮助巩固所学知识。

YOLO作为当前最流行的目标检测算法，在机器人领域有着广阔的应用前景。掌握YOLOv8的原理和ROS2集成方法，将为你开发智能机器人应用打下坚实基础。

---

## 参考资料

### YOLO官方资源

1. Ultralytics YOLOv8: <https://docs.ultralytics.com/>
2. YOLOv8 GitHub: <https://github.com/ultralytics/ultralytics>
3. YOLO Model Zoo: <https://docs.ultralytics.com/models/>

### ROS2集成

4. vision_msgs文档: <https://github.com/ros-perception/vision_msgs>
5. cv_bridge文档: <https://wiki.ros.org/cv_bridge>
6. ROS2 Launch文档: <https://docs.ros.org/en/humble/Tutorials/Launching-Tasks.html>

### 目标检测进阶

7. CIoU Loss论文: <https://arxiv.org/abs/1911.08287>
8. Focal Loss: <https://arxiv.org/abs/1708.02002>
9.anchor-Free目标检测综述: <https://arxiv.org/abs/2109.14322>

---

## 下节预告

恭喜你完成了**计算机视觉应用**模块的全部课程！从颜色识别、人脸检测、人体识别、目标追踪、图像分割到YOLO综合应用，你已经掌握了机器人视觉的核心技术。接下来可以继续学习其他模块，或将所学知识应用于实际项目中。

---

*本章学习完成！YOLO是计算机视觉的利器，建议大家多多实践，探索更多有趣的应用！*
"
