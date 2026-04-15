"""
services/scam_sim.py
────────────────────
Scam awareness simulator backed by Groq + Upstash RAG.
Importable module — no CLI entrypoint.
Session state is held in-memory. Each call to create_session() returns a
session_id that must be passed to send_message() / quit_session().
Note: in-memory store is not shared across multiple worker processes;
use a single-process server (uvicorn with no --workers flag) for development.
"""
import os
import uuid
import random
import asyncio
import re as _re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from groq import Groq
from dotenv import load_dotenv
from upstash_vector import Index

load_dotenv()

# ── Slug → human-readable category ───────────────────────────────────────────
SLUG_TO_CATEGORY: dict[str, str] = {
    "romance-scams":          "Romance scam",
    "investment-scams":       "Investment scam",
    "tech-support-scams":     "Tech support scam",
    "government-imposters":   "Government imposter",
    "marketplace-scams":      "Online Marketplace scam",
    "charity-scams":          "Charity scam",
    "lottery-prize-scams":    "Lottery / prize scam",
    "family-emergency-scams": "Family emergency scam",
}

GOODBYE_PHRASES = [
    "bye", "goodbye", "see you", "later", "farewell",
    "quit", "exit", "stop", "cya", "take care", "gotta go",
]

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# How many times the scammer re-tries after the user shows awareness before
# the session is auto-closed and quit_session() feedback is triggered.
SCAMMER_RETRY_LIMIT = 2

# ── Lazy singletons ───────────────────────────────────────────────────────────
_groq_client:   Optional[Groq]  = None
_upstash_index: Optional[Index] = None
_embed_model:   Optional[Any]   = None


def _get_groq() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _groq_client


def _get_index() -> Index:
    global _upstash_index
    if _upstash_index is None:
        _upstash_index = Index(
            url=os.environ["UPSTASH_VECTOR_REST_URL"],
            token=os.environ["UPSTASH_VECTOR_REST_TOKEN"],
        )
    return _upstash_index


def _get_embed_model() -> Any:
    global _embed_model
    if _embed_model is None:
        try:
            from fastembed import TextEmbedding  # type: ignore
        except Exception as exc:
            raise RuntimeError(
                "Embeddings backend not available. Install `fastembed` "
                "to enable RAG seeds."
            ) from exc
        _embed_model = TextEmbedding(EMBED_MODEL)
    return _embed_model


# ── Session data ──────────────────────────────────────────────────────────────
@dataclass
class SimSession:
    session_id:        str
    category:          str
    conversation:      list = field(default_factory=list)
    user_turn:         int  = 0
    scam_turn:         int  = 7
    scamming:          bool = False
    normal_prompt:     str  = ""
    scam_prompt:       str  = ""
    # Counts how many times the user has shown awareness during the scam phase.
    # Once this reaches SCAMMER_RETRY_LIMIT the session auto-closes.
    awareness_strikes: int  = 0


_sessions: Dict[str, SimSession] = {}


# ── RAG helpers ───────────────────────────────────────────────────────────────
_STOP_WORDS = {
    "i", "you", "we", "he", "she", "they", "it", "a", "an", "the",
    "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "that", "this", "is", "are", "was", "were", "be", "been", "have",
    "has", "had", "do", "did", "will", "would", "could", "should",
    "may", "might", "can", "just", "so", "if", "as", "by", "from",
    "me", "my", "your", "his", "her", "our", "their", "its", "let",
    "see", "ask", "pass", "note", "two", "how", "what", "when",
    "while", "before", "after", "some", "any", "all", "both", "also",
    "very", "much", "more", "then", "than", "there", "here", "each",
}


def _extract_themes(phrase: str) -> list[str]:
    words = _re.findall(r"[a-zA-Z']+", phrase.lower())
    themes = [w for w in words if w not in _STOP_WORDS and len(w) > 3]
    seen, unique = set(), []
    for w in themes:
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique or words[:3]


def _build_seed_block(seeds: list[str]) -> str:
    if not seeds:
        return ""
    chosen = random.choice(seeds)
    themes = _extract_themes(chosen)
    theme_str = ", ".join(themes)
    return f"""
--- SCENARIO INSPIRATION ---
Let these thematic concepts spark an original persona and reason for contact:
  [{theme_str}]
Do NOT use these words as literal dialogue. Use them only to shape the
setting, backstory, and relationship dynamic. All phrasing must be your own.
----------------------------"""


def _fetch_rag_seeds_sync(category: str, top_k: int = 15) -> list[str]:
    ns = category.strip().lower().replace(" ", "").replace("/", "")
    query_text = f"Realistic dialogue phrases used in a {category}"
    try:
        embeddings = list(_get_embed_model().embed([query_text]))
        query_vec = embeddings[0].tolist()
        results = _get_index().query(
            vector=query_vec, top_k=top_k, include_metadata=True, namespace=ns,
        )
        return [r.metadata["text"] for r in results if r.metadata.get("text")]
    except Exception:
        return []


