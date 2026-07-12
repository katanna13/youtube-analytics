# ▶ YouTube Growth Copilot

> An AI-powered YouTube analytics product that turns real channel data into clear, actionable growth decisions.

<<<<<<< HEAD

=======
**AMD Developer Hackathon: ACT II · Track 3 — Unicorn Track**
>>>>>>> 653e971 (Finalize Groq integration and hackathon submission)

---

## 🎯 Problem

YouTube Studio provides creators with large amounts of analytics data, but it does not always explain what actions a creator should take next.

Creators still need to answer questions such as:

- When should I upload?
- Which title patterns work best for my audience?
- Why did a video underperform?
- What should I publish next?
- How can I improve my content strategy?

**YouTube Growth Copilot converts raw analytics into concrete recommendations.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Channel Overview** | Traffic sources, format performance, title patterns, and weak videos |
| ⏰ **Best Upload Times** | Detects the strongest days and hours from real channel performance |
| 🤖 **ML Performance Classifier** | Predicts whether a new video is likely to be Low, Medium, High, or Viral |
| 🎬 **Next Video Ideas** | Generates five ideas based on the channel's top-performing titles |
| 🖼️ **Thumbnail Assistant** | Produces title-specific thumbnail recommendations |
| 📝 **Title Generator** | Generates titles using patterns discovered in the creator's own data |
| 📈 **Channel Audit** | Returns a channel score, strengths, growth gaps, and top actions |
| ⚠️ **Weak Video Analysis** | Diagnoses underperforming videos and proposes specific improvements |

---

## 🏗️ Architecture

```text
YouTube Data API + YouTube Analytics API
                    │
                    ▼
          OAuth2 Authentication
                    │
                    ▼
     run_pipeline.py — ingestion pipeline
                    │
                    ▼
          SQLite analytics database
     ┌──────────────┼────────────────┐
     │              │                │
   videos      daily_metrics   traffic_sources
                    │
                    ▼
   features.py — deterministic pattern detection
     ├── best upload times
     ├── format performance
     ├── traffic-source distribution
     ├── weak engagement detection
     └── title-pattern analysis
                    │
                    ▼
 insights_engine.py — Llama via Groq
     ├── upload strategy
     ├── title ideas
     ├── next-video ideas
     ├── thumbnail recommendations
     ├── weak-video diagnosis
     └── full channel audit
                    │
                    ▼
          api.py — FastAPI backend
                    │
                    ▼
       React + Recharts frontend
```

### Key engineering decisions

- **Deterministic analysis first** — statistics are calculated with SQL, Pandas, and NumPy before any LLM call.
- **LLM as a strategist** — the model receives structured statistics instead of raw private analytics.
- **Structured JSON outputs** — prompts require predictable response schemas for reliable UI rendering.
- **SQLite AI cache** — generated recommendations are cached for 24 hours.
- **In-memory pattern cache** — repeated database calculations are cached for five minutes.
- **Containerized deployment** — frontend and backend run together through Docker.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| AI | Llama 3.3 70B via Groq |
| Backend | Python, FastAPI, Uvicorn |
| Machine Learning | scikit-learn `GradientBoostingClassifier` |
| Data Processing | Pandas, NumPy, SQL |
| Database | SQLite |
| Frontend | React, Recharts, Axios |
| Authentication | Google OAuth2 |
| Data Sources | YouTube Data API v3, YouTube Analytics API v2 |
| Infrastructure | Docker |

---

## 📊 Real Dataset

The application was tested on a real Shorts channel with:

- **395 analyzed Shorts**
- **36M+ total views**
- Daily performance metrics for each video
- Retention and subscriber data
- Traffic-source breakdowns
- Publication date and time
- Real video titles and metadata

Example patterns detected by the system:

- Friday was the strongest observed upload day
- 15:00 UTC was the strongest observed upload hour
- The Shorts feed generated approximately 95.5% of traffic
- Emoji titles were associated with stronger average performance

> These patterns represent correlations observed in this channel's historical data. They do not prove that a single feature directly caused higher performance.

> YouTube Shorts average view percentage can exceed 100% because videos may loop or be replayed.

---

## 🤖 Machine Learning

The ML component predicts a video's **7-day performance category**.

### Categories

| Category | 7-day views |
|---|---:|
| Low | Below 10,000 |
| Medium | 10,000–100,000 |
| High | 100,000–1,000,000 |
| Viral | Above 1,000,000 |

### Model details

| Property | Value |
|---|---|
| Algorithm | `GradientBoostingClassifier` |
| Validation | 5-fold cross-validation |
| Target | 7-day performance category |
| Output | Class prediction and probability per category |
| Explainability | Feature importance |

### Features

- Upload hour
- Day of the week
- Month
- Title length
- Title word count
- Emoji presence
- Exclamation mark presence
- Question mark presence
- Numbers in the title

The classifier is intended as a **decision-support signal**, not a guarantee of future views.

---

## 🧠 How the AI Layer Works

The LLM does not receive the complete raw analytics database.

### 1. Calculate patterns deterministically

```python
best_hour = hour_average_views.idxmax()
best_day = day_average_views.idxmax()
top_source = traffic_views.idxmax()
```

