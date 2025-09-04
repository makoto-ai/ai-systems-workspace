from __future__ import annotations

import json
import os
import tempfile
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rotate_jsonl_if_needed(path: str, max_bytes: int = 5_000_000, keep_last_lines: int = 5000) -> None:
    """Shrink JSONL file when it exceeds size cap by keeping only the last N lines.

    - Best-effort: failures are silently ignored to avoid impacting request paths.
    - Designed for small caps (<=10MB) to keep memory usage reasonable.
    """
    try:
        if not os.path.exists(path):
            return
        size = os.path.getsize(path)
        if size <= max_bytes:
            return

        # Read last N lines using a bounded deque
        last_lines = deque(maxlen=max(1, keep_last_lines))
        with open(path, "r", encoding="utf-8", errors="ignore") as src:
            for line in src:
                last_lines.append(line)

        # Write to a temp file then atomically replace
        dir_name = os.path.dirname(path) or "."
        fd, tmp_path = tempfile.mkstemp(prefix="rotate_", suffix=".jsonl", dir=dir_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                tmp.writelines(last_lines)
            os.replace(tmp_path, path)
        finally:
            # In case replace failed
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    except Exception:
        # Never crash calling code
        pass


def append_jsonl(event: Dict[str, Any], path: str = "out/voice_metrics.jsonl") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        # Best-effort metrics; never crash the request path
        return

    # Post-write rotation (best-effort)
    _rotate_jsonl_if_needed(path)

