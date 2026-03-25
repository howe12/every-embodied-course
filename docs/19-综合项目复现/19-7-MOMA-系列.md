# 19-7 MOMA 系列

> **前置课程**：15-模仿学习基础、19-4 RH20T 数据集、19-5 RoboTurk 数据集、19-6 MIMIC 数据集
> **后续课程**：20-具身智能综合应用

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在前几节课程中，我们分别介绍了日常生活操作数据集（RH20T、RoboTurk）和医疗手术数据集（MIMIC）。本节我们将进入**移动机械臂操作**领域，学习具身智能中极具挑战性的研究方向——**MOMA（Multi-Object Mobile Manipulation）系列**。MOMA 系列涵盖大规模多目标移动操作数据集、标准化竞赛评测体系和多样化真实场景，是目前移动操作领域最具影响力的 benchmark 之一。通过本节学习，你将全面理解 MOMA 的数据体系、评测方法和使用流程，并掌握基于该数据集的代码实战技能。

---

## 1. MOMA 概述

### 1.1 什么是 MOMA

MOMA（Multi-Object Mobile Manipulation，多目标移动机械臂操作）是一个专门针对**移动机械臂**的大规模多模态遥操作数据集和评测 benchmark。与固定基座的机械臂操作不同，移动机械臂需要同时协调**底盘移动**和**臂部操作**两个子系统，完成"走到目标位置 → 执行精细操作"的复合任务，这是从实验室走向真实家庭和工厂环境的关键技术门槛。

MOMA 的核心研究问题是：**如何让机器人在复杂室内场景中，自主完成多目标物体的识别、定位、移动和操作？**

MOMA 与此前介绍的数据集的核心区别在于其**移动性**和**复合任务**：
- **移动性**：机器人需要自主导航到操作位置，而非在固定工位工作
- **复合任务**：每个任务需要多个子操作串联（如：移动 → 抓取 → 移动 → 放置）
- **场景多样性**：涵盖家庭、办公室、仓库等多种真实室内环境

### 1.2 MOMA 系列组成

MOMA 实际上是一个**系列数据集/评测体系**，包含三个核心组成部分：

| 组成部分 | 全称 | 定位 | 特点 |
|---------|------|------|------|
| **MOMA** | 基础数据集 | 学术研究基准 | 中等规模、多场景、标准评测 |
| **MOMA-Challenge** | 竞赛评测体系 | 标准化竞赛 | 统一评测协议、排行榜、基线对比 |
| **MOMA-Large** | 大规模版本 | 深度学习训练 | 超大规模、任务多样、覆盖长程任务 |

三者共享相同的**数据格式规范**和**评测协议**，但规模和侧重点不同：

- **MOMA**：验证算法有效性，适合方法研究
- **MOMA-Large**：训练大规模模型，适合端到端学习
- **MOMA-Challenge**：标准化评测，适合公平比较各方法性能

### 1.3 数据规模

| 指标 | MOMA | MOMA-Large |
|------|------|------------|
| 场景数量 | 50+ 个室内场景 | 200+ 个室内场景 |
| 任务数量 | 200+ 个操作任务 | 1,000+ 个操作任务 |
| 演示片段（Episodes） | 5,000+ 条 | 50,000+ 条 |
| 总时长 | 250,000+ 秒（约 70 小时） | 2,500,000+ 秒（约 700 小时） |
| 机器人平台 | Mobile Manipulator（KUKA+底盘） | 多种移动机械臂平台 |
| 物体类别 | 50+ 种日常物体 | 200+ 种日常物体 |
| 模态通道 | 视觉+运动学+语言+深度 | 视觉+运动学+语言+深度+触觉 |
| 采集方式 | 遥操作 + 动捕系统 | 遥操作 + 动捕系统 + 仿真自动采集 |

### 1.4 任务类型

MOMA 的任务按照操作复杂度分为四个级别：

| 级别 | 名称 | 任务示例 | 操作步骤 |
|------|------|---------|---------|
| L1 | 单步操作 | 抓取桌面上的杯子 | 到达位置 → 抓取 |
| L2 | 两步操作 | 将杯子从桌面放到柜子 | 抓取 → 移动放置 |
| L3 | 多步操作 | 将盘子、洗碗液、杯子依次放入洗碗机 | 抓取 → 移动 → 抓取 → 移动 → 放置 |
| L4 | 长程任务 | 整理桌面：将书籍归位、杯子放回、杂物收进盒子 | 多个 L3 任务的组合 |

---

## 2. MOMA-Challenge

### 2.1 竞赛任务定义

MOMA-Challenge 是 MOMA 系列的**标准化竞赛评测协议**，由国际机器人学研究社区共同维护。挑战赛的核心任务是：**给定一个自然语言指令和一个室内场景，让移动机械臂自主完成指令中指定的多目标操作任务。**

**任务输入**：
- 自然语言指令：如"请把餐桌上的红色杯子拿起来，放到厨房的架子上"
- 初始场景描述：包含场景地图、物体的类别和位置
- 视觉感知：RGB-D 相机图像、物体检测结果

**任务输出**：
- 机器人的运动轨迹（底盘 + 臂部）
- 任务完成的最终状态（物体是否到达目标位置）
- 执行时间（从开始到任务完成的时长）

**成功判定标准**：

$$
\text{Success} = \begin{cases}
1 & \text{如果目标物体到达指定区域，且姿态正确} \\
0 & \text{否则}
\end{cases}
$$

其中"目标物体到达指定区域"定义为：

$$
d_{\text{pose}}(o, g) < \epsilon_{\text{pos}} \quad \text{且} \quad |\theta_o - \theta_g| < \epsilon_{\text{ori}}
$$

即物体位置误差小于 $\epsilon_{\text{pos}}$（通常 5cm）、朝向误差小于 $\epsilon_{\text{ori}}$（通常 15°）。

### 2.2 评估指标

MOMA-Challenge 采用多维度评估体系：

| 指标 | 描述 | 权重 |
|------|------|------|
| **任务成功率（SR）** | 任务是否完全成功 | 40% |
| **物体偏移量（OS）** | 物体最终位置与目标位置的欧氏距离 | 20% |
| **执行效率（EE）** | 完成任务所需的步数或时间 | 15% |
| **轨迹平滑度（TS）** | 机器人运动轨迹的平滑程度 | 10% |
| **碰撞率（CR）** | 机器人与环境障碍物碰撞的次数 | 15% |

**综合评分公式**：

$$
\text{Score} = 0.4 \times \text{SR} + 0.2 \times (1 - \frac{\text{OS}}{\text{OS}_{\max}}) + 0.15 \times \frac{1}{1 + \text{EE}} + 0.1 \times \text{TS} + 0.15 \times (1 - \frac{\text{CR}}{\text{CR}_{\max}})
$$

### 2.3 基线方法

MOMA-Challenge 官方提供了多个基线方法的实现，用于公平对比：

| 方法 | 类型 | 描述 | 开源代码 |
|------|------|------|---------|
| **Random** | 随机策略 | 随机选择动作作为下界 | ✅ |
| **Gripper Only** | 纯臂部策略 | 仅控制臂部，不移动底盘 | ✅ |
| **VLB** | 视觉-语言基线 | 预训练 VLM 提取语言条件 | ✅ |
| **BC** | 行为克隆 | 模仿学习专家轨迹 | ✅ |
| **BC-RGB** | 视觉行为克隆 | 仅用 RGB 图像的 BC | ✅ |
| **RT-1** | Transformer 策略 | Google Robotics 的端到端方法 | ❌ |
| **ManipGPT** | 大模型规划 | 使用 LLM 进行任务规划 | ❌ |

**基线方法的核心差异**：

```
MOMA-Challenge 基线方法对比
├── 感知输入
│   ├── RGB Only（BC-RGB）：仅用 RGB 图像
│   ├── RGB-D（BC）：RGB + 深度图像
│   └── Full（BC+OS）：RGB + 深度 + 物体位姿
├── 动作输出
│   ├── Arm Only（Gripper Only）：仅 6-DOF 臂部动作
│   └── Mobile Arm（BC/VLB）：6-DOF 臂部 + 2-DOF 底盘
└── 训练方式
    ├── 行为克隆（BC/BC-RGB）：监督学习模仿
    └── 视觉-语言导航（VLB）：语言条件引导
```

---

## 3. MOMA-Large

### 3.1 数据规模与任务复杂度

MOMA-Large 是 MOMA 系列中**规模最大、难度最高**的版本，专门为训练大规模端到端模仿学习模型设计。相比 MOMA 基础版本，MOMA-Large 在以下方面进行了扩展：

**规模扩展**：
- 场景数量：50 → 200+（覆盖更多真实室内环境）
- 任务数量：200 → 1,000+（涵盖更多操作类型）
- 演示片段：5,000 → 50,000+（10 倍数据量）
- 总时长：70 小时 → 700 小时（10 倍时长）

**任务复杂度提升**：
- L4 级别任务占比从 10% 提升至 30%
- 包含更多需要多物体协同操作的任务
- 增加了长时间跨度的任务（单任务最长可达 5 分钟）

