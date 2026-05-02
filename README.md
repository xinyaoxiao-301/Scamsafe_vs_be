# ScamSafe

## Project Description

### UN Goal 16: Promoting Ethical Tech & Digital Rights

#### Overview

ScamSafe is an AI-powered scam detection and prevention website designed to protect older adults in Malaysia. The project focuses on ethical technology, digital rights, and accessible protection for users who may face a higher risk of online fraud because of limited digital literacy and age-related vulnerability.

#### Problem Statement

In the digital age, online scams are becoming increasingly common. Research shows that 74% of adults face scams monthly through phone calls, social media, and text messages. The *State of Scam Report 2024* reports that scam victims in Malaysia suffer total losses of RM54.02 billion, which is equivalent to around 3% of the nation's GDP (Global Anti-Scam Alliance, 2024).

Older adults in Malaysia aged 60 and above account for 83.7% of scam victims because of lower digital literacy and age-related cognitive decline (Saifuddin et al., 2024). Although many websites can detect malicious websites, only a small number of tools are designed to detect scams in ways that specifically support elderly users. ScamSafe responds to this gap by proposing an AI-powered scam detection and prevention website tailored to this audience.

#### Project Goal

The goal of ScamSafe is to create a simplified and trustworthy tool that helps elderly users:

- identify suspicious messages, links, and scam patterns,
- protect their financial independence,
- make safer decisions without needing advanced technical knowledge,
- and maintain dignity by avoiding shame, embarrassment, or dependence when facing suspicious situations.

#### Persona

**Name:** Feng Tan  
**Age:** 65  
**Location:** Cheras, Kuala Lumpur, Malaysia  
**Occupation:** Retired Secondary School Teacher with stable financial resources

##### Lifestyle and Behavior

- Lives with his wife while his children work in Singapore, which increases social isolation and his trust in friendly strangers.
- Uses WhatsApp and Facebook daily, but is not confident with digital security or device protection.
- Is highly responsive to messages that appear official, especially from authorities such as the police or bank representatives (Saifuddin et al., 2024).

##### Pain Points

- Stable savings and reliable income make him a prime target for investment and impersonation scams.
- Age-related decline in memory and decision-making makes it harder to identify inconsistencies in sophisticated scam scripts.
- Older victims often face significantly higher financial losses per incident than other age groups (New Straits Times, 2025).

##### Goals and Motivations

- Protect lifetime savings and maintain financial independence.
- Review suspicious content with a simple tool that does not require advanced technical skills.
- Defend himself independently while avoiding the shame or embarrassment of being defrauded.

#### Open Data and Datasets

##### Population and Demographics

- [OpenDOSM population by district](https://open.dosm.gov.my/data-catalogue/population_district)
- [OpenDOSM population dashboard](https://open.dosm.gov.my/dashboard/population)
- [data.gov.my crime dataset reference](https://data.gov.my/data-catalogue/crime_district)
  Note: this is useful for district-level context, but it is not an online scam dataset.

##### Phishing and Fraud Sources

- [OpenPhish phishing website database](https://openphish.com/phishing_database.html)
- [UNIMAS phishing dataset](https://www.fcsit.unimas.my/phishing-dataset)
- [CyberSecurity Malaysia / MyCERT fraud statistics](https://www.cybersecurity.my/portal-main/statistics-details?id=21)
  Note: the fraud statistics currently extend only to 2024.

##### Call and Message Datasets

- [Kaggle call transcript scam determinations dataset](https://www.kaggle.com/datasets/mealss/call-transcripts-scam-determinations?resource=download)
- [SMS scam detection dataset](https://github.com/vinit9638/SMS-scam-detection-dataset/blob/main/sms_scam_detection_dataset_merged_with_lang.csv)
- [SMS Spam Collection Dataset] (https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset)
- [SMS Spam Dataset] (https://www.kaggle.com/datasets/tapakah68/spam-text-messages-dataset)

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

**`POST /api/simulate/quiz`**

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

### 4. Notification Challenge

`GET /api/notifications/random`
`GET /api/notifications/{id}`


- Simulates real-life notifications
- Users decide whether to open or ignore messages
- Reveals:
  - Scam verdict
  - Explanation of red flags

---

### 5. Scam News & Prevention Tips

`GET /api/scam/news`
`GET /api/scam/news/{article_id}`

- Displays real scam news articles
- Includes:
  - Full article content
  - Prevention tips

---

## Services

| File | Purpose |
|---|---|
| `services/scam_detector.py` | Groq LLaMA scam analysis |
| `services/scam_sim.py` | RAG + Groq simulation sessions |
| `services/quiz_service.py` | Neon PostgreSQL quiz retrieval |

---

## System Architecture

### Backend
- FastAPI
- Uvicorn

### AI Layer
- Groq LLaMA (Detection + Simulation)
- RAG (Scenario generation)
- Upstash Vector DB

### Database
- Neon PostgreSQL
  - Quiz data
  - Notifications
  - Scam news

### Async Handling
- `asyncio.to_thread`
- `run_in_executor`

last update 03/05/2026 12:28am