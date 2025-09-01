"""
FastAPI Voice Roleplay Application
Complete voice-to-voice conversation system for sales training
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

# Import API routers
try:
    from api import (
        health,
        voice,
        conversation,
        chat,
        ai,
        speech,
        text,
        custom_analysis,
        custom_prompt,
        language_analysis,
        video_processing,
        context,
        reminder,
        file_upload,
        sales_roleplay,
        selftest,
        metrics,
        ws_voice,
        selftest,
    )
except ImportError:
    from app.api import (
        health,
        voice,
        conversation,
        chat,
        ai,
        speech,
        text,
        custom_analysis,
        custom_prompt,
        language_analysis,
        video_processing,
        context,
        reminder,
        file_upload,
        sales_roleplay,
        selftest,
        metrics,
        ws_voice,
    )

# Import configuration
try:
    from config import config
except ImportError:
    from app.config import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("🚀 Voice Roleplay System starting up...")

    # Initialize Voice Service
    try:
        try:
            from services.voice_service import VoiceService
        except ImportError:
            from app.services.voice_service import VoiceService
        voice_service = VoiceService()
        # VoiceServiceは__init__で初期化されるため、awaitは不要
        app.state.voice_service = voice_service
        logger.info("🎤 Voice service initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️  Could not initialize voice service: {e}")
        app.state.voice_service = None

    # Check configuration warnings
    warnings = config.check_warnings()
    if warnings:
        for warning in warnings:
            logger.warning(f"⚠️  {warning}")

    # Start reminder scheduler
    try:
        try:
            from api.reminder import startup_reminder_scheduler
        except ImportError:
            from app.api.reminder import startup_reminder_scheduler
        await startup_reminder_scheduler()
        logger.info("📧 Reminder scheduler initialized")
    except Exception as e:
        logger.warning(f"⚠️  Could not start reminder scheduler: {e}")

    logger.info("✅ Voice Roleplay System ready!")
    logger.info("🔒 Privacy-aware context understanding enabled")

    yield

    # Shutdown
    logger.info("👋 Voice Roleplay System shutting down...")

    # Cleanup voice service
    if hasattr(app.state, "voice_service") and app.state.voice_service:
        await app.state.voice_service.cleanup()
        logger.info("🎤 Voice service cleaned up")


# Create FastAPI app
app = FastAPI(
    title="Voice Roleplay System",
    description="Complete voice-to-voice conversation system for sales training with privacy protection",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static UI for minimal voice client
app.mount("/ui/voice", StaticFiles(directory="app/static/voice", html=True), name="ui-voice")


@app.get("/ui/voice")
async def ui_voice_root():
    """Serve minimal UI index explicitly to avoid 404s on no-trailing-slash."""
    return FileResponse("app/static/voice/index.html")

# Include API routers
app.include_router(health.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(conversation.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(text.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(speech.router, prefix="/api")
app.include_router(custom_analysis.router, prefix="/api")
app.include_router(custom_prompt.router, prefix="/api")
app.include_router(language_analysis.router, prefix="/api")
app.include_router(video_processing.router, prefix="/api")
app.include_router(context.router, prefix="/api")
app.include_router(reminder.router, prefix="/api")
app.include_router(file_upload.router, prefix="/api")
app.include_router(sales_roleplay.router, prefix="/api")
app.include_router(selftest.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
app.include_router(ws_voice.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if config.DEBUG else "An unexpected error occurred",
        },
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Roleplay System API",
        "version": "2.0.0",
        "features": {
            "voice_to_voice_conversation": True,
            "groq_ai_integration": True,
            "voicevox_tts": True,
            "whisperx_stt": True,
            "privacy_protected_context": True,
            "ml_quality_prediction": True,
            "ab_testing": True,
            "advanced_voice_analysis": True,
            "voice_cloning": True,
            "document_processing": True,
        },
        "privacy": {
            "personal_info_storage": False,
            "audio_storage": False,
            "context_anonymization": True,
            "gdpr_compliant": True,
        },
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    # Create output directories
    output_dir = Path("data/voicevox")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL.lower(),
    )
