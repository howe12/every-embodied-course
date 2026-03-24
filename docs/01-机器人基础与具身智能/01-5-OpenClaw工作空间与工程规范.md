# 01-5 OpenClaw工作空间与工程规范

> **前置课程**：01-4 OpenClaw概述与安装部署
> **后续课程**：01-6 多Agent自动化与协作

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：上一节我们完成了OpenClaw的安装部署，你已经可以在本地运行一个AI助手了。但你有没有想过一个问题——当AI助手需要记忆你告诉它的事情、需要和多个Agent协同工作、需要按照工程规范完成任务时，它是如何组织的？本节我们将深入OpenClaw的"大脑"——工作空间（Workspace），了解它是如何通过一套精密的文件结构和工程规范，实现持久记忆、多Agent协作和自动化任务执行的。

想象一下：你对OpenClaw说"帮我记住明天要去开会"，它下次就能主动提醒你。你说"帮我写一个专利"，它会自动分配任务给擅长不同领域的Agent，最后汇总成一份完整的专利文档。这种"有记忆、会协作、懂规范"的能力，正是工作空间赋予OpenClaw的。

---

## 1. OpenClaw工作空间概述

### 1.1 什么是工作空间？

在ROS（机器人操作系统）中，工作空间（Workspace）是一个存放项目代码、配置和编译产物的目录结构。OpenClaw借鉴了这一思想，但它的"工作空间"不是存放机器人代码的，而是存放**AI助手的大脑、记忆和工具配置**的。

**简单来说，OpenClaw工作空间就是AI助手的"家"——它决定了AI助手是谁、能做什么、如何思考、如何记忆。**

| 对比项 | ROS工作空间 | OpenClaw工作空间 |
|--------|------------|-----------------|
| 存放内容 | 机器人代码、功能包 | AI助手身份、记忆、工具配置 |
| 核心文件 | package.xml、CMakeLists.txt | SOUL.md、AGENTS.md、MEMORY.md |
| 组织方式 | 功能包（package） | Agent角色目录 |
| 编译产物 | devel、build、install | 无（纯文本文件） |

### 1.2 工作空间的本质

OpenClaw工作空间的本质是**一个结构化的文件系统**，它通过约定好的文件名和目录结构，让AI能够：

- **知道自己是谁**（通过SOUL.md）
- **知道团队成员是谁**（通过AGENTS.md）
- **记住重要的事情**（通过MEMORY.md和memory目录）
- **配置自己的工具和能力**（通过SKILL.md和TOOLS.md）
- **按照规范执行任务**（通过工程准则）

**一个生活化的比喻：**

- ROS工作空间像是一个**汽车制造厂**，各种零部件（功能包）组装成整车
- OpenClaw工作空间像是一个**人的办公室**，文件柜里放着你的身份、经验、日程和工具

---

## 2. 工作空间目录结构

### 2.1 整体架构

OpenClaw工作空间的目录结构遵循"约定优于配置"的原则，核心目录和文件都有固定的命名规范。

```
~/.openclaw/workspace/          # 工作空间根目录
├── SOUL.md                     # Agent身份定义（我是谁）
├── AGENTS.md                   # 多Agent协作框架
├── MEMORY.md                   # 长期记忆文件
├── HEARTBEAT.md                # 定时任务配置
├── TASK.md                     # 当前任务分配
├── IDENTITY.md                 # 身份标识（头像、签名等）
├── TOOLS.md                    # 工具配置笔记
├── USER.md                     # 用户信息
├── data/                       # 结构化数据目录
├── memory/                     # 记忆文件目录
│   ├── YYYY-MM-DD.md          # 每日日志
│   ├── mistakes.md            # 错题本
│   └── engineering-principles.md  # 工程准则
├── intel/                      # 公共情报目录（Daisy产出）
│   ├── DAILY-INTEL.md         # 每日情报汇总
│   └── data/                   # 情报数据
└── agent/                      # Agent角色目录
    ├── monica/                 # 首席协调官
    │   ├── SOUL.md            # Monica的身份定义
    │   ├── TASK.md            # Monica的任务分配
    │   ├── MEMORY.md          # Monica的长期记忆
    │   ├── memory/            # Monica的个人记忆
    │   │   └── YYYY-MM-DD.md
    │   └── data/              # Monica的私有数据
    ├── richard/               # 架构设计师
    ├── ross/                  # 研发工程师
    ├── angela/                # 质量分析员
    ├── daisy/                 # 嗅探研究员
    └── wendy/                 # 课程编写员
```

