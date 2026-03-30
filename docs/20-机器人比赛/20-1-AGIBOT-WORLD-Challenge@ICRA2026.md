# 20-1 AGIBOT WORLD Challenge@ICRA2026

## 概述

AGIBOT WORLD Challenge@ICRA2026 是由智元机器人举办的具身智能国际竞赛，作为 ICRA 2026 官方赛事。本课程面向零基础小白，从知识点梳理到实战应用，帮助你快速入门并参与竞赛。

**总奖池：53万美元 + 机器人采购代金券**

---

## 一、竞赛扫盲：5分钟了解两大赛道

### 1.1 两大赛道对比

| 赛道 | Reasoning to Action（推理-操作） | World Model（世界模型） |
|------|----------------------------------|--------------------------|
| **核心能力** | 推理 + 动作执行 | 视频生成 |
| **任务** | 控制机器人完成真实操作 | 生成机器人动作视频 |
| **评测方式** | Genie Sim 3.0 仿真 | EWMBench 基准 |
| **最终目标** | 线下真机决赛 | 仅线上竞赛 |
| **适合方向** | 机器人控制、VLA | 视频生成、世界模型 |

### 1.2 两个赛道在做什么？

#### Reasoning to Action（推理-操作赛道）

```
输入: "把桌子上的苹果放进篮子里"
         │
         ▼
    理解指令（VLM）
         │
         ▼
    推理规划（ACoT）
         │
         ▼
    执行动作（机器人）
         │
         ▼
    成功/失败 → 评分
```

**关键词**：VLA（视觉-语言-动作模型）、双臂协作、Sim2Real

---

#### World Model（世界模型赛道）

```
输入: 机器人观测 + 动作信号
         │
         ▼
    理解当前状态（编码）
         │
         ▼
    生成未来视频（扩散模型）
         │
         ▼
    输出: 预测机器人在场景中的交互视频
```

**关键词**：视频生成、扩散模型、具身世界模型

---

## 一.5 预备知识：Docker 与基线执行环境

### 什么是 Docker？为什么比赛需要它？

#### 🐳 Docker 是什么？

**类比理解**：想象一下，你有一个**密封的集装箱（Container）**，里面包含了：
- 运行程序所需的所有工具（Python、CUDA、库等）
- 程序本身
- 程序运行的配置文件

这个集装箱可以在**任何货船（电脑）**上运输，且里面货物完好无损地运行。

```
你的电脑                        │        比赛服务器
                               │
┌─────────────────────┐    │    ┌─────────────────────┐
│ Python 3.10         │    │    │ Python 3.10         │
│ CUDA 12.1           │    │    │ CUDA 12.1           │    ← 环境要完全一致！
│ ffmpeg 4.4          │    │    │ ffmpeg 4.4          │
│ opencv 4.9          │    │    │ opencv 4.9          │
│ 我的模型代码         │    │    │                     │
└─────────────────────┘    │    └─────────────────────┘
                               │
    如果版本不一致 → 可能出错！无法运行！
```

**Docker 的作用**：把你的整个运行环境打包，提交给服务器，服务器用完全相同的环境运行你的代码。

#### 镜像 vs 容器

```
镜像（Image）    →  就像是一张蛋糕的模具模板
容器（Container）→  用模具实际做出的蛋糕

你可以用同一个镜像创建多个独立运行的容器
```

---

### 完整基线执行流程

#### 流程总览

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Step 1  │───▶│ Step 2  │───▶│ Step 3  │───▶│ Step 4  │───▶│ Step 5  │
│ 安装    │    │ 克隆    │    │ 构建    │    │ 运行    │    │ 提交    │
│ Docker  │    │ 代码    │    │ 镜像    │    │ 基线    │    │ 模型    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

---

#### Step 1: 安装 Docker

**含义**：在你的电脑上安装一个"集装箱管理器"

```bash
# 安装 Docker（Ubuntu/Debian）
sudo apt update
sudo apt install docker.io

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 把你自己加入 docker 组（这样不用每次都 sudo）
sudo usermod -aG docker $USER
newgrp docker  # 生效后重新登录
```

**为什么需要**：Docker 是让代码在服务器上运行的唯一方式。服务器不认识 Python 脚本，只认识 Docker 镜像。

---

#### Step 2: 克隆基线代码

**含义**：把官方提供的"作业参考"下载到你的电脑

