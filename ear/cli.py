"""Ear CLI: probe / listen / digest / doctor / schema."""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__, aed_psed, aed_registry, beats, config, context, doctor as doctor_mod, editing, events_panns, fuse, install, media, mix, omni, probe, render, requests as request_plan, routing, setup as setup_mod, text_llm
from . import score as score_mod
from .asr_qwen import QwenAsrError, transcribe as qwen_transcribe

_HERE = Path(__file__).resolve().parent
SCHEMA_PATH = _HERE / "_data" / "schema" / "audio-score.schema.json"
if not SCHEMA_PATH.is_file():
    SCHEMA_PATH = _HERE.parent / "schema" / "audio-score.schema.json"
NON_SPEECH_VOCAL = {"Laughter", "Crying, sobbing", "Sigh", "Cough", "Sneeze", "Breathing"}


def load_env_file(path: str | None) -> None:
    if not path:
        return
    p = Path(path).expanduser()
    if not p.is_file():
        raise SystemExit(f"env file not found: {p}")
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        k, sep, v = line.partition("=")
        if not sep:
            continue
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v)


def _out_dir(args) -> Path:
    if args.out:
        return Path(args.out).expanduser().resolve()
    h = media.sha256_file(Path(args.input))[:8]
    stem = Path(args.input).stem[:40]
    return (Path.cwd() / ".ear" / f"{stem}-{h}").resolve()


def _turns(segments: list[dict[str, Any]], gap_ms: int = 600) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for s in segments:
        if turns and turns[-1]["speaker"] == s["speaker"] and \
                s["start_ms"] - turns[-1]["end_ms"] <= gap_ms:
            turns[-1]["end_ms"] = s["end_ms"]
            turns[-1]["texts"].append(s.get("text") or "")
        else:
            turns.append({"speaker": s["speaker"], "start_ms": s["start_ms"],
                          "end_ms": s["end_ms"], "texts": [s.get("text") or ""]})
    for t in turns:
        t["text"] = " ".join(x for x in t["texts"] if x).strip()
        t.pop("texts", None)
    return turns


def _trim(src: Path, dst: Path, seconds: float) -> Path:
    return media.cut_audio(src, dst, 0.0, seconds, sr=16000)


