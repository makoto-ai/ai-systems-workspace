#!/usr/bin/env python3
"""
論文検索システム専用Obsidian自動保存機能（日本語化対応版）
検索結果を自動的にObsidianに保存・分類
カタカナふりがな・日本語翻訳・わかりやすいファイル名対応
"""

from ..core.paper_model import Paper
import datetime
from pathlib import Path
from typing import Dict, List
import sys
import re
import requests
import json

# 相対パスの解決
# Package-relative imports are used; no sys.path modification necessary


class ObsidianPaperSaver:
    """論文検索結果をObsidianに自動保存するクラス（日本語化対応）"""

    def __init__(self, obsidian_vault_path: str = None):
        # 日本語化機能の初期化
        self._init_japanese_support()

        # デフォルトのObsidianパスを設定（voice-roleplay-systemのdocs/obsidian-knowledge）
        if obsidian_vault_path is None:
            # paper_research_systemから相対的にvault_pathを設定
            current_dir = Path(__file__).parent.parent
            obsidian_vault_path = current_dir.parent / "docs" / "obsidian-knowledge"

        self.vault_path = Path(obsidian_vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)

        # 論文専用フォルダ構造
        self.folders = {
            "research-papers": self.vault_path / "research-papers",
            "sales-psychology": self.vault_path
            / "research-papers"
            / "sales-psychology",
            "management-psychology": self.vault_path
            / "research-papers"
            / "management-psychology",
            "behavioral-economics": self.vault_path
            / "research-papers"
            / "behavioral-economics",
            "general-psychology": self.vault_path
            / "research-papers"
            / "general-psychology",
            "search-sessions": self.vault_path / "research-papers" / "search-sessions",
        }

        # フォルダ作成
        for folder in self.folders.values():
            folder.mkdir(parents=True, exist_ok=True)

        # ドメインとフォルダのマッピング
        self.domain_mapping = {
            "sales_psychology": "sales-psychology",
            "management_psychology": "management-psychology",
            "behavioral_economics": "behavioral-economics",
            "general_human_psychology": "general-psychology",
        }

        # 思考モードタグ
        self.thinking_mode_tags = {
            "thesis": "テーゼ",
            "antithesis": "アンチテーゼ",
            "synthesis": "ジンテーゼ",
            "meta_analysis": "メタ分析",
        }

    def _init_japanese_support(self):
        """日本語化サポート機能の初期化"""
        # 英語名→カタカナ変換辞書（一般的な研究者名）
        self.name_katakana_dict = {
            "John": "ジョン",
            "Jane": "ジェーン",
            "Michael": "マイケル",
            "David": "デヴィッド",
            "Robert": "ロバート",
            "William": "ウィリアム",
            "Richard": "リチャード",
            "Thomas": "トーマス",
            "Christopher": "クリストファー",
            "Daniel": "ダニエル",
            "Matthew": "マシュー",
            "Anthony": "アンソニー",
            "Mark": "マーク",
            "Donald": "ドナルド",
            "Steven": "スティーブン",
            "Paul": "ポール",
            "Andrew": "アンドリュー",
            "Joshua": "ジョシュア",
            "Kenneth": "ケネス",
            "Kevin": "ケビン",
            "Brian": "ブライアン",
            "George": "ジョージ",
            "Edward": "エドワード",
            "Ronald": "ロナルド",
            "Timothy": "ティモシー",
            "Jason": "ジェイソン",
            "Jeffrey": "ジェフリー",
            "Ryan": "ライアン",
            "Jacob": "ジェイコブ",
            "Gary": "ゲアリー",
            "Nicholas": "ニコラス",
            "Eric": "エリック",
            "Jonathan": "ジョナサン",
            "Stephen": "スティーブン",
            "Larry": "ラリー",
            "Justin": "ジャスティン",
            "Scott": "スコット",
            "Brandon": "ブランドン",
            "Benjamin": "ベンジャミン",
            "Samuel": "サミュエル",
            "Frank": "フランク",
            "Gregory": "グレゴリー",
            "Raymond": "レイモンド",
            "Alexander": "アレクサンダー",
            "Patrick": "パトリック",
            "Jack": "ジャック",
            "Dennis": "デニス",
            "Jerry": "ジェリー",
            "Mary": "メアリー",
            "Patricia": "パトリシア",
            "Jennifer": "ジェニファー",
            "Linda": "リンダ",
            "Elizabeth": "エリザベス",
            "Barbara": "バーバラ",
            "Susan": "スーザン",
            "Jessica": "ジェシカ",
            "Sarah": "サラ",
            "Karen": "カレン",
            "Nancy": "ナンシー",
            "Lisa": "リサ",
            "Betty": "ベティ",
            "Helen": "ヘレン",
            "Sandra": "サンドラ",
            "Donna": "ドナ",
            "Carol": "キャロル",
            "Ruth": "ルース",
            "Sharon": "シャロン",
            "Michelle": "ミシェル",
            "Laura": "ローラ",
            "Sarah": "サラ",
            "Kimberly": "キンバリー",
            "Deborah": "デボラ",
            "Dorothy": "ドロシー",
            "Amy": "エイミー",
            "Angela": "アンジェラ",
            "Ashley": "アシュリー",
            "Brenda": "ブレンダ",
            "Emma": "エマ",
            "Olivia": "オリビア",
            "Cynthia": "シンシア",
        }

        # 学術用語翻訳辞書
        self.academic_translation_dict = {
            "Abstract": "要約",
            "Introduction": "序論",
            "Methods": "手法",
            "Results": "結果",
            "Discussion": "考察",
            "Conclusion": "結論",
            "References": "参考文献",
            "Keywords": "キーワード",
            "Background": "背景",
            "Methodology": "方法論",
            "Analysis": "分析",
            "Findings": "知見",
            "Implications": "示唆",
            "Limitations": "限界",
            "Future work": "今後の課題",
            "Data": "データ",
            "Statistics": "統計",
            "Survey": "調査",
            "Study": "研究",
            "Research": "研究",
            "Business": "ビジネス",
            "Management": "マネジメント",
            "Psychology": "心理学",
            "Economics": "経済学",
            "Marketing": "マーケティング",
            "Sales": "営業",
            "Leadership": "リーダーシップ",
            "Organization": "組織",
            "Strategy": "戦略",
            "Performance": "パフォーマンス",
            "Success": "成功",
            "Failure": "失敗",
            "Growth": "成長",
            "Development": "発展",
            "Innovation": "イノベーション",
            "Entrepreneurship": "起業家精神",
            "Startup": "スタートアップ",
            "Enterprise": "企業",
        }

        # 検索クエリ→日本語ファイル名変換辞書
        self.query_japanese_dict = {
            "business failure": "事業失敗統計",
            "startup survival": "スタートアップ生存率",
            "entrepreneur development": "起業家発展段階",
            "small business": "中小企業研究",
            "success timeline": "成功タイムライン",
            "leadership coaching": "リーダーシップコーチング",
            "sales psychology": "営業心理学",
            "management": "マネジメント研究",
            "innovation": "イノベーション研究",
            "growth strategy": "成長戦略",
            "business model": "ビジネスモデル",
            "organizational behavior": "組織行動",
            "performance management": "パフォーマンス管理",
        }

    def _convert_name_to_katakana(self, name: str) -> str:
        """英語名をカタカナに変換"""
        if not name:
            return name

        # フルネームを分割
        name_parts = name.strip().split()
        katakana_parts = []

        for part in name_parts:
            # 辞書にある場合はそれを使用
            if part in self.name_katakana_dict:
                katakana_parts.append(f"{part}（{self.name_katakana_dict[part]}）")
            else:
                # 辞書にない場合は簡易的な変換を試行
                katakana = self._simple_katakana_conversion(part)
                if katakana:
                    katakana_parts.append(f"{part}（{katakana}）")
                else:
                    katakana_parts.append(part)

        return " ".join(katakana_parts)

    def _simple_katakana_conversion(self, name: str) -> str:
        """簡易的なカタカナ変換（基本的なルールベース）"""
        if not name or len(name) < 2:
            return ""

        # 基本的な音素変換ルール
        conversion_rules = {
            "ch": "チ",
            "sh": "シ",
            "th": "ス",
            "ph": "フ",
            "a": "ア",
            "e": "エ",
            "i": "イ",
            "o": "オ",
            "u": "ウ",
            "ka": "カ",
            "ke": "ケ",
            "ki": "キ",
            "ko": "コ",
            "ku": "ク",
            "sa": "サ",
            "se": "セ",
            "si": "シ",
            "so": "ソ",
            "su": "ス",
            "ta": "タ",
            "te": "テ",
            "ti": "チ",
            "to": "ト",
            "tu": "ツ",
            "na": "ナ",
            "ne": "ネ",
            "ni": "ニ",
            "no": "ノ",
            "nu": "ヌ",
            "ha": "ハ",
            "he": "ヘ",
            "hi": "ヒ",
            "ho": "ホ",
            "hu": "フ",
            "ma": "マ",
            "me": "メ",
            "mi": "ミ",
            "mo": "モ",
            "mu": "ム",
            "ya": "ヤ",
            "ye": "イェ",
            "yi": "イ",
            "yo": "ヨ",
            "yu": "ユ",
            "ra": "ラ",
            "re": "レ",
            "ri": "リ",
            "ro": "ロ",
            "ru": "ル",
            "wa": "ワ",
            "we": "ウェ",
            "wi": "ウィ",
            "wo": "ウォ",
            "wu": "ウ",
        }

        name_lower = name.lower()

        # 既知のパターンから簡易変換を試行（限定的）
        if name_lower.endswith("son"):
            return "ソン"
        elif name_lower.endswith("man"):
            return "マン"
        elif name_lower.endswith("er"):
            return "ー"

        return ""  # 変換できない場合は空文字

    def _translate_abstract_to_japanese(self, abstract: str) -> str:
        """英語要約を日本語に翻訳"""
        if not abstract:
            return abstract

        # 最初に辞書ベースの部分翻訳を試行
        japanese_abstract = abstract
        for english_term, japanese_term in self.academic_translation_dict.items():
            japanese_abstract = re.sub(
                r"\b" + re.escape(english_term) + r"\b",
                japanese_term,
                japanese_abstract,
                flags=re.IGNORECASE,
            )

        # 簡易的な翻訳処理を追加（基本的な文構造の認識）
        if "This study" in abstract:
            japanese_abstract = japanese_abstract.replace("This study", "本研究は")
        if "The results" in abstract:
            japanese_abstract = japanese_abstract.replace("The results", "結果として")
        if "We found" in abstract:
            japanese_abstract = japanese_abstract.replace("We found", "我々は発見した")
        if "Our findings" in abstract:
            japanese_abstract = japanese_abstract.replace("Our findings", "我々の知見")

        return f"【日本語翻訳】{japanese_abstract}\n\n【原文】{abstract}"

    def _generate_japanese_filename(self, search_query: str) -> str:
        """検索クエリから日本語ファイル名を生成"""
        # まず、既知のパターンマッチング
        query_lower = search_query.lower()

        for english_pattern, japanese_title in self.query_japanese_dict.items():
            if english_pattern in query_lower:
                return japanese_title

        # パターンマッチしない場合は、キーワード翻訳を試行
        japanese_keywords = []
        words = re.split(r"[^\w]+", search_query.lower())

        for word in words:
            if word in self.academic_translation_dict:
                japanese_keywords.append(self.academic_translation_dict[word])
            elif len(word) > 2:  # 短すぎる単語は除外
                japanese_keywords.append(word)

        if japanese_keywords:
            return "_".join(
                japanese_keywords[:3]
            )  # 最大3個のキーワード（特殊文字回避）

        return "論文検索結果"  # デフォルト

    def save_search_results(
        self,
        papers: List[Paper],
        search_query: str,
        domain: str = "sales_psychology",
        thinking_mode: str = "thesis",
        metadata: Dict = None,
    ) -> Path:
        """検索結果をObsidianに保存"""

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # 日本語ファイル名生成
        japanese_title = self._generate_japanese_filename(search_query)
        filename = f"{timestamp.split()[0]}_{japanese_title}.md"

        # 保存先フォルダ決定
        folder_name = self.domain_mapping.get(domain, "research-papers")
        folder = self.folders[folder_name]

        # タグ生成
        tags = self._generate_tags(domain, thinking_mode, papers)

        # Markdownコンテンツ生成
        markdown_content = self._generate_markdown_content(
            papers, search_query, domain, thinking_mode, timestamp, tags, metadata
        )

        # ファイル保存
        file_path = folder / filename
        file_path.write_text(markdown_content, encoding="utf-8")

        print(f"📚 論文検索結果をObsidianに保存: {filename}")
        print(f"📁 カテゴリ: {folder_name}")
        print(f"📄 論文数: {len(papers)}件")

        return file_path

    def _generate_tags(
        self, domain: str, thinking_mode: str, papers: List[Paper]
    ) -> List[str]:
        """タグを自動生成"""
        tags = ["論文検索", "学術研究"]

        # ドメインタグ
        domain_tags = {
            "sales_psychology": ["営業心理学", "セールス", "顧客心理"],
            "management_psychology": [
                "マネジメント心理学",
                "リーダーシップ",
                "組織行動",
            ],
            "behavioral_economics": ["行動経済学", "意思決定", "認知バイアス"],
            "general_human_psychology": ["人間心理学", "社会心理学", "認知心理学"],
        }
        tags.extend(domain_tags.get(domain, []))

        # 思考モードタグ
        mode_tag = self.thinking_mode_tags.get(thinking_mode, thinking_mode)
        tags.append(mode_tag)

        # 論文の特徴から追加タグ
        high_citation_count = any(
            p.citation_count and p.citation_count > 1000
            for p in papers
            if p.citation_count
        )
        if high_citation_count:
            tags.append("高被引用論文")

        recent_papers = any(
            p.publication_year and p.publication_year >= 2020
            for p in papers
            if p.publication_year
        )
        if recent_papers:
            tags.append("最新研究")

        return tags

    def _generate_markdown_content(
        self,
        papers: List[Paper],
        search_query: str,
        domain: str,
        thinking_mode: str,
        timestamp: str,
        tags: List[str],
        metadata: Dict = None,
    ) -> str:
        """Markdownコンテンツを生成"""

        domain_names = {
            "sales_psychology": "営業心理学",
            "management_psychology": "マネジメント心理学",
            "behavioral_economics": "行動経済学",
            "general_human_psychology": "汎用人間心理学",
        }

        thinking_mode_names = {
            "thesis": "テーゼ（主流理論）",
            "antithesis": "アンチテーゼ（反論・新視点）",
            "synthesis": "ジンテーゼ（統合理論）",
            "meta_analysis": "メタ分析重視",
        }

        content = f"""# 📚 {search_query} - 論文検索結果

> 🔍 **検索クエリ**: {search_query}
> 📅 **検索日時**: {timestamp}
> 🎯 **専門分野**: {domain_names.get(domain, domain)}
> 🧠 **思考モード**: {thinking_mode_names.get(thinking_mode, thinking_mode)}
> 📊 **取得論文数**: {len(papers)}件

## 📋 検索概要

"""

        if metadata:
            content += f"""### 📈 検索統計
- **総検索数**: {metadata.get('total_found', 'N/A')}件
- **フィルタ後**: {metadata.get('after_filtering', 'N/A')}件
- **最終結果**: {metadata.get('final_results', len(papers))}件

"""

        content += """## 📄 論文一覧

"""

        # 各論文の詳細
        for i, paper in enumerate(papers, 1):
            content += self._format_paper(paper, i)

        # メタデータセクション
        if metadata and metadata.get("generated_queries"):
            content += f"""
## 🔍 生成された検索クエリ

{chr(10).join([f"- {query}" for query in metadata['generated_queries']])}

"""

        # タグセクション
        content += f"""
## 🏷️ タグ

{' '.join([f'#{tag}' for tag in tags])}

## 💡 活用方法

この検索結果は以下の用途で活用できます：

- **営業スキル向上**: エビデンスベースの営業手法の学習
- **マネジメント改善**: 学術的根拠に基づく組織運営
- **研修資料作成**: 論文の引用による説得力のある資料作成
- **更なる研究**: 引用文献からの関連研究の発見

## 🔗 関連リンク

- [[論文検索システム使用方法]]
- [[営業心理学研究ノート]]
- [[エビデンスベース営業戦略]]

---

*📚 この検索結果は論文検索システムにより自動生成されました*
*🔄 最新の研究については定期的な再検索をお勧めします*
"""

        return content

    def _format_paper(self, paper: Paper, index: int) -> str:
        """個別論文のフォーマット（日本語化対応）"""

        # 著者名をカタカナ付きで表示
        if paper.authors:
            author_names_with_katakana = []
            for author in paper.authors:
                katakana_name = self._convert_name_to_katakana(author.name)
                author_names_with_katakana.append(katakana_name)
            authors_display = ", ".join(author_names_with_katakana)
        else:
            authors_display = "N/A"

        content = f"""### {index}. 📄 {paper.title}

**基本情報**:
- **著者**: {authors_display}
- **発表年**: {paper.publication_year if paper.publication_year else 'N/A'}年
- **引用数**: {paper.citation_count if paper.citation_count is not None else 'N/A'}回
- **掲載ジャーナル**: {paper.journal if paper.journal else 'N/A'}

"""

        if paper.doi:
            content += f"- **DOI**: {paper.doi}\n"

        if paper.url:
            content += f"- **URL**: {paper.url}\n"

        content += "\n"

        if paper.abstract:
            # 要約を日本語翻訳
            translated_abstract = self._translate_abstract_to_japanese(paper.abstract)
            # 概要を適切な長さに制限
            if len(translated_abstract) > 500:
                translated_abstract = (
                    translated_abstract[:500]
                    + "...\n\n（続きは元論文をご確認ください）"
                )
            content += f"**要約**: \n{translated_abstract}\n\n"

        # スコア情報
        if hasattr(paper, "total_score") and paper.total_score:
            content += f"**総合スコア**: {paper.total_score:.1f}\n"

        if hasattr(paper, "domain_score") and paper.domain_score:
            content += f"**ドメインスコア**: {paper.domain_score:.1f}\n"

        if hasattr(paper, "mode_score") and paper.mode_score:
            content += f"**モードスコア**: {paper.mode_score:.1f}\n"

        content += "\n---\n\n"

        return content

    def save_search_session(self, session_data: Dict) -> Path:
        """検索セッション全体を保存"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"検索セッション_{date_stamp}.md"
        folder = self.folders["search-sessions"]

        content = f"""# 🔍 論文検索セッション

