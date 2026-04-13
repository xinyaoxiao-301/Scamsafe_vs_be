"""
services/scam_detector.py
─────────────────────────
AI-powered scam detection using Groq. Importable module — no CLI entrypoint.
"""

import os
import json
import asyncio
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client: Groq | None = None

SYSTEM_PROMPT = """You are a scam detection expert helping elderly users stay safe online.

Analyze the given message and return a JSON response with this exact structure:
{
  "is_scam": true or false,
  "risk_level": "Very Low" | "Low" | "Medium" | "High" | "Very High",
  "confidence_percentage": <number 0-100>,
  "scam_type": "<type or 'Not a scam'>",
  "summary": "<1-2 sentence plain English explanation of why this is or isn't a scam>",
  "warning_indicators": ["<indicator 1>", "<indicator 2>", "<indicator 3>"],
  "action_steps": ["<step 1>", "<step 2>", "<step 3>"]
}

Scam types include: Phishing, Impersonation, Investment Scam, Lottery/Prize Scam,
Romance Scam, Tech Support Scam, Bank Fraud, Job Scam, Not a scam.

Warning indicators should be specific to the message (e.g. "Asks for bank details",
"Creates false urgency", "Unknown sender").
Action steps should be simple and clear (e.g. "Do not reply", "Block the sender",
"Report to your bank"). For low-risk messages, action steps should be reassuring
(e.g. "This message appears safe, but always stay cautious").

Return ONLY valid JSON. No extra text."""


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY environment variable not set.")
        _client = Groq(api_key=api_key)
    return _client


def _analyze_sync(message: str) -> dict:
    client = _get_client()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze this message:\n\n{message}"},
        ],
        temperature=0.2,
        max_tokens=600,
    )
    raw = completion.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    return json.loads(raw)


async def analyze_message(message: str) -> dict:
    """Analyze a message for scam indicators. Returns structured JSON."""
    return await asyncio.to_thread(_analyze_sync, message)
