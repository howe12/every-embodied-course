# 01-7 Skill系统与机器人工具链

> **前置课程**：01-6 多Agent自动化与协作
> **后续课程**：01-8 具身智能项目实战

**作者**：霍海杰 | **联系方式**：howe12@126.com

---

> **前置说明**：在前几节课程中，我们学习了 OpenClaw 的安装部署、工作空间工程规范，以及多 Agent 协作框架。你已经了解到，OpenClaw 是一个强大的 AI Agent 系统，支持通过配置来实现复杂的工作流程。但你有没有想过：OpenClaw 是如何调用外部工具的？"帮我查一下天气"、"把这段文字写成飞书文档"、"控制机器人移动"——这些操作是如何实现的？答案就是今天我们要深入探讨的主题：**Skill 系统**。Skill 是 OpenClaw 的核心扩展机制，它让 AI Agent 能够调用各种外部工具和服务，从而拥有"十八般武艺"。掌握 Skill 系统，你就掌握了 OpenClaw 的"万能工具箱"。

---

## 1. Skill 系统概述

### 1.1 什么是 Skill？

在 OpenClaw 中，**Skill（技能）**是一种可配置的扩展单元，它定义了 AI Agent 如何调用外部工具或服务。

你可以把 Skill 理解为"AI 的工具箱"——每个 Skill 负责一个特定的能力领域。比如：

- `weather` Skill 负责查询天气
- `feishu-doc` Skill 负责读写飞书文档
- `robot-control` Skill 负责控制机器人移动
- `pdf` Skill 负责分析 PDF 文档

当用户提出一个请求时，OpenClaw 会自动识别哪个 Skill 最适合处理这个请求，然后调用它来完成任务。这个过程就像人类大脑根据任务需求，调用不同的身体部位或工具一样——想喝水就用手端杯子，想查资料就用眼睛看书。

<img src="./images/skill_overview.jpg" alt="Skill系统概述" style="zoom:50%;" />
*图注：Skill 系统是 AI Agent 连接外部世界的桥梁*

### 1.2 Skill 与工具（Tools）的区别

你可能会问：OpenClaw 中已经有"工具"（Tools）的概念了，为什么还需要 Skill？

这是一个很好的问题。让我们来理清两者的关系：

| 特点 | 工具（Tools） | Skill |
|------|---------------|-------|
| **粒度** | 单一、原子化的操作 | 完整的功能模块，可包含多个操作 |
| **配置方式** | 在代码中直接定义 | 通过 SKILL.md 配置文件声明 |
| **触发方式** | 显式调用 | 通过自然语言描述自动匹配 |
| **复杂度** | 简单操作（如"读取文件"） | 复杂功能（如"分析 PDF 并提取关键信息"） |
| **可复用性** | 低，绑定于具体代码 | 高，独立于对话上下文 |
| **示例** | `read`、`write`、`exec` | `weather`、`feishu-doc`、`robot-control` |

**一个生活化的比喻：**

- **工具（Tools）**就像你的手指——每个手指能做简单的动作（指向、点击、按压）
- **Skill**就像一项技能——比如"弹钢琴"，它需要多个手指协调配合，才能完成一首曲子

在 OpenClaw 的架构中，**Skill 是工具的上层封装**。Skill 可以调用一个或多个底层工具，组合出更强大、更易用的功能。

### 1.3 Skill 在 OpenClaw 中的核心作用

Skill 系统在 OpenClaw 中扮演着至关重要的角色，它是 Agent 能力的"倍增器"：

**1. 扩展能力边界**
原生 OpenClaw 内置的工具是有限的。通过 Skill，Agent 可以调用飞书、GitHub、ROS 机器人、网页搜索等各种外部服务，将能力边界扩展到互联网、云平台、物理世界。

**2. 降低使用门槛**
每个 Skill 都有清晰的"触发描述"（description），Agent 只需要理解用户的自然语言请求，就能自动找到合适的 Skill 来处理。这比让 Agent 记住每个工具的调用方式要简单得多。

**3. 模块化与可维护性**
Skill 以独立文件的形式存在，每个 Skill 的代码和配置都封装在一起。修改或升级一个 Skill，不会影响其他 Skill 的正常工作。

**4. 支持复杂任务**
很多真实任务需要多步骤协作。Skill 之间可以相互调用，形成能力链。比如 `robot-control` Skill 控制机器人抓取物体，`feishu-doc` Skill 将操作日志写入文档——两者配合，完成"机器人巡检并记录"的任务。

---

## 2. OpenClaw Skill 架构

### 2.1 Skill 目录结构

一个标准的 Skill 存放在一个独立的目录中，具有统一的目录结构：

```
~/.openclaw/skills/my-skill/
├── SKILL.md          # Skill 的核心配置文件（必须）
├── references/       # 参考文档目录（可选）
├── scripts/          # 脚本文件目录（可选）
└── data/             # 数据文件目录（可选）
```

**各目录说明：**

