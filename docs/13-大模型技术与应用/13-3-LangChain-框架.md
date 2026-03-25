# 13-3 LangChain 框架

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 13-3 |
| 课程名称 | LangChain 框架 |
| 所属模块 | 13-大模型技术与应用 |
| 难度等级 | ⭐⭐⭐⭐☆ |
| 预计学时 | 4小时 |
| 前置知识 | Python基础、Prompt Engineering、大模型API调用基础 |

---

## 目录

1. [LangChain概述](#1-langchain概述)
2. [LangChain表达式语言（LCEL）](#2-langchain表达式语言lcel)
3. [Prompt模板](#3-prompt模板)
4. [Chains](#4-chains)
5. [Agents](#5-agents)
6. [Memory](#6-memory)
7. [代码实战](#7-代码实战)
8. [练习题](#8-练习题)
9. [参考答案](#9-参考答案)

---

## 1. LangChain概述

### 1.1 什么是LangChain

**LangChain** 是一个用于构建大语言模型（LLM）应用的开源框架，由Harrison Chase于2022年10月推出。它提供了一整套工具和抽象层，让开发者能够更便捷地将LLM与外部数据源、工具、以及用户交互结合起来。

LangChain的核心目标是简化**LLM应用的开发流程**。在LangChain出现之前，将LLM与外部系统集成往往需要编写大量胶水代码；有了LangChain之后，开发者可以通过声明式的组件组合来构建复杂的AI应用。

**LangChain的核心价值**：

| 价值 | 说明 |
|------|------|
| **模块化设计** | 将LLM应用拆分为独立的可复用组件 |
| **链式调用** | 通过Chains将多个组件串联成复杂流程 |
| **工具集成** | 轻松连接外部API、数据库、搜索引擎等 |
| **记忆管理** | 内置多种Memory方案，支持多轮对话 |
| **Agent支持** | 支持自主决策和工具调用的智能Agent |

### 1.2 LangChain发展历程

| 版本 | 时间 | 重要更新 |
|------|------|----------|
| **v0.0.1** | 2022年10月 | 初始发布，基础组件 |
| **v0.1.0** | 2023年 | Python/JS双版本，Chain概念成熟 |
| **v0.2.0** | 2024年 | LCEL正式发布，架构重构 |
| **v1.0.0** | 2025年 | 生产级稳定，生态完善 |

> **注意**：LangChain在2024年经历了重大架构变化，拆分为`langchain-core`、`langchain-community`、`langchain`等多个包。本课程以当前主流版本为准。

### 1.3 核心组件总览

LangChain的核心组件可以划分为以下几大类：

```
LangChain 核心组件
├── Models（模型）
│   ├── LLM（大语言模型）
│   ├── ChatModel（聊天模型）
│   └── Embeddings（嵌入模型）
├── Prompts（提示词）
│   ├── PromptTemplate
│   ├── ChatPromptTemplate
│   └── FewShotPromptTemplate
├── Chains（链）
│   ├── LLMChain
│   ├── SequentialChain
│   └── RouterChain
├── Agents（智能体）
│   ├── Agent
│   └── Tool
├── Memory（记忆）
│   ├── ConversationBufferMemory
│   ├── ConversationSummaryMemory
│   └── VectorStoreRetriever
└── Indexes（索引）
    ├── Document Loader
    ├── Text Splitter
    └── VectorStore
```

#### 1.3.1 Models（模型）

**Models** 是LangChain的核心，所有LLM交互都通过Model组件完成。LangChain支持多种模型类型：

| 模型类型 | 说明 | 使用场景 |
|----------|------|----------|
| **LLM** | 文本补全模型，接收文本输入，返回文本输出 | 文本生成、翻译 |
| **ChatModel** | 聊天模型，接收消息列表，返回聊天消息 | 对话系统 |
| **Embeddings** | 嵌入模型，将文本转为向量 | 语义搜索、RAG |

```python
# LLM 模型示例
from langchain_openai import OpenAI

# 初始化LLM（文本补全模型）
llm = OpenAI(model="gpt-3.5-turbo-instruct")

# 调用
result = llm.invoke("你好，请介绍一下自己")
print(result)
```

```python
# ChatModel 示例
from langchain_openai import ChatOpenAI

# 初始化ChatModel（聊天模型）
chat_model = ChatOpenAI(model="gpt-4")

# 调用（传入消息列表）
result = chat_model.invoke([
    {"role": "system", "content": "你是一个友好的助手"},
    {"role": "user", "content": "你好"}
])
print(result.content)
```

#### 1.3.2 Prompts（提示词）

Prompts组件负责管理和优化提示词，是LLM应用质量的关键。LangChain提供了多种Prompt模板：

| 组件 | 说明 |
|------|------|
| **PromptTemplate** | 文本补全场景的提示模板 |
| **ChatPromptTemplate** | 聊天场景的消息模板 |
| **FewShotPromptTemplate** | 带示例的少样本学习模板 |

#### 1.3.3 Chains（链）

**Chains** 是LangChain的核心概念之一。它将多个组件（Model、Prompt、Tool等）串联起来，形成完整的工作流程。Chains解决了复杂任务需要多次LLM调用的问题。

```
简单Chain：
Prompt → Model → Output

复杂Chain：
Input → Prompt1 → Model1 → Output1
                       ↓
                   Prompt2 → Model2 → Output2
                                   ↓
                               Prompt3 → Model3 → Final Output
```

#### 1.3.4 Agents（智能体）

**Agents** 是能够自主决策的智能组件。与固定流程的Chains不同，Agents可以根据输入动态决定下一步操作、选择使用哪个工具。

Agent的核心循环：

```
输入 → 推理(Reasoning) → 行动(Action) → 观察(Observation) → ...
```

#### 1.3.5 Memory（记忆）

**Memory** 为LLM应用提供记忆能力，支持多轮对话上下文。LangChain实现了多种记忆存储方案，从简单的缓冲区到摘要式记忆。

```
┌──────────────────────────────────────────┐
│              Memory 类型对比              │
├─────────────────┬────────────────────────┤
│  Conversation   │ 存储完整对话历史        │
│  BufferMemory   │ 简单直接，但有长度限制   │
├─────────────────┼────────────────────────┤
│  Conversation   │ 对话历史生成摘要        │
│  SummaryMemory  │ 节省token，适合长对话   │
├─────────────────┼────────────────────────┤
│  Conversation   │ 结合缓冲和摘要          │
│  WindowMemory   │ 保留最近N轮对话        │
└─────────────────┴────────────────────────┘
```

### 1.4 LangChain架构分层

LangChain的架构分为四个层次，从底层到高层：

| 层次 | 说明 | 开发者角色 |
|------|------|------------|
| **Level 1: 提示词** | PromptTemplate、Example Selector | 所有开发者 |
| **Level 2: 模型** | LLM、ChatModel、Embeddings | 所有开发者 |
| **Level 3: 链** | LLMChain、SequentialChain | 应用开发者 |
| **Level 4: Agent** | Agent + Tools | 高级开发者 |

---

## 2. LangChain表达式语言（LCEL）

### 2.1 什么是LCEL

**LCEL**（LangChain Expression Language，LangChain表达式语言）是LangChain从v0.2版本开始引入的声明式链式调用语法。它允许开发者以一种直观、组合式的方式构建复杂的LLM工作流。

LCEL的核心思想是：**一切皆为Runnable**。每个LangChain组件（Model、Prompt、Memory等）都实现了统一的`Runnable`接口，支持`.invoke()`、`.batch()`、`.stream()`等调用方式，并且可以像管道一样用`|`操作符串联起来。

**LCEL的优势**：

| 优势 | 说明 |
|------|------|
| **简洁直观** | 用`|`操作符替代嵌套函数调用 |
| **统一接口** | 所有组件共享相同的调用方式 |
| **惰性执行** | 链式调用只在真正需要结果时才执行 |
| **异步支持** | 原生支持异步操作，易于部署 |
| **流式输出** | 支持流式token返回，用户体验更好 |
| **可追溯** | 便于调试和监控每个环节 |

### 2.2 LCEL基础语法

LCEL的语法核心是**管道操作符**`|`。它的语义类似于Unix管道：将左侧的输出传递给右侧作为输入。

**基础语法结构**：

$$Chain_{LCEL} = Component_1 | Component_2 | Component_3 | \dots | Component_N$$

```python
# 简单LCEL链：Prompt → Model
chain = prompt | model

# 等价的传统写法
# chain = LLMChain(prompt=prompt, llm=model)
```

**invoke调用**：

```python
# 同步调用
result = chain.invoke({"输入变量": "值"})

# 异步调用
result = await chain.ainvoke({"输入变量": "值"})

# 流式调用（逐token返回）
for token in chain.stream({"输入变量": "值"}):
    print(token, end="", flush=True)
```

### 2.3 链式调用详解

#### 2.3.1 简单链

最简单的LCEL链只包含一个PromptTemplate和一个Model：

```python
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

# 定义Prompt模板
prompt = PromptTemplate.from_template(
    "请将以下中文翻译成{target_language}：{text}"
)

# 定义模型
model = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)

# 创建链：用 | 连接
chain = prompt | model

# 调用链
result = chain.invoke({
    "target_language": "英文",
    "text": "今天天气真好"
})

print(result)
```

#### 2.3.2 带输出的链

为了更好地处理输出，LCEL推荐使用`Runnable`接口的组件。可以通过`|`连接一个**输出解析器**（Output Parser）：

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI

# 组件定义
prompt = PromptTemplate.from_template(
    "{topic}的三个主要优点是什么？用JSON格式输出"
)
model = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
output_parser = StrOutputParser()  # 输出解析器

# 链：Prompt → Model → OutputParser
chain = prompt | model | output_parser

# 调用
result = chain.invoke({"topic": "人工智能"})
print(result)  # 直接输出字符串，不再是 AIMessage 对象
```

#### 2.3.3 多步骤链

LCEL支持将多个处理步骤串联成链，每个步骤都可以是任意的`Runnable`：

```python
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# 步骤1：生成故事
story_prompt = PromptTemplate.from_template(
    "以{character}为主角，写一个100字以内的冒险故事"
)
story_model = ChatOpenAI(model="gpt-4", temperature=0.9)
story_chain = story_prompt | story_model | StrOutputParser()

# 步骤2：翻译故事
translate_prompt = PromptTemplate.from_template(
    "将以下故事翻译成{language}：\n{story}"
)
translate_chain = translate_prompt | ChatOpenAI(model="gpt-4") | StrOutputParser()

# 组合链：先生成故事，再翻译
full_chain = story_chain | (lambda x: {"story": x}) | translate_chain

# 调用
result = full_chain.invoke({
    "character": "一只勇敢的小猫",
    "language": "英文"
})
print(result)
```

### 2.4 LCEL内置方法

LCEL链除了`.invoke()`之外，还提供了多种调用方式：

| 方法 | 说明 | 适用场景 |
|------|------|----------|
| `.invoke(input)` | 同步单次调用 | 批量不敏感场景 |
| `.batch(inputs)` | 同步批量调用 | 离线批量处理 |
| `.stream(input)` | 流式调用 | 需要实时反馈的对话 |
| `.ainvoke(input)` | 异步单次调用 | 高并发服务 |
| `.abatch(inputs)` | 异步批量调用 | 生产环境部署 |

```python
# 批量调用
inputs = [
    {"topic": "机器学习"},
    {"topic": "深度学习"},
    {"topic": "强化学习"}
]
results = chain.batch(inputs)

# 流式调用（适合聊天机器人）
for chunk in chain.stream({"topic": "量子计算"}):
    print(chunk, end="", flush=True)
```

### 2.5 LCEL与Runnable接口

LCEL的每个组件都实现了`Runnable`接口，这保证了它们可以被统一组合。`Runnable`接口定义如下：

| 方法 | 说明 |
|------|------|
| `.invoke(input)` | 单次同步调用 |
| `.ainvoke(input)` | 单次异步调用 |
| `.batch(inputs)` | 批量同步调用 |
| `.abatch(inputs)` | 批量异步调用 |
| `.stream(input)` | 流式调用 |
| `.astream(input)` | 异步流式调用 |
| `.bind(**kwargs)` | 绑定固定参数 |

**自定义Runnable**：

```python
from langchain_core.runnables import RunnableLambda

# 使用 RunnableLambda 将普通函数转为 Runnable
def extract_keywords(text: str) -> list:
    """从文本中提取关键词"""
    keywords = [word.strip() for word in text.split() if len(word) > 2]
    return keywords

# 将函数包装为Runnable
keyword_extractor = RunnableLambda(extract_keywords)

# 在链中使用
chain = prompt | model | output_parser | keyword_extractor
result = chain.invoke({"topic": "人工智能"})
# result 现在是 list 类型
```

---

## 3. Prompt模板

### 3.1 PromptTemplate

`PromptTemplate`是LangChain中用于生成文本提示词的基础模板。它通过变量占位符（用`{}`表示）实现动态内容的注入。

**基础用法**：

```python
from langchain_core.prompts import PromptTemplate

# 方式1：直接构建
prompt = PromptTemplate.from_template(
    "请写一首关于{topic}的诗，要求：{style}"
)

# 方式2：通过构造函数
prompt = PromptTemplate(
    input_variables=["topic", "style"],
    template="请写一首关于{topic}的诗，要求：{style}"
)

# 使用模板生成Prompt
result = prompt.format(topic="春天", style="现代诗风格，押韵")
print(result)
# 输出：请写一首关于春天的诗，要求：现代诗风格，押韵
```

**PromptTemplate的常用参数**：

| 参数 | 说明 | 示例 |
|------|------|------|
| `template` | 模板字符串 | `"请翻译成{lang}：{text}"` |
| `input_variables` | 输入变量列表 | `["lang", "text"]` |
| `partial_variables` | 部分填充的变量 | `{"format": "JSON"}` |
| `template_format` | 模板格式 | `"f-string"`（默认）或`"jinja2"` |

**部分变量填充**：

```python
# 有时候需要先填充部分变量，后续再填充其余变量
prompt = PromptTemplate.from_template(
    "请以{author}的身份，写一篇关于{topic}的文章"
)

# 先部分填充author
partial_prompt = prompt.partial(author="鲁迅")

# 后续填充topic
result = partial_prompt.format(topic="人工智能")
print(result)
# 输出：请以鲁迅的身份，写一篇关于人工智能的文章
```

### 3.2 ChatPromptTemplate

`ChatPromptTemplate`是用于聊天模型的提示模板。它与`PromptTemplate`的区别在于：`ChatPromptTemplate`生成的是**消息列表**（符合Chat API的格式），而`PromptTemplate`生成的是纯文本。

**消息角色类型**：

| 角色 | 说明 | 用途 |
|------|------|------|
| `SystemMessage` | 系统消息 | 定义AI助手的身份和行为 |
| `HumanMessage` | 用户消息 | 用户输入 |
| `AIMessage` | AI消息 | AI的回复 |

**基础用法**：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

# 方式1：简洁写法
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的{profession}，用专业但易懂的语言回答问题。"),
    ("human", "你好，请介绍一下{topic}")
])

# 使用模板
messages = prompt.format_messages(
    profession="软件工程师",
    topic="设计模式"
)

# messages 是一个消息列表
for msg in messages:
    print(f"[{msg.type}]: {msg.content}")
```

**方式2：使用消息类显式构造**：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="你是一个乐于助人的AI助手。"),
    HumanMessage(content="请问{question}？"),
    AIMessage(content="这是之前的回复。"),
    HumanMessage(content="追问：{follow_up}")
])

# 生成消息
messages = prompt.format_messages(
    question="什么是LLM",
    follow_up="它和深度学习有什么关系"
)

for msg in messages:
    print(f"[{msg.type}]: {msg.content}")
```

### 3.3 FewShotPromptTemplate

`FewShotPromptTemplate`用于实现少样本学习（Few-shot Learning）。它通过在Prompt中插入示例，帮助模型理解任务模式。

**基础用法**：

```python
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import OpenAI

# 定义示例（Few-shot Examples）
examples = [
    {
        "input": "今天天气真好",
        "output": "正向"
    },
    {
        "input": "这个产品太让人失望了",
        "output": "负向"
    },
    {
        "input": "会议室在二楼",
        "output": "中性"
    }
]

# 示例模板
example_prompt = PromptTemplate.from_template(
    "文本：{input}\n情感：{output}"
)

# FewShot模板
few_shot_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=example_prompt,
    prefix="请判断以下文本的情感类别（正向/负向/中性）：",
    suffix="文本：{input}\n情感：",
    input_variables=["input"]
)

# 使用模板
result = few_shot_prompt.format(input="太开心了！")
print(result)
```

---

## 4. Chains

### 4.1 LLMChain

`LLMChain`是LangChain最基础的链，也是其他高级链的构建块。它将PromptTemplate和LLM（或其他ChatModel）组合在一起，形成一个完整的"输入→Prompt填充→LLM调用→输出"的流程。

**基础结构**：

```
LLMChain
├── PromptTemplate（提示模板）
├── LLM / ChatModel（模型）
└── OutputParser?（可选，输出解析器）
```

**基础用法**：

```python
from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate

# 定义Prompt模板
prompt = PromptTemplate.from_template(
    "{product}的三大优点是什么？"
)

# 定义LLM
llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)

# 创建LLMChain
chain = LLMChain(llm=llm, prompt=prompt)

# 调用链
result = chain.invoke({"product": "智能手机"})
print(result)
# 输出：{'product': '智能手机', 'text': '智能手机的三大优点是...'}
```

**LLMChain的返回值**：

`LLMChain`返回的是一个字典，包含输入变量和输出文本：

```python
result = chain.invoke({"product": "电动汽车"})
# {
#     "product": "电动汽车",
#     "text": "电动汽车的三大优点是：\n1. 环保...\n2. 经济...\n3. 性能..."
# }
```

### 4.2 SequentialChain

`SequentialChain`（顺序链）用于将多个Chain按顺序执行，前一个Chain的输出会作为后一个Chain的输入的一部分。

LangChain提供了两种顺序链：

| 类型 | 说明 | 使用场景 |
|------|------|----------|
| `SequentialChain` | 通用顺序链，支持多个输入输出 | 复杂多步骤流程 |
| `SimpleSequentialChain` | 简化版，每个链只有一个输入和一个输出 | 线性步骤链 |

**SimpleSequentialChain（单输入单输出）**：

```python
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, SimpleSequentialChain
from langchain_core.prompts import PromptTemplate

# 步骤1：根据主题生成故事
story_prompt = PromptTemplate.from_template(
    "以{topic}为主题，写一个50字以内的小故事"
)
story_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4", temperature=0.9),
    prompt=story_prompt
)

# 步骤2：翻译故事
translate_prompt = PromptTemplate.from_template(
    "将以下故事翻译成{lang}：\n{story}"
)
translate_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4", temperature=0.7),
    prompt=translate_prompt
)

# 创建顺序链
chain = SimpleSequentialChain(
    chains=[story_chain, translate_chain],
    verbose=True  # 打印中间步骤
)

# 调用
result = chain.invoke({
    "topic": "勇气",
    "lang": "英文"
})
print(result)
# {'output': 'A young rabbit...'}
```

**SequentialChain（多输入多输出）**：

```python
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain, SequentialChain
from langchain_core.prompts import PromptTemplate

# 步骤1：生成产品名称和口号
generation_prompt = PromptTemplate.from_template(
    "为一款{product_type}产品起一个创意的名称和口号。\n"
    "输出格式：\n名称：xxx\n口号：xxx"
)
generation_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4", temperature=0.8),
    prompt=generation_prompt,
    output_key="name_slogan"  # 指定输出变量的key
)

# 步骤2：根据产品名称和口号写营销文案
marketing_prompt = PromptTemplate.from_template(
    "产品名称：{name}\n产品口号：{slogan}\n"
    "请写一段100字的营销文案"
)
# 注意：需要从第一步的输出中提取name和slogan
marketing_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4", temperature=0.7),
    prompt=marketing_prompt,
    output_key="marketing_text"
)