```bash
# 克隆 ACoT-VLA 基线（赛道一）
git clone https://github.com/AgibotTech/ACoT-VLA.git
cd ACoT-VLA

# 或克隆 EVAC 基线（赛道二）
git clone https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline.git
cd AgiBotWorldChallengeICRA2026-WorldModelBaseline
```

**文件结构示例**：
```
ACoT-VLA/
├── src/                    # 源代码
│   └── openpi/            # 主要程序
├── scripts/               # 运行脚本
├── configs/               # 配置文件
├── README.md              # 说明文档
└── dockerfile             # Docker 构建配方
```

---

#### Step 3: 构建 Docker 镜像

**含义**：根据官方提供的"配方"，在本地构建一个完整的运行环境

```bash
# 进入项目目录
cd ACoT-VLA

# 构建镜像（约10-30分钟，取决于网速）
docker build -f ./scripts/dockerfile -t registry.agibot.com/genie-sim/open_source:latest .
```

**"镜像" 就像是一张照片**：一旦拍好（构建完成），就可以无限复制使用。

---

#### Step 4: 启动 Docker 容器

**含义**：让你的代码在"集装箱"里运行

```bash
# 启动一个交互式容器
./scripts/start_gui.sh

# 进入容器（另开一个终端）
./scripts/into.sh

# 现在你已经在容器内部了
# 所有命令都在这个隔离环境里运行
```

**容器内部示意**：
```
┌─────────────────────────────────────┐
│         Docker 容器内部              │
│                                     │
│  (base) user@container:~$          │  ← 命令行提示符
│                                     │
│  # 这里运行的所有程序都是隔离的       │
│  # 安装的库不会影响你的真实电脑       │
│  # 退出容器后，这些改动会消失         │
│                                     │
└─────────────────────────────────────┘
```

---

#### Step 5: 运行基线

##### 赛道一（ACoT-VLA）- 启动推理服务

```bash
# 在容器内
cd openpi

# 启动推理服务（占用 8999 端口）
uv run scripts/serve_policy.py --host='0.0.0.0' --port=8999 \
    policy:checkpoint \
    --policy.config=acot_icra_simulation_challenge_reasoning_to_action \
    --policy.dir ./checkpoints/select_color/29999

# 看到类似输出说明成功：
# INFO:websockets.server:server listening on 0.0.0.0:8999
```

##### 赛道二（EVAC）- 运行推理

```bash
# 在容器内
cd AgiBotWorldChallengeICRA2026-WorldModelBaseline

# 修改 scripts/infer.sh 中的路径后运行
bash scripts/infer.sh

# 输出目录: ACWM_dataset/
```

---

#### Step 6: 提交模型

**含义**：把你修改后的容器打包，上传到服务器

```bash
# 1. 打包你的容器
docker commit <container_id> your-registry.com/your-project:v1

# 2. 推送到公开仓库
docker push your-registry.com/your-project:v1

# 3. 在比赛网站提交镜像 URL
# https://agibot-world.com/challenge2026/reasoning2action
```

---

### 流程总结表

| 步骤 | 命令 | 含义 | 耗时 |
|------|------|------|------|
| 1. 安装 Docker | `apt install docker.io` | 安装集装箱管理器 | 5分钟 |
| 2. 克隆代码 | `git clone ...` | 下载官方基线 | 2分钟 |
| 3. 构建镜像 | `docker build ...` | 制作运行环境 | 10-30分钟 |
| 4. 启动容器 | `./scripts/start_gui.sh` | 进入隔离环境 | 1分钟 |
| 5. 运行基线 | `uv run scripts/...` | 测试/训练 | 可变 |
| 6. 提交模型 | `docker push ...` | 上传作品 | 5分钟 |

---

### 常见问题 FAQ

#### Q: Docker 占用多少空间？
A: 每个镜像约 5-20 GB，容器运行时会额外占用内存。

#### Q: 容器退出后代码还在吗？
A: 代码在宿主机上，容器只是运行环境。但如果你在容器内修改了代码，需要先 `docker commit` 保存。

#### Q: 可以同时运行多个容器吗？
A: 可以，每个容器是独立的环境。

#### Q: 报错 "permission denied"？
A: 运行 `sudo usermod -aG docker $USER` 然后重新登录。

---

## 二、知识点地图：从零到参赛

### 2.1 学习路径图

