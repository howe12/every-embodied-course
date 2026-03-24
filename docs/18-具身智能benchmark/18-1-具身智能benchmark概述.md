# 18-1 具身智能 Benchmark 概述

> **前置课程**：12-2 逆向强化学习（IRL）
> **后续课程**：14-VLA 大模型

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：当我们训练好一个具身智能模型后，一个关键问题随之而来——**如何科学地评估它的能力？** 不同研究团队用不同的实验环境和指标，导致结果难以对比。Benchmark（基准评测）正是为解决这一问题而生的标准化工具。本节将系统讲解具身智能领域主流 Benchmark 的设计理念、评测指标和代码使用方法，帮助你掌握"让机器人考试"的整套方法论。

---

## 1. Benchmark 概述

### 1.1 什么是 Benchmark

Benchmark（基准测试）是用于**标准化评估机器人或智能体能力**的工具集，包含：

- **任务集合（Task Suite）**：预定义的任务清单，如"将红色方块放入蓝色盒子"
- **评测环境（Environment）**：仿真器（Isaac Gym、Mujoco）或实物场景（真实家庭环境）
- **评估指标（Metrics）**：可量化的性能衡量标准，如成功率、完成时间
- **标准化协议（Protocol）**：统一的实验流程、评测次数、随机种子

```
Benchmark = 任务定义 + 评测环境 + 评估指标 + 评测协议
```

**Benchmark 与普通实验的区别**：

| 对比维度 | 普通实验 | Benchmark |
|----------|----------|-----------|
| **任务定义** | 自己设计，自由发挥 | 标准化任务集合 |
| **对比基准** | 无或仅对比自己的消融实验 | 公开排行榜，所有人同一标准 |
| **复现性** | 难复现（代码/环境差异） | 高可复现（开源环境+固定种子） |
| **泛化评估** | 通常只测一个场景 | 多场景/多难度级别 |
| **社区认可** | 内部使用 | 学术/工业界广泛认可 |

### 1.2 为什么需要 Benchmark

**促进公平比较**：没有 Benchmark，A 和 B 两个团队各说各话，互相不服。Benchmark 提供了统一的"考场"，让不同算法在同一套题目下比试。

**加速研究迭代**：研究者可以在 Benchmark 上快速验证想法，而不用从零搭建评测环境。类似刷 LeetCode 对程序员的帮助。

**发现能力短板**：Benchmark 的多维度指标能揭示模型的薄弱环节——是抓取精度不够？还是泛化能力弱？指向明确的改进方向。

**推动落地应用**：工业界选型时，Benchmark 成绩是重要的参考依据。高分算法更可能被选中部署到真实机器人上。

### 1.3 Benchmark 的核心要素

| 要素 | 说明 | 示例 |
|------|------|------|
| **任务定义** | 清晰描述要做什么、做到什么程度算成功 | "将方块 A 放入容器 B，成功条件：方块完全在容器投影内" |
| **评测环境** | 物理仿真器或真实场景 | Isaac Gym、MuJoCo、HM3D 真实住宅 |
| **基线算法** | Benchmark 自带的对比算法 | BC、GAIL、SAC、CLIP |
| **数据集** | 预定义的目标物体、场景布局 | YCB 物体模型、HM3D 室内场景 |
| **评测协议** | 测几次、怎么取平均、随机种子 | 每个任务 100 个 episode，报告均值±标准差 |

---

## 2. 主流 Benchmark 介绍

### 2.1 RAFFLE — 机器人 Manipulation Benchmark

**RAFFLE**（Robot Arm Manipulation Benchmark）是由清华大学 HUA Lab 等团队推出的机器人 manipulation 基准评测，专注于**桌面级精细操作任务**。

