# 讯飞 QbE-KWS 关键词检索比赛 — 完整项目记录

> **比赛：** 讯飞 2026 QbE-KWS（Query by Example — Keyword Spotting）  
> **目标：** 给定 query.wav + enroll_txt，判断 query 是否包含 enroll 关键词（二分类 AUC）  
> **线上最高：** 0.86647 (submission_ctc_noise.csv)  
> **核心路线：** torchaudio Wav2Vec2 LV60K 字符 CTC 微调 + MUSAN 噪声增强 + 12 层加深微调

---

## 1. 关键发现

### 1.1 `-` token 陷阱（P0 突破）

torchaudio 2.6.0 的 Wav2Vec2 LV60K 标签集中，`-`（连字符）是 idx=0，而实际 blank token `|` 是 idx=1。

**不修复：** CTC loss 始终把 `-` 当 blank，AUC ≈ 0.51（接近随机）  
**修复方法：** 用 `logsumexp` 把 `-` 的概率合并到 `|`，将 `-` 位置设为 `-inf`

```python
blank_lp = torch.logsumexp(torch.stack([logp[:, DASH], logp[:, BLANK]], dim=1), dim=1)
logp[:, BLANK] = blank_lp
logp[:, DASH] = float("-inf")
```

修复后零样本 AUC 0.7698 → 0.770。

### 1.2 unseen = 完全未见词（731 词 0% 重叠）

通过词表交集分析确认：unseen 集 731 个词 **没有任何一个** 出现在训练集 8335 词中。这意味着 unseen 是对"未见词"泛化能力的考验，而非说话人泛化。

这对路线选择有决定性影响：
- CTC 字符分解理论上能泛化，但 26 字母组合空间仍大
- DTW 帧模板匹配在 unseen 上完全失效（AUC=0.5，跨说话人帧特征不匹配）

---

## 2. 完整实验阶段

| 阶段 | 模型 | 线上 AUC | 增量 | 文件 |
|------|------|----------|------|------|
| P0 | 零样本 + 修复 `-` | 0.770 | — | submission_ctc_p0.csv |
| P1 | 4 层 CTC 干净微调 (epoch_3) | **0.85785** | +0.088 | submission_ctc_ft.csv |
| P2 | + MUSAN 噪声增强 (epoch_6) | **0.86647** | +0.008 | submission_ctc_noise.csv |
| P3 | 12 层加深微调 (epoch_7) | 待提交 | +0.010~0.015 预期 | — |
| 融合 | P3-e7 双 pad (0.0+0.5) | 待提交 | +0.001~0.003 预期 | submission_dual_pad.csv |
| 融合 | + char n-gram LM 重排 | 待提交 | 待测 | submission_lm_*.csv |

### 训练详情

**P1（4 层 CTC 干净微调）：**
- 脚本：`finetune_ctc_merge.py`
- freeze_layers=20（训后 4 层 + CTC head + 辅助头）
- batch=8, grad_accum=2, lr=5e-5, pad=0.5s
- loss: 5.24 → 3.80 → 3.55
- epoch_3 最优，AUC seen=0.8612, unseen=0.8543, mean=0.8578

**P2（MUSAN 噪声增强）：**
- 脚本：`finetune_ctc_noise.py`
- MUSAN noise_prob=0.7, SNR 5-15dB，843 噪声文件预加载到内存
- 从 P1 epoch_3 热启动（含 optimizer state）
- loss: 6.67 → 5.02 → 4.38 → 3.41
- epoch_6 最优，AUC seen=0.8715, unseen=0.8550, mean=0.8633

**P3（12 层加深微调）：**
- 脚本：`finetune_ctc_deep12.py`
- freeze_layers=12（训后 12 层），可训练 159.6M / 315.5M (50.6%)
- 从 P2 epoch_6 热启动（optimizer state 部分恢复 71/199）
- epoch_7 最优，AUC seen=0.8723, unseen=0.8590, mean=0.8657

---

## 3. 核心技术细节

### 模型架构

```
Wav2Vec2 LV60K (24 层 Transformer)
  ├── feature_extractor (frozen)     — 7 层 CNN 提取声学特征
  ├── encoder.transformer.layers     — 24 层 Transformer
  │   ├── layer 0-11  (frozen)        — 通用声学表示
  │   └── layer 12-23 (trainable)     — 任务特化微调
  │       ├── feature_projection (frozen)
  │       └── transformer layers 12-23
  ├── aux (trainable)                — 辅助量化头（Wav2Vec2 自监督）
  └── CTC linear head                — 映射到 32 个字符标签
```

### 热启动 + optimizer state 迁移

从 4 层→12 层扩展时，optimizer state 的 param_groups 大小不匹配：
- 旧：71 参数（4 层微调）
- 新：199 参数（12 层微调）

**解决方案：** 手动位置映射，71 个旧参数恢复 Adam momentum，128 个新参数零初始化。

### 字符 n-gram LM 重排

对未见词：CTC 裸分数 noise 大 → 用字符 3-gram LM 校正"该词是否像英文"，提升信噪比。

```python
# LM 权重 α 扫描 0.005~0.05（7 档）
final_score = (1-α) × CTC_posterior + α × avg_char_3gram_prob(word)
```

---

## 4. 死胡同记录

| 尝试 | 结果 | 教训 |
|------|------|------|
| DTW 帧模板匹配 | unseen AUC=0.5 | 跨说话人帧特征不匹配，放弃 |
| 音素模型 (wav2vec2 phone) | AUC=0.67 | torchaudio 版本无音素输出，路不通 |
| 热启动忘恢复 optimizer state | loss 反弹 4.38→4.67 | Adam momentum 丢失导致重新找方向 |
| HF 格式 ctc_v2 | AUC=0.74 | 不如 torchaudio 原生 pipeline |

---

## 5. 容器环境

- **IP/端口：** 183.147.142.40:30820（密码见 memory）
- **GPU：** RTX 4090 24GB
- **Python：** 3.10（venv `/root/gpufree-data/envs/torch/`）
- **Torch：** 2.6.0+cu124
- **代码路径：** `/root/gpufree-data/kws/`
- **数据大小：** train 100K wav, eval 100K wav, dev 10K wav

---

## 6. 后续路线（基于 unseen 瓶颈诊断）

unseen = 未见词（0% 重叠于训练集），CTC 的字符泛化天花板在 ~0.859。
突破 unseen 的真正方向：

1. **字符 n-gram LM 重排**（✔ 已跑多档 α，待提交）— 最低成本
2. **CTC + 音素 G2P fallback**（音素集 ~40 个，比 26 字母组合空间小）— 中成本
3. **CTC + 孪生 0.84 融合**（两路错误模式不同，互补）— 中成本
4. **WavLM 中层特征 + 字符 CTC**（更强说话人不变性）— 高成本，ROI 不确定

**放弃 DTW 路线**（unseen=0.5，根因是跨说话人，不是未见词）。

---

## 7. 文件索引

| 文件 | 大小 | SHA-256 |
|------|------|---------|
| submission_ctc_ft.csv | 3.7M | 75547e0a... |
| submission_ctc_noise.csv | 3.7M | ccfd9ec5... |
| submission_dual_pad.csv | 3.7M | f512d942... |
| checkpoints/ctc_noise/epoch_7.pt | 2.4G | — |
| finetune_ctc_deep12.py | — | 核心训练脚本 |
| dual_pad_fusion.py | — | 双 pad 融合脚本 |

> 所有文件位于容器 `/root/gpufree-data/kws/`，容器关闭后数据持久化在 PVC 上。