```
                    ┌─────────────────────────────────────────┐
                    │           VLA / 世界模型                │
                    │  Vision-Language-Action / World Model   │
                    └─────────────────┬─────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
    ┌───────────┐              ┌───────────┐              ┌───────────┐
    │   视觉    │              │   语言    │              │   动作    │
    │ Vision   │              │ Language │              │  Action   │
    └─────┬─────┘              └─────┬─────┘              └─────┬─────┘
          │                          │                          │
          ▼                          ▼                          ▼
    • 图像识别                • 自然语言理解            • 机器人控制
    • 深度相机                • 指令解析                • 双臂协同
    • 视频生成                • Prompt设计              • 轨迹预测
```

### 2.2 赛道选择建议

| 你的背景 | 推荐赛道 | 原因 |
|----------|----------|------|
| 有 ROS/机器人基础 | **Reasoning to Action** | 直接控制机器人 |
| 有扩散模型/视频生成基础 | **World Model** | 生成视频评估 |
| 有深度学习基础 | 两者皆可 | 学习成本相近 |
| 零基础 | **Reasoning to Action** | 基线更完善，文档更详细 |

---

## 三、赛道一：Reasoning to Action（推理-操作赛道）

> **适合方向**：机器人控制、VLA、具身智能

### 3.1 赛题任务类型

| 任务类别 | 描述 | 示例 |
|----------|------|------|
| 双臂协作 | 多臂协同操作 | 双手端锅 |
| 长时序操作 | 复杂的长周期任务 | 整理桌面 |
| 高精度操作 | 精细抓取和放置 | 物流分拣 |
| 日常生活服务 | 常见场景操作 | 开门、清理 |

**具体任务**（部分）：物流分拣、倒工件、上货扶正、铲爆米花、开门、清理书桌、双手端锅

---

### 3.2 基线模型：ACoT-VLA

**ACoT-VLA**：Action Chain-of-Thought for Vision-Language-Action Models

> 论文：https://arxiv.org/abs/2601.11404
> 代码：https://github.com/AgibotTech/ACoT-VLA

#### 性能对比

| 方法 | 空间泛化 | 物体泛化 | 目标泛化 | 平均 |
|------|----------|----------|----------|------|
| π₀ | 79.6% | 21.1% | 85.2% | 94.1% |
| π₀.₅ | 70.3% | 41.7% | 92.4% | 96.9% |
| **ACoT-VLA** | **91.2%** | **62.5%** | **96.0%** | **98.5%** |

#### 模型架构

```
输入: "把红色积木放进盒子里"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    VLM 主干网络                          │
│              (视觉语言联合理解)                           │
└─────────────────────────────┬───────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────┐
│   EAR (显式推理器)   │               │   IAR (隐式推理器)   │
│ • 生成粗粒度轨迹     │               │ • 提取VLM内部表征   │
│ • 提供运动提示       │               │ • 跨注意力建模      │
└─────────┬───────────┘               └─────────┬───────────┘
          │                                   │
          └─────────────┬─────────────────────┘
                        ▼
              ┌─────────────────┐
              │  Action Chain   │
              │    of Thought   │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │    最终动作      │
              └─────────────────┘
```

---

### 3.3 测试流程（赛道一）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   准备环境   │────▶│  下载数据   │────▶│  运行基线   │────▶│  提交成绩   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

#### Step 1: 环境准备

```bash
# 克隆 Genie Sim
git clone https://github.com/AgibotTech/genie_sim.git
cd genie_sim

# 下载资产（ModelScope）
# https://modelscope.cn/datasets/agibot_world/GenieSimAssets
# 放入: genie_sim/source/geniesim/assets

# 构建 Docker 镜像
docker build -f ./scripts/dockerfile -t registry.agibot.com/genie-sim/open_source:latest .

# 启动容器
./scripts/start_gui.sh

# 进入容器
./scripts/into.sh

# 运行 demo 测试
omni_python source/geniesim/app/app.py --config ./source/geniesim/config/select_color.yml
```

#### Step 2: 下载数据集

```bash
# HuggingFace
git clone https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026

# ModelScope
git clone https://modelscope.cn/datasets/AgiBotWorld/AgiBotWorldChallenge-2026
```

#### Step 3: 运行基线

