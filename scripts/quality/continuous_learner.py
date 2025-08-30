#!/usr/bin/env python3
"""
Continuous Learning System - 継続学習による品質向上
- 過去の修正効果を蓄積・分析
- 修正戦略の自動最適化
- 成功パターンの学習・応用
"""
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import re

class ContinuousLearner:
    def __init__(self):
        self.learning_db = Path("out/learning_database.json")
        self.models_dir = Path("out/learning_models")
        self.models_dir.mkdir(exist_ok=True)
        
    def record_fix_attempt(self, tag, fix_strategy, before_metrics, after_metrics, success=True):
        """修正試行を学習データベースに記録"""
        
        fix_record = {
            'timestamp': datetime.now().isoformat(),
            'tag': tag,
            'fix_strategy': fix_strategy,
            'before_metrics': before_metrics,
            'after_metrics': after_metrics,
            'success': success,
            'improvement': self._calculate_improvement(before_metrics, after_metrics),
            'git_commit': self._get_git_commit()
        }
        
        # データベースに追加
        db = self._load_learning_db()
        db['fix_attempts'].append(fix_record)
        
        # 統計更新
        self._update_learning_stats(db)
        
        self._save_learning_db(db)
        print(f"📚 学習記録追加: {tag} → 改善度{fix_record['improvement']:.1f}%")
        
    def predict_fix_effectiveness(self, tag, fix_strategy):
        """修正効果を予測"""
        db = self._load_learning_db()
        
        # 類似修正の成功率を分析
        similar_attempts = [
            attempt for attempt in db['fix_attempts']
            if attempt['tag'].split('.')[0] == tag.split('.')[0]  # 同じカテゴリ
        ]
        
        if not similar_attempts:
            return {
                'predicted_improvement': 15.0,  # デフォルト予測
                'confidence': 'LOW',
                'sample_size': 0,
                'recommendation': 'PROCEED_WITH_CAUTION'
            }
        
        # 成功率計算
        successful = [a for a in similar_attempts if a['success']]
        success_rate = len(successful) / len(similar_attempts)
        
        # 改善度の統計
        improvements = [a['improvement'] for a in successful]
        avg_improvement = np.mean(improvements) if improvements else 0
        std_improvement = np.std(improvements) if improvements else 10
        
        # 信頼度判定
        confidence = 'HIGH' if len(similar_attempts) >= 5 else 'MEDIUM' if len(similar_attempts) >= 2 else 'LOW'
        
        # 推奨アクション
        if success_rate >= 0.8 and avg_improvement >= 10:
            recommendation = 'HIGHLY_RECOMMENDED'
        elif success_rate >= 0.6 and avg_improvement >= 5:
            recommendation = 'RECOMMENDED'
        elif success_rate >= 0.4:
            recommendation = 'PROCEED_WITH_CAUTION'
        else:
            recommendation = 'NOT_RECOMMENDED'
        
        return {
            'predicted_improvement': avg_improvement,
            'confidence': confidence,
            'success_rate': success_rate,
            'sample_size': len(similar_attempts),
            'recommendation': recommendation,
            'risk_assessment': std_improvement
        }
    
    def get_optimal_fix_strategy(self, tag):
        """タグに対する最適修正戦略を推奨"""
        db = self._load_learning_db()
        
        # タグ別成功戦略を分析
        tag_attempts = [
            attempt for attempt in db['fix_attempts']
            if attempt['tag'] == tag and attempt['success']
        ]
        
        if not tag_attempts:
            return self._get_default_strategy(tag)
        
        # 最も効果的だった戦略を抽出
        best_attempt = max(tag_attempts, key=lambda x: x['improvement'])
        
        strategy = {
            'tag': tag,
            'recommended_strategy': best_attempt['fix_strategy'],
            'expected_improvement': best_attempt['improvement'],
            'historical_success': len(tag_attempts),
            'last_success': best_attempt['timestamp'],
            'confidence_score': min(len(tag_attempts) * 0.2, 1.0)
        }
        
        print(f"🎯 最適戦略推奨: {tag}")
        print(f"   戦略: {strategy['recommended_strategy']['name']}")
        print(f"   期待改善: {strategy['expected_improvement']:.1f}%")
        print(f"   成功実績: {strategy['historical_success']}回")
        
        return strategy
    
    def analyze_learning_trends(self):
        """学習トレンドを分析"""
        db = self._load_learning_db()
        
        if len(db['fix_attempts']) < 3:
            print("📊 学習データ不足: 最低3回の修正試行が必要")
            return None
        
        # 時系列分析
        attempts = sorted(db['fix_attempts'], key=lambda x: x['timestamp'])
        recent_attempts = attempts[-10:]  # 直近10回
        
        # 成功率トレンド
        recent_success_rate = sum(1 for a in recent_attempts if a['success']) / len(recent_attempts)
        overall_success_rate = sum(1 for a in attempts if a['success']) / len(attempts)
        
        # 改善度トレンド
        recent_improvements = [a['improvement'] for a in recent_attempts if a['success']]
        overall_improvements = [a['improvement'] for a in attempts if a['success']]
        
        recent_avg_improvement = np.mean(recent_improvements) if recent_improvements else 0
        overall_avg_improvement = np.mean(overall_improvements) if overall_improvements else 0
        
        # カテゴリ別分析
        category_stats = defaultdict(list)
        for attempt in attempts:
            category = attempt['tag'].split('.')[0]
            category_stats[category].append(attempt)
        
        trend_analysis = {
            'total_attempts': len(attempts),
            'recent_success_rate': recent_success_rate,
            'overall_success_rate': overall_success_rate,
            'success_trend': 'IMPROVING' if recent_success_rate > overall_success_rate else 'DECLINING',
            'recent_avg_improvement': recent_avg_improvement,
            'overall_avg_improvement': overall_avg_improvement,
            'improvement_trend': 'IMPROVING' if recent_avg_improvement > overall_avg_improvement else 'DECLINING',
            'category_performance': {}
        }
        
        # カテゴリ別パフォーマンス
        for category, cat_attempts in category_stats.items():
            successful = [a for a in cat_attempts if a['success']]
            success_rate = len(successful) / len(cat_attempts)
            avg_improvement = np.mean([a['improvement'] for a in successful]) if successful else 0
            
            trend_analysis['category_performance'][category] = {
                'attempts': len(cat_attempts),
                'success_rate': success_rate,
                'avg_improvement': avg_improvement
            }
        
        self._report_learning_trends(trend_analysis)
        return trend_analysis
    
    def _calculate_improvement(self, before, after):
        """改善度を計算"""
        if 'pass_rate' in before and 'pass_rate' in after:
            return after['pass_rate'] - before['pass_rate']
        return 0
    
    def _get_git_commit(self):
        """現在のGitコミット取得"""
        import subprocess
        try:
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"
    
    def _load_learning_db(self):
        """学習データベースロード"""
        if not self.learning_db.exists():
            return {
                'fix_attempts': [],
                'learning_stats': {
                    'total_attempts': 0,
                    'successful_attempts': 0,
                    'avg_improvement': 0,
                    'last_updated': datetime.now().isoformat()
                }
            }
        
        with open(self.learning_db, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_learning_db(self, db):
        """学習データベース保存"""
        with open(self.learning_db, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    
    def _update_learning_stats(self, db):
        """学習統計更新"""
        attempts = db['fix_attempts']
        successful = [a for a in attempts if a['success']]
        
        db['learning_stats'] = {
            'total_attempts': len(attempts),
            'successful_attempts': len(successful),
            'success_rate': len(successful) / len(attempts) if attempts else 0,
            'avg_improvement': np.mean([a['improvement'] for a in successful]) if successful else 0,
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_default_strategy(self, tag):
        """デフォルト修正戦略"""
        strategies = {
            'TOKENIZE.hyphen_longdash': {
                'name': 'hyphen_normalization',
                'description': 'ハイフン・ダッシュ統一正規化',
                'expected_improvement': 15.0
            },
            'PUNCT.brackets_mismatch': {
                'name': 'bracket_normalization',
                'description': '括弧統一正規化',
                'expected_improvement': 12.0
            },
            'NUM.tolerance_small': {
                'name': 'numerical_tolerance_adjustment',
                'description': '数値許容範囲調整',
                'expected_improvement': 20.0
            }
        }
        
        return strategies.get(tag, {
            'name': 'generic_normalization',
            'description': '汎用正規化',
            'expected_improvement': 10.0
        })
    
    def _report_learning_trends(self, trends):
        """学習トレンドレポート"""
        print("\n" + "="*60)
        print("🧠 継続学習トレンド分析")
        print("="*60)
        
        print(f"総修正試行: {trends['total_attempts']}回")
        print(f"全体成功率: {trends['overall_success_rate']:.1%}")
        print(f"直近成功率: {trends['recent_success_rate']:.1%} ({trends['success_trend']})")
        print(f"平均改善度: {trends['overall_avg_improvement']:.1f}% → {trends['recent_avg_improvement']:.1f}% ({trends['improvement_trend']})")
        
        print("\n📊 カテゴリ別パフォーマンス:")
        for category, stats in trends['category_performance'].items():
            print(f"  {category}: {stats['success_rate']:.1%} ({stats['attempts']}回) 平均改善{stats['avg_improvement']:.1f}%")
        
        print("="*60)

def main():
    learner = ContinuousLearner()
    learner.analyze_learning_trends()

if __name__ == "__main__":
    main()
