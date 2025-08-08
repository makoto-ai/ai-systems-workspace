"""
Configuration management for Voice Roleplay System
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # HuggingFace Hub Token (for speaker diarization)
    HUGGINGFACE_HUB_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_HUB_TOKEN")
    
    # AI Service API Keys
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    #OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_GENERATIVE_AI_API_KEY: Optional[str] = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    
    # Voice Services
    VOICEVOX_HOST: str = os.getenv("VOICEVOX_HOST", "localhost")
    VOICEVOX_PORT: int = int(os.getenv("VOICEVOX_PORT", "50021"))
    
    # Advanced Features
    ENABLE_VOICE_CLONING: bool = os.getenv("ENABLE_VOICE_CLONING", "false").lower() == "true"
    ENABLE_SPEAKER_DIARIZATION: bool = os.getenv("ENABLE_SPEAKER_DIARIZATION", "false").lower() == "true"
    ENABLE_ADVANCED_VOICE_ANALYSIS: bool = os.getenv("ENABLE_ADVANCED_VOICE_ANALYSIS", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Development
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    @classmethod
    def check_warnings(cls):
        """Check configuration and provide warnings"""
        warnings = []
        
        # Only warn about HuggingFace token if speaker diarization is enabled
        if cls.ENABLE_SPEAKER_DIARIZATION and not cls.HUGGINGFACE_HUB_TOKEN:
            warnings.append("HuggingFace token not set - speaker diarization will be disabled")
        
        if cls.ENABLE_VOICE_CLONING:
            try:
                import rvc_python  # type: ignore
            except ImportError:
                warnings.append("Voice cloning enabled but rvc-python not installed")
        
        return warnings

# Create config instance
config = Config() 