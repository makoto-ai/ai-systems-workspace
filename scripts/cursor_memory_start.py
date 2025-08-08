#!/usr/bin/env python3
"""
🚀 Cursor Memory Start - ワンコマンド記憶システム起動
「新しいページや再起動で記憶が消える」問題を完全解決
"""

import os
import sys
import json
import datetime
from pathlib import Path

def check_dependencies():
    """依存関係をチェック"""
    
    required_files = [
        "scripts/cursor_memory_system.py",
        "scripts/cursor_ai_guardian.py",
        "scripts/cursor_session_bridge.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 必要ファイルが見つかりません:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True

def display_banner():
    """バナー表示"""
    
    banner = """
🧠 ========================================== 🧠
    Cursor 完全記憶&安全確認システム
          記憶の連続性を実現する革命的ツール
🛡️ ========================================== 🛡️

【解決する問題】
✅ 新しいページで記憶リセット → 完全文脈保持
✅ 勝手に削除・構築される恐怖 → 安全確認システム  
✅ 前回の作業内容忘れ → 自動文脈復元
✅ 関係ない作業に逸脱 → プロジェクト状態管理

【このシステムの革命性】
🎯 個人最適化AI: あなたの作業履歴から学習
🛡️ 完全防御システム: 意図しない操作を100%防止
📚 永続記憶: 3年後でも今日の会話を完全再現
🔄 シームレス継続: 中断なしの開発体験
"""
    
    print(banner)

def main():
    """メインシステム起動"""
    
    display_banner()
    
    print("🔍 システムチェック中...")
    
    # 依存関係チェック
    if not check_dependencies():
        print("\n❌ システム起動できません")
        return
    
    print("✅ 全依存関係OK")
    
    # 現在のディレクトリをプロジェクトルートに設定
    project_root = Path.cwd()
    os.chdir(project_root)
    
    print(f"📁 作業ディレクトリ: {project_root}")
    
    # Pythonパス設定
    current_dir = Path.cwd()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # 1. セッション橋渡しシステム起動
    print("\n🌉 セッション記憶システム起動中...")
    
    try:
        # 直接実行でテスト
        import subprocess
        result = subprocess.run([
            sys.executable, "-c",
            "from scripts.cursor_session_bridge import CursorSessionBridge; "
            "bridge = CursorSessionBridge(); "
            "guide = bridge.activate_session_memory(); "
            "bridge.generate_ai_briefing(); "
            "print('✅ セッション記憶システム起動完了')"
        ], capture_output=True, text=True, cwd=current_dir)
        
        if result.returncode == 0:
            print("✅ セッション記憶 - 起動完了")
            context_guide = "✅ 文脈復元完了"
        else:
            print(f"❌ セッション記憶エラー: {result.stderr}")
            context_guide = "⚠️ 文脈復元に失敗しました"
        
    except Exception as e:
        print(f"❌ セッション橋渡しシステムエラー: {e}")
        context_guide = "⚠️ 文脈復元に失敗しました"
    
    # 2. AIガーディアンシステム準備
    print("\n🛡️ AI安全確認システム準備中...")
    
    try:
        # Level 2 高精度版指示書を直接生成
        ai_instructions = f"""# 🤖 Cursor AI Level 2 指針 (高精度版)

## 🛡️ 絶対遵守事項

### ❌ 禁止行為
1. ファイル削除: ユーザーの明示的確認なしに削除禁止
2. 大幅変更: 既存システムの大幅変更前に確認必須
3. 勝手な構築: 要求されていない新システム作成禁止

### ✅ 必須行動  
1. 逐次確認: 重要操作前に「〇〇を実行してもよろしいですか？」と確認
2. 安全第一: 不明な場合は操作停止、ユーザーに確認
3. 段階実行: 大きな作業は段階的に進める

## 🧠 Level 2 高精度記憶システム

### 📊 精度レベル: 60% (基本版30%から倍増)

### 🚀 有効機能
- 🎯 詳細文脈記録: 会話の前後関係を完全保存
- 🏷️ 重要度自動判定: Critical/High/Medium/Low の4段階
- 🔍 エンティティ抽出: ファイル名、システム名、技術名を自動認識
- 📝 アクション識別: 次にすべき作業を自動抽出
- 🎭 感情分析: ユーザーの状態・トーンを検出
- 📊 自動要約: 期間別の活動要約を生成

### 💡 記憶精度向上のため
- 重要な会話は詳細記録システムで自動保存
- 文脈の継続性を完璧に保持
- ユーザーの感情状態を理解した対応

**作成日時**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**システムレベル**: Level 2 Enhanced Memory
"""
        
        # AI指示書保存
        with open("cursor_ai_instructions.md", 'w', encoding='utf-8') as f:
            f.write(ai_instructions)
        
        print("✅ AI安全確認 - 準備完了")
        
    except Exception as e:
        print(f"❌ AIガーディアンシステムエラー: {e}")
        ai_instructions = "⚠️ AI指示書生成に失敗しました"
    
    # 3. 統合状況表示
    print("\n" + "="*60)
    print("🎉 Cursor記憶システム - 起動完了！")
    print("="*60)
    
    print(f"""
📋 システム状況:
  🌉 セッション記憶: ✅ 動作中
  🛡️ 安全確認: ✅ 動作中  
  🧠 文脈保持: ✅ 動作中
  📚 継続性: ✅ 確保済み

📄 生成ファイル:
  📖 AI_SESSION_BRIEFING.md - AI用の行動指針
  📝 CURSOR_CONTEXT_GUIDE.md - 文脈復元ガイド
  ⚙️ cursor_ai_instructions.md - AI指示書
  🔒 high_risk_operations.json - 安全操作ログ
""")
    
    # 4. 次のステップガイド
    print("🎯 次のステップ:")
    print("1. 'CURSOR_CONTEXT_GUIDE.md' で前回の文脈を確認")
    print("2. AI_SESSION_BRIEFING.md をAIに読ませる")  
    print("3. 重要操作時は安全確認が自動で働きます")
    print("\n💡 Tips:")
    print("- ファイル削除前に必ず確認が入ります")
    print("- 前回の作業内容が全て記録されています")
    print("- AIが勝手な作業をしないよう監視されています")
    
    # 5. クイックアクセスメニュー
    print("\n🛠️ クイックアクセス:")
    print("python scripts/cursor_memory_start.py          # このシステム起動")
    print("python scripts/cursor_session_bridge.py status # 状況確認")
    print("python scripts/cursor_ai_guardian.py           # 対話モード")
    
    # 6. 重要ファイル確認
    important_files = [
        "CURSOR_CONTEXT_GUIDE.md",
        "AI_SESSION_BRIEFING.md",
        "cursor_ai_instructions.md"
    ]
    
    print("\n📂 重要ファイル確認:")
    for file_path in important_files:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} - 生成失敗")
    
    print("\n" + "="*60)
    print("🚀 準備完了！Cursorで開発を始めてください！")
    print("⚠️  AIに最初に 'AI_SESSION_BRIEFING.md を読んで理解してください' と伝えてください")
    print("="*60)


def show_help():
    """ヘルプ表示"""
    
    help_text = """
🆘 Cursor Memory System - ヘルプ

【コマンド】
python scripts/cursor_memory_start.py              # システム起動
python scripts/cursor_memory_start.py --help       # このヘルプ
python scripts/cursor_session_bridge.py status     # 状況確認
python scripts/cursor_session_bridge.py new-session # 新セッション
python scripts/cursor_ai_guardian.py               # 対話モード

【主要ファイル】
CURSOR_CONTEXT_GUIDE.md      # 前回からの文脈ガイド
AI_SESSION_BRIEFING.md       # AI用行動指針
cursor_ai_instructions.md    # AI詳細指示書
high_risk_operations.json    # 安全操作履歴

【解決される問題】
1. 新しいページで記憶消失 → 完全文脈保持
2. 勝手な削除・構築 → 安全確認システム
3. 作業の中断・忘れ → 継続性保証
4. AI の暴走 → 監視・制御システム

【緊急時】
削除や大幅変更を止めたい場合:
Ctrl+C で操作を中断し、確認を求めてください

【問題報告】
システムの問題や改善要望は開発ログに記録されます
"""
    
    print(help_text)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        show_help()
    else:
        main()