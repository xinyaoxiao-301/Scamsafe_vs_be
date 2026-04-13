"""
services/quiz_service.py
────────────────────────
Quiz question retrieval from the Neon PostgreSQL database.
Importable module — no CLI entrypoint.

DATABASE_URL is read from the DATABASE_URL environment variable (recommended)
or falls back to the hardcoded connection string already in the project.
"""

import os
import random
import asyncio
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL="postgresql://neondb_owner:npg_ZcoC14teEXmq@ep-billowing-feather-amfmzuvb.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Maps DB quiz slugs → frontend topic keys
SLUG_TO_TOPIC: dict[str, str] = {
    "romance-scams":          "romance",
    "investment-scams":       "investment",
    "tech-support-scams":     "tech-support",
    "government-imposters":   "government-imposter",
    "marketplace-scams":      "marketplace",
    "charity-scams":          "charity",
    "lottery-prize-scams":    "lottery-prize",
    "family-emergency-scams": "family-emergency",
}

# Reverse map: frontend topic key → DB quiz slug
TOPIC_TO_SLUG: dict[str, str] = {v: k for k, v in SLUG_TO_TOPIC.items()}


# ── Sync DB helpers ───────────────────────────────────────────────────────────
def _connect():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def _fetch_all_quizzes_sync() -> list[dict]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, slug, display_order
                FROM quizzes
                WHERE is_published = TRUE
                ORDER BY display_order
                """
            )
            return [dict(row) for row in cur.fetchall()]


def _fetch_questions_for_quiz_sync(quiz_id: int, limit: int) -> list[dict]:
    """Fetch `limit` random questions for a quiz, including their choices."""
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, prompt, explanation
                FROM questions
                WHERE quiz_id = %s
                ORDER BY RANDOM()
                LIMIT %s
                """,
                (quiz_id, limit),
            )
            questions = cur.fetchall()

            result = []
            for q in questions:
                cur.execute(
                    """
                    SELECT id, label, explanation, is_correct
                    FROM choices
                    WHERE question_id = %s
                    ORDER BY display_order
                    """,
                    (q["id"],),
                )
                choices = cur.fetchall()
                result.append({"question": dict(q), "choices": [dict(c) for c in choices]})
            return result


# ── Formatting helper ─────────────────────────────────────────────────────────
def _format_question(row: dict, topic: str) -> dict:
    q       = row["question"]
    choices = row["choices"]

    correct = next((c for c in choices if c["is_correct"]), choices[0] if choices else None)
    options = [{"id": str(c["id"]), "text": c["label"]} for c in choices]
    choice_explanations = {
        str(c["id"]): c["explanation"]
        for c in choices
        if c.get("explanation")
    }

    return {
        "id":                  f"q-{q['id']}",
        "topic":               topic,
        "prompt":              q["prompt"],
        "questionExplanation": q.get("explanation"),
        "options":             options,
        "correctOptionId":     str(correct["id"]) if correct else (options[0]["id"] if options else ""),
        "explanation":         {"correctReasons": [], "incorrectReasons": [], "tips": []},
        "choiceExplanations":  choice_explanations,
    }


# ── Public async API ──────────────────────────────────────────────────────────
async def get_quizzes() -> list[dict]:
    """Return the list of published quizzes (topic metadata)."""
    rows = await asyncio.to_thread(_fetch_all_quizzes_sync)
    return [
        {
            "slug":        row["slug"],
            "topic":       SLUG_TO_TOPIC.get(row["slug"], row["slug"]),
            "title":       row["title"],
            "description": row["description"],
        }
        for row in rows
    ]


async def get_questions(quiz_slug: str, count: int = 6) -> list[dict]:
    """
    Fetch `count` random questions for the given quiz slug.
    Pass slug="mixed" to draw questions from all quizzes.
    """
    all_quizzes = await asyncio.to_thread(_fetch_all_quizzes_sync)

    if quiz_slug == "mixed":
        # Pull a small sample from every quiz and shuffle
        all_formatted: list[dict] = []
        per_quiz = max(2, (count // len(all_quizzes)) + 1) if all_quizzes else count
        for quiz in all_quizzes:
            topic = SLUG_TO_TOPIC.get(quiz["slug"], quiz["slug"])
            rows  = await asyncio.to_thread(_fetch_questions_for_quiz_sync, quiz["id"], per_quiz)
            all_formatted.extend(_format_question(r, topic) for r in rows)
        random.shuffle(all_formatted)
        return all_formatted[:count]

    # Single-topic quiz
    quiz = next((q for q in all_quizzes if q["slug"] == quiz_slug), None)
    if quiz is None:
        raise ValueError(f"Quiz not found: {quiz_slug!r}")

    topic = SLUG_TO_TOPIC.get(quiz_slug, quiz_slug)
    rows  = await asyncio.to_thread(_fetch_questions_for_quiz_sync, quiz["id"], count)
    return [_format_question(r, topic) for r in rows]
