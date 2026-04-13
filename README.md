# ScamSafe Backend API

Built with FastAPI + Uvicorn. Run with:

```bash
uvicorn main:app --reload --port 8000
```

Interactive docs available at: `http://127.0.0.1:8000/docs`

---

## Environment Variables

Create a `.env` file in the backend root:

```
GROQ_API_KEY=
UPSTASH_VECTOR_REST_URL=
UPSTASH_VECTOR_REST_TOKEN=
DATABASE_URL=
```

---

## Endpoints

### 1. Scam Detection

**`POST /api/detect`**

Analyzes a message for scam patterns using Groq LLaMA.

Request:
```json
{
  "text": "Congratulations! You have won RM50,000. Click here to claim.",
  "language": "en"
}
```

Response:
```json
{
  "is_scam": true,
  "risk_level": "Very High",
  "confidence_percentage": 97,
  "scam_type": "Lottery/Prize Scam",
  "summary": "This message shows classic lottery scam patterns.",
  "warning_indicators": [
    "Unsolicited prize notification",
    "Creates false urgency",
    "Requests user to click a link"
  ],
  "action_steps": [
    "Do not click any links",
    "Block the sender",
    "Report to NACSA at www.nacsa.gov.my"
  ]
}
```

---

### 2. Scam Simulation

**`POST /api/simulate/start`**

Starts a new simulation session for a given scenario. The backend generates a persona via RAG + Groq and returns the opening message.

Scenario slugs:
- `romance-scams`
- `investment-scams`
- `tech-support-scams`
- `government-imposters`
- `marketplace-scams`
- `charity-scams`
- `lottery-prize-scams`
- `family-emergency-scams`

Request:
```json
{
  "scenario_type": "romance-scams"
}
```

Response:
```json
{
  "session_id": "a1b2c3d4-...",
  "initial_message": "Hi there! I came across your profile and thought you seemed really interesting..."
}
```

---

**`POST /api/simulate/message`**

Sends a user message and receives the bot's reply. The backend automatically escalates to scam tactics after a random number of turns. If the user falls for the scam, `fell_for_scam` is `true` and `feedback` contains the AI debrief.

Request:
```json
{
  "session_id": "a1b2c3d4-...",
  "message": "Oh hello! That's nice of you to say."
}
```

Response (normal turn):
```json
{
  "bot_reply": "I've been feeling a bit lonely lately, working overseas and all...",
  "fell_for_scam": false,
  "feedback": null
}
```

Response (user fell for scam):
```json
{
  "bot_reply": "",
  "fell_for_scam": true,
  "feedback": "1. ✅ What you did well...\n2. ⚠️ Where you went wrong...\n3. 🔴 The turning point...\n4. 💡 Tips..."
}
```

---

**`POST /api/simulate/quit`**

Ends a session early — used when the user says goodbye or chooses to stop. Returns success feedback from the AI coach.

Request:
```json
{
  "session_id": "a1b2c3d4-..."
}
```

Response:
```json
{
  "feedback": "🛡️ Great instincts! Here's what you did well...\n✅ ...\n⚠️ ...\n💡 ..."
}
```

---

### 3. Study Center Quiz

**`GET /api/quiz/topics`**

Returns all published quiz topics from the database.

Response:
```json
[
  {
    "slug": "romance-scams",
    "topic": "romance",
    "title": "Romance Scams",
    "description": "Learn to recognize emotional manipulation and money requests."
  },
  ...
]
```

---

**`GET /api/quiz/{quiz_slug}/questions?count=6`**

Returns `count` random questions for a given quiz slug. Use `mixed` as the slug for a cross-topic selection.

Example: `GET /api/quiz/romance-scams/questions?count=6`

Response:
```json
[
  {
    "id": "q-12",
    "topic": "romance",
    "prompt": "Someone you met online says they are stuck abroad and needs money urgently. What do you do?",
    "questionExplanation": "Romance scammers often fabricate emergencies to request money.",
    "options": [
      { "id": "101", "text": "Send the money immediately" },
      { "id": "102", "text": "Verify by video calling them first" },
      { "id": "103", "text": "Ask a trusted family member for advice" },
      { "id": "104", "text": "Block and report the contact" }
    ],
    "correctOptionId": "102",
    "explanation": {
      "correctReasons": [],
      "incorrectReasons": [],
      "tips": []
    },
    "choiceExplanations": {
      "101": "Sending money to unverified contacts is a common way people lose savings to romance scams.",
      "102": "Video calls make it much harder for scammers to maintain a false identity.",
      "103": "Talking to someone you trust can help you see red flags you might have missed.",
      "104": "Blocking is a safe option if you feel uncomfortable."
    }
  },
  ...
]
```

---

## Services

| File | Purpose |
|---|---|
| `services/scam_detector.py` | Groq LLaMA scam analysis |
| `services/scam_sim.py` | RAG + Groq simulation sessions |
| `services/quiz_service.py` | Neon PostgreSQL quiz retrieval |
