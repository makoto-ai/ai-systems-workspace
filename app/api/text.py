"""
テキストアップロードAPI - Phase 10
Llama 3.1 Swallow 8Bモデルを使用したテキスト分析機能
"""

import logging
import tempfile
import os
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse

try:
    from services.swallow_text_service import (
        get_swallow_service,
        SwallowTextService,
        TextAnalysisResult,
    )
except ImportError:
    from app.services.swallow_text_service import (
        get_swallow_service,
        SwallowTextService,
        TextAnalysisResult,
    )

logger = logging.getLogger(__name__)

router = APIRouter(tags=["text"])

# サポートされているファイル形式
SUPPORTED_FORMATS = {
    # Microsoft Office Documents
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
        ".docx"
    ],
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": [
        ".pptx"
    ],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-excel": [".xls"],
    # PDF Documents
    "application/pdf": [".pdf"],
    # Plain Text & Basic Formats
    "text/plain": [".txt", ".log", ".ini", ".properties", ".sql", ".conf", ".cfg"],
    "text/csv": [".csv", ".tsv"],
    "text/markdown": [".md", ".markdown"],
    "application/json": [".json"],
    # Rich Text & Formatted Text
    "application/rtf": [".rtf"],
    "text/rtf": [".rtf"],
    "text/richtext": [".rtf"],
    # Data & Configuration Files
    "application/x-yaml": [".yaml", ".yml"],
    "text/yaml": [".yaml", ".yml"],
    "application/xml": [".xml"],
    "text/xml": [".xml"],
    # Web & Markup Files
    "text/html": [".html", ".htm"],
    "text/css": [".css"],
    "application/javascript": [".js"],
    "text/javascript": [".js"],
    # Source Code Files
    "text/x-python": [".py"],
    "application/x-python-code": [".py"],
    "text/x-java-source": [".java"],
    "text/x-c": [".c", ".h"],
    "text/x-c++": [".cpp", ".cc", ".cxx", ".hpp"],
    "text/x-csharp": [".cs"],
    "text/x-php": [".php"],
    "text/x-ruby": [".rb"],
    "text/x-go": [".go"],
    "text/x-rust": [".rs"],
    "application/typescript": [".ts"],
    "text/x-sh": [".sh", ".bash"],
    "application/x-powershell": [".ps1"],
    # Other Text Formats
    "text/tab-separated-values": [".tsv"],
    "application/x-httpd-php": [".php"],
    "application/x-sh": [".sh"],
}

# 設定値を大幅に拡張
MAX_FILE_SIZE_MB = 200  # 200MBまで（Claude Projects並み）
MAX_BATCH_FILES = 50  # 50ファイル同時処理
MAX_TEXT_LENGTH = 1000000  # 1,000,000文字まで（約500ページ）
MAX_TOTAL_SIZE_MB = 1000  # 全体で1GB制限

# 高品質処理用の設定
QUALITY_PROCESSING_ENABLED = True
INTELLIGENT_CHUNKING = True
MULTI_PASS_ANALYSIS = True
CROSS_REFERENCE_ANALYSIS = True

# メモリ効率化設定
MEMORY_EFFICIENT_MODE = True
AUTO_CLEANUP = True
TEMP_FILE_CLEANUP_INTERVAL = 3600  # 1時間ごとにクリーンアップ
MAX_MEMORY_USAGE_GB = 8  # 最大8GB使用
STREAMING_PROCESSING = True  # ストリーミング処理

# PC負荷軽減設定
MEMORY_MONITORING = True  # メモリ監視
PROGRESSIVE_PROCESSING = True  # 段階的処理
BACKGROUND_CLEANUP = True  # バックグラウンドクリーンアップ
SAFE_MODE_THRESHOLD = 85  # メモリ使用率85%で安全モード


@router.get("/text/supported-formats")
async def get_supported_formats() -> Dict[str, Any]:
    """
    サポートしているファイル形式の取得

    Returns:
        サポート形式とファイルサイズ制限の情報
    """
    return {
        "supported_formats": SUPPORTED_FORMATS,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "max_batch_files": MAX_BATCH_FILES,
        "max_text_length": MAX_TEXT_LENGTH,
    }


