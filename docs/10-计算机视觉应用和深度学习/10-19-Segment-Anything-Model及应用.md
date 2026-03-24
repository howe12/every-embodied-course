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

## 5. SAM 与 YOLO 物体分割的区别

### 5.1 概述对比

SAM 和 YOLO 都是计算机视觉领域的重要模型，但它们的设计目标和应用场景有显著区别：

| 特性 | SAM | YOLO |
|------|-----|------|
| **设计目标** | 万物可分割（Prompt-based） | 目标检测与分割（Training-based） |
| **分割方式** | 提示词驱动，无需训练 | 需针对特定类别训练 |
| **输出类型** | 任意目标的分割掩膜 | 固定类别的检测框+分割掩膜 |
| **泛化能力** | 极强，可分割未见过的新类别 | 受限于训练数据集 |
| **实时性** | ViT-B可接近实时 | YOLOv8可达到30+ FPS |
| **典型应用** | 交互式分割、数据标注 | 特定场景的实时检测 |

### 5.2 核心技术对比

**① 分割范式的区别**

```
YOLO分割流程：
输入图像 → 固定类别检测 → 像素级分割 → 输出结果
       ↑
   必须指定类别（如人、车、狗）

SAM分割流程：
输入图像 + 提示词（点/框/文本）→ 分割提示指定的目标 → 输出结果
                        ↑
              可以是任意类别，无需预先定义
```

**② YOLO的分割原理**

YOLO（以YOLOv8-seg为例）采用分离头（Decoupled Head）设计：
1. 检测头：预测边界框和类别概率
2. 分割头：对每个检测到的目标生成分割掩膜

```python
# YOLOv8-seg 分割原理（伪代码）
class SegmentationHead(nn.Module):
    def __init__(self, num_classes):
        # 分割掩膜原型
        self.mask_prototypes = nn.Conv2d(256, 32, 1)  # 32个原型
        # 掩膜系数
        self.mask_coef = nn.Conv2d(num_classes, 32, 1)
    
    def forward(self, features):
        # 生成掩膜原型
        prototypes = self.mask_prototypes(features)  # [B, 32, H, W]
        
        # 预测每个目标的掩膜系数
        coefs = self.mask_coef(features)  # [B, num_classes, 32]
        
        # 掩膜 = 原型 × 系数
        masks = torch.einsum('bchw,bnc->bnhw', prototypes, coefs)
        return masks
```

**③ SAM的分割原理**

SAM采用Transformer架构的提示词驱动分割：
1. 图像编码器：ViT将图像编码为密集特征图
2. 提示词编码器：编码点/框/文本提示
3. 掩膜解码器：融合图像特征和提示特征，生成掩膜

```python
# SAM 分割原理（伪代码）
class SAM:
    def __init__(self):
        self.image_encoder = ViT_H()      # 图像编码器
        self.prompt_encoder = PromptEncoder()  # 提示词编码器
        self.mask_decoder = MaskDecoder()     # 掩膜解码器
    
    def predict(self, image, prompts):
        # 1. 编码图像
        image_features = self.image_encoder(image)  # [B, 64, 64, 1280]
        
        # 2. 编码提示词
        prompt_features = self.prompt_encoder(prompts)
        
        # 3. 解码生成掩膜
        masks = self.mask_decoder(image_features, prompt_features)
        
        return masks  # 输出分割掩膜
```

### 5.3 应用场景选择

**选择 YOLO 的场景：**
- 需要实时检测固定类别（如人、车、交通标志）
- 硬件资源有限（边缘设备）
- 场景固定，类别已知
- 需要同时获取检测框和分割掩膜

**选择 SAM 的场景：**
- 需要分割训练集中没有的新类别
- 需要交互式分割（用户点击指定目标）
- 数据标注（自动分割辅助人工标注）
- 场景复杂，类别众多且不确定
- 工业分拣等需要分割新物体的场景

### 5.4 YOLO + SAM 联合使用

在实际应用中，可以结合两者优势：

```
                    ┌──────────────┐
                    │   输入图像    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  YOLOv8检测  │ → 获取已知类别的检测框
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────▼──────┐ ┌───▼────┐ ┌────▼─────┐
       │ 已知类别分割  │ │ 背景分割 │ │ 遗漏目标 │
       │  (YOLO-seg) │ │ (SAM)  │ │  (SAM)   │
       └─────────────┘ └────────┘ └──────────┘
```

**示例：机器人分拣场景**

