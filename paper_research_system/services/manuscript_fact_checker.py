#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📝 原稿事実確認・添削システム
YouTube原稿のハルシネーション検出と信頼性向上

Features:
- 原稿から主張・データ・研究名を自動抽出
- 論文検索による事実確認
- ハルシネーション検出
- 代替エビデンス検索
- 文体保持リライター
"""

import re
import json
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import datetime
from dataclasses import dataclass
import asyncio

from services.safe_rate_limited_search_service import get_safe_rate_limited_search_service
from services.obsidian_paper_saver import ObsidianPaperSaver


@dataclass
class ExtractedClaim:
    """抽出された主張"""
    claim_type: str  # "研究結果", "統計", "定義", "主張"
    content: str
    researcher_name: Optional[str] = None
    publication_year: Optional[str] = None
    statistic_value: Optional[str] = None
    confidence_level: str = "medium"  # high, medium, low


@dataclass
class FactCheckResult:
    """事実確認結果"""
    original_claim: ExtractedClaim
    is_hallucination: bool
    evidence_papers: List[Any]
    alternative_evidence: List[Any]
    verification_score: float  # 0-1
    recommendation: str


class ManuscriptFactChecker:
    """原稿事実確認システム"""

    def __init__(self):
        """初期化"""
        self.search_service = get_safe_rate_limited_search_service()
        self.obsidian_saver = ObsidianPaperSaver()
        
        # 研究者名パターン（英語重視）
        self.researcher_patterns = [
            r'According to ([A-Za-z]+(?:\s+[A-Za-z]+)*)',
            r'([A-Za-z]+)\s+and\s+([A-Za-z]+)',
            r"([A-Za-z]+(?:\s+and\s+[A-Za-z]+)*)'s\s+\d{4}\s+(?:study|research|paper)",
        ]
        
        # 年代パターン（英語重視）
        self.year_patterns = [
            r'(\d{4})\s*study',
            r'(\d{4})\s*research',
            r'(\d{4})年',
        ]
        
        # 統計パターン
        self.statistic_patterns = [
            r'(\d+(?:\.\d+)?(?:〜|～|-)?\d*(?:\.\d+)?)(?:%|％|パーセント)',
            r'(\d+(?:\.\d+)?(?:倍|回|件|人|社))',
            r'約?(\d+(?:\.\d+)?(?:〜|～|-)?\d*(?:\.\d+)?)(?:%|％|パーセント)',
        ]
        
        # 主張パターン
        self.claim_patterns = [
            r'([^。]*?)(?:ことが|という|そうです|と言われています|ことが分かりました)',
            r'([^。]*?)(?:を示しています|が明らかになりました|ことが判明)',
            r'([^。]*?)(?:研究では|調査では|によると)',
        ]

    def extract_claims_from_manuscript(self, manuscript: str) -> List[ExtractedClaim]:
        """原稿から主張を抽出"""
        print(f"📋 原稿分析開始: '{manuscript}'")
        claims = []
        sentences = self._split_into_sentences(manuscript)
        print(f"📋 文数: {len(sentences)}")
        
        for sentence in sentences:
            print(f"\n📋 文処理: '{sentence}'")
            # 研究者名を抽出
            researchers = self._extract_researchers(sentence)
            print(f"  研究者: {researchers}")
            
            # 年代を抽出
            years = self._extract_years(sentence)
            print(f"  年代: {years}")
            
            # 統計を抽出
            statistics = self._extract_statistics(sentence)
            
            # 主張を抽出
            claim_content = self._extract_claim_content(sentence)
            
            if claim_content or researchers or statistics:
                claim = ExtractedClaim(
                    claim_type=self._determine_claim_type(sentence),
                    content=sentence,
                    researcher_name=researchers[0] if researchers else None,
                    publication_year=years[0] if years else None,
                    statistic_value=statistics[0] if statistics else None,
                    confidence_level=self._assess_confidence(sentence)
                )
                claims.append(claim)
        
        return claims

    def fact_check_claims(self, claims: List[ExtractedClaim]) -> List[FactCheckResult]:
        """主張の事実確認"""
        results = []
        
        for claim in claims:
            # 論文検索クエリを生成
            search_queries = self._generate_search_queries(claim)
            
            # 各クエリで検索
            all_evidence = []
            search_successful = False
            
            for query in search_queries:
                try:
                    papers = asyncio.run(
                        self.search_service.search_papers(query, max_results=5)
                    )
                    all_evidence.extend(papers)
                    search_successful = True
                except Exception as e:
                    print(f"⚠️ 検索エラー: {e}")
            
            # 検索が完全に失敗した場合は強制的にハルシネーション判定
            if not search_successful:
                print(f"🚨 全ての検索が失敗: {claim.content[:50]}... → ハルシネーション判定")
                all_evidence = []
            
            # ハルシネーション判定
            is_hallucination = self._detect_hallucination(claim, all_evidence)
            
            # 代替エビデンス検索
            alternative_evidence = []
            if is_hallucination or len(all_evidence) < 2:
                alternative_evidence = self._search_alternative_evidence(claim)
            
            # 検証スコア計算
            verification_score = self._calculate_verification_score(claim, all_evidence)
            
            # 推奨事項生成
            recommendation = self._generate_recommendation(claim, all_evidence, is_hallucination)
            
            result = FactCheckResult(
                original_claim=claim,
                is_hallucination=is_hallucination,
                evidence_papers=all_evidence,
                alternative_evidence=alternative_evidence,
                verification_score=verification_score,
                recommendation=recommendation
            )
            results.append(result)
        
        return results

    def generate_corrected_manuscript(self, 
                                    original_manuscript: str,
                                    fact_check_results: List[FactCheckResult]) -> str:
        """修正版原稿を生成"""
        corrected_manuscript = original_manuscript
        
        # ハルシネーション箇所を修正
        for result in fact_check_results:
            if result.is_hallucination:
                # 代替エビデンスで置き換え
                replacement = self._create_evidence_based_replacement(result)
                corrected_manuscript = self._replace_maintaining_style(
                    corrected_manuscript,
                    result.original_claim.content,
                    replacement
                )
            elif result.verification_score < 0.5:
                # 信頼性を強化
                enhancement = self._enhance_credibility(result)
                corrected_manuscript = self._enhance_text_maintaining_style(
                    corrected_manuscript,
                    result.original_claim.content,
                    enhancement
                )
        
        # YouTube最適化
        corrected_manuscript = self._optimize_for_youtube(corrected_manuscript)
        
        return corrected_manuscript

    def _split_into_sentences(self, text: str) -> List[str]:
        """文章を文単位に分割"""
        sentences = re.split(r'[。！？]', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_researchers(self, sentence: str) -> List[str]:
        """研究者名を抽出"""
        print(f"🔍 研究者名抽出: '{sentence}'")
        researchers = []
        
        for i, pattern in enumerate(self.researcher_patterns):
            matches = re.findall(pattern, sentence)
            print(f"  パターン{i+1}: {matches}")
            
            if matches:
                if isinstance(matches[0], tuple):
                    # タプル: Smith and Johnson → ('Smith', 'Johnson')
                    for match in matches:
                        combined_name = " ".join([name.strip() for name in match if name.strip()])
                        if combined_name:
                            researchers.append(combined_name)
                else:
                    # 文字列: According to Smith and Johnson → 'Smith and Johnson'
                    researchers.extend([m.strip() for m in matches if m.strip()])
        
        unique = list(set(researchers))
        print(f"🔍 最終結果: {unique}")
        return unique

    def _extract_years(self, sentence: str) -> List[str]:
        """年代を抽出"""
        print(f"🔍 年代抽出: '{sentence}'")
        years = []
        
        for i, pattern in enumerate(self.year_patterns):
            matches = re.findall(pattern, sentence)
            print(f"  年代パターン{i+1}: {matches}")
            years.extend(matches)
        
        unique = list(set(years))
        print(f"🔍 最終結果: {unique}")
        return unique

    def _extract_statistics(self, sentence: str) -> List[str]:
        """統計値を抽出"""
        statistics = []
        for pattern in self.statistic_patterns:
            matches = re.findall(pattern, sentence)
            statistics.extend(matches)
        return list(set(statistics))

    def _extract_claim_content(self, sentence: str) -> str:
        """主張内容を抽出"""
        for pattern in self.claim_patterns:
            match = re.search(pattern, sentence)
            if match:
                return match.group(1).strip()
        return sentence

    def _determine_claim_type(self, sentence: str) -> str:
        """主張の種類を判定"""
        if re.search(r'研究|論文|調査', sentence):
            return "研究結果"
        elif re.search(r'%|％|パーセント|倍|回', sentence):
            return "統計"
        elif re.search(r'とは|という|定義', sentence):
            return "定義"
        else:
            return "主張"

    def _assess_confidence(self, sentence: str) -> str:
        """信頼度を評価"""
        high_confidence_markers = ['研究によると', '論文では', 'データによると', '調査結果']
        medium_confidence_markers = ['と言われています', 'そうです', 'とされています']
        low_confidence_markers = ['らしい', 'のようです', '思います', '感じます']
        
        for marker in high_confidence_markers:
            if marker in sentence:
                return "high"
        for marker in medium_confidence_markers:
            if marker in sentence:
                return "medium"
        for marker in low_confidence_markers:
            if marker in sentence:
                return "low"
        return "medium"

    def _generate_search_queries(self, claim: ExtractedClaim) -> List[str]:
        """検索クエリを生成"""
        queries = []
        
        # 具体的な研究者名と年代がある場合は、それを最優先で厳密チェック
        if claim.researcher_name and claim.publication_year:
            # メインクエリ: 研究者名 + 年代
            queries.append(f"{claim.researcher_name} {claim.publication_year}")
            
            # バリエーション: 研究者名のみ
            if claim.researcher_name:
                queries.append(claim.researcher_name)
                
            print(f"🔍 具体的研究を検証: '{claim.researcher_name}' ({claim.publication_year}年)")
            return queries
        
        # 研究者名のみの場合
        elif claim.researcher_name:
            queries.append(claim.researcher_name)
            print(f"🔍 研究者を検証: '{claim.researcher_name}'")
            return queries
        
        # 年代のみの場合は内容ベースクエリも追加
        elif claim.publication_year:
            print(f"🔍 年代指定あり: {claim.publication_year}年")
            
        # 内容ベースのクエリ（具体的な研究主張がない場合のみ）
        if "営業" in claim.content:
            queries.append("sales performance personality traits")
        if "外向性" in claim.content:
            queries.append("extroversion sales performance")
        if "誠実性" in claim.content:
            queries.append("conscientiousness job performance")
        if "遺伝" in claim.content or "％" in claim.content:
            queries.append("personality heritability genetics")
        
        # 一般的なクエリ
        keywords = re.findall(r'[A-Za-z]+', claim.content)
        if keywords:
            queries.append(" ".join(keywords[:3]))
        
        if not queries:
            print(f"⚠️ クエリ生成失敗: {claim.content[:50]}...")
        
        return list(set(queries))

    def _detect_hallucination(self, claim: ExtractedClaim, evidence: List[Any]) -> bool:
        """ハルシネーションを検出"""
        if not evidence:
            print(f"📋 エビデンス0件: {claim.content[:50]}... → ハルシネーション")
            return True
        
        # 具体的な研究者名と年代が両方主張されている場合は厳密チェック
        if claim.researcher_name and claim.publication_year:
            matching_papers = []
            
            for paper in evidence:
                # 研究者名チェック
                author_match = False
                if hasattr(paper, 'authors') and paper.authors:
                    for author in paper.authors:
                        if claim.researcher_name.lower() in author.name.lower():
                            author_match = True
                            break
                
                # 年代チェック（±1年の許容範囲）
                year_match = False
                if hasattr(paper, 'publication_year') and paper.publication_year:
                    try:
                        if abs(int(paper.publication_year) - int(claim.publication_year)) <= 1:
                            year_match = True
                    except (ValueError, TypeError):
                        pass
                
                # 両方マッチする論文があるかチェック
                if author_match and year_match:
                    matching_papers.append(paper)
            
            if not matching_papers:
                print(f"📋 研究者'{claim.researcher_name}'年代'{claim.publication_year}'が一致する論文なし → ハルシネーション")
                return True
            else:
                print(f"✅ 研究者'{claim.researcher_name}'年代'{claim.publication_year}'の論文を確認: {len(matching_papers)}件")
                return False
        
        # 研究者名のみの場合
        if claim.researcher_name:
            found_researcher = False
            for paper in evidence:
                if hasattr(paper, 'authors') and paper.authors:
                    for author in paper.authors:
                        if claim.researcher_name.lower() in author.name.lower():
                            found_researcher = True
                            break
            if not found_researcher:
                print(f"📋 研究者'{claim.researcher_name}'が見つからない → ハルシネーション")
                return True
        
        # 年代のみの場合  
        if claim.publication_year:
            found_year = False
            for paper in evidence:
                if hasattr(paper, 'publication_year') and paper.publication_year:
                    try:
                        if abs(int(paper.publication_year) - int(claim.publication_year)) <= 2:
                            found_year = True
                            break
                    except (ValueError, TypeError):
                        pass
            if not found_year:
                print(f"📋 年代'{claim.publication_year}'の論文が見つからない → ハルシネーション") 
                return True
        
        print(f"✅ 基本的な事実確認をクリア")
        return False

    def _search_alternative_evidence(self, claim: ExtractedClaim) -> List[Any]:
        """代替エビデンスを検索"""
        alternative_queries = []
        
        if "営業" in claim.content:
            alternative_queries.extend([
                "sales personality Big Five performance",
                "extroversion conscientiousness sales success",
                "personality traits job performance meta-analysis"
            ])
        
        if "遺伝" in claim.content:
            alternative_queries.extend([
                "personality heritability twin studies",
                "Big Five genetics behavioral genetics"
            ])
        
        all_alternatives = []
        for query in alternative_queries:
            try:
                papers = asyncio.run(
                    self.search_service.search_papers(query, max_results=3)
                )
                all_alternatives.extend(papers)
            except Exception as e:
                print(f"⚠️ 代替検索エラー: {e}")
        
        return all_alternatives

    def _calculate_verification_score(self, claim: ExtractedClaim, evidence: List[Any]) -> float:
        """検証スコアを計算"""
        if not evidence:
            return 0.0
        
        score = 0.0
        total_citations = sum(getattr(paper, 'citation_count', 0) or 0 for paper in evidence)
        
        # 引用数による重み付け
        if total_citations > 1000:
            score += 0.4
        elif total_citations > 100:
            score += 0.3
        elif total_citations > 10:
            score += 0.2
        
        # エビデンス数による重み付け
        if len(evidence) >= 3:
            score += 0.3
        elif len(evidence) >= 2:
            score += 0.2
        elif len(evidence) >= 1:
            score += 0.1
        
        # 年代の新しさ
        recent_papers = [p for p in evidence if hasattr(p, 'publication_year') 
                        and p.publication_year and int(p.publication_year) >= 2010]
        if recent_papers:
            score += 0.3
        
        return min(score, 1.0)

    def _generate_recommendation(self, claim: ExtractedClaim, evidence: List[Any], is_hallucination: bool) -> str:
        """推奨事項を生成"""
        if is_hallucination:
            return "代替エビデンスで完全に置き換えることを推奨"
        elif len(evidence) == 0:
            return "エビデンス不足 - 削除または代替表現を推奨"
        elif len(evidence) < 2:
            return "エビデンス補強を推奨"
        else:
            return "信頼性十分 - 引用情報の追加を推奨"

    def _create_evidence_based_replacement(self, result: FactCheckResult) -> str:
        """エビデンスベースの置換文を作成"""
        if not result.alternative_evidence:
            return "【要検証】" + result.original_claim.content
        
        best_paper = max(result.alternative_evidence, 
                        key=lambda p: getattr(p, 'citation_count', 0) or 0)
        
        # 研究者名を抽出
        author_name = "研究者"
        if hasattr(best_paper, 'authors') and best_paper.authors:
            author_name = best_paper.authors[0].name.split()[-1]  # 姓を取得
        
        # 年代を抽出
        year = "最近"
        if hasattr(best_paper, 'publication_year') and best_paper.publication_year:
            year = f"{best_paper.publication_year}年"
        
        # 引用数情報
        citation_info = ""
        if hasattr(best_paper, 'citation_count') and best_paper.citation_count:
            if best_paper.citation_count > 1000:
                citation_info = f"（{best_paper.citation_count:,}回以上引用されている権威的研究）"
        
        # 元の主張の核心的な内容を抽出
        original_content = result.original_claim.content
        
        # 主張の主要部分を保持
        core_claim = self._extract_core_claim(original_content)
        
        # 語尾も保持
        ending = self._extract_ending(original_content)
        
        replacement = f"{author_name}の{year}の研究{citation_info}によると、{core_claim}{ending}"
        return replacement

    def _extract_core_claim(self, text: str) -> str:
        """文章から核心的な主張を抽出"""
        # 研究者名と年代を除去
        cleaned = re.sub(r'[A-Za-z]+(?:\s+[A-Za-z]+)*?(?:さん|氏|博士|教授|研究者)?(?:達|ら|等)?の', '', text)
        cleaned = re.sub(r'\d{4}年の研究によると、?', '', cleaned)
        cleaned = re.sub(r'によると、?', '', cleaned)
        
        # 語尾を除去
        cleaned = re.sub(r'(?:そうです|です|ます|である|だ|と言われています)$', '', cleaned)
        
        # 前後の空白を削除
        cleaned = cleaned.strip()
        
        return cleaned

    def _extract_ending(self, text: str) -> str:
        """文章から語尾を抽出"""
        ending_match = re.search(r'(そうです|です|ます|である|だ|と言われています)$', text)
        if ending_match:
            return ending_match.group(1)
        return "そうです"  # デフォルト

    def _replace_maintaining_style(self, text: str, original: str, replacement: str) -> str:
        """文体を維持しながら置換"""
        return text.replace(original, replacement)

    def _enhance_credibility(self, result: FactCheckResult) -> str:
        """信頼性強化情報を生成"""
        if not result.evidence_papers:
            return ""
        
        best_paper = max(result.evidence_papers, 
                        key=lambda p: getattr(p, 'citation_count', 0) or 0)
        
        enhancement = ""
        if hasattr(best_paper, 'citation_count') and best_paper.citation_count:
            if best_paper.citation_count > 1000:
                enhancement = f"（{best_paper.citation_count:,}回引用の権威的研究）"
            elif best_paper.citation_count > 100:
                enhancement = f"（{best_paper.citation_count}回引用）"
        
        return enhancement

    def _enhance_text_maintaining_style(self, text: str, original: str, enhancement: str) -> str:
        """文体を維持しながら情報を強化"""
        if not enhancement:
            return text
        
        # 文の終わりに挿入
        enhanced = original + enhancement
        return text.replace(original, enhanced)

    def _optimize_for_youtube(self, text: str) -> str:
        """YouTube最適化"""
        # 視聴者の関心を引く表現に変換
        optimizations = {
            r'研究によると': 'なんと、権威的な研究によると',
            r'ことが分かりました': 'ことが明らかになったんです',
            r'示しています': '実証されているんです',
            r'重要なのが': '特に重要なポイントが',
            r'問題は': 'ここで重要な問題があります。それは',
        }
        
        optimized_text = text
        for pattern, replacement in optimizations.items():
            optimized_text = re.sub(pattern, replacement, optimized_text)
        
        return optimized_text

    def run_full_fact_check(self, manuscript: str) -> Dict[str, Any]:
        """完全な事実確認プロセスを実行"""
        print("🔍 原稿事実確認を開始...")
        
        # 1. 主張抽出
        print("📝 主張を抽出中...")
        claims = self.extract_claims_from_manuscript(manuscript)
        print(f"✅ {len(claims)}個の主張を抽出しました")
        
        # 2. 事実確認
        print("🔍 事実確認を実行中...")
        fact_check_results = self.fact_check_claims(claims)
        
        # 3. 修正版生成
        print("✏️ 修正版原稿を生成中...")
        corrected_manuscript = self.generate_corrected_manuscript(manuscript, fact_check_results)
        
        # 4. 結果をObsidianに保存
        self._save_results_to_obsidian(manuscript, fact_check_results, corrected_manuscript)
        
        # 5. 結果サマリー
        hallucination_count = sum(1 for r in fact_check_results if r.is_hallucination)
        low_confidence_count = sum(1 for r in fact_check_results if r.verification_score < 0.5)
        
        return {
            "original_manuscript": manuscript,
            "corrected_manuscript": corrected_manuscript,
            "total_claims": len(claims),
            "hallucination_count": hallucination_count,
            "low_confidence_count": low_confidence_count,
            "fact_check_results": fact_check_results,
            "improvement_summary": self._generate_improvement_summary(fact_check_results)
        }

    def _save_results_to_obsidian(self, original: str, results: List[FactCheckResult], corrected: str):
        """結果をObsidianに保存"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        content = f"""# 原稿事実確認結果 - {timestamp}

