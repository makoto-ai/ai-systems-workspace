#!/usr/bin/env python3
"""
MCP専用サービス
Multi-Component Platform の独立サービス
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

# MCP関連のインポート
from youtube_script_generation_system import YouTubeScriptGenerator
from system_monitor import SystemMonitor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# アプリケーション状態管理
class MCPAppState:
    def __init__(self):
        self.mcp_generator: Optional[YouTubeScriptGenerator] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.is_healthy = False

mcp_app_state = MCPAppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    logger.info("MCP専用サービス起動中...")
    
    # MCP初期化
    try:
        mcp_app_state.mcp_generator = YouTubeScriptGenerator()
        logger.info("MCP Generator初期化完了")
    except Exception as e:
        logger.error(f"MCP Generator初期化エラー: {e}")
    
    # システム監視初期化
    try:
        mcp_app_state.system_monitor = SystemMonitor()
        logger.info("System Monitor初期化完了")
    except Exception as e:
        logger.error(f"System Monitor初期化エラー: {e}")
    
    mcp_app_state.is_healthy = True
    logger.info("MCP専用サービス起動完了")
    
    yield
    
    # シャットダウン時
    logger.info("MCP専用サービスシャットダウン中...")
    mcp_app_state.is_healthy = False

# FastAPIアプリケーション作成
app = FastAPI(
    title="MCP専用サービス",
    description="Multi-Component Platform 専用API",
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
def get_mcp_generator() -> YouTubeScriptGenerator:
    if not mcp_app_state.mcp_generator:
        raise HTTPException(status_code=503, detail="MCP Generator not initialized")
    return mcp_app_state.mcp_generator

def get_system_monitor() -> SystemMonitor:
    if not mcp_app_state.system_monitor:
        raise HTTPException(status_code=503, detail="System Monitor not initialized")
    return mcp_app_state.system_monitor

# ヘルスチェック
@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    health_status = {
        "status": "healthy" if mcp_app_state.is_healthy else "unhealthy",
        "services": {
            "mcp_generator": mcp_app_state.mcp_generator is not None,
            "system_monitor": mcp_app_state.system_monitor is not None
        },
        "timestamp": asyncio.get_event_loop().time()
    }
    
    if not mcp_app_state.is_healthy:
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

# メトリクスエンドポイント
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheusメトリクスエンドポイント"""
    if mcp_app_state.system_monitor:
        return mcp_app_state.system_monitor.get_system_metrics()
    return {"error": "System monitor not available"}

# MCP API
@app.post("/generate")
async def generate_script(
    request_data: Dict[str, Any],
    mcp_generator: YouTubeScriptGenerator = Depends(get_mcp_generator)
):
    """MCPスクリプト生成"""
    try:
        result = await mcp_generator.generate_script(request_data)
        
        return {
            "success": True,
            "script": result,
            "method": "mcp",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"MCP script generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# MCP設定取得
@app.get("/config")
async def get_mcp_config():
    """MCP設定取得"""
    try:
        with open("mcp_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"MCP config error: {e}")
        raise HTTPException(status_code=500, detail="Config not available")

# MCPサーバー状態
@app.get("/servers")
async def get_mcp_servers():
    """MCPサーバー一覧取得"""
    try:
        with open("mcp_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        servers = []
        for server_name, server_config in config.get("servers", {}).items():
            servers.append({
                "name": server_name,
                "description": server_config.get("description", ""),
                "commands": list(server_config.get("commands", {}).keys())
            })
        
        return {
            "servers": servers,
            "total": len(servers)
        }
    except Exception as e:
        logger.error(f"MCP servers error: {e}")
        raise HTTPException(status_code=500, detail="Servers not available")

# システム状態
@app.get("/system/status")
async def system_status(
    system_monitor: SystemMonitor = Depends(get_system_monitor)
):
    """システム状態取得"""
    try:
        metrics = system_monitor.get_system_metrics()
        
        return {
            "system_metrics": metrics,
            "services": {
                "mcp_generator": mcp_app_state.mcp_generator is not None,
                "system_monitor": mcp_app_state.system_monitor is not None
            },
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# MCPテスト
@app.post("/test")
async def test_mcp_connection():
    """MCP接続テスト"""
    try:
        # 基本的なテスト
        test_data = {
            "title": "MCP接続テスト",
            "content": "これはMCPサービスの接続テストです。",
            "style": "test"
        }
        
        if mcp_app_state.mcp_generator:
            result = await mcp_app_state.mcp_generator.generate_script(test_data)
            return {
                "success": True,
                "message": "MCP接続テスト成功",
                "result_length": len(result) if result else 0
            }
        else:
            return {
                "success": False,
                "message": "MCP Generator not available"
            }
    except Exception as e:
        logger.error(f"MCP test error: {e}")
        return {
            "success": False,
            "message": f"MCP接続テスト失敗: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(
        "mcp_service:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 