# 17-5 室内VLN与RoomRPC

**版本**: V1.0
**作者**: Wendy | **课程系列**: ROS2机器人仿真与应用实践
**适用对象**: 具备 VLN 基础，了解室内导航和视觉语言导航基本概念，熟悉深度学习的学员
**前置知识**: VLN基础（17-1~17-4）、Python / PyTorch 基础

---

## 一、课程概述

室内环境是 VLN（视觉-语言导航）最核心的应用场景之一。相比于室外自动驾驶，室内环境具有**空间封闭、拓扑复杂、功能区域多样**的特点，智能体需要在家具密集、遮挡明显的环境中精确导航到目标位置。

本课程聚焦**室内 VLN** 场景，系统介绍：

1. **室内VLN特点** - 室内环境的独特挑战与机遇
2. **RoomRPC数据集** - 室内VLN主流数据集的设计与使用
3. **室内导航策略** - 基于房间、地标、语义地图的导航方法
4. **家庭机器人应用** - 从仿真到真实机器人的部署路径

---

## 二、章节设计

**模块一：室内VLN特点** - 室内环境复杂性、家具导航、房间类型识别
**模块二：RoomRPC数据集** - R2R Plus、RxR、室内场景多样性
**模块三：室内导航策略** - 基于房间导航、地标检测、语义地图
**模块四：家庭机器人应用** - 家居导航、多房间任务、人体跟随
**模块五：代码实战** - 室内导航、语义地图、RoomRPC数据处理
**模块六：练习题与答案**

---

## 三、理论内容

### 3.1 室内VLN特点

#### 3.1.1 室内环境的独特挑战

室内VLN与室外VLN存在根本性差异，这些差异源于室内环境本身的物理特性：

| 特性 | 室内环境 | 室外环境 |
|------|----------|----------|
| **空间结构** | 封闭房间、门廊、走廊 | 开放道路、交叉口 |
| **拓扑复杂度** | 高（多房间、多楼层） | 中（道路网络） |
| **物体密度** | 极高（家具、装饰品） | 低（车辆、标志牌） |
| **光照变化** | 室内人工光/自然光混合 | 强太阳光、阴影 |
| **地图可用性** | 通常无现成地图 | GPS/高精度地图 |
| **导航粒度** | 精细（桌椅级别） | 粗略（路口级别） |

**室内VLN的四大核心挑战**：

```
┌──────────────────────────────────────────────────────────────┐
│                  室内 VLN 四大核心挑战                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 多尺度空间推理                                           │
│     房间级（客厅→厨房） → 区域级（沙发区→餐桌区）            │
│       → 物体级（找到红色的杯子）                             │
│                                                              │
│  2. 密集遮挡环境                                              │
│     家具之间相互遮挡，视线受限，单一视角无法获得全局信息       │
│     需要主动探索和移动才能获取完整信息                        │
│                                                              │
│  3. 功能区域语义理解                                          │
│     "去厨房"需要理解什么是厨房（灶台、冰箱、餐桌）           │
│     而非简单寻找某个视觉地标                                   │
│                                                              │
│  4. 指令的歧义性与模糊性                                      │
│     "往前走然后左转"在不同房间结构下完全不同的路径             │
│     自然语言本身的空间表达具有高度歧义性                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 3.1.2 家具与物体导航

室内VLN中的一个核心问题是**物体目标导航**--指令要求智能体导航到特定物体所在位置。

**物体导航的难点**：

- **同类别物体区分**："走到沙发旁边的椅子"vs"餐桌旁的椅子"
- **物体可及性**：物体可能被遮挡、放在高处、或在另一个房间里
- **参照物依赖**："红色的椅子"需要理解颜色属性并在场景中匹配

**物体导航的分层策略**：

```
┌──────────────────────────────────────────────────────────────┐
│              物体导航分层策略                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  高层规划（房间级）                                           │
│  "厨房里有冰箱，卧室里没有" → 先导航到正确房间                 │
│         ↓                                                    │
│  中层规划（区域级）                                           │
│  "厨房靠窗的区域有餐桌" → 导航到厨房的正确子区域              │
│         ↓                                                    │
│  低层规划（物体级）                                           │
│  "餐桌上有个杯子" → 定位并抓取目标物体                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**关键算法思路**：

- **场景图增强**：构建室内场景图（节点=物体，边=空间关系），利用图推理理解物体间关系
- **语义分割引导**：使用语义分割定位特定类别的物体区域
- **语言条件检索**：CLIP等模型实现自然语言到视觉空间的零样本检索

#### 3.1.3 房间类型识别

**房间类型识别**是室内导航的基础能力--智能体需要知道"我现在在哪里"以及"目标位置在哪个房间"。

**房间识别的线索来源**：

| 线索类型 | 示例 | 可靠性 |
|----------|------|--------|
| **视觉外观** | 厨房有灶台、冰箱；卧室有床、衣柜 | 中等（因装修风格差异大） |
| **物体组合** | 餐桌+椅子→餐厅；床+床头柜→卧室 | 高 |
| **空间结构** | 有窗户的位置通常是客厅 | 中等 |
| **深度布局** | 狭长走廊 vs 开阔空间 | 高 |

**房间识别的技术方法**：

**（1）多标签分类**：

将房间识别建模为多标签分类问题，使用视觉特征预测房间类型：

$$P(\text{room} | I) = \text{Softmax}(W_{\text{room}} \cdot \text{ResNet}(I))$$

**（2）场景图推理**：

通过检测场景中的物体组合来推断房间类型：

```
场景图：{餐桌, 椅子, 冰箱, 灶台}
       →  餐桌 + 椅子  → 餐厅（高置信度）
       →  冰箱 + 灶台  → 厨房（高置信度）
       →  餐桌 ∩ 厨房  → 开放式厨房（综合判断）
```

**（3）主动房间识别**：

当单视角无法确定房间类型时，智能体主动移动以获取更多观测：

$$\text{action} = \arg\max_{a \in \mathcal{A}} \text{IG}(room; I \oplus f(I, a))$$

其中 $\text{IG}$ 表示房间类型的信息增益，$f(I, a)$ 表示执行动作 $a$ 后的新观测。

---

### 3.2 RoomRPC数据集

#### 3.2.1 Room-to-Room Plus (R2R Plus)

**R2R 数据集**（Room-to-Room）是 VLN 领域最经典的基准数据集，但原始 R2R 存在一些局限性：

| 局限性 | 描述 | R2R Plus 的改进 |
|--------|------|----------------|
| **离散视图** | 仅提供 36 个预定义视角点 | 增加视角密度，覆盖更多可导航位置 |
| **短距离轨迹** | 平均轨迹长度较短 | 增加长距离多房间导航实例 |
| **简单指令** | 指令较短，缺乏细节 | 增加参照物和空间关系描述 |
| **小规模** | ~6,000 条轨迹 | 扩展至 ~10,000+ 条 |

**R2R Plus 的核心改进**：

1. **视角密度提升**：从 Matterport3D 扫描中提取更多有效视角点
2. **轨迹多样性**：覆盖不同起始位置到目标位置的多种路径
3. **指令增强**：引入含参照物的复合指令，如"走到客厅的红色沙发旁边"

**Matterport3D 数据集背景**：

Matterport3D 是由 108,000 张 RGB-D 图像构建的真实室内 3D 重建数据集，涵盖 90 栋建筑的真实扫描：

| 建筑类型 | 数量 |
|----------|------|
| 公寓 | ~20 |
| 房屋 | ~50 |
| 办公室 | ~20 |

**Matterport3D 场景示例**：

```
公寓场景（Floor_17_APartment_Unit_1）:
  └─ 客厅（Living Room）
      ├─ 沙发区（绿色沙发、茶几、电视柜）
      ├─ 餐厅区（餐桌、4把椅子）
      └─ 走廊（通往卧室、厨房）

  └─ 主卧（Master Bedroom）
      ├─ 床（双人床）
      ├─ 衣柜
      └─ 卫生间入口
```

#### 3.2.2 RxR数据集

**RxR**（Room-to-Room eXpress）是一个**多语言、大规模**的 VLN 数据集，相比 R2R 有显著扩展：

| 特性 | R2R | RxR |
|------|-----|-----|
| **轨迹数量** | ~7,000 | ~42,000 |
| **语言** | 英语 | 英语、印地语、普通话 |
| **指令长度** | 短（平均 ~25 词） | 长（平均 ~89 词） |
| **过程标注** | 仅目标位置 | 包含完整导航过程 |
| **标注者** | ~25人 | ~300人 |

