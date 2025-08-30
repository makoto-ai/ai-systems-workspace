#!/usr/bin/env python3
"""
🚀 Phase 3: リアルタイム品質監視エンジン
=====================================

リアルタイムでファイル変更を監視し、即座に品質評価を実行するシステム

主要機能:
- ファイル変更の即座検知
- 品質スコアのリアルタイム計算
- 品質劣化の自動検知
- 即座のフィードバック生成
- 学習データ統合
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
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class QualityScore:
    """品質スコア計算クラス"""
    
    def __init__(self):
        self.base_dir = Path(".")
        self.learning_data = self._load_learning_data()
    
    def _load_learning_data(self) -> Dict[str, Any]:
        """学習データを読み込み"""
        try:
            if os.path.exists("out/continuous_learning.json"):
                with open("out/continuous_learning.json") as f:
                    return json.load(f)
        except:
            pass
        return {"patterns": {}, "thresholds": {}, "weights": {}}
    
    def calculate_file_score(self, file_path: str) -> Dict[str, Any]:
        """個別ファイルの品質スコア計算"""
        score_data = {
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
            "scores": {},
            "overall_score": 0.0,
            "risk_level": "unknown",
            "issues": []
        }
        
        try:
            # ファイル種別判定
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.yml' or file_ext == '.yaml':
                score_data = self._score_yaml_file(file_path, score_data)
            elif file_ext == '.py':
                score_data = self._score_python_file(file_path, score_data)
            elif file_ext in ['.js', '.ts']:
                score_data = self._score_js_file(file_path, score_data)
            else:
                score_data["scores"]["general"] = 0.8  # 一般ファイル
            
            # 総合スコア計算
            if score_data["scores"]:
                score_data["overall_score"] = sum(score_data["scores"].values()) / len(score_data["scores"])
            
            # リスクレベル判定
            score_data["risk_level"] = self._determine_risk_level(score_data["overall_score"])
            
        except Exception as e:
            score_data["issues"].append(f"Scoring error: {e}")
            score_data["overall_score"] = 0.5
        
        return score_data
    
    def _score_yaml_file(self, file_path: str, score_data: Dict) -> Dict:
        """YAMLファイルの品質スコア"""
        try:
            # yamllint チェック
            result = subprocess.run(
                ["yamllint", "-f", "parsable", file_path],
                capture_output=True, text=True
            )
            
            issues = result.stdout.strip().split('\n') if result.stdout.strip() else []
            warning_count = len([i for i in issues if 'warning' in i])
            error_count = len([i for i in issues if 'error' in i])
            
            # スコア計算（エラー重視）
            base_score = 1.0
            base_score -= error_count * 0.3
            base_score -= warning_count * 0.1
            base_score = max(0.0, min(1.0, base_score))
            
            score_data["scores"]["yaml_syntax"] = base_score
            score_data["scores"]["yaml_warnings"] = max(0.0, 1.0 - warning_count * 0.05)
            
            if issues:
                score_data["issues"].extend(issues[:5])  # 最大5個まで
            
        except FileNotFoundError:
            score_data["scores"]["yaml_syntax"] = 0.7  # yamllint未インストール
        
        return score_data
    
    def _score_python_file(self, file_path: str, score_data: Dict) -> Dict:
        """Pythonファイルの品質スコア"""
        try:
            # 基本的な品質チェック
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # 基本メトリクス
            line_count = len(lines)
            empty_lines = sum(1 for line in lines if not line.strip())
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            
            # スコア計算
            readability_score = min(1.0, comment_lines / max(1, line_count * 0.1))
            structure_score = 0.8 if line_count < 500 else (0.6 if line_count < 1000 else 0.4)
            
            score_data["scores"]["readability"] = readability_score
            score_data["scores"]["structure"] = structure_score
            
        except Exception as e:
            score_data["issues"].append(f"Python analysis error: {e}")
        
        return score_data
    
    def _score_js_file(self, file_path: str, score_data: Dict) -> Dict:
        """JavaScript/TypeScriptファイルの品質スコア"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            lines = content.split('\n')
            line_count = len(lines)
            
            # 基本構造チェック
            structure_score = 0.8 if line_count < 300 else (0.6 if line_count < 600 else 0.4)
            
            score_data["scores"]["structure"] = structure_score
            
        except Exception as e:
            score_data["issues"].append(f"JS analysis error: {e}")
        
        return score_data
    
    def _determine_risk_level(self, score: float) -> str:
        """スコアからリスクレベル判定"""
        if score >= 0.8:
            return "low"
        elif score >= 0.6:
            return "medium"
        else:
            return "high"


