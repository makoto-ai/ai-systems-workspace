"""
Unified AI Service for Multiple Providers
Phase 8: Multi-Provider AI Architecture
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Literal
from enum import Enum

logger = logging.getLogger(__name__)

class AIProvider(Enum):
    """Available AI providers"""
    GROQ = "groq"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    SIMULATION = "simulation"

class AIServiceError(Exception):
    """AI service related errors"""
    pass

class BaseAIService(ABC):
    """Abstract base class for AI services"""
    
    def __init__(self, provider: AIProvider):
        self.provider = provider
        self.available = False
        self.error_message = None
    
    @abstractmethod
    async def chat_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Basic chat completion"""
        pass
    
    @abstractmethod
    async def sales_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        customer_profile: Dict[str, Any],
        sales_stage: str
    ) -> Dict[str, Any]:
        """Sales conversation analysis"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the service is healthy"""
        try:
            result = await self.chat_completion("Hello", max_tokens=10)
            self.available = True
            self.error_message = None
            return {
                "provider": self.provider.value,
                "status": "healthy",
                "available": True
            }
        except Exception as e:
            self.available = False
            self.error_message = str(e)
            return {
                "provider": self.provider.value,
                "status": "unhealthy",
                "available": False,
                "error": str(e)
            }

class GroqAIService(BaseAIService):
    """Groq AI service implementation"""
    
    def __init__(self):
        super().__init__(AIProvider.GROQ)
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.default_model = "llama-3.3-70b-versatile"
        
        if self.api_key:
            self.available = True
        else:
            logger.warning("GROQ_API_KEY not found")
    
    async def chat_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise AIServiceError("Groq API key not configured")
        
        try:
            from services.groq_service import GroqService
        except ImportError:
            from app.services.groq_service import GroqService
        groq_service = GroqService(self.api_key)
        result = await groq_service.chat_completion(message, model, max_tokens, temperature)
        result["provider"] = self.provider.value
        return result
    
    async def sales_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        customer_profile: Dict[str, Any],
        sales_stage: str
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise AIServiceError("Groq API key not configured")
        
        try:
            from services.groq_service import GroqService
        except ImportError:
            from app.services.groq_service import GroqService
        groq_service = GroqService(self.api_key)
        result = await groq_service.sales_analysis(user_input)
        result["provider"] = self.provider.value
        return result

class OpenAIService(BaseAIService):
    """OpenAI service implementation"""
    
    def __init__(self):
        super().__init__(AIProvider.OPENAI)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        self.default_model = "gpt-4"
        
        if self.api_key:
            self.available = True
        else:
            logger.warning("OPENAI_API_KEY not found")
    
    async def chat_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise AIServiceError("OpenAI API key not configured")
        
        import httpx
        
        model = model or self.default_model
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "response": result["choices"][0]["message"]["content"],
                "model": model,
                "usage": result.get("usage", {}),
                "provider": self.provider.value
            }
    
    async def sales_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        customer_profile: Dict[str, Any],
        sales_stage: str
    ) -> Dict[str, Any]:
        prompt = f"""
        あなたは経験豊富な営業コンサルタントです。
        
        顧客発言: {user_input}
        営業ステージ: {sales_stage}
        
        以下のJSON形式で応答してください：
        {{
            "response": "適切な営業応答",
            "intent": "detected_intent",
            "sentiment": "positive/neutral/negative",
            "buying_signals": ["signal1", "signal2"],
            "concerns": ["concern1"],
            "next_action": "recommended_action",
            "recommended_stage": "next_stage",
            "confidence": 0.85
        }}
        """
        
        result = await self.chat_completion(prompt, max_tokens=800)
        
        # Parse JSON response or provide fallback
        try:
            import json
            analysis = json.loads(result["response"])
            analysis["provider"] = self.provider.value
            return analysis
        except:
            return {
                "response": "申し訳ございません。詳しくお聞かせください。",
                "intent": "general_inquiry",
                "sentiment": "neutral",
                "buying_signals": [],
                "concerns": [],
                "next_action": "clarification",
                "recommended_stage": sales_stage,
                "confidence": 0.5,
                "provider": self.provider.value
            }