| 目录/文件 | 必需 | 说明 |
|-----------|------|------|
| `SKILL.md` | ✅ 必须 | Skill 的核心配置文件，定义名称、描述、触发条件、工具函数等 |
| `references/` | 可选 | 存放参考文档，如 API 文档、使用说明 |
| `scripts/` | 可选 | 存放辅助脚本，如数据预处理脚本 |
| `data/` | 可选 | 存放 Skill 运行时需要的静态数据 |

### 2.2 SKILL.md 文件结构

`SKILL.md` 是 Skill 的灵魂文件，它告诉 OpenClaw：这个 Skill 是做什么的？在什么情况下应该调用它？它提供了哪些函数？

一个典型的 `SKILL.md` 结构如下：

```markdown
# SKILL.md - 我的自定义技能

<description>
当用户提到[关键词/场景]时激活此技能。
</description>

## 工具函数

### 函数名：my_function
描述：执行某个操作
参数：
- param1: 参数1的说明
- param2: 参数2的说明
返回：返回值说明

## 配置说明

- 触发关键词：[trigger keywords]
- 依赖工具：[dependencies]
- 注意事项：[notes]
```

**重要字段说明：**

- **`<description>` 标签**：描述 Skill 的功能和使用场景，这是 OpenClaw 自动匹配 Skill 的核心依据
- **工具函数**：定义 Skill 提供的能力，每个函数对应一个可调用的操作
- **触发条件**：描述在什么情况下应该激活这个 Skill

### 2.3 available_skills 配置

要让 OpenClaw 知道有哪些可用的 Skill，需要在配置文件中声明它们。OpenClaw 的主配置文件中有一个 `available_skills` 字段：

```json
{
  "available_skills": [
    {
      "name": "weather",
      "location": "~/.openclaw/skills/weather/SKILL.md"
    },
    {
      "name": "robot-control",
      "location": "~/.openclaw/skills/robot-control/SKILL.md"
    },
    {
      "name": "feishu-doc",
      "location": "~/.npm-global/lib/node_modules/openclaw/extensions/feishu/skills/feishu-doc/SKILL.md"
    }
  ]
}
```

**配置说明：**

| 字段 | 说明 |
|------|------|
| `name` | Skill 的名称，用于在触发时引用 |
| `location` | SKILL.md 文件的绝对路径 |

> **注意**：`~` 表示用户主目录，如 `/home/nx_ros/`。

### 2.4 Skill 触发机制

OpenClaw 是如何知道在什么情况下调用哪个 Skill 的呢？答案是**自动语义匹配**。

当你发送一条消息时，OpenClaw 会：

1. **解析消息内容**：提取关键意图和实体
2. **遍历可用 Skill**：检查每个 Skill 的 `<description>` 描述
3. **语义匹配**：判断哪个 Skill 的描述与当前请求最匹配
4. **激活 Skill**：调用被匹配到的 Skill 来处理请求

**示例流程：**

```
用户消息："帮我查一下北京明天天气怎么样"

     │
     ▼
┌────────────────────────┐
│  OpenClaw 解析意图      │
│  关键词：北京、天气、查询 │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  遍历 available_skills │
│  匹配 weather Skill     │
│  description 匹配度最高 │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  调用 weather Skill     │
│  获取北京明天天气数据   │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  返回结果给用户         │
│  "北京明天多云，15-22℃" │
└────────────────────────┘
```

这种基于描述的触发机制非常灵活——你不需要记住具体的命令格式，只需要用自然语言描述你的需求，OpenClaw 就会自动选择合适的 Skill。

---

## 3. 常用内置 Skill

OpenClaw 提供了一系列开箱即用的内置 Skill，覆盖文档处理、代码开发、数据分析等多个领域。下面我们逐一介绍。

### 3.1 飞书系列 Skill

飞书（Feishu）是字节跳动推出的企业协作平台，OpenClaw 提供了完整的飞书 Skill 套件。

| Skill 名称 | 功能 | 场景 |
|-----------|------|------|
| `feishu-doc` | 读写飞书云文档 | 创建周报、写入会议记录 |
| `feishu-wiki` | 飞书知识库操作 | 查询知识库文章、创建节点 |
| `feishu-drive` | 飞书云空间管理 | 浏览文件夹、移动文件 |
| `feishu-bitable` | 多维表格操作 | 管理数据表格、增删改查记录 |

**feishu-doc 示例场景：**

```
用户：帮我把这段内容写入飞书文档
Agent → feishu-doc Skill → 调用飞书 API → 内容写入指定文档
```

**feishu-wiki 示例场景：**

```
用户：在知识库中创建一个"机器人巡检记录"的页面
Agent → feishu-wiki Skill → 在指定知识库节点下创建新页面
```

> **使用前提**：需要在飞书开放平台创建应用，并配置相应的权限（ scopes），详见飞书官方文档。

### 3.2 开发效率类 Skill

| Skill 名称 | 功能 | 场景 |
|-----------|------|------|
| `github` | GitHub 操作（issues、PRs、CI） | 查看 PR 状态、创建 issue |
| `coding-agent` | 代码编写代理 | 生成代码、代码审查、PR 创建 |
| `clawhub` | ClawHub CLI 工具 | 搜索安装 Skill、发布自定义 Skill |

**github Skill 示例场景：**

