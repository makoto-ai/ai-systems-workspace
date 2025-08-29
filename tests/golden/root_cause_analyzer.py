#!/usr/bin/env python3
"""
Golden Test Root Cause Analyzer
失敗理由の自動分類とタグ付けシステム
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set

class RootCause(Enum):
    """失敗理由の分類"""
    TOKENIZE = "TOKENIZE"      # トークン分割問題
    NORMALIZE = "NORMALIZE"    # 正規化辞書不足
    PROMPT = "PROMPT"          # プロンプト設計問題
    MODEL = "MODEL"            # モデル出力不安定
    DATA_DRIFT = "DATA_DRIFT"  # データ品質劣化
    FLAKY = "FLAKY"           # 再現性のない偶発的失敗
    INFRA = "INFRA"           # インフラ・環境問題

class Freshness(Enum):
    """失敗の新規性分類"""
    NEW = "NEW"        # 新規失敗
    REPEAT = "REPEAT"  # 再発失敗

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

def build_failure_history() -> Dict[str, Set[str]]:
    """過去の失敗履歴を構築（case_id -> 失敗した日付のセット）"""
    logs_dir = Path("tests/golden/logs")
    failure_history = {}
    
    if not logs_dir.exists():
        return failure_history
    
    # 全ログファイルを日付順でスキャン
    log_files = sorted(logs_dir.glob("*.jsonl"), key=lambda x: x.stem)
    
    for log_file in log_files:
        date_str = log_file.stem  # YYYYMMDD_HHMMSS形式
        date_part = date_str.split('_')[0]  # YYYYMMDD部分を取得
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if not data.get('passed', True):  # 失敗ケース
                            case_id = data.get('id', '')
                            if case_id:
                                if case_id not in failure_history:
                                    failure_history[case_id] = set()
                                failure_history[case_id].add(date_part)
                    except json.JSONDecodeError:
                        continue
    
    return failure_history

def infer_freshness(case_id: str, current_date: str, history: Dict[str, Set[str]]) -> Freshness:
    """失敗の新規性を判定"""
    if case_id not in history:
        return Freshness.NEW
    
    # 当日以前に失敗履歴があるかチェック
    past_failures = history[case_id]
    for past_date in past_failures:
        if past_date < current_date:  # 文字列比較でYYYYMMDD順序
            return Freshness.REPEAT
    
    return Freshness.NEW

def apply_freshness_to_log(log_path: Path = None):
    """観測ログにfreshnessタグを追記"""
    if log_path is None:
        log_path = Path("tests/golden/observation_log.md")
    
    if not log_path.exists():
        print(f"観測ログが見つかりません: {log_path}")
        return
    
    # 失敗履歴を構築
    failure_history = build_failure_history()
    
    # ログファイルを読み込み
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 各失敗ケース行を検索してfreshnessを追加
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        # 失敗分析セクションの行を検索
        # 形式: - **case_id**: `root_cause:XXX` - 説明
        match = re.match(r'^- \*\*([^*]+)\*\*: `root_cause:([^`]+)` - (.+)$', line)
        if match:
            case_id = match.group(1)
            root_cause = match.group(2)
            description = match.group(3)
            
            # 日付を推定（セクションヘッダーから）
            current_date = "20250829"  # デフォルト（実際は前のセクションから取得）
            
            # freshnessを判定
            freshness = infer_freshness(case_id, current_date, failure_history)
            
            # freshnessがまだ含まれていない場合のみ追加
            if "freshness:" not in line:
                updated_line = f"- **{case_id}**: `root_cause:{root_cause}` | `freshness:{freshness.value}` - {description}"
                updated_lines.append(updated_line)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # ファイルに書き戻し
    updated_content = '\n'.join(updated_lines)
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ Freshness tags updated in {log_path}")

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

def main():
    """メイン関数（CLI対応）"""
    parser = argparse.ArgumentParser(description="Golden Test Root Cause Analyzer")
    parser.add_argument("--update-freshness", action="store_true", 
                       help="観測ログにfreshnessタグを追加")
    
    args = parser.parse_args()
    
    if args.update_freshness:
        apply_freshness_to_log()
    else:
        update_observation_log_with_analysis()

if __name__ == "__main__":
    main()