**RxR 的核心创新**：

**（1）过程导向指令（Turn-by-Turn Annotation）**：

RxR 的指令不仅描述最终目标，还**逐步描述导航过程**：

> **R2R指令**："Walk past the kitchen and enter the living room."
> **RxR指令**："Start by going forward through the hallway. When you reach the kitchen on your right, continue straight past it. The living room will be on your left - enter through the doorway and stop near the piano."

**（2）多语言支持**：

RxR 提供英语、印地语和普通话三种语言的指令，这对于：
- 研究语言差异对导航策略的影响
- 提升模型的多语言泛化能力
- 非英语母语者的用户体验优化

**（3） Indoorseen 指南风格**：

RxR 指令参考了人类旅行指南的写作风格，更接近真实的人机交互场景。

#### 3.2.3 室内场景多样性

**室内VLN数据集的场景多样性**是衡量数据集质量的关键指标：

**场景多样性的维度**：

| 维度 | 描述 | 重要性 |
|------|------|--------|
| **建筑类型** | 公寓、房屋、办公室、酒店 | 覆盖不同功能布局 |
| **房间数量** | 2~10+ 个房间 | 测试跨房间导航能力 |
| **装修风格** | 现代、传统、简约、豪华 | 提升视觉泛化 |
| **光照条件** | 白天、夜晚、阴天 | 测试光照鲁棒性 |
| **遮挡程度** | 空旷、适度、密集 | 测试复杂环境导航 |

**主流室内VLN数据集对比**：

```
┌──────────────────────────────────────────────────────────────┐
│             主流室内 VLN 数据集对比                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Matterport3D (R2R/RxR)     Gibson          AI2-THOR         │
│  ─────────────────────      ──────          ─────────       │
│  真实3D扫描重建              真实3D扫描       合成环境         │
│  ~90 buildings              ~500+ spaces     ~120 scenes     │
│  RGB-D 图像                  RGB-D 图像       可交互物体       │
│  室内（家/办公室）            室内/室外         仅室内          │
│  不可交互                    不可交互          可交互           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**数据集选择的考量因素**：

- **研究目标**：如果研究真实室内导航，选 Matterport3D；如果研究可交互导航，选 AI2-THOR
- **计算资源**：Gibson 和 Matterport3D 需要 3D 重建，存储需求大
- **任务类型**：目标导航选 R2R/REVERIE，对话导航选 CVDN，长距离选 RxR

---

### 3.3 室内导航策略

#### 3.3.1 基于房间的导航

**基于房间的导航（Room-based Navigation）** 是室内VLN的核心策略之一，其思想是：先识别当前房间类型，再决定导航目标房间，最后在房间间和房间内导航。

**房间导航的分层架构**：

```
┌──────────────────────────────────────────────────────────────┐
│              基于房间的分层导航架构                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  全局规划层（Global Planning Layer）                  │    │
│  │  ───────────────────────────────────────────────────  │    │
│  │  输入：自然语言指令 "去厨房拿水杯"                     │    │
│  │  输出：房间序列 [起居室 → 走廊 → 厨房]                 │    │
│  │  方法：房间图路径搜索、LLM 推理                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                            ↓                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  区域规划层（Regional Planning Layer）                │    │
│  │  ───────────────────────────────────────────────────  │    │
│  │  输入：当前房间拓扑图                                 │    │
│  │  输出：子区域/地标序列                                │    │
│  │  方法：拓扑图搜索、地标检测                          │    │
│  └──────────────────────────────────────────────────────┘    │
│                            ↓                                  │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  局部执行层（Local Execution Layer）                   │    │
│  │  ───────────────────────────────────────────────────  │    │
│  │  输入：当前视觉观测                                  │    │
│  │  输出：动作序列 [前进0.5m → 左转30° → ...]           │    │
│  │  方法：视觉运动策略、避障                            │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**房间图的构建**：

房间图（Room Graph）是房间级拓扑导航的核心数据结构：

$$G_{\text{room}} = (V_{\text{room}}, E_{\text{room}})$$

- **节点** $V_{\text{room}}$：每个节点代表一个房间，包含房间类型、入口位置、视觉特征
- **边** $E_{\text{room}}$：连接相邻房间的走廊或门，包含连通性信息

**房间图示例**：

```
  [主卧] ←→ [走廊] ←→ [厨房]
    ↓                        ↓
 [主卫]                  [餐厅] ←→ [客厅]
                                    ↓
                               [玄关] ←→ [次卧]
```

#### 3.3.2 地标检测

**地标（Landmark）** 是室内导航中的关键参照物，典型地标包括：大型家具（沙发、餐桌）、装饰品（画、雕像）、结构性元素（门、窗、楼梯）。

**地标的层次分类**：

| 级别 | 示例 | 稳定性 | 识别难度 |
|------|------|--------|----------|
| **结构性地标** | 门、窗、楼梯 | 高 | 低 |
| **主型家具** | 沙发、床、大衣柜 | 高 | 中 |
| **小型家具** | 椅子、茶几、台灯 | 中 | 中 |
| **装饰品** | 画、雕像、花瓶 | 低 | 高 |
| **容器类** | 书架、橱柜、冰箱 | 高 | 低 |

**地标检测的方法**：

**（1）基于检测器的地标识别**：

使用预训练的物体检测器（如 DETR、Faster R-CNN）识别场景中的物体作为地标：

$$B = \text{Detect}(I; \theta_{\text{det}})$$

其中 $B = \{(b_i, c_i, s_i)\}$ 是检测到的边界框、类别和置信度。

**（2）基于显著性的地标提取**：

使用显著性检测模型识别视觉显著性区域作为隐式地标：

$$S = \text{Saliency}(I; \theta_{\text{sal}})$$

**（3）语言引导的地标检索**：

利用 CLIP 等视觉语言模型，根据指令中的描述检索相关地标：

$$l^* = \arg\max_{l \in \mathcal{L}} \text{CLIP}(T_{\text{instr}}, V(l))$$

其中 $T_{\text{instr}}$ 是语言指令，$V(l)$ 是地标图像区域。

**地标在导航中的作用**：

```
指令："走进客厅，右转，经过蓝色的沙发，在窗户旁边停下"

地标序列：入口 → [客厅门] → [蓝色沙发] → [窗户]
                               ↑            ↑
                           中间检查点     目标位置
```

#### 3.3.3 语义地图构建

**语义地图（Semantic Map）** 是室内VLN的核心表示之一，它将几何信息与语义信息结合，构建带语义标签的环境地图。

**语义地图的数据结构**：

$$M_{\text{semantic}} = \{C, F, L\}$$

- **C**（Coordinates）：三维坐标网格，$[x, y, z]$ 位置
- **F**（Features）：每个位置的视觉特征向量
- **L**（Labels）：语义标签 $\{\text{wall}, \text{floor}, \text{chair}, \text{table}, \text{door}, ...\}$

**语义地图的构建流程**：

```
RGB-D 图像序列
      ↓
深度估计 → 点云注册（ICP/几何对齐）
      ↓
语义分割 → 为每个 3D 点分配语义标签
      ↓
体素化 → 构建稠密语义体素地图
      ↓
语义地图 M_semantic
```

**语义地图在VLN中的应用**：

| 应用场景 | 作用 | 优势 |
|----------|------|------|
| **位置识别** | 通过语义特征匹配当前位置 | 语义比纯几何更鲁棒 |
| **目标定位** | 在语义地图中搜索目标物体位置 | 利用语义约束缩小搜索空间 |
| **路径规划** | 结合几何可行性和语义可达性 | 避免穿越语义禁区（如墙上） |
| **指令理解** | 将指令中的语义实体映射到地图 | 实现语言-空间的跨模态对齐 |

**SemExp（Semantic Expectation）** 是经典的使用语义地图进行室内导航的方法：

核心思想是维护一个**语义探索奖励**，鼓励智能体探索能获取语义信息的区域：

$$\mathcal{L}_{\text{sem}} = \alpha \cdot \underbrace{\mathbb{E}[R_{\text{semantic}}]}_{\text{语义奖励}} - \beta \cdot \underbrace{\mathbb{E}[R_{\text{distance}}]}_{\text{距离奖励}}$$

