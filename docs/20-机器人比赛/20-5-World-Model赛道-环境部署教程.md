# ③ 赛道二 World Model 部署课程

> **EVAC (EnerVerse-AC)** — 动作条件视频生成模型
>
> **文档编号：03** 环境部署
>
> 比赛: AgiBot World Challenge @ ICRA 2026 - World Model Track
> 目标: 根据首帧图像 + 动作信号生成后续视频，提交到 HuggingFace 评测

---

## 📋 任务概览

| 项目 | 内容 |
|------|------|
| 模型 | EVAC (EnerVerse-AC) |
| 任务 | 根据首帧图像 + 动作信号生成后续视频 |
| 评测指标 | PSNR, Scene Consistency, nDTW |
| 官方评测 | HuggingFace Space: ICRA26WM |
| 截止日期 | 2026-04-20 |

### 基线参考分数

| 指标 | EVAC 基线 |
|------|-----------|
| PSNR | 20.98 |
| Scene Consistency | 0.90 |
| nDTW | 0.91 |

---

## 🏗️ 系统架构

```
输入数据                          输出
├── frame.png (首帧图像)          生成视频 (31帧)
├── proprio_stats.h5 (动作)       └── frame_00000.jpg ~ frame_00030.jpg
├── head_intrinsic_params.json    └── head_color.mp4 (可选)
└── head_extrinsic_params_aligned.json
```

---

## 📦 环境要求

| 组件 | 版本/要求 |
|------|-----------|
| Python | 3.10.4 |
| CUDA | 11.8+ (训练) / 12.1 (推理) |
| GPU | L40 或同等显卡 (建议 24GB+ 显存) |
| 存储 | ~20GB (模型 + 数据) |
| 操作系统 | Linux |

---

## ✅ 第一阶段：环境准备

### 步骤 1.1：克隆代码仓库

```bash
cd /root/gpufree-data/projects/track2_worldmodel
git clone https://github.com/AgibotTech/AgiBotWorldChallengeICRA2026-WorldModelBaseline.git code
cd code
```

### 步骤 1.2：初始化 git 子模块

```bash
git submodule update --init --recursive
```

> 注意：`evac/` 是一个子模块，必须初始化后才能使用

### 步骤 1.3：创建 conda 环境

```bash
conda create -n enerverse python=3.10.4 -y
conda activate enerverse
```

### 步骤 1.4：安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 步骤 1.5：安装 pytorch3d（可选，推理需要）

```bash
pip install --no-index --no-cache-dir pytorch3d -f https://dl.fbaipublicfiles.com/pytorch3d/packaging/wheels/py310_cu121_pyt240/download.html
```

### ⚠️ 重要：PYTHONPATH 环境变量冲突

**问题描述：**
系统中 `PYTHONPATH` 包含 `/geniesim/generator_env/lib/python3.12/site-packages`，会与 enerverse 的 numpy 产生冲突，导致 `ModuleNotFoundError: No module named 'numpy.core._multiarray_umath'`

**解决方案（二选一）：**

**方案 A：使用时 unset**
```bash
unset PYTHONPATH
conda activate enerverse
# 然后运行你的命令
```

**方案 B：永久修复**
```bash
# 在 ~/.bashrc 中添加
echo 'export PYTHONPATH=""' >> ~/.bashrc
source ~/.bashrc
```

**方案 C：所有命令前加前缀**
```bash
unset PYTHONPATH && /opt/conda/envs/enerverse/bin/python your_script.py
```

---

## ✅ 第二阶段：模型准备

### 步骤 2.1：下载 EVAC 权重

EVAC checkpoint 已下载到：`/root/gpufree-data/models/EnerVerse-AC/EnerV_AC_deepspeed_v0.1.pt` (6GB)

或从 HuggingFace 下载：
```bash
huggingface-cli download agibot-world/EnerVerse-AC EnerV_AC_deepspeed_v0.1.pt --local-dir /root/gpufree-data/models/EnerVerse-AC
```

### 步骤 2.2：下载 CLIP ViT-H-14 模型

CLIP 模型已下载到：`/root/gpufree-data/models/CLIP-ViT-H-14/open_clip_pytorch_model.bin` (3.9GB)

或重新下载：
```bash
mkdir -p /root/gpufree-data/models/CLIP-ViT-H-14
huggingface-cli download laion/CLIP-ViT-H-14-laion2B-s32B-b79K open_clip_pytorch_model.bin --local-dir /root/gpufree-data/models/CLIP-ViT-H-14
```

---

## ✅ 第三阶段：数据集准备