**物体类别扩展**：
- 物体类别从 50 种扩展到 200+ 种
- 增加了形状相似但功能不同的物体（增加识别难度）
- 增加了需要精细操作的物体（小型物体、软体物体）

### 3.2 场景多样性

MOMA-Large 涵盖多种真实室内场景，每种场景有不同的操作挑战：

| 场景类型 | 典型环境 | 操作挑战 | 任务示例 |
|---------|---------|---------|---------|
| **家庭厨房** | 橱柜、冰箱、餐桌 | 物体遮挡、空间狭小 | 取出食材、放回餐具 |
| **客厅** | 沙发、茶几、电视柜 | 大范围移动、多物体 | 整理杂物、递送物品 |
| **卧室** | 衣柜、床头柜、书桌 | 高低位置变化、精细操作 | 叠衣服、整理书籍 |
| **办公室** | 书架、打印机、垃圾桶 | 结构化环境、办公物品 | 整理文件、清理桌面 |
| **仓库货架** | 货架、搬运箱、推车 | 高位取放、重物操作 | 拣选物品、分类摆放 |

### 3.3 仿真数据增强

MOMA-Large 在真实采集数据的基础上，引入**仿真自动生成数据**来进一步扩大规模：

```python
# 仿真数据生成伪代码
for scene_template in scene_templates:
    for object_config in object_configs:
        # 随机放置物体
        placed_objects = random_place_objects(scene_template, object_config)
        
        # 生成可行任务
        for task in generate_tasks(placed_objects):
            # 使用 RRT* 规划器生成无碰撞轨迹
            trajectory = motion_planner.plan(task)
            
            if trajectory.is_valid:
                # 添加噪声模拟真实采集
                noisy_trajectory = add_system_noise(trajectory)
                moma_large.add_episode(noisy_trajectory)
```

**仿真数据占比**：
- MOMA-Large 中，约 60% 为真实遥操作数据，40% 为仿真生成数据
- 仿真数据主要用于覆盖长尾场景（如罕见物体组合、危险操作等）
- 所有数据均经过人工验证，确保任务可执行性

---

## 4. 数据格式

### 4.1 轨迹格式

MOMA 数据集的核心是**移动机械臂的操作轨迹**，与固定基座机械臂不同的是，MOMA 轨迹包含两个额外的自由度——**底盘位置（x, y）**和**底盘朝向（θ）**。

**MOMA 轨迹数据字段**：

```python
{
    "timestamp": 1609459200000,         # 时间戳（毫秒，从 episode 开始计时）
    
    # 底盘状态（移动基座）
    "base_state": {
        "position": [1.2, -0.5],         # 底盘在地图中的 (x, y) 位置（米）
        "theta": 1.57,                    # 底盘朝向角（弧度）
        "velocity": [0.1, 0.0],          # 底盘线速度 (vx, vy)（米/秒）
        "angular_velocity": 0.05         # 底盘角速度（弧度/秒）
    },
    
    # 臂部状态（6-DOF 机械臂）
    "arm_state": {
        "joint_positions": [0.0, -0.5, 0.8, 1.2, -0.3, 0.1],  # 6 个关节角度（弧度）
        "joint_velocities": [0.01, -0.02, 0.01, 0.0, -0.01, 0.02],  # 关节速度
        "end_effector_pose": {           # 末端执行器位姿
            "position": [0.4, 0.2, 0.8],  # (x, y, z) 位置（米）
            "quaternion": [0.0, 0.0, 0.0, 1.0]  # 四元数 (qx, qy, qz, qw)
        },
        "gripper_position": 0.0          # 夹爪开度（0=全开，1=全闭）
    },
    
    # 视觉感知
    "camera_state": {
        "rgb_image": "rgb_frame_00000.jpg",  # RGB 图像文件名
        "depth_image": "depth_frame_00000.png",  # 深度图像文件名
        "camera_extrinsics": {            # 相机外参（相对于机械臂基座）
            "translation": [0.05, 0.1, 0.15],
            "rotation": [0.5, -0.5, 0.5, 0.5]
        }
    },
    
    # 自然语言指令（episode 级别，固定不变）
    "language_instruction": "请把餐桌上的红色杯子拿起来，放到厨房的架子上",
    
    # 任务进度（可选）
    "task_progress": {
        "subtask_id": 1,                 # 当前子任务 ID
        "subtask_name": "抓取杯子",        # 子任务名称
        "target_object": "红色杯子",       # 目标物体
        "target_region": "厨房架子"        # 目标区域
    }
}
```

### 4.2 场景描述格式

MOMA 的场景描述采用标准化的 JSON 格式，定义了场景中的所有物体、障碍物和可交互区域：

```python
{
    "scene_id": "kitchen_001",
    "scene_type": "家庭厨房",
    
    # 地图信息
    "map": {
        "resolution": 0.05,              # 地图分辨率（米/像素）
        "size": [10.0, 8.0],            # 地图尺寸（宽 x 高，米）
        "origin": [-5.0, -4.0],         # 地图原点（左下角世界坐标）
        "occupancy_grid": "map.pgm"     # 占据栅格地图文件
    },
    
    # 物体列表
    "objects": [
        {
            "object_id": "red_cup_1",
            "category": "杯子",
            "mesh_file": "objects/cups/red_cup.obj",
            "initial_pose": {
                "position": [0.8, -0.3, 0.75],  # 初始位置（x, y, z，米）
                "quaternion": [0.0, 0.0, 0.0, 1.0]  # 初始朝向
            },
            "bbox": [0.06, 0.06, 0.12],  # 边界框（长、宽、高，米）
            "mass": 0.2,                 # 质量（千克）
            "fragile": False,            # 是否易碎
            "grasp_type": "侧面抓取"     # 推荐抓取类型
        },
        {
            "object_id": "shelf_1",
            "category": "架子",
            "mesh_file": "objects/furniture/shelf.obj",
            "initial_pose": {
                "position": [-0.5, 1.0, 0.5],
                "quaternion": [0.0, 0.0, 0.707, 0.707]
            },
            "bbox": [0.8, 0.3, 0.02],
            "mass": 5.0,
            "static": True,              # 固定物体（不可移动）
            "graspable_region": [[-0.5, 1.0, 0.6], [-0.5, 1.0, 1.2]]  # 可放置区域
        }
    ],
    
    # 可放置区域（目标区域）
    "放置区域": [
        {
            "region_id": "kitchen_shelf",
            "category": "厨房架子",
            "pose": {"position": [-0.5, 1.0, 0.8], "quaternion": [0.0, 0.0, 0.0, 1.0]},
            "size": [0.8, 0.3, 0.5],
            "allowed_categories": ["杯子", "瓶子", "碗"]
        }
    ],
    
    # 障碍物
    "obstacles": [
        {
            "obstacle_id": "table_1",
            "category": "餐桌",
            "pose": {"position": [0.5, -0.5, 0.0], "quaternion": [0.0, 0.0, 0.0, 1.0]},
            "bbox": [1.2, 0.8, 0.75]
        }
    ]
}
```

### 4.3 任务规范格式

每个任务（Task）定义了一个完整的多目标操作目标：

```python
{
    "task_id": "task_kitchen_001",
    "task_name": "整理厨房桌面",
    "scene_id": "kitchen_001",
    
    # 自然语言指令
    "language_instruction": "把餐桌上的红色杯子拿起来，放到厨房架子上，然后把蓝色碗放到洗碗池旁边",
    
    # 任务分解（可选，供分析方法使用）
    "subtasks": [
        {
            "subtask_id": 0,
            "name": "抓取红色杯子",
            "instruction": "抓取餐桌上的红色杯子",
            "target_object": "red_cup_1",
            "success_criteria": {
                "gripper_state": "closed",
                "object_held": True
            }
        },
        {
            "subtask_id": 1,
            "name": "移动到架子",
            "instruction": "移动到厨房架子旁边",
            "target_region": "kitchen_shelf",
            "success_criteria": {
                "base_position_error": 0.1,  # 底盘位置误差阈值（米）
                "base_orientation_error": 0.26  # 底盘朝向误差阈值（弧度，约15°）
            }
        },
        {
            "subtask_id": 2,
            "name": "放置杯子",
            "instruction": "把杯子放到架子上",
            "target_region": "kitchen_shelf",
            "target_object": "red_cup_1",
            "success_criteria": {
                "object_in_region": True,
                "object_position_error": 0.05,  # 物体位置误差（米）
                "object_orientation_error": 0.26  # 物体朝向误差（弧度）
            }
        }
    ],
    
    # 评估参数
    "evaluation": {
        "time_limit": 120,               # 任务时间限制（秒）
        "max_substeps": 50,              # 最大子步骤数
        "collision_penalty": -0.1        # 每次碰撞扣分
    },
    
    # 难度等级
    "difficulty": "medium",
    "num_objects": 2,                  # 操作物体数量
    "num_regions": 2,                  # 涉及区域数量
    "requires_reorientation": True     # 是否需要重新定向
}
```

