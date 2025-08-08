#!/usr/bin/env python3
"""
🧠 Cursor Enhanced Memory System - 高精度版記憶システム
現状の基本版から大幅に精度向上した記憶システム
"""

import os
import json
import datetime
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib
try:
    from cursor_memory_system import CursorMemorySystem
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from cursor_memory_system import CursorMemorySystem

class CursorEnhancedMemory(CursorMemorySystem):
    """高精度版Cursor記憶システム"""
    
    def __init__(self, obsidian_vault_path: str = "docs/obsidian-knowledge"):
        super().__init__(obsidian_vault_path)
        
        # 拡張機能用フォルダ
        self.enhanced_dir = self.memory_dir / "enhanced"
        self.enhanced_dir.mkdir(exist_ok=True)
        
        # 詳細記録用
        self.detailed_conversations = self.enhanced_dir / "detailed_conversations"
        self.conversation_patterns = self.enhanced_dir / "conversation_patterns"
        self.auto_summaries = self.enhanced_dir / "auto_summaries"
        self.workflow_memory = self.enhanced_dir / "workflow_memory"
        
        for folder in [self.detailed_conversations, self.conversation_patterns, self.auto_summaries, self.workflow_memory]:
            folder.mkdir(exist_ok=True)
        
        # 重要度判定キーワード
        self.importance_keywords = {
            "critical": [
                "論文検索", "ハルシネーション", "事実確認", "YouTube原稿", 
                "削除禁止", "安全確認", "ワークフロー", "必須フロー"
            ],
            "high": [
                "削除", "delete", "remove", "構築", "build", "create",
                "変更", "change", "modify", "バックアップ", "backup",
                "エラー", "error", "問題", "issue", "解決", "solve",
                "完成", "complete", "実装", "implement"
            ],
            "medium": [
                "確認", "check", "テスト", "test", "実行", "run",
                "設定", "config", "追加", "add", "更新", "update",
                "インストール", "install", "起動", "start"
            ],
            "contextual": [
                "前回", "続き", "引き継ぎ", "記憶", "覚えて", "思い出",
                "なぜ", "どうして", "理由", "原因", "目的", "意図",
                "次に", "今後", "将来", "計画", "予定"
            ]
        }
    
    def record_enhanced_conversation(self, user_message: str, ai_response: str, 
                                   context_before: str = "", context_after: str = "") -> str:
        """拡張版会話記録 - 文脈と重要度を詳細に記録"""
        
        timestamp = datetime.datetime.now()
        conversation_id = hashlib.sha256(f"{timestamp.isoformat()}{user_message[:50]}".encode()).hexdigest()[:8]
        
        # 重要度判定
        importance_level = self._analyze_importance(user_message, ai_response)
        
        # 文脈分析
        context_analysis = self._analyze_context(user_message, ai_response, context_before, context_after)
        
        # 感情・ニュアンス分析
        emotional_context = self._analyze_emotional_context(user_message, ai_response)
        
        # 詳細記録
        detailed_record = {
            "conversation_id": conversation_id,
            "timestamp": timestamp.isoformat(),
            "importance_level": importance_level,
            "context_analysis": context_analysis,
            "emotional_context": emotional_context,
            "conversation": {
                "user_message": user_message,
                "ai_response": ai_response,
                "context_before": context_before,
                "context_after": context_after
            },
            "extracted_entities": self._extract_entities(user_message, ai_response),
            "action_items": self._extract_action_items(user_message, ai_response),
            "questions_raised": self._extract_questions(user_message, ai_response),
            "decisions_made": self._extract_decisions(user_message, ai_response)
        }
        
        # 保存
        detailed_file = self.detailed_conversations / f"{conversation_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_record, f, ensure_ascii=False, indent=2)
        
        # 基本記録も更新
        super().record_conversation(user_message, ai_response, "enhanced")
        
        # パターン学習
        self._update_conversation_patterns(detailed_record)
        
        return conversation_id
    
    def _analyze_importance(self, user_message: str, ai_response: str) -> str:
        """重要度分析"""
        
        text = f"{user_message} {ai_response}".lower()
        
        # 重要度チェック
        critical_count = sum(1 for keyword in self.importance_keywords["critical"] if keyword in text)
        high_count = sum(1 for keyword in self.importance_keywords["high"] if keyword in text)
        medium_count = sum(1 for keyword in self.importance_keywords["medium"] if keyword in text)
        contextual_count = sum(1 for keyword in self.importance_keywords["contextual"] if keyword in text)
        
        if critical_count >= 1:
            return "critical"
        elif high_count >= 2:
            return "critical"
        elif high_count >= 1:
            return "high"
        elif medium_count >= 2 or contextual_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _analyze_context(self, user_message: str, ai_response: str, 
                        context_before: str, context_after: str) -> Dict[str, Any]:
        """文脈分析"""
        
        return {
            "continuation_detected": any(word in user_message.lower() for word in ["続き", "前回", "引き継ぎ"]),
            "question_type": self._classify_question_type(user_message),
            "project_reference": self._extract_project_references(user_message, ai_response),
            "technical_content": self._extract_technical_content(user_message, ai_response),
            "time_references": self._extract_time_references(user_message, ai_response),
            "context_quality": {
                "before_available": bool(context_before.strip()),
                "after_available": bool(context_after.strip()),
                "context_richness": len(context_before.split()) + len(context_after.split())
            }
        }
    
    def _analyze_emotional_context(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """感情・ニュアンス分析"""
        
        user_tone = self._detect_tone(user_message)
        ai_tone = self._detect_tone(ai_response)
        
        return {
            "user_tone": user_tone,
            "ai_tone": ai_tone,
            "uncertainty_detected": any(word in user_message.lower() for word in ["わからない", "不明", "？", "確認"]),
            "satisfaction_indicators": any(word in user_message.lower() for word in ["ありがとう", "助かる", "完璧"]),
            "frustration_indicators": any(word in user_message.lower() for word in ["勘弁", "困る", "怖い", "心配"]),
            "confidence_level": self._assess_confidence_level(user_message, ai_response)
        }
    
    def _extract_entities(self, user_message: str, ai_response: str) -> Dict[str, List[str]]:
        """エンティティ抽出（ファイル名、システム名、技術名など）"""
        
        text = f"{user_message} {ai_response}"
        
        entities = {
            "file_names": re.findall(r'[\w\-\_]+\.(py|md|json|sh|sql|txt)', text),
            "system_names": re.findall(r'([A-Z][a-z]+(?:[A-Z][a-z]+)*(?:システム|System))', text),
            "commands": re.findall(r'`([^`]+)`', text),
            "technologies": re.findall(r'(Python|JavaScript|SQL|Git|Docker|API|REST|JSON)', text),
            "project_names": re.findall(r'(voice-roleplay|paper-research|monitoring)', text)
        }
        
        return {k: list(set(v)) for k, v in entities.items() if v}
    
    def _extract_action_items(self, user_message: str, ai_response: str) -> List[str]:
        """アクションアイテム抽出"""
        
        action_items = []
        
        # 「〜してください」「〜したい」パターン
        action_patterns = [
            r'(.+?)してください',
            r'(.+?)したい',
            r'(.+?)する必要があ',
            r'(.+?)を実行',
            r'(.+?)をテスト'
        ]
        
        text = f"{user_message} {ai_response}"
        for pattern in action_patterns:
            matches = re.findall(pattern, text)
            action_items.extend([match.strip() for match in matches if len(match.strip()) > 5])
        
        return list(set(action_items))
    
    def _extract_questions(self, user_message: str, ai_response: str) -> List[str]:
        """質問抽出"""
        
        questions = []
        
        # 質問パターン
        if '？' in user_message or '?' in user_message:
            questions.append(user_message.strip())
        
        # 「なぜ」「どうして」パターン
        question_starters = ['なぜ', 'どうして', 'どのように', 'いつ', 'どこで', 'だれが']
        for starter in question_starters:
            if starter in user_message.lower():
                questions.append(user_message.strip())
                break
        
        return questions
    
    def _extract_decisions(self, user_message: str, ai_response: str) -> List[str]:
        """決定事項抽出"""
        
        decisions = []
        
        # 決定パターン
        decision_patterns = [
            r'(.+?)に決定',
            r'(.+?)することにし',
            r'(.+?)を採用',
            r'(.+?)で確定'
        ]
        
        text = f"{user_message} {ai_response}"
        for pattern in decision_patterns:
            matches = re.findall(pattern, text)
            decisions.extend([match.strip() for match in matches if len(match.strip()) > 5])
        
        return decisions
    
    def generate_auto_summary(self, timeframe_hours: int = 24) -> str:
        """自動要約生成"""
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=timeframe_hours)
        
        # 期間内の会話収集
        conversations = []
        for file_path in self.detailed_conversations.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                conv_data = json.load(f)
                conv_time = datetime.datetime.fromisoformat(conv_data['timestamp'])
                if conv_time > cutoff_time:
                    conversations.append(conv_data)
        
        if not conversations:
            return "指定期間内に記録された会話はありません。"
        
        # 重要度別分類
        critical_conversations = [c for c in conversations if c['importance_level'] == 'critical']
        high_conversations = [c for c in conversations if c['importance_level'] == 'high']
        
        # エンティティ集計
        all_entities = {}
        all_actions = []
        all_decisions = []
        
        for conv in conversations:
            for entity_type, entities in conv.get('extracted_entities', {}).items():
                if entity_type not in all_entities:
                    all_entities[entity_type] = set()
                all_entities[entity_type].update(entities)
            
            all_actions.extend(conv.get('action_items', []))
            all_decisions.extend(conv.get('decisions_made', []))
        
        # 要約生成
        summary = f"""# 🧠 Enhanced Memory Auto Summary ({timeframe_hours}時間)

**生成時刻**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 統計
- **総会話数**: {len(conversations)}
- **重要度Critical**: {len(critical_conversations)}
- **重要度High**: {len(high_conversations)}

## 🎯 主要な活動
"""
        
        if critical_conversations:
            summary += "\n### 🔴 Critical級の重要事項\n"
            for conv in critical_conversations:
                summary += f"- {conv['conversation']['user_message'][:100]}...\n"
        
        if all_decisions:
            summary += "\n### ✅ 決定事項\n"
            for decision in set(all_decisions):
                summary += f"- {decision}\n"
        
        if all_actions:
            summary += "\n### 📝 アクションアイテム\n"
            for action in set(all_actions):
                summary += f"- {action}\n"
        
        if all_entities:
            summary += "\n### 🏷️ 関連エンティティ\n"
            for entity_type, entities in all_entities.items():
                if entities:
                    summary += f"**{entity_type}**: {', '.join(list(entities))}\n"
        
        # 要約ファイル保存
        summary_file = self.auto_summaries / f"summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        return summary
    
    def _classify_question_type(self, message: str) -> str:
        """質問タイプ分類"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["なぜ", "どうして", "理由"]):
            return "why_question"
        elif any(word in message_lower for word in ["どのように", "やり方", "方法"]):
            return "how_question"
        elif any(word in message_lower for word in ["いつ", "タイミング"]):
            return "when_question"
        elif any(word in message_lower for word in ["どこ", "場所"]):
            return "where_question"
        elif "？" in message or "?" in message:
            return "general_question"
        else:
            return "statement"
    
    def _extract_project_references(self, user_message: str, ai_response: str) -> List[str]:
        """プロジェクト参照抽出"""
        text = f"{user_message} {ai_response}"
        
        projects = []
        project_patterns = [
            r'(voice-roleplay[^s\s]*)',
            r'(paper-research[^s\s]*)',
            r'(monitoring[^s\s]*)',
            r'(cursor[^s\s]*)',
            r'(obsidian[^s\s]*)'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            projects.extend(matches)
        
        return list(set(projects))
    
    def _extract_technical_content(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """技術的内容抽出"""
        text = f"{user_message} {ai_response}"
        
        return {
            "code_mentioned": bool(re.search(r'`[^`]+`', text)),
            "file_operations": bool(any(word in text.lower() for word in ["削除", "作成", "変更", "移動"])),
            "system_operations": bool(any(word in text.lower() for word in ["実行", "起動", "停止", "再起動"])),
            "data_operations": bool(any(word in text.lower() for word in ["保存", "読み込み", "バックアップ", "復元"]))
        }
    
    def _extract_time_references(self, user_message: str, ai_response: str) -> List[str]:
        """時間参照抽出"""
        text = f"{user_message} {ai_response}"
        
        time_refs = []
        time_patterns = [
            r'(前回|今回|次回)',
            r'(昨日|今日|明日)',
            r'(\d+日前|\d+時間前)',
            r'(先週|今週|来週)',
            r'(最近|最後|最新)'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            time_refs.extend(matches)
        
        return list(set(time_refs))
    
    def _detect_tone(self, message: str) -> str:
        """トーン検出"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["ありがとう", "感謝", "助かる", "素晴らしい"]):
            return "positive"
        elif any(word in message_lower for word in ["困る", "怖い", "心配", "勘弁", "不安"]):
            return "negative"
        elif any(word in message_lower for word in ["？", "?", "わからない", "確認"]):
            return "questioning"
        elif any(word in message_lower for word in ["！", "!", "すごい", "完璧"]):
            return "excited"
        else:
            return "neutral"
    
    def _assess_confidence_level(self, user_message: str, ai_response: str) -> str:
        """信頼度レベル評価"""
        ai_lower = ai_response.lower()
        
        if any(word in ai_lower for word in ["確実", "間違いなく", "完璧", "100%"]):
            return "high"
        elif any(word in ai_lower for word in ["おそらく", "たぶん", "可能性", "思います"]):
            return "medium"
        elif any(word in ai_lower for word in ["わからない", "不明", "確認が必要"]):
            return "low"
        else:
            return "medium"
    
    def _update_conversation_patterns(self, conversation_record: Dict[str, Any]) -> None:
        """会話パターン学習"""
        
        patterns_file = self.conversation_patterns / "patterns.json"
        
        if patterns_file.exists():
            with open(patterns_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
        else:
            patterns = {
                "common_questions": {},
                "user_preferences": {},
                "interaction_patterns": {}
            }
        
        # パターン更新ロジック（簡略版）
        question_type = conversation_record['context_analysis']['question_type']
        if question_type not in patterns["common_questions"]:
            patterns["common_questions"][question_type] = 0
        patterns["common_questions"][question_type] += 1
        
        # 保存
        with open(patterns_file, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, ensure_ascii=False, indent=2)
    
    def record_workflow_step(self, step_name: str, step_details: Dict[str, Any]) -> str:
        """ワークフロー記憶機能 - 論文検索→原稿作成等の重要フローを記録"""
        
        timestamp = datetime.datetime.now()
        workflow_id = hashlib.sha256(f"{timestamp.isoformat()}{step_name}".encode()).hexdigest()[:8]
        
        workflow_record = {
            "workflow_id": workflow_id,
            "step_name": step_name,
            "timestamp": timestamp.isoformat(),
            "details": step_details,
            "workflow_type": self._classify_workflow_type(step_name, step_details)
        }
        
        # 重要ワークフロー判定
        if any(keyword in step_name.lower() for keyword in ["論文検索", "事実確認", "原稿作成", "youtube"]):
            workflow_record["importance"] = "critical"
            
            # 論文検索→原稿作成フローの確認
            if "原稿作成" in step_name and not self._check_paper_search_prerequisite():
                workflow_record["warning"] = "論文検索システム未実行 - ハルシネーションリスク"
        
        # 保存
        workflow_file = self.workflow_memory / f"workflow_{workflow_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(workflow_record, f, ensure_ascii=False, indent=2)
        
        return workflow_id
    
    def _classify_workflow_type(self, step_name: str, step_details: Dict[str, Any]) -> str:
        """ワークフロータイプ分類"""
        
        step_lower = step_name.lower()
        
        if any(keyword in step_lower for keyword in ["論文検索", "research", "paper"]):
            return "research_workflow"
        elif any(keyword in step_lower for keyword in ["原稿作成", "youtube", "script"]):
            return "content_creation_workflow"
        elif any(keyword in step_lower for keyword in ["事実確認", "fact", "verify"]):
            return "verification_workflow"
        elif any(keyword in step_lower for keyword in ["システム構築", "system", "build"]):
            return "system_workflow"
        else:
            return "general_workflow"
    
    def _check_paper_search_prerequisite(self) -> bool:
        """論文検索システム実行済みかチェック"""
        
        # 過去24時間以内の論文検索ワークフロー確認
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=24)
        
        for workflow_file in self.workflow_memory.glob("workflow_*.json"):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                    workflow_time = datetime.datetime.fromisoformat(workflow_data['timestamp'])
                    
                    if (workflow_time > cutoff_time and 
                        workflow_data.get('workflow_type') == 'research_workflow'):
                        return True
            except:
                continue
        
        return False
    
    def get_workflow_context(self, workflow_type: str = None, hours: int = 24) -> Dict[str, Any]:
        """ワークフロー文脈取得"""
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        workflows = []
        
        for workflow_file in self.workflow_memory.glob("workflow_*.json"):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                    workflow_time = datetime.datetime.fromisoformat(workflow_data['timestamp'])
                    
                    if workflow_time > cutoff_time:
                        if workflow_type is None or workflow_data.get('workflow_type') == workflow_type:
                            workflows.append(workflow_data)
            except:
                continue
        
        return {
            "total_workflows": len(workflows),
            "workflow_types": list(set(w.get('workflow_type', 'unknown') for w in workflows)),
            "critical_workflows": [w for w in workflows if w.get('importance') == 'critical'],
            "warnings": [w for w in workflows if 'warning' in w],
            "recent_workflows": sorted(workflows, key=lambda x: x['timestamp'], reverse=True)[:5]
        }


# 使用例
if __name__ == "__main__":
    # 高精度版テスト
    enhanced_memory = CursorEnhancedMemory()
    
    # 拡張記録テスト
    conversation_id = enhanced_memory.record_enhanced_conversation(
        "この記憶システムの精度をもっと上げられるの？",
        "はい！確実に精度を上げられます。現状は基本版で、まだまだ改善の余地があります。",
        context_before="バックアップシステム100%復旧能力確認後",
        context_after="具体的な改善策の提案へ"
    )
    
    print(f"✅ 拡張記録完了: {conversation_id}")
    
    # 自動要約生成テスト
    summary = enhanced_memory.generate_auto_summary(1)  # 過去1時間
    print("\n📋 自動要約:")
    print(summary)