```bash
# 查看某个仓库的 open issues
用户："帮我看看 langchain/langchain 有哪些 bug 类型的问题？"
Agent → github Skill → gh issue list --label bug --repo langchain/langchain
```

**coding-agent Skill 示例场景：**

```bash
# 生成一个 ROS2 节点代码
用户："帮我写一个 ROS2 订阅者节点，订阅 /cmd_vel 话题"
Agent → coding-agent → 生成 Python 代码并写入文件
```

### 3.3 数据处理类 Skill

| Skill 名称 | 功能 | 场景 |
|-----------|------|------|
| `weather` | 天气查询 | "北京明天天气怎么样？" |
| `video-frames` | 视频帧提取 | 从视频中截取关键帧 |
| `pdf` | PDF 文档分析 | 提取 PDF 中的文字和图片 |
| `multi-search-engine` | 多引擎搜索 | 同时在多个搜索引擎中搜索 |

**weather Skill 示例场景：**

```
用户：上海周末会下雨吗？
Agent → weather Skill → 查询 wttr.in 或 Open-Meteo API → 返回：
"上海周六多云，周日有小雨，建议带伞出行。"
```

**video-frames Skill 示例场景：**

```
用户：从这个机器人演示视频中，每隔 5 秒截取一帧
Agent → video-frames Skill → 使用 ffmpeg 提取帧 → 保存为图片文件
```

### 3.4 机器人专用 Skill

| Skill 名称 | 功能 | 平台 |
|-----------|------|------|
| `robot-control` | 通用机器人控制 | 通用 |
| `turtlebot3-control` | TurtleBot3 专用控制 | TurtleBot3 |
| `agent-reach` | 平台工具接入 | 多平台 |

**robot-control 典型使用场景：**

```
用户：让机器人向前移动 1 米
Agent → robot-control Skill → ROS2 话题发布 → robot_node 接收 → 执行运动
```

**turtlebot3-control 典型使用场景：**

```
用户：TurtleBot3 原地左转 90 度
Agent → turtlebot3-control Skill → /cmd_vel 话题发布角速度命令
```

**agent-reach 典型使用场景：**

```
用户：帮我配置 Twitter 平台接入
Agent → agent-reach Skill → 引导用户完成 OAuth 授权流程
```

---

## 4. 自定义 Skill 开发

除了使用内置 Skill，你还可以开发自己的 Skill 来满足特定需求。自定义 Skill 开发分为几个步骤：

### 4.1 创建 Skill 目录结构

首先，创建一个新的 Skill 目录：

```bash
# 在 ~/.openclaw/skills/ 下创建新 Skill
mkdir -p ~/.openclaw/skills/my-custom-skill
cd ~/.openclaw/skills/my-custom-skill

# 创建必要的子目录
mkdir -p references scripts data
```

目录结构如下：

```
~/.openclaw/skills/my-custom-skill/
├── SKILL.md          # 稍后编写
├── references/       # API 文档、参考说明
├── scripts/          # 辅助脚本
└── data/             # 静态数据文件
```

### 4.2 编写 SKILL.md

SKILL.md 是 Skill 的核心配置。下面是一个完整的示例：

```markdown
# SKILL.md - 我的自定义天气预警 Skill

<description>
当用户询问某个城市的空气质量（AQI）、空气污染等级或需要空气预警信息时，激活此技能。
触发关键词包括：空气质量、AQI、空气污染、PM2.5、雾霾、空气预警。
</description>

## 工具函数

### 函数名：get_air_quality
描述：查询指定城市的实时空气质量
参数：
- city: 城市名称（中文或英文）
返回：包含 AQI、PM2.5、PM10、污染等级、建议等字段的 JSON 对象

### 函数名：get_air_forecast
描述：查询指定城市未来 3 天的空气质量预报
参数：
- city: 城市名称
返回：每天的 AQI 范围和污染等级

## 配置说明

- 触发关键词：空气质量、AQI、空气污染、PM2.5、雾霾
- 依赖接口：Open-Meteo Air Quality API（免费，无需 API Key）
- 数据来源：https://open-meteo.com/
- 注意事项：
  1. AQI 标准采用美国 EPA 标准（0-500）
  2. 中国标准请使用aqicn.org接口
```

### 4.3 工具函数的实现

SKILL.md 中声明的函数，需要在实际代码中实现。对于 OpenClaw 内置的工具函数（如 `web_fetch`、`exec`），直接在 Skill 描述中声明即可使用。对于需要自定义实现的场景，可以通过 `scripts/` 目录下的脚本实现。

**示例：web_fetch 实现空气质量查询**

在 SKILL.md 中声明的 `get_air_quality` 函数，可以直接利用 OpenClaw 内置的 `web_fetch` 工具来实现：

```
当用户询问空气质量时，我将：
1. 使用 web_fetch 工具请求 Open-Meteo Air Quality API
2. 传入城市坐标（经纬度）和查询参数
3. 解析返回的 JSON 数据
4. 按以下格式整理结果：
   - 城市：[城市名]
   - AQI：[数值]
   - PM2.5：[数值] μg/m³
   - 污染等级：[优良/轻度/中度/重度/严重]
   - 健康建议：[根据等级给出户外活动建议]
5. 返回整理后的结果
```