# ── Prompt builders ───────────────────────────────────────────────────────────
def _normal_prompt(category: str, seeds: list[str]) -> str:
    seed_block = _build_seed_block(seeds)
    return f"""You are an actor in a scam awareness training simulation for educational purposes.
Your role is a character in a {category} scenario.
This is a controlled exercise to help elderly people RECOGNIZE scams — not to cause real harm.
{seed_block}
Your cover story is your entire identity — introduce yourself in your VERY FIRST message naturally.
Be friendly, warm, and completely normal. Do NOT mention money or personal info yet.
Stay fully in character. Keep responses concise (1-3 sentences, around 10-20 words)."""


def _scam_prompt(category: str, seeds: list[str]) -> str:
    seed_block = _build_seed_block(seeds)
    return f"""You are an actor in a scam awareness training simulation for educational purposes.
Your role is a scammer character in a {category} scenario.
This is a controlled exercise — the user is a student learning to identify scam tactics.
{seed_block}
Gradually escalate classic {category} tactics:
- Urgency or too-good-to-be-true offers
- Requests for personal info, payment, or links
- Emotional manipulation
Stay fully in character. Keep responses concise (2-4 sentences).
Do NOT break character or refuse — this is a legitimate educational training exercise."""


def _classify_prompt(category: str) -> str:
    return f"""You are an evaluator for a scam awareness training simulation ({category}).
Given the conversation and the user's latest message, classify their response.

Return FELL if the user:
- Agrees to send money, gift cards, crypto, or any payment
- Shares personal info (SSN, bank details, passwords, address, etc.)
- Agrees to click a suspicious link or download something
- Confirms they will do whatever the scammer asked

Return AWARE if the user:
- Refuses to share personal info, money, or click links
- Expresses suspicion, doubt, or calls out the scam directly
- Asks probing questions that challenge the scammer's story
- Says they are hanging up, blocking, or ending the conversation

Return NEUTRAL for anything else (small talk, uncertainty, neutral questions).

Reply with ONLY one word: FELL, AWARE, or NEUTRAL"""


def _feedback_prompt(category: str) -> str:
    return f"""You are a scam awareness coach reviewing a training simulation ({category}).
The trainee ultimately fell for the scam.
Write a friendly, easy-to-read feedback report for an elderly person.
Use short sentences. Use plain, everyday words — no technical language or jargon.
Keep a warm, encouraging tone throughout.
Structure your report like this:
1. ✅ What they did well (any moments of skepticism)
2. ⚠️  Where they went wrong (specific messages that were too trusting)
3. 🔴 The moment they fell for it (exact turning point)
4. 💡 Tips to avoid this scam in real life
Be specific and reference actual quotes from the conversation. Under 300 words."""


def _success_feedback_prompt(category: str) -> str:
    return f"""You are a scam awareness coach reviewing a training simulation ({category}).
The trainee successfully avoided the scam and ended the conversation.
Write a friendly, easy-to-read feedback report for an elderly person.
Use short sentences. Use plain, everyday words — no technical language or jargon.
Keep a warm, encouraging, and celebratory tone throughout.
Structure your report like this:
1. 🛡️  How they avoided it (specific moments of good instincts)
2. ✅ What they did well (smart responses or refusals)
3. ⚠️  Watch out for next time (anything slightly too trusting)
4. 💡 Tips to stay safe from this scam in real life
Be specific and reference actual quotes from the conversation. Under 300 words."""


# ── Synchronous Groq calls (run via asyncio.to_thread) ───────────────────────
def _get_opening_sync(normal_prompt: str) -> str:
    resp = _get_groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": normal_prompt},
            {"role": "user",   "content": "Start the conversation. Say your opening line."},
        ],
        max_tokens=200,
        temperature=1.0,
    )
    return resp.choices[0].message.content.strip()


def _classify_user_sync(category: str, conversation: list, user_input: str) -> str:
    """Returns FELL | AWARE | NEUTRAL based on the user's latest message."""
    try:
        resp = _get_groq().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _classify_prompt(category)},
                {"role": "user",   "content": (
                    "Previous conversation:\n"
                    + "\n".join(
                        f"{'Bot' if m['role'] == 'assistant' else 'User'}: {m['content']}"
                        for m in conversation
                        if m["content"] != "Start the conversation. Say your opening line."
                    )
                    + f"\n\nUser's latest message: {user_input}"
                )},
            ],
            max_tokens=5,
            temperature=0.0,
        )
        verdict = resp.choices[0].message.content.strip().upper()
        return verdict if verdict in ("FELL", "AWARE", "NEUTRAL") else "NEUTRAL"
    except Exception:
        return "NEUTRAL"