### 2.2 目录功能详解

**根目录核心文件**

| 文件 | 作用 | 谁负责维护 |
|------|------|-----------|
| `SOUL.md` | 定义当前Agent的身份、性格、行为准则 | Agent自己 |
| `AGENTS.md` | 定义6 Agent协作框架、职责边界、工作流程 | Monica |
| `MEMORY.md` | 存储重要决策、经验总结、长期目标 | Monica |
| `HEARTBEAT.md` | 配置定时任务（cron jobs） | Monica |
| `TASK.md` | 记录当前正在执行的任务分配 | Monica |
| `IDENTITY.md` | Agent的头像、签名、名称等身份标识 | Agent自己 |
| `TOOLS.md` | 本地工具配置笔记（相机名、SSH别名等） | Agent自己 |
| `USER.md` | 了解用户：偏好、时区、项目背景 | Monica |

**memory目录（记忆系统）**

| 文件 | 作用 | 更新频率 |
|------|------|---------|
| `YYYY-MM-DD.md` | 当天工作日志，记录做了什么、决策、经验 | 每天 |
| `mistakes.md` | 错题本，记录犯过的错误和规避方案 | 每次犯错后 |
| `engineering-principles.md` | 工程准则，规范工作流程 | 定期更新 |

**agent目录（团队成员）**

| Agent | 角色 | 团队职责 |
|-------|------|---------|
| Monica | 首席协调官 | 对话入口、任务分配、进度汇报 |
| Richard | 架构设计师 | 技术方案设计、系统架构 |
| Ross | 研发工程师 | 代码实现、Bug修复 |
| Angela | 质量分析员 | 测试验证、问题审核 |
| Daisy | 嗅探研究员 | 情报收集、技术调研 |
| Wendy | 课程编写员 | 文档编写、知识沉淀 |

---

## 3. 核心文件详解

### 3.1 SOUL.md——Agent的灵魂

**SOUL.md**是定义Agent身份的核心文件。每个Agent都有自己的SOUL.md，它告诉AI：

- **我是谁**（名字、角色、团队定位）
- **我应该怎么做**（行为准则、回复风格）
- **我的核心职责**（每天该做什么）
- **我的工作流程**（如何启动、如何协作）

**示例：Monica的SOUL.md片段**

```markdown
# SOUL.md - Who You Are

你是 **Monica**，6 Agent团队的首席协调官。

## 核心定位
- 你是团队与用户沟通的唯一接口
- 你的职责是分配任务，不是执行任务
- 你必须通过 sessions_spawn 启动子代理

## 行为准则
- Be genuinely helpful, not performatively helpful
- Have opinions — 你可以不同意、可以有自己的偏好
- Be resourceful before asking — 先自己想办法，再提问
- Earn trust through competence — 用能力赢得信任

## 职责边界
| ✅ 应该做 | ❌ 不应该做 |
|----------|-------------|
| 与用户对话 | 直接执行测试命令 |
| 分配任务给子代理 | 越位执行 |
| 协调、汇报 | 代替子代理工作 |
```

**为什么SOUL.md如此重要？**

1. **身份认同**：没有SOUL.md，AI只是一个通用的聊天机器人。有了SOUL.md，它才成为"Monica"或"Ross"
2. **行为一致性**：SOUL.md约束AI的回复风格，避免"今天热情明天冷漠"
3. **角色专业化**：不同Agent有不同SOUL.md，确保专业的人做专业的事

### 3.2 AGENTS.md——团队协作宪法

**AGENTS.md**定义了6 Agent团队的组织架构、工作流程和协作规范。它是团队的"宪法"——所有Agent都必须遵守。

