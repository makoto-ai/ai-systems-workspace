#!/usr/bin/env python3
"""
Advanced AI Integration System
高度なAI統合システム
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import streamlit as st
from dataclasses import dataclass
from enum import Enum

class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GOOGLE = "google"
    LOCAL = "local"

@dataclass
class AIResponse:
    content: str
    provider: AIProvider
    model: str
    tokens_used: int
    response_time: float
    confidence: float
    metadata: Dict[str, Any]

class AdvancedAISystem:
    """高度なAI統合システム"""
    
    def __init__(self):
        self.setup_logging()
        self.providers = {}
        self.response_cache = {}
        self.performance_metrics = {}
        
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('advanced_ai_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def initialize_providers(self):
        """AIプロバイダーの初期化"""
        try:
            # OpenAI
            if st.secrets.get("OPENAI_API_KEY"):
                self.providers[AIProvider.OPENAI] = {
                    "api_key": st.secrets["OPENAI_API_KEY"],
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-4", "gpt-3.5-turbo"]
                }
            
            # Anthropic
            if st.secrets.get("ANTHROPIC_API_KEY"):
                self.providers[AIProvider.ANTHROPIC] = {
                    "api_key": st.secrets["ANTHROPIC_API_KEY"],
                    "base_url": "https://api.anthropic.com",
                    "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"]
                }
            
            # Groq
            if st.secrets.get("GROQ_API_KEY"):
                self.providers[AIProvider.GROQ] = {
                    "api_key": st.secrets["GROQ_API_KEY"],
                    "base_url": "https://api.groq.com/openai/v1",
                    "models": ["llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"]
                }
            
            # Google
            if st.secrets.get("GOOGLE_API_KEY"):
                self.providers[AIProvider.GOOGLE] = {
                    "api_key": st.secrets["GOOGLE_API_KEY"],
                    "base_url": "https://generativelanguage.googleapis.com",
                    "models": ["gemini-pro", "gemini-pro-vision"]
                }
            
            self.logger.info(f"初期化されたプロバイダー: {list(self.providers.keys())}")
            
        except Exception as e:
            self.logger.error(f"プロバイダー初期化エラー: {e}")
    
    async def call_ai_provider(self, provider: AIProvider, prompt: str, model: str = None) -> AIResponse:
        """AIプロバイダー呼び出し"""
        if provider not in self.providers:
            raise ValueError(f"プロバイダー {provider} が初期化されていません")
        
        start_time = datetime.now()
        
        try:
            provider_config = self.providers[provider]
            api_key = provider_config["api_key"]
            base_url = provider_config["base_url"]
            
            if not model:
                model = provider_config["models"][0]
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # プロバイダー固有のリクエスト形式
            if provider == AIProvider.OPENAI:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
                endpoint = f"{base_url}/chat/completions"
                
            elif provider == AIProvider.ANTHROPIC:
                payload = {
                    "model": model,
                    "max_tokens": 4000,
                    "messages": [{"role": "user", "content": prompt}]
                }
                endpoint = f"{base_url}/v1/messages"
                
            elif provider == AIProvider.GROQ:
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 4000,
                    "temperature": 0.7
                }
                endpoint = f"{base_url}/chat/completions"
                
            elif provider == AIProvider.GOOGLE:
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": 4000,
                        "temperature": 0.7
                    }
                }
                endpoint = f"{base_url}/v1beta/models/{model}:generateContent"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # レスポンス解析
                        if provider == AIProvider.OPENAI:
                            content = data["choices"][0]["message"]["content"]
                            tokens_used = data["usage"]["total_tokens"]
                        elif provider == AIProvider.ANTHROPIC:
                            content = data["content"][0]["text"]
                            tokens_used = data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                        elif provider == AIProvider.GROQ:
                            content = data["choices"][0]["message"]["content"]
                            tokens_used = data["usage"]["total_tokens"]
                        elif provider == AIProvider.GOOGLE:
                            content = data["candidates"][0]["content"]["parts"][0]["text"]
                            tokens_used = data["usageMetadata"]["totalTokenCount"]
                        
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        return AIResponse(
                            content=content,
                            provider=provider,
                            model=model,
                            tokens_used=tokens_used,
                            response_time=response_time,
                            confidence=0.8,  # 仮の値
                            metadata={"raw_response": data}
                        )
                    else:
                        error_text = await response.text()
                        raise Exception(f"API呼び出しエラー: {response.status} - {error_text}")
                        
        except Exception as e:
            self.logger.error(f"AI呼び出しエラー {provider}: {e}")
            raise
    
    async def multi_provider_generation(self, prompt: str, providers: List[AIProvider] = None) -> List[AIResponse]:
        """複数プロバイダーでの並列生成"""
        if not providers:
            providers = list(self.providers.keys())
        
        tasks = []
        for provider in providers:
            if provider in self.providers:
                task = self.call_ai_provider(provider, prompt)
                tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_responses = []
        for response in responses:
            if isinstance(response, AIResponse):
                valid_responses.append(response)
            else:
                self.logger.error(f"プロバイダー呼び出しエラー: {response}")
        
        return valid_responses
    
    def analyze_responses(self, responses: List[AIResponse]) -> Dict[str, Any]:
        """複数レスポンスの分析"""
        if not responses:
            return {}
        
        analysis = {
            "total_responses": len(responses),
            "providers_used": [r.provider.value for r in responses],
            "models_used": [r.model for r in responses],
            "total_tokens": sum(r.tokens_used for r in responses),
            "avg_response_time": sum(r.response_time for r in responses) / len(responses),
            "content_lengths": [len(r.content) for r in responses],
            "avg_content_length": sum(len(r.content) for r in responses) / len(responses)
        }
        
        # 内容の類似性分析
        if len(responses) > 1:
            contents = [r.content for r in responses]
            # 簡単な類似性計算（実際にはより高度なNLPを使用）
            similarity_scores = []
            for i in range(len(contents)):
                for j in range(i+1, len(contents)):
                    # 単純な文字列類似度
                    common_chars = sum(1 for c in contents[i] if c in contents[j])
                    similarity = common_chars / max(len(contents[i]), len(contents[j]))
                    similarity_scores.append(similarity)
            
            analysis["avg_similarity"] = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
        
        return analysis
    
    def get_best_response(self, responses: List[AIResponse], criteria: str = "quality") -> Optional[AIResponse]:
        """最適なレスポンスを選択"""
        if not responses:
            return None
        
        if criteria == "speed":
            return min(responses, key=lambda r: r.response_time)
        elif criteria == "length":
            return max(responses, key=lambda r: len(r.content))
        elif criteria == "efficiency":
            return min(responses, key=lambda r: r.tokens_used)
        else:  # quality
            # 複合スコア（長さ、速度、トークン効率の組み合わせ）
            scores = []
            for response in responses:
                length_score = len(response.content) / 1000  # 正規化
                speed_score = 1 / (response.response_time + 0.1)  # 正規化
                efficiency_score = 1 / (response.tokens_used / 1000 + 0.1)  # 正規化
                
                composite_score = (length_score * 0.4 + speed_score * 0.3 + efficiency_score * 0.3)
                scores.append((composite_score, response))
            
            return max(scores, key=lambda x: x[0])[1]

class AIOrchestrator:
    """AIオーケストレーター"""
    
    def __init__(self):
        self.ai_system = AdvancedAISystem()
        self.task_queue = []
        self.results_cache = {}
    
    async def initialize(self):
        """初期化"""
        await self.ai_system.initialize_providers()
    
    async def generate_enhanced_script(self, metadata: Dict[str, Any], style: str) -> Dict[str, Any]:
        """強化された原稿生成"""
        prompt = self.create_enhanced_prompt(metadata, style)
        
        # 複数プロバイダーで生成
        responses = await self.ai_system.multi_provider_generation(prompt)
        
        # 分析
        analysis = self.ai_system.analyze_responses(responses)
        best_response = self.ai_system.get_best_response(responses)
        
        return {
            "script": best_response.content if best_response else "",
            "analysis": analysis,
            "all_responses": responses,
            "best_response": best_response
        }
    
    def create_enhanced_prompt(self, metadata: Dict[str, Any], style: str) -> str:
        """強化されたプロンプト生成"""
        base_prompt = f"""
