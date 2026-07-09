"""
insights_engine.py — AI Decision Engine cu Gemma 4 via Fireworks AI
Primește patterns calculate din features.py și generează insights acționabile.
"""

import os
import json
import hashlib
import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
FIREWORKS_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
MODEL = "accounts/fireworks/models/gemma-4-26b-a4b-it"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "youtube_analytics.db")
CACHE_TTL_HOURS = 24


# ── Cache SQLite ──────────────────────────────────────────────────────────────
def _get_cache_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_cache (
            cache_key   TEXT PRIMARY KEY,
            response    TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def _cache_get(key: str):
    """Returnează răspunsul din cache dacă e valid (sub 24h), altfel None."""
    conn = _get_cache_conn()
    row = conn.execute("""
        SELECT response, created_at FROM ai_cache
        WHERE cache_key = ?
    """, (key,)).fetchone()
    conn.close()

    if not row:
        return None

    created = datetime.fromisoformat(row[1])
    age_hours = (datetime.now() - created).total_seconds() / 3600

    if age_hours > CACHE_TTL_HOURS:
        return None

    return json.loads(row[0])


def _cache_set(key: str, response: dict):
    """Salvează răspunsul în cache."""
    conn = _get_cache_conn()
    conn.execute("""
        INSERT OR REPLACE INTO ai_cache (cache_key, response, created_at)
        VALUES (?, ?, datetime('now'))
    """, (key, json.dumps(response)))
    conn.commit()
    conn.close()


def _make_cache_key(patterns: dict, insight_type: str) -> str:
    """Generează un cache key unic din patterns + tipul de insight."""
    content = json.dumps(patterns, sort_keys=True) + insight_type
    return hashlib.md5(content.encode()).hexdigest()


# ── Fireworks API Call ────────────────────────────────────────────────────────
def _call_gemma(prompt: str) -> str:
    """Apelează Gemma 4 via Fireworks AI și returnează textul răspunsului."""
    headers = {
        "Authorization": f"Bearer {FIREWORKS_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a YouTube growth strategist AI. "
                    "You analyze real channel data and provide specific, actionable insights. "
                    "Always respond with valid JSON only. No markdown, no explanation outside JSON."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 600,
        "temperature": 0.3,
    }

    response = requests.post(FIREWORKS_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


def _parse_json_response(raw: str) -> dict:
    """Parsează răspunsul JSON de la Gemma 4, robust la erori."""
    try:
        # Curăță markdown dacă există
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        return {"error": "Could not parse AI response", "raw": raw[:200]}


# ── 1. Best Upload Strategy ───────────────────────────────────────────────────
def get_upload_strategy(patterns: dict) -> dict:
    """
    Generează strategia optimă de upload bazată pe ore și zile.
    Input: patterns["upload_times"]
    """
    cache_key = _make_cache_key(patterns.get("upload_times", {}), "upload_strategy")
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    ut = patterns["upload_times"]

    prompt = f"""
Analyze this YouTube channel's upload timing data and provide a growth strategy.

Channel timing data:
- Best upload hour: {ut['best_hour']}:00 UTC ({ut['best_hour_avg_views']:,} avg views)
- Worst upload hour: {ut['worst_hour']}:00 UTC
- Best upload day: {ut['best_day']} ({ut['best_day_avg_views']:,} avg views)
- Worst upload day: {ut['worst_day']}
- Top 3 hours: {ut['top_3_hours']}

Respond with this exact JSON structure:
{{
  "optimal_schedule": "specific day and time recommendation",
  "why_it_works": "1-2 sentences explaining the pattern",
  "avoid": "what to avoid and why",
  "action_items": ["action 1", "action 2", "action 3"]
}}
"""

    raw = _call_gemma(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 2. Title Ideas ────────────────────────────────────────────────────────────
def get_title_ideas(patterns: dict, topic: str = "") -> dict:
    """
    Generează idei de titluri bazate pe pattern-urile canalului.
    Input: patterns["title_patterns"] + topic opțional
    """
    cache_key = _make_cache_key(patterns.get("title_patterns", {}), f"title_ideas_{topic}")
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    tp = patterns["title_patterns"]
    topic_line = f"Topic/niche: {topic}" if topic else "General content for this channel"

    prompt = f"""
Generate YouTube title ideas based on this channel's real performance data.

Title performance data:
- Emoji in title helps: {tp['emoji_helps']} (with: {tp['avg_views_with_emoji']:,} vs without: {tp['avg_views_without_emoji']:,} avg views)
- Exclamation mark helps: {tp['exclamation_helps']} (with: {tp['avg_views_with_exclamation']:,} vs without: {tp['avg_views_without_exclamation']:,} avg views)
- Best title length: {tp['best_title_length_bucket']} characters
- Average title length: {tp['avg_title_length']} characters
{topic_line}

Respond with this exact JSON structure:
{{
  "title_ideas": ["title 1", "title 2", "title 3", "title 4", "title 5"],
  "title_formula": "the winning formula based on data",
  "key_insight": "most important title pattern discovered"
}}
"""

    raw = _call_gemma(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 3. Weak Video Analysis ────────────────────────────────────────────────────
def analyze_weak_video(patterns: dict, video_title: str, retention: float, views: int) -> dict:
    """
    Analizeaza de ce un video a avut engagement slab.
    Input: patterns + date despre video specific
    """
    cache_key = _make_cache_key({"title": video_title, "retention": retention}, "weak_video")
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    we = patterns["weak_engagement"]
    vl = patterns["video_length"]

    prompt = f"""
Analyze why this YouTube video underperformed and provide specific improvement advice.

Video data:
- Title: "{video_title}"
- Average retention: {retention}%
- Total views: {views:,}

Channel benchmarks:
- Channel average retention: {we['channel_avg_retention']}%
- Channel average views: {we['channel_avg_views']:,}
- Better format for this channel: {vl['better_format']} ({vl['multiplier']}x better)

Respond with this exact JSON structure:
{{
  "likely_reasons": ["reason 1", "reason 2", "reason 3"],
  "retention_diagnosis": "what the retention % tells us",
  "specific_fixes": ["fix 1", "fix 2", "fix 3"],
  "should_republish": true or false,
  "republish_advice": "specific advice if should republish"
}}
"""

    raw = _call_gemma(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 4. Thumbnail Recommendations ─────────────────────────────────────────────
def get_thumbnail_recommendations(patterns: dict) -> dict:
    """
    Generează recomandări pentru thumbnail bazate pe pattern-urile canalului.
    """
    cache_key = _make_cache_key(patterns.get("traffic", {}), "thumbnail")
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    tp = patterns["title_patterns"]
    vl = patterns["video_length"]

    prompt = f"""
Provide YouTube thumbnail recommendations based on this channel's performance data.

Channel data:
- Better format: {vl['better_format']} ({vl['multiplier']}x more views)
- Emoji in titles helps: {tp['emoji_helps']}
- Top traffic source: {patterns['traffic']['top_source']}

Respond with this exact JSON structure:
{{
  "expression": "recommended facial expression or main subject",
  "text_overlay": "recommended text style and max words",
  "colors": "recommended color scheme and why",
  "composition": "recommended layout",
  "reasoning": "why these elements work for this channel"
}}
"""

    raw = _call_gemma(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 5. Channel Audit & Growth Gaps ───────────────────────────────────────────
def get_channel_audit(patterns: dict) -> dict:
    """
    Audit complet al canalului cu growth gaps identificate.
    """
    cache_key = _make_cache_key(patterns, "channel_audit")
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    ut = patterns["upload_times"]
    vl = patterns["video_length"]
    tr = patterns["traffic"]
    we = patterns["weak_engagement"]

    prompt = f"""
Perform a complete YouTube channel audit and identify growth gaps.

Channel statistics:
- Best upload time: {ut['best_day']} at {ut['best_hour']}:00 UTC
- Better content format: {vl['better_format']} ({vl['multiplier']}x better performance)
- Total Shorts: {vl['total_shorts']} | Total Long-form: {vl['total_longform']}
- Top traffic source: {tr['top_source']} ({tr['top_source_percentage']}% of views)
- Channel avg retention: {we['channel_avg_retention']}%
- Videos with weak engagement: {we['total_weak_count']}

Respond with this exact JSON structure:
{{
  "channel_score": a number from 1 to 10,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "growth_gaps": ["gap 1", "gap 2", "gap 3"],
  "top_3_actions": ["action 1", "action 2", "action 3"],
  "traffic_diversity_score": a number from 1 to 10,
  "content_mix_advice": "specific advice on Shorts vs Long-form ratio"
}}
"""

    raw = _call_gemma(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── Master function ───────────────────────────────────────────────────────────
def get_full_insights(patterns: dict, topic: str = "") -> dict:
    """
    Rulează toate analizele și returnează insights complete.
    Folosit de dashboard.py și api.py
    """
    return {
        "upload_strategy": get_upload_strategy(patterns),
        "title_ideas": get_title_ideas(patterns, topic),
        "thumbnail": get_thumbnail_recommendations(patterns),
        "channel_audit": get_channel_audit(patterns),
    }


if __name__ == "__main__":
    from features import get_all_patterns

    print("Calculez patterns...")
    patterns = get_all_patterns()

    print("Generez insights cu Gemma 4...")
    insights = get_full_insights(patterns, topic="lifestyle/entertainment")

    print(json.dumps(insights, indent=2, ensure_ascii=False))


# ── 6. Next Video Ideas ───────────────────────────────────────────────────────
def get_next_video_ideas(top_titles: list, patterns: dict) -> dict:
    """
    Generează idei de clipuri viitoare bazate pe titlurile reale ale canalului.
    Input: lista de titluri top performante + patterns
    """
    cache_key = _make_cache_key({"titles": top_titles[:5]}, "next_video_ideas")
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    vl = patterns["video_length"]
    tp = patterns["title_patterns"]

    titles_str = "\n".join([f"- {t}" for t in top_titles[:15]])

    prompt = f"""
You are a YouTube content strategist. Based on these real top-performing video titles from a channel, generate next video ideas that match the channel's style and audience.

Top performing titles from this channel:
{titles_str}

Channel data:
- Better format: {vl['better_format']} ({vl['multiplier']}x better views)
- Emoji in titles helps: {tp['emoji_helps']}
- Best title length: {tp['best_title_length_bucket']}

Respond with this exact JSON structure:
{{
  "video_ideas": [
    {{"title": "video title idea 1", "why": "why this would perform well"}},
    {{"title": "video title idea 2", "why": "why this would perform well"}},
    {{"title": "video title idea 3", "why": "why this would perform well"}},
    {{"title": "video title idea 4", "why": "why this would perform well"}},
    {{"title": "video title idea 5", "why": "why this would perform well"}}
  ],
  "content_pattern": "what pattern do the top videos follow",
  "niche": "what niche/theme dominates this channel"
}}
"""

    raw = _call_gemma(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 7. Thumbnail Based on Title ───────────────────────────────────────────────
def get_thumbnail_from_title(title: str, top_titles: list, patterns: dict) -> dict:
    """
    Generează recomandări thumbnail specifice pentru un titlu dat.
    Bazat pe titlurile care au performat bine pe canal.
    """
    cache_key = _make_cache_key({"title": title}, "thumbnail_from_title")
    cached = _cache_get(cache_key)
    if cached:
        return {**cached, "from_cache": True}

    tp = patterns["title_patterns"]
    vl = patterns["video_length"]

    top_str = "\n".join([f"- {t}" for t in top_titles[:10]])

    prompt = f"""
You are a YouTube thumbnail designer. Create specific thumbnail recommendations for this video title, based on what works for this channel.

Video title: "{title}"

Top performing titles on this channel (for style reference):
{top_str}

Channel performance data:
- Emoji helps: {tp['emoji_helps']}
- Better format: {vl['better_format']}
- Top traffic source: {patterns['traffic']['top_source']}

Respond with this exact JSON structure:
{{
  "main_subject": "what should be the main visual element",
  "expression": "what facial expression or reaction to show",
  "text_overlay": "exact text to put on thumbnail (max 4 words)",
  "text_style": "color and style of text overlay",
  "background": "background color and style",
  "composition": "how to arrange elements",
  "hook_element": "one surprising/clickbait visual element to add",
  "reasoning": "why these choices fit this specific title and channel"
}}
"""

    raw = _call_gemma(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result
