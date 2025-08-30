#!/usr/bin/env python3
"""
Outlook newsletters → Obsidian saver
Reads exported text from AppleScript and writes Markdown notes under
docs/obsidian-knowledge/newsletters/<sender>/<YYYY>/<YYYY-MM-DD>_<subject>.md
"""

from __future__ import annotations

import sys
import re
import os
from pathlib import Path
from datetime import datetime


VAULT = Path(__file__).resolve().parents[1] / "docs" / "obsidian-knowledge"
BASE_DIR = VAULT / "newsletters"

ALLOWLIST = {
    "message@palmbeach.jp",
    "info@million-sales.com",
    "info@mag.ikehaya.com",
    "mail@the-3rd-brain.com",
}


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[\n\r\t]", " ", name)
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:80] if len(name) > 80 else name


def parse_export(text: str):
    items = []
    if text.strip() in ("", "NO_SELECTION"):
        return items
    blocks = [b for b in text.split("---") if b.strip()]
    for b in blocks:
        subject_match = re.search(r"^SUBJECT:\s*(.*)$", b, re.M)
        sender_match = re.search(r"^SENDER:\s*(.*)$", b, re.M)
        content_match = re.search(r"CONTENT_START\n([\s\S]*?)\nCONTENT_END", b, re.M)
        subject = subject_match.group(1).strip() if subject_match else "(No Subject)"
        sender = sender_match.group(1).strip() if sender_match else "Unknown"
        sender_email_match = re.search(r"^SENDER_EMAIL:\s*(.*)$", b, re.M)
        sender_email = (sender_email_match.group(1).strip() if sender_email_match else "").lower()
        # Fallback: extract first email from header/body if missing
        if not sender_email:
            any_email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", b)
            if any_email_match:
                sender_email = any_email_match.group(0).lower()
        content = content_match.group(1).rstrip() if content_match else "(No Content)"
        items.append({"subject": subject, "sender": sender, "sender_email": sender_email, "content": content})
    return items


def save_item(item: dict) -> Path:
    sender = sanitize_filename(item.get("sender", "Unknown")) or "Unknown"
    subject = sanitize_filename(item.get("subject", "(No Subject)")) or "No_Subject"
    y = datetime.now().strftime("%Y")
    d = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    # Prefer domain folder when sender_email is available
    sender_email = (item.get("sender_email") or "").lower()
    domain_folder = None
    if "@" in sender_email:
        try:
            domain_folder = sender_email.split("@", 1)[1]
        except Exception:
            domain_folder = None
    folder_name = sanitize_filename(domain_folder) if domain_folder else sender
    target_dir = BASE_DIR / folder_name / y
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{d}_{subject}.md"
    path = target_dir / filename
    md = (
        f"# {subject}\n\n"
        f"> 📅 受信日時: {datetime.now():%Y-%m-%d %H:%M:%S}\n"
        f"> ✉️ 送信元: {sender}\n\n"
        f"## 本文\n\n{item.get('content','')}\n"
    )
    path.write_text(md, encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    data = sys.stdin.read()
    items = parse_export(data)
    if not items:
        print("NO_ITEMS")
        return 0
    filtered = []
    for it in items:
        email = (it.get("sender_email") or "").lower()
        if email in ALLOWLIST:
            filtered.append(it)
        else:
            # Skip non-allowed senders
            pass
    if not filtered:
        print("NO_ALLOWED_ITEMS")
        return 0
    saved = [save_item(it) for it in filtered]
    for p in saved:
        print(f"SAVED:{p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