### 2. Send compact statistics to the model

```json
{
  "best_hour": 15,
  "best_day": "Friday",
  "top_traffic_source": "SHORTS",
  "top_traffic_percentage": 95.5
}
```

### 3. Receive structured recommendations

```json
{
  "optimal_schedule": "Publish on Friday around 15:00 UTC",
  "why_it_works": "This slot is associated with the strongest historical performance.",
  "action_items": [
    "Test the slot for the next three uploads",
    "Compare seven-day performance",
    "Keep the content format consistent during the experiment"
  ]
}
```

This architecture makes the AI layer:

- more predictable;
- more token-efficient;
- easier to cache;
- easier to validate;
- safer for private analytics data.

---

## 🚀 Quick Start with Docker

### Prerequisites

- Docker Desktop
- A Groq API key
- A prepared SQLite analytics database at `db/youtube_analytics.db`

### 1. Clone the repository

```bash
git clone https://github.com/katanna13/youtube-analytics.git
cd youtube-analytics
```

### 2. Create `.env`

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### 3. Build the image

```bash
docker build -t youtube-growth-copilot .
```

### 4. Run the application

```bash
docker run --rm \
  --name youtube-growth-copilot \
  -p 8000:8000 \
  -p 3000:3000 \
  --env-file .env \
  youtube-growth-copilot
```

Open:

- React application: `http://localhost:3000`
- FastAPI documentation: `http://localhost:8000/docs`
- Backend health response: `http://localhost:8000/`

---

## 💻 Run Without Docker

### Backend

```bash
pip install -r requirements.txt
python api.py
```

The backend runs at:

```text
http://localhost:8000
```

### Frontend

Open another terminal:

```bash
cd frontend
npm install
npm start
```

The frontend runs at:

```text
http://localhost:3000
```

---

## 📥 Import Your Own YouTube Data

### 1. Add Google OAuth credentials

Place your Google OAuth client file at:

```text
auth/client_secret.json
```

### 2. Run the ingestion pipeline

```bash
python run_pipeline.py
```

The pipeline:

1. retrieves every uploaded video using pagination;
2. downloads video metadata;
3. retrieves daily analytics;
4. retrieves traffic-source data;
5. writes the results to SQLite using idempotent upserts.

Authentication tokens and private credentials must never be committed.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API and active-model information |
| `GET` | `/patterns` | All deterministic channel patterns |
| `GET` | `/best-times` | Best observed days and hours |
| `GET` | `/analyze-channel` | Combined AI-powered channel analysis |
| `GET` | `/channel-audit` | Channel score, strengths, gaps, and actions |
| `GET` | `/next-video-ideas` | Five AI-generated content ideas |
| `GET` | `/ml-metrics` | Classifier accuracy, distribution, and feature importance |
| `POST` | `/ml-predict` | Predict a video's performance category |
| `POST` | `/generate-strategy` | Generate title and thumbnail recommendations |
| `POST` | `/thumbnail-from-title` | Generate a thumbnail concept for a title |
| `POST` | `/video/{video_id}/insights` | Diagnose a weak video |

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

---

## 📁 Project Structure

```text
youtube-analytics/
├── api.py
├── features.py
├── insights_engine.py
├── run_pipeline.py
├── requirements.txt
├── Dockerfile
├── start.sh
├── auth/
│   ├── authenticate.py
│   └── client_secret.json          # not committed
├── db/
│   ├── db.py
│   ├── schema.sql
│   └── youtube_analytics.db
└── frontend/
    ├── package.json
    └── src/
        ├── App.js
        ├── App.css
        ├── components/
        │   ├── Sidebar.js
        │   └── Sidebar.css
        ├── hooks/
        │   └── useApi.js
        └── pages/
            ├── Overview.js
            ├── BestTimes.js
            ├── MLPredictor.js
            ├── AIInsights.js
            └── ChannelAudit.js
```

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | API key used for Llama-powered recommendations |
| `GROQ_MODEL` | No | Groq model override; defaults to `llama-3.3-70b-versatile` |
| `REACT_APP_API_URL` | No | Backend URL; defaults to `http://localhost:8000` |

Example:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

---

<<<<<<< HEAD
=======
## 🔒 Security and Privacy

The repository must not contain:

- `.env`;
- Groq API keys;
- Google OAuth client secrets;
- OAuth token files;
- unsanitized private creator analytics.

The AI model receives calculated statistics and selected titles rather than the entire raw database.

---

## 🧪 Final Verification

```bash
docker build --no-cache -t youtube-growth-copilot .
docker run --rm \
  --name youtube-growth-copilot \
  -p 8000:8000 \
  -p 3000:3000 \
  --env-file .env \
  youtube-growth-copilot
```

Verify:

```text
http://localhost:3000
http://localhost:8000/
http://localhost:8000/docs
http://localhost:8000/patterns
http://localhost:8000/best-times
```

Then test at least one AI-powered operation from the frontend.

---

## 👤 Author

**Mihai Catana**

Built for the **AMD Developer Hackathon: ACT II — Track 3, Unicorn Track**.
>>>>>>> 653e971 (Finalize Groq integration and hackathon submission)