### 步骤 3.1：下载数据集

```bash
mkdir -p /root/gpufree-data/datasets/track2
cd /root/gpufree-data/datasets/track2

# 下载验证集（用于本地测试）
huggingface-cli download agibot-world/AgiBotWorldChallenge-2026 WorldModel/val.tar.gz --local-dir . --repo-type dataset

# 下载测试集（用于正式提交）
huggingface-cli download agibot-world/AgiBotWorldChallenge-2026 WorldModel/test.tar.gz --local-dir . --repo-type dataset

# 解压
tar -xzf val.tar.gz
tar -xzf test.tar.gz
```

### ⚠️ 重要：数据集结构说明

**不要重新组织数据！** 原始数据结构就是正确的：

```
test/
└── info_dataset/
    ├── 2012/                    # 年份（不是 task_id！）
    │   ├── 12385780013200460/  # Episode 长ID（不是 episode_0！）
    │   │   ├── frame.png
    │   │   ├── proprio_stats.h5
    │   │   └── ...
    │   ├── 12386490148101790/
    │   └── 12389110213002608/
    ├── 2014/
    ├── 2015/
    └── ... (其他年份)
```

**关键点：**
- `2012`, `2014` 等是**年份/场景ID**，不是 task_0, task_1
- `12385780013200460` 等是**原始 episode 长ID**，不是 episode_0, episode_1
- **不要**重新组织为 task/episode 结构！

### 步骤 3.2：验证数据结构

```bash
ls /root/gpufree-data/datasets/track2/test/info_dataset/
# 应该显示: 2012 2014 2015 2016 2017 2019 2020 2021 2022 2023

ls /root/gpufree-data/datasets/track2/test/info_dataset/2012/
# 应该显示: 12385780013200460 12386490148101790 12389110213002608
```

---

## ✅ 第四阶段：配置文件准备

### 步骤 4.1：创建推理配置文件

从模板复制并修改：

```bash
cd /root/gpufree-data/projects/track2_worldmodel/code

# 复制配置
cp evac/configs/agibotworld/config.yaml infer_config.yaml

# 修改路径
sed -i 's|PATH_TO_CHECKPOINT|/root/gpufree-data/models/EnerVerse-AC/EnerV_AC_deepspeed_v0.1.pt|g' infer_config.yaml
sed -i 's|CLIP_WEIGHT_PATH|/root/gpufree-data/models/CLIP-ViT-H-14/open_clip_pytorch_model.bin|g' infer_config.yaml
```

### 步骤 4.2：验证配置

```bash
grep -E "pretrained_checkpoint|abspath" infer_config.yaml
```

应该显示：
```
pretrained_checkpoint: /root/gpufree-data/models/EnerVerse-AC/EnerV_AC_deepspeed_v0.1.pt
abspath: /root/gpufree-data/models/CLIP-ViT-H-14/open_clip_pytorch_model.bin
```

### ⚠️ 代码修复：infer_all.py 语法错误

如果运行时报 `SyntaxError`，需要修复 `evac/main/infer_all.py` 第 224 行：

```bash
# 找到这行（缺少逗号）
parser.add_argument(
    "--input_root", "-i", type=str
    help="Path to the input directory"
)

# 修改为（添加逗号）
parser.add_argument(
    "--input_root", "-i", type=str,
    help="Path to the input directory"
)
```

---

## ✅ 第五阶段：推理测试

### 步骤 5.1：运行推理

```bash
cd /root/gpufree-data/projects/track2_worldmodel/code

# 创建输出目录
mkdir -p /root/gpufree-data/datasets/track2/output

# 运行推理（n_pred=1 表示每个样本生成1个预测）
# 注意：-i 参数是 info_dataset 目录本身，不是其父目录！
unset PYTHONPATH && /opt/conda/envs/enerverse/bin/python evac/main/infer_all.py \
    -i /root/gpufree-data/datasets/track2/test/info_dataset \
    -s /root/gpufree-data/datasets/track2/output \
    --ckp_path /root/gpufree-data/models/EnerVerse-AC/EnerV_AC_deepspeed_v0.1.pt \
    --config_path /root/gpufree-data/projects/track2_worldmodel/code/infer_config.yaml \
    --n_pred 1 \
    --device cuda
```

### ⚠️ 输出格式说明

推理脚本输出的是 **mp4 视频文件**，不是 jpg 帧序列！