## 📝 元の原稿
{original}

## ✅ 修正版原稿
{corrected}

## 🔍 事実確認詳細
"""
        
        for i, result in enumerate(results, 1):
            content += f"""
### {i}. 主張分析
- **元の主張**: {result.original_claim.content}
- **ハルシネーション**: {'❌ あり' if result.is_hallucination else '✅ なし'}
- **検証スコア**: {result.verification_score:.2f}
- **推奨事項**: {result.recommendation}
- **エビデンス数**: {len(result.evidence_papers)}個

"""

        filename = f"原稿事実確認_{timestamp}.md"
        file_path = self.obsidian_saver.vault_path / "fact-check-reports" / filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📁 結果をObsidianに保存: {filename}")

    def _generate_improvement_summary(self, results: List[FactCheckResult]) -> str:
        """改善サマリーを生成"""
        hallucinations = [r for r in results if r.is_hallucination]
        low_confidence = [r for r in results if r.verification_score < 0.5]
        
        summary = f"""
🎯 原稿改善サマリー:
- ハルシネーション修正: {len(hallucinations)}箇所
- 信頼性強化: {len(low_confidence)}箇所
- 全体的な信頼性向上度: {(1 - len(hallucinations) / max(len(results), 1)) * 100:.0f}%
"""
        return summary
    def _check_flexible_author_match(self, claim_researcher: str, paper) -> bool:
        """柔軟な研究者名マッチング"""
        if not hasattr(paper, 'authors') or not paper.authors:
            return False
        
        # 研究者名を分割（"Barrick and Mount" → ["Barrick", "Mount"]）
        researcher_parts = self._split_researcher_name(claim_researcher)
        paper_authors = [author.name.lower() for author in paper.authors]
        
        print(f"  🔍 マッチング: {researcher_parts} vs {paper_authors}")
        
        # 全ての姓が論文の著者に含まれているかチェック
        matches = []
        for part in researcher_parts:
            part_found = False
            for author_name in paper_authors:
                if part.lower() in author_name:
                    matches.append(f"{part} → {author_name}")
                    part_found = True
                    break
            if not part_found:
                print(f"  ❌ 未発見: {part}")
                return False
        
        print(f"  ✅ 全マッチ: {matches}")
        return True

    def _split_researcher_name(self, researcher_name: str) -> List[str]:
        """研究者名を分割"""
        # "Smith and Johnson" → ["Smith", "Johnson"]
        # "According to Smith" → ["Smith"]
        parts = []
        
        # " and "で分割
        if " and " in researcher_name:
            parts = [part.strip() for part in researcher_name.split(" and ")]
        else:
            # 単一名の場合、最後の単語を姓として使用
            words = researcher_name.strip().split()
            if words:
                parts = [words[-1]]  # 最後の単語を姓とする
        
        return [part for part in parts if part and len(part) > 2]  # 2文字以上の有効な姓のみ

    
# 新しいfact_check_claimsメソッド（修正版）
def fact_check_claims(self, claims: List[ExtractedClaim]) -> List[FactCheckResult]:
    """主張の事実確認（修正版）"""
    print("🔧 修正版fact_check_claims実行開始")
    results = []
    
    for claim in claims:
        print(f"🔧 クレーム処理: {claim.researcher_name} ({claim.publication_year})")
        # 論文検索クエリを生成
        search_queries = self._generate_search_queries(claim)
        print(f"🔍 生成されたクエリ: {search_queries}")
        
        # 各クエリで検索
        all_evidence = []
        search_successful = False
        
        print(f"🔧 検索ループ開始: {len(search_queries)}個のクエリ")
        for i, query in enumerate(search_queries):
            try:
                print(f"🔍 検索クエリ実行 [{i+1}/{len(search_queries)}]: \"{query}\"")
                papers = asyncio.run(
                    self.search_service.search_papers(query, max_results=5)
                )
                print(f"  → {len(papers)}件の論文取得")
                all_evidence.extend(papers)
                search_successful = True
            except Exception as e:
                print(f"⚠️ 検索エラー: {e}")
        print(f"🔧 検索ループ完了")
        
        # 検索が完全に失敗した場合は強制的にハルシネーション判定
        if not search_successful:
            print(f"🚨 全ての検索が失敗: {claim.content[:50]}... → ハルシネーション判定")
            all_evidence = []
        else:
            print(f"✅ 検索成功: {len(all_evidence)}件のエビデンス取得")
        
        # ハルシネーション判定
        print(f"🔍 ハルシネーション判定開始: エビデンス数={len(all_evidence)}")
        is_hallucination = self._detect_hallucination(claim, all_evidence)
        print(f"�� ハルシネーション判定結果: {is_hallucination}")
        
        # 代替エビデンス検索
        alternative_evidence = []
        if is_hallucination or len(all_evidence) < 2:
            alternative_evidence = self._search_alternative_evidence(claim)
        
        # 検証スコア計算
        verification_score = self._calculate_verification_score(claim, all_evidence)
        
        # 推奨事項生成
        recommendation = self._generate_recommendation(claim, all_evidence, is_hallucination)
        
        result = FactCheckResult(
            original_claim=claim,
            is_hallucination=is_hallucination,
            evidence_papers=all_evidence,
            alternative_evidence=alternative_evidence,
            verification_score=verification_score,
            recommendation=recommendation
        )
        results.append(result)
    
    return results

# メソッドを上書き
ManuscriptFactChecker.fact_check_claims = fact_check_claims


# 完全新規の研究者名抽出メソッド
def new_extract_researchers(self, sentence):
    """新しい研究者名抽出メソッド"""
    print(f"🔧 新規抽出メソッド実行: '{sentence}'")
    researchers = []
    
    # パターン1: According to X

# === 最適化されたメソッド（クリーンアップ後に再追加） ===

def new_extract_researchers(self, sentence):
    """最適化された研究者名抽出メソッド"""
    import re
    print(f"🔧 新規抽出メソッド実行: '{sentence}'")
    researchers = []
    
    # パターン1: According to X
    pattern1 = r'According to ([A-Za-z]+(?:\s+[A-Za-z]+)*)'
    matches1 = re.findall(pattern1, sentence)
    if matches1:
        print(f"  パターン1結果: {matches1}")
        researchers.extend(matches1)
    
    # パターン2: X and Y (直接処理)
    pattern2 = r'([A-Za-z]+)\s+and\s+([A-Za-z]+)'
    matches2 = re.findall(pattern2, sentence)
    if matches2:
        print(f"  パターン2結果: {matches2}")
        for match in matches2:
            combined = f"{match[0]} and {match[1]}"
            researchers.append(combined)
            print(f"  タプル結合: {match} → '{combined}'")
    
    # パターン3: X's study
    pattern3 = r"([A-Za-z]+(?:\s+and\s+[A-Za-z]+)*)'s\s+\d{4}\s+(?:study|research|paper)"
    matches3 = re.findall(pattern3, sentence)
    if matches3:
        print(f"  パターン3結果: {matches3}")
        researchers.extend(matches3)
    
    # 重複除去し、andを含むものを先頭に
    unique = list(set(researchers))
    and_first = [r for r in unique if " and " in r] + [r for r in unique if " and " not in r]
    
    print(f"🔧 新規メソッド結果: {and_first}")
    return and_first

def new_detect_hallucination(self, claim, evidence):
    """最適化されたハルシネーション検出メソッド"""
    print(f"🔧 新規ハルシネーション判定: '{claim.researcher_name}' ({claim.publication_year})")
    
    if not evidence:
        print(f"📋 エビデンス0件 → ハルシネーション")
        return True
    
    print(f"📋 エビデンス{len(evidence)}件で検証開始")
    
    # 研究者名と年代の両方がある場合
    if claim.researcher_name and claim.publication_year:
        matching_papers = []
        
        for i, paper in enumerate(evidence):
            print(f"🔍 論文{i+1}チェック: {paper.title[:40]}...")
            
            # 著者マッチング（改良版）
            author_match = False
            if " and " in claim.researcher_name:
                parts = [p.strip() for p in claim.researcher_name.split(" and ")]
                print(f"  名前分割: {parts}")
                
                all_parts_found = True
                matches = []
                for part in parts:
                    part_found = False
                    for author in paper.authors:
                        if part.lower() in author.name.lower():
                            matches.append(f"{part} → {author.name}")
                            part_found = True
                            break
                    if not part_found:
                        all_parts_found = False
                        break
                
                author_match = all_parts_found
                if matches:
                    print(f"  マッチング: {matches}")
            else:
                # 単一名の場合
                for author in paper.authors:
                    if claim.researcher_name.lower() in author.name.lower():
                        author_match = True
                        print(f"  マッチング: {claim.researcher_name} → {author.name}")
                        break
            
            print(f"  → 著者マッチ: {author_match}")
            
            # 年代チェック（±1年の許容範囲）
            year_match = False
            if hasattr(paper, 'publication_year') and paper.publication_year:
                try:
                    year_diff = abs(int(paper.publication_year) - int(claim.publication_year))
                    year_match = year_diff <= 1
                    print(f"  → 年代マッチ: {year_match} ({paper.publication_year} vs {claim.publication_year})")
                except (ValueError, TypeError):
                    print(f"  → 年代エラー")
                    pass
            
            # 両方マッチする論文があるかチェック
            if author_match and year_match:
                matching_papers.append(paper)
                print(f"  ✅ 完全マッチ!")
        
        if not matching_papers:
            print(f"📋 完全マッチする論文なし → ハルシネーション")
            return True
        else:
            print(f"✅ 完全マッチする論文発見: {len(matching_papers)}件 → 実在研究")
            return False
    
    print(f"✅ 基本チェック通過")
    return False

# メソッド置き換え
ManuscriptFactChecker._extract_researchers = new_extract_researchers
ManuscriptFactChecker._detect_hallucination = new_detect_hallucination
