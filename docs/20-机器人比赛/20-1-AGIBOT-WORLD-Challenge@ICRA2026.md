# 20-1 AGIBOT WORLD Challenge@ICRA2026

## 概述

AGIBOT WORLD Challenge@ICRA2026 是由智元机器人举办的具身智能国际竞赛，作为 ICRA 2026 官方赛事。本课程面向零基础小白，从知识点梳理到实战应用，帮助你快速入门并参与竞赛。

---

## 一、竞赛扫盲：5分钟了解这是什么比赛

### 1.1 比赛在做什么？

想象一下：你给机器人一段文字指令，比如"把桌子上的苹果放进篮子里"，机器人需要：
1. **看懂**你在说什么（理解）
2. **规划**该怎么做（推理）
3. **执行**具体的动作（操作）

这就是 **Reasoning to Action（推理-操作赛道）** 考察的核心能力。

### 1.2 为什么叫"Reasoning to Action"？

| 传统方式 | Reasoning to Action |
|----------|---------------------|
| 直接输出动作 | 先"思考"再行动 |
| 动作和推理分离 | 推理过程用动作描述 |
| 难以解释 | 可追溯、可解释 |

简单说：机器人不仅要会做，还要会"思考怎么做"。

---

## 二、知识点地图：从零到参赛

### 2.1 学习路径图

```
                    ┌─────────────────────────────────────┐
                    │       VLA (视觉-语言-动作模型)        │
                    │   Vision-Language-Action Model        │
                    └─────────────────┬─────────────────────┘
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
    • 目标检测                • Prompt设计              • 轨迹规划
```

### 2.2 必学知识点清单

#### 🔴 入门级（必须掌握）

| 知识点 | 用途 | 学习难度 |
|--------|------|----------|
| Python 基础 | 写代码、处理数据 | ⭐ |
| Linux 基础 | 跑代码、看日志 | ⭐ |
| ROS2 基础 | 机器人通信 | ⭐⭐ |
| 深度学习入门 | 理解模型原理 | ⭐⭐ |

#### 🟡 进阶级（理解原理）

| 知识点 | 用途 | 学习难度 |
|--------|------|----------|
| Transformer | 模型架构 | ⭐⭐⭐ |
| VLM (视觉语言模型) | 看图理解 | ⭐⭐⭐ |
| VLA (视觉语言动作) | 端到端控制 | ⭐⭐⭐ |
| 仿真平台 | 测试环境 | ⭐⭐⭐ |

#### 🟢 高级（优化提升）

| 知识点 | 用途 | 学习难度 |
|--------|------|----------|
| Action Chain-of-Thought | ACoT-VLA 核心 | ⭐⭐⭐⭐ |
| 模仿学习 | 训练策略 | ⭐⭐⭐⭐ |
| Sim2Real | 仿真到真实 | ⭐⭐⭐⭐ |

---

## 三、核心框架：ACoT-VLA 基线模型解析

### 3.1 ACoT-VLA 是什么？

**ACoT-VLA** 是本次竞赛的基线模型，全称 **Action Chain-of-Thought for Vision-Language-Action Models**。

> 论文：https://arxiv.org/abs/2601.11404
> 代码：https://github.com/AgibotTech/ACoT-VLA

### 3.2 为什么选它做基线？

| 对比 | π₀ | π₀.₅ | ACoT-VLA (我们) |
|------|-----|------|-----------------|
| 空间泛化 | 79.6% | 70.3% | **91.2%** |
| 物体泛化 | 21.1% | 41.7% | **62.5%** |
| 平均 | 67.4% | 75.7% | **84.1%** |

ACoT-VLA 在各类泛化测试中表现最优，特别适合竞赛。

### 3.3 模型架构拆解

```
输入: "把红色积木放进盒子里"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                    VLM 主干网络                          │
│              (视觉语言联合理解)                           │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐            │
│   │ 图像输入 │───▶│ 视觉编码 │    │ 语言指令 │───▶│ 语言编码 ││   └─────────┘    └─────────┘    └─────────┘    └─────────┘│
└─────────────────────────────┬───────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          ▼                                       ▼
┌─────────────────────┐               ┌─────────────────────┐
│   EAR (显式推理器)   │               │   IAR (隐式推理器)   │
│ Explicit Action     │               │ Implicit Action      │
│ Reasoner            │               │ Reasoner            │
│                     │               │                     │
│ • 生成粗粒度轨迹     │               │ • 提取VLM内部表征   │
│ • 提供运动提示       │               │ • 跨注意力建模      │
└─────────┬───────────┘               └─────────┬───────────┘
          │                                   │
          └─────────────┬─────────────────────┘
                        ▼
              ┌─────────────────┐
              │  Action Chain   │
              │    of Thought   │
              │   (动作链思考)   │
              └────────┬────────┘
                       ▼
              ┌─────────────────┐
              │    最终动作      │
              │   控制机器人     │
              └─────────────────┘
```

