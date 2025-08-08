"""
Unified AI Service API Endpoints
Phase 8: Multi-Provider AI Management
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
import logging

try:
    from services.ai_service import get_unified_ai_service, AIProvider, AIServiceError
except ImportError:
    from app.services.ai_service import get_unified_ai_service, AIProvider, AIServiceError

logger = logging.getLogger(__name__)
router = APIRouter()

class ChatRequest(BaseModel):
    """Request model for chat completion"""
    message: str = Field(..., description="Input message")
    model: Optional[str] = Field(None, description="Specific model to use")
    max_tokens: int = Field(1000, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Sampling temperature")
    provider: Optional[str] = Field(None, description="Specific AI provider to use")

class SalesAnalysisRequest(BaseModel):
    """Request model for sales analysis"""
    user_input: str = Field(..., description="Customer input")
    conversation_history: List[Dict[str, Any]] = Field(default=[], description="Previous conversation")
    customer_profile: Dict[str, Any] = Field(default={}, description="Customer information")
    sales_stage: str = Field("prospecting", description="Current sales stage")
    provider: Optional[str] = Field(None, description="Specific AI provider to use")

class ProviderSwitchRequest(BaseModel):
    """Request model for switching primary provider"""
    provider: str = Field(..., description="Provider to set as primary")

@router.post("/chat")
async def chat_completion(request: ChatRequest) -> Dict[str, Any]:
    """
    Chat completion with automatic provider fallback
    
    Supports multiple AI providers:
    - groq: Groq API (fast, cost-effective)
    - openai: OpenAI GPT models
    - claude: Claude AI

    - simulation: Rule-based fallback
    """
    try:
        ai_service = get_unified_ai_service()
        
        # Convert provider string to enum if specified
        provider = None
        if request.provider:
            try:
                provider = AIProvider(request.provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid provider: {request.provider}. Available: {ai_service.get_available_providers()}"
                )
        
        result = await ai_service.chat_completion(
            message=request.message,
            model=request.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            provider=provider
        )
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for invalid provider)
        raise
    except AIServiceError as e:
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat completion: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

@router.post("/sales-analysis")
async def sales_analysis(request: SalesAnalysisRequest) -> Dict[str, Any]:
    """
    Advanced sales conversation analysis with provider fallback
    
    Analyzes customer input and provides:
    - Intent detection
    - Sentiment analysis
    - Buying signals
    - Recommended actions
    - Next sales stage
    """
    try:
        ai_service = get_unified_ai_service()
        
        # Convert provider string to enum if specified
        provider = None
        if request.provider:
            try:
                provider = AIProvider(request.provider.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid provider: {request.provider}. Available: {ai_service.get_available_providers()}"
                )
        
        result = await ai_service.sales_analysis(
            user_input=request.user_input,
            conversation_history=request.conversation_history,
            customer_profile=request.customer_profile,
            sales_stage=request.sales_stage,
            provider=provider
        )
        
        return {
            "success": True,
            "analysis": result
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 400 for invalid provider)
        raise
    except AIServiceError as e:
        logger.error(f"AI service error: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in sales analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sales analysis failed: {str(e)}")

@router.get("/providers")
async def get_providers() -> Dict[str, Any]:
    """
    Get information about available AI providers
    """
    try:
        ai_service = get_unified_ai_service()
        health_status = await ai_service.health_check()
        
        return {
            "success": True,
            "providers": health_status
        }
        
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/providers/switch")
async def switch_primary_provider(request: ProviderSwitchRequest) -> Dict[str, Any]:
    """
    Switch the primary AI provider
    """
    try:
        ai_service = get_unified_ai_service()
        
        # Convert provider string to enum
        try:
            provider = AIProvider(request.provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid provider: {request.provider}. Available: {ai_service.get_available_providers()}"
            )
        
        ai_service.set_primary_provider(provider)
        
        return {
            "success": True,
            "message": f"Primary provider switched to {provider.value}",
            "primary_provider": provider.value
        }
        
    except AIServiceError as e:
        logger.error(f"Provider switch error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error switching provider: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def ai_health_check() -> Dict[str, Any]:
    """
    Comprehensive health check for all AI providers
    """
    try:
        ai_service = get_unified_ai_service()
        health_status = await ai_service.health_check()
        
        return {
            "success": True,
            "health": health_status
        }
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """
    Get available models for each provider
    """
    try:
        models_info = {
            "groq": {
                "models": [
                    "llama-3.3-70b-versatile",
                    "llama-3.1-8b-instant", 
                    "mixtral-8x7b-32768",
                    "gemma2-9b-it"
                ],
                "default": "llama-3.3-70b-versatile",
                "description": "Fast inference with Groq LPU"
            },
            "openai": {
                "models": [
                    "gpt-4",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo"
                ],
                "default": "gpt-4",
                "description": "OpenAI GPT models"
            },
            "claude": {
                "models": [
                    "claude-3-sonnet-20240229",
                    "claude-3-haiku-20240307"
                ],
                "default": "claude-3-sonnet-20240229",
                "description": "Anthropic Claude models"
            },
            "gemini": {
                "models": [
                    "gemini-pro",
                    "gemini-pro-vision",
                    "gemini-1.5-pro",
                    "gemini-1.5-flash"
                ],
                "default": "gemini-pro",
                "description": "Google Gemini models"
            },

            "simulation": {
                "models": ["rule-based"],
                "default": "rule-based",
                "description": "Local simulation (always available)"
            }
        }
        
        return {
            "success": True,
            "models": models_info
        }
        
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 