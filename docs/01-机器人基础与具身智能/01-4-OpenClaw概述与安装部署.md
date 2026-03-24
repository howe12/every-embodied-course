# 01-4 OpenClaw概述与安装部署

> **前置课程**：01-3 具身智能概述
> **后续课程**：01-5 具身智能开发环境搭建

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：上一节我们深入探讨了具身智能的核心概念——智能的大脑与行动的身体如何协同工作。我们认识了感知层、规划层、学习层的三层架构，也了解了波士顿动力Atlas、特斯拉Optimus、Figure 01等明星项目。但你有没有想过：这些具身智能系统背后，是什么在协调它们的"大脑"和"身体"？答案是——**AI Agent 框架**。在具身智能的实际部署中，AI Agent 负责管理多模态感知融合、复杂任务规划、长短期记忆、以及与人类的自然交互。本节课我们将认识一个强大的开源AI Agent框架——**OpenClaw**，它是连接大模型与物理世界的重要桥梁。

想象一下：你设计了一个能够感知环境、理解指令、并且能执行复杂任务的具身智能机器人。但问题是——谁来协调这一切？谁来管理机器人的"记忆"？谁来让它与用户进行自然对话？谁来安排多个子任务有序执行？

在传统机器人软件架构中，这些功能往往需要工程师手写大量胶水代码。但现在，有了OpenClaw，你可以把这些复杂的管理工作交给一个模块化、可扩展的AI Agent框架。你只需要专注于机器人的核心能力——感知、控制、执行——而通用智能的部分，交给OpenClaw来处理。

---

## 1. OpenClaw 简介

### 1.1 什么是 OpenClaw？

**OpenClaw** 是一个开源的 AI Agent（人工智能代理）框架，由独立开发者维护，旨在帮助用户快速构建和部署多功能的 AI 智能体。它的核心理念是：**让 AI Agent 的构建变得简单、可扩展、且富有表现力**。

如果用一句话来概括 OpenClaw：

> **OpenClaw = 模块化的 AI Agent 运行时 + 多平台消息接入 + 可编程的工具系统 + 持久化记忆系统**

OpenClaw 并不是凭空诞生的。它的设计借鉴了多个成熟的开源项目和最佳实践，包括：

- **LangChain Agent** 的工具调用理念
- **ChatGPT Plugins** 的插件架构
- **MetaGPT** 的多智能体协作思路
- **Node.js 生态** 的工具链优势

### 1.2 OpenClaw 与具身智能的关系

你可能会问：OpenClaw 是一个软件框架，它与我们之前讨论的具身智能有什么关系？

这个关系非常密切。回顾 01-3 中提到的具身智能三层架构：

| 层次 | 功能 | OpenClaw 能做什么 |
|------|------|------------------|
| **感知层** | 传感器融合、环境理解 | 通过工具调用接入视觉、语音等感知能力 |
| **规划层** | 任务分解、动作规划 | Agent 推理引擎 + 工具调用链 |
| **学习层** | 经验积累、知识更新 | 记忆系统 + RAG 知识检索 |
| **交互层** | 人机对话、状态反馈 | 多平台消息接入（飞书、Discord等） |

**OpenClaw 在具身智能系统中的定位**，相当于整个系统的"协调中枢"或"智能管家"：

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw Agent                       │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐          │
│  │  记忆系统   │  │  工具系统   │  │  对话引擎   │          │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘          │
│        └──────────────┼──────────────┘                 │
│                       ▼                                 │
│              ┌─────────────────┐                        │
│              │   推理与规划引擎  │                        │
│              └────────┬────────┘                        │
└───────────────────────┼─────────────────────────────────┘
                        ▼
         ┌──────────────────────────┐
         │     具身智能机器人        │
         │  ┌────┐ ┌────┐ ┌────┐  │
         │  │感知│ │规划│ │执行│  │
         │  └────┘ └────┘ └────┘  │
         └──────────────────────────┘
```

- **OpenClaw** 是机器人的"大脑皮层"——负责思考、对话、记忆
- **具体的运动控制** 仍然由专业的机器人控制器完成（ROS、机械臂SDK等）
- **OpenClaw** 通过**工具调用**与下层控制系统交互

### 1.3 OpenClaw 的核心特性

**① 多 Agent 协作框架**

OpenClaw 支持同时运行多个 Agent，每个 Agent 可以有不同的角色、能力和知识背景。它们可以分工合作，共同完成复杂任务。这与我们之前提到的多智能体系统（Multi-Agent System）理念一脉相承。

例如，一个具身智能任务可以这样分配：
- **Agent A（规划者）**：理解用户指令，制定执行计划
- **Agent B（感知者）**：处理传感器数据，描述环境状态
- **Agent C（执行者）**：调用工具，执行具体动作

**② 丰富的工具集成（Tools）**

OpenClaw 提供了强大的工具系统，Agent 可以调用任意自定义工具来扩展能力。内置工具包括：

| 工具类别 | 示例工具 | 功能说明 |
|----------|----------|----------|
| **文件操作** | read, write, edit | 读写编辑本地文件 |
| **Shell 命令** | exec | 执行系统命令 |
| **网络访问** | web_fetch, web_search | 获取网页内容、搜索信息 |
| **飞书集成** | feishu_doc, feishu_wiki | 操作飞书文档、知识库 |
| **代码执行** | python, node | 运行代码片段 |
| **定时任务** | cron | 周期性触发任务 |
| **消息推送** | message | 发送消息到各平台 |

你也可以编写自己的自定义工具，OpenClaw 提供了清晰的工具开发接口。

**③ 持久化记忆系统（Memory）**

与纯文本对话不同，OpenClaw 具备持久化记忆能力：

- **短期记忆**：当前对话上下文，由 LLM 自动管理
- **长期记忆**：存储在本地文件中的结构化知识，可跨会话保留
- **错题本**：记录 Agent 的错误和规避方案，持续自我改进
- **每日日志**：记录每天发生的事件和决策

这种记忆系统让 Agent 能够"记住"之前的交互历史，不断积累经验。

**④ 多平台消息接入**

OpenClaw 可以接入多种即时通讯平台，实现"对话即服务"：

| 平台 | 支持情况 | 典型场景 |
|------|----------|----------|
| **飞书（Lark）** | ✅ 完整支持 | 企业内部助手 |
| **Discord** | ✅ 完整支持 | 社区 Bot |
| **Telegram** | ✅ 完整支持 | 个人助手 |
| **WhatsApp** | ✅ 完整支持 | 跨平台消息 |
| **微信** | ⚠️ 需要企业账号 | 国内办公 |

**⑤ 技能系统（Skills）**

OpenClaw 提供了可扩展的技能（Skill）系统，每个 Skill 就是一个独立的功能模块，包含：

- **SKILL.md**：技能的描述和使用说明
- **相关脚本**：实现具体功能的代码
- **配置参数**：可调整的运行参数

Skills 可以像"插件"一样被加载或卸载，按需扩展 Agent 的能力。

---

## 2. OpenClaw 架构

理解 OpenClaw 的架构，是高效使用它的前提。OpenClaw 的设计遵循了清晰的分层结构，每个组件各司其职，又相互协作。

### 2.1 核心组件：Gateway、Agent、Session

OpenClaw 的核心由三个主要组件构成：**Gateway（网关）**、**Agent（智能体）** 和 **Session（会话）**。

```
┌─────────────────────────────────────────────────────────┐
│                     OpenClaw Gateway                    │
│              （统一的入口和路由中枢）                      │
└──────────────────────┬──────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
   ┌───────────┐ ┌───────────┐ ┌───────────┐
   │  Session  │ │  Session  │ │  Session  │
   │  会话 1    │ │  会话 2    │ │  会话 3    │
   │           │ │           │ │           │
   │ ┌───────┐ │ │ ┌───────┐ │ │ ┌───────┐ │
   │ │Agent A│ │ │ │Agent B│ │ │ │Agent C│ │
   │ └───────┘ │ │ └───────┘ │ │ └───────┘ │
   └───────────┘ └───────────┘ └───────────┘
