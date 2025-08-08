#!/usr/bin/env python3
"""
研究→YouTube原稿生成API
FastAPI + MCP統合版
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from youtube_script_generation_system import (
    YouTubeScriptGenerator, 
    ResearchMetadata, 
    YouTubeScript
)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション
app = FastAPI(
    title="研究→YouTube原稿生成API",
    description="MCP統合による最大限の事実正確性とアルゴリズム性能",
    version="3.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydanticモデル
class ResearchMetadataRequest(BaseModel):
    """研究メタデータリクエスト"""
    title: str = Field(..., description="研究タイトル")
    authors: List[str] = Field(..., description="著者リスト")
    abstract: str = Field(..., description="研究要約")
    publication_year: int = Field(..., description="発表年")
    journal: str = Field(..., description="ジャーナル名")
    doi: Optional[str] = Field(None, description="DOI")
    citation_count: int = Field(0, description="引用数")
    keywords: Optional[List[str]] = Field(None, description="キーワード")
    institutions: Optional[List[str]] = Field(None, description="研究機関")

class YouTubeScriptRequest(BaseModel):
    """YouTube原稿生成リクエスト"""
    research_data: ResearchMetadataRequest
    style: str = Field("popular", description="原稿スタイル")
    output_format: str = Field("youtube", description="出力形式")

class YouTubeScriptResponse(BaseModel):
    """YouTube原稿生成レスポンス"""
    success: bool
    script: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float
    confidence_score: Optional[float] = None
    safety_flags: Optional[List[Dict[str, str]]] = None

class BatchProcessingRequest(BaseModel):
    """バッチ処理リクエスト"""
    research_data_list: List[ResearchMetadataRequest]
    style: str = Field("popular", description="原稿スタイル")
    output_format: str = Field("youtube", description="出力形式")

class BatchProcessingResponse(BaseModel):
    """バッチ処理レスポンス"""
    success: bool
    results: List[Dict[str, Any]]
    total_processing_time: float
    success_count: int
    error_count: int

# グローバル変数
script_generator = YouTubeScriptGenerator()
processing_queue = []

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の初期化"""
    logger.info("YouTube Script Generation API starting up...")
    
    # ログディレクトリ作成
    Path("logs").mkdir(exist_ok=True)
    
    # MCPファイルの存在確認
    mcp_files = [
        ".cursor/mcp_claude_constitution.json",
        ".cursor/mcp_sparrow.json", 
        ".cursor/mcp_guardrails.json",
        ".cursor/project-rules.json"
    ]
    
    for file_path in mcp_files:
        if not Path(file_path).exists():
            logger.warning(f"MCP file not found: {file_path}")

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "研究→YouTube原稿生成API v3.0",
        "version": "3.0.0",
        "mcp_integration": True,
        "features": [
            "Anthropic's Constitutional AI",
            "Google DeepMind's Sparrow Logic", 
            "Microsoft Guardrails",
            "Model Routing System"
        ]
    }

@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mcp_files_loaded": True
    }

@app.post("/generate-script", response_model=YouTubeScriptResponse)
async def generate_youtube_script(request: YouTubeScriptRequest):
    """YouTube原稿生成エンドポイント"""
    start_time = datetime.now()
    
    try:
        # リクエストデータをResearchMetadataに変換
        research_data = ResearchMetadata(
            title=request.research_data.title,
            authors=request.research_data.authors,
            abstract=request.research_data.abstract,
            publication_year=request.research_data.publication_year,
            journal=request.research_data.journal,
            doi=request.research_data.doi,
            citation_count=request.research_data.citation_count,
            keywords=request.research_data.keywords,
            institutions=request.research_data.institutions
        )
        
        # YouTube原稿生成
        script = await script_generator.generate_script(
            research_data, 
            style=request.style
        )
        
        # 処理時間計算
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # レスポンス作成
        script_dict = {
            "title": script.title,
            "hook": script.hook,
            "introduction": script.introduction,
            "main_content": script.main_content,
            "conclusion": script.conclusion,
            "call_to_action": script.call_to_action,
            "total_duration": script.total_duration,
            "sources": script.sources,
            "confidence_score": script.confidence_score,
            "safety_flags": script.safety_flags
        }
        
        return YouTubeScriptResponse(
            success=True,
            script=script_dict,
            processing_time=processing_time,
            confidence_score=script.confidence_score,
            safety_flags=script.safety_flags
        )
        
    except Exception as e:
        logger.error(f"Script generation failed: {str(e)}")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return YouTubeScriptResponse(
            success=False,
            error=str(e),
            processing_time=processing_time
        )

