# scripts/quality/tag_failures.py
import re, sys, json, os, csv, pathlib, yaml
log = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else None
rules_path = pathlib.Path(sys.argv[2]) if len(sys.argv)>2 else pathlib.Path("scripts/quality/tag_rules.yaml")
if not log or not log.exists(): 
    print("usage: python scripts/quality/tag_failures.py <logfile> [rules.yaml]"); sys.exit(1)
rules = yaml.safe_load(open(rules_path))["rules"]
txt = open(log, 'r', encoding='utf-8', errors='ignore').read()
# 抽出対象（失敗/不一致/エラー行）
cand = [l.strip() for l in txt.splitlines() if re.search(r'(FAIL|FAILED|Assertion|mismatch|error|✖)', l, re.I)]
def sig(line):
    s = line.lower()
    s = re.sub(r'\d+(\.\d+)?\s?ms','',s)
    s = re.sub(r'\s+',' ',s).strip()
    return s
uniq = {}
for line in cand:
    uniq.setdefault(sig(line), line)
lines = list(uniq.values())
compiled = [(r['tag'], re.compile(r['pattern'], re.I)) for r in rules]
def tags_for(line):
    ts = [tag for tag,pat in compiled if pat.search(line)]
    return ts or ["OTHER"]
counts, examples = {}, {}
for line in lines:
    for t in tags_for(line):
        counts[t] = counts.get(t,0)+1
        examples.setdefault(t,[]); 
        if len(examples[t])<2: examples[t].append(line[:180])
total = sum(counts.values()) or 1
pareto = sorted(([t,c, round(c*100/total,1)] for t,c in counts.items()), key=lambda x:x[1], reverse=True)
os.makedirs("out", exist_ok=True)
json.dump({"total": total, "counts": counts, "pareto": pareto, "examples": examples}, open("out/tags.json","w"), ensure_ascii=False, indent=2)
with open("out/pareto.csv","w", newline='', encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["tag","count","share_%"]); w.writerows(pareto)
print("Wrote out/tags.json and out/pareto.csv")
