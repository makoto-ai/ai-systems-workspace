#!/usr/bin/env python3
from __future__ import annotations
"""
AI Systems Hybrid メインアプリケーション
MCPとComposerの統合システム
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, APIRouter, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
import httpx
from fastapi.websockets import WebSocket, WebSocketDisconnect

# オプショナルインポート
try:
    from opentelemetry import trace, metrics  # type: ignore
    from opentelemetry.sdk.trace import TracerProvider  # type: ignore
    from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
    from opentelemetry.sdk.metrics import MeterProvider  # type: ignore
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader  # type: ignore
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter  # type: ignore
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
    from opentelemetry.instrumentation.requests import RequestsInstrumentor  # type: ignore
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    # オプショナル機能なので警告は不要

# ローカルインポート
try:
    from modules.composer import ScriptComposer, ComposerError
    from modules.prompt_generator import PaperMetadata
    COMPOSER_AVAILABLE = True
except ImportError:
    COMPOSER_AVAILABLE = False
    logging.warning("Composer module not available")

try:
    from youtube_script_generation_system import YouTubeScriptGenerator
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP module not available")

try:
    from system_monitor import get_system_monitor, SystemMonitor
    MONITOR_AVAILABLE = True
except ImportError:
    MONITOR_AVAILABLE = False
    logging.warning("System monitor not available")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional Voice API / Service (for local VOICEVOX integration)
try:
    from app.api import voice as voice_api  # type: ignore
except Exception:
    voice_api = None
    logger.warning("voice API router not available")

try:
    from app.services.voice_service import VoiceService  # type: ignore
    VOICE_AVAILABLE = True
except Exception:
    VOICE_AVAILABLE = False
    VoiceService = None  # type: ignore
    logger.warning("VoiceService not available")

# アプリケーション状態管理
class AppState:
    def __init__(self):
        self.composer: Optional[ScriptComposer] = None
        self.mcp_generator: Optional[YouTubeScriptGenerator] = None
        self.system_monitor: Optional["SystemMonitor"] = None
        self.voice_service: Optional["VoiceService"] = None
        self.is_healthy = False

app_state = AppState()

def setup_telemetry():
    """OpenTelemetry設定"""
    if not OTEL_AVAILABLE:
        logger.info("OpenTelemetry not available - skipping telemetry setup")
        return
    
    try:
        # トレース設定
        trace.set_tracer_provider(TracerProvider())
        trace.get_tracer_provider().add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
        )
        
        # メトリクス設定
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint="http://otel-collector:4317")
        )
        metrics.set_meter_provider(MeterProvider(metric_readers=[metric_reader]))
        
        logger.info("OpenTelemetry設定完了")
    except Exception as e:
        logger.error(f"OpenTelemetry設定エラー: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時
    logger.info("AI Systems Hybrid 起動中...")
    
    # OpenTelemetry設定
    setup_telemetry()
    
    # Composer初期化
    if COMPOSER_AVAILABLE:
        try:
            app_state.composer = ScriptComposer()
            logger.info("Composer初期化完了")
        except Exception as e:
            logger.error(f"Composer初期化エラー: {e}")
    
    # MCP Generator初期化
    if MCP_AVAILABLE:
        try:
            app_state.mcp_generator = YouTubeScriptGenerator()
            logger.info("MCP Generator初期化完了")
        except Exception as e:
            logger.error(f"MCP Generator初期化エラー: {e}")
    
    # システム監視初期化
    if MONITOR_AVAILABLE:
        try:
            from system_monitor import get_system_monitor as get_monitor
            app_state.system_monitor = get_monitor()
            # 監視を開始
            if app_state.system_monitor:
                try:
                    app_state.system_monitor.start_monitoring()
                    logger.info("System Monitor初期化完了")
                except Exception as e:
                    logger.error(f"System Monitor監視開始エラー: {e}")
                    app_state.system_monitor = None
            else:
                logger.warning("System MonitorインスタンスがNoneです")
        except Exception as e:
            logger.error(f"System Monitor初期化エラー: {e}")
            app_state.system_monitor = None
    
    # VoiceService 初期化（存在する場合のみ）
    if VOICE_AVAILABLE and VoiceService is not None:
        try:
            vs = VoiceService()
            app_state.voice_service = vs
            app.state.voice_service = vs  # voice.router互換
            logger.info("Voice service initialized for hybrid app")
        except Exception as e:
            logger.warning(f"Voice service init failed: {e}")
            app_state.voice_service = None
    
    # Vault接続テスト（オプショナル）
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://vault:8200/v1/sys/health", timeout=5.0)
            if response.status_code == 200:
                logger.info("Vault接続成功")
            else:
                logger.info("Vault接続失敗 - オプショナル機能")
    except Exception as e:
        logger.info(f"Vault接続エラー - オプショナル機能: {e}")
    
    app_state.is_healthy = True
    logger.info("AI Systems Hybrid 起動完了")
    
    yield
    
    # シャットダウン時
    logger.info("AI Systems Hybrid シャットダウン中...")
    app_state.is_healthy = False

# FastAPIアプリケーション作成
app = FastAPI(
    title="AI Systems Hybrid",
    description="MCPとComposerの統合AIシステム",
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

# OpenTelemetry計装（利用可能な場合）
if OTEL_AVAILABLE:
    try:
        FastAPIInstrumentor.instrument_app(app)
        RequestsInstrumentor().instrument()
        logger.info("OpenTelemetry計装完了")
    except Exception as e:
        logger.error(f"OpenTelemetry計装エラー: {e}")

# 依存関係
def get_composer() -> Optional[ScriptComposer]:
    if not app_state.composer:
        raise HTTPException(status_code=503, detail="Composer not initialized")
    return app_state.composer

def get_mcp_generator() -> Optional[YouTubeScriptGenerator]:
    if not app_state.mcp_generator:
        raise HTTPException(status_code=503, detail="MCP Generator not initialized")
    return app_state.mcp_generator

def get_system_monitor() -> Optional["SystemMonitor"]:
    """システムモニター取得"""
    if not MONITOR_AVAILABLE:
        return None
    try:
        from system_monitor import get_system_monitor as get_monitor
        monitor = get_monitor()
        if monitor is None:
            logger.warning("System monitor instance is None")
        return monitor
    except Exception as e:
        logger.error(f"System monitor取得エラー: {e}")
        return None

# ヘルスチェック
@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    health_status = {
        "status": "healthy",
        "services": {
            "composer": app_state.composer is not None,
            "mcp_generator": app_state.mcp_generator is not None,
            "system_monitor": app_state.system_monitor is not None
        },
        "modules": {
            "composer_available": COMPOSER_AVAILABLE,
            "mcp_available": MCP_AVAILABLE,
            "monitor_available": MONITOR_AVAILABLE,
            "otel_available": OTEL_AVAILABLE
        },
        "timestamp": asyncio.get_event_loop().time()
    }
    
    return health_status

# メトリクスエンドポイント（Prometheus互換）
@app.get("/metrics")
async def metrics_endpoint():
    """Prometheusメトリクスエンドポイント"""
    if app_state.system_monitor:
        return app_state.system_monitor.get_prometheus_metrics()
    return JSONResponse(status_code=503, content={"error": "System monitor not available"})

# Voice API を /api に統合（存在時）
if voice_api is not None:
    try:
        app.include_router(voice_api.router, prefix="/api")
        logger.info("voice API router mounted at /api")
    except Exception as e:
        logger.error(f"Mount voice router failed: {e}")

# Minimal TTS router (fallback)
class TTSReq(BaseModel):
    text: str = Field(..., min_length=1)
    speaker_id: int = Field(...)

tts_router = APIRouter(prefix="/api/tts", tags=["tts"])

@tts_router.get("/speakers")
async def tts_speakers():
    if app_state.voice_service is None:
        return {"speakers": [], "status": "unavailable"}
    try:
        return await app_state.voice_service.get_speakers()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@tts_router.post("/text-to-speech")
async def tts_synthesize(req: TTSReq):
    if app_state.voice_service is None:
        raise HTTPException(status_code=503, detail="Voice service not available")
    try:
        wav = await app_state.voice_service.synthesize_voice(text=req.text, speaker_id=req.speaker_id)
        if not wav:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
        return Response(content=wav, media_type="audio/wav")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

app.include_router(tts_router)

# Composer API
@app.post("/composer/generate")
async def generate_composer_script(
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
            "method": "composer",
            "timestamp": asyncio.get_event_loop().time()
        }
    except ComposerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Composer script generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# MCP API
@app.post("/mcp/generate")
async def generate_mcp_script(
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

# ハイブリッド API
@app.post("/hybrid/generate")
async def generate_hybrid_script(
    metadata: Dict[str, Any],
    abstract: str,
    style: str = "popular"
):
    """ハイブリッドスクリプト生成（Composer + MCP）"""
    try:
        results = {}
        
        # Composer生成
        if app_state.composer:
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
                
                composer_result = app_state.composer.compose_script(paper_metadata, abstract, style)
                results["composer"] = composer_result
            except Exception as e:
                logger.error(f"Composer generation error: {e}")
                results["composer"] = {"error": str(e)}
        
        # MCP生成
        if app_state.mcp_generator:
            try:
                mcp_data = {"title": metadata.get("title", ""), "content": abstract, "style": style}
                mcp_result = await app_state.mcp_generator.generate_script(mcp_data)
                results["mcp"] = mcp_result
            except Exception as e:
                logger.error(f"MCP generation error: {e}")
                results["mcp"] = {"error": str(e)}
        
        return {
            "success": True,
            "results": results,
            "method": "hybrid",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Hybrid script generation error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# システム状態
@app.get("/system/status")
async def system_status(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """システム状態取得"""
    try:
        if system_monitor is None:
            return {
                "system_metrics": {"error": "System monitor not available"},
                "services": {
                    "composer": app_state.composer is not None,
                    "mcp_generator": app_state.mcp_generator is not None,
                    "system_monitor": app_state.system_monitor is not None
                },
                "timestamp": asyncio.get_event_loop().time()
            }
        
        metrics = system_monitor.get_system_metrics()
        
        return {
            "system_metrics": metrics,
            "services": {
                "composer": app_state.composer is not None,
                "mcp_generator": app_state.mcp_generator is not None,
                "system_monitor": app_state.system_monitor is not None
            },
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"System status error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 健全性サマリー
@app.get("/system/health")
async def system_health(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """システム健全性サマリー取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        health_summary = system_monitor.get_health_summary()
        return health_summary
    except Exception as e:
        logger.error(f"System health error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# パフォーマンス分析
@app.get("/system/performance")
async def system_performance(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """パフォーマンス分析取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        performance_analysis = system_monitor.get_performance_analysis()
        return performance_analysis
    except Exception as e:
        logger.error(f"System performance error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 健全性トレンド
@app.get("/system/health/trends")
async def system_health_trends(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """健全性トレンド取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        health_trends = system_monitor.get_health_trends()
        return health_trends
    except Exception as e:
        logger.error(f"System health trends error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# システム推奨事項
@app.get("/system/recommendations")
async def system_recommendations(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """システム推奨事項取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        recommendations = system_monitor.get_system_recommendations()
        return {
            "recommendations": recommendations,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"System recommendations error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# アラート履歴
@app.get("/system/alerts")
async def system_alerts(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """アラート履歴取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        alert_history = system_monitor.get_alert_history()
        return {
            "alerts": alert_history,
            "total_alerts": len(alert_history),
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"System alerts error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 監視設定
@app.get("/system/monitoring/config")
async def get_monitoring_config(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """監視設定取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        return {
            "alert_thresholds": system_monitor.alert_thresholds,
            "monitoring_config": system_monitor.monitoring_config,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Monitoring config error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 包括的システムレポート
@app.get("/system/report")
async def system_report(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """包括的システムレポート取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        # 各種データを収集
        health_summary = system_monitor.get_health_summary()
        performance_analysis = system_monitor.get_performance_analysis()
        health_trends = system_monitor.get_health_trends()
        recommendations = system_monitor.get_system_recommendations()
        alert_history = system_monitor.get_alert_history()
        
        # レポートを構築
        report = {
            "summary": {
                "status": health_summary.get('status', 'unknown'),
                "overall_score": health_summary.get('overall_score', 0),
                "timestamp": asyncio.get_event_loop().time()
            },
            "health": health_summary,
            "performance": performance_analysis,
            "trends": health_trends,
            "recommendations": recommendations,
            "alerts": {
                "recent_alerts": alert_history[-10:] if alert_history else [],  # 最新10件
                "total_alerts": len(alert_history),
                "critical_alerts": len([a for a in alert_history if a.get('severity') == 'critical']),
                "warning_alerts": len([a for a in alert_history if a.get('severity') == 'warning'])
            },
            "services": {
                "composer": app_state.composer is not None,
                "mcp_generator": app_state.mcp_generator is not None,
                "system_monitor": app_state.system_monitor is not None
            }
        }
        
        return report
    except Exception as e:
        logger.error(f"System report error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 監視ダッシュボード
@app.get("/dashboard", response_class=HTMLResponse)
async def monitoring_dashboard(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """監視ダッシュボード表示"""
    try:
        if system_monitor is None:
            return HTMLResponse(content="<h1>System monitor not available</h1>")
        
        return HTMLResponse(content=system_monitor.get_dashboard_html())
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return HTMLResponse(content=f"<h1>Dashboard error: {e}</h1>")

# WebSocket監視エンドポイント
@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket監視エンドポイント"""
    try:
        if app_state.system_monitor is None:
            await websocket.close(code=1000, reason="System monitor not available")
            return
        
        # WebSocket接続を追加
        await app_state.system_monitor.connect_websocket(websocket)
        
        # リアルタイム監視を開始
        app_state.system_monitor.start_real_time_monitoring()
        
        try:
            # 接続を維持
            while True:
                # クライアントからのメッセージを待機
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # メッセージタイプに応じて処理
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    }))
                elif message.get('type') == 'get_status':
                    health_summary = app_state.system_monitor.get_health_summary()
                    await websocket.send_text(json.dumps({
                        'type': 'status_update',
                        'data': health_summary
                    }))
                
        except WebSocketDisconnect:
            logger.info("WebSocket接続が切断されました")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # WebSocket接続を削除
            await app_state.system_monitor.disconnect_websocket(websocket)
            # リアルタイム監視を停止
            app_state.system_monitor.stop_real_time_monitoring()
            
    except Exception as e:
        logger.error(f"WebSocket monitor error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass

# 監視イベント取得
@app.get("/system/events")
async def system_events(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """監視イベント取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        events = system_monitor.get_monitoring_events()
        return events
    except Exception as e:
        logger.error(f"System events error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# リアルタイム監視制御
@app.post("/system/monitoring/start")
async def start_real_time_monitoring(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """リアルタイム監視開始"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        system_monitor.start_real_time_monitoring()
        return {"status": "success", "message": "Real-time monitoring started"}
    except Exception as e:
        logger.error(f"Start monitoring error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/system/monitoring/stop")
async def stop_real_time_monitoring(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """リアルタイム監視停止"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        system_monitor.stop_real_time_monitoring()
        return {"status": "success", "message": "Real-time monitoring stopped"}
    except Exception as e:
        logger.error(f"Stop monitoring error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 予測分析
@app.get("/system/predictive")
async def predictive_analysis(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """予測分析取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        predictive_data = system_monitor.get_predictive_analysis()
        return predictive_data
    except Exception as e:
        logger.error(f"Predictive analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# セキュリティ監査
@app.get("/system/security/audit")
async def security_audit(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """セキュリティ監査実行"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        audit_results = system_monitor.get_security_audit()
        return audit_results
    except Exception as e:
        logger.error(f"Security audit error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 自動修復提案
@app.get("/system/recovery/suggestions")
async def auto_recovery_suggestions(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """自動修復提案取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        suggestions = system_monitor.get_auto_recovery_suggestions()
        return {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "high_priority": len([s for s in suggestions if s.get('priority') == 'high']),
            "automated": len([s for s in suggestions if s.get('automated') == True]),
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Auto recovery suggestions error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 包括的システム分析
@app.get("/system/analysis/comprehensive")
async def comprehensive_analysis(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """包括的システム分析"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        # 各種分析データを収集
        health_summary = system_monitor.get_health_summary()
        performance_analysis = system_monitor.get_performance_analysis()
        predictive_analysis = system_monitor.get_predictive_analysis()
        security_audit = system_monitor.get_security_audit()
        recovery_suggestions = system_monitor.get_auto_recovery_suggestions()
        monitoring_events = system_monitor.get_monitoring_events()
        
        # 総合スコアの計算
        health_score = health_summary.get('overall_score', 0)
        security_score = security_audit.get('overall_score', 0)
        performance_score = 100  # パフォーマンス分析から計算
        
        if 'error' not in performance_analysis:
            cpu_trend = performance_analysis.get('trends', {}).get('cpu', {})
            memory_trend = performance_analysis.get('trends', {}).get('memory', {})
            
            # トレンドに基づくスコア調整
            if cpu_trend.get('direction') == 'increasing' and cpu_trend.get('strength') == 'strong':
                performance_score -= 20
            if memory_trend.get('direction') == 'increasing' and memory_trend.get('strength') == 'strong':
                performance_score -= 15
        
        comprehensive_score = (health_score + security_score + performance_score) / 3
        
        # 分析結果を構築
        analysis = {
            "summary": {
                "comprehensive_score": comprehensive_score,
                "health_score": health_score,
                "security_score": security_score,
                "performance_score": performance_score,
                "timestamp": asyncio.get_event_loop().time()
            },
            "health": health_summary,
            "performance": performance_analysis,
            "predictive": predictive_analysis,
            "security": security_audit,
            "recovery": {
                "suggestions": recovery_suggestions,
                "total_suggestions": len(recovery_suggestions),
                "high_priority": len([s for s in recovery_suggestions if s.get('priority') == 'high']),
                "automated": len([s for s in recovery_suggestions if s.get('automated') == True])
            },
            "events": monitoring_events,
            "recommendations": {
                "immediate": [],
                "short_term": [],
                "long_term": []
            }
        }
        
        # 推奨事項の分類
        if comprehensive_score < 70:
            analysis["recommendations"]["immediate"].append("システム全体の最適化が緊急に必要です")
        elif comprehensive_score < 85:
            analysis["recommendations"]["short_term"].append("システムの改善を検討してください")
        else:
            analysis["recommendations"]["long_term"].append("継続的な監視を維持してください")
        
        # セキュリティ推奨事項
        if security_score < 80:
            analysis["recommendations"]["immediate"].append("セキュリティ設定の見直しが必要です")
        
        # パフォーマンス推奨事項
        if performance_score < 80:
            analysis["recommendations"]["short_term"].append("パフォーマンス最適化を検討してください")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# システム最適化提案
@app.get("/system/optimization/proposals")
async def system_optimization_proposals(
    system_monitor: "SystemMonitor" = Depends(get_system_monitor)
):
    """システム最適化提案取得"""
    try:
        if system_monitor is None:
            return {"error": "System monitor not available"}
        
        # 各種分析から最適化提案を生成
        health_summary = system_monitor.get_health_summary()
        performance_analysis = system_monitor.get_performance_analysis()
        predictive_analysis = system_monitor.get_predictive_analysis()
        
        proposals = []
        
        # パフォーマンス最適化提案
        if 'error' not in performance_analysis:
            cpu_trend = performance_analysis.get('trends', {}).get('cpu', {})
            memory_trend = performance_analysis.get('trends', {}).get('memory', {})
            
            if cpu_trend.get('direction') == 'increasing':
                proposals.append({
                    'category': 'performance',
                    'type': 'cpu_optimization',
                    'priority': 'high' if cpu_trend.get('strength') == 'strong' else 'medium',
                    'description': 'CPU使用率が上昇傾向のため、プロセス最適化を推奨します',
                    'impact': 'high',
                    'effort': 'medium',
                    'automated': False
                })
            
            if memory_trend.get('direction') == 'increasing':
                proposals.append({
                    'category': 'performance',
                    'type': 'memory_optimization',
                    'priority': 'high' if memory_trend.get('strength') == 'strong' else 'medium',
                    'description': 'メモリ使用率が上昇傾向のため、メモリ管理の改善を推奨します',
                    'impact': 'high',
                    'effort': 'low',
                    'automated': True
                })
        
        # 予測分析からの提案
        if 'error' not in predictive_analysis:
            predictions = predictive_analysis.get('predictions', {})
            
            if predictions.get('cpu', {}).get('predicted', 0) > 90:
                proposals.append({
                    'category': 'predictive',
                    'type': 'preventive_cpu_optimization',
                    'priority': 'high',
                    'description': 'CPU使用率が90%を超えると予測されるため、事前の最適化を推奨します',
                    'impact': 'high',
                    'effort': 'medium',
                    'automated': False
                })
            
            if predictions.get('memory', {}).get('predicted', 0) > 95:
                proposals.append({
                    'category': 'predictive',
                    'type': 'preventive_memory_cleanup',
                    'priority': 'critical',
                    'description': 'メモリ使用率が95%を超えると予測されるため、緊急のクリーンアップを推奨します',
                    'impact': 'critical',
                    'effort': 'low',
                    'automated': True
                })
        
        # 健全性からの提案
        if health_summary.get('status') == 'warning':
            proposals.append({
                'category': 'health',
                'type': 'system_health_improvement',
                'priority': 'medium',
                'description': 'システム健全性が警告レベルです。全体的な最適化を推奨します',
                'impact': 'medium',
                'effort': 'high',
                'automated': False
            })
        
        return {
            "proposals": proposals,
            "total_proposals": len(proposals),
            "by_priority": {
                "critical": len([p for p in proposals if p.get('priority') == 'critical']),
                "high": len([p for p in proposals if p.get('priority') == 'high']),
                "medium": len([p for p in proposals if p.get('priority') == 'medium']),
                "low": len([p for p in proposals if p.get('priority') == 'low'])
            },
            "by_category": {
                "performance": len([p for p in proposals if p.get('category') == 'performance']),
                "predictive": len([p for p in proposals if p.get('category') == 'predictive']),
                "health": len([p for p in proposals if p.get('category') == 'health'])
            },
            "automated_count": len([p for p in proposals if p.get('automated') == True]),
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        logger.error(f"Optimization proposals error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 統合テスト
@app.post("/test/integration")
async def test_integration():
    """統合テスト"""
    test_results = {}
    
    # Composerテスト
    if app_state.composer:
        try:
            test_metadata = PaperMetadata(
                title="統合テスト",
                authors=["テスト著者"],
                abstract="これは統合テストです。",
                publication_year=2024
            )
            result = app_state.composer.compose_script(test_metadata, "テスト要約", "popular")
            test_results["composer"] = {"success": True, "length": len(result)}
        except Exception as e:
            test_results["composer"] = {"success": False, "error": str(e)}
    
    # MCPテスト
    if app_state.mcp_generator:
        try:
            test_data = {"title": "統合テスト", "content": "テスト内容", "style": "test"}
            result = await app_state.mcp_generator.generate_script(test_data)
            test_results["mcp"] = {"success": True, "length": len(result)}
        except Exception as e:
            test_results["mcp"] = {"success": False, "error": str(e)}
    
    return {
        "success": True,
        "test_results": test_results,
        "timestamp": asyncio.get_event_loop().time()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main_hybrid:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 