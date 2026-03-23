# 10-7 Segment Anything Model 及应用

> **前置课程**：10-5 图像分割及应用
> **后续课程**：10-8 单目深度估计及应用

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：SAM（Segment Anything Model）是由 Meta AI 于 2023 年发布的革命性图像分割模型，它首次实现了"万物可分割"的目标——通过灵活的提示词（点、框、文本）可以对图像中的任意目标进行分割，无需重新训练。本节将深入讲解 SAM 的模型原理、提示词分割机制，并演示如何在 ROS2 中集成 SAM 实现机器人视觉应用。

---

## 1. SAM 概述

### 1.1 什么是 SAM

Segment Anything Model（SAM）是 Meta AI 在 2023 年发布的第一个图像分割基础模型。与传统分割模型不同，SAM 能够根据用户的提示词（Prompt）对图像中的任意目标进行分割，实现了"万物皆可分割"（Segment Anything）的目标。

SAM 的核心创新在于：
- **提示词驱动**：通过点、框、文本等提示词指定分割目标，无需针对特定类别训练
- **强大泛化能力**：基于超大规模数据集（1100万张图像，10亿个掩膜）训练，泛化能力极强
- **实时分割**：优化后的模型可在浏览器中实时运行

### 1.2 SAM 的应用场景

SAM 在机器人领域有广泛应用：
- **工业分拣**：通过框选或点击指定待分拣物体，无需重新训练即可分割新类别
- **场景理解**：快速分割室内外场景中的各种物体，构建语义地图
- **抓取检测**：结合 SAM 的实例分割结果，计算机器人抓取点
- **医学图像**：辅助医生标注医学影像中的感兴趣区域

---

## 2. SAM 模型原理

### 2.1 SAM 整体架构

SAM 的整体架构包含三个核心组件：图像编码器（Image Encoder）、提示词编码器（Prompt Encoder）和掩膜解码器（Mask Decoder）。

```
输入图像 ──▶ 图像编码器 ──┐
                        ├──▶ 掩膜解码器 ──▶ 分割掩膜
点/框/文本 ──▶ 提示词编码器 ──┘
```

**图像编码器**：使用预训练的 MAE（Masked Autoencoder）ViT（Vision Transformer）模型，将输入图像编码为密集的特征图。

**提示词编码器**：将点、框、文本等提示词编码为相应的特征表示。

**掩膜解码器**：根据图像特征和提示词特征，生成目标掩膜。

### 2.2 图像编码器

SAM 使用 ViT-H（Vision Transformer Large）作为图像编码器，输入图像被分割为 16×16 的 patches，经过多层 Transformer 编码后输出密集特征图。

设输入图像为 $I \in \mathbb{R}^{H \times W \times 3}$，图像编码器输出特征图：
$$F = \text{ImageEncoder}(I), \quad F \in \mathbb{R}^{H/16 \times W/16 \times D}$$

其中 $D=1280$ 是特征维度。

### 2.3 提示词编码器

SAM 支持三种类型的提示词：

**点提示词（Point Prompt）**：
- 包括前景点和背景点
- 每个点用位置编码和标签（前/后景）表示
- 点特征与对应位置的特征图位置相加

**框提示词（Box Prompt）**：
- 由左上角和右下角坐标定义
- 通过两个点的位置编码和角点嵌入表示
- 使用 Bounding Box Embedding 表示

**文本提示词（Text Prompt）**：
- 使用 CLIP（Contrastive Language-Image Pre-Training）文本编码器
- 将文本提示词编码为文本特征向量
- 支持自由文本描述分割目标

### 2.4 掩膜解码器

掩膜解码器是一个轻量级的 Transformer 网络，根据图像特征和提示词特征生成分割掩膜。

解码器包含多层自注意力和交叉注意力模块：
- **自注意力（Self-Attention）**：在图像特征上进行全局推理
- **交叉注意力（Cross-Attention）**：在图像特征和提示词特征之间进行交互