```python
import cv2
import torch
from ultralytics import YOLO
from segment_anything import sam_model_registry, SamPredictor

class HybridSegmentor:
    """YOLO + SAM 混合分割器"""
    
    def __init__(self):
        # 加载YOLO（检测已知类别）
        self.yolo = YOLO('yolov8m-seg.pt')
        
        # 加载SAM（分割未知类别）
        sam = torch.hub.load('facebookresearch/sam', 'sam_vit_b_4b8939')
        sam.to('cuda' if torch.cuda.is_available() else 'cpu')
        self.sam = SamPredictor(sam)
        
        # 已知类别（YOLO训练的COCO数据集）
        self.known_classes = self.yolo.names
        
        # 未知类别（需要用户指定）
        self.unknown_class_id = 80  # YOLO中"thing"类的总数
    
    def segment(self, image, target_class=None):
        """
        分割主函数
        
        参数:
            image: BGR图像
            target_class: 目标类别（可选），None表示分割所有已知目标
        
        返回:
            results: 分割结果列表
        """
        # 1. YOLO检测
        yolo_results = self.yolo(image, verbose=False)[0]
        
        results = []
        
        # 2. 处理YOLO检测到的目标
        if yolo_results.masks is not None:
            for i, (box, mask, conf, cls) in enumerate(zip(
                yolo_results.boxes,
                yolo_results.masks.xy,
                yolo_results.conf,
                yolo_results.cls
            )):
                cls_id = int(cls)
                cls_name = self.known_classes[cls_id]
                
                # 如果指定了目标类别，只分割该类别
                if target_class and cls_name != target_class:
                    continue
                
                results.append({
                    'class': cls_name,
                    'class_id': cls_id,
                    'mask': mask,
                    'confidence': float(conf),
                    'source': 'yolo'
                })
        
        # 3. 如果需要，分割未知类别（使用SAM）
        if target_class and target_class not in self.known_classes:
            # 用户指定了未知类别，使用SAM
            self.sam.set_image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # 假设用户提供了一个框或点
            # 这里简化处理，实际中需要用户交互
            masks, scores, _ = self.sam.predict(
                point_coords=None,
                point_labels=None,
                box=box.xyxy.cpu().numpy(),
                multimask_output=False
            )
            
            results.append({
                'class': target_class,
                'class_id': -1,
                'mask': masks[0],
                'confidence': float(scores[0]),
                'source': 'sam'
            })
        
        return results
    
    def segment_with_click(self, image, click_point, foreground=True):
        """
        用户点击分割（SAM辅助）
        
        参数:
            image: BGR图像
            click_point: 点击坐标 [x, y]
            foreground: True为前景点，False为背景点
        
        返回:
            mask: 分割掩膜
        """
        self.sam.set_image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        masks, scores, _ = self.sam.predict(
            point_coords=[click_point],
            point_labels=[1 if foreground else 0],
            multimask_output=True
        )
        
        return masks[np.argmax(scores)], np.max(scores)


# 使用示例
if __name__ == "__main__":
    segmentor = HybridSegmentor()
    
    # 读取图像
    image = cv2.imread("robot_scene.jpg")
    
    # 方案1：分割所有已知目标
    results = segmentor.segment(image)
    print(f"检测到 {len(results)} 个目标")
    
    # 方案2：只分割"人"类别
    people = segmentor.segment(image, target_class="person")
    
    # 方案3：用户点击分割
    mask, score = segmentor.segment_with_click(image, [320, 240], foreground=True)
```

### 5.5 性能对比

| 模型 | 输入尺寸 | 参数量 | FPS (RTX 3090) | mIoU (COCO) |
|------|----------|--------|----------------|-------------|
| YOLOv8m-seg | 640×640 | 52M | ~45 | 45.2 |
| SAM ViT-B | 1024×1024 | 94M | ~30 | N/A (prompt-based) |
| SAM ViT-H | 1024×1024 | 636M | ~8 | N/A (prompt-based) |

**注意**：SAM的评估方式与YOLO不同。SAM是提示词驱动的"万物分割"，没有固定的类别集合，因此无法直接在COCO等固定类别数据集上计算mIoU。

---

## 6. 程序设计分析与实践指导

### 6.1 程序设计要素

从零基础的角度，一个完整的SAM应用需要包含以下核心要素：