**示例：使用 exec 执行本地脚本**

如果需要执行本地脚本，可以使用 `exec` 工具：

```bash
# scripts/query_aqi.sh
#!/bin/bash
# 空气质量查询脚本
# 用法：./query_aqi.sh <城市名>

CITY=$1
echo "正在查询 $CITY 的空气质量..."

# 这里可以调用外部 API 或本地数据库
# 返回 JSON 格式结果
```

### 4.4 触发条件的配置技巧

Skill 的触发依赖于 `<description>` 描述。好的描述能让 Skill 被准确匹配。以下是一些编写技巧：

**✅ 好的描述示例：**

```markdown
<description>
当用户需要查询天气信息时激活，包括：
- 当前温度、湿度、风速
- 未来几天的天气预报
- 特殊天气预警（暴雨、台风、高温）
触发词：天气、多少度、下雨吗、冷不冷
</description>
```

**❌ 不好的描述示例：**

```markdown
<description>
查询天气
</description>
```

**技巧总结：**

| 技巧 | 说明 | 示例 |
|------|------|------|
| **列举场景** | 列出所有可能的使用场景 | "当用户需要查天气、查温度时" |
| **包含关键词** | 列出常见触发词 | "触发词：天气、多少度" |
| **说明输入输出** | 明确函数的输入参数和返回值 | "输入城市名，返回温度和湿度" |
| **避免歧义** | 描述要清晰，不要有歧义 | "不是 XX 场景，而是 XX 场景" |

### 4.5 注册 Skill

创建完 Skill 后，需要在 OpenClaw 配置文件中注册：

```json
{
  "available_skills": [
    // ... 其他 Skill
    {
      "name": "my-custom-skill",
      "location": "~/.openclaw/skills/my-custom-skill/SKILL.md"
    }
  ]
}
```

注册后，重启 OpenClaw Gateway 即可生效。

---

## 5. ClawHub 与 Skill 市场

### 5.1 什么是 ClawHub？

**ClawHub**（`clawhub.com`）是 OpenClaw 的官方 Skill 市场，类似于 VS Code 的插件市场。你可以在这里搜索、安装、更新和发布 Skill。

ClawHub 提供了一个命令行工具 `clawhub`，让你在终端中就能完成所有操作。

### 5.2 ClawHub CLI 安装

如果尚未安装，执行以下命令：

```bash
# 通过 npm 全局安装
npm install -g clawhub

# 验证安装
clawhub --version
```

### 5.3 搜索和安装 Skill

```bash
# 搜索 Skill
clawhub search robot
# 输出：
# - robot-control    通用机器人控制
# - turtlebot3       TurtleBot3 专用控制
# - ROS2-tools       ROS2 工具链集成

# 安装 Skill
clawhub install robot-control
# 输出：Installing robot-control... Done!

# 查看已安装的 Skill
clawhub list
```

### 5.4 发布自定义 Skill

如果你开发了一个很好用的 Skill，可以发布到 ClawHub 与社区分享：

```bash
# 登录 ClawHub 账号
clawhub login

# 发布 Skill（当前目录必须是 Skill 根目录）
clawhub publish

# 发布时需要填写：
# - Skill 名称
# - 版本号（语义化版本，如 1.0.0）
# - 描述
# - 分类标签
```

### 5.5 更新 Skill

```bash
# 更新单个 Skill
clawhub update robot-control

# 更新所有已安装的 Skill
clawhub update --all

# 查看可更新的 Skill
clawhub outdated
```

---

## 6. 机器人工具链集成

### 6.1 ROS2 工具链

ROS2（Robot Operating System 2）是机器人软件开发的核心框架。OpenClaw 可以与 ROS2 无缝集成，形成强大的机器人开发工具链。

**ROS2 工具链全景图：**

| 工具类别 | 常用工具 | OpenClaw 集成方式 |
|---------|---------|------------------|
| **核心通信** | rclcpp、rclpy、rclcpp_action | 通过话题/服务调用 |
| **可视化** | rviz2、rviz | exec 工具启动 |
| **仿真** | Gazebo、Ignition | exec 工具启动 |
| **调试** | ros2 topic echo、ros2 service call | exec 工具执行 |
| **构建** | colcon、ament | exec 工具执行 |
| **导航** | Nav2（navigation2） | robot-control Skill |

**OpenClaw 与 ROS2 的协作模式：**

```
用户自然语言指令
       │
       ▼
┌─────────────────┐
│  OpenClaw Agent │
│  （理解意图）   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  robot-control  │
│  Skill          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ROS2 话题/服务  │
│  /cmd_vel 等    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  机器人/仿真器   │
│  Gazebo / 实体   │
└─────────────────┘
```

### 6.2 仿真环境工具

在没有实体机器人的情况下，可以使用仿真环境进行开发和测试。

**常用仿真环境：**