最终输出三个掩膜预测：
$$M_1, M_2, M_3 = \text{MaskDecoder}(F, P)$$

其中 $M_i \in \mathbb{R}^{H \times W}$ 是三个不同 IoU 阈值下的掩膜预测。SAM 同时输出三个预测是为了处理歧义性（ambiguous）情况，选择最高质量的掩膜作为最终输出。

### 2.5 歧义性处理

SAM 引入了"歧义性感知"（Ambiguity-Aware）设计，当提示词对应多个可能的分割目标时，模型同时输出多个候选掩膜。这一设计使 SAM 能够处理复杂场景中的歧义情况。

---

## 3. SAM 的三种使用模式

### 3.1 自动分割（Automatic Segmentation）

在自动分割模式下，SAM 会分割图像中的所有显著物体，无需任何提示词。这通过在网格上采样点，对每个点生成掩膜，然后进行后处理（去除重叠和冗余掩膜）实现。

### 3.2 点提示分割（Point Prompt Segmentation）

用户可以通过点击前景点或背景点指定分割目标：
- **前景点**：标记要分割的物体
- **背景点**：标记不要包含在分割结果中的区域

SAM 根据点的位置和标签，从图像特征中提取对应区域的特征，生成目标掩膜。

### 3.3 框提示分割（Box Prompt Segmentation）

用户可以通过绘制边界框指定分割目标，SAM 会分割框内的主要物体。这种方式比点提示更精确，适用于目标边界清晰的情况。

### 3.4 文本提示分割（Text Prompt Segmentation）

SAM 支持通过文本描述指定分割目标，例如"person"、"car"等。使用 CLIP 文本编码器将文本映射到特征空间，然后根据文本和图像特征的相似度生成分割掩膜。

---

## 4. SAM Python 实现

### 4.1 环境配置

SAM 可以通过 pip 安装：

```bash
pip install segment-anything
```

或者使用 PyTorch Hub 加载：

```python
import torch
torch.hub.load('facebookresearch/sam', 'sam_vit_h_4b8939')
```

### 4.2 SAM 基础使用

```python
import torch
import cv2
import numpy as np
from segment_anything import sam_model_registry, SamPredictor


def init_sam():
    """初始化SAM模型"""
    # 使用ViT-H模型（最大、最准确的版本）
    sam_checkpoint = "sam_vit_h_4b8939.pth"
    model_type = "vit_h"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # 注册模型
    sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam.to(device=device)
    
    # 创建预测器
    predictor = SamPredictor(sam)
    
    return predictor, device


def segment_from_point(predictor, image, point_coords, point_labels):
    """
    基于点提示词进行分割
    
    参数:
        predictor: SAM预测器
        image: 输入图像 (H, W, 3)
        point_coords: 点坐标，形状为 (N, 2)，列对应 x, y
        point_labels: 点标签，1表示前景，0表示背景
    
    返回:
        mask: 分割掩膜 (H, W)
        score: 置信度分数
    """
    # 设置图像
    predictor.set_image(image)
    
    # 点提示词分割
    masks, scores, logits = predictor.predict(
        point_coords=point_coords,
        point_labels=point_labels,
        multimask_output=True  # 输出多个候选掩膜
    )
    
    # 选择得分最高的掩膜
    best_mask = masks[np.argmax(scores)]
    best_score = np.max(scores)
    
    return best_mask, best_score


def segment_from_box(predictor, image, box):
    """
    基于框提示词进行分割
    
    参数:
        predictor: SAM预测器
        image: 输入图像 (H, W, 3)
        box: 边界框 [x_min, y_min, x_max, y_max]
    
    返回:
        mask: 分割掩膜 (H, W)
    """
    predictor.set_image(image)
    
    masks, scores, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        box=np.array(box),
        multimask_output=False  # 框提示不需要多输出
    )
    
    return masks[0], scores[0]


def automatic_segmentation(predictor, image):
    """
    自动分割图像中的所有物体
    
    参数:
        predictor: SAM预测器
        image: 输入图像 (H, W, 3)
    
    返回:
        masks: 所有分割掩膜列表
    """
    from segment_anything import SamAutomaticMaskGenerator
    
    # 创建自动分割生成器
    mask_generator = SamAutomaticMaskGenerator(predictor.model)
    
    # 生成所有掩膜
    anns = mask_generator.generate(image)
    
    # 提取掩膜
    masks = [ann['segmentation'] for ann in anns]
    
    return masks, anns


if __name__ == "__main__":
    # 初始化
    predictor, device = init_sam()
    print(f"使用设备: {device}")
    
    # 读取图像
    image = cv2.imread("test_image.jpg")
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 点提示分割示例
    point_coords = np.array([[200, 300]])  # 点击位置的坐标
    point_labels = np.array([1])  # 1表示前景点
    
    mask, score = segment_from_point(predictor, image, point_coords, point_labels)
    print(f"点提示分割 - 得分: {score:.3f}")
    
    # 框提示分割示例
    box = [100, 100, 400, 400]  # [x_min, y_min, x_max, y_max]
    mask, score = segment_from_box(predictor, image, box)
    print(f"框提示分割 - 得分: {score:.3f}")
```