```

**Gateway（网关）**

Gateway 是 OpenClaw 的核心守护进程，负责：

- 接收来自各个平台（飞书、Discord、Telegram）的消息
- 管理所有的 Session 和 Agent 实例
- 维护 Agent 之间的通信和协作
- 提供 Web UI 和 CLI 管理界面

你可以把 Gateway 理解为 OpenClaw 的"操作系统内核"，它必须始终运行在后台。

**Agent（智能体）**

Agent 是执行具体任务的"工作者"。每个 Agent 有：

| 属性 | 说明 |
|------|------|
| **角色（Role）** | Agent 的身份定义，如"规划者"、"执行者" |
| **系统提示（System Prompt）** | 定义 Agent 的行为准则和背景知识 |
| **工具集（Tools）** | Agent 可以调用的工具列表 |
| **记忆（Memory）** | Agent 的个人记忆文件 |
| **技能（Skills）** | Agent 加载的技能模块 |

在 OpenClaw 中，你可以运行多个 Agent，它们可以：

- **串行协作**：一个 Agent 的输出作为另一个 Agent 的输入
- **并行协作**：多个 Agent 同时处理不同子任务
- **层级协作**：一个主 Agent 分配任务给多个子 Agent

**Session（会话）**

Session 代表一次完整的交互会话。它管理：

- 对话的历史记录（消息列表）
- 当前活跃的 Agent
- 会话级别的上下文和状态

每个外部平台的用户对话，对应 OpenClaw 中的一个 Session。Session 结束后，其历史记录会被保存到记忆文件中。

### 2.2 工具系统（Tools）

**工具的定义**

在 OpenClaw 中，工具是一个**可被 Agent 调用的函数**。每个工具有：

- **名称（name）**：唯一标识符
- **描述（description）**：说明工具的用途
- **参数模式（parameters）**：工具接受的输入参数
- **执行逻辑（handler）**：工具的实际行为

```javascript
// OpenClaw 工具定义示例（JSON 格式）
{
  "name": "get_robot_battery",
  "description": "获取机器人当前电池电量",
  "parameters": {
    "type": "object",
    "properties": {
      "robot_id": {
        "type": "string",
        "description": "机器人标识符"
      }
    },
    "required": ["robot_id"]
  }
}
```

**工具调用流程**

Agent 调用工具的过程，是一个"思考-决策-执行"的循环：

```
用户指令 ──► Agent 推理 ──► 选择工具 ──► 执行工具 ──► 接收结果 ──► Agent 再次推理 ──► ...
```

1. Agent 接收用户指令，在思维链（Chain of Thought）中分析需要哪些工具
2. Agent 生成符合工具参数模式的 JSON 调用请求
3. OpenClaw 执行工具，将结果返回给 Agent
4. Agent 根据结果继续推理，直到完成任务

**内置工具 vs 自定义工具**

OpenClaw 自带丰富的内置工具，覆盖了文件操作、网络访问、系统命令等常见场景。对于具身智能开发者，更重要的是学会编写**自定义工具**，来接入机器人的控制系统。

```javascript
// 自定义工具示例：控制机器人移动
const robot_move_tool = {
  name: "robot_move",
  description: "控制机器人移动到指定位置",
  parameters: {
    type: "object",
    properties: {
      direction: {
        type: "string",
        enum: ["forward", "backward", "left", "right"],
        description: "移动方向"
      },
      distance: {
        type: "number",
        description: "移动距离（米）"
      }
    },
    required: ["direction", "distance"]
  },
  // 工具的执行逻辑（异步函数）
  handler: async ({ direction, distance }) => {
    // 调用机器人 SDK 执行移动
    const result = await robotSDK.move(direction, distance);
    return `机器人向${direction}移动了${distance}米，当前位置：${result.position}`;
  }
};
```

### 2.3 记忆系统（Memory）

OpenClaw 的记忆系统是其区别于普通聊天机器人的关键特性。它模仿了人类的记忆机制，将记忆分为不同的层次和类型。

**三层记忆架构**

| 记忆类型 | 存储位置 | 生命周期 | 容量 | 内容示例 |
|----------|----------|----------|------|----------|
| **上下文记忆** | LLM 上下文窗口 | 当前会话 | 有限（取决于模型） | 用户刚才说了什么 |
| **短期记忆** | Session 历史 | 当前会话 | 中等 | 今天讨论了什么主题 |
| **长期记忆** | 本地文件（Markdown/JSON） | 跨会话 | 几乎无限 | 用户的长期偏好、历史交互 |

**记忆文件结构**

```markdown
# 记忆文件目录结构
~/.openclaw/workspace/
├── memory/
│   ├── 2026-03-24.md       # 每日日志（当天事件）
│   ├── mistakes.md         # 错题本（错误记录）
│   └── engineering-principles.md  # 工程准则
├── agent/
│   └── [agent-name]/
│       ├── SOUL.md         # Agent 身份定义
│       ├── MEMORY.md       # Agent 长期记忆
│       └── TASK.md         # 当前任务
└── data/                   # 结构化数据
```

**记忆的工作原理**

当 Agent 需要做决策时，它会检索相关的记忆：

1. **上下文构建**：将上下文记忆（当前对话）放入 Prompt
2. **记忆检索**：从长期记忆中检索与当前任务相关的片段
3. **记忆融合**：将检索到的记忆片段注入到 Prompt 中
4. **决策执行**：Agent 基于完整的上下文做出响应

这种方法让 Agent 能够：
- 记住用户的长期偏好（"用户喜欢简洁的回答"）
- 积累经验教训（"上次这个命令失败了，换个方法"）
- 保持上下文连续性（跨会话理解用户需求）

**错题本机制**

OpenClaw 的一个独特设计是**错题本（Mistakes Log）**。每当 Agent 犯错或收到用户的纠正，相关信息会被记录到错题本中：

```markdown
## 错题本记录示例

### 日期：2026-03-24

**错误类型**：工具调用参数错误
**场景**：执行 robot_move 工具时，距离参数传了负数
**错误信息**：`Distance must be positive`
**规避方案**：
- 在调用移动工具前，先检查参数是否为正数
- 添加参数校验逻辑：`Math.abs(distance)`
**相关规则**：
- 移动距离必须 > 0
- 角度参数范围：-180° 到 180°
```

这个机制让 Agent 能够"吃一堑长一智"，同一个错误不会犯两次。

### 2.4 6 Agent 协作框架

OpenClaw 支持多 Agent 协作。在具身智能课程项目中，我们定义了一个 **6 Agent 协作框架**，每个 Agent 有明确的角色和职责。

**团队成员一览**

| Agent | 角色名 | 职责 | 核心文件 |
|-------|--------|------|----------|
| **Monica** | 首席协调官 | 与用户对话，分配任务，协调团队 | SOUL.md, TASK.md |
| **Richard** | 架构设计师 | 设计系统架构，制定技术方案 | SOUL.md |
| **Ross** | 研发工程师 | 代码实现，bug 修复 | SOUL.md |
| **Angela** | 质量分析员 | 测试验证，质量评估 | SOUL.md |
| **Daisy** | 嗅探研究员 | 前沿情报收集，技术调研 | SOUL.md |
| **Wendy** | 课程编写员 | 文档编写，知识沉淀 | SOUL.md |

**协作流程**

```
用户 ──► Monica（接收需求）
           │
           ├──► 创建 TASK.md（任务分配）
           │
           ▼
     ┌─────────────────┐
     │  任务分配决策    │
     └────────┬────────┘
              │
    ┌─────────┼─────────┬──────────┬──────────┐
    ▼         ▼         ▼          ▼          ▼