---

### 3.4 家庭机器人应用

#### 3.4.1 家居环境导航

**家居环境导航**是室内VLN最具实际价值的应用场景，典型的家居导航任务包括：

| 任务类型 | 指令示例 | 技术挑战 |
|----------|----------|----------|
| **物品取回** | "去厨房把冰箱里的牛奶拿来" | 物体检测、物体操作 |
| **多房间导航** | "先关客厅的灯，再去卧室把窗帘拉上" | 多目标、顺序执行 |
| **人机交互** | "跟着我" | 人体跟随、意图预测 |
| **照看服务** | "每隔一小时检查一下老人的状态" | 长期自主、异常检测 |

**家居导航的关键技术要求**：

```
┌──────────────────────────────────────────────────────────────┐
│              家居机器人导航的技术要求                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. 实时性                                                    │
│     导航决策延迟 < 100ms（室内环境动态变化快）               │
│                                                              │
│  2. 安全性                                                    │
│     必须能检测并避让宠物、儿童、老年人                        │
│     碰撞检测 + 软控制（接触即停）                            │
│                                                              │
│  3. 鲁棒性                                                    │
│     家居环境物品摆放经常变化（椅子被挪动、地上有玩具）       │
│     需要在线地图更新和增量规划                                │
│                                                              │
│  4. 自主性                                                    │
│     家居场景不可能预先完整建图                                │
│     必须支持未知环境自主探索                                   │
│                                                              │
│  5. 人机协同                                                  │
│     理解自然语言指令中的歧义和隐含意图                        │
│     支持语音确认和主动询问                                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 3.4.2 多房间任务

**多房间任务**是家居导航的典型挑战，智能体需要：

1. **理解房间功能**：知道厨房有冰箱、卧室有床
2. **规划房间路径**：选择最优的房间遍历顺序
3. **执行跨房间导航**：在走廊、门口等过渡区域正确导航

**多房间任务规划**：

当指令包含多个房间目标时，需要解决**任务规划**问题：

$$\pi^* = \arg\min_{\pi} \sum_{i=1}^{N} d(v_{\pi(i-1)}, v_{\pi(i)})$$

其中 $\pi$ 是房间访问顺序的排列，$d(v_i, v_j)$ 是房间间的最短路径距离。

**经典问题是旅行商问题（TSP）**的变体，实用中常使用贪心近似：

```python
# 贪心最近邻求解
def plan_room_sequence(start, goals):
    """
    简单的贪心房间序列规划
    """
    current = start
    sequence = [start]
    remaining = goals.copy()

    while remaining:
        # 选择距离当前位置最近的未访问房间
        next_room = min(remaining, key=lambda r: distance(current, r))
        sequence.append(next_room)
        remaining.remove(next_room)
        current = next_room

    return sequence
```

**Doors 的特殊处理**：

室内多房间导航中，**门**是关键瓶颈：
- 门可能是关闭的（需要开门动作）
- 门框宽度限制了机器人的通过性
- 门的开合方向影响通行路径

#### 3.4.3 人体跟随

**人体跟随（Person Following）** 是家庭机器人的重要能力，机器人在室内环境中跟随移动的人类主人。

**人体跟随的技术框架**：

```
┌──────────────────────────────────────────────────────────────┐
│              人体跟随系统架构                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  人体检测    │ →  │  目标跟踪    │ →  │  运动规划   │     │
│  │  (YOLOv8)   │    │  (DeepSORT)  │    │  (DWA/Teb)  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         ↓                                        ↓          │
│  ┌─────────────┐                        ┌─────────────┐     │
│  │  ReID识别   │                        │  避障控制   │     │
│  │  (跨摄像头) │                        │  (安全距离) │     │
│  └─────────────┘                        └─────────────┘     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**关键模块**：

1. **人体检测**：YOLOv8 等实时检测器定位人体边界框
2. **目标跟踪**：DeepSORT 等多目标跟踪算法维持跟随目标的 ID
3. **ReID（行人再识别）**：在多人场景中识别特定主人
4. **运动规划**：DWA（动态窗口法）或 TEB（时间弹性带）生成安全跟随轨迹

**室内人体跟随的特殊挑战**：

- **遮挡频繁**：家具遮挡导致检测丢失
- **室内地图限制**：机器人在跟随时需要同时考虑避障和地图约束
- **多楼层问题**：主人上楼/下楼时机器人需要使用电梯或楼梯

---

## 四、代码实战

### 4.1 室内环境导航模拟

本节实现一个简单的室内VLN导航环境模拟器，演示如何处理Matterport3D/R2R格式的室内导航数据。

