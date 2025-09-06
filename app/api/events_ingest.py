from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime

router = APIRouter(prefix="/api", tags=["events"])


class IngestTurn(BaseModel):
    tenant: str = Field(...)
    session_id: Optional[str]
    turn_id: Optional[str]
    payload: Dict[str, Any]


@router.post("/ingest/turn")
async def ingest_turn(ev: IngestTurn) -> Dict[str, Any]:
    # TODO: insert into Postgres events (append-only)
    # Placeholder returns canonical event envelope
    if not ev.payload:
        raise HTTPException(status_code=400, detail="payload required")
    return {
        "ok": True,
        "event": {
            "type": "ingest_turn",
            "tenant": ev.tenant,
            "session": ev.session_id,
            "turn": ev.turn_id,
            "ts": datetime.utcnow().isoformat() + "Z",
            "payload": ev.payload,
        },
    }


class ScoreReq(BaseModel):
    tenant: str
    session_id: Optional[str]
    turn_id: Optional[str]
    metrics: Dict[str, Any]


@router.post("/score")
async def score(req: ScoreReq) -> Dict[str, Any]:
    if not req.metrics:
        raise HTTPException(status_code=400, detail="metrics required")
    return {"ok": True, "recorded": {"type": "score", **req.model_dump()}}


class SimRunReq(BaseModel):
    tenant: str
    scenario_id: Optional[str]
    params: Dict[str, Any] = Field(default_factory=dict)


@router.post("/sim/run")
async def sim_run(req: SimRunReq) -> Dict[str, Any]:
    # Placeholder simulation result
    result = {"steps": 10, "success": True, "visited": ["A", "B", "C"]}
    return {"ok": True, "sim_run": {"scenario": req.scenario_id, "result": result}}


@router.get("/metrics/overview")
async def metrics_overview(tenant: str) -> Dict[str, Any]:
    # Placeholder: would query mv_kpi_overview
    return {
        "tenant": tenant,
        "kpi": {
            "turns": 120,
            "rebuttal_success_rate": 0.62,
            "ng_rate": 0.08,
            "silence_ratio": 0.11,
        },
    }


