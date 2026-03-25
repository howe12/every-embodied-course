# 18-4 CALVIN 与长程任务链评估

> **前置课程**：18-1 具身智能 Benchmark 概述、18-2 CALVIN 基准
> **后续课程**：18-5 Benchmark 项目实战

---

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 18-4 |
| 课程名称 | CALVIN 与长程任务链评估 |
| 所属模块 | 18-具身智能benchmark |
| 难度等级 | ⭐⭐⭐⭐☆ |
| 预计学时 | 4小时 |
| 前置知识 | CALVIN 基准（18-2）、强化学习基础（14-1）、大模型技术（13-1）、PyTorch 基础 |

---

## 目录

1. [CALVIN 概述与 ABCD 难度体系](#1-calvin-概述与-abcd-难度体系)
2. [长程任务链设计原理](#2-长程任务链设计原理)
3. [评估协议：语言泛化与零样本迁移](#3-评估协议语言泛化与零样本迁移)
4. [基线方法：CAPS 与 Language Table](#4-基线方法caps-与-language-table)
5. [代码实现](#5-代码实现)
6. [练习题](#6-练习题)
7. [参考答案](#7-参考答案)

---

## 1. CALVIN 概述与 ABCD 难度体系

### 1.1 为什么需要长程任务链 Benchmark

在真实机器人场景中，人类指令往往是**复合的、长时序的**：

> *"先把红色方块放进抽屉，然后关上门，接着把蓝色的杯子放到桌上，最后把灯打开"*

这类指令包含 4 个子任务，子任务之间存在**时序依赖**和**物体依赖**。传统单步 Benchmark（如 RLBench 单一任务）无法评测这种能力。

**长程任务链评测的必要性**：

| 维度 | 单一任务 Benchmark | 长程任务链 Benchmark（CALVIN） |
|------|---------------------|----------------------------------|
| **任务长度** | 1 步 | 2~6 步 |
| **时序依赖** | 无 | 有（顺序/物体/状态依赖） |
| **语言复杂度** | 简短命令 | 完整自然语言句子 |
| **评测重点** | 动作精度 | 语言理解 + 长时序规划 + 动作执行 |
| **典型失败** | 抓取失败 | 第 2 步之后动作混乱 |

CALVIN 正是为解决这一评测空白而设计的。

### 1.2 CALVIN 数据集总览

**CALVIN**（Composing Actions from Language for Vision-based IN-context control）由 DeepMind 等团队发布，核心贡献是**语言条件化的长时序多步操作 Benchmark**。

**数据集核心参数**：

| 参数 | 数值 |
|------|------|
| 仿真引擎 | PyBullet |
| 机械臂 | Franka Panda 7DoF |
| 场景数 | 1 个标准桌面场景 |
| 任务类别 | 4 大类（推移、抓取放置、抽屉、开关） |
| 任务总数 | 34 个单一技能 |
| 最大链长 | 6 步 |
| 语言指令数 | ~2,500 条不同指令 |
| 视觉输入 | RGB-D + 机器人状态 |
| 发布年份 | 2022 |

**GitHub**：`https://github.com/calvin-dataset/calvin`

**论文**：[CALVIN: A Multi-Task Benchmark for Learning from Human Feedback](https://arxiv.org/abs/2204.11913)

### 1.3 ABCD 四级难度体系

CALVIN 的核心创新之一是 **ABCD 四级难度体系**，从易到难逐级增加评测难度：

```
CALVIN ABCD 难度递增体系

难度 A（语言理解）          难度 B（短链执行）
  单句指令                    2步链
  ↓                          ↓
  "把红色块放到盒子里"         "把红块放盒子里，然后开抽屉"
  
难度 C（长链 + 干扰）        难度 D（零样本 + 干扰）
  4步链 + 干扰指令             全新语言描述 + 干扰物体
  ↓                          ↓
  "依次完成：放块→开抽屉→     "请将那个圆柱体置于
  放块→关抽屉→推开关"          左侧容器中，然后调节
                               旋钮至右侧位置"
```

**ABCD 各难度详解**：

**难度 A：单步语言理解（Single-Step Language）**

- 评测目标：验证机器人能否正确理解单步语言指令
- 任务链长：仅 1 步（无链式）
- 语言描述：简短单句，如 *"pick the red block"*
- 评测重点：语言→动作映射的准确性

**难度 B：短链执行（Short-Horizon Chaining）**

- 评测目标：验证两步骤链的执行能力
- 任务链长：2 步
- 指令示例：*"put the red block in the drawer, then open the blue drawer"*
- 评测重点：两步之间的时序衔接

**难度 C：长链 + 干扰（Long-Horizon with Distractors）**

- 评测目标：验证 4 步以上长链的执行能力，同时存在干扰指令
- 任务链长：4~6 步
- 干扰类型：
  - 语言干扰：指令中包含与任务无关的描述
  - 物体干扰：场景中出现与目标无关的物体
  - 状态干扰：部分物体处于非预期状态
- 评测重点：长时序记忆、抗干扰能力

**难度 D：零样本语言泛化（Zero-Shot Language Generalization）**

- 评测目标：验证模型对**训练时未见过的语言指令**的泛化能力
- 任务链长：任意（2~6 步）
- 语言来源：全新的语言描述，与训练集无重叠
- 评测重点：语言泛化、语义理解、组合泛化

**ABCD 难度对应的评测指标侧重点**：

| 难度 | 核心指标 | 辅助指标 |
|------|---------|---------|
| **A** | 单步成功率 $\text{SR}_{\text{single}}$ | 动作精度 |
| **B** | 两步连续成功率 $\text{CSR}_2$ | 链完成率 |
| **C** | 长链成功率 $\text{SR}_{\text{task}}$、平均完成步数 ACS | $\text{CSR}_k$（$k$=3,4） |
| **D** | 零样本成功率、语言泛化率 | 与 A/B/C 的成功率差距 |

---

## 2. 长程任务链设计原理

### 2.1 语言指令结构分析

CALVIN 的语言指令是**自然语言描述的复合动作**，每条指令包含多个子任务描述。指令设计遵循以下原则：

**结构特征**：

```python
"""
CALVIN 指令结构分析
"""
# CALVIN 指令示例
instruction = "首先将红色方块放入左侧盒子，然后打开右侧抽屉，最后把蓝色球放进抽屉"

# 指令结构拆解
instruction_structure = {
    'full_text': instruction,
    'subtasks': [
        {
            'id': 1,
            'description': '将红色方块放入左侧盒子',
            'action_type': 'pick_and_place',
            'target_object': 'red_block',
            'container': 'left_box',
            'marker': '首先'
        },
        {
            'id': 2,
            'description': '打开右侧抽屉',
            'action_type': 'drawer_open',
            'target_object': 'right_drawer',
            'marker': '然后'
        },
        {
            'id': 3,
            'description': '把蓝色球放进抽屉',
            'action_type': 'pick_and_place',
            'target_object': 'blue_ball',
            'container': 'right_drawer',  # 承接上一步的状态
            'marker': '最后'
        }
    ],
    'temporal_dependency': True,  # 存在时序依赖
    'object_dependency': True      # 物体依赖（抽屉需先打开才能放球）
}

print(f"子任务数量: {len(instruction_structure['subtasks'])}")
print(f"时序依赖: {instruction_structure['temporal_dependency']}")
print(f"物体依赖: {instruction_structure['object_dependency']}")
```

**语言标记词**：

| 标记词 | 含义 | 时序含义 |
|--------|------|---------|
| 首先/先 | 第一步 | 开始 |
| 然后/接着 | 后续步骤 | 顺序执行 |
| 最后/之后 | 最后步骤 | 结束 |
| 再 | 重复或补充步骤 | 继续 |

### 2.2 任务链依赖图

CALVIN 任务链的子任务之间存在**有向依赖关系**，可以用依赖图表示：

```python
"""
CALVIN 任务链依赖图
"""
# 定义任务节点和依赖边
task_graph = {
    'nodes': [
        {'id': 'A', 'task': '推移红块到中央'},
        {'id': 'B', 'task': '打开左抽屉'},
        {'id': 'C', 'task': '抓取蓝球'},
        {'id': 'D', 'task': '将蓝球放入左抽屉'},
        {'id': 'E', 'task': '关闭抽屉'},
    ],
    'edges': [
        ('A', 'C'),  # A完成后才能C（物体A移动后C才能到达）
        ('B', 'D'),  # B完成后才能D（抽屉先打开）
        ('C', 'D'),  # C完成后才能D（球要先抓取）
        ('D', 'E'),  # D完成后才能E（东西放好才能关）
    ]
}

# 可视化依赖关系
print("依赖图边（拓扑排序顺序）：")
print("  A → C → D → E")
print("  B → D")
print()
print("关键路径（最长路径）：")
print("  A → C → D → E （4步）")
print()
print("最短可执行路径：")
print("  A → C → D → E （必须按序执行）")
```

**依赖类型分类**：

| 依赖类型 | 定义 | 示例 | 对评测的影响 |
|---------|------|------|-------------|
| **时序依赖** | 必须先完成后一个才能开始 | "先开抽屉，再放东西" | 一步错，全链失败 |
| **物体依赖** | 一个任务的物体是另一个的目标 | "把球放盒子里，再把盒子推走" | 物体状态需维护 |
| **空间依赖** | 位置关系约束动作 | "把物体放到抽屉打开后的位置" | 需要空间推理 |
| **状态依赖** | 机械/场景状态约束 | "灯必须先开才能看到物体" | 状态机维护 |

### 2.3 任务链生成规则

CALVIN 的任务链不是随机拼接，而是通过**手工设计的组合规则**生成，确保依赖合理且物理可行：

```python
"""
CALVIN 任务链自动生成规则
"""

# 基础任务库（34个单步技能）
primitive_skills = {
    'push': ['push_red_block', 'push_blue_block', 'push_green_ball'],
    'pick_place': ['place_red_in_left_box', 'place_blue_in_right_box'],
    'drawer': ['open_left_drawer', 'close_left_drawer', 'open_right_drawer'],
    'switch': ['toggle_switch_left', 'toggle_switch_right', 'rotate_knob'],
}

# 任务链生成规则
chain_rules = {
    # 规则1：推移后抓取（物体位置改变后需重新定位）
    ('push', 'pick_place'): {
        'valid': True,
        'constraint': '抓取目标必须在推移后的新位置',
        'example': '推红块到中央 → 抓取红块'
    },
    
    # 规则2：开抽屉后才能放东西进去
    ('drawer_open', 'pick_place'): {
        'valid': True,
        'constraint': 'pick_place的目标容器必须是已打开的抽屉',
        'example': '打开左抽屉 → 放蓝球进左抽屉'
    },
    
    # 规则3：放东西后才能关抽屉
    ('pick_place', 'drawer_close'): {
        'valid': True,
        'constraint': '关抽屉前该抽屉必须已有物体',
        'example': '放球进抽屉 → 关抽屉'
    },
    
    # 规则4：关闭抽屉后不能再往里放（物理不可行）
    ('drawer_close', 'pick_place'): {
        'valid': False,
        'reason': '物理不可行：关上的抽屉无法放入物体'
    },
}

def generate_valid_chain(max_steps=4):
    """
    生成一条有效的任务链
    
    Args:
        max_steps: 最大步数（不超过6步）
    
    Returns:
        chain: 有效任务链列表
    """
    import random
    
    chain = []
    available_primitives = list(primitive_skills.keys())
    
    for step in range(max_steps):
        task_type = random.choice(available_primitives)
        skill = random.choice(primitive_skills[task_type])
        
        chain.append({
            'step': step + 1,
            'type': task_type,
            'skill': skill
        })
    
    return chain

# 示例：生成一条4步链
example_chain = generate_valid_chain(max_steps=4)
print("生成的任务链：")
for task in example_chain:
    print(f"  步骤{task['step']}: {task['skill']}")
```

### 2.4 成功标准定义

CALVIN 对每个子任务定义了**严格的成功条件（Success Criteria）**，只有满足所有条件才计入成功：

```python
"""
CALVIN 子任务成功标准定义
"""

# 各类任务的成功条件
success_criteria = {
    # ============ 推移任务 ============
    'push': {
        'description': '将物体推移到目标区域',
        'conditions': [
            {
                'name': 'position_check',
                'type': 'distance',
                'target': 'object',
                'goal': 'target_zone',
                'threshold': 0.05,  # 物体中心距目标区域中心 < 5cm
                'unit': 'meters'
            },
            {
                'name': 'height_check',
                'type': 'z_above_table',
                'threshold': 0.02,  # 物体高度 > 桌面 2cm（仍在桌上）
                'unit': 'meters'
            }
        ],
        'success_formula': 'position_check AND height_check'
    },
    
    # ============ 抓取放置任务 ============
    'pick_and_place': {
        'description': '抓取物体并放置到目标容器/位置',
        'conditions': [
            {
                'name': 'pick_check',
                'type': 'gripper_holds_object',
                'description': '夹爪成功抓握住物体'
            },
            {
                'name': 'place_position',
                'type': 'distance',
                'target': 'object',
                'goal': 'target_position',
                'threshold': 0.05,
                'unit': 'meters'
            },
            {
                'name': 'place_height',
                'type': 'z_above_target',
                'threshold': 0.03,  # 物体高度在目标位置上方
                'unit': 'meters'
            }
        ],
        'success_formula': 'pick_check AND place_position AND place_height'
    },
    
    # ============ 抽屉操作任务 ============
    'drawer_open': {
        'description': '打开指定抽屉',
        'conditions': [
            {
                'name': 'drawer_angle',
                'type': 'joint_angle',
                'joint': 'drawer_joint',
                'threshold': 0.26,  # 抽屉打开角度 > 15°（≈0.26rad）
                'unit': 'radians'
            },
            {
                'name': 'object_not_dropped',
                'type': 'object_in_drawer',
                'description': '抽屉内物体未掉落'
            }
        ],
        'success_formula': 'drawer_angle AND object_not_dropped'
    },
    
    # ============ 开关操作任务 ============
    'switch_toggle': {
        'description': '将开关拨到指定状态',
        'conditions': [
            {
                'name': 'switch_state',
                'type': 'discrete_state',
                'goal_state': 'on',  # 或 'off'
                'threshold': None
            }
        ],
        'success_formula': 'switch_state'
    }
}

def evaluate_success(task_type, observation):
    """
    评估子任务是否成功
    
    Args:
        task_type: 任务类型
        observation: 当前观测（包含位置、关节角度等）
    
    Returns:
        success: bool
        details: 详细评判信息
    """
    criteria = success_criteria[task_type]
    results = {}
    
    for cond in criteria['conditions']:
        if cond['type'] == 'distance':
            # 计算物体到目标的距离
            obj_pos = observation[f"{cond['target']}_position"]
            goal_pos = observation[f"{cond['goal']}_position"]
            dist = ((obj_pos - goal_pos) ** 2).sum() ** 0.5
            results[cond['name']] = dist < cond['threshold']
            
        elif cond['type'] == 'joint_angle':
            # 检查关节角度
            joint_pos = observation['joint_states'][cond['joint']]
            results[cond['name']] = abs(joint_pos) > cond['threshold']
            
        elif cond['type'] == 'discrete_state':
            # 检查开关状态
            state = observation['switch_state']
            results[cond['name']] = state == cond['goal_state']
    
    # 根据成功公式计算最终结果
    formula = criteria['success_formula']
    # 实际使用时需用安全的 eval 替代
    success = all(results.get(k, False) for k in results.keys())
    
    return success, results

print("成功标准库已定义，可对各类型子任务进行评判")
```

---

## 3. 评估协议：语言泛化与零样本迁移

### 3.1 标准评估协议

CALVIN 定义了**标准化评测流程**，确保所有方法在同等条件下比较：

```python
"""
CALVIN 标准评测协议
"""

# ============ 评测配置 ============
eval_protocol = {
    # 环境配置
    'env': {
        'scene': 'CALVIN-standard-table',
        'robot': 'panda_arm',
        'camera': ['front', 'wrist'],  # 前置相机 + 手腕相机
        'observation': ['rgb', 'depth', 'robot_state', 'task_lang'],
    },
    
    # 评测任务集
    'task_splits': {
        'ABC': {
            'description': 'A+B+C 难度评测（语言内插）',
            'train_instructions': 1800,   # 训练指令数
            'eval_instructions': 300,      # 评测指令数
            'difficulty': ['A', 'B', 'C'],
            'language_scope': 'seen'       # 训练见过的语言表述
        },
        'D': {
            'description': 'D 难度评测（语言泛化）',
            'eval_instructions': 500,      # 全新语言指令
            'difficulty': ['D'],
            'language_scope': 'unseen'     # 未见过的语言表述
        }
    },
    
    # 评测参数
    'eval_params': {
        'episodes_per_task': 25,         # 每条指令评测 25 次
        'max_steps_per_episode': 300,    # 每回合最多 300 步
        'seed_range': list(range(42, 52)),  # 不同随机种子（10个）
        'reset_variations': 5,           # 初始状态变化数
    }
}

# ============ 评测执行流程 ============
def run_calvin_evaluation(agent, task_split='ABC', verbose=True):
    """
    运行 CALVIN 标准评测
    
    步骤：
    1. 加载评测指令集
    2. 对每条指令执行 N 次评测
    3. 计算各项指标
    4. 汇总结果并报告
    
    Args:
        agent: 待评测的策略模型（接受 language + observation → action）
        task_split: 'ABC' 或 'D'
        verbose: 是否打印详细过程
    
    Returns:
        results: 评测结果字典
    """
    import numpy as np
    
    # 模拟环境（实际使用 calvin_environment）
    class DummyEnv:
        def reset(self, seed=0):
            return {}, {'subtask_status': [0, 0, 0]}
        def step(self, action):
            done = np.random.rand() < 0.05  # 5% 概率 episode 结束
            info = {'subtask_status': [1, 1, 0]}  # 前两步完成
            return {}, 0.0, done, False, info
    
    env = DummyEnv()
    instructions = [{'id': f'i{i}', 'description': f'instruction {i}', 
                     'subtasks': [f'task{i}_0', f'task{i}_1', f'task{i}_2']} 
                    for i in range(5)]
    
    # 初始化结果记录
    task_results = {instr['id']: [] for instr in instructions}
    
    # 对每条指令进行评测
    for instr in instructions:
        instr_id = instr['id']
        
        for seed in eval_protocol['eval_params']['seed_range']:
            obs, info = env.reset(seed=seed)
            completed_steps = 0
            
            for step_idx in range(eval_protocol['eval_params']['max_steps_per_episode']):
                # Agent 接收语言指令和观测，输出动作（模拟）
                action = agent.predict(observation=obs, language=instr['description'])
                obs, reward, terminated, truncated, info = env.step(action)
                completed_steps = sum(info.get('subtask_status', []))
                
                if terminated or truncated:
                    break
            
            task_results[instr_id].append({
                'seed': seed,
                'completed_steps': completed_steps,
                'total_steps': len(instr['subtasks']),
                'success': completed_steps == len(instr['subtasks'])
            })
            
            if verbose:
                print(f"  指令 {instr_id} [seed={seed}]: "
                      f"完成 {completed_steps}/{len(instr['subtasks'])} 步")
    
    # 计算汇总指标
    results = compute_calvin_metrics(task_results)
    return results

def compute_calvin_metrics(task_results):
    """
    计算 CALVIN 评测指标
    
    核心指标：
    - SR_task: 整链成功率
    - ACS: 平均完成步数
    - CSR_k: 连续 k 步成功率
    """
    import numpy as np
    
    all_completions = []
    all_successes = []
    
    for instr_id, runs in task_results.items():
        for run in runs:
            all_completions.append(run['completed_steps'])
            all_successes.append(run['success'])
    
    # 平均完成步数（Average Completion Steps）
    acs = np.mean(all_completions)
    
    # 整链成功率（Task Success Rate）
    sr_task = np.mean(all_successes)
    
    # 连续 k 步成功率（Chain Success Rate）
    max_steps = max(all_completions) if all_completions else 0
    csr = {}
    for k in range(1, max_steps + 1):
        csr[k] = np.mean([c >= k for c in all_completions])
    
    return {
        'ACS': acs,
        'SR_task': sr_task,
        'CSR': csr,
        'N_evaluations': len(all_completions)
    }

print("CALVIN 标准评测协议已就绪")
```

### 3.2 语言泛化评估

语言泛化是 CALVIN 区分其他 Benchmark 的关键评测维度，衡量模型对**未见过语言指令**的理解和执行能力。

**语言泛化的三个层次**：

| 层次 | 说明 | 示例 | 评测目标 |
|------|------|------|---------|
| **词汇泛化** | 同一物体/动作的不同词汇表达 | "red block" / "crimson cube" | 词汇多样性 |
| **句式泛化** | 不同句式表达相同语义 | "pick up" / "grasp" / "get" | 句式多样性 |
| **组合泛化** | 新组合的未见过的子任务 | "push red, then place blue"（训练时分别见过） | 组合能力 |

```python
"""
语言泛化评估详细实现
"""

# ============ 语言泛化测试集构建 ============
class LanguageGeneralizationEvaluator:
    """
    CALVIN 语言泛化评估器
    
    评测语言模型对未见过指令的泛化能力
    """
    
    def __init__(self, language_model, calvin_env):
        self.model = language_model
        self.env = calvin_env
        
        # 加载标准语言泛化测试集
        self.test_suite = self._load_generalization_suite()
    
    def _load_generalization_suite(self):
        """
        加载语言泛化测试集
        
        测试集包含三个层次的泛化样本：
        - Seen: 训练时见过的指令（用于基线对比）
        - Synonym: 同义词替换（词汇泛化）
        - Paraphrase: 句式改写（句式泛化）
        - Compositional: 组合泛化
        """
        test_suite = {
            # 训练时见过的指令（基线）
            'seen': [
                {
                    'id': 'seen_001',
                    'text': 'put the red block in the left drawer',
                    'task_chain': ['pick_red_block', 'place_in_left_drawer'],
                    'language_type': 'training_set'
                },
            ],
            
            # 同义词替换（词汇泛化）
            'synonym': [
                {
                    'id': 'syn_001',
                    'text': 'place the crimson cube inside the left compartment',
                    # red → crimson/scarlet/ruby, drawer → compartment/tray/container
                    'task_chain': ['pick_red_block', 'place_in_left_drawer'],
                    'language_type': 'vocabulary_substitution',
                    'transformations': [
                        {'original': 'red', 'replaced': 'crimson/scarlet/ruby'},
                        {'original': 'drawer', 'replaced': 'compartment/tray/container'}
                    ]
                },
                {
                    'id': 'syn_002',
                    'text': 'slide the azure sphere onto the right shelf',
                    # blue → azure/navy/cobalt, push → slide/shove
                    'task_chain': ['push_blue_ball', 'target_right'],
                    'language_type': 'vocabulary_substitution',
                },
            ],
            
            # 句式改写（句式泛化）
            'paraphrase': [
                {
                    'id': 'para_001',
                    'text': 'First, you need to grasp the red block. After that, put it into the left drawer.',
                    'task_chain': ['pick_red_block', 'place_in_left_drawer'],
                    'language_type': 'sentence_paraphrase',
                    'transformations': [
                        {'original': 'put ... in', 'replaced': 'place ... into / insert ... into'},
                        {'original': 'First', 'replaced': 'Initially / To begin with'}
                    ]
                },
            ],
            
            # 组合泛化（训练时各子任务分别见过，但组合是新的）
            'compositional': [
                {
                    'id': 'comp_001',
                    'text': 'open the left drawer, then place the green ball inside, and finally close the drawer',
                    'task_chain': ['open_left_drawer', 'place_green_ball', 'close_left_drawer'],
                    'language_type': 'compositional',
                    'note': '每个单步都在训练集出现过，但此组合方式未见过'
                },
            ]
        }
        
        return test_suite
    
    def evaluate_language_generalization(self):
        """
        执行完整的语言泛化评估
        
        Returns:
            results: 各泛化层次的详细评测结果
        """
        import numpy as np
        
        results = {}
        
        for level_name, samples in self.test_suite.items():
            level_successes = []
            level_completions = []
            
            for sample in samples:
                instr_id = sample['id']
                lang_text = sample['text']
                
                # 多次评测取平均
                n_runs = 25
                run_results = []
                
                for _ in range(n_runs):
                    obs, info = self.env.reset()
                    total_steps = 0
                    completed = 0
                    
                    for step in range(300):  # max steps
                        action = self.model.predict(
                            observation=obs,
                            language=lang_text
                        )
                        obs, reward, term, trunc, info = self.env.step(action)
                        completed = sum(info.get('subtask_status', []))
                        total_steps += 1
                        
                        if term or trunc:
                            break
                    
                    run_results.append({
                        'completed_steps': completed,
                        'expected_steps': len(sample['task_chain']),
                        'success': completed == len(sample['task_chain'])
                    })
                
                # 计算该样本的平均结果
                avg_completed = np.mean([r['completed_steps'] for r in run_results])
                avg_success = np.mean([r['success'] for r in run_results])
                
                level_successes.append(avg_success)
                level_completions.append(avg_completed)
            
            # 汇总该层次结果
            results[level_name] = {
                'mean_success_rate': np.mean(level_successes),
                'mean_completion_steps': np.mean(level_completions),
                'n_samples': len(samples)
            }
        
        return results

print("语言泛化评估器已就绪")
```

### 3.3 零样本迁移评估

零样本迁移（Zero-Shot Transfer）是 CALVIN 评测体系中**最难**的一档，对应**难度 D**，评估模型在完全未训练过的语言指令上的表现：

```python
"""
零样本迁移评估
"""

# ============ 零样本任务构建 ============
class ZeroShotTransferEvaluator:
    """
    CALVIN 零样本迁移评估
    
    核心思路：
    1. 训练时：模型学习"语言 → 动作"的映射能力
    2. 评测时：提供完全未见过的新语言指令
    3. 评估：模型能否通过语言理解泛化到新任务
    """
    
    def __init__(self, agent, calvin_env):
        self.agent = agent
        self.env = calvin_env
        
        # 定义零样本任务集（这些指令在训练时完全未出现）
        self.zero_shot_tasks = [
            {
                'id': 'zs_001',
                'instruction': '将最左边那个物体移到右侧的盒子里去',
                'subtasks': ['move_leftmost_object', 'to_right_box'],
                'novelty': '从未见过的量词（最左边）和方向描述'
            },
            {
                'id': 'zs_002',
                'instruction': 'rotate the knob three times clockwise, then place the cylinder beside it',
                'subtasks': ['rotate_knob_3x', 'place_cylinder_beside'],
                'novelty': '数量修饰（three times）+ 空间关系（beside）'
            },
            {
                'id': 'zs_003',
                'instruction': '先关掉开关，等两秒，再打开它',
                'subtasks': ['switch_off', 'wait_2s', 'switch_on'],
                'novelty': '时序动作（等两秒）+ 逆向操作'
            },
        ]
    
    def evaluate_zero_shot(self, verbose=True):
        """
        执行零样本迁移评测
        
        评估指标：
        - ZS-SR: 零样本整链成功率
        - ZS-ACS: 零样本平均完成步数
        - Generalization Gap: 与训练集表现的差距
        """
        import numpy as np
        
        results = []
        
        for task in self.zero_shot_tasks:
            task_id = task['id']
            instruction = task['instruction']
            
            # 运行多次评测
            n_runs = 50  # 零样本评测增加评测次数以确保统计显著性
            run_successes = []
            run_completions = []
            
            for run_idx in range(n_runs):
                obs, _ = self.env.reset(seed=run_idx)
                
                completed_steps = 0
                expected_steps = len(task['subtasks'])
                
                for step in range(300):
                    # Agent 根据全新指令推理动作
                    action = self.agent.predict(
                        observation=obs,
                        language=instruction,  # 完全未见过的新指令
                        mode='zero_shot'       # 零样本模式
                    )
                    
                    obs, reward, term, trunc, info = self.env.step(action)
                    completed_steps = sum(info.get('subtask_status', []))
                    
                    if term or trunc:
                        break
                
                run_successes.append(completed_steps == expected_steps)
                run_completions.append(completed_steps)
            
            # 计算该任务的零样本成功率
            zs_sr = np.mean(run_successes)
            zs_acs = np.mean(run_completions)
            
            results.append({
                'task_id': task_id,
                'instruction': instruction,
                'novelty_type': task['novelty'],
                'zero_shot_sr': zs_sr,
                'zero_shot_acs': zs_acs,
                'n_runs': n_runs
            })
            
            if verbose:
                print(f"  [{task_id}] {instruction[:40]}...")
                print(f"    ZS-SR: {zs_sr:.2%} | ZS-ACS: {zs_acs:.2f}")
        
        # 汇总结果
        overall_zs_sr = np.mean([r['zero_shot_sr'] for r in results])
        overall_zs_acs = np.mean([r['zero_shot_acs'] for r in results])
        
        return {
            'per_task': results,
            'overall_zero_shot_sr': overall_zs_sr,
            'overall_zero_shot_acs': overall_zs_acs,
            'n_tasks': len(results)
        }

print("零样本迁移评估器已就绪")
```

---

## 4. 基线方法：CAPS 与 Language Table

### 4.1 CAPS：条件化动作生成策略

**CAPS**（Conditional Action Policies from Segmentation）是 CALVIN 论文中提出的基线方法，核心思想是将语言指令编码为**条件向量**，然后基于条件向量生成动作。

**CAPS 架构**：

```
CAPS 整体架构（文字版）

┌──────────────┐     ┌──────────────┐     ┌────────────────────┐
│   RGB 图像   │     │  深度图像    │     │   语言指令 Embed   │
└──────┬───────┘     └──────┬───────┘     └────────┬───────────┘
       │                    │                      │
       ▼                    ▼                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    视觉编码器（CNN）                           │
│                  将 RGB + Depth 编码为视觉特征                  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  条件向量 c     │
                    │ (语言指令编码)   │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  动作策略网络 π(a|o,c)  │
              │  输入：视觉特征 + 条件向量│
              │  输出：7维连续动作      │
              └──────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   机械臂执行    │
                    │   7DoF 动作     │
                    └─────────────────┘
```

**CAPS 的核心创新**：

| 创新点 | 说明 |
|--------|------|
| **条件向量解耦** | 语言指令编码为独立条件向量，与视觉特征拼接输入策略网络 |
| **多任务统一策略** | 一个策略网络处理所有 34 个任务，通过条件向量区分 |
| **序列分割** | 自动推断当前执行到哪一步（子任务边界检测） |

**CAPS 代码实现**：

```python
"""
CAPS 模型实现（简化版）
"""
import torch
import torch.nn as nn

class LanguageEncoder(nn.Module):
    """
    语言编码器：将自然语言指令编码为条件向量
    
    使用预训练语言模型（如 CLIP）提取语言特征
    """
    def __init__(self, embedding_dim=512):
        super().__init__()
        # 使用简单的 LSTM 编码器（实际用 CLIP 等预训练模型）
        self.lstm = nn.LSTM(
            input_size=300,        # 词嵌入维度
            hidden_size=256,
            num_layers=2,
            batch_first=True,
            bidirectional=True
        )
        self.projection = nn.Linear(512, embedding_dim)  # 映射到条件向量维度    
    def forward(self, language_input):
        """
        Args:
            language_input: (batch, seq_len, embed_dim) 词嵌入序列
        
        Returns:
            condition_vector: (batch, embedding_dim) 条件向量
        """
        # LSTM 编码
        lstm_out, (h_n, c_n) = self.lstm(language_input)
        # 双向 LSTM 的最后隐状态拼接
        h_forward = h_n[-2, :, :]    # 正向最后隐状态
        h_backward = h_n[-1, :, :]   # 反向最后隐状态
        combined = torch.cat([h_forward, h_backward], dim=-1)  # (batch, 512)
        
        # 投影到条件向量空间
        condition_vector = self.projection(combined)  # (batch, embedding_dim)
        return condition_vector


class VisualEncoder(nn.Module):
    """
    视觉编码器：将 RGB + Depth 图像编码为视觉特征
    
    使用双分支 CNN 分别处理 RGB 和 Depth，然后融合
    """
    def __init__(self, feature_dim=512):
        super().__init__()
        
        # RGB 分支（EfficientNet-style）
        self.rgb_conv = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((7, 7)),
            nn.Flatten(),
            nn.Linear(128 * 7 * 7, feature_dim),
            nn.ReLU()
        )
        
        # Depth 分支（结构与 RGB 分支相同，输入通道数为 1）
        self.depth_conv = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((7, 7)),
            nn.Flatten(),
            nn.Linear(128 * 7 * 7, feature_dim),
            nn.ReLU()
        )
        
        # 特征融合层
        self.fusion = nn.Linear(feature_dim * 2, feature_dim)
    
    def forward(self, rgb, depth):
        """
        Args:
            rgb: (batch, 3, H, W)
            depth: (batch, 1, H, W)
        
        Returns:
            visual_features: (batch, feature_dim)
        """
        rgb_feat = self.rgb_conv(rgb)       # (batch, feature_dim)
        depth_feat = self.depth_conv(depth) # (batch, feature_dim)
        
        # 拼接融合
        combined = torch.cat([rgb_feat, depth_feat], dim=-1)
        visual_features = self.fusion(combined)
        
        return visual_features


class CAPSPolicy(nn.Module):
    """
    CAPS 条件化动作策略网络
    
    将视觉特征和语言条件向量拼接，输入策略网络输出动作
    """
    def __init__(self, visual_dim=512, language_dim=512, action_dim=7, hidden_dim=256):
        super().__init__()
        
        # 视觉编码器
        self.visual_encoder = VisualEncoder(feature_dim=visual_dim)
        
        # 语言编码器
        self.language_encoder = LanguageEncoder(embedding_dim=language_dim)
        
        # 融合与策略网络
        self.fusion_layer = nn.Linear(visual_dim + language_dim, hidden_dim)
        self.policy_network = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)  # 输出 7 维动作
        )
        
        # 动作标准差（用于连续动作的方差预测）
        self.log_std = nn.Parameter(torch.zeros(action_dim))
    
    def forward(self, rgb, depth, language_embedding):
        """
        前向传播
        
        Args:
            rgb: (batch, 3, H, W) RGB 图像
            depth: (batch, 1, H, W) 深度图像
            language_embedding: (batch, seq_len, embed_dim) 语言词嵌入序列
        
        Returns:
            action_mean: (batch, action_dim) 动作均值
            action_std: (batch, action_dim) 动作标准差
        """
        # 编码视觉和语言
        visual_feat = self.visual_encoder(rgb, depth)
        lang_feat = self.language_encoder(language_embedding)
        
        # 拼接视觉特征和语言条件向量
        combined = torch.cat([visual_feat, lang_feat], dim=-1)  # (batch, 1024)
        
        # 融合层
        fused = torch.relu(self.fusion_layer(combined))  # (batch, hidden_dim)
        
        # 策略网络输出动作均值
        action_mean = self.policy_network(fused)  # (batch, action_dim)
        
        # 动作标准差（可学习参数）
        action_std = torch.exp(self.log_std).expand_as(action_mean)
        
        return action_mean, action_std
    
    def predict_action(self, rgb, depth, language_embedding, deterministic=False):
        """
        预测动作（用于推理）
        
        Args:
            deterministic: 若为 True，返回均值；否则采样
        """
        action_mean, action_std = self.forward(rgb, depth, language_embedding)
        
        if deterministic:
            return action_mean
        else:
            # 从正态分布采样
            noise = torch.randn_like(action_mean)
            action = action_mean + action_std * noise
            return action


# ============ CAPS 训练示例 ============
def train_caps_on_calvin():
    """
    CAPS 在 CALVIN 上的训练示例
    """
    import torch.optim as optim
    
    # 初始化模型
    policy = CAPSPolicy(
        visual_dim=512,
        language_dim=512,
        action_dim=7,
        hidden_dim=256
    )
    
    # 优化器（AdamW，学习率 1e-4）
    optimizer = optim.AdamW(policy.parameters(), lr=1e-4, weight_decay=1e-2)
    
    # 模拟训练循环
    n_epochs = 100
    batch_size = 32
    
    for epoch in range(n_epochs):
        total_loss = 0.0
        
        # 模拟一个 batch 的数据
        rgb = torch.randn(batch_size, 3, 200, 200)
        depth = torch.randn(batch_size, 1, 200, 200)
        lang_emb = torch.randn(batch_size, 20, 300)  # seq_len=20, embed=300
        target_action = torch.randn(batch_size, 7)
        
        # 前向传播
        action_mean, action_std = policy(rgb, depth, lang_emb)
        
        # 行为克隆损失：最小化动作均方误差
        # 同时鼓励标准差不要过大（正则化）
        loss = torch.mean((action_mean - target_action) ** 2)
        loss = loss + 0.01 * torch.mean(torch.log(action_std ** 2 + 1e-6))
        
        # 反向传播
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(policy.parameters(), max_norm=1.0)
        optimizer.step()
        
        total_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{n_epochs}, Loss: {total_loss:.4f}")
    
    print("CAPS 训练完成！")
    return policy

print("CAPS 模型已定义，可用于 CALVIN 长程任务训练")

### 4.2 Language Table：语言条件桌面操控

**Language Table** 是 Google 推出的另一个语言条件机器人操控环境，与 CALVIN 相比更轻量，主要用于**语言-动作对齐**的研究。

**Language Table vs CALVIN**：

| 维度 | Language Table | CALVIN |
|------|----------------|--------|
| **场景** | 2D 俯视桌面 | 3D PyBullet 仿真 |
| **机械臂** | 无（推块agent） | Franka Panda 7DoF |
| **任务链长** | 1~2 步 | 2~6 步 |
| **语言复杂度** | 简单指令 | 复合自然语言 |
| **研究重点** | 语言-动作对齐 | 长程规划 + 语言泛化 |
| **数据规模** | ~200K 演示 | ~1M 演示 |

**Language Table 核心机制**：

```python
"""
Language Table 环境示例
"""

class LanguageTableEnv:
    """
    Language Table 仿真环境（简化版）
    
    特点：
    - 俯视视角（2D 投影）
    - 物体在桌面上滑动（2D 位置）
    - 夹爪简化为"推"动作
    """
    
    def __init__(self):
        self.observation_space = {
            'rgb': (128, 128, 3),       # 俯视 RGB 图像
            'object_positions': (4, 2), # 最多 4 个物体的 (x, y) 位置
            'gripper_pos': (2,),         # 夹爪 (x, y) 位置
        }
        self.action_space = (3,)         # (dx, dy, gripper_action)
        
        # 物体列表
        self.objects = ['red_block', 'blue_block', 'green_ball', 'yellow_cylinder']
        
        # 初始位置（随机）
        import numpy as np
        self.positions = {obj: np.random.rand(2) * 0.8 + 0.1 for obj in self.objects}
    
    def reset(self):
        """重置环境"""
        import numpy as np
        self.positions = {obj: np.random.rand(2) * 0.8 + 0.1 for obj in self.objects}
        return self._get_observation()
    
    def step(self, action):
        """
        执行动作
        
        Args:
            action: (dx, dy, grip) - 位置增量和夹爪动作
        """
        import numpy as np
        
        dx, dy, grip = action
        gripper_pos = self.positions.get('gripper', np.array([0.5, 0.5]))
        
        # 更新夹爪位置
        new_gripper = np.clip(gripper_pos + np.array([dx, dy]), 0.1, 0.9)
        self.positions['gripper'] = new_gripper
        
        # 检查是否推动物体（夹爪与物体足够近时）
        for obj, pos in self.positions.items():
            if obj == 'gripper':
                continue
            dist = np.linalg.norm(new_gripper - pos)
            if dist < 0.1:  # 接触阈值
                self.positions[obj] = np.clip(pos + np.array([dx, dy]) * 0.5, 0.1, 0.9)
        
        obs = self._get_observation()
        reward = self._compute_reward()
        done = False  # Language Table 通常不设终止条件
        info = {}
        
        return obs, reward, done, info
    
    def _get_observation(self):
        """获取当前观测"""
        import numpy as np
        obs = {
            'rgb': np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8),
            'object_positions': np.array([self.positions[obj] for obj in self.objects]),
            'gripper_pos': self.positions.get('gripper', np.array([0.5, 0.5])),
        }
        return obs
    
    def _compute_reward(self):
        """计算奖励（简化版：任务相关）"""
        return 0.0


def language_table_evaluation():
    """
    Language Table 评测示例
    
    评测语言条件策略在不同语言指令下的成功率
    """
    import numpy as np
    
    env = LanguageTableEnv()
    
    # 评测指令集
    instructions = [
        "push the red block to the left",
        "move the blue block near the green ball",
        "slide the yellow cylinder to the center",
        "push all the objects to the right side",
    ]
    
    results = {}
    
    for instr in instructions:
        # 多次评测
        successes = []
        
        for _ in range(20):
            obs = env.reset()
            
            for step in range(100):  # 最多 100 步
                # 模拟语言条件策略（随机策略作为基线）
                action = np.random.randn(3) * 0.1  # 小幅随机动作
                obs, reward, done, info = env.step(action)
                
                if done:
                    break
            
            # 判断是否完成任务（简化：随机给结果）
            successes.append(np.random.rand() < 0.3)  # 30% 成功率
        
        results[instr] = {
            'success_rate': np.mean(successes),
            'n_evaluations': len(successes)
        }
        
        print(f"指令: '{instr}'")
        print(f"  成功率: {results[instr]['success_rate']:.2%}")
    
    return results

print("Language Table 环境已就绪")

### 4.3 其他模仿学习基线

除 CAPS 和 Language Table 外，CALVIN 还评估了以下模仿学习基线方法：

**主要基线方法汇总**：

| 方法 | 类型 | 特点 | 在 CALVIN 上的表现 |
|------|------|------|-------------------|
| **RT-1** | VLA 模型 | 13万条数据训练的视觉-语言-动作 Transformer | Action-32k: SR~45% |
| **BC-Z** | 行为克隆 | 支持零样本新任务泛化 | Action-32k: SR~40% |
| **GATO** | 多任务策略 | 单个模型处理所有任务 | Action-32k: SR~38% |
| **CALVIN 基线（ Ours）** | CAPS | 条件化策略 + 序列分割 | Action-32k: SR~52% |
| **随机策略** | — | 随机动作采样 | Action-32k: SR~5% |

**RT-1 详解**：

RT-1（Robotics Transformer 1）是 Google Robotics 提出的早期 VLA 模型，在 CALVIN 上作为经典基线：

```python
"""
RT-1 风格策略网络（简化实现）
"""

class RT1Policy(nn.Module):
    """
    RT-1 风格的 Vision-Language-Action 模型
    
    架构：EfficientNet 视觉编码 + TokenLearner 语言压缩 + FiLM 条件融合 + RNN 动作解码
    """
    def __init__(self, action_dim=7):
        super().__init__()
        
        # 视觉编码器（EfficientNet-B0）
        from torchvision.models import efficientnet_b0
        self.vision_encoder = efficientnet_b0(weights=None)
        self.vision_encoder.classifier = nn.Identity()  # 移除分类头
        vision_feature_dim = 1280
        
        # 语言编码器（Universal Sentence Encoder）
        self.language_encoder = nn.Linear(512, 256)  # 简化：假设已有多语言嵌入
        
        # FiLM 条件融合层（Feature-wise Linear Modulation）
        # 使用语言特征调制视觉特征
        self.film_beta = nn.Linear(256, vision_feature_dim)
        self.film_gamma = nn.Linear(256, vision_feature_dim)
        
        # 动作解码器（RNN）
        self.action_rnn = nn.LSTM(
            input_size=vision_feature_dim + 256,  # 视觉特征 + 语言特征
            hidden_size=512,
            num_layers=2,
            batch_first=True
        )
        
        # 动作输出头
        self.action_head = nn.Linear(512, action_dim)
        
        # 历史动作队列（用于时序连贯性）
        self.action_queue = []
        self.queue_size = 6  # 保存最近 6 个动作
    
    def forward(self, rgb_images, language_embedding, hidden_state=None):
        """
        Args:
            rgb_images: (batch, T, 3, H, W) 图像序列（历史帧）
            language_embedding: (batch, lang_dim) 语言嵌入
            hidden_state: LSTM 隐状态
        
        Returns:
            actions: (batch, action_dim) 当前动作
            new_hidden: LSTM 新的隐状态
        """
        batch_size = rgb_images.shape[0]
        
        # 1. 视觉编码：对所有历史帧编码并求平均（保留时序信息）
        all视觉_features = []
        for t in range(rgb_images.shape[1]):
            rgb_t = rgb_images[:, t]  # (batch, 3, H, W)
            feat_t = self.vision_encoder(rgb_t)  # (batch, vision_feature_dim)
            all视觉_features.append(feat_t)
        
        # 时序聚合（简单平均）
        visual_features = torch.stack(all视觉_features, dim=1).mean(dim=1)  # (batch, vision_dim)
        
        # 2. 语言编码
        lang_features = torch.relu(self.language_encoder(language_embedding))  # (batch, 256)
        
        # 3. FiLM 条件融合
        beta = self.film_beta(lang_features)   # (batch, vision_dim)
        gamma = self.film_gamma(lang_features) # (batch, vision_dim)
        
        # modulated = gamma * visual + beta
        modulated_features = gamma * visual_features + beta
        
        # 4. 拼接历史动作（如果有）
        if self.action_queue:
            history_actions = torch.stack(self.action_queue[-self.queue_size:], dim=1)
            # 将历史动作展平拼接到视觉特征
            history_flat = history_actions.reshape(batch_size, -1)
            modulated_features = torch.cat([modulated_features, history_flat], dim=-1)
        
        # 5. RNN 解码动作
        rnn_input = modulated_features.unsqueeze(1)  # (batch, 1, feature_dim)
        rnn_out, new_hidden = self.action_rnn(rnn_input, hidden_state)
        
        # 6. 输出动作
        action = torch.tanh(self.action_head(rnn_out.squeeze(1)))  # (batch, action_dim)
        
        # 更新动作队列
        self.action_queue.append(action.detach())
        if len(self.action_queue) > self.queue_size:
            self.action_queue.pop(0)
        
        return action, new_hidden
    
    def reset(self):
        """重置隐状态和动作队列"""
        self.action_queue = []
        return None


def evaluate_imitation_baselines():
    """
    评估各类模仿学习基线在 CALVIN 上的表现
    
    返回各方法的平均成功率和平均完成步数
    """
    import numpy as np
    
    # 各方法的模拟结果（基于论文数据）
    baseline_results = {
        'RT-1': {
            'Action-1k':  {'SR': 0.23, 'ACS': 1.8, 'CSR_2': 0.38},
            'Action-32k': {'SR': 0.45, 'ACS': 2.4, 'CSR_2': 0.61},
        },
        'BC-Z': {
            'Action-1k':  {'SR': 0.19, 'ACS': 1.5, 'CSR_2': 0.31},
            'Action-32k': {'SR': 0.40, 'ACS': 2.2, 'CSR_2': 0.55},
        },
        'CAPS': {
            'Action-1k':  {'SR': 0.28, 'ACS': 2.0, 'CSR_2': 0.45},
            'Action-32k': {'SR': 0.52, 'ACS': 2.8, 'CSR_2': 0.68},
        },
        'GATO': {
            'Action-1k':  {'SR': 0.18, 'ACS': 1.4, 'CSR_2': 0.29},
            'Action-32k': {'SR': 0.38, 'ACS': 2.1, 'CSR_2': 0.52},
        },
        'Random': {
            'Action-1k':  {'SR': 0.03, 'ACS': 0.5, 'CSR_2': 0.05},
            'Action-32k': {'SR': 0.03, 'ACS': 0.5, 'CSR_2': 0.05},
        },
    }
    
    print("=" * 60)
    print(f"{'基线方法':<12} {'评测集':<12} {'整链SR':<10} {'ACS':<8} {'CSR_2':<8}")
    print("=" * 60)
    
    for method, data in baseline_results.items():
        for dataset, metrics in data.items():
            print(f"{method:<12} {dataset:<12} "
                  f"{metrics['SR']:<10.2%} {metrics['ACS']:<8.2f} {metrics['CSR_2']:<8.2%}")
    print("=" * 60)
    
    return baseline_results

print("模仿学习基线评估已就绪")

---

## 5. 代码实现

### 5.1 CALVIN 环境加载与基础评测

```python
"""
CALVIN 环境加载与长程任务链评测
完整代码示例
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Tuple, Optional

# ============ 1. CALVIN 环境模拟 ============

class CALVINSimulator:
    """
    CALVIN 仿真环境简化实现
    
    实际使用时安装 calvinrobot 包：
    pip install calvinrobot
    """
    
    def __init__(self, task_difficulty='ABC'):
        """
        初始化 CALVIN 仿真环境
        
        Args:
            task_difficulty: 'ABC'（内插语言）或 'D'（泛化语言）
        """
        self.task_difficulty = task_difficulty
        self.max_steps = 300
        self.action_dim = 7  # 7DoF 动作
        
        # 初始化场景物体
        self.objects = {
            'red_block': {'position': np.array([0.3, 0.0, 0.0]), 'size': 0.04},
            'blue_block': {'position': np.array([0.0, 0.2, 0.0]), 'size': 0.04},
            'green_ball': {'position': np.array([-0.2, -0.1, 0.0]), 'size': 0.03},
            'left_drawer': {'open': False, 'joint_angle': 0.0},
            'right_drawer': {'open': False, 'joint_angle': 0.0},
            'switch': {'state': 'off'},
        }
        
        # 加载任务链库
        self.task_chains = self._load_task_chains()
        
        # 初始化机械臂状态
        self.gripper_pos = np.array([0.0, 0.0, 0.2])
        self.gripper_open = True
        self.joint_angles = np.zeros(7)
    
    def _load_task_chains(self) -> List[Dict]:
        """
        加载预定义的任务链
        
        每条任务链包含：
        - id: 唯一标识
        - instruction: 自然语言指令
        - subtasks: 子任务列表
        - difficulty: ABCD 难度等级
        """
        task_chains = [
            # ========== 难度 A：单步 ==========
            {
                'id': 'A_001',
                'difficulty': 'A',
                'instruction': 'Pick the red block.',
                'subtasks': [
                    {'type': 'pick', 'target': 'red_block', 'goal_position': None}
                ]
            },
            # ========== 难度 B：2步链 ==========
            {
                'id': 'B_001',
                'difficulty': 'B',
                'instruction': 'Pick the red block and place it in the left drawer.',
                'subtasks': [
                    {'type': 'pick', 'target': 'red_block'},
                    {'type': 'place', 'target': 'red_block', 'goal': 'left_drawer'}
                ]
            },
            # ========== 难度 C：4步链 ==========
            {
                'id': 'C_001',
                'difficulty': 'C',
                'instruction': 'Push the red block to the center, then open the left drawer, '
                               'place the blue block inside, and close the drawer.',
                'subtasks': [
                    {'type': 'push', 'target': 'red_block', 'goal_position': np.array([0.0, 0.0, 0.0])},
                    {'type': 'open_drawer', 'target': 'left_drawer'},
                    {'type': 'pick', 'target': 'blue_block'},
                    {'type': 'place', 'target': 'blue_block', 'goal': 'left_drawer'},
                    {'type': 'close_drawer', 'target': 'left_drawer'},
                ]
            },
            # ========== 难度 D：零样本（全新语言描述）==========
            {
                'id': 'D_001',
                'difficulty': 'D',
                'instruction': 'Initiate by displacing the crimson cube towards the origin, '
                               'subsequently accessing the primary storage compartment, '
                               'depositing the azure prism therein, '
                               'and securing the compartment.',
                'subtasks': [
                    {'type': 'push', 'target': 'red_block', 'goal_position': np.array([0.0, 0.0, 0.0])},
                    {'type': 'open_drawer', 'target': 'left_drawer'},
                    {'type': 'pick', 'target': 'blue_block'},
                    {'type': 'place', 'target': 'blue_block', 'goal': 'left_drawer'},
                    {'type': 'close_drawer', 'target': 'left_drawer'},
                ],
                'note': '使用未见过的词汇（crimson=红, azure=蓝, prism=块）'
            },
        ]
        return task_chains
    
    def reset(self, task_chain_id: Optional[str] = None) -> Tuple[Dict, Dict]:
        """
        重置环境
        
        Args:
            task_chain_id: 指定任务链 ID，若为 None 则随机选择
        
        Returns:
            observation: 当前观测
            info: 附加信息（含任务描述和子任务列表）
        """
        # 随机重置物体位置
        np.random.seed()
        for obj_name, obj_data in self.objects.items():
            if obj_name in ['left_drawer', 'right_drawer', 'switch']:
                continue  # 这些物体不随机化初始状态
            obj_data['position'] = np.random.rand(3) * 0.4 - 0.2  # 范围 [-0.2, 0.2]
            obj_data['position'][2] = 0.0  # 保持桌面高度
        
        # 重置抽屉和开关状态
        self.objects['left_drawer']['open'] = False
        self.objects['right_drawer']['open'] = False
        self.objects['switch']['state'] = 'off'
        
        # 重置机械臂
        self.gripper_pos = np.array([0.0, 0.0, 0.2])
        self.gripper_open = True
        self.joint_angles = np.zeros(7)
        
        # 选择任务链
        if task_chain_id is None:
            available_chains = [tc for tc in self.task_chains 
                               if tc['difficulty'] in self.task_difficulty]
            task_chain = np.random.choice(available_chains)
        else:
            task_chain = next(tc for tc in self.task_chains if tc['id'] == task_chain_id)
        
        # 初始化子任务状态
        self.current_subtask_idx = 0
        self.subtask_completed = [False] * len(task_chain['subtasks'])
        self.current_task_chain = task_chain
        
        return self._get_observation(), {
            'task_chain_id': task_chain['id'],
            'instruction': task_chain['instruction'],
            'subtasks': task_chain['subtasks'],
            'subtask_completed': self.subtask_completed.copy()
        }
    
    def _get_observation(self) -> Dict:
        """
        获取当前观测
        
        Returns:
            observation: 包含 RGB 图像、深度图像、机器人状态的字典
        """
        # 模拟 RGB 图像（实际从 PyBullet 获取）
        rgb = np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        
        # 模拟深度图像
        depth = np.random.rand(200, 200, 1).astype(np.float32)
        
        # 机器人状态
        robot_state = np.concatenate([
            self.joint_angles,           # 7 个关节角度
            [1.0 if self.gripper_open else 0.0],  # 夹爪状态
            self.gripper_pos,            # 夹爪位置 (x, y, z)
        ])  # (15,)
        
        return {
            'rgb': rgb,
            'depth': depth,
            'robot_state': robot_state,
        }
    
    def step(self, action: np.ndarray) -> Tuple[Dict, float, bool, bool, Dict]:
        """
        执行动作
        
        Args:
            action: 7维动作向量
                   [dx, dy, dz, gripper, wrist_rot, ...]
        
        Returns:
            observation: 下一时刻观测
            reward: 奖励（简化：任务完成才给奖励）
            terminated: 是否结束（任务链完成或失败）
            truncated: 是否截断（达到最大步数）
            info: 附加信息
        """
        # 解析动作
        delta_pos = action[:3] * 0.1  # 缩放位移
        gripper_action = action[3]
        
        # 更新夹爪位置
        self.gripper_pos = self.gripper_pos + delta_pos
        self.gripper_pos = np.clip(self.gripper_pos, -0.3, 0.3)
        
        # 更新夹爪开合
        self.gripper_open = gripper_action > 0.5
        
        # 更新关节角度（简化）
        self.joint_angles = self.joint_angles + action[4:11] * 0.01
        
        # 检查当前子任务是否完成
        current_task = self.current_task_chain['subtasks'][self.current_subtask_idx]
        task_done = self._check_subtask_completion(current_task)
        
        if task_done and not self.subtask_completed[self.current_subtask_idx]:
            self.subtask_completed[self.current_subtask_idx] = True
            self.current_subtask_idx += 1
        
        # 检查是否完成整个任务链
        all_done = all(self.subtask_completed)
        
        # 计算奖励
        completed_steps = sum(self.subtask_completed)
        reward = completed_steps * 1.0  # 每完成一步给 1.0 奖励
        
        terminated = all_done
        truncated = (completed_steps == 0 and np.random.rand() < 0.01)  # 模拟随机失败
        
        info = {
            'subtask_completed': self.subtask_completed.copy(),
            'completed_steps': completed_steps,
            'total_steps': len(self.current_task_chain['subtasks']),
            'current_subtask': self.current_subtask_idx
        }
        
        return self._get_observation(), reward, terminated, truncated, info
    
    def _check_subtask_completion(self, subtask: Dict) -> bool:
        """
        检查子任务是否完成
        
        Args:
            subtask: 子任务字典
        
        Returns:
            True if completed, False otherwise
        """
        import numpy as np
        
        stype = subtask['type']
        
        if stype == 'pick':
            target_pos = self.objects[subtask['target']]['position']
            dist = np.linalg.norm(self.gripper_pos[:2] - target_pos[:2])
            return (dist < 0.08 and not self.gripper_open)
        
        elif stype == 'place':
            if subtask['goal'] == 'left_drawer':
                drawer_open = self.objects['left_drawer']['open']
                target_pos = self.objects[subtask['target']]['position']
                in_drawer = abs(target_pos[0]) < 0.1 and abs(target_pos[1] - (-0.15)) < 0.05
                return drawer_open and in_drawer
            return False
        
        elif stype == 'push':
            target_pos = subtask['goal_position']
            obj_pos = self.objects[subtask['target']]['position']
            dist = np.linalg.norm(obj_pos - target_pos)
            return dist < 0.05
        
        elif stype == 'open_drawer':
            return self.objects[subtask['target']]['open']
        
        elif stype == 'close_drawer':
            return not self.objects[subtask['target']]['open']
        
        return False


# ============ 2. 语言条件策略（简化版）===========

class LanguageConditionedPolicy(nn.Module):
    """
    语言条件化策略网络（简化版）
    
    输入：视觉观测 + 语言指令
    输出：动作
    """
    
    def __init__(self, action_dim=7, hidden_dim=256):
        super().__init__()
        
        # 视觉编码器（简化 CNN）
        self.visual_encoder = nn.Sequential(
            nn.Conv2d(3, 32, 3, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1), nn.ReLU(),
            nn.AdaptiveAvgPool2d((7, 7)),
            nn.Flatten(),
            nn.Linear(128 * 7 * 7, hidden_dim)
        )
        
        # 语言编码器（简化：直接投影到隐藏维度）
        self.language_encoder = nn.Sequential(
            nn.Linear(512, hidden_dim),  # 假设输入是预计算的语言嵌入
            nn.ReLU()
        )
        
        # 融合 + 策略头
        self.fusion = nn.Linear(hidden_dim * 2, hidden_dim)
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Tanh()  # 动作归一化到 [-1, 1]
        )
    
    def forward(self, rgb, language_embedding):
        """
        前向传播
        
        Args:
            rgb: (batch, 3, H, W) RGB 图像
            language_embedding: (batch, lang_dim) 语言嵌入
        
        Returns:
            action: (batch, action_dim) 动作
        """
        visual_feat = self.visual_encoder(rgb)
        lang_feat = self.language_encoder(language_embedding)
        
        # 拼接融合
        combined = torch.cat([visual_feat, lang_feat], dim=-1)
        fused = torch.relu(self.fusion(combined))
        
        action = self.policy_head(fused)
        return action
    
    @torch.no_grad()
    def predict(self, rgb, language_embedding):
        """推理时的动作预测"""
        return self.forward(rgb, language_embedding)


# ============ 3. 长程任务链评估主函数 ============

def evaluate_long_horizon_tasks(
    policy: LanguageConditionedPolicy,
    env: CALVINSimulator,
    difficulty: str = 'ABC',
    num_episodes: int = 100
) -> Dict:
    """
    评估长程任务链执行能力
    
    Args:
        policy: 待评测的语言条件策略
        env: CALVIN 仿真环境
        difficulty: 评测难度级别
        num_episodes: 每个任务链评测次数
    
    Returns:
        evaluation_results: 包含各项指标的评测结果
    """
    # 筛选对应难度的任务链
    task_chains = [tc for tc in env.task_chains if tc['difficulty'] in difficulty]
    
    all_results = []
    
    print(f"\n{'='*60}")
    print(f"开始 CALVIN 长程任务链评测（难度: {difficulty}）")
    print(f"任务链数量: {len(task_chains)}, 每链评测 {num_episodes} 次")
    print(f"{'='*60}\n")
    
    for task_chain in task_chains:
        chain_id = task_chain['id']
        instruction = task_chain['instruction']
        n_subtasks = len(task_chain['subtasks'])
        
        chain_results = {
            'chain_id': chain_id,
            'n_subtasks': n_subtasks,
            'episodes': []
        }
        
        for episode in range(num_episodes):
            # 重置环境（指定任务链）
            obs, info = env.reset(task_chain_id=chain_id)
            
            completed_steps = 0
            episode_reward = 0.0
            
            for step in range(env.max_steps):
                # 模拟语言嵌入（实际用 CLIP 等模型计算）
                lang_embedding = torch.randn(1, 512)
                
                # RGB 图像
                rgb_tensor = torch.FloatTensor(obs['rgb']).permute(2, 0, 1).unsqueeze(0) / 255.0
                
                # 策略推理
                action = policy.predict(rgb_tensor, lang_embedding)
                action_np = action.squeeze(0).cpu().numpy()
                
                # 环境交互
                obs, reward, terminated, truncated, info = env.step(action_np)
                episode_reward += reward
                completed_steps = info['completed_steps']
                
                if terminated or truncated:
                    break
            
            chain_results['episodes'].append({
                'episode': episode,
                'completed_steps': completed_steps,
                'total_steps': n_subtasks,
                'success': completed_steps == n_subtasks,
                'reward': episode_reward
            })
        
        # 汇总该任务链的结果
        episodes = chain_results['episodes']
        sr = np.mean([ep['success'] for ep in episodes])
        acs = np.mean([ep['completed_steps'] for ep in episodes])
        avg_reward = np.mean([ep['reward'] for ep in episodes])
        
        print(f"[{chain_id}] {n_subtasks}步链 | "
              f"SR: {sr:.2%} | ACS: {acs:.2f} | Avg Reward: {avg_reward:.2f}")
        
        all_results.append({
            'chain_id': chain_id,
            'difficulty': task_chain['difficulty'],
            'n_subtasks': n_subtasks,
            'success_rate': sr,
            'average_completion_steps': acs,
            'average_reward': avg_reward,
        })
    
    # 汇总整体结果
    overall_sr = np.mean([r['success_rate'] for r in all_results])
    overall_acs = np.mean([r['average_completion_steps'] for r in all_results])
    
    print(f"\n{'='*60}")
    print(f"整体结果：SR = {overall_sr:.2%} | ACS = {overall_acs:.2f}")
    print(f"{'='*60}\n")
    
    return {
        'per_chain_results': all_results,
        'overall_sr': overall_sr,
        'overall_acs': overall_acs,
        'num_chains': len(all_results),
        'num_episodes_per_chain': num_episodes
    }


# ============ 4. 主程序入口 ============

def main():
    """
    主程序：加载环境，运行评估，输出结果
    """
    print("=" * 60)
    print("CALVIN 长程任务链评估")
    print("=" * 60)
    
    # 1. 初始化仿真环境
    print("\n[1/4] 初始化 CALVIN 仿真环境...")
    env = CALVINSimulator(task_difficulty='ABCD')
    print(f"     已加载 {len(env.task_chains)} 条任务链")
    
    # 2. 初始化策略网络
    print("\n[2/4] 初始化语言条件策略...")
    policy = LanguageConditionedPolicy(action_dim=7, hidden_dim=256)
    print(f"     模型参数量: {sum(p.numel() for p in policy.parameters()):,}")
    
    # 3. 评估 ABC 难度（内插语言）
    print("\n[3/4] 评测 ABC 难度（语言内插）...")
    abc_results = evaluate_long_horizon_tasks(
        policy=policy,
        env=env,
        difficulty='ABC',
        num_episodes=50
    )
    
    # 4. 评估 D 难度（零样本泛化）
    print("\n[4/4] 评测 D 难度（零样本泛化）...")
    d_results = evaluate_long_horizon_tasks(
        policy=policy,
        env=env,
        difficulty='D',
        num_episodes=50
    )
    
    # 5. 汇总对比
    print("\n" + "=" * 60)
    print("评测结果汇总")
    print("=" * 60)
    print(f"{'难度':<10} {'整链成功率 SR':<20} {'平均完成步数 ACS':<20}")
    print("-" * 60)
    print(f"{'ABC (内插)':<10} {abc_results['overall_sr']:<20.2%} {abc_results['overall_acs']:<20.2f}")
    print(f"{'D (零样本)':<10} {d_results['overall_sr']:<20.2%} {d_results['overall_acs']:<20.2f}")
    print("=" * 60)
    
    return abc_results, d_results


if __name__ == '__main__':
    abc_results, d_results = main()

---

## 6. 练习题

### 选择题

**1. CALVIN 的 ABCD 难度体系中，难度 D 主要评估什么能力？**

A. 单一动作的语言理解准确性

B. 零样本语言泛化能力

C. 动作精度和抓取成功率

D. 多任务联合训练效果

---

**2. CALVIN 的 ABCD 四级难度中，哪一级专门用于评估**零样本语言泛化**？**

A. 难度 A

B. 难度 B

C. 难度 C

D. 难度 D

---

**3. 在 CALVIN 长程任务链中，以下哪种依赖关系意味着"必须先完成后一个任务才能执行当前任务"？**

A. 时序依赖

B. 物体依赖

C. 空间依赖

D. 状态依赖

---

**4. CAPS（Conditional Action Policies）的核心思想是什么？**

A. 使用强化学习探索最优动作序列

B. 将语言指令编码为条件向量，与视觉特征拼接后输入统一策略网络

C. 对每个任务训练独立的策略网络

D. 使用预训练的 CLIP 直接生成动作

---

**5. CALVIN 中 "Chain Success Rate"（CSR_k）的定义是？**

A. 连续 $k$ 个子任务都能完成的概率

B. 整条任务链至少有 $k$ 个子任务完成的概率

C. $k$ 个随机选择的任务步骤完成的比例

D. 长度为 $k$ 的任务链占总任务链的比例

---

### 简答题

**6. 解释 CALVIN ABCD 四级难度体系的设计理念。每级难度分别对应什么研究问题？**

---

**7. 为什么 CALVIN 需要设计"长程任务链"评测，而不是像 RLBench 那样评测单一任务？这种设计对评估 VLA 模型的哪些能力特别重要？**

---

**8. CAPS 和 Language Table 在设计目标上有什么区别？各自更适合研究哪些问题？**

---

**9. CALVIN 的语言泛化评估分为词汇泛化、句式泛化和组合泛化三个层次。请解释这三个层次的含义，并说明为什么组合泛化是难度最高的。**

---

**10. 在 CALVIN 长程任务链评测中，假设某策略的 $\text{ACS}=2.8$，而任务链平均长度为 4 步。请分析这个策略的表现意味着什么？它的主要失败模式可能是什么？**

---

## 7. 参考答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | 难度 D 专门用于评估零样本语言泛化，即模型对训练时完全未见过的新语言指令的泛化能力。 |
| 2 | **D** | 难度 D（Zero-Shot Language Generalization）是 CALVIN 中最难的一级，评测完全未见过的语言指令。 |
| 3 | **A** | 时序依赖（Temporal Dependency）定义了任务之间的先后执行顺序，必须满足先后约束。 |
| 4 | **B** | CAPS 的核心创新是将语言指令编码为独立条件向量，与视觉特征拼接后输入统一的多任务策略网络。 |
| 5 | **A** | $\text{CSR}_k$ 定义为连续 $k$ 个子任务都能完成的概率，是长程任务链评测的核心指标之一。 |

---

### 简答题答案

**6. CALVIN ABCD 四级难度体系的设计理念**

CALVIN 的 ABCD 难度体系采用**渐进式增加难度**的设计理念，从语言理解到零样本泛化，逐级提升评测难度：

| 难度等级 | 评测目标 | 对应研究问题 |
|---------|---------|------------|
| **A（单步语言理解）** | 验证语言→动作映射的基本能力 | 基础语言条件化操控、指令解析 |
| **B（短链执行）** | 验证两步任务链的时序衔接 | 多步操作协调、动作序列规划 |
| **C（长链+干扰）** | 验证 4~6 步长链 + 干扰条件下的执行 | 长时序记忆、抗干扰能力、状态维护 |
| **D（零样本泛化）** | 验证对全新语言指令的泛化 | 语言泛化、组合泛化、语义理解深度 |

**设计理念**：每一级难度都对应一个具体的研究问题，难度递增确保评测能逐步揭示模型的不足之处，而非仅得到"成功率 0"或"成功率 100"的二元结果。

---

**7. 长程任务链评测的必要性**

CALVIN 设计长程任务链评测的核心原因：**真实人类指令是复合的、长时序的**。

| 维度 | RLBench（单步） | CALVIN（长程链） |
|------|-----------------|-----------------|
| **任务长度** | 1 步 | 2~6 步 |
| **评测重点** | 动作执行精度 | 语言理解 + 长时序规划 + 动作执行 |
| **时序依赖** | 无 | 有（顺序/物体/状态依赖） |
| **典型失败模式** | 抓取失败 | 第 2 步之后动作混乱 |

长程任务链评测对 VLA 模型以下能力特别重要：

1. **语言理解深度**：能否理解复合指令中的多个子任务描述
2. **长时序规划**：能否规划并执行正确的子任务执行顺序
3. **上下文记忆**：能否在多步执行中维护场景状态（物体位置、抽屉开闭等）
4. **抗干扰能力**：能否在存在干扰指令或干扰物体时仍正确执行
5. **错误恢复**：某一步失败后能否继续尝试或调整

---

**8. CAPS vs Language Table 的设计目标区别**

| 维度 | CAPS | Language Table |
|------|------|---------------|
| **研究重点** | 长程任务规划 + 语言泛化 | 语言-动作对齐（轻量级） |
| **场景复杂度** | 3D PyBullet，Franka 机械臂 | 2D 俯视桌面，推块操作 |
| **任务链长** | 2~6 步 | 1~2 步 |
| **语言复杂度** | 复合自然语言 | 简单指令 |
| **数据规模** | ~1M 演示 | ~200K 演示 |
| **核心贡献** | ABCD 难度体系、零样本评测 | 语言-动作对齐基线 |

**各自适用的研究问题**：

- **CAPS 更适合**：研究长程规划、语言泛化、多任务统一策略
- **Language Table 更适合**：研究语言-动作对齐的表示学习、快速微调、数据效率

---

**9. 语言泛化三个层次详解**

| 层次 | 含义 | 示例 | 难度 |
|------|------|------|------|
| **词汇泛化** | 同一物体/动作用不同词汇表达 | "red block" → "crimson cube" | 中等 |
| **句式泛化** | 相同语义用不同句式表达 | "pick up" → "grasp" / "get" | 中等 |
| **组合泛化** | 训练时各子任务分别见过，但此组合方式全新 | 各单步见过，但"先A后B再C"组合未见 | **最高** |

**组合泛化是最难的原因**：

1. **需要语义理解而非记忆**：词汇泛化和句式泛化可以通过同义词词典或句式模板解决；组合泛化需要真正理解每个子任务的语义才能正确组合
2. **组合空间指数增长**：$n$ 个子任务的组合数为 $2^n$，远超训练见过的组合
3. **需要泛化而非插值**：模型必须在见过的子任务之间进行**组合外推**，而非简单的插值
4. **长程依赖的叠加**：组合泛化的指令往往也是长链（4+ 步），进一步增加了难度

---

**10. $\text{ACS}=2.8$ 的策略分析**

$\text{ACS}=2.8$ 意味着在平均长度为 4 步的任务链上，该策略平均能完成 2.8 步。

**表现解读**：

| 指标 | 数值 | 含义 |
|------|------|------|
| 整链完成率 | 假设约 15%~25% | 大部分任务链未能完整完成 |
| $\text{ACS}$ | 2.8 / 4.0 = **70%** 完成率 | 平均能完成 70% 的步骤 |
| 失败位置 | 大多在第 3、4 步 | 长程步骤执行困难 |

**主要失败模式分析**：

```
任务链完成情况分布（假设100次评测）：
  完成 4 步（完整）：约 15 次
  完成 3 步：约 40 次  ← 主要失败区
  完成 2 步：约 30 次
  完成 1 步：约 10 次
  完成 0 步：约 5 次
  
失败原因推断：
  - 第 3、4 步的失败可能是：
    ① 前期执行中引入误差累积（定位偏差）
    ② 场景状态被破坏（前序操作影响后续）
    ③ 长程指令理解不准确（遗忘早期指令细节）
    ④ 夹爪/物体状态不一致（物体掉落后无法恢复）
```

**改进方向**：

1. **增加步骤判别器**：识别当前执行到哪一步（子任务边界检测）
2. **状态估计网络**：显式估计场景状态（抽屉开闭、物体位置）
3. **层级规划**：将长链分解为"子目标序列"，逐个子目标执行
4. **错误恢复机制**：检测失败并尝试重新执行当前子任务

---

*本课程完结。下一节：18-5 Benchmark 项目实战*
