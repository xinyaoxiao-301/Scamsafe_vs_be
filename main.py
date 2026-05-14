"""
main.py — ScamSafe Backend API
──────────────────────────────
Run with:
    uvicorn main:app --reload --port 8000

Required environment variables (put in a .env file):
    GROQ_API_KEY
    UPSTASH_VECTOR_REST_URL
    UPSTASH_VECTOR_REST_TOKEN
    DATABASE_URL  (Neon psql connection string)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal

from services.scam_detector import analyze_message
from services.scam_sim import create_session, send_message, quit_session
from services.quiz_service import get_quizzes, get_questions
from services.notification_service import get_random_notification, get_notification_by_id
from services.scam_news import init_db_pool, close_db_pool, get_news_list, get_article_with_tips

app = FastAPI(title="ScamSafe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supported simulation languages
SimLanguage = Literal["en", "ms", "zh"]


# ── Epic 1: Scam Detection ───────────────────────────────────────────────────

class DetectRequest(BaseModel):
    text:     str
    language: str = "en"


@app.post("/api/detect")
async def detect(req: DetectRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        result = await analyze_message(req.text, req.language)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Epic 3: Scam Simulation ──────────────────────────────────────────────────

class StartRequest(BaseModel):
    scenario_type: str
    language:      SimLanguage = "en"


class MessageRequest(BaseModel):
    session_id: str
    message:    str


class QuitRequest(BaseModel):
    session_id: str


@app.post("/api/simulate/start")
async def simulate_start(req: StartRequest):
    try:
        return await create_session(req.scenario_type, req.language)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/simulate/message")
async def simulate_message(req: MessageRequest):
    try:
        return await send_message(req.session_id, req.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/simulate/quit")
async def simulate_quit(req: QuitRequest):
    try:
        return await quit_session(req.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Epic 2: Study Center Quiz ────────────────────────────────────────────────

@app.get("/api/quiz/topics")
async def quiz_topics(language: str = "en"):
    """
    Query param:  language — 'en' (default) | 'ms' | 'zh'
    Returns the list of published quiz topics with translated titles/descriptions.
    """
    try:
        return await get_quizzes(language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/quiz/{quiz_slug}/questions")
async def quiz_questions(quiz_slug: str, count: int = 6, language: str = "en"):
    """
    Path param:   quiz_slug — a quiz slug or "mixed"
    Query params:
        count    — number of questions to return (default 6)
        language — 'en' (default) | 'ms' | 'zh'

    Questions and choices are returned in the requested language where
    translations exist, falling back to English for untranslated rows.
    """
    try:
        return await get_questions(quiz_slug, count, language)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Epic 4: Notification Challenge ──────────────────────────────────────────

@app.get("/api/notifications/random")
async def notification_random(language: str = "en"):
    """
    Fetch one random notification to display to the user.
    The label (scam / not_scam) is intentionally withheld.

    Query param:  language — 'en' (default) | 'ms' | 'zh'
    Response:     { id: int, message: string }
    """
    try:
        return await get_random_notification(language)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/notifications/{notification_id}")
async def notification_reveal(notification_id: int, language: str = "en"):
    """
    Reveal the verdict for a notification after the user clicks 'Open'.

    Path param:   notification_id
    Query param:  language — 'en' (default) | 'ms' | 'zh'
    Response:     { id, message, label, is_scam, explanations }
    """
    try:
        return await get_notification_by_id(notification_id, language)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ── Epic 5: Scam News & Tips ─────────────────────────────────────────────────

@app.get("/api/scam/news")
async def scam_news_list(limit: int = 10, language: str = "en"):
    """
    Query params:
        limit    — max articles to return (default 10)
        language — 'en' (default) | 'ms' | 'zh'
    """
    try:
        return await get_news_list(limit, language)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/scam/news/{article_id}")
async def scam_news_detail(article_id: int, language: str = "en"):
    """
    Path param:   article_id
    Query param:  language — 'en' (default) | 'ms' | 'zh'
    """
    try:
        article = await get_article_with_tips(article_id, language)
        if article is None:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc