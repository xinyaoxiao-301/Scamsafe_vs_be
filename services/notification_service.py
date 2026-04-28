"""
services/notification_service.py
─────────────────────────────────
Fetches notification rows from the Neon (PostgreSQL) notifications table.

Table schema:
    CREATE TABLE IF NOT EXISTS notifications (
        id      SERIAL PRIMARY KEY,
        label   VARCHAR(10) NOT NULL,   -- "scam" | "not_scam"
        message TEXT        NOT NULL
    );

Environment variable required:
    DATABASE_URL  — psql connection string, e.g.
                    postgresql://user:pass@host/dbname?sslmode=require

How to test locally:
    1. To start the program, run `uvicorn main:app --reload --port 8000`
    2. Fetch a random notification: `curl http://localhost:8000/api/notifications/random`
    3. Reveal the result: `curl http://localhost:8000/api/notifications/3` (replace 3 with the actual ID from step 2)
"""


import os
import asyncio
import psycopg2
import psycopg2.extras


def _get_connection():
    # database URL needs to be hardcoded here because the async functions that call it run in a separate thread
    database_url = "postgresql://neondb_owner:npg_uTKRYhEgG1I4@ep-rapid-field-an7tq1ks.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    if not database_url:
        raise EnvironmentError("DATABASE_URL environment variable is not set.")
    return psycopg2.connect(database_url, cursor_factory=psycopg2.extras.RealDictCursor)


def _fetch_random_notification() -> dict:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, message FROM notifications ORDER BY RANDOM() LIMIT 1"
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        raise ValueError("No notifications found in the database.")

    return {"id": row["id"], "message": row["message"]}


def _fetch_notification_by_id(notification_id: int) -> dict:
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, label, message FROM notifications WHERE id = %s",
                (notification_id,),
            )
            row = cur.fetchone()

            if row is None:
                raise ValueError(f"Notification with id={notification_id} not found.")

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
    finally:
        conn.close()

    explanations = [r["explanation_text"] for r in explanation_rows]

    return {
        "id":           row["id"],
        "message":      row["message"],
        "label":        row["label"],
        "is_scam":      row["label"] == "scam",
        "explanations": explanations,
    }


async def get_random_notification() -> dict:
    """
    Return one random row from the notifications table.
    The label is intentionally EXCLUDED so the frontend cannot
    inspect it before the user clicks 'Open'.

    Returns: { id: int, message: str }
    Raises:  ValueError if the table is empty.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_random_notification)


async def get_notification_by_id(notification_id: int) -> dict:
    """
    Return the full row (including label) for a given notification ID.
    Called after the user clicks 'Open' to reveal the verdict.

    Returns: { id: int, message: str, label: str, is_scam: bool }
    Raises:  ValueError if the ID does not exist.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_notification_by_id, notification_id)