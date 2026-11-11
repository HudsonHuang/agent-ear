"""Qwen Audio 3.1 filetrans client (DashScope async ASR).

Reuses the same submit/poll/upload pattern as the mugen/new-chat project.
No local ASR; this is the default speech backend.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import requests

MODEL = "qwen-audio-3.1-asr-flash-filetrans"
DEFAULT_BASE = "https://dashscope.aliyuncs.com/api/v1"


class QwenAsrError(RuntimeError):
    pass


def resolve_credentials() -> tuple[str, str, str]:
    """Return (api_key, base_url, source) via the shared config resolver."""
    from . import config
    q = config.get_qwen()
    if not q.get("api_key"):
        raise QwenAsrError(
            "Qwen API key is not configured. Run `agent-ear setup`, set "
            "DASHSCOPE_API_KEY, or use --no-asr / --mode privacy.")
    return q["api_key"], config.normalize_url(q["base_url"], "/api/v1"), q.get("source") or "config"

def _base() -> str:
    return resolve_credentials()[1]


def _key() -> str:
    return resolve_credentials()[0]


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_key()}",
        "Content-Type": "application/json",
        "X-DashScope-OssResourceResolve": "enable",
    }


def upload(path: Path) -> str:
    """Upload to DashScope's OSS and return an oss:// URL."""
    r = requests.get(f"{_base()}/uploads", headers=_headers(),
                     params={"action": "getPolicy", "model": MODEL}, timeout=60)
    if r.status_code >= 300:
        raise QwenAsrError(f"upload policy {r.status_code}: {r.text[:500]}")
    body = r.json()
    info = body.get("output") or body.get("data")
    if not info:
        raise QwenAsrError(f"upload policy missing output: {str(body)[:500]}")
    key = f"{info['upload_dir']}/{path.name}"
    with path.open("rb") as fh:
        files = {"file": (path.name, fh, "application/octet-stream")}
        data = {
            "OSSAccessKeyId": info["oss_access_key_id"],
            "Signature": info["signature"],
            "policy": info["policy"],
            "key": key,
            "x-oss-object-acl": info["x_oss_object_acl"],
            "x-oss-forbid-overwrite": str(info["x_oss_forbid_overwrite"]).lower(),
            "success_action_status": "200",
            "x-oss-content-type": "application/octet-stream",
        }
        up = requests.post(info["upload_host"], files=files, data=data, timeout=3600)
    if up.status_code != 200:
        raise QwenAsrError(f"upload {up.status_code}: {up.text[:500]}")
    return f"oss://{key}"


def submit(file_url: str, *, diarization: bool = True, speakers: int | None = 2,
           language_hints: list[str] | None = None,
           vocabulary: dict | None = None) -> str:
    params: dict[str, Any] = {"channel_id": [0]}
    if diarization:
        params["diarization_enabled"] = True
    if speakers:
        params["speaker_count"] = speakers
    if language_hints:
        params["language_hints"] = language_hints
    if vocabulary:
        params["vocabulary"] = vocabulary
    body = {"model": MODEL, "input": {"file_urls": [file_url]}, "parameters": params}
    r = requests.post(f"{_base()}/services/audio/asr/transcription",
                      headers={**_headers(), "X-DashScope-Async": "enable"},
                      json=body, timeout=120)
    if r.status_code >= 300:
        raise QwenAsrError(f"submit {r.status_code}: {r.text[:800]}")
    try:
        return r.json()["output"]["task_id"]
    except Exception as exc:
        raise QwenAsrError(f"submit response missing task_id: {r.text[:500]}") from exc


def poll(task_id: str, *, timeout: float = 7200, interval: float = 5.0,
         on_progress=None) -> dict:
    t0 = time.time()
    while True:
        r = requests.get(f"{_base()}/tasks/{task_id}", headers=_headers(), timeout=120)
        if r.status_code >= 300:
            raise QwenAsrError(f"poll {r.status_code}: {r.text[:800]}")
        data = r.json()
        status = (data.get("output") or {}).get("task_status")
        if on_progress:
            on_progress(status, time.time() - t0)
        if status in ("SUCCEEDED", "FAILED", "CANCELED"):
            if status != "SUCCEEDED":
                raise QwenAsrError(f"task {task_id} {status}: {str(data)[:800]}")
            return data
        if time.time() - t0 > timeout:
            raise QwenAsrError(f"task {task_id} timeout after {timeout}s")
        time.sleep(interval)


def fetch_result(query: dict) -> dict:
    results = (query.get("output") or {}).get("results") or []
    if not results:
        raise QwenAsrError(f"no results: {str(query)[:800]}")
    res = results[0]
    if res.get("subtask_status") != "SUCCEEDED":
        raise QwenAsrError(f"subtask failed: {str(res)[:800]}")
    url = res.get("transcription_url")
    if not url:
        raise QwenAsrError(f"no transcription_url: {str(res)[:500]}")
    r = requests.get(url, timeout=300)
    if r.status_code >= 300:
        raise QwenAsrError(f"download transcript {r.status_code}: {r.text[:500]}")
    return r.json()


def normalize(result: dict, *, language: str | None = None) -> dict[str, Any]:
    transcripts = result.get("transcripts") or []
    segments: list[dict[str, Any]] = []
    speech_ms = 0
    for tr in transcripts:
        speech_ms += int(tr.get("content_duration_in_milliseconds") or 0)
        for s in tr.get("sentences") or []:
            start = int(s.get("begin_time") or 0)
            end = int(s.get("end_time") or 0)
            if end <= start:
                continue
            words = []
            for w in s.get("words") or []:
                ws = int(w.get("begin_time") or 0)
                we = int(w.get("end_time") or 0)
                text = (w.get("text") or "")
                if we <= ws or not text.strip():
                    continue
                words.append({"t_ms": ws, "d_ms": we - ws, "w": text,
                              "conf": w.get("confidence")})
            segments.append({
                "start_ms": start,
                "end_ms": end,
                "speaker": f"S{int(s.get('speaker_id') or 0)}",
                "text": (s.get("text") or "").strip(),
                "lang": language or "",
                "conf": None,
                "words": words,
            })
    segments.sort(key=lambda x: (x["start_ms"], x["end_ms"]))
    for i, seg in enumerate(segments, 1):
        seg["id"] = f"sp_{i:04d}"
    return {
        "provider": "qwen-audio-3.1-filetrans",
        "model": MODEL,
        "speech_ms": speech_ms,
        "segments": segments,
        "usage": result.get("usage") or {},
        "properties": result.get("properties") or {},
    }


def transcribe(path: Path, *, language_hints: list[str] | None = None,
               speakers: int | None = 2, diarization: bool = True,
               vocabulary: dict | None = None, file_url: str | None = None,
               timeout: float = 7200, verbose: bool = False) -> dict[str, Any]:
    url = file_url or upload(path)
    if verbose:
        print(f"[qwen] submitted {path.name} ({path.stat().st_size/1e6:.1f} MB)", flush=True)
    tid = submit(url, diarization=diarization, speakers=speakers,
                 language_hints=language_hints, vocabulary=vocabulary)
    if verbose:
        print(f"[qwen] task {tid}", flush=True)
    query = poll(tid, timeout=timeout,
                 on_progress=(lambda st, dt: print(f"[qwen] {st} {dt:.0f}s", flush=True))
                 if verbose else None)
    result = fetch_result(query)
    out = normalize(result, language=(language_hints or [None])[0])
    out["task_id"] = tid
    out["file_url"] = url
    return out
