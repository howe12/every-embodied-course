# 01-6 多Agent自动化与协作

> **前置课程**：01-5 OpenClaw工作空间与工程规范
> **后续课程**：01-7 Skill系统与机器人工具链

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：上一节我们学习了OpenClaw的工作空间结构和工程规范，理解了文件组织、工具配置和记忆管理的基本方法。但你有没有想过一个问题——当一个任务复杂到需要多种能力时，单个Agent是否还够用？比如，用户说"帮我开发一个机器人导航功能，要求能自主规避障碍物、实时绘制地图、并且能与人对话交互"，这件事让一个Agent从头做到尾，可能效率很低，质量也难以保证。这就引出了我们今天的主题——**多Agent自动化与协作**。从本节课开始，我们将学习如何让多个Agent协同工作，模拟一个真实团队的开发流程，大幅提升任务处理能力。

想象一个软件开发团队：
- 产品经理负责和客户沟通需求
- 架构师负责设计系统方案
- 程序员负责写代码
- 测试工程师负责验证质量

每个人各司其职，协作完成复杂项目。OpenClaw的6 Agent框架正是模拟了这样的团队结构。

---

## 1. 什么是多Agent系统？

### 1.1 从"单兵作战"到"团队协作"

在深入了解多Agent系统之前，让我们先思考一个问题：为什么一个人类团队比一个人效率高？

因为人类在长期实践中发现，**专业化分工**能够大幅提升效率。一个全能的"万金油"什么都懂一点，但什么都不精；而一个团队通过明确分工，让每个人专注于自己擅长的领域，互相配合，能够完成远超个人能力的复杂任务。

**多Agent系统（Multi-Agent System）**的核心思想正是如此：**将复杂任务分解，分配给多个专门化的Agent，每个Agent专注于自己的职责，通过协作完成整体目标。**

<img src="./images/single_vs_multi_agent.jpg" alt="单Agent vs 多Agent" style="zoom:50%;" />
*图注：单Agent像一个人独自完成所有工作，多Agent像一个团队分工协作*

### 1.2 多Agent系统的核心定义

> **多Agent系统**指的是由多个自主运行的Agent组成的系统，这些Agent各自拥有独立的职责和能力，通过通信协作共同完成复杂任务。每个Agent可以访问不同的工具、拥有不同的专业知识，它们之间通过消息传递和文件共享实现协调。

简单来说：

**多Agent系统 = 多个专业Agent + 通信机制 + 协作流程**

这个定义包含三个关键要素：

- **多个专业Agent**：每个Agent都有自己的专长，不是"万金油"
- **通信机制**：Agent之间需要传递消息、共享信息
- **协作流程**：明确谁负责什么、先做什么后做什么

### 1.3 多Agent vs 单Agent

| 特点 | 单Agent | 多Agent |
|------|---------|---------|
| **处理能力** | 一人承担所有任务 | 分工专业化 |
| **响应速度** | 单线处理，速度较慢 | 并行执行，效率更高 |
| **专业深度** | 广而不精 | 专而深 |
| **复杂任务** | 容易顾此失彼 | 各司其职，游刃有余 |
| **错误影响** | 一个错，全盘错 | 相互校验，风险分散 |
| **扩展性** | 受限于单一Agent能力 | 可灵活增减Agent角色 |
| **典型代表** | ChatGPT单次对话 | OpenClaw 6 Agent框架 |

**一个生动的比喻：**

- 单Agent就像一个独自完成所有工序的手工作坊——从采购原料到生产制造，从包装到销售，全靠一个人。效率低，容易出错，而且产品质量取决于这个人的全面程度。

- 多Agent就像一条现代化流水线——每个人只负责一道工序，专业化程度高，效率高，而且各工序之间有质检环节，发现问题可以及时修正。

<img src="./images/assembly_line.jpg" alt="流水线 vs 手工作坊" style="zoom:50%;" />
*图注：多Agent就像流水线，每个Agent专注于自己的工序*

### 1.4 多Agent在具身智能中的应用

在具身智能领域，多Agent系统的应用场景非常广泛：

**场景一：机器人协同控制**

一个完整的机器人系统可能需要同时运行多个功能模块：
- 感知Agent：处理传感器数据，理解环境
- 规划Agent：制定运动策略
- 控制Agent：执行具体的动作
- 通信Agent：与其他机器人或云端通信

每个Agent运行在机器人的不同计算单元上，协同完成复杂任务。

**场景二：智能问答与任务执行**

当你对机器人说"帮我规划一条去机场的路线，要避开拥堵路段"：
- 对话Agent理解你的需求
- 导航Agent查询路线
- 交通Agent分析实时路况
- 控制Agent将路线下发到车载系统

**场景三：多机器人协作**

在工业场景中，多台机器人需要协同工作：
- 一台负责搬运
- 一台负责装配
- 一台负责质检

它们通过通信协调进度，确保每个环节无缝衔接。

---

## 2. OpenClaw 6 Agent 协作框架

OpenClaw实现了一个6 Agent协作框架，模拟了一个真实软件开发团队的分工协作模式。这个框架从2026年3月开始运行，是整个系统的核心协调机制。

### 2.1 团队成员一览

| Agent | 角色名称 | 核心职责 | 类比团队 |
|-------|----------|----------|----------|
| **Monica** | 首席协调官 | 与用户对话，分配任务，协调各方 | 产品经理/项目经理 |
| **Richard** | 架构设计师 | 设计系统架构，制定技术方案 | 架构师 |
| **Ross** | 研发工程师 | 代码实现，bug修复 | 程序员 |
| **Angela** | 质量分析员 | 测试验证，质量评估 | 测试工程师 |
| **Daisy** | 嗅探研究员 | 前沿情报收集，技术调研 | 技术研究员 |
| **Wendy** | 课程编写员 | 文档编写，知识沉淀 | 技术文档工程师 |

