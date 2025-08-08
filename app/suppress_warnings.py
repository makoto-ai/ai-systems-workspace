"""
Suppress specific warnings in the Voice Roleplay System
"""
import warnings
import os

def suppress_warnings():
    """Suppress known warnings that don't affect functionality"""
    
    # Suppress pkg_resources deprecation warning
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="pkg_resources")
    warnings.filterwarnings("ignore", message="pkg_resources is deprecated")
    
    # Suppress pyannote.audio version mismatch warnings
    warnings.filterwarnings("ignore", message="Model was trained with pyannote.audio")
    warnings.filterwarnings("ignore", message="Model was trained with torch")
    
    # Suppress PyTorch Lightning upgrade warnings
    warnings.filterwarnings("ignore", message="Lightning automatically upgraded")
    
    # Suppress SpeechBrain deprecation warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="speechbrain")
    
    # Suppress transformers gradient checkpointing warning
    warnings.filterwarnings("ignore", message="Passing `gradient_checkpointing`")
    
    # Set environment variable to reduce verbosity
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    
    # Reduce logging verbosity for specific modules
    import logging
    logging.getLogger("speechbrain").setLevel(logging.ERROR)
    logging.getLogger("pyannote").setLevel(logging.ERROR)
    logging.getLogger("whisperx").setLevel(logging.WARNING) 