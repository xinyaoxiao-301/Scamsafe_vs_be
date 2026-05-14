"""
services/quiz_service.py
────────────────────────
Quiz question retrieval from the Neon PostgreSQL database.
Importable module — no CLI entrypoint.

DATABASE_URL is read from the DATABASE_URL environment variable (recommended)
or falls back to the hardcoded connection string already in the project.

Multilingual support
────────────────────
The schema ships English text in the base tables (quizzes, questions, choices)
and optional translations in quiz_translations, question_translations, and
choice_translations keyed by language_code (e.g. "ms", "zh").

Pass language="en" (default) to return base-table text.
Pass language="ms" or language="zh" to get translated text where available,
falling back to the English base-table text for any row that has no
translation yet.
"""

import os
import random
import asyncio
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_ZcoC14teEXmq@ep-billowing-feather-amfmzuvb.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
)

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

# Supported non-English language codes
SUPPORTED_LANGUAGES = {"ms", "zh"}


# ── Sync DB helpers ───────────────────────────────────────────────────────────

def _connect():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def _fetch_all_quizzes_sync(language: str = "en") -> list[dict]:
    """
    Fetch all published quizzes.  When language is not "en", coalesce
    translated title/description onto the base-table row.
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            if language in SUPPORTED_LANGUAGES:
                cur.execute(
                    """
                    SELECT
                        q.id,
                        q.slug,
                        q.display_order,
                        COALESCE(qt.title,       q.title)       AS title,
                        COALESCE(qt.description, q.description) AS description
                    FROM quizzes q
                    LEFT JOIN quiz_translations qt
                        ON qt.quiz_id = q.id AND qt.language_code = %s
                    WHERE q.is_published = TRUE
                    ORDER BY q.display_order
                    """,
                    (language,),
                )
            else:
                cur.execute(
                    """
                    SELECT id, title, description, slug, display_order
                    FROM quizzes
                    WHERE is_published = TRUE
                    ORDER BY display_order
                    """
                )
            return [dict(row) for row in cur.fetchall()]


def _fetch_questions_for_quiz_sync(
    quiz_id: int,
    limit: int,
    language: str = "en",
) -> list[dict]:
    """
    Fetch `limit` random questions for a quiz, including their choices.
    For non-English languages the translated text is coalesced over the
    English base-table text so partially-translated quizzes still work.
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            if language in SUPPORTED_LANGUAGES:
                cur.execute(
                    """
                    SELECT
                        q.id,
                        COALESCE(qt.prompt,      q.prompt)      AS prompt,
                        COALESCE(qt.explanation, q.explanation) AS explanation
                    FROM questions q
                    LEFT JOIN question_translations qt
                        ON qt.question_id = q.id AND qt.language_code = %s
                    WHERE q.quiz_id = %s
                    ORDER BY RANDOM()
                    LIMIT %s
                    """,
                    (language, quiz_id, limit),
                )
            else:
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
                if language in SUPPORTED_LANGUAGES:
                    cur.execute(
                        """
                        SELECT
                            c.id,
                            COALESCE(ct.label,       c.label)       AS label,
                            COALESCE(ct.explanation, c.explanation) AS explanation,
                            c.is_correct,
                            c.display_order
                        FROM choices c
                        LEFT JOIN choice_translations ct
                            ON ct.choice_id = c.id AND ct.language_code = %s
                        WHERE c.question_id = %s
                        ORDER BY c.display_order
                        """,
                        (language, q["id"]),
                    )
                else:
                    cur.execute(
                        """
                        SELECT id, label, explanation, is_correct, display_order
                        FROM choices
                        WHERE question_id = %s
                        ORDER BY display_order
                        """,
                        (q["id"],),
                    )
                choices = cur.fetchall()
                result.append({
                    "question": dict(q),
                    "choices":  [dict(c) for c in choices],
                })
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

async def get_quizzes(language: str = "en") -> list[dict]:
    """Return the list of published quizzes (topic metadata)."""
    rows = await asyncio.to_thread(_fetch_all_quizzes_sync, language)
    return [
        {
            "slug":        row["slug"],
            "topic":       SLUG_TO_TOPIC.get(row["slug"], row["slug"]),
            "title":       row["title"],
            "description": row["description"],
        }
        for row in rows
    ]


async def get_questions(
    quiz_slug: str,
    count: int = 6,
    language: str = "en",
) -> list[dict]:
    """
    Fetch `count` random questions for the given quiz slug.
    Pass slug="mixed" to draw questions from all quizzes.
    Pass language="ms" or "zh" to receive translated content.
    """
    all_quizzes = await asyncio.to_thread(_fetch_all_quizzes_sync, language)

    if quiz_slug == "mixed":
        # Pull a small sample from every quiz and shuffle
        all_formatted: list[dict] = []
        per_quiz = max(2, (count // len(all_quizzes)) + 1) if all_quizzes else count
        for quiz in all_quizzes:
            topic = SLUG_TO_TOPIC.get(quiz["slug"], quiz["slug"])
            rows  = await asyncio.to_thread(
                _fetch_questions_for_quiz_sync, quiz["id"], per_quiz, language
            )
            all_formatted.extend(_format_question(r, topic) for r in rows)
        random.shuffle(all_formatted)
        return all_formatted[:count]

    # Single-topic quiz
    quiz = next((q for q in all_quizzes if q["slug"] == quiz_slug), None)
    if quiz is None:
        raise ValueError(f"Quiz not found: {quiz_slug!r}")

    topic = SLUG_TO_TOPIC.get(quiz_slug, quiz_slug)
    rows  = await asyncio.to_thread(
        _fetch_questions_for_quiz_sync, quiz["id"], count, language
    )
    return [_format_question(r, topic) for r in rows]