# 创建顺序链
chain = SequentialChain(
    chains=[generation_chain, marketing_chain],
    input_variables=["product_type"],  # 最开始的输入变量
    output_variables=["name_slogan", "marketing_text"],  # 最终输出变量
    verbose=True
)

# 调用
result = chain.invoke({"product_type": "智能手表"})
print(result)
```

### 4.3 RouterChain

`RouterChain`是一种高级Chain，它能够根据输入动态选择下一个处理Chain。这在构建需要处理多种任务类型的应用中非常有用，例如智能客服系统。

**RouterChain的组成**：

```
RouterChain
├── RouteChain（路由链）：决定使用哪个子链
├── default_chain（默认链）：当没有路由匹配时使用
└── destination_chains（目标链）：实际执行任务的各种子链
```

**使用场景示例**：

```python
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.chains.router import MultiPromptChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 定义多个目标链的Prompt模板
biology_template = "你是一位生物学专家。请回答以下生物学问题：\n\n问题：{question}"
math_template = "你是一位数学家。请回答以下数学问题：\n\n问题：{question}"
history_template = "你是一位历史学家。请回答以下历史问题：\n\n问题：{question}"

# 创建各目标链
biology_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4"),
    prompt=PromptTemplate.from_template(biology_template),
    output_parser=StrOutputParser()
)