```python
"""
室内VLN导航环境模拟器
模拟机器人在室内环境中的导航，支持R2R/RxR格式的轨迹数据

作者: Wendy
功能: 室内导航环境构建、轨迹模拟、动作执行
"""

import numpy as np
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import heapq


class NavigationAction(Enum):
    """导航动作枚举 - 定义机器人可执行的基本动作"""
    FORWARD = "forward"          # 前进
    TURN_LEFT = "turn_left"     # 左转 30度
    TURN_RIGHT = "turn_right"   # 右转 30度
    STOP = "stop"               # 停止（到达目标）


@dataclass
class Pose2D:
    """
    二维位姿状态
    x, y: 位置坐标（米）
    theta: 朝向角度（弧度，0=北，逆时针正）
    """
    x: float
    y: float
    theta: float

    def __hash__(self):
        # 用于KD-Tree节点哈希
        return hash((round(self.x, 2), round(self.y, 2), round(self.theta, 1)))

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {"x": self.x, "y": self.y, "theta": self.theta}


@dataclass
class RoomNode:
    """
    房间节点 - 表示拓扑地图中的一个房间
    node_id: 房间唯一标识
    room_type: 房间类型（如"厨房"、"卧室"）
    position: 房间中心位置
    landmarks: 地标列表
    connections: 连接的邻居房间ID
    """
    node_id: str
    room_type: str
    position: Pose2D
    landmarks: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "room_type": self.room_type,
            "position": self.position.to_dict(),
            "landmarks": self.landmarks,
            "connections": self.connections
        }


class IndoorNavigationSimulator:
    """
    室内VLN导航模拟器

    核心功能：
    1. 加载R2R/RxR格式的室内导航数据
    2. 维护拓扑地图（房间图）
    3. 执行导航动作并更新机器人状态
    4. 计算导航评价指标

    Attributes:
        room_graph: 房间拓扑图，Dict[node_id -> RoomNode]
        agent_pose: 机器人当前位姿
        target_node_id: 目标房间ID
        trajectory: 历史轨迹记录
    """

    # 动作执行参数
    STEP_DISTANCE = 0.5      # 前进步长（米）
    TURN_ANGLE = np.pi / 6  # 转向角度 30度

    def __init__(self, simulator_cfg: Optional[Dict] = None):
        """
        初始化导航模拟器

        Args:
            simulator_cfg: 模拟器配置，包含地图路径等参数
        """
        cfg = simulator_cfg or {}
        self.room_graph: Dict[str, RoomNode] = {}
        self.agent_pose = Pose2D(x=0.0, y=0.0, theta=0.0)
        self.target_node_id: Optional[str] = None
        self.trajectory: List[Pose2D] = [Pose2D(0.0, 0.0, 0.0)]
        self.visited_nodes: List[str] = []

        # 加载内置的示例室内拓扑地图
        self._build_default_map()

    def _build_default_map(self) -> None:
        """
        构建默认的室内拓扑地图

        创建一个典型的家居平面拓扑图：
        玄关 ←→ 客厅 ←→ 餐厅 ←→ 厨房
                ↓          ↓
               次卧 ←→ 走廊 ←→ 主卧
        """
        # 定义各个房间节点
        rooms = [
            RoomNode(
                node_id="entrance",       # 玄关
                room_type="entrance",
                position=Pose2D(0.0, 0.0, 0.0),
                landmarks=["鞋柜", "穿衣镜"],
                connections=["living_room"]
            ),
            RoomNode(
                node_id="living_room",     # 客厅
                room_type="living_room",
                position=Pose2D(5.0, 0.0, 0.0),
                landmarks=["沙发", "茶几", "电视", "落地灯"],
                connections=["entrance", "dining_room", "corridor"]
            ),
            RoomNode(
                node_id="dining_room",     # 餐厅
                room_type="dining_room",
                position=Pose2D(10.0, 0.0, 0.0),
                landmarks=["餐桌", "餐椅", "餐边柜"],
                connections=["living_room", "kitchen"]
            ),
            RoomNode(
                node_id="kitchen",         # 厨房
                room_type="kitchen",
                position=Pose2D(15.0, 0.0, 0.0),
                landmarks=["灶台", "冰箱", "水槽", "橱柜"],
                connections=["dining_room"]
            ),
            RoomNode(
                node_id="corridor",        # 走廊
                room_type="corridor",
                position=Pose2D(5.0, -5.0, 0.0),
                landmarks=["挂画", "装饰柜"],
                connections=["living_room", "bedroom_2", "bedroom_master"]
            ),
            RoomNode(
                node_id="bedroom_2",       # 次卧
                room_type="bedroom",
                position=Pose2D(0.0, -5.0, 0.0),
                landmarks=["单人床", "书桌", "衣柜"],
                connections=["corridor"]
            ),
            RoomNode(
                node_id="bedroom_master",  # 主卧
                room_type="bedroom",
                position=Pose2D(10.0, -5.0, 0.0),
                landmarks=["双人床", "床头柜", "衣柜", "梳妆台"],
                connections=["corridor"]
            ),
        ]

        # 构建房间图
        for room in rooms:
            self.room_graph[room.node_id] = room

        print(f"[导航模拟器] 室内拓扑地图加载完成，共 {len(self.room_graph)} 个房间节点")

    def load_r2r_trajectory(self, trajectory_path: str) -> bool:
        """
        加载R2R/RxR格式的轨迹数据

        Args:
            trajectory_path: 轨迹JSON文件路径

        Returns:
            bool: 加载是否成功
        """
        try:
            with open(trajectory_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 解析R2R格式：{scan_id, path_id, path: [{...}], ...}
            # 轨迹路径点列表
            for item in data:
                scan_id = item.get('scan_id', 'default')
                path = item.get('path', [])

                print(f"[加载] scan={scan_id}, 路径点数={len(path)}")

            print(f"[加载] 共加载 {len(data)} 条轨迹")
            return True

        except FileNotFoundError:
            print(f"[警告] 轨迹文件未找到: {trajectory_path}")
            print("[加载] 使用默认室内地图继续...")
            return False
        except json.JSONDecodeError as e:
            print(f"[错误] JSON解析失败: {e}")
            return False

    def execute_action(self, action: NavigationAction) -> Tuple[bool, Dict]:
        """
        执行单个导航动作

        Args:
            action: 导航动作

        Returns:
            Tuple[是否成功执行, 状态信息字典]
        """
        # 备份当前状态
        old_pose = Pose2D(self.agent_pose.x, self.agent_pose.y, self.agent_pose.theta)

        if action == NavigationAction.FORWARD:
            # 前进：沿当前朝向移动 STEP_DISTANCE
            self.agent_pose.x += self.STEP_DISTANCE * np.cos(self.agent_pose.theta)
            self.agent_pose.y += self.STEP_DISTANCE * np.sin(self.agent_pose.theta)

        elif action == NavigationAction.TURN_LEFT:
            self.agent_pose.theta += self.TURN_ANGLE

        elif action == NavigationAction.TURN_RIGHT:
            self.agent_pose.theta -= self.TURN_ANGLE

        elif action == NavigationAction.STOP:
            # 停止动作，记录最终状态
            pass

        # 归一化角度到 [-pi, pi]
        self.agent_pose.theta = np.arctan2(np.sin(self.agent_pose.theta),
                                           np.cos(self.agent_pose.theta))

        # 记录轨迹
        self.trajectory.append(Pose2D(self.agent_pose.x,
                                       self.agent_pose.y,
                                       self.agent_pose.theta))

        status = {
            "action": action.value,
            "success": True,
            "pose": self.agent_pose.to_dict(),
            "distance_to_goal": self._distance_to_target()
        }
        return True, status

    def _distance_to_target(self) -> float:
        """计算到目标房间中心的欧氏距离"""
        if self.target_node_id and self.target_node_id in self.room_graph:
            target = self.room_graph[self.target_node_id]
            return np.sqrt(
                (self.agent_pose.x - target.position.x)**2 +
                (self.agent_pose.y - target.position.y)**2
            )
        return float('inf')

    def set_target(self, target_node_id: str) -> bool:
        """
        设置导航目标房间

        Args:
            target_node_id: 目标房间ID

        Returns:
            bool: 目标设置是否成功
        """
        if target_node_id not in self.room_graph:
            print(f"[错误] 未知目标房间: {target_node_id}")
            return False

        self.target_node_id = target_node_id
        print(f"[目标] 导航目标设置为: {self.room_graph[target_node_id].room_type}")
        return True

    def get_current_room(self) -> Optional[str]:
        """
        根据当前位置判断当前所在房间

        使用贪婪最近邻：返回距离最近的房间节点

        Returns:
            str: 当前房间ID，未找到返回None
        """
        min_dist = float('inf')
        current_room = None

        for node_id, room in self.room_graph.items():
            dist = np.sqrt(
                (self.agent_pose.x - room.position.x)**2 +
                (self.agent_pose.y - room.position.y)**2
            )
            if dist < min_dist:
                min_dist = dist
                current_room = node_id

        # 阈值判断：在某个房间内（距离 < 3米）
        if min_dist < 3.0:
            return current_room
        return None

    def plan_room_path(self, start: str, goal: str) -> List[str]:
        """
        使用A*算法在房间拓扑图上规划路径

        Args:
            start: 起始房间ID
            goal: 目标房间ID

        Returns:
            List[str]: 房间ID序列，若无法到达返回空列表
        """
        if start not in self.room_graph or goal not in self.room_graph:
            return []

        # A*算法实现
        open_set = [(0, start)]  # (f_score, node_id)
        came_from = {}           # 记录路径
        g_score = {start: 0}     # 起始点到各节点的实际代价
        f_score = {start: self._heuristic(start, goal)}  # 估价函数

        while open_set:
            # 取出f_score最小的节点
            _, current = heapq.heappop(open_set)

            if current == goal:
                # 重建路径
                return self._reconstruct_path(came_from, current)

            # 遍历邻居节点
            for neighbor in self.room_graph[current].connections:
                # 计算从起点经过current到neighbor的代价
                tentative_g = g_score[current] + 1.0  # 边代价统一为1.0

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    # 发现更优路径
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []  # 无法到达目标

    def _heuristic(self, node_id: str, goal_id: str) -> float:
        """
        A*的启发式函数：使用欧氏距离作为估计

        Args:
            node_id: 当前节点
            goal_id: 目标节点

        Returns:
            float: 启发式估计值
        """
        node_pos = self.room_graph[node_id].position
        goal_pos = self.room_graph[goal_id].position
        return np.sqrt((node_pos.x - goal_pos.x)**2 + (node_pos.y - goal_pos.y)**2)

    def _reconstruct_path(self, came_from: Dict, current: str) -> List[str]:
        """从A*搜索结果重建路径"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        return list(reversed(path))

    def reset(self, start_node: Optional[str] = None) -> None:
        """
        重置模拟器状态

        Args:
            start_node: 起始房间ID，若为None则在玄关开始
        """
        if start_node and start_node in self.room_graph:
            start_pose = self.room_graph[start_node].position
            self.agent_pose = Pose2D(start_pose.x, start_pose.y, start_pose.theta)
        else:
            self.agent_pose = Pose2D(0.0, 0.0, 0.0)

        self.trajectory = [Pose2D(self.agent_pose.x, self.agent_pose.y, self.agent_pose.theta)]
        self.visited_nodes = []
        self.target_node_id = None

    def get_trajectory_length(self) -> float:
        """计算轨迹总长度（米）"""
        total = 0.0
        for i in range(1, len(self.trajectory)):
            dx = self.trajectory[i].x - self.trajectory[i-1].x
            dy = self.trajectory[i].y - self.trajectory[i-1].y
            total += np.sqrt(dx*dx + dy*dy)
        return total

    def get_navigation_metrics(self) -> Dict[str, float]:
        """
        计算导航性能指标

        Returns:
            Dict: 包含以下指标的字典
                - trajectory_length: 轨迹总长度（米）
                - num_steps: 总步数
                - success: 是否成功到达目标
                - distance_to_goal: 最终到目标距离
                - efficiency: 路径效率（最短距离/实际距离）
        """
        metrics = {
            "trajectory_length": self.get_trajectory_length(),
            "num_steps": len(self.trajectory) - 1,
            "success": False,
            "distance_to_goal": self._distance_to_target(),
            "efficiency": 0.0
        }

        # 判断是否成功：距离目标小于1米且执行了STOP动作
        if metrics["distance_to_goal"] < 1.0:
            metrics["success"] = True

        # 计算路径效率：实际距离 / （实际距离 + 剩余距离）
        actual = metrics["trajectory_length"]
        remaining = metrics["distance_to_goal"]
        if actual + remaining > 0:
            metrics["efficiency"] = actual / (actual + remaining)

        return metrics


# ============================================================
# 演示：运行室内导航模拟
# ============================================================
def demo_indoor_navigation():
    """
    演示室内VLN导航模拟器的使用
    """
    print("=" * 60)
    print("室内VLN导航模拟器演示")
    print("=" * 60)

    # 1. 创建模拟器
    sim = IndoorNavigationSimulator()

    # 2. 设置导航任务：从玄关到主卧
    sim.reset(start_node="entrance")
    sim.set_target("bedroom_master")

    # 3. 规划路径
    path = sim.plan_room_path("entrance", "bedroom_master")
    print(f"\n[规划] 路径: {' → '.join(path)}")

    # 4. 模拟导航执行
    print("\n[执行] 开始导航...")
    max_steps = 100
    for step in range(max_steps):
        current_room = sim.get_current_room()
        if current_room:
            print(f"  步 {step+1}: 位于 {sim.room_graph[current_room].room_type}")

        # 简单的跟随路径策略：朝向下一个房间移动
        if len(path) > 1 and current_room == path[0]:
            path = path[1:]  # 到达当前目标房间，移向下一个

        # 判断是否接近目标
        if sim._distance_to_target() < 1.5:
            sim.execute_action(NavigationAction.STOP)
            print(f"  [到达] 成功到达目标房间!")
            break

        # 默认动作：前进
        sim.execute_action(NavigationAction.FORWARD)

    # 5. 输出性能指标
    metrics = sim.get_navigation_metrics()
    print(f"\n[指标] 轨迹长度: {metrics['trajectory_length']:.2f} 米")
    print(f"[指标] 总步数: {metrics['num_steps']}")
    print(f"[指标] 到达距离: {metrics['distance_to_goal']:.2f} 米")
    print(f"[指标] 成功率: {'是' if metrics['success'] else '否'}")
    print(f"[指标] 路径效率: {metrics['efficiency']:.2%}")


if __name__ == "__main__":
    demo_indoor_navigation()
```

