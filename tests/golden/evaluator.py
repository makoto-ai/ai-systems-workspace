import re


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
    # 空白区切り優先。なければ正規表現抽出
    s = (s or "").strip()
    if " " in s:
        return [_normalize_token(t) for t in s.split() if t]
    return [_normalize_token(t) for t in re.findall(r"[A-Za-z0-9ぁ-んァ-ン一-龥]+", s)]


def score(reference: str, prediction: str) -> float:
    """0..1 の簡易スコア（必須キーワード被覆率）

    - reference: 必須キーワード列（空白区切り推奨）
    - prediction: モデル出力（空白区切りキーワード列を想定）
    スコア = (referenceに含まれる語のうち、predictionに含まれた語の割合)
    """
    ref = set(_tokens(reference))
    pred = set(_tokens(prediction))
    if not ref and not pred:
        return 1.0
    if not ref:
        return 0.0
    hits = len(ref & pred)
    return hits / len(ref)
