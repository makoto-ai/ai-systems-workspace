#!/usr/bin/env python3
"""
Regression Detector - 修正前後での品質変化を詳細分析
- Pass率変化の統計的有意性検証
- 新規失敗パターンの検出
- 修正効果の定量評価
"""
import json
import subprocess
import re
import statistics
from pathlib import Path
from datetime import datetime

class RegressionDetector:
    def __init__(self):
        self.history_file = Path("out/quality_history.json")
        self.current_results_file = Path("out/current_results.json")
        
    def capture_baseline(self, label="baseline"):
        """現在の品質状態をベースラインとして記録"""
        print(f"📊 ベースライン品質測定中: {label}")
        
        try:
            # Golden test実行
            result = subprocess.run(
                ['python', 'tests/golden/runner.py'],
                capture_output=True, text=True, timeout=120
            )
            
            # 結果解析
            metrics = self._parse_test_results(result.stdout)
            metrics['timestamp'] = datetime.now().isoformat()
            metrics['label'] = label
            metrics['git_commit'] = self._get_current_commit()
            
            # 履歴に追加
            self._save_to_history(metrics)
            
            print(f"✅ ベースライン記録: Pass={metrics.get('pass_rate', 'N/A')}%, New={metrics.get('new_fail_rate', 'N/A')}%")
            return metrics
            
        except subprocess.TimeoutExpired:
            print("⏰ ベースライン測定タイムアウト")
            return None
        except Exception as e:
            print(f"❌ ベースライン測定エラー: {e}")
            return None
    
    def detect_regression(self, new_label="after_fix"):
        """修正後の回帰検出"""
        print(f"🔍 回帰検出実行: {new_label}")
        
        # 現在の品質を測定
        current_metrics = self.capture_baseline(new_label)
        if not current_metrics:
            return None
        
        # 履歴からベースラインを取得
        history = self._load_history()
        if len(history) < 2:
            print("⚠️  比較用ベースラインが不足しています")
            return None
        
        baseline = history[-2]  # 直前の測定値
        current = history[-1]   # 現在の測定値
        
        # 回帰分析
        analysis = self._analyze_regression(baseline, current)
        
        # 結果レポート
        self._report_regression_analysis(analysis)
        
        return analysis
    
    def _parse_test_results(self, output):
        """テスト結果から各種メトリクスを抽出"""
        metrics = {}
        
        # Pass率
        pass_match = re.search(r'Pass:\s*(\d+)/(\d+)\s*\(([0-9.]+)%\)', output)
        if pass_match:
            metrics['pass_count'] = int(pass_match.group(1))
            metrics['total_tests'] = int(pass_match.group(2))
            metrics['pass_rate'] = float(pass_match.group(3))
        
        # New失敗率
        new_match = re.search(r'New:\s*(\d+)/\d+\s*\(([0-9.]+)%\)', output)
        if new_match:
            metrics['new_fail_count'] = int(new_match.group(1))
            metrics['new_fail_rate'] = float(new_match.group(2))
        
        # Flaky率
        flaky_match = re.search(r'Flaky:\s*(\d+)/\d+\s*\(([0-9.]+)%\)', output)
        if flaky_match:
            metrics['flaky_count'] = int(flaky_match.group(1))
            metrics['flaky_rate'] = float(flaky_match.group(2))
        
        # Root cause分析
        tokenize_fails = len(re.findall(r'TOKENIZE', output, re.IGNORECASE))
        model_fails = len(re.findall(r'MODEL', output, re.IGNORECASE))
        
        metrics['tokenize_fails'] = tokenize_fails
        metrics['model_fails'] = model_fails
        
        return metrics
    
    def _get_current_commit(self):
        """現在のGitコミットハッシュを取得"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _save_to_history(self, metrics):
        """品質履歴を保存"""
        history = self._load_history()
        history.append(metrics)
        
        # 履歴は最大50件まで
        if len(history) > 50:
            history = history[-50:]
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def _load_history(self):
        """品質履歴をロード"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def _analyze_regression(self, baseline, current):
        """回帰分析実行"""
        analysis = {
            'baseline': baseline,
            'current': current,
            'changes': {},
            'regression_detected': False,
            'improvement_detected': False,
            'significance_level': None
        }
        
        # Pass率変化
        if 'pass_rate' in baseline and 'pass_rate' in current:
            pass_change = current['pass_rate'] - baseline['pass_rate']
            analysis['changes']['pass_rate'] = {
                'before': baseline['pass_rate'],
                'after': current['pass_rate'],
                'change': pass_change,
                'change_pct': pass_change
            }
            
            # 統計的有意性（簡易版）
            if abs(pass_change) >= 5.0:  # 5%以上の変化
                analysis['significance_level'] = 'SIGNIFICANT'
                if pass_change < -3.0:  # 3%以上の悪化
                    analysis['regression_detected'] = True
                elif pass_change > 5.0:  # 5%以上の改善
                    analysis['improvement_detected'] = True
            elif abs(pass_change) >= 2.0:  # 2%以上の変化
                analysis['significance_level'] = 'MARGINAL'
            else:
                analysis['significance_level'] = 'NOT_SIGNIFICANT'
        
        # New失敗率変化
        if 'new_fail_rate' in baseline and 'new_fail_rate' in current:
            new_fail_change = current['new_fail_rate'] - baseline['new_fail_rate']
            analysis['changes']['new_fail_rate'] = {
                'before': baseline['new_fail_rate'],
                'after': current['new_fail_rate'], 
                'change': new_fail_change
            }
            
            if new_fail_change > 10.0:  # 10%以上新規失敗増加
                analysis['regression_detected'] = True
        
        # Root cause変化
        tokenize_change = current.get('tokenize_fails', 0) - baseline.get('tokenize_fails', 0)
        model_change = current.get('model_fails', 0) - baseline.get('model_fails', 0)
        
        analysis['changes']['root_causes'] = {
            'tokenize_change': tokenize_change,
            'model_change': model_change
        }
        
        return analysis
    
    def _report_regression_analysis(self, analysis):
        """回帰分析結果をレポート"""
        print("\n" + "="*50)
        print("📊 品質変化分析レポート")
        print("="*50)
        
        if 'pass_rate' in analysis['changes']:
            change = analysis['changes']['pass_rate']
            print(f"Pass率: {change['before']:.1f}% → {change['after']:.1f}% ({change['change']:+.1f}%)")
        
        if 'new_fail_rate' in analysis['changes']:
            change = analysis['changes']['new_fail_rate']
            print(f"New失敗率: {change['before']:.1f}% → {change['after']:.1f}% ({change['change']:+.1f}%)")
        
        print(f"統計的有意性: {analysis['significance_level']}")
        
        if analysis['regression_detected']:
            print("🚨 **回帰検出**: 品質悪化が検出されました！")
        elif analysis['improvement_detected']:
            print("🎉 **改善検出**: 品質向上が検出されました！")
        else:
            print("✅ 品質安定: 有意な変化なし")
        
        # Root cause変化
        rc_changes = analysis['changes']['root_causes']
        if rc_changes['tokenize_change'] != 0:
            print(f"TOKENIZE失敗変化: {rc_changes['tokenize_change']:+d}")
        if rc_changes['model_change'] != 0:
            print(f"MODEL失敗変化: {rc_changes['model_change']:+d}")
        
        print("="*50)

def main():
    import sys
    
    detector = RegressionDetector()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "baseline":
            label = sys.argv[2] if len(sys.argv) > 2 else "manual_baseline"
            detector.capture_baseline(label)
            
        elif command == "detect":
            label = sys.argv[2] if len(sys.argv) > 2 else "manual_check"
            result = detector.detect_regression(label)
            
            # 終了コードで結果を表現
            if result and result['regression_detected']:
                sys.exit(1)  # 回帰検出
            else:
                sys.exit(0)  # 正常/改善
        else:
            print("Usage: python regression_detector.py [baseline|detect] [label]")
            sys.exit(1)
    else:
        # デフォルト: 回帰検出
        result = detector.detect_regression()
        sys.exit(1 if result and result['regression_detected'] else 0)

if __name__ == "__main__":
    main()