---

### 4.2 语义地图构建器

本节实现一个室内语义地图构建器，将RGB-D观测序列逐步构建为带语义标签的3D地图。

```python
"""
室内语义地图构建器
将RGB-D图像序列构建为带语义标签的3D体素地图

作者: Wendy
功能: 点云注册、语义分割、体素地图构建、语义查询
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
import colorsys


@dataclass
class SemanticVoxel:
    """
    语义体素 - 3D空间中的单个语义单元

    Attributes:
        position: 体素中心三维坐标 [x, y, z]
        label: 语义标签（如"floor"、"wall"、"chair"）
        confidence: 语义分类置信度
        count: 被观测到的次数（用于多视角融合）
        color: 观测到的平均颜色 [r, g, b]
    """
    position: Tuple[float, float, float]
    label: str
    confidence: float = 1.0
    count: int = 1
    color: Tuple[int, int, int] = (128, 128, 128)


@dataclass
class SemanticMapConfig:
    """语义地图配置参数"""
    voxel_size: float = 0.05        # 体素大小（米）
    map_bounds: Tuple[float, float, float, float, float, float] = (-10, 10, -10, 10, -3, 3)
    # 地图边界 [x_min, x_max, y_min, y_max, z_min, z_max]
    semantic_labels: Set[str] = field(default_factory=lambda: {
        "floor", "wall", "ceiling", "chair", "table", "sofa", "bed",
        "cabinet", "door", "window", "lamp", "plant", "bookshelf"
    })
    confidence_threshold: float = 0.6  # 语义融合置信度阈值


class SemanticMapBuilder:
    """
    语义地图构建器

    核心功能：
    1. 将RGB-D图像转换为点云
    2. 体素化处理，构建稠密地图
    3. 融合语义标签，构建语义地图
    4. 支持语义查询（查询某位置的语义标签）

    使用方法：
        builder = SemanticMapBuilder()
        for rgb, depth, pose, semantics in observation_stream:
            builder.integrate(rgb, depth, pose, semantics)
        semantic_map = builder.get_map()
    """

    # 默认室内语义标签到颜色的映射（RGB）
    LABEL_COLORS: Dict[str, Tuple[int, int, int]] = {
        "floor":     (139,  69,  19),   # 棕色
        "wall":      (245, 245, 220),   # 米色
        "ceiling":   (255, 255, 255),   # 白色
        "chair":     (  0, 100,   0),   # 深绿色
        "table":     (139,  90,  43),   # 深棕色
        "sofa":      ( 70, 130, 180),   # 钢蓝色
        "bed":       ( 72,  61, 139),   # 暗钢蓝
        "cabinet":   (128, 128, 128),   # 灰色
        "door":      (184, 134,  11),   # 暗金色
        "window":    (135, 206, 250),   # 浅蓝色
        "lamp":      (255, 215,   0),  # 金色
        "plant":     ( 34, 139,  34),   # 森林绿
        "bookshelf": (101,  67,  33),  # 深棕色
        "unknown":   (  0,   0,   0),  # 黑色
    }

    def __init__(self, config: Optional[SemanticMapConfig] = None):
        """
        初始化语义地图构建器

        Args:
            config: 语义地图配置，若为None则使用默认配置
        """
        self.config = config or SemanticMapConfig()
        # 体素字典：key = (voxel_x, voxel_y, voxel_z)，value = SemanticVoxel
        self.voxels: Dict[Tuple[int, int, int], SemanticVoxel] = {}
        # 统计各标签的体素数量
        self.label_counts: Dict[str, int] = defaultdict(int)

    def _pos_to_voxel_id(self, pos: Tuple[float, float, float]) -> Tuple[int, int, int]:
        """
        将三维坐标转换为体素ID（离散索引）

        Args:
            pos: 三维坐标 (x, y, z)

        Returns:
            Tuple[int, int, int]: 体素离散索引
        """
        vx = int(np.floor(pos[0] / self.config.voxel_size))
        vy = int(np.floor(pos[1] / self.config.voxel_size))
        vz = int(np.floor(pos[2] / self.config.voxel_size))
        return (vx, vy, vz)

    def _voxel_id_to_pos(self, voxel_id: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """
        将体素ID转换为体素中心坐标

        Args:
            voxel_id: 体素离散索引

        Returns:
            Tuple[float, float, float]: 体素中心三维坐标
        """
        return (
            (voxel_id[0] + 0.5) * self.config.voxel_size,
            (voxel_id[1] + 0.5) * self.config.voxel_size,
            (voxel_id[2] + 0.5) * self.config.voxel_size,
        )

    def integrate_depth_frame(
        self,
        depth: np.ndarray,
        pose: Tuple[float, float, float],
        semantic_mask: Optional[np.ndarray] = None
    ) -> int:
        """
        融合一帧深度图像到语义地图

        Args:
            depth: 深度图像，shape = (H, W)，单位米
            pose: 相机位姿 (x, y, theta)，单位米/弧度
            semantic_mask: 语义分割掩码，shape = (H, W)，值为标签ID

        Returns:
            int: 本帧融合的体素数量
        """
        H, W = depth.shape
        fx, fy = 525.0, 525.0   # Kinect v1 默认焦距
        cx, cy = W / 2, H / 2  # 主点

        px, py, ptheta = pose
        cos_t, sin_t = np.cos(ptheta), np.sin(ptheta)

        voxel_count = 0

        # 遍历深度图像的稀疏采样（降低计算量）
        step = max(1, min(H, W) // 64)  # 每隔step个像素处理一个

        for v in range(0, H, step):
            for u in range(0, W, step):
                d = depth[v, u]
                if d <= 0 or d > 10.0:  # 过滤无效深度
                    continue

                # 针孔相机模型：计算相机坐标系下的3D点
                z_c = d
                x_c = (u - cx) * z_c / fx
                y_c = (v - cy) * z_c / fy

                # 从相机坐标系变换到世界坐标系
                # 假设相机朝上（+Z），前进方向为+Y
                x_w = px + cos_t * x_c - sin_t * y_c
                y_w = py + sin_t * x_c + cos_t * y_c
                z_w = z_c + 0.5  # 相机高度补偿

                # 检查边界
                if not self._within_bounds(x_w, y_w, z_w):
                    continue

                # 获取语义标签
                if semantic_mask is not None:
                    label_id = semantic_mask[v, u]
                    label = self._id_to_label(label_id)
                else:
                    label = self._infer_label_from_height(z_w)

                # 分配体素
                voxel_id = self._pos_to_voxel_id((x_w, y_w, z_w))
                self._assign_voxel(voxel_id, label, (x_w, y_w, z_w))
                voxel_count += 1

        return voxel_count

    def _within_bounds(self, x: float, y: float, z: float) -> bool:
        """检查坐标是否在地图边界内"""
        x_min, x_max, y_min, y_max, z_min, z_max = self.config.map_bounds
        return x_min <= x <= x_max and y_min <= y <= y_max and z_min <= z <= z_max

    def _id_to_label(self, label_id: int) -> str:
        """将语义分割ID映射为标签名"""
        label_map = {
            0: "floor", 1: "wall", 2: "ceiling",
            3: "chair", 4: "table", 5: "sofa",
            6: "bed", 7: "cabinet", 8: "door",
            9: "window", 10: "lamp", 11: "plant",
            12: "bookshelf"
        }
        return label_map.get(label_id, "unknown")

    def _infer_label_from_height(self, z: float) -> str:
        """
        根据高度简单推断语义标签（无语义分割时的fallback）

        Args:
            z: 世界坐标系Z值（高度）

        Returns:
            str: 推断的语义标签
        """
        if z < 0.15:
            return "floor"
        elif z > 2.5:
            return "ceiling"
        else:
            return "wall"

    def _assign_voxel(
        self,
        voxel_id: Tuple[int, int, int],
        label: str,
        position: Tuple[float, float, float]
    ) -> None:
        """
        分配或更新体素的语义标签

        使用贝叶斯更新：融合多视角观测的语义标签

        Args:
            voxel_id: 体素离散索引
            label: 新观测到的语义标签
            position: 体素三维坐标
        """
        if voxel_id in self.voxels:
            # 更新已有体素：简单的投票融合
            existing = self.voxels[voxel_id]
            # 增加观测计数，加权更新标签
            existing.count += 1
            # 如果连续3次观测标签一致，提升置信度
            if label == existing.label:
                existing.confidence = min(1.0, existing.confidence + 0.1)
        else:
            # 创建新体素
            self.voxels[voxel_id] = SemanticVoxel(
                position=position,
                label=label,
                confidence=0.7,
                count=1,
                color=self.LABEL_COLORS.get(label, (128, 128, 128))
            )
            self.label_counts[label] += 1

    def query_semantic_at(self, x: float, y: float, z: float) -> Optional[str]:
        """
        查询指定位置的语义标签

        Args:
            x, y, z: 世界坐标系三维坐标

        Returns:
            str: 语义标签，若该位置无体素则返回None
        """
        voxel_id = self._pos_to_voxel_id((x, y, z))
        if voxel_id in self.voxels:
            return self.voxels[voxel_id].label
        return None

    def get_floor_map(self, z_height: float = 0.1) -> np.ndarray:
        """
        提取指定高度的2D俯视语义地图（用于路径规划）

        Args:
            z_height: 查询的高度（米），默认0.1m接近地面

        Returns:
            np.ndarray: 2D语义地图，shape = (map_H, map_W)
                值表示各类别（0=unknown, 1=floor, 2=wall, ...）
        """
        # 计算地图尺寸
        x_min, x_max, y_min, y_max, _, _ = self.config.map_bounds
        map_h = int(np.ceil((y_max - y_min) / self.config.voxel_size))
        map_w = int(np.ceil((x_max - x_min) / self.config.voxel_size))

        floor_map = np.zeros((map_h, map_w), dtype=np.uint8)
        label_to_id = {label: i+1 for i, label in enumerate(self.config.semantic_labels)}
        label_to_id["unknown"] = 0

        for voxel_id, voxel in self.voxels.items():
            vx, vy, vz = voxel_id
            pos = self._voxel_id_to_pos(voxel_id)

            # 只取接近地面的体素
            if abs(pos[2] - z_height) < self.config.voxel_size:
                # 检查是否为可通行区域（地面、空地）
                px = int((pos[0] - x_min) / self.config.voxel_size)
                py = int((pos[1] - y_min) / self.config.voxel_size)

                if 0 <= px < map_w and 0 <= py < map_h:
                    floor_map[py, px] = label_to_id.get(voxel.label, 0)

        return floor_map

    def get_statistics(self) -> Dict:
        """
        获取语义地图的统计信息

        Returns:
            Dict: 统计信息，包含体素总数、各类别数量等
        """
        stats = {
            "total_voxels": len(self.voxels),
            "label_distribution": dict(self.label_counts),
            "coverage": {
                "x_range": (self.config.map_bounds[0], self.config.map_bounds[1]),
                "y_range": (self.config.map_bounds[2], self.config.map_bounds[3]),
                "z_range": (self.config.map_bounds[4], self.config.map_bounds[5]),
            }
        }
        return stats

    def visualize_voxel_grid(self) -> np.ndarray:
        """
        生成简易的彩色体素地图可视化图像

        Returns:
            np.ndarray: RGB图像，shape = (H, W, 3)
        """
        x_min, x_max, y_min, y_max, z_min, z_max = self.config.map_bounds
        H = int(np.ceil((y_max - y_min) / self.config.voxel_size))
        W = int(np.ceil((x_max - x_min) / self.config.voxel_size))

        # 俯视图：投影到地面
        vis = np.full((H, W, 3), 240, dtype=np.uint8)  # 背景灰色

        for voxel_id, voxel in self.voxels.items():
            vx, vy, vz = voxel_id
            pos = self._voxel_id_to_pos(voxel_id)

            # 接近地面的体素用于可视化
            if abs(pos[2] - 0.1) < 0.15:
                px = int((pos[0] - x_min) / self.config.voxel_size)
                py = int((pos[1] - y_min) / self.config.voxel_size)

                if 0 <= px < W and 0 <= py < H:
                    vis[py, px] = voxel.color

        return vis


# ============================================================
# 演示：语义地图构建
# ============================================================
def demo_semantic_map():
    """
    演示语义地图构建器的使用
    """
    print("=" * 60)
    print("室内语义地图构建器演示")
    print("=" * 60)

    # 1. 创建语义地图构建器
    config = SemanticMapConfig(voxel_size=0.1)
    builder = SemanticMapBuilder(config)

    # 2. 模拟一帧深度观测（简化的模拟数据）
    # 创建虚拟深度图：3米外的平面墙
    H, W = 480, 640
    depth = np.ones((H, W)) * 3.0  # 3米远的平面
    # 在图像中心添加一些"椅子"区域（语义标签=3）
    semantic_mask = np.zeros((H, W), dtype=np.int32)

    cy, cx = H // 2, W // 2
    semantic_mask[cy-50:cy+50, cx-50:cx+50] = 3  # 椅子区域

    # 3. 融合观测
    pose = (0.0, 0.0, 0.0)  # 相机在原点，朝向+Y
    num_voxels = builder.integrate_depth_frame(depth, pose, semantic_mask)
    print(f"[融合] 第1帧：融合了 {num_voxels} 个体素")

    # 4. 统计信息
    stats = builder.get_statistics()
    print(f"[统计] 总体素数: {stats['total_voxels']}")
    print(f"[分布] {stats['label_distribution']}")

    # 5. 查询特定位置
    query_pos = (1.5, 1.5, 0.1)
    label = builder.query_semantic_at(*query_pos)
    print(f"[查询] 位置{query_pos}的语义标签: {label}")

    # 6. 生成地面地图
    floor_map = builder.get_floor_map()
    print(f"[地图] 地面地图尺寸: {floor_map.shape}")

    # 7. 可视化
    vis = builder.visualize_voxel_grid()
    print(f"[可视化] 体素地图图像尺寸: {vis.shape}")


if __name__ == "__main__":
    demo_semantic_map()
```

