-- Schema pentru YouTube Analytics Pipeline
-- Design: star schema simplu - 1 tabel dimensiune (videos) + 2 tabele de fapte (time-series)

CREATE TABLE IF NOT EXISTS videos (
    video_id            TEXT PRIMARY KEY,
    channel_id           TEXT NOT NULL,
    title                TEXT,
    description          TEXT,
    published_at         TEXT NOT NULL,   -- ISO 8601, ex: 2026-01-18T16:30:17Z
    duration_seconds      INTEGER,
    category_id          TEXT,
    thumbnail_url         TEXT,
    is_short             INTEGER DEFAULT 0,  -- 1/0, dedus din durata sau titlu
    created_at           TEXT DEFAULT (datetime('now')),
    updated_at           TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS daily_metrics (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id                 TEXT NOT NULL,
    date                     TEXT NOT NULL,   -- YYYY-MM-DD
    views                    INTEGER DEFAULT 0,
    estimated_minutes_watched INTEGER DEFAULT 0,
    average_view_duration     INTEGER DEFAULT 0,   -- secunde
    average_view_percentage   REAL DEFAULT 0,
    subscribers_gained        INTEGER DEFAULT 0,
    subscribers_lost          INTEGER DEFAULT 0,
    fetched_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    UNIQUE (video_id, date)
);

CREATE TABLE IF NOT EXISTS traffic_sources (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id                 TEXT NOT NULL,
    traffic_source_type       TEXT NOT NULL,   -- SEARCH, SUGGESTED, EXTERNAL, etc.
    views                    INTEGER DEFAULT 0,
    estimated_minutes_watched INTEGER DEFAULT 0,
    fetched_at               TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    UNIQUE (video_id, traffic_source_type)
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_video_date ON daily_metrics(video_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date);
CREATE INDEX IF NOT EXISTS idx_traffic_sources_video ON traffic_sources(video_id);
CREATE INDEX IF NOT EXISTS idx_videos_published ON videos(published_at);
