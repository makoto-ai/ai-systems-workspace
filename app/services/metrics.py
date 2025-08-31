from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(event: Dict[str, Any], path: str = "out/voice_metrics.jsonl") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # Best-effort metrics; never crash the request path
        pass