class RealtimeQualityHandler(FileSystemEventHandler):
    """リアルタイム品質監視ハンドラー"""
    
    def __init__(self):
        self.quality_scorer = QualityScore()
        self.recent_changes = []
        self.quality_history = []
        self.debounce_time = 1.0  # 1秒のデバウンス
        self.last_event_time = {}
        
        # 監視対象拡張子
        self.monitored_extensions = {'.py', '.yml', '.yaml', '.js', '.ts', '.md', '.json'}
        
        # 除外ディレクトリ
        self.excluded_dirs = {'.git', 'node_modules', '__pycache__', '.pytest_cache', 'dist', 'build'}
    
    def should_monitor(self, file_path: str) -> bool:
        """監視対象ファイルかチェック"""
        path = Path(file_path)
        
        # 除外ディレクトリチェック
        for part in path.parts:
            if part in self.excluded_dirs:
                return False
        
        # 拡張子チェック
        if path.suffix.lower() in self.monitored_extensions:
            return True
        
        return False
    
    def on_modified(self, event):
        """ファイル変更時の処理"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        if not self.should_monitor(file_path):
            return
        
        # デバウンス処理
        current_time = time.time()
        if file_path in self.last_event_time:
            if current_time - self.last_event_time[file_path] < self.debounce_time:
                return
        
        self.last_event_time[file_path] = current_time
        
        # 品質評価を別スレッドで実行
        threading.Thread(target=self._evaluate_quality, args=(file_path,), daemon=True).start()
    
    def _evaluate_quality(self, file_path: str):
        """品質評価実行"""
        try:
            print(f"📊 Analyzing: {file_path}")
            
            # 品質スコア計算
            score_data = self.quality_scorer.calculate_file_score(file_path)
            
            # 履歴に追加
            self.quality_history.append(score_data)
            
            # 最新100件まで保持
            if len(self.quality_history) > 100:
                self.quality_history = self.quality_history[-100:]
            
            # フィードバック表示
            self._display_feedback(score_data)
            
            # 品質劣化チェック
            self._check_quality_degradation(score_data)
            
            # データ保存
            self._save_quality_data()
            
        except Exception as e:
            print(f"❌ Quality evaluation error for {file_path}: {e}")
    
    def _display_feedback(self, score_data: Dict):
        """フィードバック表示"""
        file_name = Path(score_data["file"]).name
        score = score_data["overall_score"]
        risk = score_data["risk_level"]
        
        # リスクレベル別の表示
        if risk == "high":
            print(f"🚨 HIGH RISK: {file_name} (Score: {score:.2f})")
            for issue in score_data["issues"][:3]:  # 最大3個
                print(f"   ⚠️  {issue}")
        elif risk == "medium":
            print(f"🔶 MEDIUM RISK: {file_name} (Score: {score:.2f})")
        else:
            print(f"✅ LOW RISK: {file_name} (Score: {score:.2f})")
        
        # 具体的なスコア表示
        if len(score_data["scores"]) > 1:
            print(f"   📈 Details: {', '.join([f'{k}:{v:.2f}' for k, v in score_data['scores'].items()])}")
    
    def _check_quality_degradation(self, current_score: Dict):
        """品質劣化チェック"""
        if len(self.quality_history) < 2:
            return
        
        # 同じファイルの過去のスコアと比較
        file_path = current_score["file"]
        previous_scores = [
            h for h in self.quality_history[-10:]  # 直近10個
            if h["file"] == file_path and h["timestamp"] != current_score["timestamp"]
        ]
        
        if not previous_scores:
            return
        
        latest_previous = previous_scores[-1]
        current = current_score["overall_score"]
        previous = latest_previous["overall_score"]
        
        # 品質劣化閾値: 0.2以上の低下
        if current < previous - 0.2:
            print(f"📉 QUALITY DEGRADATION DETECTED!")
            print(f"   File: {Path(file_path).name}")
            print(f"   Score: {previous:.2f} → {current:.2f} (Δ{current-previous:.2f})")
            print(f"   🔧 Consider reviewing recent changes")
    
    def _save_quality_data(self):
        """品質データ保存"""
        try:
            os.makedirs("out", exist_ok=True)
            
            # リアルタイム品質データ保存
            quality_summary = {
                "last_updated": datetime.now().isoformat(),
                "total_evaluations": len(self.quality_history),
                "recent_scores": self.quality_history[-10:],
                "risk_distribution": self._calculate_risk_distribution(),
                "average_score": self._calculate_average_score()
            }
            
            with open("out/realtime_quality.json", "w") as f:
                json.dump(quality_summary, f, indent=2)
                
        except Exception as e:
            print(f"❌ Save error: {e}")
    
    def _calculate_risk_distribution(self) -> Dict[str, int]:
        """リスク分布計算"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        
        for score_data in self.quality_history[-20:]:  # 直近20個
            risk = score_data.get("risk_level", "unknown")
            if risk in distribution:
                distribution[risk] += 1
        
        return distribution
    
    def _calculate_average_score(self) -> float:
        """平均スコア計算"""
        if not self.quality_history:
            return 0.0
        
        recent_scores = [s["overall_score"] for s in self.quality_history[-20:]]
        return sum(recent_scores) / len(recent_scores) if recent_scores else 0.0


