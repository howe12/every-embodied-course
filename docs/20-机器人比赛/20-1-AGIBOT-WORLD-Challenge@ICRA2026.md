# 20-1 AGIBOT WORLD Challenge@ICRA2026

## 概述

AGIBOT WORLD Challenge@ICRA2026 是由智元机器人（AgiBot）举办的具身智能机器人国际竞赛，作为 ICRA 2026 的官方竞赛项目。大赛以 **"即刻开赛！"** 为口号，汇聚全球顶尖团队共赴智能机器人竞技盛宴。

### 赛事规模

- **总奖池**：**53万美元** 💰
- **额外福利**：表现突出的队伍将获得智元机器人采购代金券

### 两大核心赛道

| 赛道 | 简介 |
|------|------|
| **Reasoning to Action** | 推理-操作赛道，评估模型的推理和动作执行能力 |
| **World Model** | 世界模型赛道，聚焦具身世界模型的核心能力 |

---

## 赛道一：Reasoning to Action（推理-操作赛道）

### 赛道目标

本赛道旨在评估模型的推理和动作执行能力，包括：
- **线上仿真赛段**：基于仿真平台进行模型评测
- **线下真机赛段**：在真实机器人上验证模型性能

参赛者将基于 AGIBOT WORLD 开源数据集，训练能够解决一系列复杂任务的模型。

### 技术特点

- 聚焦 **Sim2Real Gap（仿真到真实差距）**
- 实现从 **开放词汇理解** 到 **真实物理交互** 的稳健泛化
- 赛题结合落地项目与 **Genie Sim 3.0** 仿真平台设计
- 覆盖：物流、工业、超市、餐饮、家居等常见场景

### 任务示例（部分）

以下是该赛道涉及的实际任务类型，通过图片展示了具体操作场景：

| 任务 | 描述 |
|------|------|
| 物流分拣 | 机器人进行物品分类和分拣操作 |
| 倒工件 | 将工件从一个容器倒入另一个容器 |
| 上货并扶正倾斜商品 | 整理货架，将倾斜商品扶正 |
| 铲爆米花 | 精细操作，模拟爆米花铲取 |
| 开门 | 门把手操作与开门动作 |
| 清理书桌 | 整理桌面物品 |
| 双手端锅 | 双臂协同作业 |

> 💡 左右滑动查看更多任务示例

### 评测工具：Genie Sim 3.0

业内首个大语言模型驱动的开源仿真平台：

- **数字孪生级高保真环境**：融合三维重建与视觉生成
- **场景、资产和任务与测试服务器保持一致**
- 支持参赛者进行 **本地闭环评估**
- 使用智元自研具身大脑 **Genie Reasoner**
- 实现基于 VLM 的 **全自动评测**

> 🔗 官网：https://agibot-world.com/genie-sim

---

## 赛道二：World Model（世界模型赛道）

### 赛道目标

聚焦具身世界模型的核心能力——**基于机器人动作精准建模物理环境动态**。

参赛者需基于 AGIBOT WORLD 数据集训练 **视频生成模型**，根据所提供的机器人真实观测与动作信号，生成机器人在 **10 组真实作业场景** 下的交互视频。

### 数据集

| 项目 | 说明 |
|------|------|
| 训练集 | 10 个不同任务组成，涵盖超 **30,000 条**真实轨迹 |
| 交互类型 | 抓取、放置、推、拉等多样化的机器人-环境交互 |
| 测试集 | 包含专家轨迹和不完美动作轨迹（如空抓、碰撞），全面评估泛化能力 |

> 🔗 数据集：https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026/tree/main/WorldModel

### 基线模型：EVAC

智元自研并开源的具身世界模型：

- **首个由机器人动作驱动的具身世界模型**
- 基于全量 AGIBOT WORLD 数据进行预训练

> 🔗 基线代码：https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline

### 评测基准：EWMBench

基于具身世界模型评测基准 **EWMBench** 进行评估：

- **图像质量**
- **场景一致性**
- **轨迹遵循度**
- 多维度全方位评估生成模型表现

> 🔗 评测基准：https://github.com/AgibotTech/EWMBench

### 评测服务器

部署在 HuggingFace 上的评测服务器，排行榜单实时更新！

> 🔗 评测服务器：https://huggingface.co/spaces/agibot-world/ICRA26WM

---

## 数据集资源

### Reasoning2Action 数据集

| 平台 | 链接 |
|------|------|
| HuggingFace | https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026 |
| ModelScope | https://modelscope.cn/datasets/AgiBotWorld/AgiBotWorldChallenge-2026 |

