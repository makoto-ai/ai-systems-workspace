#!/usr/bin/env python3
"""
🧠 Cursor完全記憶&安全確認システム
セッション間での完全文脈保持とAI暴走防止機能
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

class CursorMemorySystem:
    """Cursorの記憶を完全管理するシステム"""
    
    def __init__(self, obsidian_vault_path: str = "docs/obsidian-knowledge"):
        self.vault_path = Path(obsidian_vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
        
        # 記憶システム専用フォルダ
        self.memory_dir = self.vault_path / "ai-memory"
        self.memory_dir.mkdir(exist_ok=True)
        
        # サブフォルダ作成
        self.folders = {
            "sessions": self.memory_dir / "sessions",  # 会話履歴
            "context": self.memory_dir / "context",    # プロジェクト文脈
            "safety": self.memory_dir / "safety",      # 安全確認ログ
            "tasks": self.memory_dir / "tasks",        # 継続タスク
            "backups": self.memory_dir / "backups"     # 状態バックアップ
        }
        
        for folder in self.folders.values():
            folder.mkdir(exist_ok=True)
        
        # 現在のセッション状態ファイル
        self.current_session_file = self.memory_dir / "current_session.json"
        self.project_state_file = self.memory_dir / "project_state.json"
        self.conversation_history_file = self.memory_dir / "conversation_history.md"
    
    def start_new_session(self, user_intent: str = "新しい開発セッション") -> str:
        """新しいセッションを開始し、前回の文脈を読み込み"""
        
        session_id = f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 前回のセッション終了処理
        self._finalize_previous_session()
        
        # 現在のプロジェクト状態読み込み
        project_context = self._load_project_context()
        
        # 最近の会話履歴読み込み
        recent_conversations = self._load_recent_conversations()
        
        # 継続中のタスク読み込み
        ongoing_tasks = self._load_ongoing_tasks()
        
        # 総会話数を計算（既存セッション + 拡張記憶システム）
        total_conversation_count = self._calculate_total_conversations()
        
        # 新セッション初期化
        session_data = {
            "session_id": session_id,
            "start_time": datetime.datetime.now().isoformat(),
            "user_intent": user_intent,
            "project_context": project_context,
            "recent_conversations": recent_conversations,
            "ongoing_tasks": ongoing_tasks,
            "conversation_count": total_conversation_count,
            "session_conversation_count": 0,  # このセッション内の会話数
            "safety_confirmations": []
        }
        
        # セッション状態保存
        with open(self.current_session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # 文脈復元ガイド生成
        context_guide = self._generate_context_guide(session_data)
        
        return context_guide
    
    def record_conversation(self, user_message: str, ai_response: str, 
                          conversation_type: str = "development") -> None:
        """会話を記録し、文脈を更新"""
        
        timestamp = datetime.datetime.now().isoformat()
        conversation_id = hashlib.sha256(f"{timestamp}{user_message[:50]}".encode()).hexdigest()[:8]
        
        # 現在のセッション読み込み
        if self.current_session_file.exists():
            with open(self.current_session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        else:
            session_data = self.start_new_session("継続セッション")
        
        # 会話記録
        conversation_record = {
            "conversation_id": conversation_id,
            "timestamp": timestamp,
            "type": conversation_type,
            "user_message": user_message,
            "ai_response": ai_response,
            "context_hash": self._generate_context_hash(user_message, ai_response)
        }
        
        # Markdownファイルに追記
        with open(self.conversation_history_file, 'a', encoding='utf-8') as f:
            f.write(f"\n\n## 💬 {conversation_id} ({timestamp})\n\n")
            f.write(f"### 👤 ユーザー\n{user_message}\n\n")
            f.write(f"### 🤖 AI\n{ai_response}\n\n")
            f.write(f"**タイプ**: {conversation_type}\n\n")
        
        # セッション更新
        session_data["conversation_count"] += 1
        session_data["session_conversation_count"] = session_data.get("session_conversation_count", 0) + 1
        session_data["last_conversation"] = conversation_record
        
        with open(self.current_session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # 重要度判定と自動保存
        if self._is_important_conversation(user_message, ai_response):
            self._save_important_conversation(conversation_record)
    
    def request_safety_confirmation(self, operation: str, details: str, 
                                  risk_level: str = "medium") -> Dict[str, Any]:
        """重要操作前の安全確認を要求"""
        
        confirmation_id = f"safety_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        confirmation_data = {
            "confirmation_id": confirmation_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "operation": operation,
            "details": details,
            "risk_level": risk_level,
            "requires_user_approval": True,
            "approved": False
        }
        
        # 安全確認ログ保存
        safety_log_file = self.folders["safety"] / f"{confirmation_id}.json"
        with open(safety_log_file, 'w', encoding='utf-8') as f:
            json.dump(confirmation_data, f, ensure_ascii=False, indent=2)
        
        # 確認メッセージ生成
        confirmation_message = f"""