### 4.4 数据文件结构

```
moma_dataset/
├── moma_release/
│   ├── train/                         # 训练集
│   │   ├── episode_00001/
│   │   │   ├── metadata.json          # Episode 元数据
│   │   │   ├── trajectory.csv          # 完整轨迹数据
│   │   │   ├── images/
│   │   │   │   ├── rgb/
│   │   │   │   │   ├── rgb_00000.jpg
│   │   │   │   │   └── ...
│   │   │   │   └── depth/
│   │   │   │       ├── depth_00000.png
│   │   │   │       └── ...
│   │   │   └── task.json              # 任务定义
│   │   └── ...
│   │
│   ├── val/                           # 验证集
│   │   └── ...
│   │
│   └── test/                          # 测试集（无 GT）
│       └── ...
│
├── moma_large/                        # MOMA-Large 扩展数据
│   ├── real/                          # 真实采集数据
│   └── synthetic/                     # 仿真生成数据
│
├── moma_challenge/                    # Challenge 评测专用
│   ├── evaluation_protocol.md         # 评测协议
│   ├── baseline_methods/              # 基线方法代码
│   └── official_scoring.py            # 官方评分脚本
│
├── scenes/                            # 场景文件
│   ├── kitchen_001/
│   │   ├── map.pgm
│   │   ├── map.yaml
│   │   ├── objects.yaml
│   │   └── meshes/
│   └── ...
│
└── dataset_statistics.json            # 数据集统计信息
```

---

## 5. 使用方法

### 5.1 环境配置

MOMA 数据集的环境配置涉及多个依赖库，建议使用 conda 创建独立环境：

```bash
# 创建 conda 环境
conda create -n moma python=3.9
conda activate moma

# 安装 PyTorch（根据 CUDA 版本选择）
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118

# 安装 MOMA 专用依赖
pip install numpy pandas opencv-python matplotlib pillow
pip install pyyaml scipy trimesh pyrender
pip install open3d==0.17.0  # 3D 可视化
pip install pandas opencv-python scikit-learn

# 安装仿真环境（可选，用于数据生成）
pip install pybullet gymnasium

# 克隆 MOMA 官方代码库
git clone https://github.com/moma-dataset/MOMA.git
cd MOMA
pip install -e .

# 验证安装
python -c "import moma; print('MOMA 安装成功')"
```

### 5.2 数据下载

MOMA 数据集的获取需要访问官方数据门户：

```bash
# 方式一：从官方数据门户下载（需要注册）
# 1. 访问 https://moma-dataset.github.io/
# 2. 注册账号并申请数据访问权限
# 3. 获批后获取下载链接

# 方式二：使用官方下载脚本（推荐）
cd MOMA
python scripts/download.py \
    --dataset moma \
    --split train \
    --output ./data/moma_release/ \
    --credentials your_email:your_token

# 方式三：使用 AWS S3（需 AWS 账号）
aws s3 sync s3://moma-dataset/release/moma_release/ ./data/moma_release/

# 下载 MOMA-Large（需要额外申请）
python scripts/download.py \
    --dataset moma_large \
    --split train \
    --output ./data/moma_large/

# 下载场景文件
python scripts/download.py \
    --dataset scenes \
    --output ./data/scenes/

# 验证数据完整性
python scripts/verify_dataset.py --data_root ./data/moma_release/
```

### 5.3 任务执行

MOMA 的任务执行分为**离线评测**和**在线仿真**两种模式：

**离线评测模式**（用于验证模型性能）：

```bash
# 使用官方评测脚本评估模型
cd MOMA/moma_challenge

python evaluate.py \
    --model-path ./checkpoints/moma_bc_model.pth \
    --dataset ./data/moma_release/val/ \
    --output-dir ./results/ \
    --num-workers 4 \
    --device cuda

# 预期输出
# Loading model from ./checkpoints/moma_bc_model.pth
# Evaluating on 500 episodes...
# [████████████████████] 100%
# Success Rate: 0.723
# Object Offset: 0.043m
# Execution Efficiency: 0.812
# Trajectory Smoothness: 0.891
# Collision Rate: 0.152
# Overall Score: 0.724
```

**在线仿真模式**（用于可视化执行过程）：

```bash
# 启动 PyBullet 仿真环境
python sim_loop.py \
    --scene kitchen_001 \
    --task task_kitchen_001 \
    --model ./checkpoints/moma_bc_model.pth \
    --visualize True \
    --record True \
    --output-dir ./videos/
```

### 5.4 结果提交

MOMA-Challenge 的结果提交需要遵循标准格式：

```bash
# 准备提交文件
mkdir -p submission.zip
cp results/*.json submission.zip/

# 生成提交元数据
python scripts/generate_submission.py \
    --results-dir ./results/ \
    --model-name "MyModel" \
    --contact-email "researcher@example.com" \
    --output submission.zip

# 提交到官方评测服务器
curl -X POST \
    -F "file=@submission.zip" \
    -F "team_name=MyTeam" \
    -F "method_description=Behavior Cloning with RGB-D input" \
    https://moma-challenge.aiservice.com/submit
```

---

## 6. 代码实战

### 6.1 MOMA 数据加载器