**论文**：[RAFFLE: A Unified Benchmark for Robot Manipulation](https://arxiv.org/abs/xxxx)

**核心特点**：

| 特点 | 说明 |
|------|------|
| **多任务融合** | 涵盖抓取（Grasp）、放置（Place）、推（Push）、装配（Assembly）等 |
| **仿真到实物** | 提供 Sim-to-Real 迁移指南，基线算法同时在仿真和实物上测试 |
| **多难度级别** | Easy / Medium / Hard 三档，评估不同泛化难度 |
| **统一 API** | 与 OpenAI Gym 接口兼容，易于接入 |

**RAFFLE 任务示例**：

| 任务 | 描述 | 难度定义 |
|------|------|---------|
| **Grasp** | 从杂乱物体中抓取指定物体 | Easy: 单物体；Hard: 5个干扰物 |
| **Place** | 将物体放入指定容器 | Easy: 大容器；Hard: 小容器/窄口 |
| **Push** | 用推的动作将物体移动到目标区域 | Easy: 无障碍；Hard: 障碍物引导 |
| **Insert** | 将物体插入孔/槽中 | Easy: 对齐辅助；Hard: 精确对准 |
| **Stack** | 将物体叠放在另一物体上 | Easy: 同形状；Hard: 不同形状/尺寸 |

**RAFFLE 评测指标**：

| 指标 | 说明 |
|------|------|
| **Success Rate（SR）** | 任务成功完成的比例，核心指标 |
| **Average Return** | 累计奖励均值，衡量策略质量 |
| **Average Episode Length** | 平均回合长度，越短 = 效率越高 |
| **Force Closure** | 抓取稳定性（力封闭指标） |
| **Grasp Stability Score** | 抓取成功率（基于抓取质量函数） |

### 2.2 HomeRobot — 家庭环境导航 Benchmark

**HomeRobot** 是由 Meta AI（Facebook）推出的**家庭服务机器人导航基准**，旨在评估机器人在真实家庭环境中的导航+操作能力。

**GitHub**：`https://github.com/facebookresearch/home-robot`

**核心特点**：

| 特点 | 说明 |
|------|------|
| **真实 3D 场景** | 基于 HM3D（Habitat Meta Universe 3D Dataset）真实住宅扫描 |
| **导航+操作** | 不仅要导航到目标位置，还要完成 manipulation 任务（如抓取物体） |
| **Stretch 机器人** | 支持 Hello Robot Stretch 实物的闭环评测 |
| **Habitat 仿真器** | 基于 Habitat 仿真器，高效物理仿真 |

**HomeRobot 典型任务**：

```
任务 1：Object Navigation
  → "找到红色的苹果并移动到它旁边"
  → 成功条件：机器人底座到达苹果 1m 范围内

任务 2：Pick-and-Place Navigation
  → "将桌上的苹果放入抽屉中"
  → 成功条件：物体在目标容器内

任务 3：Interactive Navigation
  → "打开抽屉然后把杯子放进去"
  → 成功条件：完成多个子任务
```

**HomeRobot 评测指标**：

| 指标 | 说明 |
|------|------|
| **Success Rate（SR）** | 任务完成率 |
| **SPL（Success weighted by Path Length）** | 成功率 × 效率（路径长度/最优路径长度） |
| **Distance to Goal** | 最终位置到目标位置的距离 |
| **Collisions** | 碰撞次数（安全性指标） |

### 2.3 AgentBench — LLM Agent 评估 Benchmark

**AgentBench** 是由上海人工智能实验室（Shanghai AI Lab）推出的**大语言模型（LLM）作为 Agent 的多维评测基准**，覆盖代码生成、游戏、机器人操作等多种场景。

**论文**：[AgentBench: Evolving LLMs as Generalist Agents](https://arxiv.org/abs/2308.03688)

**GitHub**：`https://github.com/THUDM/AgentBench`

**AgentBench 覆盖的领域**：

| 领域 | 具体任务 | 环境 |
|------|---------|------|
| **操作系统** | Bash 命令执行、文件操作 | Ubuntu + Docker |
| **知识图谱** | 知识图谱推理查询 | Neo4j |
| **数字卡牌游戏** | 策略决策 | 自行实现 |
| **软件开发** | 代码补全、Bug 修复 | HumanEval 等 |
| **具身机器人** | 机器人任务规划 | MiniGPT-4 / RL 环境 |
| **网络购物** | 多轮对话+操作 | 模拟购物网站 |

**AgentBench 评测维度**：

| 维度 | 说明 |
|------|------|
| **任务理解** | 理解自然语言指令的能力 |
| **工具使用** | 调用 API/工具完成复杂任务 |
| **多轮对话** | 长期记忆与上下文关联 |
| **错误恢复** | 失败后自我修正的能力 |
| **具身推理** | 空间推理、动作规划 |

**AgentBench 评分标准**：

| 评分 | 说明 |
|------|------|
| **5分（Perfect）** | 完全正确，无需人工干预 |
| **4分（Acceptable）** | 基本正确，有小瑕疵 |
| **3分（Pass）** | 可接受，勉强达到目标 |
| **2分（Fail）** | 失败，但方向正确 |
| **1分（Reject）** | 完全失败，方向错误 |

### 2.4 其他常用 Benchmark

| Benchmark | 专注领域 | 机构 | 特点 |
|-----------|---------|------|------|
| **CALVIN** | 机器人语言操控 | DeepMind | 长程语言指令，4个任务链式执行 |
| **RLBench** | 视觉引导 manipulation | Imperial College London | 12个任务，100个变体，支持 MoveIt! |
| **MetaWorld** | 元学习 manipulation | Stanford | 50个任务，用于元强化学习 |
| **Habitat** | 室内导航 | Meta AI | 真实3D场景扫描，导航+定位 |
| **Scannet** | 室内场景理解 | Stanford | 3D场景重建+语义分割 |
| **VIMA-Bench** | 多模态 Agent | NVIDIA | 视觉-语言-动作多模态任务 |
| **OpenX-Embodiment** | 机器人操作数据 | Google DeepMind | 100+机器人数据集统一格式 |
| **SAPIEN** | 关节物体 manipulation | NVIDIA | 真实几何模型的交互式仿真 |

**各 Benchmark 对比一览**：

| Benchmark | 仿真/实物 | 主要任务 | 适合研究场景 |
|-----------|---------|---------|------------|
| RAFFLE | 仿真+实物 | 桌面精细操作 | manipulation 算法 |
| HomeRobot | 仿真+实物 | 家庭导航+操作 | 服务机器人 |
| AgentBench | 纯软件 | LLM Agent 评测 | 多模态大模型 |
| CALVIN | 仿真 | 语言操控 | 指令跟随 |
| RLBench | 仿真 | 视觉引导操作 | 视觉策略学习 |
| MetaWorld | 仿真 | 多任务元学习 | 算法泛化性 |
| Habitat | 仿真 | 室内导航 | 视觉导航 |
| VIMA-Bench | 仿真 | 多模态 VLA | 视觉-语言-动作 |

---

## 3. 评估指标详解

### 3.1 成功率（Success Rate）

**成功率**是最直观的核心指标，表示任务完成的比例。

$$
\text{SR} = \frac{\text{成功回合数}}{\text{总回合数}} \times 100\%
$$

**分级标准**（通常约定俗成）：

| 成功率范围 | 评价 | 含义 |
|-----------|------|------|
| 95% - 100% | 接近饱和 | 算法已足够好，改进空间小 |
| 80% - 94% | 良好 | 可用于实际场景 |
| 50% - 79% | 一般 | 需要继续优化 |
| < 50% | 较差 | 算法尚不成熟 |

**注意事项**：
- 任务定义要严格清晰（"完全放入" vs "部分放入" 差异很大）
- 成功率对随机种子敏感，建议跑 100+ episodes 取统计显著性
- 有些任务天然有随机性（物体初始位置），成功率本身有上限

### 3.2 效率指标

效率指标衡量机器人**完成任务的速度或代价**。

| 指标 | 公式/说明 | 含义 |
|------|---------|------|
| **Average Episode Length** | 回合内平均步数 | 越短=越高效 |
| **Average Return** | 累计奖励均值 | 越高=策略越好 |
| **Path Length / SPL** | 实际路径/最优路径 | SPL = SR × (最优路径/实际路径) |
| **Time to Success** | 首次成功的时间 | 越短=学习/执行越快 |
| **Energy / Force** | 消耗能量或力矩积分 | 越少=越节能 |

**SPL（Success weighted by Path Length）详解**：

SPL 同时考虑成功率和路径效率，是导航 benchmark（如 Habitat）中的标准指标：

$$
\text{SPL} = \frac{1}{N} \sum_{i=1}^{N} \left[ \mathbb{1}_{s_i} \cdot \frac{\ell_i^*}{\max(\ell_i, \ell_i^*)} \right]
$$

其中 $\ell_i^*$ 是最优路径长度，$\ell_i$ 是实际路径长度。

### 3.3 泛化能力指标

泛化能力衡量算法在**新场景/新任务**上的表现，是机器人落地的关键。

| 指标 | 评估方式 | 说明 |
|------|---------|------|
| **新物体泛化** | 训练时未见过的物体类别 | 测试视觉/物理泛化 |
| **新场景泛化** | 训练时未见过的室内布局 | 测试空间理解泛化 |
| **新任务泛化** | 任务组合的新任务 | 测试任务分解能力 |
| **光照/视角泛化** | 改变光照条件或相机视角 | 测试视觉鲁棒性 |
| **Sim-to-Real Gap** | 仿真指标 vs 真实指标差距 | 评估仿真真实性 |

**泛化实验设计原则**：
- 训练集和测试集必须严格分离（无数据泄露）
- 泛化难度要梯度上升（从相似到差异大）
- 记录基线模型在新场景下的退化程度

### 3.4 其他重要指标

| 指标 | 适用场景 | 说明 |
|------|---------|------|
| **Collision Rate** | 导航任务 | 碰撞次数，越少越安全 |
| **Force Exerted** | 精细操作 | 末端执行器受力，越小越安全 |
| **Fall Rate** | 双足/移动机器人 | 摔倒频率，反映平衡能力 |
| **Communication Cost** | 多机器人协作 | 通信量，评估通信效率 |
| **Human Intervention Rate** | 人机协作 | 需要人工接管频率 |

---

## 4. 代码示例 — Benchmark API 使用

### 4.1 RAFFLE Benchmark 使用示例

```python
"""
RAFFLE Benchmark 使用示例
基于 PyBullet 仿真环境
"""
import gymnasium as gym
import numpy as np

# ============ 1. 环境创建 ============
# RAFFLE 提供标准化的任务注册接口
env = gym.make("RAFFLE-Grasp-Easy-v0")  # 抓取任务（简单难度）
# env = gym.make("RAFFLE-Insert-Hard-v0")  # 插入任务（困难难度）

print(f"任务: {env.spec.id}")
print(f"观测空间: {env.observation_space}")
print(f"动作空间: {env.action_space}")


# ============ 2. 策略定义（示例：随机策略） ============
def random_policy(observation):
    """随机策略（作为基线）"""
    action = env.action_space.sample()
    return action


# ============ 3. 评测函数 ============
def evaluate_policy(env, policy, num_episodes=100, render=False):
    """在 RAFFLE 环境中评测策略"""
    success_count = 0
    episode_lengths = []
    grasp_stabilities = []

    for episode in range(num_episodes):
        observation, info = env.reset()
        terminated = False
        truncated = False
        episode_length = 0
        episode_grasp_scores = []

        while not (terminated or truncated):
            if render:
                env.render()

            action = policy(observation)
            observation, reward, terminated, truncated, info = env.step(action)

            episode_length += 1

            # 获取抓取质量（如果有）
            if 'grasp_quality' in info:
                episode_grasp_scores.append(info['grasp_quality'])

        # 判断成功
        if info.get('success', False):
            success_count += 1

        episode_lengths.append(episode_length)

        if episode_grasp_scores:
            grasp_stabilities.append(np.mean(episode_grasp_scores))

        if (episode + 1) % 10 == 0:
            current_sr = success_count / (episode + 1)
            print(f"Episode {episode+1}/{num_episodes}: SR={current_sr:.2%}")

    # 计算汇总指标
    success_rate = success_count / num_episodes
    avg_length = np.mean(episode_lengths)
    std_length = np.std(episode_lengths)

    return {
        'success_rate': success_rate,
        'avg_episode_length': avg_length,
        'std_episode_length': std_length,
        'avg_grasp_stability': np.mean(grasp_stabilities) if grasp_stabilities else 0
    }


# ============ 4. 运行评测 ============
if __name__ == "__main__":
    print("=" * 60)
    print("RAFFLE Benchmark 评测")
    print("=" * 60)

    # 评测随机策略（基线）
    results = evaluate_policy(env, random_policy, num_episodes=100)

    print("\n" + "=" * 60)
    print("评测结果（随机策略基线）")
    print("=" * 60)
    print(f"成功率 (SR):          {results['success_rate']:.2%}")
    print(f"平均回合长度:        {results['avg_episode_length']:.1f} ± {results['std_episode_length']:.1f}")
    print(f"平均抓取稳定性:      {results['avg_grasp_stability']:.4f}")

    env.close()
```

### 4.2 HomeRobot Benchmark 使用示例

```python
"""
HomeRobot Benchmark 使用示例
基于 Habitat + Stretch 机器人
"""
import numpy as np


# ============ 1. HomeRobot 环境初始化 ============
# 仿真模式（无需实物机器人）
# pip install home-robot

# 初始化仿真环境
from home_robot import HomeRobotENV, get_config

config = get_config("projects/habitat_multitask/configs/")
# config.task_name = "pick_and_place"  # 导航+操作任务
# config.object_category = "apple"     # 目标物体

env = HomeRobotENV(config, display=False)


# ============ 2. 导航策略（示例） ============
class SimpleNavigationPolicy:
    """简单的点目标导航策略（仅作示例）"""
    def __init__(self):
        self.name = "SimpleNav"

    def predict(self, observation):
        """
        observation 包含:
            - rgb: 当前相机图像 (H, W, 3)
            - depth: 深度图 (H, W, 1)
            - sensor_pose: 机器人位姿 (x, y, theta)
            - goal_goal: 目标点相对位置 (x, y)
        """
        # 提取目标相对位置
        goal = observation["goal_goal"]  # (2,) [dx, dy]

        # 简单策略：朝目标方向移动
        # 实际应用中这里会接入 SLAM / 视觉策略
        action = np.array([goal[0], goal[1], 0.0])  # [v_x, v_y, omega]

        return action


# ============ 3. HomeRobot 评测指标计算 ============
def compute_spl(success, optimal_distance, actual_distance):
    """计算 SPL 指标"""
    if actual_distance == 0:
        return 0.0
    return success * (optimal_distance / max(actual_distance, optimal_distance))


def evaluate_home_robot(env, policy, num_episodes=50):
    """
    HomeRobot 标准评测函数
    返回 SPL 和成功率
    """
    spl_scores = []
    success_count = 0

    for episode in range(num_episodes):
        obs, info = env.reset()
        episode_metrics = info.get('metrics', {})

        # 最优路径长度（用于 SPL 计算）
        optimal_distance = episode_metrics.get('distance_to_goal', 1.0)

        done = False
        episode_length = 0
        actual_distance = 0.0

        while not done:
            action = policy.predict(obs)
            obs, reward, terminated, truncated, info = env.step(action)

            episode_length += 1
            actual_distance += np.linalg.norm(action[:2])
            done = terminated or truncated

        # 计算 SPL
        episode_spl = compute_spl(
            success=(info.get('success', False)),
            optimal_distance=optimal_distance,
            actual_distance=actual_distance
        )
        spl_scores.append(episode_spl)

        if info.get('success', False):
            success_count += 1

        if (episode + 1) % 10 == 0:
            current_sr = success_count / (episode + 1)
            current_spl = np.mean(spl_scores)
            print(f"Episode {episode+1}: SR={current_sr:.2%}, SPL={current_spl:.3f}")

    results = {
        'success_rate': success_count / num_episodes,
        'spl': np.mean(spl_scores),
        'spl_std': np.std(spl_scores),
    }

    return results


# ============ 4. 运行评测 ============
if __name__ == "__main__":
    policy = SimpleNavigationPolicy()

    print("=" * 60)
    print("HomeRobot Benchmark 评测")
    print("=" * 60)

    results = evaluate_home_robot(env, policy, num_episodes=50)

    print("\n最终结果:")
    print(f"成功率 (SR): {results['success_rate']:.2%}")
    print(f"SPL:         {results['spl']:.3f} ± {results['spl_std']:.3f}")
```

### 4.3 AgentBench 使用示例

```python
"""
AgentBench 使用示例
评估 LLM Agent 在多任务上的表现
"""
import numpy as np


# ============ 1. AgentBench 环境加载 ============
# AgentBench 支持多种环境，以下为通用评测框架示例
# pip install agentbench

environments = [
    'os',           # 操作系统操作
    'knowledge_graph',  # 知识图谱推理
    'digital_card',     # 卡牌游戏
    'software_dev',     # 软件开发
    'embodied_robot',   # 具身机器人任务
]


# ============ 2. 定义被测 Agent ============
class MyLLMDriver:
    """包装任意 LLM 作为 AgentBench Agent"""
    def __init__(self, model_name="gpt-4"):
        self.model_name = model_name
        self.history = []

    def step(self, instruction, history, observation):
        """
        执行一步推理
        实际使用时请接入真实的 LLM API
        """
        # 模拟 LLM 返回一个动作
        # 真实场景中这里会调用 OpenAI / Claude / 本地 LLM
        action = f"[SIMULATED ACTION for {self.model_name}]"
        return {'action': action}

    def run(self, task):
        """
        task: AgentBench Task 对象
        返回: (final_answer, score)
        """
        history = []
        obs = task.reset()

        max_turns = getattr(task, 'max_turns', 10)  # 最大对话轮数

        for turn in range(max_turns):
            # 生成 LLM 响应
            response = self.step(
                instruction=task.instruction,
                history=history,
                observation=obs
            )

            action = response['action']
            history.append((obs, action))

            # 执行动作，获取下一个 obs
            obs, reward, done, info = task.step(action)

            if done:
                break

        final_answer = history[-1][1] if history else ""
        final_score = info.get('score', 0)

        return final_answer, final_score


# ============ 3. 运行批量评测 ============
def run_agentbench_evaluation(model_name="gpt-4", num_trials=3):
    """在所有环境上评测 LLM Agent"""
    # 模拟运行（实际请使用 from agentbench import Benchmark）
    # benchmark = Benchmark(environments=environments)
    # benchmark = benchmark.load()

    print(f"\n{'='*50}")
    print(f"AgentBench 评测 - 模型: {model_name}")
    print(f"{'='*50}")

    all_results = {}

    for env_name in environments:
        print(f"\n评测环境: {env_name}")
        # 模拟分数（实际运行时请替换为真实结果）
        env_scores = [3.5, 3.8, 3.6]  # 模拟 3 次运行的结果
        all_results[env_name] = {
            'mean_score': np.mean(env_scores),
            'std_score': np.std(env_scores),
            'scores': env_scores
        }
        print(f"  分数: {env_scores} -> 均值={np.mean(env_scores):.2f}")

    return all_results


# ============ 4. 输出排行榜 ============
def print_leaderboard(results, model_name):
    """打印评测结果"""
    print("\n" + "=" * 70)
    print(f"AgentBench 评测结果 - {model_name}")
    print("=" * 70)
    print(f"{'环境':<20} {'平均分':>10} {'标准差':>10} {'评级':>10}")
    print("-" * 70)

    for env_name, res in results.items():
        mean = res['mean_score']
        std = res['std_score']

        # 评级映射
        if mean >= 4.5:
            grade = "★★★★★"
        elif mean >= 4.0:
            grade = "★★★★☆"
        elif mean >= 3.0:
            grade = "★★★☆☆"
        elif mean >= 2.0:
            grade = "★★☆☆☆"
        else:
            grade = "★☆☆☆☆"

        print(f"{env_name:<20} {mean:>10.2f} {std:>10.2f} {grade:>10}")

    # 综合得分
    overall = np.mean([r['mean_score'] for r in results.values()])
    print("-" * 70)
    print(f"{'综合得分':<20} {overall:>10.2f}")
    print("=" * 70)


if __name__ == "__main__":
    results = run_agentbench_evaluation(model_name="gpt-4", num_trials=3)
    print_leaderboard(results, "GPT-4")
```

### 4.4 通用 Benchmark 评测框架

```python
"""
通用 Benchmark 评测框架
适配任何 Gymnasium 兼容环境
"""
import gymnasium as gym
import numpy as np
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
import json
import os


@dataclass
class EvaluationResult:
    """评测结果数据类"""
    task_name: str
    policy_name: str
    num_episodes: int
    success_rate: float
    avg_episode_length: float
    std_episode_length: float
    avg_reward: float
    std_reward: float
    extra_metrics: Dict[str, float]


class BenchmarkEvaluator:
    """通用 Benchmark 评测器"""

    def __init__(self, env_id: str, policy_name: str = "policy"):
        self.env_id = env_id
        self.policy_name = policy_name
        self.env = None
        self.results: List[EvaluationResult] = []

    def make_env(self):
        """创建环境"""
        self.env = gym.make(self.env_id)
        return self.env

    def evaluate(
        self,
        policy: Callable,
        num_episodes: int = 100,
        extra_metrics_fn: Optional[Callable] = None
    ) -> EvaluationResult:
        """
        评测策略

        Args:
            policy: 策略函数，接受 obs 返回 action
            num_episodes: 评测回合数
            extra_metrics_fn: 额外指标计算函数 (env, info) -> dict
        """
        if self.env is None:
            self.make_env()

        episode_lengths = []
        episode_rewards = []
        success_count = 0
        extra_metric_values: Dict[str, List[float]] = {}

        for episode in range(num_episodes):
            obs, info = self.env.reset()
            done = False
            episode_reward = 0
            step_count = 0

            if extra_metrics_fn:
                # 初始化额外指标存储
                for key in extra_metrics_fn(self.env, {}).keys():
                    extra_metric_values.setdefault(key, [])

            while not done:
                action = policy(obs)
                obs, reward, terminated, truncated, info = self.env.step(action)

                episode_reward += reward
                step_count += 1
                done = terminated or truncated

            episode_lengths.append(step_count)
            episode_rewards.append(episode_reward)

            if info.get('success', False):
                success_count += 1

            # 收集额外指标
            if extra_metrics_fn:
                extra = extra_metrics_fn(self.env, info)
                for key, val in extra.items():
                    extra_metric_values[key].append(val)

            if (episode + 1) % 20 == 0:
                print(f"  [{episode+1}/{num_episodes}] SR={success_count/(episode+1):.2%}")

        # 汇总结果
        result = EvaluationResult(
            task_name=self.env_id,
            policy_name=self.policy_name,
            num_episodes=num_episodes,
            success_rate=success_count / num_episodes,
            avg_episode_length=float(np.mean(episode_lengths)),
            std_episode_length=float(np.std(episode_lengths)),
            avg_reward=float(np.mean(episode_rewards)),
            std_reward=float(np.std(episode_rewards)),
            extra_metrics={
                key: float(np.mean(vals))
                for key, vals in extra_metric_values.items()
            }
        )

        self.results.append(result)
        return result

    def save_results(self, filepath: str):
        """保存评测结果到 JSON"""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)

        results_dict = []
        for r in self.results:
            results_dict.append({
                'task_name': r.task_name,
                'policy_name': r.policy_name,
                'num_episodes': r.num_episodes,
                'success_rate': r.success_rate,
                'avg_episode_length': r.avg_episode_length,
                'std_episode_length': r.std_episode_length,
                'avg_reward': r.avg_reward,
                'std_reward': r.std_reward,
                'extra_metrics': r.extra_metrics
            })

        with open(filepath, 'w') as f:
            json.dump(results_dict, f, indent=2)

        print(f"结果已保存至 {filepath}")

    def print_summary(self):
        """打印评测汇总"""
        print("\n" + "=" * 70)
        print("Benchmark 评测汇总")
        print("=" * 70)
        print(f"{'任务':<30} {'策略':<15} {'SR':>8} {'平均长度':>10} {'平均奖励':>10}")
        print("-" * 70)

        for r in self.results:
            print(
                f"{r.task_name:<30} {r.policy_name:<15} "
                f"{r.success_rate:>8.2%} {r.avg_episode_length:>10.1f} "
                f"{r.avg_reward:>10.2f}"
            )

        print("=" * 70)


# ============ 使用示例 ============
if __name__ == "__main__":
    evaluator = BenchmarkEvaluator("CartPole-v1", "RandomPolicy")

    def random_policy(obs):
        return evaluator.env.action_space.sample()

    result = evaluator.evaluate(random_policy, num_episodes=100)

    evaluator.print_summary()
    evaluator.save_results("benchmark_results/cartpole_random.json")
```

---

## 5. 练习题

### 选择题

**1. Benchmark 的核心作用是什么？**
- A. 加速机器人本体的开发
- B. 提供标准化的评测环境和方法，实现公平比较
- C. 直接提升机器人的操作精度
- D. 替代强化学习训练

**2. SPL（Success weighted by Path Length）指标同时考虑了？**
- A. 成功率和泛化能力
- B. 成功率和路径效率
- C. 抓取稳定性和成功率
- D. 能耗和执行时间

**3. HomeRobot Benchmark 的主要应用场景是？**
- A. 工业装配线
- B. 家庭服务机器人的导航+操作
- C. 自动驾驶车辆
- D. 医疗手术机器人

**4. RAFFLE 的核心评测任务类型是？**
- A. 室内导航
- B. 桌面级精细操作（抓取、放置、插入）
- C. 自然语言对话
- D. 多智能体协作

**5. 泛化能力评测的关键是？**
- A. 训练集和测试集完全相同
- B. 训练集和测试集严格分离，且测试集代表新场景
- C. 只测试最简单的场景
- D. 多次测试取平均值即可

### 简答题

**6. 解释什么是 Sim-to-Real Gap，以及为什么它是具身智能 Benchmark 评测中的重要考量因素。**

**7. 对比 RAFFLE、HomeRobot、AgentBench 三个 Benchmark 的侧重点、应用场景和核心评测指标。**

**8. 你正在开发一个家庭服务机器人，需要选择合适的 Benchmark 进行评测。请说明你会选择哪个 Benchmark，并给出评测方案设计（包括任务选择、指标选择、泛化测试方案）。**

---

## 6. 练习题答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | Benchmark 的核心作用是标准化评测，让不同算法在统一的任务、环境、指标下进行公平比较。 |
| 2 | **B** | SPL = Success × (最优路径 / 实际路径)，同时衡量了成功率和路径效率。 |
| 3 | **B** | HomeRobot 专注于家庭服务机器人的导航+操作场景，基于真实住宅 3D 扫描环境。 |
| 4 | **B** | RAFFLE 专注于机器人手臂的桌面精细操作任务，包括抓取、放置、推、插入、叠放等。 |
| 5 | **B** | 泛化能力测试的核心是确保训练集和测试集严格分离，且测试场景代表算法在实际部署中会遇到的新情况。 |

### 简答题答案

**6. Sim-to-Real Gap 的概念与重要性**

**Sim-to-Real Gap（仿真-现实差距）**指的是机器人在仿真环境中训练得到的策略，在迁移到真实物理世界时性能下降的现象。这是具身智能 Benchmark 评测中的核心考量因素，原因如下：

- **物理真实性不足**：仿真器的物理参数（摩擦力、关节刚度、传感器噪声）与真实机器人存在偏差
- **视觉差异**：仿真生成的图像与真实相机拍摄的图像在纹理、光照、阴影上有本质区别
- **传感器噪声模型**：真实传感器（IMU、深度相机、力矩传感器）的噪声特性难以精确建模
- **控制延迟**：仿真中的控制循环是理想化的，真实机器人存在通信延迟和控制滞后

**评测意义**：一个在仿真 Benchmark 上表现优秀的算法，如果在 Sim-to-Real Gap 上表现差，则无法实际部署。因此评测时应该：
1. 报告仿真指标的同时说明可能的现实差距
2. 在 Benchmark 中包含 Domain Randomization（领域随机化）测试
3. 尽可能提供实机评测子集（如 RAFFLE 支持的仿真+实物双测）

---

**7. RAFFLE、HomeRobot、AgentBench 三大 Benchmark 对比**

| 维度 | RAFFLE | HomeRobot | AgentBench |
|------|--------|-----------|------------|
| **侧重点** | 机器人手臂桌面精细操作 | 家庭环境导航+操作 | LLM 作为 Agent 的通用能力 |
| **核心任务** | 抓取、放置、推、插入、叠放 | 导航到目标、物体操作、多步任务 | OS操作、知识推理、代码开发、机器人任务规划 |
| **环境** | PyBullet/Isaac Gym仿真+实物 | Habitat仿真+Stretch实物 | 纯软件仿真（Docker/模拟器） |
| **核心指标** | 成功率、抓取稳定性 | SR、SPL、碰撞次数 | 1-5 分制任务完成度 |

核心差异：RAFFLE 专注"手"（manipulation），HomeRobot 专注"移动+手"，AgentBench 专注"大脑"（LLM Agent）。

---

**8. 家庭服务机器人 Benchmark 评测方案**

**选择 Benchmark**：首选 **HomeRobot**（Meta AI），次选 RAFFLE + Habitat 组合。

**评测任务选择**：

| 任务类型 | 具体任务 | 难度级别 |
|---------|---------|---------|
| 导航 | Object Navigation（找苹果） | Easy → Hard |
| 操作 | Pick-and-Place（抓取放置） | Medium |
| 多步 | Interactive Navigation（开抽屉+放杯子） | Hard |
| 泛化 | 新物体/新场景（训练未见过的房间） | Cross-domain |

**指标选择**：

| 指标
| 指标类型 | 指标名称 | 说明 |
|---------|---------|------|
| 核心指标 | SR（成功率） | 任务完成比例，主衡量标准 |
| 效率指标 | SPL | 成功率加权路径效率 |
| 安全性指标 | 碰撞次数 | 物理安全性 |
| 泛化指标 | 新场景 SR | 跨房间/跨物体泛化能力 |

**泛化测试方案**：

1. **物体泛化**：在 HM3D 物体集合中留出 20% 未训练物体类别，评估抓取/导航在新物体上的成功率退化
2. **场景泛化**：使用 Habitat 官方划分的 Train/Val 场景分割，Val 场景完全不出现在训练数据中
3. **光照/时间泛化**：在仿真中随机化光照强度、阴影方向，测试视觉策略的鲁棒性
4. **Sim-to-Real**：在仿真达标后，在真实 Stretch 机器人上进行 10-20 个 episode 的闭环验证

---

## 本章小结

| 概念 | 要点 |
|------|------|
| **Benchmark** | 标准化评测工具 = 任务集合 + 评测环境 + 评估指标 + 评测协议 |
| **RAFFLE** | 桌面精细操作 benchmark（抓取/放置/插入/叠放），支持仿真+实物 |
| **HomeRobot** | 家庭服务机器人 benchmark，导航+操作，基于 HM3D 真实场景 |
| **AgentBench** | LLM Agent 多维评测，覆盖 OS/知识图谱/机器人/软件开发 |
| **成功率（SR）** | 最核心指标，任务完成比例，对随机种子敏感需多次评测 |
| **SPL** | 同时衡量成功率和路径效率，适合导航任务 |
| **泛化能力** | 在新场景/新物体上的表现，训练-测试严格分离 |
| **Sim-to-Real Gap** | 仿真与真实的性能差距，通过 Domain Randomization 缩小 |
| **评测框架** | BenchmarkEvaluator 通用框架，适配任意 Gymnasium 环境 |

**延伸学习资源**：
- RAFFLE Paper: `https://arxiv.org/abs/xxxx`
- HomeRobot GitHub: `https://github.com/facebookresearch/home-robot`
- AgentBench Paper: `https://arxiv.org/abs/2308.03688`
- CALVIN Benchmark: `https://github.com/calvin-dataset/calvin`
- MetaWorld: `https://github.com/rlworkgroup/metaworld`
- VIMA-Bench: `https://vimalabs.github.io/`
- Habitat: `https://aihabitat.org/`
