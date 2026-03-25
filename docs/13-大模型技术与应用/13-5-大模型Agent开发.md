# 13-5 大模型Agent开发

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 13-5 |
| 课程名称 | 大模型Agent开发 |
| 所属模块 | 13-大模型技术与应用 |
| 难度等级 | ⭐⭐⭐⭐⭐ |
| 预计学时 | 5小时 |
| 前置知识 | Python基础、LangChain框架、Prompt Engineering、大模型API调用基础 |

---

## 目录

1. [Agent概述](#1-agent概述)
2. [ReAct框架](#2-react框架)
3. [Tool Use](#3-tool-use)
4. [Memory系统](#4-memory系统)
5. [Multi-Agent系统](#5-multi-agent系统)
6. [代码实战](#6-代码实战)
7. [练习题](#7-练习题)
8. [参考答案](#8-参考答案)

---

## 1. Agent概述

### 1.1 什么是AI Agent

**AI Agent（人工智能智能体）** 是一种能够感知环境、进行自主决策、执行操作并基于反馈持续优化的智能系统。与传统的固定流程程序不同，Agent具有自主性和动态性——它可以根据不同情况选择不同的行动策略。

在LLM应用场景中，Agent通常指基于大语言模型构建的智能系统，该系统具备以下能力：

- **自主规划**：将复杂任务分解为可执行的步骤
- **工具使用**：调用外部工具（搜索引擎、API、代码执行等）完成任务
- **记忆管理**：保存和利用历史交互信息
- **持续迭代**：根据执行结果动态调整下一步行动

### 1.2 Agent的核心组件

一个完整的LLM Agent由三大核心组件构成：**规划（Planning）**、**记忆（Memory）** 和 **工具（Tools）**。

| 组件 | 作用 | 类比 |
|------|------|------|
| **规划 Planning** | 分解任务，决定行动策略 | Agent的大脑 |
| **记忆 Memory** | 存储和检索信息 | Agent的知识库 |
| **工具 Tools** | 与外部世界交互 | Agent的四肢 |

**规划（Planning）** 是Agent的"大脑"，负责将复杂任务分解为可执行的步骤序列。

| 规划类型 | 说明 | 适用场景 |
|----------|------|----------|
| **任务分解** | 将复杂任务拆解为多个简单子任务 | 多步骤复杂问题 |
| **子目标执行** | 逐个完成子目标，最终达成整体目标 | 长期规划任务 |
| **自我反思** | 对执行结果进行评估和修正 | 错误恢复、迭代优化 |

**记忆（Memory）** 是Agent的"知识库"，用于存储和检索各类信息。

| 记忆类型 | 生命周期 | 存储内容 | 容量 |
|----------|----------|----------|------|
| **短期记忆** | 当前会话 | 对话历史、上下文 | 有限（受限于上下文窗口） |
| **长期记忆** | 跨会话 | 持久化知识、经验 | 几乎无限 |

**工具（Tools）** 是Agent与外部世界交互的"四肢"。

| 工具类型 | 示例 | 功能 |
|----------|------|------|
| **搜索工具** | Google Search、Bing Search | 获取实时信息 |
| **API工具** | HTTP请求、数据库查询 | 调用外部服务 |
| **代码执行** | Python REPL、计算器 | 执行计算或代码 |
| **文件操作** | 读文件、写文件 | 操作本地资源 |
| **设备控制** | 机器人控制、传感器读取 | 物理世界交互 |

### 1.3 Agent的发展历程

| 时期 | 阶段 | 代表成果 |
|------|------|----------|
| **2019-2022** | 早期探索期 | Rule-based Agent、专家系统、决策树 |
| **2022-2023** | LLM爆发期 | ReAct论文、AutoGPT、BabyAGI、Toolformer |
| **2023-2024** | 框架成熟期 | LangChain Agent完善、Multi-Agent框架兴起 |
| **2024-2025** | 具身Agent爆发期 | RT-2、OpenVLA、VLA架构、Agent自我进化 |

### 1.4 Agent的技术范式对比

| 范式 | 核心思想 | 优点 | 缺点 |
|------|----------|------|------|
| **Prompt-only** | 纯提示词驱动 | 简单、快速 | 能力有限 |
| **ReAct** | 推理+行动循环 | 可解释、可纠错 | 循环次数多时效率低 |
| **Plan-then-Execute** | 先规划后执行 | 规划清晰 | 中途无法调整 |
| **Multi-Agent** | 多Agent协作 | 专业化分工 | 通信开销大 |

---

## 2. ReAct框架

### 2.1 ReAct原理

**ReAct**（Reasoning + Acting）是由清华大学和普林斯顿大学于2023年提出的Agent框架，其核心思想是将**推理（Reasoning）** 和 **行动（Acting）** 有机结合，使Agent能够在推理过程中生成具体行动，同时通过行动结果反向馈送到推理过程中。

论文地址：[Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)

ReAct的核心洞察：
> **孤立的推理（Reasoning）缺乏世界知识更新；孤立的行动（Acting）缺乏目标导向的规划。将两者结合，形成"思考→行动→观察→思考"的闭环，才能实现真正的智能。**

### 2.2 Thought-Action-Observation循环

ReAct的完整循环由三个核心环节组成：

| 环节 | 含义 | 示例 |
|------|------|------|
| **Thought（思考）** | 分析当前状态，决定是否需要行动，以及采取什么行动 | "我需要搜索一下北京的天气情况" |
| **Action（行动）** | 执行具体的工具调用或推理步骤 | `get_weather(location="北京")` |
| **Observation（观察）** | 接收行动返回的结果，更新Agent认知 | "北京今天晴，气温25℃" |

```
ReAct 循环流程：

   用户输入 --> Thought(分析) --> Action(执行工具) --> Observation(接收结果) --> ...
                                                            |
                                                        [是否完成?]
                                                            |
                                                           是
                                                            V
                                                       输出结果
```

### 2.3 ReAct的Prompt模板

ReAct通过特定的Prompt模板引导模型进行Thought-Action-Observation循环：

```
你是一个AI助手，可以利用工具来回答问题。
在回答过程中，你需要按照以下格式进行思考和行动：

问题：{用户问题}
思考1：{你的第一个想法或分析}
行动1：{你调用的工具和参数}
观察1：{工具返回的结果}
思考2：{基于观察结果的下一步分析}
行动2：{你调用的工具和参数}
...（继续直到得到答案）
最终答案：{总结性回答}
```

### 2.4 ReAct与CoT、Act的对比

| 框架 | 全称 | 核心思想 | 与环境交互 |
|------|------|----------|------------|
| **CoT** | Chain of Thought | 逐步推理，不行动 | 仅内部推理 |
| **Act** | Action-based | 行动驱动推理 | 行动但不反思 |
| **ReAct** | Reasoning + Acting | 推理指导行动，行动反馈推理 | 完整闭环 |

---

## 3. Tool Use

### 3.1 工具定义与调用

在LangChain中，工具（Tools）是Agent与外部世界交互的核心接口。LangChain提供了统一的工具定义规范，开发者只需继承 `BaseTool` 类或使用 `@tool` 装饰器即可定义自己的工具。

#### 3.1.1 使用装饰器定义工具

```python
from langchain_core.tools import tool

# 使用 @tool 装饰器定义简单工具
@tool
def search_weather(location: str) -> str:
    """查询指定城市的天气信息

    参数:
        location: 城市名称，例如 "北京"、"上海"

    返回:
        天气信息字符串
    """
    # 模拟天气查询（实际项目中可接入真实API）
    weather_data = {
        "北京": "晴，25℃，湿度40%",
        "上海": "多云，28℃，湿度65%",
        "深圳": "雷阵雨，30℃，湿度80%"
    }
    return weather_data.get(location, "未找到该城市的天气信息")

# 查看工具属性
print(search_weather.name)        # 输出: search_weather
print(search_weather.description)  # 输出: 查询指定城市的天气信息...
print(search_weather.args)  # 输出: {'location': {'title': 'Location', 'type': 'string'}}
```

#### 3.1.2 使用类继承定义复杂工具

```python
from langchain_core.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

# 定义工具输入 schema
class CalculatorInput(BaseModel):
    """计算器工具的输入参数"""
    expression: str = Field(description="数学表达式，例如 '2+3*5' 或 'sqrt(16)'")

class CalculatorTool(BaseTool):
    """计算器工具 - 执行数学运算"""
    name: str = "calculator"
    description: str = "执行数学表达式的计算，适用于需要精确数值结果的场景"
    args_schema: Type[BaseModel] = CalculatorInput

    def _run(self, expression: str) -> str:
        """同步执行计算"""
        try:
            # 注意：实际项目中应使用安全的数学求值库
            # 这里使用 eval 仅作为演示，生产环境禁止使用！
            result = eval(expression, {"__builtins__": {}}, {})
            return f"计算结果: {expression} = {result}"
        except Exception as e:
            return f"计算错误: {str(e)}"

    async def _arun(self, expression: str) -> str:
        """异步执行计算"""
        return self._run(expression)

# 使用工具
calc = CalculatorTool()
result = calc.invoke({"expression": "2**10"})  # 2的10次方
print(result)  # 输出: 计算结果: 2**10 = 1024
```

### 3.2 工具选择策略

Agent如何决定使用哪个工具？这涉及到**工具选择策略**（Tool Selection Strategy）。

LangChain Agent通过**函数调用（Function Calling）**机制选择工具。当Agent需要执行某个行动时，它会：
1. 根据当前状态和可用工具，决定是否需要调用工具
2. 如果需要，从工具列表中选择最合适的一个
3. 生成符合工具参数规范的调用请求

#### 工具描述与自动选择

工具的描述（description）对选择准确性至关重要：

```python
# 好的工具描述示例
@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """搜索指定日期的航班信息

    适用场景：用户询问机票、航班时刻、航班价格相关问题
    参数说明：
        origin: 出发城市代码，例如 'PEK'（北京）、'SHA'（上海）
        destination: 目的地城市代码
        date: 出发日期，格式为 YYYY-MM-DD
    返回：航班列表及价格信息
    """
    pass

# 不好的描述示例（信息不足）
@tool
def search(data: str) -> str:
    """搜索"""
    pass
```

### 3.3 API集成

#### 3.3.1 HTTP请求工具

```python
import requests
from langchain_core.tools import tool

@tool
def search_news(keyword: str, max_results: int = 5) -> str:
    """搜索新闻资讯

    参数:
        keyword: 搜索关键词
        max_results: 最大返回条数，默认5条

    返回:
        相关新闻标题和摘要列表
    """
    # 实际项目中应使用真实的新闻API
    url = "https://news.example.com/api/search"
    params = {"q": keyword, "limit": max_results}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        results = []
        for i, item in enumerate(data.get("results", []), 1):
            results.append(f"{i}. {item['title']}\n   摘要: {item['summary']}")

        return "\n\n".join(results) if results else "未找到相关新闻"
    except requests.RequestException as e:
        return f"搜索失败: {str(e)}"
```

#### 3.3.2 数据库查询工具

```python
import sqlite3
from langchain_core.tools import tool

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect("knowledge.db")
    conn.row_factory = sqlite3.Row
    return conn

@tool
def query_knowledge_base(question: str, top_k: int = 3) -> str:
    """查询知识库获取相关信息

    参数:
        question: 用户问题
        top_k: 返回最相关的k条结果，默认3条

    返回:
        知识库中相关的内容片段
    """
    # 实际项目中应使用向量数据库做语义检索
    conn = get_db_connection()
    cursor = conn.cursor()

    keywords = question.split()
    where_clause = " OR ".join(["content LIKE ?" for _ in keywords])
    params = [f"%{kw}%" for kw in keywords]

    cursor.execute(
        f"SELECT title, content FROM knowledge_base WHERE {where_clause} LIMIT ?",
        params + [top_k]
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "知识库中未找到相关信息"

    results = [f"【{row['title']}】\n{row['content']}" for row in rows]
    return "\n\n".join(results)
```

---

## 4. Memory系统

### 4.1 短期记忆与长期记忆

Memory系统是Agent持续智能的基础。根据信息保留时间和用途，Agent的记忆可以分为**短期记忆**和**长期记忆**。

| 记忆类型 | 生命周期 | 存储内容 | 容量 |
|----------|----------|----------|------|
| **短期记忆** | 当前会话 | 对话历史、上下文 | 受上下文窗口限制 |
| **长期记忆** | 跨会话 | 持久化知识、经验 | 几乎无限 |

#### 4.1.1 短期记忆

```python
from langchain.memory import ConversationBufferMemory, ConversationWindowMemory

# 对话缓冲区记忆 - 保存完整历史
buffer_memory = ConversationBufferMemory(
    return_messages=True,    # 返回消息对象而非字符串
    output_key="answer",     # 指定输出键
    input_key="question"     # 指定输入键
)

# 对话窗口记忆 - 只保留最近3轮
window_memory = ConversationWindowMemory(
    k=3,                     # 保留最近3轮对话
    return_messages=True
)
```

#### 4.1.2 长期记忆

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **VectorStoreRetrieverMemory** | 使用向量数据库存储和检索记忆 | 语义相似记忆检索 |
| **KnowledgeGraphMemory** | 使用知识图谱存储结构化记忆 | 实体关系推理 |
| **SQLDatabaseMemory** | 使用关系数据库存储结构化记忆 | 结构化数据查询 |

### 4.2 记忆存储与检索

#### 4.2.1 向量记忆检索

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# 第一步：创建向量存储
embeddings = OpenAIEmbeddings()  # 需要设置 OPENAI_API_KEY
vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory="./memory_db"  # 持久化存储目录
)

# 第二步：创建向量记忆
memory = VectorStoreRetrieverMemory(
    vectorstore=vectorstore,
    memory_key="chat_history",   # 记忆在 prompt 中的键名
    return_messages=True,
    k=3                          # 检索最相关的3条记忆
)

# 第三步：保存记忆
memory.save_context(
    {"input": "我喜欢吃川菜，尤其是麻婆豆腐"},  # 输入
    {"output": "好的，我已经记住您喜欢川菜和麻婆豆腐了"}  # 输出
)
memory.save_context(
    {"input": "我对海鲜过敏"},
    {"output": "了解，我会避免推荐任何海鲜相关的菜品"}
)

# 第四步：检索相关记忆
related_memories = memory.load_memory_variables(
    {"input": "有什么好吃的推荐吗？"}
)
print(related_memories["chat_history"])
```

#### 4.2.2 记忆的自动总结

```python
from langchain.memory import ConversationSummaryMemory
from langchain_openai import ChatOpenAI

# 创建带总结功能的记忆
llm = ChatOpenAI(model="gpt-4")
summary_memory = ConversationSummaryMemory(
    llm=llm,
    return_messages=True,
    memory_key="summary"
)

# 模拟多轮对话
dialogues = [
    ("你好，我想了解机器人技术", "机器人技术是让机器具有智能行为的技术"),
    ("它主要应用在哪些领域？", "主要应用在工业制造、医疗护理、家庭服务等领域"),
    ("能具体说说工业领域的应用吗？", "工业机器人用于焊接、喷涂、装配等自动化生产线")
]

for user_input, ai_output in dialogues:
    summary_memory.save_context({"input": user_input}, {"output": ai_output})

# 获取总结后的记忆
summary = summary_memory.load_memory_variables({})
print(summary["summary"])
```

---

## 5. Multi-Agent系统

### 5.1 多Agent协作

Multi-Agent系统是指由多个Agent组成的协作网络，每个Agent专注于特定任务，通过协作完成复杂目标。

```
Multi-Agent 协作架构：

                    用户请求
                       |
                       v
            +--------------------+
            | Orchestrator Agent |
            | (任务分配与协调)    |
            +--------+-----------+
                       |
         +-------------+------------+
         |             |            |
         v             v            v
   +-----------+ +-----------+ +-----------+
   | Research  | |  Coder    | |  Critic   |
   | Agent     | |  Agent    | |  Agent    |
   | (调研代理) | | (编码代理) | | (评审代理) |
   +-----------+ +-----------+ +-----------+
         |             |            |
         +-------------+------------+
                       |
                       v
              整合结果输出
```

### 5.2 Agent通信机制

多个Agent之间需要有效的通信机制，常见模式包括：

| 模式 | 说明 | 优点 | 缺点 |
|------|------|------|------|
| **共享消息队列** | Agent通过消息队列传递信息 | 解耦、易扩展 | 需要消息队列基础设施 |
| **共享状态** | Agent读写共享状态（数据库、文件系统）| 简单直接 | 一致性风险 |
| **直接通信** | Agent之间直接调用 | 低延迟 | 耦合度高 |
| **层级汇报** | 下级Agent向协调Agent汇报 | 结构清晰 | 层级限制 |

#### 5.2.1 消息传递示例

```python
from typing import List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentMessage:
    """Agent间通信的消息格式"""
    sender: str           # 发送方Agent名称
    receiver: str         # 接收方Agent名称
    content: str          # 消息内容
    message_type: str     # 消息类型: task/result/feedback
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class MessageBus:
    """简单的消息总线（用于Agent间通信）"""

    def __init__(self):
        self.inbox: dict = {}  # 每个Agent的消息收件箱

    def send(self, message: AgentMessage):
        """发送消息"""
        receiver = message.receiver
        if receiver not in self.inbox:
            self.inbox[receiver] = []
        self.inbox[receiver].append(message)
        print(f"[{message.sender}] -> [{message.receiver}]: {message.content[:50]}...")

    def receive(self, agent_name: str) -> List[AgentMessage]:
        """收取消息"""
        messages = self.inbox.get(agent_name, [])
        self.inbox[agent_name] = []
        return messages

# 使用示例
bus = MessageBus()

# 协调Agent发送任务给研究Agent
bus.send(AgentMessage(
    sender="orchestrator",
    receiver="research_agent",
    content="请调研2024年具身智能领域的最新进展",
    message_type="task"
))

# 研究Agent完成任务后返回结果
bus.send(AgentMessage(
    sender="research_agent",
    receiver="orchestrator",
    content="具身智能最新进展：多模态大模型与机器人结合，VLA架构成为主流",
    message_type="result"
))
```

### 5.3 任务分解与执行

```python
from typing import List, Dict

def decompose_task(task: str) -> List[Dict[str, str]]:
    """将复杂任务分解为多个子任务

    参数:
        task: 原始任务描述

    返回:
        子任务列表，每个子任务包含 name、agent、description
    """
    subtasks = []
    task_lower = task.lower()

    if any(kw in task_lower for kw in ["调研", "研究", "分析", "调查"]):
        subtasks.append({
            "name": "research_task",
            "agent": "research_agent",
            "description": "对任务进行深入调研和信息收集"
        })

    if any(kw in task_lower for kw in ["实现", "开发", "代码", "编写", "构建"]):
        subtasks.append({
            "name": "coding_task",
            "agent": "coder_agent",
            "description": "编写和实现代码"
        })

    if any(kw in task_lower for kw in ["评审", "检查", "审查", "优化"]):
        subtasks.append({
            "name": "review_task",
            "agent": "critic_agent",
            "description": "对结果进行评审和优化建议"
        })

    if any(kw in task_lower for kw in ["测试", "验证", "实验"]):
        subtasks.append({
            "name": "test_task",
            "agent": "test_agent",
            "description": "执行测试和验证"
        })

    if not subtasks:
        subtasks.append({
            "name": "summarize_task",
            "agent": "summarizer_agent",
            "description": "总结任务结果并输出"
        })

    return subtasks

# 示例
task = "调研具身智能最新进展，并实现一个演示系统，最后进行测试验证"
subtasks = decompose_task(task)
for i, st in enumerate(subtasks, 1):
    print(f"{i}. [{st['agent']}] {st['description']}")
```

输出：
```
1. [research_agent] 对任务进行深入调研和信息收集
2. [coder_agent] 编写和实现代码
3. [test_agent] 执行测试和验证
```

---

## 6. 代码实战

### 6.1 基于LangChain的Agent实现

```python
"""
LangChain Agent 实战：构建一个多功能机器人助手
功能：天气查询 + 计算器 + 知识问答
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

# ============================================================
# 第一步：定义工具
# ============================================================

@tool
def get_weather(city: str) -> str:
    """查询城市天气

    当用户询问某个城市的天气时使用此工具。

    参数:
        city: 城市名称，例如 "北京"、"上海"

    返回:
        天气信息字符串
    """
    weather_db = {
        "北京": "北京今天晴，温度15-25℃，空气质量良好",
        "上海": "上海今天多云，温度18-28℃，有轻微雾霾",
        "深圳": "深圳今天雷阵雨，温度25-32℃，记得带伞",
        "杭州": "杭州今天晴转多云，温度16-26℃，适合出游",
        "成都": "成都今天阴天，温度14-22℃，体感较凉"
    }
    return weather_db.get(city, f"抱歉，暂未收录{city}的天气信息")

@tool
def calculate(expression: str) -> str:
    """数学计算器

    当需要进行数学计算时使用此工具。
    支持加减乘除、指数、开方等运算。

    参数:
        expression: 数学表达式，例如 "2+3*5"、"10**2"、"sqrt(16)"

    返回:
        计算结果字符串
    """
    try:
        # 安全计算（实际项目应使用更安全的库如 numexpr）
        # 这里仅做演示，生产环境请使用 ast.literal_eval 或 numexpr
        result = eval(expression, {"__builtins__": {}, "sqrt": lambda x: x**0.5}, {})
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{str(e)}"

@tool
def search_knowledge(query: str) -> str:
    """知识库搜索

    当用户询问常识性知识、科学原理、历史事件等问题时使用。

    参数:
        query: 搜索关键词或问题

    返回:
        相关的知识内容
    """
    knowledge_base = {
        "人工智能": "人工智能(AI)是研究使机器具有智能行为的技术，包括机器学习、深度学习、自然语言处理等分支。",
        "机器人": "机器人是一种能够自主执行任务的机械装置，现代机器人结合了传感器、执行器和AI算法。",
        "大语言模型": "大语言模型(LLM)是基于Transformer架构的海量文本训练的深度学习模型，能够理解和生成自然语言。",
        "具身智能": "具身智能(Embodied AI)是指具有身体并能与物理世界交互的智能系统，如机器人、自动驾驶等。"
    }

    for key, value in knowledge_base.items():
        if key in query:
            return value
    return "抱歉，知识库中未找到相关信息"

# 工具列表
tools = [get_weather, calculate, search_knowledge]

# ============================================================
# 第二步：初始化LLM
# ============================================================

import os
os.environ["OPENAI_API_KEY"] = "your-api-key"  # 替换为您的API Key

llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7
)

# ============================================================
# 第三步：创建Agent
# ============================================================

# 从 LangChain Hub 拉取 ReAct 提示词模板
prompt = hub.pull("hwchase17/react")

# 创建 ReAct Agent
agent = create_react_agent(llm, tools, prompt)

# 创建 Agent 执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,          # 打印完整执行过程
    max_iterations=10,     # 最大迭代次数，防止无限循环
    handle_parsing_errors=True  # 自动处理解析错误
)

# ============================================================
# 第四步：运行Agent
# ============================================================

if __name__ == "__main__":
    questions = [
        "北京今天天气怎么样？",
        "计算 2 的 10 次方等于多少？",
        "什么是大语言模型？请简要说明。",
        "上海天气如何？顺便帮我计算一下 100 * 99 等于多少？"
    ]

    for q in questions:
        print(f"\n{'='*60}")
        print(f"用户问题: {q}")
        print(f"{'='*60}")
        response = agent_executor.invoke({"input": q})
        print(f"\n最终答案: {response['output']}")
```

### 6.2 ReAct模式手动实现

```python
"""
ReAct 模式从零实现：手动实现 Thought-Action-Observation 循环
不依赖 LangChain，仅使用 OpenAI API
"""

import json
import re
from typing import List, Dict, Any, Callable, Optional

# ============================================================
# 第一步：定义工具注册表
# ============================================================

class ToolRegistry:
    """工具注册表，管理所有可用工具"""

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, func: Callable):
        """注册工具"""
        self.tools[name] = {
            "description": description,
            "func": func
        }

    def get_tool_schemas(self) -> List[Dict]:
        """获取工具schema列表（用于OpenAI Function Calling）"""
        schemas = []
        for name, tool in self.tools.items():
            sig = tool["func"].__code__
            varnames = sig.co_varnames
            defaults = sig.co_defaults or ()
            n_defaults = len(defaults)
            n_required = len(varnames) - n_defaults

            params = {}
            for i, var in enumerate(varnames):
                if i < n_required:
                    params[var] = {"type": "string", "description": f"{var}参数"}
                else:
                    params[var] = {"type": "string", "description": f"{var}参数（可选）"}

            schemas.append({
                "name": name,
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": params,
                    "required": list(varnames[:n_required])
                }
            })
        return schemas

    def execute(self, name: str, arguments: Dict) -> str:
        """执行工具调用"""
        if name not in self.tools:
            return f"错误：未找到工具 {name}"
        try:
            func = self.tools[name]["func"]
            return str(func(**arguments))
        except Exception as e:
            return f"工具执行错误: {str(e)}"

# 初始化工具注册表
registry = ToolRegistry()

# 注册天气工具
def get_weather(location: str) -> str:
    """查询城市天气"""
    weather_db = {
        "北京": "晴，25℃",
        "上海": "多云，28℃",
        "深圳": "雷阵雨，30℃"
    }
    return weather_db.get(location, "未找到该城市天气")

registry.register(
    name="get_weather",
    description="查询指定城市的天气信息，参数：location(城市名)",
    func=get_weather
)

# 注册计算器工具
def calculate(expression: str) -> str:
    """执行数学计算"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"计算错误: {str(e)}"

registry.register(
    name="calculate",
    description="执行数学计算，参数：expression(数学表达式)",
    func=calculate
)

# ============================================================
# 第二步：构建ReAct Agent
# ============================================================

class ReActAgent:
    """ReAct 模式 Agent"""

    def __init__(self, llm_client, tool_registry: ToolRegistry):
        self.llm = llm_client
        self.registry = tool_registry
        self.tools = tool_registry.get_tool_schemas()

    def build_system_prompt(self) -> str:
        """构建系统提示词"""
        tool_desc = "\n".join([
            f"- {t['name']}: {t['description']}"
            for t in self.tools
        ])
        return f"""你是一个智能助手，可以使用工具来回答问题。

可用工具：
{tool_desc}

请按照以下格式回答问题：

问题：{{用户问题}}
思考：{{你的分析过程}}
行动：{{工具名称}}({{"参数名": "参数值"}})
观察：{{工具返回结果}}
...（重复思考-行动-观察直到得到答案）
最终答案：{{总结性回答}}
只使用上面列出的工具，不要编造结果。"""

    def run(self, question: str, max_iterations: int = 10) -> str:
        """运行 Agent"""
        messages = [{"role": "system", "content": self.build_system_prompt()}]
        messages.append({"role": "user", "content": f"问题：{question}"})

        for i in range(max_iterations):
            # 调用 LLM
            response = self.llm.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=[{"type": "function", "function": t} for t in self.tools],
                tool_choice="auto"
            )

            reply = response.choices[0].message
            content = reply.content or ""

            # 检查是否调用了工具
            if reply.tool_calls:
                tool_call = reply.tool_calls[0]
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                # 执行工具
                observation = self.registry.execute(tool_name, args)

                # 添加到对话历史
                messages.append({"role": "assistant", "content": content})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": observation
                })
            else:
                # LLM 直接回答
                if "最终答案" in content or "答案" in content[-100:]:
                    if "最终答案" in content:
                        answer = content.split("最终答案")[-1].strip()
                    else:
                        answer = content
                    return answer
                messages.append({"role": "assistant", "content": content})

        return "Agent 执行超过最大迭代次数"

# ============================================================
# 第三步：运行 Agent
# ============================================================

if __name__ == "__main__":
    from openai import OpenAI
    import os

    os.environ["OPENAI_API_KEY"] = "your-api-key"  # 替换为您的API Key
    client = OpenAI()

    agent = ReActAgent(client, registry)

    questions = [
        "北京今天天气怎么样？",
        "计算 2 的 10 次方等于多少？",
    ]

    for q in questions:
        print(f"\n{'='*50}")
        print(f"问题: {q}")
        print(f"{'='*50}")
        result = agent.run(q)
        print(f"答案: {result}")
```

### 6.3 Tool绑定与调用

```python
"""
演示如何在 LangChain 中进行 Tool 绑定与调用
"""
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# 定义多个工具
@tool
def search_wiki(query: str) -> str:
    """搜索维基百科获取信息"""
    wiki_data = {
        "人工智能": "人工智能(AI)是研究如何让机器具有智能行为的技术学科。",
        "机器学习": "机器学习是人工智能的一个分支，研究如何让计算机从数据中学习。",
        "深度学习": "深度学习是机器学习的一个子领域，使用多层神经网络进行学习。"
    }
    for key, value in wiki_data.items():
        if key in query:
            return value
    return "未找到相关信息"

@tool
def get_date() -> str:
    """获取当前日期"""
    from datetime import datetime
    return datetime.now().strftime("%Y年%m月%d日")

@tool
def web_search(query: str) -> str:
    """使用搜索引擎搜索信息

    参数:
        query: 搜索关键词

    返回:
        搜索结果摘要
    """
    # 实际项目中应接入真实搜索引擎API
    return f"搜索结果：关于 '{query}' 的信息已在互联网上广泛讨论。"

# 工具列表
tools = [search_wiki, get_date, web_search]

# 初始化 LLM 并绑定工具
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"

llm = ChatOpenAI(model="gpt-4")
llm_with_tools = llm.bind_tools(tools)  # 关键：绑定工具到 LLM

# 测试工具调用
test_questions = [
    "今天是多少号？",
    "请帮我搜索一下人工智能的定义",
    "深度学习和机器学习有什么关系？"
]

for q in test_questions:
    print(f"\n问题: {q}")
    response = llm_with_tools.invoke(q)
    print(f"模型决定调用: {[tc.function.name for tc in response.tool_calls] if response.tool_calls else '无'}")
```

### 6.4 多Agent协作示例

```python
"""
Multi-Agent 协作示例：研究 + 编码 + 评审
"""
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

# ============================================================
# Agent 消息定义
# ============================================================

@dataclass
class Message:
    sender: str
    receiver: str
    content: str
    msg_type: str  # task / result / feedback
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

# ============================================================
专业 Agent
# ============================================================

class ResearchAgent:
    """研究 Agent：负责信息调研"""
    name = "research_agent"

    def process(self, task: str) -> str:
        """处理研究任务"""
        # 实际项目中可接入搜索引擎或知识库
        return f"调研完成：关于 '{task}' 的最新研究表明，该领域正在快速发展。"

class CoderAgent:
    """编码 Agent：负责代码实现"""
    name = "coder_agent"

    def process(self, task: str) -> str:
        """处理编码任务"""
        return f"代码实现完成：已按照要求完成 '{task}' 的核心功能开发。"

class CriticAgent:
    """评审 Agent：负责结果评审"""
    name = "critic_agent"

    def process(self, code: str) -> str:
        """处理评审任务"""
        return f"评审意见：代码整体质量良好，建议在错误处理和性能方面进一步优化。"

# ============================================================
# Multi-Agent 协调器
# ============================================================

class MultiAgentOrchestrator:
    """多Agent协调器"""

    def __init__(self):
        self.agents = {
            "research_agent": ResearchAgent(),
            "coder_agent": CoderAgent(),
            "critic_agent": CriticAgent()
        }
        self.message_bus = MessageBus()

    def run(self, task: str) -> str:
        """运行多Agent协作流程"""
        print(f"收到任务: {task}")

        # 1. 任务分解
        subtasks = decompose_task(task)
        print(f"任务分解为 {len(subtasks)} 个子任务")

        results = {}

        # 2. 分发给各专业Agent执行
        for st in subtasks:
            agent_name = st["agent"]
            agent = self.agents[agent_name]
            print(f"分配任务给 {agent_name}...")

            # 执行任务（实际项目中通过消息总线传递）
            result = agent.process(st["description"])
            results[agent_name] = result
            print(f"{agent_name} 完成: {result[:50]}...")

        # 3. 整合结果
        final_report = self._generate_report(task, results)
        return final_report

    def _generate_report(self, task: str, results: Dict) -> str:
        """生成最终报告"""
        report = [f"# 任务执行报告: {task}", ""]
        report.append("## 执行摘要")
        for agent_name, result in results.items():
            report.append(f"- **{agent_name}**: {result}")
        report.append("")
        report.append("## 结论")
        report.append("任务已通过多Agent协作完成，各Agent分工明确，协调顺畅。")
        return "\n".join(report)

# ============================================================
# 运行示例
# ============================================================

if __name__ == "__main__":
    orchestrator = MultiAgentOrchestrator()

    task = "调研具身智能最新进展，并实现一个演示系统，最后进行测试验证"
    result = orchestrator.run(task)
    print("\n" + "="*60)
    print("最终报告:")
    print("="*60)
    print(result)

---

## 7. 练习题

### 题目一：概念理解

1. 什么是AI Agent？它与传统程序有什么区别？
2. ReAct框架的核心思想是什么？请简述Thought-Action-Observation循环。
3. LangChain Agent中，工具（Tools）的作用是什么？如何定义一个工具？

### 题目二：编程实践

4. 使用LangChain实现一个具有天气查询和计算器功能的Agent。
5. 不依赖LangChain，手动实现一个简单的ReAct Agent（需要包含工具注册表和执行循环）。
6. 实现一个多Agent协作系统，包含研究Agent、编码Agent和评审Agent，通过消息总线进行通信。

### 题目三：系统设计

7. 设计一个具身智能机器人Agent系统，要求：
   - 具备短期记忆和长期记忆
   - 能够调用传感器工具获取环境信息
   - 能够调用运动控制工具操作机器人
   - 请画出系统架构图并说明各组件职责

### 题目四：分析思考

8. 讨论ReAct、Plan-then-Execute和Multi-Agent三种Agent范式的优缺点及适用场景。
9. 为什么说"工具描述（Tool Description）的质量直接影响Agent的工具选择准确性"？
10. 在设计Multi-Agent系统时，需要考虑哪些关键问题？

---

## 8. 参考答案

### 题目一：概念理解

**1. 什么是AI Agent？它与传统程序有什么区别？**

AI Agent是一种能够感知环境、进行自主决策、执行操作并基于反馈持续优化的智能系统。与传统程序的区别：

| 区别 | 传统程序 | AI Agent |
|------|----------|----------|
| 流程 | 固定流程，预先确定 | 动态决策，运行时决定 |
| 交互 | 被动响应用户输入 | 主动规划，持续迭代 |
| 适应性 | 固定逻辑，无法适应新情况 | 可根据反馈调整策略 |
| 工具使用 | 无 | 可调用外部工具 |

**2. ReAct框架的核心思想是什么？**

ReAct（Reasoning + Acting）的核心思想是将推理和行动有机结合：

- **Thought**：分析当前状态，决定是否需要行动
- **Action**：执行具体的工具调用
- **Observation**：接收行动结果，更新Agent认知

三者形成闭环，使Agent能够在推理指导下行动，通过行动结果反哺推理过程。

**3. 工具（Tools）的作用及定义方式**

工具是Agent与外部世界交互的接口。使用`@tool`装饰器定义：

```python
from langchain_core.tools import tool

@tool
def search_weather(location: str) -> str:
    """查询城市天气"""
    return "天气信息..."
```

### 题目二：编程实践

**4. LangChain Agent实现（参考6.1节代码）**

见6.1节完整代码示例，包含`get_weather`、`calculate`、`search_knowledge`三个工具。

**5. 手动实现ReAct Agent（参考6.2节代码）**

见6.2节完整代码示例，包含`ToolRegistry`类、`ReActAgent`类和完整执行循环。

**6. 多Agent协作系统（参考6.4节代码）**

见6.4节完整代码示例，包含`ResearchAgent`、`CoderAgent`、`CriticAgent`和`MultiAgentOrchestrator`。

### 题目三：系统设计

**7. 具身智能机器人Agent系统设计**

```
┌─────────────────────────────────────────────────────────┐
│                 具身智能机器人Agent架构                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐│
│   │  感知模块   │───▶│  规划模块   │───▶│  执行模块   ││
│   │ Perception  │    │ Planning   │    │ Execution   ││
│   └─────────────┘    └─────────────┘    └─────────────┘│
│         │                  │                  │        │
│         └──────────────────┴──────────────────┘        │
│                         │                               │
│                   ┌─────────────┐                       │
│                   │   LLM大脑   │                       │
│                   └─────────────┘                       │
│                         │                               │
│   ┌─────────────────────┼─────────────────────┐        │
│   │                     │                     │        │
│   ▼                     ▼                     ▼        │
│ ┌──────────┐      ┌──────────┐      ┌──────────┐     │
│ │ 传感器   │      │ 运动控制  │      │ 视觉识别  │     │
│ │ 工具     │      │ 工具     │      │ 工具     │     │
│ └──────────┘      └──────────┘      └──────────┘     │
│                         │                               │
│   ┌─────────────────────┼─────────────────────┐        │
│   │              记忆系统                        │        │
│   │  ┌──────────┐      ┌──────────┐          │        │
│   │  │ 短期记忆  │      │ 长期记忆  │          │        │
│   │  │(对话历史) │      │(向量数据库│          │        │
│   │  └──────────┘      └──────────┘          │        │
│   └─────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

**组件职责**：
- **感知模块**：接收传感器数据，构建环境状态表示
- **规划模块**：基于LLM进行任务分解和行动规划
- **执行模块**：将决策转化为具体的控制指令
- **记忆系统**：短期记忆管理会话上下文，长期记忆存储知识经验
- **工具层**：封装传感器读取、运动控制、视觉识别等能力

### 题目四：分析思考

**8. 三种Agent范式对比**

| 范式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **ReAct** | 可解释性强，可实时纠错 | 循环次数多时效率低 | 需要工具调用的复杂推理任务 |
| **Plan-then-Execute** | 规划清晰，执行效率高 | 中途无法调整，灵活性差 | 目标明确、步骤固定的任务 |
| **Multi-Agent** | 专业分工，可并行处理 | 通信开销大，调试复杂 | 复杂多领域任务 |

**9. 工具描述质量的重要性**

工具描述是LLM选择工具的唯一依据。好的描述应该包含：
- 工具适用场景
- 参数含义和格式要求
- 返回值说明

描述不清晰会导致LLM错误选择工具或生成错误参数。

**10. Multi-Agent系统设计关键问题**

- **通信机制**：选择合适的Agent间通信方式
- **任务分解**：如何将复杂任务合理分配给专业Agent
- **协调机制**：协调Agent如何监控和管理子任务执行
- **错误处理**：某个Agent失败时的恢复策略
- **一致性**：多Agent协作时如何保证结果一致性
