#!/usr/bin/env python3
"""
Google Trends (PyTrends) daily fetcher for JP.
Safe read-only. If pytrends is not available, falls back to web API-free mode
by skipping gracefully.

Output: out/trends_daily.json (rolling append with date key)
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def try_pytrends(topics: list[str]) -> dict:
    try:
        from pytrends.request import TrendReq  # type: ignore
    except Exception:
        return {"ok": False, "error": "pytrends_not_installed"}

    py = TrendReq(hl="ja-JP", tz=540)
    res: dict[str, dict] = {}
    for kw in topics:
        try:
            py.build_payload([kw], timeframe="today 3-m", geo="JP")
            df = py.interest_over_time()
            if df is not None and not df.empty:
                series = df[kw].tail(30).fillna(0).astype(int).tolist()
                res[kw] = {"last30": series}
        except Exception as e:  # pragma: no cover
            res[kw] = {"error": str(e)}
    return {"ok": True, "data": res}


def main() -> int:
    topics = [
        "営業", "セールス", "顧客理解", "成約率", "商談", "プレゼン",
        "YouTube アルゴリズム", "タイトル", "サムネイル",
    ]
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "trends_daily.json"

    result = try_pytrends(topics)
    bundle = {"date": str(date.today()), "result": result}

    # merge append-style json (simple array file)
    if out_path.exists():
        try:
            arr = json.loads(out_path.read_text(encoding="utf-8"))
            if isinstance(arr, list):
                arr.append(bundle)
                out_path.write_text(json.dumps(arr, ensure_ascii=False, indent=2), encoding="utf-8")
            else:
                out_path.write_text(json.dumps([bundle], ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            out_path.write_text(json.dumps([bundle], ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        out_path.write_text(json.dumps([bundle], ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "saved": str(out_path)} , ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


