# scripts/quality/parse_metrics.py
# 用途: CIログから Pass/New/Flaky を抽出し、ENV形式で出力（PASS=70 など）。失敗時はunknown。
import re, sys, json
txt = open(sys.argv[1], 'r', encoding='utf-8', errors='ignore').read() if len(sys.argv)>1 else ''
def find(pat):
    m = re.search(pat, txt, re.IGNORECASE)
    return m.group(1) if m else 'unknown'
# 代表的な表記ゆれをカバー（Pass: 70% / PASS=70% / pass 70 % など）
pass_v  = find(r'Pass\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)%')
new_v   = find(r'New\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)%')
flaky_v = find(r'Flaky\s*[:=]\s*([0-9]+(?:\.[0-9]+)?)%')
print(f"PASS={pass_v}")
print(f"NEW={new_v}")
print(f"FLAKY={flaky_v}")
