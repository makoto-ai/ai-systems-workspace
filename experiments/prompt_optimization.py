#!/usr/bin/env python3
"""
Prompt Optimization for Golden Test Phase 4
プロンプト最適化実験システム（固有名詞保護・フォーマット強化・数値テンプレート）
"""

import json
import argparse
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import sys
import requests
import re

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    sys.path.append(str(Path(__file__).parent.parent / "tests" / "golden"))
    from evaluator import score
    from root_cause_analyzer import analyze_failure_root_cause, RootCause
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure modules are accessible from project root")
    sys.exit(1)

class PromptOptimizer:
    """プロンプト最適化実験クラス"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise Exception("GROQ_API_KEY not found")
        
        # Phase4向けプロンプトバリエーション
        self.prompt_variants = {
            "baseline": """以下の入力に対して、関連するキーワードを空白区切りで出力してください。

入力: {input_text}

出力は必ずキーワードのみ（説明文不要）:""",
            
            "compound_protected": """以下の入力に対して、関連するキーワードを空白区切りで出力してください。
複合語・固有名詞は分割せず、そのまま出力してください。

入力: {input_text}

例:
入力: マーケティング戦略の分析ダッシュボード作成
出力: マーケティング戦略 分析ダッシュボード 作成

入力: 営業ロープレAIシステムの改善
出力: 営業ロープレ AIシステム 改善

入力: CI/CDパイプラインの自動化設定
出力: CI/CD パイプライン 自動化 設定

出力は必ずキーワードのみ（説明文不要）:""",
            
            "format_enhanced": """以下の入力に対して、関連するキーワードを空白区切りで出力してください。
複合語は分割せず、数値・単位は正確に、専門用語は原形のまま出力してください。

入力: {input_text}

【出力例】
入力: 売上分析のダッシュボード改善で90%の精度向上
出力: 売上分析 ダッシュボード 改善 90% 精度向上

入力: 音声認識システムの応答時間を200ms短縮
出力: 音声認識システム 応答時間 200ms 短縮

入力: 営業ロープレ自動化によるCI整備の効率化
出力: 営業ロープレ 自動化 CI整備 効率化

【重要】出力は必ずキーワードのみ（説明文・文章は不要）:""",
            
            "template_explicit": """タスク: キーワード抽出
入力: {input_text}
出力形式: 空白区切りキーワード

【抽出ルール】
1. 複合語は分割しない（例：「営業ロープレ」「分析ダッシュボード」）
2. 数値と単位はセットで出力（例：「90%」「200ms」）
3. 専門用語は省略しない（例：「AI」→「AIシステム」、「CI」→「CI整備」）
4. 説明文・文章は一切含めない

【出力例】
営業システム → 営業システム
分析機能の向上 → 分析機能 向上
90%の改善効果 → 90% 改善効果

