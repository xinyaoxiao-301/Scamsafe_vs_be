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
    "marketplace-scams":      "Marketplace scam",
    "charity-scams":          "Charity scam",
    "lottery-prize-scams":    "Lottery / prize scam",
    "family-emergency-scams": "Family emergency scam",
}

GOODBYE_PHRASES = [
    "bye", "goodbye", "see you", "later", "farewell",
    "quit", "exit", "stop", "cya", "take care", "gotta go",
]

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ── Lazy singletons ───────────────────────────────────────────────────────────
_groq_client:    Optional[Groq]                = None
_upstash_index:  Optional[Index]              = None
_embed_model:    Optional[Any] = None


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
    session_id:    str
    category:      str
    conversation:  list = field(default_factory=list)
    user_turn:     int  = 0
    scam_turn:     int  = 7
    scamming:      bool = False
    normal_prompt: str  = ""
    scam_prompt:   str  = ""


_sessions: Dict[str, SimSession] = {}


# ── RAG helpers (same logic as original scam_sim.py) ─────────────────────────
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


def _judge_prompt(category: str) -> str:
    return f"""You are an evaluator for a scam awareness training simulation ({category}).
Given the user's latest message, decide if they have "fallen for the scam."
A user HAS fallen for the scam if they:
- Agree to send money, gift cards, crypto, or any payment
- Share personal info (SSN, bank details, passwords, address, etc.)
- Agree to click a suspicious link or download something
- Confirm they will do whatever the scammer asked
A user has NOT fallen if they ask questions, express skepticism, refuse, or just make small talk.
Reply with ONLY one word: FELL or SAFE"""


def _feedback_prompt(category: str) -> str:
    return f"""You are a scam awareness coach reviewing a training simulation ({category}).
The trainee ultimately fell for the scam.
Write a structured feedback report:
1. ✅ What they did well (any moments of skepticism)
2. ⚠️  Where they went wrong (specific messages that were too trusting)
3. 🔴 The moment they fell for it (exact turning point)
4. 💡 Tips to avoid this scam in real life
Be specific, reference actual quotes, and keep the tone encouraging but honest. Under 300 words."""


def _success_feedback_prompt(category: str) -> str:
    return f"""You are a scam awareness coach reviewing a training simulation ({category}).
The trainee successfully avoided the scam and ended the conversation.
Write an encouraging feedback report:
1. 🛡️  How they avoided it (specific moments of good instincts)
2. ✅ What they did well (smart responses or refusals)
3. ⚠️  Watch out for next time (anything slightly too trusting)
4. 💡 Tips to stay safe from this scam in real life
Be specific, reference actual quotes, keep the tone warm and encouraging. Under 300 words."""


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


def _check_fell_sync(category: str, conversation: list, user_input: str) -> bool:
    try:
        resp = _get_groq().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _judge_prompt(category)},
                {"role": "user",   "content": (
                    f"Previous conversation:\n"
                    + "\n".join(
                        f"{'Bot' if m['role']=='assistant' else 'User'}: {m['content']}"
                        for m in conversation
                        if m["content"] != "Start the conversation. Say your opening line."
                    )
                    + f"\n\nUser's latest message: {user_input}"
                )},
            ],
            max_tokens=5,
            temperature=0.0,
        )
        return "FELL" in resp.choices[0].message.content.strip().upper()
    except Exception:
        return False


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

    seeds = await asyncio.to_thread(_fetch_rag_seeds_sync, category)

    normal_prompt = _normal_prompt(category, seeds)
    scam_prompt   = _scam_prompt(category, seeds)
    scam_turn     = random.randint(3, 5)

    opening = await asyncio.to_thread(_get_opening_sync, normal_prompt)

    session = SimSession(
        session_id    = str(uuid.uuid4()),
        category      = category,
        conversation  = [
            {"role": "user",      "content": "Start the conversation. Say your opening line."},
            {"role": "assistant", "content": opening},
        ],
        user_turn     = 0,
        scam_turn     = scam_turn,
        scamming      = False,
        normal_prompt = normal_prompt,
        scam_prompt   = scam_prompt,
    )
    _sessions[session.session_id] = session

    return {"session_id": session.session_id, "initial_message": opening}


async def send_message(session_id: str, user_message: str) -> dict:
    """
    Send a user message and get the bot's reply.
    Returns: { bot_reply, fell_for_scam, feedback }
    """
    session = _sessions.get(session_id)
    if not session:
        raise ValueError("Session not found or already ended.")

    # Switch to scam mode when it's time
    if not session.scamming and session.user_turn >= session.scam_turn:
        session.scamming = True

    # Judge only during scam phase
    fell = False
    if session.scamming:
        fell = await asyncio.to_thread(
            _check_fell_sync, session.category, session.conversation, user_message
        )

    session.conversation.append({"role": "user", "content": user_message})
    session.user_turn += 1

    if fell:
        feedback = await asyncio.to_thread(
            _feedback_sync, session.category, session.conversation
        )
        del _sessions[session_id]
        return {"bot_reply": "", "fell_for_scam": True, "feedback": feedback}

    system_prompt = session.scam_prompt if session.scamming else session.normal_prompt
    bot_reply = await asyncio.to_thread(
        _bot_reply_sync, system_prompt, session.conversation
    )
    session.conversation.append({"role": "assistant", "content": bot_reply})

    return {"bot_reply": bot_reply, "fell_for_scam": False, "feedback": None}


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
