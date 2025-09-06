from fastapi import APIRouter, Request
from typing import Dict, Any, List
import os, json, time, statistics
from app.services.metrics import append_jsonl

router = APIRouter()

@router.post("/metrics/voice")
async def post_voice_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    os.makedirs("out", exist_ok=True)
    append_jsonl({
        "ts": payload.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "turnIndex": payload.get("turnIndex"),
        "route": payload.get("route"),
        "recMs": payload.get("recMs"),
        "asrMs": payload.get("asrMs"),
        "textMs": payload.get("textMs"),
        "ttsMs": payload.get("ttsMs"),
        "firstAudioMs": payload.get("firstAudioMs"),
        "asrOk": payload.get("asrOk", None),
    }, path="out/voice_metrics.jsonl")
    return {"ok": True}

@router.get("/metrics/voice/summary")
async def get_voice_metrics_summary(window: int = 50) -> Dict[str, Any]:
    path = "out/voice_metrics.jsonl"
    if not os.path.exists(path):
        return {"count": 0, "p50": None, "p90": None, "asr_rate": None, "passed": False}
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-max(1, window):]
        items: List[Dict[str, Any]] = []
        for ln in lines:
            try:
                items.append(json.loads(ln))
            except Exception:
                pass
        if not items:
            return {"count": 0, "p50": None, "p90": None, "asr_rate": None, "passed": False}
        lats = [max(0.0, (it.get("firstAudioMs") or 0)/1000.0) for it in items if isinstance(it.get("firstAudioMs"), (int, float))]
        asr_ok = sum(1 for it in items if bool(it.get("asrOk")))
        count = len(lats)
        p50 = statistics.median(lats) if lats else None
        p90 = (statistics.quantiles(lats, n=10)[8] if len(lats) >= 2 else p50) if lats else None
        asr_rate = (asr_ok / len(items)) if items else None
        passed = (p50 is not None and p90 is not None and p50 <= 1.2 and p90 <= 1.8 and asr_rate is not None and asr_rate >= 0.95)
        return {
            "count": count,
            "p50": round(p50, 3) if p50 is not None else None,
            "p90": round(p90, 3) if p90 is not None else None,
            "asr_rate": round(asr_rate, 3) if asr_rate is not None else None,
            "passed": passed,
        }
    except Exception as e:
        return {"error": str(e), "passed": False}


@router.get("/metrics/perf/history")
async def get_perf_history(n: int = 50) -> Dict[str, Any]:
    path_hist = "out/voice_performance_history.jsonl"
    path_single = "out/voice_performance.json"
    history: List[Dict[str, Any]] = []
    try:
        if os.path.exists(path_hist):
            with open(path_hist, "r", encoding="utf-8") as f:
                lines = f.readlines()[-max(1, n):]
            for ln in lines:
                try:
                    obj = json.loads(ln)
                    ts = obj.get("ts")
                    res = obj.get("result") or {}
                    entry = {
                        "ts": ts,
                        "p50": res.get("p50"),
                        "p90": res.get("p90"),
                        "asr_rate": res.get("asr_rate"),
                        "passed": res.get("passed"),
                    }
                    history.append(entry)
                except Exception:
                    pass
        elif os.path.exists(path_single):
            with open(path_single, "r", encoding="utf-8") as f:
                res = json.load(f)
            history.append({
                "ts": res.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S"),
                "p50": res.get("p50"),
                "p90": res.get("p90"),
                "asr_rate": res.get("asr_rate"),
                "passed": res.get("passed"),
            })
    except Exception as e:
        return {"error": str(e), "history": []}
    return {"count": len(history), "history": history}


@router.get("/metrics/perf/summary")
async def get_perf_summary(window: int = 20) -> Dict[str, Any]:
    # Summarize last result and pass ratio over window
    hist = await get_perf_history(window)
    if isinstance(hist, dict) and hist.get("history") is not None:
        history = hist["history"]
        if not history:
            return {"count": 0, "p50": None, "p90": None, "asr_rate": None, "passed": False, "pass_ratio": None}
        last = history[-1]
        passed_count = sum(1 for h in history if h.get("passed"))
        pass_ratio = passed_count / len(history) if history else None
        return {
            "count": len(history),
            "p50": last.get("p50"),
            "p90": last.get("p90"),
            "asr_rate": last.get("asr_rate"),
            "passed": last.get("passed"),
            "pass_ratio": round(pass_ratio, 3) if pass_ratio is not None else None,
        }
    return {"count": 0, "p50": None, "p90": None, "asr_rate": None, "passed": False, "pass_ratio": None}