```python
import json
import numpy as np
import torch
import pandas as pd
import cv2
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class MOMA Dataset(Dataset):
    """
    MOMA 数据集加载器
    
    支持：
    - 多模态数据加载（视觉 + 运动学 + 语言）
    - 任务难度过滤
    - 数据归一化
    - 序列采样
    """
    
    def __init__(
        self,
        data_root: str,
        split: str = "train",
        difficulty: Optional[List[str]] = None,
        min_objects: int = 1,
        seq_length: int = 32,
        image_size: Tuple[int, int] = (224, 224),
        load_images: bool = True,
        normalize: bool = True,
        camera_name: str = "wrist"  # wrist / overhead / forearm
    ):
        """
        参数:
            data_root: 数据根目录
            split: 数据集划分（train / val / test）
            difficulty: 任务难度过滤（easy / medium / hard / expert）
            min_objects: 最少操作物体数量
            seq_length: 序列长度
            image_size: 图像resize大小
            load_images: 是否加载图像
            normalize: 是否归一化
            camera_name: 相机视角
        """
        self.data_root = Path(data_root)
        self.split = split
        self.difficulty = difficulty
        self.min_objects = min_objects
        self.seq_length = seq_length
        self.image_size = image_size
        self.load_images = load_images
        self.normalize = normalize
        self.camera_name = camera_name
        
        self.episodes: List[Dict] = []
        self._scan_episodes()
        
        if self.normalize:
            self._compute_normalization_stats()
    
    def _scan_episodes(self):
        """扫描所有有效的 episode"""
        split_dir = self.data_root / "moma_release" / self.split
        
        for ep_dir in sorted(split_dir.iterdir()):
            if not ep_dir.name.startswith("episode_"):
                continue
            
            # 加载元数据
            meta_file = ep_dir / "metadata.json"
            if not meta_file.exists():
                continue
            
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            
            # 难度过滤
            if self.difficulty:
                task_diff = meta.get("task", {}).get("difficulty", "medium")
                if task_diff not in self.difficulty:
                    continue
            
            # 物体数量过滤
            num_objs = meta.get("task", {}).get("num_objects", 1)
            if num_objs < self.min_objects:
                continue
            
            # 加载任务定义
            task_file = ep_dir / "task.json"
            if task_file.exists():
                with open(task_file, 'r') as f:
                    task = json.load(f)
            else:
                task = {}
            
            self.episodes.append({
                "path": ep_dir,
                "meta": meta,
                "task": task,
                "task_id": meta.get("task_id", ep_dir.name),
                "scene_id": meta.get("scene_id", "unknown"),
                "difficulty": meta.get("task", {}).get("difficulty", "medium"),
                "num_objects": num_objs,
                "language_instruction": meta.get("language_instruction", "")
            })
        
        print(f"[{self.split}] 加载了 {len(self.episodes)} 个有效 episode")
    
    def _compute_normalization_stats(self):
        """计算归一化参数"""
        print("计算归一化参数...")
        
        sample_size = min(100, len(self.episodes))
        sampled_idx = np.random.choice(len(self.episodes), sample_size, replace=False)
        
        all_base_positions = []
        all_arm_joints = []
        all_actions = []
        
        for idx in sampled_idx:
            try:
                traj_file = self.episodes[idx]["path"] / "trajectory.csv"
                df = pd.read_csv(traj_file)
                
                base_pos = df[["base_x", "base_y"]].values
                arm_joints = df[[f"arm_joint_{i}" for i in range(6)]].values
                
                # 动作 = 状态增量
                base_action = np.diff(base_pos, axis=0)
                base_action = np.vstack([base_action, base_action[-1]])
                
                all_base_positions.append(base_pos)
                all_arm_joints.append(arm_joints)
                all_actions.append(base_action)
            except Exception:
                continue
        
        if all_base_positions:
            all_base = np.concatenate(all_base_positions, axis=0)
            all_arm = np.concatenate(all_arm_joints, axis=0)
            all_act = np.concatenate(all_actions, axis=0)
            
            self.base_mean = torch.FloatTensor(all_base.mean(axis=0))
            self.base_std = torch.FloatTensor(all_base.std(axis=0) + 1e-7)
            self.arm_mean = torch.FloatTensor(all_arm.mean(axis=0))
            self.arm_std = torch.FloatTensor(all_arm.std(axis=0) + 1e-7)
            self.action_mean = torch.FloatTensor(all_act.mean(axis=0))
            self.action_std = torch.FloatTensor(all_act.std(axis=0) + 1e-7)
        else:
            self.base_mean = torch.zeros(2)
            self.base_std = torch.ones(2)
            self.arm_mean = torch.zeros(6)
            self.arm_std = torch.ones(6)
            self.action_mean = torch.zeros(2)
            self.action_std = torch.ones(2)
    
    def _load_trajectory(self, ep_path: Path) -> Dict[str, np.ndarray]:
        """加载单个 episode 的轨迹数据"""
        traj_file = ep_path / "trajectory.csv"
        df = pd.read_csv(traj_file)
        
        # 底盘状态：位置 (x, y) + 朝向角 theta
        base_state = df[["base_x", "base_y", "base_theta"]].values
        
        # 臂部状态：6 个关节角
        arm_joints = df[[f"arm_joint_{i}" for i in range(6)]].values
        
        # 末端执行器位姿
        ee_pose = df[["ee_x", "ee_y", "ee_z", "ee_qx", "ee_qy", "ee_qz", "ee_qw"]].values
        
        # 夹爪状态
        gripper = df["gripper_position"].values
        
        # 时间戳
        timestamps = df["timestamp"].values
        
        return {
            "timestamps": timestamps.astype(np.float64),
            "base_state": base_state.astype(np.float32),
            "arm_joints": arm_joints.astype(np.float32),
            "ee_pose": ee_pose.astype(np.float32),
            "gripper": gripper.astype(np.float32)
        }
    
    def _load_image(self, ep_path: Path, frame_idx: int, modality: str = "rgb") -> np.ndarray:
        """加载单帧图像"""
        if modality == "rgb":
            img_dir = ep_path / "images" / "rgb"
            img_name = f"rgb_{frame_idx:05d}.jpg"
        else:
            img_dir = ep_path / "images" / "depth"
            img_name = f"depth_{frame_idx:05d}.png"
        
        img_path = img_dir / img_name
        if not img_path.exists():
            return np.zeros((*self.image_size, 3 if modality == "rgb" else 1), dtype=np.uint8)
        
        img = cv2.imread(str(img_path))
        if img is None:
            return np.zeros((*self.image_size, 3 if modality == "rgb" else 1), dtype=np.uint8)
        
        if modality == "rgb":
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img = img.astype(np.float32) / 1000.0  # 深度图转米
        
        img = cv2.resize(img, self.image_size)
        return img
    
    def __len__(self) -> int:
        return len(self.episodes)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """获取一个 episode 的数据"""
        ep = self.episodes[idx]
        traj = self._load_trajectory(ep["path"])
        
        T = len(traj["timestamps"])
        
        # 构建设状态向量：底盘(3) + 臂部(6) + 夹爪(1) = 10维
        state = np.concatenate([
            traj["base_state"],
            traj["arm_joints"],
            traj["gripper"].reshape(-1, 1)
        ], axis=1).astype(np.float32)
        
        # 动作 = 底盘位置增量 + 臂部关节增量
        base_action = np.diff(traj["base_state"][:, :2], axis=0)
        base_action = np.vstack([base_action, base_action[-1]])
        
        arm_action = np.diff(traj["arm_joints"], axis=0)
        arm_action = np.vstack([arm_action, arm_action[-1]])
        
        action = np.concatenate([base_action, arm_action], axis=1).astype(np.float32)
        
        state = torch.FloatTensor(state)
        action = torch.FloatTensor(action)
        
        if self.normalize:
            # 归一化：底盘 + 臂部
            base_part = (state[:, :3] - self.base_mean) / self.base_std
            arm_part = (state[:, 3:9] - self.arm_mean) / self.arm_std
            gripper_part = state[:, 9:10]
            state = torch.cat([base_part, arm_part, gripper_part], dim=1)
            
            action_base = (action[:, :2] - self.action_mean) / self.action_std
            action_arm = action[:, 2:]
            action = torch.cat([action_base, action_arm], dim=1)
        
        # 序列截断
        seq_len = min(T, self.seq_length)
        state = state[:seq_len]
        action = action[:seq_len]
        
        return {
)
    
    def _load_trajectory(self, ep_path: Path) -> List[Dict]:
        """加载单个 episode 的轨迹数据"""
        traj_file = ep_path / "trajectory.json"
        if not traj_file.exists():
            return []
        
        with open(traj_file, 'r') as f:
            trajectory = json.load(f)
        
        return trajectory
    
    def __len__(self) -> int:
        return len(self.episodes)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        获取一个 episode 的数据
        
        返回:
            dict: 包含以下键的字典
                - base_states: 底盘状态序列 (seq_len, 5)
                - arm_states: 机械臂状态序列 (seq_len, 10)
                - actions: 动作序列 (seq_len, 10)
                - task_name: 任务名称
                - success: 是否成功
                - robot_type: 机器人类型
        """
        ep = self.episodes[idx]
        trajectory = self._load_trajectory(ep["path"])
        
        # 提取状态和动作序列
        base_states = []
        arm_states = []
        actions = []
        
        for frame in trajectory:
            # 底盘状态
            base = frame.get("base_state", {})
            base_pos = base.get("position", [0, 0])
            base_yaw = base.get("orientation", 0)
            base_vel = base.get("velocity", [0, 0])
            base_state = base_pos + [base_yaw] + base_vel
            
            # 机械臂状态
            arm = frame.get("arm_state", {})
            arm_joints = arm.get("joint_positions", [0] * 7)
            ee_pos = arm.get("end_effector_pose", {}).get("position", [0, 0, 0])
            arm_state = arm_joints + ee_pos
            
            # 动作
            action_data = frame.get("action", {})
            base_action = action_data.get("base_velocity", [0, 0])
            arm_action = action_data.get("arm_delta", [0] * 7)
            gripper_action = [action_data.get("gripper_action", 0)]
            action = base_action + arm_action + gripper_action
            
            base_states.append(base_state)
            arm_states.append(arm_state)
            actions.append(action)
        
        base_states = np.array(base_states, dtype=np.float32)
        arm_states = np.array(arm_states, dtype=np.float32)
        actions = np.array(actions, dtype=np.float32)
        
        # 归一化
        if self.normalize:
            base_states = (base_states - self.base_state_mean.numpy()) / self.base_state_std.numpy()
            arm_states = (arm_states - self.arm_state_mean.numpy()) / self.arm_state_std.numpy()
            actions = (actions - self.action_mean.numpy()) / self.action_std.numpy()
        
        # 转换为 tensor
        base_states = torch.FloatTensor(base_states)
        arm_states = torch.FloatTensor(arm_states)
        actions = torch.FloatTensor(actions)
        
        # 截断到指定序列长度
        seq_len = min(len(actions), self.seq_length)
        base_states = base_states[:seq_len]
        arm_states = arm_states[:seq_len]
        actions = actions[:seq_len]
        
        return {
            "base_states": base_states,
            "arm_states": arm_states,
            "actions": actions,
            "task_name": ep["task_name"],
            "success": torch.tensor(ep["success"], dtype=torch.float32),
            "robot_type": ep["robot_type"]
        }


def create_moma_dataloader(
    data_root: str,
    split: str = "train",
    batch_size: int = 32,
    robot_type: Optional[List[str]] = None,
    task_types: Optional[List[str]] = None,
    difficulty_levels: Optional[List[str]] = None,
    shuffle: bool = True,
    num_workers: int = 4,
    seq_length: int = 32
) -> DataLoader:
    """
    创建 MOMA 数据加载器
    
    参数:
        data_root: 数据集根目录
        split: 数据集划分
        batch_size: 批次大小
        robot_type: 机器人类型过滤
        task_types: 任务类型过滤
        difficulty_levels: 难度等级过滤
        shuffle: 是否打乱
        num_workers: 数据加载线程数
        seq_length: 序列长度
    
    返回:
        DataLoader 实例
    """
    dataset = MOMADataset(
        data_root=data_root,
        split=split,
        robot_type=robot_type,
        task_types=task_types,
        difficulty_levels=difficulty_levels,
        normalize=True,
        seq_length=seq_length
    )
    
    def collate_fn(batch):
        """自定义批次整理函数"""
        max_len = max(item["actions"].shape[0] for item in batch)
        
        padded_base = []
        padded_arm = []
        padded_actions = []
        masks = []
        
        for item in batch:
            seq_len = item["actions"].shape[0]
            pad_len = max_len - seq_len
            
            if pad_len > 0:
                # Padding：用最后一步填充
                base_pad = torch.cat([item["base_states"]] * (pad_len // seq_len + 1), dim=0)[:pad_len]
                arm_pad = torch.cat([item["arm_states"]] * (pad_len // seq_len + 1), dim=0)[:pad_len]
                action_pad = torch.cat([item["actions"]] * (pad_len // seq_len + 1), dim=0)[:pad_len]
                
                base = torch.cat([item["base_states"], base_pad], dim=0)
                arm = torch.cat([item["arm_states"], arm_pad], dim=0)
                action = torch.cat([item["actions"], action_pad], dim=0)
                mask = torch.cat([torch.ones(seq_len), torch.zeros(pad_len)], dim=0)
            else:
                base = item["base_states"]
                arm = item["arm_states"]
                action = item["actions"]
                mask = torch.ones(seq_len)
            
            padded_base.append(base)
            padded_arm.append(arm)
            padded_actions.append(action)
            masks.append(mask)
        
        return {
            "base_states": torch.stack(padded_base),      # (batch, max_len, 5)
            "arm_states": torch.stack(padded_arm),        # (batch, max_len, 10)
            "actions": torch.stack(padded_actions),      # (batch, max_len, 10)
            "mask": torch.stack(masks),                  # (batch, max_len)
            "task_names": [item["task_name"] for item in batch],
            "success": torch.stack([item["success"] for item in batch]),
            "robot_types": [item["robot_type"] for item in batch]
        }
    
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        collate_fn=collate_fn,
        pin_memory=True
    )
```