```bash
# 启动推理服务
cd openpi
uv run scripts/serve_policy.py --host='0.0.0.0' --port=8999 \
    policy:checkpoint \
    --policy.config=acot_icra_simulation_challenge_reasoning_to_action \
    --policy.dir ./checkpoints/select_color/29999

# 运行 ICRA 任务（另开终端）
./scripts/start_gui.sh  # 启动仿真容器
./scripts/into.sh
cd /geniesim/main

# 配置 VLM 评分（可选）
export BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export API_KEY=your_api_key
export VL_MODEL=qwen3-vl-plus

# 运行任务
./scripts/run_icra_tasks.sh

# 收集评分
python3 scripts/stat_average.py
```

#### Step 4: 提交成绩

```bash
# 构建 Docker 镜像
docker build -t your-registry.com/your-project:v1 .

# 推送
docker push your-registry.com/your-project:v1

# 在测试服务器提交
# https://agibot-world.com/challenge2026/reasoning2action
# 点击 "New Submission"
```

---

### 3.4 代码结构分析（赛道一）

```
ACoT-VLA/
├── src/openpi/
│   ├── training/           # 训练相关
│   │   ├── config.py      # 配置文件
│   │   └── trainer.py     # 训练器
│   ├── inference/         # 推理相关
│   │   ├── policy.py     # 策略模型
│   │   └── server.py     # 推理服务
│   └── models/           # 模型定义
│       ├── vlm.py        # VLM 主干
│       ├── ear.py        # EAR 推理器
│       └── iar.py        # IAR 推理器
├── scripts/
│   ├── train.sh          # 训练脚本
│   └── server.sh         # 服务脚本
└── configs/
    └── acot_icra_*.yaml   # ICRA 专用配置
```

#### 关键配置

```python
# src/openpi/training/config.py
config_name = "acot_icra_simulation_challenge_reasoning_to_action"

model:
  vlm_backbone: "Qwen/Qwen2-VL-7B"
  ear_hidden_dim: 256
  iar_cross_attention_layers: 4

training:
  batch_size: 16
  learning_rate: 1e-4
```

---

### 3.5 优化方法（赛道一）

| 优化方向 | 方法 | 效果 |
|----------|------|------|
| 数据增强 | 随机视角、光照、纹理 | 提升泛化 |
| 模型微调 | LoRA (rank=16) | 低成本高效 |
| Prompt 工程 | 优化指令模板 | 更准确理解 |
| 多模态融合 | RGB + 深度 | 更丰富信息 |

---

## 四、赛道二：World Model（世界模型赛道）

> **适合方向**：视频生成、扩散模型、具身世界模型

### 4.1 赛题任务类型

**核心任务**：基于机器人动作信号，生成机器人在真实场景中的交互视频。

```
输入: 机器人观测（图像序列）+ 动作信号
         │
         ▼
    编码当前状态
         │
         ▼
    扩散模型生成未来帧
         │
         ▼
    输出: 预测视频（10组场景）
```

**数据集规模**：
- 训练集：10 个任务，超 **30,000 条**真实轨迹
- 交互类型：抓取、放置、推、拉等

---

### 4.2 基线模型：EVAC

**EVAC**：EnerVerse with Action Condition

> 代码：https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline
> 论文：https://arxiv.org/abs/2505.09723

#### 基线性能（验证集）

| 指标 | 值 |
|------|-----|
| PSNR | 20.9841 |
| Scene Consistency | 0.9013 |
| nDTW | 0.9065 |

#### 模型架构

```
输入: 观测图像序列 + 动作信号
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                  CLIP 视觉编码                           │
│              (图像条件注入)                              │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 扩散 Transformer                        │
│              (时空一致性建模)                           │
└─────────────────────────────┬───────────────────────────┘
                              │
                              ▼
              ┌─────────────────────────┐
              │    生成未来视频帧        │
              │    (30,000+ 轨迹预训练)  │
              └─────────────────────────┘
```

---

### 4.3 测试流程（赛道二）

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   准备环境   │────▶│  下载数据   │────▶│  推理生成   │────▶│  提交成绩   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

#### Step 1: 环境准备

```bash
# 克隆基线代码
git clone https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline.git
cd AgiBotWorldChallengeICRA2026-WorldModelBaseline

# 创建环境
conda create -n enerverse python=3.10.4
conda activate enerverse

# 安装依赖
pip install -r requirements.txt

# 安装 pytorch3d（CUDA 12.1 版本）
pip install --no-index --no-cache-dir pytorch3d -f \
  https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu121_pyt240/download.html

# 更新子模块
git submodule update --remote
```

#### Step 2: 下载数据集

