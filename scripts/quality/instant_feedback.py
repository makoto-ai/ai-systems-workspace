#!/usr/bin/env python3
"""
⚡ Phase 3: 即座フィードバックシステム
===============================

開発者にリアルタイムで品質情報とフィードバックを提供するシステム

主要機能:
- 即座の視覚的フィードバック
- 品質スコアのリアルタイム表示
- 改善提案の即座表示
- 非侵入的通知システム
- カスタマイズ可能な表示設定
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
from dataclasses import dataclass
import tempfile


@dataclass
class FeedbackMessage:
    """フィードバックメッセージクラス"""
    level: str  # "info", "warning", "error", "success"
    title: str
    message: str
    file_path: str
    score: float
    suggestions: List[str]
    timestamp: datetime
    duration: int = 5  # 表示秒数


class VisualFeedback:
    """視覚的フィードバッククラス"""
    
    def __init__(self):
        self.colors = {
            "reset": "\033[0m",
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "purple": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "bold": "\033[1m",
            "underline": "\033[4m"
        }
        
        self.icons = {
            "success": "✅",
            "info": "ℹ️ ",
            "warning": "⚠️ ",
            "error": "❌",
            "score": "📊",
            "suggestion": "💡",
            "time": "⏰",
            "file": "📄"
        }
    
    def colorize(self, text: str, color: str) -> str:
        """テキストに色を付ける"""
        if color in self.colors:
            return f"{self.colors[color]}{text}{self.colors['reset']}"
        return text
    
    def create_progress_bar(self, score: float, width: int = 20) -> str:
        """品質スコアのプログレスバー作成"""
        filled = int(score * width)
        bar = "█" * filled + "▒" * (width - filled)
        
        if score >= 0.8:
            color = "green"
        elif score >= 0.6:
            color = "yellow"
        else:
            color = "red"
        
        return self.colorize(bar, color)
    
    def create_score_badge(self, score: float) -> str:
        """スコアバッジ作成"""
        percentage = int(score * 100)
        
        if score >= 0.8:
            return self.colorize(f"🟢 {percentage}%", "green")
        elif score >= 0.6:
            return self.colorize(f"🟡 {percentage}%", "yellow")
        else:
            return self.colorize(f"🔴 {percentage}%", "red")
    
    def format_file_name(self, file_path: str, max_length: int = 30) -> str:
        """ファイル名を整形"""
        file_name = Path(file_path).name
        if len(file_name) > max_length:
            file_name = "..." + file_name[-(max_length-3):]
        return self.colorize(file_name, "cyan")


class NotificationSystem:
    """通知システムクラス"""
    
    def __init__(self):
        self.notification_history = []
        self.max_history = 50
    
    def send_desktop_notification(self, title: str, message: str, level: str = "info"):
        """デスクトップ通知送信"""
        try:
            # macOS notification
            if sys.platform == "darwin":
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "{message}" with title "{title}"'
                ], check=False)
            
            # Linux notification
            elif sys.platform == "linux":
                subprocess.run([
                    "notify-send", title, message
                ], check=False)
            
            # Windows notification (if pywin32 available)
            elif sys.platform == "win32":
                try:
                    import win10toast
                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                except ImportError:
                    pass
            
        except Exception as e:
            # 通知失敗は無視（開発の邪魔にならないように）
            pass
    
    def log_notification(self, notification: Dict[str, Any]):
        """通知履歴記録"""
        self.notification_history.append(notification)
        
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]


class InstantFeedbackEngine:
    """即座フィードバックエンジン"""
    
    def __init__(self):
        self.visual = VisualFeedback()
        self.notifications = NotificationSystem()
        self.feedback_queue = []
        self.settings = self._load_settings()
        self.is_running = False
    
    def _load_settings(self) -> Dict[str, Any]:
        """設定読み込み"""
        default_settings = {
            "show_desktop_notifications": True,
            "show_score_bar": True,
            "show_suggestions": True,
            "notification_threshold": 0.7,  # この以下でデスクトップ通知
            "max_suggestions": 3,
            "feedback_duration": 5,
            "quiet_mode": False
        }
        
        try:
            settings_path = "out/feedback_settings.json"
            if os.path.exists(settings_path):
                with open(settings_path) as f:
                    user_settings = json.load(f)
                    default_settings.update(user_settings)
        except:
            pass
        
        return default_settings
    
    def process_quality_feedback(self, file_path: str, score: float, issues: List[str] = None, 
                                suggestions: List[str] = None) -> None:
        """品質フィードバック処理"""
        issues = issues or []
        suggestions = suggestions or []
        
        # フィードバックレベル決定
        level = self._determine_feedback_level(score)
        
        # フィードバックメッセージ作成
        feedback = FeedbackMessage(
            level=level,
            title=self._create_title(file_path, score, level),
            message=self._create_message(score, issues),
            file_path=file_path,
            score=score,
            suggestions=suggestions,
            timestamp=datetime.now(),
            duration=self.settings["feedback_duration"]
        )
        
        # フィードバック表示
        self._display_feedback(feedback)
        
        # デスクトップ通知（必要に応じて）
        if (self.settings["show_desktop_notifications"] and 
            score < self.settings["notification_threshold"]):
            self._send_notification(feedback)
        
        # 履歴記録
        self._record_feedback(feedback)
    
    def _determine_feedback_level(self, score: float) -> str:
        """フィードバックレベル判定"""
        if score >= 0.8:
            return "success"
        elif score >= 0.6:
            return "warning"
        else:
            return "error"
    
    def _create_title(self, file_path: str, score: float, level: str) -> str:
        """タイトル作成"""
        file_name = Path(file_path).name
        
        if level == "success":
            return f"✅ High Quality: {file_name}"
        elif level == "warning":
            return f"⚠️  Quality Check: {file_name}"
        else:
            return f"❌ Quality Issue: {file_name}"
    
    def _create_message(self, score: float, issues: List[str]) -> str:
        """メッセージ作成"""
        message_parts = [f"Quality Score: {score:.2f}"]
        
        if issues:
            top_issues = issues[:3]  # 上位3つのみ
            message_parts.extend([f"• {issue}" for issue in top_issues])
        
        return "\\n".join(message_parts)
    
    def _display_feedback(self, feedback: FeedbackMessage):
        """フィードバック表示"""
        if self.settings["quiet_mode"]:
            return
        
        print()  # 空行
        print("=" * 60)
        
        # ヘッダー
        file_display = self.visual.format_file_name(feedback.file_path)
        score_badge = self.visual.create_score_badge(feedback.score)
        timestamp = feedback.timestamp.strftime("%H:%M:%S")
        
        print(f"📄 {file_display} | {score_badge} | ⏰ {timestamp}")
        
        # スコアバー（設定で有効の場合）
        if self.settings["show_score_bar"]:
            score_bar = self.visual.create_progress_bar(feedback.score)
            print(f"📊 Quality: {score_bar} ({feedback.score:.2f})")
        
        # 詳細メッセージ
        if feedback.message:
            print(f"📋 Details:")
            for line in feedback.message.split("\\n"):
                if line.strip():
                    print(f"   {line}")
        
        # 提案（設定で有効の場合）
        if (self.settings["show_suggestions"] and feedback.suggestions):
            print(f"💡 Suggestions:")
            max_suggestions = self.settings["max_suggestions"]
            for suggestion in feedback.suggestions[:max_suggestions]:
                print(f"   • {suggestion}")
        
        print("=" * 60)
        print()  # 空行
    
    def _send_notification(self, feedback: FeedbackMessage):
        """デスクトップ通知送信"""
        title = feedback.title
        message = f"Score: {feedback.score:.2f}"
        
        if feedback.suggestions:
            message += f"\\n{feedback.suggestions[0]}"  # 最初の提案のみ
        
        self.notifications.send_desktop_notification(
            title, message, feedback.level
        )
    
    def _record_feedback(self, feedback: FeedbackMessage):
        """フィードバック記録"""
        record = {
            "timestamp": feedback.timestamp.isoformat(),
            "file": feedback.file_path,
            "score": feedback.score,
            "level": feedback.level,
            "message": feedback.message,
            "suggestions": feedback.suggestions
        }
        
        # 履歴ファイルに追加
        try:
            os.makedirs("out", exist_ok=True)
            with open("out/feedback_history.json", "a") as f:
                f.write(json.dumps(record) + "\\n")
        except:
            pass
        
        # 通知システムに記録
        self.notifications.log_notification(record)
    
    def create_quality_summary(self) -> Dict[str, Any]:
        """品質サマリー作成"""
        try:
            # 最近のフィードバック履歴を読み込み
            history = []
            if os.path.exists("out/feedback_history.json"):
                with open("out/feedback_history.json") as f:
                    for line in f:
                        if line.strip():
                            history.append(json.loads(line))
            
            # 直近10件で統計計算
            recent = history[-10:] if len(history) >= 10 else history
            
            if not recent:
                return {"message": "No recent feedback data"}
            
            scores = [f["score"] for f in recent]
            avg_score = sum(scores) / len(scores)
            
            level_counts = {}
            for f in recent:
                level = f["level"]
                level_counts[level] = level_counts.get(level, 0) + 1
            
            return {
                "total_feedback": len(history),
                "recent_count": len(recent),
                "average_score": avg_score,
                "level_distribution": level_counts,
                "last_feedback": recent[-1]["timestamp"] if recent else None,
                "trend": "improving" if len(recent) >= 2 and recent[-1]["score"] > recent[-2]["score"] else "stable"
            }
            
        except Exception as e:
            return {"error": f"Summary creation failed: {e}"}
    
    def display_summary(self):
        """サマリー表示"""
        summary = self.create_quality_summary()
        
        print("📊 Quality Feedback Summary")
        print("=" * 40)
        
        if "error" in summary:
            print(f"❌ {summary['error']}")
            return
        
        if "message" in summary:
            print(f"ℹ️  {summary['message']}")
            return
        
        print(f"📈 Total Feedback: {summary['total_feedback']}")
        print(f"🔄 Recent Items: {summary['recent_count']}")
        print(f"📊 Average Score: {summary['average_score']:.2f}")
        print(f"📅 Last Update: {summary['last_feedback']}")
        print(f"📈 Trend: {summary['trend']}")
        
        if summary['level_distribution']:
            print("📋 Level Distribution:")
            for level, count in summary['level_distribution'].items():
                print(f"   {level}: {count}")
        
        print("=" * 40)


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="⚡ Instant Feedback System")
    parser.add_argument("--file", "-f", help="File to analyze and provide feedback")
    parser.add_argument("--score", "-s", type=float, default=0.75, help="Quality score")
    parser.add_argument("--issues", nargs="*", help="List of issues")
    parser.add_argument("--suggestions", nargs="*", help="List of suggestions") 
    parser.add_argument("--summary", action="store_true", help="Show feedback summary")
    parser.add_argument("--test", action="store_true", help="Run test mode")
    
    args = parser.parse_args()
    
    feedback_engine = InstantFeedbackEngine()
    
    if args.summary:
        # サマリー表示
        feedback_engine.display_summary()
        
    elif args.test:
        # テストモード
        print("🧪 Instant Feedback Test Mode")
        print("=" * 40)
        
        # さまざまなスコアでテスト
        test_cases = [
            {"score": 0.9, "level": "success", "file": "high_quality.py"},
            {"score": 0.7, "level": "warning", "file": "medium_quality.py"}, 
            {"score": 0.4, "level": "error", "file": "low_quality.py"}
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\\n--- Test Case {i} ---")
            feedback_engine.process_quality_feedback(
                file_path=test_case["file"],
                score=test_case["score"],
                issues=[f"Issue {i} for {test_case['level']} case"],
                suggestions=[f"Fix suggestion {i}", f"Improvement tip {i}"]
            )
            time.sleep(1)  # 表示間隔
        
        print("\\n✅ Test completed!")
        
    elif args.file:
        # 実際のファイル処理
        issues = args.issues or []
        suggestions = args.suggestions or [
            "Consider adding comments",
            "Review code structure",
            "Check for unused variables"
        ]
        
        feedback_engine.process_quality_feedback(
            file_path=args.file,
            score=args.score,
            issues=issues,
            suggestions=suggestions
        )
        
    else:
        print("❌ Please specify --file, --summary, or --test")
        parser.print_help()


if __name__ == "__main__":
    main()