class GeminiAIService(BaseAIService):
    """Gemini AI service implementation"""
    
    def __init__(self):
        super().__init__(AIProvider.GEMINI)
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.default_model = "gemini-1.5-flash"
        
        if self.api_key:
            self.available = True
        else:
            logger.warning("GEMINI_API_KEY not found")
    
    async def chat_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise AIServiceError("Gemini API key not configured")
        
        import httpx
        
        model = model or self.default_model
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": message}
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                "response": result["candidates"][0]["content"]["parts"][0]["text"],
                "model": model,
                "usage": result.get("usageMetadata", {}),
                "provider": self.provider.value
            }
    
    async def sales_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        customer_profile: Dict[str, Any],
        sales_stage: str
    ) -> Dict[str, Any]:
        prompt = f"""
        あなたは経験豊富な営業コンサルタントです。
        
        顧客発言: {user_input}
        営業ステージ: {sales_stage}
        
        以下のJSON形式で応答してください：
        {{
            "response": "適切な営業応答",
            "intent": "detected_intent",
            "sentiment": "positive/neutral/negative",
            "buying_signals": ["signal1", "signal2"],
            "concerns": ["concern1"],
            "next_action": "recommended_action",
            "recommended_stage": "next_stage",
            "confidence": 0.85
        }}
        """
        
        result = await self.chat_completion(prompt, max_tokens=800)
        
        try:
            import json
            analysis = json.loads(result["response"])
            analysis["provider"] = self.provider.value
            return analysis
        except:
            return {
                "response": "申し訳ございません。詳しくお聞かせください。",
                "intent": "general_inquiry",
                "sentiment": "neutral",
                "buying_signals": [],
                "concerns": [],
                "next_action": "clarification",
                "recommended_stage": sales_stage,
                "confidence": 0.5,
                "provider": self.provider.value
            }

class ClaudeAIService(BaseAIService):
    """Claude AI service implementation"""
    
    def __init__(self):
        super().__init__(AIProvider.CLAUDE)
        self.api_key = os.getenv("CLAUDE_API_KEY")
        self.base_url = "https://api.anthropic.com"
        self.default_model = "claude-3-5-sonnet-20241022"
        
        if self.api_key:
            # APIキーの形式チェック
            if self.api_key.startswith("sk-ant-api03-"):
                self.available = True
            else:
                logger.warning("Claude API key format invalid - should start with 'sk-ant-api03-'")
                self.available = False
        else:
            logger.warning("CLAUDE_API_KEY not found - Claude will be unavailable")
            self.available = False
    
    async def chat_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        if not self.api_key or not self.available:
            raise AIServiceError("Claude API key not configured")
        
        import httpx
        
        model = model or self.default_model
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": message}]
        }
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 400:
                    error_detail = response.text
                    
                    # クレジット不足の場合は警告のみ（定期的に復旧チェック）
                    if "credit balance is too low" in error_detail.lower():
                        logger.warning("Claude API: Credit balance too low - will retry later")
                        # availableは維持してフォールバック時に再試行可能にする
                        raise AIServiceError("Claude API: Credit balance insufficient - please add credits at https://console.anthropic.com/")
                    else:
                        logger.error(f"Claude API 400 error: {error_detail}")
                        raise AIServiceError(f"Claude API request error: {error_detail}")
                
                response.raise_for_status()
                
                result = response.json()
                return {
                    "response": result["content"][0]["text"],
                    "model": model,
                    "usage": result.get("usage", {}),
                    "provider": self.provider.value
                }
        except httpx.HTTPError as e:
            logger.error(f"Claude HTTP error: {e}")
            raise AIServiceError(f"Claude API request failed: {e}")
        except Exception as e:
            logger.error(f"Claude unexpected error: {e}")
            raise AIServiceError(f"Claude service error: {e}")
    
    async def sales_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        customer_profile: Dict[str, Any],
        sales_stage: str
    ) -> Dict[str, Any]:
        # Similar implementation to OpenAI
        prompt = f"""
        あなたは経験豊富な営業コンサルタントです。
        
        顧客発言: {user_input}
        営業ステージ: {sales_stage}
        
        以下のJSON形式で応答してください：
        {{
            "response": "適切な営業応答",
            "intent": "detected_intent",
            "sentiment": "positive/neutral/negative",
            "buying_signals": ["signal1", "signal2"],
            "concerns": ["concern1"],
            "next_action": "recommended_action",
            "recommended_stage": "next_stage",
            "confidence": 0.85
        }}
        """
        
        result = await self.chat_completion(prompt, max_tokens=800)
        
        try:
            import json
            analysis = json.loads(result["response"])
            analysis["provider"] = self.provider.value
            return analysis
        except:
            return {
                "response": "申し訳ございません。詳しくお聞かせください。",
                "intent": "general_inquiry",
                "sentiment": "neutral",
                "buying_signals": [],
                "concerns": [],
                "next_action": "clarification",
                "recommended_stage": sales_stage,
                "confidence": 0.5,
                "provider": self.provider.value
            }

