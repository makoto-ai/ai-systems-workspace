#!/usr/bin/env python3
"""
Unknownニュースレターをドメイン推定で再分類
"""

from pathlib import Path
import re

VAULT = Path("docs/obsidian-knowledge/newsletters")


def guess_domain_from_file(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    # 1) 明示の SENDER_EMAIL を探す
    m = re.search(r"SENDER_EMAIL\s*[:：]\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+)", text)
    if m:
        email = m.group(1).lower()
        if "@" in email:
            return email.split("@", 1)[1]
    # 2) 本文からメールを拾う
    m2 = re.search(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)", text)
    if m2:
        return m2.group(1).lower()
    return None


def main():
    unknown_dir = VAULT / "Unknown"
    if not unknown_dir.exists():
        print("No Unknown dir.")
        return 0
    moved = 0
    for md in unknown_dir.rglob("*.md"):
        domain = guess_domain_from_file(md)
        # fallback bucket when domain cannot be inferred
        dest_folder = domain if domain else "_unclassified"
        target = VAULT / dest_folder / md.parent.name  # keep YYYY layer
        target.mkdir(parents=True, exist_ok=True)
        new_path = target / md.name
        try:
            md.replace(new_path)
            moved += 1
            print(f"Moved: {md} -> {new_path}")
        except Exception as e:
            print(f"Skip move {md}: {e}")
    print(f"Reclassified: {moved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