每个任务包含**数百条完整操作轨迹**，高质量数据全面开源。

### World Model 数据集

> 🔗 https://huggingface.co/datasets/agibot-world/AgiBotWorldChallenge-2026/tree/main/WorldModel

---

## 基线模型

### Reasoning to Action 基线：ACoT-VLA

帮助参赛者快速掌握训练、测试及提交流程。

> 🔗 https://github.com/AgibotTech/ACoT-VLA

### World Model 基线：EVAC

首个由机器人动作驱动的具身世界模型。

> 🔗 https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline

---

## 关键赛程

| 日期 | 事项 |
|------|------|
| **2月12日** | 比赛报名开启 |
| **2月28日** | 两大赛道服务器开启 ✅ 已开启 |
| **4月20日** | 比赛服务器关闭 |
| **4月30日** | 线上赛段结果公布 |
| **6月1日** | 线下真机决赛 |

---

## 评测规则

### Reasoning to Action

1. **本地仿真验证**：使用 Genie Sim 3.0 进行本地闭环评估
2. **Docker 镜像提交**：构建包含模型、代码和所有依赖项的镜像
3. **每天提交限制**：每队每天最多 **2 次** 提交机会
4. **服务器评测**：系统自动拉取并运行镜像进行评测

### World Model

1. 登录 HuggingFace 评测服务器
2. 根据参赛指引提交结果
3. 排行榜单实时更新

---

## 参赛支持

### 报名官网

访问比赛主页获取赛事资源详情，提交训练模型，与全球开发者同台竞技：

> 🔗 Reasoning to Action：https://agibot-world.com/challenge2026/reasoning2action/quick-start

### 社区交流

| 平台 | 链接 |
|------|------|
| **赛事飞书群** | https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=b03mea0a-1212-428a-8b78-f77cf6f591e3 |
| **Discord** | 加入讨论（官方频道） |

### 邮箱支持

技术问题、合作咨询：agibot-world-challenge@agibot.com

---

## 快速开始

### 步骤一：环境准备

```bash
# 克隆 Genie Sim 3.0
git clone https://github.com/your-repo/genie-sim.git
cd genie-sim

# 安装依赖
pip install -r requirements.txt

# 下载数据集
python scripts/download_data.py --dataset Reasoning2Action-Sim
```

### 步骤二：运行基线

```bash
# 运行基线模型
python run_baseline.py --model ACoT-VLA --task 01

# 本地验证
python evaluate.py --local --submit
```

### 步骤三：提交作品

```bash
# 构建 Docker 镜像
docker build -t your-image:v1 .

# 推送到镜像仓库
docker push your-registry.com/your-image:v1

# 在测试服务器提交
# 访问 https://agibot-world.com/challenge2026/reasoning2action
# 点击 New Submission 填写镜像 URL
```

---

## 常见问题

### Q1: 是否可以使用自己的数据集？
可以，但获奖需在技术报告中明确描述数据使用情况。

### Q2: 每天提交次数有限制吗？
是的，每队每天最多 2 次提交。建议充分本地测试后再提交。

### Q3: World Model 赛道有线下赛吗？
World Model 赛道仅设置线上竞赛阶段。Reasoning to Action 赛道有线下真机决赛。

### Q4: 评测失败怎么办？
可在 My Submissions 页面下载日志文件诊断问题。

---

## 总结

AGIBOT WORLD Challenge@ICRA2026 是具身智能领域的重要竞赛：

- ✅ **53万美元** 总奖池 + 机器人采购代金券
- ✅ **两大赛道**：Reasoning to Action + World Model
- ✅ **10 个任务场景**：物流分拣、开门、双手端锅等
- ✅ **30,000+ 条真实轨迹** 数据集
- ✅ **Genie Sim 3.0** 开源仿真平台
- ✅ **ACoT-VLA / EVAC** 基线模型
- ✅ 完整的训练-测试-提交流程

---

## 延伸阅读

- [智元AGIBOT公众号文章](https://mp.weixin.qq.com/s/dITx3LvurBcugv1e0Ur-TQ)
- [Genie Sim 3.0 官网](https://agibot-world.com/genie-sim)
- [ACoT-VLA 基线模型](https://github.com/AgibotTech/ACoT-VLA)
- [EVAC 基线模型](https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline)
- [EWMBench 评测基准](https://github.com/AgibotTech/EWMBench)
- [HuggingFace 评测服务器](https://huggingface.co/spaces/agibot-world/ICRA26WM)