math_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4"),
    prompt=PromptTemplate.from_template(math_template),
    output_parser=StrOutputParser()
)

history_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4"),
    prompt=PromptTemplate.from_template(history_template),
    output_parser=StrOutputParser()
)

# 路由链的Prompt（决定将问题路由到哪个链）
router_template = """
根据用户的问题，判断应该使用哪个专家链来回答。

可用链：
- biology：生物学问题
- math：数学问题
- history：历史问题

问题：{question}

只输出链的名称（如biology/math/history），不要其他内容。
"""

router_chain = LLMChain(
    llm=ChatOpenAI(model="gpt-4"),
    prompt=PromptTemplate.from_template(router_template),
    output_parser=StrOutputParser()
)

# 创建多路由链
chain = MultiPromptChain(
    router_chain=router_chain,
    destination_chains={
        "biology": biology_chain,
        "math": math_chain,
        "history": history_chain
    },
    default_chain=LLMChain(
        llm=ChatOpenAI(model="gpt-4"),
        prompt=PromptTemplate.from_template("请礼貌地回答：{question}"),
        output_parser=StrOutputParser()
    ),
    verbose=True
)

# 测试
result1 = chain.invoke({"question": "光合作用是如何进行的？"})
print(result1)

result2 = chain.invoke({"question": "1+1等于多少？"})
print(result2)
```

---

## 5. Agents

### 5.1 Agent概述

**Agent**（智能体）是LangChain中能够**自主决策**的组件。与固定流程的Chain不同，Agent可以根据输入动态决定：
- 是否需要调用工具
- 调用哪个工具
- 工具调用的参数是什么
- 何时结束执行

**Agent vs Chain**：

| 特性 | Chain | Agent |
|------|-------|-------|
| 执行流程 | 固定，预先定义 | 动态，由Agent决定 |
| 工具使用 | 不支持 | 支持 |
| 决策能力 | 无 | 有 |
| 适用场景 | 固定流程任务 | 需要判断的复杂任务 |

**Agent的核心循环**：

```
输入 → 推理(Reasoning) → 行动(Action) → 观察(Observation) → 推理 → ...
```

### 5.2 Agent类型

LangChain支持多种类型的Agent，每种Agent有不同的决策机制：

| Agent类型 | 说明 | 适用场景 |
|-----------|------|----------|
| **zero-shot-react** | 基于ReAct框架，零样本决策 | 通用任务 |
| **conversational-react** | 对话场景的ReAct Agent | 聊天机器人 |
| **chat-zero-shot-react** | 基于ChatModel的ReAct | 现代应用 |
| **self-ask-with-search** | 自我提问+搜索 | 需要搜索的任务 |

**ReAct框架**（Reasoning + Acting）：

ReAct是Agent最常用的决策框架，核心思想是交替进行**推理**和**行动**：

```
Thought: 我需要思考下一步做什么
Action: 执行某个动作（如调用工具）
Observation: 观察动作的结果
...（重复直到得到答案）
```

### 5.3 Tool的使用

**Tool**（工具）是Agent进行决策后执行的具体操作。LangChain内置了多种常用工具，也支持自定义工具。

**内置工具示例**：

| 工具 | 说明 | 用途 |
|------|------|------|
| `search` | 网络搜索 | 获取实时信息 |
| `wikipedia` | 维基百科查询 | 百科知识检索 |
| `python_repl` | Python解释器 | 数学计算 |
| `ddg-search` | DuckDuckGo搜索 | 免API搜索 |

**自定义Tool**：

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# 定义一个自定义工具：计算字符串长度
def get_string_length(text: str) -> int:
    """获取字符串的长度"""
    return len(text)

def reverse_text(text: str) -> str:
    """反转字符串"""
    return text[::-1]

# 将函数包装为Tool
tools = [
    Tool(
        name="get_length",
        func=get_string_length,
        description="获取输入字符串的长度，返回一个整数"
    ),
    Tool(
        name="reverse",
        func=reverse_text,
        description="反转输入的字符串"
    )
]

# 创建Agent
model = ChatOpenAI(model="gpt-4", temperature=0)

# Agent使用的Prompt（包含工具描述）
prompt = PromptTemplate.from_template("""你是一个智能助手，可以使用以下工具回答问题。

可用工具：
{tools}

请用以下格式回答：

问题：输入的问题
思考：你的思考过程
行动：工具名称
行动输入：工具的输入参数
观察：工具返回的结果
...（重复以上步骤直到完成）
最终答案：{input}
""")

# 创建Agent
agent = create_react_agent(model, tools, prompt)

# 创建Agent执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5  # 最多执行5步
)

# 运行Agent
result = agent_executor.invoke({"input": "'LangChain'这个单词有几个字母？"})
print(result)
```