```bash
# 下载 World Model 数据集
# https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026/tree/main/WorldModel

# 下载测试集
wget https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026/blob/main/WorldModel/test.tar.gz

# 下载验证集（用于本地评测）
wget https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026/blob/main/WorldModel/val.tar.gz
```

#### Step 3: 推理生成

```bash
# 修改 scripts/infer.sh 中的路径

# 运行推理
bash scripts/infer.sh

# 输出目录: ACWM_dataset/
# ├── task_0/
# │   ├── episode_0/
# │   │   ├── 0/video/  # 预测1
# │   │   ├── 1/video/  # 预测2
# │   │   └── 2/video/  # 预测3
```

#### Step 4: 本地评测

```bash
# 克隆 EWMBench
git clone https://github.com/AgibotTech/EWMBench.git
cd EWMBench

# 准备数据目录
DIRPATH_TO_YOUR_DATASET/
 gt_dataset/
 ├── task_1/
 │   └── episode_1/video/...
 └── ...

# 修改 config.yaml
model_name: ACWM
data:
 gt_path: DIRPATH_TO_YOUR_DATASET/gt_dataset
 val_base: DIRPATH_SAVE_PREDICTION/ACWM_dataset

# 运行评测
bash processing.sh ./config.yaml
python evaluate.py --dimension 'semantics' 'trajectory_consistency' \
  'diversity' 'scene_consistency' 'psnr' 'ssim' --config ./config.yaml
```

#### Step 5: 提交成绩

```bash
# 访问 HuggingFace 评测服务器
# https://huggingface.co/spaces/agibot-world/ICRA26WM

# 按指引提交生成的视频
# 实时排行榜
```

---

### 4.4 代码结构分析（赛道二）

```
AgiBotWorldChallengeICRA2026-WorldModelBaseline/
├── configs/
│   └── agibotworld/
│       ├── train_config_challenge_wm.yaml    # 竞赛训练配置
│       └── train_configs.yaml                # 预训练配置
├── scripts/
│   ├── infer.sh                              # 推理脚本
│   ├── train.sh                              # 训练脚本
│   └── processing.sh                         # 预处理脚本
├── models/
│   └── evac/                                 # EVAC 模型
├── datasets/
│   └── reorganized_data/                     # 数据组织
└── checkpoints/
    └── *.pt                                  # 预训练权重
```

#### 关键配置

```yaml
# configs/agibotworld/train_config_challenge_wm.yaml

model:
  pretrained_checkpoint: /path/to/EVAC_checkpoint.pt
  
model.params.img_cond_stage_config.params.abspath: /path/to/CLIP_pytorch_model.bin

data.params.train.params.data_roots: /path/to/AgiBotWorld_dataset
```

---

### 4.5 优化方法（赛道二）

| 优化方向 | 方法 | 效果 |
|----------|------|------|
| 相机标定误差 | 校正方法 | 减少系统误差 |
| 视频质量 | 使用更强的视频生成模型 | 更高 PSNR |
| 动作信号注入 | 改进注入方式 | 更好轨迹一致性 |
| Preference Learning | 人类偏好对齐 | 更高质量生成 |

#### 进阶方向推荐

- **更高性能视频生成模型**：如 DynamiCrafter, LVDM
- **动作信号注入**：更巧妙的编码方式
- **世界模型研究**：GenieEnvisioner-Sim, Ctrl-World, DreamDojo

---

## 五、知识点对比与关联

### 5.1 两赛道知识点对比

| 知识点 | 赛道一（Reasoning to Action） | 赛道二（World Model） |
|--------|------------------------------|----------------------|
| **核心模型** | VLA（视觉-语言-动作） | 扩散 Transformer |
| **输入** | 图像 + 语言指令 | 图像序列 + 动作信号 |
| **输出** | 机器人动作 | 生成视频 |
| **评测** | 任务成功率 | PSNR/场景一致性/nDTW |
| **环境** | Genie Sim 3.0 | EWMBench |
| **提交格式** | Docker 镜像 | 视频文件 |

### 5.2 共同知识点

| 知识点 | 用途 | 对应课程 |
|--------|------|----------|
| Python 基础 | 写代码 | 04-4 Linux基础 |
| 深度学习 | 模型理解 | 10-14 深度学习 |
| Transformer | 模型架构 | 13-1 LLM基础 |
| 数据处理 | 数据集管理 | 06-1~06-4 传感器 |
| Linux/Docker | 环境部署 | 04-4, 07-2 |

