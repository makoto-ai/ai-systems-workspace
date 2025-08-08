#!/usr/bin/env python3
"""
🌉 Cursor Session Bridge - セッション間記憶橋渡しシステム
新しいセッション開始時に前回の文脈を自動復元
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
try:
    from cursor_memory_system import CursorMemorySystem
    from cursor_memory_enhanced import CursorEnhancedMemory
except ImportError:
    import sys
    sys.path.insert(0, '.')
    from scripts.cursor_memory_system import CursorMemorySystem
    from scripts.cursor_memory_enhanced import CursorEnhancedMemory

class CursorSessionBridge:
    """セッション間で記憶を橋渡しするシステム"""
    
    def __init__(self):
        self.memory_system = CursorMemorySystem()
        self.enhanced_memory = CursorEnhancedMemory()
        self.session_marker_file = Path(".cursor_session_active")
        self.context_file = Path("CURSOR_CONTEXT_GUIDE.md")
        
    def detect_new_session(self) -> bool:
        """新しいセッションかどうかを検出"""
        
        # セッションマーカーファイルが存在しない場合は新セッション
        if not self.session_marker_file.exists():
            return True
        
        # ファイルの更新時刻を確認（30分以上前なら新セッション扱い）
        try:
            last_modified = datetime.datetime.fromtimestamp(
                self.session_marker_file.stat().st_mtime
            )
            time_diff = datetime.datetime.now() - last_modified
            
            # 30分以上経過していれば新セッション
            return time_diff.total_seconds() > 1800
            
        except Exception:
            return True
    
    def activate_session_memory(self, force_new: bool = False) -> str:
        """セッション記憶を活性化し、文脈ガイドを生成"""
        
        is_new_session = force_new or self.detect_new_session()
        
        if is_new_session:
            print("🔍 新しいセッションを検出しました")
            print("📚 前回の文脈を復元中...")
            
            # 拡張記憶システムから最新の要約を取得
            enhanced_summary = self.enhanced_memory.generate_auto_summary(48)  # 過去48時間
            
            # ワークフロー文脈も取得
            workflow_context = self.enhanced_memory.get_workflow_context(hours=48)
            
            # 新セッション開始
            context_guide = self.memory_system.start_new_session(
                "セッション継続（自動検出）"
            )
            
            # 拡張情報を文脈ガイドに統合
            enhanced_context_guide = self._integrate_enhanced_context(
                context_guide, enhanced_summary, workflow_context
            )
            
            # セッションマーカー更新
            self._update_session_marker()
            
            # 文脈ガイド保存
            self._save_context_guide(enhanced_context_guide)
            
            print("✅ 文脈復元完了！")
            return enhanced_context_guide
        
        else:
            print("🔄 既存セッション継続中")
            # 既存の文脈ガイドを読み込み
            if self.context_file.exists():
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # ファイルがない場合は新規作成
                return self.activate_session_memory(force_new=True)
    
    def update_session_activity(self, activity_description: str) -> None:
        """セッション活動を更新"""
        
        # セッションマーカー更新
        self._update_session_marker()
        
        # 活動をメモリシステムに記録
        self.memory_system.record_conversation(
            activity_description,
            "Activity recorded",
            "session_activity"
        )
        
        # 拡張記憶システムにも記録
        self.enhanced_memory.record_enhanced_conversation(
            activity_description,
            "Activity recorded",
            context_before="Session activity update",
            context_after="Activity logged"
        )
    
    def generate_ai_briefing(self) -> str:
        """新しいAIセッション用のブリーフィングを生成"""
        
        context_guide = self.activate_session_memory()
        
        briefing = f"""# 🤖 AI Assistant Session Briefing

**⚠️ 重要**: このブリーフィングを読んで理解してから対応してください

## 📋 セッション開始指針

### 🛡️ 絶対遵守ルール
1. **削除禁止**: ファイル削除前に必ず確認を取る
2. **変更確認**: 既存システムの変更前に承認を求める
3. **段階実行**: 大きな作業は段階的に進める
4. **記録保持**: 重要な決定は記録する

### 📚 前回からの継続文脈

{context_guide}

---

## 🎯 推奨開始フレーズ

「前回の続きから開始します。以下の文脈を確認し、何か不明な点があれば質問してください。」

## 💬 確認必須フレーズ

- 「〇〇を削除してもよろしいですか？」
- 「〇〇を変更します。問題ないでしょうか？」
- 「〇〇を新規作成します。承認いただけますか？」

---

