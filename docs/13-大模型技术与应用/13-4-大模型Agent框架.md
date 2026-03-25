# 13-4 大模型Agent框架

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 13-4 |
| 课程名称 | 大模型Agent框架 |
| 所属模块 | 13-大模型技术与应用 |
| 难度等级 | ⭐⭐⭐⭐⭐ |
| 预计学时 | 5小时 |
| 前置知识 | Python基础、大模型API调用、LangChain基础、Prompt Engineering |

---

## 目录

1. [LLM Agent 概述](#1-llm-agent-概述)
2. [主流 Agent 框架](#2-主流-agent-框架)
3. [Agent 核心组件](#3-agent-核心组件)
4. [具身智能 Agent](#4-具身智能-agent)
5. [代码实战](#5-代码实战)
6. [练习题](#6-练习题)
7. [参考答案](#7-参考答案)

---

## 1. LLM Agent 概述

### 1.1 什么是 LLM Agent

**LLM Agent（基于大语言模型的智能体）** 是一种以大语言模型为核心控制器，能够自主感知环境、进行决策、调用工具、执行动作并根据反馈持续优化的智能系统。与传统程序不同，LLM Agent 不是预先编写好的固定流程，而是由大模型根据当前情境动态决定行为。

传统软件 vs LLM Agent 的核心区别：

| 维度 | 传统软件 | LLM Agent |
|------|----------|-----------|
| **控制流** | 开发者预设 | 模型动态决定 |
| **工具调用** | 硬编码 | 灵活选择 |
| **错误恢复** | 人工处理 | 自我反思修正 |
| **适应新任务** | 需修改代码 | 仅需调整提示词 |
| **推理过程** | 黑盒逻辑 | 可观察的思考链 |

### 1.2 Agent 的核心公式

Agent 的核心可以概括为以下公式：

$$
\text{Agent} = \text{LLM} + \text{Tools} + \text{Memory} + \text{Planning}
$$

| 组件 | 英文名 | 作用 | 类比 |
|------|--------|------|------|
| **大模型** | LLM | 推理、决策、生成 | Agent 的大脑 |
| **工具** | Tools | 与外部世界交互 | Agent 的四肢 |
| **记忆** | Memory | 存储和检索信息 | Agent 的知识库 |
| **规划** | Planning | 分解任务、设计策略 | Agent 的指挥官 |

### 1.3 两大核心范式

#### ReAct 范式（推理+行动同步）

**ReAct（Reasoning + Acting）** 的核心是"边想边做"——在推理过程中同步执行行动，通过行动结果反哺推理，形成紧密的思考-行动-观察闭环。

```
用户输入
    │
    ▼
┌───────────────────────────────────────┐
│          Thought：分析当前状态         │
│    "我需要先查询天气，再决定是否出门"   │
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│          Action：执行工具调用          │
│      search_weather(location="北京")  │
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│        Observation：接收行动结果        │
│        "北京：晴，25℃，适合出门"        │
└───────────────────────────────────────┘
    │
    ▼（循环直到任务完成）
    │
    ▼
最终答案
```

**ReAct 的优势**：可解释性强，每一步都有思考记录；能够根据观察结果动态调整策略。

**ReAct 的劣势**：循环次数增多时效率下降；过多中间步骤可能累积误差。

#### Plan-and-Execute 范式（先规划后执行）

**Plan-and-Execute（计划-执行分离）** 的核心是"谋定而后动"——先由规划器生成完整的任务计划，再由执行器按顺序执行。

```
用户输入："帮我泡一杯咖啡"
    │
    ▼
┌───────────────────────────────────────┐
│       Planner：生成任务计划            │
│  1. 烧开水                            │
│  2. 取咖啡粉                          │
│  3. 将热水倒入杯中                    │
│  4. 搅拌均匀                          │
└───────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────┐
│       Executor：按计划顺序执行         │
│  Step 1: boil_water() → 成功 ✓       │
│  Step 2: get_coffee_powder() → 成功 ✓│
│  Step 3: pour_water(cup) → 成功 ✓   │
│  Step 4: stir() → 成功 ✓             │
└───────────────────────────────────────┘
    │
    ▼
任务完成
```

**Plan-and-Execute 的优势**：规划全局可见，便于人工审查和调整；适合长周期任务。

**Plan-and-Execute 的劣势**：执行过程中无法根据意外情况动态调整计划（除非引入自我修正机制）。

#### 两种范式的对比

| 特性 | ReAct | Plan-and-Execute |
|------|-------|------------------|
| **执行顺序** | 思考与行动交织 | 先规划后执行 |
| **灵活性** | 高（可实时调整） | 低（按计划执行） |
| **可解释性** | 每步可见 | 计划层面可见 |
| **适合场景** | 探索性任务 | 流程固定任务 |
| **通信开销** | 低 | 高（Planner + Executor） |
| **代表性框架** | LangChain Agent | BabyAGI、MetaGPT |

---

## 2. 主流 Agent 框架

### 2.1 LangChain Agents

**LangChain** 是目前最成熟的 LLM 应用开发框架，提供了完整的 Agent 支持体系。

| 模块 | 功能 |
|------|------|
| **LCEL** | LangChain Expression Language，链式调用语法 |
| **AgentExecutor** | Agent 执行引擎，管理循环与终止 |
| **Tools** | 工具定义与注册 |
| **Memory** | 对话历史与记忆管理 |
| **Callbacks** | 事件回调与日志 |

LangChain 支持多种 Agent 类型：

| Agent 类型 | 说明 | 适用场景 |
|------------|------|----------|
| **zero-shot-react-description** | 零样本 ReAct Agent，通过工具描述选择工具 | 通用场景 |
| **conversational-react-description** | 对话式 ReAct Agent，保持上下文 | 对话系统 |
| **react-docstore** | 带文档存储的 ReAct Agent | 知识库问答 |
| **self-ask-with-search** | 自我追问 Agent | 多跳推理 |

### 2.2 LlamaIndex Agent

**LlamaIndex** 原名 GPT Index，专注于知识检索增强，其 Agent 模块建立在 LangChain 之上，针对知识密集型任务做了深度优化。

| 特性 | 说明 |
|------|------|
| **Query Engine Agent** | 基于知识库的问答 Agent |
| **SubQuestion Agent** | 将复杂问题分解为多个子问题分别检索 |
| **Router Agent** | 根据问题类型选择不同的 Query Engine |
| **Data Agent** | 对结构化/非结构化数据进行 Tool Use |

### 2.3 AutoGPT / BabyAGI

| 框架 | 特点 | 定位 |
|------|------|------|
| **AutoGPT** | 自主任务分解与执行，全自动循环 | 实验性、自主代理标杆 |
| **BabyAGI** | 精简的任务管理 + 向量存储，Plan-and-Execute | 轻量级任务自动化 |

**AutoGPT** 的核心流程：
```
目标设定 → 任务分解 → 自动执行 → 结果评估 → 自我批评 → 新任务生成 → 循环
```

**BabyAGI** 的核心流程：
```
用户输入 → 任务创建 → 任务优先级排序 → 任务执行 → 结果存储 → 生成新任务 → 循环
```

### 2.4 MetaGPT（多Agent协作）

**MetaGPT** 是复旦大学提出的多 Agent 协作框架，创新性地将软件工程方法论引入 Agent 协作。

MetaGPT 的核心设计：
- **Role（角色）**：每个 Agent 有明确的角色定义（工程师、产品经理、架构师等）
- **SOP（标准操作流程）**：每个角色有标准化的操作流程
- **消息队列**：Agent 之间通过结构化消息通信
- **协作约束**：通过角色约束避免 Agent 行为混乱

```python
# MetaGPT 简化架构示意
roles = [
    Role(name="产品经理", goal="撰写需求文档", context="..."),
    Role(name="架构师", goal="设计系统架构", context="..."),
    Role(name="工程师", goal="编写代码", context="..."),
]
# Agent 间通过消息队列共享中间结果
```

### 2.5 CrewAI（多Agent编排）

**CrewAI** 是一个新兴的多 Agent 编排框架，以简洁的 API 和直观的任务分配机制著称。

| 概念 | 说明 |
|------|------|
| **Agent** | 独立的工作单元，有角色、目标和工具 |
| **Task** | 具体任务，描述期望输出 |
| **Crew** | Agent + Task 的组合，管理执行流程 |
| **Process** | 执行流程（Sequential / Hierarchical） |

```python
# CrewAI 核心概念代码示例
from crewai import Agent, Task, Crew

# 定义 Agent
researcher = Agent(
    role="研究员",
    goal="收集最新AI技术动态",
    backstory="你是一位资深AI研究员，擅长信息检索"
)

# 定义 Task
research_task = Task(description="搜索2024年最新的多模态模型进展", agent=researcher)

# 组建 Crew 并执行
crew = Crew(agents=[researcher], tasks=[research_task])
result = crew.kickoff()
```

### 2.6 主流框架对比

| 维度 | LangChain | LlamaIndex | AutoGPT | MetaGPT | CrewAI |
|------|-----------|------------|---------|---------|--------|
| **单Agent** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **多Agent** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **知识检索** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |
| **学习曲线** | 陡峭 | 中等 | 平缓 | 中等 | 平缓 |
| **生产可用性** | 高 | 高 | 中 | 中 | 中 |
| **具身智能** | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

---

## 3. Agent 核心组件

### 3.1 工具定义与调用（Tool Use）

#### 3.1.1 工具的定义方式

在 LangChain 中，工具通过 `@tool` 装饰器或继承 `BaseTool` 类来定义。

```python
from langchain_core.tools import tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# 方式一：使用 @tool 装饰器定义工具（最简洁）
@tool
def get_calculator(expression: str) -> str:
    """执行数学计算

    参数:
        expression: 数学表达式，例如 "2 + 3 * 5" 或 "sqrt(16)"

    返回:
        计算结果的字符串表示
    """
    try:
        # 使用 Python 内置 eval 进行安全计算（生产环境请用 ast 或专门计算库）
        result = eval(expression, {"__builtins__": {}, "sqrt": __import__("math").sqrt})
        return f"计算结果：{result}"
    except Exception as e:
        return f"计算错误：{e}"

# 方式二：使用 LangChain 内置工具
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
```

#### 3.1.2 工具绑定的核心逻辑

工具调用的核心流程：

```
用户问题
    │
    ▼
LLM 判断是否需要调用工具
    │
    ├── 不需要 → 直接生成文本回复
    │
    └── 需要 → 选择合适的工具并生成参数
                    │
                    ▼
            执行工具调用
                    │
                    ▼
            接收工具返回结果
                    │
                    ▼
        将结果加入上下文，循环直到完成
```

**工具调用的 Prompt 关键要素**：

| 要素 | 说明 |
|------|------|
| **工具描述（Description）** | 清晰描述工具功能，LLM 据此决定是否调用 |
| **参数模式（Schema）** | 定义参数类型和约束，LLM 据此生成参数 |
| **返回值说明** | 明确返回内容格式，便于 LLM 解析 |

#### 3.1.3 多个工具的选择策略

当存在多个可用工具时，LLM 需要根据任务判断选择哪个工具：

```python
# 工具选择示例
@tool
def search_news(topic: str) -> str:
    """搜索最新的新闻资讯

    参数:
        topic: 新闻主题关键词

    返回:
        最新新闻列表（标题+摘要）
    """
    # 模拟搜索逻辑
    return f"关于'{topic}'的最新新闻：1. xxx 2. yyy"

@tool
def get_weather(city: str) -> str:
    """查询城市天气

    参数:
        city: 城市名称，例如"北京"

    返回:
        天气情况描述
    """
    return f"{city}今天晴，气温22-28℃，适合出行"

@tool
def calculate(expression: str) -> str:
    """数学计算器

    参数:
        expression: 数学表达式，例如 "2**10"

    返回:
        计算结果
    """
    try:
        result = eval(expression)
        return str(result)
    except:
        return "计算错误"

# 工具列表 - LLM 会根据用户问题自动选择合适的工具
tools = [search_news, get_weather, calculate]
```

### 3.2 记忆系统（Memory）

Agent 的记忆系统分为三类：**短期记忆**、**长期记忆**、**混合记忆**。

#### 3.2.1 短期记忆

短期记忆存储当前会话内的对话历史，受限于上下文窗口大小。

```python
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.chat_models import init_chat_model

# 短期记忆：维护对话历史
chat_history = [
    SystemMessage(content="你是一个有帮助的机器人助手"),
    HumanMessage(content="北京今天的天气如何？"),
    AIMessage(content="北京今天晴，气温22-28℃。"),
    HumanMessage(content="那上海呢？"),
]
# 模型基于完整的对话历史（短期记忆）理解上下文
response = chat_model.invoke(chat_history)
```

#### 3.2.2 长期记忆

长期记忆通过外部向量存储实现，跨会话持久化保存重要信息。

```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.schema import Document

# 长期记忆：使用向量数据库存储
embedding_model = OpenAIEmbeddings()

# 创建一个向量存储作为长期记忆
vectorstore = Chroma(
    collection_name="agent_memory",
    embedding_function=embedding_model
)

# 向量数据库中添加记忆
documents = [
    Document(page_content="用户偏好使用中文交流", metadata={"type": "user_preference"}),
    Document(page_content="用户感兴趣的领域：机器人、计算机视觉、AI Agent", metadata={"type": "interest"}),
    Document(page_content="用户上次询问过强化学习的基本概念", metadata={"type": "topic_history"}),
]
vectorstore.add_documents(documents)

# 检索相关记忆
def retrieve_memory(query: str, top_k: int = 3) -> list[str]:
    """根据查询检索相关的长期记忆

    参数:
        query: 查询文本
        top_k: 返回最相关的 k 条记忆

    返回:
        记忆内容列表
    """
    docs = vectorstore.similarity_search(query, k=top_k)
    return [doc.page_content for doc in docs]

# 示例：检索用户偏好
user_prefs = retrieve_memory("用户喜欢什么语言？")
print(user_prefs)  # ['用户偏好使用中文交流']
```

#### 3.2.3 混合记忆系统

将短期记忆和长期记忆结合，构建完整的记忆架构：

```python
class HybridMemory:
    """混合记忆系统：整合短期记忆和长期记忆"""

    def __init__(self):
        # 短期记忆：对话历史
        self.short_term = []
        # 长期记忆：向量数据库
        self.long_term_vectorstore = vectorstore
        self.embedding_model = embedding_model

    def add_interaction(self, role: str, content: str):
        """添加一轮对话到短期记忆"""
        self.short_term.append({"role": role, "content": content})

    def get_context(self, current_query: str, top_k: int = 3) -> str:
        """获取完整上下文：短期记忆 + 相关长期记忆"""
        # 构建短期记忆字符串
        short_context = "\n".join(
            [f"{item['role']}: {item['content']}" for item in self.short_term[-5:]]
        )
        # 检索长期记忆
        long_memories = self.long_term_vectorstore.similarity_search(
            current_query, k=top_k
        )
        long_context = "\n".join([doc.page_content for doc in long_memories])

        return f"=== 短期记忆 ===\n{short_context}\n\n=== 长期记忆（相关）===\n{long_context}"

    def save_to_long_term(self, content: str, metadata: dict):
        """将重要信息从短期记忆存入长期记忆"""
        doc = Document(page_content=content, metadata=metadata)
        self.long_term_vectorstore.add_documents([doc])

# 使用混合记忆
memory = HybridMemory()
memory.add_interaction("user", "我想学习机器人编程")
memory.add_interaction("assistant", "推荐从ROS2开始学习")

# 获取完整上下文
context = memory.get_context("用户想学什么？")
print(context)
```

### 3.3 规划模块（Planning）

#### 3.3.1 任务分解（Task Decomposition）

将复杂任务分解为多个可管理的子任务：

```python
def task_decomposition(task: str, model) -> list[str]:
    """使用 LLM 进行任务分解

    参数:
        task: 原始任务描述
        model: LLM 模型实例

    返回:
        子任务列表
    """
    prompt = f"""将以下任务分解为3-7个具体可执行的子任务：

任务：{task}

请按顺序列出子任务，格式如下：
1. [子任务1描述]
2. [子任务2描述]
...
"""
    response = model.invoke([HumanMessage(content=prompt)])
    # 解析子任务列表
    lines = response.content.strip().split('\n')
    subtasks = [line.strip() for line in lines if line.strip()]
    return subtasks

# 示例
subtasks = task_decomposition("帮我准备一顿健康的晚餐", chat_model)
for i, s in enumerate(subtasks, 1):
    print(f"{i}. {s}")
```

#### 3.3.2 自我修正（Self-Correction）

Agent 在执行过程中根据反馈进行自我修正：

```python
class SelfCorrectingAgent:
    """具有自我修正能力的 Agent"""

    def __init__(self, llm, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries

    def execute_with_correction(self, task: str, tools: list) -> str:
        """带自我修正的任务执行"""
        for attempt in range(self.max_retries):
            # Step 1: 生成计划或行动
            plan = self.llm.invoke([
                HumanMessage(content=f"任务：{task}\n尝试次数：{attempt + 1}"),
                AIMessage(content=f"上一步结果或初始状态：")
            ])

            # 模拟执行和获取反馈
            # 实际场景中，这里会调用工具并获得观察结果
            result = f"执行结果（尝试 {attempt + 1}）"

            # Step 2: 评估结果
            evaluation = self.llm.invoke([
                HumanMessage(content=f"任务：{task}"),
                HumanMessage(content=f"执行结果：{result}"),
                HumanMessage(content="评估：任务是否成功完成？如果失败，说明原因并提出修正方案。"),
            ])

            # Step 3: 检查是否需要修正
            if "成功" in evaluation.content or "完成" in evaluation.content:
                return result

            # 需要修正，继续循环
            task = f"{task}（修正：{evaluation.content}）"

        return "达到最大重试次数，任务未能完成"
```

### 3.4 多轮对话管理

多轮对话管理协调 Agent 的持续交互：

```python
class ConversationManager:
    """多轮对话管理器"""

    def __init__(self, agent, max_turns: int = 20):
        self.agent = agent
        self.max_turns = max_turns
        self.conversation_history = []
        self.turn_count = 0

    def chat(self, user_input: str) -> str:
        """处理一轮对话

        参数:
            user_input: 用户输入

        返回:
            Agent 回复
        """
        # 添加用户消息
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        # 调用 Agent（包含完整历史）
        response = self.agent.invoke({
            "input": user_input,
            "chat_history": self.conversation_history[:-1]
        })

        # 添加 Agent 回复
        self.conversation_history.append({
            "role": "assistant",
            "content": response["output"]
        })

        self.turn_count += 1
        return response["output"]

    def should_continue(self) -> bool:
        """判断是否继续对话"""
        # 可自定义终止条件
        return self.turn_count < self.max_turns
```

---

## 4. 具身智能 Agent

### 4.1 机器人任务规划Agent

具身智能 Agent 的核心使命是使机器人能够理解高层任务指令，并自主规划执行序列。

```
用户指令："把桌上的杯子拿给我"
    │
    ▼
┌─────────────────────────────────────────────┐
│  感知层（Perception）                        │
│  - 视觉识别：检测桌面上的物体                 │
│  - 场景理解：理解物体空间位置关系              │
│  - 状态估计：机器人当前位置与姿态              │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  规划层（Planning）                          │
│  - 任务分解：移动 → 抓取 → 搬运 → 放置       │
│  - 运动规划：路径规划、避障                   │
│  - 动作序列生成                              │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  执行层（Execution）                         │
│  - 运动控制：驱动电机执行动作                 │
│  - 反馈控制：实时调整执行策略                  │
│  - 安全监控：碰撞检测、异常处理               │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│  观察层（Observation）                       │
│  - 执行结果反馈                              │
│  - 环境状态更新                              │
│  - 任务完成判定                              │
└─────────────────────────────────────────────┘
```

具身智能 Agent 的 Prompt 设计示例：

```
你是一个机器人控制 Agent，负责将自然语言指令转换为机器人动作序列。

可用工具：
- get_visual_scene(): 获取当前视觉场景描述
- get_robot_state(): 获取机器人当前位置和状态
- plan_path(start, goal): 规划从起点到终点的路径
- move_to(position): 控制机器人移动到指定位置
- grasp(object_id): 控制机械爪抓取指定物体
- release(): 释放机械爪
- check_object_position(object_id): 查询物体当前位置

执行流程：
1. 理解用户指令中的目标物体和位置
2. 感知当前场景，获取物体分布
3. 规划动作序列
4. 依次执行动作，每步观察结果
5. 任务完成后返回执行摘要
```

### 4.2 感知-决策-执行闭环

具身智能 Agent 通过持续闭环实现与环境的交互：

```python
class EmbodiedAgent:
    """具身智能 Agent：感知-决策-执行闭环"""

    def __init__(self, llm, robot_controller, perception_module):
        self.llm = llm                      # 大模型（决策大脑）
        self.robot = robot_controller        # 机器人控制器
        self.perception = perception_module  # 感知模块

    def run闭环(self, task: str, max_steps: int = 20):
        """执行具身任务的主循环

        参数:
            task: 自然语言任务描述
            max_steps: 最大执行步数，防止无限循环
        """
        print(f"🎯 任务：{task}")

        for step in range(max_steps):
            print(f"\n--- 步骤 {step + 1} ---")

            # Step 1: 感知（Perception）
            scene_info = self.perception.get_scene()
            robot_state = self.robot.get_state()
            print(f"👁️ 感知：{scene_info}")
            print(f"🤖 机器人状态：{robot_state}")

            # Step 2: 决策（Decision）
            decision_prompt = f"""当前状态：
- 场景：{scene_info}
- 机器人：{robot_state}
- 任务：{task}
- 当前步骤：{step + 1}/{max_steps}

请决定下一步动作（从以下选择或自行描述）：
可用动作：move_to, grasp, release, look_at, speak, stop

输出格式：
思考：[分析当前情况]
动作：[具体动作名称和参数]
"""
            decision = self.llm.invoke([HumanMessage(content=decision_prompt)])
            print(f"🧠 决策：{decision.content}")

            # Step 3: 执行（Execution）
            action, params = self.parse_action(decision.content)
            if action == "stop":
                print("✅ 任务完成")
                break

            result = self.robot.execute(action, params)
            print(f"⚙️ 执行结果：{result}")

            # Step 4: 检查完成状态
            if self.check_completion(task, scene_info):
                print("✅ 任务达成")
                break

        else:
            print("⚠️ 达到最大步数，任务未完成")

    def parse_action(self, decision_text: str) -> tuple:
        """从 LLM 输出中解析动作名称和参数"""
        # 简化解析逻辑，实际场景使用更robust的解析
        if "move_to" in decision_text:
            return "move_to", {"position": "target"}
        elif "grasp" in decision_text:
            return "grasp", {"object_id": "cup"}
        elif "release" in decision_text:
            return "release", {}
        elif "stop" in decision_text:
            return "stop", {}
        return "stop", {}
```

### 4.3 多机器人通信Agent

多机器人协作需要 Agent 之间的通信与协调：

```python
class MultiRobotAgent:
    """多机器人协调 Agent"""

    def __init__(self, llm, robots: dict):
        """
        参数:
            llm: 大模型实例
            robots: 机器人字典 {"robot_id": robot_controller}
        """
        self.llm = llm
        self.robots = robots
        self.shared_memory = []  # 共享通信内存

    def broadcast_message(self, sender: str, message: str):
        """广播消息到所有机器人"""
        self.shared_memory.append({"sender": sender, "message": message, "type": "broadcast"})
        print(f"📢 [{sender}] 广播：{message}")

    def send_direct_message(self, from_id: str, to_id: str, message: str):
        """向指定机器人发送消息"""
        self.shared_memory.append({
            "sender": from_id,
            "receiver": to_id,
            "message": message,
            "type": "direct"
        })
        print(f"📨 [{from_id}] → [{to_id}]：{message}")

    def coordinate_task(self, task: str):
        """协调多机器人完成复杂任务"""
        # 步骤1：任务分解
        subtasks = self.llm.invoke([
            HumanMessage(content=f"任务：{task}\n可用机器人：{list(self.robots.keys())}\n将任务分解并分配给合适的机器人。")
        ])
        print(f"📋 任务分解：{subtasks.content}")

        # 步骤2：并发执行（模拟）
        # 实际场景中，多个机器人可以真正并发执行
        print("\n🤝 多机器人协作执行中...")

        # 示例：robot_A 搬箱子，robot_B 开门
        self.broadcast_message("coordinator", f"开始执行：{task}")
        self.send_direct_message("coordinator", "robot_A", "请移动到货架前拿起箱子")
        self.send_direct_message("coordinator", "robot_B", "请移动到门口打开门")

        # 步骤3：等待完成信号
        print("\n⏳ 等待各机器人完成任务...")
```

---

## 5. 代码实战

### 5.1 LangChain Agent 工具调用实战

本节实现一个完整的 LangChain Agent，支持天气查询、计算器和新闻搜索三大工具。

```python
"""
LangChain Agent 工具调用实战
功能：实现一个多工具 Agent，能够回答天气、计算、新闻等问题
"""

# ============================================================
# 第一步：导入必要的库
# ============================================================
import os
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain.chat_models import init_chat_model
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

# ============================================================
# 第二步：设置 API Key（请替换为你的实际 Key）
# ============================================================
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"
# 本示例使用兼容接口，实际情况可替换为 OpenAI / DashSpring 等

# ============================================================
# 第三步：定义工具函数
# ============================================================

@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气信息

    参数:
        city: 城市名称，例如"北京"、"上海"

    返回:
        天气情况描述字符串
    """
    # 模拟天气数据（实际项目中应调用真实天气 API）
    weather_db = {
        "北京": "北京今天晴，气温15-25℃，空气质量良好，适合户外活动",
        "上海": "上海今天多云转阴，气温18-27℃，局部有小雨，记得带伞",
        "深圳": "深圳今天晴朗，气温22-30℃，阳光强烈，注意防晒",
        "成都": "成都今天阴天，气温14-22℃，空气质量中等",
    }
    return weather_db.get(city, f"抱歉，暂不支持查询{city}的天气")

@tool
def calculate(expression: str) -> str:
    """数学计算器，执行各类数学运算

    参数:
        expression: 数学表达式，支持加减乘除和常见函数
                    例如："2 + 3"、"sqrt(16)"、"10 ** 2"

    返回:
        计算结果的字符串表示
    """
    try:
        import math
        # 使用安全的方式执行计算（生产环境推荐用 ast 模块解析）
        allowed_names = {"sqrt": math.sqrt, "pi": math.pi, "e": math.e,
                        "sin": math.sin, "cos": math.cos, "tan": math.tan,
                        "log": math.log, "log10": math.log10}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}。请检查表达式是否合法。"

@tool
def search_news(topic: str) -> str:
    """搜索指定主题的最新新闻

    参数:
        topic: 新闻主题或关键词，例如"人工智能"、"机器人"

    返回:
        最新新闻列表的字符串描述
    """
    # 模拟新闻数据（实际项目中应调用真实新闻 API）
    news_db = {
        "人工智能": "1. OpenAI 发布 GPT-5，性能大幅提升  2. Google DeepMind 提出新架构  3. 我国 AI 产业规模突破万亿",
        "机器人": "1. 波士顿动力展示新型 Atlas 机器人  2. 特斯拉 Optimus 即将量产  3. 我国机器人装机量全球第一",
        "具身智能": "1. VLA 大模型成为研究热点  2. 机器人控制迎来新范式  3. CALVIN 基准刷新纪录",
    }
    return news_db.get(topic, f"暂无{topic}相关的最新新闻")

# 工具列表
tools = [get_weather, calculate, search_news]
print(f"✅ 已注册 {len(tools)} 个工具：{[t.name for t in tools]}")

# ============================================================
# 第四步：初始化大模型
# ============================================================
# 使用兼容接口初始化模型（实际使用时替换为真实 API）
llm = init_chat_model(
    model="groq:llama-3.3-70b",
    temperature=0,
)

# ============================================================
# 第五步：创建 ReAct Agent
# ============================================================
# 从 LangChain Hub 拉取 ReAct 风格的 Prompt 模板
prompt = hub.pull("hwchase17/react")

# 创建 Agent
agent = create_react_agent(llm, tools, prompt)

# 创建 Agent 执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,       # 打印完整思考过程
    max_iterations=10,  # 最多循环 10 次，防止无限循环
    handle_parsing_errors=True,  # 自动处理解析错误
)

# ============================================================
# 第六步：测试 Agent
# ============================================================

print("\n" + "=" * 60)
print("🤖 Agent 测试开始")
print("=" * 60)

# 测试问题列表
test_questions = [
    "北京今天的天气怎么样？",
    "帮我计算一下：sqrt(144) + 10 ** 2",
    "最近有什么人工智能方面的新闻？",
    "我想了解机器人领域的最新进展",
    "如果上海气温是20度，而北京比上海低5度，那北京是多少度？",
]

for q in test_questions:
    print(f"\n📌 用户问题：{q}")
    print("-" * 40)
    result = agent_executor.invoke({"input": q})
    print(f"✅ Agent 最终回复：{result['output']}")
    print("=" * 60)
```

### 5.2 ReAct 策略手动实现

本节手动实现一个完整的 ReAct 循环，不依赖 LangChain Agent框架，以便深入理解 ReAct 的内部机制。

```python
"""
ReAct 策略手动实现
不依赖 LangChain Agent，从零实现 Thought-Action-Observation 循环
"""

import json
from typing import Literal

# ============================================================
# 第一步：定义工具（与 5.1 节类似）
# ============================================================

def get_weather(city: str) -> str:
    """查询天气"""
    weather_db = {
        "北京": "晴，15-25℃",
        "上海": "多云，18-27℃",
        "深圳": "晴，22-30℃",
    }
    return weather_db.get(city, f"不支持查询{city}")

def calculate(expression: str) -> str:
    """数学计算"""
    try:
        import math
        allowed = {"sqrt": math.sqrt, "pi": math.pi, "e": math.e}
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"错误: {e}"

def search_wiki(query: str) -> str:
    """模拟维基百科搜索"""
    kb = {
        "人工智能": "人工智能（AI）是计算机科学的一个分支，致力于开发能够模拟人类智能的系统。",
        "机器人": "机器人是一种自动化的机械装置，能够执行预设的任务或自主适应环境。",
        "大语言模型": "大语言模型（LLM）是基于深度学习的大型语言模型，能够理解和生成自然语言。",
    }
    for key, val in kb.items():
        if key in query:
            return val
    return f"未找到与'{query}'相关的百科条目"

# 工具注册表（模拟 LangChain 的工具注册机制）
TOOL_REGISTRY = {
    "get_weather": get_weather,
    "calculate": calculate,
    "search_wiki": search_wiki,
}

# 工具描述表（LLM 据此决定调用哪个工具）
TOOL_DESCRIPTIONS = """
你可以使用以下工具：

1. get_weather(city: str) -> str
   功能：查询指定城市的天气
   示例调用：get_weather(city="北京")

2. calculate(expression: str) -> str
   功能：执行数学计算
   示例调用：calculate(expression="2+3*5")

3. search_wiki(query: str) -> str
   功能：在百科数据库中搜索相关词条
   示例调用：search_wiki(query="人工智能")
"""

# ============================================================
# 第二步：定义 ReAct 循环核心逻辑
# ============================================================

def parse_llm_response(response: str) -> tuple:
    """解析 LLM 回复，提取 Thought、Action、Action Input

    简化实现：假设 LLM 按照以下格式回复：
    Thought: [思考内容]
    Action: [工具名称]
    Action Input: [参数]
    """
    thought = ""
    action = None
    action_input = ""

    lines = response.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line.startswith("Thought:"):
            thought = line[len("Thought:"):].strip()
        elif line.startswith("Action:"):
            action = line[len("Action:"):].strip()
        elif line.startswith("Action Input:"):
            action_input = line[len("Action Input:"):].strip()

    return thought, action, action_input

def execute_action(tool_name: str, tool_input: str) -> str:
    """执行工具调用并返回结果"""
    if tool_name not in TOOL_REGISTRY:
        return f"错误：未知工具 '{tool_name}'"
    try:
        # 简化处理：假设输入是直接的字符串参数
        result = TOOL_REGISTRY[tool_name](tool_input)
        return result
    except Exception as e:
        return f"工具执行错误：{e}"

def react_loop(question: str, llm, max_iterations: int = 8) -> str:
    """ReAct 主循环

    参数:
        question: 用户问题
        llm: 大模型实例（需支持 `.invoke()` 接口）
        max_iterations: 最大循环次数，防止无限循环

    返回:
        最终答案字符串
    """
    # 完整的 ReAct Prompt 模板
    react_prompt_template = """你是一个智能助手，通过思考和行动来回答问题。

{tool_descriptions}

请按以下格式回答：

问题：{question}
{history}
Thought: [你的思考，分析当前情况，决定是否需要调用工具]
Action: [工具名称，如果不需调用工具则写 "finish"]
Action Input: [工具参数，如果不调用工具则留空]
"""
    history = ""  # 思考历史

    for i in range(max_iterations):
        # 构建当前轮次的 Prompt
        prompt = react_prompt_template.format(
            tool_descriptions=TOOL_DESCRIPTIONS,
            question=question,
            history=history
        )

        # 调用 LLM 获取响应
        llm_response = llm.invoke([HumanMessage(content=prompt)])
        response_text = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

        print(f"\n【ReAct 第 {i+1} 轮】")
        print(f"LLM 回复：\n{response_text}")

        # 解析 LLM 回复
        thought, action, action_input = parse_llm_response(response_text)
        history += f"Thought: {thought}\nAction: {action}\nAction Input: {action_input}\n"

        # 如果是结束信号，提取最终答案
        if action == "finish" or action is None:
            # 尝试从回复中提取最终答案
            if "Final Answer:" in response_text:
                final = response_text.split("Final Answer:")[-1].strip()
            else:
                final = response_text.split("final")[-1].strip() if "final" in response_text.lower() else response_text
            return final

        # 执行工具调用
        observation = execute_action(action, action_input)
        print(f"执行结果：{observation}")
        history += f"Observation: {observation}\n\n"

    return "达到最大循环次数，未能得出答案"

# ============================================================
# 第三步：测试 ReAct 手动实现
# ============================================================
# 注意：由于没有真实 API key，以下代码在有 API 时可运行
# 使用方法：
#   from langchain.chat_models import init_chat_model
#   llm = init_chat_model("groq:llama-3.3-70b")
#   result = react_loop("北京天气怎么样？", llm)

print("✅ ReAct 手动实现完成")
print("\n核心流程：")
print("  1. 构建 ReAct Prompt（包含工具描述）")
print("  2. 调用 LLM 获取 Thought + Action")
print("  3. 解析 Action 并执行工具")
print("  4. 将执行结果作为 Observation 加入历史")
print("  5. 循环直到 LLM 返回 finish 或达到最大次数")

# ============================================================
# 第四步：关键概念总结
# ============================================================
print("\n" + "=" * 60)
print("📚 ReAct vs LangChain Agent 对比")
print("=" * 60)
print("""
| 维度     | 手动 ReAct 实现     | LangChain Agent         |
|----------|---------------------|-------------------------|
| 灵活性   | 高，可完全定制      | 中，需遵循框架规范      |
| 开发量   | 大，从零实现        | 小，框架提供基础设施    |
| 调试难度 | 低，流程透明        | 高，框架内部黑盒        |
| 适用场景 | 研究/教学/定制需求  | 生产环境快速开发        |
""")
```

### 5.3 构建具身智能任务执行Agent

本节实现一个面向机器人场景的具身智能 Agent，支持视觉感知、任务规划和动作执行。

```python
"""
具身智能任务执行 Agent
功能：接收高层自然语言指令，转换为机器人动作序列并执行
"""

from dataclasses import dataclass, field
from typing import Literal

# ============================================================
# 第一步：定义具身Agent的核心数据结构
# ============================================================

@dataclass
class ObjectInfo:
    """物体信息"""
    id: str
    name: str
    position: tuple  # (x, y, z) 坐标
    status: str      # "in_scene", "held", "placed"

@dataclass
class RobotState:
    """机器人状态"""
    position: tuple        # 机器人当前位置
    gripper_status: str    # "open", "closed", "empty"
    held_object: str       # 手上拿着的物体ID，无则为 None

@dataclass
class SceneState:
    """场景状态"""
    objects: list[ObjectInfo]  # 场景中的物体列表
    robot: RobotState          # 机器人状态

# ============================================================
# 第二步：定义动作执行函数
# ============================================================

class RobotSimulator:
    """机器人模拟器（实际项目中替换为真实机器人接口）"""

    def __init__(self):
        self.scene = SceneState(
            objects=[
                ObjectInfo(id="cup", name="杯子", position=(0.5, 0.0, 0.8), status="in_scene"),
                ObjectInfo(id="table", name="桌子", position=(1.0, 0.0, 0.0), status="in_scene"),
                ObjectInfo(id="target_zone", name="目标区", position=(-0.5, 0.5, 0.0), status="in_scene"),
            ],
            robot=RobotState(position=(0.0, 0.0, 0.0), gripper_status="open", held_object=None)
        )
        self.execution_log = []  # 动作执行日志

    def move_to(self, position: tuple) -> str:
        """移动机器人到指定位置

        参数:
            position: 目标位置元组 (x, y, z)

        返回:
            执行结果描述
        """
        self.robot.position = position
        log = f"🤖 移动到位置 {position}"
        self.execution_log.append(log)
        return log

    def grasp(self, object_id: str) -> str:
        """抓取指定物体

        参数:
            object_id: 物体ID

        返回:
            执行结果描述
        """
        if self.robot.held_object is not None:
            return f"⚠️ 手上已有物体 {self.robot.held_object}，请先放置"

        for obj in self.scene.objects:
            if obj.id == object_id:
                if self.robot.gripper_status != "open":
                    return "⚠️ 机械爪未打开，无法抓取"
                # 检查物体是否在可达范围内
                distance = sum((a - b) ** 2 for a, b in zip(self.robot.position, obj.position)) ** 0.5
                if distance > 0.5:
                    return f"⚠️ 物体距离太远（{distance:.2f}m），需要靠近后再抓取"
                self.robot.held_object = object_id
                self.robot.gripper_status = "closed"
                obj.status = "held"
                log = f"🤖 抓取物体 {obj.name} (ID: {object_id})"
                self.execution_log.append(log)
                return log
        return f"⚠️ 未找到物体 {object_id}"

    def release(self) -> str:
        """释放机械爪（放置物体）

        返回:
            执行结果描述
        """
        if self.robot.held_object is None:
            return "⚠️ 手上没有物体，无需释放"
        for obj in self.scene.objects:
            if obj.id == self.robot.held_object:
                obj.position = self.robot.position
                obj.status = "placed"
                log = f"🤖 在 {self.robot.position} 放置了物体 {obj.name}"
                self.execution_log.append(log)
                self.robot.held_object = None
                self.robot.gripper_status = "open"
                return log
        return "⚠️ 释放失败"

    def get_scene_description(self) -> str:
        """获取当前场景的自然语言描述"""
        parts = []
        parts.append(f"机器人当前位置：{self.robot.position}")
        parts.append(f"机械爪状态：{self.robot.gripper_status}" +
                     (f"，手持 {self.robot.held_object}" if self.robot.held_object else "，空"))
        parts.append("场景中的物体：")
        for obj in self.scene.objects:
            parts.append(f"  - {obj.name} 在 {obj.position}，状态：{obj.status}")
        return "\n".join(parts)

# ============================================================
# 第三步：定义具身智能Agent
# ============================================================

class EmbodiedTaskAgent:
    """具身智能任务执行 Agent

    接收高层自然语言指令，将其分解为可执行的机器人动作序列，
    并在模拟器中执行全部流程。
    """

    def __init__(self, llm, robot: RobotSimulator):
        self.llm = llm              # 大模型（决策大脑）
        self.robot = robot           # 机器人模拟器

    def decompose_task(self, task: str) -> list[str]:
        """使用 LLM 将高层任务分解为动作序列

        参数:
            task: 自然语言任务描述，例如"把杯子放到桌子左边"

        返回:
            动作描述列表
        """
        prompt = f"""你是一个机器人任务规划器。将以下任务分解为具体的机器人动作序列。

可用动作：
- move_to(position): 移动到指定位置，position 为 (x, y, z) 元组
- grasp(object_id): 抓取指定物体
- release(): 释放机械爪

当前场景信息：
{self.robot.get_scene_description()}

任务：{task}

请将任务分解为动作序列，格式为：
1. [动作描述：move_to/camera_look/grasp/release]
2. ...

只输出动作序列，不要解释。"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        text = response.content if hasattr(response, 'content') else str(response)

        # 解析动作序列（简化版）
        lines = text.strip().split('\n')
        actions = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                actions.append(line)
        return actions

    def execute_action_sequence(self, actions: list[str]) -> dict:
        """执行动作序列

        参数:
            actions: 动作描述列表

        返回:
            执行结果字典，包含 success（是否成功）和 log（执行日志）
        """
        results = []
        for action_desc in actions:
            print(f"⚙️ 执行：{action_desc}")

            # 简化解析：从动作描述中提取动作类型和参数
            action_lower = action_desc.lower()

            if "move_to" in action_lower or "移动" in action_lower:
                # 解析位置参数（简化：从描述中提取坐标）
                # 实际场景中应使用更 robust 的解析方式
                if "桌子" in action_desc:
                    result = self.robot.move_to((1.0, 0.0, 0.0))
                elif "杯子" in action_desc or "目标" in action_desc or "左边" in action_desc:
                    result = self.robot.move_to((0.5, 0.0, 0.8))
                else:
                    result = self.robot.move_to((0.0, 0.0, 0.0))
                results.append(result)

            elif "grasp" in action_lower or "抓取" in action_lower:
                result = self.robot.grasp("cup")
                results.append(result)

            elif "release" in action_lower or "放置" in action_lower or "释放" in action_lower:
                result = self.robot.release()
                results.append(result)

            else:
                results.append(f"⚠️ 无法解析动作：{action_desc}")

        return {"success": all("🤖" in r for r in results), "log": results}

    def run(self, task: str) -> str:
        """执行完整任务流程

        参数:
            task: 自然语言任务描述

        返回:
            任务执行报告
        """
        print(f"\n{'='*60}")
        print(f"🎯 接收任务：{task}")
        print(f"{'='*60}")
        print(f"\n📍 当前场景：\n{self.robot.get_scene_description()}")

        # Step 1: 任务分解
        print(f"\n🧠 步骤1：任务分解...")
        actions = self.decompose_task(task)
        print(f"分解为 {len(actions)} 个动作：")
        for a in actions:
            print(f"  - {a}")

        # Step 2: 执行动作序列
        print(f"\n⚙️ 步骤2：执行动作序列...")
        exec_result = self.execute_action_sequence(actions)

        # Step 3: 生成执行报告
        print(f"\n📊 步骤3：生成执行报告...")
        report = f"""
{'='*60}
📋 任务执行报告
{'='*60}
任务：{task}
状态：{'✅ 成功' if exec_result['success'] else '⚠️ 部分成功'}

执行日志：
{chr(10).join(exec_result['log'])}

最终场景状态：
{self.robot.get_scene_description()}
"""
        return report

# ============================================================
# 第四步：测试具身智能 Agent
# ============================================================
print("\n" + "=" * 60)
print("🤖 具身智能 Agent 测试")
print("=" * 60)

# 初始化（无真实 API 时可运行模拟）
robot_sim = RobotSimulator()
print(f"✅ 机器人模拟器初始化完成")
print(f"✅ 初始状态：{robot_sim.get_scene_description()}")

# 模拟执行一个完整任务
print("\n" + "-" * 40)
print("【模拟执行】任务：把杯子拿起来")
robot_sim.move_to((0.5, 0.0, 0.8))
robot_sim.grasp("cup")
print(robot_sim.get_scene_description())

print("\n" + "-" * 40)
print("【模拟执行】任务：把杯子放到目标区域")
robot_sim.move_to((-0.5, 0.5, 0.0))
robot_sim.release()
print(robot_sim.get_scene_description())

print("\n✅ 具身智能 Agent 模拟测试完成")
print("\n📌 说明：")
print("  - 当有真实 LLM API 时，EmbodiedTaskAgent.decompose_task()")
print("    会调用大模型进行任务分解，实现真正的智能规划")
print("  - RobotSimulator 可替换为 ROS 机器人接口，实现物理控制")
```

---

## 6. 练习题

### 6.1 选择题

**1. 关于 LLM Agent 的核心公式，以下哪个是正确的？**

A. Agent = LLM + API + Database + UI
B. Agent = LLM + Tools + Memory + Planning
C. Agent = LLM + VectorDB + Prompt + Chain
D. Agent = LLM + Fine-tuning + RAG + Tools

---

**2. ReAct 范式与 Plan-and-Execute 范式最大的区别是？**

A. ReAct 需要更多内存，Plan-and-Execute 需要更多工具
B. ReAct 是边推理边行动，Plan-and-Execute 是先规划后执行
C. ReAct 只能用于对话，Plan-and-Execute 只能用于机器人
D. ReAct 不需要 LLM，Plan-and-Execute 必须用 LLM

---

**3. 以下哪个不是 LangChain 支持的 Agent 类型？**

A. zero-shot-react-description
B. conversational-react-description
C. self-ask-with-search
D. transformer-react-agent

---

**4. 在具身智能 Agent 中，"感知-决策-执行闭环"的正确顺序是？**

A. 感知 → 规划 → 执行 → 观察 → 感知
B. 感知 → 决策 → 执行 → 观察 → 决策
C. 感知 → 决策 → 规划 → 执行 → 观察
D. 感知 → 执行 → 决策 → 规划 → 观察

---

**5. 短期记忆和长期记忆的主要区别在于？**

A. 短期记忆存储在 RAM，长期记忆存储在磁盘 —— 两者没有本质区别
B. 短期记忆用于当前会话，长期记忆通过向量数据库实现跨会话持久化
C. 短期记忆容量大，长期记忆容量小
D. 长期记忆比短期记忆更准确

---

### 6.2 简答题

**6. 请简述 ReAct 范式中 Thought-Action-Observation 三个环节各自的作用，并说明它们如何形成闭环。**

**7. 比较 LangChain Agents 和 CrewAI 在多 Agent 协作方面的设计理念差异，并说明各自的适用场景。**

**8. 在具身智能场景中，为什么需要"感知-决策-执行"闭环？与传统编程的"顺序执行"相比，它有什么优势？**

---

## 7. 参考答案

### 6.1 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **B** | Agent 的核心公式是 LLM（大脑）+ Tools（四肢）+ Memory（知识库）+ Planning（指挥官）。其他选项包含了不相关的组件。 |
| 2 | **B** | ReAct 的核心是推理与行动交织进行（边想边做）；Plan-and-Execute 则先由规划器生成完整计划，再由执行器按顺序执行（谋定后动）。 |
| 3 | **D** | LangChain 支持 zero-shot-react-description、conversational-react-description、self-ask-with-search 等 Agent 类型，"transformer-react-agent" 不是 LangChain 的合法 Agent 类型。 |
| 4 | **B** | 正确的闭环是：感知环境 → 基于感知做决策 → 执行动作 → 观察执行结果 → 根据观察更新决策（而非重新规划）。 |
| 5 | **B** | 短期记忆（对话历史）服务于当前会话，容量受限于上下文窗口；长期记忆通过向量数据库实现跨会话持久化，容量几乎无限。两者在存储介质、生命周期和容量上均有本质区别。 |

---

### 6.2 简答题答案

**第6题参考答案：**

ReAct 的三个核心环节及其作用：

- **Thought（思考）**：分析当前状态，判断是否需要调用工具以及调用哪个工具。这是 LLM 的推理过程，类似于人类的思考分析阶段。
- **Action（行动）**：根据思考结果执行具体的工具调用，如搜索信息、执行计算、控制机器人等。这是将推理结果转化为实际行动的环节。
- **Observation（观察）**：接收工具返回的结果，更新 Agent 对环境的认知，为下一轮思考提供输入。

**闭环形成机制**：
```
Thought → Action → Observation → Thought → ...
                   ↑
                   └── 将观察结果反馈给思考，更新认知
```

这种闭环使 Agent 能够根据行动结果动态调整策略，而非一次性生成全部答案。观察结果会作为新的上下文影响下一轮思考，从而实现"边做边想"的智能行为。

---

**第7题参考答案：**

| 维度 | LangChain Agents | CrewAI |
|------|------------------|--------|
| **设计理念** | 单 Agent 为核心，工具驱动 | 多 Agent 编排为核心，角色驱动 |
| **多 Agent 支持** | 通过 Agent + Tool 组合实现 | 原生支持多 Agent 协作（通过 Crew） |
| **协作机制** | 通过共享工具和 Memory 间接协作 | 通过 Process（Sequential/Hierarchical）显式编排 |
| **学习曲线** | 陡峭（模块多、概念多） | 平缓（API 简洁直观） |
| **适用场景** | 通用 LLM 应用、知识库问答、生产系统 | 多角色协作任务、团队模拟、工作流自动化 |
| **典型案例** | RAG + Tool Use Agent | 营销 Agent 团队、软件开发团队 |

**总结**：LangChain 适合需要精细控制单 Agent 行为和工具调用的场景；CrewAI 适合需要多角色分工协作、快速构建 Agent 团队的场景。

---

**第8题参考答案：**

**为什么需要闭环**：
具身智能的核心特征是 Agent（机器人）与物理世界持续交互。物理世界充满不确定性和变化——物体位置可能改变、障碍物可能出现、动作执行可能有误差。闭环使机器人能够：
1. **感知变化**：通过传感器实时获取环境状态
2. **根据变化调整决策**：如果杯子被移动了，机器人需要重新规划
3. **验证执行效果**：确认动作是否成功完成

**与传统顺序执行相比的优势**：

| 维度 | 传统顺序执行 | 感知-决策-执行闭环 |
|------|-------------|-------------------|
| **对变化的响应** | 固定流程，无法适应 | 实时感知，动态调整 |
| **错误恢复** | 失败即停止 | 自动检测并尝试修正 |
| **适应性** | 只适合环境固定场景 | 适合复杂多变的真实环境 |
| **执行效率** | 可能做无用功（如物体已移走仍去抓取） | 每步都有反馈，高效精准 |
| **代码复杂度** | 简单但脆弱 | 复杂但健壮 |

**典型例子**：让机器人去桌上拿杯子。如果杯子被人在执行过程中移走了，开环系统会扑个空；闭环系统会在抓取失败后感知到异常，重新定位杯子或报告问题。这就是闭环对于具身智能不可替代的价值。

---

## 课程总结

本课程系统学习了 LLM Agent 框架的核心知识：

| 模块 | 关键内容 |
|------|----------|
| **Agent 概述** | Agent = LLM + Tools + Memory + Planning；ReAct 与 Plan-and-Execute 两大范式 |
| **主流框架** | LangChain（工具生态）、LlamaIndex（知识检索）、AutoGPT/BabyAGI（自主代理）、MetaGPT（多Agent协作）、CrewAI（多Agent编排） |
| **核心组件** | Tool Use（工具定义与选择）、Memory（短期/长期/混合）、Planning（任务分解与自我修正）、对话管理 |
| **具身智能** | 感知-决策-执行闭环、多机器人通信Agent |
| **代码实战** | LangChain Agent 工具调用、ReAct 手动实现、具身任务执行Agent |

---

*课程版本：v1.0 | 更新日期：2026-03-25 | 编写者：Wendy Agent*