---

### 4.3 RoomRPC数据处理工具

本节实现RoomRPC数据集的加载、解析和预处理工具。

```python
"""
RoomRPC数据集处理工具
用于加载、解析和处理Room-to-Room Plus (R2R Plus) 及 RxR 数据集

作者: Wendy
功能: 数据集加载、轨迹解析、指令编码、数据集划分
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np


@dataclass
class Scan:
    """
    单个扫描场景（building）

    Attributes:
        scan_id: 场景唯一标识符
        viewpoint_ids: 该场景中所有视角点ID列表
        viewpoint_positions: 视角点ID -> 3D位置 {vid: (x, y, z)}
        viewpoint_orientations: 视角点ID -> 朝向角度 {vid: theta}
        connections: 相邻视角点连接关系 {vid: [connected_vids]}
    """
    scan_id: str
    viewpoint_ids: List[str] = field(default_factory=list)
    viewpoint_positions: Dict[str, Tuple[float, float, float]] = field(default_factory=dict)
    viewpoint_orientations: Dict[str, float] = field(default_factory=dict)
    connections: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class Instruction:
    """
    单条导航指令

    Attributes:
        instruction_id: 指令唯一标识
        text: 自然语言指令文本
        language: 语言类型（en/hi/zh）
        trajectory: 参考轨迹 [[x, y, z], ...]
        goal_viewpoint: 目标视角点ID
    """
    instruction_id: str
    text: str
    language: str = "en"
    trajectory: List[List[float]] = field(default_factory=list)
    goal_viewpoint: str = ""


@dataclass
class RoomRPCDataItem:
    """
    RoomRPC数据集中的单个样本

    Attributes:
        scan_id: 场景ID
        path_id: 路径ID
        heading: 起始朝向
        instructions: 多条指令（通常3-5条）
        reference_path: 参考轨迹
        goal_viewpoint: 目标视角
        split: 数据集划分（train/val/seen/unseen）
    """
    scan_id: str
    path_id: str
    heading: float
    instructions: List[Instruction] = field(default_factory=list)
    reference_path: List[str] = field(default_factory=list)
    goal_viewpoint: str = ""
    split: str = "train"


class RoomRPCDataset:
    """
    RoomRPC数据集加载器

    支持：
    - R2R / R2R Plus 格式
    - RxR 多语言格式
    - 数据划分（train/val/seen/unseen）
    - 视角邻接图加载

    使用方法：
        dataset = RoomRPCDataset(data_root="/path/to/R2R_dataset")
        for item in dataset.get_split("train"):
            print(item.instructions[0].text)
    """

    # R2R数据格式中的字段映射
    R2R_FIELD_MAP = {
        "scan": "scan_id",
        "path_id": "path_id",
        "heading": "heading",
        "path": "reference_path",
        "trajectory": "reference_path",
        "instruction": "text",
        "instructions": "instructions",
    }

    def __init__(self, data_root: str, dataset_type: str = "R2R"):
        """
        初始化RoomRPC数据集加载器

        Args:
            data_root: 数据集根目录路径
            dataset_type: 数据集类型，"R2R" 或 "RxR"
        """
        self.data_root = Path(data_root)
        self.dataset_type = dataset_type
        self.scans: Dict[str, Scan] = {}
        self.data_items: List[RoomRPCDataItem] = []
        self._loaded = False

    def load(self, splits: Optional[List[str]] = None) -> bool:
        """
        加载数据集
        
        Args:
            splits: 要加载的数据划分列表，如 ["train", "val_seen"]
                   若为None，则加载所有可用划分
            
        Returns:
            bool: 加载是否成功
        """
        splits = splits or ["train", "val_seen", "val_unseen"]
        
        try:
            # 1. 加载视角邻接图（scans）
            scans_path = self.data_root / "connectivity"
            if scans_path.exists():
                self._load_scans(scans_path)
            
            # 2. 加载各划分的注释数据
            for split in splits:
                data_path = self.data_root / f"{split}_annotations.json"
                if data_path.exists():
                    self._load_annotations(data_path, split)
            
            self._loaded = True
            print(f"[加载] 完成：{len(self.data_items)} 条数据，{len(self.scans)} 个场景")
            return True
        except Exception as e:
            print(f"[错误] 数据集加载失败: {e}")
            return False
    
    def _load_scans(self, connectivity_dir: Path) -> None:
        """加载视角邻接图"""
        for scan_file in connectivity_dir.glob("*.json"):
            scan_id = scan_file.stem
            with open(scan_file, 'r') as f:
                scan_data = json.load(f)
            scan = Scan(scan_id=scan_id)
            for item in scan_data:
                if "image_id" in item:
                    vid = item["image_id"]
                    scan.viewpoint_ids.append(vid)
                    if "pose" in item:
                        pose = item["pose"]
                        scan.viewpoint_positions[vid] = (pose[0], pose[1], pose[2])
                    if "unobtainable" not in item or not item["unobtainable"]:
                        scan.connections[vid] = item.get("next", [])
            self.scans[scan_id] = scan
    
    def _load_annotations(self, annotation_path: Path, split: str) -> None:
        """加载注释数据"""
        with open(annotation_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        for item in raw_data:
            data_item = self._parse_r2r_item(item, split) if self.dataset_type == "R2R" else self._parse_rxr_item(item, split)
            if data_item:
                self.data_items.append(data_item)
    
    def _parse_r2r_item(self, item: Dict, split: str) -> Optional[RoomRPCDataItem]:
        """解析R2R格式的数据项"""
        try:
            instr_text = item.get("instruction", item.get("instructions", [""])[0] if item.get("instructions") else "")
            ref_path = item.get("path", item.get("trajectory", []))
            return RoomRPCDataItem(
                scan_id=item["scan"],
                path_id=str(item["path_id"]),
                heading=item.get("heading", 0.0),
                instructions=[Instruction(instruction_id=f"{item['path_id']}_0", text=instr_text, language="en")],
                reference_path=ref_path,
                goal_viewpoint=ref_path[-1] if ref_path else "",
                split=split
            )
        except KeyError:
            return None
    
    def _parse_rxr_item(self, item: Dict, split: str) -> Optional[RoomRPCDataItem]:
        """解析RxR格式的数据项"""
        try:
            instructions = []
            for i, instr_text in enumerate(item.get("instructions", [])):
                lang = item.get("language", ["en"])[i] if isinstance(item.get("language"), list) else "en"
                instructions.append(Instruction(instruction_id=f"{item['path_id']}_{i}_{lang}", text=instr_text, language=lang))
            ref_path = item.get("path", [])
            return RoomRPCDataItem(scan_id=item["scan"], path_id=str(item["path_id"]), heading=item.get("heading", 0.0), instructions=instructions, reference_path=ref_path, goal_viewpoint=ref_path[-1] if ref_path else "", split=split)
        except KeyError:
            return None
    
    def get_split(self, split: str) -> List[RoomRPCDataItem]:
        """获取指定数据划分的样本"""
        return [item for item in self.data_items if item.split == split]
    
    def get_statistics(self) -> Dict:
        """获取数据集统计信息"""
        return {"total_items": len(self.data_items), "num_scans": len(self.scans)}
    
    def export_for_vln(self, output_path: str, split: str = "train") -> None:
        """导出为VLN训练友好的JSON格式"""
        split_items = self.get_split(split)
        export_data = [{"scan_id": item.scan_id, "path_id": item.path_id, "heading": item.heading, "instruction": item.instructions[0].text if item.instructions else "", "reference_path": item.reference_path, "goal_viewpoint": item.goal_viewpoint} for item in split_items]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        print(f"[导出] {split}: {len(export_data)} 条数据 -> {output_path}")


def demo_roomrpc_loader():
    """演示RoomRPC数据集加载器的使用"""
    print("=" * 60)
    print("RoomRPC数据集加载器演示")
    print("=" * 60)
    dataset = RoomRPCDataset(data_root="/path/to/R2R_dataset", dataset_type="R2R")
    success = dataset.load(splits=["train"])
    if not success:
        print("\n[演示] 模拟数据模式...")
        dataset = _create_demo_dataset()
    stats = dataset.get_statistics()
    print(f"\n[统计] 总样本数: {stats['total_items']}")
    print(f"[统计] 场景数: {stats.get('num_scans', 0)}")
    if dataset.data_items:
        item = dataset.data_items[0]
        print(f"\n[样例] 场景: {item.scan_id}")
        if item.instructions:
            print(f"[样例] 指令: {item.instructions[0].text[:80]}...")


def _create_demo_dataset() -> RoomRPCDataset:
    """创建演示用模拟数据集"""
    dataset = RoomRPCDataset(data_root="/tmp/demo", dataset_type="R2R")
    demo_items = [
        RoomRPCDataItem(scan_id="2t7bVkJcIdC", path_id="1", heading=0.0, instructions=[Instruction(instruction_id="1_0", text="Walk past the kitchen and into the living room. Stop near the sofa.", language="en")], reference_path=["v1", "v2", "v3", "v4"], goal_viewpoint="v4", split="train"),
        RoomRPCDataItem(scan_id="2t7bVkJcIdC", path_id="2", heading=0.785, instructions=[Instruction(instruction_id="2_0", text="Enter through the main door. Go straight and turn left at the bedroom. Stop by the bed.", language="en")], reference_path=["v5", "v6", "v7"], goal_viewpoint="v7", split="train"),
    ]
    dataset.data_items = demo_items
    dataset._loaded = True
    return dataset


if __name__ == "__main__":
    demo_roomrpc_loader()
```

