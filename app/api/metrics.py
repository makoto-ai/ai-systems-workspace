from fastapi import APIRouter, Request
from typing import Dict, Any, List
import os, json, time, statistics

router = APIRouter()

@router.post("/metrics/voice")
async def post_voice_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    os.makedirs("out", exist_ok=True)
    line = json.dumps({
        "ts": payload.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "turnIndex": payload.get("turnIndex"),
        "route": payload.get("route"),
        "recMs": payload.get("recMs"),
        "asrMs": payload.get("asrMs"),
        "textMs": payload.get("textMs"),
        "ttsMs": payload.get("ttsMs"),
        "firstAudioMs": payload.get("firstAudioMs"),
    }, ensure_ascii=False)
    with open("out/voice_metrics.jsonl", "a", encoding="utf-8") as f:
        f.write(line + "\n")
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