### 5.3 理论到实践映射

```
赛道一（Reasoning to Action）
├── VLM 视觉语言模型    → 10-14, 10-20, 13-7
├── 动作链思考         → 14-3 DQN/PPO
├── 双臂协同控制       → 05-5, 05-7, 11-4
├── 仿真平台           → 07-2, 07-5
└── Sim2Real          → 15-1~15-5

赛道二（World Model）
├── 扩散模型          → 13-1 LLM基础（扩展）
├── 视频生成          → 10-19 SAM（扩展）
├── 具身世界模型      → 14-7 RL安全约束
├── CLIP 视觉编码     → 10-15~10-17 YOLO
└── 评测基准          → 18-1~18-5 benchmark
```

---

## 六、关键赛程

| 日期 | 事项 | 赛道 |
|------|------|------|
| **2月12日** | 比赛报名开启 | 两者 |
| **2月28日** | 服务器开启 | 两者 |
| **4月20日** | 比赛服务器关闭 | 两者 |
| **4月30日** | 线上赛段结果公布 | 两者 |
| **6月1日** | 线下真机决赛 | 仅赛道一 |

---

## 七、资源汇总

### 官方资源

| 资源 | 赛道 | 链接 |
|------|------|------|
| 竞赛主页 | 全部 | https://agibot-world.com/challenge2026 |
| Genie Sim 文档 | 赛道一 | https://agibot-world.com/sim-evaluation/docs/ |
| ACoT-VLA 代码 | 赛道一 | https://github.com/AgibotTech/ACoT-VLA |
| EVAC 基线代码 | 赛道二 | https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline |
| EWMBench | 赛道二 | https://github.com/AgibotTech/EWMBench |
| HuggingFace 评测 | 赛道二 | https://huggingface.co/spaces/agibot-world/ICRA26WM |
| 数据集 (HF) | 全部 | https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026 |

### 社区支持

| 平台 | 链接 |
|------|------|
| 飞书群 | https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=b03mea0a-1212-428a-8b78-f77cf6f591e3 |
| Discord | https://discord.gg/9UTYfReA |
| 邮箱 | agibot-world-challenge@agibot.com |

---

## 八、快速上手检查清单

### 赛道一（Reasoning to Action）

- [ ] 确认硬件配置（GPU ≥ RTX 4080）
- [ ] 安装 Docker 和 NVIDIA Isaac Sim
- [ ] 克隆 Genie Sim 代码仓库
- [ ] 运行 select_color demo 测试环境
- [ ] 克隆 ACoT-VLA 并理解架构
- [ ] 下载 Reasoning2Action 数据集
- [ ] 启动推理服务并运行评测
- [ ] 构建并提交 Docker 镜像

### 赛道二（World Model）

- [ ] 确认硬件配置（GPU ≥ RTX 4080）
- [ ] 创建 conda 环境并安装依赖
- [ ] 克隆 EVAC 基线代码仓库
- [ ] 下载 World Model 数据集
- [ ] 下载 EVAC 和 CLIP 预训练权重
- [ ] 运行推理生成视频
- [ ] 使用 EWMBench 本地评测
- [ ] 提交到 HuggingFace 评测服务器

---

## 九、如何选择赛道？

### 选赛道一，如果：

- 你有 ROS/机器人控制经验
- 你想直接控制物理机器人
- 你对 VLA（视觉-语言-动作）模型感兴趣
- 你想参加线下真机决赛

### 选赛道二，如果：

- 你有视频生成/扩散模型经验
- 你对具身世界模型感兴趣
- 你想研究 Sim2Real 的视频预测部分
- 你更擅长算法优化而非硬件控制

### 两个都参加：

- 两个赛道可以同时参加
- 使用同一数据集，不同任务目标
- 分别提交，分别计分

---

## 总结

本课程为你提供了：

1. ✅ **两大赛道清晰对比**：Reasoning to Action vs World Model
2. ✅ **各自的学习路径**：从 Python 到专业知识的分阶段指南
3. ✅ **完整的测试流程**：环境 → 数据 → 推理 → 提交
4. ✅ **代码结构分析**：ACoT-VLA / EVAC 详细解析
5. ✅ **理论关联**：每个模块对应课程章节
6. ✅ **优化方法**：两个赛道各自的优化方向
7. ✅ **赛道选择指南**：根据背景选择最适合的赛道

祝你参赛顺利！🚀