**生成日時**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ **注意**: このブリーフィングの内容を無視して勝手な操作を行うことは禁止されています。
"""
        
        # ブリーフィングファイル保存
        briefing_file = Path("AI_SESSION_BRIEFING.md")
        with open(briefing_file, 'w', encoding='utf-8') as f:
            f.write(briefing)
        
        return briefing
    
    def create_session_summary(self) -> Dict[str, Any]:
        """現在のセッション要約を作成"""
        
        # 拡張記憶システムからの統計も取得
        workflow_context = self.enhanced_memory.get_workflow_context(hours=24)
        
        summary = {
            "session_id": f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.datetime.now().isoformat(),
            "context_guide": self.memory_system.get_session_context(),
            "active_marker_exists": self.session_marker_file.exists(),
            "context_file_exists": self.context_file.exists(),
            "enhanced_memory_stats": {
                "total_workflows": workflow_context.get('total_workflows', 0),
                "critical_workflows": len(workflow_context.get('critical_workflows', [])),
                "warnings": len(workflow_context.get('warnings', [])),
                "workflow_types": workflow_context.get('workflow_types', [])
            }
        }
        
        return summary
    
    def end_session(self) -> None:
        """セッション終了処理"""
        
        print("🔚 セッション終了処理中...")
        
        # 最終状態を記録
        final_summary = self.create_session_summary()
        
        # セッション終了ログ
        end_log_file = Path("session_end_log.json")
        
        if end_log_file.exists():
            with open(end_log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(final_summary)
        
        with open(end_log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        
        # セッションマーカー削除
        if self.session_marker_file.exists():
            self.session_marker_file.unlink()
        
        print("✅ セッション終了完了")
    
    def _update_session_marker(self) -> None:
        """セッションマーカーファイルを更新"""
        
        marker_data = {
            "last_update": datetime.datetime.now().isoformat(),
            "session_active": True
        }
        
        with open(self.session_marker_file, 'w', encoding='utf-8') as f:
            json.dump(marker_data, f, ensure_ascii=False, indent=2)
    
    def _save_context_guide(self, context_guide: str) -> None:
        """文脈ガイドをファイルに保存"""
        
        enhanced_guide = f"""# 🧠 Cursor 文脈復元ガイド

**最終更新**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{context_guide}

---

## 🚀 作業再開のためのチェックリスト

- [ ] 前回の継続タスクを確認
- [ ] 重要な決定事項を確認
- [ ] 完了済みタスクを確認
- [ ] 安全確認履歴を確認

## 📞 ヘルプが必要な場合

```bash
# セッション状況確認
python scripts/cursor_session_bridge.py status

# 新しいセッション強制開始
python scripts/cursor_session_bridge.py new-session

# セッション終了
python scripts/cursor_session_bridge.py end-session
```

⚠️ **重要**: 削除や大幅変更前には必ず確認を取ってください！
"""
        
        with open(self.context_file, 'w', encoding='utf-8') as f:
            f.write(enhanced_guide)
    
    def _integrate_enhanced_context(self, base_context: str, enhanced_summary: str, 
                                  workflow_context: Dict[str, Any]) -> str:
        """拡張記憶システムの情報を基本文脈に統合"""
        
        enhanced_context = base_context + f"""

## 🔍 拡張記憶システム情報

### 📊 最近の活動要約（48時間）
{enhanced_summary}

### ⚡ ワークフロー状況
- **総ワークフロー数**: {workflow_context.get('total_workflows', 0)}
- **ワークフロータイプ**: {', '.join(workflow_context.get('workflow_types', []))}
- **重要ワークフロー**: {len(workflow_context.get('critical_workflows', []))}件
- **警告**: {len(workflow_context.get('warnings', []))}件

### 🚨 重要な警告
"""
        
        # 警告があれば表示
        warnings = workflow_context.get('warnings', [])
        if warnings:
            for warning in warnings:
                enhanced_context += f"- ⚠️ {warning.get('step_name', '')}: {warning.get('warning', '')}\n"
        else:
            enhanced_context += "現在警告はありません\n"
        
        enhanced_context += f"""
### 🎯 最近の重要ワークフロー
"""
        
        # 重要ワークフローがあれば表示
        critical_workflows = workflow_context.get('critical_workflows', [])
        if critical_workflows:
            for workflow in critical_workflows[-3:]:  # 最新3件
                timestamp = workflow.get('timestamp', '')
                time_part = timestamp.split('T')[1][:5] if 'T' in timestamp else timestamp
                enhanced_context += f"- [{time_part}] {workflow.get('step_name', '')}\n"
        else:
            enhanced_context += "重要ワークフローはありません\n"
        
        enhanced_context += """
---
**🧠 拡張記憶統合**: このセッションでは基本記憶システムと拡張記憶システムが連携して動作しています。
"""
        
        return enhanced_context


# コマンドライン実行部分
def main():
    """メイン実行関数"""
    
    import sys
    
    bridge = CursorSessionBridge()
    
    if len(sys.argv) < 2:
        # デフォルト動作：セッション活性化
        print("🌉 Cursor Session Bridge")
        print("="*40)
        
        briefing = bridge.generate_ai_briefing()
        print("\n✅ AIブリーフィング生成完了")
        print(f"📄 ファイル: AI_SESSION_BRIEFING.md")
        print(f"📄 文脈ガイド: CURSOR_CONTEXT_GUIDE.md")
        
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        # セッション状況確認
        print("📊 セッション状況:")
        summary = bridge.create_session_summary()
        print(f"セッションID: {summary['session_id']}")
        print(f"マーカーファイル: {'✅' if summary['active_marker_exists'] else '❌'}")
        print(f"文脈ファイル: {'✅' if summary['context_file_exists'] else '❌'}")
        
    elif command == "new-session":
        # 新セッション強制開始
        print("🔄 新セッション強制開始...")
        bridge.activate_session_memory(force_new=True)
        bridge.generate_ai_briefing()
        print("✅ 新セッション開始完了")
        
    elif command == "end-session":
        # セッション終了
        bridge.end_session()
        
    elif command == "briefing":
        # AIブリーフィング生成
        briefing = bridge.generate_ai_briefing()
        print("✅ AIブリーフィング生成完了")
        
    else:
        print(f"❌ 不明なコマンド: {command}")
        print("利用可能コマンド: status, new-session, end-session, briefing")


if __name__ == "__main__":
    main()