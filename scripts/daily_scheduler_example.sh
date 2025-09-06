#!/bin/sh
# Daily scheduler example (cron compatible)
# Safe read-only collectors and scorer. Adjust PATH to your environment.

cd "$(dirname "$0")/.." || exit 1

# RSS (official)
python3 scripts/collect_official_rss.py || true

# Google Trends (optional: requires pytrends)
python3 scripts/collect_trends_daily.py || true

# Keyword scorer + A/B suggestions
python3 scripts/keyword_scorer_ab.py || true

echo "[daily] completed at $(date)"