### 5.4 完整Agent示例：带搜索的问答助手

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.tools.ddg_search import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# 创建搜索工具
search_tool = DuckDuckGoSearchRun()

# 包装为LangChain Tool格式
tools = [
    Tool(
        name="search",
        func=search_tool.invoke,
        description="当你需要搜索网络信息时使用此工具。输入应该是搜索查询字符串。"
    )
]

# 创建模型
model = ChatOpenAI(model="gpt-4", temperature=0)

# Agent的Prompt
prompt = PromptTemplate.from_template("""你是一个智能问答助手，可以通过搜索网络来获取最新、最准确的信息。

## 你的能力
- 你可以搜索网络来回答问题
- 你可以一步一步思考
- 你必须基于搜索结果来回答

## 回答格式
请按以下格式回答：

问题：{input}

思考：首先判断是否需要搜索，如果需要，我应该搜索什么关键词？

行动：search
行动输入：[搜索关键词]
观察：[搜索结果的摘要]

最终答案：[综合搜索结果的回答]

## 规则
1. 如果问题可以用知识回答，可以直接回答
2. 如果需要最新信息或有疑问，必须先搜索
3. 回答要引用搜索结果中的关键信息
""")

# 创建Agent
agent = create_react_agent(model, tools, prompt)

# 创建执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=3
)