**核心内容结构**

```markdown
# AGENTS.md - Workspace 工作规范

## 1. 启动流程
每次会话开始，Agent必须按顺序：
1. Read SOUL.md — 确定我是谁
2. Read USER.md — 了解用户
3. Read memory/YYYY-MM-DD.md — 当天日志
4. If in MAIN SESSION: Read MEMORY.md — 长期记忆

## 2. 6 Agent协作框架
| Agent | 角色 | 职责 |
|-------|------|------|
| Monica | 首席协调官 | 对话入口、任务分配 |
| Richard | 架构设计师 | 技术方案设计 |
| Ross | 研发工程师 | 代码实现 |
| Angela | 质量分析员 | 测试验证 |
| Daisy | 嗅探研究员 | 情报收集 |
| Wendy | 课程编写员 | 文档编写 |

## 3. 职责边界
- Monica不应该直接执行测试命令
- 测试任务必须分配给Angela或Ross

## 4. 测试/工程任务流程
1. 读取错题本
2. 读取工程准则
3. 分配任务前提取相关规避规则
4. 制定计划
5. 与用户确认审核
6. 分配任务给子代理执行
7. 记录结果到错题本
```

### 3.3 HEARTBEAT.md——定时任务心脏

**HEARTBEAT.md**配置OpenClaw的定时任务功能，让AI能够自动执行周期性工作。

**基本概念**

HEARTBEAT（心跳）是OpenClaw的定时任务机制。它通过cron表达式定义任务执行时间：

```bash
# HEARTBEAT.md 中的 cron 格式
*/5 * * * *    # 每5分钟执行
0 9 * * *      # 每天9点执行
0 */2 * * *    # 每2小时执行
```

**典型配置示例**

```markdown
# HEARTBEAT.md - 定时任务配置

## 课程编写任务

| 时间 | Agent | 任务 |
|------|-------|------|
| 09:00-12:00 | Wendy | 编写当天课程 |
| 14:00-15:00 | Monica | 审核前一天课程 |
| 15:00-18:00 | Wendy | 继续编写课程 |

## 专利编写任务

| 时间 | Agent | 任务 |
|------|-------|------|
| 01:00-07:00 | Ross | 编写专利（每小时1个） |
| 08:00 | Angela | 审核所有专利 |
```

**Cron表达式详解**

| 表达式 | 含义 | 示例 |
|--------|------|------|
| `* * * * *` | 分 时 日 月 周 | 全部 |
| `*/5 * * * *` | 每5分钟 | 监控任务 |
| `0 9 * * *` | 每天9:00 | 早间任务 |
| `0 */2 * * *` | 每2小时 | 定期检查 |
| `0 9 * * 1-5` | 工作日9:00 | 工作日任务 |

---

## 4. 记忆系统详解

### 4.1 为什么AI需要记忆系统？

人类大脑的记忆是有限的，而且会随时间模糊。AI助手面临同样的问题——每次新会话开始，AI"醒来"时是空白的，它不知道上次发生了什么。

OpenClaw的记忆系统解决的就是这个问题：**Memory is limited — 想记住就写下来，Text > Brain。**

**记忆系统的三层结构**

| 层级 | 文件 | 作用 | 生命周期 |
|------|------|------|---------|
| **短期记忆** | `memory/YYYY-MM-DD.md` | 当天工作日志 | 每天 |
| **中期记忆** | `MEMORY.md` | 重要决策、经验总结 | 长期 |
| **长期记忆** | `memory/mistakes.md` | 错误规避、已验证方案 | 永久 |

### 4.2 每日日志（YYYY-MM-DD.md）

**命名规范**：必须是`YYYY-MM-DD.md`格式，如`2026-03-24.md`

**标准模板**

```markdown
# 2026-03-24 工作日志

## 任务
- 编写课程 01-5 OpenClaw工作空间与工程规范
- 审核课程 01-4

## 决策
- 采用与01-3一致的编写风格
- 代码示例使用Python+ROS2

## 经验
- 定时任务cron表达式注意时区问题
- 复杂任务先制定计划再执行

## 问题与解决
- 问题：Git提交冲突
- 解决：先pull再push
```