@router.get("/text/model-status")
async def get_model_status(
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    モデル状態の取得

    Returns:
        モデルの読み込み状況と設定情報
    """
    return {
        "model_name": service.model_name,
        "device": service.device,
        "is_loaded": service.is_model_loaded,
        "status": "loaded" if service.is_model_loaded else "unloaded",
    }


@router.post("/text/model/load")
async def load_model(
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    モデルの読み込み

    Returns:
        読み込み結果
    """
    try:
        success = await service.load_model()
        if success:
            return {
                "status": "success",
                "message": "Model loaded successfully",
                "model_name": service.model_name,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to load model")
    except Exception as e:
        logger.error(f"モデル読み込みエラー: {e}")
        raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")


@router.post("/text/model/unload")
async def unload_model(
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    モデルの解放

    Returns:
        解放結果
    """
    try:
        service.unload_model()
        return {"status": "success", "message": "Model unloaded successfully"}
    except Exception as e:
        logger.error(f"モデル解放エラー: {e}")
        raise HTTPException(status_code=500, detail=f"Model unloading failed: {str(e)}")


@router.post("/text/analyze")
async def analyze_text_content(
    text: str = Form(...),
    document_type: str = Form(default="general"),
    analysis_type: str = Form(default="comprehensive"),
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    テキスト内容の分析

    Args:
        text: 分析対象のテキスト
        document_type: ドキュメントタイプ（sales_document, product_spec等）
        analysis_type: 分析タイプ（comprehensive, faq, summary等）

    Returns:
        分析結果
    """
    try:
        # テキストの検証
        if not text or text.strip() == "":
            raise HTTPException(status_code=400, detail="Text content is empty")

        if len(text.encode("utf-8")) > MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=413,
                detail=f"Text content exceeds maximum length of {MAX_TEXT_LENGTH} bytes",
            )

        # 分析タイプに応じた処理
        if analysis_type == "faq":
            faqs = await service.generate_faq(text)
            return {
                "status": "success",
                "text_info": {
                    "length": len(text),
                    "document_type": document_type,
                    "analysis_type": analysis_type,
                },
                "faqs": faqs,
            }

        elif analysis_type == "comprehensive":
            # 包括的分析
            if document_type == "sales_document":
                result = await service.analyze_sales_document(text)
            else:
                result = await service.process_customer_document(text, document_type)

            return {
                "status": "success",
                "text_info": {
                    "length": len(text),
                    "document_type": document_type,
                    "analysis_type": analysis_type,
                },
                "analysis": {
                    "summary": result.summary,
                    "key_points": result.key_points,
                    "customer_info": result.customer_info,
                    "sales_insights": result.sales_insights,
                    "confidence": result.confidence,
                },
            }

        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported analysis type: {analysis_type}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"テキスト分析エラー: {e}")
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")


@router.post("/text/upload/analyze")
async def upload_and_analyze_file(
    file: UploadFile = File(...),
    document_type: str = Form(default="general"),
    analysis_type: str = Form(default="comprehensive"),
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    ファイルアップロードと分析（Phase 1: 大幅拡張版）

    Args:
        file: アップロードファイル（最大200MB）
        document_type: ドキュメントタイプ
        analysis_type: 分析タイプ

    Returns:
        拡張された分析結果
    """
    try:
        # ファイル形式の検証
        content_type = file.content_type
        if content_type not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {content_type}. Supported types: {list(SUPPORTED_FORMATS.keys())}",
            )

        # ファイルサイズの検証（200MBまで拡張）
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum of {MAX_FILE_SIZE_MB}MB",
            )

        logger.info(f"Processing large file: {file.filename} ({file_size_mb:.1f}MB)")

        # ファイル内容の読み取り
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # 拡張されたドキュメントプロセッサを使用
        try:
            from services.document_processor import get_document_processor
        except ImportError:
            from app.services.document_processor import get_document_processor
        document_processor = get_document_processor()

        # インテリジェントチャンク処理を使用
        if INTELLIGENT_CHUNKING and file_size_mb > 10:  # 10MB以上でチャンク処理
            logger.info("Using intelligent chunking for large file")
            processed_result = await document_processor.process_document_with_chunking(
                file_content,
                file.filename or "unknown",
                content_type,
                target_provider="groq",  # デフォルトプロバイダー
            )
        else:
            # 通常処理
            processed_result = await document_processor.process_document(
                file_content, file.filename or "unknown", content_type
            )

        # テキスト長の検証（拡張）
        extracted_text = processed_result.get("text", "")
        text_length = len(extracted_text)

        if text_length > MAX_TEXT_LENGTH:
            logger.warning(
                f"Text length ({text_length}) exceeds limit ({MAX_TEXT_LENGTH}), truncating..."
            )
            extracted_text = extracted_text[:MAX_TEXT_LENGTH]
            processed_result["text"] = extracted_text
            processed_result["truncated"] = True
            processed_result["original_length"] = text_length

        # 高品質分析の実行
        if analysis_type == "comprehensive" and QUALITY_PROCESSING_ENABLED:
            # 高品質処理モード
            analysis_result = await service.process_large_document_for_training(
                extracted_text,
                document_type=document_type,
                max_chunks=30,  # 大量チャンク対応
            )

            return {
                "status": "success",
                "processing_mode": "high_quality",
                "file_info": {
                    "filename": file.filename,
                    "size_mb": file_size_mb,
                    "content_type": content_type,
                    "document_type": processed_result.get("document_type", "unknown"),
                    "pages_estimated": processed_result.get("word_count", 0)
                    // 250,  # 250語/ページ想定
                    "processing_time": "calculated",
                },
                "document_analysis": processed_result,
                "ai_analysis": analysis_result,
                "quality_metrics": analysis_result.get("quality_metrics", {}),
                "capabilities": {
                    "chunking_used": processed_result.get("total_chunks", 0) > 1,
                    "multi_pass_analysis": MULTI_PASS_ANALYSIS,
                    "cross_reference": CROSS_REFERENCE_ANALYSIS,
                },
            }

        elif analysis_type == "faq":
            # FAQ生成
            if text_length > 50000:  # 大量テキストの場合は要約してからFAQ生成
                summary_text = extracted_text[:50000] + "..."
                faqs = await service.generate_faq(summary_text)
            else:
                faqs = await service.generate_faq(extracted_text)

            return {
                "status": "success",
                "processing_mode": "faq_generation",
                "file_info": {
                    "filename": file.filename,
                    "size_mb": file_size_mb,
                    "text_length": text_length,
                    "document_type": processed_result.get("document_type", "unknown"),
                },
                "document_analysis": processed_result,
                "faqs": faqs,
            }

        elif analysis_type == "summary":
            # 要約生成（大量テキスト対応）
            if document_type == "sales_document":
                summary_result = await service.analyze_sales_document(extracted_text)
            else:
                summary_result = await service.analyze_general_document(extracted_text)

            return {
                "status": "success",
                "processing_mode": "summary_generation",
                "file_info": {
                    "filename": file.filename,
                    "size_mb": file_size_mb,
                    "text_length": text_length,
                    "document_type": processed_result.get("document_type", "unknown"),
                },
                "document_analysis": processed_result,
                "summary": summary_result,
            }

        else:
            # 標準分析
            if document_type == "sales_document":
                analysis_result = await service.analyze_sales_document(extracted_text)
            else:
                analysis_result = await service.analyze_general_document(extracted_text)

            return {
                "status": "success",
                "processing_mode": "standard",
                "file_info": {
                    "filename": file.filename,
                    "size_mb": file_size_mb,
                    "text_length": text_length,
                    "document_type": processed_result.get("document_type", "unknown"),
                },
                "document_analysis": processed_result,
                "analysis": analysis_result,
            }

    except HTTPException:
        # HTTPExceptionは再スロー
        raise
    except Exception as e:
        logger.error(f"Large file analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/text/batch/analyze")
async def batch_analyze_files(
    files: List[UploadFile] = File(...),
    document_type: str = Form(default="general"),
    analysis_type: str = Form(default="comprehensive"),
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    バッチファイル分析（Phase 1: 50ファイル対応）

    Args:
        files: アップロードファイルリスト（最大50ファイル）
        document_type: ドキュメントタイプ
        analysis_type: 分析タイプ

    Returns:
        バッチ分析結果
    """
    try:
        # ファイル数の検証（50ファイルまで拡張）
        if len(files) > MAX_BATCH_FILES:
            raise HTTPException(
                status_code=413,
                detail=f"Too many files: {len(files)}. Maximum allowed: {MAX_BATCH_FILES}",
            )

        # 総ファイルサイズの検証
        total_size_mb = 0
        file_info_list = []

        for file in files:
            content = await file.read()
            size_mb = len(content) / (1024 * 1024)
            total_size_mb += size_mb

            file_info_list.append(
                {
                    "filename": file.filename,
                    "size_mb": size_mb,
                    "content": content,
                    "content_type": file.content_type,
                }
            )

        if total_size_mb > MAX_TOTAL_SIZE_MB:
            raise HTTPException(
                status_code=413,
                detail=f"Total size ({total_size_mb:.1f}MB) exceeds limit ({MAX_TOTAL_SIZE_MB}MB)",
            )

        logger.info(
            f"Processing batch: {len(files)} files, total {total_size_mb:.1f}MB"
        )

        # バッチ処理実行
        batch_results = []
        documents_for_training = []

        for i, file_info in enumerate(file_info_list):
            try:
                # 個別ファイル処理
                try:
                    from services.document_processor import get_document_processor
                except ImportError:
                    from app.services.document_processor import get_document_processor
                document_processor = get_document_processor()

                if file_info["size_mb"] > 10:  # 大ファイルはチャンク処理
                    processed_result = (
                        await document_processor.process_document_with_chunking(
                            file_info["content"],
                            file_info["filename"] or f"file_{i+1}",
                            file_info["content_type"],
                            target_provider="groq",
                        )
                    )
                else:
                    processed_result = await document_processor.process_document(
                        file_info["content"],
                        file_info["filename"] or f"file_{i+1}",
                        file_info["content_type"],
                    )

                # 分析結果を追加
                file_result = {
                    "file_index": i + 1,
                    "filename": file_info["filename"],
                    "size_mb": file_info["size_mb"],
                    "processing_status": "success",
                    "document_analysis": processed_result,
                }

                # 高品質処理用データを準備
                if QUALITY_PROCESSING_ENABLED and analysis_type == "comprehensive":
                    documents_for_training.append(
                        {
                            "content": processed_result.get("text", ""),
                            "type": document_type,
                            "priority": 3,  # デフォルト優先度
                            "filename": file_info["filename"],
                        }
                    )

                batch_results.append(file_result)

            except Exception as e:
                logger.error(f"File {file_info['filename']} processing failed: {e}")
                batch_results.append(
                    {
                        "file_index": i + 1,
                        "filename": file_info["filename"],
                        "size_mb": file_info["size_mb"],
                        "processing_status": "error",
                        "error": str(e),
                    }
                )

        # 高品質統合分析（有効な場合）
        integrated_analysis = None
        if documents_for_training and QUALITY_PROCESSING_ENABLED:
            try:
                integrated_analysis = await service.process_high_quality_training_data(
                    documents_for_training,
                    project_name=f"batch_analysis_{len(files)}_files",
                )
            except Exception as e:
                logger.error(f"Integrated analysis failed: {e}")

        return {
            "status": "success",
            "batch_info": {
                "total_files": len(files),
                "total_size_mb": total_size_mb,
                "successful_files": len(
                    [
                        r
                        for r in batch_results
                        if r.get("processing_status") == "success"
                    ]
                ),
                "failed_files": len(
                    [r for r in batch_results if r.get("processing_status") == "error"]
                ),
                "processing_mode": (
                    "high_quality" if integrated_analysis else "standard"
                ),
            },
            "individual_results": batch_results,
            "integrated_analysis": integrated_analysis,
            "capabilities": {
                "max_files_supported": MAX_BATCH_FILES,
                "max_total_size_mb": MAX_TOTAL_SIZE_MB,
                "intelligent_chunking": INTELLIGENT_CHUNKING,
                "quality_processing": QUALITY_PROCESSING_ENABLED,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.post("/text/google-docs/analyze")
async def analyze_google_docs(
    document_url: str = Form(...),
    analysis_type: str = Form(default="comprehensive"),
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    Google Docsドキュメントの分析

    Args:
        document_url: Google DocsのURL
        analysis_type: 分析タイプ

    Returns:
        分析結果
    """
    try:
        # Extract document ID from URL
        import re

        doc_id_match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", document_url)
        if not doc_id_match:
            raise HTTPException(status_code=400, detail="Invalid Google Docs URL")

        document_id = doc_id_match.group(1)

        # TODO: Implement Google Docs API integration
        # For now, return a placeholder response

        return {
            "status": "success",
            "message": "Google Docs integration coming soon",
            "document_id": document_id,
            "document_url": document_url,
            "analysis_type": analysis_type,
            "note": "This feature requires Google API credentials configuration",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google Docs分析エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"Google Docs analysis failed: {str(e)}"
        )


@router.post("/text/google-sheets/analyze")
async def analyze_google_sheets(
    spreadsheet_url: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    analysis_type: str = Form(default="comprehensive"),
    service: SwallowTextService = Depends(get_swallow_service),
) -> Dict[str, Any]:
    """
    Google Sheetsスプレッドシートの分析

    Args:
        spreadsheet_url: Google SheetsのURL
        sheet_name: 特定のシート名（オプション）
        analysis_type: 分析タイプ

    Returns:
        分析結果
    """
    try:
        # Extract spreadsheet ID from URL
        import re

        sheet_id_match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", spreadsheet_url)
        if not sheet_id_match:
            raise HTTPException(status_code=400, detail="Invalid Google Sheets URL")

        spreadsheet_id = sheet_id_match.group(1)

        # TODO: Implement Google Sheets API integration

        return {
            "status": "success",
            "message": "Google Sheets integration coming soon",
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": spreadsheet_url,
            "sheet_name": sheet_name,
            "analysis_type": analysis_type,
            "note": "This feature requires Google API credentials configuration",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google Sheets分析エラー: {e}")
        raise HTTPException(
            status_code=500, detail=f"Google Sheets analysis failed: {str(e)}"
        )


@router.get("/text/file-formats")
async def get_supported_file_formats() -> Dict[str, Any]:
    """
    拡張されたサポートファイル形式の一覧

    Returns:
        サポートされている全ファイル形式の詳細情報
    """
    return {
        "office_documents": {
            "word": [".docx"],
            "excel": [".xlsx", ".xls"],
            "powerpoint": [".pptx"],
            "description": "Microsoft Office documents with full text extraction",
        },
        "pdf_documents": {
            "formats": [".pdf"],
            "description": "PDF documents with advanced text extraction",
        },
        "text_formats": {
            "plain_text": [".txt", ".log"],
            "markup": [".md", ".markdown", ".html", ".htm"],
            "data": [".csv", ".tsv", ".json"],
            "config": [".yaml", ".yml", ".xml", ".ini", ".properties"],
            "rich_text": [".rtf"],
            "description": "Various text and configuration file formats",
        },
        "source_code": {
            "languages": [
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".cs",
                ".php",
                ".rb",
                ".go",
                ".rs",
            ],
            "scripts": [".sh", ".sql", ".css"],
            "description": "Source code files and scripts",
        },
        "google_workspace": {
            "docs": "Google Docs (via URL)",
            "sheets": "Google Sheets (via URL)",
            "slides": "Google Slides (coming soon)",
            "description": "Google Workspace documents via API integration",
        },
        "limits": {
            "max_file_size_mb": MAX_FILE_SIZE_MB,
            "max_batch_files": MAX_BATCH_FILES,
            "max_text_length": MAX_TEXT_LENGTH,
        },
        "features": {
            "encoding_detection": "Automatic character encoding detection",
            "batch_processing": f"Process up to {MAX_BATCH_FILES} files simultaneously",
            "text_extraction": "Advanced text extraction from complex formats",
            "metadata_extraction": "File metadata and structure analysis",
        },
    }
