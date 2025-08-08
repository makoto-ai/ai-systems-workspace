"""
Health check endpoints
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint - same as detailed for compatibility"""
    return await detailed_health_check()

@router.get("/health/basic")
async def basic_health_check():
    """Ultra-lightweight health check for frontend"""
    return {"status": "ok"}

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with AI service status"""
    try:
        try:
            from services.ai_service import get_unified_ai_service
        except ImportError:
            from app.services.ai_service import get_unified_ai_service
        ai_service = get_unified_ai_service()
        available_providers = ai_service.get_available_providers()
        
        # 基本的なプロバイダー情報を構築
        providers_info = {}
        for provider in available_providers:
            providers_info[provider] = {
                "provider": provider,
                "status": "healthy",
                "available": True
            }
        
        return {
            "success": True,
            "health": {
                "unified_ai_service": "healthy",
                "primary_provider": ai_service.primary_provider,
                "available_providers": available_providers,
                "providers": providers_info
            }
        }
    except ImportError as e:
        return {
            "success": False,
            "error": f"AI service not available: {str(e)}",
            "health": {
                "unified_ai_service": "unavailable",
                "reason": "Import error"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI service error: {str(e)}",
            "health": {
                "unified_ai_service": "error",
                "error_details": str(e)
            }
        }

# 元の詳細ヘルスチェックを /api/health のデフォルトに設定
@router.get("")
async def complete_health_check():
    """Complete health check with AI service status - default health endpoint"""
    return await detailed_health_check() 