| 仿真器 | 特点 | 适用场景 |
|--------|------|----------|
| **Gazebo** | 强大、物理引擎成熟、社区活跃 | 室外、移动机器人 |
| **Webots** | 跨平台、易用、内置大量机器人模型 | 教育、研究 |
| **Isaac Sim** | NVIDIA 出品、高保真渲染 | 精密操作、仿真到现实 |
| **Unity/Unreal** | 游戏引擎改写、高保真渲染 | 数字孪生、视觉仿真 |

**在 OpenClaw 中启动 Gazebo 仿真：**

```bash
# 使用 exec 工具启动 Gazebo 仿真
exec: "gazebo /path/to/robot.world"
```

### 6.3 调试与监控工具

机器人开发离不开调试和监控。以下是常用的调试工具，以及它们在 OpenClaw 中的使用方式：

**话题（Topic）调试：**

```bash
# 查看当前活跃话题
ros2 topic list

# 查看话题消息频率
ros2 topic hz /cmd_vel

# 实时监听话题数据
ros2 topic echo /scan
```

**参数（Parameter）调试：**

```bash
# 列出节点参数
ros2 param list

# 获取参数值
ros2 param get /robot_node speed

# 设置参数值
ros2 param set /robot_node speed 1.5
```

**节点（Node）调试：**

```bash
# 查看活跃节点
ros2 node list

# 查看节点信息
ros2 node info /robot_node
```

**OpenClaw 中的调试工作流：**

```
用户：帮我检查一下 /scan 话题的数据是否正常
       │
       ▼
OpenClaw → exec: ros2 topic echo /scan
       │
       ▼
解析返回数据 → 检查数据格式和内容 → 返回诊断结果
```

### 6.4 综合实践：OpenClaw + ROS2 开发工作流

下面展示一个典型的开发工作流，演示如何用自然语言控制 ROS2 机器人：

**场景：让 TurtleBot3 机器人执行巡逻任务**

```markdown
用户：让 TurtleBot3 在办公室区域巡逻一圈

Agent 理解 → 分解任务：
1. 启动 TurtleBot3 仿真/连接实体机器人
2. 加载地图
3. 启动自主导航
4. 巡逻完成后返回报告

实际操作（通过 Skill 调用）：
Step 1: exec 启动仿真
   ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py

Step 2: exec 加载导航
   ros2 launch turtlebot3_navigation2 navigation2.launch.py
   map:=/path/to/map.yaml

Step 3: robot-control 发布导航目标点
   - 目标点1: (2.0, 1.0)
   - 目标点2: (4.0, -1.0)
   - 目标点3: (0.0, 0.0) 返回起点

Step 4: feishu-doc 写入巡逻日志
   巡逻完成，共经过 3 个点，总用时 12 分钟
```

---

## 7. 实践代码

### 7.1 自定义 Skill 开发示例

下面我们从头开发一个完整的 Skill：`ros2-toolkit`，用于查询 ROS2 系统状态。

**Step 1：创建目录结构**

```bash
mkdir -p ~/.openclaw/skills/ros2-toolkit/{references,scripts,data}
```

**Step 2：编写 SKILL.md**

```markdown
# SKILL.md - ROS2 工具包 Skill

<description>
当用户需要与 ROS2（Robot Operating System 2）进行交互时激活此技能。
适用场景包括：
- 查询 ROS2 话题（topic）、服务（service）、节点（node）列表
- 监听话题数据
- 调用 ROS2 服务
- 查看和设置参数
- 启动/停止 ROS2  launch 文件
- 检查 ROS2 环境状态
触发关键词：ROS2、话题、服务、节点、rviz、gazebo、launch、colcon
</description>

## 工具函数

### 函数名：list_topics
描述：列出当前 ROS2 系统中所有活跃的话题
参数：无
返回：话题名称列表及类型

### 函数名：echo_topic
描述：实时监听指定话题的消息
参数：
- topic_name: 话题名称（字符串）
- count: 监听消息数量（整数，默认 1）
返回：话题消息内容

### 函数名：list_nodes
描述：列出当前 ROS2 系统中的所有活跃节点
参数：无
返回：节点名称列表

### 函数名：call_service
描述：调用指定的 ROS2 服务
参数：
- service_name: 服务名称（字符串）
- service_type: 服务类型（字符串）
- request_data: 请求数据（对象）
返回：服务响应内容

### 函数名：get_system_status
描述：获取 ROS2 系统整体状态
参数：无
返回：包含话题数、节点数、服务数、参数数的摘要信息

## 配置说明

- 触发关键词：ROS2、ros2、topic、service、node、launch、rviz
- 依赖环境：ROS2 已安装并 source（如 source /opt/ros/jazzy/setup.bash）
- 注意事项：
  1. 某些命令需要 ROS2 环境已初始化
  2. 监听话题是长时间运行操作，默认只监听 1 条消息
  3. 调用服务需要知道正确的服务类型和请求格式
```

**Step 3：编写辅助脚本（可选）**

```bash
# scripts/ros2_status.sh
#!/bin/bash
# 获取 ROS2 系统整体状态

echo "=== ROS2 System Status ==="
echo ""
echo "--- Active Nodes ---"
ros2 node list 2>/dev/null || echo "No nodes running"
echo ""
echo "--- Active Topics ---"
ros2 topic list 2>/dev/null || echo "No topics available"
echo ""
echo "--- Active Services ---"
ros2 service list 2>/dev/null || echo "No services available"
echo ""
echo "--- Parameters ---"
ros2 param list 2>/dev/null || echo "No parameters"
```

