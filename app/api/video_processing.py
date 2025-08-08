"""
Video Processing API
Handles video upload, processing, and usage limit management
"""

import logging
import tempfile
import os
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
import asyncio

try:
    from services.usage_limit_service import get_usage_limit_service, UsageLimitService
except ImportError:
    from app.services.usage_limit_service import (
        get_usage_limit_service,
        UsageLimitService,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["video"])

# Supported video formats
SUPPORTED_VIDEO_FORMATS = {
    "video/mp4": [".mp4"],
    "video/avi": [".avi"],
    "video/mov": [".mov"],
    "video/quicktime": [".mov"],
    "video/x-msvideo": [".avi"],
    "video/webm": [".webm"],
    "video/mkv": [".mkv"],
    "video/x-matroska": [".mkv"],
}

# Processing limits
MAX_VIDEO_SIZE_MB = 1000  # 1GB max file size
MAX_VIDEO_DURATION_MINUTES = 60  # 1 hour max duration
SUPPORTED_SAMPLE_RATES = [16000, 22050, 44100, 48000]


@router.get("/supported-formats")
async def get_supported_formats() -> Dict[str, Any]:
    """
    Get supported video formats and processing limits

    Returns:
        Supported formats and limits information
    """
    return {
        "supported_formats": SUPPORTED_VIDEO_FORMATS,
        "limits": {
            "max_file_size_mb": MAX_VIDEO_SIZE_MB,
            "max_duration_minutes": MAX_VIDEO_DURATION_MINUTES,
            "supported_sample_rates": SUPPORTED_SAMPLE_RATES,
        },
        "processing_info": {
            "audio_extraction": "Automatic audio extraction from video",
            "speech_recognition": "Japanese speech recognition with WhisperX",
            "output_format": "Transcription and analysis results",
            "cloud_processing": "Processed on Hetzner Cloud for zero local load",
        },
        "usage_limits": {
            "max_video_processing_minutes": 60,
            "session_consumption": "1 roleplay session per video analysis",
            "reset_period": "30 days",
        },
    }


@router.post("/check-limits")
async def check_processing_limits(
    user_id: str = Form(...),
    video_duration_minutes: int = Form(...),
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
) -> Dict[str, Any]:
    """
    Check if user can process video of given duration

    Args:
        user_id: User identifier
        video_duration_minutes: Video duration in minutes

    Returns:
        Limit check result
    """
    try:
        result = await usage_service.can_process_video(user_id, video_duration_minutes)

        return {
            "success": True,
            "can_process": result["can_process"],
            "details": result,
        }

    except Exception as e:
        logger.error(f"Error checking processing limits: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check limits: {str(e)}")


