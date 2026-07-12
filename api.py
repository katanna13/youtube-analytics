"""
api.py — FastAPI layer pentru YouTube Growth Copilot
Expune endpoints pentru pattern detection, ML predictions si AI insights.
"""

# ── 1. Imports ────────────────────────────────────────────────────────────────
import os
import sqlite3
import time
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn.metrics import accuracy_score

from features import get_all_patterns, get_best_upload_times
from insights_engine import (
    get_upload_strategy,
    get_title_ideas,
    analyze_weak_video,
    get_thumbnail_recommendations,
    get_channel_audit,
    get_full_insights,
    get_next_video_ideas,
    get_thumbnail_from_title,
)

# ── 2. App + CORS ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="YouTube Growth Copilot API",
    description="AI-powered YouTube channel analysis using Gemma 4 via Fireworks AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 3. Config ─────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "youtube_analytics.db")

FEATURES = [
    "hour", "day_of_week", "month", "title_length",
    "has_emoji", "has_exclamation", "has_question",
    "title_word_count", "title_has_numbers"
]

# Categorii de performanta bazate pe distributia reala a canalului
CATEGORIES = ["Low (<10K)", "Medium (10K-100K)", "High (100K-1M)", "Viral (1M+)"]


def classify_views(views):
    """Clasifică views în 4 categorii de performanță."""
    if views < 10_000: return 0
    if views < 100_000: return 1
    if views < 1_000_000: return 2
    return 3


# ── 4. Cache in-memory ────────────────────────────────────────────────────────
_patterns_cache = None
_patterns_cache_time = 0
PATTERNS_TTL = 300


def get_cached_patterns() -> dict:
    global _patterns_cache, _patterns_cache_time
    now = time.time()
    if _patterns_cache is None or (now - _patterns_cache_time) > PATTERNS_TTL:
        _patterns_cache = get_all_patterns()
        _patterns_cache_time = now
    return _patterns_cache


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def build_ml_dataframe():
    """Construieste DataFrame-ul pentru ML din SQLite."""
    conn = get_db_conn()
    first7 = pd.read_sql("""
        SELECT d.video_id,
               SUM(CASE WHEN julianday(d.date) - julianday(v.published_at) <= 7
                        THEN d.views ELSE 0 END) as views_7d,
               SUM(d.views) as total_views
        FROM daily_metrics d
        JOIN videos v ON d.video_id = v.video_id
        GROUP BY d.video_id
        HAVING total_views > 0
    """, conn)
    vids = pd.read_sql("""
        SELECT video_id, title, published_at, duration_seconds, is_short
        FROM videos
    """, conn)
    conn.close()

    df = vids.merge(first7, on="video_id")
    df["published_at"] = pd.to_datetime(df["published_at"])
    df["hour"] = df["published_at"].dt.hour
    df["day_of_week"] = df["published_at"].dt.dayofweek
    df["month"] = df["published_at"].dt.month
    df["title_length"] = df["title"].str.len()
    df["has_emoji"] = df["title"].str.contains(r'[^\x00-\x7F]', regex=True).astype(int)
    df["has_exclamation"] = df["title"].str.contains("!").astype(int)
    df["has_question"] = df["title"].str.contains(r'\?').astype(int)
    df["title_word_count"] = df["title"].str.split().str.len()
    df["title_has_numbers"] = df["title"].str.contains(r'\d').astype(int)
    df["category"] = df["views_7d"].apply(classify_views)

    return df.dropna(subset=FEATURES + ["views_7d"])


# ── 5. Pydantic Models ────────────────────────────────────────────────────────
class VideoAnalysisRequest(BaseModel):
    video_id: str
    title: str
    retention: float
    views: int


class TitleIdeasRequest(BaseModel):
    topic: Optional[str] = ""


class ThumbnailFromTitleRequest(BaseModel):
    title: str


class MLPredictRequest(BaseModel):
    hour: int
    day_of_week: int
    month: int
    title_length: int
    has_emoji: int
    has_exclamation: int
    has_question: int
    title_word_count: int
    title_has_numbers: int


# ── 6. Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "YouTube Growth Copilot API",
        "version": "1.0.0",
        "provider": "Groq",
        "model": "llama-3.3-70b-versatile",
    }