Richard   Ross      Angela     Daisy      Wendy
架构设计   代码实现   测试验证    情报收集    文档编写
    │         │         │          │          │
    └─────────┴─────────┴──────────┴──────────┘
                          │
                          ▼
                    Monica（汇总汇报）
                          │
                          ▼
                       用户
```

**为什么要多 Agent？**

- **专业化分工**：每个 Agent 专注于自己的领域，避免"全能但平庸"
- **并发执行**：多个子任务可以同时处理，提高效率
- **可扩展性**：新增角色只需添加新的 Agent，不影响现有架构
- **故障隔离**：一个 Agent 的问题不会影响其他 Agent

**6 Agent 的文件组织**

```
~/.openclaw/workspace/
├── SOUL.md          # 主 Agent（Monica）的身份定义
├── AGENTS.md        # 6 Agent 协作框架说明
├── USER.md          # 用户信息
├── MEMORY.md        # Monica 的长期记忆
├── HEARTBEAT.md     # 心跳/进度追踪
├── TASK.md          # 当前任务分配状态
└── agent/
    ├── monica/      # 首席协调官
    ├── richard/     # 架构设计师
    ├── ross/        # 研发工程师
    ├── angela/      # 质量分析员
    ├── daisy/       # 嗅探研究员
    └── wendy/       # 课程编写员
```

---

## 3. OpenClaw 安装与配置

本节将详细介绍如何在自己的机器上安装和配置 OpenClaw。

### 3.1 环境要求

OpenClaw 基于 **Node.js** 开发，运行它需要以下环境：

| 要求 | 最低版本 | 推荐版本 | 说明 |
|------|----------|----------|------|
| **Node.js** | v18.0.0 | v20.x LTS | OpenClaw 的运行时 |
| **npm** | v8.0.0 | v10.x | Node.js 包管理器 |
| **Python** | v3.8 | v3.11 | 部分工具需要 Python 环境 |
| **操作系统** | macOS 12+ / Ubuntu 20.04+ / Windows 10+ | macOS 14 / Ubuntu 22.04 | 主流操作系统均可 |
| **内存** | 4GB | 8GB+ | Agent 推理需要一定内存 |
| **磁盘** | 2GB 可用 | 5GB+ | 安装文件和记忆数据 |

**检查当前环境：**

```bash
# 检查 Node.js 版本
node --version
# 输出示例：v20.17.0

# 检查 npm 版本
npm --version
# 输出示例：10.8.2

# 检查 Python 版本
python3 --version
# 输出示例：Python 3.11.0
```

### 3.2 npm 全局安装（推荐方式）

**第一步：安装 OpenClaw CLI**

```bash
# 使用 npm 全局安装 OpenClaw
npm install -g openclaw

# 验证安装是否成功
openclaw --version
# 输出示例：openclaw v1.2.3
```

**第二步：初始化配置目录**

```bash
# 创建并初始化 OpenClaw 工作目录
openclaw init

# 交互式问答：
# ? 选择安装模式
#   ❯ standard（标准模式，包含所有功能）
#     minimal（最小模式，仅核心功能）
#     custom（自定义模式，按需选择组件）

# ? 输入 AI 模型 API 地址（留空使用默认）
#   直接回车跳过

# ? 输入 AI 模型 API Key
#   请输入您的 API Key

# ? 选择默认运行时
#   ❯ minimax（MiniMax）
#     openai（OpenAI）
#     anthropic（Anthropic Claude）
#     ollama（本地 Ollama）
```

初始化完成后，会在用户目录下创建 `.openclaw` 目录：

```bash
# 查看初始化生成的目录结构
ls -la ~/.openclaw/
# 输出：
# total/          # 插件和扩展
# skills/         # 技能目录
# workspace/      # 工作区（记忆、任务等）
# config.yml      # 主配置文件
# gateway.db      # SQLite 数据库（会话存储）
```

### 3.3 Docker 安装（可选）

如果你熟悉 Docker，也可以使用容器方式运行 OpenClaw：

```bash
# 拉取 OpenClaw 镜像
docker pull openclaw/openclaw:latest

# 运行容器（前台模式）
docker run -it \
  -v ~/.openclaw:/app/.openclaw \
  -p 3000:3000 \
  openclaw/openclaw:latest

# 运行容器（后台模式）
docker run -d \
  --name openclaw \
  -v ~/.openclaw:/app/.openclaw \
  -p 3000:3000 \
  openclaw/openclaw:latest
```

**Docker 方式的优势：**
- 环境隔离，不需要担心依赖冲突
- 一键部署，适合服务器场景
- 版本切换方便

**Docker 方式的局限：**
- 无法直接访问宿主机的硬件设备（如串口）
- 工具调用需要额外配置端口映射

### 3.4 配置文件说明

OpenClaw 的主配置文件是 `~/.openclaw/config.yml`，以下是关键配置项的中文注释：

```yaml
# OpenClaw 主配置文件
# 配置文件版本，便于后续升级迁移
version: "1.0"

# 运行模式
mode: standard  # standard | minimal | development

# AI 模型配置
model:
  provider: minimax          # 模型提供商：minimax | openai | anthropic | ollama
  model: MiniMax-M2.7        # 模型名称
  api_url: ""                # API 地址（留空使用默认值）
  api_key: "your-api-key"    # API 密钥
  max_tokens: 16384          # 最大输出 token 数
  temperature: 0.7           # 温度参数（创造性 vs 确定性）

# Gateway 配置
gateway:
  host: "0.0.0.0"            # 监听地址（0.0.0.0 允许外部访问）
  port: 3000                 # 监听端口
  session_timeout: 3600      # 会话超时时间（秒）
  log_level: info            # 日志级别：debug | info | warn | error

# 平台接入配置
channels:
  # 飞书配置
  feishu:
    enabled: true
    app_id: "cli_xxxxxxxxxxxx"      # 飞书应用 App ID
    app_secret: "xxxxxxxxxxxx"      # 飞书应用 App Secret
    verification_token: "xxxxxxxx"  # 事件订阅验证 Token
    encrypt_key: "xxxxxxxx"          # 消息加密密钥

  # Discord 配置
  discord:
    enabled: false
    bot_token: ""                   # Discord Bot Token

  # Telegram 配置
  telegram:
    enabled: false
    bot_token: ""                   # Telegram Bot Token

# 工具系统配置
tools:
  enabled: true                    # 是否启用工具调用
  allowed_tools:                   # 允许调用的工具白名单
    - read
    - write
    - exec
    - web_fetch
    - web_search
  denied_tools: []                 # 禁止调用的工具黑名单

# 记忆系统配置
memory:
  enabled: true
  storage_path: ~/.openclaw/workspace  # 记忆存储路径
  max_history: 1000                  # 保留的最大历史消息数
  auto_save: true                   # 自动保存记忆

# 定时任务配置
cron:
  enabled: true
  jobs:
    # 示例：每天早上 9 点发送天气提醒
    - id: daily_weather
      name: "每日天气提醒"
      schedule: "0 9 * * *"         # Cron 表达式：每天 9:00 执行
      action: tool                  # 执行动作类型：tool | agent | webhook
      tool: web_fetch               # 调用的工具
      params:
        url: "https://wttr.in/beijing?format=3"

# 技能加载配置
skills:
  auto_load: true                   # 是否自动加载技能
  paths:                            # 技能搜索路径
    - ~/.openclaw/skills            # 用户自定义技能
    - ~/.npm-global/lib/node_modules/openclaw/skills  # 内置技能

# 安全配置
security:
  allowed_origins:                 # 允许的请求来源（CORS）
    - "https://your-domain.com"
  max_file_size: 10485760           # 最大文件大小（10MB）
  exec_whitelist:                   # 允许执行的命令白名单
    - "ls"
    - "cat"
    - "grep"
```

### 3.5 配置初始化（交互式）

如果你不想手动编辑配置文件，也可以使用交互式向导：

```bash
# 启动交互式配置向导
openclaw config init

# 输出示例：
# ┌─────────────────────────────────────────┐
# │     OpenClaw 配置向导                     │
# └─────────────────────────────────────────┘
#
# ? 请选择配置模式
#   ❯ 快速配置（推荐新手）
#     完整配置（自定义所有选项）
#     从模板选择
#
# ? 请输入 AI 模型 API Key
#   ████████████████████████████
#
# ? 请选择要接入的平台
#   ◉ 飞书
#   ○ Discord
#   ○ Telegram
#
# ...（继续交互问答）
```

---

## 4. OpenClaw 快速开始

本节将通过一个完整的示例，带领你快速上手 OpenClaw。

### 4.1 启动 Gateway

Gateway 是 OpenClaw 的核心服务，必须首先启动：

**方式一：前台启动（开发调试用）**

```bash
# 启动 Gateway，显示日志输出
openclaw gateway start

# 正常启动后，会看到类似输出：
# [OpenClaw Gateway] v1.2.3 启动中...
# [Gateway] 加载配置文件：~/.openclaw/config.yml
# [Gateway] 初始化 AI 模型：MiniMax-M2.7
# [Gateway] 启动 HTTP 服务器：0.0.0.0:3000
# [Gateway] 飞书频道已连接
# [Gateway] ✅ Gateway 启动完成！
```

**方式二：后台启动（生产环境用）**

```bash
# 使用 nohup 后台运行，日志输出到文件
nohup openclaw gateway start > ~/.openclaw/gateway.log 2>&1 &

# 查看 Gateway 状态
openclaw gateway status
# 输出示例：
# [Gateway] 运行状态：运行中
# [Gateway] PID：12345
# [Gateway] 启动时间：2026-03-24 09:00:00
# [Gateway] 内存占用：128MB
# [Gateway] 活跃会话：3

# 停止 Gateway
openclaw gateway stop
```

**方式三：Docker 启动**

```bash
# 一键启动（后台运行）
docker run -d \
  --name openclaw \
  --restart unless-stopped \
  -v ~/.openclaw:/app/.openclaw \
  -p 3000:3000 \
  openclaw/openclaw:latest
```

### 4.2 创建第一个 Agent

Agent 是 OpenClaw 的执行单元。下面我们创建一个最简单的 Agent：

**使用 CLI 创建 Agent：**

```bash
# 创建名为 "my-robot" 的 Agent
openclaw agent create my-robot

# 交互式输入 Agent 信息：
# ? Agent 角色名：机器人助手
# ? Agent 描述：一个能够帮助用户控制机器人的助手
# ? 系统提示词（回车使用默认）：
#   （将使用默认模板）
# ? 选择初始工具：
#   ◉ read, write
#   ◉ exec
#   ◉ web_fetch
#   ○ (全选)

# 创建完成！
# [Agent] my-robot 已创建
# [Agent] 配置文件：~/.openclaw/workspace/agent/my-robot/SOUL.md
```

**查看 Agent 列表：**

```bash
# 列出所有 Agent
openclaw agent list

# 输出示例：
# ┌───────────┬────────────┬────────────┬───────────┐
# │ 名称       │ 角色        │ 状态        │ 会话数    │
# ├───────────┼────────────┼────────────┼───────────┤
# │ my-robot  │ 机器人助手  │ 运行中      │ 2         │
# │ monica    │ 首席协调官  │ 运行中      │ 1         │
# └───────────┴────────────┴────────────┴───────────┘
```

### 4.3 基本命令使用

**与 Agent 对话（交互模式）：**

```bash
# 启动交互式对话
openclaw chat my-robot

# 对话示例：
# ┌─────────────────────────────────────────┐
# │  🤖 my-robot                           │
# └─────────────────────────────────────────┘
# > 你好，请介绍一下你自己
#
# 你好！我是 my-robot，一个智能机器人助手。
# 我可以帮助你：
# - 回答问题
# - 控制机器人移动
# - 查询传感器数据
# ...
#
# > 控制机器人向前移动1米
#
# 正在调用 robot_move 工具...
# 机器人已向前移动 1 米，当前位置：(1.0, 0.0)
```

**单次命令执行（非交互模式）：**

```bash
# 单次问答
openclaw ask my-robot "机器人当前位置在哪里？"

# 执行工具
openclaw exec my-robot "调用 robot_move，direction=forward，distance=0.5"

# 批量执行脚本
openclaw script my-robot ./my-task.js
```

**管理 Agent：**

```bash
# 查看 Agent 详细信息
openclaw agent info my-robot

# 停止 Agent
openclaw agent stop my-robot

# 重启 Agent
openclaw agent restart my-robot

# 删除 Agent
openclaw agent delete my-robot
```

### 4.4 Web UI 使用

OpenClaw 还提供了 Web 管理界面，方便通过浏览器进行操作：

```
┌─────────────────────────────────────────────────────────┐
│  🌐 访问地址                                             │
│                                                         │
│  本地访问：http://localhost:3000                        │
│  外部访问：http://<服务器IP>:3000                       │
│                                                         │
│  默认账号：admin                                         │
│  默认密码：（在首次启动时设置）                           │
└─────────────────────────────────────────────────────────┘
```

Web UI 提供了：
- **会话管理**：查看、切换、导出历史会话
- **Agent 管理**：创建、编辑、监控 Agent
- **日志查看**：实时查看 Gateway 运行日志
- **配置编辑**：可视化编辑配置文件
- **工具测试**：单独测试某个工具的调用

---

## 5. OpenClaw 进阶配置

### 5.1 飞书平台接入

飞书是国内最常用的企业协作平台之一，OpenClaw 提供了完整的飞书接入支持。

**第一步：在飞书开放平台创建应用**

1. 访问 [飞书开放平台](https://open.feishu.cn/app)
2. 点击「创建企业自建应用」
3. 填写应用名称和描述
4. 在「凭证与基础信息」中获取 **App ID** 和 **App Secret**

**第二步：配置事件订阅**

1. 在应用详情页，点击「添加应用能力」→「机器人」
2. 进入「事件订阅」页面
3. 配置请求地址（URL）：`https://your-domain.com/feishu/webhook`
4. 添加事件订阅：
   - `im.message.receive_v1`（接收消息）

**第三步：在 OpenClaw 中配置飞书**

```yaml
# config.yml 中添加飞书配置
channels:
  feishu:
    enabled: true
    # 从飞书开放平台获取
    app_id: "cli_xxxxxxxxxxxxxxxx"     # 应用 App ID
    app_secret: "xxxxxxxxxxxxxxxx"     # 应用 App Secret
    
    # 机器人配置
    bot:
      name: "OpenClaw助手"             # 机器人名称
      avatar: ""                        # 机器人头像 URL
    
    # 消息处理配置
    message:
      auto_reply: true                  # 是否自动回复
      reply_mention: true                # 回复时是否 @ 用户
      
    # 权限配置
    permissions:
      # 需要申请的权限（按需添加）
      - "im:message"
      - "im:message.group_at_msg"
```

**第四步：配置加解密（可选但推荐）**

```yaml
channels:
  feishu:
    # 事件订阅的加密配置
    verification_token: "your-verification-token"  # 飞书后台配置
    encrypt_key: "your-encrypt-key"                 # 用于消息加密的密钥
```

**第五步：重启 Gateway**

```bash
# 重启 Gateway 使配置生效
openclaw gateway restart

# 确认飞书连接成功
openclaw gateway status
# 输出应包含：[Feishu] ✅ 已连接到飞书
```

### 5.2 Discord 平台接入

Discord 是一个功能强大的即时通讯平台，适合社区和游戏场景。

```yaml
# config.yml 中添加 Discord 配置
channels:
  discord:
    enabled: true
    bot_token: "your-discord-bot-token"  # Discord Bot Token
    guild_id: "123456789"                # 服务器（Guild）ID
    
    # 消息配置
    message:
      prefix: "/"                          # 指令前缀（如 /ask, /help）
      mention_reply: true                  # @机器人时是否回复
```

**Discord Bot 权限申请：**
1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 创建新 Application
3. 在「Bot」页面获取 Token
4. 配置 Intent 权限：
   - **Message Content Intent**（必须开启，用于读取消息内容）
   - **Server Members Intent**（可选）

### 5.3 Telegram 平台接入

Telegram 以其开放的 Bot API 和良好的开发体验著称。

```yaml
# config.yml 中添加 Telegram 配置
channels:
  telegram:
    enabled: true
    bot_token: "your-telegram-bot-token"  # 从 @BotFather 获取
    
    # 消息配置
    message:
      prefix: "/"                           # 指令前缀
      admin_ids:                            # 管理员用户 ID 列表
        - 123456789
        - 987654321
```

**创建 Telegram Bot 步骤：**
1. 在 Telegram 中搜索 **@BotFather**
2. 发送 `/newbot` 创建新机器人
3. 按照提示设置机器人名称和用户名
4. 复制获得的 **Bot Token** 到配置文件中

### 5.4 工具配置进阶

工具是 OpenClaw 扩展能力的关键。你可以通过配置来控制工具的访问权限。

**启用/禁用特定工具：**

```yaml
tools:
  # 启用工具系统
  enabled: true
  
  # 只允许使用以下工具（白名单）
  allowed_tools:
    - read          # 读取文件
    - write         # 写入文件
    - web_fetch     # 获取网页
    - web_search    # 搜索网络
  
  # 禁止使用以下工具（黑名单）
  denied_tools:
    - exec          # 生产环境禁用 shell 执行
    - python        # 禁用 Python 解释器
```

**自定义工具目录：**

```yaml
tools:
  # 自定义工具的存放目录
  custom_tools_path: ~/.openclaw/tools
  
  # 工具执行超时时间（毫秒）
  timeout: 30000
  
  # 是否允许工具并行执行
  parallel: true
```

### 5.5 记忆系统配置

```yaml
# 记忆系统配置
memory:
  enabled: true
  
  # 记忆存储位置
  storage_path: ~/.openclaw/workspace
  
  # 短期记忆配置
  short_term:
    max_messages: 1000          # 最大保留消息数
    ttl_hours: 24               # 过期时间（小时）
  
  # 长期记忆配置
  long_term:
    auto_summarize: true        # 自动摘要总结
    summarize_threshold: 500    # 触发摘要的消息数
    summarize_template: "请简要总结以下对话的核心要点："
  
  # 记忆检索配置
  retrieval:
    top_k: 5                    # 检索返回的最相关记忆数
    similarity_threshold: 0.7   # 相似度阈值
```

### 5.6 定时任务（Cron）配置

定时任务允许你预设周期性执行的操作，非常适合自动化运维场景。

```yaml
cron:
  enabled: true
  
  # 时区设置
  timezone: "Asia/Shanghai"
  
  # 任务列表
  jobs:
    # 示例 1：每天早上 9 点发送天气
    - id: daily_weather
      name: "每日天气提醒"
      schedule: "0 9 * * *"          # Cron 表达式：每天 9:00
      action: tool                    # 执行类型：tool | agent | webhook
      tool: web_fetch                 # 调用的工具名称
      params:
        url: "https://wttr.in/beijing?format=3"

    # 示例 2：每小时检查机器人状态
    - id: robot_health_check
      name: "机器人健康检查"
      schedule: "0 * * * *"           # Cron 表达式：每小时整点
      action: agent
      agent: robot-monitor            # 指定执行的 Agent
      task: health_check              # Agent 的任务名称

    # 示例 3：每周一早上生成周报
    - id: weekly_report
      name: "周报生成"
      schedule: "0 9 * * 1"           # Cron 表达式：每周一 9:00
      action: webhook
      url: "https://your-server.com/api/report"
      method: POST

---

## 6. OpenClaw 开发

本节将介绍如何基于 OpenClaw 进行二次开发，包括自定义工具、编写 Agent 技能，以及管理记忆文件。

### 6.1 自定义工具开发

自定义工具是扩展 OpenClaw 能力的主要方式。以下是开发一个自定义机器人控制工具的完整流程。

**第一步：创建工具目录**

```bash
# 创建自定义工具目录
mkdir -p ~/.openclaw/tools

# 创建工具文件
touch ~/.openclaw/tools/robot_control.js
```

**第二步：编写工具代码**

```javascript
// ~/.openclaw/tools/robot_control.js
// 自定义工具：控制机器人移动

/**
 * 工具名称：robot_move
 * 功能描述：控制机器人向指定方向移动一定距离
 * 参数：
 *   - direction: 移动方向（forward | backward | left | right）
 *   - distance: 移动距离（米），必须为正数
 * 返回：机器人移动结果和当前位置
 */
const robot_move_tool = {
  // 工具唯一标识符
  name: "robot_move",
  
  // 工具功能描述（Agent 会读取此描述决定何时调用）
  description: "控制机器人向指定方向移动一定距离。适用于机器人需要改变位置的场景。",
  
  // 参数模式定义（使用 JSON Schema）
  parameters: {
    type: "object",
    properties: {
      direction: {
        type: "string",
        enum: ["forward", "backward", "left", "right"],
        description: "移动方向：forward(前)、backward(后)、left(左)、right(右)"
      },
      distance: {
        type: "number",
        description: "移动距离，单位为米，必须为正数"
      },
      speed: {
        type: "number",
        description: "移动速度，单位m/s，可选，默认为0.5",
        default: 0.5
      }
    },
    required: ["direction", "distance"]
  },
  
  // 工具执行函数（异步）
  handler: async ({ direction, distance, speed = 0.5 }) => {
    // 参数校验：距离必须为正数
    if (distance <= 0) {
      return {
        success: false,
        error: "距离必须为正数"
      };
    }
    
    // 参数校验：距离不能超过最大值（安全限制）
    if (distance > 10) {
      return {
        success: false,
        error: "距离不能超过10米（安全限制）"
      };
    }
    
    try {
      // 调用机器人 SDK 执行移动
      // 注意：这里的 robotSDK 是与具体机器人对接的适配器
      const result = await robotSDK.move({
        direction: direction,
        distance: distance,
        speed: speed
      });
      
      // 返回成功结果
      return {
        success: true,
        position: result.position,      // 当前坐标 (x, y)
        orientation: result.orientation, // 当前朝向角度
        message: `机器人向${direction}移动了${distance}米`
      };
    } catch (error) {
      // 捕获并处理异常
      return {
        success: false,
        error: `移动失败：${error.message}`
      };
    }
  }
};

/**
 * 工具名称：robot_get_status
 * 功能描述：获取机器人当前状态信息
 */
const robot_get_status_tool = {
  name: "robot_get_status",
  description: "获取机器人当前的电池电量、位置、速度等状态信息",
  parameters: {
    type: "object",
    properties: {}
    // 无需参数
  },
  handler: async () => {
    try {
      const status = await robotSDK.getStatus();
      return {
        success: true,
        battery: status.battery,          // 电量百分比
        position: status.position,        // 当前位置
        orientation: status.orientation,   // 当前朝向
        velocity: status.velocity,         // 当前速度
        temperature: status.temperature,   // 核心温度
        timestamp: new Date().toISOString() // 状态时间戳
      };
    } catch (error) {
      return {
        success: false,
        error: `状态查询失败：${error.message}`
      };
    }
  }
};

// 导出工具定义（必须）
module.exports = {
  tools: [robot_move_tool, robot_get_status_tool]
};
```

**第三步：在配置中启用自定义工具**

```yaml
# config.yml
tools:
  enabled: true
  # 添加自定义工具目录
  custom_tools_path: ~/.openclaw/tools
  # 将自定义工具添加到白名单
  allowed_tools:
    - read
    - write
    - robot_move          # 新增：机器人移动工具
    - robot_get_status    # 新增：机器人状态查询
```

**第四步：注册工具到 OpenClaw**

```bash
# 重新加载工具（无需重启 Gateway）
openclaw tools reload

# 查看已加载的工具列表
openclaw tools list
# 输出：
# ┌─────────────────┬─────────────────────────────┐
# │ 工具名称         │ 描述                          │
# ├─────────────────┼─────────────────────────────┤
# │ robot_move      │ 控制机器人向指定方向移动        │
# │ robot_get_status │ 获取机器人当前状态信息         │
# │ read            │ 读取文件内容                   │
# │ write           │ 写入文件内容                   │
# └─────────────────┴─────────────────────────────┘
```

### 6.2 Agent 技能（Skill）编写

技能（Skill）是 OpenClaw 的高级扩展机制，一个 Skill 可以包含多个工具、模板和配置。

**Skill 目录结构**

```
~/.openclaw/skills/
└── robot-control/              # 机器人控制技能目录
    ├── SKILL.md               # 技能定义文件（必须）
    ├── scripts/
    │   ├── move.js            # 移动相关脚本
    │   ├── sensor.js          # 传感器脚本
    │   └── navigation.js      # 导航脚本
    └── config/
        └── default.yml        # 默认配置参数
```

**编写 SKILL.md**

```markdown
# robot-control 技能

## 技能描述

本技能为 OpenClaw Agent 提供机器人控制能力，包括移动、导航、传感器查询等功能。

## 适用场景

- 用户请求控制机器人移动
- 查询机器人当前位置和状态
- 执行预定义的导航任务
- 实时监控机器人电量和工作状态

## 依赖工具

| 工具名称 | 用途 |
|----------|------|
| robot_move | 控制机器人移动 |
| robot_get_status | 获取机器人状态 |
| robot_navigate | 执行路径导航 |

## 使用示例

```
用户：机器人向前移动2米
Agent：调用 robot_move(direction="forward", distance=2)

用户：机器人现在在哪？
Agent：调用 robot_get_status() 并解析返回的位置信息

用户：去厨房
Agent：调用 robot_navigate(target="kitchen")
```

## 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_speed | number | 1.0 | 最大移动速度 m/s |
| safe_distance | number | 0.5 | 障碍物安全距离 m |
| battery_low_threshold | number | 20 | 低电量警告阈值 % |

## 注意事项

- 移动距离单次不超过 10 米（安全限制）
- 速度建议不超过 1.5 m/s（室内环境）
- 电量低于 10% 时建议停止任务并返回充电
```

### 6.3 记忆文件管理

OpenClaw 的记忆系统通过文件系统实现持久化，了解其结构有助于更好地管理 Agent 的知识。

**创建和管理每日日志**

```bash
# 手动创建今日日志
cat > ~/.openclaw/workspace/memory/2026-03-24.md << 'EOF'
# 每日日志 - 2026-03-24

## 今日事件

- 上午：完成了 OpenClaw Gateway 的安装和配置
- 下午：创建了第一个自定义 Agent（my-robot）
- 傍晚：接入了飞书平台，测试消息收发正常

## 任务记录

- ✅ 完成机器人移动工具开发
- ✅ 完成飞书接入配置
- ⏳ 进行中：定时任务配置

## 待办事项

- [ ] 测试机器人导航功能
- [ ] 配置 Discord 频道接入
- [ ] 编写工具使用文档
EOF

echo "日志创建成功"
```

**错题本更新**

```bash
# 更新错题本
cat >> ~/.openclaw/workspace/memory/mistakes.md << 'EOF'

### 日期：2026-03-24

**错误类型**：工具参数校验缺失
**场景**：调用 robot_move 时，距离参数传了负数（-1）
**错误信息**：`robot_move failed: Distance must be positive`
**影响**：机器人拒绝执行，任务中断
**规避方案**：
1. 在调用工具前检查参数是否为正数
2. 使用 `Math.abs()` 对距离取绝对值
3. 在工具内部增加参数校验并返回友好错误信息
**相关代码**：
```javascript
// 错误写法
const result = await robot_move(direction, distance);

// 正确写法
if (distance <= 0) {
  return "错误：距离必须为正数";
}
const safeDistance = Math.abs(distance);
const result = await robot_move(direction, safeDistance);
```
EOF
```

**查看 Agent 长期记忆**

```bash
# 查看 Monica Agent 的长期记忆
cat ~/.openclaw/workspace/agent/monica/MEMORY.md

# 输出示例：
# # Monica 长期记忆
# 
# ## 用户信息
# - 主要用户：霍海杰
# - 联系方式：howe12@126.com
# - 时区：Asia/Shanghai
# 
# ## 项目背景
# - 正在开发具身智能课程体系
# - 课程仓库：/home/nx_ros/Music/every-embodied-course
# 
# ## 已知偏好
# - 喜欢简洁直接的回答
# - 代码需要中文注释
# - 文档使用 docsify 格式
```

---

## 7. 实践代码

### 7.1 OpenClaw 完整配置示例

以下是一个完整的 `config.yml` 配置示例，包含了本节介绍的所有主要功能：

```yaml
# ============================================================
# OpenClaw 完整配置文件
# 版本：1.0
# 最后更新：2026-03-24
# ============================================================

# ---------- 基础配置 ----------
version: "1.0"
mode: "standard"                    # 运行模式：standard | minimal | development

# ---------- AI 模型配置 ----------
model:
  provider: "minimax"               # 模型提供商
  model: "MiniMax-M2.7"             # 模型名称
  api_key: "your-api-key-here"      # API 密钥
  max_tokens: 16384                 # 最大输出 token
  temperature: 0.7                   # 创造性参数（0-1）

# ---------- Gateway 配置 ----------
gateway:
  host: "0.0.0.0"                   # 监听地址
  port: 3000                        # 监听端口
  session_timeout: 3600             # 会话超时（秒）
  log_level: "info"                 # 日志级别