**写入时机**
- 每次完成关键任务后
- 每天会话结束时
- 做重要决策时

### 4.3 错题本（mistakes.md）

**错题本的核心价值**：不重复犯同样的错误。

**记录格式**

```markdown
## [问题名称] ⚠️

- **现象**: （发生了什么）
- **根因**: （为什么会发生）
- **规避方案**: （怎么避免）
- **状态**: （已记录/已验证/待解决）
- **记录时间**: YYYY-MM-DD
```

**错题本示例**

```markdown
## Gazebo启动后进程崩溃 ⚠️

- **现象**: gzserver启动后立即退出(exit code 255)
- **根因**: 之前测试的gzserver残留进程占用资源
- **规避方案**: 
  ```bash
  pkill -9 -f gzserver
  pkill -9 -f gzclient
  sleep 5
  ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
  ```
- **状态**: ✅ 已验证
- **记录时间**: 2026-03-07
```

### 4.4 工程准则（engineering-principles.md）

**engineering-principles.md**是团队工程实践的经验结晶，它规范了标准工作流程。

**核心原则**

```markdown
# 工程思维准则

## 1. 计划先行原则
做任何任务前，必须先制定详细计划表

## 2. 架构理解原则
创建或分析工程前，先搞清节点拓扑

## 3. 进程清理原则
每次执行ROS工程前，必须清理残留进程

## 4. 错题本原则
每个错误都要记录到错题本

## 5. 验证闭环原则
每个修复必须验证，不能只看到错误消失就结束
```

---

## 5. 6 Agent协作框架工程规范

### 5.1 团队组织架构

6 Agent协作框架是OpenClaw的"团队作战"模式。当用户提出复杂任务时，Monica作为首席协调官，会将任务拆分后分配给不同专业的Agent。

**团队成员及职责**

| Agent | 角色 | 核心技能 | 典型任务 |
|-------|------|---------|---------|
| Monica | 首席协调官 | 对话、任务分配、进度把控 | 接收需求、分配任务、汇报结果 |
| Richard | 架构设计师 | 系统设计、技术选型 | 设计整体方案、评估可行性 |
| Ross | 研发工程师 | 编码、调试、集成 | 写代码、修Bug、系统集成 |
| Angela | 质量分析员 | 测试、验证、质量评估 | 功能测试、性能评估、问题审核 |
| Daisy | 嗅探研究员 | 信息收集、技术调研 | 调研竞品、分析趋势、收集情报 |
| Wendy | 课程编写员 | 文档撰写、知识整理 | 编写教程、沉淀经验、整理文档 |

### 5.2 标准协作流程

**任务分配标准流程**

```
用户需求
   ↓
Monica接收 → 分析任务 → 制定计划
   ↓
与用户确认审核
   ↓
分配任务给子代理（sessions_spawn）
   ↓
子代理执行任务
   ↓
结果汇总 → Monica汇报给用户
```

**任务分配示例**

假设用户说"帮我写一个ROS2导航功能的专利"：

```markdown
## 任务分配：ROS2导航专利编写

### Monica 分析
- 这是一个技术+文档类任务
- 需要：技术方案设计(Richard) + 代码实现(Ross) + 文档撰写(Wendy)

### 分配计划
| Agent | 任务 |
|-------|------|
| Richard | 设计导航专利技术框架和创新点 |
| Ross | 编写核心算法代码和实施例 |
| Wendy | 整合成完整专利文档 |

### 执行
[sessions_spawn] Richard → [sessions_spawn] Ross → [sessions_spawn] Wendy
```

### 5.3 Agent角色定义文件（SOUL.md）

每个Agent的SOUL.md定义了该Agent的身份和行为规范。

**Agent SOUL.md 标准结构**

```markdown
# SOUL.md - [Agent名称]

## 身份定义
- 我是谁
- 我的团队角色
- 我的核心职责

## 行为准则
- ✅ 应该做的
- ❌ 不应该做的

## 工作流程
1. 启动时做什么
2. 收到任务时做什么
3. 完成任务后做什么

## 专业能力
- 技能1
- 技能2
```

