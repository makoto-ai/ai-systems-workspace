from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    from core.voicevox import (
        VoicevoxClient,
        VoicevoxConnectionError,
        EmotionParams,
        Speaker,
    )
    from core.speakers import VOICEVOX_SPEAKER_MAPPING
except ImportError:
    from app.core.voicevox import (
        VoicevoxClient,
        VoicevoxConnectionError,
        EmotionParams,
        Speaker,
    )
    from app.core.speakers import VOICEVOX_SPEAKER_MAPPING
import weakref
import os

logger = logging.getLogger(__name__)


class VoiceServiceError(Exception):
    """音声サービスのエラー"""

    pass


class SpeakerNotFoundError(Exception):
    """話者が見つからないエラー"""

    pass


class VoiceService:
    _instances = weakref.WeakValueDictionary()

    def __new__(
        cls, host: str = "localhost", port: str = "50021", test_mode: bool = False
    ):
        """シングルトンインスタンスを作成または取得します"""
        key = (host, port, test_mode)
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(
        self, host: str = "localhost", port: str = "50021", test_mode: bool = False
    ):
        """初期化（シングルトンインスタンスの場合は一度だけ実行）"""
        if not hasattr(self, "_initialized") or not self._initialized:
            logger.info(f"Initializing VoiceService with host={host}, port={port}")
            self.client = VoicevoxClient(host=host, port=port)
            self.output_dir = Path(os.getenv("OUTPUT_DIR", "./data/voicevox"))
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.test_mode = test_mode
            self._initialized = True
            logger.info("VoiceService initialized successfully")

    async def cleanup(self):
        """サービスのクリーンアップを行います"""
        try:
            await self.client.close()
            logger.info("VoiceService cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during VoiceService cleanup: {e}")
            raise VoiceServiceError(f"Failed to cleanup VoiceService: {e}")

    async def check_voicevox_status(self) -> bool:
        """VOICEVOXサーバーの状態を確認します"""
        try:
            # VOICEVOXサーバーの状態を確認
            speakers = await self.client.get_speakers()
            return len(speakers) > 0
        except Exception as e:
            logger.error(f"Failed to check VOICEVOX status: {e}")
            return False

    async def synthesize_voice(
        self, text: str, speaker_id: int, emotion: Optional[EmotionParams] = None
    ) -> Optional[bytes]:
        """テキストから音声データを生成する (EXTREME SPEED MODE: 0.2-0.4秒)"""
        try:
            # 話者IDのバリデーション
            if not await self.validate_speaker_id(speaker_id):
                raise SpeakerNotFoundError(f"Speaker ID {speaker_id} not found")

            # テストモードの場合はモックデータを返す
            if self.test_mode:
                # テスト用の簡単なWAVヘッダー付きダミーデータ
                # 実際のWAVファイルの最小構造を模擬
                wav_header = (
                    b"RIFF"
                    + b"\x00" * 4
                    + b"WAVE"
                    + b"fmt "
                    + b"\x00" * 16
                    + b"data"
                    + b"\x00" * 4
                )
                return wav_header + b"\x00" * 100  # ダミーの音声データ

            # EXTREME SPEED: Skip speaker validation for speed
            # Use VOICEVOX mapping directly
            if speaker_id in VOICEVOX_SPEAKER_MAPPING:
                voicevox_params = VOICEVOX_SPEAKER_MAPPING[speaker_id]
                speaker_id = voicevox_params["speaker"]

            # Do not truncate: synthesize full text to avoid early cut-off
            # (VOICEVOX handles sentence-length inputs; allow full reply)

            # EXTREME SPEED: Skip emotion parameters completely
            # Create audio query with absolute minimum settings
            audio_query = await self.client.create_audio_query(text, speaker_id)
            if not audio_query:
                logger.error("Failed to create audio query")
                return None

            # EXTREME SPEED: Tune audio_query for faster first audio
            try:
                # Speed up speech while keeping naturalness
                audio_query["speedScale"] = float(max(1.2, min(1.50, audio_query.get("speedScale", 1.35))))
                # Minimize leading/trailing silences
                audio_query["prePhonemeLength"] = float(min(0.05, audio_query.get("prePhonemeLength", 0.1)))
                audio_query["postPhonemeLength"] = float(min(0.06, audio_query.get("postPhonemeLength", 0.1)))
                # Shorten pauses between sentences if present
                if "pauseLength" in audio_query:
                    audio_query["pauseLength"] = float(min(0.05, audio_query.get("pauseLength", 0.1)))
                if "pauseLengthScale" in audio_query:
                    audio_query["pauseLengthScale"] = float(min(0.8, audio_query.get("pauseLengthScale", 1.0)))
            except Exception:
                # If the query format differs, continue safely
                pass

            wav_data = await self.client.synthesis(audio_query, speaker_id)
            if not wav_data:
                logger.error("Failed to synthesize audio")
                return None

            return wav_data

        except SpeakerNotFoundError:
            # 話者エラーは再度スローする
            raise
        except Exception as e:
            logger.error(f"Error in extreme speed voice synthesis: {e}")
            # EXTREME SPEED: Return minimal error audio
            return b""  # Empty bytes for fastest fallback

    async def get_speakers(self) -> Dict[str, Dict[str, Any]]:
        """利用可能な話者の一覧を取得する"""
        try:
            # テストモードの場合はモックデータを返す
            if self.test_mode:
                return {
                    "1": {
                        "id": 1,
                        "name": "Test Speaker 1",
                        "description": "Test speaker for unit tests",
                    },
                    "2": {
                        "id": 2,
                        "name": "Test Speaker 2",
                        "description": "Test speaker for unit tests",
                    },
                    "3": {
                        "id": 3,
                        "name": "Test Speaker 3",
                        "description": "Test speaker for unit tests",
                    },
                }

            speakers = await self.client.get_speakers()
            speaker_dict = {}

            # VOICEVOXの話者を追加
            for speaker in speakers:
                speaker_dict[str(speaker.id)] = {
                    "id": speaker.id,
                    "name": speaker.name,
                    "description": f"VOICEVOX Speaker {speaker.id}",
                }

            # ビジネス話者のマッピングを追加
            for business_id, voicevox_params in VOICEVOX_SPEAKER_MAPPING.items():
                voicevox_id = str(voicevox_params["speaker"])
                if voicevox_id in speaker_dict:
                    speaker_dict[str(business_id)] = speaker_dict[voicevox_id].copy()
                    speaker_dict[str(business_id)]["id"] = business_id

            return speaker_dict
        except Exception as e:
            logger.error(f"Failed to get speakers: {e}")
            raise VoiceServiceError(f"Failed to get speakers: {e}")

    async def validate_speaker_id(self, speaker_id: int) -> bool:
        """話者IDが有効かどうかを確認する"""
        try:
            logger.info(f"Validating speaker ID: {speaker_id}")
            # テストモードの場合は特定の話者IDのみ有効とする
            if self.test_mode:
                valid_ids = [1, 2, 3, 4, 5]  # テスト用の有効な話者ID
                is_valid = speaker_id in valid_ids
                logger.info(
                    f"Test mode: Speaker ID {speaker_id} is {'valid' if is_valid else 'invalid'}"
                )
                return is_valid

            speakers = await self.get_speakers()
            logger.info(f"Available speakers: {list(speakers.keys())}")
            is_valid = str(speaker_id) in speakers
            logger.info(
                f"Speaker ID {speaker_id} is {'valid' if is_valid else 'invalid'}"
            )
            return is_valid
        except Exception as e:
            logger.error(f"Error validating speaker ID: {e}")
            return False
