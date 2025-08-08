# Speaker Diarization Setup Guide

## Overview

Speaker diarization is the process of partitioning an audio stream into homogeneous segments according to the speaker identity. This feature allows the system to identify "who spoke when" in multi-speaker conversations.

## Prerequisites

### 1. HuggingFace Account and Token

To use speaker diarization, you need a HuggingFace account and access token:

1. **Create Account**: Go to [HuggingFace](https://huggingface.co) and create an account
2. **Get Access Token**: Visit [Settings → Access Tokens](https://huggingface.co/settings/tokens)
3. **Create Token**: Create a new token with "Read" permissions

### 2. Accept User Agreements

You must accept the user agreements for the following models:

1. **pyannote/segmentation-3.0**: https://huggingface.co/pyannote/segmentation-3.0
2. **pyannote/speaker-diarization-3.1**: https://huggingface.co/pyannote/speaker-diarization-3.1

Click "Accept" on both model pages while logged into your HuggingFace account.

## Configuration

### Environment Variable

Set your HuggingFace token as an environment variable:

```bash
export HF_TOKEN="your_huggingface_token_here"
```

### Using .env File

Create a `.env` file in the project root:

```bash
# HuggingFace Token for Speaker Diarization
HF_TOKEN=your_huggingface_token_here
```

### Programmatic Configuration

You can also pass the token directly when initializing the service:

```python
from app.services.speech_service import get_speech_service

# Initialize with HF token
service = get_speech_service(hf_token="your_token_here")
```

## Usage Examples

### API Request with Diarization

```python
import requests

# Transcription with speaker diarization
payload = {
    "audio": "base64_encoded_audio_data",
    "language": "ja",
    "enable_diarization": True,
    "min_speakers": 2,
    "max_speakers": 5
}

response = requests.post(
    "http://localhost:8080/speech/transcribe/base64",
    json=payload
)

result = response.json()
print(f"Speakers found: {result['speakers']}")
print(f"Speaker count: {result['speaker_count']}")
```

### Response Format with Diarization

```json
{
    "text": "Full transcribed text",
    "language": "ja",
    "confidence": 0.95,
    "duration": 30.5,
    "speaker_count": 3,
    "speakers": ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"],
    "has_diarization": true,
    "segments": [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "Hello, this is speaker one.",
            "confidence": 0.92,
            "speaker": "SPEAKER_00"
        },
        {
            "start": 2.8,
            "end": 5.1,
            "text": "And this is speaker two responding.",
            "confidence": 0.88,
            "speaker": "SPEAKER_01"
        }
    ]
}
```

## Testing Speaker Diarization

### Run Test Suite

```bash
python test_whisper.py
```

The test will show whether speaker diarization is available:

- ✅ **Working**: HuggingFace token configured correctly
- ❌ **Not Available**: Token missing or invalid

### Expected Test Output

```
📋 Test: Model Information
----------------------------------------
✅ Model Info:
   - Model: base
   - Device: cpu
   - HF Token: ✅
   - Transcription: ✅
   - Alignment: ✅
   - Speaker Diarization: ✅
```

## Troubleshooting

### Common Issues

1. **Token Not Found**
   ```
   No HuggingFace token provided - speaker diarization disabled
   ```
   **Solution**: Set the `HF_TOKEN` environment variable

2. **Invalid Token**
   ```
   Failed to load diarization model: HTTP 401 Unauthorized
   ```
   **Solution**: Check your token is correct and has read permissions

3. **User Agreement Not Accepted**
   ```
   Failed to load diarization model: HTTP 403 Forbidden
   ```
   **Solution**: Accept user agreements for both pyannote models

4. **Model Loading Failed**
   ```
   Failed to load diarization model on demand
   ```
   **Solution**: Check internet connection and HuggingFace status

### Performance Considerations

- **CPU vs GPU**: Diarization is faster on GPU but works on CPU
- **Memory Usage**: Speaker diarization requires additional ~1-2GB RAM
- **Processing Time**: Adds ~2-5x processing time compared to transcription only
- **Model Size**: Downloads ~500MB of models on first use

## Sales Roleplay Use Cases

### Customer-Representative Conversations

```python
# Analyze sales call with customer and representative
payload = {
    "audio": sales_call_audio,
    "enable_diarization": True,
    "min_speakers": 2,  # Customer + Representative
    "max_speakers": 3,  # Allow for potential supervisor
    "language": "ja"
}
```

### Benefits for Sales Training

1. **Speaker Identification**: Automatically identify customer vs representative
2. **Talk Time Analysis**: Measure who speaks more and when
3. **Conversation Flow**: Understand interaction patterns
4. **Quality Assessment**: Analyze response timing and overlap
5. **Training Material**: Generate speaker-specific feedback

### Integration with VOICEVOX

The system can combine diarization with TTS for full voice-to-voice roleplay:

1. **Input**: Multi-speaker audio (customer + trainee)
2. **Process**: 
   - Transcribe with speaker labels
   - Analyze conversation with Dify
   - Generate coaching feedback
3. **Output**: Synthesized feedback via VOICEVOX

## Advanced Configuration

### Custom Speaker Limits

```python
# For large meetings
max_speakers = 10

# For one-on-one calls  
min_speakers = 2
max_speakers = 2
```

### Language-Specific Settings

Currently supported languages for diarization:
- Japanese (ja)
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)

## Security Notes

- Store HuggingFace tokens securely
- Use environment variables in production
- Rotate tokens periodically
- Monitor token usage on HuggingFace dashboard

## Next Steps

1. Test basic transcription first
2. Configure HuggingFace token
3. Test speaker diarization
4. Integrate with Dify workflows
5. Deploy with environment variables 