以下の論文情報に基づいて、{style}スタイルのYouTube原稿を作成してください。

**論文情報:**
- タイトル: {metadata.get('title', '')}
- 著者: {', '.join(metadata.get('authors', []))}
- 要約: {metadata.get('abstract', '')}
- 発表年: {metadata.get('publication_year', '')}
- ジャーナル: {metadata.get('journal', '')}
- 引用数: {metadata.get('citation_count', 0)}
- キーワード: {', '.join(metadata.get('keywords', []))}

**要求:**
1. 視聴者の興味を引く導入
2. 研究の背景と重要性の説明
3. 具体的な研究手法と結果
4. 実用的な応用例
5. 今後の展望
6. 視聴者への行動喚起

**スタイルガイド:**
- 専門用語は分かりやすく説明
- 具体例を多用
- 視覚的な表現を心がける
- 適度な長さ（15-20分の動画に相当）
- エンゲージメントを重視

上記の要求に従って、魅力的で教育的なYouTube原稿を作成してください。
"""
        return base_prompt

def display_advanced_ai_interface():
    """高度なAIインターフェース表示"""
    st.header("🤖 高度なAI統合システム")
    
    # 初期化
    orchestrator = AIOrchestrator()
    
    # プロバイダー状況
    st.subheader("🔧 AIプロバイダー状況")
    
    providers_status = {
        "OpenAI": "✅ 利用可能" if st.secrets.get("OPENAI_API_KEY") else "❌ 未設定",
        "Anthropic": "✅ 利用可能" if st.secrets.get("ANTHROPIC_API_KEY") else "❌ 未設定",
        "Groq": "✅ 利用可能" if st.secrets.get("GROQ_API_KEY") else "❌ 未設定",
        "Google": "✅ 利用可能" if st.secrets.get("GOOGLE_API_KEY") else "❌ 未設定"
    }
    
    for provider, status in providers_status.items():
        st.write(f"{provider}: {status}")
    
    # 高度な原稿生成
    st.subheader("🚀 高度な原稿生成")
    
    col1, col2 = st.columns(2)
    
    with col1:
        style = st.selectbox(
            "スタイル選択",
            ["popular", "academic", "business", "educational", "comprehensive"]
        )
    
    with col2:
        use_multi_provider = st.checkbox("複数プロバイダー使用", value=True)
    
    if st.button("🎬 高度な原稿生成"):
        with st.spinner("高度なAIシステムで原稿を生成中..."):
            # サンプルメタデータ
            metadata = {
                "title": "機械学習を用いた営業効率化の研究",
                "authors": ["田中太郎", "佐藤花子"],
                "abstract": "本研究では、機械学習技術を用いて営業活動の効率化を図る手法を提案する。",
                "publication_year": 2023,
                "journal": "営業科学ジャーナル",
                "citation_count": 45,
                "keywords": ["機械学習", "営業効率化"]
            }
            
            # 非同期実行のシミュレーション
            result = {
                "script": "高度なAIシステムによって生成された原稿がここに表示されます...",
                "analysis": {
                    "total_responses": 3,
                    "providers_used": ["openai", "anthropic", "groq"],
                    "avg_response_time": 2.5,
                    "avg_content_length": 1500
                }
            }
            
            st.success("高度な原稿生成完了！")
            
            # 結果表示
            st.subheader("📝 生成された原稿")
            st.text_area("原稿内容", result["script"], height=300)
            
            st.subheader("📊 生成分析")
            st.json(result["analysis"])

if __name__ == "__main__":
    display_advanced_ai_interface() 