### 5.4 任务分配文件（TASK.md）

每个Agent目录下的TASK.md记录当前该Agent被分配的任务。

**TASK.md格式**

```markdown
# TASK.md - 当前任务

## 任务状态
| 任务ID | 描述 | 状态 | 截止时间 |
|--------|------|------|---------|
| T001 | 编写专利第一章 | 🔄 进行中 | 2026-03-25 |
| T002 | 审核T001 | ⏳ 待开始 | 2026-03-25 |

## 当前执行
- 正在执行：T001
- 进度：50%

## 更新记录
- 2026-03-24 14:00: 创建任务 T001, T002
```

### 5.5 记忆文件管理规范

**每日日志规范**

| 维度 | 规范 |
|------|------|
| 命名 | `YYYY-MM-DD.md`，如`2026-03-24.md` |
| 位置 | `memory/` 或 `agent/{agent}/memory/` |
| 内容 | 任务、决策、经验、问题解决 |
| 更新 | 每天结束时或完成关键任务后 |

**长期记忆规范**

| 维度 | 规范 |
|------|------|
| 命名 | `MEMORY.md` |
| 位置 | 根目录或`agent/{agent}/` |
| 内容 | 重要决策、核心经验、长期目标 |
| 更新 | 每周日或积累20条后整理 |

---

## 6. 工具与技能配置规范

### 6.1 TOOLS.md——本地工具笔记

**TOOLS.md**存放Agent的本地环境配置信息，是"私人笔记"。

**典型内容**

```markdown
# TOOLS.md - Local Notes

## 相机
- living-room → 主区域，180°广角
- front-door → 门口，动体触发

## SSH
- home-server → 192.168.1.100, user: admin
- robot-nx → 192.168.1.101, user: nx_ros

## TTS
- 首选语音: "Nova"（温暖，略偏英式）
- 默认扬声器: Kitchen HomePod

## ROS
- ROS_DOMAIN_ID: 30
- 工作空间: ~/ros2_ws
```

### 6.2 IDENTITY.md——身份标识

**IDENTITY.md**定义Agent的身份元数据。

```markdown
# IDENTITY.md - Who Am I?

- **Name:** Monica
- **Creature:** AI Assistant / 首席协调官
- **Vibe:** 专业、高效、友善但有立场
- **Emoji:** 🤖
- **Avatar:** avatars/monica.png
```

### 6.3 SKILL.md——技能定义

**SKILL.md**定义Agent的专业技能和使用方法。

**技能文件存放位置**

```
~/.npm-global/lib/node_modules/openclaw/skills/
├── github/
│   ├── SKILL.md       # 技能使用说明
│   └── scripts/       # 辅助脚本
├── weather/
│   └── SKILL.md
└── ...
```

**SKILL.md标准格式**

```markdown
# SKILL.md - [技能名称]

## 触发条件
什么时候使用这个技能

## 使用方法
1. 步骤1
2. 步骤2

## 参数说明
| 参数 | 说明 | 默认值 |
|------|------|--------|
| param1 | 参数1说明 | default |

## 注意事项
- 注意点1
- 注意点2
```

---

## 7. 定时任务配置规范

### 7.1 HEARTBEAT.md配置

**HEARTBEAT.md**定义定时任务，每个任务包含：时间、Agent、任务内容。

**完整示例**

```markdown
# HEARTBEAT.md - 定时任务配置

## 每日课程编写

| 时间 | Agent | 任务 | 状态 |
|------|-------|------|------|
| 09:00 | Wendy | 编写当天课程第一篇 | ✅ |
| 14:00 | Monica | 审核前一天课程 | ✅ |
| 15:00 | Wendy | 编写当天课程第二篇 | ✅ |

## 专利编写任务

| 时间 | Agent | 任务 | 状态 |
|------|-------|------|------|
| 01:00 | Ross | 人机交互-手势识别专利 | ✅ |
| 02:00 | Ross | 机器人安全-碰撞检测专利 | ✅ |
| 08:00 | Angela | 审核所有专利 | ✅ |
```