<img src="./images/six_agents.jpg" alt="6 Agent协作框架" style="zoom:50%;" />
*图注：OpenClaw 6 Agent团队——各司其职，协同工作*

### 2.2 各Agent详细介绍

#### Monica — 首席协调官

Monica是整个团队的"门面"，是用户与系统交互的唯一接口。

**核心职责：**
- 接收和处理用户需求
- 创建任务分配文件（TASK.md）
- 调度子Agent执行任务
- 汇总结果，向用户汇报

**关键文件：**
```
~/.openclaw/workspace/openclaw/agent/monica/
├── SOUL.md    # 身份定义
├── TASK.md    # 当前任务分配
└── memory/    # 记忆存储
```

**为什么需要Monica作为唯一接口？**

这就像一个公司的前台——所有外部联系都经过她，再分发到各个部门。如果每个人都可以直接对外联络，信息和决策就会混乱不堪。Monica确保了：
- 用户只需要和一个"人"沟通，不用了解内部复杂结构
- 任务分配有统一入口，不会出现重复或遗漏
- 决策有据可查，所有任务都通过TASK.md追踪

#### Richard — 架构设计师

Richard是团队的技术大脑，负责在动手之前先把方案想清楚。

**核心职责：**
- 分析需求，设计系统架构
- 制定技术方案和实现计划
- 评估技术风险和可行性
- 输出架构文档和实现路线图

**工作原则：**
- **"先想后做"** — 复杂任务必须先设计再实施
- **"图纸先行"** — 架构图优于代码，先画图再写代码
- **"风险评估"** — 明确可能遇到的问题和应对策略

**类比：** Richard就像建筑设计师——在建造大楼之前，先画好图纸、计算结构、评估材料。没有设计师的图纸，工人是无法开工的。

#### Ross — 研发工程师

Ross是团队的执行者，负责把方案变成可运行的代码。

**核心职责：**
- 按照Richard设计的方案实现代码
- 调试和修复bug
- 编写技术文档和注释
- 持续集成，确保代码质量

**工作原则：**
- **"代码即文档"** — 代码要有清晰的中文注释
- **"小步快跑"** — 每次改动不要太大，及时验证
- **"测试驱动"** — 先写测试再写实现，保证可验证性

**类比：** Ross就像建筑工人——按照设计师的图纸，把大楼从地基开始一砖一瓦地建造起来。

#### Angela — 质量分析员

Angela是团队的守护者，确保交付给用户的产品质量过关。

**核心职责：**
- 设计测试用例，覆盖各种场景
- 执行测试，验证功能正确性
- 评估性能，发现瓶颈
- 输出测试报告，提出改进建议

**工作原则：**
- **"质量第一"** — 有bug的产品不能交付
- **"全面覆盖"** — 正常场景和边界场景都要测试
- **"以数据说话"** — 测试结论要有数据和证据支撑

**类比：** Angela就像建筑质检员——大楼建好后，要检查结构是否安全、管线是否通畅、门窗是否能正常开关。质检不通过，不能交房。

#### Daisy — 嗅探研究员

Daisy是团队的情报员，负责收集外部信息，为决策提供依据。

**核心职责：**
- 收集前沿技术动态
- 调研竞品和行业趋势
- 分析新技术的可行性和价值
- 整理情报报告，供团队参考

**工作原则：**
- **"情报优先"** — 重大决策前必须收集足够信息
- **"来源可靠"** — 信息要有据可查，不能道听途说
- **"及时更新"** — 技术变化快，情报要保持新鲜

**类比：** Daisy就像市场调研员——在开发新产品之前，先去市场看看有没有类似产品、用户有什么需求、技术发展到什么程度。

#### Wendy — 课程编写员

Wendy是团队的知识沉淀者，负责把团队的智慧记录下来。

**核心职责：**
- 编写课程文档和教程
- 整理技术文档和最佳实践
- 建立知识库，沉淀经验
- 维护文档更新，确保准确性

**工作原则：**
- **"文档先行"** — 代码可以跑，但文档不可少
- **"图文并茂"** — 好的文档要有代码示例和图表
- **"持续更新"** — 技术在演进，文档也要同步更新

**类比：** Wendy就像技术作家——把团队的实战经验和技术知识整理成书，让后来人可以站在前人的肩膀上继续前进。

### 2.3 Agent间的关系图

```
                    ┌─────────────┐
                    │   用户      │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Monica     │ 首席协调官
                    │  (唯一接口) │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
     ┌───────────┐  ┌───────────┐  ┌───────────┐
     │  Richard  │  │   Ross    │  │   Daisy   │
     │ 架构设计师│  │ 研发工程师│  │ 嗅探研究员│
     └─────┬─────┘  └─────┬─────┘  └───────────┘
           │              │
           │              ▼
           │       ┌───────────┐
           │       │  Angela   │
           │       │ 质量分析员│
           │       └───────────┘
           │
           ▼
     ┌───────────┐
     │   Wendy   │
     │ 课程编写员│
     └───────────┘
```

**协作流程解读：**

1. 用户向Monica提出需求
2. Monica创建TASK.md，分配任务
3. **并行执行**：
   - Richard设计架构
   - Daisy收集情报
   - Ross准备实现方案