### 6.2 轨迹可视化

下面实现 MOMA 轨迹的可视化功能：

```python
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from typing import List, Dict, Optional

def visualize_moma_trajectory(trajectory: List[Dict], save_path: Optional[str] = None):
    """
    可视化 MOMA 移动操作轨迹
    
    参数:
        trajectory: MOMA 轨迹数据列表
        save_path: 保存路径（PNG）
    """
    # 提取底盘轨迹（2D 位置）
    base_positions = np.array([
        frame["base_state"]["position"]
        for frame in trajectory if "base_state" in frame
    ])
    
    # 提取末端执行器 3D 轨迹
    ee_positions = np.array([
        frame["arm_state"]["end_effector_pose"]["position"]
        for frame in trajectory if "arm_state" in frame
    ])
    
    # 提取夹爪状态
    gripper_states = np.array([
        frame["arm_state"]["gripper_state"]
        for frame in trajectory if "arm_state" in frame
    ])
    
    fig = plt.figure(figsize=(16, 5))
    
    # 左图：底盘移动轨迹（俯视图）
    ax1 = fig.add_subplot(131)
    ax1.plot(base_positions[:, 0], base_positions[:, 1], 'b-', linewidth=2, alpha=0.6)
    ax1.scatter(base_positions[0, 0], base_positions[0, 1], c='green', s=100, 
                label='起点', zorder=5)
    ax1.scatter(base_positions[-1, 0], base_positions[-1, 1], c='red', s=100, 
                label='终点', zorder=5)
    ax1.set_xlabel('X (m)')
    ax1.set_ylabel('Y (m)')
    ax1.set_title('底盘移动轨迹（俯视图）')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.axis('equal')
    
    # 中图：末端执行器 3D 轨迹
    ax2 = fig.add_subplot(132, projection='3d')
    colors = ['green' if g > 0.5 else 'red' for g in gripper_states]
    ax2.scatter(ee_positions[:, 0], ee_positions[:, 1], ee_positions[:, 2], 
                c=colors, s=5, alpha=0.6)
    ax2.plot(ee_positions[:, 0], ee_positions[:, 1], ee_positions[:, 2], 
             'b-', alpha=0.3, linewidth=1)
    ax2.set_xlabel('X (m)')
    ax2.set_ylabel('Y (m)')
    ax2.set_zlabel('Z (m)')
    ax2.set_title('末端执行器 3D 轨迹\n绿=夹爪闭合，红=夹爪张开')
    
    # 右图：底盘+末端轨迹时间对比
    ax3 = fig.add_subplot(133)
    time = np.arange(len(base_positions)) / 30.0  # 假设 30Hz
    
    ax3.plot(time, base_positions[:, 0], label='底盘 X', alpha=0.8)
    ax3.plot(time, base_positions[:, 1], label='底盘 Y', alpha=0.8)
    if len(ee_positions) > 0:
        # 归一化到同一尺度便于对比
        ee_z_normalized = (ee_positions[:, 2] - ee_positions[:, 2].min()) / \
                         (ee_positions[:, 2].max() - ee_positions[:, 2].min() + 1e-6)
        ee_z_scaled = ee_z_normalized * 2 + 1  # 缩放到 1~3m 范围
        ax3.plot(time[:len(ee_z_scaled)], ee_z_scaled, label='末端 Z（归一化）', alpha=0.8)
    
    ax3.set_xlabel('时间 (s)')
    ax3.set_ylabel('位置 (m)')
    ax3.set_title('位置随时间变化')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"轨迹图已保存: {save_path}")
    
    plt.show()
    plt.close()


def plot_moma_dataset_statistics(data_root: str):
    """
    绘制 MOMA 数据集统计信息
    
    包括：任务分布、难度分布、机器人类型分布、轨迹长度分布
    """
    data_root = Path(data_root)
    
    # 收集统计信息
    task_counts = {}
    difficulty_counts = {}
    robot_counts = {}
    trajectory_lengths = []
    
    for split in ["train", "val", "test"]:
        split_root = data_root / split
        if not split_root.exists():
            continue
        
        for ep_dir in sorted(split_root.iterdir()):
            if not ep_dir.name.startswith("episode_"):
                continue
            
            meta_file = ep_dir / "metadata.json"
            traj_file = ep_dir / "trajectory.json"
            
            if not meta_file.exists() or not traj_file.exists():
                continue
            
            try:
                with open(meta_file) as f:
                    meta = json.load(f)
                
                with open(traj_file) as f:
                    traj = json.load(f)
                
                # 任务类型
                task = meta.get("task_name", "unknown")
                task_counts[task] = task_counts.get(task, 0) + 1
                
                # 难度等级
                diff = meta.get("difficulty", {}).get("level", "unknown")
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
                
                # 机器人类型
                robot = meta.get("robot_type", "unknown")
                robot_counts[robot] = robot_counts.get(robot, 0) + 1
                
                # 轨迹长度
                trajectory_lengths.append(len(traj))
                
            except Exception:
                continue
    
    # 创建图表
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 任务类型分布
    if task_counts:
        tasks = list(task_counts.keys())[:10]  # 最多显示前10个
        counts = [task_counts[t] for t in tasks]
        axes[0, 0].barh(tasks, counts)
        axes[0, 0].set_xlabel('Episode 数量')
        axes[0, 0].set_title('任务类型分布（Top 10）')
    
    # 难度等级分布
    if difficulty_counts:
        diffs = list(difficulty_counts.keys())
        diff_vals = list(difficulty_counts.values())
        axes[0, 1].bar(diffs, diff_vals, color=['green', 'yellow', 'orange', 'red'])
        axes[0, 1].set_xlabel('难度等级')
        axes[0, 1].set_ylabel('Episode 数量')
        axes[0, 1].set_title('难度等级分布')
    
    # 机器人类型分布
    if robot_counts:
        robots = list(robot_counts.keys())
        robot_vals = list(robot_counts.values())
        axes[1, 0].bar(robots, robot_vals, color=['blue', 'purple', 'cyan'])
        axes[1, 0].set_xlabel('机器人类型')
        axes[1, 0].set_ylabel('Episode 数量')
        axes[1, 0].set_title('机器人类型分布')
    
    # 轨迹长度分布
    if trajectory_lengths:
        axes[1, 1].hist(trajectory_lengths, bins=50, edgecolor='black', alpha=0.7)
        axes[1, 1].set_xlabel('轨迹长度（帧）')
        axes[1, 1].set_ylabel('Episode 数量')
        axes[1, 1].set_title(f'轨迹长度分布\n均值: {np.mean(trajectory_lengths):.0f} 帧')
        axes[1, 1].axvline(np.mean(trajectory_lengths), color='r', linestyle='--', label='均值')
        axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig('moma_statistics.png', dpi=150)
    print(f"统计图已保存: moma_statistics.png")
    plt.close()
```

### 6.3 评估脚本

下面实现 MOMA 策略的评估脚本：