@app.post("/batch-generate", response_model=BatchProcessingResponse)
async def batch_generate_scripts(request: BatchProcessingRequest):
    """バッチ処理エンドポイント"""
    start_time = datetime.now()
    results = []
    success_count = 0
    error_count = 0
    
    for i, research_data_req in enumerate(request.research_data_list):
        try:
            # リクエストデータをResearchMetadataに変換
            research_data = ResearchMetadata(
                title=research_data_req.title,
                authors=research_data_req.authors,
                abstract=research_data_req.abstract,
                publication_year=research_data_req.publication_year,
                journal=research_data_req.journal,
                doi=research_data_req.doi,
                citation_count=research_data_req.citation_count,
                keywords=research_data_req.keywords,
                institutions=research_data_req.institutions
            )
            
            # YouTube原稿生成
            script = await script_generator.generate_script(
                research_data, 
                style=request.style
            )
            
            # 結果を追加
            script_dict = {
                "index": i,
                "title": script.title,
                "hook": script.hook,
                "introduction": script.introduction,
                "main_content": script.main_content,
                "conclusion": script.conclusion,
                "call_to_action": script.call_to_action,
                "total_duration": script.total_duration,
                "sources": script.sources,
                "confidence_score": script.confidence_score,
                "safety_flags": script.safety_flags,
                "success": True
            }
            
            results.append(script_dict)
            success_count += 1
            
        except Exception as e:
            logger.error(f"Batch processing failed for index {i}: {str(e)}")
            
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
            error_count += 1
    
    total_processing_time = (datetime.now() - start_time).total_seconds()
    
    return BatchProcessingResponse(
        success=error_count == 0,
        results=results,
        total_processing_time=total_processing_time,
        success_count=success_count,
        error_count=error_count
    )

@app.get("/mcp-status")
async def get_mcp_status():
    """MCP設定状況を取得"""
    mcp_files = {
        "constitutional_ai": ".cursor/mcp_claude_constitution.json",
        "sparrow_logic": ".cursor/mcp_sparrow.json",
        "guardrails": ".cursor/mcp_guardrails.json",
        "project_rules": ".cursor/project-rules.json"
    }
    
    status = {}
    for name, file_path in mcp_files.items():
        file_exists = Path(file_path).exists()
        status[name] = {
            "exists": file_exists,
            "path": file_path
        }
        
        if file_exists:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    status[name]["valid_json"] = True
                    status[name]["size"] = len(json.dumps(content))
            except Exception as e:
                status[name]["valid_json"] = False
                status[name]["error"] = str(e)
    
    return {
        "mcp_status": status,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/logs/guardrail-violations")
async def get_guardrail_violations():
    """Guardrails違反ログを取得"""
    log_file = "logs/guardrail_violations.json"
    
    if not Path(log_file).exists():
        return {"violations": [], "message": "No violations logged"}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            violations = json.load(f)
        
        return {
            "violations": violations,
            "total_count": len(violations),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read violation log: {str(e)}")

@app.post("/validate-citations")
async def validate_citations(content: str, sources: List[Dict[str, str]]):
    """引用検証エンドポイント"""
    try:
        from youtube_script_generation_system import MCPSparrowLogic
        
        sparrow_logic = MCPSparrowLogic()
        is_valid, violations = sparrow_logic.validate_citations(content, sources)
        
        return {
            "valid": is_valid,
            "violations": violations,
            "total_violations": len(violations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Citation validation failed: {str(e)}")

@app.post("/check-safety")
async def check_content_safety(content: str):
    """コンテンツ安全性チェックエンドポイント"""
    try:
        from youtube_script_generation_system import MCPGuardrails
        
        guardrails = MCPGuardrails()
        is_safe, violations = guardrails.check_content_safety(content)
        
        return {
            "safe": is_safe,
            "violations": violations,
            "total_violations": len(violations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Safety check failed: {str(e)}")

@app.get("/styles")
async def get_available_styles():
    """利用可能なスタイルを取得"""
    return {
        "styles": [
            {
                "id": "popular",
                "name": "一般向け",
                "description": "一般視聴者向けの魅力的な原稿",
                "duration": "10-15分"
            },
            {
                "id": "academic", 
                "name": "学術的",
                "description": "学術的で正確な原稿",
                "duration": "15-20分"
            },
            {
                "id": "business",
                "name": "ビジネス向け", 
                "description": "ビジネスパーソン向けの実用的な原稿",
                "duration": "12-18分"
            },
            {
                "id": "educational",
                "name": "教育的",
                "description": "教育的で体系的な原稿", 
                "duration": "20-30分"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 