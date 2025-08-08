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
            "educational": self._get_educational_template()
        }
    
    def create_prompt_from_metadata(self, metadata: PaperMetadata, style: str = "popular") -> str:
        """
        論文メタデータからYouTube用原稿プロンプトを生成
        
        Args:
            metadata: 論文メタデータ
            style: プロンプトスタイル ("academic", "popular", "business", "educational")
        
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
    prompt = generator.create_prompt_from_metadata(sample_metadata, "popular")
    print("生成されたプロンプト:")
    print(prompt) 