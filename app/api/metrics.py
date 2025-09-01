from fastapi import APIRouter, Request
from typing import Dict, Any
import os, json, time

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


