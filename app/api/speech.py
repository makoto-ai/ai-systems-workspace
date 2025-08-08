"""
Speech-to-Text API endpoints using OpenAI Whisper
Phase 6: Speech-to-Text Integration
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

try:
    from services.speech_service import get_speech_service, SpeechServiceError
    from config import config
except ImportError:
    from app.services.speech_service import get_speech_service, SpeechServiceError
    from app.config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/speech", tags=["speech"])

class TranscriptionResponse(BaseModel):
    """Response model for transcription"""
    text: str
    language: str
    confidence: float
    segments: List[Dict[str, Any]]
    processing_time: float
    duration: float
    speaker_count: int
    speakers: List[str]
    has_diarization: bool

class TranscriptionRequest(BaseModel):
    """Request model for transcription with text input"""
    model_config = {"protected_namespaces": ()}
    
    audio_data: str = Field(..., description="Base64 encoded audio data")
    language: Optional[str] = Field("ja", description="Language code (default: ja)")
    model_size: Optional[str] = Field("base", description="Whisper model size")
    enable_diarization: Optional[bool] = Field(False, description="Enable speaker diarization")
    min_speakers: Optional[int] = Field(1, description="Minimum number of speakers")
    max_speakers: Optional[int] = Field(None, description="Maximum number of speakers")

@router.get("/models")
async def get_available_models() -> Dict[str, Any]:
    """Get available Whisper models and supported languages"""
    try:
        speech_service = get_speech_service()
        return {
            "models": ["tiny", "base", "small", "medium", "large"],
            "languages": list(speech_service.get_supported_languages().keys()),
            "language_names": speech_service.get_supported_languages()
        }
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/model/info")
async def get_model_info() -> Dict[str, Any]:
    """Get current model information"""
    try:
        speech_service = get_speech_service()
        return speech_service.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe")
async def transcribe_audio_file(
    file: UploadFile = File(...),
    language: Optional[str] = "ja"
) -> TranscriptionResponse:
    """
    Transcribe an uploaded audio file to text
    
    Args:
        file: Audio file (supported formats: wav, mp3, m4a, flac, etc.)
        language: Language code (default: ja for Japanese)
        
    Returns:
        Transcription results with text, confidence, and segments
    """
    import time
    start_time = time.time()
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.content_type}. Please upload an audio file."
            )
        
        # Read audio data
        audio_data = await file.read()
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Get speech service and transcribe
        speech_service = get_speech_service()
        result = await speech_service.transcribe_audio(audio_data, language)
        
        processing_time = time.time() - start_time
        
        return TranscriptionResponse(
            text=result["text"],
            language=result["language"],
            confidence=result["confidence"],
            segments=result["segments"],
            processing_time=processing_time,
            duration=result.get("duration", 0.0),
            speaker_count=result.get("speaker_count", 0),
            speakers=result.get("speakers", []),
            has_diarization=result.get("has_diarization", False)
        )
        
    except SpeechServiceError as e:
        logger.error(f"Speech service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.post("/transcribe/base64")
async def transcribe_base64_audio(
    request: TranscriptionRequest
) -> TranscriptionResponse:
    """
    Transcribe audio from base64 encoded data
    
    Args:
        request: Transcription request with base64 audio data
        
    Returns:
        Transcription results
    """
    import time
    import base64
    start_time = time.time()
    
    try:
        # Decode base64 audio data
        try:
            audio_data = base64.b64decode(request.audio_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 data: {str(e)}")
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio data")
        
        # Get speech service and transcribe
        model_size = request.model_size or "base"
        speech_service = get_speech_service(model_size=model_size)
        result = await speech_service.transcribe_audio(
            audio_data, 
            request.language,
            enable_diarization=request.enable_diarization or False,
            min_speakers=request.min_speakers or 1,
            max_speakers=request.max_speakers
        )
        
        processing_time = time.time() - start_time
        
        return TranscriptionResponse(
            text=result["text"],
            language=result["language"],
            confidence=result["confidence"],
            segments=result["segments"],
            processing_time=processing_time,
            duration=result.get("duration", 0.0),
            speaker_count=result.get("speaker_count", 0),
            speakers=result.get("speakers", []),
            has_diarization=result.get("has_diarization", False)
        )
        
    except SpeechServiceError as e:
        logger.error(f"Speech service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in base64 transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

# OpenAI Whisper compatible endpoint
@router.post("/audio/transcriptions")
async def openai_compatible_transcription(
    file: UploadFile = File(...),
    model: str = "whisper-1",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
    response_format: Optional[str] = "json",
    temperature: Optional[float] = 0.0
) -> Dict[str, Any]:
    """
    OpenAI Whisper API compatible transcription endpoint
    
    Args:
        file: Audio file to transcribe
        model: Model name (ignored, always uses local Whisper)
        language: Language of the input audio
        prompt: Optional text to guide the model's style
        response_format: Response format (json, text, srt, verbose_json, vtt)
        temperature: Sampling temperature
        
    Returns:
        Transcription in requested format
    """
    import time
    start_time = time.time()
    
    try:
        # Read audio data
        audio_data = await file.read()
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Get speech service and transcribe
        speech_service = get_speech_service()
        result = await speech_service.transcribe_audio(audio_data, language)
        
        processing_time = time.time() - start_time
        
        # Format response based on requested format
        if response_format == "text":
            return {"text": result["text"]}
        elif response_format == "verbose_json":
            return {
                "task": "transcribe",
                "language": result["language"],
                "duration": result["segments"][-1]["end"] if result["segments"] else 0.0,
                "text": result["text"],
                "segments": result["segments"]
            }
        else:  # json (default)
            return {"text": result["text"]}
            
    except SpeechServiceError as e:
        logger.error(f"Speech service error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in OpenAI compatible transcription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@router.get("/health")
async def speech_health_check() -> Dict[str, Any]:
    """Health check for speech service"""
    try:
        speech_service = get_speech_service()
        model_info = speech_service.get_model_info()
        return {
            "status": "healthy",
            "service": "speech-to-text",
            "model_loaded": model_info["loaded"],
            "model_size": model_info["model_size"],
            "device": model_info["device"],
            "features": model_info.get("features", {})
        }
    except Exception as e:
        logger.error(f"Speech service health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "speech-to-text",
            "error": str(e)
        } 