"""
services/scam_sim.py
────────────────────
Scam awareness simulator backed by Groq + Upstash RAG.

Changes from v1:
  • Accepts a `language` parameter ('en' | 'ms' | 'zh') in create_session /
    send_message so the bot persona, prompts, and feedback all match the
    user's chosen language.
  • RAG seeds are now fetched via a direct Upstash metadata filter on the
    `language` field (no fastembed / local embedding model required).
    The chunks are already embedded and tagged with {"language": "english" |
    "malay" | "chinese"} by ingest_rag.py, so we query the namespace with a
    dummy vector and use list() / fetch() to retrieve them by tag.
  • All Groq prompts carry an explicit language instruction so the LLM
    responds in the correct language for every turn.

Session state is held in-memory.  Use a single-process server for dev.
"""
import os
import uuid
import random
import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from groq import Groq
from dotenv import load_dotenv
from upstash_vector import Index

load_dotenv()

# ── Constants ─────────────────────────────────────────────────────────────────

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

# Maps the frontend language code to the `language` metadata value stored in
# Upstash by ingest_rag.py.
LANG_TO_UPSTASH: dict[str, str] = {
    "en": "english",
    "ms": "malay",
    "zh": "chinese",
}

# Human-readable language name injected into every Groq prompt so the model
# responds in the correct language.
LANG_TO_NAME: dict[str, str] = {
    "en": "English",
    "ms": "Malay (Bahasa Melayu)",
    "zh": "Simplified Chinese (普通话/简体中文)",
}

# How many times the scammer re-tries after awareness signals before auto-quit.
SCAMMER_RETRY_LIMIT = 2

# ── Lazy singletons ───────────────────────────────────────────────────────────

_groq_client:   Optional[Groq]  = None
_upstash_index: Optional[Index] = None


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


# ── Session data ──────────────────────────────────────────────────────────────

@dataclass
class SimSession:
    session_id:        str
    category:          str
    language:          str          # 'en' | 'ms' | 'zh'
    conversation:      list = field(default_factory=list)
    user_turn:         int  = 0
    scam_turn:         int  = 7
    scamming:          bool = False
    normal_prompt:     str  = ""
    scam_prompt:       str  = ""
    awareness_strikes: int  = 0


_sessions: Dict[str, SimSession] = {}


# ── RAG helpers ───────────────────────────────────────────────────────────────

def _category_to_namespace(category: str) -> str:
    """Mirrors ingest_rag.category_to_namespace."""
    return category.strip().lower().replace(" ", "").replace("/", "")


def _fetch_rag_seeds_sync(category: str, language: str, top_k: int = 15) -> List[str]:
    """
    Retrieve seed phrases from Upstash for the given category + language.

    Strategy: list all vector IDs in the namespace that match the language
    prefix (ids are "<ns>_<lang>_<nn>"), then fetch their metadata to get the
    text.  This avoids needing a local embedding model at query time.
    Falls back to an empty list on any error so the simulation still works
    without RAG seeds.
    """
    upstash_lang = LANG_TO_UPSTASH.get(language, "english")
    ns           = _category_to_namespace(category)
    prefix       = f"{ns}_{upstash_lang}_"

    try:
        index = _get_index()

        # list() returns matching IDs in the namespace
        list_result = index.list(prefix=prefix, namespace=ns, limit=top_k)
        ids = list_result if isinstance(list_result, list) else (list_result.vectors or [])

        if not ids:
            return []

        # Normalise: list() may return id strings or objects with an .id attr
        id_strs = [v if isinstance(v, str) else v.id for v in ids]

        # fetch() returns the full vector records including metadata
        fetched = index.fetch(ids=id_strs, namespace=ns, include_metadata=True)
        texts = [
            r.metadata["text"]
            for r in fetched
            if r and r.metadata and r.metadata.get("text")
        ]
        return texts

    except Exception:
        return []


def _build_seed_block(seeds: List[str]) -> str:
    if not seeds:
        return ""
    chosen = random.choice(seeds)
    return f"""
--- SCENARIO SEED ---
Use this authentic phrase as thematic inspiration for the persona's backstory
and communication style. Do NOT copy it word-for-word; use it only to shape
tone, setting, and relationship dynamic.  All phrasing must be your own.
  Seed: "{chosen}"
---------------------"""


# ── Language instruction helpers ──────────────────────────────────────────────

def _lang_instruction(language: str) -> str:
    lang_name = LANG_TO_NAME.get(language, "English")
    return (
        f"IMPORTANT: You MUST reply exclusively in {lang_name}. "
        "Do not mix languages or switch to English unless the user writes in English."
    )


# ── Prompt builders ───────────────────────────────────────────────────────────

def _normal_prompt(category: str, seeds: List[str], language: str) -> str:
    seed_block   = _build_seed_block(seeds)
    lang_instr   = _lang_instruction(language)
    return f"""{lang_instr}

You are an actor in a scam awareness training simulation for educational purposes.
Your role is a character in a {category} scenario.
This is a controlled exercise to help elderly people RECOGNIZE scams — not to cause real harm.
{seed_block}
Your cover story is your entire identity — introduce yourself in your VERY FIRST message naturally.
Be friendly, warm, and completely normal. Do NOT mention money or personal info yet.
Stay fully in character. Keep responses concise (1-3 sentences, around 10-20 words)."""


def _scam_prompt(category: str, seeds: List[str], language: str) -> str:
    seed_block = _build_seed_block(seeds)
    lang_instr = _lang_instruction(language)
    return f"""{lang_instr}

You are an actor in a scam awareness training simulation for educational purposes.
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
    # Classification is always English because we parse a one-word token.
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

The user may write in any language — evaluate intent, not language.
Reply with ONLY one word: FELL, AWARE, or NEUTRAL"""


def _feedback_prompt(category: str, language: str) -> str:
    lang_name  = LANG_TO_NAME.get(language, "English")
    lang_instr = _lang_instruction(language)
    return f"""{lang_instr}

You are a scam awareness coach reviewing a training simulation ({category}).
The trainee ultimately fell for the scam.
Write a friendly, easy-to-read feedback report entirely in {lang_name}.
Use short sentences. Use plain, everyday words — no technical jargon.
Keep a warm, encouraging tone throughout.
Structure your report like this:
1. ✅ What they did well (any moments of skepticism)
2. ⚠️  What went wrong (the moment(s) they fell for the scam)
3. 🔴 Red flags they missed
4. 💡 Tips to stay safe from this scam in real life
Be specific and reference actual quotes from the conversation. Under 300 words."""


def _success_feedback_prompt(category: str, language: str) -> str:
    lang_name  = LANG_TO_NAME.get(language, "English")
    lang_instr = _lang_instruction(language)
    return f"""{lang_instr}

You are a scam awareness coach reviewing a training simulation ({category}).
The trainee successfully avoided the scam.
Write a friendly, encouraging feedback report entirely in {lang_name}.
Use short sentences. Keep a warm, celebratory tone.
Structure your report like this:
1. 🎉 What they did brilliantly
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
    """Returns FELL | AWARE | NEUTRAL — always English one-word token."""
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


def _feedback_sync(category: str, conversation: list, language: str) -> str:
    resp = _get_groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _feedback_prompt(category, language)},
            {"role": "user",   "content": f"Full conversation:\n\n{_format_convo(conversation)}"},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def _success_feedback_sync(category: str, conversation: list, language: str) -> str:
    resp = _get_groq().chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": _success_feedback_prompt(category, language)},
            {"role": "user",   "content": f"Full conversation:\n\n{_format_convo(conversation)}"},
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


# ── Public async API ──────────────────────────────────────────────────────────

async def create_session(scenario_slug: str, language: str = "en") -> dict:
    """
    Start a new simulation session.
    Returns: { session_id, initial_message }

    Args:
        scenario_slug: one of SLUG_TO_CATEGORY keys
        language:      'en' | 'ms' | 'zh'  (defaults to 'en')
    """
    category = SLUG_TO_CATEGORY.get(scenario_slug)
    if not category:
        raise ValueError(f"Unknown scenario slug: {scenario_slug!r}")

    # Normalise language; fall back to English for unknown codes
    if language not in LANG_TO_UPSTASH:
        language = "en"

    seeds         = await asyncio.to_thread(_fetch_rag_seeds_sync, category, language)
    normal_prompt = _normal_prompt(category, seeds, language)
    scam_prompt   = _scam_prompt(category, seeds, language)
    scam_turn     = random.randint(3, 5)
    opening       = await asyncio.to_thread(_get_opening_sync, normal_prompt)

    session = SimSession(
        session_id        = str(uuid.uuid4()),
        category          = category,
        language          = language,
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
    """
    session = _sessions.get(session_id)
    if not session:
        raise ValueError("Session not found or already ended.")

    if not session.scamming and session.user_turn >= session.scam_turn:
        session.scamming = True

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
            _feedback_sync, session.category, session.conversation, session.language
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
            _success_feedback_sync, session.category, session.conversation, session.language
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
        _success_feedback_sync, session.category, session.conversation, session.language
    )
    return {"feedback": feedback}