# 运行
result = agent_executor.invoke({
    "input": "2024年诺贝尔物理学奖得主是谁？"
})
print(result)
```

### 5.5 Tool使用注意事项

| 注意事项 | 说明 |
|----------|------|
| **Tool数量控制** | Tool数量过多会导致Agent决策困难，建议不超过10个 |
| **描述要准确** | Tool的description直接决定Agent是否选择它 |
| **错误处理** | Agent执行可能出错，需要设置`max_iterations`和`handle_parsing_errors` |
| **避免无限循环** | 设置最大迭代次数，防止Agent陷入死循环 |

```python
# 错误处理配置
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,  # 自动处理解析错误
    early_stopping_method="force"  # 强制停止方法
)
```

---

## 6. Memory

### 6.1 Memory概述

**Memory**（记忆）为LLM应用提供持久化对话上下文的能力。没有Memory的Agent就像金鱼一样，每次对话都是全新的；有了Memory，Agent才能真正理解对话的连续性。

**为什么需要Memory？**：

| 问题 | 说明 | Memory解决方案 |
|------|------|---------------|
| **上下文丢失** | 每次请求都是独立上下文 | 保存历史对话 |
| **Token浪费** | 重复传递历史信息 | 压缩、摘要历史 |
| **体验差** | 用户需要重复说明背景 | 保持会话连贯性 |

### 6.2 ConversationBufferMemory

`ConversationBufferMemory`是最简单的Memory实现，它将完整的对话历史存储在内存中，每次调用时将全部历史作为上下文传递给模型。

**基础用法**：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

# 初始化模型和Prompt
model = ChatOpenAI(model="gpt-4", temperature=0.7)
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个乐于助人的AI助手。"),
    MessagesPlaceholder(variable_name="history"),  # 对话历史占位符
    ("human", "{input}")
])

# 创建Memory
memory = ConversationBufferMemory(
    memory_key="history",  # 与MessagesPlaceholder的variable_name对应
    return_messages=True   # 返回消息对象而非字符串
)

# 创建链（包含Memory）
chain = LLMChain(
    llm=model,
    prompt=prompt,
    memory=memory,
    verbose=True
)

# 第一轮对话
result1 = chain.invoke({"input": "我叫张三，请记住我的名字"})
print(result1)

# 第二轮对话
result2 = chain.invoke({"input": "我叫什么名字？"})
print(result2)  # 应该能记住"张三"
```

### 6.3 ConversationSummaryMemory

`ConversationSummaryMemory`在每次对话后将历史信息压缩成摘要，适合**长对话**场景，避免超出模型的上下文窗口限制。

**基础用法**：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationSummaryMemory

# 初始化模型
model = ChatOpenAI(model="gpt-4", temperature=0.7)