### 7.2 Cron任务编写规范

**Cron表达式格式**

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日 (1 - 31)
│ │ │ ┌───────────── 月 (1 - 12)
│ │ │ │ ┌───────────── 星期 (0 - 6，0为周日)
│ │ │ │ │
* * * * *
```

**常用Cron表达式**

| 表达式 | 含义 |
|--------|------|
| `* * * * *` | 每分钟 |
| `*/5 * * * *` | 每5分钟 |
| `0 * * * *` | 每小时整点 |
| `0 9 * * *` | 每天9:00 |
| `0 9 * * 1-5` | 工作日9:00 |
| `*/30 * * * *` | 每30分钟 |

---

## 8. 工程实践示例

### 8.1 典型工作空间文件结构

```
~/.openclaw/workspace/                    # 工作空间根目录
│
├── SOUL.md                               # Monica身份定义
├── AGENTS.md                             # 6 Agent协作框架
├── MEMORY.md                             # Monica长期记忆
├── HEARTBEAT.md                          # 定时任务配置
├── TASK.md                               # 当前任务分配
├── IDENTITY.md                           
├── TOOLS.md                              
├── USER.md                               
│
├── data/                                 # 结构化数据
│   ├── course_progress.json             # 课程进度数据
│   └── patent_status.yaml               # 专利状态数据
│
├── memory/                               # 公共记忆目录
│   ├── 2026-03-24.md                    # 今日工作日志
│   ├── 2026-03-23.md                   # 昨日工作日志
│   ├── mistakes.md                      # 错题本
│   └── engineering-principles.md        # 工程准则
│
├── intel/                                # 公共情报目录
│   ├── DAILY-INTEL.md                   # 每日情报汇总
│   └── data/                            # 原始情报数据
│
└── agent/                               # Agent角色目录
    ├── monica/                          # 首席协调官
    │   ├── SOUL.md                      # Monica身份
    │   ├── TASK.md                      # Monica任务
    │   ├── MEMORY.md                    # Monica长期记忆
    │   ├── memory/                      # Monica个人记忆
    │   │   └── 2026-03-24.md
    │   └── data/                        # Monica个人数据
    │
    ├── richard/                         # 架构设计师
    │   ├── SOUL.md
    │   ├── TASK.md
    │   └── memory/
    │
    ├── ross/                            # 研发工程师
    │   ├── SOUL.md
    │   ├── TASK.md
    │   └── memory/
    │
    ├── angela/                          # 质量分析员
    │   ├── SOUL.md
    │   ├── TASK.md
    │   └── memory/
    │
    ├── daisy/                           # 嗅探研究员
    │   ├── SOUL.md
    │   ├── TASK.md
    │   └── memory/
    │
    └── wendy/                           # 课程编写员
        ├── SOUL.md
        ├── TASK.md
        └── memory/
```

### 8.2 每日日志模板

```markdown
# 2026-03-24 工作日志

## 任务完成情况
| 任务 | 状态 | 说明 |
|------|------|------|
| 课程01-5编写 | ✅ 完成 | 已提交Git |
| 课程01-4审核 | ✅ 完成 | 通过 |
| 专利第一章 | 🔄 进行中 | 完成80% |

## 重要决策
1. 采用docsify格式编写课程
2. 代码示例统一使用Python3

## 经验总结
- 复杂任务先制定计划再执行，效率更高
- Git提交前先pull避免冲突

## 遇到的问题
- Git推送被拒绝（远程有更新）
- 解决：先git pull --rebase，再git push

## 明日计划
- 完成专利第一章
- 开始编写课程01-6
```

### 8.3 定时任务配置示例

```markdown
# HEARTBEAT.md - 课程编写定时任务

## 每日编写计划

| 时间 | Agent | 任务 | Cron |
|------|-------|------|------|
| 09:00-10:00 | Wendy | 编写课程第一部分 | `0 9 * * *` |
| 10:00-11:00 | Wendy | 编写课程第二部分 | `0 10 * * *` |
| 14:00-15:00 | Monica | 审核上午编写内容 | `0 14 * * *` |
| 15:00-16:00 | Wendy | 修订审核反馈 | `0 15 * * *` |

