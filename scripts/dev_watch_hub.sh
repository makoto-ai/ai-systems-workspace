#!/bin/zsh
# touch: trigger auto-whiten watcher at $(date '+%F %T')
set -u

REPO="${REPO:-$HOME/ai-driven/ai-systems-workspace}"
LOG="${LOG:-$HOME/Documents/Logs/pre_commit_watch.log}"
INTERVAL="${INTERVAL:-3}"
SOUND="${SOUND:-/System/Library/Sounds/Glass.aiff}"
mkdir -p "$(dirname "$LOG")"

if [[ $# -gt 0 ]]; then
  # 引数で動作を指定する自動モード
  case "$1" in
    precommit)
      CHOICE="Pre-commit 監視（拡張）" ;;
    stackwatch)
      CHOICE="総合スタック監視（3秒ごと）" ;;
    tail)
      CHOICE="監視ログを tail -f" ;;
    toppid)
      CHOICE="特定PIDを top で監視" ;;
    stop)
      CHOICE="監視を停止（pkill）" ;;
    *)
      CHOICE="__CANCEL__" ;;
  esac
else
  # 手動メニュー
  CHOICE=$(osascript \
    -e 'set L to {"Pre-commit 監視（拡張）","総合スタック監視（3秒ごと）","監視ログを tail -f","特定PIDを top で監視","監視を停止（pkill）"}' \
    -e 'set C to choose from list L' \
    -e 'if C is false then return "__CANCEL__" else return item 1 of C as string end if')
fi

[[ "$CHOICE" == "__CANCEL__" ]] && exit 0

run_term(){
  local cmd="$1"
  /usr/bin/osascript - "$cmd" <<'OSA'
on run argv
  set cmd to item 1 of argv
  tell application "Terminal"
    activate
    do script cmd
  end tell
end run
OSA
}

case "$CHOICE" in
  "Pre-commit 監視（拡張）")
    run_term "/bin/zsh -lc 'cd \"$REPO\"; echo \"== $(date '+%F %T') :: watch start ==\" >> \"$LOG\"; while pgrep -f pre-commit >/dev/null 2>&1; do date '+%F %T' >> \"$LOG\"; sleep 5; done; osascript -e \"display notification \\\"pre-commit: finished\\\" with title \\\"KM Watch\\\"\"'" ;;
  "総合スタック監視（3秒ごと）")
    run_term "/bin/zsh -lc 'INTERVAL=$INTERVAL; while true; do \
clear; date \"+%F %T\"; \
echo \"=== PROCESSES (pre-commit/python/docker) ===\"; \
ps -Ao pid,etime,pcpu,pmem,command | egrep \"pre-commit|python(3\\.[0-9])?|docker|pytest\" | grep -v egrep | head -n 40 || true; \
echo; \
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then \
  echo \"=== DOCKER CONTAINERS ===\"; \
  docker ps --format \"table {{.Names}}\\t{{.Status}}\\t{{.Image}}\"; \
  echo; \
  echo \"=== DOCKER STATS (1-shot) ===\"; \
  docker stats --no-stream --format \"table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}\"; \
else \
  echo \"(docker not running)\"; \
fi; \
sleep $INTERVAL; done'" ;;
  "監視ログを tail -f")
    run_term "/bin/zsh -lc 'mkdir -p \"$(dirname \"$LOG\")\"; touch \"$LOG\"; tail -f \"$LOG\"'" ;;
  "特定PIDを top で監視")
    PID=$(osascript -e 'text returned of (display dialog "監視する PID:" default answer "" buttons {"OK"} default button "OK")') || exit 0
    [[ -z "$PID" ]] && exit 0
    run_term "/bin/zsh -lc 'top -pid \"$PID\"'" ;;
  "監視を停止（pkill）")
    pkill -f "pre-commit run|pre-commit autoupdate|stackwatch" || true
    osascript -e 'display notification "watchers: stop signal sent" with title "KM Watch"' ;;
esac


