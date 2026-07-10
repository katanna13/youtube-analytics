# ▶ YouTube Growth Copilot

> AI-powered YouTube channel analysis that turns real channel data into actionable growth strategies — powered by Gemma 4 via Fireworks AI on AMD infrastructure.



---

## 🎯 What It Does

Most YouTube creators post blindly — no idea when to upload, what titles work, or why some videos flop. YouTube Growth Copilot analyzes your real channel data and generates specific, data-backed growth strategies using Gemma 4.

**Real data. Real insights. No guessing.**

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Channel Overview** | Traffic sources, format performance, weak videos |
| ⏰ **Best Times** | Best day/hour to post based on your actual views |
| 🤖 **ML Predictor** | GradientBoosting model predicts 7-day views (37% RMSE improvement) |
| 🎬 **Next Video Ideas** | Gemma 4 analyzes your top titles and generates 5 video ideas |
| 🖼️ **Thumbnail Generator** | Enter a title → get specific thumbnail recommendations |
| ⏰ **Upload Strategy** | AI-generated posting schedule based on your data |
| 📈 **Channel Audit** | Full audit with score, strengths, growth gaps, top 3 actions |
| ⚠️ **Weak Video Analysis** | Find out why a specific video underperformed |

---

## 🏗️ Architecture

```
YouTube Data API + Analytics API
        ↓
OAuth2 Authentication
        ↓
run_pipeline.py — ingestion pipeline
        ↓
SQLite Star Schema (3 tables)
        ↓
features.py — deterministic pattern detection
  ├── get_best_upload_times()
  ├── get_video_length_patterns()
  ├── get_traffic_patterns()
  ├── get_weak_engagement_videos()
  └── get_title_patterns()
        ↓
insights_engine.py — Gemma 4 via Fireworks AI
  ├── get_upload_strategy()
  ├── get_title_ideas()
  ├── get_next_video_ideas()
  ├── get_thumbnail_from_title()
  ├── analyze_weak_video()
  └── get_channel_audit()
        ↓
api.py — FastAPI (10 endpoints)
        ↓
React Frontend — YouTube-themed UI
```

**Key engineering decisions:**
- **Deterministic first** — patterns calculated with real math before any LLM call
- **LLM as explainer** — Gemma 4 receives computed statistics, not raw data
- **SQLite cache** — AI responses cached for 24h (saves tokens)
- **In-memory cache** — patterns cached for 5 minutes (saves DB reads)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| AI Model | Gemma 4 26B A4B via Fireworks AI (AMD hardware) |
| Backend | Python, FastAPI, uvicorn |
| ML | scikit-learn GradientBoostingRegressor |
| Data | SQLite star schema, Pandas |
| Frontend | React, Recharts, Axios |
| Infrastructure | Docker, AMD Developer Cloud |
| Data Source | YouTube Data API v3, YouTube Analytics API v2 |

---

## 🚀 Quick Start

### Prerequisites
- Docker
- Fireworks AI API key
- YouTube channel with OAuth2 credentials (optional — demo data included)

### Run with Docker

```bash
# Clone the repo
git clone https://github.com/katanna13/youtube-analytics
cd youtube-analytics

# Run with your Fireworks API key
docker run -p 8000:8000 -p 3000:3000 \
  -e FIREWORKS_API_KEY=your_key_here \
  youtube-growth-copilot
```

Open `http://localhost:3000` for the React UI.
Open `http://localhost:8000/docs` for the API docs.

### Run without Docker

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
cd frontend && npm install && cd ..

# Add your Fireworks API key
echo "FIREWORKS_API_KEY=your_key_here" > .env

# Start backend
python api.py

# Start frontend (new terminal)
cd frontend && npm start
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/patterns` | All patterns from SQLite (no AI) |
| GET | `/best-times` | Best upload hours and days |
| GET | `/analyze-channel` | Full AI analysis via Gemma 4 |
| GET | `/channel-audit` | Channel score + growth gaps |
| GET | `/next-video-ideas` | 5 video ideas based on your top titles |
| GET | `/ml-metrics` | R², RMSE, model performance |
| POST | `/ml-predict` | Predict 7-day views for a video |
| POST | `/generate-strategy` | Title ideas + thumbnail tips |
| POST | `/thumbnail-from-title` | Thumbnail recommendations for a title |
| POST | `/video/{id}/insights` | Analyze why a video underperformed |

Full docs at `http://localhost:8000/docs`

---

## 📊 Dataset

Real YouTube channel data:
- **399 videos**
- **36.5M+ total views**
- **Daily metrics** per video since publication
- **Traffic sources** breakdown

---

## 🧠 How the AI Works

Instead of sending raw data to Gemma 4, the system:

1. **Calculates patterns first** (math, no AI)
   ```
   short_videos_multiplier = avg_views_shorts / avg_views_longform
   best_hour = argmax(avg_views_per_hour)
   ```

2. **Sends only statistics to Gemma 4**
   ```json
   {
     "best_hour": 18,
     "best_day": "Friday",
     "short_videos_multiplier": 2.3
   }
   ```

3. **Gets structured JSON back**
   ```json
   {
     "optimal_schedule": "Post Shorts on Friday at 18:00 UTC",
     "why_it_works": "...",
     "action_items": ["...", "...", "..."]
   }
   ```

This makes outputs **predictable**, **fast**, and **token-efficient**.

---

## 🏆 ML Model Performance

| Metric | Value |
|---|---|
| Algorithm | GradientBoostingRegressor |
| Target | Views in first 7 days |
| Validation | 5-fold cross-validation |
| RMSE improvement | **37% vs median baseline** |
| Features | Duration, upload time, title length, emoji, format |

---

## 📁 Project Structure

```
youtube-analytics/
├── api.py                  # FastAPI — 10 endpoints
├── features.py             # Pattern detection (deterministic)
├── insights_engine.py      # Gemma 4 integration + SQLite cache
├── run_pipeline.py         # YouTube API ingestion
├── auth/
│   └── authenticate.py     # OAuth2
├── db/
│   ├── db.py               # SQLite upsert functions
│   ├── schema.sql          # Star schema
│   └── youtube_analytics.db
├── frontend/
│   └── src/
│       ├── App.js
│       ├── components/Sidebar.js
│       ├── hooks/useApi.js
│       └── pages/
│           ├── Overview.js
│           ├── BestTimes.js
│           ├── MLPredictor.js
│           ├── AIInsights.js
│           └── ChannelAudit.js
├── Dockerfile
├── start.sh
├── requirements.txt
└── .env                    # FIREWORKS_API_KEY (not committed)
```

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `FIREWORKS_API_KEY` | Fireworks AI API key for Gemma 4 |
| `REACT_APP_API_URL` | Backend URL (default: `http://localhost:8000`) |

---

