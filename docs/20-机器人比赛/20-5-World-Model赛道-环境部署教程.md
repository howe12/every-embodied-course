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
