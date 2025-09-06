#!/usr/bin/env bash
set -euo pipefail

curl -s -X POST http://127.0.0.1:8000/api/selftest/run | jq -r '.report.elapsed_sec, .report.steps, .report.tts, .report.asr.text? // .report.asr' | cat
echo "\nReport saved to out/selftest_report.json"