🚨 **安全確認が必要です**

**操作**: {operation}
**詳細**: {details}
**リスクレベル**: {risk_level}

この操作を実行してもよろしいですか？

✅ **承認**: 操作を実行
❌ **拒否**: 操作をキャンセル
🔍 **詳細**: より詳しい情報を確認

**確認ID**: {confirmation_id}
"""
        
        return {
            "confirmation_id": confirmation_id,
            "message": confirmation_message,
            "requires_approval": True
        }
    
    def process_safety_approval(self, confirmation_id: str, approved: bool, 
                              user_comment: str = "") -> bool:
        """安全確認の承認・拒否を処理"""
        
        safety_log_file = self.folders["safety"] / f"{confirmation_id}.json"
        
        if not safety_log_file.exists():
            return False
        
        with open(safety_log_file, 'r', encoding='utf-8') as f:
            confirmation_data = json.load(f)
        
        confirmation_data["approved"] = approved
        confirmation_data["user_comment"] = user_comment
        confirmation_data["decision_time"] = datetime.datetime.now().isoformat()
        
        with open(safety_log_file, 'w', encoding='utf-8') as f:
            json.dump(confirmation_data, f, ensure_ascii=False, indent=2)
        
        # セッションに記録
        if self.current_session_file.exists():
            with open(self.current_session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            session_data["safety_confirmations"].append({
                "confirmation_id": confirmation_id,
                "operation": confirmation_data["operation"],
                "approved": approved,
                "timestamp": confirmation_data["decision_time"]
            })
            
            with open(self.current_session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        return approved
    
    def update_project_state(self, completed_tasks: List[str] = None, 
                           new_tasks: List[str] = None,
                           current_focus: str = None,
                           important_decisions: List[str] = None) -> None:
        """プロジェクト状態を更新"""
        
        # 現在の状態読み込み
        if self.project_state_file.exists():
            with open(self.project_state_file, 'r', encoding='utf-8') as f:
                project_state = json.load(f)
        else:
            project_state = {
                "created": datetime.datetime.now().isoformat(),
                "completed_tasks": [],
                "ongoing_tasks": [],
                "important_decisions": [],
                "current_focus": None
            }
        
        # 状態更新
        if completed_tasks:
            project_state["completed_tasks"].extend(completed_tasks)
            # 完了タスクを進行中から削除
            for task in completed_tasks:
                if task in project_state["ongoing_tasks"]:
                    project_state["ongoing_tasks"].remove(task)
        
        if new_tasks:
            project_state["ongoing_tasks"].extend(new_tasks)
        
        if current_focus:
            project_state["current_focus"] = current_focus
        
        if important_decisions:
            project_state["important_decisions"].extend(important_decisions)
        
        project_state["last_updated"] = datetime.datetime.now().isoformat()
        
        # 保存
        with open(self.project_state_file, 'w', encoding='utf-8') as f:
            json.dump(project_state, f, ensure_ascii=False, indent=2)
    
    def get_session_context(self) -> str:
        """現在のセッション文脈を取得"""
        
        if not self.current_session_file.exists():
            return "❌ アクティブなセッションがありません。新しいセッションを開始してください。"
        
        with open(self.current_session_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        return self._generate_context_guide(session_data)
    
    def _generate_context_guide(self, session_data: Dict[str, Any]) -> str:
        """文脈復元ガイドを生成"""
        
        guide = f"""
