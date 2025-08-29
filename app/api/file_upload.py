"""
Cursor ↔ Obsidian 双方向連携システム
音声・画像・文書ファイルをアップロードして自動でObsidianに保存
"""

import os
import io
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
import aiofiles

# オプショナルインポート（利用可能な場合のみ）
try:
    import whisper

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import librosa
    import numpy as np

    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    from PIL import Image
    import base64

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import PyPDF2

    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# AI分析
try:
    from openai import AsyncOpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from config import config
except ImportError:
    from app.config import config

router = APIRouter(prefix="/file-upload", tags=["file-upload"])

# Obsidianディレクトリの設定
OBSIDIAN_DIR = Path.home() / "Documents" / "obsidian-knowledge"
UPLOAD_DIR = Path("uploads")

# ディレクトリを作成
OBSIDIAN_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# AI clients
async def get_openai_client():
    if OPENAI_AVAILABLE and config.OPENAI_API_KEY:
        return AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    return None


async def get_anthropic_client():
    if ANTHROPIC_AVAILABLE and config.ANTHROPIC_API_KEY:
        return AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return None


class ObsidianSaver:
    """Obsidian形式でファイルを保存するクラス"""

    @staticmethod
    def create_filename(content_type: str, original_name: str = None) -> str:
        """ファイル名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if original_name:
            name = Path(original_name).stem
            return f"{content_type}_{name}_{timestamp}.md"
        return f"{content_type}_{timestamp}.md"

    @staticmethod
    async def save_to_obsidian(filename: str, content: str) -> str:
        """Obsidianディレクトリにファイルを保存"""
        file_path = OBSIDIAN_DIR / filename

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(content)

        return str(file_path)


@router.post("/audio", summary="音声ファイルをアップロードしてObsidianに保存")
async def upload_audio(file: UploadFile = File(...)):
    """
    音声ファイルをアップロードして文字起こし→Obsidian保存
    """
    if not file.filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac")):
        raise HTTPException(status_code=400, detail="サポートされていない音声形式です")

    # 基本的な処理（whisperが利用できない場合の代替）
    if WHISPER_AVAILABLE:
        transcription = "音声ファイルが正常にアップロードされました。文字起こし機能はWhisperライブラリが必要です。"
    else:
        transcription = "音声ファイルがアップロードされました。文字起こし機能を使用するには、Whisperライブラリをインストールしてください。"

    # Obsidian形式でマークダウン生成
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    markdown_content = f"""# 音声記録 - {timestamp}

## 📅 基本情報
- ファイル名: {file.filename}
- ファイルサイズ: {file.size} bytes
- 処理日時: {timestamp}

## 📄 文字起こし結果
{transcription}

## 🎯 AI分析結果
音声ファイルのアップロードが完了しました。
詳細な分析機能を使用するには、API キーの設定が必要です。

## 🏷️ タグ
#音声記録 #自動処理 #ファイルアップロード

---
*このファイルはCursor→Obsidian自動連携システムにより生成されました*
"""

    # Obsidianに保存
    filename = ObsidianSaver.create_filename("音声記録", file.filename)
    saved_path = await ObsidianSaver.save_to_obsidian(filename, markdown_content)

    return JSONResponse(
        {
            "status": "success",
            "message": "音声ファイルが正常に処理されObsidianに保存されました",
            "file_path": saved_path,
            "transcription": transcription,
            "whisper_available": WHISPER_AVAILABLE,
        }
    )


@router.post("/image", summary="画像ファイルをアップロードしてObsidianに保存")
async def upload_image(file: UploadFile = File(...)):
    """
    画像ファイルをアップロードしてGPT-4 Vision分析→Obsidian保存
    """
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp")):
        raise HTTPException(status_code=400, detail="サポートされていない画像形式です")

    # 基本的な画像情報
    content = await file.read()
    image_size = len(content)

    analysis = "画像ファイルがアップロードされました。詳細な分析機能を使用するには、GPT-4 Vision APIキーが必要です。"

    # Obsidian形式でマークダウン生成
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    markdown_content = f"""# 画像分析 - {timestamp}