class SimulationAIService(BaseAIService):
    """Simulation service (always available)"""
    
    def __init__(self):
        super().__init__(AIProvider.SIMULATION)
        self.available = True
    
    async def chat_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        # Simple rule-based response
        response = "ありがとうございます。詳しくお聞かせください。"
        
        return {
            "response": response,
            "model": "simulation",
            "usage": {"total_tokens": len(message) + len(response)},
            "provider": self.provider.value
        }
    
    async def sales_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        customer_profile: Dict[str, Any],
        sales_stage: str
    ) -> Dict[str, Any]:
        # Simple rule-based sales analysis
        intent = "information_request"
        if "料金" in user_input or "価格" in user_input or "コスト" in user_input:
            intent = "pricing_inquiry"
        elif "機能" in user_input or "できる" in user_input:
            intent = "feature_inquiry"
        elif "検討" in user_input or "考える" in user_input:
            intent = "consideration"
        elif "高い" in user_input or "安い" in user_input:
            intent = "price_objection"
        
        response = "ご質問いただき、ありがとうございます。申し訳ございませんが、もう少し詳しく教えていただけますでしょうか？お客様のご要望に最適なご提案をさせていただきたく思います。"
        
        return {
            "response": response,
            "intent": intent,
            "sentiment": "neutral",
            "buying_signals": [],
            "concerns": [],
            "next_action": "clarify_requirements",
            "recommended_stage": sales_stage,
            "confidence": 0.7,
            "provider": self.provider.value
        }

