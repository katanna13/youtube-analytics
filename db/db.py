"""
Conexiune SQLite + funcții de upsert pentru schema YouTube Analytics.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_analytics.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Creează tabelele dacă nu există deja (idempotent)."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Baza de date inițializată la: {DB_PATH}")


def upsert_video(conn, video):
    """
    video = dict cu cheile: video_id, channel_id, title, description,
            published_at, duration_seconds, category_id, thumbnail_url, is_short
    """
    conn.execute("""
        INSERT INTO videos (video_id, channel_id, title, description, published_at,
                             duration_seconds, category_id, thumbnail_url, is_short, updated_at)
        VALUES (:video_id, :channel_id, :title, :description, :published_at,
                :duration_seconds, :category_id, :thumbnail_url, :is_short, datetime('now'))
        ON CONFLICT(video_id) DO UPDATE SET
            title = excluded.title,
            description = excluded.description,
            duration_seconds = excluded.duration_seconds,
            category_id = excluded.category_id,
            thumbnail_url = excluded.thumbnail_url,
            is_short = excluded.is_short,
            updated_at = datetime('now')
    """, video)


def upsert_daily_metric(conn, metric):
    """
    metric = dict cu cheile: video_id, date, views, estimated_minutes_watched,
             average_view_duration, average_view_percentage,
             subscribers_gained, subscribers_lost
    """
    conn.execute("""
        INSERT INTO daily_metrics (video_id, date, views, estimated_minutes_watched,
                                    average_view_duration, average_view_percentage,
                                    subscribers_gained, subscribers_lost, fetched_at)
        VALUES (:video_id, :date, :views, :estimated_minutes_watched,
                :average_view_duration, :average_view_percentage,
                :subscribers_gained, :subscribers_lost, datetime('now'))
        ON CONFLICT(video_id, date) DO UPDATE SET
            views = excluded.views,
            estimated_minutes_watched = excluded.estimated_minutes_watched,
            average_view_duration = excluded.average_view_duration,
            average_view_percentage = excluded.average_view_percentage,
            subscribers_gained = excluded.subscribers_gained,
            subscribers_lost = excluded.subscribers_lost,
            fetched_at = datetime('now')
    """, metric)


def upsert_traffic_source(conn, traffic):
    """
    traffic = dict cu cheile: video_id, traffic_source_type, views, estimated_minutes_watched
    """
    conn.execute("""
        INSERT INTO traffic_sources (video_id, traffic_source_type, views, estimated_minutes_watched, fetched_at)
        VALUES (:video_id, :traffic_source_type, :views, :estimated_minutes_watched, datetime('now'))
        ON CONFLICT(video_id, traffic_source_type) DO UPDATE SET
            views = excluded.views,
            estimated_minutes_watched = excluded.estimated_minutes_watched,
            fetched_at = datetime('now')
    """, traffic)


if __name__ == "__main__":
    init_db()