### 7.2 Skill 调用示例

以下是用户在 OpenClaw 中调用 Skill 的常见场景：

**场景 1：查询天气**

```
用户：上海明天会下雨吗？

OpenClaw 匹配 → weather Skill
Skill 执行：
  1. web_fetch 请求天气 API
  2. 解析返回数据
  3. 生成回复

返回：上海明天白天多云，傍晚有小雨概率 40%，建议带伞出门。
```

**场景 2：操作飞书文档**

```
用户：在"机器人项目"知识库下，创建一份"周报模板"文档

OpenClaw 匹配 → feishu-wiki Skill
Skill 执行：
  1. feishu_wiki 获取知识库节点列表
  2. feishu_doc create 在指定位置创建文档
  3. 写入预设的周报模板内容

返回：文档创建成功，链接：https://feishu.cn/docx/xxxxxx
```

**场景 3：控制机器人**

```
用户：让机器人停止移动

OpenClaw 匹配 → robot-control Skill
Skill 执行：
  1. 发布 /cmd_vel 话题，设置为全零速度
  2. 等待执行确认
  3. 返回执行结果

返回：机器人已停止。当前位置 (1.23, 0.45)，朝向 180°。
```

### 7.3 机器人工具链集成示例

下面是一个完整的示例，演示如何用 OpenClaw 操控 TurtleBot3：

**示例：TurtleBot3 自主导航巡逻**

```python
#!/usr/bin/env python3
"""
TurtleBot3 自主巡逻脚本
功能：让 TurtleBot3 按预设路径点自主移动

作者：霍海杰
日期：2026-03-24
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav2_simple_commander.robot_navigator import RobotNavigator
import time


class TurtleBot3Patrol(Node):
    """TurtleBot3 巡逻节点"""

    def __init__(self):
        super().__init__('turtlebot3_patrol')
        # 创建速度命令发布者
        self.cmd_vel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.get_logger().info('TurtleBot3 Patrol Node 已启动')

    def move_forward(self, distance=0.5):
        """向前移动指定距离（米）"""
        msg = Twist()
        msg.linear.x = 0.2  # 设置前进速度 0.2 m/s
        duration = distance / 0.2  # 计算需要的时间

        self.get_logger().info(f'前进 {distance} 米...')
        start_time = time.time()

        while time.time() - start_time < duration:
            self.cmd_vel_pub.publish(msg)
            time.sleep(0.1)

        # 停止
        self.stop()

    def turn(self, angle=90):
        """原地旋转指定角度（度）"""
        msg = Twist()
        angular_speed = 0.5  # 角速度 rad/s
        msg.angular.z = angular_speed if angle > 0 else -angular_speed
        duration = abs(angle) / 57.3 / angular_speed  # 角度转弧度 / 角速度

        direction = '左' if angle > 0 else '右'
        self.get_logger().info(f'{direction}转 {abs(angle)} 度...')
        start_time = time.time()

        while time.time() - start_time < duration:
            self.cmd_vel_pub.publish(msg)
            time.sleep(0.1)

        # 停止
        self.stop()

    def stop(self):
        """停止移动"""
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0
        self.cmd_vel_pub.publish(msg)
        self.get_logger().info('机器人已停止')


def main(args=None):
    """主函数：执行方形巡逻路径"""
    rclpy.init(args=args)
    patrol = TurtleBot3Patrol()

    # 定义巡逻路径点（方形路径）
    patrol_points = [
        {'action': 'forward', 'distance': 1.0},
        {'action': 'turn', 'angle': 90},
        {'action': 'forward', 'distance': 1.0},
        {'action': 'turn', 'angle': 90},
        {'action': 'forward', 'distance': 1.0},
        {'action': 'turn', 'angle': 90},
        {'action': 'forward', 'distance': 1.0},
        {'action': 'turn', 'angle': 90},  # 返回初始方向
    ]

    try:
        print("开始执行巡逻任务...")
        for i, point in enumerate(patrol_points):
            print(f"步骤 {i+1}/{len(patrol_points)}: {point}")
            if point['action'] == 'forward':
                patrol.move_forward(point['distance'])
            elif point['action'] == 'turn':
                patrol.turn(point['angle'])
            time.sleep(0.5)  # 每步之间稍作停顿

        print("巡逻任务完成！返回起点。")

    except KeyboardInterrupt:
        print("用户中断，正在停止...")
        patrol.stop()

    finally:
        patrol.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

**在 OpenClaw 中通过 Skill 调用上述脚本：**

```
用户：执行 TurtleBot3 巡逻任务

