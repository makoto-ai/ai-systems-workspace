#!/usr/bin/env python3
"""
Official sources RSS/Atom collector (safe, read-only)

- Creator Insider (YouTube creator official)
- YouTube Official Blog (category: creators if available)
- YouTube Help Community (RSS for updates/articles when available)

Outputs:
  out/official_news.jsonl  (one JSON per line)

Notes:
- This script only performs HTTP GET to public feeds. No scraping of gated pages.
- feedparser is optional. If not installed, falls back to xml.etree.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import contextlib

try:
    import feedparser  # type: ignore
except Exception:  # pragma: no cover
    feedparser = None  # noqa: N816

import urllib.request


@dataclass
class FeedItem:
    source: str
    title: str
    link: str
    published: Optional[str]
    summary: Optional[str]


SOURCES = [
    # Creator Insider (YouTube公式のクリエイター向け情報)
    ("creator_insider", "https://www.youtube.com/feeds/videos.xml?channel_id=UCGg-UqjRgzhYDPJMr-9HXCg"),
    # YouTube Official Blog (全体RSS)
    ("youtube_official_blog", "https://blog.youtube/feeds/rss/"),
    # YouTube Help (ヘルプ アップデートのRSSは限定的。ここではYouTubeカテゴリのヘルプ記事RSSを利用)
    ("google_help_youtube", "https://support.google.com/youtube/feeds/news.xml"),
]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ai-systems-workspace/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:  # nosec B310
        return r.read()


def parse_feed_bytes(data: bytes, source: str) -> List[FeedItem]:
    items: List[FeedItem] = []
    if feedparser is not None:
        fp = feedparser.parse(data)
        for e in fp.get("entries", []):
            items.append(
                FeedItem(
                    source=source,
                    title=str(e.get("title", "")),
                    link=str(e.get("link", "")),
                    published=str(e.get("published", "")) if e.get("published") else None,
                    summary=str(e.get("summary", "")) if e.get("summary") else None,
                )
            )
        return items

    # fallback: very light XML parse
    import xml.etree.ElementTree as ET  # noqa: N814

    with contextlib.suppress(Exception):
        root = ET.fromstring(data.decode("utf-8", errors="ignore"))
        # handle rss/channel/item or atom:feed/entry
        # rss
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate")
            desc = item.findtext("description")
            items.append(FeedItem(source=source, title=title, link=link, published=pub, summary=desc))

        # atom
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//a:entry", ns):
            title = (entry.findtext("a:title", default="", namespaces=ns) or "")
            link = ""
            link_el = entry.find("a:link", ns)
            if link_el is not None and link_el.get("href"):
                link = link_el.get("href")  # type: ignore[assignment]
            pub = entry.findtext("a:updated", default=None, namespaces=ns)
            summary = entry.findtext("a:summary", default=None, namespaces=ns)
            items.append(FeedItem(source=source, title=title, link=link, published=pub, summary=summary))

    return items


def main() -> int:
    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "official_news.jsonl"

    total = 0
    with out_path.open("a", encoding="utf-8") as f:
        for name, url in SOURCES:
            try:
                data = fetch(url)
                items = parse_feed_bytes(data, name)
                stamped = datetime.utcnow().isoformat() + "Z"
                for it in items:
                    rec = asdict(it)
                    rec["ts"] = stamped
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total += len(items)
            except Exception as e:  # pragma: no cover
                sys.stderr.write(f"[warn] {name} failed: {e}\n")

    print(json.dumps({"ok": True, "written": total, "path": str(out_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