## 课程进度监控

| Cron | 任务 | Agent |
|------|------|-------|
| `*/30 * * * *` | 检查课程进度 | Monica |
| `0 18 * * *` | 日报汇总 | Monica |
```

---

## 9. 工程规范总结

### 9.1 文件命名规范

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 每日日志 | `YYYY-MM-DD.md` | `2026-03-24.md` |
| Agent任务 | `TASK.md` | `agent/ross/TASK.md` |
| Agent记忆 | `MEMORY.md` | `agent/monica/MEMORY.md` |
| 错题本 | `mistakes.md` | `memory/mistakes.md` |
| 定时配置 | `HEARTBEAT.md` | `HEARTBEAT.md` |

### 9.2 内容管理规范

**想记住就写下来，Text > Brain。**

| 场景 | 应该写入的文件 |
|------|--------------|
| 今天做了什么 | `memory/YYYY-MM-DD.md` |
| 重要决策 | `MEMORY.md` |
| 犯过的错误 | `memory/mistakes.md` |
| 工程经验 | `memory/engineering-principles.md` |
| 当前任务 | `TASK.md` |
| 定时任务 | `HEARTBEAT.md` |

### 9.3 协作规范

**6 Agent团队的核心原则**

1. **Monica是对外唯一接口**：用户只和Monica对话，Monica分配任务给团队
2. **专业的事交给专业的人**：测试交给Angela，写代码交给Ross
3. **记忆文件是团队共享资产**：重要经验写入共享文件惠及全员
4. **错题本是团队智慧结晶**：每个错误都是团队进步的阶梯

---

## 练习题

### 基础题

**1. OpenClaw工作空间的根目录在哪里？**

<details>
<summary>点击查看答案</summary>

OpenClaw工作空间的根目录位于 `~/.openclaw/workspace/`。

</details>

**2. SOUL.md文件的作用是什么？**

<details>
<summary>点击查看答案</summary>

SOUL.md是定义Agent身份的核心文件，它告诉AI：
- **我是谁**（名字、角色）
- **我应该怎么做**（行为准则、回复风格）
- **我的核心职责**（每天该做什么）
- **我的工作流程**（如何启动、如何协作）

简单来说，SOUL.md就是AI的"灵魂"——没有它，AI只是一个通用聊天机器人；有了它，AI才成为有身份、有性格的专业助手。

</details>

**3. 6 Agent团队中，各个Agent的角色是什么？**

<details>
<summary>点击查看答案</summary>

| Agent | 角色 | 核心职责 |
|-------|------|---------|
| **Monica** | 首席协调官 | 对话入口、任务分配、进度汇报 |
| **Richard** | 架构设计师 | 技术方案设计、系统架构 |
| **Ross** | 研发工程师 | 代码实现、Bug修复 |
| **Angela** | 质量分析员 | 测试验证、质量评估 |
| **Daisy** | 嗅探研究员 | 情报收集、技术调研 |
| **Wendy** | 课程编写员 | 文档编写、知识沉淀 |

</details>

**4. HEARTBEAT.md的作用是什么？**

<details>
<summary>点击查看答案</summary>

HEARTBEAT.md配置OpenClaw的定时任务功能，让AI能够自动执行周期性工作。它定义：
- 哪些任务需要定时执行
- 任务在什么时间执行（通过cron表达式）
- 哪个Agent负责执行

例如：每天9点自动编写课程，每小时自动收集技术情报等。

</details>

**5. 为什么需要错题本（mistakes.md）？**

<details>
<summary>点击查看答案</summary>

错题本的核心价值是**不重复犯同样的错误**。

工程实践中，同样的错误可能被不同的Agent在不同时间重复犯下。错题本的作用：
1. **记录错误**：现象、根因、规避方案
2. **避免重犯**：其他Agent遇到类似问题时可以查阅
3. **经验沉淀**：团队智慧的可复用资产

正如人类学习的"错题本"——每次考试后的错题整理是进步的关键。

</details>

### 进阶题

**1. 为什么Monica不应该直接执行测试命令？**

<details>
<summary>点击查看答案</summary>

Monica作为首席协调官，职责是**分配任务、协调进度、汇报结果**，而非直接执行任务。具体原因：

1. **专业分工**：测试需要专业的测试环境和工具，Monica不具备
2. **效率考虑**：同时协调和执行会降低效率
3. **质量保证**：Angela作为质量分析员有更专业的测试视角
4. **职责清晰**：越位执行会导致职责边界模糊

**正确的流程**：
```
用户需求 → Monica接收 → 分析任务 → 分配给Angela/Ross执行
                                    ↓