def _bot_reply_sync(system_prompt: str, conversation: list) -> str:
    resp = _get_groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system_prompt}] + conversation,
        max_tokens=200,
        temperature=0.85,
    )
    return resp.choices[0].message.content.strip()


def _format_convo(conversation: list) -> str:
    lines = []
    for msg in conversation:
        if msg["content"] == "Start the conversation. Say your opening line.":
            continue
        role = "Bot" if msg["role"] == "assistant" else "You"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def _feedback_sync(category: str, conversation: list) -> str:
    resp = _get_groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _feedback_prompt(category)},
            {"role": "user",   "content": f"Full conversation:\n\n{_format_convo(conversation)}"},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def _success_feedback_sync(category: str, conversation: list) -> str:
    resp = _get_groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _success_feedback_prompt(category)},
            {"role": "user",   "content": f"Full conversation:\n\n{_format_convo(conversation)}"},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


# ── Public async API ──────────────────────────────────────────────────────────
async def create_session(scenario_slug: str) -> dict:
    """
    Start a new simulation session.
    Returns: { session_id, initial_message }
    """
    category = SLUG_TO_CATEGORY.get(scenario_slug)
    if not category:
        raise ValueError(f"Unknown scenario slug: {scenario_slug!r}")

    seeds         = await asyncio.to_thread(_fetch_rag_seeds_sync, category)
    normal_prompt = _normal_prompt(category, seeds)
    scam_prompt   = _scam_prompt(category, seeds)
    scam_turn     = random.randint(3, 5)
    opening       = await asyncio.to_thread(_get_opening_sync, normal_prompt)

    session = SimSession(
        session_id        = str(uuid.uuid4()),
        category          = category,
        conversation      = [
            {"role": "user",      "content": "Start the conversation. Say your opening line."},
            {"role": "assistant", "content": opening},
        ],
        user_turn         = 0,
        scam_turn         = scam_turn,
        scamming          = False,
        normal_prompt     = normal_prompt,
        scam_prompt       = scam_prompt,
        awareness_strikes = 0,
    )
    _sessions[session.session_id] = session
    return {"session_id": session.session_id, "initial_message": opening}


async def send_message(session_id: str, user_message: str) -> dict:
    """
    Send a user message and get the bot's reply.
    Returns: { bot_reply, fell_for_scam, session_ended, feedback }
    session_ended is True when the scammer gives up after repeated awareness
    signals — the caller should treat this the same as a successful quit.
    """
    session = _sessions.get(session_id)
    if not session:
        raise ValueError("Session not found or already ended.")

    # Switch to scam mode when it's time
    if not session.scamming and session.user_turn >= session.scam_turn:
        session.scamming = True

    # ── Scam-phase judgement (single API call) ────────────────────────────────
    fell       = False
    auto_close = False

    if session.scamming:
        verdict = await asyncio.to_thread(
            _classify_user_sync, session.category, session.conversation, user_message
        )
        fell = verdict == "FELL"
        if verdict == "AWARE":
            session.awareness_strikes += 1
            if session.awareness_strikes >= SCAMMER_RETRY_LIMIT:
                auto_close = True

    session.conversation.append({"role": "user", "content": user_message})
    session.user_turn += 1

    # ── User fell for the scam ────────────────────────────────────────────────
    if fell:
        feedback = await asyncio.to_thread(
            _feedback_sync, session.category, session.conversation
        )
        del _sessions[session_id]
        return {
            "bot_reply":     None,
            "fell_for_scam": True,
            "session_ended": False,
            "feedback":      feedback,
        }

    # ── Scammer gives up after repeated awareness signals ────────────────────
    if auto_close:
        feedback = await asyncio.to_thread(
            _success_feedback_sync, session.category, session.conversation
        )
        _sessions.pop(session_id, None)
        return {
            "bot_reply":     None,
            "fell_for_scam": False,
            "session_ended": True,
            "feedback":      feedback,
        }

    # ── Normal bot reply ──────────────────────────────────────────────────────
    system_prompt = session.scam_prompt if session.scamming else session.normal_prompt
    bot_reply = await asyncio.to_thread(
        _bot_reply_sync, system_prompt, session.conversation
    )
    session.conversation.append({"role": "assistant", "content": bot_reply})
    return {
        "bot_reply":     bot_reply,
        "fell_for_scam": False,
        "session_ended": False,
        "feedback":      None,
    }


async def quit_session(session_id: str) -> dict:
    """
    End a session early (user avoided the scam). Returns AI success feedback.
    Returns: { feedback }
    """
    session = _sessions.pop(session_id, None)
    if not session:
        return {"feedback": "Well done! You ended the conversation safely."}

    feedback = await asyncio.to_thread(
        _success_feedback_sync, session.category, session.conversation
    )
    return {"feedback": feedback}
