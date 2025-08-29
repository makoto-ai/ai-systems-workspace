#!/usr/bin/env python3
"""
Golden Test Root Cause Analyzer
失敗理由の自動分類とタグ付けシステム
"""

import json
import re
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

class RootCause(Enum):
    """失敗理由の分類"""
    TOKENIZE = "TOKENIZE"      # トークン分割問題
    NORMALIZE = "NORMALIZE"    # 正規化辞書不足
    PROMPT = "PROMPT"          # プロンプト設計問題
    MODEL = "MODEL"            # モデル出力不安定
    DATA_DRIFT = "DATA_DRIFT"  # データ品質劣化
    FLAKY = "FLAKY"           # 再現性のない偶発的失敗
    INFRA = "INFRA"           # インフラ・環境問題

def analyze_failure_root_cause(case_id: str, reference: str, prediction: str, score: float) -> RootCause:
    """失敗ケースの根本原因を自動分析"""
    
    # 空の予測 → インフラ問題の可能性
    if not prediction.strip():
        return RootCause.INFRA
    
    ref_tokens = set(reference.split())
    pred_tokens = set(prediction.split())
    
    # 完全に異なる語彙 → モデル問題
    if len(ref_tokens & pred_tokens) == 0:
        return RootCause.MODEL
    
    # 部分一致があるが低スコア → 正規化問題の可能性
    if 0 < score < 0.3:
        # 類似語があるかチェック
        for ref_token in ref_tokens:
            for pred_token in pred_tokens:
                if _is_similar_token(ref_token, pred_token):
                    return RootCause.NORMALIZE
        return RootCause.TOKENIZE
    
    # 中程度のスコア → トークン分割問題
    if 0.3 <= score < 0.7:
        return RootCause.TOKENIZE
    
    # 高スコアだが不合格 → Flaky（境界線上）
    if score >= 0.7:
        return RootCause.FLAKY
    
    return RootCause.MODEL

def _is_similar_token(token1: str, token2: str) -> bool:
    """トークンの類似性チェック"""
    # 部分文字列チェック
    if token1 in token2 or token2 in token1:
        return True
    
    # 英日混在チェック
    similar_pairs = [
        ("ai", "aiシステム"),
        ("学習", "学習改善"),
        ("分析", "分析ダッシュボード"),
        ("ci", "ci整備"),
    ]
    
    for pair in similar_pairs:
        if (token1.lower() in pair and token2.lower() in pair) or \
           (token2.lower() in pair and token1.lower() in pair):
            return True
    
    return False

def extract_failures_from_log(log_path: Path) -> List[Dict]:
    """ログファイルから失敗ケースを抽出"""
    failures = []
    
    if not log_path.exists():
        return failures
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if not data.get('passed', True):  # 失敗ケースのみ
                        failures.append(data)
                except json.JSONDecodeError:
                    continue
    
    return failures

def analyze_recent_failures() -> Dict[str, List[Dict]]:
    """直近のログから失敗分析を実行"""
    logs_dir = Path("tests/golden/logs")
    
    if not logs_dir.exists():
        return {}
    
    # 最新2つのログファイルを取得
    log_files = sorted(logs_dir.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)[:2]
    
    analysis_results = {}
    
    for log_file in log_files:
        failures = extract_failures_from_log(log_file)
        analyzed_failures = []
        
        for failure in failures:
            root_cause = analyze_failure_root_cause(
                failure.get('id', ''),
                failure.get('reference', ''),
                failure.get('prediction', ''),
                failure.get('score', 0.0)
            )
            
            analyzed_failures.append({
                'case_id': failure.get('id'),
                'root_cause': root_cause.value,
                'score': failure.get('score', 0.0),
                'reference': failure.get('reference', ''),
                'prediction': failure.get('prediction', ''),
                'description': _generate_description(root_cause, failure)
            })
        
        analysis_results[log_file.stem] = analyzed_failures
    
    return analysis_results

def _generate_description(root_cause: RootCause, failure: Dict) -> str:
    """失敗理由の説明文生成"""
    case_id = failure.get('id', 'unknown')
    
    descriptions = {
        RootCause.TOKENIZE: f"複合語・分割問題",
        RootCause.NORMALIZE: f"正規化辞書不足",
        RootCause.PROMPT: f"プロンプト設計問題",
        RootCause.MODEL: f"モデル出力不安定",
        RootCause.DATA_DRIFT: f"データ品質劣化",
        RootCause.FLAKY: f"再現性なし（境界線上）",
        RootCause.INFRA: f"インフラ・環境問題"
    }
    
    return descriptions.get(root_cause, "不明な原因")

def update_observation_log_with_analysis():
    """観測ログに分析結果を追記"""
    analysis_results = analyze_recent_failures()
    
    if not analysis_results:
        print("分析対象の失敗ケースが見つかりませんでした")
        return
    
    print("🔍 Root Cause Analysis Results:")
    print("=" * 40)
    
    for log_file, failures in analysis_results.items():
        print(f"\n📅 {log_file}:")
        if not failures:
            print("  ✅ 失敗ケースなし")
            continue
            
        for failure in failures:
            print(f"  - {failure['case_id']}: `root_cause:{failure['root_cause']}` - {failure['description']}")
    
    # 統計情報
    all_failures = []
    for failures in analysis_results.values():
        all_failures.extend(failures)
    
    if all_failures:
        root_cause_counts = {}
        for failure in all_failures:
            cause = failure['root_cause']
            root_cause_counts[cause] = root_cause_counts.get(cause, 0) + 1
        
        print(f"\n📊 Root Cause Distribution:")
        for cause, count in sorted(root_cause_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(all_failures)) * 100
            print(f"  - {cause}: {count}件 ({percentage:.1f}%)")

if __name__ == "__main__":
    update_observation_log_with_analysis()