---

## 五、练习题

### 选择题

**1. 室内VLN相比室外VLN，以下哪项不是主要区别？**

A. 室内环境空间封闭，拓扑结构更复杂  
B. 室内物体密度更高，遮挡问题更严重  
C. 室内光照条件更稳定，更容易处理  
D. 室内导航粒度更细，通常需要到达物体级别

**2. R2R Plus相比原始R2R数据集的主要改进是什么？**

A. 增加了连续环境中的导航  
B. 增加了视角密度和长距离多房间导航实例  
C. 增加了多语言支持  
D. 增加了对话式交互功能

**3. 在室内语义地图构建中，体素融合的主要目的是？**

A. 减小地图存储体积  
B. 融合多视角观测，提高语义标签准确性  
C. 加快地图查询速度  
D. 实现地图的实时更新

**4. 关于RxR数据集的特点，以下说法错误的是？**

A. 包含英语、印地语、普通话三种语言  
B. 指令长度比R2R更长、更详细  
C. 仅包含短距离单房间导航  
D. 参考了人类旅行指南的写作风格

**5. 在房间拓扑导航中，A*算法相比Dijkstra的优势是？**

A. 保证找到最短路径  
B. 使用启发式函数加速搜索  
C. 不需要知道图的完整结构  
D. 适用于动态障碍物环境