# ---------- 平台接入配置 ----------
channels:
  # 飞书
  feishu:
    enabled: true
    app_id: "cli_xxxxxxxxxxxxxxxx"
    app_secret: "xxxxxxxxxxxxxxxx"
    verification_token: "xxxxxxxx"
    encrypt_key: "xxxxxxxx"
  
  # Discord
  discord:
    enabled: false
    bot_token: ""
  
  # Telegram
  telegram:
    enabled: false
    bot_token: ""

# ---------- 工具配置 ----------
tools:
  enabled: true
  allowed_tools:
    - read
    - write
    - edit
    - exec
    - web_fetch
    - web_search
    - robot_move
    - robot_get_status
  denied_tools: []
  custom_tools_path: ~/.openclaw/tools
  timeout: 30000

# ---------- 记忆配置 ----------
memory:
  enabled: true
  storage_path: ~/.openclaw/workspace
  max_history: 1000
  auto_save: true

# ---------- 定时任务配置 ----------
cron:
  enabled: true
  timezone: "Asia/Shanghai"
  jobs:
    - id: daily_weather
      schedule: "0 9 * * *"
      action: tool
      tool: web_fetch
      params:
        url: "https://wttr.in/beijing?format=3"

# ---------- 技能配置 ----------
skills:
  auto_load: true
  paths:
    - ~/.openclaw/skills
    - ~/.npm-global/lib/node_modules/openclaw/skills
```

### 7.2 定时任务配置示例

**定时任务场景一：机器人定时巡检**

```yaml
cron:
  enabled: true
  timezone: "Asia/Shanghai"
  
  jobs:
    # 每小时执行一次机器人巡检
    - id: robot_patrol
      name: "机器人定时巡检"
      schedule: "0 * * * *"          # 每小时整点
      action: agent
      agent: robot-guard              # 值班机器 Agent
      task: patrol
    
    # 每天早上8点发送机器人状态摘要
    - id: morning_status
      name: "早间状态报告"
      schedule: "0 8 * * *"
      action: agent
      agent: robot-monitor
      task: send_morning_report
```

**定时任务场景二：课程内容自动更新**

```yaml
    # 每天凌晨2点同步飞书课程文档
    - id: sync_feishu_docs
      name: "飞书文档同步"
      schedule: "0 2 * * *"
      action: webhook
      url: "https://your-server.com/api/feishu-sync"
      method: POST
      headers:
        Authorization: "Bearer your-token"
```

### 7.3 工具调用示例

**场景一：具身智能任务执行**

```javascript
// 具身智能任务执行示例
async function execute_embodied_task(task) {
  // 1. 理解用户指令
  const plan = await agent.think(task);
  
  // 2. 分步执行
  const steps = plan.steps;
  for (const step of steps) {
    console.log(`执行步骤：${step.description}`);
    
    // 调用相应工具
    const result = await tools.call(step.tool, step.params);
    
    // 3. 处理结果和反馈
    if (!result.success) {
      console.error(`步骤失败：${result.error}`);
      // 根据错误类型决定是重试还是调整策略
      if (result.retryable) {
        console.log("尝试备用方案...");
        const altResult = await tools.call(step.alt_tool, step.params);
      }
    }
    
    // 4. 等待执行稳定（具身动作需要物理时间）
    await sleep(result.estimated_duration || 1000);
  }
  
  // 5. 返回最终结果
  return { success: true, final_position: await tools.call("robot_get_status") };
}
```

**场景二：多 Agent 协作任务**

```javascript
// 多 Agent 协作示例：用户要求"规划并执行机器人到厨房取水"
// 由三个 Agent 协作完成：
//   - Richard（规划者）：制定行动计划
//   - Ross（执行者）：执行具体动作
//   - Angela（质检员）：验证执行结果

async function collaborative_task(task) {
  // Step 1: Richard 制定计划
  const plan = await agents.richard.think(task);
  // 输出：{ steps: ["走到厨房", "拿起水杯", "返回"], estimated_time: "5分钟" }
  
  // Step 2: Ross 执行计划（带 Angela 监控）
  let step_index = 0;
  for (const step of plan.steps) {
    // Ross 执行当前步骤
    const result = await agents.ross.execute(step);
    
    // Angela 验证执行结果
    const verification = await agents.angela.verify(step, result);
    
    if (!verification.passed) {
      // 验证失败，记录并尝试修复
      await agents.ross.retry(step, verification.issues);
    }
    
    step_index++;
  }
  
  // Step 3: 返回完成报告
  return {
    success: true,
    task: task,
    steps_completed: step_index,
    total_time: Date.now() - start_time
  };
}
```

---

## 练习题

### 基础题

**1. OpenClaw 的三大核心组件是什么？**

<details>
<summary>点击查看答案</summary>

OpenClaw 的三大核心组件是：

- **Gateway（网关）**：OpenClaw 的核心守护进程，负责接收消息、管理 Session 和 Agent、维持系统运行
- **Agent（智能体）**：执行具体任务的"工作者"，拥有角色、工具集、记忆和技能
- **Session（会话）**：代表一次完整的交互会话，管理对话历史和上下文

</details>

**2. OpenClaw 的记忆系统分为哪三层？请简要说明每层的特点。**

<details>
<summary>点击查看答案</summary>

OpenClaw 的记忆系统分为三层：

| 层次 | 存储位置 | 生命周期 | 特点 |
|------|----------|----------|------|
| **上下文记忆** | LLM 上下文窗口 | 当前会话 | 容量有限（取决于模型），直接参与推理 |
| **短期记忆** | Session 历史 | 当前会话 | 存储近期对话，可用于检索增强 |
| **长期记忆** | 本地文件（Markdown/JSON） | 跨会话 |几乎无限容量，存储用户偏好、历史经验 |

</details>

**3. 在具身智能系统中，OpenClaw 扮演什么角色？**

<details>
<summary>点击查看答案</summary>

在具身智能系统中，OpenClaw 扮演"协调中枢"或"智能管家"的角色：

- **相当于机器人的"大脑皮层"**：负责思考、对话、记忆
- **与下层控制系统的桥梁**：通过工具调用与 ROS、机械臂 SDK 等交互
- **不直接控制运动**：具体的运动控制仍由专业控制器完成

</details>

**4. 如何使用 npm 全局安装 OpenClaw？**

<details>
<summary>点击查看答案</summary>

使用以下命令安装和验证：

```bash
# 全局安装
npm install -g openclaw

# 验证安装
openclaw --version

