#!/bin/bash
# しきい値自動昇格/降格スクリプト（階層ルール対応）

set -euo pipefail

echo "🎯 しきい値自動昇格/降格チェック（階層ルール）"
echo "============================================="

# 作業ディレクトリ設定
cd /Users/araimakoto/ai-driven/ai-systems-workspace

# 設定ファイル読み込み
CONFIG_FILE="tests/golden/config.yml"
LOG_FILE="tests/golden/observation_log.md"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 設定ファイルが見つかりません: $CONFIG_FILE"
    exit 1
fi

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ 観測ログが見つかりません: $LOG_FILE"
    exit 1
fi

# Python スクリプトで詳細な判定を実行（Phase 3: 二重ゲート対応）
python3 << 'EOF'
import yaml
import re
import json
from datetime import datetime
from pathlib import Path

def load_config():
    with open("tests/golden/config.yml", 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def parse_observation_log():
    """観測ログから直近データを抽出"""
    log_file = Path("tests/golden/observation_log.md")
    
    weekly_data = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 週次観測セクションを抽出（日付順でソート）
        pattern = r'## (\d{4}-\d{2}-\d{2}) - 週次観測.*?合格率.*?(\d+)/(\d+) \((\d+)%\)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            date_str, passed, total, percentage = match
            weekly_data.append({
                'date': datetime.strptime(date_str, "%Y-%m-%d").date(),
                'passed': int(passed),
                'total': int(total),
                'percentage': int(percentage)
            })
        
        # 日付でソート（新しい順）
        weekly_data.sort(key=lambda x: x['date'], reverse=True)
        
    except Exception as e:
        print(f"❌ 観測ログ解析エラー: {e}")
        return []
    
    return weekly_data

def analyze_failure_reasons():
    """不合格理由の分析（辞書/正規化で説明可能かチェック）"""
    # 実装簡略化：現在は常にTrue（辞書で説明可能と仮定）
    # 本格実装では tests/golden/logs/ の詳細分析が必要
    return True

def get_next_threshold(current_threshold):
    """次のしきい値を取得"""
    threshold_map = {
        0.3: 0.5,
        0.5: 0.7,
        0.7: 0.85,
        0.85: 0.9
    }
    return threshold_map.get(current_threshold)

def get_prev_threshold(current_threshold):
    """前のしきい値を取得"""
    threshold_map = {
        0.5: 0.3,
        0.7: 0.5,
        0.85: 0.7,
        0.9: 0.85
    }
    return threshold_map.get(current_threshold)

def check_upgrade_conditions(current_threshold, weekly_data, config):
    """昇格条件をチェック"""
    upgrade_rules = config.get('upgrade_rules', {})
    
    # 現在のしきい値に対応するルールを取得
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
        return False, "昇格ルールが見つかりません"
    
    rule = upgrade_rules[rule_key]
    required_weeks = rule['consecutive_weeks']
    min_pass_rate = rule['min_pass_rate']
    condition = rule['condition']
    
    print(f"📋 昇格ルール ({current_threshold} → {get_next_threshold(current_threshold)})")
    print(f"   - 必要週数: {required_weeks}週連続")
    print(f"   - 最低合格率: {min_pass_rate}%")
    print(f"   - 条件: {condition}")
    
    # 必要な週数分のデータがあるかチェック
    if len(weekly_data) < required_weeks:
        return False, f"データ不足: {required_weeks}週分必要（現在: {len(weekly_data)}週）"
    
    # 連続して基準を満たしているかチェック
    recent_weeks = weekly_data[:required_weeks]
    for i, week in enumerate(recent_weeks):
        if week['percentage'] < min_pass_rate:
            return False, f"{i+1}週前の合格率が基準未達: {week['percentage']}% < {min_pass_rate}%"
    
    # 特別条件のチェック
    if current_threshold == 0.5:
        # 不合格原因が辞書/正規化で説明可能
        if not analyze_failure_reasons():
            return False, "不合格原因が辞書/正規化では説明困難"
    elif current_threshold == 0.7:
        # 新規不合格の70%以上を次週までに解決可能（簡略化：常にTrue）
        pass
    
    return True, f"{required_weeks}週連続{min_pass_rate}%以上達成"

def check_downgrade_conditions(current_threshold, weekly_data, config):
    """降格条件をチェック"""
    downgrade_rules = config.get('downgrade_rules', {})
    consecutive_weeks_fail = downgrade_rules.get('consecutive_weeks_fail', 2)
    fail_threshold_ratio = downgrade_rules.get('fail_threshold_ratio', 0.8)
    
    fail_threshold = current_threshold * 100 * fail_threshold_ratio
    
    print(f"📉 降格チェック")
    print(f"   - 失敗基準: {consecutive_weeks_fail}週連続で{fail_threshold:.1f}%未満")
    
    if len(weekly_data) < consecutive_weeks_fail:
        return False, f"データ不足: {consecutive_weeks_fail}週分必要"
    
    # 連続して基準を下回っているかチェック
    recent_weeks = weekly_data[:consecutive_weeks_fail]
    for i, week in enumerate(recent_weeks):
        if week['percentage'] >= fail_threshold:
            return False, f"{i+1}週前は基準クリア: {week['percentage']}% >= {fail_threshold:.1f}%"
    
    return True, f"{consecutive_weeks_fail}週連続で基準未達"

def main():
    config = load_config()
    current_threshold = config.get('threshold', 0.3)
    
    print(f"📊 現在のしきい値: {current_threshold}")
    
    # 観測データを取得
    weekly_data = parse_observation_log()
    if not weekly_data:
        print("⏳ 観測データがありません")
        return
    
    print(f"📈 直近{len(weekly_data)}週の合格率:")
    for i, week in enumerate(weekly_data[:5]):  # 最新5週まで表示
        print(f"   {week['date']}: {week['percentage']}%")
    
    # 降格チェック（優先）
    should_downgrade, downgrade_reason = check_downgrade_conditions(current_threshold, weekly_data, config)
    
    if should_downgrade:
        prev_threshold = get_prev_threshold(current_threshold)
        if prev_threshold is None:
            print("⚠️ これ以上降格できません")
            return
        
        print(f"📉 降格条件満足: {downgrade_reason}")
        update_threshold(current_threshold, prev_threshold, "降格", downgrade_reason, weekly_data)
        return
    
    # 昇格チェック
    should_upgrade, upgrade_reason = check_upgrade_conditions(current_threshold, weekly_data, config)
    
    if should_upgrade:
        next_threshold = get_next_threshold(current_threshold)
        if next_threshold is None:
            print("🎉 既に最高しきい値に到達しています")
            return
        
        print(f"🚀 昇格条件満足: {upgrade_reason}")
        update_threshold(current_threshold, next_threshold, "昇格", upgrade_reason, weekly_data)
    else:
        print(f"📊 据え置き: {upgrade_reason}")

def update_threshold(old_threshold, new_threshold, action_type, reason, weekly_data):
    """しきい値を更新してPRを作成"""
    import subprocess
    import os
    from datetime import datetime
    
    print(f"🔄 {action_type}: {old_threshold} → {new_threshold}")
    
    # ブランチ名生成
    action_prefix = "upgrade" if new_threshold > old_threshold else "downgrade"
    branch_name = f"auto/{action_prefix}-threshold-to-{new_threshold}-{datetime.now().strftime('%Y%m%d')}"
    
    try:
        # Gitの設定確認
        try:
            subprocess.run(['git', 'config', 'user.email'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            subprocess.run(['git', 'config', 'user.email', 'github-actions@github.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'GitHub Actions'], check=True)
        
        # 新しいブランチを作成
        subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
        
        # 設定ファイルを更新
        with open('tests/golden/config.yml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_content = re.sub(
            rf'threshold: {old_threshold}',
            f'threshold: {new_threshold}',
            content
        )
        
        with open('tests/golden/config.yml', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        # 観測ログに記録
        recent_rates = [str(w['percentage']) for w in weekly_data[:3]]
        log_entry = f"""

## {datetime.now().strftime('%Y-%m-%d')} - しきい値自動{action_type}

### {action_type}実行
- **旧しきい値**: {old_threshold}
- **新しきい値**: {new_threshold}
- **理由**: {reason}
- **直近合格率**: {', '.join(recent_rates)}%

"""
        
        with open('tests/golden/observation_log.md', 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # 変更をコミット
        subprocess.run(['git', 'add', 'tests/golden/config.yml', 'tests/golden/observation_log.md'], check=True)
        
        commit_msg = f"🎯 Auto-{action_type} threshold: {old_threshold} → {new_threshold}\n\n- {reason}\n- 直近合格率: {', '.join(recent_rates)}%"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        print(f"✅ コミット完了: {branch_name}")
        
        # PRの作成（GitHub CLIが利用可能な場合）
        try:
            action_emoji = "🚀" if new_threshold > old_threshold else "📉"
            pr_title = f"{action_emoji} Golden Test しきい値{action_type}: {old_threshold} → {new_threshold}"
            
            pr_body = f"""## {action_emoji} しきい値自動{action_type}

### {action_type}内容
- **旧しきい値**: {old_threshold}
- **新しきい値**: {new_threshold}

### {action_type}理由
{reason}

### 直近の合格率
- {', '.join(recent_rates)}%

### 変更ファイル
- `tests/golden/config.yml`: しきい値更新
- `tests/golden/observation_log.md`: {action_type}記録追加

### 注意事項
この{action_type}により、Golden Testの合格基準が{"厳しく" if new_threshold > old_threshold else "緩く"}なります。
マージ後は新しいしきい値での品質監視が開始されます。

### 自動生成
このPRは `scripts/bump_threshold_if_stable.sh` により自動生成されました。"""

            subprocess.run([
                'gh', 'pr', 'create',
                '--title', pr_title,
                '--body', pr_body,
                '--label', 'golden-test,auto-generated',
                '--assignee', '@me'
            ], check=True)
            
            print("✅ PR作成完了")
            
        except subprocess.CalledProcessError:
            print("⚠️ GitHub CLI未インストール - 手動でPRを作成してください")
            print(f"ブランチ: {branch_name}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git操作エラー: {e}")
    except Exception as e:
        print(f"❌ {action_type}処理エラー: {e}")

if __name__ == "__main__":
    main()
EOF

echo ""
echo "🎯 しきい値判定処理完了"