### 3.4 两个推理器详解

#### EAR（显式动作推理器）

**作用**：像人类"心里想"一样，生成粗粒度的动作计划

```python
# 伪代码示例
def EAR_forward(observation, instruction):
    # 输入: 相机看到的图像 + "把苹果放进篮子"
    # 输出: "先伸手 → 抓住苹果 → 移动到篮子上方 → 松开"
    
    trajectory = synthesize_motion_plan(observation, instruction)
    return trajectory  # 动作意图序列
```

#### IAR（隐式动作推理器）

**作用**：从 VLM 内部表征中"挖掘"动作知识

```python
# 伪代码示例
def IAR_forward(vlm_hidden_states):
    # 输入: VLM 各层的特征表示
    # 输出: 潜在动作先验
    
    action_prior = cross_attention_model(vlm_hidden_states)
    return action_prior  # 动作概率分布
```

### 3.5 Action Chain-of-Thought（动作链思考）

**核心思想**：推理过程本身就是动作意图的表达

```
传统推理: "我应该拿那个红色的东西" 
          → 没有具体动作信息

ACoT推理: "伸手 → 抓取 → 举起 → 移动 → 放下"
          → 直接可执行的动序列
```

---

## 四、测试流程：从小白到参赛

### 4.1 完整流程图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   准备环境   │────▶│  下载数据   │────▶│  运行基线   │────▶│  提交成绩   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  • Docker            • HuggingFace       • 推理服务           • 打包镜像
  • NVIDIA Isaac      • ModelScope        • 仿真评测           • 上传仓库
  • Genie Sim 3.0     • 数据格式转换       • 本地测试           • 服务器评测
```

### 4.2 环境准备（Step 1）

#### 硬件要求

| 配置 | 最低 | 推荐 |
|------|------|------|
| 系统 | Ubuntu 22.04 | Ubuntu 22.04 |
| GPU | RTX 4080 (32GB) | RTX 4090D (64GB) |
| 内存 | 32GB | 64GB |
| 存储 | 50GB SSD | 1TB NVMe SSD |

#### 软件安装

```bash
# 1. 克隆 Genie Sim
git clone https://github.com/AgibotTech/genie_sim.git
cd genie_sim

# 2. 下载资产（来自 ModelScope）
# 访问: https://modelscope.cn/datasets/agibot_world/GenieSimAssets
# 下载后放入: genie_sim/source/geniesim/assets

# 3. 构建 Docker 镜像（推荐方式）
cd genie_sim
docker build -f ./scripts/dockerfile -t registry.agibot.com/genie-sim/open_source:latest .

# 4. 启动容器
./scripts/start_gui.sh

# 5. 进入容器
./scripts/into.sh

# 6. 运行 demo 测试环境
omni_python source/geniesim/app/app.py --config ./source/geniesim/config/select_color.yml
```

### 4.3 数据下载（Step 2）

```bash
# Reasoning2Action 数据集
# HuggingFace
git clone https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026

# ModelScope
git clone https://modelscope.cn/datasets/AgiBotWorld/AgiBotWorldChallenge-2026

# 数据格式说明
# ├── observations/      # 图像观测
# ├── actions/           # 机器人动作
# ├── language/          # 语言指令
# └── metadata/          # 任务信息
```

### 4.4 运行基线（Step 3）

#### 启动推理服务

```bash
# 在容器中启动推理服务
cd openpi

# 计算归一化统计量
uv run scripts/compute_norm_stats.py --config-name=acot_icra_simulation_challenge_reasoning_to_action

# 启动训练（如需微调）
bash scripts/train.sh acot_icra_simulation_challenge_reasoning_to_action my_experiment

# 启动推理服务（默认端口 8999）
uv run scripts/serve_policy.py --host='0.0.0.0' --port=8999 \
    policy:checkpoint \
    --policy.config=acot_icra_simulation_challenge_reasoning_to_action \
    --policy.dir ./checkpoints/select_color/29999
```

#### 运行仿真评测

```bash
# 另开终端，启动仿真容器
./scripts/start_gui.sh

# 配置 VLM 评分（如需）
export BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export API_KEY=your_api_key
export VL_MODEL=qwen3-vl-plus

# 运行 ICRA 任务
./scripts/into.sh  # 进入仿真容器
cd /geniesim/main
./scripts/run_icra_tasks.sh

# 收集评分
python3 scripts/stat_average.py
```

### 4.5 提交成绩（Step 4）

```bash
# 1. 构建你的 Docker 镜像
docker build -t your-docker-registry.com/your-project:v1 .

# 2. 推送到公开仓库
docker push your-docker-registry.com/your-project:v1

# 3. 在测试服务器提交
# 访问: https://agibot-world.com/challenge2026/reasoning2action
# 点击 "New Submission"
# 填写镜像 URL

# 4. 查看结果
# 点击 "My Submissions" 查看评测结果
# 点击 "Leaderboard" 查看排名
```

---

## 五、基线代码分析

### 5.1 代码结构

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

### 5.2 关键配置文件

```python
# src/openpi/training/config.py

# 竞赛专用配置
config_name = "acot_icra_simulation_challenge_reasoning_to_action"

# 配置内容示例
model:
  vlm_backbone: "Qwen/Qwen2-VL-7B"  # VLM 主干
  ear_hidden_dim: 256                # EAR 隐层维度
  iar_cross_attention_layers: 4       # IAR 跨注意力层数

training:
  batch_size: 16
  learning_rate: 1e-4
  num_epochs: 100

data:
  dataset_path: "agibot_world/Reasoning2Action-Sim"
  image_resolution: [224, 224]
```

### 5.3 推理服务核心代码

```python
# openpi/src/openpi/inference/policy.py (简化伪代码)

class ACoTPolicy:
    def __init__(self, config):
        # 1. 加载 VLM 主干
        self.vlm = load_vlm(config.vlm_backbone)
        
        # 2. 初始化 EAR（显式推理器）
        self.ear = ExplicitActionReasoner(
            hidden_dim=config.ear_hidden_dim
        )
        
        # 3. 初始化 IAR（隐式推理器）
        self.iar = ImplicitActionReasoner(
            cross_attention_layers=config.iar_cross_attention_layers
        )
    
    def forward(self, observation, instruction):
        """
        输入: 图像观测 + 语言指令
        输出: 机器人动作
        """
        # Step 1: VLM 编码
        vlm_features = self.vlm.encode(observation, instruction)
        
        # Step 2: EAR 生成动作意图
        explicit_plan = self.ear(vlm_features)
        
        # Step 3: IAR 提取隐式先验
        implicit_prior = self.iar(vlm_features)
        
        # Step 4: 融合 + 解码动作
        action = self.decode(explicit_plan, implicit_prior)
        
        return action
```

---

## 六、理论知识关联

### 6.1 知识点 → 对应理论

| 功能模块 | 涉及理论 | 参考课程 |
|----------|----------|----------|
| VLM 主干 | Transformer, Attention | 10-14 深度学习, 10-20 VLM |
| 动作预测 | 强化学习, 策略网络 | 14-1~14-3 强化学习 |
| 仿真环境 | Isaac Sim, ROS2 | 07-2~07-4 仿真技术 |
| 双臂控制 | 运动学, 协调控制 | 05-1~05-8 运动控制 |
| 数据集 | 模仿学习, 示教学习 | 15-1~15-5 模仿学习 |

### 6.2 理论到实践的映射

```
深度学习基础 ──────────────────────────────────▶ 模型训练
    │                                              │
    ▼                                              ▼
CNN/ViT ──────────────────────────────────────▶ 视觉编码
    │                                              │
    ▼                                              ▼
Transformer ──────────────────────────────────▶ VLM 主干
    │                                              │
    ▼                                              ▼
Action Chain-of-Thought ───────────────────────▶ ACoT-VLA
    │                                              │
    ▼                                              ▼
模仿学习 ──────────────────────────────────────▶ 数据集训练
    │                                              │
    ▼                                              ▼
Sim2Real ──────────────────────────────────────▶ 仿真到真实
```

---

## 七、优化方法

### 7.1 可以优化的地方

#### 🔧 优化方向 1: 数据增强

```python
# 在训练配置中添加数据增强
data_augmentation:
  random_camera_view: true        # 随机相机视角
  random_light: true               # 随机光照
  random_texture: true             # 随机纹理
  noise_injection: true            # 噪声注入
```

#### 🔧 优化方向 2: 模型微调

```python
# 使用 LoRA 进行高效微调
fine_tuning:
  method: "lora"
  lora_rank: 16
  lora_alpha: 32
  target_modules: ["q_proj", "v_proj"]
```

#### 🔧 优化方向 3: Prompt 工程

```python
# 优化语言指令模板
prompt_template = """
你是一个机器人控制专家。
任务: {instruction}
当前观察: 请描述你看到了什么
可用物品: 请列出场景中的物品
下一步行动: 基于以上信息，输出你的动作计划
"""
```

#### 🔧 优化方向 4: 多模态融合

```python
# 融合深度信息
multimodal_fusion:
  rgb_encoder: true
  depth_encoder: true
  fusion_method: "cross_attention"  # 或 "concat"
```

### 7.2 竞赛特定技巧

| 任务类型 | 技巧 | 说明 |
|----------|------|------|
| 物流分拣 | 目标检测优化 | 分离密集物体 |
| 开门 | 探索策略 | 找到把手位置 |
| 双手端锅 | 双臂协同 | 同步控制 |
| 清理桌面 | 任务分解 | 先整理后清理 |

---

## 八、关键赛程

| 日期 | 事项 | 状态 |
|------|------|------|
| **2月12日** | 比赛报名开启 | ✅ |
| **2月28日** | 服务器开启 | ✅ 已开启 |
| **4月20日** | 提交截止 | ⏳ 倒计时 |
| **4月30日** | 结果公布 | ⏳ |
| **6月1日** | 线下决赛 | ⏳ |

---

## 九、资源汇总

### 官方资源

| 资源 | 链接 |
|------|------|
| 竞赛主页 | https://agibot-world.com/challenge2026 |
| Genie Sim 文档 | https://agibot-world.com/sim-evaluation/docs/ |
| ACoT-VLA 代码 | https://github.com/AgibotTech/ACoT-VLA |
| 数据集 (HF) | https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026 |
| 数据集 (MS) | https://modelscope.cn/datasets/AgiBotWorld/AgiBotWorldChallenge-2026 |

### 课程关联

| 竞赛涉及内容 | 对应课程章节 |
|--------------|--------------|
| VLM 视觉语言模型 | 10-14, 10-20, 13-7 |
| 强化学习 | 14-1, 14-2, 14-3 |
| 仿真平台 | 07-2, 07-5 |
| 双臂控制 | 05-5, 05-7, 11-4 |
| 模仿学习 | 15-1, 15-2, 15-3 |

### 社区支持

| 平台 | 链接 |
|------|------|
| 飞书群 | https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=b03mea0a-1212-428a-8b78-f77cf6f591e3 |
| Discord | https://discord.gg/9UTYfReA |
| 邮箱 | agibot-world-challenge@agibot.com |

---

## 十、快速上手检查清单

- [ ] 确认硬件配置（GPU ≥ RTX 4080）
- [ ] 安装 Docker 和 NVIDIA Isaac Sim
- [ ] 克隆 Genie Sim 代码仓库
- [ ] 下载并配置数据集
- [ ] 运行 select_color demo 测试环境
- [ ] 克隆 ACoT-VLA 并理解架构
- [ ] 启动推理服务
- [ ] 运行完整 ICRA 任务评测
- [ ] 构建自己的 Docker 镜像
- [ ] 提交到测试服务器

---

## 总结

本课程为你提供了：

1. ✅ **知识点地图**：从 Python 到 VLA 的完整学习路径
2. ✅ **ACoT-VLA 解析**：显式/隐式推理器 + 动作链思考
3. ✅ **完整测试流程**：环境准备 → 数据下载 → 运行基线 → 提交
4. ✅ **代码结构分析**：配置、训练、推理服务详解
5. ✅ **理论知识关联**：每个模块对应的学习理论
6. ✅ **优化方法**：数据增强、模型微调、Prompt 工程

祝你参赛顺利！🚀