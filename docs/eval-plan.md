# 评估计划：MMAU-Pro 子集 + CMDAR（精简版）

> 目标：用最小的评测成本，看清「Ear + 文本 LM」在音频理解上的水位，以及它和 Gemini 3.x 的差距。
>
> 边界：**不做 Live Translation / 实时 / 空间声学 / 多音频**，所以只取**离线、单文件、非空间、单选 MCQ** 的子集。

## 1. 为什么用 MMAU-Pro，而不是原始 MMAU

原始 MMAU 已经偏旧：Gemini 2.5 Pro 在 v05.15.25 上约 69.4%，人类 82.2，区分度下降；且题目平均只有 10 秒。**MMAU-Pro** 更接近现在的前沿：

- 5,305 条、49 项技能、11 类；平均 123.8 秒，覆盖短/中/长/超长。
- 人类 77.9；Gemini 3.1 Pro 72.2、3.7 Flash 70.4、3.5 Flash 68.5；Qwen3-Omni 62.9；Caption+GPT-4o 只有 35.3。
- 关键：**Google 自己的 Gemini 2.5/3 技术报告并不报 MMAU / AudioBench / AIR-Bench**；官方只报 FLEURS WER、CoVoST2 BLEU。所以所有 Gemini 的 MMAU 分数都是第三方复跑，不能当作官方能力证明。我们的评估也只是「同一子集上的参照」，不是给 Gemini 打分。

MMAU-Pro 官方包 47.5GB，太重。优先用社区整理好的 **short / close-ended / single-audio 子集 1,522 条（约 910MB）**，从中分层抽样；如果带宽允许，再用官方包核对 20 条。该子集是**非官方整理**，需在报告里注明。

## 2. 子集设计（约 190 条）

| 集合 | 条数 | 采样 | 评分 |
|---|---:|---|---|
| MMAU-Pro（short/single/close） | 100 | Sound 35 / Music 35 / Speech 30；其中至少 10 条 speech+sound / speech+music 混合；排除 spatial、multi-audio、voice-chat、open-ended | 严格 exact match + 官方 lenient match 双报 |
| CMDAR-main | 80 | 中文单文件单选 MCQ；覆盖 5 类推理（社会关系/事件/场景/异常/时序） | 严格 exact match |
| 内部剪辑集 | 10 | 自选真实视频：卡点、找笑声、SDH、配音 QA | 人工/规则检查 |

- 固定 seed（20261111），保存 item id，保证可复现。
- MMAU-Pro 若只能拿到官方 47.5GB 包：先抽 100 条所需音频，不保留全量。
- 不取：MMAU-Pro 的 spatial / multi-audio / voice-chat / open-ended；CMDAR 的 multi-audio / open-ended。
- 不取：任何 Live Translation、实时、直播数据。

## 3. 三条对照线

| 线 | 输入 | 目的 |
|---|---|---|
| A. 无音频 | question + choices | 测语言先验/猜题下限（4 选 1 ≈ 25%） |
| B. Ear + 文本 LM | `hearing.md` L1 + question + choices | 测 Ear 的实际增益 |
| C. Gemini 公开分数 | 不实际调用 | 水位参照：MMAU-Pro 72.2 / 70.4 / 68.5 |

可选 D：oracle transcript（若数据有转写）→ 区分「感知错」和「推理错」。

**不用 Gemini 做 judge**：MCQ 直接 exact match；open-ended 不进主评分。Gemini 只作为公开分数参照，不跑 API、不打标。

## 4. 指标

- 总体 accuracy + 分 domain（sound/music/speech）+ 混合题单列。
- 相对无音频 baseline 的提升；目标 ≥ +15pt。
- 与 Gemini 公开分数的差距（只报告，不设硬指标）。
- 两种匹配口径都报：**严格 exact match** 与 MMAU 官方 lenient token-subset；避免「聊天式回答」被误判。
- 每题延迟/成本；Ear 缓存命中率。
- 中间层：
  - ASR：FLEURS zh/ja/en 各 50 条，CER/WER。
  - 事件：ESC-50 或 AudioSet 子集，frame-level / clip-level F1（BEATs Strong 单独）。
  - 节拍：GTZAN/SMC 子集，beat F1（Beat This! 单独）。
- 失败分类：感知错 / 定位错 / 推理错 / 格式错。

## 5. 数据与许可

| 数据集 | 许可/访问 | 用法 |
|---|---|---|
| MMAU-Pro | CC-BY-NC 4.0；官方 `gamma-lab-umd/MMAU-Pro`（47.5GB）；社区 short 子集 910MB（非官方） | 内部评估；不提交音频 |
| CMDAR | **MIT**；GitHub `luckyerr/CMDAR` + HF `LLLLuckyer/CMDAR`，WAV 随仓库 | 内部评估；电影片段版权仍归原方 |
| FLEURS | CC-BY-4.0 | ASR 子集 |
| ESC-50 | CC-BY-NC 4.0 | 事件子集 |

- 所有音频放 `eval/data/`，gitignore；只提交 `item_id + answer + prediction`。
- 国内下载用 `HF_ENDPOINT=https://hf-mirror.com` 或代理。

## 6. Harness 设计

```bash
# 1) 准备子集（只下载选中条目）
python eval/prepare.py --bench mmau_pro_short --limit 100 --seed 20261111
python eval/prepare.py --bench cmdar --limit 80 --seed 20261111

# 2) 生成 Ear 输出（断点续跑）
python eval/run_ear.py --items eval/data/items.jsonl --out eval/cache

# 3) 三条线
python eval/run_bench.py --items eval/data/items.jsonl --line no_audio
python eval/run_bench.py --items eval/data/items.jsonl --line ear
python eval/report.py --results eval/results/*.jsonl
```

适配器接口：

```python
# eval/benchmarks/base.py
Item = {
  "id": str, "bench": str, "audio": Path,
  "question": str, "choices": list[str], "answer": str,  # "A".."D"
  "domain": str, "task_type": str, "mix": str | None,
}
```

`run_bench.py`：
- 对每条 item 调 `agent-ear listen`（缓存 `sha256(audio)`）。
- 读 `hearing.md` L1；拼 prompt：`[hearing note] + question + choices + "只输出字母"`。
- 文本 LLM 走 OpenAI-compatible 接口：`EVAL_LLM_BASE_URL` / `EVAL_LLM_MODEL` / `EVAL_LLM_API_KEY`。
- 解析首字母；非法输出记为 `format_error`，单独报告，不混进 accuracy。

## 7. 预期与解读

- Speech 类应明显高于无音频；Music/Sound 取决于 BEATs Strong / AudioSet Strong 标签覆盖。
- 参考量级：Caption+GPT-4o 在 MMAU-Pro 只有 35.3%；我们的「Ear 文本化 + 文本 LM」如果落在 35–50%，说明融合层有价值但音乐/细粒度声音仍是瓶颈；如果低于 30%，先修 digest/标签。
- 如果 Ear+文本 LM 只比无音频高几个点：先修 digest/关系描述，再加模型。
- 如果 Speech 高、Sound 低：BEATs/AudioSet Strong 事件层是瓶颈，考虑换 checkpoint 或补类别。
- 如果 CMDAR 明显低于 MMAU-Pro：检查中文 ASR（Qwen language_hints）和中文标签映射。

## 8. 不评什么

- Live Translation / 实时通话 / 实时理解 / 直播。
- 空间声学 / 空间定位 / 多轨空间。
- 多音频（multi-audio）、voice-chat、open-ended（MVP）。
- 完整音乐总谱 / 声纹身份 / 情绪诊断。