@router.post("/upload/analyze")
async def upload_and_analyze_video(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    processing_quality: str = Form(default="medium"),
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
) -> Dict[str, Any]:
    """
    Upload and analyze video file with usage limit enforcement

    Args:
        file: Video file to process
        user_id: User identifier
        processing_quality: Processing quality (low, medium, high)

    Returns:
        Video analysis results
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("video/"):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Please upload a video file.",
            )

        if file.content_type not in SUPPORTED_VIDEO_FORMATS:
            raise HTTPException(
                status_code=415, detail=f"Unsupported video format: {file.content_type}"
            )

        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        # Check file size
        if file_size_mb > MAX_VIDEO_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum of {MAX_VIDEO_SIZE_MB}MB",
            )

        # Estimate video duration (placeholder - would need actual video analysis)
        # For now, we'll use a simple estimation based on file size
        estimated_duration_minutes = max(1, int(file_size_mb / 10))  # Rough estimate

        # Check if duration exceeds max allowed
        if estimated_duration_minutes > MAX_VIDEO_DURATION_MINUTES:
            raise HTTPException(
                status_code=413,
                detail=f"Estimated video duration ({estimated_duration_minutes}min) exceeds maximum of {MAX_VIDEO_DURATION_MINUTES}min",
            )

        # Check usage limits
        can_process_result = await usage_service.can_process_video(
            user_id, estimated_duration_minutes
        )
        if not can_process_result["can_process"]:
            raise HTTPException(status_code=429, detail=can_process_result["message"])

        # Consume usage quota
        consumption_result = await usage_service.consume_video_processing(
            user_id, estimated_duration_minutes
        )
        if not consumption_result["success"]:
            raise HTTPException(status_code=429, detail=consumption_result["message"])

        # Process video (placeholder implementation)
        # In real implementation, this would:
        # 1. Upload to Hetzner Cloud
        # 2. Extract audio from video
        # 3. Process with WhisperX
        # 4. Return transcription and analysis

        processing_result = await _process_video_placeholder(
            file_content,
            file.filename or "video",
            estimated_duration_minutes,
            processing_quality,
        )

        return {
            "success": True,
            "video_info": {
                "filename": file.filename,
                "size_mb": file_size_mb,
                "estimated_duration_minutes": estimated_duration_minutes,
                "processing_quality": processing_quality,
            },
            "usage_info": {
                "video_minutes_consumed": consumption_result["video_minutes_consumed"],
                "roleplay_sessions_consumed": consumption_result[
                    "roleplay_sessions_consumed"
                ],
                "remaining_video_minutes": consumption_result[
                    "remaining_video_minutes"
                ],
                "remaining_roleplay_sessions": consumption_result[
                    "remaining_roleplay_sessions"
                ],
            },
            "processing_results": processing_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing video: {e}")
        raise HTTPException(
            status_code=500, detail=f"Video processing failed: {str(e)}"
        )


async def _process_video_placeholder(
    file_content: bytes, filename: str, duration_minutes: int, quality: str
) -> Dict[str, Any]:
    """
    Placeholder for actual video processing
    In real implementation, this would handle cloud processing
    """
    # Simulate processing time
    await asyncio.sleep(2)

    return {
        "transcription": {
            "text": "これは動画処理のプレースホルダーです。実際の実装では、Hetzner Cloudで音声抽出と音声認識を行います。",
            "confidence": 0.95,
            "language": "ja",
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "これは動画処理のプレースホルダーです。",
                    "confidence": 0.96,
                },
                {
                    "start": 5.0,
                    "end": 10.0,
                    "text": "実際の実装では、Hetzner Cloudで音声抽出と音声認識を行います。",
                    "confidence": 0.94,
                },
            ],
        },
        "analysis": {
            "summary": "動画の音声内容を分析し、営業ロープレに活用できる情報を抽出しました。",
            "key_points": ["顧客の関心事項", "購買意欲の兆候", "懸念点や反対意見"],
            "customer_insights": {
                "type": "ANALYTICAL",
                "engagement_level": "high",
                "buying_signals": ["価格について質問", "導入時期の確認"],
            },
        },
        "processing_info": {
            "duration_minutes": duration_minutes,
            "quality": quality,
            "processing_time_seconds": 2,
            "cloud_processing": True,
        },
    }


@router.get("/usage/{user_id}")
async def get_user_usage(
    user_id: str, usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    Get user's video processing usage statistics

    Args:
        user_id: User identifier

    Returns:
        User usage information
    """
    try:
        usage_info = await usage_service.get_user_usage(user_id)

        return {"success": True, "usage": usage_info}

    except Exception as e:
        logger.error(f"Error getting user usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage: {str(e)}")


@router.post("/admin/reset-user")
async def admin_reset_user_usage(
    user_id: str = Form(...),
    admin_key: str = Form(...),
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
) -> Dict[str, Any]:
    """
    Admin endpoint to reset user usage

    Args:
        user_id: User identifier
        admin_key: Admin authentication key

    Returns:
        Reset result
    """
    # Simple admin key check (in production, use proper authentication)
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    try:
        result = await usage_service.admin_reset_user(user_id)

        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error resetting user usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset usage: {str(e)}")


@router.post("/admin/add-sessions")
async def admin_add_sessions(
    user_id: str = Form(...),
    additional_sessions: int = Form(...),
    admin_key: str = Form(...),
    usage_service: UsageLimitService = Depends(get_usage_limit_service),
) -> Dict[str, Any]:
    """
    Admin endpoint to add roleplay sessions

    Args:
        user_id: User identifier
        additional_sessions: Number of sessions to add
        admin_key: Admin authentication key

    Returns:
        Addition result
    """
    # Simple admin key check (in production, use proper authentication)
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    try:
        result = await usage_service.admin_add_sessions(user_id, additional_sessions)

        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error adding sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add sessions: {str(e)}")


@router.get("/admin/all-users")
async def admin_get_all_users_usage(
    admin_key: str, usage_service: UsageLimitService = Depends(get_usage_limit_service)
) -> Dict[str, Any]:
    """
    Admin endpoint to get all users' usage statistics

    Args:
        admin_key: Admin authentication key

    Returns:
        All users' usage information
    """
    # Simple admin key check (in production, use proper authentication)
    if admin_key != "admin123":
        raise HTTPException(status_code=403, detail="Invalid admin key")

    try:
        all_usage = await usage_service.get_all_users_usage()

        return {"success": True, "all_usage": all_usage}

    except Exception as e:
        logger.error(f"Error getting all users usage: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get all usage: {str(e)}"
        )