```
┌─────────────────────────────────────────────────────────────┐
│                      SAM 应用程序架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                            │
│  │  模型加载   │  • 模型类型选择（vit_h/l/b）                 │
│  │  模块      │  • 模型权重路径配置                          │
│  │            │  • 设备选择（GPU/CPU）                       │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  图像输入   │  • 图像读取（本地/相机/ROS话题）              │
│  │  模块      │  • 图像预处理（resize、normalize）            │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  提示词输入 │  • 点提示（坐标+标签）                      │
│  │  模块      │  • 框提示（左上+右下坐标）                   │
│  │            │  • 文本提示（CLIP编码）                     │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  分割预测   │  • 图像编码                                │
│  │  模块      │  • 提示词编码                               │
│  │            │  • 掩膜解码                                │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  结果输出   │  • 掩膜可视化                              │
│  │  模块      │  • 坐标转换                                  │
│  │            │  • 数据发布（ROS话题）                      │
│  └─────────────┘                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 程序执行流程详解

**完整的SAM程序执行流程：**

```python
"""
SAM 程序执行流程伪代码

1. 初始化阶段
   ├── 导入依赖库
   ├── 配置模型参数
   ├── 加载模型权重
   └── 初始化预测器

2. 图像输入阶段
   ├── 读取图像文件 或 接收相机/ROS话题
   ├── BGR → RGB 色彩空间转换
   └── 图像验证（尺寸、格式检查）

3. 分割预测阶段
   ├── predictor.set_image(image)  # 图像编码（耗时最长）
   ├── 编码提示词（点/框/文本）
   ├── predictor.predict()        # 掩膜解码
   └── 后处理（选择最佳掩膜）

4. 结果输出阶段
   ├── 掩膜二值化
   ├── 可视化绘制
   └── 发布/保存结果
"""

# 实际代码流程
def sam_segmentation_pipeline(image_path, point_coords, point_labels):
    # ========== 1. 初始化 ==========
    sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h.pth")
    sam.to(device="cuda")
    sam.eval()
    predictor = SamPredictor(sam)
    
    # ========== 2. 图像输入 ==========
    image = cv2.imread(image_path)          # BGR格式
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # 转为RGB
    
    # ========== 3. 分割预测 ==========
    predictor.set_image(image_rgb)           # [耗时 ~0.1-0.3秒]
    masks, scores, logits = predictor.predict(
        point_coords=np.array(point_coords),  # [[x1,y1], [x2,y2]]
        point_labels=np.array(point_labels),  # [1, 0] 前景/背景
        multimask_output=True                 # 输出多个候选
    )
    
    # ========== 4. 结果输出 ==========
    best_mask = masks[np.argmax(scores)]     # 选择得分最高的掩膜
    
    # 可视化
    visualize_mask(image_rgb, best_mask)
    
    return best_mask, np.max(scores)
```

### 6.3 模型与参数的放置位置

**SAM模型文件结构：**

```
your_project/
├── models/                              # 模型文件夹
│   ├── sam_vit_h_4b8939.pth            # ViT-H 大模型 (~2.4GB)
│   ├── sam_vit_l_4b8939.pth            # ViT-L 中模型 (~1.2GB)
│   └── sam_vit_b_4b8939.pth            # ViT-B 小模型 (~375MB)
│
├── configs/                             # 配置文件
│   └── sam_config.py                   # SAM配置参数
│
├── scripts/
│   └── download_models.sh              # 模型下载脚本
│
├── sam_app.py                          # 主程序
└── requirements.txt
```

**配置文件示例（sam_config.py）：**

```python
"""
SAM 配置参数文件

这个文件集中管理SAM相关的所有配置参数，
方便根据不同部署环境进行调整。
"""

# ========== 模型配置 ==========
MODEL_CONFIG = {
    # 模型类型：vit_h / vit_l / vit_b
    # vit_h: 最高精度，速度最慢
    # vit_l: 中等精度，中等速度
    # vit_b: 最低精度，速度最快（推荐实时应用）
    "model_type": "vit_b",  # 默认使用vit_b平衡精度和速度
    
    # 模型权重路径
    # 支持绝对路径和相对路径
    "checkpoint_path": "models/sam_vit_b_4b8939.pth",
    
    # 可选：从PyTorch Hub自动下载（首次运行时下载）
    "use_hub_download": False,
}

# ========== 设备配置 ==========
DEVICE_CONFIG = {
    # 计算设备
    # "cuda": 使用NVIDIA GPU（推荐，速度快）
    # "cpu": 使用CPU（速度慢，不推荐）
    "device": "cuda",  # 自动选择可用设备
    
    # CPU线程数（仅CPU模式时有效）
    "num_threads": 4,
}

# ========== 分割参数 ==========
SEGMENT_CONFIG = {
    # 多掩膜输出
    # True: 输出3个候选掩膜（处理歧义性）
    # False: 输出1个最佳掩膜
    "multimask_output": True,
    
    # 最小掩膜面积阈值
    # 小于此面积的掩膜会被过滤掉
    "min_mask_area": 1000,  # 像素面积
    
    # 预测稳定性
    # 值越高，掩膜越稳定但边界可能不够精细
    "stability_score_thresh": 0.95,
}

