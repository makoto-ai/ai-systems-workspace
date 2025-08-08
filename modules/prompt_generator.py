"""
論文メタデータからYouTube用原稿プロンプトを生成するモジュール
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PaperMetadata:
    """論文メタデータの構造体"""
    title: str
    authors: List[str]
    abstract: str
    doi: Optional[str] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    citation_count: Optional[int] = None
    institutions: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


class PromptGenerator:
    """論文メタデータからYouTube用原稿プロンプトを生成するクラス"""
    
    def __init__(self):
        self.template_prompts = {
            "academic": self._get_academic_template(),
            "popular": self._get_popular_template(),
            "business": self._get_business_template(),
            "educational": self._get_educational_template(),
            "comprehensive": self._get_comprehensive_template(),  # 20分以上の長編
            "deep_dive": self._get_deep_dive_template(),        # 30分以上の詳細版
            "lecture": self._get_lecture_template()             # 45分以上の講義形式
        }
    
    def create_prompt_from_metadata(self, metadata: PaperMetadata, style: str = "popular") -> str:
        """
        論文メタデータからYouTube用原稿プロンプトを生成
        
        Args:
            metadata: 論文メタデータ
            style: プロンプトスタイル ("academic", "popular", "business", "educational", "comprehensive", "deep_dive", "lecture")
        
        Returns:
            生成されたプロンプト文字列
        """
        template = self.template_prompts.get(style, self.template_prompts["popular"])
        
        # メタデータから情報を抽出
        context_info = self._extract_context_info(metadata)
        
        # プロンプトを構築
        prompt = template.format(
            title=metadata.title,
            authors=", ".join(metadata.authors[:3]),  # 最初の3人の著者のみ
            abstract=metadata.abstract,
            year=metadata.publication_year or "最近",
            journal=metadata.journal or "学術誌",
            citations=metadata.citation_count or 0,
            institutions=", ".join(metadata.institutions[:2]) if metadata.institutions else "研究機関",
            keywords=", ".join(metadata.keywords[:5]) if metadata.keywords else "",
            context=context_info
        )
        
        return prompt
    
    def _extract_context_info(self, metadata: PaperMetadata) -> str:
        """メタデータからコンテキスト情報を抽出"""
        context_parts = []
        
        if metadata.citation_count and metadata.citation_count > 50:
            context_parts.append(f"この研究は{metadata.citation_count}回以上引用されている重要な論文です")
        
        if metadata.institutions:
            context_parts.append(f"研究機関: {', '.join(metadata.institutions[:2])}")
        
        if metadata.keywords:
            context_parts.append(f"キーワード: {', '.join(metadata.keywords[:3])}")
        
        return " ".join(context_parts) if context_parts else "最新の研究結果です"
    
    def _get_academic_template(self) -> str:
        """学術的なスタイルのテンプレート"""
        return """以下の学術論文の内容を基に、専門的なYouTube原稿を作成してください。

論文情報:
- タイトル: {title}
- 著者: {authors}
- 発表年: {year}
- 掲載誌: {journal}
- 引用数: {citations}
- 研究機関: {institutions}
- キーワード: {keywords}

論文要約:
{abstract}

コンテキスト情報:
{context}

要求事項:
1. 学術的な正確性を保ちながら、専門外の視聴者にも理解できるように説明
2. 研究の背景、方法、結果、意義を体系的に整理
3. 専門用語は適切に説明を加える
4. 視聴者の知識レベルを考慮した段階的な説明
5. 研究の実用性や将来への影響についても言及

出力形式:
- 動画時間: 15-20分
- 構成: 導入(2分) → 背景(3分) → 方法(5分) → 結果(5分) → 考察(3分) → まとめ(2分)
- トーン: 専門的だが親しみやすい"""
    
    def _get_popular_template(self) -> str:
        """一般向けスタイルのテンプレート"""
        return """以下の研究論文を基に、一般視聴者向けの魅力的なYouTube原稿を作成してください。

研究情報:
- 研究タイトル: {title}
- 研究者: {authors}
- 発表年: {year}
- 研究機関: {institutions}
- 研究分野: {keywords}

研究内容:
{abstract}

背景情報:
{context}

要求事項:
1. 視聴者の日常生活に関連付けて説明
2. 衝撃的な発見や意外な結果を強調
3. 具体例や比喩を使って分かりやすく説明
4. 視聴者の好奇心を刺激する構成
5. 「なぜこの研究が重要なのか」を明確に伝える

出力形式:
- 動画時間: 10-15分
- 構成: フック(30秒) → 問題提起(2分) → 研究紹介(5分) → 結果解説(5分) → 影響・展望(2分) → まとめ(30秒)
- トーン: 親しみやすく、興味を引く"""
    
    def _get_business_template(self) -> str:
        """ビジネス向けスタイルのテンプレート"""
        return """以下の研究論文を基に、ビジネスパーソン向けの実用的なYouTube原稿を作成してください。

研究情報:
- 研究タイトル: {title}
- 研究者: {authors}
- 発表年: {year}
- 研究機関: {institutions}
- 分野: {keywords}

研究概要:
{abstract}

ビジネス関連情報:
{context}

要求事項:
1. ビジネスへの応用可能性を重点的に説明
2. 投資対効果や市場機会について言及
3. 実践的なアクションプランを提示
4. 競合優位性や差別化要因を明確化
5. リスクと機会の両面をバランスよく説明

出力形式:
- 動画時間: 12-18分
- 構成: ビジネス課題(2分) → 研究紹介(4分) → 応用可能性(6分) → 実装戦略(4分) → 投資判断(2分)
- トーン: 実践的で戦略的"""
    
    def _get_educational_template(self) -> str:
        """教育向けスタイルのテンプレート"""
        return """以下の研究論文を基に、教育目的のYouTube原稿を作成してください。