@app.get("/patterns")
def get_patterns():
    try:
        return {"status": "ok", "data": get_cached_patterns()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/best-times")
def get_best_times():
    try:
        return {"status": "ok", "data": get_best_upload_times()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze-channel")
def analyze_channel(topic: Optional[str] = Query(default="")):
    try:
        patterns = get_cached_patterns()
        insights = get_full_insights(patterns, topic=topic)
        return {"status": "ok", "patterns": patterns, "insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/video/{video_id}/insights")
def video_insights(video_id: str, body: VideoAnalysisRequest):
    try:
        patterns = get_cached_patterns()
        analysis = analyze_weak_video(
            patterns=patterns,
            video_title=body.title,
            retention=body.retention,
            views=body.views,
        )
        return {"status": "ok", "video_id": video_id, "analysis": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-strategy")
def generate_strategy(body: TitleIdeasRequest):
    try:
        patterns = get_cached_patterns()
        title_ideas = get_title_ideas(patterns, topic=body.topic)
        thumbnail = get_thumbnail_recommendations(patterns)
        return {"status": "ok", "title_ideas": title_ideas, "thumbnail_recommendations": thumbnail}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/channel-audit")
def channel_audit():
    try:
        patterns = get_cached_patterns()
        audit = get_channel_audit(patterns)
        return {"status": "ok", "audit": audit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/next-video-ideas")
def next_video_ideas():
    try:
        conn = get_db_conn()
        top_videos = pd.read_sql("""
            SELECT v.title, SUM(d.views) as total_views
            FROM videos v
            JOIN daily_metrics d ON v.video_id = d.video_id
            GROUP BY v.video_id
            ORDER BY total_views DESC
            LIMIT 20
        """, conn)
        conn.close()

        top_titles = top_videos["title"].tolist()
        patterns = get_cached_patterns()
        ideas = get_next_video_ideas(top_titles, patterns)
        return {"status": "ok", "top_titles": top_titles[:10], "ideas": ideas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/thumbnail-from-title")
def thumbnail_from_title(body: ThumbnailFromTitleRequest):
    try:
        conn = get_db_conn()
        top_videos = pd.read_sql("""
            SELECT v.title, SUM(d.views) as total_views
            FROM videos v
            JOIN daily_metrics d ON v.video_id = d.video_id
            GROUP BY v.video_id
            ORDER BY total_views DESC
            LIMIT 10
        """, conn)
        conn.close()

        top_titles = top_videos["title"].tolist()
        patterns = get_cached_patterns()
        thumb = get_thumbnail_from_title(body.title, top_titles, patterns)
        return {"status": "ok", "title": body.title, "thumbnail": thumb}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ml-predict")
def ml_predict(body: MLPredictRequest):
    """
    Clasificator GradientBoosting — prezice categoria de performanta:
    Low (<10K) / Medium (10K-100K) / High (100K-1M) / Viral (1M+)
    """
    try:
        df = build_ml_dataframe()
        X = df[FEATURES]
        y = df["category"]

        model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
        model.fit(X, y)

        X_pred = pd.DataFrame([{
            "hour": body.hour,
            "day_of_week": body.day_of_week,
            "month": body.month,
            "title_length": body.title_length,
            "has_emoji": body.has_emoji,
            "has_exclamation": body.has_exclamation,
            "has_question": body.has_question,
            "title_word_count": body.title_word_count,
            "title_has_numbers": body.title_has_numbers,
        }])

        predicted_class = int(model.predict(X_pred)[0])
        probabilities = model.predict_proba(X_pred)[0].tolist()
        importance = dict(zip(FEATURES, model.feature_importances_.tolist()))

        return {
            "status": "ok",
            "predicted_category": CATEGORIES[predicted_class],
            "predicted_class": predicted_class,
            "probabilities": {CATEGORIES[i]: round(p * 100, 1) for i, p in enumerate(probabilities)},
            "feature_importance": importance,
            "model": "GradientBoostingClassifier",
            "trained_on": len(df),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ml-metrics")
def ml_metrics():
    """Returneaza metricile clasificatorului (accuracy, distribution)."""
    try:
        df = build_ml_dataframe()
        X = df[FEATURES]
        y = df["category"]

        model = GradientBoostingClassifier(n_estimators=100, max_depth=4, random_state=42)
        y_pred = cross_val_predict(model, X, y, cv=5)
        accuracy = float(accuracy_score(y, y_pred))

        model.fit(X, y)
        importance = dict(zip(FEATURES, model.feature_importances_.tolist()))

        # Distributia categoriilor
        distribution = {
            CATEGORIES[i]: int((y == i).sum())
            for i in range(4)
        }

        return {
            "status": "ok",
            "accuracy": accuracy,
            "distribution": distribution,
            "feature_importance": importance,
            "trained_on": len(df),
            "categories": CATEGORIES,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 7. Start ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
