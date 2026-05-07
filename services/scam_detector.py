"""
services/scam_detector.py
─────────────────────────
AI-powered scam detection using Groq. Importable module — no CLI entrypoint.

Supports three response languages: English ('en'), Malay ('ms'), Chinese ('zh').
Structural enum fields (risk_level, scam_type, is_scam) are always returned in
English so the frontend type-guards and label maps work regardless of language.
Only the human-readable fields (summary, warning_indicators, action_steps) are
localised.
"""

import os
import json
import asyncio
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client: Groq | None = None

# ---------------------------------------------------------------------------
# Language-aware system prompts
# ---------------------------------------------------------------------------

_SCHEMA_BLOCK = """Return a JSON object with EXACTLY these keys — no extras, no omissions:
{
  "is_scam": true or false,
  "risk_level": "Very Low" | "Low" | "Medium" | "High" | "Very High",
  "scam_type": "<type — see allowed list below>",
  "summary": "<human-readable explanation>",
  "warning_indicators": ["<indicator 1>", "<indicator 2>", "<indicator 3>"],
  "action_steps": ["<step 1>", "<step 2>", "<step 3>"]
}"""

_ENUM_BLOCK = """risk_level MUST be exactly one of (in English, verbatim):
  "Very Low", "Low", "Medium", "High", "Very High"

scam_type MUST be exactly one of (in English, verbatim):
  "Phishing", "Impersonation", "Investment Scam", "Lottery/Prize Scam",
  "Romance Scam", "Tech Support Scam", "Bank Fraud", "Other", "Not a scam"

IMPORTANT: risk_level and scam_type MUST always be in English, exactly as listed
above. Do NOT translate these two fields."""

_SYSTEM_PROMPTS: dict[str, str] = {
    "en": f"""You are a scam detection expert helping elderly users stay safe online.

Analyse the given message and return a JSON response as described below.

{_SCHEMA_BLOCK}

{_ENUM_BLOCK}

Write summary, warning_indicators, and action_steps in plain English.
- summary: 1–2 sentences explaining why the message is or is not a scam.
- warning_indicators: specific red flags found in the message
  (e.g. "Asks for bank details", "Creates false urgency", "Unknown sender").
- action_steps: simple, clear next steps
  (e.g. "Do not reply", "Block the sender", "Report to your bank").
  For low-risk messages use reassuring steps
  (e.g. "This message appears safe, but always stay cautious").

Return ONLY valid JSON. No extra text, no markdown fences.""",

    "ms": f"""Anda adalah pakar pengesanan penipuan yang membantu pengguna warga emas
kekal selamat dalam talian.

Analisis mesej yang diberikan dan kembalikan respons JSON seperti di bawah.

{_SCHEMA_BLOCK}

{_ENUM_BLOCK}

Tulis summary, warning_indicators, dan action_steps dalam Bahasa Melayu yang
mudah difahami.
- summary: 1–2 ayat yang menerangkan sama ada mesej ini penipuan atau tidak.
- warning_indicators: tanda amaran khusus yang ditemui dalam mesej
  (cth. "Meminta maklumat bank", "Mewujudkan kepanikan palsu", "Penghantar tidak dikenali").
- action_steps: langkah mudah dan jelas yang perlu diambil
  (cth. "Jangan balas", "Sekat penghantar", "Laporkan kepada bank anda").
  Untuk mesej berisiko rendah, gunakan langkah yang menenangkan
  (cth. "Mesej ini nampak selamat, tetapi sentiasa berhati-hati").

Kembalikan HANYA JSON yang sah. Tiada teks tambahan, tiada markdown.""",

    "zh": f"""您是一位诈骗检测专家，帮助老年用户在网络上保持安全。

分析给定的消息，并按以下格式返回 JSON 响应。

{_SCHEMA_BLOCK}

{_ENUM_BLOCK}

请用简体中文撰写 summary、warning_indicators 和 action_steps。
- summary：1–2 句话，解释该消息是否为诈骗及原因。
- warning_indicators：消息中发现的具体风险信号
  （例如："要求提供银行信息"、"制造虚假紧迫感"、"未知发件人"）。
- action_steps：简单明了的下一步建议
  （例如："不要回复"、"屏蔽发件人"、"向您的银行举报"）。
  对于低风险消息，使用令人放心的建议
  （例如："此消息看起来是安全的，但请始终保持谨慎"）。

只返回有效的 JSON，不要有额外文字或 Markdown 代码块。""",
}

# Fall back to English for any unsupported language code.
_SUPPORTED_LANGUAGES = frozenset(_SYSTEM_PROMPTS.keys())


# ---------------------------------------------------------------------------
# Groq client helpers
# ---------------------------------------------------------------------------

def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY environment variable not set.")
        _client = Groq(api_key=api_key)
    return _client


VALID_SCAM_TYPES = {
    "Phishing", "Impersonation", "Investment Scam",
    "Lottery/Prize Scam", "Romance Scam", "Tech Support Scam",
    "Bank Fraud", "Other", "Not a scam",
}

VALID_RISK_LEVELS = {
    "Very Low", "Low", "Medium", "High", "Very High",
}


def _analyze_sync(message: str, language: str = "en") -> dict:
    lang = language if language in _SUPPORTED_LANGUAGES else "en"
    system_prompt = _SYSTEM_PROMPTS[lang]

    client = _get_client()
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyse this message:\n\n{message}"},
        ],
        temperature=0.2,
        max_tokens=700,
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from model: {e}\nRaw: {raw!r}")

    # Sanitise enum fields — the model must always return these in English, but
    # guard against accidental translation or hallucination just in case.
    if result.get("scam_type") not in VALID_SCAM_TYPES:
        result["scam_type"] = "Other"
    if result.get("risk_level") not in VALID_RISK_LEVELS:
        result["risk_level"] = "Low"

    return result


async def analyze_message(message: str, language: str = "en") -> dict:
    """Analyse a message for scam indicators.

    Args:
        message:  The raw text to evaluate.
        language: BCP-47 language tag — 'en', 'ms', or 'zh'.
                  Falls back to 'en' for any unsupported value.

    Returns:
        Structured JSON dict. risk_level and scam_type are always English enum
        strings; summary, warning_indicators, and action_steps are localised.
    """
    return await asyncio.to_thread(_analyze_sync, message, language)