### 4.3 批量分割与后处理

```python
import numpy as np
import cv2
from segment_anything import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator


class SAMSegmentor:
    """SAM分割封装类"""
    
    def __init__(self, model_type="vit_h", checkpoint_path=None, device=None):
        """
        初始化SAM分割器
        
        参数:
            model_type: 模型类型，vit_h/vit_l/vit_b
            checkpoint_path: 模型权重路径
            device: 计算设备
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        if checkpoint_path:
            sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
        else:
            # 使用PyTorch Hub加载
            sam = torch.hub.load('facebookresearch/sam', model_type)
        
        sam.to(device=self.device)
        sam.eval()
        
        self.predictor = SamPredictor(sam)
        self.mask_generator = SamAutomaticMaskGenerator(sam)
    
    def segment_single_point(self, image, x, y, foreground=True):
        """
        单点分割
        
        参数:
            image: RGB图像
            x, y: 点击坐标
            foreground: True为前景点，False为背景点
        
        返回:
            mask: 二值掩膜
        """
        point_coords = np.array([[x, y]])
        point_labels = np.array([1 if foreground else 0])
        
        self.predictor.set_image(image)
        masks, scores, _ = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=True
        )
        
        return masks[np.argmax(scores)], np.max(scores)
    
    def segment_multiple_points(self, image, points, labels):
        """
        多点分割
        
        参数:
            image: RGB图像
            points: 点坐标列表 [(x1,y1), (x2,y2), ...]
            labels: 点标签列表 [1, 0, ...] (1前景，0背景)
        
        返回:
            mask: 二值掩膜
        """
        point_coords = np.array(points)
        point_labels = np.array(labels)
        
        self.predictor.set_image(image)
        masks, scores, _ = self.predictor.predict(
            point_coords=point_coords,
            point_labels=point_labels,
            multimask_output=True
        )
        
        return masks[np.argmax(scores)], np.max(scores)
    
    def segment_box(self, image, box):
        """
        框分割
        
        参数:
            image: RGB图像
            box: [x_min, y_min, x_max, y_max]
        
        返回:
            mask: 二值掩膜
        """
        self.predictor.set_image(image)
        masks, scores, _ = self.predictor.predict(
            point_coords=None,
            point_labels=None,
            box=np.array(box),
            multimask_output=False
        )
        
        return masks[0], scores[0]
    
    def segment_all_objects(self, image, min_area=1000):
        """
        自动分割所有物体
        
        参数:
            image: RGB图像
            min_area: 最小连通区域面积阈值
        
        返回:
            masks: 掩膜列表
            annotations: 包含边界框、面积等信息的注解列表
        """
        anns = self.mask_generator.generate(image)
        
        # 按面积降序排序
        anns = sorted(anns, key=lambda x: x['area'], reverse=True)
        
        # 过滤小目标
        anns = [ann for ann in anns if ann['area'] >= min_area]
        
        masks = [ann['segmentation'] for ann in anns]
        
        return masks, anns
    
    def segment_with_text(self, image, text, clip_model, clip_processor):
        """
        使用CLIP文本提示进行分割
        
        参数:
            image: RGB图像
            text: 文本描述，如"person", "car"
            clip_model: CLIP模型
            clip_processor: CLIP处理器
        
        返回:
            masks: 分割掩膜列表
        """
        # 使用CLIP编码文本
        text_inputs = clip_processor(text=text, return_tensors="pt").to(self.device)
        text_features = clip_model.get_text_features(**text_inputs)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        
        # 获取图像特征
        self.predictor.set_image(image)
        image_features = self.predictor.features
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        # 计算相似度
        similarity = (image_features @ text_features.T).squeeze()
        
        # 使用相似度图引导分割
        # 这里简化处理，实际应用中可能需要更复杂的策略
        return similarity.cpu().numpy()


def visualize_masks(image, masks, anns=None, alpha=0.5):
    """
    可视化分割结果
    
    参数:
        image: RGB图像
        masks: 掩膜列表
        anns: 注解列表（可选）
        alpha: 叠加透明度
    
    返回:
        colored_mask: 带掩膜颜色的图像
    """
    h, w = image.shape[:2]
    colored = image.copy()
    
    # 为每个掩膜分配随机颜色
    colors = np.random.randint(0, 255, size=(len(masks), 3), dtype=np.uint8)
    
    for i, mask in enumerate(masks):
        color = colors[i]
        
        # 创建彩色掩膜
        colored_mask = np.zeros_like(image)
        colored_mask[mask] = color
        
        # 叠加到原图
        colored = cv2.addWeighted(colored, 1, colored_mask, alpha, 0)
        
        # 绘制边界
        contours, _ = cv2.findContours(
            mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        cv2.drawContours(colored, contours, -1, tuple(map(int, color)), 2)
        
        # 绘制边界框（如果有）
        if anns is not None and i < len(anns):
            bbox = anns[i]['bbox']
            x, y, w, h = bbox
            cv2.rectangle(colored, (x, y), (x+w, y+h), tuple(map(int, color)), 2)
    
    return colored


if __name__ == "__main__":
    import torch
    
    # 初始化分割器（需要先下载模型权重）
    # checkpoint = "sam_vit_h_4b8939.pth"
    # segmentor = SAMSegmentor(model_type="vit_h", checkpoint_path=checkpoint)
    
    print("SAM分割器类定义完成")
    print("提示：请从 https://github.com/facebookresearch/segment-anything 下载模型权重")
```

