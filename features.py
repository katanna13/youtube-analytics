"""
features.py — Pattern detection din datele reale YouTube
Citește din SQLite și calculează patterns cu math real.
Output: dict structurat pentru insights_engine.py
"""

import sqlite3
import pandas as pd
import numpy as np
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "youtube_analytics.db")

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── 1. Best Upload Times ─────────────────────────────────────────────────────
def get_best_upload_times() -> dict:
    """
    Calculează cele mai bune ore și zile pentru upload.
    Logică: group by hour/day → avg views per video → argmax
    """
    conn = get_connection()

    # Views totale per video
    total_views = pd.read_sql("""
        SELECT video_id, SUM(views) as total_views
        FROM daily_metrics
        GROUP BY video_id
    """, conn)

    # Metadata video cu ora și ziua publicării
    videos = pd.read_sql("""
        SELECT video_id, published_at
        FROM videos
    """, conn)

    conn.close()

    df = videos.merge(total_views, on="video_id")
    df["published_at"] = pd.to_datetime(df["published_at"])
    df["hour"] = df["published_at"].dt.hour
    df["day"] = df["published_at"].dt.day_name()

    # Avg views per hour
    hour_avg = df.groupby("hour")["total_views"].mean()
    best_hour = int(hour_avg.idxmax())
    worst_hour = int(hour_avg.idxmin())

    # Avg views per day
    day_avg = df.groupby("day")["total_views"].mean().reindex(DAY_ORDER)
    best_day = day_avg.idxmax()
    worst_day = day_avg.idxmin()

    # Top 3 ore
    top_hours = hour_avg.nlargest(3).index.tolist()

    return {
        "best_hour": best_hour,
        "worst_hour": worst_hour,
        "best_day": best_day,
        "worst_day": worst_day,
        "top_3_hours": top_hours,
        "best_hour_avg_views": int(hour_avg[best_hour]),
        "best_day_avg_views": int(day_avg[best_day]),
        "hour_data": hour_avg.to_dict(),
        "day_data": day_avg.to_dict(),
    }


# ── 2. Video Length Patterns ──────────────────────────────────────────────────
def get_video_length_patterns() -> dict:
    """
    Calculează performanța Shorts vs Long-form.
    Logică: avg views per video pentru is_short=1 vs is_short=0
    """
    conn = get_connection()

    total_views = pd.read_sql("""
        SELECT video_id, SUM(views) as total_views
        FROM daily_metrics
        GROUP BY video_id
    """, conn)

    videos = pd.read_sql("""
        SELECT video_id, duration_seconds, is_short
        FROM videos
    """, conn)

    conn.close()

    df = videos.merge(total_views, on="video_id")

    shorts = df[df["is_short"] == 1]["total_views"]
    longs = df[df["is_short"] == 0]["total_views"]

    avg_shorts = float(shorts.mean()) if len(shorts) > 0 else 0
    avg_longs = float(longs.mean()) if len(longs) > 0 else 0

    # Multiplier: de câte ori sunt Shorts mai bune decât Long-form sau invers
    if avg_longs > 0:
        multiplier = avg_shorts / avg_longs
    else:
        multiplier = 1.0

    better_format = "Shorts" if avg_shorts > avg_longs else "Long-form"

    return {
        "avg_views_shorts": int(avg_shorts),
        "avg_views_longform": int(avg_longs),
        "better_format": better_format,
        "multiplier": round(multiplier, 2),
        "total_shorts": len(shorts),
        "total_longform": len(longs),
        "shorts_total_views": int(shorts.sum()),
        "longform_total_views": int(longs.sum()),
    }


# ── 3. Traffic Source Patterns ────────────────────────────────────────────────
def get_traffic_patterns() -> dict:
    """
    Calculează top traffic sources și distribuția lor.
    Logică: group by traffic_source_type → sum views → sort desc
    """
    conn = get_connection()

    traffic = pd.read_sql("""
        SELECT traffic_source_type, SUM(views) as total_views
        FROM traffic_sources
        GROUP BY traffic_source_type
        ORDER BY total_views DESC
    """, conn)

    conn.close()

    total = traffic["total_views"].sum()
    traffic["percentage"] = (traffic["total_views"] / total * 100).round(1)

    top_source = traffic.iloc[0]["traffic_source_type"]
    top_source_pct = traffic.iloc[0]["percentage"]

    return {
        "top_source": top_source,
        "top_source_percentage": float(top_source_pct),
        "sources": traffic.set_index("traffic_source_type")[["total_views", "percentage"]].to_dict("index"),
        "top_3_sources": traffic.head(3)["traffic_source_type"].tolist(),
    }


