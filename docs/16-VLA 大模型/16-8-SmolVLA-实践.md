# 16-8 SmolVLA实践

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 16-8 |
| 课程名称 | SmolVLA实践 |
| 所属模块 | 16-VLA 大模型 |
| 难度等级 | ⭐⭐⭐ |
| 预计学时 | 3小时 |
| 前置知识 | VLA基础、Python基础、深度学习基础 |

---

## 目录

1. [为什么需要小模型](#1-为什么需要小模型)
2. [SmolVLA简介](#2-smolvla简介)
3. [SmolVLA架构解析](#3-smolvla架构解析)
4. [环境配置与安装](#4-环境配置与安装)
5. [模型推理实战](#5-模型推理实战)
6. [数据收集与微调](#6-数据收集与微调)
7. [部署到真实机器人](#7-部署到真实机器人)
8. [练习题](#8-练习题)
9. [参考答案](#9-参考答案)

---

## 1. 为什么需要小模型

### 1.1 大模型的烦恼

想象一下，你学会了一道复杂的川菜料理。比如**宫保鸡丁**。要做得和米其林厨师一样，你需要：
- 多年的厨艺训练
- 专业的厨房设备
- 大量的练习素材

现在的VLA模型就像是这样一个"米其林大厨"：
- **RT-2**：55亿参数，需要高端GPU集群训练
- **OpenVLA**：70亿参数，需要至少32GB显存运行
- **π0**：数十亿参数，训练成本高达数百万美元

这就像是：
```
普通研究者想学做菜 → 米其林厨师说："先买一个专业厨房再说！"
```

门槛太高了！

### 1.2 小模型的逆袭

但是！
- 普通人做家常菜也很好吃啊
- 不需要那么多调料，也能做出美味
- 家里的厨房足够了

**SmolVLA** 就是这样一个"家常菜大厨"：
- 只需要 **4.5亿参数**
- 一张消费级GPU就能训练
- 甚至CPU都能推理

> "我不是来替代大酒店的，我只是让每个人都能在家做顿饭"

---

## 2. SmolVLA简介

### 2.1 它是谁

**SmolVLA**（Small Vision-Language-Action）是由 Hugging Face LeRobot 团队开发的小型化VLA模型，发表于2025年6月。

| 特性 | 说明 |
|------|------|
| 参数总量 | **4.5亿** (450M) |
| 参数量级 | 约为RT-2的 **1/10** |
| 训练硬件 | **单张GPU** (如RTX 3090) |
| 推理硬件 | 消费级GPU或CPU |
| 训练数据 | 社区贡献的机器人数据 |
| 代码开源 | huggingface/lerobot |

### 2.2 性能对比

| 模型 | 参数 | 训练成本 | 推理显存 |  SimRG Cube |
|------|------|----------|---------|----------|-----------|
| RT-2 | 55B | $100万+ | 80GB+ | 85% |
| OpenVLA | 7B | $50万+ | 32GB+ | 72% |
| **SmolVLA** | **450M** | **< $1万** | **< 8GB** | **79%** |

**惊喜！** SmolVLA 在模拟器 Benchmark 上的表现接近RT-2，但参数少了100多倍！

### 2.3 核心设计理念

SmolVLA 的设计哲学是：**"够用就好"**

```
大模型：我要追求极致性能
SmolVLA：我要让每个人都能用
```

| 大模型思维 | SmolVLA思维 |
|-----------|-------------|
| 数据越多越好 | 社区数据也能用 |
| 算力越强越好 | 单卡也能训 |
| 参数越多越好 | 够用就行 |
| 追求SOTA | 追求可及性 |

---

## 3. SmolVLA架构解析

### 3.1 模型结构

SmolVLA 的架构可以理解为一个"三明治"：

```
┌─────────────────────────────────┐
│         视觉输入层               │  ← 相机图像
│   (EfficientViT视觉编码器)       │
├─────────────────────────────────┤
│         语言层                  │  ← "把杯子拿起"
│   (SmolLM语言模型)              │
├─────────────────────────────────┤
│         动作层                  ���  ← 输出动作
│   (动作预测头)                  │
└─────────────────────────────────┘
```

### 3.2 各模块详解

#### 视觉编码器：EfficientViT

不是用很大的ViT，而是用优化过的轻量级版本：
- 参数量：约100M
- 推理速度：比ViT-L快3倍

#### 语言模型：SmolLM

- 基于 SmolLM (1.7B) 
- 专门微调用于机器人指令理解
- 支持多语言指令

#### 动作预测：离散化动作空间

和RT-2 类似，SmolVLA 也使用离散化动作：

```python
# 动作离散化示例
action_bins = 256  # 动作空间离散为256个bin
action = discretize(real_action, action_bins)
```

每个动作分量分别预测：
- 机械臂末端位置 (x, y, z)
- 夹爪开合 (gripper)
- 基座移动 (base_x, base_y, base_theta)

### 3.3 异步推理（独门秘籍）

SmolVLA 的一个亮点是**异步推理栈**：

```
传统方式：                 SmolVLA方式：
────────────────────    ────────────────────
看画面 → 等动作           看画面 → 缓存结果
等动作 → 执行            缓存中 → 直接执行
执行   → 看画面         执行   → 同时准备下一帧
```

好处：
- 控制频率：可以达到 **30Hz**（传统只有3-5Hz）
- 延迟更稳定，不会手忙脚乱

---

## 4. 环境配置与安装

### 4.1 硬件要求

| 配置 | 最低 | 推荐 |
|------|------|------|
| GPU | GTX 3090 | RTX 4090 / A100 |
| 显存 | 8GB | 16GB |
| 内存 | 16GB | 32GB |
| 硬盘 | 50GB | 100GB SSD |

### 4.2 安装步骤

```bash
# 1. 创建 conda 环境
conda create -n smolvla python=3.10
conda activate smolvla

# 2. 安装PyTorch
pip install torch torchvision torchaudio

# 3. 安装 LeRobot
pip install lerobot

# 4. 或者从源码安装
git clone https://github.com/huggingface/lerobot
cd lerobot
pip install -e .
```

### 4.3 验证安装

```python
import lerobot
from lerobot.robots import RivalzRobot

# 检查版本
print(lerobot.__version__)  # 应该输出 0.2.0 或更高
```

---

## 5. 模型推理实战

### 5.1 快速推理示例

```python
import torch
from lerobot.scripts import inference

# 加载预训练模型
model = inference.load_model("smolvla/smolvla-450m")

# 准备输入
image = torch.randn(1, 3, 224, 224)  # 相机图像
instruction = "pick up the cup"       # 指令

# 推理
action = model.predict(image, instruction)

print(f"Predicted action: {action}")
# 输出类似：[0.12, -0.05, 0.30, 1.0, 0.0, 0.0]
#        [x,    y,    z,  gripper, base_x, base_y]
```

### 5.2 在模拟器中使用

以 **LeRobot** 模拟器为例：

```python
from lerobot.envs import SimEnv
from lerobot.agents import SmolVLAAgent

# 创建环境
env = SimEnv(task="reach", robot="kapa")

# 创建智能体
agent = SmolVLAAgent(model="smolvla/smolvla-450m")

# 运行 episodes
for episode in range(10):
    obs = env.reset()
    done = False
    
    while not done:
        # 获取动作
        action = agent.act(obs)
        
        # 执行
        obs, reward, done, info = env.step(action)
        
    print(f"Episode {episode} done, reward: {reward}")
```

### 5.3 CPU推理

如果只有CPU也可以运行（会慢一些）：

```python
model = inference.load_model(
    "smolvla/smolvla-450m",
    device="cpu"  # 用CPU
)

# CPU推理会慢一些，但可以用
action = model.predict(image, instruction)
print(f"推理耗时: {model.last_inference_time:.2f}s")
```

---

## 6. 数据收集与微调

### 6.1 数据格式

SmolVLA 使用 LeRobot 标准数据格式：

```python
from lerobot.common.datasets import RobotDataset

# 数据示例
episode = {
    "image": [H, W, 3],           # 相机图像
    "state": [state_dim],          # 机器人状态
    "action": [action_dim],        # 执行的动作
    "language_instruction": str,   # 语言指令
}

# 创建数据集
dataset = RobotDataset("my_robot_data/")
dataset.add_episode(episode)
dataset.save()
```

### 6.2 收集数据

使用 LeRobot 的 teleoperation 接口：

```bash
# 启动数据收集
python -m lerobot.scripts.teleop \
    --robot-type kapa \
    --camera-image wildcpu \
    --save-traj \
    --output-dir ./my_data
```

操作步骤：
1. 连接机器人
2. 用手柄控制机器人
3. 系统自动录制数据
4. 按 ESC 保存

### 6.3 微调模型

```bash
# 微调命令
python -m lerobot.scripts.train \
    --model-name smolvla \
    --pretrained-path smolvla/smolvla-450m \
    --dataset ./my_data \
    --epochs 50 \
    --batch-size 8 \
    --learning-rate 1e-4
```

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| batch-size | 批大小 | 8-16 |
| learning-rate | 学习率 | 1e-4 |
| epochs | 训练轮数 | 50-100 |
| gradient-accum | 梯度累积 | 4 |

### 6.4 检查点保存

```bash
# 训练会自动保存到 ./outputs/
ls -la outputs/
# smolvla_epoch_10.pt
# smolvla_epoch_20.pt
# ...
# smolvla_best.pt
```

---

## 7. 部署到真实机器人

### 7.1 支持的机器人

SmolVLA 支持多种机器人：

| 机器人 | 自由度 | 应用场景 |
|--------|--------|----------|
| Aloha | 14 | 精细操作 |
| UB | 6 | 桌面操作 |
| Kapa | 7 | 通用操作 |
| WidowX | 6 | 简单操作 |

### 7.2 部署代码

```python
from lerobot.robots import RivalzRobot
from lerobot.agents import SmolVLAAgent

# 连接机器人
robot = RivalzRobot(
    camera="usb_cam",
    kinematics="aloha"
)

# 加载微调后的模型
agent = SmolVLAAgent(
    model="./outputs/smolvla_best.pt",
    device="cuda"
)

# 主循环
while True:
    # 获取观察
    obs = robot.get_observation()
    
    # 推理动作
    action = agent.act(obs)
    
    # 执行
    robot.exec(action)
```

### 7.3 实时控制

```python
import time

# 目标控制频率：30Hz
dt = 1 / 30

while True:
    loop_start = time.time()
    
    # 推理 + 执行
    obs = robot.get_observation()
    action = agent.act(obs)
    robot.exec(action)
    
    # 等待
    elapsed = time.time() - loop_start
    if elapsed < dt:
        time.sleep(dt - elapsed)
```

---

## 8. 练习题

### 基础题

1. **参数对比**：计算SmolVLA的参数是RT-2的多少分之一？
2. **硬件选择**：如果你只有一张GTX 1060显卡，能否运行SmolVLA？需要什么条件？
3. **动作空间**：SmolVLA的输出动作包含哪些维度？

### 进阶题

4. **代码阅读**：阅读 `lerobot/lerobot/agent/smolvla.py` 中的 `act` 方法，解释其工作流程
5. **数据格式**：设计一个用于"收拾桌面"任务的数据集格式，说明需要记录哪些字段
6. **性能分析**：对比SmolVLA在GPU和CPU上的推理速度差异，分析瓶颈在哪里

### 实战题

7. **本地推理**：运行LeRobot提供的 `demo_inference.py`，验证模型能正常推理
8. **模拟器测试**：在LeRobot模拟器中运行SmolVLA，统计10个episode的平均成功率

---

## 9. 参考答案

### 基础题答案

1. **参数对比**
   - SmolVLA: 4.5亿参数
   - RT-2: 55亿参数
   - 比值: 4.5 / 55 ≈ **1/12**
   - 即约 **1/12** 或 **8.2%**

2. **硬件选择**
   - GTX 1060 (6GB显存) 可以运行，但建议：
     - 使用量化版本 (4-bit)
     - 或降低分辨率
     - 或仅用于推理，训练建议用更好显卡

3. **动作空间**
   - 末端位置 (x, y, z)：3维
   - 夹爪开合 (gripper)：1维
   - 基座移动 (base_x, base_y, base_theta)：3维
   - 共 **7维**

### 进阶题答案

4. **代码流程**
   ```python
   def act(self, observation):
       # 1. 视觉编码
       visual_features = self.vision_encoder(observation.image)
       
       # 2. 指令编码
       text_features = self.text_encoder(instruction)
       
       # 3. 融合
       fused = self.fuse(visual_features, text_features)
       
       # 4. 动作预测
       action = self.action_head(fused)
       
       # 5. 离散化
       action = self.discretize(action)
       
       return action
   ```

5. **数据格式**
   ```python
   episode = {
       "image": [H, W, 3],              # 第一人称图像
       "depth": [H, W],                # 深度图像（可选）
       "state": [joint_pos, gripper],    # 机器人状态
       "action": [dx, dy, dz, d_gripper, wait],  # 相对动作
       "language_instruction": "把红色积木放到蓝色盒子里",  # 指令
       "success": bool,                   # 是否成功
   }
   ```

6. **性能分析**
   - GPU推理：约 **50ms** (20fps)
   - CPU推理：约 **500ms** (2fps)
   - 瓶颈：视觉编码器（占80%时间）
   - 优化：可以用INT8量化或减小输入分辨率

### 实战题答案

7. **本地推理**
   ```bash
   # 运行demo
   cd lerobot
   python examples/demo_inference.py
   
   # 成功标志：输出类似
   # Action: [0.12, -0.05, 0.30, 1.0]
   ```

8. **模拟器测试**
   ```python
   from lerobot.envs import SimEnv
   from lerobot.agents import SmolVLAAgent
   
   env = SimEnv(task="reach", robot="kapa")
   agent = SmolVLAAgent("smolvla/smolvla-450m")
   
   success_count = 0
   for i in range(10):
       obs = env.reset()
       done = False
       while not done:
           action = agent.act(obs)
           obs, reward, done, _ = env.step(action)
       if reward > 0:
           success_count += 1
   
   print(f"成功率: {success_count}/10 = {success_count*10}%")
   # 典型结果：约70-80%
   ```

---

## 参考资源

- [SmolVLA 论文](https://arxiv.org/abs/2506.01844)
- [LeRobot GitHub](https://github.com/huggingface/lerobot)
- [SmolVLA HuggingFace](https://huggingface.co/blog/smolvla)
- [官方文档](https://docs.lerobot.io)

---

*更新于 2026-03-31*