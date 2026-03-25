# 18-2 RLBench 与机械臂操作评估

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 18-2 |
| 课程名称 | RLBench 与机械臂操作评估 |
| 所属模块 | 18-具身智能benchmark |
| 难度等级 | ⭐⭐⭐⭐☆ |
| 预计学时 | 4小时 |
| 前置知识 | 机器人学基础（第二章）、强化学习基础（14-1）、PyTorch 基础、具身智能 Benchmark 概述（18-1） |

---

## 目录

1. [RLBench 详解](#1-rlbench-详解)
2. [评估流程](#2-评估流程)
3. [典型任务分析](#3-典型任务分析)
4. [基线方法](#4-基线方法)
5. [代码实现](#5-代码实现)
6. [练习题](#6-练习题)
7. [参考答案](#7-参考答案)

---

## 1. RLBench 详解

### 1.1 101 个任务概述

RLBench（Robot Learning Benchmark）是由伦敦帝国理工学院（Imperial College London）联合 DeepMind 推出的**大规模视觉引导机械臂操作 Benchmark**，收录了 **101 个**差异化的机器人操作任务，每个任务都有明确的成功条件、自动化评估协议和预生成的高质量演示轨迹。

**论文**：[RLBench: The Robot Learning Benchmark & Learning Environment](https://arxiv.org/abs/1909.12271)

**GitHub**：`https://github.com/stepjam/RLBench`

**核心数据一览**：

| 指标 | 数值 |
|------|------|
| 任务总数 | 101 |
| 任务变体数 | 每个任务 100+ 随机初始配置 |
| 演示轨迹 | 10,000+ 条专家轨迹 |
| 视觉输入 | RGB、深度、分割掩码（多视角） |
| 机械臂支持 | Franka Panda、Fetch、Panda |
| 仿真引擎 | PyBullet |
| 发布年份 | 2019 |

**RLBench 任务全景图**：

```
RLBench 101 个任务分类
│
├── 基础操作类（约 20 个）
│   ├── close_drawer          # 关闭抽屉
│   ├── open_drawer           # 打开抽屉
│   ├── turn_tap              # 旋转水龙头
│   ├── press_switch          # 按开关
│   └── slide_block           # 滑动方块
│
├── 抓取放置类（约 25 个）
│   ├── pick_and_place        # 抓取并放置
│   ├── pick_and_place_single # 单物体抓放
│   ├── stack_blocks          # 堆叠方块
│   ├── place_in_drawer       # 放入抽屉
│   ├── place_in_tray         # 放入托盘
│   └── throw_in_basket       # 扔入篮子
│
├── 精细操作类（约 20 个）
│   ├── insert_peg_in_hole    # 插销入孔
│   ├── screw_bulb            # 拧灯泡
│   ├── wipe_board            # 擦白板
│   ├── insert_round_peg      # 插入圆销
│   └── plug_charger          # 插入充电器
│
├── 多步操作类（约 18 个）
│   ├── open_door_then_close  # 开门后关闭
│   ├── open_drawer_pick_object_place_in_drawer
│   ├── push_button_then_open_drawer
│   └── multi_step_sequence
│
├── 视觉推理类（约 10 个）
│   ├── reach_target          # 到达目标位置
│   ├── push_button_object_on_switch
│   ├── find_and_reach       # 寻找并到达
│   └── open_coloured_box    # 打开指定颜色盒子
│
└── 其他操作类（约 8 个）
    ├── meat_on_noodles       # 放肉到面
    ├── drag_brush            # 拖动刷子
    └── tower_build           # 搭建塔
```

### 1.2 视觉引导特点

RLBench 的核心特色是**多视角视觉引导**，每个任务同时提供多种视觉输入：

```
RLBench 视觉输入架构

前端相机（Front Camera）
├── RGB 图像（640×480）
├── 深度图像（Depth Map）
└── 分割掩码（Instance Segmentation）

俯视相机（Overhead Camera）
├── RGB 图像
└── 深度图像

腕部相机（Wrist Camera）
├── RGB 图像
└── 深度图像

辅助视角
├── 左相机
└── 右相机
```

**RLBench 与其他 Benchmark 的视觉对比**：

| 维度 | RLBench | MetaWorld | CALVIN | ManiSkill |
|------|---------|-----------|--------|-----------|
| **RGB 输入** | ✅ 多视角 | ❌ 状态空间 | ✅ 单目 | ✅ GPU 渲染 |
| **Depth 输入** | ✅ 多视角 | ❌ | ✅ | ✅ |
| **分割掩码** | ✅ | ❌ | ❌ | ✅ |
| **腕部相机** | ✅ | ❌ | ❌ | 可选 |
| **相机数量** | 4+ | 0 | 1 | 可配置 |

### 1.3 MoveIt! 集成

RLBench 深度集成 **MoveIt!** 运动规划框架：

```
用户高层指令（如 "pick up the red cube"）
           ↓
   任务规划层（Task Planning）
           ↓
   运动规划层（MoveIt! Motion Planning）
           ↓
   逆运动学求解（IK Solver）
           ↓
   关节轨迹执行（Joint Trajectory Execution）
           ↓
   仿真/真机执行
```

| 功能 | 说明 |
|------|------|
| **逆运动学（IK）** | 末端执行器位姿 → 关节角度 |
| **碰撞检测** | 规划时避免机器人与环境碰撞 |
| **路径平滑** | 对粗糙路径进行样条插值平滑 |
| **约束规划** | 满足关节限位、末端姿态等约束 |

### 1.4 低样本学习

RLBench 的核心研究目标是推动**低样本（Few-shot）机器人操作学习**：

**为什么需要低样本学习？**

| 问题 | 数据需求 | 现实挑战 |
|------|---------|---------|
| 真实机器人数据采集 | 10,000+ 条轨迹 | 耗时、昂贵、磨损 |
| 仿真数据生成 | 100,000+ 条 | 计算成本高 |
| 新任务适应 | 每个新任务都要重新训练 | 无法规模化 |
| **低样本学习** | **< 100 条演示** | **可行** |

**RLBench 低样本评测协议**：

| 协议 | 训练数据量 | 评测任务 | 目标 |
|------|-----------|---------|------|
| **Few-shot 10** | 10 条演示/任务 | 同分布变体 | 验证少样本模仿学习 |
| **Few-shot 100** | 100 条演示/任务 | 同分布变体 | 验证数据效率 |
| **Zero-shot** | 0 条新任务数据 | 新物体/新场景 | 验证泛化能力 |

---

## 2. 评估流程

### 2.1 环境配置

**系统要求**：

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| **操作系统** | Ubuntu 18.04/20.04/22.04 | Linux 最佳 |
| **Python** | 3.7 - 3.9 | 推荐 3.8 |
| **GPU** | NVIDIA GPU（建议 8GB+） | 用于视觉策略训练 |
| **CPU** | 4 核以上 | 并行环境 |
| **磁盘** | 20GB+ | 任务资源文件 |
| **内存** | 16GB+ | 并行数据加载 |

**安装步骤**：

```bash
# 步骤 1：创建虚拟环境
conda create -n rlbench python=3.8
conda activate rlbench

# 步骤 2：安装 PyBullet（RLBench 仿真引擎）
pip install pybullet

# 步骤 3：安装 RLBench
pip install rlbench

# 步骤 4：下载任务资源（约 4GB）
python -m rlbench.download_tasks --all

# 步骤 5：验证安装
python -c "
from rlbench import Environment
from rlbench.observation_config import ObservationConfig

# 创建观测配置（启用视觉输入）
obs_config = ObservationConfig()
obs_config.set_all(True)

# 创建环境
env = Environment('sim', obs_config)
print('RLBench 安装成功！')
env.shutdown()
"
```

### 2.2 任务定义

RLBench 中每个任务都遵循标准化的定义接口：

```python
"""
RLBench 任务定义结构
每个任务包含：描述、初始化、成功条件
"""
from rlbench.backend.task import Task
from rlbench.backend.conditions import (
    ConditionSet,
    AttachedCondition
)
from pyrep.objects.shape import Shape
from pyrep.objects.joint import Joint


class PickAndPlaceSingle(Task):
    """
    抓取并放置单个物体
    
    任务描述：
    - 初始状态：物体在桌面上随机位置
    - 目标状态：物体被放置到指定目标区域
    - 成功条件：物体在目标区域且被稳定放置
    """
    
    def init_task(self):
        """任务初始化 - 定义场景中的物体和成功条件"""
        # 获取场景物体引用
        self.target = Shape('red_block')        # 目标物体（红色方块）
        self.target_zone = Shape('target_zone')  # 目标区域
        
        # 获取夹爪
        gripper = self.get_object('panda_gripper')
        
        # 设置成功条件：物体被抓住 + 在目标区域
        attached = AttachedCondition(gripper, self.target)
        self.register_success_conditions([attached])
    
    def init_episode(self, index):
        """
        每个 Episode 初始化
        index 控制不同的变体配置（RLBench 为每个任务预定义 100+ 变体）
        """
        # 随机化物体初始位置（基于 index 变体）
        self.target.set_position([
            0.3 + 0.1 * (index % 10),  # x: 0.3-0.4
            0.0 + 0.1 * (index % 5),  # y: 0.0-0.4
            0.75                        # z: 桌面高度
        ])
        
        # 设置目标区域位置
        self.target_zone.set_position([0.4, -0.2, 0.75])
        
        return "抓取红色方块并放到目标区域"
```

### 2.3 评估协议

**标准评测流程**：

```
RLBench 评测协议

1. 任务选择：从 101 个任务中选择评测子集
   └─→ 常用选择：10个核心任务 / 全部101个

2. 变体遍历：对每个任务遍历所有变体（index 0-N）
   └─→ 报告每个变体的成功率
   └─→ 计算平均成功率和标准差

3. 动作空间选择
   └─→ 末端执行器空间（EE Pose）
   └─→ 关节空间（Joint Position）

4. 评测指标记录
   └─→ 成功率（SR）
   └─→ 平均回合长度
   └─→ 演示成功率（BC/IL 方法）

5. 结果汇总
   └─→ Per-task SR 表
   └─→ 平均 SR
   └─→ 标准差/置信区间
```

**评测任务分组**：

| 分组 | 任务数 | 适用场景 | 评测耗时 |
|------|-------|---------|---------|
| **核心组（Core-10）** | 10 | 快速基线对比 | ~2 小时 |
| **标准组（Standard-30）** | 30 | 全面评测 | ~6 小时 |
| **完整组（Full-101）** | 101 | 论文提交级别 | ~20 小时 |

### 2.4 结果分析

```python
"""
RLBench 评测结果分析
"""
from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass
class TaskResult:
    """单个任务的评测结果"""
    task_name: str                              # 任务名称
    variants_success: List[bool]                # 每个变体的成功/失败
    variants_lengths: List[int]                 # 每个变体的回合长度
    
    @property
    def success_rate(self) -> float:
        """计算任务成功率"""
        return np.mean(self.variants_success)
    
    @property
    def success_std(self) -> float:
        """计算成功率标准差"""
        return np.std(self.variants_success)
    
    @property
    def mean_length(self) -> float:
        """平均回合长度"""
        return np.mean(self.variants_lengths)


@dataclass
class BenchmarkResult:
    """完整 Benchmark 评测结果"""
    all_task_results: Dict[str, TaskResult]
    
    def overall_success_rate(self) -> float:
        """全任务平均成功率"""
        all_srs = [r.success_rate for r in self.all_task_results.values()]
        return np.mean(all_srs)
    
    def generate_report(self) -> str:
        """生成文本报告"""
        report = []
        report.append("=" * 70)
        report.append("RLBench Benchmark 评测报告")
        report.append("=" * 70)
        report.append(f"\n【总体统计】")
        report.append(f"  任务总数: {len(self.all_task_results)}")
        report.append(f"  平均成功率: {self.overall_success_rate():.2%}")
        report.append(f"\n【Per-Task 结果】")
        report.append(f"{'任务名':<40} {'SR':>8} {'平均长度':>10}")
        report.append("-" * 70)
        
        for task_name, result in sorted(self.all_task_results.items()):
            report.append(
                f"{task_name:<40} "
                f"{result.success_rate:>8.2%} "
                f"{result.mean_length:>10.1f}"
            )
        report.append("=" * 70)
        return "\n".join(report)
```

---

## 3. 典型任务分析

### 3.1 抓取与放置

**抓取放置**是 RLBench 中最基础也是最重要的任务类别：

```
任务：pick_and_place_single
目标：抓取桌面上的目标物体，放置到指定目标区域

抓取放置子步骤：

Step 1: 视觉定位
  └─→ 从 RGB/Depth 图像中检测目标物体

Step 2: 接近物体
  └─→ 移动末端执行器到物体上方预抓取位置

Step 3: 张开夹爪
  └─→ 将夹爪移动到物体两侧，对齐姿态

Step 4: 闭合抓取
  └─→ 闭合夹爪，判断是否成功抓住
       └─→ 通过力反馈或物体附着状态判断

Step 5: 抬起物体
  └─→ 垂直向上移动，保持抓取稳定性

Step 6: 移动到目标区域
  └─→ 水平移动到目标区域上方，避免碰撞

Step 7: 放置物体
  └─→ 下降低于物体高度，打开夹爪释放物体

Step 8: 撤离
  └─→ 向上和向后移动，确认任务完成
```

**抓取放置任务难度分析**：

| 难度因子 | 简单 | 中等 | 困难 |
|---------|------|------|------|
| 物体形状 | 方形（易对齐） | 圆形（对称） | 不规则 |
| 物体材质 | 哑光（好检测） | 塑料（有反光） | 透明（深度不准确） |
| 目标区域 | 大（容差大） | 中等 | 小（精确放置） |
| 障碍物 | 无 | 1-2 个 | 多个/需避障 |

### 3.2 抽屉开关

**抽屉开关**任务考验机器人的**关节操作和顺序执行**能力：

```
抽屉开关任务分解

类型 A: open_drawer
  Step 1: 定位抽屉把手（视觉识别）
  Step 2: 接近把手（规划无碰撞路径）
  Step 3: 抓取把手（夹爪闭合）
  Step 4: 拉动抽屉（沿滑轨方向牵引）
  Step 5: 达到完全打开位置（释放把手）

类型 B: open_drawer_pick_object_place_in_drawer
  Step 1: 打开抽屉
  Step 2: 抓取物体
  Step 3: 将物体放入抽屉
  Step 4: 关闭抽屉
  Step 5: 完成任务

关键技能：
  - 把手抓取（对准+抓取）
  - 牵引操作（沿导轨方向力控）
  - 顺序执行（开→放→关）
```

**抽屉操作的挑战**：

| 挑战 | 描述 | 解决思路 |
|------|------|---------|
| **力控感知** | 抽屉滑动需要持续牵引力 | 阻抗控制或力反馈 |
| **方向对齐** | 必须沿滑轨方向拉动 | 视觉引导对齐 |
| **手柄多样性** | 不同抽屉把手形状不同 | 视觉识别+自适应抓取 |
| **顺序依赖** | 后续步骤依赖前面状态 | 任务规划保证顺序 |

### 3.3 物体操纵

**物体操纵**类任务涉及更精细的物理交互：

| 任务 | 操作类型 | 关键难度 |
|------|---------|---------|
| **stack_blocks** | 精确堆叠 | 3D 对齐、放置稳定性 |
| **wipe_board** | 擦拭动作 | 平面接触、轨迹平滑 |
| **sweep_to_dust** | 扫入垃圾 | 工具使用、力控制 |
| **insert_peg_in_hole** | 插销入孔 | 精确对准、孔内插入 |
| **screw_bulb** | 拧灯泡 | 旋转操作、螺纹对齐 |

**堆叠方块任务详解**：

```
stack_blocks 任务流程

目标：将 N 个方块按顺序堆叠成塔

子步骤：
1. 抓取第一个方块
2. 移动到目标堆叠位置上方
3. 精确对齐（x, y 位置）
4. 下放（z 位置精确控制）
5. 打开夹爪释放
6. 重复步骤 1-5 堆叠下一个

技术难点：
- 3D 对齐：x, y, z 三个方向都要精确
- 放置稳定性：已堆叠的方块可能倒塌
- 视觉遮挡：上层方块遮挡下层

解决方案：
- 使用深度图像估计 3D 位置
- 低速放置减少冲击
- 视觉伺服实时调整
```

### 3.4 视觉定位

**视觉定位**任务要求机器人基于视觉感知执行操作：

```
视觉定位任务能力分解

1. 物体检测
   └─→ 从 RGB 图像中定位目标物体
        └─→ 2D bbox 或 instance mask

2. 3D 姿态估计
   └─→ 估计物体 6D 位姿（位置 + 旋转）
        └─→ 方法：深度 + 几何 / 神经网络

3. 目标指定
   └─→ 理解目标区域/目标物体描述

4. 运动规划
   └─→ 末端执行器对准目标
        └─→ 逆运动学求解

5. 执行反馈
   └─→ 视觉伺服在线调整
        └─→ 目标检测确认成功
```

---

## 4. 基线方法

### 4.1 BC-INA（行为克隆 with Instance Normalization）

**BC-INA** 是 RLBench 官方基线方法，在 RLBench 论文中作为主要对比基准提出。

**核心思想**：

```
BC-INA = 行为克隆（Behavioral Cloning）+ 实例归一化（Instance Normalization）

行为克隆（BC）：
  └─→ 模仿学习的基础方法
       └─→ 学习从观测到动作的映射：π(o) → a
       └─→ 使用专家演示数据 (o_t, a_t) 监督学习

实例归一化（INA）：
  └─→ 源自图像分割任务的 normalization 技巧
       └─→ 在策略网络中对图像特征做 Instance Normalization
       └─→ 作用：消除场景/物体颜色等外观变化的影响
       └─→ 关注几何结构而非纹理
```

**BC vs InstanceNorm 对比**：

| 归一化方法 | 归一化维度 | 作用 |
|-----------|-----------|------|
| **BatchNorm** | batch × channels | 减少 internal covariate shift，加速训练 |
| **LayerNorm** | channels × H × W | 归一化每个样本，不依赖 batch |
| **InstanceNorm** | channels × H × W | 保留样式信息，消除全局颜色变化 |
| **GroupNorm** | channels groups × H × W | batch 不依赖，适合小 batch |

**BC-INA 网络架构**：

```python
"""
BC-INA 策略网络
观测图像 → CNN编码 → Instance Norm → 动作输出
"""
import torch
import torch.nn as nn
from torchvision import models


class BCINAPolicy(nn.Module):
    """
    BC-INA 策略网络
    
    核心设计：
    1. 共享 CNN 编码器（处理多视角图像）
    2. Instance Normalization 增强泛化
    3. MLP 动作头输出 7DoF 动作（位置 + 四元数 + gripper）
    """
    
    def __init__(self, action_dim=7, camera_names=None):
        super().__init__()
        if camera_names is None:
            camera_names = ['front', 'left', 'right', 'overhead']
        self.camera_names = camera_names
        
        # 共享 CNN 编码器（4个视角共用）
        # 使用 ResNet18 去掉最后分类层
        backbone = models.resnet18(pretrained=False)
        self.encoder = nn.Sequential(*list(backbone.children())[:-1])  # 输出 [B, 512, 1, 1]
        
        # Instance Normalization（关键设计）
        # 不同于 BatchNorm，InstanceNorm 对每个样本独立归一化
        # 保留几何结构但消除全局颜色/光照变化
        self.instance_norm = nn.InstanceNorm2d(num_features=512, affine=True)
        
        # 融合层：合并多相机特征
        self.fusion = nn.Sequential(
            nn.Linear(512 * len(camera_names), 512),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(512, 256),
            nn.ReLU(),
        )
        
        # 动作头：输出 action_dim 维动作
        # 7DoF = 3DoF 位置 + 4DoF 四元数旋转
        # 8DoF = 7DoF + 1DoF gripper
        self.action_head = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, action_dim),
        )
    
    def forward(self, obs_dict):
        """
        前向传播
        
        Args:
            obs_dict: 字典，key 为相机名，value 为图像 tensor
                     shape: [batch_size, 3, H, W]
        Returns:
            actions: [batch_size, action_dim]
        """
        features = []
        
        for cam_name in self.camera_names:
            if cam_name in obs_dict:
                img = obs_dict[cam_name]  # [B, 3, H, W]
                
                # CNN 特征提取
                feat = self.encoder(img)  # [B, 512, 1, 1]
                feat = feat.squeeze(-1).squeeze(-1)  # [B, 512]
                
                # Instance Normalization（保持空间维度）
                # 注：实际实现中 InstanceNorm 在 conv 层后应用
                features.append(feat)
        
        # 多相机特征拼接
        fused = torch.cat(features, dim=1)  # [B, 512 * num_cameras]
        
        # 融合
        fused = self.fusion(fused)  # [B, 256]
        
        # 动作输出
        actions = self.action_head(fused)  # [B, action_dim]
        
        return actions


# BC-INA 训练循环
def train_bc_ina(policy, demos, config):
    """
    BC-INA 训练
    
    Args:
        policy: BCINAPolicy 实例
        demos: 演示数据列表，每个 demo 是 (observations, actions) 元组
        config: 训练配置
    """
    optimizer = torch.optim.Adam(policy.parameters(), lr=config.lr)
    mse_loss = nn.MSELoss()
    
    for epoch in range(config.epochs):
        total_loss = 0.0
        
        # 遍历所有演示数据
        for demo in demos:
            obs_dict, actions = demo
            
            # 前向传播
            pred_actions = policy(obs_dict)  # [B, action_dim]
            
            # MSE 损失（行为克隆核心）
            loss = mse_loss(pred_actions, actions)
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{config.epochs}, Loss: {total_loss/len(demos):.4f}")


# BC-INA 评测
def evaluate_bc_ina(policy, env, tasks, num_episodes=100):
    """
    BC-INA 评测
    
    Returns:
        results: Dict[task_name, success_rate]
    """
    results = {}
    
    for task_name in tasks:
        task = env.get_task(task_name)
        successes = []
        
        for episode in range(num_episodes):
            obs = task.reset()
            done = False
            
            while not done:
                # 策略推理
                with torch.no_grad():
                    action = policy(obs)  # numpy action
                
                # 环境执行
                obs, reward, done, info = task.step(action)
                
                if done:
                    successes.append(info.get('success', False))
        
        results[task_name] = np.mean(successes)
    
    return results
```

### 4.2 RRL（Representations for Robotic Manipulation）

**RRL**（Representations for Robotic Manipulation）提出使用**3D 场景表征**来增强机器人操作能力：

**核心思想**：

```
RRL = 3D 场景表征 + 动作预测

关键洞察：
  └─→ 2D 图像策略难以处理 3D 几何问题（深度估计、精确放置）
  └─→ RRL 提出学习 3D 表征（点云/体素）直接预测动作

架构：
  3D 表征学习 → 动作预测网络 → 6DoF 末端执行器动作
```

**RRL 在 RLBench 上的应用**：

| 阶段 | 操作 | 说明 |
|------|------|------|
| **表征学习** | PointNet / VoxelNet | 从多视角 RGB-D 学习 3D 表征 |
| **动作预测** | MLP 动作头 | 从 3D 表征预测动作 |
| **执行** | MoveIt! IK | 将末端执行器动作转换为关节轨迹 |

### 4.3 GNM（Generalist Manipulation Model）

**GNM**（Generalist Manipulation Model）是一个**通用机器人操作模型**：

**核心思想**：

```
GNM = 通用视觉编码 + 任务特定解码器

目标：一个模型泛化到多个任务，而非每个任务单独训练

架构：
  多任务数据 → 共享视觉编码器 → 任务特定动作头

关键设计：
  1. 大量多任务数据联合训练
  2. 任务embedding区分不同任务
  3. 动作空间归一化（归一化到 [-1, 1]）
```

**GNM 在 RLBench 上的评测**：

| 指标 | GNM | BC-INA |
|------|-----|--------|
| **101 任务平均 SR** | 40.6% | 25.0% |
| **Zero-shot 新任务** | 显著更好 | 较差 |
| **数据效率** | 更高（多任务迁移） | 较低 |

---

## 5. 代码实现

### 5.1 RLBench 环境加载

```python
"""
RLBench 环境加载与基础使用
"""
import numpy as np
from rlbench import Environment, Task
from rlbench.observation_config import ObservationConfig


def create_rlbench_env(
    robot='panda',
    headless=True,
    enable_rgb=True,
    enable_depth=True,
    enable_segmentation=True
):
    """
    创建 RLBench 环境
    
    Args:
        robot: 机械臂类型 ('panda', 'fetch', 'widowx')
        headless: 无头模式（不渲染窗口）
        enable_rgb: 启用 RGB 相机输入
        enable_depth: 启用深度相机输入
        enable_segmentation: 启用分割掩码输入
    
    Returns:
        env: RLBench 环境实例
        obs_config: 观测配置
    """
    # 创建观测配置
    obs_config = ObservationConfig()
    
    # 配置各个相机的观测模式
    if enable_rgb:
        obs_config.set_all_rgbs(True)
    else:
        obs_config.set_all_rgbs(False)
    
    if enable_depth:
        obs_config.set_all_depths(True)
    else:
        obs_config.set_all_depths(False)
    
    if enable_segmentation:
        obs_config.set_all_segmantations(True)
    else:
        obs_config.set_all_segmantations(False)
    
    # 启用其他必要观测
    obs_config.gripper_pose = True          # 末端执行器位姿
    obs_config.joint_positions = True       # 关节位置
    obs_config.joint_velocities = True       # 关节速度
    obs_config.gripper_open = True           # 夹爪开合状态
    
    # 创建环境
    env = Environment(
        mode='sim',           # 'sim' 或 'real'
        obs_config=obs_config,
        headless=headless
    )
    
    return env


def load_task(env, task_class):
    """
    加载指定任务
    
    Args:
        env: RLBench 环境实例
        task_class: Task 类（如 Task.PICK_AND_PLACE）
    
    Returns:
        task: 任务实例
    """
    task = env.get_task(task_class)
    return task


def get_observation_shape(obs_config):
    """
    获取观测空间维度
    
    Returns:
        obs_shape: 观测维度字典
    """
    # front camera RGB shape
    front_rgb_shape = (3, 128, 128) if obs_config.front.rgb else None
    
    return {
        'rgb': front_rgb_shape,          # RGB 图像
        'depth': (1, 128, 128),           # 深度图像
        'gripper_pose': (7,),             # 末端执行器位姿 [x,y,z,rx,ry,rz,rw]
        'joint_positions': (7,),          # 关节位置
        'gripper_open': (1,),             # 夹爪开合 [0=闭合, 1=打开]
    }


def demo_task(task, num_demos=5):
    """
    演示任务执行（使用专家演示轨迹）
    
    Args:
        task: 任务实例
        num_demos: 演示数量
    """
    for i in range(num_demos):
        print(f"\n--- 演示 {i+1}/{num_demos} ---")
        
        # 重置任务，获取初始观测
        obs = task.reset()
        
        # 获取描述
        description = task.get_task_description()
        print(f"任务描述: {description}")
        
        # 执行一个步骤（专家动作）
        obs, reward, done, info = task.step(task.get_optimal_action(obs))
        
        print(f"奖励: {reward:.3f}, 完成: {done}, 信息: {info}")
        
        if done:
            print("任务成功！")
        else:
            print("任务失败或未完成")


# 使用示例
if __name__ == "__main__":
    print("创建 RLBench 环境...")
    
    # 创建环境（启用所有视觉输入）
    env = create_rlbench_env(
        robot='panda',
        headless=False,
        enable_rgb=True,
        enable_depth=True,
        enable_segmentation=True
    )
    
    print("环境创建成功！")
    print(f"可用任务列表: {list(Task.__members__.keys())[:10]}...")
    
    # 加载 pick_and_place_single 任务
    try:
        from rlbench.backend.task import Task as RLBenchTask
        task = env.get_task(RLBenchTask.PICK_AND_PLACE_SINGLE)
        print("\n任务加载成功！")
        
        # 获取观测维度
        obs = task.reset()
        print(f"RGB shape: {obs.front_rgb.shape}")
        print(f"Depth shape: {obs.front_depth.shape}")
        print(f"Gripper pose: {obs.gripper_pose}")
        
        demo_task(task, num_demos=2)
        
    except Exception as e:
        print(f"任务加载失败: {e}")
    
    # 关闭环境
    env.shutdown()
    print("\n环境已关闭")
```

### 5.2 任务执行与评估

```python
"""
RLBench 任务执行与评估
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import os


class RLBencheEvaluator:
    """
    RLBench 任务评估器
    
    功能：
    - 单任务评测
    - 多任务批量评测
    - 结果保存与分析
    """
    
    def __init__(self, env, task_class, num_variants=100):
        """
        初始化评估器
        
        Args:
            env: RLBench 环境实例
            task_class: Task 类
            num_variants: 评测的变体数量
        """
        self.env = env
        self.task_class = task_class
        self.num_variants = num_variants
        self.task = None
        
        # 评测结果记录
        self.results = {
            'successes': [],
            'lengths': [],
            'rewards': [],
            'variants': [],
        }
    
    def reset_task(self, variant_index):
        """
        重置任务到指定变体
        
        Args:
            variant_index: 变体索引（0 到 num_variants-1）
        
        Returns:
            obs: 初始观测
        """
        self.task = self.env.get_task(self.task_class)
        obs = self.task.reset(variant=variant_index)
        return obs
    
    def execute_action(self, action):
        """
        执行动作并获取下一个观测
        
        Args:
            action: 动作数组
        
        Returns:
            obs: 下一个观测
            reward: 奖励
            done: 是否结束
            info: 额外信息
        """
        return self.task.step(action)
    
    def evaluate_policy(
        self,
        policy_fn,
        num_variants: Optional[int] = None,
        max_steps: int = 100,
        render: bool = False
    ) -> Dict:
        """
        评估策略在任务上的表现
        
        Args:
            policy_fn: 策略函数，输入观测，输出动作
                      signature: action = policy_fn(obs)
            num_variants: 评测变体数（None 表示使用默认值）
            max_steps: 每个 episode 最大步数
            render: 是否渲染
        
        Returns:
            results: 评测结果字典
        """
        if num_variants is None:
            num_variants = self.num_variants
        
        successes = []
        lengths = []
        rewards = []
        
        for variant_idx in range(num_variants):
            # 重置任务
            obs = self.reset_task(variant_idx)
            
            done = False
            step_count = 0
            episode_reward = 0.0
            
            while not done and step_count < max_steps:
                # 渲染（如需要）
                if render:
                    self.env.render()
                
                # 策略推理
                action = policy_fn(obs)
                
                # 环境执行
                obs, reward, done, info = self.execute_action(action)
                
                episode_reward += reward
                step_count += 1
            
            # 记录结果
            successes.append(bool(info.get('success', False)))
            lengths.append(step_count)
            rewards.append(episode_reward)
            
            # 打印进度
            if (variant_idx + 1) % 20 == 0:
                current_sr = np.mean(successes)
                print(f"  变体 {variant_idx+1}/{num_variants}, SR={current_sr:.2%}")
        
        # 计算统计指标
        results = {
            'success_rate': np.mean(successes),
            'success_std': np.std(successes),
            'mean_length': np.mean(lengths),
            'mean_reward': np.mean(rewards),
            'successes': successes,
            'lengths': lengths,
            'rewards': rewards,
        }
        
        return results


### 5.3 批量评测代码

class MultiTaskRLBenchEvaluator:
    """
    RLBench 多任务评估器
    
    支持批量评测多个任务，计算整体性能指标
    """
    
    def __init__(self, env, num_variants=100):
        """
        初始化多任务评估器
        
        Args:
            env: RLBench 环境实例
            num_variants: 每个任务的变体数量
        """
        self.env = env
        self.num_variants = num_variants
        self.task_evaluators = {}
        self.results = {}
    
    def add_task(self, task_name, task_class):
        """
        添加评测任务
        
        Args:
            task_name: 任务名称（字符串）
            task_class: Task 类
        """
        self.task_evaluators[task_name] = RLBencheEvaluator(
            self.env, task_class, self.num_variants
        )
    
    def evaluate_all(
        self,
        policy_fn,
        tasks: Optional[List[str]] = None,
        num_variants: Optional[int] = None,
        max_steps: int = 100
    ) -> Dict[str, Dict]:
        """
        在所有任务上评测策略
        
        Args:
            policy_fn: 策略函数
            tasks: 要评测的任务名称列表（None 表示全部）
            num_variants: 每个任务的变体数
            max_steps: 最大步数
        
        Returns:
            results: Dict[task_name, task_results]
        """
        if tasks is None:
            tasks = list(self.task_evaluators.keys())
        
        print(f"\n{'='*60}")
        print(f"RLBench 多任务评测")
        print(f"任务数: {len(tasks)}")
        print(f"每任务变体数: {num_variants or self.num_variants}")
        print(f"{'='*60}\n")
        
        for task_name in tasks:
            if task_name not in self.task_evaluators:
                print(f"警告: 任务 {task_name} 未注册，跳过")
                continue
            
            print(f">>> 评测任务: {task_name}")
            
            evaluator = self.task_evaluators[task_name]
            
            try:
                task_results = evaluator.evaluate_policy(
                    policy_fn=policy_fn,
                    num_variants=num_variants,
                    max_steps=max_steps,
                    render=False
                )
                self.results[task_name] = task_results
                
                print(f"  成功率: {task_results['success_rate']:.2%}")
                print(f"  平均长度: {task_results['mean_length']:.1f}")
                print()
                
            except Exception as e:
                print(f"  任务 {task_name} 评测失败: {e}")
        
        return self.results
    
    def compute_overall_metrics(self) -> Dict[str, float]:
        """
        计算整体性能指标
        
        Returns:
            metrics: 整体指标字典
        """
        if not self.results:
            return {}
        
        all_success_rates = [r['success_rate'] for r in self.results.values()]
        all_lengths = [r['mean_length'] for r in self.results.values()]
        
        return {
            'overall_success_rate': np.mean(all_success_rates),
            'success_rate_std': np.std(all_success_rates),
            'overall_mean_length': np.mean(all_lengths),
            'num_tasks_evaluated': len(self.results),
        }
    
    def print_summary(self):
        """
        打印评测汇总表
        """
        if not self.results:
            print("没有可用的评测结果")
            return
        
        print("\n" + "=" * 80)
        print(f"RLBench 多任务评测汇总")
        print("=" * 80)
        print(f"{'任务名':<45} {'成功率':>10} {'平均长度':>10}")
        print("-" * 80)
        
        for task_name, result in sorted(self.results.items()):
            print(
                f"{task_name:<45} "
                f"{result['success_rate']:>10.2%} "
                f"{result['mean_length']:>10.1f}"
            )
        
        print("-" * 80)
        overall = self.compute_overall_metrics()
        print(
            f"{'整体平均':<45} "
            f"{overall['overall_success_rate']:>10.2%} "
            f"{overall['overall_mean_length']:>10.1f}"
        )
        print("=" * 80)
    
    def save_results(self, filepath: str):
        """
        保存评测结果到 JSON 文件
        
        Args:
            filepath: 保存路径
        """
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        
        # 序列化（排除原始列表数据）
        serializable_results = {}
        for task_name, result in self.results.items():
            serializable_results[task_name] = {
                'success_rate': float(result['success_rate']),
                'success_std': float(result['success_std']),
                'mean_length': float(result['mean_length']),
                'mean_reward': float(result['mean_reward']),
            }
        
        data = {
            'num_variants': self.num_variants,
            'results': serializable_results,
            'overall': self.compute_overall_metrics(),
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"评测结果已保存至: {filepath}")


# ============ 使用示例 ============
if __name__ == "__main__":
    print("=" * 60)
    print("RLBench 评测代码示例")
    print("=" * 60)
    
    # 步骤 1：创建环境
    from rlbench.observation_config import ObservationConfig
    from rlbench.backend.task import Task
    
    obs_config = ObservationConfig()
    obs_config.set_all(True)
    
    env = Environment(mode='sim', obs_config=obs_config, headless=True)
    print("环境创建成功！")
    
    # 步骤 2：定义策略
    def random_policy(obs):
        """随机策略（基线）"""
        # 返回随机动作（末端执行器位姿 + gripper）
        action = np.random.uniform(-1, 1, size=8)  # 7DoF pose + gripper
        return action
    
    # 步骤 3：单任务评测
    print("\n--- 单任务评测 ---")
    evaluator = RLBencheEvaluator(env, Task.PICK_AND_PLACE_SINGLE, num_variants=50)
    
    results = evaluator.evaluate_policy(
        policy_fn=random_policy,
        num_variants=50,
        max_steps=100
    )
    
    print(f"\n评测结果:")
    print(f"  成功率: {results['success_rate']:.2%}")
    print(f"  平均长度: {results['mean_length']:.1f}")
    
    # 步骤 4：多任务评测
    print("\n--- 多任务批量评测 ---")
    multi_eval = MultiTaskRLBenchEvaluator(env, num_variants=30)
    
    # 添加评测任务
    multi_eval.add_task('pick_and_place_single', Task.PICK_AND_PLACE_SINGLE)
    multi_eval.add_task('reach_target', Task.REACH_TARGET)
    multi_eval.add_task('open_drawer', Task.OPEN_DRAWER)
    multi_eval.add_task('close_drawer', Task.CLOSE_DRAWER)
    multi_eval.add_task('press_switch', Task.PRESS_SWITCH)
    
    # 执行批量评测
    all_results = multi_eval.evaluate_all(
        policy_fn=random_policy,
        max_steps=100
    )
    
    # 打印汇总
    multi_eval.print_summary()
    
    # 保存结果
    multi_eval.save_results("results/rlbench_evaluation.json")
    
    # 关闭环境
    env.shutdown()
    print("\n评测完成！")

---

## 6. 练习题

### 选择题

**1. RLBench 收录了多少个差异化的机器人操作任务？**
- A. 50 个
- B. 80 个
- C. 101 个
- D. 150 个

**2. RLBench 的核心视觉特点是什么？**
- A. 单目 RGB 相机输入
- B. 多视角视觉输入（RGB + Depth + 分割掩码）
- C. 仅支持深度相机
- D. 不提供视觉输入

**3. 以下哪个不是 RLBench 评测的核心指标？**
- A. 成功率（Success Rate）
- B. 平均回合长度
- C. BLEU 分数
- D. 演示成功率（Demo Success Rate）

**4. BC-INA 方法中，Instance Normalization 的主要作用是？**
- A. 加速训练收敛
- B. 消除 batch 依赖
- C. 消除场景/物体颜色等外观变化，保留几何结构
- D. 替代 dropout 正则化

**5. RLBench 中 MoveIt! 集成的主要作用是什么？**
- A. 提供仿真渲染
- B. 提供逆运动学求解和碰撞检测
- C. 提供视觉感知
- D. 提供数据存储

**6. 关于 RLBench 低样本学习，以下说法正确的是？**
- A. RLBench 仅支持全量数据训练，不支持少样本
- B. 每个任务 100+ 变体可用于元学习跨变体迁移
- C. RLBench 不提供演示数据
- D. 低样本学习不是 RLBench 的研究目标

**7. 在抓取放置任务中，以下哪个不是必需的子步骤？**
- A. 视觉定位目标物体
- B. 闭合夹爪抓取
- C. 使用语言模型生成动作
- D. 移动到目标区域放置

**8. RRL 方法的核心改进是？**
- A. 使用 2D 图像策略
- B. 学习 3D 场景表征
- C. 仅使用关节状态输入
- D. 替代 MoveIt! 做运动规划

### 简答题

**9. 解释 RLBench 的任务变体（Variant）机制，以及它对低样本学习的意义。**

**10. 描述 BC-INA 方法的核心设计，并说明 Instance Normalization 为什么能提升泛化能力。**

**11. 对比 RLBench 与 CALVIN Benchmark 的异同，包括任务类型、视觉输入、评测重点等方面。**

**12. 假设你要在 RLBench 上评测一个新提出的机器人操作策略，请说明完整的评测流程设计，包括任务选择、评测指标、数据使用等。**

---

## 7. 参考答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **C** | RLBench 收录了 101 个差异化的机器人操作任务，这是其核心特色之一。 |
| 2 | **B** | RLBench 提供多视角视觉输入（前端、俯视、腕部等多个相机），同时包含 RGB、Depth 和分割掩码。 |
| 3 | **C** | BLEU 分数是自然语言处理指标，不是 RLBench 的评测指标。RLBench 核心指标包括成功率、平均回合长度、演示成功率。 |
| 4 | **C** | Instance Normalization 在图像分割等领域被证明能消除全局颜色/光照变化的影响，使网络更关注几何结构和空间关系，从而提升跨场景泛化能力。 |
| 5 | **B** | MoveIt! 在 RLBench 中提供逆运动学求解（末端执行器位姿 → 关节角度）和碰撞检测（规划无碰撞路径）。 |
| 6 | **B** | 每个任务 100+ 变体提供了丰富的任务配置多样性，支持元学习跨变体迁移，是低样本学习的天然支撑。RLBench 也提供了 10,000+ 专家演示轨迹。 |
| 7 | **C** | 语言模型生成动作不是抓取放置任务的必要子步骤。核心步骤是视觉定位→接近→抓取→移动→放置→撤离。 |
| 8 | **B** | RRL（Representations for Robotic Manipulation）的核心改进是提出学习 3D 场景表征（点云/体素）来直接预测动作，解决 2D 图像策略难以处理精确 3D 操作的问题。 |

### 简答题答案

**9. RLBench 任务变体机制及对低样本学习的意义**

RLBench 的**变体（Variant）机制**是指每个任务支持 100+ 个不同的初始配置和目标配置：

```
变体机制：
  - 每个任务定义了多个变体索引（variant index）
  - 同一任务的不同变体对应不同的初始状态/目标状态
  - 示例（pick_and_place_single）：
    - variant 0: 物体在位置 A，目标区域在 B
    - variant 1: 物体在位置 C，目标区域在 D
    - ...最多支持 100+ 个变体

变体多样性来源：
  1. 物体初始位置随机化
  2. 目标位置随机化
  3. 障碍物配置变化
  4. 目标物体颜色/形状变化（部分任务）

低样本学习意义：
  1. 跨变体迁移：一个任务 ≈ 100 个"子任务"
  2. 元学习支持：MTL/ML 协议天然支持（训练变体→测试变体）
  3. 数据效率：少量演示 × 100 变体 = 有效数据量大幅增加
  4. 过拟合缓解：变体多样性防止模型过拟合单一配置
```

---

**10. BC-INA 核心设计及 Instance Normalization 泛化原理**

**BC-INA 核心设计**：

```
BC-INA = 行为克隆（BC）+ 实例归一化（INA）

行为克隆：
  - 收集专家演示轨迹 (o_t, a_t)
  - 监督学习：min Σ||π_θ(o_t) - a_t||²
  - 简单有效，是模仿学习的基础

Instance Normalization（关键设计）：
  - 对每个样本的每个通道，在空间维度 (H×W) 上独立归一化
  - 公式：z = (x - μ) / σ * γ + β
    其中 μ, σ 是当前样本当前通道的均值和标准差
  
  - 对比 BatchNorm：
    BatchNorm: 使用 batch 内其他样本的统计量
    InstanceNorm: 仅使用当前样本自身的统计量
```

**Instance Normalization 提升泛化的原因**：

| 特性 | BatchNorm | InstanceNorm |
|------|-----------|--------------|
| 归一化维度 | batch × channels | channels × H × W |
| 样本独立性 | 依赖 batch 统计量 | 完全独立 |
| 保留内容 | 归一化整体分布 | 保留每个样本独特风格 |
| 保留几何 | 一般 | **几何结构被保留** |

**泛化原理**：
- InstanceNorm 消除的是**全局外观变化**（整体亮度、对比度、颜色色调）
- 保留的是**空间结构和相对关系**（边缘、形状、相对位置）
- RLBench 中不同变体的物体颜色、场景光照不同，但几何结构相同
- INA 让网络更关注"物体在哪里、形状是什么"，而非"物体是什么颜色"
- 结果：模型对新的颜色配置、光照变化更鲁棒，泛化到新变体

---

**11. RLBench 与 CALVIN Benchmark 对比**

| 维度 | RLBench | CALVIN |
|------|---------|--------|
| **任务数量** | 101 个 | 26 个任务，ABCD 四个难度 |
| **核心特色** | 大规模多样化任务库 | 语言条件化长程任务链 |
| **仿真引擎** | PyBullet | PyBullet |
| **机械臂** | Franka Panda / Fetch | KUKA LBR |
| **视觉输入** | 多视角 RGB + Depth + 分割（4+相机） | 单目 RGB 相机 |
| **任务类型** | 抓取、放置、操作、精细操作等 | 桌面操作 + 抽屉/开关 |
| **任务链** | 多为单步任务（部分多步） | 核心特色：4 步长程任务链 |
| **语言指令** | 可选文本描述 | **核心：自然语言指令** |
| **评测重点** | 任务多样性、视觉策略、少样本泛化 | 长程规划、语言理解、多步推理 |
| **演示数据** | ✅ 10,000+ 轨迹 | ✅ 提供 |
| **典型基线** | BC-INA, RRL, GNM | LAPO, HULK, LangGAP |
| **适用研究** | 视觉运动策略、多任务学习 | 语言条件化、多步规划 |

**互补性**：
- RLBench 适合研究**任务多样性**和**视觉泛化**
- CALVIN 适合研究**语言理解**和**长程规划**
- 两者结合可覆盖更全面的具身操作研究

---

**12. RLBench 新策略完整评测流程设计**

**① 任务选择策略**

| 选择方案 | 任务数 | 适用场景 |
|---------|-------|---------|
| 快速验证 | Core-10（pick/place/reach/open/switch等） | 算法消融实验 |
| 标准评测 | Standard-30 | 论文对比基线 |
| 完整评测 | Full-101 | 论文最终结果 |

**② 评测指标体系**

| 指标类型 | 指标名称 | 计算方式 |
|---------|---------|---------|
| 核心指标 | 成功率（SR） | 成功次数 / 总次数 |
| 效率指标 | 平均回合长度 | 总步数 / 回合数 |
| 效率指标 | SPL（成功率加权路径效率） | SR × (最优路径/实际路径) |
| 安全指标 | 碰撞率 | 碰撞次数 / 总步数 |
| 泛化指标 | 新变体成功率 | 测试变体 SR vs 训练变体 SR |

**③ 评测配置**

```python
# 评测配置示例
eval_config = {
    'num_variants_per_task': 100,      # 每个任务评测 100 个变体
    'episodes_per_variant': 1,         # 每个变体 1 次（变体已提供多样性）
    'max_steps_per_episode': 100,      # 最大步数限制
    'action_space': 'ee_pose',          # 末端执行器空间
    'seed': 42,                         # 固定随机种子
    'headless': True,                   # 无头模式
}
```

**④ 数据使用方案**

| 方法 | 训练数据 | 评测数据 |
|------|---------|---------|
| **从零训练** | 任务内所有变体的演示 | 同任务变体（in-distribution） |
| **少样本微调** | 每个任务 10-100 条演示 | 同任务新变体 |
| **跨任务迁移** | 训练任务演示 | 测试任务（zero-shot） |

**⑤ 完整评测流程**

```
1. 准备阶段
   └─→ 安装 RLBench 环境
   └─→ 下载任务资源
   └─→ 选择评测任务子集

2. 基线复现
   └─→ 运行 BC-INA 等基线方法
   └─→ 验证评测流程正确性

3. 策略评测
   └─→ 加载待评测策略
   └─→ 在每个任务上运行评测
   └─→ 记录成功/失败、回合长度等信息

4. 结果分析
   └─→ 计算 Per-task SR 和整体 SR
   └─→ 生成评测报告表格
   └─→ 绘制成功率柱状图

5. 消融实验（可选）
   └─→ 改变动作空间（EE Pose vs Joint）
   └─→ 改变演示数据量
   └─→ 改变视觉输入配置
```

**⑥ 结果报告模板**

```
RLBench 评测结果

【评测配置】
- 任务数: 30
- 每任务变体: 100
- 动作空间: EE Pose
- 随机种子: 42

【Per-Task 结果】
任务名                       成功率    平均长度
-------------------------------------------------
pick_and_place_single         85.0%      42.3
reach_target                  92.0%      18.5
open_drawer                   78.0%      35.2
close_drawer                  81.0%      28.7
...

【整体结果】
- 平均成功率: 78.3% ± 12.5%
- 平均回合长度: 35.6
```

