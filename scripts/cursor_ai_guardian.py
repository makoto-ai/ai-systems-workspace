#!/usr/bin/env python3
"""
🛡️ Cursor AI Guardian - AI暴走防止&記憶統合システム
ユーザーの「勝手に削除されたり構築されるのが怖い」問題を完全解決
"""

import os
import sys
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
try:
    from cursor_memory_system import CursorMemorySystem
except ImportError:
    import sys
    sys.path.insert(0, '.')
    from scripts.cursor_memory_system import CursorMemorySystem

class CursorAIGuardian:
    """AI暴走防止と記憶管理を統合したガーディアンシステム"""
    
    def __init__(self):
        self.memory_system = CursorMemorySystem()
        self.high_risk_operations = [
            "delete", "remove", "rm", "削除", "消去",
            "drop", "truncate", "clear", "clean",
            "格式", "format", "フォーマット"
        ]
        self.medium_risk_operations = [
            "create", "build", "構築", "作成", "新規",
            "modify", "change", "変更", "修正",
            "install", "インストール", "setup"
        ]
        
    def initialize_session(self, user_intent: str = None) -> str:
        """セッション初期化とAIへの指示書生成"""
        
        if not user_intent:
            user_intent = self._prompt_user_intent()
        
        # セッション開始
        context_guide = self.memory_system.start_new_session(user_intent)
        
        # AI指示書生成
        ai_instructions = self._generate_ai_instructions(context_guide)
        
        # ファイル保存
        instructions_file = Path("cursor_ai_instructions.md")
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(ai_instructions)
        
        print(f"✅ AI指示書を生成しました: {instructions_file}")
        print("\n" + "="*60)
        print("🧠 セッション初期化完了！")
        print("="*60)
        print(context_guide)
        print("="*60)
        
        return ai_instructions
    
    def analyze_user_request(self, user_message: str) -> Dict[str, Any]:
        """ユーザーリクエストを分析し、安全性を判定"""
        
        message_lower = user_message.lower()
        risk_level = "low"
        requires_confirmation = False
        risky_operations = []
        
        # 高リスク操作検出
        for operation in self.high_risk_operations:
            if operation in message_lower:
                risk_level = "high"
                requires_confirmation = True
                risky_operations.append(operation)
        
        # 中リスク操作検出
        if risk_level == "low":
            for operation in self.medium_risk_operations:
                if operation in message_lower:
                    risk_level = "medium"
                    requires_confirmation = True
                    risky_operations.append(operation)
        
        analysis = {
            "user_message": user_message,
            "risk_level": risk_level,
            "requires_confirmation": requires_confirmation,
            "risky_operations": risky_operations,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return analysis
    
    def request_user_confirmation(self, analysis: Dict[str, Any]) -> bool:
        """ユーザーに確認を求める"""
        
        operations_str = ", ".join(analysis["risky_operations"])
        risk_emoji = "🔴" if analysis["risk_level"] == "high" else "🟡"
        
        print(f"\n{risk_emoji} 安全確認が必要です！")
        print("-" * 50)
        print(f"検出された操作: {operations_str}")
        print(f"リスクレベル: {analysis['risk_level']}")
        print(f"ユーザーメッセージ: {analysis['user_message']}")
        print("-" * 50)
        
        if analysis["risk_level"] == "high":
            print("⚠️  HIGH RISK: ファイル削除やシステム変更が含まれています！")
        
        print("\n以下の操作を実行してもよろしいですか？")
        print("y: はい、実行してください")
        print("n: いいえ、実行しないでください") 
        print("d: 詳細を確認してから決めます")
        
        while True:
            choice = input("\n選択 (y/n/d): ").lower().strip()
            
            if choice in ['y', 'yes', 'はい']:
                # 承認をログに記録
                self.memory_system.process_safety_approval(
                    f"manual_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    True,
                    "ユーザーが手動で承認"
                )
                return True
                
            elif choice in ['n', 'no', 'いいえ']:
                # 拒否をログに記録
                self.memory_system.process_safety_approval(
                    f"manual_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    False,
                    "ユーザーが手動で拒否"
                )
                print("❌ 操作がキャンセルされました。")
                return False
                
            elif choice in ['d', 'detail', '詳細']:
                self._show_detailed_info(analysis)
                continue
                
            else:
                print("❌ 無効な選択です。y, n, d のいずれかを入力してください。")
    
    def record_session_activity(self, user_message: str, ai_response: str = None, 
                               approved: bool = True) -> None:
        """セッション活動を記録"""
        
        if ai_response is None:
            ai_response = "処理中..."
        
        # 記憶システムに記録
        self.memory_system.record_conversation(user_message, ai_response)
        
        # 重要操作の場合は追加ログ
        analysis = self.analyze_user_request(user_message)
        if analysis["requires_confirmation"]:
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "user_message": user_message,
                "risk_analysis": analysis,
                "approved": approved,
                "ai_response_summary": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
            }
            
            # 高リスク操作ログファイル
            risk_log_file = Path("high_risk_operations.json")
            
            if risk_log_file.exists():
                with open(risk_log_file, 'r', encoding='utf-8') as f:
                    risk_logs = json.load(f)
            else:
                risk_logs = []
            
            risk_logs.append(log_entry)
            
            with open(risk_log_file, 'w', encoding='utf-8') as f:
                json.dump(risk_logs, f, ensure_ascii=False, indent=2)
    
    def get_session_summary(self) -> str:
        """現在のセッション要約を取得"""
        return self.memory_system.get_session_context()
    
    def update_project_progress(self, completed: List[str] = None, 
                              new_tasks: List[str] = None,
                              focus: str = None) -> None:
        """プロジェクト進捗を更新"""
        self.memory_system.update_project_state(
            completed_tasks=completed,
            new_tasks=new_tasks,
            current_focus=focus
        )
    
    def _prompt_user_intent(self) -> str:
        """ユーザーの意図を確認"""
        print("🎯 今回のセッションの目的を教えてください:")
        print("例: 'バックアップシステムの改善', '新機能の実装', '論文検索システムの拡張'")
        
        intent = input("\n目的: ").strip()
        return intent if intent else "一般的な開発作業"
    
    def _generate_ai_instructions(self, context_guide: str) -> str:
        """AIへの指示書を生成"""
        
        instructions = f"""# 🤖 Cursor AI 行動指針

## 🛡️ 絶対遵守事項

### ❌ 禁止行為
1. **ファイル削除**: ユーザーの明示的確認なしに、いかなるファイルも削除してはいけません
2. **大幅変更**: 既存システムを大きく変更する前に、必ず確認を取ってください
3. **勝手な構築**: ユーザーが要求していない新しいシステムを勝手に作らないでください
4. **設定変更**: 重要な設定ファイルを変更する前に確認してください

### ✅ 必須行動
1. **逐次確認**: 重要な操作前には「〇〇を実行してもよろしいですか？」と確認
2. **文脈保持**: 以下の文脈を常に意識して対応してください
3. **安全第一**: 不明な場合は操作を停止し、ユーザーに確認を求める
4. **記録保持**: 重要な決定や変更は記録に残す

## 🧠 現在のセッション文脈

{context_guide}

## 🔧 作業手順

1. **リクエスト分析**: ユーザーの要求を理解し、リスクを評価
2. **確認要求**: 中〜高リスク操作の場合は確認を取る
3. **段階的実行**: 一度に大きな変更をせず、段階的に進める
4. **結果報告**: 実行した内容を明確に報告
5. **文脈更新**: 新しい情報や決定事項を記録

## 💬 確認フレーズ例

- 「〇〇ファイルを削除しますが、よろしいですか？」
- 「〇〇システムを新規作成します。問題ないでしょうか？」
- 「〇〇の設定を変更します。承認いただけますか？」

---

⚠️ **重要**: この指針に反する行動は一切禁止です。
不明な点がある場合は、必ずユーザーに確認してください。

**作成日時**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return instructions
    
    def _show_detailed_info(self, analysis: Dict[str, Any]) -> None:
        """詳細情報を表示"""
        
        print("\n" + "="*60)
        print("📋 詳細情報")
        print("="*60)
        print(f"メッセージ: {analysis['user_message']}")
        print(f"リスクレベル: {analysis['risk_level']}")
        print(f"検出操作: {', '.join(analysis['risky_operations'])}")
        print(f"分析時刻: {analysis['timestamp']}")
        print("\n💡 推奨事項:")
        
        if analysis['risk_level'] == "high":
            print("- バックアップを確認してから実行")
            print("- 段階的に実行し、各段階で確認")
            print("- 取り消し手順を事前に確認")
        else:
            print("- 実行前に期待される結果を確認")
            print("- 問題が発生した場合の対処法を準備")
        
        print("="*60)


# メイン実行部分
def main():
    """メイン実行関数"""
    
    print("🛡️ Cursor AI Guardian - 起動中...")
    print("AI暴走防止&記憶システム")
    print("="*50)
    
    guardian = CursorAIGuardian()
    
    # 対話モード
    print("\n🎯 新しいセッションを開始します")
    guardian.initialize_session()
    
    print("\n💬 対話モードに入ります")
    print("終了するには 'exit' または 'quit' を入力してください")
    
    while True:
        try:
            user_input = input("\n👤 ユーザー: ").strip()
            
            if user_input.lower() in ['exit', 'quit', '終了']:
                print("👋 セッションを終了します")
                break
            
            if not user_input:
                continue
            
            # リスク分析
            analysis = guardian.analyze_user_request(user_input)
            
            # 確認が必要な場合
            if analysis["requires_confirmation"]:
                approved = guardian.request_user_confirmation(analysis)
                if not approved:
                    continue
            
            # セッションに記録
            guardian.record_session_activity(user_input, "承認済み操作", True)
            
            print(f"✅ '{user_input}' の実行が承認されました")
            print("💡 この内容をCursor AIに伝えて実行してもらってください")
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 中断されました")
            break
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()