4. Ross根据Richard的方案实现代码
5. Angela测试Ross的代码
6. Wendy记录整个过程，形成文档
7. Monica汇总结果，向用户汇报

---

## 3. Agent通信机制

多Agent系统的高效运转，离不开可靠的通信机制。OpenClaw实现了一套轻量级但强大的通信体系。

### 3.1 Session 会话管理

**Session（会话）**是OpenClaw中Agent通信的基础单元。每个Agent运行时都处于一个独立的Session中。

**Session的核心概念：**

| 概念 | 说明 |
|------|------|
| **Session ID** | 每个会话的唯一标识符 |
| **父会话** | 启动子Agent的主会话 |
| **子会话** | 被启动的子Agent会话 |
| **会话上下文** | 包含Agent的"记忆"——历史消息、文件状态 |

**Session的层级关系：**

```
主会话 (Monica)
├── 子会话 1 (Richard)
├── 子会话 2 (Ross)
├── 子会话 3 (Angela)
└── 子会话 4 (Daisy)
```

**为什么需要Session？**

就像人类的对话——你说一句话，对方记住了你说的内容，才能理解你接下来的意思。Session就是Agent的"记忆容器"，它保存了：
- 之前说过的话
- 读取过的文件
- 做过的决策

没有Session，Agent每次都是"从零开始"，无法积累上下文。

### 3.2 消息传递

Agent之间通过消息传递进行通信。消息是结构化的，包含：

```json
{
  "from": "Monica",           // 发送者
  "to": "Ross",               // 接收者
  "type": "task",             // 消息类型
  "content": "实现XXX功能",    // 具体内容
  "timestamp": "2026-03-24"   // 时间戳
}
```

**消息类型：**

| 类型 | 说明 | 示例 |
|------|------|------|
| **task** | 任务分配 | Monica告诉Ross要做什么 |
| **result** | 结果汇报 | Ross告诉Monica完成了什么 |
| **info** | 信息共享 | Daisy告诉团队发现了什么 |
| **query** | 询问请求 | Angela询问某个实现细节 |
| **error** | 错误报告 | Ross报告遇到了什么问题 |

**消息传递的流程：**

```
Monica ──"任务"──▶ Ross
                    │
                    ▼
              Ross 处理任务
                    │
                    ▼
Monica ◀──"结果"── Ross
```

### 3.3 文件通信（TASK.md）

TASK.md是OpenClaw中最重要的文件通信载体。它是一个任务分配文件，Monica创建它来描述任务，子Agent读取它来了解要做什么。

**TASK.md的标准格式：**

```markdown
# 任务：XXX功能开发

## 任务背景
用户需要开发一个XXX功能，用于解决XXX问题。

## 重要规则（来自错题本）
- 禁止使用 `&` 后台启动，请使用前台启动或 nohup
- 启动后必须等待 XX 秒
- 每步完成后必须报告状态

## 具体步骤

### 步骤 1：需求分析
- [ ] 理解XXX需求
- [ ] 确认输入输出

### 步骤 2：环境准备
- [ ] 检查依赖
- [ ] 准备测试数据

### 步骤 3：代码实现
- [ ] 实现核心逻辑
- [ ] 添加单元测试

## 预期交付物
- 源代码文件
- 测试报告

## 截止时间
2026-03-24 18:00
```

**TASK.md的流转过程：**

```
Monica                Ross                  Angela
创建TASK.md          读取TASK.md            读取TASK.md
   │                     │                     │
   │    "去做这个任务"    │                     │
   ├─────────────────────▶│                     │
   │                     │                     │
   │               执行任务...                  │
   │                     │                     │
   │                     │    "测试结果"       │
   │                     ├────────────────────▶│
   │                     │                     │
   │              "完成了"                      │
   ◀─────────────────────┤                     │
   │                     │                     │
```

**为什么用文件而不是直接消息传递？**

这是一个很好的问题。直接消息传递看似更简单，但存在几个问题：

| 直接消息的问题 | 文件通信的优势 |
|----------------|----------------|
| 消息容易丢失 | 文件持久化，不会丢失 |
| 难以追踪历史 | 可以随时查看完整记录 |
| 复杂任务难以描述 | 可以结构化地描述复杂任务 |
| 无法附加上下文 | 可以附加代码、配置等 |

TASK.md就像一个"任务书"——白纸黑字，清清楚楚，避免了口头传达容易产生的误解。

---

## 4. 任务分配与执行流程

### 4.1 任务创建与分配

当用户向Monica提出一个需求时，完整的处理流程如下：

**第一步：理解需求**

Monica首先需要准确理解用户想要什么。有时候用户表达得很模糊，Monica需要主动追问确认。

**第二步：创建TASK.md**

Monica根据需求创建TASK.md，明确：
- 任务目标是什么
- 分成哪几个步骤
- 每个步骤由谁负责
- 交付物是什么

**第三步：分配任务**

Monica使用`sessions_spawn`工具启动子Agent，将任务分配下去。

```javascript
// 分配任务给子Agent的示例代码
{
  action: "sessions_spawn",
  agent: "ross",           // 指定由Ross执行
  runtime: "openclaw",      // 运行环境
  input: {
    task: "实现用户登录功能",  // 任务描述
    context: {              // 额外上下文
      skills: ["nodejs", "mysql"],  // 需要的技能
      deadline: "2026-03-25"        // 截止时间
    }
  }
}
```

### 4.2 子Agent启动（sessions_spawn）

`sessions_spawn`是OpenClaw中启动子Agent的核心工具。

**基本用法：**