# 创建Memory
memory = ConversationSummaryMemory(
    memory_key="history",
    return_messages=True,
    llm=model  # 需要LLM来生成摘要
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个乐于助人的AI助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# 创建链
chain = LLMChain(
    llm=model,
    prompt=prompt,
    memory=memory
)

# 多轮对话
chain.invoke({"input": "我叫李明，是一名软件工程师。"})
chain.invoke({"input": "我从事什么工作？"})
chain.invoke({"input": "我叫什么名字？"})

# 查看当前的摘要记忆
print(memory.buffer)  # 对话历史已被压缩为摘要
```

### 6.4 对话Memory的选用建议

| Memory类型 | 优点 | 缺点 | 适用场景 |
|------------|------|------|----------|
| **ConversationBufferMemory** | 保留完整对话 | Token消耗大 | 短对话（<10轮） |
| **ConversationSummaryMemory** | 节省Token | 细节可能丢失 | 长对话 |
| **ConversationBufferWindowMemory** | 保留最近N轮 | 更早信息丢失 | 中等长度对话 |

**LCEL中集成Memory**：

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain

# LCEL风格集成Memory
model = ChatOpenAI(model="gpt-4")
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# 在LCEL链中使用
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个专业的AI助手。"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# 手动实现带Memory的链
def get_response(question: str) -> str:
    # 加载历史
    chat_history = memory.load_memory_variables({
    chat_history = memory.load_memory_variables({})["chat_history"]
    
    # 调用链
    response = chain.invoke({
        "question": question,
        "chat_history": chat_history
    })
    
    # 保存对话
    memory.save_context(
        {"question": question},
        {"answer": response["answer"]}
    )
    
    return response["answer"]
```

---

## 7. 代码实战

### 7.1 环境准备

```bash
# 安装 LangChain 核心包
pip install langchain langchain-core langchain-community

# 安装 LangChain OpenAI 集成
pip install langchain-openai

# 安装其他常用依赖
pip install duckduckgo-search wikipedia python-repl  # Agent工具
pip install faiss-cpu  # 向量数据库（可选）
```

### 7.2 基础LLMChain构建

```python
#!/usr/bin/env python3
# examples/basic_llm_chain.py
"""
基础LLMChain构建实战
演示如何用LangChain构建一个简单的翻译链
"""

import os


class BasicLLMChainDemo:
    """
    基础LLMChain演示类
    展示LangChain的核心用法
    """
    def __init__(self, provider="deepseek", model=None):
        """
        初始化LLMChain演示

        参数:
            provider: API提供商 ('openai', 'deepseek')
            model: 模型名称
        """
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model_name = model or self.default_models.get(provider, "gpt-4")

        # 根据不同provider初始化客户端
        if provider == "openai":
            from langchain_openai import OpenAI
            self.llm = OpenAI(model=self.model_name, temperature=0.7)
        elif provider == "deepseek":
            from langchain_openai import OpenAI
            self.llm = OpenAI(
                model=self.model_name,
                temperature=0.7,
                base_url="https://api.deepseek.com",
                api_key=os.getenv("DEEPSEEK_API_KEY")
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        print(f"[INFO] LLMChain演示初始化: {provider}/{self.model_name}")

    def build_translation_chain(self):
        """
        构建翻译链

        返回:
            LLMChain: 翻译链
        """
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain

        # 定义翻译Prompt模板
        prompt = PromptTemplate.from_template(
            "请将以下中文翻译成{target_language}，只输出翻译结果：\n{text}"
        )

        # 创建LLMChain
        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain

    def build_summarization_chain(self):
        """
        构建摘要链

        返回:
            LLMChain: 摘要链
        """
        from langchain.prompts import PromptTemplate
        from langchain.chains import LLMChain

        prompt = PromptTemplate.from_template(
            "请将以下文章压缩成100字以内的摘要：\n{article}"
        )

        chain = LLMChain(llm=self.llm, prompt=prompt)
        return chain

    def run_translation(self):
        """运行翻译演示"""
        print("=" * 60)
        print("翻译链演示")
        print("=" * 60)

        chain = self.build_translation_chain()

        # 翻译任务
        result = chain.invoke({
            "target_language": "英文",
            "text": "今天天气真好，适合出去散步。"
        })

        print(f"\n原文：今天天气真好，适合出去散步。")
        print(f"翻译：{result['text'].strip()}")

        return result

    def run_summarization(self):
        """运行摘要演示"""
        print("\n" + "=" * 60)
        print("摘要链演示")
        print("=" * 60)

        chain = self.build_summarization_chain()

        article = """
        人工智能（AI）是当前科技领域最热门的话题之一。它涵盖了机器学习、
        深度学习、自然语言处理等多个分支。近年来，随着大语言模型的发展，
        AI在自然语言理解方面取得了突破性进展。大语言模型如GPT、BERT等，
        已经在客服、内容创作、代码编写等领域得到广泛应用。未来，随着技术
        的不断进步，AI有望在更多领域发挥重要作用，包括医疗诊断、自动驾驶、
        科学研究等。同时，AI伦理和安全问题也日益受到关注。
        """

        result = chain.invoke({"article": article})

        print(f"\n原文（{len(article)}字）：\n{article}")
        print(f"\n摘要：{result['text'].strip()}")

        return result

    def run_lcel_chain(self):
        """
        使用LCEL语法构建链（现代写法）
        """
        print("\n" + "=" * 60)
        print("LCEL语法链演示")
        print("=" * 60)

        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        # 使用LCEL语法构建链
        chain = (
            PromptTemplate.from_template(
                "{product}的三大优点是什么？简洁回答。"
            )
            | self.llm
            | StrOutputParser()
        )

        # 调用链
        result = chain.invoke({"product": "电动汽车"})

        print(f"\n问题：电动汽车的三大优点是什么？")
        print(f"回答：{result}")

        return result


def demo_basic_chain():
    """
    基础链演示入口
    """
    print("=" * 60)
    print("LangChain 基础LLMChain实战")
    print("=" * 60)

    # 初始化（使用DeepSeek作为示例）
    demo = BasicLLMChainDemo(provider="deepseek")

    # 1. 翻译链
    demo.run_translation()

    # 2. 摘要链
    demo.run_summarization()

    # 3. LCEL链
    demo.run_lcel_chain()


if __name__ == "__main__":
    demo_basic_chain()
```

### 7.3 RAG链实现

```python
#!/usr/bin/env python3
# examples/rag_chain.py
"""
RAG（检索增强生成）链实战
演示如何使用LangChain构建一个基于私有知识的问答系统
"""

import os


class RAGChainDemo:
    """
    RAG链演示类
    展示如何将文档检索与大模型结合
    """
    def __init__(self, provider="deepseek", model=None):
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model_name = model or self.default_models.get(provider, "gpt-4")

        if provider == "openai":
            from langchain_openai import OpenAI, OpenAIEmbeddings
            self.llm = OpenAI(model=self.model_name, temperature=0)
            self.embeddings = OpenAIEmbeddings()
        elif provider == "deepseek":
            from langchain_openai import OpenAI, OpenAIEmbeddings
            self.llm = OpenAI(
                model=self.model_name,
                temperature=0,
                base_url="https://api.deepseek.com",
                api_key=os.getenv("DEEPSEEK_API_KEY")
            )
            self.embeddings = OpenAIEmbeddings(
                base_url="https://api.deepseek.com",
                api_key=os.getenv("DEEPSEEK_API_KEY")
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        print(f"[INFO] RAG链演示初始化: {provider}/{self.model_name}")

    def build_rag_chain(self, documents):
        """
        构建RAG链

        参数:
            documents: 文档列表，每个文档为dict，包含page_content和metadata

        返回:
            RAG链对象
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import FAISS
        from langchain.chains import RetrievalQA
        from langchain.prompts import PromptTemplate

        # 1. 文档分割
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,      # 每个chunk的大小
            chunk_overlap=50,    # chunk之间的重叠
            length_function=len
        )

        # 从文档字符串创建docs
        docs = []
        for doc in documents:
            splits = text_splitter.split_text(doc["page_content"])
            for split in splits:
                docs.append({
                    "page_content": split,
                    "metadata": doc.get("metadata", {})
                })

        # 2. 创建向量存储
        # 将文本列表和元数据列表分开
        texts = [d["page_content"] for d in docs]
        metadatas = [d["metadata"] for d in docs]

        vectorstore = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas
        )

        # 3. 创建检索器
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 2}  # 返回最相关的2个chunks
        )

        # 4. 定义Prompt模板
        prompt = PromptTemplate.from_template(
            """基于以下参考资料回答用户问题。如果资料中没有相关信息，
请说明"根据提供的资料无法回答这个问题"。

参考资料：
{context}

用户问题：{question}

回答要求：
1. 只基于提供的参考资料回答
2. 回答要清晰、有条理
3. 列出参考资料中支持你回答的关键引用
"""
        )

        # 5. 创建RAG链
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",  # 将所有检索内容拼接
            retriever=retriever,
            return_source_documents=True,  # 返回源文档
            chain_type_kwargs={"prompt": prompt}
        )

        return chain

    def run_qa(self):
        """
        运行问答演示
        """
        print("=" * 60)
        print("RAG 问答系统演示")
        print("=" * 60)

        # 模拟公司知识库文档
        documents = [
            {
                "page_content": """
                公司名称：科技创新有限公司
                成立时间：2015年
                主要业务：人工智能软件开发
                总部地址：北京市海淀区
                """,
                "metadata": {"source": "公司简介"}
            },
            {
                "page_content": """
                产品A是一款智能客服系统，具有以下特点：
                1. 支持多轮对话
                2. 支持知识库问答
                3. 支持人工转接
                4. 支持数据分析
                定价：基础版免费，专业版99元/月
                """,
                "metadata": {"source": "产品手册"}
            },
            {
                "page_content": """
                售后服务政策：
                1. 7天无理由退款
                2. 24小时在线客服
                3. 每年2次免费培训
                4. 终身免费升级
                联系方式：400-123-4567
                """,
                "metadata": {"source": "售后政策"}
            }
        ]

        # 构建RAG链
        chain = self.build_rag_chain(documents)

        # 问答测试
        questions = [
            "公司的全称是什么？在哪里？",
            "产品A有哪些功能？价格如何？",
            "售后服务包括哪些内容？"
        ]

        for q in questions:
            print(f"\n问题：{q}")
            result = chain.invoke({"query": q})
            print(f"回答：{result['result']}")
            print(f"参考来源：{[d.metadata['source'] for d in result['source_documents']]}")


def demo_rag():
    """
    RAG演示入口
    """
    demo = RAGChainDemo(provider="deepseek")
    demo.run_qa()


if __name__ == "__main__":
    demo_rag()
```

### 7.4 对话Agent实现

```python
#!/usr/bin/env python3
# examples/conversational_agent.py
"""
对话Agent实战
演示如何使用LangChain构建一个带有Memory的对话Agent
"""

import os


class ConversationalAgentDemo:
    """
    对话Agent演示类
    展示如何构建支持工具调用和多轮对话的Agent
    """
    def __init__(self, provider="deepseek", model=None):
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model_name = model or self.default_models.get(provider, "gpt-4")

        if provider == "openai":
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model=self.model_name, temperature=0)
        elif provider == "deepseek":
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=self.model_name,
                temperature=0,
                base_url="https://api.deepseek.com",
                api_key=os.getenv("DEEPSEEK_API_KEY")
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        print(f"[INFO] 对话Agent演示初始化: {provider}/{self.model_name}")

    def build_tools(self):
        """
        定义Agent可用的工具

        返回:
            list: Tool列表
        """
        from langchain.agents import Tool
        from langchain_community.tools.ddg_search import DuckDuckGoSearchRun

        # 网络搜索工具
        search_tool = DuckDuckGoSearchRun()

        # 自定义工具：计算器
        def calculator(expression: str) -> str:
            """执行数学计算"""
            try:
                result = eval(expression)
                return f"计算结果：{result}"
            except Exception as e:
                return f"计算错误：{e}"

        # 自定义工具：获取当前时间
        def get_current_time() -> str:
            """获取当前日期和时间"""
            from datetime import datetime
            now = datetime.now()
            return now.strftime("%Y年%m月%d日 %H:%M:%S")

        tools = [
            Tool(
                name="search",
                func=search_tool.invoke,
                description="当你需要搜索网络信息或最新新闻时使用此工具。输入应该是搜索查询字符串。"
            ),
            Tool(
                name="calculator",
                func=calculator,
                description="执行数学计算。输入应该是一个数学表达式，如 '2+3*5' 或 '10**2'。"
            ),
            Tool(
                name="get_time",
                func=get_current_time,
                description="获取当前日期和时间。无需输入参数。"
            )
        ]

        return tools

    def build_agent_with_memory(self):
        """
        构建带Memory的对话Agent

        返回:
            AgentExecutor: Agent执行器
        """
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        from langchain.memory import ConversationBufferMemory

        # 创建工具
        tools = self.build_tools()

        # 创建Memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # 创建Agent的Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能助手，名为小E。你有以下能力：
1. 回答各种问题
2. 搜索网络获取最新信息
3. 执行数学计算
4. 获取当前时间

请用友好、专业的方式回答。如果需要使用工具，必须按照指定格式调用。"""),
            MessagesPlaceholder(variable_name="chat_history"),  # 对话历史
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")  # Agent工作区
        ])

        # 创建Agent
        agent = create_react_agent(self.llm, tools, prompt)

        # 创建执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.memory,  # 绑定Memory
            verbose=True,
            max_iterations=5
        )

        return agent_executor

    def chat_loop(self):
        """
        对话循环
        """
        print("=" * 60)
        print("对话Agent演示（输入 'quit' 退出）")
        print("=" * 60)

        agent = self.build_agent_with_memory()

        while True:
            user_input = input("\n你：")
            if user_input.lower() in ["quit", "退出", "q"]:
                print("再见！")
                break

            result = agent.invoke({"input": user_input})
            print(f"\n小E：{result['output']}")

            # 查看Memory状态
            history = self.memory.load_memory_variables({})["chat_history"]
            print(f"\n[调试] 当前对话轮数：{len([m for m in history if hasattr(m, 'type') and m.type == 'human'])}")


def demo_conversational_agent():
    """
    对话Agent演示入口
    """
    demo = ConversationalAgentDemo(provider="deepseek")
    demo.chat_loop()


if __name__ == "__main__":
    # 注意：此演示需要交互式输入
    # 为了非交互式演示，这里只打印说明
    print("=" * 60)
    print("对话Agent演示说明")
    print("=" * 60)
    print("""
运行此演示将启动一个交互式对话循环。

Agent具备以下能力：
1. 回答通用问题
2. 使用DuckDuckGo搜索网络
3. 执行数学计算
4. 获取当前时间
5. 记住对话历史

退出命令：quit / 退出 / q
""")
    # demo_conversational_agent()
```

---

## 8. 练习题

### 基础题

**1. 选择题**

1.1 LangChain的核心设计思想"一切皆为Runnable"指的是：
- A. 所有组件都可以被运行
- B. 所有组件都实现了统一的Runnable接口，可以统一调用和组合
- C. LangChain只能运行Python代码
- D. LangChain不需要其他依赖

1.2 LCEL中管道操作符`|`的作用是：
- A. 逻辑或运算
- B. 将左侧组件的输出作为右侧组件的输入
- C. 创建一个新的变量
- D. 并行执行多个组件

1.3 在LangChain中，`LLMChain`和`SequentialChain`的主要区别是：
- A. LLMChain更快
- B. SequentialChain可以串联多个LLMChain
- C. LLMChain支持Prompt，SequentialChain不支持
- D. 两者没有区别

1.4 Agent的核心循环是：
- A. 输入→输出→结束
- B. 推理→行动→观察→推理
- C. 请求→响应→结束
- D. 加载→执行→保存

1.5 `ConversationSummaryMemory`相比`ConversationBufferMemory`的优势是：
- A. 保留更多细节
- B. 节省Token，适合长对话
- C. 速度更快
- D. 更容易实现

**2. 简答题**

2.1 简述LangChain的核心组件及其作用。

2.2 解释LCEL（LangChain表达式语言）的核心理念。

2.3 说明LLMChain、SequentialChain、RouterChain各自的适用场景。

2.4 描述ReAct框架的工作原理。

2.5 比较三种Memory类型的优缺点及适用场景。

**3. 编程题**

3.1 使用LangChain构建一个翻译链，支持中译英和英译中两种模式。

3.2 使用SequentialChain实现一个"新闻摘要→关键词提取→分类"的处理流程。

### 提高题

**4. 综合题**

4.1 设计一个基于LangChain的智能客服系统架构，包含：Agent、Tool、Memory的使用方案，并说明各组件如何协作。

4.2 比较LCEL与传统LLMChain写法的异同，并说明LCEL的优势。

**5. 实战题**

5.1 使用LangChain和DuckDuckGo搜索工具，实现一个能回答实时问题的Agent。

5.2 实现一个带Memory的多轮对话系统，能够记住用户的个人信息和偏好设置。

---

## 9. 参考答案

### 基础题答案

**1. 选择题**

1.1 **答案：B**
解析：LangChain的核心设计思想是"一切皆为Runnable"，即所有组件（Model、Prompt、Memory等）都实现了统一的`Runnable`接口，支持`.invoke()`、`.stream()`等统一调用方式，便于组合。

1.2 **答案：B**
解析：在LCEL中，管道操作符`|`的作用是将左侧组件的输出作为右侧组件的输入，实现组件间的数据流动，类似Unix管道的语义。

1.3 **答案：B**
解析：`LLMChain`是单个"Prompt→Model"的组合；`SequentialChain`可以串联多个`LLMChain`，让前一个链的输出作为后一个链的输入。

1.4 **答案：B**
解析：Agent的核心循环是"推理(Reasoning)→行动(Action)→观察(Observation)→推理..."，通过不断循环直到任务完成。

1.5 **答案：B**
解析：`ConversationSummaryMemory`在每次对话后将历史压缩成摘要，因此可以节省Token消耗，避免超出模型的上下文窗口限制，适合长对话场景。

**2. 简答题**

2.1 **LangChain核心组件**：

| 组件 | 作用 |
|------|------|
| **Models** | LLM调用封装，支持OpenAI、DeepSeek等多种模型 |
| **Prompts** | Prompt模板管理，支持动态变量注入 |
| **Chains** | 组件串联，将多个步骤组合成工作流 |
| **Agents** | 自主决策，支持工具调用和动态规划 |
| **Memory** | 对话记忆，支持多轮上下文 |
| **Indexes** | 文档处理，支持RAG等场景 |

2.2 **LCEL核心理念**：

LCEL的核心理念是"声明式组合"和"统一Runnable接口"：
- 所有组件实现统一的`Runnable`接口
- 通过`|`操作符实现声明式组合
- 支持惰性执行、异步操作、流式输出
- 让复杂工作流的构建像搭积木一样简单

2.3 **三种Chain的适用场景**：

| Chain类型 | 适用场景 |
|-----------|----------|
| **LLMChain** | 单一Prompt→Model的简单任务 |
| **SequentialChain** | 多步骤顺序执行，前一步输出影响后一步输入 |
| **RouterChain** | 需要根据输入动态选择处理路径 |

2.4 **ReAct框架原理**：

ReAct = Reasoning + Acting，交替进行：
1. **Thought**：思考当前状态，决定下一步
2. **Action**：执行某个动作（如调用工具）
3. **Observation**：观察动作结果
4. 重复直到任务完成

这让Agent能够在"思考"和"行动"之间切换，实现动态决策。

2.5 **Memory类型对比**：

| 类型 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **BufferMemory** | 保留完整对话 | Token消耗大 | 短对话（<10轮） |
| **SummaryMemory** | 节省Token | 细节可能丢失 | 长对话 |
| **WindowMemory** | 平衡两者 | 更早信息丢失 | 中等对话 |

**3. 编程题答案**

3.1 **翻译链实现**：

```python
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# 初始化LLM
llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)

# 中译英链
zh_to_en_prompt = PromptTemplate.from_template(
    "将以下中文翻译成英文：\n{text}"
)
zh_to_en_chain = LLMChain(llm=llm, prompt=zh_to_en_prompt)

# 英译中链
en_to_zh_prompt = PromptTemplate.from_template(
    "Translate the following to Chinese：\n{text}"
)
en_to_zh_chain = LLMChain(llm=llm, prompt=en_to_zh_prompt)

# 使用
result1 = zh_to_en_chain.invoke({"text": "今天天气真好"})
print(result1["text"])  # It's a lovely day today.

result2 = en_to_zh_chain.invoke({"text": "Hello, world!"})
print(result2["text"])  # 你好，世界！
```

3.2 **SequentialChain流程**：

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, SequentialChain

llm = ChatOpenAI(model="gpt-4", temperature=0)

# 步骤1：生成新闻摘要
summary_prompt = PromptTemplate.from_template(
    "请为以下新闻生成100字以内的摘要：\n{news}"
)
summary_chain = LLMChain(
    llm=llm, prompt=summary_prompt, output_key="summary"
)

# 步骤2：提取关键词
keyword_prompt = PromptTemplate.from_template(
    "从以下摘要中提取5个关键词：\n{summary}"
)
keyword_chain = LLMChain(
    llm=llm, prompt=keyword_prompt, output_key="keywords"
)

# 步骤3：分类
category_prompt = PromptTemplate.from_template(
    "为以下新闻摘要分类（科技/财经/娱乐/体育/其他）：\n{summary}"
)
category_chain = LLMChain(
    llm=llm, prompt=category_prompt, output_key="category"
)

# 串联
chain = SequentialChain(
    chains=[summary_chain, keyword_chain, category_chain],
    input_variables=["news"],
    output_variables=["summary", "keywords", "category"],
    verbose=True
)

result = chain.invoke({
    "news": "某科技公司今日发布了最新款智能手机，配备最新处理器..."
})
```

### 提高题答案

**4. 综合题**

4.1 **智能客服架构设计**：

```
┌─────────────────────────────────────────────────┐
│              智能客服系统架构                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────┐    ┌──────────┐    ┌───────────┐  │
│  │  用户   │───→│  Router  │───→│  Agent    │  │
│  │  输入   │    │  Chain   │    │  + Tools  │  │
│  └─────────┘    └──────────┘    └─────┬─────┘  │
│                                        │        │
│  ┌──────────────┐              ┌──────▼──────┐  │
│  │   Memory     │←─────────────│   LLM       │  │
│  │ (历史记忆)    │              │  (决策+回复) │  │
│  └──────────────┘              └─────────────┘  │
│                                        │        │
│                              ┌─────────▼────────┐ │
│                              │    Tools         │ │
│                              │  - 知识库检索    │ │
│                              │  - 订单查询      │ │
│                              │  - 转人工       │ │
│                              └─────────────────┘ │
└─────────────────────────────────────────────────┘
```

4.2 **LCEL vs 传统LLMChain**：

| 方面 | 传统LLMChain | LCEL |
|------|-------------|------|
| 语法 | `LLMChain(llm, prompt)` | `prompt \| llm` |
| 组合方式 | 嵌套构造函数 | 管道操作符 |
| 输出处理 | 手动解析 | `\| output_parser` |
| 流式支持 | 需额外配置 | `.stream()`原生支持 |
| 调试 | 较困难 | `verbose=True`可追溯 |

LCEL的优势：更简洁、更统一、更好的异步和流式支持。

---

## 总结

本课程学习了LangChain框架的核心知识，包括：

1. **LangChain概述**：理解LangChain的定义、核心组件和架构分层
2. **LCEL表达式语言**：掌握"一切皆为Runnable"的设计理念和管道调用语法
3. **Prompt模板**：学会使用PromptTemplate、ChatPromptTemplate、FewShotPromptTemplate
4. **Chains**：掌握LLMChain、SequentialChain、RouterChain的用法
5. **Agents**：理解Agent的自主决策机制和ReAct框架
6. **Memory**：学会使用ConversationBufferMemory和ConversationSummaryMemory
7. **代码实战**：构建基础链、RAG链、对话Agent

---

**下一步学习：**
- [13-1 LLM基础与大模型概述](../13-1-LLM基础与大模型概述.md)
- [13-2 Prompt Engineering](../13-2-Prompt-Engineering.md)

---

*本课程由 Every Emodied Course 项目组编写 - 2026*
