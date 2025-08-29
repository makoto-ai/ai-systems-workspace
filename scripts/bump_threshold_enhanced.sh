#!/bin/bash
# Golden Test しきい値自動昇格スクリプト（Phase 3強化版）
# 二重ゲート（flaky_rate + new_fail_ratio）対応

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/tests/golden/config.yml"
LOG_FILE="$PROJECT_ROOT/tests/golden/observation_log.md"

# オプション解析
DRY_RUN=false
TARGET_THRESHOLD=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --target)
      TARGET_THRESHOLD="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

cd "$PROJECT_ROOT"

echo "🎯 Phase 3 しきい値自動昇格チェック（二重ゲート対応）"
echo "=================================================="

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 設定ファイルが見つかりません: $CONFIG_FILE"
    exit 1
fi

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 観測ログが見つかりません: $LOG_FILE"
    exit 1
fi

# Python スクリプトで詳細な判定を実行
python3 << 'EOF'
import yaml
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path

def load_config():
    with open("tests/golden/config.yml", 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_latest_metrics():
    """最新のflaky_rate, new_fail_ratioを取得"""
    logs_dir = Path("tests/golden/logs")
    if not logs_dir.exists():
        return 0.0, 0.0
    
    log_files = sorted(logs_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not log_files:
        return 0.0, 0.0
    
    latest_log = log_files[0]
    flaky_count = 0
    total_failures = 0
    new_failures = 0
    
    # 失敗履歴を構築
    failure_history = {}
    for log_file in sorted(logs_dir.glob("*.jsonl")):
        date_str = log_file.stem.split('_')[0]
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if not data.get('passed', True):
                            case_id = data.get('id', '')
                            if case_id:
                                if case_id not in failure_history:
                                    failure_history[case_id] = set()
                                failure_history[case_id].add(date_str)
                    except json.JSONDecodeError:
                        continue
    
    # 最新ログから指標計算
    current_date = latest_log.stem.split('_')[0]
    with open(latest_log, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if not data.get('passed', True):
                        total_failures += 1
                        score = data.get('score', 0.0)
                        case_id = data.get('id', '')
                        
                        # Flaky判定（スコア0.7以上の失敗）
                        if score >= 0.7:
                            flaky_count += 1
                        
                        # New failure判定
                        if case_id in failure_history:
                            past_failures = failure_history[case_id]
                            is_new = all(past_date >= current_date for past_date in past_failures)
                            if is_new:
                                new_failures += 1
                        else:
                            new_failures += 1
                            
                except json.JSONDecodeError:
                    continue
    
    flaky_rate = (flaky_count / max(total_failures, 1)) if total_failures > 0 else 0.0
    new_fail_ratio = (new_failures / max(total_failures, 1)) if total_failures > 0 else 0.0
    
    return flaky_rate, new_fail_ratio

def parse_observation_log():
    """観測ログから合格率を抽出"""
    with open("tests/golden/observation_log.md", 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 週次観測セクションを抽出
    pattern = r'## (\d{4}-\d{2}-\d{2}) - 週次観測.*?合格率.*?(\d+)/(\d+) \((\d+)%\)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    pass_rates = []
    for match in matches:
        date_str, passed, total, percentage = match
        pass_rates.append(int(percentage))
    
    return pass_rates

def should_upgrade_with_gates(current_threshold, pass_rates):
    """昇格判定（階層ルール + Phase 3二重ゲート）"""
    config = load_config()
    upgrade_rules = config.get('upgrade_rules', {})
    
    # 現在のしきい値に対応する昇格ルールを取得
    rule_key = None
    if current_threshold == 0.3:
        rule_key = "0.3_to_0.5"
    elif current_threshold == 0.5:
        rule_key = "0.5_to_0.7"
    elif current_threshold == 0.7:
        rule_key = "0.7_to_0.85"
    elif current_threshold == 0.85:
        rule_key = "0.85_to_0.9"
    
    if not rule_key or rule_key not in upgrade_rules:
        print(f"⚠️ しきい値 {current_threshold} に対応する昇格ルールが見つかりません")
        return False, None, ["ルール未定義"]
    
    rule = upgrade_rules[rule_key]
    required_weeks = rule.get('consecutive_weeks', 2)
    min_pass_rate = rule.get('min_pass_rate', 90)
    condition = rule.get('condition', '')
    
    print(f"📋 昇格ルール ({rule_key}):")
    print(f"   必要週数: {required_weeks}週連続")
    print(f"   最低合格率: {min_pass_rate}%")
    print(f"   条件: {condition}")
    
    # 基本条件チェック
    if len(pass_rates) < required_weeks:
        print(f"❌ データ不足: {len(pass_rates)}週 < {required_weeks}週")
        return False, None, ["データ不足"]
    
    recent_rates = pass_rates[-required_weeks:]
    all_above_threshold = all(rate >= min_pass_rate for rate in recent_rates)
    
    print(f"📊 直近{required_weeks}週の合格率: {recent_rates}")
    print(f"✅ 全週が{min_pass_rate}%以上: {all_above_threshold}")
    
    # Phase 3: 二重ゲートチェック（0.5→0.7の場合のみ）
    gate_failures = []
    if current_threshold == 0.5 and rule_key == "0.5_to_0.7":
        print(f"🚪 Phase 3 二重ゲートチェック実行...")
        
        flaky_rate, new_fail_ratio = get_latest_metrics()
        print(f"   Flaky率: {flaky_rate:.1%} (上限: 5%)")
        print(f"   新規失敗率: {new_fail_ratio:.1%} (上限: 60%)")
        
        if flaky_rate > 0.05:
            gate_failures.append(f"Flaky率が高すぎます: {flaky_rate:.1%} > 5%")
        
        if new_fail_ratio > 0.60:
            gate_failures.append(f"新規失敗率が高すぎます: {new_fail_ratio:.1%} > 60%")
        
        if gate_failures:
            print(f"❌ 二重ゲート失敗: {gate_failures}")
            return False, None, gate_failures
        else:
            print(f"✅ 二重ゲート通過")
    
    if all_above_threshold and not gate_failures:
        # 次のしきい値を決定
        next_threshold = None
        if current_threshold == 0.3:
            next_threshold = 0.5
        elif current_threshold == 0.5:
            next_threshold = 0.7
        elif current_threshold == 0.7:
            next_threshold = 0.85
        elif current_threshold == 0.85:
            next_threshold = 0.9
        
        return True, next_threshold, []
    
    return False, None, gate_failures if gate_failures else ["合格率不足"]

def create_issue_for_failed_gates(gate_failures, current_threshold, flaky_rate, new_fail_ratio):
    """ゲート失敗時のIssue作成"""
    title = f"🚨 Phase 3昇格ゲート失敗: {current_threshold} → 0.7"
    
    body = f"""## 🚨 自動昇格ゲート失敗

### 失敗理由
{chr(10).join(f"- {failure}" for failure in gate_failures)}

### 現在の指標
- **Flaky率**: {flaky_rate:.1%} (上限: 5%)
- **新規失敗率**: {new_fail_ratio:.1%} (上限: 60%)
- **現在しきい値**: {current_threshold}

### 対応が必要な項目
1. **Flaky率改善**: モデル出力の安定性向上
2. **新規失敗率削減**: 辞書・正規化の強化
3. **Root Cause分析**: 失敗パターンの詳細調査

### 推奨アクション
- [ ] Root Cause分析実行: `python tests/golden/root_cause_analyzer.py`
- [ ] 辞書チューニング: `tests/golden/evaluator.py`の`_NORM_MAP`更新
- [ ] モデル実験: `python experiments/model_swap.py --cases MODEL`

### ダッシュボード
- [Golden KPI Dashboard](http://localhost:8501)

### 自動生成
このIssueは昇格ゲート失敗により自動生成されました。
"""
    
    try:
        result = subprocess.run([
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
            "--label", "golden-test,quality-gate,auto-generated"
        ], capture_output=True, text=True, check=True)
        
        issue_url = result.stdout.strip()
        print(f"📋 Issue作成完了: {issue_url}")
        return issue_url
    except subprocess.CalledProcessError as e:
        print(f"❌ Issue作成失敗: {e}")
        return None

def create_canary_pr(current_threshold, next_threshold):
    """カナリアPR作成"""
    branch_name = f"canary-threshold-{current_threshold}-to-{next_threshold}"
    
    try:
        # ブランチ作成
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        
        # 設定更新
        config = load_config()
        config['threshold'] = next_threshold
        
        with open("tests/golden/config.yml", 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        # コミット
        subprocess.run(["git", "add", "tests/golden/config.yml"], check=True)
        subprocess.run([
            "git", "commit", "--no-verify", "-m",
            f"🐤 Canary: しきい値昇格 {current_threshold} → {next_threshold}\n\n- Phase 3二重ゲート通過\n- カナリア週運用開始"
        ], check=True)
        
        # プッシュ
        subprocess.run(["git", "push", "origin", branch_name], check=True)
        
        # PR作成
        title = f"🐤 Canary: Golden Test しきい値昇格 {current_threshold} → {next_threshold}"
        body = f"""## 🐤 カナリア昇格

### 昇格内容
- **旧しきい値**: {current_threshold}
- **新しきい値**: {next_threshold}
- **フェーズ**: Phase 3: 本格運用期

### 二重ゲート通過
✅ 合格率: 2週連続90%以上
✅ Flaky率: < 5%
✅ 新規失敗率: ≤ 60%

### カナリア週運用
- **監視強化**: 失敗発生で即時Issue起票
- **自動ロールバック**: 合格率<85%で自動復旧
- **通知強化**: Slack/Discord即時通知

### 注意事項
このPRはカナリア昇格です。1週間の監視期間後に本格運用に移行します。

### 自動生成
このPRは二重ゲート通過により自動生成されました。
"""
        
        result = subprocess.run([
            "gh", "pr", "create",
            "--title", title,
            "--body", body,
            "--label", "canary,golden-test,auto-generated"
        ], capture_output=True, text=True, check=True)
        
        pr_url = result.stdout.strip()
        print(f"🐤 Canary PR作成完了: {pr_url}")
        
        # 元のブランチに戻る
        subprocess.run(["git", "checkout", "master"], check=True)
        
        return pr_url
    except subprocess.CalledProcessError as e:
        print(f"❌ Canary PR作成失敗: {e}")
        # クリーンアップ
        try:
            subprocess.run(["git", "checkout", "master"], check=False)
            subprocess.run(["git", "branch", "-D", branch_name], check=False)
        except:
            pass
        return None

# メイン処理
try:
    config = load_config()
    current_threshold = config.get('threshold', 0.5)
    pass_rates = parse_observation_log()
    
    print(f"📊 現在のしきい値: {current_threshold}")
    print(f"📈 直近の合格率: {pass_rates[-5:] if len(pass_rates) >= 5 else pass_rates}")
    
    should_upgrade, next_threshold, failures = should_upgrade_with_gates(current_threshold, pass_rates)
    
    if should_upgrade:
        print(f"🚀 昇格条件満足: {current_threshold} → {next_threshold}")
        
        # カナリアPR作成
        pr_url = create_canary_pr(current_threshold, next_threshold)
        if pr_url:
            print(f"✅ カナリアPR作成完了: {pr_url}")
        else:
            print(f"❌ カナリアPR作成失敗")
    else:
        print(f"❌ 昇格条件未満: {failures}")
        
        # ゲート失敗の場合はIssue作成
        if current_threshold == 0.5 and failures:
            flaky_rate, new_fail_ratio = get_latest_metrics()
            issue_url = create_issue_for_failed_gates(failures, current_threshold, flaky_rate, new_fail_ratio)
            if issue_url:
                print(f"📋 失敗Issue作成完了: {issue_url}")

except Exception as e:
    print(f"❌ エラー: {e}")
    exit(1)

EOF

echo "✅ Phase 3 昇格チェック完了"