# ========== ROS配置 ==========
ROS_CONFIG = {
    # 话题名称
    "image_topic": "/camera/image_raw",
    "mask_topic": "/sam/segmentation_mask",
    "click_topic": "/click_point",
    
    # 消息队列大小
    "queue_size": 10,
}
```

**参数修改指南：**

| 参数 | 可选值 | 修改影响 | 推荐场景 |
|------|--------|---------|---------|
| `model_type` | vit_h / vit_l / vit_b | 精度与速度权衡 | 精度优先用h，实时用b |
| `device` | cuda / cpu | 运行设备 | 有GPU用cuda |
| `multimask_output` | True / False | 输出数量 | 交互式用True，自动用False |
| `min_mask_area` | 整数 | 过滤小目标 | 根据场景调整 |
| `stability_score_thresh` | 0.0-1.0 | 掩膜稳定性 | 值越高越稳定 |

### 6.4 程序执行分析

**各步骤耗时分析（RTX 3060 GPU）：**

```python
"""
SAM 各步骤耗时分析（ViT-B, 1024×1024输入）

步骤                        耗时        占比
─────────────────────────────────────────────
1. 模型加载                  ~2秒        (仅首次)
2. 图像编码 set_image()      ~50ms       70%
3. 提示词编码                ~1ms        1%
4. 掩膜解码 predict()       ~20ms       28%
5. 结果处理                  ~1ms        1%
─────────────────────────────────────────────
总计（单次分割）             ~72ms       100%

FPS ≈ 14（理论值，实际略低）
"""

# 实际测量代码
import time

def benchmark_sam(predictor, image, num_iterations=100):
    """测量SAM执行速度"""
    # 预热
    for _ in range(5):
        predictor.set_image(image)
        predictor.predict(point_coords=[[100, 100]], point_labels=[1])
    
    # 正式测量
    times = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        
        predictor.set_image(image)
        masks, scores, _ = predictor.predict(
            point_coords=[[100, 100]],
            point_labels=[1],
            multimask_output=True
        )
        
        elapsed = (time.perf_counter() - start) * 1000  # 毫秒
        times.append(elapsed)
    
    print(f"平均耗时: {np.mean(times):.2f} ms")
    print(f"中位数耗时: {np.median(times):.2f} ms")
    print(f"FPS: {1000/np.mean(times):.1f}")
```

### 6.5 部署关注要点

**① 环境依赖安装：**

```bash
# 基础依赖
pip install torch torchvision

# SAM官方库
pip install segment-anything

# ROS2依赖（如需集成ROS）
pip install rospkg rospy cv_bridge

# 图像处理
pip install opencv-python numpy
```

**② 模型下载：**

```bash
# 方法1：手动下载（推荐，可控）
# 从以下地址下载模型权重：
# https://github.com/facebookresearch/segment-anything#model-checkpoints

# ViT-B (375MB) - 推荐实时应用
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_4b8939.pth

# ViT-L (1.2GB) - 平衡选择
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_4b8939.pth

# ViT-H (2.4GB) - 最高精度
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth


# 方法2：PyTorch Hub自动下载（首次运行时自动下载）
python -c "import torch; torch.hub.load('facebookresearch/sam', 'sam_vit_b_4b8939')"
```

**③ 常见问题与解决方案：**

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| CUDA out of memory | 图像太大/模型太大 | 减小图像尺寸或使用更小的模型 |
| 模型加载失败 | 权重文件损坏或路径错误 | 检查文件MD5，重新下载 |
| 分割结果为空 | 提示词位置无有效目标 | 调整点击位置或使用自动分割 |
| 速度太慢 | 使用CPU推理 | 确保CUDA可用或换用更小的模型 |
| ROS话题无数据 | 话题名称不匹配 | 检查 `ros2 topic list` |

**④ ROS2部署检查清单：**

```bash
# 1. 确认模型文件存在
ls -la models/sam_vit_b_4b8939.pth

# 2. 测试模型加载
python3 -c "import torch; from segment_anything import sam_model_registry; sam = sam_model_registry['vit_b'](); print('模型加载成功')"

# 3. 检查ROS2环境
echo $ROS_DISTRO  # 应该显示 humble 或 foxy
source /opt/ros/humble/setup.bash

# 4. 编译功能包
cd ~/ros2_ws && colcon build --packages-select sam_segmentation

# 5. 运行节点
ros2 run sam_segmentation sam_segmentation_node