def cmd_listen_local(args) -> int:
    t0 = time.time()
    src_in = Path(args.input).expanduser().resolve()
    if not src_in.is_file():
        raise SystemExit(f"input not found: {src_in}")
    out = _out_dir(args)
    out.mkdir(parents=True, exist_ok=True)
    work = out / "work"
    work.mkdir(exist_ok=True)
    score_path = out / "audio-score.json"
    if score_path.is_file() and not args.force:
        print(f"cached: {score_path}")
        print(json.loads(score_path.read_text(encoding="utf-8"))["views"]["one_line"])
        return 0

    src = src_in
    trimmed_ms = None
    if args.max_seconds:
        trimmed = _trim(src_in, work / "input_trim.wav", args.max_seconds)
        src = trimmed
        trimmed_ms = int(args.max_seconds * 1000)

    try:
        aed_id = aed_registry.resolve(args.aed)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(f"[ear] {src_in.name} → {out} (aed={aed_id})", flush=True)
    pr = probe.probe_audio(src, work)
    duration_ms = pr["duration_ms"]
    warnings: list[str] = list(pr.get("warnings") or [])
    if args.mode == "privacy":
        if not args.no_asr:
            args.no_asr = True
            warnings.append("privacy mode: ASR disabled (MOSS backend not implemented yet)")
    elif args.mode == "music":
        if not args.no_beats:
            args.force_beats = True
        warnings.append("music mode: MVP uses default backends + beat grid; sections/MIDI not implemented")
    capabilities: dict[str, Any] = {"fusion": "rules-v1", **pr.get("capabilities", {})}
    info = pr["media"]

    # 32k wav for PANNs / Beat This!
    wav32 = work / "audio_32k.wav"
    if not wav32.is_file():
        media.extract_audio(src, wav32, sr=32000)
    wav16 = work / "audio_16k.wav"
    if not wav16.is_file():
        media.extract_audio(src, wav16, sr=16000)

    # Event layer: PANNs. Cheap, always on unless disabled.
    ev: dict[str, Any] = {"events": [], "music_ratio": 0.0, "speech_ratio": 0.0,
                          "event_ratio": 0.0, "top_labels": []}
    if not args.no_events:
        if aed_id == "psed_beats":
            print("[ear] PretrainedSED BEATs Strong (40ms) ...", flush=True)
            try:
                ev = aed_psed.analyze(wav16, device=args.device)
                capabilities["events"] = "pretrainedsed-beats-strong"
            except Exception as exc:
                warnings.append(f"PretrainedSED BEATs failed: {type(exc).__name__}: {str(exc)[:240]}")
                capabilities["events"] = None
        if aed_id == "panns" or (capabilities["events"] is None and aed_id != "psed_beats"):
            print("[ear] PANNs CNN14 ...", flush=True)
            try:
                tagger = events_panns.PannsTagger(device=args.device)
                ev = tagger.analyze(wav32, duration_ms)
                capabilities["events"] = "panns-cnn14-clip-window"
            except Exception as exc:
                warnings.append(f"PANNs failed: {type(exc).__name__}: {str(exc)[:240]}")
                capabilities["events"] = None
        if aed_id == "psed_beats" and capabilities["events"] is None:
            warnings.append("BEATs unavailable; events disabled (use --aed panns to fallback)")
    else:
        capabilities["events"] = None

    speech_ratio = max(float(pr["speech"].get("ratio") or 0.0),
                       float(ev.get("speech_ratio") or 0.0))
    music_ratio = float(ev.get("music_ratio") or 0.0)

    # Speech layer: Qwen filetrans, gated by speech presence.
    speech: dict[str, Any] = {"provider": None, "segments": [], "usage": {}}
    if not args.no_asr and pr["has_audio"] and speech_ratio >= args.min_speech_ratio:
        print(f"[ear] Qwen ASR (speech ratio {speech_ratio:.2f}) ...", flush=True)
        try:
            speech = qwen_transcribe(
                wav16, language_hints=args.language, speakers=args.speakers,
                diarization=not args.no_diarization, verbose=args.verbose,
            )
            capabilities["speech"] = speech["provider"]
        except Exception as exc:
            warnings.append(
                f"Qwen ASR failed: {type(exc).__name__}: {str(exc)[:200]} "
                "(check DASHSCOPE_API_KEY/base_url, or use --no-asr)")
            capabilities["speech"] = None
    else:
        if args.no_asr:
            warnings.append("ASR disabled by --no-asr")
        elif pr["has_audio"]:
            warnings.append(f"ASR skipped: speech ratio {speech_ratio:.2f} < {args.min_speech_ratio}")
        capabilities["speech"] = None

    # Do not pretend the file is silent when ASR is disabled/failed. Keep
    # VAD spans as untranscribed placeholders, clearly marked.
    if not speech.get("segments") and pr["has_audio"] \
            and speech_ratio >= args.min_speech_ratio:
        vad_spans = (pr.get("speech") or {}).get("segments") or []
        if vad_spans:
            speech = {
                "provider": "vad-only",
                "segments": [
                    {
                        "id": f"sp_{i:04d}",
                        "start_ms": int(s["start_ms"]),
                        "end_ms": int(s["end_ms"]),
                        "speaker": "S?",
                        "text": "",
                        "lang": (args.language or [""])[0],
                        "conf": None,
                        "words": [],
                        "source": "vad",
                    }
                    for i, s in enumerate(vad_spans, 1)
                ],
                "usage": {},
            }
            capabilities["speech"] = "vad-only"
            warnings.append("ASR unavailable/disabled; speech intervals come from VAD, no transcript")

    # Music layer: beat tracking gated by music presence.
    music_track: dict[str, Any] | None = None
    if not args.no_beats and (music_ratio >= args.min_music_ratio or args.force_beats):
        print(f"[ear] Beat This! (music ratio {music_ratio:.2f}) ...", flush=True)
        try:
            bt = beats.track(wav32, device=args.device, model=args.beat_model)
            music_track = {
                "id": "mu_0001",
                "start_ms": 0,
                "end_ms": duration_ms,
                "bpm": bt.get("bpm"),
                "beats_ms": bt.get("beats_ms") or [],
                "downbeats_ms": bt.get("downbeats_ms") or [],
                "beat_positions": bt.get("beat_positions") or [],
                "sections": [],
                "genre": None,
                "mood": None,
                "instruments": [],
                "vocals": None,
                "quality": bt.get("quality"),
                "provider": bt.get("provider"),
            }
            capabilities["music"] = bt.get("provider")
        except Exception as exc:
            warnings.append(f"Beat This! failed: {type(exc).__name__}: {str(exc)[:240]}")
            capabilities["music"] = None
            music_track = None
    else:
        capabilities["music"] = None
        if pr["has_audio"] and music_ratio < args.min_music_ratio:
            warnings.append(f"beat tracking skipped: music ratio {music_ratio:.2f} < {args.min_music_ratio}")

    segments = speech.get("segments") or []
    if segments and duration_ms < 90000:
        warnings.append("file <90s: speaker labels may collapse to one speaker; treat S0/S1 as anonymous")
    turns = _turns(segments)
    non_vocal = [e for e in (ev.get("events") or []) if e.get("label") in NON_SPEECH_VOCAL]

    timeline = fuse.merge_timeline(
        duration_ms=duration_ms, speech=segments, events=ev.get("events") or [],
        music=music_track,
    )
    if len(timeline) >= fuse.MAX_TIMELINE:
        warnings.append(f"timeline coarsened to {len(timeline)} entries")
    relations = fuse.build_relations(
        speech=segments, events=ev.get("events") or [], music=music_track)
    speakers = sorted({s.get("speaker") for s in segments
                       if s.get("speaker") and s.get("speaker") != "S?"})
    languages = sorted({s.get("lang") for s in segments if s.get("lang")})
    views = fuse.build_views(
        duration_ms=duration_ms, speech=segments, events=ev.get("events") or [],
        music=music_track, timeline=timeline, speakers=speakers)

    scene = "unknown"
    if speech_ratio >= 0.5:
        scene = "talk / vlog / interview"
    elif music_ratio >= 0.5 and speech_ratio < 0.2:
        scene = "music / performance"
    elif ev.get("events"):
        scene = "ambience / sfx"

    score: dict[str, Any] = {
        "schema": "ear.score/1",
        "source": {
            "path": str(src_in),
            "sha256": media.sha256_file(src_in),
            "duration_ms": duration_ms,
            "fps": (info.get("video") or {}).get("fps") if info.get("has_video") else None,
            "pts_offset_ms": 0,
            "trimmed_to_ms": trimmed_ms,
        },
        "capabilities": capabilities,
        "global": {
            "summary": views["one_line"],
            "duration_ms": duration_ms,
            "speech_ratio": round(speech_ratio, 4),
            "music_ratio": round(music_ratio, 4),
            "event_ratio": round(float(ev.get("event_ratio") or 0.0), 4),
            "speakers": len(speakers),
            "languages": languages,
            "scene": scene,
            "mood_curve": [],
            "mode": args.mode,
            "top_sounds": ev.get("top_labels") or [],
        },
        "speech": {"segments": segments, "turns": turns, "non_speech_vocal": non_vocal},
        "music": {"tracks": [music_track] if music_track else [], "lyrics": []},
        "events": ev.get("events") or [],
        "relations": relations,
        "timeline": timeline,
        "views": views,
        "warnings": warnings,
        "provenance": {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tool_version": __version__,
            "elapsed_s": round(time.time() - t0, 2),
            "params": {
                "mode": args.mode, "language": args.language, "speakers": args.speakers,
                "min_speech_ratio": args.min_speech_ratio, "min_music_ratio": args.min_music_ratio,
                "beat_model": args.beat_model, "max_seconds": args.max_seconds,
            },
            "probe": {"loudness": pr.get("loudness"), "silence_count": len(pr.get("silence") or [])},
        },
    }

    # Validate schema; never fail a listen on a schema warning.
    try:
        import jsonschema
        if SCHEMA_PATH.is_file():
            jsonschema.validate(score, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    except Exception as exc:
        warnings.append(f"schema validation: {type(exc).__name__}: {str(exc)[:240]}")

    score_path.write_text(json.dumps(score, ensure_ascii=False, indent=2), encoding="utf-8")
    with gzip.open(out / "audio-score.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(score, fh, ensure_ascii=False)
    (out / "hearing.md").write_text(render.render_hearing(score), encoding="utf-8")
    (out / "context.md").write_text(context.build_context(score), encoding="utf-8")
    (out / "digest.md").write_text(render.render_digest(score, level=1), encoding="utf-8")

    print("")
    print(views["one_line"])
    print(f"speech={len(segments)} events={len(score['events'])} "
          f"beats={len((music_track or {}).get('beats_ms') or [])} "
          f"timeline={len(timeline)} warnings={len(warnings)}")
    print(f"wrote {score_path}")
    print(f"wrote {out/'hearing.md'}")
    return 0


def _write_score(score: dict[str, Any], out: Path) -> int:
    warnings = score.setdefault("warnings", [])
    try:
        import jsonschema
        if SCHEMA_PATH.is_file():
            jsonschema.validate(score, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))
    except Exception as exc:
        warnings.append(f"schema validation: {type(exc).__name__}: {str(exc)[:200]}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "audio-score.json").write_text(
        json.dumps(score, ensure_ascii=False, indent=2), encoding="utf-8")
    with gzip.open(out / "audio-score.json.gz", "wt", encoding="utf-8") as fh:
        json.dump(score, fh, ensure_ascii=False)
    (out / "hearing.md").write_text(render.render_hearing(score), encoding="utf-8")
    (out / "context.md").write_text(context.build_context(score), encoding="utf-8")
    (out / "digest.md").write_text(render.render_digest(score, level=1), encoding="utf-8")
    print("")
    print(score["views"]["one_line"])
    print(f"speech={len(score['speech']['segments'])} events={len(score['events'])} "
          f"timeline={len(score['timeline'])} warnings={len(warnings)}")
    print(f"wrote {out/'audio-score.json'}")
    print(f"wrote {out/'hearing.md'}")
    return 0


def cmd_listen_omni(args) -> int:
    t0 = time.time()
    src_in = Path(args.input).expanduser().resolve()
    if not src_in.is_file():
        raise SystemExit(f"input not found: {src_in}")
    out = _out_dir(args)
    work = out / "work"
    work.mkdir(parents=True, exist_ok=True)
    score_path = out / "audio-score.json"
    if score_path.is_file() and not args.force:
        score = json.loads(score_path.read_text(encoding="utf-8"))
        print(f"cached: {score_path}")
        print(score["views"]["one_line"])
        return 0

    src = src_in
    trimmed_ms = None
    if args.max_seconds:
        src = _trim(src_in, work / "input_trim.wav", args.max_seconds)
        trimmed_ms = int(args.max_seconds * 1000)
    info = media.media_info(src_in)
    duration_ms = int(media.media_info(src)["duration_ms"])

    plan = request_plan.parse_request(getattr(args, "request", None))
    if plan and plan.intent == "privacy":
        print("[ear] request=privacy -> local only", flush=True)
        args.mode = "privacy"
        args.no_asr = True
        return cmd_listen_local(args)
    profile = "events" if plan and plan.intent == "events" else "full"
    targets = plan.labels if profile == "events" else None
    print(f"[ear] Omni analyze ({duration_ms/1000:.0f}s, profile={profile}"
          + (f", targets={targets}" if targets else "") + ") ...", flush=True)
    res = omni.analyze(src, thinking=args.omni_thinking, profile=profile, targets=targets)
    score = score_mod.from_omni(
        res, source_path=str(src_in), sha256=media.sha256_file(src_in),
        duration_ms=duration_ms, mode=args.mode, elapsed_s=time.time() - t0)
    score["source"]["fps"] = (info.get("video") or {}).get("fps") if info.get("has_video") else None
    score["source"]["trimmed_to_ms"] = trimmed_ms
    score["capabilities"]["mode"] = args.mode
    score["intent"] = {"requested": (plan.needs if plan else (args.need or "")),
                       "labels": (plan.labels if plan else []),
                       "request": (plan.raw if plan else ""),
                       "skipped": []}

    if args.mode in ("precise", "music"):
        if args.need:
            needs = routing.parse_needs(args.need, mode=args.mode)
        elif plan:
            needs = list(plan.needs)
        else:
            needs = routing.parse_needs(None, mode=args.mode)
        exec_plan = routing.plan("precise" if args.mode == "precise" else "music", needs, res)
        score["capabilities"]["mode"] = args.mode
        score["intent"] = {"requested": needs,
                           "labels": (plan.labels if plan else []),
                           "request": (plan.raw if plan else ""),
                           "skipped": [k for k, v in exec_plan.items() if k != "omni" and not v]}
        wav16 = work / "audio_16k.wav"
        if (exec_plan["asr"] or exec_plan["aed"]) and not wav16.is_file():
            media.extract_audio(src, wav16, sr=16000)
        if exec_plan["asr"]:
            print("[ear] Qwen ASR (precise) ...", flush=True)
            try:
                asr = qwen_transcribe(wav16, language_hints=args.language,
                                      speakers=args.speakers,
                                      diarization=not args.no_diarization,
                                      verbose=args.verbose)
                score_mod.apply_asr(score, asr)
            except Exception as exc:
                score["warnings"].append(
                    f"Qwen ASR failed: {type(exc).__name__}: {str(exc)[:200]}")
        if exec_plan["aed"]:
            print("[ear] BEATs refine ...", flush=True)
            try:
                local = aed_psed.analyze(wav16, device=args.device)
                n = score_mod.refine_events(score, local.get("events") or [])
                score["warnings"].append(f"refined {n} Omni events with 40ms AED")
                score["capabilities"]["aed"] = local.get("provider")
            except Exception as exc:
                score["warnings"].append(
                    f"BEATs refine failed: {type(exc).__name__}: {str(exc)[:200]}")
        if exec_plan["beat"]:
            print("[ear] Beat This! (precise) ...", flush=True)
            wav32 = work / "audio_32k.wav"
            if not wav32.is_file():
                media.extract_audio(src, wav32, sr=32000)
            try:
                bt = beats.track(wav32, device=args.device, model=args.beat_model)
                score_mod.apply_beats(score, bt, duration_ms)
            except Exception as exc:
                score["warnings"].append(
                    f"Beat This! failed: {type(exc).__name__}: {str(exc)[:200]}")
        score_mod.finalize(score)

    score["provenance"]["elapsed_s"] = round(time.time() - t0, 2)
    score["provenance"]["omni"] = {
        "usage": res.get("usage") or {}, "wall_s": res.get("wall_s"),
        "chunks": res.get("chunks"),
    }
    return _write_score(score, out)


def cmd_listen(args) -> int:
    if args.mode == "privacy":
        if not args.no_asr:
            args.no_asr = True
        return cmd_listen_local(args)
    return cmd_listen_omni(args)


def cmd_ask(args) -> int:
    src = Path(args.input).expanduser().resolve() if args.input else None
    choices = [x.strip() for x in (args.choices or "").split("|") if x.strip()] or None
    if args.score:
        sp = Path(args.score).expanduser()
        if sp.is_dir():
            sp = sp / "audio-score.json"
        sc = json.loads(sp.read_text(encoding="utf-8"))
        ctx = context.build_context(sc, max_chars=args.max_context_chars)
        res = text_llm.answer(ctx, args.question, choices, model=args.text_model)
        answer = res.get("letter") or res.get("content") or ""
        print(answer)
        if args.json:
            print(json.dumps({"answer": answer, "context_chars": len(ctx),
                              "model": res.get("model"), "usage": res.get("usage")},
                             ensure_ascii=False, indent=2))
        return 0
    if not src or not src.is_file():
        raise SystemExit("input not found (or pass --score)")
    print(f"[ear] Omni analyze+answer ({args.question[:60]}) ...", flush=True)
    t0 = time.time()
    res = omni.analyze(src, thinking=args.thinking, question=args.question, choices=choices)
    answer = res.get("answer") or res.get("summary") or "(no answer)"
    score_path = None
    if not args.no_save:
        out = Path(args.out).expanduser() if args.out else Path(".ear/ask") / media.sha256_file(src)[:12]
        info = media.media_info(src)
        sc = score_mod.from_omni(
            res, source_path=str(src), sha256=media.sha256_file(src),
            duration_ms=int(info["duration_ms"]), mode="basic",
            elapsed_s=time.time() - t0)
        sc["intent"] = {"requested": ["describe", "ask"], "skipped": []}
        sc["warnings"].extend(res.get("warnings") or [])
        _write_score(sc, out)
        score_path = str(out / "audio-score.json")
    if args.json:
        print(json.dumps({"answer": answer, "analysis": res, "score_path": score_path},
                         ensure_ascii=False, indent=2))
    else:
        print(answer)
        print(f"\n[model={res.get('provider')} wall={res.get('wall_s')}s "
              f"segments={len(res.get('segments') or [])} events={len(res.get('events') or [])} "
              f"score={score_path or '-'}]")
    if args.out and args.json:
        out = Path(args.out).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        (out / "ask.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0

def _labels(raw: str | None) -> list[str] | None:
    return [x.strip() for x in (raw or "").split(",") if x.strip()] or None


def cmd_export(args) -> int:
    score, sp = editing.load_score(args.score)
    out = Path(args.out).expanduser() if args.out else sp.parent / ("captions.srt" if args.format == "srt" else "timeline.edl")
    if args.format == "srt":
        text = editing.srt(score, sdh=not args.no_sdh, speaker=args.speaker)
    elif args.format == "edl":
        text = editing.edl(score, labels=_labels(args.labels), fps=args.fps,
                           pad_before=args.pad_before, pad_after=args.pad_after)
    else:
        raise SystemExit(f"unsupported export format: {args.format}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(out)
    return 0


def cmd_highlights(args) -> int:
    score, sp = editing.load_score(args.score)
    items = editing.highlights(score, top=args.top, by=_labels(args.by),
                               pad_before=args.pad_before, pad_after=args.pad_after,
                               min_gap=args.min_gap)
    if not items:
        raise SystemExit("no matching highlights")
    out = Path(args.out).expanduser() if args.out else sp.parent / f"highlights.{args.format}"
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "json":
        payload = {"source": score.get("source", {}), "highlights": items}
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    elif args.format == "md":
        out.write_text(editing.highlights_md(score, items), encoding="utf-8")
    elif args.format == "edl":
        pseudo = {"source": score.get("source", {}),
                  "events": [{"id": f"hl_{x['rank']}", "start_ms": x["start_ms"],
                              "end_ms": x["end_ms"], "label": x["label"],
                              "conf": x["score"]} for x in items]}
        out.write_text(editing.edl(pseudo, fps=args.fps, title="agent-ear highlights"), encoding="utf-8")
    print(out)
    for x in items:
        print(f"{x['rank']}. {x['start_ms']}–{x['end_ms']} {x['label']} ({x['score']})")
    return 0


def cmd_mixcheck(args) -> int:
    d = mix.analyze(Path(args.input).expanduser())
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(f"{d['path']}: {d['duration_s']}s  LUFS={d['lufs']}  TP={d['true_peak_db']}  "
              f"peak={d['peak_dbfs']}  crest={d['crest_db']}  clipping={d['clipping_samples']}")
        for k, v in d["bands_pct"].items():
            print(f"  {k}: {v['pct']}% ({v['db']} dB)")
        for w in d["warnings"]:
            print("  ! " + w)
    return 0


def cmd_compare(args) -> int:
    d = mix.compare(Path(args.a).expanduser(), Path(args.b).expanduser())
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print("delta B - A:")
        for k, v in d["delta_b_minus_a"].items():
            print(f"  {k}: {v:+}")
        for w in d["warnings"]:
            print("  ! " + w)
    return 0


def cmd_probe(args) -> int:
    src = Path(args.input).expanduser().resolve()
    if not src.is_file():
        raise SystemExit(f"input not found: {src}")
    out = Path(args.out).expanduser().resolve() if args.out else (Path.cwd() / ".ear" / "probe")
    data = probe.probe_audio(src, out)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_digest(args) -> int:
    p = Path(args.path).expanduser().resolve()
    if p.is_dir():
        p = p / "audio-score.json"
    score = json.loads(p.read_text(encoding="utf-8"))
    print(render.render_digest(score, level=args.level))
    return 0


def cmd_doctor(args) -> int:
    d = doctor_mod.collect(check_api=getattr(args, "check_api", False),
                           scope=getattr(args, "scope", "user"),
                           project_root=getattr(args, "project_root", None))
    if getattr(args, "fix", False):
        for row in d.get("skills") or []:
            if not row.get("installed"):
                try:
                    install.install_skill(install.target(row["target"]), force=False)
                    d["fix"] = d.get("fix", []) + [f"installed {row['target']}"]
                except Exception as exc:
                    d["fix"] = d.get("fix", []) + [f"{row['target']}: {exc}"]
    if getattr(args, "json", False):
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(doctor_mod.human(d))
    return 0


def cmd_config(args) -> int:
    action = args.action
    if action == "path":
        print(config.config_path())
        return 0
    if action == "show":
        q = config.get_qwen()
        print(json.dumps({"path": str(config.config_path()),
                          "key": config.mask(q.get("api_key") or ""),
                          "configured": bool(q.get("api_key")),
                          "source": q.get("source"),
                          "base_url": q.get("base_url"),
                          "omni_model": q.get("omni_model"),
                          "asr_model": q.get("asr_model")},
                         ensure_ascii=False, indent=2))
        return 0
    if action == "set-key":
        import getpass
        if getattr(args, "api_key_stdin", False):
            key = sys.stdin.readline().strip()
        else:
            key = getpass.getpass("Qwen API Key: ").strip()
        if not key:
            raise SystemExit("empty key")
        base = args.base_url or config.get_qwen().get("base_url") or config.DEFAULT_BASE
        if not args.skip_api_check:
            c = config.check_qwen(key, base)
            if not c.get("ok"):
                print(f"warning: key check failed ({c.get('status') or c.get('error')})",
                      file=sys.stderr)
                if not args.force:
                    raise SystemExit("not saved; use --force to save anyway")
        p = config.save_qwen(key, base)
        print(f"wrote {p}")
        return 0
    raise SystemExit(f"unknown config action: {action}")


def cmd_skill(args) -> int:
    action = args.action
    if action == "list":
        rows = install.list_skills(scope=args.scope, project_root=args.project_root)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0
    targets = install.parse_targets(args.target or "codex")
    for t in targets:
        if action == "install":
            r = install.install_skill(t, scope=args.scope, project_root=args.project_root,
                                      force=args.force, dry_run=args.dry_run)
        elif action == "uninstall":
            r = install.uninstall_skill(t, scope=args.scope, project_root=args.project_root,
                                        force=args.force, dry_run=args.dry_run)
        else:
            raise SystemExit(f"unknown skill action: {action}")
        print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


def cmd_uninstall(args) -> int:
    targets = install.parse_targets(args.target or "all")
    for t in targets:
        r = install.uninstall_skill(t, scope=args.scope, project_root=args.project_root,
                                    force=args.force, dry_run=args.dry_run)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    if args.purge:
        p = config.config_path()
        if p.is_file():
            p.unlink()
            print(f"removed {p}")
        print("models/cache are not removed automatically; delete ~/.cache/ear if desired")
    return 0


def cmd_setup(args) -> int:
    return setup_mod.run(args)

def cmd_schema(args) -> int:
    print(str(SCHEMA_PATH))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="agent-ear", description="Compile audio/video into a time-indexed audio score.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    lp = sub.add_parser("listen", help="analyze a file and write audio-score.json + hearing.md")
    lp.add_argument("input")
    lp.add_argument("--out")
    lp.add_argument("--mode", choices=["basic", "precise", "music", "privacy", "default"], default="basic")
    lp.add_argument("--language", action="append", help="language hint, e.g. --language ja")
    lp.add_argument("--speakers", type=int, default=None, help="speaker count for diarization")
    lp.add_argument("--no-asr", action="store_true")
    lp.add_argument("--no-events", action="store_true")
    lp.add_argument("--no-beats", action="store_true")
    lp.add_argument("--no-diarization", action="store_true")
    lp.add_argument("--force-beats", action="store_true")
    lp.add_argument("--beat-model", default="small0")
    lp.add_argument("--aed", default="auto", help="AED provider id (auto, psed_beats, panns)")
    lp.add_argument("--need", default=None, help="comma list: transcript,events,beat,music,none")
    lp.add_argument("--request", default=None, help="natural-language request, e.g. '把笑声都剪出来'")
    lp.add_argument("--omni-thinking", type=int, default=256)
    lp.add_argument("--min-speech-ratio", type=float, default=0.05)
    lp.add_argument("--min-music-ratio", type=float, default=0.15)
    lp.add_argument("--max-seconds", type=float, default=None)
    lp.add_argument("--device", default="cpu")
    lp.add_argument("--env-file")
    lp.add_argument("--force", action="store_true")
    lp.add_argument("--verbose", action="store_true")
    lp.set_defaults(func=cmd_listen)

    aq = sub.add_parser("ask", help="one Omni call: full analysis + answer; or --score -> text LM")
    aq.add_argument("input", nargs="?")
    aq.add_argument("question")
    aq.add_argument("--score", help="ask against a saved audio-score.json (no Omni call)")
    aq.add_argument("--text-model", default="qwen-plus")
    aq.add_argument("--max-context-chars", type=int, default=12000)
    aq.add_argument("--thinking", type=int, default=256)
    aq.add_argument("--choices", help="MCQ choices separated by |")
    aq.add_argument("--no-save", action="store_true", help="do not write audio-score/hearing.md")
    aq.add_argument("--json", action="store_true")
    aq.add_argument("--out", help="score directory (default: .ear/ask/<sha>)")
    aq.set_defaults(func=cmd_ask)

    pp = sub.add_parser("probe", help="cheap signal probe only")
    pp.add_argument("input")
    pp.add_argument("--out")
    pp.set_defaults(func=cmd_probe)

    dp = sub.add_parser("digest", help="print a compact digest from a score")
    dp.add_argument("path")
    dp.add_argument("--level", type=int, default=1)
    dp.set_defaults(func=cmd_digest)

    ex = sub.add_parser("export", help="export SRT/EDL from a saved score")
    ex.add_argument("score")
    ex.add_argument("--format", choices=["srt", "edl"], default="srt")
    ex.add_argument("--out")
    ex.add_argument("--no-sdh", action="store_true")
    ex.add_argument("--speaker", action="store_true")
    ex.add_argument("--labels", help="EDL only: comma labels, e.g. Laughter,Applause")
    ex.add_argument("--fps", type=float)
    ex.add_argument("--pad-before", type=int, default=0)
    ex.add_argument("--pad-after", type=int, default=0)
    ex.set_defaults(func=cmd_export)

    hl = sub.add_parser("highlights", help="rank events into highlight clips")
    hl.add_argument("score")
    hl.add_argument("--top", type=int, default=5)
    hl.add_argument("--by", help="comma labels, e.g. Laughter,Applause")
    hl.add_argument("--pad-before", type=int, default=300)
    hl.add_argument("--pad-after", type=int, default=500)
    hl.add_argument("--min-gap", type=int, default=400)
    hl.add_argument("--format", choices=["json", "md", "edl"], default="json")
    hl.add_argument("--out")
    hl.add_argument("--fps", type=float)
    hl.set_defaults(func=cmd_highlights)

    mx = sub.add_parser("mixcheck", help="local LUFS/true-peak/clipping/band report")
    mx.add_argument("input")
    mx.add_argument("--json", action="store_true")
    mx.set_defaults(func=cmd_mixcheck)

    cmp = sub.add_parser("compare", help="compare two audio renders for DAW feedback")
    cmp.add_argument("a")
    cmp.add_argument("b")
    cmp.add_argument("--json", action="store_true")
    cmp.set_defaults(func=cmd_compare)

    doc = sub.add_parser("doctor", help="check dependencies/config/skills")
    doc.add_argument("--env-file")
    doc.add_argument("--json", action="store_true")
    doc.add_argument("--check-api", action="store_true")
    doc.add_argument("--fix", action="store_true")
    doc.add_argument("--scope", choices=["user", "project"], default="user")
    doc.add_argument("--project-root", type=Path)
    doc.set_defaults(func=cmd_doctor)

    st = sub.add_parser("setup", help="interactive first-run setup (key + agent skills)")
    st.add_argument("--target", default=None, help="codex,dsh,claude,all")
    st.add_argument("--scope", choices=["user", "project"], default="user")
    st.add_argument("--project-root", type=Path)
    st.add_argument("--api-key-stdin", action="store_true")
    st.add_argument("--base-url")
    st.add_argument("--skip-key", action="store_true")
    st.add_argument("--skip-api-check", action="store_true")
    st.add_argument("--non-interactive", action="store_true")
    st.add_argument("--with-local", action="store_true")
    st.add_argument("--download-models", action="store_true")
    st.add_argument("--install-ffmpeg", action="store_true", help="Windows: download a local static ffmpeg")
    st.add_argument("--force", action="store_true")
    st.add_argument("--dry-run", action="store_true")
    st.set_defaults(func=cmd_setup)

    cfg = sub.add_parser("config", help="show/set configuration")
    cfg.add_argument("action", choices=["path", "show", "set-key"])
    cfg.add_argument("--base-url")
    cfg.add_argument("--api-key-stdin", action="store_true")
    cfg.add_argument("--skip-api-check", action="store_true")
    cfg.add_argument("--force", action="store_true")
    cfg.set_defaults(func=cmd_config)

    sk = sub.add_parser("skill", help="install/list/uninstall agent skills")
    sk.add_argument("action", choices=["install", "list", "uninstall"])
    sk.add_argument("--target", default=None, help="codex,dsh,claude,all")
    sk.add_argument("--scope", choices=["user", "project"], default="user")
    sk.add_argument("--project-root", type=Path)
    sk.add_argument("--force", action="store_true")
    sk.add_argument("--dry-run", action="store_true")
    sk.set_defaults(func=cmd_skill)

    un = sub.add_parser("uninstall", help="remove installed skills (and optionally config)")
    un.add_argument("--target", default="all")
    un.add_argument("--scope", choices=["user", "project"], default="user")
    un.add_argument("--project-root", type=Path)
    un.add_argument("--force", action="store_true")
    un.add_argument("--dry-run", action="store_true")
    un.add_argument("--purge", action="store_true")
    un.set_defaults(func=cmd_uninstall)

    sc = sub.add_parser("schema", help="print schema path")
    sc.set_defaults(func=cmd_schema)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "env_file", None):
        load_env_file(args.env_file)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
