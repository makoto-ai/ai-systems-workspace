#!/usr/bin/env python3
"""
Keyword scoring and simple A/B suggestion generator.

Inputs:
  - out/official_news.jsonl (optional)
  - out/trends_daily.json (optional)
  - out/youtube_channel_insights.json (optional; title_len_median, bracket_rate etc.)

Output:
  - out/ab_suggestions.json

Scoring:
  - Base keywords from trends + curated sales terms
  - Score = recency_weight(from trends) + presence in official feeds (boost)
  - Generate two title variants using top keywords and channel median length
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from typing import List


def load_trends_words() -> Counter:
    p = Path("out/trends_daily.json")
    c: Counter = Counter()
    if not p.exists():
        return c
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for entry in data[-3:]:  # last 3 days
                if not isinstance(entry, dict):
                    continue
                res = (entry.get("result") or {}).get("data") or {}
                for kw, obj in res.items():
                    if isinstance(obj, dict) and obj.get("last30"):
                        c[kw] += int(sum(obj["last30"]) / max(len(obj["last30"]), 1))
    except Exception:
        pass
    return c


def load_official_words() -> Counter:
    p = Path("out/official_news.jsonl")
    c: Counter = Counter()
    if not p.exists():
        return c
    try:
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                j = json.loads(line)
            except Exception:
                continue
            title = str(j.get("title", ""))
            for w in ["YouTube", "アルゴリズム", "タイトル", "ショート", "収益", "おすすめ"]:
                if w in title:
                    c[w] += 5
    except Exception:
        pass
    return c


def generate_titles(top_words: List[str], median_len: int) -> List[str]:
    # Keep within ~median_len using simple heuristic
    base = top_words[:3]
    a = f"【{base[0]}】{base[1]}でも{base[2]}する方法" if len(base) >= 3 else "【最新】成果が出る方法"
    b = f"{base[2]}で伸ばす！{base[0]}の{base[1]}戦略" if len(base) >= 3 else "逆転の5戦略"
    return [a[: max(median_len, 20)], b[: max(median_len, 20)]]


def main() -> int:
    trends = load_trends_words()
    official = load_official_words()
    scores = trends + official

    # default seeds if empty
    if not scores:
        scores.update({"営業": 10, "セールス": 8, "顧客理解": 7, "成約率": 6})

    top = [w for w, _ in scores.most_common(10)]

    median_len = 32
    ci_path = Path("out/youtube_channel_insights.json")
    if ci_path.exists():
        try:
            j = json.loads(ci_path.read_text(encoding="utf-8"))
            pattern = j.get("pattern") or {}
            if isinstance(pattern, dict) and pattern.get("title_len_median"):
                median_len = int(pattern["title_len_median"]) or 32
        except Exception:
            pass

    suggestions = {
        "ts": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "top_keywords": top,
        "title_candidates": generate_titles(top, median_len),
        "thumbnail_text": [f"{top[0]}{top[1]}で逆転" if len(top) >= 2 else "逆転可", "才能ゼロOK|5戦略"],
    }

    out_dir = Path("out"); out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "ab_suggestions.json"
    out.write_text(json.dumps(suggestions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "saved": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