# ── 4. Weak Engagement Videos ─────────────────────────────────────────────────
def get_weak_engagement_videos(n: int = 5) -> dict:
    """
    Găsește videouri cu engagement slab față de media canalului.
    Logică: avg_view_percentage sub media canalului → candidate pentru analiză
    """
    conn = get_connection()

    engagement = pd.read_sql("""
        SELECT d.video_id, v.title,
               AVG(d.average_view_percentage) as avg_retention,
               SUM(d.views) as total_views,
               SUM(d.subscribers_gained) - SUM(d.subscribers_lost) as net_subs
        FROM daily_metrics d
        JOIN videos v ON d.video_id = v.video_id
        WHERE d.average_view_percentage > 0
        GROUP BY d.video_id
        HAVING total_views > 100
    """, conn)

    conn.close()

    channel_avg_retention = float(engagement["avg_retention"].mean())
    channel_avg_views = float(engagement["total_views"].mean())

    # Videouri cu retention sub medie
    weak = engagement[
        engagement["avg_retention"] < channel_avg_retention
    ].nsmallest(n, "avg_retention")

    weak_list = []
    for _, row in weak.iterrows():
        weak_list.append({
            "video_id": row["video_id"],
            "title": row["title"][:60],
            "avg_retention": round(float(row["avg_retention"]), 1),
            "total_views": int(row["total_views"]),
            "net_subs": int(row["net_subs"]),
            "below_avg_by": round(channel_avg_retention - float(row["avg_retention"]), 1),
        })

    return {
        "channel_avg_retention": round(channel_avg_retention, 1),
        "channel_avg_views": int(channel_avg_views),
        "weak_videos": weak_list,
        "total_weak_count": len(engagement[engagement["avg_retention"] < channel_avg_retention]),
    }


# ── 5. Title Patterns ─────────────────────────────────────────────────────────
def get_title_patterns() -> dict:
    """
    Analizează ce caracteristici din titluri corelează cu views mari.
    Logică: compară avg views pentru titluri cu/fără emoji, !, ?, lungime
    """
    conn = get_connection()

    total_views = pd.read_sql("""
        SELECT video_id, SUM(views) as total_views
        FROM daily_metrics
        GROUP BY video_id
    """, conn)

    videos = pd.read_sql("""
        SELECT video_id, title
        FROM videos
    """, conn)

    conn.close()

    df = videos.merge(total_views, on="video_id")

    # Features din titlu
    df["has_emoji"] = df["title"].str.contains(r'[^\x00-\x7F]', regex=True)
    df["has_exclamation"] = df["title"].str.contains("!")
    df["has_question"] = df["title"].str.contains(r'\?', regex=True)
    df["title_length"] = df["title"].str.len()
    df["title_length_bucket"] = pd.cut(df["title_length"],
                                        bins=[0, 30, 50, 70, 200],
                                        labels=["short", "medium", "long", "very_long"])

    # Avg views per feature
    emoji_boost = df.groupby("has_emoji")["total_views"].mean()
    excl_boost = df.groupby("has_exclamation")["total_views"].mean()
    length_avg = df.groupby("title_length_bucket", observed=True)["total_views"].mean()

    best_length = str(length_avg.idxmax())

    return {
        "emoji_helps": bool(emoji_boost.get(True, 0) > emoji_boost.get(False, 0)),
        "avg_views_with_emoji": int(emoji_boost.get(True, 0)),
        "avg_views_without_emoji": int(emoji_boost.get(False, 0)),
        "exclamation_helps": bool(excl_boost.get(True, 0) > excl_boost.get(False, 0)),
        "avg_views_with_exclamation": int(excl_boost.get(True, 0)),
        "avg_views_without_exclamation": int(excl_boost.get(False, 0)),
        "best_title_length_bucket": best_length,
        "length_performance": {str(k): int(v) for k, v in length_avg.items()},
        "avg_title_length": round(float(df["title_length"].mean()), 1),
    }


# ── Master function ───────────────────────────────────────────────────────────
def get_all_patterns() -> dict:
    """
    Rulează toate funcțiile și returnează un dict complet.
    Acesta e input-ul pentru insights_engine.py (Gemma 4).
    """
    return {
        "upload_times": get_best_upload_times(),
        "video_length": get_video_length_patterns(),
        "traffic": get_traffic_patterns(),
        "weak_engagement": get_weak_engagement_videos(),
        "title_patterns": get_title_patterns(),
    }


if __name__ == "__main__":
    import json
    patterns = get_all_patterns()
    print(json.dumps(patterns, indent=2, default=str))