```
output_video/
├── 2012/                              # 年份
│   ├── 12385780013200460/             # Episode 长ID
│   │   ├── 0/                         # 预测 ID
│   │   │   └── video/
│   │   │       └── outputs.mp4        # 视频文件！
│   │   ├── 1/
│   │   │   └── video/
│   │   │       └── outputs.mp4
│   │   └── 2/
│   └── ... (其他 episodes)
├── 2014/
└── ...
```

**帧数计算：** 每个视频帧数 = proprio_stats.h5 中的动作数量 - 1

---

## ✅ 第六阶段：完整推理（可选）

### 步骤 6.1：在完整验证集上推理

```bash
# 运行完整验证集推理（可能需要数小时）
cd /root/gpufree-data/projects/track2_worldmodel/code

unset PYTHONPATH && /opt/conda/envs/enerverse/bin/python evac/main/infer_all.py \
    -i /root/gpufree-data/datasets/track2/test/info_dataset \
    -s /root/gpufree-data/datasets/track2/full_output \
    --ckp_path /root/gpufree-data/models/EnerVerse-AC/EnerV_AC_deepspeed_v0.1.pt \
    --config_path /root/gpufree-data/projects/track2_worldmodel/code/infer_config.yaml \
    --n_pred 3 \
    --device cuda
```

### 步骤 6.2：在测试集上推理（用于提交）

```bash
# 运行测试集推理
cd /root/gpufree-data/projects/track2_worldmodel/code

unset PYTHONPATH && /opt/conda/envs/enerverse/bin/python evac/main/infer_all.py \
    -i /root/gpufree-data/datasets/track2/test/info_dataset \
    -s /root/gpufree-data/datasets/track2/test_output \
    --ckp_path /root/gpufree-data/models/EnerVerse-AC/EnerV_AC_deepspeed_v0.1.pt \
    --config_path /root/gpufree-data/projects/track2_worldmodel/code/infer_config.yaml \
    --n_pred 3 \
    --device cuda
```

### ⚠️ 重要：提交格式（必须！）

**推理输出需要转换为官方要求的提交格式！**

**正确格式：**
```
submission_dataset/
├── meta_info.txt
├── 2012/
│   ├── 12385780013200460/
│   │   ├── 0/
│   │   │   └── video/
│   │   │       └── frame_00000.jpg ~ frame_00053.jpg
│   │   ├── 1/
│   │   │   └── video/
│   │   └── 2/
│   │       └── video/
│   └── 12386490148101790/
│       └── ...
├── 2014/
└── ...
```

**生成提交包的命令：**
```bash
cd /root/gpufree-data/datasets/track2

# 1. 创建正确的目录结构
mkdir -p submission_dataset
cp -r test_output_video/* submission_dataset/

# 2. 添加 meta_info.txt（你的注册邮箱）
echo "your_email@example.com" > submission_dataset/meta_info.txt

# 3. 打包
zip -r submission.zip ./submission_dataset
```

**❌ 错误格式（不要用）：**
```
PREDICTIONS/task_0/episode_0/0/video/frame_*.jpg  # 这是错的！
```

---

## ⚠️ 常见问题

### Q1: `ModuleNotFoundError: No module named 'numpy.core._multiarray_umath'`
**原因：** PYTHONPATH 环境变量冲突  
**解决：** `unset PYTHONPATH && conda activate enerverse`

### Q2: `SyntaxError: invalid syntax` at infer_all.py
**原因：** 代码缺少逗号（官方 bug）  
**解决：** 参考第四阶段第 4.2 节的修复

### Q3: CLIP 下载被限速
**解决：** 使用 `huggingface-cli` 并设置 `HF_TOKEN`

### Q4: 显存不足 (CUDA Out of Memory)
**解决：** 减少 `batch_size` 或在配置中使用 `fp16` 推理

### Q5: 数据结构不匹配
**解决：** 参考第三阶段第 3.2 节 - **不要重新组织数据！**

### Q6: huggingface-cli 下载 404
**原因：** 需要指定 `--repo-type dataset`  
**解决：** `huggingface-cli download ... --repo-type dataset`

### Q7: 提交后返回 "Evaluation error: Format Error!"
**原因：** 提交格式错误！  
**解决：** 确保使用正确的目录结构：
- 根目录必须是 `submission_dataset/`（不是 `PREDICTIONS/`）
- 年份文件夹必须是 `2012`, `2014` 等（不是 `task_0`, `task_1`）
- Episode 文件夹必须是长 ID 如 `12385780013200460`（不是 `episode_0`）

### Q8: 推理输出是 mp4 而不是 jpg
**原因：** 正常！推理脚本输出 mp4 视频  
**解决：** 使用 ffmpeg 转换为帧序列：
```bash
ffmpeg -i outputs.mp4 -q:v 2 frame_%05d.jpg -y
```

