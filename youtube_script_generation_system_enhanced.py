#!/usr/bin/env python3
"""
研究→YouTube原稿生成システム v3.1
MCP統合版 - 最大限の事実正確性とアルゴリズム性能（改善版）
"""

import json
import asyncio
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
import openai
from anthropic import Anthropic
from enum import Enum

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_script_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """エラー重要度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ProcessingStage(Enum):
    """処理段階"""
    INITIALIZATION = "initialization"
    RESEARCH_ANALYSIS = "research_analysis"
    CONTENT_GENERATION = "content_generation"
    CITATION_VALIDATION = "citation_validation"
    SAFETY_CHECK = "safety_check"
    FORMAT_CONVERSION = "format_conversion"
    QUALITY_ASSESSMENT = "quality_assessment"
    FINAL_OUTPUT = "final_output"

@dataclass
class ResearchMetadata:
    """研究メタデータ"""
    title: str
    authors: List[str]
    abstract: str
    publication_year: int
    journal: str
    doi: Optional[str] = None
    citation_count: int = 0
    keywords: List[str] = None
    institutions: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)

@dataclass
class YouTubeScript:
    """YouTube原稿"""
    title: str
    hook: str
    introduction: str
    main_content: str
    conclusion: str
    call_to_action: str
    total_duration: int  # 秒
    sources: List[Dict[str, str]]
    confidence_score: float
    safety_flags: List[Dict[str, str]]
    processing_time: float
    quality_metrics: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)

class QualityMetrics:
    """品質評価メトリクス"""
    
    @staticmethod
    def calculate_readability_score(text: str) -> float:
        """可読性スコア計算"""
        sentences = text.split('。')
        words = text.split()
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        # 理想的な文の長さは20-30語
        if 20 <= avg_sentence_length <= 30:
            return 1.0
        elif 15 <= avg_sentence_length <= 35:
            return 0.8
        elif 10 <= avg_sentence_length <= 40:
            return 0.6
        else:
            return 0.4
    
    @staticmethod
    def calculate_engagement_score(text: str) -> float:
        """エンゲージメントスコア計算"""
        engagement_keywords = [
            "驚くべき", "興味深い", "重要な", "効果的", "革新的",
            "実用的", "具体的", "明確", "分かりやすい", "魅力的"
        ]
        
        score = 0.0
        for keyword in engagement_keywords:
            if keyword in text:
                score += 0.1
        
        return min(score, 1.0)
    
    @staticmethod
    def calculate_structure_score(sections: Dict[str, str]) -> float:
        """構造スコア計算"""
        required_sections = ["hook", "introduction", "main_content", "conclusion", "call_to_action"]
        
        score = 0.0
        for section in required_sections:
            if section in sections and sections[section].strip():
                score += 0.2
        
        return score

class ErrorHandler:
    """エラーハンドラー"""
    
    def __init__(self):
        self.error_history = []
        self.recovery_strategies = {
            "api_timeout": self._handle_api_timeout,
            "citation_missing": self._handle_citation_missing,
            "safety_violation": self._handle_safety_violation,
            "format_error": self._handle_format_error
        }
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                  severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> Dict[str, Any]:
        """エラーログ記録"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'severity': severity.value,
            'context': context or {},
            'recovered': False
        }
        
        self.error_history.append(error_info)
        logger.error(f"Error in {context.get('stage', 'unknown')}: {error}")
        
        return error_info
    
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """エラー処理"""
        error_type = type(error).__name__
        
        if error_type in self.recovery_strategies:
            try:
                return await self.recovery_strategies[error_type](error, context)
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")
        
        return None
    
    async def _handle_api_timeout(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """APIタイムアウト処理"""
        logger.warning("API timeout detected, retrying with reduced tokens...")
        return {"action": "retry_with_reduced_tokens", "max_tokens": 2000}
    
    async def _handle_citation_missing(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """引用不足処理"""
        logger.warning("Citation missing, regenerating with citation enforcement...")
        return {"action": "regenerate_with_citations", "enforce_citations": True}
    
    async def _handle_safety_violation(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """安全性違反処理"""
        logger.warning("Safety violation detected, applying safety filters...")
        return {"action": "apply_safety_filters", "strict_mode": True}
    
    async def _handle_format_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """形式エラー処理"""
        logger.warning("Format error detected, using fallback format...")
        return {"action": "use_fallback_format", "format": "simple"}

class MCPConstitutionalAI:
    """Anthropic's Constitutional AI 実装"""
    
    def __init__(self, constitution_file: str = ".cursor/mcp_claude_constitution.json"):
        self.constitution = self._load_constitution(constitution_file)
        self.anthropic = Anthropic()
        self.error_handler = ErrorHandler()
    
    def _load_constitution(self, file_path: str) -> Dict[str, Any]:
        """憲法ルールを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Constitution file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in constitution file: {e}")
            return {}
    
    async def generate_with_constitution(self, prompt: str, research_data: ResearchMetadata, 
                                       max_retries: int = 3) -> str:
        """憲法ルールを適用して生成"""
        for attempt in range(max_retries):
            try:
                constitutional_prompt = self._apply_constitutional_rules(prompt, research_data)
                
                response = await self.anthropic.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[
                        {
                            "role": "user",
                            "content": constitutional_prompt
                        }
                    ]
                )
                
                return response.content[0].text
                
            except Exception as e:
                error_context = {
                    "stage": ProcessingStage.CONTENT_GENERATION.value,
                    "attempt": attempt + 1,
                    "max_retries": max_retries
                }
                
                error_info = self.error_handler.log_error(e, error_context, ErrorSeverity.HIGH)
                
                if attempt == max_retries - 1:
                    raise e
                
                # リトライ前に待機
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Maximum retries exceeded")
    
    def _apply_constitutional_rules(self, prompt: str, research_data: ResearchMetadata) -> str:
        """憲法ルールを適用"""
        rules = self.constitution.get("constitutionalAI", {}).get("rules", {})
        
        constitutional_prompt = f"""
{self._get_factual_accuracy_rules(rules)}
{self._get_citation_rules(rules)}
{self._get_tone_rules(rules)}
{self._get_safety_rules(rules)}

研究データ:
- タイトル: {research_data.title}
- 著者: {', '.join(research_data.authors)}
- DOI: {research_data.doi or 'N/A'}
- 発表年: {research_data.publication_year}
- 要約: {research_data.abstract}

要求: {prompt}

上記の憲法ルールに従って、事実に基づいた正確なYouTube原稿を作成してください。
"""
        return constitutional_prompt
    
    def _get_factual_accuracy_rules(self, rules: Dict) -> str:
        """事実正確性ルール"""
        factual_rules = rules.get("factualAccuracy", {}).get("rules", [])
        return "## 事実正確性ルール:\n" + "\n".join(f"- {rule}" for rule in factual_rules)
    
    def _get_citation_rules(self, rules: Dict) -> str:
        """引用ルール"""
        citation_rules = rules.get("citationEnforcement", {}).get("rules", [])
        return "## 引用ルール:\n" + "\n".join(f"- {rule}" for rule in citation_rules)
    
    def _get_tone_rules(self, rules: Dict) -> str:
        """トーンルール"""
        tone_rules = rules.get("toneControl", {}).get("rules", [])
        return "## トーンルール:\n" + "\n".join(f"- {rule}" for rule in tone_rules)
    
    def _get_safety_rules(self, rules: Dict) -> str:
        """安全性ルール"""
        safety_rules = rules.get("safetyChecks", {}).get("rules", [])
        return "## 安全性ルール:\n" + "\n".join(f"- {rule}" for rule in safety_rules)

class MCPSparrowLogic:
    """Google DeepMind's Sparrow Logic 実装"""
    
    def __init__(self, sparrow_file: str = ".cursor/mcp_sparrow.json"):
        self.sparrow_rules = self._load_sparrow_rules(sparrow_file)
        self.error_handler = ErrorHandler()
    
    def _load_sparrow_rules(self, file_path: str) -> Dict[str, Any]:
        """Sparrowルールを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Sparrow rules file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in sparrow rules file: {e}")
            return {}
    
    def validate_citations(self, content: str, sources: List[Dict[str, str]]) -> Tuple[bool, List[str]]:
        """引用を検証"""
        try:
            citation_rules = self.sparrow_rules.get("sparrowLogic", {}).get("citationRules", {})
            mandatory_rules = citation_rules.get("mandatoryCitations", {}).get("rules", [])
            
            violations = []
            
            # 各段落に引用があるかチェック
            paragraphs = content.split('\n\n')
            for i, paragraph in enumerate(paragraphs):
                if paragraph.strip() and not self._has_citation(paragraph, sources):
                    violations.append(f"段落 {i+1} に引用がありません")
            
            # 科学的主張にDOIがあるかチェック
            scientific_claims = self._extract_scientific_claims(content)
            for claim in scientific_claims:
                if not self._has_doi_citation(claim, sources):
                    violations.append(f"科学的主張 '{claim[:50]}...' にDOI引用がありません")
            
            return len(violations) == 0, violations
            
        except Exception as e:
            error_context = {
                "stage": ProcessingStage.CITATION_VALIDATION.value,
                "content_length": len(content),
                "sources_count": len(sources)
            }
            self.error_handler.log_error(e, error_context, ErrorSeverity.MEDIUM)
            return False, [f"引用検証エラー: {str(e)}"]
    
    def _has_citation(self, paragraph: str, sources: List[Dict[str, str]]) -> bool:
        """段落に引用があるかチェック"""
        # 簡単な引用パターンマッチング
        citation_patterns = [
            r'\[.*?\]',  # [Author, Year]
            r'\(.*?\d{4}.*?\)',  # (Author, 2024)
            r'https?://',  # URL
            r'DOI:',  # DOI
        ]
        
        import re
        for pattern in citation_patterns:
            if re.search(pattern, paragraph):
                return True
        
        return False
    
    def _extract_scientific_claims(self, content: str) -> List[str]:
        """科学的主張を抽出"""
        # 科学的主張のキーワード
        scientific_keywords = [
            "研究によると", "実験で", "調査で", "分析で", "統計で",
            "shows", "demonstrates", "proves", "confirms", "reveals"
        ]
        
        claims = []
        sentences = content.split('。')
        
        for sentence in sentences:
            for keyword in scientific_keywords:
                if keyword in sentence:
                    claims.append(sentence.strip())
                    break
        
        return claims
    
    def _has_doi_citation(self, claim: str, sources: List[Dict[str, str]]) -> bool:
        """DOI引用があるかチェック"""
        for source in sources:
            if source.get("doi") or "doi.org" in source.get("url", ""):
                return True
        return False

class MCPGuardrails:
    """Microsoft Guardrails 実装"""
    
    def __init__(self, guardrails_file: str = ".cursor/mcp_guardrails.json"):
        self.guardrails = self._load_guardrails(guardrails_file)
        self.violation_log = []
        self.error_handler = ErrorHandler()
    
    def _load_guardrails(self, file_path: str) -> Dict[str, Any]:
        """Guardrailsを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Guardrails file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in guardrails file: {e}")
            return {}
    
    def check_content_safety(self, content: str) -> Tuple[bool, List[Dict[str, str]]]:
        """コンテンツ安全性をチェック"""
        try:
            safety_rules = self.guardrails.get("guardrails", {}).get("safetyRules", {})
            blocked_phrases = safety_rules.get("blockedPhrases", {}).get("phrases", [])
            
            violations = []
            
            # ブロックされたフレーズをチェック
            for phrase in blocked_phrases:
                if phrase.lower() in content.lower():
                    violations.append({
                        "type": "blocked_phrase",
                        "severity": "critical",
                        "phrase": phrase,
                        "description": f"ブロックされたフレーズ '{phrase}' が検出されました"
                    })
            
            # 医療コンテンツチェック
            if self._contains_medical_content(content):
                medical_violations = self._check_medical_content(content, safety_rules)
                violations.extend(medical_violations)
            
            # 金融コンテンツチェック
            if self._contains_financial_content(content):
                financial_violations = self._check_financial_content(content, safety_rules)
                violations.extend(financial_violations)
            
            # 心理コンテンツチェック
            if self._contains_psychological_content(content):
                psychological_violations = self._check_psychological_content(content, safety_rules)
                violations.extend(psychological_violations)
            
            # 違反をログに記録
            if violations:
                self._log_violations(violations, content)
            
            return len(violations) == 0, violations
            
        except Exception as e:
            error_context = {
                "stage": ProcessingStage.SAFETY_CHECK.value,
                "content_length": len(content)
            }
            self.error_handler.log_error(e, error_context, ErrorSeverity.HIGH)
            return False, [{"type": "safety_check_error", "severity": "critical", "description": str(e)}]
    
    def _contains_medical_content(self, content: str) -> bool:
        """医療コンテンツを含むかチェック"""
        medical_keywords = ["治療", "薬", "病気", "症状", "診断", "医師", "病院"]
        return any(keyword in content for keyword in medical_keywords)
    
    def _contains_financial_content(self, content: str) -> bool:
        """金融コンテンツを含むかチェック"""
        financial_keywords = ["投資", "株", "為替", "利益", "損失", "リターン", "リスク"]
        return any(keyword in content for keyword in financial_keywords)
    
    def _contains_psychological_content(self, content: str) -> bool:
        """心理コンテンツを含むかチェック"""
        psychological_keywords = ["心理", "精神", "ストレス", "うつ", "不安", "セラピー"]
        return any(keyword in content for keyword in psychological_keywords)
    
    def _check_medical_content(self, content: str, safety_rules: Dict) -> List[Dict[str, str]]:
        """医療コンテンツをチェック"""
        violations = []
        medical_rules = safety_rules.get("medicalContent", {}).get("rules", [])
        required_disclaimers = safety_rules.get("medicalContent", {}).get("requiredDisclaimers", [])
        
        # 免責事項が含まれているかチェック
        for disclaimer in required_disclaimers:
            if disclaimer not in content:
                violations.append({
                    "type": "medical_content",
                    "severity": "high",
                    "description": f"医療コンテンツに必要な免責事項 '{disclaimer}' が含まれていません"
                })
        
        return violations
    
    def _check_financial_content(self, content: str, safety_rules: Dict) -> List[Dict[str, str]]:
        """金融コンテンツをチェック"""
        violations = []
        financial_rules = safety_rules.get("financialContent", {}).get("rules", [])
        required_disclaimers = safety_rules.get("financialContent", {}).get("requiredDisclaimers", [])
        
        # 免責事項が含まれているかチェック
        for disclaimer in required_disclaimers:
            if disclaimer not in content:
                violations.append({
                    "type": "financial_content",
                    "severity": "high",
                    "description": f"金融コンテンツに必要な免責事項 '{disclaimer}' が含まれていません"
                })
        
        return violations
    
    def _check_psychological_content(self, content: str, safety_rules: Dict) -> List[Dict[str, str]]:
        """心理コンテンツをチェック"""
        violations = []
        psychological_rules = safety_rules.get("psychologicalContent", {}).get("rules", [])
        required_disclaimers = safety_rules.get("psychologicalContent", {}).get("requiredDisclaimers", [])
        
        # 免責事項が含まれているかチェック
        for disclaimer in required_disclaimers:
            if disclaimer not in content:
                violations.append({
                    "type": "psychological_content",
                    "severity": "high",
                    "description": f"心理コンテンツに必要な免責事項 '{disclaimer}' が含まれていません"
                })
        
        return violations
    
    def _log_violations(self, violations: List[Dict[str, str]], content: str):
        """違反をログに記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "violations": violations,
            "content_preview": content[:200] + "..." if len(content) > 200 else content
        }
        
        self.violation_log.append(log_entry)
        
        # ログファイルに保存
        log_file = "logs/guardrail_violations.json"
        Path("logs").mkdir(exist_ok=True)
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.violation_log, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save violation log: {e}")

class ModelRouter:
    """モデルルーティングシステム"""
    
    def __init__(self, project_rules_file: str = ".cursor/project-rules.json"):
        self.project_rules = self._load_project_rules(project_rules_file)
        self.openai_client = openai.AsyncOpenAI()
        self.error_handler = ErrorHandler()
    
    def _load_project_rules(self, file_path: str) -> Dict[str, Any]:
        """プロジェクトルールを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Project rules file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in project rules file: {e}")
            return {}
    
    async def route_task(self, task_type: str, content: str, research_data: ResearchMetadata) -> str:
        """タスクタイプに基づいてモデルをルーティング"""
        try:
            model_routing = self.project_rules.get("projectRules", {}).get("modelRouting", {})
            
            if task_type in ["long-form", "academic", "complex"]:
                # Claude使用
                return await self._use_claude(content, research_data)
            else:
                # GPT使用
                return await self._use_gpt(content, research_data)
                
        except Exception as e:
            error_context = {
                "stage": ProcessingStage.CONTENT_GENERATION.value,
                "task_type": task_type
            }
            self.error_handler.log_error(e, error_context, ErrorSeverity.HIGH)
            raise e
    
    async def _use_claude(self, content: str, research_data: ResearchMetadata) -> str:
        """Claudeを使用"""
        constitutional_ai = MCPConstitutionalAI()
        return await constitutional_ai.generate_with_constitution(content, research_data)
    
    async def _use_gpt(self, content: str, research_data: ResearchMetadata) -> str:
        """GPTを使用"""
        try:
            gpt_prompt = self._create_gpt_prompt(content, research_data)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precision-focused fact-checker and summarizer."},
                    {"role": "user", "content": gpt_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_context = {
                "stage": ProcessingStage.CONTENT_GENERATION.value,
                "model": "gpt-4o"
            }
            self.error_handler.log_error(e, error_context, ErrorSeverity.HIGH)
            raise e
    
    def _create_gpt_prompt(self, content: str, research_data: ResearchMetadata) -> str:
        """GPT用プロンプトを作成"""
        return f"""
研究データ:
- タイトル: {research_data.title}
- 著者: {', '.join(research_data.authors)}
- DOI: {research_data.doi or 'N/A'}
- 要約: {research_data.abstract}

要求: {content}

JSON形式で精密な要約を作成してください。
"""

class YouTubeScriptGenerator:
    """YouTube原稿生成システム"""
    
    def __init__(self):
        self.constitutional_ai = MCPConstitutionalAI()
        self.sparrow_logic = MCPSparrowLogic()
        self.guardrails = MCPGuardrails()
        self.model_router = ModelRouter()
        self.error_handler = ErrorHandler()
        self.quality_metrics = QualityMetrics()
    
    async def generate_script(self, research_data: ResearchMetadata, style: str = "popular") -> YouTubeScript:
        """YouTube原稿を生成"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Generating YouTube script for: {research_data.title}")
            
            # 1. 研究要約生成（Claude使用）
            summary_prompt = self._create_summary_prompt(style)
            summary = await self.constitutional_ai.generate_with_constitution(summary_prompt, research_data)
            
            # 2. 引用検証（Sparrow Logic）
            sources = self._extract_sources(research_data)
            citation_valid, citation_violations = self.sparrow_logic.validate_citations(summary, sources)
            
            if not citation_valid:
                logger.warning(f"Citation violations: {citation_violations}")
                # 引用を追加して再生成
                summary = await self._regenerate_with_citations(summary, sources, research_data)
            
            # 3. 安全性チェック（Guardrails）
            safety_valid, safety_violations = self.guardrails.check_content_safety(summary)
            
            if not safety_valid:
                logger.warning(f"Safety violations: {safety_violations}")
                # 安全性を改善して再生成
                summary = await self._regenerate_with_safety(summary, safety_violations, research_data)
            
            # 4. YouTube形式に変換
            script_sections = self._convert_to_youtube_format(summary, style)
            
            # 5. 品質評価
            quality_metrics = self._calculate_quality_metrics(summary, script_sections)
            confidence_score = self._calculate_confidence_score(summary, citation_valid, safety_valid)
            
            # 6. 処理時間計算
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return YouTubeScript(
                title=research_data.title,
                hook=script_sections["hook"],
                introduction=script_sections["introduction"],
                main_content=script_sections["main_content"],
                conclusion=script_sections["conclusion"],
                call_to_action=script_sections["call_to_action"],
                total_duration=script_sections["total_duration"],
                sources=sources,
                confidence_score=confidence_score,
                safety_flags=safety_violations,
                processing_time=processing_time,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            error_context = {
                "stage": ProcessingStage.CONTENT_GENERATION.value,
                "research_title": research_data.title,
                "style": style
            }
            self.error_handler.log_error(e, error_context, ErrorSeverity.CRITICAL)
            raise e
    
    def _create_summary_prompt(self, style: str) -> str:
        """要約プロンプトを作成"""
        style_prompts = {
            "popular": "一般視聴者向けの魅力的なYouTube原稿を作成してください。",
            "academic": "学術的で正確なYouTube原稿を作成してください。",
            "business": "ビジネスパーソン向けの実用的なYouTube原稿を作成してください。",
            "educational": "教育的で体系的なYouTube原稿を作成してください。"
        }
        
        return style_prompts.get(style, style_prompts["popular"])
    
    def _extract_sources(self, research_data: ResearchMetadata) -> List[Dict[str, str]]:
        """ソースを抽出"""
        sources = []
        
        if research_data.doi:
            sources.append({
                "type": "academic",
                "url": f"https://doi.org/{research_data.doi}",
                "doi": research_data.doi,
                "title": research_data.title,
                "authors": ", ".join(research_data.authors),
                "year": str(research_data.publication_year)
            })
        
        return sources
    
    async def _regenerate_with_citations(self, summary: str, sources: List[Dict[str, str]], research_data: ResearchMetadata) -> str:
        """引用を追加して再生成"""
        citation_prompt = f"""
以下の要約に適切な引用を追加してください:

{summary}

利用可能なソース:
{json.dumps(sources, ensure_ascii=False, indent=2)}

各段落に適切な引用を追加し、科学的主張には必ずDOIを記載してください。
"""
        
        return await self.constitutional_ai.generate_with_constitution(citation_prompt, research_data)
    
    async def _regenerate_with_safety(self, summary: str, safety_violations: List[Dict[str, str]], research_data: ResearchMetadata) -> str:
        """安全性を改善して再生成"""
        safety_prompt = f"""
以下の要約の安全性を改善してください:

{summary}

検出された安全性問題:
{json.dumps(safety_violations, ensure_ascii=False, indent=2)}

適切な免責事項を追加し、危険な表現を修正してください。
"""
        
        return await self.constitutional_ai.generate_with_constitution(safety_prompt, research_data)
    
    def _convert_to_youtube_format(self, summary: str, style: str) -> Dict[str, str]:
        """YouTube形式に変換"""
        # 高度な分割ロジック
        sections = self._split_into_sections(summary, style)
        
        return {
            "hook": sections.get("hook", "興味深い研究結果をご紹介します"),
            "introduction": sections.get("introduction", "この研究について詳しく見ていきましょう"),
            "main_content": sections.get("main_content", "研究の詳細について説明します"),
            "conclusion": sections.get("conclusion", "まとめ"),
            "call_to_action": sections.get("call_to_action", "チャンネル登録をお願いします"),
            "total_duration": self._calculate_duration(sections, style)
        }
    
    def _split_into_sections(self, summary: str, style: str) -> Dict[str, str]:
        """要約をセクションに分割"""
        paragraphs = summary.split('\n\n')
        
        if len(paragraphs) < 3:
            # 短い場合は単純分割
            return {
                "hook": paragraphs[0] if paragraphs else "",
                "introduction": paragraphs[1] if len(paragraphs) > 1 else "",
                "main_content": "\n\n".join(paragraphs[2:-1]) if len(paragraphs) > 3 else "",
                "conclusion": paragraphs[-1] if len(paragraphs) > 1 else "",
                "call_to_action": "チャンネル登録をお願いします"
            }
        
        # スタイル別の分割ロジック
        if style == "popular":
            return self._split_popular_style(paragraphs)
        elif style == "academic":
            return self._split_academic_style(paragraphs)
        elif style == "business":
            return self._split_business_style(paragraphs)
        else:
            return self._split_educational_style(paragraphs)
    
    def _split_popular_style(self, paragraphs: List[str]) -> Dict[str, str]:
        """一般向けスタイルの分割"""
        return {
            "hook": paragraphs[0] if paragraphs else "",
            "introduction": paragraphs[1] if len(paragraphs) > 1 else "",
            "main_content": "\n\n".join(paragraphs[2:-2]) if len(paragraphs) > 4 else "",
            "conclusion": paragraphs[-2] if len(paragraphs) > 2 else "",
            "call_to_action": paragraphs[-1] if paragraphs else "チャンネル登録をお願いします"
        }
    
    def _split_academic_style(self, paragraphs: List[str]) -> Dict[str, str]:
        """学術的スタイルの分割"""
        return {
            "hook": paragraphs[0] if paragraphs else "",
            "introduction": paragraphs[1] if len(paragraphs) > 1 else "",
            "main_content": "\n\n".join(paragraphs[2:-2]) if len(paragraphs) > 4 else "",
            "conclusion": paragraphs[-2] if len(paragraphs) > 2 else "",
            "call_to_action": "さらなる研究の詳細は論文をご参照ください"
        }
    
    def _split_business_style(self, paragraphs: List[str]) -> Dict[str, str]:
        """ビジネススタイルの分割"""
        return {
            "hook": paragraphs[0] if paragraphs else "",
            "introduction": paragraphs[1] if len(paragraphs) > 1 else "",
            "main_content": "\n\n".join(paragraphs[2:-2]) if len(paragraphs) > 4 else "",
            "conclusion": paragraphs[-2] if len(paragraphs) > 2 else "",
            "call_to_action": "ビジネスへの応用について詳しく知りたい方はお問い合わせください"
        }
    
    def _split_educational_style(self, paragraphs: List[str]) -> Dict[str, str]:
        """教育的スタイルの分割"""
        return {
            "hook": paragraphs[0] if paragraphs else "",
            "introduction": paragraphs[1] if len(paragraphs) > 1 else "",
            "main_content": "\n\n".join(paragraphs[2:-2]) if len(paragraphs) > 4 else "",
            "conclusion": paragraphs[-2] if len(paragraphs) > 2 else "",
            "call_to_action": "次回もお楽しみに"
        }
    
    def _calculate_duration(self, sections: Dict[str, str], style: str) -> int:
        """動画時間を計算"""
        base_duration = {
            "popular": 900,    # 15分
            "academic": 1200,  # 20分
            "business": 1080,  # 18分
            "educational": 1800 # 30分
        }
        
        return base_duration.get(style, 900)
    
    def _calculate_quality_metrics(self, summary: str, sections: Dict[str, str]) -> Dict[str, float]:
        """品質メトリクスを計算"""
        return {
            "readability_score": self.quality_metrics.calculate_readability_score(summary),
            "engagement_score": self.quality_metrics.calculate_engagement_score(summary),
            "structure_score": self.quality_metrics.calculate_structure_score(sections)
        }
    
    def _calculate_confidence_score(self, summary: str, citation_valid: bool, safety_valid: bool) -> float:
        """信頼度スコアを計算"""
        score = 0.5  # ベーススコア
        
        if citation_valid:
            score += 0.3
        
        if safety_valid:
            score += 0.2
        
        # 長さによる調整
        if len(summary) > 1000:
            score += 0.1
        
        return min(score, 1.0)

async def main():
    """メイン関数"""
    # サンプル研究データ
    research_data = ResearchMetadata(
        title="AIによる営業パフォーマンス向上の研究",
        authors=["田中太郎", "佐藤花子"],
        abstract="本研究では、AI技術を活用した営業手法の効果を検証しました。",
        publication_year=2024,
        journal="Journal of Sales Technology",
        doi="10.1234/jst.2024.001",
        citation_count=15,
        keywords=["AI", "営業", "パフォーマンス"],
        institutions=["東京大学"]
    )
    
    # YouTube原稿生成
    generator = YouTubeScriptGenerator()
    script = await generator.generate_script(research_data, style="popular")
    
    # 結果を表示
    print("=== YouTube Script Generation Complete ===")
    print(f"Title: {script.title}")
    print(f"Confidence Score: {script.confidence_score:.2f}")
    print(f"Safety Flags: {len(script.safety_flags)}")
    print(f"Total Duration: {script.total_duration} seconds")
    print(f"Processing Time: {script.processing_time:.2f} seconds")
    print(f"Quality Metrics: {script.quality_metrics}")
    print("\n=== Script Sections ===")
    print(f"Hook: {script.hook}")
    print(f"Introduction: {script.introduction}")
    print(f"Main Content: {script.main_content[:200]}...")
    print(f"Conclusion: {script.conclusion}")
    print(f"Call to Action: {script.call_to_action}")

if __name__ == "__main__":
    asyncio.run(main()) 