# scripts/quality/abort_if_needed.py
# 用途: PASS/NEWを与えて、早期Abort条件 (Pass<65 or New>70) なら PR にラベル付与＆警告コメント（デフォルトは閉じない）。
import os, subprocess, sys
def num(x):
    try: return float(x)
    except: return None
PASS  = num(os.environ.get('PASS'))
NEW   = num(os.environ.get('NEW'))
FLAKY = num(os.environ.get('FLAKY'))
abort = False
if PASS is not None and PASS < 65: abort = True
if NEW  is not None and NEW  > 70: abort = True
pr_num = subprocess.check_output(["gh","pr","view","--json","number","--jq",".number"]).decode().strip()
if abort:
    subprocess.run(["gh","pr","edit",pr_num,"--add-label","early-abort"], check=False)
    body = f"⚠️ **Early Abort 条件検知**: Pass={PASS}%, New={NEW}%, Flaky={FLAKY}%\nPRはデータ収集目的のためクローズはせず、修正を推奨します。"
else:
    body = f"✅ **継続OK**: Pass={PASS}%, New={NEW}%, Flaky={FLAKY}%（早期Abort基準を満たさず）"
subprocess.run(["gh","pr","comment",pr_num,"--body",body], check=False)
print("ABORT=", "YES" if abort else "NO")