---

## 📁 关键路径汇总

| 组件 | 路径 |
|------|------|
| 代码仓库 | `/root/gpufree-data/projects/track2_worldmodel/code/` |
| EVAC 权重 | `/root/gpufree-data/models/EnerVerse-AC/EnerV_AC_deepspeed_v0.1.pt` |
| CLIP 模型 | `/root/gpufree-data/models/CLIP-ViT-H-14/open_clip_pytorch_model.bin` |
| 测试集数据 | `/root/gpufree-data/datasets/track2/test/info_dataset/` |
| 推理输出（视频） | `/root/gpufree-data/datasets/track2/test_output_video/` |
| 提交包 | `/root/gpufree-data/datasets/track2/submission.zip` |
| 推理配置 | `/root/gpufree-data/projects/track2_worldmodel/code/infer_config.yaml` |
| 优化脚本 | `/root/gpufree-data/projects/track2_worldmodel/evac_modified/` |

---

## 📝 执行记录

| 时间 | 步骤 | 状态 | 备注 |
|------|------|------|------|
| - | 1.1 克隆代码仓库 | ✅ | 已克隆到 `code/` |
| - | 1.2-1.4 依赖检查 | ✅ | enerverse 环境已包含所有依赖 |
| - | ⚠️ PYTHONPATH 冲突 | ✅ | 需 unset PYTHONPATH 使用 |
| - | 2.1 CLIP ViT-H-14 | ✅ | 3.9GB 已下载 |
| - | evac 子模块 | ✅ | 已初始化 |
| - | 推理配置文件 | ✅ | 已创建并替换路径 |
| - | 数据集下载 | ✅ | val.tar.gz + test.tar.gz |
| - | 数据结构验证 | ✅ | 保持原始结构（不重新组织）|
| - | 推理测试 | ✅ | 成功生成 mp4 视频 |
| 2026-04-08 | ⚠️ 提交格式错误修复 | ✅ | 修复为 submission_dataset/年份/长ID |
| 2026-04-08 | 相机校准补偿优化 | ✅ | rot=0.01, trans=0.005 有效 |



## ✅ 第七阶段：推理流程与理论对照（重点章节）

### 7.1 推理流程全景图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EVAC 推理完整流程                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  【输入】                                                                   │
│  frame.png (512×512) + proprio_stats.h5 (7维) + camera_params            │
│       ↓                        ↓                      ↓                    │
│  阶段一：输入编码                                                        │
│  CLIP ViT-H-14 ─────────→ 1024维    MLP ─────────→ 14维               │
│       └──────────────────────┬───────────────────────┘                    │
│                              ↓                                              │
│  阶段二：条件融合 ────→ 1038维 ────→ Cross Attention 注入 U-Net           │
│                              ↓                                              │
│  阶段三：DDIM 循环（~70%时间）←── 主要瓶颈                                │
│  初始化纯噪声 zₜ → for t in reversed(timesteps): → z₀(干净隐变量)       │
│                              ↓                                              │
│  阶段四：VAE解码 ────→ 31帧视频输出 (512×512)                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 每一步骤详解与理论映射

#### 步骤 A：读取首帧图像 → CLIP 编码（对应 20-3 第3章 3.2节）

**代码位置**：`evac/model/backbone/clip_encoder.py`

**做了什么**：`image → CLIP → [1024] 语义特征向量`

**理论对应**：CLIP（Contrastive Language-Image Pre-training）见过4亿张图文对，理解语义而非仅认像素。

**可调优点**：换更大CLIP（ViT-G-14/EVA-CLIP）| 场景适配微调 | 多尺度特征

---

#### 步骤 B：读取动作信号 → MLP 编码（对应 20-3 第3章 3.3节）

**代码位置**：`evac/model/backbone/action_encoder.py`

**做了什么**：`action [T,7] → MLP → [T,14]`

**动作7维**：x,y,z(位置) + qx,qy,qz,qw(四元数姿态) + gripper(夹爪)

**为什么 nDTW 容易低**：当前 MLP 处理独立帧动作，**无法建模时序依赖**！这是最大短板。

**可调优点（最关键！）**：
| 方向 | 方法 | 难度 | 预期提升 |
|------|------|------|----------|
| 时序建模 | MLP → LSTM/GRU | ⭐⭐ | **nDTW ↑↑** |
| 时序建模 | MLP → 1D-CNN | ⭐⭐ | nDTW ↑ |
| 注意力机制 | Temporal Attention | ⭐⭐⭐ | nDTW ↑↑ |
| 动作差分 | 用 Δ动作 而非绝对动作 | ⭐ | nDTW ↑ |

