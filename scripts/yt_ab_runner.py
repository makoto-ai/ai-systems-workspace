#!/usr/bin/env python3
"""
YouTube Title A/B Runner (safe by default: dry-run)

Functions:
 1) Discover latest video on your channel using API key (read-only)
 2) Load A/B title suggestions from out/ab_suggestions.json
 3) Produce a plan -> out/ab_plan.json (no changes by default)

To actually apply (set Title A), run with environment APPLY=1 and OAuth write token
scopes: ['https://www.googleapis.com/auth/youtube',
         'https://www.googleapis.com/auth/youtube.force-ssl']

Token file: out/credentials/google_tokens_youtube_write.json
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any


def load_env(path: Path) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def discover_latest_video(api_key: str, channel_id: str) -> str | None:
    try:
        from googleapiclient.discovery import build  # type: ignore
    except Exception:
        return None

    yt = build("youtube", "v3", developerKey=api_key)
    q = yt.search().list(
        part="id",
        channelId=channel_id,
        order="date",
        type="video",
        maxResults=1,
    )
    resp = q.execute()
    items = resp.get("items") or []
    if not items:
        return None
    return (items[0].get("id") or {}).get("videoId")


def get_video_title(api_key: str, video_id: str) -> str | None:
    try:
        from googleapiclient.discovery import build  # type: ignore
    except Exception:
        return None
    yt = build("youtube", "v3", developerKey=api_key)
    r = yt.videos().list(part="snippet", id=video_id).execute()
    items = r.get("items") or []
    if not items:
        return None
    return (items[0].get("snippet") or {}).get("title")


def apply_title_oauth(video_id: str, new_title: str, token_file: Path) -> Dict[str, Any]:
    # Requires google-auth, google-auth-oauthlib, google-api-python-client
    try:
        from googleapiclient.discovery import build  # type: ignore
        from google.oauth2.credentials import Credentials  # type: ignore
        from google.auth.transport.requests import Request  # type: ignore
    except Exception as e:  # pragma: no cover
        return {"ok": False, "error": f"deps_missing: {e}"}

    scopes = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]
    if not token_file.exists():
        return {"ok": False, "error": f"token_missing: {token_file}"}

    creds = Credentials.from_authorized_user_file(str(token_file), scopes)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        token_file.write_text(creds.to_json(), encoding="utf-8")

    yt = build("youtube", "v3", credentials=creds)
    body = {
        "id": video_id,
        "snippet": {
            "title": new_title,
        },
    }
    # We must also include categoryId and other required fields if missing; try to fetch first
    current = yt.videos().list(part="snippet", id=video_id).execute()
    items = current.get("items") or []
    if items:
        sn = items[0].get("snippet", {})
        body["snippet"].update({
            "categoryId": sn.get("categoryId", "22"),
            "description": sn.get("description", ""),
            "tags": sn.get("tags", []),
            "defaultLanguage": sn.get("defaultLanguage"),
            "defaultAudioLanguage": sn.get("defaultAudioLanguage"),
        })

    upd = yt.videos().update(part="snippet", body=body).execute()
    return {"ok": True, "response": upd}


def main() -> int:
    ws = Path.cwd()
    env = load_env(ws / ".env")
    channel_id = env.get("YOUTUBE_CHANNEL_ID")
    key_path = env.get("YOUTUBE_DATA_API_KEY_FILE", "youtube_api_key.txt")
    api_key = Path(key_path).read_text(encoding="utf-8").strip() if Path(key_path).exists() else ""

    out_dir = ws / "out"
    out_dir.mkdir(exist_ok=True)

    # Load suggestions
    sugg = {"title_candidates": ["【最新】成果が出る方法", "逆転の5戦略"]}
    sp = out_dir / "ab_suggestions.json"
    if sp.exists():
        try:
            sugg = json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            pass

    if not channel_id or not api_key:
        plan = {"ok": False, "error": "missing channel_id or api_key in .env/youtube_api_key.txt"}
        (out_dir / "ab_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(plan, ensure_ascii=False))
        return 0

    vid = discover_latest_video(api_key, channel_id)
    current_title = get_video_title(api_key, vid) if vid else None

    plan = {
        "ok": True,
        "video_id": vid,
        "current_title": current_title,
        "candidates": sugg.get("title_candidates", []),
        "apply": bool(os.getenv("APPLY")),
    }

    # Dry-run by default
    if not os.getenv("APPLY"):
        (out_dir / "ab_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(plan, ensure_ascii=False))
        return 0

    # Apply Title A using OAuth token
    token_file = out_dir / "credentials" / "google_tokens_youtube_write.json"
    cand = (sugg.get("title_candidates") or [None])[0]
    if not vid or not cand:
        plan["ok"] = False
        plan["error"] = "missing video_id or candidate"
        (out_dir / "ab_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(plan, ensure_ascii=False))
        return 0

    res = apply_title_oauth(vid, cand[:95], token_file)
    plan["apply_result"] = res
    (out_dir / "ab_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