robot-control Skill 处理：
1. 检测到 TurtleBot3 环境（ros2 topic list 包含 /cmd_vel）
2. 通过 exec 工具运行 patrol_node.py
3. 监控 /cmd_vel 和 /odom 话题确认执行
4. 返回巡逻完成报告
```

---

## 练习题

### 基础题

**1. 什么是 Skill？它与工具（Tools）的主要区别是什么？**

<details>
<summary>点击查看答案</summary>

**Skill** 是 OpenClaw 中的可配置扩展单元，定义 AI Agent 如何调用外部工具或服务。

**Skill 与 Tools 的主要区别：**

| 区别 | Tools | Skill |
|------|-------|-------|
| 粒度 | 单一、原子化操作 | 完整功能模块，可包含多个操作 |
| 配置方式 | 代码中直接定义 | SKILL.md 配置文件声明 |
| 触发方式 | 显式调用 | 自然语言自动匹配 |
| 复杂度 | 简单操作 | 复杂功能 |
| 示例 | read、write、exec | weather、feishu-doc、robot-control |

**类比**：Tools 像手指（做简单动作），Skill 像弹钢琴技能（多手指协调完成复杂曲子）。

</details>

**2. Skill 目录的标准结构是什么？**

<details>
<summary>点击查看答案</summary>

标准 Skill 目录结构：

```
~/.openclaw/skills/<skill-name>/
├── SKILL.md          # 核心配置文件（必须）
├── references/       # 参考文档目录（可选）
├── scripts/          # 脚本文件目录（可选）
└── data/             # 数据文件目录（可选）
```

其中 `SKILL.md` 是必须文件，定义 Skill 的名称、描述、工具函数等核心信息。

</details>

**3. 如何注册一个新的 Skill？**

<details>
<summary>点击查看答案</summary>

在 OpenClaw 配置文件的 `available_skills` 字段中添加 Skill 条目：

```json
{
  "available_skills": [
    {
      "name": "my-skill",
      "location": "~/.openclaw/skills/my-skill/SKILL.md"
    }
  ]
}
```

注册后需要重启 OpenClaw Gateway 才能生效。

</details>

**4. ClawHub 的主要功能有哪些？**

<details>
<summary>点击查看答案</summary>

ClawHub 是 OpenClaw 的官方 Skill 市场，主要功能包括：

- **搜索 Skill**：`clawhub search <keyword>`
- **安装 Skill**：`clawhub install <skill-name>`
- **列出已安装**：`clawhub list`
- **更新 Skill**：`clawhub update <skill-name>`
- **发布 Skill**：`clawhub publish`
- **登录账号**：`clawhub login`

</details>

### 进阶题

**1. 设计一个自定义 Skill，实现"每日机器人状态报告"功能**

<details>
<summary>点击查看答案</summary>

**Skill 名称**：`daily-robot-report`

**SKILL.md 设计：**

```markdown
<description>
当用户需要生成机器人每日状态报告时激活，包括：
- 机器人当前位置和状态
- 今日任务执行记录
- 传感器数据摘要
- 电池电量变化
- 异常告警记录
触发词：日报、状态报告、机器人报告、巡检报告
</description>

## 工具函数

### get_robot_status
描述：获取机器人当前状态
返回：位置、电量、工作模式

### get_task_logs
描述：获取今日任务执行日志
返回：任务名称、时间戳、执行结果

### get_sensor_summary
描述：获取今日传感器数据摘要
返回：各类传感器的统计值（里程、IMU、激光雷达等）

### get_battery_log
描述：获取电池电量变化记录
返回：今日电量曲线和关键时间点

### get_alerts
描述：获取今日异常告警记录
返回：告警类型、时间、内容

## 完整工作流

```python
def generate_daily_report():
    # 1. 获取机器人状态
    status = get_robot_status()

    # 2. 获取任务日志
    logs = get_task_logs()

    # 3. 获取传感器摘要
    sensor = get_sensor_summary()

    # 4. 获取电池记录
    battery = get_battery_log()

    # 5. 获取告警
    alerts = get_alerts()

    # 6. 生成报告（Markdown 格式）
    report = f"""
    # 机器人每日状态报告

    ## 1. 当前状态
    - 位置：{status['position']}
    - 电量：{status['battery']}%
    - 模式：{status['mode']}

    ## 2. 今日任务
    共执行 {len(logs)} 项任务，详见任务日志

    ## 3. 传感器摘要
    {sensor}

    ## 4. 电池曲线
    {battery}

    ## 5. 异常告警
    {'无' if not alerts else alerts}
    """

    # 7. 写入飞书文档
    feishu_doc.write(report)

    return report
```

</details>

**2. 描述 OpenClaw 的 Skill 触发机制，以及如何编写高效的触发描述。**

<details>
<summary>点击查看答案</summary>

**触发机制流程：**

```
用户消息 → 意图解析 → 遍历 available_skills → 语义匹配 → 激活 Skill → 返回结果
```

**各步骤详解：**

1. **解析消息内容**：提取关键词和实体（如城市、时间、动作）
2. **遍历可用 Skill**：检查每个 Skill 的 `<description>` 描述
3. **语义匹配**：计算描述与当前请求的语义相似度
4. **激活 Skill**：调用匹配度最高的 Skill 执行任务

**高效触发描述的编写原则：**