```javascript
// 启动一个子Agent
sessions_spawn({
  agent: "ross",           // Agent类型
  runtime: "openclaw",      // 运行环境
  input: {                  // 传递给子Agent的输入
    task: "具体任务描述",
    context: {}             // 上下文信息
  }
})
```

**参数说明：**

| 参数 | 必须 | 说明 |
|------|------|------|
| `agent` | 是 | 子Agent类型，可选：richard/ross/angela/daisy/wendy |
| `runtime` | 是 | 运行环境，通常为 `openclaw` |
| `input.task` | 是 | 具体任务描述 |
| `input.context` | 否 | 额外上下文，如技能要求、截止时间等 |
| `input.files` | 否 | 需要传递给子Agent的文件列表 |

**并行启动多个子Agent：**

```javascript
// 同时启动多个子Agent（并行执行）
Promise.all([
  sessions_spawn({ agent: "richard", runtime: "openclaw", input: { task: "设计架构" } }),
  sessions_spawn({ agent: "daisy", runtime: "openclaw", input: { task: "收集情报" } })
])
```

**顺序执行（等待子Agent完成后执行下一步）：**

```javascript
// 先启动Richard，等他完成后，再启动Ross
const archResult = await sessions_spawn({ agent: "richard", runtime: "openclaw", input: { task: "设计架构" } })
const codeResult = await sessions_spawn({ agent: "ross", runtime: "openclaw", input: { task: "实现代码", architecture: archResult } })
```

### 4.3 结果汇总与汇报

当子Agent完成任务后，结果会返回给Monica。Monica负责：

1. **收集结果**：汇总各个子Agent的输出
2. **质量检查**：确认交付物是否符合要求
3. **向用户汇报**：用用户能理解的语言总结结果

**结果汇总的示例流程：**

```
时间线：
14:00  Monica接收用户需求
14:05  Monica创建TASK.md，分配任务
14:06  Richard完成架构设计
14:06  Daisy完成情报收集
14:07  Ross开始代码实现
14:30  Ross完成代码，提交测试
14:35  Angela完成测试，发现1个bug
14:40  Ross修复bug
14:45  Angela再次测试，通过
14:50  Monica汇总结果，向用户汇报
```

---

## 5. 定时任务与自动化

### 5.1 Cron 定时任务配置

在OpenClaw中，可以通过HEARTBEAT.md配置定时任务，实现自动化执行。

**HEARTBEAT.md的标准格式：**

```markdown
# HEARTBEAT.md - 心跳配置

## 定时任务

### 每日专利编写任务
| 时间   | Agent  | 任务              |
|--------|--------|-------------------|
| 01:00  | Ross   | 编写专利1         |
| 02:00  | Ross   | 编写专利2         |
| 03:00  | Ross   | 编写专利3         |
| 08:00  | Angela | 审核所有专利      |

### 每日课程编写任务
| 时间   | Agent  | 任务              |
|--------|--------|-------------------|
| 09:00  | Wendy  | 编写当天课程      |
| 15:00  | Angela | 审核前一天课程   |
```

**Cron表达式说明：**

| 表达式 | 含义 |
|--------|------|
| `0 * * * *` | 每小时整点执行 |
| `*/5 * * * *` | 每5分钟执行 |
| `0 9 * * *` | 每天9:00执行 |
| `0 9 * * 1-5` | 工作日9:00执行 |

### 5.2 心跳机制（Heartbeat）

**Heartbeat（心跳）**是OpenClaw实现定时任务的核心机制。

**心跳的工作原理：**

```
┌──────────────┐     每N分钟      ┌──────────────┐
│  OpenClaw    │ ───────────────▶ │  HEARTBEAT   │
│  系统        │                  │  检查器      │
└──────────────┘                  └──────┬───────┘
                                          │
                                          ▼
                                  ┌──────────────┐
                                  │ 根据配置     │
                                  │ 启动对应Agent│
                                  └──────┬───────┘
                                          │
                                          ▼
                                  ┌──────────────┐
                                  │ 执行定时任务  │
                                  └──────────────┘
```

**心跳检查的内容：**

| 检查项 | 说明 |
|--------|------|
| 时间条件 | 当前时间是否符合Cron表达式 |
| 任务状态 | 上次执行是否成功完成 |
| 互斥锁 | 是否有其他实例正在执行 |
| 重试次数 | 失败后是否需要重试 |

### 5.3 自动任务触发

除了定时触发，OpenClaw还支持事件触发和条件触发。

**事件触发：**

```markdown
## 事件触发

当以下事件发生时，自动执行对应任务：

| 事件                    | 触发任务               |
|------------------------|------------------------|
| 用户发送"专利"关键词    | 启动专利编写流程        |
| Git Push到main分支      | 自动部署到生产环境      |
| 监控发现系统异常         | 启动故障诊断流程        |
```

**条件触发：**

```markdown
## 条件触发

当以下条件满足时，自动执行对应任务：

| 条件                        | 触发任务               |
|----------------------------|------------------------|
| 新课程编写完成              | 自动部署到GitHub Pages |
| 课程审核发现问题            | 通知Wendy修改          |
| 专利编写数量未达标          | 提醒并增加执行频率      |
```

### 5.4 自动化工作流示例

**示例：每日专利编写工作流**

