#!/usr/bin/env python3
"""
Composer専用サービス
論文検証＆原稿生成Composerの独立サービス
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

# Composer関連のインポート
from modules.composer import ScriptComposer, ComposerError
from modules.prompt_generator import PaperMetadata
from system_monitor import SystemMonitor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# アプリケーション状態管理
class ComposerAppState:
    def __init__(self):
        self.composer: Optional[ScriptComposer] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.is_healthy = False

composer_app_state = ComposerAppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    logger.info("Composer専用サービス起動中...")
    
    # Composer初期化
    try:
        composer_app_state.composer = ScriptComposer()
        logger.info("Composer初期化完了")
    except Exception as e:
        logger.error(f"Composer初期化エラー: {e}")
    
    # システム監視初期化
    try:
        composer_app_state.system_monitor = SystemMonitor()
        logger.info("System Monitor初期化完了")
    except Exception as e:
        logger.error(f"System Monitor初期化エラー: {e}")
    
    composer_app_state.is_healthy = True
    logger.info("Composer専用サービス起動完了")
    
    yield
    
    # シャットダウン時
    logger.info("Composer専用サービスシャットダウン中...")
    composer_app_state.is_healthy = False

# FastAPIアプリケーション作成
app = FastAPI(
    title="Composer専用サービス",
    description="論文検証＆原稿生成Composer専用API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依存関係
def get_composer() -> ScriptComposer:
    if not composer_app_state.composer:
        raise HTTPException(status_code=503, detail="Composer not initialized")
    return composer_app_state.composer

def get_system_monitor() -> SystemMonitor:
    if not composer_app_state.system_monitor:
        raise HTTPException(status_code=503, detail="System Monitor not initialized")
    return composer_app_state.system_monitor

# ヘルスチェック
@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    health_status = {
        "status": "healthy" if composer_app_state.is_healthy else "unhealthy",
        "services": {
            "composer": composer_app_state.composer is not None,
            "system_monitor": composer_app_state.system_monitor is not None
        },
        "timestamp": asyncio.get_event_loop().time()
    }
    
    if not composer_app_state.is_healthy:
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

# メトリクスエンドポイント
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheusメトリクスエンドポイント"""
    if composer_app_state.system_monitor:
        return composer_app_state.system_monitor.get_system_metrics()
    return {"error": "System monitor not available"}

# Composer API
@app.post("/generate")
async def generate_script(
    metadata: Dict[str, Any],
    abstract: str,
    style: str = "popular",
    composer: ScriptComposer = Depends(get_composer)
):
    """Composerスクリプト生成"""
    try:
        paper_metadata = PaperMetadata(
            title=metadata.get("title", ""),
            authors=metadata.get("authors", []),
            abstract=metadata.get("abstract", ""),
            doi=metadata.get("doi"),
            publication_year=metadata.get("publication_year"),
            journal=metadata.get("journal"),
            citation_count=metadata.get("citation_count"),
            institutions=metadata.get("institutions"),
            keywords=metadata.get("keywords")
        )
        
        result = composer.compose_script(paper_metadata, abstract, style)
        
        return {
            "success": True,
            "script": result,
            "length": len(result),
            "style": style,
            "timestamp": asyncio.get_event_loop().time()
        }
    except ComposerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Composer script generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# JSONファイルからの生成
@app.post("/generate-from-json")
async def generate_from_json(
    metadata_file: str,
    abstract: str,
    style: str = "popular",
    composer: ScriptComposer = Depends(get_composer)
):
    """JSONファイルからのスクリプト生成"""
    try:
        result = composer.compose_from_json(metadata_file, abstract, style)
        
        return {
            "success": True,
            "script": result,
            "metadata_file": metadata_file,
            "style": style,
            "timestamp": asyncio.get_event_loop().time()
        }
    except ComposerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Composer JSON generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Composer設定取得
@app.get("/config")
async def get_composer_config():
    """Composer設定取得"""
    try:
        with open("composer_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Composer config error: {e}")
        raise HTTPException(status_code=500, detail="Config not available")

# チェーン一覧取得
@app.get("/chains")
async def get_composer_chains():
    """Composerチェーン一覧取得"""
    try:
        with open("composer_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        chains = []
        for chain in config.get("chains", []):
            chains.append({
                "name": chain.get("name", ""),
                "model": chain.get("model", ""),
                "prompt": chain.get("prompt", ""),
                "features": chain.get("features", [])
            })
        
        return {
            "chains": chains,
            "total": len(chains)
        }
    except Exception as e:
        logger.error(f"Composer chains error: {e}")
        raise HTTPException(status_code=500, detail="Chains not available")

# ワークフロー一覧取得
@app.get("/workflows")
async def get_composer_workflows():
    """Composerワークフロー一覧取得"""
    try:
        with open("composer_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        workflows = []
        for workflow in config.get("workflows", []):
            workflows.append({
                "name": workflow.get("name", ""),
                "description": workflow.get("description", ""),
                "steps": workflow.get("steps", [])
            })
        
        return {
            "workflows": workflows,
            "total": len(workflows)
        }
    except Exception as e:
        logger.error(f"Composer workflows error: {e}")
        raise HTTPException(status_code=500, detail="Workflows not available")

# システム状態
@app.get("/system/status")
async def system_status(
    system_monitor: SystemMonitor = Depends(get_system_monitor)
):
    """システム状態取得"""
    try:
        metrics = system_monitor.get_system_metrics()
        composer_status = composer_app_state.composer.get_system_status() if composer_app_state.composer else None
        
        return {
            "system_metrics": metrics,
            "composer_status": composer_status,
            "services": {
                "composer": composer_app_state.composer is not None,
                "system_monitor": composer_app_state.system_monitor is not None
            },
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Composerテスト
@app.post("/test")
async def test_composer_connection():
    """Composer接続テスト"""
    try:
        # 基本的なテスト
        test_metadata = PaperMetadata(
            title="Composer接続テスト",
            authors=["テスト著者"],
            abstract="これはComposerサービスの接続テストです。",
            publication_year=2024
        )
        
        if composer_app_state.composer:
            result = composer_app_state.composer.compose_script(
                test_metadata, 
                "テスト要約", 
                "popular"
            )
            return {
                "success": True,
                "message": "Composer接続テスト成功",
                "result_length": len(result) if result else 0
            }
        else:
            return {
                "success": False,
                "message": "Composer not available"
            }
    except Exception as e:
        logger.error(f"Composer test error: {e}")
        return {
            "success": False,
            "message": f"Composer接続テスト失敗: {str(e)}"
        }

# メタデータ検証
@app.post("/validate-metadata")
async def validate_metadata(
    metadata: Dict[str, Any],
    composer: ScriptComposer = Depends(get_composer)
):
    """メタデータ検証"""
    try:
        paper_metadata = PaperMetadata(
            title=metadata.get("title", ""),
            authors=metadata.get("authors", []),
            abstract=metadata.get("abstract", ""),
            doi=metadata.get("doi"),
            publication_year=metadata.get("publication_year"),
            journal=metadata.get("journal"),
            citation_count=metadata.get("citation_count"),
            institutions=metadata.get("institutions"),
            keywords=metadata.get("keywords")
        )
        
        validation_result = composer.validate_metadata(paper_metadata)
        
        return {
            "success": True,
            "validation": validation_result,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Metadata validation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    uvicorn.run(
        "composer_service:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    ) 