```python
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List
import json

def evaluate_mobile_manipulation_policy(
    policy,
    test_data_root: str,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
    max_episodes: int = 100
) -> Dict[str, float]:
    """
    评估移动操作策略
    
    参数:
        policy: 训练好的策略模型
        test_data_root: 测试数据根目录
        device: 计算设备
        max_episodes: 最大评估 episode 数
    
    返回:
        评估指标字典
    """
    policy.eval()
    policy.to(device)
    
    dataset = MOMADataset(
        data_root=test_data_root,
        split="test",
        normalize=True,
        seq_length=32
    )
    
    success_count = 0
    total_base_error = 0.0
    total_arm_error = 0.0
    total_gripper_error = 0.0
    num_steps = 0
    
    with torch.no_grad():
        for i in range(min(max_episodes, len(dataset))):
            data = dataset[i]
            
            base_states = data["base_states"].to(device).unsqueeze(0)
            arm_states = data["arm_states"].to(device).unsqueeze(0)
            actions = data["actions"]
            
            # 合并状态
            combined_state = torch.cat([base_states, arm_states], dim=-1)
            
            # 预测动作
            pred_actions = policy(combined_state)
            
            # 计算误差（前2维：底盘速度误差；后8维：臂+夹爪误差）
            pred_np = pred_actions.squeeze(0).cpu().numpy()
            target_np = actions.numpy()
            
            # 对每个时间步计算误差
            for t in range(min(len(pred_np), len(target_np))):
                # 底盘动作误差（前2维）
                base_error = np.linalg.norm(pred_np[t, :2] - target_np[t, :2])
                total_base_error += base_error
                
                # 机械臂动作误差（后8维）
                arm_error = np.linalg.norm(pred_np[t, 2:] - target_np[t, 2:])
                total_arm_error += arm_error
                
                num_steps += 1
            
            # 简单的成功判定：平均误差小于阈值
            avg_error = total_base_error / max(num_steps, 1) + \
                        total_arm_error / max(num_steps, 1)
            
            if avg_error < 0.2:  # 阈值 0.2（归一化后）
                success_count += 1
    
    num_episodes = min(max_episodes, len(dataset))
    
    results = {
        "success_rate": success_count / max(num_episodes, 1),
        "avg_base_error": total_base_error / max(num_steps, 1),
        "avg_arm_error": total_arm_error / max(num_steps, 1),
        "num_evaluated": num_episodes,
        "total_steps": num_steps
    }
    
    print(f"评估结果：")
    print(f"  成功率: {results['success_rate']:.2%}")
    print(f"  平均底盘误差: {results['avg_base_error']:.4f}")
    print(f"  平均机械臂误差: {results['avg_arm_error']:.4f}")
    print(f"  评估 Episode 数: {results['num_evaluated']}")
    
    return results


def run_moma_challenge_evaluation(
    policy,
    challenge_data_root: str,
    output_dir: str = "./results"
) -> str:
    """
    运行 MOMA-Challenge 风格的多维度评估
    
    参数:
        policy: 待评估策略
        challenge_data_root: 竞赛数据目录
        output_dir: 结果输出目录
    
    返回:
        结果文件路径
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    policy.eval()
    policy.to(device)
    
    dataset = MOMADataset(
        data_root=challenge_data_root,
        split="test",
        normalize=True,
        seq_length=32
    )
    
    results = []
    
    for i, ep_info in enumerate(dataset.episodes[:100]):  # 评估前100个任务
        episode_path = ep_info["path"]
        
        # 加载轨迹
        with open(episode_path / "trajectory.json") as f:
            trajectory = json.load(f)
        
        # 加载任务规范
        with open(episode_path / "metadata.json") as f:
            meta = json.load(f)
        
        # 模拟执行
        episode_reward = 0.0
        collision_count = 0
        execution_time = 0.0
        
        for step_idx, step_data in enumerate(trajectory):
            # 构造观测
            base = step_data.get("base_state", {})
            arm = step_data.get("arm_state", {})
            
            base_state = np.array(
                base.get("position", [0, 0]) + 
                [base.get("orientation", 0)] + 
                base.get("velocity", [0, 0]),
                dtype=np.float32
            )
            arm_state = np.array(
                arm.get("joint_positions", [0] * 7) + 
                arm.get("end_effector_pose", {}).get("position", [0, 0, 0]),
                dtype=np.float32
            )
            
            # 合并观测
            obs = torch.FloatTensor(
                np.concatenate([base_state, arm_state])
            ).unsqueeze(0).to(device)
            
            # 策略预测
            with torch.no_grad():
                action = policy(obs).squeeze(0).cpu().numpy()
            
            # 模拟奖励（实际应用中需要仿真环境）
            step_reward = -0.01  # 每步小惩罚
            episode_reward += step_reward
            
            # 模拟碰撞检测
            if np.random.random() < 0.01:  # 1% 概率碰撞
                collision_count += 1
                episode_reward -= 1.0
            
            # 时间累计
            execution_time += 1.0 / 30.0  # 假设 30Hz
        
        # 判断成功（实际根据任务目标判定）
        time_limit = meta.get("difficulty", {}).get("time_limit", 120.0)
        success = episode_reward > -10.0 and collision_count < 5
        
        # 计算路径效率
        base_positions = [
            frame["base_state"]["position"]
            for frame in trajectory if "base_state" in frame
        ]
        if len(base_positions) >= 2:
            path_length = sum(
                np.linalg.norm(np.array(base_positions[i+1]) - np.array(base_positions[i]))
                for i in range(len(base_positions) - 1)
            )
        else:
            path_length = 0.0
        
        results.append({
            "task_id": ep_info["task_name"],
            "success": success,
            "execution_time": execution_time,
            "path_length": path_length,
            "collision_count": collision_count,
            "reward": episode_reward,
            "path_efficiency": min(1.0, 10.0 / max(path_length, 0.1))  # 假设最优路径10m
        })
    
    # 保存结果
    output_file = Path(output_dir) / "challenge_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # 计算综合评分
    success_rate = np.mean([r["success"] for r in results])
    avg_time = np.mean([r["execution_time"] for r in results])
    avg_collision = np.mean([r["collision_count"] for r in results])
    avg_efficiency = np.mean([r["path_efficiency"] for r in results])
    
    # MOMA 综合评分公式
    T_max = 120.0  # 最大允许时间
    S_total = (
        0.4 * float(success_rate) +
        0.2 * max(0, (T_max - avg_time) / T_max) +
        0.15 * avg_efficiency +
        0.15 * max(0, 1.0 - avg_collision / 10.0) +
        0.1 * max(0, 1.0 - avg_collision / 5.0)
    )
    
    summary = {
        "success_rate": float(success_rate),
        "avg_execution_time": float(avg_time),
        "avg_collision_count": float(avg_collision),
        "avg_path_efficiency": float(avg_efficiency),
        "composite_score": float(S_total),
        "num_tasks": len(results)
    }
    
    with open(Path(output_dir) / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n===== MOMA-Challenge 评估结果 =====")
    print(f"任务数: {summary['num_tasks']}")
    print(f"成功率: {summary['success_rate']:.2%}")
    print(f"平均执行时间: {summary['avg_execution_time']:.1f}s")
    print(f"平均碰撞次数: {summary['avg_collision_count']:.2f}")
    print(f"平均路径效率: {summary['avg_path_efficiency']:.2%}")
    print(f"综合评分: {summary['composite_score']:.3f}")
    print(f"=====================================")
    
    return str(output_file)
```

---

## 7. 练习题

### 选择题

1. **MOMA 数据集的"移动操作"中的"移动"指的是？**
   - A. 机械臂关节的移动
   - B. 机器人底盘的空间移动
   - C. 末端执行器的移动
   - D. 相机视角的移动

2. **MOMA-Large 数据集中，Fetch 机器人类型的 Episode 占比约是？**
   - A. 20%
   - B. 25%
   - C. 55%
   - D. 80%

3. **MOMA 的 10 维动作空间中，前 2 维表示？**
   - A. 机械臂末端位置增量
   - B. 底盘速度（线速度 + 角速度）
   - C. 夹爪开度
   - D. 相机视角

4. **MOMA-Challenge 综合评分公式中，成功率的权重是？**
   - A. 10%
   - B. 15%
   - C. 20%
   - D. 40%

5. **MOMA-Large 的任务复杂度分层中，L3 代表？**
   - A. 近距离操作（导航距离 < 2m）
   - B. 中距离移动（2-10m）
   - C. 远距离导航+操作（> 10m）
   - D. 开放域任务

### 填空题

6. **MOMA 动作空间的第 8-10 维依次表示 ________、________、________。**

7. **MOMA 的底盘状态包含 2D 位置、朝向角和速度，其中速度是 ________ 维向量。**

8. **MOMA-Challenge 的多维度评估体系包含 5 个指标：成功率、执行时间、路径效率、________ 和 ________。**

9. **端到端模仿学习策略网络的激光雷达编码器输入维度是 ________。**

10. **MOMA 场景描述中的 `navigation_goals` 字段用于标注 ________ 的位置和朝向信息。**

### 简答题

11. **比较固定基座机械臂和移动机械臂的操作难点，说明为什么 MOMA 的数据采集更复杂。**

12. **说明 MOMA-Challenge 综合评分公式中各项指标的含义及权重分配的依据。**

13. **描述 MOMA-Large 四级任务复杂度（L1-L4）的设计逻辑及其对策略训练的帮助。**

14. **解释端到端模仿学习和分层策略各自的优缺点。**

15. **说明 MOMA 数据集在归一化参数计算中，为什么底盘状态和机械臂状态需要分别归一化？**