```
┌─────────────────────────────────────────────────────────────┐
│                    每日专利编写工作流                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  01:00 ──▶ Ross: 编写专利1（人机交互-手势识别）              │
│                │                                            │
│                ▼                                            │
│  02:00 ──▶ Ross: 编写专利2（机器人安全-碰撞检测）            │
│                │                                            │
│                ▼                                            │
│  03:00 ──▶ Ross: 编写专利3（语音情感识别）                   │
│                │                                            │
│                ▼                                            │
│  ...     ──▶ Ross: 继续编写其他专利                          │
│                │                                            │
│                ▼                                            │
│  08:00 ──▶ Angela: 审核所有专利                              │
│                │                                            │
│                ├── 发现问题 ──▶ 返回Ross修改                 │
│                │                                            │
│                └── 审核通过 ──▶ 进入知识库                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 协作最佳实践

### 6.1 任务边界定义

**清晰的任务边界**是高效协作的前提。每个Agent应该清楚：
- 我负责什么？
- 我不负责什么？
- 我应该找谁协作？

**任务边界定义的原则：**

| 原则 | 说明 | 反面案例 |
|------|------|----------|
| **单一职责** | 每个Agent只做一件事 | Monica直接去写代码 |
| **接口清晰** | Agent之间通过明确接口交互 | Ross直接去和用户沟通 |
| **不越俎代庖** | 做好自己的事，不替他Agent做决定 | Richard替Ross选择具体实现细节 |

**示例：任务边界定义**

```
Monica的边界：
✅ 应该：分配任务、协调进度、向用户汇报
❌ 不应该：直接写代码、直接测试功能

Ross的边界：
✅ 应该：按照方案实现代码、修复bug
❌ 不应该：直接和用户沟通需求、决定系统架构

Angela的边界：
✅ 应该：测试功能、报告bug、评估质量
❌ 不应该：自己修改代码、自己决定是否上线
```

### 6.2 记忆系统维护

记忆系统是Agent持续工作的基础。好的记忆管理能让Agent"记住"重要信息，避免重复犯错。

**记忆文件层次：**

| 文件 | 内容 | 频率 |
|------|------|------|
| `memory/YYYY-MM-DD.md` | 当天工作日志 | 每天自动创建 |
| `MEMORY.md` | 长期记忆 | 每周整理 |
| `memory/mistakes.md` | 错题本 | 每次犯错时更新 |

**记忆维护的黄金法则：**

> **Memory is limited — 想记住就写下来**
> **Text > Brain — 文件比记忆更可靠**

**示例：当天的记忆记录**

```markdown
# 2026-03-24 工作日志

## 任务
- 完成了01-5课程编写
- 审核了10-2课程

## 决策
- 决定使用nohup而非&后台启动
- 决定在测试前先读取错题本

## 经验
- 多Agent并行执行时，需要确保任务之间无依赖关系
- 定时任务需要设置合理的重试机制

## 待处理
- [ ] 01-6课程需要添加更多实践代码
```

### 6.3 错误处理与恢复

在实际运行中，错误是不可避免的。好的错误处理机制能够：

1. **快速发现问题** — 第一时间知道哪里出了问题
2. **隔离影响范围** — 防止一个Agent的错误扩散到整个系统
3. **自动恢复** — 在可能的情况下自动恢复正常运行

**错误处理的三层机制：**

| 层次 | 机制 | 说明 |
|------|------|------|
| **预防层** | 任务前置检查 | 执行前检查依赖、环境是否就绪 |
| **检测层** | 实时监控 | 运行中监控状态，发现异常立即告警 |
| **恢复层** | 自动重试/回滚 | 出错时尝试自动恢复或回滚到上一版本 |

**错误处理的代码示例：**

```javascript
// 错误处理的示例代码
async function executeTask(task) {
  try {
    // 第一层：前置检查
    if (!await checkPrerequisites(task)) {
      throw new Error("前置条件不满足");
    }
    
    // 第二层：执行任务
    const result = await runTask(task);
    
    // 第三层：结果验证
    if (!await validateResult(result)) {
      throw new Error("结果验证失败");
    }
    
    return { success: true, result };
    
  } catch (error) {
    // 错误记录
    console.error(`任务执行失败: ${error.message}`);
    
    // 判断是否可重试
    if (isRetryable(error) && task.retryCount < 3) {
      console.log(`正在重试... (${task.retryCount + 1}/3)`);
      task.retryCount++;
      return executeTask(task);  // 递归重试
    }
    
    // 不可重试的错误，报告给Monica
    await reportToMonica({
      task: task.name,
      error: error.message,
      stage: detectErrorStage(error)
    });
    
    return { success: false, error: error.message };
  }
}
```

**常见的错误类型及处理策略：**

| 错误类型 | 示例 | 处理策略 |
|----------|------|----------|
| **环境错误** | 依赖未安装 | 自动安装依赖，或回滚到上一版本 |
| **超时错误** | 任务执行超时 | 增加超时时间，或拆分为小任务 |
| **权限错误** | 无文件读写权限 | 请求授权，或使用有权限的路径 |
| **资源不足** | 内存不足 | 清理资源，或使用更小的模型 |
| **逻辑错误** | 代码有bug | 回滚代码，通知Ross修复 |

---

## 7. 实践代码

### 7.1 6 Agent 协作示例

以下是一个完整的6 Agent协作示例，展示了如何完成一个"开发机器人避障功能"的任务。

**场景描述：**
用户提出需求："我需要一个能自主规避障碍物的机器人功能，请帮我开发。"

**代码实现：**

```javascript
// ============================================
// 6 Agent 协作示例：机器人避障功能开发
// ============================================