---

#### 步骤 C：条件融合（对应 20-3 第4章 4.3节）

**代码位置**：`evac/model/diffusion/conditioning.py`

**做了什么**：`concat([image_feature, action_feature]) → [1038] → Cross Attention 注入 U-Net`

**可调优点**：自适应融合（门控机制）| 逐层渐进融合 | 双向融合注意力

---

#### 步骤 D：DDIM 循环去噪（对应 20-3 第4章 4.1/4.2节）⭐最耗时

**代码位置**：`evac/model/diffusion/ddim_sampler.py`

**做了什么**：
```python
z_t = torch.randn([B, 4, 32, 32])  # 初始化
for t in reversed(timesteps):
    cond = fuse_condition(z_t, image_feature, action_feature)  # ①条件融合
    noise_pred = unet(z_t, t, cond)  # ②U-Net预测噪声 (~60%时间)
    z_t = ddim_step(noise_pred, z_t, t)  # ③DDIM去噪
z_0 = z_t
```

**DDIM步骤时间**：条件融合~10% | U-Net前向~60% | DDIM更新~30%

**ddim_steps 参数**：
| 值 | 速度 | PSNR | 适用 |
|----|------|------|------|
| 15 | 快 | 一般 | 开发调试 |
| 20 | 中 | 较好 | 快速验证 |
| **27** | 慢 | **最好** | **官方提交** |

---

#### 步骤 E：VAE 解码（对应 20-3 第3章 3.4节）

**代码位置**：`evac/model/decoder/vae.py`

**做了什么**：`z_0 [4,32,32] → VAE Decoder → frame [3,512,512]`

**可调优点**：更高分辨率（VAE→GAN）| 时序VAE（视频平滑）| 超分辨率后处理

---

### 7.3 各部分时间成本分析

```
单次预测 ≈ 27秒

CLIP编码  ██░░░░░░░░░░░░  ~1秒 (5%)
MLP编码   █░░░░░░░░░░░░  ~0.5秒 (2%)
DDIM循环  ████████████████ ~18秒 (70%)  ← 主要瓶颈
VAE解码   ████░░░░░░░░░░░  ~2秒 (8%)
I/O保存   ██████████░░░░░░  ~5秒 (20%)
```

**优化策略**：提速→优化DDIM | 提质量→优化动作编码器+CLIP

---

### 7.4 调优方向完整指南（按指标分类）

| 指标 | 含义 | 薄弱环节 | 优先优化方向 |
|------|------|----------|--------------|
| **PSNR** | 像素级图像相似度 | CLIP/VAE/步数 | CLIP升级 > ddim_steps > VAE |
| **Scene Consistency** | 空间一致性 | U-Net/时间注意力 | 时间注意力 > U-Net跳跃连接 |
| **nDTW** | 动作轨迹准确度 | **动作编码器** ← 最大短板 | **MLP → 时序模型** ← 最关键！ |

**快速提分（1天）**：ddim_steps=35（+0.2 PSNR）| n_pred=3（+0.5 nDTW）

**中等优化（1周）**：MLP → LSTM（nDTW +2~5）

**深度优化（2-4周）**：CLIP升级（PSNR+2~3）| Temporal Attention（nDTW+3~5）| U-Net改进（Scene+1~2）


### 7.5 常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| nDTW 很低（<0.8） | 动作编码器太弱 | 优先优化 MLP → LSTM |
| PSNR 很低（<20） | CLIP 或 ddim_steps 不够 | 换更大 CLIP 或加步数 |
| Scene Consistency 低 | 时间注意力不够 | 加入时序建模 |
| 推理太慢（>40秒） | ddim_steps 太多或 I/O 瓶颈 | 减少步数或批量推理 |
| 显存不足 | 批量太大 | 减小 batch_size |

---

### 7.6 调优自检清单

优化前先问自己：

- [ ] 我的 **nDTW** 是多少？低于 0.85 先优化动作编码器
- [ ] 我的 **PSNR** 是多少？低于 21 先优化 CLIP 或步数
- [ ] 我的 **Scene Consistency** 是多少？低于 0.92 先优化时间注意力
- [ ] 我的推理时间是多久？超过 30 秒先优化 I/O

**优先顺序建议**：
```
nDTW低  → MLP→LSTM（最关键！）
PSNR低  → CLIP升级 + ddim_steps=27
Scene低  → 时序注意力
速度慢  → 减少ddim_steps或批量推理
```