🧠 **Cursor記憶システム - セッション文脈**

## 📋 現在のセッション
- **セッションID**: {session_data.get('session_id')}
- **開始時刻**: {session_data.get('start_time')}
- **ユーザー意図**: {session_data.get('user_intent')}
- **総会話数**: {session_data.get('conversation_count', 0)}
- **このセッション**: {session_data.get('session_conversation_count', 0)}回

## 🎯 現在のフォーカス
{session_data.get('project_context', {}).get('current_focus', '設定されていません')}

## 📝 継続中のタスク
"""
        
        ongoing_tasks = session_data.get('ongoing_tasks', [])
        if ongoing_tasks:
            for i, task in enumerate(ongoing_tasks, 1):
                guide += f"{i}. {task}\n"
        else:
            guide += "現在継続中のタスクはありません\n"
        
        guide += f"""
## ✅ 最近完了したタスク
"""
        
        completed_tasks = session_data.get('project_context', {}).get('completed_tasks', [])
        recent_completed = completed_tasks[-5:] if completed_tasks else []
        if recent_completed:
            for task in recent_completed:
                guide += f"- {task}\n"
        else:
            guide += "最近完了したタスクはありません\n"
        
        guide += f"""
## 🔒 安全確認履歴
"""
        
        safety_confirmations = session_data.get('safety_confirmations', [])
        if safety_confirmations:
            for conf in safety_confirmations[-3:]:  # 最新3件
                status = "✅ 承認" if conf["approved"] else "❌ 拒否"
                guide += f"- {conf['operation']}: {status}\n"
        else:
            guide += "安全確認履歴はありません\n"
        
        guide += f"""
## 💬 最近の会話要約
"""
        
        recent_conversations = session_data.get('recent_conversations', [])
        if recent_conversations:
            for conv in recent_conversations[-5:]:  # 最新5件に増加
                importance_indicator = ""
                if conv.get('importance') == 'critical':
                    importance_indicator = " 🔴"
                elif conv.get('importance') == 'high':
                    importance_indicator = " 🟡"
                
                timestamp = conv.get('timestamp', '')
                if 'T' in timestamp:
                    # ISO形式の場合、時刻部分のみ抽出
                    time_part = timestamp.split('T')[1][:5] if 'T' in timestamp else timestamp
                else:
                    time_part = timestamp
                
                guide += f"- [{time_part}]{importance_indicator} {conv.get('summary', '')[:80]}...\n"
        else:
            guide += "最近の会話履歴はありません\n"
        
        guide += f"""
