"""
services/notification_service.py
─────────────────────────────────
Fetches notification rows from the Neon (PostgreSQL) notifications table,
with support for translated content based on the selected language.

Supported language codes:
    'en'  — English (default, reads from base notifications / explanation tables)
    'ms'  — Bahasa Melayu (reads from notification_translation / explanation_translation)
    'zh'  — Chinese (reads from notification_translation / explanation_translation)

Table schema:
    notifications(id, label, message)
    explanation(id, notification_id, explanation_number, explanation_text)
    notification_translation(notification_id, language_code, translated_message, translated_label)
    explanation_translation(explanation_id, language_code, translated_text)

Environment variable required:
    DATABASE_URL  — psql connection string

How to test locally:
    1. uvicorn main:app --reload --port 8000
    2. curl "http://localhost:8000/api/notifications/random?language=ms"
    3. curl "http://localhost:8000/api/notifications/3?language=zh"
"""

import asyncio
import os

import psycopg2
import psycopg2.extras

_DATABASE_URL = "postgresql://neondb_owner:npg_uTKRYhEgG1I4@ep-rapid-field-an7tq1ks.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

SUPPORTED_LANGUAGES = {"en", "ms", "zh"}


def _get_connection():
    database_url = _DATABASE_URL or os.environ.get("DATABASE_URL")
    if not database_url:
        raise EnvironmentError("DATABASE_URL environment variable is not set.")
    return psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)


def _normalise_language(language: str) -> str:
    """Return a supported language code, falling back to 'en'."""
    lang = (language or "en").lower().strip()
    # Accept full locale tags like 'zh-Hans-MY' → 'zh'
    lang = lang.split("-")[0]
    return lang if lang in SUPPORTED_LANGUAGES else "en"


# ---------------------------------------------------------------------------
# Random notification
# ---------------------------------------------------------------------------

def _fetch_random_notification(language: str) -> dict:
    lang = _normalise_language(language)
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            if lang == "en":
                cur.execute(
                    "SELECT id, message FROM notifications ORDER BY RANDOM() LIMIT 1"
                )
            else:
                # Join with translations; fall back to base English row when no
                # translation exists for this notification.
                cur.execute(
                    """
                    SELECT
                        n.id,
                        COALESCE(nt.translated_message, n.message) AS message
                    FROM notifications n
                    LEFT JOIN notification_translation nt
                        ON nt.notification_id = n.id
                        AND nt.language_code = %s
                    ORDER BY RANDOM()
                    LIMIT 1
                    """,
                    (lang,),
                )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError("No notifications found in the database.")

    return {"id": row["id"], "message": row["message"]}


# ---------------------------------------------------------------------------
# Reveal by ID
# ---------------------------------------------------------------------------

def _fetch_notification_by_id(notification_id: int, language: str) -> dict:
    lang = _normalise_language(language)
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            if lang == "en":
                cur.execute(
                    "SELECT id, label, message FROM notifications WHERE id = %s",
                    (notification_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT
                        n.id,
                        COALESCE(nt.translated_label, n.label) AS label,
                        COALESCE(nt.translated_message, n.message) AS message
                    FROM notifications n
                    LEFT JOIN notification_translation nt
                        ON nt.notification_id = n.id
                        AND nt.language_code = %s
                    WHERE n.id = %s
                    """,
                    (lang, notification_id),
                )

            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Notification with id={notification_id} not found.")

            if lang == "en":
                cur.execute(
                    """
                    SELECT explanation_number, explanation_text
                    FROM explanation
                    WHERE notification_id = %s
                    ORDER BY explanation_number ASC
                    """,
                    (notification_id,),
                )
                explanation_rows = cur.fetchall()
                explanations = [r["explanation_text"] for r in explanation_rows]
            else:
                # Fetch translated explanations, falling back to English text
                # when no translation row exists.
                cur.execute(
                    """
                    SELECT
                        e.explanation_number,
                        COALESCE(et.translated_text, e.explanation_text) AS explanation_text
                    FROM explanation e
                    LEFT JOIN explanation_translation et
                        ON et.explanation_id = e.id
                        AND et.language_code = %s
                    WHERE e.notification_id = %s
                    ORDER BY e.explanation_number ASC
                    """,
                    (lang, notification_id),
                )
                explanation_rows = cur.fetchall()
                explanations = [r["explanation_text"] for r in explanation_rows]

    finally:
        conn.close()

    return {
        "id": row["id"],
        "message": row["message"],
        "label": row["label"],
        "is_scam": row["label"] == "scam",
        "explanations": explanations,
    }


# ---------------------------------------------------------------------------
# Public async API
# ---------------------------------------------------------------------------

async def get_random_notification(language: str = "en") -> dict:
    """
    Return one random notification row (label withheld) in the requested language.

    Returns: { id: int, message: str }
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_random_notification, language)


async def get_notification_by_id(notification_id: int, language: str = "en") -> dict:
    """
    Return the full notification row (including label and explanations) for the
    given ID, in the requested language.

    Returns: { id, message, label, is_scam, explanations }
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _fetch_notification_by_id, notification_id, language
    )