研究情報:
- 研究タイトル: {title}
- 研究者: {authors}
- 発表年: {year}
- 研究機関: {institutions}
- 分野: {keywords}

研究内容:
{abstract}

教育関連情報:
{context}

要求事項:
1. 学習目標を明確に設定
2. 段階的な学習プロセスを提示
3. 実践的な演習や課題を組み込む
4. 学習者の理解度を確認するポイントを設定
5. さらなる学習のためのリソースを提供

出力形式:
- 動画時間: 20-30分
- 構成: 学習目標(1分) → 基礎知識(5分) → 研究紹介(8分) → 実践演習(10分) → 理解確認(3分) → 次回予告(3分)
- トーン: 教育的で体系的"""
    
    def _get_comprehensive_template(self) -> str:
        """包括的スタイルのテンプレート（20分以上）"""
        return """以下の研究論文を基に、包括的で詳細なYouTube原稿を作成してください。

研究情報:
- 研究タイトル: {title}
- 研究者: {authors}
- 発表年: {year}
- 研究機関: {institutions}
- 分野: {keywords}

研究内容:
{abstract}

包括的解説情報:
{context}

要求事項:
1. 研究の全貌を包括的に解説
2. 背景から応用まで、すべての側面を詳しく説明
3. 関連研究や先行研究との比較も含める
4. 実践的な応用例を多数提示
5. 将来の研究方向や可能性についても言及

出力形式:
- 動画時間: 25-35分
- 構成: 
  - 導入・問題提起(3分)
  - 研究背景・先行研究(5分)
  - 研究手法・理論的枠組み(8分)
  - 実験・分析結果(8分)
  - 考察・解釈(5分)
  - 応用・実践例(3分)
  - 今後の展望(2分)
  - まとめ(1分)
- トーン: 詳細で包括的、専門的だが理解しやすい"""
    
    def _get_deep_dive_template(self) -> str:
        """深掘りスタイルのテンプレート（30分以上）"""
        return """以下の研究論文を基に、深掘り解説のYouTube原稿を作成してください。

研究情報:
- 研究タイトル: {title}
- 研究者: {authors}
- 発表年: {year}
- 研究機関: {institutions}
- 分野: {keywords}

研究内容:
{abstract}

深掘り解説情報:
{context}

要求事項:
1. 研究の核心部分を徹底的に深掘り
2. 技術的詳細や数式も分かりやすく説明
3. 実験の各段階を詳細に解説
4. 失敗や課題も含めて、研究のリアルな側面を紹介
5. 視聴者が研究者の思考プロセスを追体験できる構成

出力形式:
- 動画時間: 35-45分
- 構成:
  - 導入・研究の重要性(4分)
  - 理論的背景・先行研究の詳細(8分)
  - 研究手法の技術的詳細(10分)
  - 実験・分析の詳細プロセス(10分)
  - 結果の詳細解釈(6分)
  - 技術的課題・限界(3分)
  - 今後の研究方向性(2分)
  - まとめ・質疑応答(2分)
- トーン: 専門的で詳細、技術的だが理解しやすい"""
    
    def _get_lecture_template(self) -> str:
        """講義形式のテンプレート（45分以上）"""
        return """以下の研究論文を基に、大学講義レベルの詳細なYouTube原稿を作成してください。

研究情報:
- 研究タイトル: {title}
- 研究者: {authors}
- 発表年: {year}
- 研究機関: {institutions}
- 分野: {keywords}

研究内容:
{abstract}

講義形式解説情報:
{context}

要求事項:
1. 大学講義レベルの詳細な解説
2. 基礎理論から応用まで体系的に説明
3. 数式や技術的詳細も含めて完全解説
4. 関連分野との接続点も明示
5. 学生が独学できるレベルの詳細さ

出力形式:
- 動画時間: 50-60分
- 構成:
  - 講義概要・学習目標(3分)
  - 基礎理論・概念の詳細解説(12分)
  - 研究背景・先行研究の包括的レビュー(10分)
  - 研究手法・理論的枠組みの詳細(15分)
  - 実験・分析・結果の詳細解説(12分)
  - 考察・解釈・応用可能性(5分)
  - 今後の研究課題・発展方向(2分)
  - まとめ・復習ポイント(1分)
- トーン: 学術的で体系的、教育効果を重視"""


def create_prompt_from_metadata(metadata: PaperMetadata, style: str = "popular") -> str:
    """
    論文メタデータからプロンプトを生成する便利関数
    
    Args:
        metadata: 論文メタデータ
        style: プロンプトスタイル
    
    Returns:
        生成されたプロンプト
    """
    generator = PromptGenerator()
    return generator.create_prompt_from_metadata(metadata, style)


if __name__ == "__main__":
    # テスト用のサンプルデータ
    sample_metadata = PaperMetadata(
        title="機械学習を用いた営業効率化の研究",
        authors=["田中太郎", "佐藤花子", "鈴木一郎"],
        abstract="本研究では、機械学習技術を用いて営業活動の効率化を図る手法を提案する。顧客データの分析により、成約率を30%向上させることに成功した。",
        doi="10.1000/example.2023.001",
        publication_year=2023,
        journal="営業科学ジャーナル",
        citation_count=45,
        institutions=["東京大学", "営業研究所"],
        keywords=["機械学習", "営業効率化", "顧客分析", "成約率向上"]
    )
    
    generator = PromptGenerator()
    prompt = generator.create_prompt_from_metadata(sample_metadata, "comprehensive")
    print("生成されたプロンプト:")
    print(prompt) 