---
⚠️ **重要**: このガイドを参考に、前回までの文脈を理解した上で対応してください。
勝手に削除や大幅変更を行わず、必ず確認を取ってください。
"""
        
        return guide
    
    def _load_project_context(self) -> Dict[str, Any]:
        """プロジェクト文脈を読み込み"""
        if self.project_state_file.exists():
            with open(self.project_state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_recent_conversations(self) -> List[Dict[str, Any]]:
        """最近の会話履歴を読み込み"""
        conversations = []
        
        # Markdownファイルから会話履歴を読み込み
        if self.conversation_history_file.exists():
            try:
                with open(self.conversation_history_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 会話IDを検索して最新の会話を抽出
                import re
                conversation_pattern = r'## 💬 ([a-f0-9]{8}) \((.*?)\)'
                matches = re.findall(conversation_pattern, content)
                
                # 最新の5件を取得
                for conv_id, timestamp in matches[-5:]:
                    conversations.append({
                        "conversation_id": conv_id,
                        "timestamp": timestamp,
                        "summary": f"会話 {conv_id}"
                    })
            except Exception as e:
                print(f"会話履歴読み込みエラー: {e}")
        
        # 拡張記憶システムからも読み込み
        enhanced_dir = self.memory_dir / "enhanced" / "detailed_conversations"
        if enhanced_dir.exists():
            try:
                import json
                conversation_files = list(enhanced_dir.glob("*.json"))
                # 最新の5件を追加
                for conv_file in sorted(conversation_files, key=lambda x: x.stat().st_mtime)[-5:]:
                    with open(conv_file, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                    
                    conversations.append({
                        "conversation_id": conv_data.get("conversation_id"),
                        "timestamp": conv_data.get("timestamp"),
                        "summary": conv_data["conversation"]["user_message"][:100],
                        "importance": conv_data.get("importance_level", "low")
                    })
            except Exception as e:
                print(f"拡張記憶読み込みエラー: {e}")
        
        return conversations[-10:]  # 最新10件まで
    
    def _calculate_total_conversations(self) -> int:
        """総会話数を計算（全セッション + 拡張記憶システム）"""
        total_count = 0
        
        # 過去のセッションファイルから会話数を集計
        sessions_dir = self.folders["sessions"]
        if sessions_dir.exists():
            try:
                for session_file in sessions_dir.glob("*.json"):
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    total_count += session_data.get('conversation_count', 0)
            except Exception as e:
                print(f"セッション履歴読み込みエラー: {e}")
        
        # 拡張記憶システムからの会話数を追加
        enhanced_dir = self.memory_dir / "enhanced" / "detailed_conversations"
        if enhanced_dir.exists():
            try:
                conversation_files = list(enhanced_dir.glob("*.json"))
                total_count += len(conversation_files)
            except Exception as e:
                print(f"拡張記憶カウントエラー: {e}")
        
        # Markdownファイルからも会話数をカウント
        if self.conversation_history_file.exists():
            try:
                with open(self.conversation_history_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                import re
                conversation_pattern = r'## 💬 ([a-f0-9]{8})'
                matches = re.findall(conversation_pattern, content)
                total_count += len(matches)
            except Exception as e:
                print(f"Markdown会話カウントエラー: {e}")
        
        return total_count
    
    def _load_ongoing_tasks(self) -> List[str]:
        """継続中のタスクを読み込み"""
        project_context = self._load_project_context()
        return project_context.get('ongoing_tasks', [])
    
    def _finalize_previous_session(self) -> None:
        """前回のセッションを終了処理"""
        if self.current_session_file.exists():
            with open(self.current_session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # セッション終了時刻記録
            session_data["end_time"] = datetime.datetime.now().isoformat()
            
            # 過去セッションとして保存
            session_file = self.folders["sessions"] / f"{session_data['session_id']}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    def _generate_context_hash(self, user_message: str, ai_response: str) -> str:
        """文脈のハッシュを生成"""
        content = f"{user_message}{ai_response}"
        return hashlib.sha256(content.encode()).hexdigest()[:8]
    
    def _is_important_conversation(self, user_message: str, ai_response: str) -> bool:
        """重要な会話かどうかを判定"""
        important_keywords = [
            "削除", "delete", "remove", "構築", "実装", "作成", "create",
            "変更", "修正", "fix", "update", "バックアップ", "backup"
        ]
        
        text = f"{user_message} {ai_response}".lower()
        return any(keyword in text for keyword in important_keywords)
    
    def _save_important_conversation(self, conversation_record: Dict[str, Any]) -> None:
        """重要な会話を別途保存"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        important_file = self.folders["backups"] / f"important_conversation_{timestamp}.json"
        
        with open(important_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_record, f, ensure_ascii=False, indent=2)


# 使用例とテスト
if __name__ == "__main__":
    # テスト実行
    memory_system = CursorMemorySystem()
    
    # 新セッション開始
    context_guide = memory_system.start_new_session("論文検索システムの機能拡張")
    print("🧠 新セッション開始")
    print(context_guide)
    
    # 会話記録テスト
    memory_system.record_conversation(
        "バックアップシステムを改善したい",
        "バックアップシステムの改善を行います。安全確認が必要です。",
        "development"
    )
    
    # 安全確認テスト
    confirmation = memory_system.request_safety_confirmation(
        "既存ファイルの削除",
        "不要なバックアップファイルを削除します",
        "high"
    )
    print("\n🚨 安全確認:")
    print(confirmation["message"])
    
    # プロジェクト状態更新テスト
    memory_system.update_project_state(
        completed_tasks=["バックアップシステム構築"],
        new_tasks=["安全確認システム実装"],
        current_focus="Cursor記憶システム開発"
    )
    
    print("\n✅ テスト完了!")