| 原则 | 做法 | 示例 |
|------|------|------|
| **场景列举** | 列出所有适用场景 | "当用户需要查天气、空气质量、穿衣建议时" |
| **关键词覆盖** | 包含常见触发词 | "触发词：天气、多少度、下雨吗" |
| **边界说明** | 明确不触发的场景 | "不是查日历，而是查天气" |
| **输入输出** | 声明函数签名 | "输入城市名，返回温度和天气状况" |
| **避免歧义** | 描述精准、不重叠 | "本 Skill 不处理文档创建，仅处理天气查询" |

**好的描述示例：**

```markdown
<description>
当用户需要查询天气时激活此技能，包括：
- 当前温度、湿度、风速
- 未来 3-5 天天气预报
- 特殊天气预警（暴雨、台风、寒潮、高温）
- 穿衣指数和出行建议
触发词：天气、多少度、下雨吗、冷不冷、热不热、要不要带伞
注意：本技能不查询空气质量（请使用 air-quality Skill）
</description>
```

</details>

**3. 如何将 OpenClaw 与 ROS2 集成，实现自然语言控制机器人？请描述完整的工作流程。**

<details>
<summary>点击查看答案</summary>

**完整工作流程：**

```
用户自然语言 → OpenClaw Agent 理解意图 → robot-control Skill → ROS2 话题/服务 → 机器人执行
```

**Step 1：环境准备**
- ROS2 已安装（如 Ubuntu 22.04 + ROS2 Jazzy）
- OpenClaw 已安装并配置
- robot-control Skill 已注册
- 机器人或仿真器已启动

**Step 2：Agent 理解用户意图**
```
用户：让机器人向前移动 1 米，然后左转 90 度
OpenClaw 解析：识别为运动控制请求，激活 robot-control Skill
```

**Step 3：Skill 分解任务**
```python
# 任务分解
tasks = [
    {'action': 'move_forward', 'distance': 1.0},
    {'action': 'turn_left', 'angle': 90}
]
```

**Step 4：通过 ROS2 话题发布命令**
```bash
# 发布前进命令（0.2 m/s，5秒）
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

# 发布停止命令
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

# 发布旋转命令
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.5}}"
```

**Step 5：监控执行结果**
```bash
# 监听里程计确认移动
ros2 topic echo /odom

# 监听激光雷达确认环境感知
ros2 topic echo /scan
```

**Step 6：返回执行结果**
```
任务执行完成：
- 前进 1.0 米 ✓
- 左转 90 度 ✓
- 当前位置：(2.0, 1.0)，朝向：90°
```

**关键集成点：**

| 集成层 | 技术实现 | OpenClaw 工具 |
|--------|----------|---------------|
| 通信接口 | ROS2 Topic/Service | exec 工具执行 ros2 CLI |
| 运动控制 | /cmd_vel 话题 | robot-control Skill |
| 状态反馈 | /odom、/scan 话题 | exec topic echo |
| 导航规划 | Nav2 | turtlebot3-navigation Skill |
| 日志记录 | ros2 bag | exec 工具执行 |

</details>

---

## 本章小结

| 概念 | 说明 |
|------|------|
| **Skill** | OpenClaw 的可配置扩展单元，定义 Agent 如何调用外部工具或服务 |
| **SKILL.md** | Skill 的核心配置文件，包含描述、工具函数、触发条件 |
| **Skill 目录结构** | SKILL.md（必须）+ references/ + scripts/ + data/ |
| **触发机制** | 自然语言 → 语义匹配 → 自动激活最合适的 Skill |
| **available_skills** | OpenClaw 配置中声明可用 Skill 的列表 |
| **ClawHub** | OpenClaw 官方 Skill 市场，提供搜索/安装/发布功能 |
| **内置 Skill** | feishu-doc、feishu-wiki、feishu-drive、github、weather、pdf、video-frames 等 |
| **机器人 Skill** | robot-control、turtlebot3-control、agent-reach |
| **ROS2 工具链** | rclcpp、rviz2、Gazebo、Nav2、colcon 等 |
| **Sim-to-Real** | 仿真训练 → 真实部署的迁移流程 |

---

## 延伸阅读

1. **OpenClaw 官方文档**：<https://docs.openclaw.com/>
2. **ClawHub Skill 市场**：<https://clawhub.com/>
3. **ROS2 官方文档**：<https://docs.ros.org/en/jazzy/>
4. **TurtleBot3 教程**：<https://emanual.robotis.com/docs/en/platform/turtlebot3/overview/>
5. **Gazebo 仿真入门**：<https://gazebosim.org/docs>
6. **Nav2 导航栈**：<https://navigation.ros.org/>

---

## 学有余力

如果你对 Skill 系统感兴趣，可以进一步探索以下方向：

- **开发一个完整的 Feishu Bot Skill**：集成飞书机器人，实现消息自动回复
- **开发 ROS2 监控 Skill**：实时监控 ROS2 系统状态，自动告警
- **使用 Agent-reach 接入 Twitter/Reddit**：让 AI Agent 能够读写社交媒体
- **探索 VLA（视觉-语言-动作）模型与 Skill 的结合**：让机器人通过视觉理解场景并执行复杂任务

---

*下节课程预告：01-8 具身智能项目实战，我们将综合运用前面学到的知识，从零开始完成一个完整的机器人具身智能项目。敬请期待！*
