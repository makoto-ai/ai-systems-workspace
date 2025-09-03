#!/usr/bin/env python3
"""
Unified launcher CLI (大枠/中枠/小枠) with profiles.

Usage:
  python3 scripts/ai_launcher.py run --profile youtube-opt
  python3 scripts/ai_launcher.py list

Profiles YAML search order:
  profiles/*.yaml

Each profile defines:
  frame: 大枠|中枠|小枠
  steps:
    - name: "Collect official RSS"
      cmd: "python3 scripts/collect_official_rss.py"
    - name: "Trends"
      cmd: "python3 scripts/collect_trends_daily.py"
    - name: "Suggest A/B"
      cmd: "python3 scripts/keyword_scorer_ab.py"

All steps are read-only by default; profiles can include a guarded step with env APPLY=1 if desired.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


@dataclass
class Step:
    name: str
    cmd: str


@dataclass
class Profile:
    key: str
    frame: str
    steps: List[Step]


def load_profiles() -> Dict[str, Profile]:
    prof_dir = Path("profiles")
    prof_dir.mkdir(exist_ok=True)
    profiles: Dict[str, Profile] = {}
    for p in prof_dir.glob("*.yaml"):
        try:
            if yaml is None:
                continue
            data: Dict[str, Any] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            key = data.get("key") or p.stem
            frame = data.get("frame") or "中枠"
            steps = [Step(name=s.get("name", "step"), cmd=s.get("cmd", "")) for s in data.get("steps", [])]
            profiles[key] = Profile(key=key, frame=frame, steps=steps)
        except Exception as e:  # pragma: no cover
            sys.stderr.write(f"[warn] failed to load {p}: {e}\n")
    return profiles


def run_profile(profile: Profile) -> int:
    print(json.dumps({"profile": profile.key, "frame": profile.frame, "steps": [s.name for s in profile.steps]}, ensure_ascii=False))
    for s in profile.steps:
        print(f"\n▶ {s.name}")
        if not s.cmd:
            continue
        try:
            subprocess.run(s.cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            sys.stderr.write(f"[error] step failed: {s.name}: {e}\n")
            return e.returncode or 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AI unified launcher")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list")
    runp = sub.add_parser("run")
    runp.add_argument("--profile", required=True)
    args = ap.parse_args()

    profs = load_profiles()
    if args.cmd == "list":
        for k, p in profs.items():
            print(f"{k}\t{p.frame}\t{len(p.steps)} steps")
        return 0
    elif args.cmd == "run":
        prof = profs.get(args.profile)
        if not prof:
            sys.stderr.write(f"profile not found: {args.profile}\n")
            return 1
        return run_profile(prof)
    else:
        ap.print_help()
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


