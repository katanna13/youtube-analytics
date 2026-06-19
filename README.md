# 📊 YouTube Analytics Pipeline

An end-to-end YouTube analytics system that ingests real channel data via the YouTube API, stores it in a structured SQLite database, and surfaces actionable insights through an ML-powered Streamlit dashboard.

> **TL;DR:** OAuth2 → YouTube Data API + Analytics API → SQLite (star schema) → Streamlit dashboard with ML-based view prediction, automated insights, and data quality checks. Built on real channel data: **399 videos, 36M+ views, 17,000+ daily metric rows.**

---

## 🏗️ Architecture

```
YouTube Data API v3       YouTube Analytics API v2
        │                           │
        └───────────┬───────────────┘
                    │
               OAuth2 Auth
                    │
           pipeline/run_pipeline.py
                    │
       ┌────────────┼────────────┐
       │            │            │
    videos    daily_metrics  traffic_sources
       │            │            │
       └────────────┼────────────┘
               SQLite DB
            (star schema)
                    │
            dashboard.py
                    │
     ┌──────────────┼──────────────┐
     │              │              │
   KPIs         ML Model      Insights
Best Time     Predictor     Auto-generated
Correlations  Data Quality  CSV Export
```

---

## 📁 Project Structure

```
youtube-analytics/
├── auth/
│   ├── authenticate.py       # OAuth2 flow + token persistence
│   └── client_secret.json    # ⚠️ NOT committed — add your own
├── db/
│   ├── db.py                 # SQLite connection + upsert functions
│   ├── schema.sql            # Star schema definition
│   └── youtube_analytics.db  # ⚠️ NOT committed — generated locally
├── pipeline/
│   ├── run_pipeline.py       # Main ingestion pipeline
│   ├── test_fetch.py         # YouTube Data API connection test
│   └── test_analytics.py     # YouTube Analytics API test
├── dashboard.py              # Streamlit analytics dashboard
├── Dockerfile
├── requirements.txt
└── .gitignore
```

---

## ⚙️ Data Pipeline

### Ingestion (`run_pipeline.py`)
```
Channel ID
  → uploads playlist (paginated — no 50-video limit)
  → video metadata (title, duration, published_at, is_short)
  → daily metrics per video (views, watch time, retention, subscribers)
  → traffic sources per video (SEARCH, SUGGESTED, SHORTS, etc.)
  → SQLite upsert (idempotent — safe to re-run anytime)
```

**Quota:** ~2 Analytics API units/video × 399 videos ≈ 800 units/day (default quota: 10,000).

### Database Schema (Star Schema)
```sql
videos          — dimension table (video metadata)
daily_metrics   — fact table (time-series, UNIQUE on video_id + date)
traffic_sources — fact table (aggregated, UNIQUE on video_id + source_type)
```

---

## 📊 Dashboard Features

| Section | Description |
|---------|-------------|
| **KPIs** | Views, watch hours, net subscribers, avg retention — filterable by period |
| **Daily Views** | Area chart with period filter (30/90/365 days) |
| **Traffic Sources** | Pie chart: SHORTS, SEARCH, SUGGESTED, SUBSCRIBER, etc. |
| **Top Videos** | Table with views, watch hours, retention, Short/Long label |
| **Shorts vs Long-form** | Side-by-side daily views comparison |
| **Retention Distribution** | Histogram of avg view % across all videos |
| **⏰ Best Time to Post** | Avg views by day of week and upload hour |
| **🔗 Correlations** | Duration vs Views, Title Length vs Views (OLS trendlines) |
| **🤖 ML Predictor** | Gradient Boosting model — predict 7-day views for your next video |
| **🔍 Data Quality** | Duplicate checks, missing IDs, latest ingestion timestamp |
| **💡 Auto Insights** | Channel-level insights generated automatically from real data |
| **📥 CSV Export** | Download videos, daily metrics, traffic sources as CSV |

---

## 🤖 ML Model

**Algorithm:** Gradient Boosting Regressor (scikit-learn)

**Features:**
- `duration_seconds`, `is_short`
- `hour`, `day_of_week`, `month` (upload timing)
- `title_length`, `has_emoji`, `has_exclamation`, `has_question`

**Target:** `log(views in first 7 days)`

**Validation:** 5-fold cross-validation with R², RMSE, MAE and baseline comparison

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Google API credentials
- Create a project at [Google Cloud Console](https://console.cloud.google.com)
- Enable **YouTube Data API v3** and **YouTube Analytics API**
- Download OAuth2 credentials → save as `auth/client_secret.json`

### 3. Run the ingestion pipeline
```bash
python pipeline/run_pipeline.py
```
First run opens a browser for OAuth2 authentication. Token is saved locally for future runs.

### 4. Launch the dashboard
```bash
streamlit run dashboard.py
```

### 5. Or run with Docker
```bash
docker build -t youtube-analytics .
docker run -p 8501:8501 youtube-analytics
```

---

## 🧱 Tech Stack

| Layer | Technology | Role |
|-------|------------|------|
| Auth | Google OAuth2 | API authentication + token persistence |
| Ingestion | YouTube Data API v3 | Video metadata, channel info |
| Analytics | YouTube Analytics API v2 | Daily metrics, traffic sources |
| Storage | SQLite | Star schema, idempotent upsert |
| ML | scikit-learn (GradientBoosting) | View count prediction |
| Dashboard | Streamlit + Plotly | Interactive analytics UI |
| Deployment | Docker | Containerized, reproducible environment |

---

## ⚖️ Design Tradeoffs

| Decision | Reason |
|----------|--------|
| SQLite over cloud DB | Zero infrastructure, portable, sufficient for single-channel scale |
| Idempotent upsert | Pipeline is safe to re-run without duplicates |
| Star schema | Enables fast aggregation queries for the dashboard |
| Log-transform on target | Reduces skew in view distribution for better ML fit |
| 2-day analytics delay | YouTube Analytics has ~48h processing delay — accounted for in pipeline |

---

## 📌 Future Improvements

- Automated daily ingestion via scheduler (cron / GitHub Actions)
- Thumbnail feature extraction (color, face detection) for ML
- Multi-channel support
- CTR and impressions data (requires additional API scopes)
- Cloud deployment (Streamlit Cloud / Railway)