Monica汇报 ← 结果汇总 ← Angela/Ross执行
```

</details>

**2. OpenClaw的记忆系统如何实现"持久记忆"？**

<details>
<summary>点击查看答案</summary>

OpenClaw通过三层记忆结构实现持久记忆：

| 层级 | 文件 | 作用 | 生命周期 |
|------|------|------|---------|
| **短期记忆** | `memory/YYYY-MM-DD.md` | 当天工作日志 | 每天 |
| **中期记忆** | `MEMORY.md` | 重要决策、经验总结 | 长期 |
| **长期记忆** | `memory/mistakes.md` | 错误规避、已验证方案 | 永久 |

**工作原理**：
1. 每次会话开始，Agent读取相关记忆文件
2. 完成任务后，将结果写入当日日志
3. 定期（日/周）整理日志，归入长期记忆文件
4. 遇到错误时，立即记录到错题本

**核心原则**：Memory is limited — 想记住就写下来，Text > Brain。

</details>

**3. 如果你需要为一个新Agent（比如"数据分析师"）建立工作规范，应该创建哪些文件？**

<details>
<summary>点击查看答案</summary>

需要创建以下文件：

**1. Agent定义文件**
```
agent/data_analyst/
├── SOUL.md          # Agent身份定义（我是数据分析师）
├── TASK.md          # 当前任务分配
├── MEMORY.md        # 长期记忆
└── memory/
    └── YYYY-MM-DD.md  # 个人每日日志
```

**2. 更新团队规范**
```
AGENTS.md            # 添加data_analyst到团队列表
```

**3. 更新协作流程**
```
HEARTBEAT.md         # 添加数据分析师的定时任务
TASK.md              # 如果是Monica，需要记录任务分配
```

**SOUL.md需要包含**：
- Agent身份（数据分析师）
- 核心技能（SQL、Python数据分析、统计建模）
- 行为准则
- 工作流程（接收任务→分析数据→输出报告）

</details>

---

## 本章小结

| 概念 | 说明 |
|------|------|
| **工作空间** | AI助手的"家"，存放身份、记忆、工具配置的结构化文件系统 |
| **SOUL.md** | Agent的灵魂，定义身份、行为准则、工作流程 |
| **AGENTS.md** | 团队协作宪法，定义6 Agent框架和协作规范 |
| **HEARTBEAT.md** | 定时任务配置，通过cron表达式定义自动执行的任务 |
| **MEMORY.md** | 长期记忆，存储重要决策和经验 |
| **错题本** | 错误规避记录，防止重复犯错 |
| **6 Agent框架** | Monica协调 + Richard架构 + Ross编码 + Angela测试 + Daisy情报 + Wendy文档 |
| **记忆原则** | Memory is limited — 想记住就写下来，Text > Brain |

---

## 延伸阅读

1. **OpenClaw官方文档**：[OpenClaw GitHub](https://github.com/howieowulf/openclaw)
2. **Cron表达式教程**：<https://crontab.guru/>
3. **6 Agent框架实践**：`~/.openclaw/workspace/AGENTS.md`
4. **工程准则**：`~/.openclaw/workspace/memory/engineering-principles.md`

---

*下节课程预告：在01-6中，我们将学习多Agent自动化与协作——了解如何让6个Agent像一个团队一样高效配合，完成复杂任务，敬请期待。*