# 初始化配置（交互式）
openclaw init
```

</details>

**5. 6 Agent 协作框架中，哪两个 Agent 分别负责"架构设计"和"测试验证"？**

<details>
<summary>点击查看答案</summary>

- **Richard**（架构设计师）：负责设计系统架构，制定技术方案
- **Angela**（质量分析员）：负责测试验证，质量评估

</details>

### 进阶题

**1. 为什么具身智能系统需要 OpenClaw 这样的 Agent 框架，而不能直接用大模型控制机器人？**

<details>
<summary>点击查看答案</summary>

具身智能系统需要 OpenClaw 的原因：

**① 响应时间不匹配**
- 大模型推理通常需要秒级时间（如 GPT-4 单次推理可能需要 3-5 秒）
- 机器人运动控制需要毫秒级实时响应
- OpenClaw 通过工具调用解耦：慢速推理（规划）由大模型负责，快速执行由专用控制器负责

**② 工具调用能力**
- 大模型本身无法直接操作文件系统、网络服务、机器人硬件
- OpenClaw 提供了标准化的工具系统，让 Agent 能够调用任意外部能力
- 这使得"感知-规划-执行"的闭环成为可能

**③ 多 Agent 协作需求**
- 复杂任务需要多个专业 Agent 分工（如规划者、执行者、质检员）
- 大模型是单实例的，无法原生支持多 Agent 并行协作
- OpenClaw 的 6 Agent 框架天然支持任务分解和并行执行

**④ 记忆和经验积累**
- 大模型没有持久化记忆，关闭对话后无法记住之前发生的事
- OpenClaw 的三层记忆系统让 Agent 能够跨会话积累经验
- 这对于需要长期学习进化的具身智能至关重要

**⑤ 多平台接入**
- 具身智能机器人需要与用户交互，但用户可能在飞书、Discord、Telegram 等不同平台
- OpenClaw 统一接入这些平台，提供一致的交互体验

</details>

**2. 请设计一个自定义工具，用于控制机器人夹爪（机械臂末端执行器）抓取物体。工具需要包含完整的定义和执行逻辑。**

<details>
<summary>点击查看答案</summary>

```javascript
// 自定义工具：机器人夹爪控制
const robot_gripper_tool = {
  name: "robot_gripper",
  description: "控制机器人夹爪开合以抓取或释放物体。适用于需要操作物体的场景。",
  
  parameters: {
    type: "object",
    properties: {
      action: {
        type: "string",
        enum: ["open", "close", "release"],
        description: "夹爪动作：open(打开)、close(抓取)、release(释放)"
      },
      force: {
        type: "number",
        description: "抓取力度（百分比），范围 0-100，仅 close 时有效",
        default: 50
      },
      object_type: {
        type: "string",
        description: "被抓取物体的类型，用于调整抓取策略",
        default: "generic"
      }
    },
    required: ["action"]
  },
  
  handler: async ({ action, force = 50, object_type = "generic" }) => {
    // 参数校验
    if (action === "close" && (force < 0 || force > 100)) {
      return {
        success: false,
        error: "力度必须在 0-100 之间"
      };
    }
    
    try {
      switch (action) {
        case "open":
          // 打开夹爪
          await robotSDK.gripper.open();
          return { success: true, state: "opened", message: "夹爪已打开" };
        
        case "close":
          // 抓取物体
          // 根据物体类型调整抓取策略
          const gripConfig = getGripConfig(object_type);
          await robotSDK.gripper.close({
            force: force,
            max_gap: gripConfig.maxGap,
            target_position: gripConfig.targetPosition
          });
          
          // 验证抓取是否成功
          const grip_success = await robotSDK.gripper.isHolding();
          return {
            success: grip_success,
            state: grip_success ? "holding" : "empty",
            message: grip_success 
              ? `已成功抓取${object_type}类型物体` 
              : "抓取失败，夹爪内无物体"
          };
        
        case "release":
          // 释放物体
          await robotSDK.gripper.release();
          return { success: true, state: "released", message: "已释放物体" };
        
        default:
          return { success: false, error: "未知动作类型" };
      }
    } catch (error) {
      return { success: false, error: `夹爪控制失败：${error.message}` };
    }
  }
};

// 根据物体类型获取抓取配置
function getGripConfig(objectType) {
  const configs = {
    small: { maxGap: 0.02, targetPosition: 0.01 },    // 小物体
    medium: { maxGap: 0.05, targetPosition: 0.03 },    # 中等物体
    large: { maxGap: 0.10, targetPosition: 0.06 },     # 大物体
    generic: { maxGap: 0.05, targetPosition: 0.03 }    # 通用
  };
  return configs[objectType] || configs.generic;
}

module.exports = { tools: [robot_gripper_tool] };
```

</details>

**3. 定时任务的 Cron 表达式 `0 9 * * 1` 表示什么时间？请设计一个适合具身智能机器人"每小时电量检查并报告"的 Cron 表达式。**

<details>
<summary>点击查看答案</summary>

**`0 9 * * 1` 的含义：**

- `0`：第 0 分钟
- `9`：早上 9 点
- `*`：每天（任何日期）
- `*`：每月（任何月份）
- `1`：每周一

**所以 `0 9 * * 1` 表示：每周一早上 9:00**

**具身智能机器人电量检查的 Cron 表达式设计：**

| 场景 | Cron 表达式 | 含义 |
|------|-------------|------|
| 每小时整点检查 | `0 * * * *` | 每小时第 0 分钟执行 |
| 每30分钟检查一次 | `0,30 * * * *` | 每小时第 0 和 30 分钟执行 |
| 工作时间每小时检查 | `0 9-18 * * 1-5` | 工作日（周一至周五）9:00-18:00 每小时检查 |
| 关键任务前检查 | `0 */2 * * *` | 每2小时检查一次 |

**推荐方案（具身智能机器人场景）：**

```yaml
cron:
  jobs:
    # 常规每小时电量检查
    - id: hourly_battery_check
      name: "每小时电量检查"
      schedule: "0 * * * *"          # 每小时整点
      action: agent
      agent: robot-monitor
      task: battery_check
    
    # 电量低于 20% 时每 30 分钟检查一次（通过 separate cron 实现）
    - id: frequent_battery_check
      name: "低电量加强监控"
      schedule: "*/30 * * * *"       # 每 30 分钟
      action: tool
      tool: robot_get_status
      # 配合 agent 逻辑判断是否需要充电
```

</details>

---

## 本章小结

| 概念 | 说明 |
|------|------|
| **OpenClaw** | 开源 AI Agent 框架，提供模块化运行时、多平台接入、工具系统和记忆系统 |
| **核心组件** | Gateway（网关）、Agent（智能体）、Session（会话） |
| **工具系统** | 可扩展的工具调用机制，支持内置工具和自定义工具 |
| **记忆系统** | 三层记忆架构：上下文记忆 → 短期记忆 → 长期记忆 |
| **6 Agent 框架** | Monica（协调）、Richard（架构）、Ross（研发）、Angela（测试）、Daisy（情报）、Wendy（课程） |
| **平台接入** | 支持飞书、Discord、Telegram、WhatsApp 等多个平台 |
| **技能（Skill）** | 可扩展的功能模块，包含工具、脚本和配置 |
| **错题本机制** | 记录 Agent 错误并积累规避经验，持续自我改进 |

---

## 延伸阅读

1. **OpenClaw 官方文档**：<https://github.com/howieone/openclaw>
2. **LangChain Agent 架构**：[LangChain Agents 官方文档](https://python.langchain.com/docs/concepts/agents/)
3. **MetaGPT 多智能体框架**：[MetaGPT GitHub](https://github.com/geekan/MetaGPT)
4. **Cron 表达式教程**：[Crontab.guru](https://crontab.guru/)——在线 Cron 表达式生成器和解释器
5. **飞书开放平台开发文档**：[飞书开发者平台](https://open.feishu.cn/document/home)

---

## 学有余力

如果你对 OpenClaw 感兴趣，可以进一步探索以下方向：

- **接入更多平台**：尝试接入钉钉、企业微信，实现全平台覆盖
- **开发更多自定义工具**：为机器人开发视觉识别、语音合成、运动规划等工具
- **多 Agent 协作实践**：设计一个需要多个 Agent 协作完成的复杂任务
- **记忆系统优化**：研究 RAG（检索增强生成）技术，提升记忆检索精度
- **性能调优**：调整模型参数和工具超时配置，优化系统响应速度

---

*下节课程预告：在 01-5 中，我们将学习具身智能开发环境的搭建，包括 ROS2、Python、Node.js 等关键软件的安装配置，为后续的实践开发做好准备，敬请期待。*