---

## 5. SAM 模型对比与选择

SAM 提供了三种规模的模型，用户可以根据精度和速度需求进行选择：

| 模型 | 参数量 | 编码器速度 | 掩膜质量 | 适用场景 |
|------|--------|-----------|---------|---------|
| ViT-H | 636M | 较慢 | 最高 | 高精度服务器部署 |
| ViT-L | 308M | 中等 | 高 | 桌面端实时应用 |
| ViT-B | 94M | 较快 | 中等 | 边缘设备、实时应用 |

对于机器人实时应用，推荐使用 ViT-B 模型以获得更好的实时性。

---

## 6. ROS2 集成与机器人应用

### 6.1 SAM ROS2 节点架构

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   相机驱动节点   │ ────▶│   SAM 分割节点   │ ────▶│  机器人控制节点  │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   可视化节点     │
                        └─────────────────┘
```

### 6.2 SAM 分割节点实现

```python
# sam_segmentation_node.py - ROS2 SAM 分割节点
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField
from geometry_msgs.msg import Point
from vision_msgs.msg import Detection2DArray, BoundingBox2D
from cv_bridge import CvBridge
import numpy as np
import torch
import cv2


class SAMSegmentationNode(Node):
    """ROS2 SAM 分割节点"""
    
    def __init__(self):
        super().__init__('sam_segmentation_node')
        
        self.bridge = CvBridge()
        
        # 初始化设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.get_logger().info(f"使用设备: {self.device}")
        
        # 加载 SAM 模型
        self._load_model()
        
        # 订阅图像话题
        self.image_sub = self.create_subscription(
            Image,
            'input_image',
            self.image_callback,
            10
        )
        
        # 订阅点击点话题（用于点提示分割）
        self.click_sub = self.create_subscription(
            Point,
            'click_point',
            self.click_callback,
            10
        )
        
        # 发布分割结果
        self.mask_pub = self.create_publisher(Image, 'segmentation_mask', 10)
        self.result_pub = self.create_publisher(
            Detection2DArray, 'segmentation_detections', 10
        )
        
        # 存储最新图像和点击点
        self.current_image = None
        self.current_points = []
        self.current_labels = []
        
        self.get_logger().info('SAM 分割节点已启动')
        self.get_logger().info('提示：发布点击点到 /click_point 话题进行点提示分割')
    
    def _load_model(self):
        """加载 SAM 模型"""
        try:
            from segment_anything import sam_model_registry, SamPredictor
            
            # 模型配置（根据实际下载的模型选择）
            model_type = "vit_h"
            checkpoint_path = "/path/to/sam_vit_h_4b8939.pth"
            
            # 尝试加载本地模型，如果没有则下载
            try:
                sam = sam_model_registry[model_type](checkpoint=checkpoint_path)
            except FileNotFoundError:
                self.get_logger().warn("本地模型未找到，使用 PyTorch Hub 加载")
                sam = torch.hub.load(
                    'facebookresearch/sam', 
                    'sam_vit_h_4b8939',
                    pretrained=True
                )
            
            sam.to(device=self.device)
            sam.eval()
            
            self.predictor = SamPredictor(sam)
            self.get_logger().info('SAM 模型加载成功')
            
        except ImportError:
            self.get_logger().error(
                "segment_anything 未安装，请运行: pip install segment-anything"
            )
            self.predictor = None
    
    def segment_with_points(self, image, points, labels):
        """
        使用点提示词进行分割
        
        参数:
            image: BGR 图像
            points: 点坐标列表 [(x1,y1), (x2,y2), ...]
            labels: 标签列表 [1, 0, ...] (1前景，0背景)
        
        返回:
            mask: 二值掩膜
            score: 置信度分数
        """
        if self.predictor is None:
            return None, 0.0
        
        # 转换为 RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 设置图像
        self.predictor.set_image(image_rgb)
        
        # 预测
        masks, scores, _ = self.predictor.predict(
            point_coords=np.array(points),
            point_labels=np.array(labels),
            multimask_output=True
        )
        
        return masks[np.argmax(scores)], np.max(scores)
    
    def segment_with_box(self, image, box):
        """
        使用框提示词进行分割
        
        参数:
            image: BGR 图像
            box: [x_min, y_min, x_max, y_max]
        
        返回:
            mask: 二值掩膜
            score: 置信度分数
        """
        if self.predictor is None:
            return None, 0.0
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        self.predictor.set_image(image_rgb)
        masks, scores, _ = self.predictor.predict(
            point_coords=None,
            point_labels=None,
            box=np.array(box),
            multimask_output=False
        )
        
        return masks[0], scores[0]
    
    def auto_segment(self, image):
        """
        自动分割所有物体
        
        参数:
            image: BGR 图像
        
        返回:
            masks: 掩膜列表
            anns: 注解列表
        """
        from segment_anything import SamAutomaticMaskGenerator
        
        if self.predictor is None:
            return [], []
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        mask_generator = SamAutomaticMaskGenerator(self.predictor.model)
        anns = mask_generator.generate(image_rgb)
        
        masks = [ann['segmentation'] for ann in anns]
        
        return masks, anns
    
    def click_callback(self, msg):
        """点击点回调"""
        x, y = int(msg.x), int(msg.y)
        
        # 切换标签（奇数次点击为前景，偶数次为背景）
        is_foreground = len(self.current_points) % 2 == 0
        
        self.current_points.append([x, y])
        self.current_labels.append(1 if is_foreground else 0)
        
        self.get_logger().info(
            f"收到点击点: ({x}, {y}), 标签: {'前景' if is_foreground else '背景'}"
        )
        
        # 如果有图像，则执行分割
        if self.current_image is not None:
            self._perform_segmentation()
    
    def _perform_segmentation(self):
        """执行分割"""
        if len(self.current_points) < 1:
            return
        
        mask, score = self.segment_with_points(
            self.current_image, self.current_points, self.current_labels
        )
        
        if mask is not None:
            # 发布掩膜
            mask_msg = self.bridge.cv2_to_imgmsg(
                (mask * 255).astype(np.uint8), encoding='mono8'
            )
            mask_msg.header.stamp = self.get_clock().now().to_msg()
            self.mask_pub.publish(mask_msg)
            
            self.get_logger().info(f"分割完成，得分: {score:.3f}")
    
    def image_callback(self, msg):
        """图像回调"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.current_image = cv_image
            
            # 自动分割模式（如果配置启用）
            # masks, anns = self.auto_segment(cv_image)
            
        except Exception as e:
            self.get_logger().error(f'图像处理失败: {str(e)}')


def main(args=None):
    rclpy.init(args=args)
    node = SAMSegmentationNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 6.3 机器人抓取应用

```python
# sam_grasp_node.py - SAM 辅助的机器人抓取节点
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Point, PointStamped
from visualization_msgs.msg import Marker, MarkerArray
from cv_bridge import CvBridge
import numpy as np
import cv2


class SAMGraspNode(Node):
    """基于 SAM 的机器人抓取节点"""
    
    def __init__(self):
        super().__init__('sam_grasp_node')
        self.bridge = CvBridge()
        
        # 图像订阅
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10
        )
        
        # 点击点订阅
        self.click_sub = self.create_subscription(
            Point, '/click_point', self.click_callback, 10
        )
        
        # 抓取点发布
        self.grasp_pub = self.create_publisher(MarkerArray, '/grasp/markers', 10)
        self.grasp_point_pub = self.create_publisher(
            PointStamped, '/grasp/point', 10
        )
        
        # 分割掩膜发布
        self.mask_pub = self.create_publisher(Image, '/grasp/mask', 10)
        
        self.current_image = None
        self.click_points = []
        self.click_labels = []
        
        self.get_logger().info('SAM 抓取节点已启动')
        self.get_logger().info('提示：点击图像中的物体进行抓取点计算')
    
    def load_sam(self):
        """加载 SAM 模型"""
        import torch
        try:
            from segment_anything import sam_model_registry, SamPredictor
            
            sam = torch.hub.load(
                'facebookresearch/sam', 
                'sam_vit_b_4b8939',  # 使用较小的 ViT-B 模型
                pretrained=True
            )
            sam.to('cuda' if torch.cuda.is_available() else 'cpu')
            sam.eval()
            
            return SamPredictor(sam)
        except Exception as e:
            self.get_logger().error(f"SAM 模型加载失败: {e}")
            return None
    
    def image_callback(self, msg):
        """图像回调"""
        self.current_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
    
    def click_callback(self, msg):
        """点击点回调"""
        x, y = int(msg.x), int(msg.y)
        is_foreground = len(self.click_points) % 2 == 0
        
        self.click_points.append([x, y])
        self.click_labels.append(1 if is_foreground else 0)
        
        self.get_logger().info(
            f"点击点: ({x}, {y}), {'前景' if is_foreground else '背景'}"
        )
        
        if len(self.click_points) >= 1:
            self.compute_grasp_point()
    
    def compute_grasp_point(self):
        """计算抓取点"""
        if self.predictor is None or self.current_image is None:
            return
        
        image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        
        self.predictor.set_image(image_rgb)
        masks, scores, _ = self.predictor.predict(
            point_coords=np.array(self.click_points),
            point_labels=np.array(self.click_labels),
            multimask_output=True
        )
        
        mask = masks[np.argmax(scores)]
        
        # 发布掩膜
        mask_msg = self.bridge.cv2_to_imgmsg(
            (mask * 255).astype(np.uint8), encoding='mono8'
        )
        self.mask_pub.publish(mask_msg)
        
        # 计算抓取点（掩膜中心）
        ys, xs = np.where(mask)
        if len(xs) > 0 and len(ys) > 0:
            cx, cy = int(np.mean(xs)), int(np.mean(ys))
            
            # 发布抓取点
            grasp_point = PointStamped()
            grasp_point.header.stamp = self.get_clock().now().to_msg()
            grasp_point.header.frame_id = 'camera_link'
            grasp_point.point.x = cx * 0.001  # 假设像素坐标到米的转换
            grasp_point.point.y = cy * 0.001
            grasp_point.point.z = 0.0
            self.grasp_point_pub.publish(grasp_point)
            
            # 发布可视化标记
            self.publish_grasp_marker(cx, cy)
    
    def publish_grasp_marker(self, cx, cy):
        """发布抓取点标记"""
        marker = Marker()
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.header.frame_id = 'camera_link'
        marker.type = Marker.SPHERE
        marker.action = Marker.ADD
        marker.pose.position.x = cx * 0.001
        marker.pose.position.y = cy * 0.001
        marker.pose.position.z = 0.0
        marker.scale.x = 0.03
        marker.scale.y = 0.03
        marker.scale.z = 0.03
        marker.color.r = 1.0
        marker.color.g = 0.0
        marker.color.b = 0.0
        marker.color.a = 1.0
        
        marker_array = MarkerArray()
        marker_array.markers.append(marker)
        self.grasp_pub.publish(marker_array)
    
    def destroy_node(self):
        self.get_logger().info('SAM 抓取节点已关闭')
        super().destroy_node()


if __name__ == '__main__':
    rclpy.init(args=None)
    node = SAMGraspNode()
    
    # 加载 SAM
    node.predictor = node.load_sam()
    
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
```

### 6.4 运行系统

```bash
# 编译功能包
cd ~/ros2_ws
colcon build --packages-select sam_segmentation
source install/setup.bash

# 启动相机
ros2 run v4l2_camera v4l2_camera_node

# 启动 SAM 分割节点
ros2 run sam_segmentation sam_segmentation_node

# 查看分割结果
ros2 run rqt_image_view rqt_image_view
# 选择话题: /segmentation_mask
```

---

## 7. 练习题

### 选择题

1. SAM（Segment Anything Model）的核心创新是什么？
   - A) 使用卷积神经网络进行分割
   - B) 通过提示词实现任意目标的分割
   - C) 实时目标跟踪
   - D) 3D 场景重建
   
   **答案：B**。SAM 的核心创新是通过灵活的提示词（点、框、文本）实现任意目标的分割，无需针对特定类别重新训练。

2. SAM 的图像编码器使用的是什么架构？
   - A) ResNet
   - B) VGG
   - C) Vision Transformer (ViT)
   - D) MobileNet
   
   **答案：C**。SAM 使用预训练的 MAE ViT（Vision Transformer）作为图像编码器。

3. 在 SAM 的点提示词分割中，label=1 和 label=0 分别表示什么？
   - A) label=1 表示背景点，label=0 表示前景点
   - B) label=1 表示前景点，label=0 表示背景点
   - C) 两者都表示前景点
   - D) 两者都表示背景点
   
   **答案：B**。在 SAM 中，label=1 表示前景点（要分割的物体），label=0 表示背景点（不要包含的区域）。

4. SAM 三种模型规模中，哪个精度最高但速度最慢？
   - A) ViT-B
   - B) ViT-L
   - C) ViT-H
   - D) 三者精度相同
   
   **答案：C**。ViT-H 是最大规模的模型，参数量最大，精度最高，但速度最慢；ViT-B 最小，速度最快，适合实时应用。

### 实践题

5. 使用 SAM 实现一个交互式分割工具，用户可以多次点击添加前景点和背景点，并实时更新分割结果。
   
   **参考答案**：
   
   ```python
   import cv2
   import numpy as np
   import torch
   from segment_anything import sam_model_registry, SamPredictor
   
   class InteractiveSegmentor:
       """交互式分割工具"""
       
       def __init__(self, model_type="vit_h", checkpoint=None):
           sam = sam_model_registry[model_type](checkpoint=checkpoint)
           sam.to(device="cuda" if torch.cuda.is_available() else "cpu")
           sam.eval()
           self.predictor = SamPredictor(sam)
           
           self.points = []
           self.labels = []
           self.current_mask = None
   
       def mouse_callback(self, event, x, y, flags, param):
           """鼠标回调"""
           if event == cv2.EVENT_LBUTTONDOWN:
               self.points.append([x, y])
               self.labels.append(1)  # 左键：前景点
               self.update_mask()
           elif event == cv2.EVENT_RBUTTONDOWN:
               self.points.append([x, y])
               self.labels.append(0)  # 右键：背景点
               self.update_mask()
           elif event == cv2.EVENT_MBUTTONDOWN:
               self.reset()
   
       def reset(self):
           """重置"""
           self.points = []
           self.labels = []
           self.current_mask = None
   
       def update_mask(self):
           """更新分割掩膜"""
           if len(self.points) == 0:
               return
           
           masks, scores, _ = self.predictor.predict(
               point_coords=np.array(self.points),
               point_labels=np.array(self.labels),
               multimask_output=True
           )
           self.current_mask = masks[np.argmax(scores)]
   
       def run(self, image):
           """运行交互式分割"""
           self.predictor.set_image(image)
           
           window_name = "SAM Interactive Segmentation"
           cv2.namedWindow(window_name)
           cv2.setMouseCallback(window_name, self.mouse_callback)
           
           while True:
               display = image.copy()
               
               # 绘制点击点
               for i, (pt, label) in enumerate(zip(self.points, self.labels)):
                   color = (0, 255, 0) if label == 1 else (0, 0, 255)
                   cv2.circle(display, tuple(pt), 5, color, -1)
               
               # 绘制分割掩膜
               if self.current_mask is not None:
                   mask_overlay = np.zeros_like(image)
                   mask_overlay[self.current_mask] = [0, 255, 0, 128]
                   display = cv2.addWeighted(display, 1, mask_overlay, 0.5, 0)
               
               cv2.imshow(window_name, display)
               
               key = cv2.waitKey(1) & 0xFF
               if key == ord('q'):
                   break
               elif key == ord('r'):
                   self.reset()
                   self.current_mask = None
   
           cv2.destroyAllWindows()
           return self.current_mask
   
   # 使用
   import torch
   segmentor = InteractiveSegmentor(
       model_type="vit_h",
       checkpoint="sam_vit_h_4b8939.pth"
   )
   
   image = cv2.imread("test.jpg")
   mask = segmentor.run(image)
   ```

6. 修改 SAM ROS2 节点，实现自动分割模式：自动检测并分割图像中所有物体，按面积排序，并发布所有分割结果。
   
   **提示**：