// 第一步：Monica接收需求，创建任务
async function startDevelopment() {
  // Monica: 创建任务分配文件
  const taskContent = `
# 任务：机器人避障功能开发

## 需求背景
用户需要一个能自主规避障碍物的机器人功能。

## 子任务分解

### 子任务1：技术调研（Daisy）
- 调研当前主流的避障算法
- 分析各算法的优缺点和适用场景

### 子任务2：架构设计（Richard）
- 设计避障功能的系统架构
- 选择合适的技术方案
- 输出架构设计文档

### 子任务3：代码实现（Ross）
- 根据架构设计实现避障算法
- 编写单元测试

### 子任务4：测试验证（Angela）
- 设计测试用例
- 执行功能测试
- 输出测试报告

### 子任务5：文档编写（Wendy）
- 编写使用文档
- 整理技术文档

## 交付物
1. 避障算法源代码
2. 测试报告
3. 使用文档
  `;

  // Monica写入TASK.md
  await writeFile('~/.openclaw/workspace/TASK.md', taskContent);
  console.log('Monica: 任务分配文件已创建');
  
  // Monica: 启动子Agent并行执行
  console.log('Monica: 正在分配子任务...');
  
  const [researchResult, archResult] = await Promise.all([
    // 并行执行：技术调研 + 架构设计
    sessions_spawn({
      agent: 'daisy',
      runtime: 'openclaw',
      input: {
        task: '调研机器人避障算法，分析各算法优缺点',
        output: '避障算法调研报告'
      }
    }),
    
    sessions_spawn({
      agent: 'richard',
      runtime: 'openclaw',
      input: {
        task: '设计机器人避障功能的系统架构',
        context: { useCases: ['室内导航', '室外巡检'] }
      }
    })
  ]);

  console.log('Daisy: 调研完成', researchResult.summary);
  console.log('Richard: 架构设计完成', archResult.architecture);
  
  // 第二步：基于调研和架构，并行实现代码和测试准备
  const [codeResult, docResult] = await Promise.all([
    // Ross: 实现代码
    sessions_spawn({
      agent: 'ross',
      runtime: 'openclaw',
      input: {
        task: '实现机器人避障功能代码',
        architecture: archResult.architecture,
        algorithms: researchResult.recommendedAlgorithms
      }
    }),
    
    // Wendy: 同步准备文档
    sessions_spawn({
      agent: 'wendy',
      runtime: 'openclaw',
      input: {
        task: '编写避障功能使用文档',
        context: { isDraft: true }
      }
    })
  ]);

  console.log('Ross: 代码实现完成', codeResult.files);
  
  // 第三步：Angela测试代码
  const testResult = await sessions_spawn({
    agent: 'angela',
    runtime: 'openclaw',
    input: {
      task: '测试机器人避障功能',
      code: codeResult.files,
      testCases: [
        '静态障碍物场景',
        '动态障碍物场景',
        '狭窄通道场景',
        '紧急制动场景'
      ]
    }
  });

  // 第四步：Monica汇总结果
  console.log('Monica: 汇总结果...');
  
  const summary = {
    task: '机器人避障功能开发',
    status: testResult.allPassed ? '完成' : '部分完成',
    deliverables: {
      sourceCode: codeResult.files,
      testReport: testResult.report,
      documentation: docResult.docs
    },
    issues: testResult.issues || []
  };
  
  // 向用户汇报
  return summary;
}
```

### 7.2 定时任务配置示例

**HEARTBEAT.md配置示例：**

```markdown
# HEARTBEAT.md - 心跳配置

## 定时任务

### 每日课程编写任务
| 时间     | Agent  | 任务                      | Cron表达式    |
|----------|--------|---------------------------|---------------|
| 09:00    | Wendy  | 编写当天课程              | 0 9 * * *     |
| 14:00    | Angela | 审核前一天课程            | 0 14 * * *    |

### 专利编写任务（每小时）
| 时间  | Agent | 任务                      | Cron表达式         |
|-------|-------|---------------------------|--------------------|
| 01:00 | Ross  | 编写专利1                 | 0 1 * * *          |
| 02:00 | Ross  | 编写专利2                 | 0 2 * * *          |
| 03:00 | Ross  | 编写专利3                 | 0 3 * * *          |
| 04:00 | Ross  | 编写专利4                 | 0 4 * * *          |
| 05:00 | Ross  | 编写专利5                 | 0 5 * * *          |

### 监控任务（每5分钟）
| 时间       | Agent  | 任务                      | Cron表达式      |
|------------|--------|---------------------------|-----------------|
| */5 * * * * | Monica | 检查课程编写进度           | */5 * * * *     |

## 任务执行流程

### 课程编写流程
09:00 Wendy启动 → Wendy编写课程 → 14:00 Angela审核 → 
    ├── 通过 → 部署到GitHub Pages
    └── 不通过 → 返回Wendy修改

### 专利编写流程
01:00-07:00 Ross循环执行 → 每小时编写1个专利 →
08:00 Angela审核所有专利 → 报告给Monica
```

### 7.3 自动化工作流示例

以下是一个完整的自动化工作流示例：每日课程编写 → 审核 → 部署。

```javascript
// ============================================
// 自动化工作流：课程编写 → 审核 → 部署
// ============================================