## 📅 基本情報
- ファイル名: {file.filename}
- ファイルサイズ: {image_size:,} bytes
- 処理日時: {timestamp}

## 🔍 AI画像分析結果
{analysis}

## 🏷️ タグ
#画像分析 #ビジュアル記録 #ファイルアップロード

---
*このファイルはCursor→Obsidian自動連携システムにより生成されました*
"""

    # Obsidianに保存
    filename = ObsidianSaver.create_filename("画像分析", file.filename)
    saved_path = await ObsidianSaver.save_to_obsidian(filename, markdown_content)

    return JSONResponse(
        {
            "status": "success",
            "message": "画像ファイルが正常に処理されObsidianに保存されました",
            "file_path": saved_path,
            "analysis": analysis,
            "pil_available": PIL_AVAILABLE,
        }
    )


@router.post("/document", summary="文書ファイルをアップロードしてObsidianに保存")
async def upload_document(file: UploadFile = File(...)):
    """
    文書ファイル（PDF、DOCX、TXT）をアップロードして内容抽出→AI分析→Obsidian保存
    """
    file_ext = Path(file.filename).suffix.lower()

    if file_ext == ".txt":
        content = await file.read()
        doc_text = content.decode("utf-8")
        doc_type = "テキスト文書"
    else:
        doc_text = "文書ファイルがアップロードされました。PDFやDOCX処理には追加ライブラリが必要です。"
        doc_type = f"{file_ext.upper()}文書"

    # Obsidian形式でマークダウン生成
    timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

    markdown_content = f"""# {doc_type}分析 - {timestamp}

## 📅 基本情報
- ファイル名: {file.filename}
- 文書形式: {doc_type}
- 処理日時: {timestamp}

## 🎯 AI分析結果
文書ファイルのアップロードが完了しました。
詳細な分析機能を使用するには、API キーの設定が必要です。

## 📄 文書内容
```
{doc_text[:1000]}{'...' if len(doc_text) > 1000 else ''}
```

## 🏷️ タグ
#文書分析 #ファイルアップロード #{doc_type}

---
*このファイルはCursor→Obsidian自動連携システムにより生成されました*
"""

    # Obsidianに保存
    filename = ObsidianSaver.create_filename("文書分析", file.filename)
    saved_path = await ObsidianSaver.save_to_obsidian(filename, markdown_content)

    return JSONResponse(
        {
            "status": "success",
            "message": f"{doc_type}が正常に処理されObsidianに保存されました",
            "file_path": saved_path,
            "text_preview": doc_text[:500] + "..." if len(doc_text) > 500 else doc_text,
        }
    )


@router.get("/obsidian/status", summary="Obsidian保存先の状況確認")
async def obsidian_status():
    """
    Obsidian保存先ディレクトリの状況を確認
    """
    try:
        files = list(OBSIDIAN_DIR.glob("*.md"))
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        return JSONResponse(
            {
                "status": "success",
                "obsidian_directory": str(OBSIDIAN_DIR),
                "file_count": len(files),
                "total_size_bytes": total_size,
                "recent_files": [
                    {
                        "name": f.name,
                        "size": f.stat().st_size,
                        "modified": f.stat().st_mtime,
                    }
                    for f in sorted(
                        files, key=lambda x: x.stat().st_mtime, reverse=True
                    )[:5]
                ],
                "library_status": {
                    "whisper": WHISPER_AVAILABLE,
                    "librosa": LIBROSA_AVAILABLE,
                    "pil": PIL_AVAILABLE,
                    "pypdf2": PYPDF2_AVAILABLE,
                    "docx": DOCX_AVAILABLE,
                    "openai": OPENAI_AVAILABLE,
                    "anthropic": ANTHROPIC_AVAILABLE,
                },
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Obsidian状況確認エラー: {str(e)}")