class UnifiedAIService:
    """Unified AI service that manages multiple providers"""
    
    def __init__(self):
        self.providers: Dict[AIProvider, BaseAIService] = {}
        self.primary_provider = None
        self.fallback_providers = []
        
        # Initialize all available providers
        self._initialize_providers()
        
        # Set up provider hierarchy
        self._setup_provider_hierarchy()
    
    def _initialize_providers(self):
        """Initialize all AI service providers"""
        provider_classes = {
            AIProvider.GROQ: GroqAIService,
            AIProvider.OPENAI: OpenAIService,
            AIProvider.CLAUDE: ClaudeAIService,
            AIProvider.GEMINI: GeminiAIService,
            AIProvider.SIMULATION: SimulationAIService,
        }
        
        for provider, service_class in provider_classes.items():
            try:
                service = service_class()
                self.providers[provider] = service
                logger.info(f"Initialized {provider.value} service (available: {service.available})")
            except Exception as e:
                logger.error(f"Failed to initialize {provider.value} service: {e}")
    
    def _setup_provider_hierarchy(self):
        """Set up primary and fallback providers based on availability"""
        # Preferred order: Groq -> OpenAI -> Claude -> Gemini -> Simulation
        preferred_order = [
            AIProvider.GROQ,
            AIProvider.OPENAI,
            AIProvider.CLAUDE,
            AIProvider.GEMINI,
            AIProvider.SIMULATION
        ]
        
        available_providers = [
            provider for provider in preferred_order 
            if provider in self.providers and self.providers[provider].available
        ]
        
        if available_providers:
            self.primary_provider = available_providers[0]
            self.fallback_providers = available_providers[1:]
            logger.info(f"Primary provider: {self.primary_provider.value}")
            logger.info(f"Fallback providers: {[p.value for p in self.fallback_providers]}")
        else:
            logger.error("No AI providers available!")
    
    async def chat_completion(
        self, 
        message: str, 
        model: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """Chat completion with automatic fallback"""
        
        # Use specified provider or primary
        target_provider = provider or self.primary_provider
        
        if target_provider and target_provider in self.providers:
            try:
                result = await self.providers[target_provider].chat_completion(
                    message, model, max_tokens, temperature
                )
                return result
            except Exception as e:
                logger.error(f"{target_provider.value} failed: {e}")
                
                # Try fallback providers
                for fallback in self.fallback_providers:
                    try:
                        logger.info(f"Trying fallback provider: {fallback.value}")
                        result = await self.providers[fallback].chat_completion(
                            message, model, max_tokens, temperature
                        )
                        return result
                    except Exception as fallback_error:
                        logger.error(f"{fallback.value} fallback failed: {fallback_error}")
                        continue
        
        raise AIServiceError("All AI providers failed")
    
    async def sales_analysis(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        customer_profile: Dict[str, Any],
        sales_stage: str,
        provider: Optional[AIProvider] = None
    ) -> Dict[str, Any]:
        """Sales analysis with automatic fallback"""
        
        # Use specified provider or primary
        target_provider = provider or self.primary_provider
        
        if target_provider and target_provider in self.providers:
            try:
                result = await self.providers[target_provider].sales_analysis(
                    user_input, conversation_history, customer_profile, sales_stage
                )
                return result
            except Exception as e:
                logger.error(f"{target_provider.value} failed: {e}")
                
                # Try fallback providers
                for fallback in self.fallback_providers:
                    try:
                        logger.info(f"Trying fallback provider: {fallback.value}")
                        result = await self.providers[fallback].sales_analysis(
                            user_input, conversation_history, customer_profile, sales_stage
                        )
                        return result
                    except Exception as fallback_error:
                        logger.error(f"{fallback.value} fallback failed: {fallback_error}")
                        continue
        
        raise AIServiceError("All AI providers failed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers"""
        health_status = {
            "unified_ai_service": "healthy",
            "primary_provider": self.primary_provider.value if self.primary_provider else None,
            "providers": {}
        }
        
        for provider, service in self.providers.items():
            health_status["providers"][provider.value] = await service.health_check()
        
        return health_status
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return [
            provider.value for provider, service in self.providers.items() 
            if service.available
        ]
    
    def set_primary_provider(self, provider: AIProvider):
        """Manually set primary provider"""
        if provider in self.providers and self.providers[provider].available:
            self.primary_provider = provider
            # Rebuild fallback list
            self.fallback_providers = [
                p for p in self.providers.keys() 
                if p != provider and self.providers[p].available
            ]
            logger.info(f"Primary provider changed to: {provider.value}")
        else:
            raise AIServiceError(f"Provider {provider.value} not available")

# Global unified AI service instance
_unified_ai_service: Optional[UnifiedAIService] = None

def get_unified_ai_service() -> UnifiedAIService:
    """Get or create unified AI service instance"""
    global _unified_ai_service
    if _unified_ai_service is None:
        _unified_ai_service = UnifiedAIService()
    return _unified_ai_service 