### 编程题

16. **编写代码实现按难度等级统计 MOMA 数据集中各难度等级的 Episode 数量**：
    - 输入：数据集根目录
    - 输出：各难度等级（L1-L4）的数量统计
    - 要求：分别统计 train/val/test 三个划分

17. **基于 MOMA 数据集，实现一个简单的移动操作评估函数**：
    - 输入：一段演示轨迹的 base_state 序列
    - 计算底盘移动总距离、平均速度、轨迹平滑度
    - 输出：综合运动质量评分

18. **实现一个分层移动操作策略的训练脚本**：
    - 高层策略：语言指令 -> 导航目标点
    - 低层策略：视觉 + 状态 -> 动作
    - 使用行为克隆损失训练
    - 支持断点续训

---

## 8. 练习题答案

### 选择题

1. **答案：B**
   - MOMA 的"移动"指机器人底盘（Mobile Base）的空间移动，能够让机器人在整个室内空间内导航和操作

2. **答案：C**
   - Fetch 机器人占比约 55%，PR2 约 25%，Stretch 约 20%

3. **答案：B**
   - 前 2 维是底盘速度 $(v_x, v_\omega)$，线速度 + 角速度

4. **答案：D**
   - 成功率的权重是 40%，是所有指标中权重最高的

5. **答案：C**
   - L3 是远距离导航+操作，导航距离 > 10m，涉及多物体和长时序任务

### 填空题

6. **答案：第7个关节增量、第6个关节增量、夹爪目标开度**
   - 动作空间 10 维：$[v_x, v_\omega, \Delta q_1, \Delta q_2, \Delta q_3, \Delta q_4, \Delta q_5, \Delta q_6, \Delta q_7, g]$
   - 其中 $\Delta q_7$ 是第7关节增量，$g$ 是夹爪

7. **答案：2**
   - 速度是 $(v_x, v_\omega)$ 两个分量：线速度（m/s）和角速度（rad/s）

8. **答案：操作精度、安全性**
   - 五个指标：任务成功率（40%）、执行时间（20%）、路径效率（15%）、操作精度（15%）、安全性（10%）

9. **答案：360**
   - 激光雷达编码器输入是 360 维向量（360 束激光扫描）

10. **答案：导航目标点**
    - `navigation_goals` 标注了场景中各个可导航目标点的位置 $(x, y)$ 和朝向角

### 简答题

11. **固定基座 vs 移动机械臂操作难点对比**：

| 维度 | 固定基座机械臂 | 移动机械臂 |
|------|--------------|-----------|
| 工作空间 | 固定，通常约 1m³ | 可移动，覆盖整个室内空间 |
| 基坐标系 | 固定不变 | 随底盘移动持续变化 |
| 定位问题 | 一次性标定 | 需要持续定位和重定位 |
| 控制耦合 | 无耦合 | 底盘运动与臂运动相互影响 |
| 数据采集 | 仅需记录臂关节和末端 | 需同步记录底盘 + 臂 + 激光雷达 |

**MOMA 数据采集更复杂的原因**：
- 需要同步记录底盘和机械臂两个子系统
- 激光雷达数据的实时处理
- 导航和操作之间的协调标注
- 多场景（家庭/办公室/工厂）的环境布置成本高

12. **MOMA-Challenge 综合评分公式解析**：

| 指标 | 权重 | 含义 |
|------|------|------|
| 成功率 | 40% | 任务是否完成，权重最高因为这是核心指标 |
| 执行时间 | 20% | 效率指标，鼓励快速完成任务 |
| 路径效率 | 15% | 路径优化程度，间接反映导航规划质量 |
| 操作精度 | 15% | 物体放置精度、夹爪对齐度等 |
| 安全性 | 10% | 碰撞和力限幅违规，权重最低但不可忽视 |

权重分配依据：任务成功是最重要的目标，因此权重最高；安全性和精度虽然重要但属于辅助指标，因此权重相对较低。

13. **MOMA-Large 四级任务复杂度设计逻辑**：

**L1（近距离操作 < 2m）**：
- 让策略先学习基础的机械臂操作技能
- 排除导航干扰，专注于抓取、放置等核心操作

**L2（中距离移动 2-10m）**：
- 引入导航能力，学习底盘和臂的协调控制
- 任务更加真实，需要在移动过程中保持操作

**L3（远距离 > 10m）**：
- 测试长距离导航和复杂多步操作的鲁棒性
- 数据量占比最大（30%），覆盖主流应用场景

**L4（开放域）**：
- 最高难度，需要语言理解、推理和规划能力
- 促进 VLN（视觉-语言-导航）方向的探索

这种分层设计的帮助：
- 可以渐进式训练（先 L1 后 L2/L3）
- 便于分析策略在不同复杂度下的表现
- 为课程学习（Curriculum Learning）提供天然支撑

14. **端到端 vs 分层策略对比**：

**端到端模仿学习**：
- 优点：不需要手动设计中间表示；可以利用数据自动学习有用的特征；架构统一，易于实现
- 缺点：需要大量数据才能训练好；可解释性差；难以调试；难以保证安全约束

**分层策略**：
- 优点：每一层可以独立设计和调试；可以利用传统导航/操作算法；可解释性好；安全性更容易保证（可以在高层加入约束）
- 缺点：需要手工设计中间表示；层与层之间的误差可能累积；需要更多的领域知识

15. **底盘和机械臂状态分别归一化的原因**：

底盘状态和机械臂状态的**物理含义和数值范围完全不同**：
- 底盘位置单位是米，范围可能是 0-20m
- 机械臂关节角度单位是弧度，范围可能是 -3.14 到 3.14
- 末端位置也是米，范围可能只有 0-1m

如果合并归一化：
- 不同量纲的特征会相互干扰
- 收敛速度会受最不敏感维度的主导
- 模型难以平衡对不同状态的关注

分别归一化可以保证：
- 每种状态都在 $[-1, 1]$ 或 $[0, 1]$ 范围内
- 模型对底盘和臂的学习更加平衡
- 避免因数值尺度差异导致的梯度问题

### 编程题答案

16. **按难度等级统计**：

```python
import json
from pathlib import Path
from collections import defaultdict

def count_episodes_by_difficulty(data_root: str):
    """
    按难度等级统计 MOMA Episode 数量
    
    参数:
        data_root: MOMA 数据集根目录
    
    返回:
        dict: 各划分各难度等级的统计
    """
    data_root = Path(data_root)
    results = defaultdict(lambda: defaultdict(int))
    
    for split in ["train", "val", "test"]:
        split_root = data_root / split
        if not split_root.exists():
            continue
        
        for ep_dir in sorted(split_root.iterdir()):
            if not ep_dir.name.startswith("episode_"):
                continue
            
            meta_file = ep_dir / "metadata.json"
            if not meta_file.exists():
                continue
            
            try:
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                
                difficulty = meta.get("difficulty", {}).get("level", "unknown")
                results[split][difficulty] += 1
                
            except Exception:
                continue
    
    # 打印结果
    print("=" * 50)
    print("MOMA 数据集难度等级统计")
    print("=" * 50)
    
    all_levels = ["L1", "L2", "L3", "L4", "unknown"]
    
    for split in ["train", "val", "test"]:
        print(f"\n{split.upper()} 集：")
        total = sum(results[split].values())
        for level in all_levels:
            count = results[split][level]
            pct = count / max(total, 1) * 100
            print(f"  {level}: {count:5d} ({pct:5.1f}%)")
        print(f"  总计: {total:5d}")
    
    return dict(results)

if __name__ == "__main__":
    stats = count_episodes_by_difficulty("./moma_supervised")
```

17. **移动操作评估函数**：