// 工作流配置
const courseWorkflow = {
  name: '课程编写自动化流程',
  steps: [
    {
      name: '课程编写',
      agent: 'wendy',
      schedule: '0 9 * * *',  // 每天9点执行
      execute: async (context) => {
        // 读取当天要编写的课程大纲
        const courseOutline = await readFile('~/.openclaw/workspace/course_outline.md');
        
        // Wendy编写课程
        const result = await sessions_spawn({
          agent: 'wendy',
          runtime: 'openclaw',
          input: {
            task: `编写课程：${courseOutline.todayCourse}`,
            template: 'course_template.md',  // 课程模板
            reference: courseOutline.reference || null  // 参考资料
          }
        });
        
        return { course: result.course, files: result.outputFiles };
      }
    },
    
    {
      name: '课程审核',
      agent: 'angela',
      schedule: '0 14 * * *',  // 每天14点执行
      execute: async (context) => {
        // Angela读取上午编写的课程
        const courseFile = context.steps[0].output.course;
        
        const result = await sessions_spawn({
          agent: 'angela',
          runtime: 'openclaw',
          input: {
            task: '审核课程质量',
            course: courseFile,
            checklist: [
              '是否符合课程模板格式',
              '代码是否有中文注释',
              '              '是否有练习题和答案',
              '内容是否准确完整'
            ]
          }
        });
        
        return { approved: result.approved, issues: result.issues || [] };
      }
    },
    
    {
      name: '问题修正',
      agent: 'wendy',
      trigger: 'conditional',  // 条件触发：有审核问题时执行
      condition: (context) => context.steps[1].output.issues.length > 0,
      execute: async (context) => {
        // Wendy根据审核反馈修正课程
        const issues = context.steps[1].output.issues;
        
        const result = await sessions_spawn({
          agent: 'wendy',
          runtime: 'openclaw',
          input: {
            task: '根据审核反馈修正课程',
            issues: issues
          }
        });
        
        return { revised: result.revised };
      }
    },
    
    {
      name: '部署发布',
      agent: 'monica',
      trigger: 'conditional',  // 条件触发：审核通过时执行
      condition: (context) => context.steps[1].output.approved === true,
      execute: async (context) => {
        // Monica将课程部署到GitHub Pages
        const courseFile = context.steps[0].output.course;
        
        await exec('git add -A');
        await exec('git commit -m "更新课程"');
        await exec('git push origin main');
        
        console.log('Monica: 课程已部署到GitHub Pages');
        return { deployed: true, url: 'https://...' };
      }
    }
  ]
};
```

**工作流执行示例：**

```
时间线：
09:00  Wendy: 开始编写课程（并行执行，不阻塞）
        │
        ▼
14:00  Angela: 审核课程
        │
        ├── 发现问题 ──▶ 触发 Wendy修正
        │
        └── 通过 ──▶ 触发 Monica部署

15:00  Wendy: 修正完成（如果有问题）
        │
        ▼
Monica: 部署完成，向用户汇报
```

---

## 练习题

### 基础题

**1. OpenClaw 6 Agent框架包含哪些角色？各自的职责是什么？**

<details>
<summary>点击查看答案</summary>

| Agent | 角色 | 核心职责 |
|-------|------|----------|
| Monica | 首席协调官 | 与用户对话，分配任务，协调各方 |
| Richard | 架构设计师 | 设计系统架构，制定技术方案 |
| Ross | 研发工程师 | 代码实现，bug修复 |
| Angela | 质量分析员 | 测试验证，质量评估 |
| Daisy | 嗅探研究员 | 前沿情报收集，技术调研 |
| Wendy | 课程编写员 | 文档编写，知识沉淀 |

</details>

**2. TASK.md在多Agent协作中的作用是什么？**

<details>
<summary>点击查看答案</summary>

TASK.md是OpenClaw中最重要的文件通信载体，作用包括：

1. **任务描述**：清晰记录任务目标、步骤、交付物
2. **信息传递**：Monica创建，子Agent读取，避免口头传达的误解
3. **持久化存储**：文件形式保存，不会丢失，方便追踪历史
4. **上下文附加**：可以附加代码、配置等复杂信息
5. **责任明确**：白纸黑字，清清楚楚，明确谁负责什么

</details>

**3. sessions_spawn的作用是什么？请写出基本用法。**

<details>
<summary>点击查看答案</summary>

`sessions_spawn`是OpenClaw中启动子Agent的核心工具。

**基本用法：**
```javascript
sessions_spawn({
  agent: "ross",           // Agent类型
  runtime: "openclaw",     // 运行环境
  input: {                 // 传递给子Agent的输入
    task: "具体任务描述",
    context: {}            // 上下文信息
  }
})
```

**并行执行：**
```javascript
Promise.all([
  sessions_spawn({ agent: "richard", runtime: "openclaw", input: { task: "设计架构" } }),
  sessions_spawn({ agent: "daisy", runtime: "openclaw", input: { task: "收集情报" } })
])
```

</details>

**4. 多Agent相比单Agent有哪些优势？**

<details>
<summary>点击查看答案</summary>

| 优势 | 说明 |
|------|------|
| **分工专业化** | 每个Agent专注于自己的专长领域 |
| **并行执行** | 多个Agent可同时工作，效率更高 |
| **相互校验** | 一个Agent的输出可由另一个Agent验证 |
| **风险分散** | 一个Agent出错不会影响整个系统 |
| **扩展性强** | 可灵活增减Agent角色，适应不同任务 |
| **更易维护** | 每个Agent职责单一，问题定位更容易 |

</details>

### 进阶题

**1. 为什么Monica是多Agent框架中用户交互的唯一接口？这样做有什么好处？**

<details>
<summary>点击查看答案</summary>

**原因：**

Monica作为唯一接口，就像公司的前台——所有外部联系都经过她，再分发到各个部门。

**好处：**

1. **简化用户交互**：用户只需要和一个"人"沟通，不用了解内部复杂结构
2. **统一任务入口**：任务分配有统一入口，不会出现重复或遗漏
3. **决策可追踪**：所有任务都通过TASK.md追踪，有据可查
4. **防止信息混乱**：如果每个人都可以直接对外联络，信息流会混乱不堪
5. **保护内部Agent**：内部实现细节对用户透明，接口稳定

**类比：** 就像你去医院挂号，挂号员（Monica）会根据你的病情分配到不同科室（子Agent），你不需要知道医院内部是怎么运作的。

</details>

**2. 设计一个多Agent协作流程，完成"开发一个图像识别机器人"任务。**

<details>
<summary>点击查看答案</summary>

**任务分解：**

```
用户需求：开发一个图像识别机器人

