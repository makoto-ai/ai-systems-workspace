from typing import Optional, Dict, Any, List, cast
import aiohttp
import asyncio
from pathlib import Path
import logging
from .speakers import get_voicevox_params, get_all_speakers
import re
import weakref
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Speaker:
    id: int
    name: str


@dataclass
class EmotionParams:
    pitch: float = 0.0
    speed: float = 1.0
    intonation: float = 1.0
    volume: float = 1.0
    pre_phoneme: float = 0.1
    post_phoneme: float = 0.1

    @classmethod
    def happy(cls) -> "EmotionParams":
        return cls(pitch=0.1, speed=1.2, intonation=1.2, volume=1.2)

    @classmethod
    def sad(cls) -> "EmotionParams":
        return cls(pitch=-0.1, speed=0.8, intonation=0.8, volume=0.8)

    @classmethod
    def angry(cls) -> "EmotionParams":
        return cls(pitch=0.1, speed=1.3, intonation=1.5, volume=1.5)

    @classmethod
    def surprised(cls) -> "EmotionParams":
        return cls(pitch=0.15, speed=1.4, intonation=1.8, volume=1.2)

    def apply_to_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """感情パラメータをクエリに適用する"""
        query.update(
            {
                "speedScale": self.speed,
                "pitchScale": self.pitch,
                "intonationScale": self.intonation,
                "volumeScale": self.volume,
                "prePhonemeLength": self.pre_phoneme,
                "postPhonemeLength": self.post_phoneme,
            }
        )
        return query


class VoicevoxConnectionError(Exception):
    """VOICEVOXサーバーとの通信エラー"""

    pass


class VoicevoxClient:
    _instances = weakref.WeakValueDictionary()

    def __new__(
        cls,
        host: str = "localhost",
        port: str = "50021",
        max_retries: int = 3,
        retry_interval: float = 1.0,
    ):
        """シングルトンインスタンスを作成または取得します"""
        key = (host, port)
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[key] = instance
        return cls._instances[key]

    def __init__(
        self,
        host: str = "localhost",
        port: str = "50021",
        max_retries: int = 3,
        retry_interval: float = 1.0,
    ):
        """初期化（シングルトンインスタンスの場合は一度だけ実行）"""
        if not hasattr(self, "_initialized") or not self._initialized:
            self.host = host
            self.port = port
            self.base_url = f"http://{host}:{port}"
            self.max_retries = max_retries
            self.retry_interval = retry_interval
            self._session: Optional[aiohttp.ClientSession] = None
            self._initialized = True
            logger.info(f"VoicevoxClient initialized with base_url: {self.base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """セッションを取得または初期化する"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_speakers(self) -> List[Speaker]:
        """利用可能な話者の一覧を取得する"""
        try:
            logger.info("Fetching speakers from VOICEVOX")
            session = await self._get_session()
            async with session.get(f"{self.base_url}/speakers") as response:
                if response.status != 200:
                    logger.error(f"Failed to get speakers: {response.status}")
                    raise VoicevoxConnectionError(
                        f"Failed to get speakers: {response.status}"
                    )
                data = await response.json()
                speakers = []
                for speaker_data in data:
                    for style in speaker_data["styles"]:
                        speaker = Speaker(
                            id=style["id"],
                            name=f"{speaker_data['name']} ({style['name']})",
                        )
                        speakers.append(speaker)
                        logger.info(f"Found speaker: {speaker.name} (ID: {speaker.id})")
                return speakers
        except Exception as e:
            logger.error(f"Error getting speakers: {e}")
            raise VoicevoxConnectionError(f"Failed to get speakers: {e}")

    async def create_audio_query(self, text: str, speaker_id: int) -> Dict[str, Any]:
        """音声合成用のクエリを作成する"""
        try:
            session = await self._get_session()
            params = {"text": text, "speaker": speaker_id}
            async with session.post(
                f"{self.base_url}/audio_query", params=params
            ) as response:
                if response.status != 200:
                    raise VoicevoxConnectionError(
                        f"Failed to create audio query: {response.status}"
                    )
                return await response.json()
        except Exception as e:
            logger.error(f"Error creating audio query: {e}")
            raise VoicevoxConnectionError(f"Failed to create audio query: {e}")

    async def synthesis(self, audio_query: Dict[str, Any], speaker_id: int) -> bytes:
        """音声を合成する"""
        try:
            session = await self._get_session()
            params = {"speaker": speaker_id}
            async with session.post(
                f"{self.base_url}/synthesis", params=params, json=audio_query
            ) as response:
                if response.status != 200:
                    raise VoicevoxConnectionError(
                        f"Failed to synthesize audio: {response.status}"
                    )
                return await response.read()
        except Exception as e:
            logger.error(f"Error synthesizing audio: {e}")
            raise VoicevoxConnectionError(f"Failed to synthesize audio: {e}")

    async def close(self):
        """セッションを閉じる"""
        try:
            if self._session and not self._session.closed:
                await self._session.close()
                self._session = None
                logger.info("VoicevoxClient session closed successfully")
        except Exception as e:
            logger.error(f"Error closing VoicevoxClient session: {e}")
            raise VoicevoxConnectionError(f"Failed to close session: {e}")

    def _apply_emotion_params(
        self, audio_query: Dict[str, Any], emotion: Optional[EmotionParams] = None
    ) -> Dict[str, Any]:
        """感情パラメータを適用"""
        if emotion is None:
            return audio_query
        return emotion.apply_to_query(audio_query)

    def _process_text_with_pauses(self, text: str) -> List[str]:
        """テキストをポーズ制御付きで処理"""
        # カスタムポーズマーカーの処理 (例: <p>, <pause>, ...)
        text = re.sub(r"<p>", "。。。", text)
        text = re.sub(r"<pause>", "。。。", text)

        # 文末の処理
        text = re.sub(r"([。、．，!?！？])", r"\1。", text)

        # 長いポーズの処理
        text = re.sub(r"。{3,}", "。。。", text)

        # テキストを文に分割
        sentences = re.split(r"([。、．，!?！？]。)", text)
        return [s for s in sentences if s.strip()]

    async def text_to_speech(
        self,
        text: str,
        speaker_id: int,
        output_path: Optional[Path] = None,
        enable_interrogative_upspeak: bool = True,
        emotion: Optional[EmotionParams] = None,
    ) -> Path:
        """テキストから音声を生成し、ファイルに保存します"""
        try:
            # テキストをポーズ制御付きで処理
            text_parts = self._process_text_with_pauses(text)
            all_wav_data = []

            for part in text_parts:
                # 音声合成用のクエリを作成
                audio_query = await self.create_audio_query(part, speaker_id)

                # 感情パラメータを適用
                audio_query = self._apply_emotion_params(audio_query, emotion)

                # 疑問文の自動調整
                if enable_interrogative_upspeak and part.strip().endswith(("?", "？")):
                    audio_query["accent_phrases"][-1]["pitch"] = 1.5

                # 音声を合成
                wav_data = await self.synthesis(audio_query, speaker_id)
                all_wav_data.append(wav_data)

            # 出力パスが指定されていない場合は一時ファイルを作成
            if output_path is None:
                output_path = Path("data/voicevox/output.wav")

            # 出力ディレクトリが存在しない場合は作成
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 音声データをファイルに保存
            with open(output_path, "wb") as f:
                for wav_data in all_wav_data:
                    f.write(wav_data)

            return output_path

        except Exception as e:
            raise VoicevoxConnectionError(f"Failed to generate voice: {e}")