> 📅 **セッション開始**: {timestamp}
> 🎯 **検索回数**: {session_data.get('search_count', 0)}回

## 📊 セッション統計

- **総検索論文数**: {session_data.get('total_papers', 0)}件
- **ユニーク論文数**: {session_data.get('unique_papers', 0)}件
- **平均関連性スコア**: {session_data.get('avg_relevance', 0):.2f}

## 🔍 実行した検索

{chr(10).join([f"### {i + 1}. {search['query']}" + chr(10) + f"- **分野**: {search['domain']}" + chr(10) + f"- **モード**: {search['thinking_mode']}" + chr(10) + f"- **結果**: {search['result_count']}件" + chr(10) for i, search in enumerate(session_data.get('searches', []))])}

## 🏷️ タグ

#検索セッション #論文研究 #学術調査

---

*🤖 このセッション記録は自動生成されました*
"""

        file_path = folder / filename
        file_path.write_text(content, encoding="utf-8")

        print(f"📝 検索セッション記録をObsidianに保存: {filename}")

        return file_path


# 使用例とテスト用の関数


def test_obsidian_paper_saver():
    """テスト用の論文保存"""
    from ..core.paper_model import Paper, Author

    # テスト用論文データ
    test_papers = [
        Paper(
            title="The Impact of Trust on Sales Performance: A Meta-Analysis",
            authors=[Author(name="John Smith"), Author(name="Jane Doe")],
            publication_year=2023,
            citation_count=150,
            abstract="This meta-analysis examines the relationship between trust and sales performance across 50 studies...",
            journal="Journal of Sales Research",
            doi="https://doi.org/10.1000/test.2023.001",
            source_api="semantic_scholar",
        )
    ]

    saver = ObsidianPaperSaver()

    file_path = saver.save_search_results(
        papers=test_papers,
        search_query="信頼関係と営業成績",
        domain="sales_psychology",
        thinking_mode="thesis",
        metadata={"total_found": 15, "after_filtering": 8, "final_results": 1},
    )

    print(f"✅ テスト保存完了: {file_path}")


if __name__ == "__main__":
    test_obsidian_paper_saver()
