# 13-2 Prompt Engineering

## 课程说明

| 项目 | 内容 |
|------|------|
| 课程编号 | 13-2 |
| 课程名称 | Prompt Engineering（提示工程） |
| 所属模块 | 13-大模型技术与应用 |
| 难度等级 | ⭐⭐⭐☆☆ |
| 预计学时 | 3小时 |
| 前置知识 | Python基础、大模型基本概念 |

---

## 目录

1. [Prompt工程概述](#1-prompt工程概述)
2. [Prompt基础技巧](#2-prompt基础技巧)
3. [高级Prompt技术](#3-高级prompt技术)
4. [Prompt模式与框架](#4-prompt模式与框架)
5. [代码实战](#5-代码实战)
6. [练习题](#6-练习题)
7. [参考答案](#7-参考答案)

---

## 1. Prompt工程概述

### 1.1 什么是Prompt

**Prompt**（提示）是用户与大语言模型（LLM）交互时输入的文本内容，它引导模型生成特定的输出。在传统机器学习中，模型需要通过大量数据训练来学习任务；而在LLM时代，我们通过精心设计的Prompt来"激发"模型已经学到的知识和能力。

简单来说，Prompt就是**与AI对话的方式**——你如何提问、如何设定角色、如何提供上下文，都直接影响模型的输出质量。

一个完整的Prompt通常包含以下要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| **指令（Instruction）** | 明确告诉模型要做什么 | "请将以下中文翻译成英文" |
| **上下文（Context）** | 提供背景信息，帮助模型理解 | "这是一封商务邮件" |
| **输入数据（Input）** | 具体需要处理的内容 | 实际的文本、问题、数据 |
| **输出格式（Format）** | 期望的输出形式 | "请以JSON格式输出" |
| **示例（Examples）** | Few-shot演示 | 输入→输出的样例对 |

### 1.2 什么是Prompt工程

**Prompt工程**（Prompt Engineering）是研究和优化Prompt设计的一门学科，旨在通过精心设计的提示词来更有效地引导大语言模型完成各种任务。它不需要训练或修改模型参数，而是通过**优化输入文本**来提升模型输出质量。

Prompt工程的核心价值在于：

- **成本效益**：相比模型微调，Prompt工程的成本几乎为零
- **快速迭代**：可以即时测试和优化
- **灵活适应**：同一个模型可以通过不同Prompt适配多种任务
- **能力挖掘**：激发模型已有的潜在能力

### 1.3 Prompt工程的重要性

Prompt工程在LLM应用中扮演着至关重要的角色，原因如下：

**1. 模型能力的"放大器"**

同样的模型，优秀的Prompt可以显著提升输出质量。研究表明，Prompt的细微差别会导致输出结果的巨大差异。

```
Prompt: "写一首诗"
→ 输出: "春眠不觉晓..."（一首普通诗）

Prompt: "以杜甫的写作风格，写一首关于人工智能的七言律诗，要求押韵工整"
→ 输出: "芯片神通不易才..."（更精准、更有意境的诗）
```

**2. 弥补模型局限**

LLM在数学计算、实时信息等方面存在局限，通过精心设计的Prompt可以引导模型进行更好的推理，降低幻觉（Hallucination）风险。

**3. 任务适配的核心手段**

在实际应用中，我们通常不会为每个任务训练一个新模型，而是通过设计不同的Prompt来让同一个模型完成不同任务。Prompt工程是实现LLM实用化的关键技术。

### 1.4 Prompt工程发展历程

| 阶段 | 时间 | 特点 | 代表技术 |
|------|------|------|----------|
| 萌芽期 | 2020-2021 | 简单问答 | 零样本提示 |
| 发展期 | 2022 | 上下文学习兴起 | Few-shot、思维链 |
| 成熟期 | 2023 | 系统化方法论 | CoT、ToT、ReAct |
| 融合期 | 2024-至今 | 与Agent结合 | 工具调用、多步骤推理 |

### 1.5 Prompt质量的影响因素

一个高质量的Prompt通常具备以下特征：

| 特征 | 描述 | 良好示例 | 不良示例 |
|------|------|----------|----------|
| **清晰性** | 指令明确、无歧义 | "请将句子中所有动词改为过去式" | "处理一下这句话" |
| **具体性** | 包含足够的细节 | "写一篇800字的议论文" | "写一篇文章" |
| **结构性** | 格式规范、层次分明 | 带编号的步骤列表 | 混杂在一起的描述 |
| **上下文相关性** | 提供相关背景 | "作为客服，请回复以下投诉" | 直接提问无任何设定 |
| **目标导向** | 明确期望输出 | "以JSON格式返回：{姓名，年龄}" | "告诉我相关信息" |

---

## 2. Prompt基础技巧

### 2.1 清晰明确的指令

清晰性是Prompt设计的首要原则。模糊的指令会导致模型输出不确定或不符合预期。

**核心原则**：
- 使用具体的动词替代模糊的动词
- 明确说明任务范围和边界
- 分解复杂任务为多个简单步骤

```python
# 不良Prompt示例
prompt_bad = "处理一下这些数据"

# 良好Prompt示例
prompt_good = """
请对以下销售数据进行处理：
1. 筛选出销售额超过10000元的记录
2. 按销售日期从新到旧排序
3. 计算每个月的销售总额
4. 以CSV格式输出结果

数据：
日期,商品,销售额
2024-01-01,手机,15000
2024-01-02,电脑,22000
2024-01-03,耳机,5000
"""
```

**常用动词参考**：

| 模糊动词 | 具体动词 |
|----------|----------|
| 处理 | 分析、转换、提取、汇总、筛选 |
| 看看 | 检查、验证、评估、比较 |
| 写 | 创作、生成、编写、制定、回复 |
| 解释 | 说明、阐述、定义、对比、分析 |

### 2.2 结构化输出

通过明确的格式要求，可以让模型输出更易于程序解析或直接使用。

**JSON格式输出**：

```python
prompt_json = """
请分析以下文本的情感，并返回JSON格式结果。

文本：今天天气真好，心情特别舒畅。

要求返回格式：
{
    "sentiment": "正面/负面/中性",
    "confidence": 0.0-1.0之间的置信度,
    "keywords": ["关键词1", "关键词2"],
    "reason": "简短的分析理由"
}
"""
```

**Markdown表格输出**：

```python
prompt_table = """
请比较以下三种编程语言的特点，用Markdown表格输出：

比较维度：学习难度、应用场景、执行效率、社区生态

语言：Python、Java、C++
"""
```

**带编号的列表输出**：

```python
prompt_list = """
请列出学习Python爬虫的5个关键步骤，每个步骤包含：
1. 步骤名称
2. 核心知识点
3. 推荐学习资源（1-2个）

以清晰的编号列表形式呈现。
"""
```

### 2.3 Few-shot示例

**Few-shot Learning**（少样本学习）是指在Prompt中提供少量（通常1-5个）示例，帮助模型理解任务模式。与零样本不同，Few-shot通过示例"示范"了期望的输入-输出对应关系。

**为什么Few-shot有效？**

模型在预训练阶段学到了大量知识，但需要通过示例来激活与当前任务相关的知识子集。Few-shot本质上是一种**隐式的上下文学习**（In-Context Learning）。

**Few-shot示例结构**：

```
示例1：
输入：[具体输入1]
输出：[期望输出1]

示例2：
输入：[具体输入2]
输出：[期望输出2]

示例3：
输入：[具体输入3]
输出：[期望输出3]

现在请处理：
输入：[实际输入]
输出：
```

**实践示例**：

```python
# 零样本（Zero-shot）
prompt_zero = """
请判断以下评论的情感是正向还是负向：

评论："这家餐厅的服务太差了，等了半小时才上菜。"
"""

# 少样本（Few-shot）
prompt_few = """
请判断评论的情感是正向还是负向：

示例1：
评论："味道很棒，下次还会再来！"
情感：正向

示例2：
评论："环境一般，价格偏贵。"
情感：负向

示例3：
评论："性价比很高，推荐！"
情感：正向

现在请判断：
评论："等了半小时才上菜，而且菜都凉了。"
情感：
"""
```

**Few-shot设计技巧**：

| 技巧 | 说明 | 示例 |
|------|------|------|
| 示例多样性 | 覆盖不同类型的输入 | 包含正负例、边界情况 |
| 示例顺序 | 先简单后复杂 | 帮助模型逐步理解 |
| 标签一致性 | 输出标签格式统一 | 始终使用"正向/负向"而非混用 |
| 数量控制 | 通常2-5个示例最佳 | 过多反而分散注意力 |

### 2.4 角色设定技巧

通过设定角色，可以让模型以特定的身份和视角来回答问题，这往往能显著提升回答的质量和专业性。

**基础角色设定**：

```python
prompt_role = """
你是一位经验丰富的Python后端工程师，具有10年开发经验。

请解释什么是Python中的装饰器（Decorator），
要求：
1. 用通俗易懂的语言解释概念
2. 提供至少2个实际代码示例
3. 说明常见的使用场景
"""
```

**带约束的角色设定**：

```python
prompt_role_constrained = """
你是一位严谨的大学计算机教授，在教授学生时注重理论与实践结合。

请讲解"面向对象编程"的三大特性（封装、继承、多态），
要求：
- 理论讲解控制在200字以内
- 每个特性提供一个Python代码示例
- 结合生活中的实际例子帮助理解
"""
```

### 2.5 分隔符与格式控制

使用分隔符可以清晰地标记Prompt的不同部分，帮助模型正确理解指令边界。

**常用分隔符**：

| 分隔符类型 | 写法 | 用途 |
|------------|------|------|
| XML标签 | `<input>` `</input>` | 标记输入内容 |
| 三个反引号 | ``` ``` | 标记代码块 |
| 竖线 | `\|` | 分隔不同部分 |
| 章节标题 | `###` | 标记不同段落 |

```python
prompt_delimiter = """
# 任务
请总结以下文章的主要内容。

### 文章内容
<content>
人工智能（AI）是当前科技领域最热门的话题之一。它涵盖了机器学习、深度学习、自然语言处理等多个分支。近年来，随着大语言模型的发展，AI在自然语言理解方面取得了突破性进展。
</content>

### 输出要求
- 总结不超过100字
- 提取3个关键词
- 用 bullet list 呈现
"""
```

---

## 3. 高级Prompt技术

### 3.1 Chain-of-Thought（CoT）思维链

**Chain-of-Thought**（思维链，简称CoT）是由Google研究人员在2022年提出的提示技术。核心思想是：**引导模型在给出最终答案之前，先展示推理过程**。

为什么CoT有效？

1. **过程监督**：将最终答案的正确性转化为推理步骤的正确性
2. **知识激活**：强制模型调用与问题相关的中间知识
3. **错误定位**：推理过程便于发现和修正错误

**标准CoT格式**：

```python
prompt_cot = """
问题：小明有5个苹果，小红给了他3个，后来小明吃了2个，现在还剩多少个？

思维链：
1. 小明开始有5个苹果
2. 小红给了他3个，所以 5 + 3 = 8 个
3. 小明吃了2个，所以 8 - 2 = 6 个
最终答案：6个
"""
```

**Few-shot CoT vs Zero-shot CoT**：

| 类型 | 描述 | 适用场景 |
|------|------|----------|
| **Few-shot CoT** | 提供包含推理过程的示例 | 复杂推理任务，效果更好 |
| **Zero-shot CoT** | 添加"Let's think step by step"触发推理 | 快速应用，效果稍弱 |

### 3.2 Zero-shot CoT

Zero-shot CoT是CoT的简化版本，不需要手工设计示例，只需在问题后添加一句触发词即可。

**核心公式**：

$$Prompt_{Zero-shot-CoT} = Prompt_{original} + "让我们一步步思考"$$

```python
# 不使用Zero-shot CoT
prompt_original = """
一家书店有120本书，第一天卖了30本，第二天卖了剩下的1/3，
还剩多少本书？
"""

# 使用Zero-shot CoT
prompt_zeroshot_cot = """
一家书店有120本书，第一天卖了30本，第二天卖了剩下的1/3，
还剩多少本书？

让我们一步步思考：
"""
```

**进阶触发词**：

| 触发词（中文） | 触发词（英文） | 效果 |
|----------------|----------------|------|
| 让我们一步步思考 | Let's think step by step | 最常用，效果稳定 |
| 仔细分析这个问题 | Let me analyze this carefully | 适合分析类问题 |
| 首先...然后...最后 | First...Then...Finally | 适合流程类问题 |

### 3.3 Tree of Thoughts（ToT）思维树

**Tree of Thoughts**（思维树，ToT）是对CoT的扩展，它不是线性推理，而是探索多条可能的思考路径，然后在每条路径上继续分支，最终选择最优路径。

**ToT vs CoT**：

```
CoT（线性）：
A → B → C → D（一个答案）

ToT（树状）：
         A
      ↙  ↓  ↘
     B1   B2   B3
    ↙↓   ↙↓   ↙↓
   C1 C2 C3 C4 C5 C6
```

**ToT的核心步骤**：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 思维分解 | 将问题分解为若干思考步骤 |
| 2 | 候选生成 | 每个步骤生成多个候选想法 |
| 3 | 状态评估 | 评估每个状态是否可能达到目标 |
| 4 | 搜索回溯 | 选择最佳路径，必要时回溯 |

**ToT实现示例**：

```python
prompt_tot = """
你是一个战略规划专家，需要为一家AI创业公司制定3年发展规划。

## 第一步：问题分解
请列出需要考虑的核心维度（例如：技术、市场、产品、团队、资金等）。

## 第二步：每个维度生成多个方案
对每个维度，生成2-3个不同方向的方案，并简要说明优劣。

## 第三步：评估组合
从所有方案中，选择最合理的3个维度组合，给出最终建议。

## 第四步：制定时间表
基于选择的方案，制定3年规划的时间表（按年列出里程碑）。

请确保每个步骤都有清晰的推理过程。
"""
```

### 3.4 ReAct（推理+行动）

**ReAct**（Reasoning + Acting）是由清华大学和Google联合提出的方法，它将推理（Reasoning）和行动（Acting）结合起来，特别适合需要与外部环境交互的任务。

**ReAct的核心循环**：

```
观察(Observation) → 推理(Reasoning) → 行动(Action) → 观察(Observation) → ...
```

**ReAct Prompt模板**：

```python
prompt_react = """
你是一个智能助手，可以调用工具来完成任务。

## 可用工具
1. search(query) - 搜索网络获取信息
2. calculator(expression) - 执行数学计算

## 任务
请回答：2024年诺贝尔物理学奖得主的主要贡献是什么？

## 请按照以下格式回答：
思考：我需要先搜索2024年诺贝尔物理学奖相关信息
行动：search("2024 Nobel Prize Physics winner")
观察：结果显示XXX
思考：现在我知道了XXX，需要进一步了解具体贡献
行动：search("2024 Nobel Physics winner contributions")
观察：...
思考：现在我有足够信息给出完整答案
最终答案：[你的回答]
"""
```

### 3.5 自动Prompt优化

在实际应用中，我们可以让LLM自己来优化Prompt，这被称为**自动Prompt工程**（Automatic Prompt Engineering）。

```python
# 自动优化Prompt
prompt_optimizer = """
你是一位Prompt工程专家。请优化以下Prompt，使其更加清晰有效。

原始Prompt：
"帮我写一个程序"

请从以下维度优化：
1. 明确具体任务
2. 添加角色设定
3. 指定输出格式
4. 添加约束条件

优化后的Prompt应该可以直接使用。
"""
```

### 3.6 高级技术对比总结

| 技术 | 核心思想 | 适用场景 | 复杂度 |
|------|----------|----------|--------|
| **Zero-shot** | 直接提问，无需示例 | 简单任务 | ⭐ |
| **Few-shot** | 提供示例，隐式学习 | 模式化任务 | ⭐⭐ |
| **CoT** | 展示推理过程 | 数学、逻辑推理 | ⭐⭐ |
| **Zero-shot CoT** | 添加触发词诱导推理 | 快速应用 | ⭐ |
| **ToT** | 多路径探索 | 复杂规划、创意任务 | ⭐⭐⭐ |
| **ReAct** | 推理+行动+观察 | 工具使用、信息检索 | ⭐⭐⭐ |

---

## 4. Prompt模式与框架

### 4.1 RAG中的Prompt设计

**RAG**（Retrieval-Augmented Generation，检索增强生成）是将外部知识库与大模型结合的技术。在RAG系统中，Prompt设计需要同时考虑**检索结果**和**原始问题**。

**RAG Prompt核心要素**：

```python
prompt_rag = """
你是一个知识问答助手。请基于提供的参考资料回答用户问题。

## 参考资料
{retrieved_context}

## 用户问题
{user_question}

## 回答要求
1. 仅基于提供的参考资料回答，不要编造信息
2. 如果参考资料中没有相关信息，请明确说明"根据提供的资料，我无法回答这个问题"
3. 回答要条理清晰，重要信息用加粗标注
4. 列出参考资料中支持你回答的关键引文
"""
```

**RAG Prompt优化策略**：

| 策略 | 说明 | 示例 |
|------|------|------|
| 上下文截断 | 限制检索内容长度，避免超过模型上下文 | 只保留最相关的top-k段落 |
| 查询重写 | 将用户问题改写为更适合检索的形式 | "AI是什么"→"人工智能定义与原理" |
| 混合提示 | 结合多个检索结果，提供多角度信息 | 同时提供维基百科和专业论文 |
| 引用标注 | 要求模型标注信息来源 | "根据[1]，..." |

### 4.2 Agent中的Prompt设计

**Agent**（智能体）是指能够自主感知环境、做出决策并执行动作的系统。在Agent架构中，Prompt不仅指导模型回答问题，还定义了工具使用、决策流程等。

**Agent Prompt核心框架**：

```python
prompt_agent = """
# 系统角色
你是一个智能机器人助手，能够帮助用户完成各种任务。

## 可用工具
{available_tools}

## 行为准则
1. 分析用户请求，确定是否需要使用工具
2. 如果需要工具，明确指定要使用的工具及参数
3. 每次只调用一个工具，等待结果后再决定下一步
4. 工具调用必须遵循指定格式

## 工具调用格式
当你需要调用工具时，请使用以下JSON格式：
{
    "tool": "工具名称",
    "args": {
        "param1": "参数值1",
        "param2": "参数值2"
    }
}

## 对话历史
{chat_history}

## 当前用户请求
{user_message}

## 你的思考过程
{self_relection}

## 你的决策
"""
```

**ReAct Agent完整实现**：

```python
prompt_react_agent = """
# 智能Agent系统

你是一个配备了工具调用能力的智能助手。

## 可用工具
1. search(query: str) - 搜索网络，返回最相关结果
2. calculator(expr: str) - 数学计算
3. get_weather(city: str) - 获取城市天气
4. translate(text: str, target_lang: str) - 翻译文本

## Agent循环
对于每个用户请求，按照以下步骤执行：

### 步骤1：理解任务（Reasoning）
分析用户请求，判断需要哪些信息或工具。

### 步骤2：选择行动（Action）
如果需要外部信息或计算，选择合适的工具调用。
如果可以直接回答，直接进入步骤4。

### 步骤3：观察结果（Observation）
获取工具返回结果，更新对问题的理解。

### 步骤4：给出答案（Answer）
基于所有可用信息，给出完整回答。

## 示例对话

用户：请帮我查一下北京今天的天气，以及北京到上海的距离。

助手：
思考：用户需要两个信息，北京天气和北京到上海的距离。这两个信息我都不知道，需要调用工具获取。

行动：
{
    "tool": "get_weather",
    "args": {"city": "北京"}
}

观察：天气数据显示北京今天晴，温度15-25度。

思考：天气信息已获取，但还不知道距离，需要继续调用工具。

行动：
{
    "tool": "search",
    "args": {"query": "北京到上海距离多少公里"}
}

观察：搜索结果显示约1200公里。

最终答案：北京今天天气晴朗，气温15-25度。北京到上海的距离约为1200公里。

## 用户当前请求
{current_request}

## 开始执行
"""
```

### 4.3 任务导向型Prompt模板

针对不同类型的任务，可以使用特定的Prompt模板。

**代码生成类**：

```python
prompt_code = """
## 任务
你是一位专业的{语言}开发工程师，请编写符合以下要求的代码。

## 技术栈
- 语言：{language}
- 框架：{framework}
- 版本要求：{version}

## 功能需求
{requirements}

## 代码规范
1. 包含完整的函数/类文档字符串
2. 添加必要的注释说明
3. 包含基础错误处理
4. 代码风格遵循PEP8（Python）或对应语言规范

## 输出格式
直接输出代码，不包含其他说明。如果代码较长，请分段输出并说明每段的作用。
"""
```

**数据分析类**：

```python
prompt_analysis = """
## 角色
你是一位数据分析师，擅长从数据中提取有价值的 insights。

## 数据来源
{data_content}

## 分析目标
{analysis_objective}

## 分析要求
1. 先对数据进行描述性统计分析
2. 识别数据中的模式、趋势或异常
3. 提供具有可操作性的建议
4. 所有结论必须有数据支撑

## 输出格式
1. 执行摘要（不超过100字）
2. 详细分析（包含图表描述）
3. 建议与结论
4. 技术附录（如有需要）
"""
```

### 4.4 Prompt安全与约束

在实际应用中，Prompt还需要考虑安全性和约束条件。

```python
prompt_with_constraints = """
你是一个客服对话机器人，请遵守以下规则：

## 绝对禁止
1. 不讨论政治、宗教等敏感话题
2. 不透露公司内部机密信息
3. 不承诺超出服务范围的事情
4. 不使用辱骂、歧视性语言

## 边界处理
1. 如果用户询问你不知道的信息，回复"这个问题我暂时无法回答，请联系人工客服"
2. 如果用户表达负面情绪，先进行情绪安抚
3. 如果涉及投诉，认真记录并承诺跟进

## 回复风格
1. 语气友好、专业
2. 使用"您"称呼用户
3. 避免过于技术化的术语
4. 主动询问是否还有其他需要帮助

## 当前对话
{conversation_history}

## 用户最新消息
{user_message}

## 你的回复
"""
```

---

## 5. 代码实战

### 5.1 环境准备

```bash
# 安装必要的库
pip install openai anthropic transformers

# 设置API密钥（根据使用的模型选择）
# OpenAI
export OPENAI_API_KEY="your-api-key"

# 或使用国内模型（如DeepSeek）
export DEEPSEEK_API_KEY="your-api-key"
```

### 5.2 Few-shot Learning 实现

```python
#!/usr/bin/env python3
# examples/fewshot_learning.py
"""
Few-shot Learning 实战：情感分析
通过提供少量示例，让模型学习情感分类的模式
"""

import os


class FewShotClassifier:
    """
    Few-shot 少样本分类器
    通过在Prompt中提供示例来指导模型分类
    """
    def __init__(self, provider="openai", model=None):
        """
        初始化分类器

        参数:
            provider: API提供商 ('openai', 'deepseek')
            model: 模型名称
        """
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model = model or self.default_models.get(provider, "gpt-4")

        # 根据不同provider初始化客户端
        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "deepseek":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        print(f"[INFO] Few-shot分类器初始化: {provider}/{self.model}")

    def _build_prompt(self, examples, input_text):
        """
        构建Few-shot Prompt

        参数:
            examples: 示例列表，每个示例为 {"input": "...", "output": "..."}
            input_text: 待分类的输入文本

        返回:
            str: 构建好的Prompt
        """
        # 构建示例部分
        examples_str = "\n\n".join([
            f"示例{i+1}：\n文本：{ex['input']}\n情感：{ex['output']}"
            for i, ex in enumerate(examples)
        ])

        prompt = f"""请分析以下文本的情感类别。

## 情感类别说明
- 正向：表达积极情绪，如开心、满意、喜爱
- 负向：表达消极情绪，如难过、不满、厌恶
- 中性：客观描述，无明显情感倾向

## 示例
{examples_str}

## 待分类文本
文本：{input_text}

## 要求
1. 只输出情感类别（正向/负向/中性），不需其他说明
2. 如果文本情感复杂，选择最突出的情感类别
"""
        return prompt

    def classify(self, text, examples=None):
        """
        对文本进行情感分类

        参数:
            text: 待分类文本
            examples: few-shot示例列表，默认使用预设示例

        返回:
            str: 情感类别
        """
        # 默认示例
        if examples is None:
            examples = [
                {"input": "这部电影太精彩了！", "output": "正向"},
                {"input": "服务态度很差，很失望", "output": "负向"},
                {"input": "今天气温20度，适合外出", "output": "中性"},
            ]

        prompt = self._build_prompt(examples, text)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # 低温度确保输出稳定
                max_tokens=50
            )

            result = response.choices[0].message.content.strip()
            return result

        except Exception as e:
            print(f"[ERROR] 分类失败: {e}")
            return "分类失败"

    def batch_classify(self, texts, examples=None):
        """
        批量分类

        参数:
            texts: 文本列表
            examples: few-shot示例

        返回:
            list: 分类结果列表
        """
        results = []
        for text in texts:
            result = self.classify(text, examples)
            results.append({
                "text": text,
                "sentiment": result
            })
            print(f"  [{result}] {text[:30]}...")
        return results


def demo_sentiment_classification():
    """
    情感分类演示
    """
    print("=" * 60)
    print("Few-shot Learning 情感分类演示")
    print("=" * 60)

    # 初始化分类器（使用DeepSeek作为示例）
    classifier = FewShotClassifier(provider="deepseek")

    # 测试文本
    test_texts = [
        "这个产品完全超出预期，太好用了！",
        "等了两个月才到货，真的很无语",
        "根据测试数据显示，性能提升了15%",
        "味道一般，环境还可以",
        "强烈推荐这家店，老板人超好！"
    ]

    # 执行分类
    print("\n[INFO] 执行情感分类...")
    results = classifier.batch_classify(test_texts)

    # 统计结果
    sentiment_counts = {}
    for r in results:
        sentiment_counts[r['sentiment']] = sentiment_counts.get(r['sentiment'], 0) + 1

    print("\n[结果统计]")
    for sentiment, count in sentiment_counts.items():
        print(f"  {sentiment}: {count}条")

    return results


def demo_custom_domain():
    """
    自定义领域的Few-shot分类演示
    """
    print("\n" + "=" * 60)
    print("Few-shot Learning 自定义领域演示（意图识别）")
    print("=" * 60)

    classifier = FewShotClassifier(provider="deepseek")

    # 自定义领域的few-shot示例
    intent_examples = [
        {"input": "播放周杰伦的晴天", "output": "播放音乐"},
        {"input": "把客厅灯打开", "output": "控制灯光"},
        {"input": "今天天气怎么样", "output": "查询天气"},
        {"input": "帮我设置明早8点的闹钟", "output": "设置闹钟"},
    ]

    # 测试意图识别
    test_intents = [
        "我想听歌",
        "房间太暗了，开一下灯",
        "明天会下雨吗",
        "提醒我下午3点开会"
    ]

    print("\n[INFO] 执行意图识别...")
    for text in test_intents:
        result = classifier.classify(text, examples=intent_examples)
        print(f"  [{result}] {text}")

    return None


if __name__ == "__main__":
    import sys

    # 运行演示
    demo_sentiment_classification()
    demo_custom_domain()
```

### 5.3 CoT提示实现

```python
#!/usr/bin/env python3
# examples/cot_reasoning.py
"""
Chain-of-Thought (CoT) 思维链推理实战
通过引导模型展示推理过程，提升复杂问题的解答准确率
"""

import os
import re


class CoTReasoner:
    """
    Chain-of-Thought 思维链推理器
    支持Zero-shot CoT和Few-shot CoT两种模式
    """
    def __init__(self, provider="openai", model=None):
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model = model or self.default_models.get(provider, "gpt-4")

        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "deepseek":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        print(f"[INFO] CoT推理器初始化: {provider}/{self.model}")

    def zero_shot_cot(self, question, trigger_phrase=None):
        """
        Zero-shot CoT：无需示例，只需添加触发词

        参数:
            question: 问题
            trigger_phrase: 触发词，默认使用"让我们一步步思考"

        返回:
            dict: 包含推理过程和最终答案
        """
        if trigger_phrase is None:
            trigger_phrase = "让我们一步步思考："

        prompt = f"""{question}

{trigger_phrase}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )

            full_response = response.choices[0].message.content

            # 尝试分离推理过程和最终答案
            # 通常最终答案在文本末尾，用"最终答案"、"答案"等标记
            answer_pattern = r'(?:最终)?答案[：:]\s*(.+?)(?:\n|$)'
            match = re.search(answer_pattern, full_response)

            if match:
                final_answer = match.group(1).strip()
                reasoning = full_response[:match.start()].strip()
            else:
                # 如果没有明确的答案标记，将最后一段作为答案
                parts = full_response.split('\n')
                reasoning = '\n'.join(parts[:-1])
                final_answer = parts[-1].strip() if parts else full_response

            return {
                "reasoning": reasoning,
                "answer": final_answer,
                "full_response": full_response
            }

        except Exception as e:
            print(f"[ERROR] CoT推理失败: {e}")
            return {"reasoning": "", "answer": "推理失败", "full_response": ""}

    def few_shot_cot(self, question, examples):
        """
        Few-shot CoT：提供带有完整推理过程的示例

        参数:
            question: 问题
            examples: 示例列表，每个示例为 {"question": "...", "reasoning": "...", "answer": "..."}

        返回:
            dict: 包含推理过程和最终答案
        """
        # 构建示例部分
        examples_str = "\n\n".join([
            f"问题：{ex['question']}\n\n思考过程：\n{ex['reasoning']}\n\n最终答案：{ex['answer']}"
            for ex in examples
        ])

        prompt = f"""请像示例一样，先展示思考过程，再给出最终答案。

## 示例
{examples_str}

## 当前问题
问题：{question}

思考过程：
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )

            full_response = response.choices[0].message.content

            # 提取最终答案
            answer_pattern = r'最终答案[：:]\s*(.+?)(?:\n|$)'
            match = re.search(answer_pattern, full_response)

            if match:
                final_answer = match.group(1).strip()
                reasoning = full_response[:match.start()].strip()
            else:
                reasoning = full_response
                final_answer = "未找到明确答案"

            return {
                "reasoning": reasoning,
                "answer": final_answer,
                "full_response": full_response
            }

        except Exception as e:
            print(f"[ERROR] Few-shot CoT推理失败: {e}")
            return {"reasoning": "", "answer": "推理失败", "full_response": ""}


def demo_math_reasoning():
    """
    数学推理演示
    """
    print("=" * 60)
    print("CoT 思维链 - 数学推理演示")
    print("=" * 60)

    reasoner = CoTReasoner(provider="deepseek")

    # 数学问题
    math_problem = """
水果店有苹果、橘子和梨三种水果。
- 苹果有30个
- 橘子比苹果多15个
- 梨的数量是橘子的2倍
- 其中有5个苹果是坏的

请问：好的水果一共有多少个？
"""

    print("\n[Zero-shot CoT]")
    print(f"问题：{math_problem.strip()}")
    result = reasoner.zero_shot_cot(math_problem)
    print(f"\n推理过程：\n{result['reasoning']}")
    print(f"\n最终答案：{result['answer']}")

    # Few-shot示例
    examples = [
        {
            "question": "小明有10本书，给了小红3本，又买了5本，现在有几本？",
            "reasoning": "1. 小明开始有10本书\n2. 给了小红3本，剩下 10-3=7 本\n3. 又买了5本，现在有 7+5=12 本",
            "answer": "12本"
        }
    ]

    print("\n" + "-" * 40)
    print("[Few-shot CoT]")
    print(f"问题：{math_problem.strip()}")
    result = reasoner.few_shot_cot(math_problem, examples)
    print(f"\n推理过程：\n{result['reasoning']}")
    print(f"\n最终答案：{result['answer']}")


def demo_logic_reasoning():
    """
    逻辑推理演示
    """
    print("\n" + "=" * 60)
    print("CoT 思维链 - 逻辑推理演示")
    print("=" * 60)

    reasoner = CoTReasoner(provider="deepseek")

    logic_problem = """
所有猫都喜欢吃鱼。
小明养了一只猫叫"花花"。

请判断：小明的猫花花喜欢吃鱼吗？请说明推理过程。
"""

    print(f"\n问题：{logic_problem.strip()}")
    result = reasoner.zero_shot_cot(logic_problem)
    print(f"\n推理过程：\n{result['reasoning']}")
    print(f"\n最终答案：{result['answer']}")


def compare_methods():
    """
    对比Zero-shot vs Few-shot CoT效果
    """
    print("\n" + "=" * 60)
    print("CoT 方法对比：Zero-shot vs Few-shot")
    print("=" * 60)

    reasoner = CoTReasoner(provider="deepseek")

    problem = """
一个水池有进水管和出水管。
- 进水管每分钟进水10升
- 出水管每分钟出水6升
- 水池容量为200升

请问：2小时后，水池中有多少水？
"""

    print(f"\n问题：{problem.strip()}\n")

    print("[方法1: Zero-shot CoT]")
    result1 = reasoner.zero_shot_cot(problem)
    print(f"答案：{result1['answer']}\n")

    print("[方法2: Few-shot CoT]")
    examples = [
        {
            "question": "一个水池有进水管，每分钟进水8升。打开1小时后，水池有多少水？",
            "reasoning": "1小时 = 60分钟\n每分钟进水8升\n总共进水：60 × 8 = 480升",
            "answer": "480升"
        }
    ]
    result2 = reasoner.few_shot_cot(problem, examples)
    print(f"答案：{result2['answer']}\n")


if __name__ == "__main__":
    # 数学推理演示
    demo_math_reasoning()

    # 逻辑推理演示
    demo_logic_reasoning()

    # 方法对比
    compare_methods()


### 5.4 结构化输出解析

```python
#!/usr/bin/env python3
# examples/structured_output.py
"""
结构化输出解析实战
将大模型的自由文本输出解析为结构化数据
"""

import os
import json
import re


class StructuredOutputParser:
    """
    结构化输出解析器
    通过Prompt设计引导模型输出结构化数据，然后进行解析
    """
    def __init__(self, provider="openai", model=None):
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model = model or self.default_models.get(provider, "gpt-4")

        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "deepseek":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        print(f"[INFO] 结构化解析器初始化: {provider}/{self.model}")

    def _build_json_prompt(self, task_description, output_schema, input_data):
        """
        构建JSON输出的Prompt

        参数:
            task_description: 任务描述
            output_schema: 输出JSON Schema
            input_data: 输入数据

        返回:
            str: 完整的Prompt
        """
        schema_str = json.dumps(output_schema, ensure_ascii=False, indent=2)

        prompt = f"""{task_description}

## 输入数据
{input_data}

## 输出要求
请严格按照以下JSON Schema输出，不要包含任何其他内容：

```json
{schema_str}
```

## 重要提示
1. 只输出JSON，不要有任何解释性文字
2. 所有字段必须按照Schema填写
3. 如果某个字段没有对应信息，使用null
"""
        return prompt

    def parse_json_output(self, text):
        """
        从模型输出中提取JSON

        参数:
            text: 模型输出的文本

        返回:
            dict: 解析后的JSON对象
        """
        # 方法1：尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 方法2：提取 ```json ... ``` 代码块
        json_pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(json_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 方法3：提取 { ... } 第一个JSON对象
        json_pattern = r'\{[\s\S]*\}'
        match = re.search(json_pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        print(f"[WARN] 无法解析JSON: {text[:100]}...")
        return None

    def extract_structured(self, task, schema, data, parse_method="json"):
        """
        提取结构化信息

        参数:
            task: 任务描述
            schema: 输出Schema
            data: 输入数据
            parse_method: 解析方法 ('json', 'regex', 'table')

        返回:
            解析后的结构化数据
        """
        if parse_method == "json":
            prompt = self._build_json_prompt(task, schema, data)
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=1024
                )
                raw_output = response.choices[0].message.content
                return self.parse_json_output(raw_output)
            except Exception as e:
                print(f"[ERROR] 提取失败: {e}")
                return None

        elif parse_method == "regex":
            return self._extract_with_regex(task, data)

        elif parse_method == "table":
            return self._extract_table(task, data)

    def _extract_with_regex(self, pattern_description, text):
        """
        使用正则表达式提取信息

        参数:
            pattern_description: 提取规则描述
            text: 待提取文本

        返回:
            dict: 提取结果
        """
        prompt = f"""{pattern_description}

请从以下文本中提取信息，返回JSON格式：

文本：
{text}

输出格式：
{{"field1": "值1", "field2": "值2"}}

只输出JSON。
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=512
            )
            return self.parse_json_output(response.choices[0].message.content)
        except Exception as e:
            print(f"[ERROR] Regex提取失败: {e}")
            return None

    def _extract_table(self, table_description, text):
        """
        提取为表格格式

        参数:
            table_description: 表格描述
            text: 待提取文本

        返回:
            list: 表格数据（每行一个字典）
        """
        prompt = f"""{table_description}

请从以下文本中提取信息，以Markdown表格形式输出：

文本：
{text}

## 要求
1. 第一行是表头
2. 使用标准Markdown表格格式（|列1|列2|...）
3. 不要输出其他内容
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[ERROR] 表格提取失败: {e}")
            return None


def demo_json_extraction():
    """
    JSON提取演示
    """
    print("=" * 60)
    print("结构化输出解析 - JSON提取演示")
    print("=" * 60)

    parser = StructuredOutputParser(provider="deepseek")

    # 定义输出Schema
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "人名"},
            "age": {"type": "integer", "description": "年龄"},
            "occupation": {"type": "string", "description": "职业"},
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "技能列表"
            },
            "email": {"type": "string", "description": "邮箱"}
        },
        "required": ["name", "occupation"]
    }

    # 输入文本
    input_text = """
    张三先生今年35岁，是一名资深的软件工程师。他熟练掌握Python、Java和Go三种编程语言，
    同时也是Docker和Kubernetes方面的专家。他的工作邮箱是 zhangsan@example.com。
    在加入现在的公司之前，他曾在多家互联网公司工作过。
    """

    result = parser.extract_structured(
        task="请从以下文本中提取人物信息",
        schema=schema,
        data=input_text,
        parse_method="json"
    )

    if result:
        print(f"\n[提取结果]")
        print(json.dumps(result, ensure_ascii=False, indent=2))


def demo_table_extraction():
    """
    表格提取演示
    """
    print("\n" + "=" * 60)
    print("结构化输出解析 - 表格提取演示")
    print("=" * 60)

    parser = StructuredOutputParser(provider="deepseek")

    # 输入文本
    input_text = """
    2024年第一季度，各产品销售情况如下：
    产品A销售额120万元，同比增长25%；
    产品B销售额85万元，同比增长12%；
    产品C销售额200万元，同比增长30%；
    产品D销售额65万元，同比下降5%。
    """

    result = parser.extract_structured(
        task="提取产品销售数据为表格",
        schema=None,
        data=input_text,
        parse_method="table"
    )

    if result:
        print(f"\n[提取结果]")
        print(result)


def demo_regex_extraction():
    """
    正则提取演示：提取会议信息
    """
    print("\n" + "=" * 60)
    print("结构化输出解析 - 会议信息提取")
    print("=" * 60)

    parser = StructuredOutputParser(provider="deepseek")

    input_text = """
    会议室预订确认函：
    会议名称：2024年度产品规划会议
    时间：2024年3月15日 14:00-17:00
    地点：总部大厦A座3楼会议室
    参会人员：李明（产品总监）、王芳（研发经理）、张伟（市场总监）
    会议主题：讨论2024年产品路线图和关键里程碑
    """

    schema = {
        "meeting_name": "会议名称",
        "date": "日期",
        "time": "时间",
        "location": "地点",
        "attendees": "参会人员列表",
        "topic": "会议主题"
    }

    result = parser.extract_structured(
        task="从以下会议信息文本中提取结构化数据，返回JSON",
        schema=schema,
        data=input_text,
        parse_method="json"
    )

    if result:
        print(f"\n[提取结果]")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    # JSON提取演示
    demo_json_extraction()

    # 表格提取演示
    demo_table_extraction()

    # 会议信息提取演示
    demo_regex_extraction()
```

### 5.5 端到端Prompt工程实战

```python
#!/usr/bin/env python3
# examples/prompt_engineering_demo.py
"""
端到端Prompt工程实战：构建一个智能客服助手
整合多种Prompt技术，展示完整的企业级应用
"""

import os
import json


class SmartCustomerService:
    """
    智能客服系统
    整合角色设定、Few-shot、CoT等多种Prompt技术
    """
    def __init__(self, provider="openai", model=None):
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model = model or self.default_models.get(provider, "gpt-4")

        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "deepseek":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )
        else:
            raise ValueError(f"不支持的提供商: {provider}")

        # 对话历史
        self.conversation_history = []

        print(f"[INFO] 智能客服系统初始化: {provider}/{self.model}")

    def _build_system_prompt(self):
        """
        构建系统级Prompt
        包含角色设定、行为规则、知识边界等
        """
        system_prompt = """你是一个专业的智能客服助手，名为"小E"。

## 身份设定
- 你是某科技公司的在线客服，代表公司为用户提供服务
- 你友好、专业、高效，始终以用户满意度为目标
- 你了解公司的产品、政策和服务流程

## 服务准则
1. **积极倾听**：认真理解用户的问题和需求
2. **准确回答**：基于已知信息准确回答，不确定时主动说明
3. **主动建议**：在解决当前问题后，适度提供相关建议
4. **情绪共鸣**：用户有负面情绪时，先表达理解和共情

## 知识边界
- 熟悉：公司产品功能、使用方法、常见问题解决方案
- 了解：一般性技术概念、行业常识
- 不知道：未公开的公司内部信息、竞品详细对比、具体价格（需转人工）

## 回复风格
- 语气：友好、亲切、专业
- 称呼：使用"您"称呼用户，自称"我"
- 格式：段落简洁，适当使用bullet list
- 长度：一般不超过200字，复杂问题可适当延长

## 安全与合规
- 不泄露用户个人信息
- 不承诺超出服务范围的的事情
- 涉及投诉或严重问题时，引导转人工服务"""
        return system_prompt

    def _classify_intent(self, user_message):
        """
        使用Few-shot进行意图分类

        参数:
            user_message: 用户消息

        返回:
            str: 意图类别
        """
        intent_examples = [
            {"input": "你们的产品怎么使用？", "output": "product_usage"},
            {"input": "这个功能在哪里找？", "output": "product_usage"},
            {"input": "我的订单什么时候发货？", "output": "order_inquiry"},
            {"input": "查一下我的账号信息", "output": "account_info"},
            {"input": "功能不好用，报个bug", "output": "feedback"},
            {"input": "我要退款", "output": "refund"},
            {"input": "你好，我想咨询一下", "output": "general_inquiry"},
            {"input": "功能建议：希望能增加XX功能", "output": "suggestion"},
        ]

        examples_str = "\n".join([
            f"用户：{ex['input']}\n意图：{ex['output']}"
            for ex in intent_examples
        ])

        prompt = f"""请判断用户消息的意图类别。

## 意图类别
- product_usage: 产品使用方法咨询
- order_inquiry: 订单相关咨询
- account_info: 账户信息查询
- feedback: 问题反馈/bug报告
- refund: 退款相关
- general_inquiry: 一般性咨询
- suggestion: 功能建议

## 示例
{examples_str}

## 用户消息
{user_message}

## 要求
只输出意图类别代码，不要其他说明。
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=50
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] 意图分类失败: {e}")
            return "general_inquiry"

    def _generate_response(self, user_message, intent):
        """
        根据意图生成回复
        结合Few-shot示例和CoT推理

        参数:
            user_message: 用户消息
            intent: 已分类的意图

        返回:
            str: 生成的回复
        """
        # 构建带Few-shot示例的Prompt
        examples_map = {
            "product_usage": """示例1：
用户：怎么创建新项目？
助手：您好！创建新项目的步骤如下：\n1. 登录后点击首页的"+新项目"按钮\n2. 填写项目名称和描述\n3. 选择模板（可选）\n4. 点击"创建"完成

示例2：
用户：这个图表怎么导出？
助手：导出图表很简单：\n1. 点击图表右上角的"..."菜单\n2. 选择"导出"选项\n3. 选择格式（PNG/SVG/PDF）\n4. 点击下载即可""",

            "order_inquiry": """示例1：
用户：我的订单还没到
助手：您好，让我帮您查询一下订单状态。请提供您的订单号，我来为您查看物流信息。

示例2：
用户：订单号12345什么时候能到
助手：您好，根据物流信息，您的订单预计将在2-3个工作日内送达。如有紧急需要，您可以联系客服获取更多帮助。""",

            "refund": """示例1：
用户：我要申请退款
助手：您好，理解您想要退款。退款申请我可以协助您处理：
1. 如果订单未发货，可以直接取消并退款
2. 如果已发货，需要等收货后退回处理
请问您的订单目前是什么状态呢？"""
        }

        examples = examples_map.get(intent, "")

        prompt = f"""{self._build_system_prompt()}

## 当前对话上下文
{self._format_history()}

## 用户最新消息
{user_message}

## 已识别的用户意图
{intent}

{"## 参考示例\n" + examples if examples else ""}

## 要求
1. 先理解用户问题的核心
2. 结合示例风格回复
3. 如需用户提供信息，主动询问
4. 回复控制在200字以内
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": f"当前对话：\n{self._format_history()}\n\n用户消息：{user_message}\n\n意图：{intent}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] 回复生成失败: {e}")
            return "抱歉，系统现在有点忙，请稍后再试。"

    def _format_history(self):
        """
        格式化对话历史

        返回:
            str: 格式化的历史记录
        """
        if not self.conversation_history:
            return "（这是对话的开始）"

        formatted = []
        for msg in self.conversation_history[-6:]:  # 只保留最近6条
            role = "用户" if msg["role"] == "user" else "助手"
            formatted.append(f"{role}：{msg['content'][:100]}")
        return "\n".join(formatted)

    def chat(self, user_message):
        """
        处理用户消息

        参数:
            user_message: 用户输入

        返回:
            str: 助手回复
        """
        # 1. 意图分类（Few-shot）
        intent = self._classify_intent(user_message)
        print(f"[意图识别] {intent}")

        # 2. 生成回复
        response = self._generate_response(user_message, intent)

        # 3. 更新历史
        self.conversation_history.append({"role": "user", "content": user_message})
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def reset(self):
        """
        重置对话历史
        """
        self.conversation_history = []
        print("[INFO] 对话历史已重置")


def demo_customer_service():
    """
    智能客服演示
    """
    print("=" * 60)
    print("智能客服系统演示")
    print("=" * 60)

    service = SmartCustomerService(provider="deepseek")

    # 模拟对话
    test_messages = [
        "你好，我想咨询一下产品怎么使用",
        "创建项目的时候一直报错是怎么回事",
        "我的订单编号是ORDER20240315，什么时候能发货？",
        "你们这个功能很好用，建议能增加导出功能",
    ]

    for msg in test_messages:
        print(f"\n【用户】{msg}")
        reply = service.chat(msg)
        print(f"【小E】{reply}")

    # 查看意图分布
    print("\n[INFO] 对话模拟完成")


if __name__ == "__main__":
    demo_customer_service()
```

---

## 6. 练习题

### 基础题

**1. 选择题**

1.1 以下哪一项不是Prompt的核心要素？
- A. 指令（Instruction）
- B. 上下文（Context）
- C. 模型参数（Parameters）
- D. 示例（Examples）

1.2 Few-shot Learning相比Zero-shot的优势是：
- A. 不需要任何示例
- B. 通过示例帮助模型理解任务模式
- C. 速度更快
- D. 适用于所有任务

1.3 Chain-of-Thought（CoT）思维链的核心思想是：
- A. 减少推理步骤
- B. 跳过中间过程直接给出答案
- C. 展示完整的推理过程
- D. 使用更多示例

1.4 Zero-shot CoT的触发词通常是：
- A. "请回答"
- B. "让我们一步步思考"
- C. "以上都不是"
- D. "总结一下"

1.5 在RAG系统中，Prompt设计需要额外考虑：
- A. 模型大小
- B. 检索结果的整合
- C. 训练数据
- D. 模型架构

**2. 简答题**

2.1 简述Prompt工程的定义及其核心价值。

2.2 解释Few-shot Learning的工作原理，为什么它有效？

2.3 比较CoT和ToT两种推理技术的异同。

2.4 说明在Agent系统中，Prompt设计需要包含哪些关键要素。

2.5 列举至少3种提高Prompt清晰性的技巧。

**3. 编程题**

3.1 编写Python代码，实现一个Few-shot文本分类器，能够根据少量示例对文本进行情感分类。

3.2 编写Python代码，实现Zero-shot CoT推理，对数学问题进行分步解答。

### 提高题

**4. 综合题**

4.1 设计一个完整的客服对话系统Prompt，包含：系统角色、行为规则、知识边界、回复风格等组成部分，并说明每个部分的设计思路。

4.2 分析Tree of Thoughts（ToT）与Chain-of-Thought（CoT）的适用场景差异，并各举一个实际应用案例。

**5. 实战题**

5.1 使用OpenAI或DeepSeek API，实现一个结构化信息提取工具，能够从非结构化文本中提取实体（人名、地点、时间、组织）并以JSON格式输出。

5.2 实现一个多步骤任务规划Prompt，让模型能够将"帮我规划一周的健康生活"这样的模糊请求分解为可执行的步骤。

---

## 7. 参考答案

### 基础题答案

**1. 选择题**

1.1 **答案：C**
解析：Prompt的核心要素包括指令、上下文、输入数据、输出格式和示例。模型参数不属于Prompt的组成部分。

1.2 **答案：B**
解析：Few-shot通过提供少量示例，帮助模型理解输入与输出的对应关系，从而更好地完成分类或其他任务。

1.3 **答案：C**
解析：CoT的核心思想是引导模型展示完整的推理过程，而非直接给出答案，通过"思考过程"来提高复杂问题的解答质量。

1.4 **答案：B**
解析：Zero-shot CoT的经典触发词是"让我们一步步思考"（Let's think step by step），它能诱导模型进行分步推理。

1.5 **答案：B**
解析：RAG系统需要将检索到的外部知识整合到Prompt中，帮助模型基于真实信息回答问题。

**2. 简答题**

2.1 **Prompt工程定义与核心价值**：

| 方面 | 内容 |
|------|------|
| **定义** | 研究和优化Prompt设计的一门学科，通过优化输入文本来提升模型输出质量 |
| **核心价值** | 成本效益高（无需训练）、快速迭代、灵活适应任务、挖掘模型潜力 |

2.2 **Few-shot Learning原理**：

Few-shot通过在Prompt中提供少量示例，让模型从示例中学习输入-输出的映射规律，无需参数更新。其有效性源于：
- 模型在预训练中已学到大量知识，示例帮助激活相关知识子集
- 示例提供了任务的具体模式，比纯文字描述更直观
- 模型具备"情境学习"能力，能在上下文中快速适应新任务

2.3 **CoT vs ToT异同**：

| 方面 | CoT | ToT |
|------|-----|-----|
| 推理方式 | 线性，单条路径 | 树状，多条路径 |
| 探索性 | 低，固定方向 | 高，可回溯 |
| 适用场景 | 数学计算、逻辑推理 | 复杂规划、创意生成 |
| 计算成本 | 低 | 高 |

2.4 **Agent Prompt关键要素**：

| 要素 | 说明 |
|------|------|
| 角色定义 | 明确Agent的身份和能力范围 |
| 工具描述 | 可用工具列表及使用说明 |
| 决策流程 | 推理-行动-观察的循环机制 |
| 输出格式 | 工具调用的JSON格式规范 |
| 安全约束 | 边界条件和限制说明 |

2.5 **提高Prompt清晰性的技巧**：

1. 使用具体动词替代模糊动词
2. 提供明确的输出格式要求
3. 分解复杂任务为多个简单步骤
4. 使用分隔符标记不同内容块
5. 提供充分的上下文信息

**3. 编程题答案**

3.1 **Few-shot文本分类器**：

```python
#!/usr/bin/env python3
"""
Few-shot文本分类器实现
"""

import os

class FewShotClassifier:
    def __init__(self, provider="deepseek", model=None):
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model = model or self.default_models.get(provider, "gpt-4")

        if provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "deepseek":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )

    def _build_prompt(self, examples, input_text):
        """构建Few-shot Prompt"""
        examples_str = "\n".join([
            f"文本：{ex['input']}\n情感：{ex['output']}"
            for ex in examples
        ])

        return f"""请分析文本的情感类别（正向/负向/中性）。

示例：
{examples_str}

待分类文本：{input_text}

只输出：正向 / 负向 / 中性
"""

    def classify(self, text, examples=None):
        """执行分类"""
        if examples is None:
            examples = [
                {"input": "太棒了，非常满意！", "output": "正向"},
                {"input": "质量很差，不推荐", "output": "负向"},
                {"input": "今天周一", "output": "中性"},
            ]

        prompt = self._build_prompt(examples, text)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()


# 使用示例
classifier = FewShotClassifier(provider="deepseek")
result = classifier.classify("产品效果超出预期，点赞！")
print(f"分类结果: {result}")  # 正向
```

3.2 **Zero-shot CoT推理**：

```python
#!/usr/bin/env python3
"""
Zero-shot CoT 数学推理实现
"""

import os

class CoTReasoner:
    def __init__(self, provider="deepseek", model=None):
        self.provider = provider
        self.default_models = {
            "openai": "gpt-4",
            "deepseek": "deepseek-chat"
        }
        self.model = model or self.default_models.get(provider, "gpt-4")

        if provider == "deepseek":
            from openai import OpenAI
            self.client = OpenAI(
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com"
            )

    def reason(self, problem):
        """执行Zero-shot CoT推理"""
        prompt = f"""{problem}

让我们一步步思考：
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024
        )
        return response.choices[0].message.content


# 使用示例
reasoner = CoTReasoner(provider="deepseek")
problem = "小明有25元，买了3本每本7元的书，还剩多少元？"
result = reasoner.reason(problem)
print(result)
```

### 提高题答案

**4. 综合题**

4.1 **客服系统Prompt设计**：

```python
customer_service_prompt = """
# 角色定义
你是一个专业的在线客服助手，名为"小e"。

# 行为规则
1. 积极倾听，理解用户真实需求
2. 准确回答，不知道的主动说明
3. 超出范围及时转人工

# 知识边界
- 熟悉：产品功能、使用方法、常见问题
- 不知道：价格（需查询）、竞品对比（不评价）

# 回复风格
- 语气友好，使用"您"
- 段落简洁，关键信息加粗
- 复杂问题分步骤说明
"""
```

4.2 **CoT vs ToT适用场景**：

| 技术 | 适用场景 | 案例 |
|------|----------|------|
| **CoT** | 有明确逻辑路径的问题 | 数学计算、代码调试、逻辑推理 |
| **ToT** | 需要探索和规划的问题 | 商业策略制定、旅行规划、创意写作 |

**案例**：
- CoT应用：解数学应用题"小明买水果，总价52元，橙子5元/斤，苹果8元/斤，共买了8斤，求各买多少斤"
- ToT应用：制定"三个月内用户增长50%"的产品策略，需要探索多个方向并评估

---

## 总结

本课程学习了Prompt Engineering的核心知识，包括：

1. **Prompt工程概述**：理解Prompt的定义、Prompt工程的概念及其重要性
2. **基础技巧**：清晰指令、结构化输出、Few-shot示例、角色设定
3. **高级技术**：CoT思维链、Zero-shot CoT、Tree of Thoughts、ReAct
4. **Prompt模式**：RAG中的Prompt设计、Agent中的Prompt设计
5. **代码实战**：Few-shot分类器、CoT推理器、结构化输出解析器

---

**下一步学习：**
- [13-1 LLM基础与大模型概述](../13-1-LLM基础与大模型概述.md)
- [13-3 LangChain 框架](../13-3-LangChain框架/13-3-LangChain框架.md)

---

*本课程由 Every Emodied Course 项目组编写 - 2026*