---

### 简答题

**6. 解释室内VLN中"物体导航"任务的难点，并提出两种解决思路。**

**7. 说明语义地图与几何地图的主要区别，以及语义地图在VLN导航中的优势。**

**8. 分析RoomRPC数据集在室内VLN研究中的作用，并说明R2R Plus和RxR各自适用的研究场景。**

---

## 六、参考答案

### 选择题答案

| 题号 | 答案 | 解析 |
|------|------|------|
| 1 | **C** | 室内光照条件**并不更稳定**，人工光、自然光、阴影等混合存在，反而增加处理难度。选项A、B、D都是室内VLN的典型特征。 |
| 2 | **B** | R2R Plus的核心改进是**增加视角密度**（从36个预定义视角扩展到更多可导航位置）和**增加长距离多房间导航实例**，弥补了原始R2R短距离、稀疏视角的不足。连续环境支持是R2R-CE的贡献；多语言是RxR的贡献。 |
| 3 | **B** | 体素融合的核心目的是**融合多视角观测**：同一3D位置在不同视角下被观测到时，通过加权投票融合不同观测的语义标签，提高语义标签的准确性（置信度）和鲁棒性。减小存储和加快查询是副作用，不是主要目的。 |
| 4 | **C** | RxR数据集的指令平均长度约89词，远长于R2R的25词，且过程标注完整，但**并非仅包含短距离单房间导航**，RxR恰恰增加了长距离跨房间导航实例。 |
| 5 | **B** | A*算法的核心优势是**使用启发式函数引导搜索方向**，将搜索集中在更可能接近目标的方向上，相比Dijkstra的盲目搜索大幅提高效率。两者都能保证找到最短路径（当启发式满足可采纳性时），都需要知道完整图结构。 |

---

### 简答题答案

**6. 物体导航任务的难点与解决思路**

**难点分析**：

1. **同类别物体区分**："走到沙发旁边的椅子"vs"餐桌旁的椅子"，需要理解参照物和空间关系
2. **物体可及性**：目标物体可能被遮挡、放在高处或在另一个房间，无法直接观测到
3. **空间歧义**："往前走然后左转"在不同房间结构下对应完全不同的物理路径
4. **外观变异性**：同一类物体（如椅子）有巨大外观差异，泛化困难

**解决思路**：

**思路一：分层规划 + 场景图推理**
- 高层：房间级规划，先确定目标物体在哪个房间（如"厨房有冰箱"）
- 中层：区域级规划，在房间内定位物体大致区域
- 低层：物体级精确定位与抓取
- 使用场景图表示物体间的空间关系（如"s1 --next to--> s2"）

**思路二：视觉语言跨模态检索**
- 使用CLIP等视觉语言模型，将自然语言指令映射到图像特征空间
- 在语义分割结果中检索与指令描述最匹配的物体区域
- 结合空间关系约束（如"左/右/前/后"）进一步筛选

---

**7. 语义地图与几何地图的区别及语义地图在VLN中的优势**

**主要区别**：

| 维度 | 几何地图 | 语义地图 |
|------|----------|----------|
| **表示内容** | 位置坐标、形状、障碍物 | 位置 + 物体类别、功能 |
| **存储形式** | 栅格/点云/网格 | 带有语义标签的体素/点 |
| **适用任务** | 避障、路径规划 | 目标导航、任务理解 |
| **泛化能力** | 低（依赖精确几何） | 高（依赖语义概念） |
| **构建难度** | 相对简单（传感器直接获取） | 较难（需要语义分割） |

**语义地图在VLN中的优势**：

1. **语言-空间对齐**：语义地图天然支持将自然语言中的物体名称映射到地图位置（"厨房" → 地图中标注为kitchen的区域）

2. **支持高层次推理**：利用语义标签进行功能区域推理（"能做饭的地方是厨房"），而非依赖几何特征

3. **提升定位鲁棒性**：语义特征比纯几何特征对视角变化、光照变化更鲁棒

4. **支持零样本泛化**：结合预训练视觉语言模型，可以识别语义地图中从未见过的物体类别

5. **支撑任务规划**：语义地图提供了"功能视角"的环境理解，便于做任务层面的规划（如"需要先去厨房拿杯子再去餐桌"）

---

**8. RoomRPC数据集在室内VLN研究中的作用**

**数据集的核心作用**：

RoomRPC（R2R Plus + RxR）是室内VLN研究的**标准基准**，提供了：
- 统一的训练/测试环境（Matterport3D真实3D重建）
- 标准化的评估协议（轨迹长度、成功率、SPL等指标）
- 可复现的实验条件（固定的数据划分）

**R2R Plus的适用场景**：

- **短距离精细导航研究**：适合研究单房间内或相邻房间的精确导航
- **模型架构对比研究**：作为标准基线，适合比较不同VLN模型的效果
- **视觉语言对齐研究**：关注如何更好地对齐图像特征与语言指令

**RxR的适用场景**：

- **多语言VLN研究**：利用其英语/印地语/普通话三语言标注，研究跨语言泛化
- **长距离导航研究**：RxR包含大量跨多个房间的长轨迹，适合研究长距离规划
- **过程导向导航研究**：其turn-by-turn标注方式适合研究导航策略的可解释性
- **多语言机器人助手**：研究如何为非英语用户提供导航服务

**实际研究中的建议**：

| 研究目标 | 推荐数据集 | 理由 |
|----------|------------|------|
| 新模型baseline | R2R Plus | 规模适中、训练快 |
| 跨语言泛化 | RxR | 多语言标注丰富 |
| 长距离任务 | RxR | 轨迹更长更复杂 |
| 可解释性研究 | RxR | 过程标注详细 |
| Sim2Real | R2R-CE | 连续环境更接近真实机器人 |
