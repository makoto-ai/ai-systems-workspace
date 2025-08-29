#!/usr/bin/env python3
"""
Model Swap Experiment for Golden Tests
MODEL起因失敗に対する小規模実験レーン
"""

import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # 相対インポートを試行
    sys.path.append(str(Path(__file__).parent.parent / "app"))
    sys.path.append(str(Path(__file__).parent.parent / "tests" / "golden"))
    
    from services.ai_service import UnifiedAIService, AIProvider
    from evaluator import score
    from root_cause_analyzer import analyze_failure_root_cause
except ImportError:
    try:
        # 絶対インポートを試行
        from app.services.ai_service import UnifiedAIService, AIProvider
        from tests.golden.evaluator import score
        from tests.golden.root_cause_analyzer import analyze_failure_root_cause
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure modules are accessible from project root")
        sys.exit(1)

class ModelExperiment:
    """モデル実験クラス"""
    
    def __init__(self):
        self.ai_service = UnifiedAIService()
        
    def get_model_cases(self, root_cause_filter: str = "MODEL") -> List[Dict]:
        """指定されたroot_causeのケースを取得"""
        cases_dir = Path("tests/golden/cases")
        if not cases_dir.exists():
            raise FileNotFoundError(f"Test cases directory not found: {cases_dir}")
        
        # 最新のログから失敗ケースを特定
        logs_dir = Path("tests/golden/logs")
        failed_cases = set()
        
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
        
        # 該当ケースのファイルを読み込み
        target_cases = []
        for case_file in sorted(cases_dir.glob("*.json")):
            try:
                with open(case_file, 'r', encoding='utf-8') as f:
                    case_data = json.load(f)
                
                case_id = case_data.get("id", case_file.stem)
                if case_id in failed_cases:
                    target_cases.append(case_data)
                    
            except Exception as e:
                print(f"❌ Error loading {case_file}: {e}")
                continue
        
        return target_cases
    
    def run_model_comparison(self, cases: List[Dict], models: List[AIProvider]) -> Dict[str, Any]:
        """複数モデルでの比較実験"""
        results = {}
        
        for model in models:
            print(f"🔬 Testing model: {model.value}")
            model_results = {
                "model": model.value,
                "cases": [],
                "pass_at_1": 0,
                "avg_score": 0.0,
                "total_time": 0.0,
                "api_calls": 0
            }
            
            total_score = 0.0
            passed_cases = 0
            start_time = time.time()
            
            for case in cases:
                case_id = case.get("id", "unknown")
                reference = case.get("reference", "")
                input_text = case.get("input", "")
                
                try:
                    # モデル予測実行
                    case_start = time.time()
                    prediction = self.predict_with_model(input_text, model)
                    case_time = time.time() - case_start
                    
                    # スコア計算
                    test_score = score(reference, prediction)
                    passed = test_score >= 0.5  # 現在のしきい値
                    
                    if passed:
                        passed_cases += 1
                    
                    total_score += test_score
                    model_results["api_calls"] += 1
                    
                    case_result = {
                        "case_id": case_id,
                        "score": test_score,
                        "passed": passed,
                        "time_ms": case_time * 1000,
                        "reference": reference,
                        "prediction": prediction
                    }
                    model_results["cases"].append(case_result)
                    
                    print(f"  {case_id}: {test_score:.3f} ({'✅' if passed else '❌'})")
                    
                except Exception as e:
                    print(f"  ❌ {case_id}: Error - {e}")
                    case_result = {
                        "case_id": case_id,
                        "score": 0.0,
                        "passed": False,
                        "error": str(e),
                        "time_ms": 0
                    }
                    model_results["cases"].append(case_result)
            
            # 統計計算
            total_time = time.time() - start_time
            model_results["pass_at_1"] = passed_cases / len(cases) if cases else 0
            model_results["avg_score"] = total_score / len(cases) if cases else 0
            model_results["total_time"] = total_time
            
            print(f"  📊 Pass@1: {model_results['pass_at_1']:.1%}")
            print(f"  📊 Avg Score: {model_results['avg_score']:.3f}")
            print(f"  ⏱️ Total Time: {total_time:.2f}s")
            
            results[model.value] = model_results
        
        return results
    
    def predict_with_model(self, input_text: str, model: AIProvider) -> str:
        """指定モデルで予測実行"""
        prompt = f"""以下の入力に対して、関連するキーワードを空白区切りで出力してください。

入力: {input_text}

出力は必ずキーワードのみ（説明文不要）:"""
        
        try:
            # 簡易的な直接実装（非同期回避）
            import os
            import requests
            
            api_key = os.getenv('GROQ_API_KEY')
            if not api_key:
                raise Exception("GROQ_API_KEY not found")
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'llama3-8b-8192',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.0,
                'max_tokens': 60
            }
            
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response = result['choices'][0]['message']['content']
            else:
                raise Exception(f"API error: {response.status_code}")
            
            # レスポンスをサニタイズ
            prediction = response.strip().replace('\n', ' ')
            prediction = ' '.join(prediction.split())  # 複数スペースを単一に
            
            return prediction
            
        except Exception as e:
            print(f"❌ Model prediction error: {e}")
            return ""
    
    def estimate_cost(self, results: Dict[str, Any]) -> Dict[str, float]:
        """API コスト見積り（概算）"""
        # 簡易的なコスト見積り（実際のレートは変動）
        cost_per_1k_tokens = {
            "groq": 0.0001,      # 非常に安価
            "openai": 0.002,     # GPT-4o mini想定
            "anthropic": 0.003,  # Claude 3.5 Sonnet想定
            "gemini": 0.001      # Gemini Pro想定
        }
        
        estimated_costs = {}
        for model_name, model_results in results.items():
            # 簡易計算: API呼び出し数 × 平均トークン数 × レート
            api_calls = model_results.get("api_calls", 0)
            estimated_tokens = api_calls * 100  # 1回あたり約100トークンと仮定
            
            rate = cost_per_1k_tokens.get(model_name.lower(), 0.002)
            estimated_cost = (estimated_tokens / 1000) * rate
            
            estimated_costs[model_name] = estimated_cost
        
        return estimated_costs

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Model Swap Experiment")
    parser.add_argument("--cases", type=str, default="MODEL",
                       help="対象とするroot_cause（MODEL, TOKENIZE, etc.）")
    parser.add_argument("--out", type=str, default="out/model_exp.json",
                       help="結果出力パス")
    parser.add_argument("--models", nargs="+", 
                       choices=["groq", "openai", "anthropic", "gemini"],
                       default=["groq", "openai"],
                       help="比較対象モデル")
    
    args = parser.parse_args()
    
    try:
        experiment = ModelExperiment()
        
        # 対象ケース取得
        print(f"🔍 Collecting cases with root_cause: {args.cases}")
        target_cases = experiment.get_model_cases(args.cases)
        
        if not target_cases:
            print(f"❌ No cases found for root_cause: {args.cases}")
            return False
        
        print(f"📋 Found {len(target_cases)} cases")
        
        # モデル変換
        model_providers = []
        for model_name in args.models:
            if model_name == "groq":
                model_providers.append(AIProvider.GROQ)
            elif model_name == "openai":
                model_providers.append(AIProvider.OPENAI)
            elif model_name == "anthropic":
                model_providers.append(AIProvider.ANTHROPIC)
            elif model_name == "gemini":
                model_providers.append(AIProvider.GEMINI)
        
        # 実験実行
        print(f"🧪 Running experiment with {len(model_providers)} models")
        results = experiment.run_model_comparison(target_cases, model_providers)
        
        # コスト見積り
        costs = experiment.estimate_cost(results)
        
        # レポート生成
        report = {
            "experiment": {
                "timestamp": datetime.now().isoformat(),
                "root_cause_filter": args.cases,
                "total_cases": len(target_cases),
                "models_tested": len(model_providers)
            },
            "results": results,
            "cost_estimates_usd": costs,
            "summary": {
                "best_model": max(results.keys(), key=lambda k: results[k]["pass_at_1"]) if results else None,
                "best_pass_rate": max(r["pass_at_1"] for r in results.values()) if results else 0,
                "fastest_model": min(results.keys(), key=lambda k: results[k]["total_time"]) if results else None,
                "cheapest_model": min(costs.keys(), key=lambda k: costs[k]) if costs else None
            }
        }
        
        # 結果保存
        output_path = Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Experiment report saved: {output_path}")
        
        # サマリー表示
        print(f"\n📊 Experiment Summary:")
        print(f"  Best Model: {report['summary']['best_model']} ({report['summary']['best_pass_rate']:.1%})")
        print(f"  Fastest: {report['summary']['fastest_model']}")
        print(f"  Cheapest: {report['summary']['cheapest_model']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Experiment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