# 6. 检查话题
ros2 topic list | grep -E "image|mask|sam"
```

### 6.6 可修改参数详解

**SAMPredictor.predict() 参数：**

```python
def predict(
    self,
    point_coords=None,      # 点提示坐标，形状 [N, 2]，N为点数
    point_labels=None,      # 点标签，形状 [N]，1=前景，0=背景
    box=None,               # 框提示，形状 [4]，格式 [x1, y1, x2, y2]
    mask_input=None,        # 上一帧的掩膜（用于视频分割）
    multimask_output=True,  # 是否输出多个候选掩膜
    return_logits=False,    # 是否返回logits（用于视频分割）
    stability_score_thresh=0.95,  # 稳定性阈值
):
    """
    SAM 预测函数参数详解
    """
```

**参数组合使用示例：**

```python
# 示例1：单点前景分割
masks, scores, _ = predictor.predict(
    point_coords=np.array([[200, 300]]),
    point_labels=np.array([1]),  # 1表示这是要分割的目标
)

# 示例2：前景点+背景点分割
masks, scores, _ = predictor.predict(
    point_coords=np.array([[200, 300], [100, 100]]),  # 两个点
    point_labels=np.array([1, 0]),  # 第一个是前景，第二个是背景
)

# 示例3：框分割
masks, scores, _ = predictor.predict(
    box=np.array([100, 100, 400, 400]),  # 左上角(100,100)，右下角(400,400)
)

# 示例4：自动分割（分割所有显著目标）
from segment_anything import SamAutomaticMaskGenerator
mask_generator = SamAutomaticMaskGenerator(predictor.model)
anns = mask_generator.generate(image)  # 返回所有检测到的目标
```

### 6.7 快速开始模板

```python
#!/usr/bin/env python3
"""
SAM 快速开始模板

使用方法：
1. 修改 MODEL_PATH 为实际模型路径
2. 运行 python sam_quickstart.py --image your_image.jpg --point 100 200
"""

import argparse
import cv2
import numpy as np
import torch
from segment_anything import sam_model_registry, SamPredictor

# ========== 配置区（根据环境修改） ==========
MODEL_PATH = "sam_vit_b_4b8939.pth"  # 模型路径
MODEL_TYPE = "vit_b"                   # 模型类型
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ========== 初始化函数 ==========
def init_sam(model_path, model_type, device):
    """初始化SAM模型"""
    sam = sam_model_registry[model_type](checkpoint=model_path)
    sam.to(device=device)
    sam.eval()
    return SamPredictor(sam)

# ========== 分割函数 ==========
def segment_point(image, predictor, x, y, foreground=True):
    """基于点击点分割"""
    predictor.set_image(image)
    
    masks, scores, _ = predictor.predict(
        point_coords=np.array([[x, y]]),
        point_labels=np.array([1 if foreground else 0]),
        multimask_output=True
    )
    
    best_idx = np.argmax(scores)
    return masks[best_idx], scores[best_idx]

# ========== 主函数 ==========
def main():
    parser = argparse.ArgumentParser(description="SAM 快速分割工具")
    parser.add_argument("--image", "-i", required=True, help="输入图像路径")
    parser.add_argument("--point", "-p", nargs=2, type=int, help="点击点坐标 x y")
    parser.add_argument("--model", "-m", default=MODEL_PATH, help="模型路径")
    args = parser.parse_args()
    
    # 初始化
    print(f"加载模型: {args.model}")
    predictor = init_sam(args.model, MODEL_TYPE, DEVICE)
    
    # 读取图像
    image = cv2.imread(args.image)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 分割
    if args.point:
        x, y = args.point
        print(f"分割点: ({x}, {y})")
        mask, score = segment_point(image_rgb, predictor, x, y)
        
        # 可视化
        result = image.copy()
        result[mask] = [0, 255, 0]  # 绿色叠加
        
        cv2.imwrite("result.jpg", result)
        print(f"结果已保存到 result.jpg，得分: {score:.3f}")
    else:
        print("请使用 --point 参数指定分割点")

if __name__ == "__main__":
    main()
```

**运行方式：**
```bash
# 安装依赖
pip install segment-anything opencv-python numpy torch

# 下载模型（ViT-B）
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_4b8939.pth

# 运行
python sam_quickstart.py -i test.jpg -p 320 240
```

## 7. ROS2 集成与机器人应用

### 7.1 SAM ROS2 节点架构

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

### 7.2 SAM 分割节点实现

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

### 7.3 机器人抓取应用

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

### 7.4 运行系统

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

## 8. 练习题

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