```python
import numpy as np

def evaluate_motion_quality(base_states_sequence):
    """
    评估底盘运动质量
    
    参数:
        base_states_sequence: 底盘状态列表
                             每项为 {"position": [x, y], "orientation": theta, "velocity": [vx, vw]}
    
    返回:
        dict: 包含各项运动质量指标的字典
    """
    if len(base_states_sequence) < 2:
        return {"total_distance": 0.0, "avg_speed": 0.0, 
                "smoothness": 0.0, "quality_score": 0.0}
    
    # 提取位置序列
    positions = np.array([s["position"] for s in base_states_sequence])
    velocities = np.array([s.get("velocity", [0, 0]) for s in base_states_sequence])
    orientations = np.array([s.get("orientation", 0) for s in base_states_sequence])
    
    # 1. 移动总距离
    diffs = np.diff(positions, axis=0)
    segment_distances = np.linalg.norm(diffs, axis=1)
    total_distance = segment_distances.sum()
    
    # 2. 平均速度（假设 30Hz）
    linear_speeds = velocities[:, 0]  # 线速度
    avg_speed = np.mean(np.abs(linear_speeds))
    
    # 3. 轨迹平滑度（基于加速度方差）
    accelerations = np.diff(velocities, axis=0) * 30.0  # 假设 30Hz
    smoothness = 1.0 / (1.0 + np.std(accelerations))  # 标准差越小越平滑
    
    # 4. 综合评分（0-100）
    distance_score = min(total_distance / 20.0, 1.0) * 30  # 距离得分（满分30）
    speed_score = min(avg_speed / 0.3, 1.0) * 30           # 速度得分（满分30）
    smooth_score = smoothness * 40                          # 平滑度得分（满分40）
    
    quality_score = distance_score + speed_score + smooth_score
    
    return {
        "total_distance": round(total_distance, 3),
        "avg_speed": round(avg_speed, 3),
        "smoothness": round(smoothness, 3),
        "quality_score": round(quality_score, 1),
        "grade": "A" if quality_score >= 80 else "B" if quality_score >= 60 else "C" if quality_score >= 40 else "D"
    }


# 18. 分层策略训练脚本（含断点续训）

import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from torch.utils.data import DataLoader
import json

class HighLevelPolicy(nn.Module):
    """
    高层策略：语言指令 -> 导航目标点
    
    使用简单的 MLP 实现
    """
    def __init__(self, lang_dim=128, hidden_dim=256, output_dim=3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(lang_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.Tanh()  # 输出归一化到 [-1, 1]
        )
        self.output_scale = nn.Parameter(torch.ones(output_dim) * 0.5)
    
    def forward(self, lang_feat):
        return self.net(lang_feat) * self.output_scale


class LowLevelPolicy(nn.Module):
    """
    低层策略：视觉特征 + 状态 -> 动作
    
    输入：图像特征 + 底盘状态 + 机械臂状态
    输出：9维动作（2底盘 + 7关节）
    """
    def __init__(self, vision_dim=128, state_dim=15, hidden_dim=256, action_dim=9):
        super().__init__()
        
        self.network = nn.Sequential(
            nn.Linear(vision_dim + state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh()
        )
        
        self.action_scale = nn.Parameter(torch.ones(action_dim) * 0.5)
    
    def forward(self, vision_feat, state):
        combined = torch.cat([vision_feat, state], dim=-1)
        action = self.network(combined) * self.action_scale
        return action


def train_hierarchical_policy(
    data_root: str,
    save_dir: str = "./checkpoints",
    epochs: int = 100,
    lr: float = 1e-3,
    batch_size: int = 64,
    device: str = "cuda"
):
    """
    分层移动操作策略训练
    
    参数:
        data_root: 数据集目录
        save_dir: 模型保存目录
        epochs: 训练轮数
        lr: 学习率
        batch_size: 批次大小
        device: 计算设备
    """
    from pathlib import Path
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    device = torch.device(device)
    
    # 加载数据
    print("加载数据集...")
    dataloader = create_moma_dataloader(
        data_root=data_root,
        split="train",
        batch_size=batch_size,
        shuffle=True,
        num_workers=4
    )
    
    # 创建模型
    print("初始化模型...")
    high_level = HighLevelPolicy().to(device)
    low_level = LowLevelPolicy().to(device)
    
    optimizer_h = torch.optim.Adam(high_level.parameters(), lr=lr)
    optimizer_l = torch.optim.Adam(low_level.parameters(), lr=lr)
    
    # 断点续训
    save_path_h = Path(save_dir) / "high_level_policy.pth"
    save_path_l = Path(save_dir) / "low_level_policy.pth"
    start_epoch = 0
    best_loss = float('inf')
    
    if save_path_h.exists():
        print("检测到已有模型，从检查点恢复...")
        checkpoint_h = torch.load(save_path_h, map_location=device)
        high_level.load_state_dict(checkpoint_h['model_state_dict'])
        optimizer_h.load_state_dict(checkpoint_h['optimizer_state_dict'])
        start_epoch = checkpoint_h['epoch'] + 1
        best_loss = checkpoint_h.get('best_loss', float('inf'))
        print(f"  从 epoch {start_epoch} 继续，最佳损失: {best_loss:.6f}")
    
    # 训练循环
    print(f"开始训练，共 {epochs} 个 epochs...")
    
    for epoch in range(start_epoch, epochs):
        high_level.train()
        low_level.train()
        
        total_loss_h = 0.0
        total_loss_l = 0.0
        num_batches = 0
        
        for batch in dataloader:
            # 模拟语言特征（实际应用中需要语言编码器）
            batch_size_actual = batch["base_states"].shape[0]
            lang_feat = torch.randn(batch_size_actual, 128).to(device)
            
            # 目标导航点（从轨迹末尾提取）
            # 实际应用中应该从任务规范中获取
            nav_targets = torch.randn(batch_size_actual, 3).to(device) * 0.5
            
            # 高层策略损失
            pred_nav = high_level(lang_feat)
            loss_h = nn.MSELoss()(pred_nav, nav_targets)
            
            optimizer_h.zero_grad()
            loss_h.backward()
            torch.nn.utils.clip_grad_norm_(high_level.parameters(), max_norm=1.0)
            optimizer_h.step()
            
            # 低层策略损失
            states = torch.cat([batch["base_states"], batch["arm_states"]], dim=-1).to(device)
            actions = batch["actions"].to(device)
            
            # 模拟视觉特征
            vision_feat = torch.randn(batch_size_actual, 128).to(device)
            pred_actions = low_level(vision_feat, states[:, -1, :])  # 取最后一帧
            
            loss_l = nn.MSELoss()(pred_actions, actions[:, -1, :])
            
            optimizer_l.zero_grad()
            loss_l.backward()
            torch.nn.utils.clip_grad_norm_(low_level.parameters(), max_norm=1.0)
            optimizer_l.step()
            
            total_loss_h += loss_h.item()
            total_loss_l += loss_l.item()
            num_batches += 1
        
        avg_loss_h = total_loss_h / max(num_batches, 1)
        avg_loss_l = total_loss_l / max(num_batches, 1)
        avg_total = avg_loss_h + avg_loss_l
        
        marker = " *" if avg_total < best_loss else ""
        if avg_total < best_loss:
            best_loss = avg_total
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs}, "
                  f"L_h={avg_loss_h:.6f}, L_l={avg_loss_l:.6f}, "
                  f"L_total={avg_total:.6f}{marker}")
        
        # 保存检查点
        if (epoch + 1) % 20 == 0:
            torch.save({
                'epoch': epoch,
                'model_state_dict': high_level.state_dict(),
                'optimizer_state_dict': optimizer_h.state_dict(),
                'best_loss': best_loss
            }, save_path_h)
            torch.save({
                'epoch': epoch,
                'model_state_dict': low_level.state_dict(),
                'optimizer_state_dict': optimizer_l.state_dict()
            }, save_path_l)
            print(f"  -> 保存检查点 (epoch={epoch+1})")
    
    # 最终保存
    torch.save(high_level.state_dict(), save_path_h)
    torch.save(low_level.state_dict(), save_path_l)
    print(f"\n训练完成！最佳损失: {best_loss:.6f}")
    print(f"模型保存位置: {save_dir}")

---

## 本章小结

本节课程系统介绍了 MOMA（Multi-Operation Mobile Manipulator）移动操作数据集系列：

1. **数据集概述**：MOMA 是专注于移动机械臂操作的大规模数据集系列，包含 MOMA-Supervised、MOMA-Challenge、MOMA-Large、MOMA-Industry 四个子数据集。与固定基座数据集相比，MOMA 的核心挑战在于底盘移动与机械臂操作的耦合问题

2. **MOMA-Challenge**：年度移动操作竞赛，包含移动抓取、物体归置、场景重建、人机交接等核心任务，采用 5 维度评估体系（成功率 40%、执行时间 20%、路径效率 15%、操作精度 15%、安全性 10%）

3. **MOMA-Large**：最大规模的移动操作数据集，80,000+ Episodes，涵盖 200+ 任务类型，按复杂度分为 L1-L4 四个层级，覆盖家庭（60%）、办公室（25%）、工厂（15%）等多种场景

4. **数据格式**：10 维动作空间（前 2 维底盘速度 + 后 7 维关节增量 + 1 维夹爪），包含底盘状态、机械臂状态、视觉观测等多模态信息

5. **使用方法**：支持 pip 安装、Docker 容器和源码编译三种方式，可配合 Habitat-Sim、PyBullet、Isaac Gym 等仿真环境使用

6. **代码实战**：实现了完整的数据加载器（支持多机器人/多任务过滤、归一化）、轨迹可视化工具（底盘轨迹 + 末端轨迹 + 时间序列）和分层策略训练脚本（高层语言->导航目标 + 低层视觉+状态->动作）

7. **练习题**：涵盖选择题、填空题、简答题和编程题，全面检验对 MOMA 数据集设计理念、数据格式、评估体系和代码实现的理解

---

**相关资源**：

- MOMA 官网：https://moma-dataset.github.io/
- GitHub 仓库：https://github.com/moma-dataset/moma
- MOMA-Challenge：https://moma-challenge.github.io/
- PyBullet Fetch 机器人：https://github.com/bulletphysics/bullet3
- Habitat-Sim：https://aihabitat.org/