Monica（首席协调官）
    │
    ├── TASK.md创建与分配
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│                    并行执行阶段                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Daisy（嗅探研究员）         Richard（架构设计师）        │
│  - 调研图像识别算法          - 设计系统架构              │
│  - 分析YOLO/SSD等方案        - 选择技术栈                │
│  - 整理调研报告              - 输出架构文档              │
│                                                          │
└─────────────────────────────────────────────────────────┘
    │                        │
    │ 调研报告                 │ 架构设计
    │                        │
    ▼                        ▼
┌─────────────────────────────────────────────────────────┐
│                    串行执行阶段                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Ross（研发工程师）                                       │
│  - 实现图像采集模块                                       │
│  - 实现目标检测模块                                       │
│  - 实现结果输出模块                                       │
│  - 编写单元测试                                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
    │
    │ 代码
    ▼
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  Angela（质量分析员）                                     │
│  - 设计测试用例                                           │
│  - 执行功能测试                                           │
│  - 性能测试（FPS、精度）                                  │
│  - 输出测试报告                                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
    │
    │ 测试结果
    ▼
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  Wendy（课程编写员）                                      │
│  - 编写使用文档                                           │
│  - 整理API文档                                            │
│  - 编写示例代码                                           │
│                                                          │
└─────────────────────────────────────────────────────────┘
    │
    ▼
Monica 汇总结果，向用户汇报
```

**关键点：**
- 调研和架构设计可以并行
- 代码实现依赖架构设计，必须串行
- 测试依赖代码实现，必须串行
- 文档编写可以与代码实现并行

</details>

**3. 如果Angela在测试时发现Ross的代码有严重bug，应该如何处理？**

<details>
<summary>点击查看答案</summary>

**处理流程：**

```
Angela发现严重bug
      │
      ▼
Angela记录bug详情（写入测试报告）
      │
      ▼
Angela通过TASK.md或消息通知Monica
      │
      ▼
Monica评估bug严重性，决定处理方式
      │
      ├── 严重（阻塞）：立即分配修复任务给Ross
      │               │
      │               ▼
      │          Ross修复bug
      │               │
      │               ▼
      │          Angela重新测试
      │               │
      │               ├── 通过 ──▶ 继续流程
      │               │
      │               └── 仍有问题 ──▶ 再次返回Ross
      │
      └── 不严重：记录到bug列表，后续迭代修复
```

**关键原则：**

| 原则 | 说明 |
|------|------|
| **质量第一** | 有严重bug的产品不能交付 |
| **责任明确** | Ross负责修复，Angela负责验证 |
| **不越权** | Angela不能自己动手改代码 |
| **有据可查** | 所有沟通通过TASK.md记录 |
| **持续验证** | 修复后必须重新测试确认 |

**错误处理机制：**

```javascript
// Angela测试时的错误报告
async function testAndReport(code) {
  try {
    const result = await runTests(code);
    return { passed: true, report: result };
  } catch (error) {
    // 记录bug详情
    await reportToMonica({
      type: 'bug_found',
      severity: error.severity,  // critical/high/medium/low
      description: error.message,
      reproduce: error.reproduceSteps,
      suggestedFix: error.suggestedFix
    });
    return { passed: false, issues: [error] };
  }
}
```

</details>

---

## 本章小结

| 概念 | 说明 |
|------|------|
| **多Agent系统** | 多个专业Agent + 通信机制 + 协作流程，分工协作完成复杂任务 |
| **OpenClaw 6 Agent** | Monica(协调)、Richard(架构)、Ross(开发)、Angela(测试)、Daisy(调研)、Wendy(文档) |
| **Session** | Agent通信的基础单元，包含上下文和历史消息 |
| **TASK.md** | 任务分配文件，Monica创建，子Agent读取执行 |
| **sessions_spawn** | 启动子Agent的核心工具，支持并行和串行执行 |
| **Heartbeat** | 定时任务机制，通过HEARTBEAT.md配置 |
| **任务边界** | 清晰定义每个Agent的职责范围，避免越权 |
| **记忆系统** | memory/日期.md + MEMORY.md + mistakes.md |
| **错误处理** | 预防层 + 检测层 + 恢复层三层机制 |

---

## 延伸阅读

1. **Multi-Agent System综述**：Wooldridge & Jennings, "Intelligent Agents: Theory and Practice"
2. **Agent通信机制**：FIPA Agent Communication Language (ACL)
3. **任务分配算法**：市场机制、拍卖模型在多Agent任务分配中的应用
4. **OpenClaw官方文档**：Agent协作框架设计文档

---

## 学有余力

如果你对多Agent系统感兴趣，可以进一步探索以下方向：

- **Agent间协商协议**：多Agent如何就任务分配达成共识
- **分布式Agent架构**：Agent运行在不同机器上如何通信
- **多Agent强化学习**：Agent如何通过学习学会协作
- **Agent社会行为**：信任、声誉、激励机制设计

---

*下节课程预告：在01-7中，我们将学习OpenClaw的Skill系统与机器人工具链，了解如何扩展Agent的能力边界，敬请期待。*
