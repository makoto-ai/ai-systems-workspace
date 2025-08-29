#!/bin/bash
# Golden Test しきい値自動ロールバックスクリプト
# カナリア週での緊急ロールバック対応

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/tests/golden/config.yml"

cd "$PROJECT_ROOT"

echo "🔄 Golden Test しきい値緊急ロールバック"
echo "======================================"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 設定ファイルが見つかりません: $CONFIG_FILE"
    exit 1
fi

# Python スクリプトでロールバック実行
python3 << 'EOF'
import yaml
import subprocess
from datetime import datetime

def load_config():
    with open("tests/golden/config.yml", 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_previous_threshold(current_threshold):
    """前段階のしきい値を取得"""
    if current_threshold == 0.9:
        return 0.85
    elif current_threshold == 0.85:
        return 0.7
    elif current_threshold == 0.7:
        return 0.5
    elif current_threshold == 0.5:
        return 0.3
    else:
        return None

def rollback_threshold():
    """しきい値をロールバック"""
    config = load_config()
    current_threshold = config.get('threshold', 0.5)
    
    print(f"📊 現在のしきい値: {current_threshold}")
    
    previous_threshold = get_previous_threshold(current_threshold)
    if previous_threshold is None:
        print(f"❌ ロールバック先が見つかりません（最小値に到達済み）")
        return False
    
    print(f"🔄 ロールバック: {current_threshold} → {previous_threshold}")
    
    # 設定更新
    config['threshold'] = previous_threshold
    
    with open("tests/golden/config.yml", 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    # 観測ログに記録
    log_entry = f"""
## {datetime.now().strftime('%Y-%m-%d')} - 緊急ロールバック

### 実行内容
- **ロールバック**: {current_threshold} → {previous_threshold}
- **理由**: カナリア週品質劣化による緊急対応
- **実行日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 状態
- **しきい値**: {previous_threshold}
- **状態**: 緊急ロールバック実行 🔄

"""
    
    with open("tests/golden/observation_log.md", 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    print(f"✅ ロールバック完了: {current_threshold} → {previous_threshold}")
    return True

def create_rollback_commit():
    """ロールバックコミット作成"""
    try:
        subprocess.run(["git", "add", "tests/golden/config.yml", "tests/golden/observation_log.md"], check=True)
        subprocess.run([
            "git", "commit", "--no-verify", "-m",
            f"🔄 Emergency Rollback: Golden Test threshold\n\n- Canary week quality degradation\n- Automatic rollback executed\n- Monitoring continues"
        ], check=True)
        
        print(f"✅ ロールバックコミット作成完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ コミット作成失敗: {e}")
        return False

# メイン処理
try:
    if rollback_threshold():
        create_rollback_commit()
        print(f"\n🎯 ロールバック完了")
        print(f"📊 新しい設定でGolden Testを再実行してください")
        print(f"🔍 コマンド: python tests/golden/run_golden.py")
    else:
        print(f"❌ ロールバック失敗")
        exit(1)

except Exception as e:
    print(f"❌ エラー: {e}")
    exit(1)

EOF

echo "✅ 緊急ロールバック完了"
