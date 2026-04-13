"""
api/analyze.py
──────────────
FastAPI route that exposes scam_detector.py over HTTP.

Mount in your main app:
    from api.analyze import router
    app.include_router(router)

Or run standalone:
    uvicorn api.analyze:app --reload --port 8000
"""

from fastapi import APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from services.scam_detector import analyze_message

router = APIRouter(prefix="/api")


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10_000)


class AnalyzeResponse(BaseModel):
    is_scam: bool
    risk_level: str
    confidence_pct: float
    scam_type: str
    summary: str
    indicators: list[dict]   # [{ "title": str, "description": str }]
    guidance: list[str]


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    try:
        raw: dict = await analyze_message(body.message)
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analysis failed: {exc}") from exc

    return AnalyzeResponse(
        is_scam=raw["is_scam"],
        risk_level=raw["risk_level"],
        confidence_pct=raw["confidence_percentage"],
        scam_type=raw["scam_type"],
        summary=raw["summary"],
        indicators=[{"title": i, "description": ""} for i in raw["warning_indicators"]],
        guidance=raw["action_steps"],
    )


# Standalone dev server
try:
    from fastapi import FastAPI
    app = FastAPI(title="ScamSafe API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router)
except ImportError:
    pass