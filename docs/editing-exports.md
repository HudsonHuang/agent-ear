# 剪辑/DAW 输出：SRT、EDL、Highlights、Mixcheck、Compare

agent-ear 的输出不止 `audio-score.json`。这一层把“时间轴”变成剪辑/DAW 能直接用的结果。

## 1. SRT / SDH

```bash
agent-ear export .ear/my-video --format srt
# -> .ear/my-video/captions.srt
```

- 词级/分段字幕来自 `speech.segments`；
- 默认带 SDH 非语音提示（`[笑声]`、`[掌声]` 等）；
- `--speaker` 加说话人前缀；
- `--no-sdh` 关闭事件提示；
- `--out captions.zh.srt` 指定输出。

## 2. EDL（CMX3600）

```bash
agent-ear export .ear/my-video --format edl --labels Laughter,Applause
# -> .ear/my-video/timeline.edl
```

- 每个事件一条 clip，源时间码来自 score，记录时间码顺序累加；
- `--fps` 不传时用 `source.fps`，再退回 30；
- `--pad-before/--pad-after` 加余量；
- 适合导入 Premiere / Resolve / Final Cut（CMX3600 兼容）。

## 3. Highlights

```bash
agent-ear highlights .ear/my-video --top 5 --by Laughter --format json
agent-ear highlights .ear/my-video --top 5 --by Laughter --format edl
```

- 按 `salience + conf` 排序，合并重叠候选；
- 默认前后各留 300/500ms；
- 输出 `start/end/label/score/source_event`；
- 可直接转 EDL 做高光粗剪。

## 4. Mixcheck / Compare（DAW 闭环）

```bash
agent-ear mixcheck render.wav --json
agent-ear compare before.wav after.wav --json
```

`mixcheck` 给：

- LUFS / true peak / LRA；
- peak / RMS / crest；
- clipping 样本数；
- 低频/中频/中高频/高频占比；
- warnings。

`compare` 给两份 render 的 delta，适合：

```text
生成/编辑 → render → mixcheck/compare → agent 调整 → render → ...
```

不调用 Qwen，本地跑；用于 DAW、混音、AI 音频生成后的自检。

## 5. 边界

- SRT 的精度取决于 score：basic 0.5–2s，precise 词级；
- EDL 的帧率按 `source.fps`；没有视频 fps 时默认 30；
- Highlights 是候选，不是自动剪辑决策；最终要人/agent 复核；
- `compare` 是测量，不判断“好不好听”。
