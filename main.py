"""
main.py — ScamSafe Backend API
──────────────────────────────
Run with:
    uvicorn main:app --reload --port 8000

If your frontend dev server is on a different port, configure a proxy so that
requests to /api/* are forwarded here, OR set the VITE_API_URL / NEXT_PUBLIC_API_URL
env var in your frontend to http://localhost:8000 and update the API_BASE constant
in the frontend service files accordingly.

Required environment variables (put in a .env file):
    GROQ_API_KEY
    UPSTASH_VECTOR_REST_URL
    UPSTASH_VECTOR_REST_TOKEN
    DATABASE_URL  (Neon psql connection string)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.scam_detector import analyze_message
from services.scam_sim import create_session, send_message, quit_session
from services.quiz_service import get_quizzes, get_questions
from services.notification_service import get_random_notification, get_notification_by_id

app = FastAPI(title="ScamSafe API")

# ── CORS ───────────────────────────────────────────────────────────────────────
# Allow all origins for local development. Tighten in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# 1. Scam Detection
# ──────────────────────────────────────────────────────────────────────────────

class DetectRequest(BaseModel):
    text:     str
    language: str = "en"


@app.post("/api/detect")
async def detect(req: DetectRequest):
    """
    Analyze a message for scam patterns using the Groq LLM.

    Request body:  { text: string, language?: string }
    Response:      { is_scam, risk_level, confidence_percentage,
                     scam_type, summary, warning_indicators, action_steps }
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    try:
        result = await analyze_message(req.text)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ──────────────────────────────────────────────────────────────────────────────
# 2. Scam Simulation
# ──────────────────────────────────────────────────────────────────────────────

class StartRequest(BaseModel):
    scenario_type: str  # e.g. "romance-scams"


class MessageRequest(BaseModel):
    session_id: str
    message:    str


class QuitRequest(BaseModel):
    session_id: str


@app.post("/api/simulate/start")
async def simulate_start(req: StartRequest):
    """
    Start a new simulation session for the given scenario slug.

    Request body:  { scenario_type: string }
    Response:      { session_id: string, initial_message: string }
    """
    try:
        return await create_session(req.scenario_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/simulate/message")
async def simulate_message(req: MessageRequest):
    """
    Send a user message and receive the bot's reply (or scam-fell feedback).

    Request body:  { session_id: string, message: string }
    Response:      { bot_reply: string, fell_for_scam: bool, feedback: string | null }
    """
    try:
        return await send_message(req.session_id, req.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/simulate/quit")
async def simulate_quit(req: QuitRequest):
    """
    End a session early (user successfully avoided the scam).

    Request body:  { session_id: string }
    Response:      { feedback: string }
    """
    try:
        return await quit_session(req.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ──────────────────────────────────────────────────────────────────────────────
# 3. Study Center Quiz
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/quiz/topics")
async def quiz_topics():
    """
    Return the list of published quiz topics (English only).

    Response: [{ slug, topic, title, description }]
    """
    try:
        return await get_quizzes()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/quiz/{quiz_slug}/questions")
async def quiz_questions(quiz_slug: str, count: int = 6):
    """
    Return `count` random questions for a given quiz slug.
    Use slug "mixed" to get a cross-topic selection.

    Response: [{ id, topic, prompt, questionExplanation, options,
                 correctOptionId, explanation, choiceExplanations }]
    """
    try:
        return await get_questions(quiz_slug, count)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ──────────────────────────────────────────────────────────────────────────────
# 4. Notification Challenge
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/api/notifications/random")
async def notification_random():
    """
    Fetch one random notification to display to the user.
    The label (scam / not_scam) is intentionally withheld so the
    user cannot inspect it before deciding to open or dismiss.

    Response: { id: int, message: string }
    """
    try:
        return await get_random_notification()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/notifications/{notification_id}")
async def notification_reveal(notification_id: int):
    """
    Reveal the verdict for a notification after the user clicks 'Open'.

    Path param:  notification_id — the id returned by /api/notifications/random
    Response:    { id: int, message: string, label: string, is_scam: bool }
    """
    try:
        return await get_notification_by_id(notification_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except EnvironmentError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc