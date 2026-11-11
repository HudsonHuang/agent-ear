# Eval

第一轮水位评估：**MMAU-Pro short/single/close 100 条 + CMDAR-main 80 条**。

## 数据

- `eval/data/mmau_items.jsonl`：MMAU-Pro 100（30 sound / 30 music / 30 speech / 10 mixed），已排除 spatial / multi-audio / open-ended。
- `eval/data/cmdar_items.jsonl`：CMDAR 80（中文，9 类推理均衡）。
- 音频在 `eval/data/`，已 gitignore；不提交。

## 跑

```bash
# no-audio baseline
python eval/run_eval.py --line no_audio --workers 4

# Ear + 文本 LLM
python eval/run_eval.py --line ear --workers 4

# 汇总
python eval/report.py --results eval/results/no_audio.jsonl eval/results/ear.jsonl
```

- 文本 LLM 默认 `qwen-plus`；可用 `EVAL_LLM_BASE_URL` / `EVAL_LLM_MODEL` / `EVAL_LLM_API_KEY` 覆盖，未设置时读 `~/.bailian/config.json`。
- Ear 输出缓存到 `eval/cache/<bench>/<id>/`，重复跑不重新分析。
- 每行结果：`id / bench / domain / answer / pred / correct / format_error / ear_s / note_chars / error`。

## 口径

- 4 选 1，严格首字母 exact match；非法输出记 `format_error`，不混入 accuracy 的分母解释。
- MMAU-Pro 用英文标签（`EAR_LABEL_LANG=en`）；CMDAR 用中文标签。
- 不做 Gemini judge；Gemini 公开分数只作参照。

## 结果

见 [第一轮水位结果](../docs/eval-results-2026-11-11.md) 与 `eval/results/`。
