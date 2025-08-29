import re
import unicodedata
import yaml
from pathlib import Path


def load_norm_rules():
    """正規化ルールをYAMLから読み込み"""
    rules_file = Path("out/norm_rule_candidates.yaml")
    if rules_file.exists():
        try:
            with open(rules_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            pass
    return {}

def normalize_text(text: str) -> str:
    """テキストの高度正規化"""
    if not text:
        return ""
    
    # NFKC正規化（全角/半角統一）
    text = unicodedata.normalize('NFKC', text)
    
    # casefold（大小文字統一）
    text = text.casefold()
    
    # 空白圧縮
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 正規化ルール適用
    rules = load_norm_rules()
    
    # 記号・句読点統一
    punct_mapping = rules.get('normalization', {}).get('punctuation_mapping', {})
    for original, normalized in punct_mapping.items():
        text = text.replace(original, normalized)
    
    # 単位統一
    unit_mapping = rules.get('normalization', {}).get('unit_mapping', {})
    for original, normalized in unit_mapping.items():
        text = text.replace(original, normalized)
    
    return text

def match_numbers(text1: str, text2: str, abs_threshold: float = 1.0, rel_threshold: float = 0.05) -> bool:
    """数値の近似マッチング"""
    # 数値を抽出
    nums1 = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', text1)]
    nums2 = [float(x) for x in re.findall(r'\d+(?:\.\d+)?', text2)]
    
    if not nums1 or not nums2:
        return len(nums1) == len(nums2)  # 両方とも数値なしなら一致
    
    # 各数値ペアで近似チェック
    for num1 in nums1:
        found_match = False
        for num2 in nums2:
            abs_diff = abs(num1 - num2)
            rel_diff = abs_diff / max(abs(num1), abs(num2), 1e-10)
            
            if abs_diff <= abs_threshold or rel_diff <= rel_threshold:
                found_match = True
                break
        
        if not found_match:
            return False
    
    return True

def apply_synonyms(tokens: set, synonyms_dict: dict) -> set:
    """同義語を適用してトークンセットを拡張"""
    expanded_tokens = tokens.copy()
    
    for token in tokens:
        for key, synonyms in synonyms_dict.items():
            if token == key:
                expanded_tokens.update(synonyms)
            elif token in synonyms:
                expanded_tokens.add(key)
                expanded_tokens.update(synonyms)
    
    return expanded_tokens

def similarity_gate(reference: str, prediction: str, threshold: float = 0.92) -> bool:
    """類似度ゲート：正規化後の類似度が高い場合はNORMALIZEパス扱い"""
    if not reference or not prediction:
        return False
    
    # 正規化適用
    norm_ref = normalize_text(reference)
    norm_pred = normalize_text(prediction)
    
    # トークン化
    ref_tokens = set(norm_ref.split())
    pred_tokens = set(norm_pred.split())
    
    # 同義語適用
    rules = load_norm_rules()
    synonyms = rules.get('synonyms', {})
    
    ref_tokens = apply_synonyms(ref_tokens, synonyms)
    pred_tokens = apply_synonyms(pred_tokens, synonyms)
    
    # Jaccard類似度計算
    if not ref_tokens and not pred_tokens:
        return True
    if not ref_tokens or not pred_tokens:
        return False
    
    intersection = len(ref_tokens & pred_tokens)
    union = len(ref_tokens | pred_tokens)
    jaccard = intersection / union
    
    return jaccard >= threshold


_NORM_MAP = {
    # English variants
    "black hole": "blackhole",
    "blackhole": "blackhole",
    # Japanese variants
    "ブラックホール": "blackhole",
    # Whisper/Obsidian canonical
    "whisper": "whisper",
    "obsidian": "obsidian",
    # generic normalizations could be extended here
    # CI/DevOps variants
    "ci": "ci",
    "ci整備": "ci",
    "ci/cd": "ci",
    "cicd": "ci",
    "ci_cd": "ci",
    "continuous integration": "ci",
    # Roleplay variants
    "営業ロープレ": "営業ロープレ",
    "営業ロールプレイ": "営業ロープレ",
    "営業ロープレイ": "営業ロープレ",
    "roleplay": "営業ロープレ",
    "voice roleplay": "営業ロープレ",
    # Automation variants
    "自動化": "自動化",
    "automation": "自動化",
    # Safety/guardrails variants
    "暴走防止": "暴走防止",
    "暴走対策": "暴走防止",
    "ガードレール": "暴走防止",
    "安全": "暴走防止",
    # Structure/config variants
    "構成": "構成",
    "config": "構成",
    # Quality/Testing variants
    "品質ゲート": "品質ゲート",
    "テスト強化": "テスト強化",
    "テスト": "テスト",
    "品質向上": "品質向上",
    "品質": "品質",
    # Security variants
    "セキュリティ検知": "セキュリティ検知",
    "セキュリティ": "セキュリティ",
    "脆弱性": "脆弱性",
    "チェック": "チェック",
    # Process improvement variants
    "無駄削減": "無駄削減",
    "効率化": "効率化",
    "最適化": "最適化",
    "改善": "改善",
    # Learning/AI variants
    "学習改善": "学習改善",
    "学習": "学習改善",  # 学習 → 学習改善 に正規化
    "精度": "精度",
    "モデル精度": "モデル精度",
    "向上": "向上",
    "モデル": "モデル",
    "ai": "aiシステム",  # AI → AIシステム に正規化
    "aiシステム": "aiシステム",
    # Dashboard/Analytics variants
    "分析ダッシュボード": "分析ダッシュボード",
    "ダッシュボード": "分析ダッシュボード",
    "分析": "分析ダッシュボード",  # 分析 → 分析ダッシュボード に正規化（複合語優先）
    "可視化": "可視化",
    "メトリクス": "メトリクス",
    "監視": "監視",
    # Feedback/Response variants
    "フィードバック効率化": "フィードバック効率化",
    "フィードバック": "フィードバック効率化",
    "レスポンス時間": "レスポンス時間",
    "短縮": "短縮",
    # DevOps variants
    "デプロイ": "デプロイ",
    "devops": "devops",
    "統合": "統合",
    "プロセス": "プロセス",
    "開発プロセス": "プロセス",
    "機能": "機能",
    "システム": "システム",
}


def _normalize_token(t: str) -> str:
    tl = (t or "").lower().strip()
    # collapse multiple spaces inside tokens (if any)
    tl = re.sub(r"\s+", " ", tl)
    # direct map
    return _NORM_MAP.get(tl, tl)


def _tokens(s: str) -> list[str]:
    # 高度正規化を適用
    s = normalize_text(s or "")
    if " " in s:
        return [_normalize_token(t) for t in s.split() if t]
    return [_normalize_token(t) for t in re.findall(r"[A-Za-z0-9ぁ-んァ-ン一-龥]+", s)]


def score(reference: str, prediction: str) -> float:
    """0..1 の簡易スコア（必須キーワード被覆率）

    - reference: 必須キーワード列（空白区切り推奨）
    - prediction: モデル出力（空白区切りキーワード列を想定）
    スコア = (referenceに含まれる語のうち、predictionに含まれた語の割合)
    
    強化版：
    1. 高度正規化適用
    2. 類似度ゲートでNORMALIZE救済
    3. 数値近似マッチング
    4. 同義語展開
    """
    # 類似度ゲートチェック（NORMALIZE救済）
    if similarity_gate(reference, prediction, threshold=0.92):
        return 1.0  # 正規化で解決可能 → 合格扱い
    
    # 数値近似チェック
    if match_numbers(reference, prediction):
        # 数値が近似一致する場合はボーナス
        base_score = _calculate_base_score(reference, prediction)
        return min(1.0, base_score + 0.1)  # 10%ボーナス
    
    return _calculate_base_score(reference, prediction)

def _calculate_base_score(reference: str, prediction: str) -> float:
    """基本スコア計算"""
    ref = set(_tokens(reference))
    pred = set(_tokens(prediction))
    
    # 同義語展開
    rules = load_norm_rules()
    synonyms = rules.get('synonyms', {})
    
    ref = apply_synonyms(ref, synonyms)
    pred = apply_synonyms(pred, synonyms)
    
    if not ref and not pred:
        return 1.0
    if not ref:
        return 0.0
    
    hits = len(ref & pred)
    return hits / len(ref)