出力:"""
        }
    
    def get_model_cases(self, root_cause_filter: str = None, limit: int = None) -> List[Dict]:
        """テストケースを取得（root_cause_filterで絞り込み可能）"""
        cases_dir = Path("tests/golden/cases")
        if not cases_dir.exists():
            raise FileNotFoundError(f"Test cases directory not found: {cases_dir}")
        
        # ログから失敗ケースを特定
        failed_cases = set()
        if root_cause_filter:
            logs_dir = Path("tests/golden/logs")
            if logs_dir.exists():
                log_files = sorted(logs_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
                if log_files:
                    latest_log = log_files[0]
                    with open(latest_log, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                try:
                                    data = json.loads(line)
                                    if not data.get('passed', True):
                                        case_id = data.get('id', '')
                                        reference = data.get('reference', '')
                                        prediction = data.get('prediction', '')
                                        test_score = data.get('score', 0.0)
                                        
                                        # Root Cause分析
                                        root_cause = analyze_failure_root_cause(case_id, reference, prediction, test_score)
                                        if root_cause.value == root_cause_filter:
                                            failed_cases.add(case_id)
                                except json.JSONDecodeError:
                                    continue
        
        # テストケース読み込み
        target_cases = []
        for case_file in sorted(cases_dir.glob("*.json")):
            try:
                with open(case_file, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                
                case_id = case_data.get("id", case_file.stem)
                
                # フィルタリング
                if root_cause_filter and case_id not in failed_cases:
                    continue
                
                target_cases.append(case_data)
                
                # 件数制限
                if limit and len(target_cases) >= limit:
                    break
                    
            except Exception as e:
                print(f"❌ Error loading {case_file}: {e}")
                continue
        
        return target_cases
    
    def predict_with_prompt(self, input_text: str, prompt_template: str) -> str:
        """指定プロンプトテンプレートで予測実行"""
        prompt = prompt_template.format(input_text=input_text)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'llama3-8b-8192',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.0,
            'max_tokens': 80
        }
        
        try:
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                prediction = result['choices'][0]['message']['content']
            else:
                raise Exception(f"API error: {response.status_code}")
            
            # レスポンスをサニタイズ
            prediction = prediction.strip().replace('\n', ' ')
            prediction = ' '.join(prediction.split())  # 複数スペースを単一に
            
            return prediction
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return ""
    
    def run_optimization_experiment(self, cases: List[Dict], budget: int = 20) -> Dict[str, Any]:
        """プロンプト最適化実験を実行"""
        results = {}
        
        # 予算内でケースを制限
        if len(cases) > budget:
            cases = cases[:budget]
            print(f"⚠️ Budget limit: Testing {budget} cases out of {len(cases)}")
        
        for variant_name, prompt_template in self.prompt_variants.items():
            print(f"🔬 Testing prompt variant: {variant_name}")
            
            variant_results = {
                "variant": variant_name,
                "cases": [],
                "pass_at_85": 0,  # Phase4: 0.85しきい値での合格率
                "avg_score": 0.0,
                "jaccard_avg": 0.0,
                "api_calls": 0,
                "total_time": 0.0
            }
            
            total_score = 0.0
            total_jaccard = 0.0
            passed_at_85 = 0
            start_time = time.time()
            
            for case in cases:
                case_id = case.get("id", "unknown")
                reference = case.get("reference", "")
                input_text = case.get("input", "")
                
                try:
                    # プロンプト予測実行
                    case_start = time.time()
                    prediction = self.predict_with_prompt(input_text, prompt_template)
                    case_time = time.time() - case_start
                    
                    # スコア計算
                    test_score = score(reference, prediction)
                    passed_85 = test_score >= 0.85  # Phase4しきい値
                    
                    # Jaccard類似度計算
                    jaccard = self._calculate_jaccard(reference, prediction)
                    
                    if passed_85:
                        passed_at_85 += 1
                    
                    total_score += test_score
                    total_jaccard += jaccard
                    variant_results["api_calls"] += 1
                    
                    case_result = {
                        "case_id": case_id,
                        "score": test_score,
                        "jaccard": jaccard,
                        "passed_85": passed_85,
                        "time_ms": case_time * 1000,
                        "reference": reference,
                        "prediction": prediction
                    }
                    variant_results["cases"].append(case_result)
                    
                    print(f"  {case_id}: {test_score:.3f} ({'✅' if passed_85 else '❌'})")
                    
                except Exception as e:
                    print(f"  ❌ {case_id}: Error - {e}")
                    case_result = {
                        "case_id": case_id,
                        "score": 0.0,
                        "jaccard": 0.0,
                        "passed_85": False,
                        "error": str(e),
                        "time_ms": 0
                    }
                    variant_results["cases"].append(case_result)
            
            # 統計計算
            total_time = time.time() - start_time
            variant_results["pass_at_85"] = passed_at_85 / len(cases) if cases else 0
            variant_results["avg_score"] = total_score / len(cases) if cases else 0
            variant_results["jaccard_avg"] = total_jaccard / len(cases) if cases else 0
            variant_results["total_time"] = total_time
            
            print(f"  📊 Pass@0.85: {variant_results['pass_at_85']:.1%}")
            print(f"  📊 Avg Score: {variant_results['avg_score']:.3f}")
            print(f"  📊 Jaccard: {variant_results['jaccard_avg']:.3f}")
            print(f"  ⏱️ Total Time: {total_time:.2f}s")
            
            results[variant_name] = variant_results
        
        return results
    
    def _calculate_jaccard(self, reference: str, prediction: str) -> float:
        """Jaccard類似度計算"""
        ref_tokens = set(reference.split()) if reference else set()
        pred_tokens = set(prediction.split()) if prediction else set()
        
        if not ref_tokens and not pred_tokens:
            return 1.0
        if not ref_tokens or not pred_tokens:
            return 0.0
        
        intersection = len(ref_tokens & pred_tokens)
        union = len(ref_tokens | pred_tokens)
        
        return intersection / union
    
    def generate_improvement_suggestions(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """結果から改善提案を生成"""
        suggestions = []
        
        # 最優秀バリアントを特定
        best_variant = max(results.keys(), key=lambda k: results[k]["pass_at_85"])
        best_performance = results[best_variant]["pass_at_85"]
        
        if best_performance > results.get("baseline", {}).get("pass_at_85", 0):
            improvement = best_performance - results.get("baseline", {}).get("pass_at_85", 0)
            suggestions.append({
                "type": "prompt:best-variant",
                "description": f"{best_variant}により{improvement:.1%}の改善",
                "priority": "high" if improvement > 0.1 else "medium"
            })
        
        # 複合語保護の効果チェック
        if "compound_protected" in results:
            compound_perf = results["compound_protected"]["pass_at_85"]
            baseline_perf = results.get("baseline", {}).get("pass_at_85", 0)
            if compound_perf > baseline_perf:
                suggestions.append({
                    "type": "prompt:compound-lock", 
                    "description": f"複合語保護で{compound_perf - baseline_perf:.1%}改善",
                    "priority": "high"
                })
        
        # フォーマット強化の効果チェック
        if "format_enhanced" in results:
            format_perf = results["format_enhanced"]["pass_at_85"]
            baseline_perf = results.get("baseline", {}).get("pass_at_85", 0)
            if format_perf > baseline_perf:
                suggestions.append({
                    "type": "prompt:format-enhance",
                    "description": f"フォーマット強化で{format_perf - baseline_perf:.1%}改善",
                    "priority": "medium"
                })
        
        return suggestions

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Prompt Optimization Experiment")
    parser.add_argument("--budget", type=int, default=20,
                       help="実験予算（API呼び出し数の制限）")
    parser.add_argument("--metric", choices=["jaccard", "score"], default="jaccard",
                       help="最適化メトリクス")
    parser.add_argument("--out", type=str, default="out/prompt_opt_phase4.json",
                       help="結果出力パス")
    parser.add_argument("--filter", choices=["MODEL", "PROMPT", "TOKENIZE"], 
                       help="特定のroot_causeのみテスト")
    
    args = parser.parse_args()
    
    try:
        optimizer = PromptOptimizer()
        
        # テストケース取得
        print(f"🔍 Collecting test cases (filter: {args.filter or 'all'})")
        target_cases = optimizer.get_model_cases(args.filter, limit=args.budget)
        
        if not target_cases:
            print(f"❌ No cases found for filter: {args.filter}")
            return False
        
        print(f"📋 Found {len(target_cases)} cases (budget: {args.budget})")
        
        # 最適化実験実行
        print(f"🧪 Running prompt optimization experiment")
        results = optimizer.run_optimization_experiment(target_cases, args.budget)
        
        # 改善提案生成
        suggestions = optimizer.generate_improvement_suggestions(results)
        
        # レポート生成
        report = {
            "experiment": {
                "timestamp": datetime.now().isoformat(),
                "budget": args.budget,
                "metric": args.metric,
                "root_cause_filter": args.filter,
                "total_cases": len(target_cases)
            },
            "results": results,
            "improvement_suggestions": suggestions,
            "summary": {
                "best_variant": max(results.keys(), key=lambda k: results[k]["pass_at_85"]) if results else None,
                "best_pass_at_85": max(r["pass_at_85"] for r in results.values()) if results else 0,
                "baseline_improvement": (max(r["pass_at_85"] for r in results.values()) - 
                                       results.get("baseline", {}).get("pass_at_85", 0)) if results else 0
            }
        }
        
        # 結果保存
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Prompt optimization report saved: {output_path}")
        
        # サマリー表示
        print(f"\n📊 Optimization Summary:")
        print(f"  Best Variant: {report['summary']['best_variant']}")
        print(f"  Best Pass@0.85: {report['summary']['best_pass_at_85']:.1%}")
        print(f"  Improvement: {report['summary']['baseline_improvement']:+.1%}")
        
        print(f"\n💡 Top Suggestions:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"  {i}. {suggestion['type']}: {suggestion['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)