class RealtimeQualityMonitor:
    """リアルタイム品質監視メインクラス"""
    
    def __init__(self, watch_path: str = "."):
        self.watch_path = watch_path
        self.observer = Observer()
        self.handler = RealtimeQualityHandler()
        self.is_running = False
    
    def start(self):
        """監視開始"""
        print("🚀 Realtime Quality Monitor Starting...")
        print(f"📂 Watching: {os.path.abspath(self.watch_path)}")
        print("⚡ File changes will be analyzed instantly")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 50)
        
        self.observer.schedule(self.handler, self.watch_path, recursive=True)
        self.observer.start()
        self.is_running = True
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """監視停止"""
        if self.is_running:
            print("\n🛑 Stopping Realtime Quality Monitor...")
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            
            # 最終統計表示
            self._display_final_stats()
    
    def _display_final_stats(self):
        """最終統計表示"""
        history = self.handler.quality_history
        
        if not history:
            print("📊 No quality evaluations performed")
            return
        
        print(f"\n📊 Final Statistics:")
        print(f"   Total evaluations: {len(history)}")
        print(f"   Average score: {self.handler._calculate_average_score():.2f}")
        
        risk_dist = self.handler._calculate_risk_distribution()
        print(f"   Risk distribution: High:{risk_dist['high']}, Medium:{risk_dist['medium']}, Low:{risk_dist['low']}")
        
        print(f"📄 Quality report saved: out/realtime_quality.json")


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="🚀 Realtime Quality Monitor")
    parser.add_argument("--path", "-p", default=".", help="Path to watch (default: current directory)")
    parser.add_argument("--test", action="store_true", help="Run test mode (analyze current state and exit)")
    
    args = parser.parse_args()
    
    if args.test:
        # テストモード: 現在の状態を分析して終了
        print("🧪 Test Mode: Analyzing current state...")
        handler = RealtimeQualityHandler()
        
        # 重要ファイルをテスト分析
        test_files = [
            ".github/workflows/pr-quality-check.yml",
            "tests/golden/evaluator.py",
            "scripts/quality/tag_failures.py"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                score_data = handler.quality_scorer.calculate_file_score(file_path)
                handler._display_feedback(score_data)
        
        handler._save_quality_data()
        print("✅ Test analysis complete")
    else:
        # 通常モード: リアルタイム監視開始
        monitor = RealtimeQualityMonitor(args.path)
        monitor.start()


if __name__ == "__main__":
    main()



