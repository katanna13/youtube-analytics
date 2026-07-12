"""
insights_engine.py — AI Decision Engine cu Llama 3.3 70B via Groq
Primește patterns calculate din features.py și generează insights acționabile.
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# ── Groq configuration ────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
AI_PROVIDER = "groq"

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "db",
    "youtube_analytics.db",
)
CACHE_TTL_HOURS = 24


# ── Cache SQLite ──────────────────────────────────────────────────────────────
def _get_cache_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_cache (
            cache_key   TEXT PRIMARY KEY,
            response    TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()
    return conn


def _cache_get(key: str):
    """Returnează răspunsul din cache dacă are sub 24h, altfel None."""
    conn = _get_cache_conn()
    row = conn.execute(
        """
        SELECT response, created_at
        FROM ai_cache
        WHERE cache_key = ?
        """,
        (key,),
    ).fetchone()
    conn.close()

    if not row:
        return None

    created = datetime.fromisoformat(row[1])
    age_hours = (datetime.now() - created).total_seconds() / 3600

    if age_hours > CACHE_TTL_HOURS:
        return None

    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None


def _cache_set(key: str, response: dict):
    """Salvează răspunsul AI în cache."""
    conn = _get_cache_conn()
    conn.execute(
        """
        INSERT OR REPLACE INTO ai_cache (cache_key, response, created_at)
        VALUES (?, ?, datetime('now'))
        """,
        (key, json.dumps(response, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def _make_cache_key(patterns: dict, insight_type: str) -> str:
    """
    Generează un cache key unic din date, tipul insight-ului,
    provider și model.

    Includerea providerului și modelului evită reutilizarea accidentală
    a răspunsurilor generate anterior de Gemma/Fireworks.
    """
    content = (
        json.dumps(patterns, sort_keys=True, ensure_ascii=False)
        + insight_type
        + AI_PROVIDER
        + MODEL
    )
    return hashlib.md5(content.encode("utf-8")).hexdigest()


# ── Groq API Call ─────────────────────────────────────────────────────────────
def _call_llm(prompt: str) -> str:
    """Apelează Llama prin Groq și returnează textul răspunsului."""

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY lipsește. Adaugă cheia Groq în fișierul .env."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a YouTube growth strategist AI. "
                    "You analyze real channel data and provide specific, "
                    "actionable insights. "
                    "Always respond with valid JSON only. "
                    "Do not use markdown and do not include any explanation "
                    "outside the JSON object."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "max_completion_tokens": 600,
        "temperature": 0.3,
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=45,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"Nu s-a putut realiza conexiunea la Groq: {exc}") from exc

    if not response.ok:
        raise RuntimeError(
            f"Groq API error {response.status_code}: {response.text[:500]}"
        )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "Groq a returnat un răspuns într-un format neașteptat."
        ) from exc

    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Groq a returnat un răspuns gol.")

    return content


def _parse_json_response(raw: str) -> dict:
    """Parsează răspunsul JSON al modelului și elimină eventualele code fences."""
    clean = raw.strip()

    if clean.startswith("```"):
        lines = clean.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        clean = "\n".join(lines).strip()

    if clean.lower().startswith("json"):
        clean = clean[4:].lstrip()

    try:
        result = json.loads(clean)
    except json.JSONDecodeError:
        return {
            "error": "Could not parse AI response",
            "raw": raw[:500],
            "provider": AI_PROVIDER,
            "model": MODEL,
        }

    if not isinstance(result, dict):
        return {
            "error": "AI response was valid JSON, but not a JSON object",
            "raw": raw[:500],
            "provider": AI_PROVIDER,
            "model": MODEL,
        }

    return result


# ── 1. Best Upload Strategy ───────────────────────────────────────────────────
def get_upload_strategy(patterns: dict) -> dict:
    """
    Generează strategia optimă de upload bazată pe ore și zile.
    Input: patterns["upload_times"]
    """
    cache_key = _make_cache_key(
        patterns.get("upload_times", {}),
        "upload_strategy",
    )
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

Treat these values as observed associations, not proof that upload time alone
caused the performance difference.

Respond with this exact JSON structure:
{{
  "optimal_schedule": "specific day and time recommendation",
  "why_it_works": "1-2 sentences explaining the observed pattern",
  "avoid": "what to avoid and why",
  "action_items": ["action 1", "action 2", "action 3"]
}}
"""

    raw = _call_llm(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 2. Title Ideas ────────────────────────────────────────────────────────────
def get_title_ideas(patterns: dict, topic: str = "") -> dict:
    """
    Generează idei de titluri bazate pe pattern-urile canalului.
    Input: patterns["title_patterns"] + topic opțional
    """
    cache_key = _make_cache_key(
        patterns.get("title_patterns", {}),
        f"title_ideas_{topic}",
    )
    cached = _cache_get(cache_key)

    if cached:
        return {**cached, "from_cache": True}

    tp = patterns["title_patterns"]
    topic_line = (
        f"Topic/niche: {topic}"
        if topic
        else "General content for this channel"
    )

    prompt = f"""
Generate YouTube title ideas based on this channel's real performance data.

Title performance data:
- Emoji in title helps: {tp['emoji_helps']}
  (with: {tp['avg_views_with_emoji']:,} vs without: {tp['avg_views_without_emoji']:,} avg views)
- Exclamation mark helps: {tp['exclamation_helps']}
  (with: {tp['avg_views_with_exclamation']:,} vs without: {tp['avg_views_without_exclamation']:,} avg views)
- Best title length bucket: {tp['best_title_length_bucket']}
- Average title length: {tp['avg_title_length']} characters
- {topic_line}

Treat these statistics as channel-specific associations, not universal rules.

Respond with this exact JSON structure:
{{
  "title_ideas": ["title 1", "title 2", "title 3", "title 4", "title 5"],
  "title_formula": "the winning formula based on the channel data",
  "key_insight": "most important title pattern discovered"
}}
"""

    raw = _call_llm(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 3. Weak Video Analysis ────────────────────────────────────────────────────
def analyze_weak_video(
    patterns: dict,
    video_title: str,
    retention: float,
    views: int,
) -> dict:
    """
    Analizează de ce un video a avut engagement slab.
    Input: patterns + date despre video specific.
    """
    cache_key = _make_cache_key(
        {
            "title": video_title,
            "retention": retention,
            "views": views,
        },
        "weak_video",
    )
    cached = _cache_get(cache_key)

    if cached:
        return {**cached, "from_cache": True}

    we = patterns["weak_engagement"]
    vl = patterns["video_length"]

    format_context = (
        f"{vl['better_format']} ({vl['multiplier']}x better)"
        if vl.get("multiplier") is not None
        else f"{vl['better_format']} (no comparison baseline available)"
    )

    prompt = f"""
Analyze why this YouTube video underperformed and provide specific improvement advice.

Video data:
- Title: "{video_title}"
- Average retention: {retention}%
- Total views: {views:,}

Channel benchmarks:
- Channel average retention: {we['channel_avg_retention']}%
- Channel average views: {we['channel_avg_views']:,}
- Better format for this channel: {format_context}

Important context:
For YouTube Shorts, average view percentage can exceed 100% because viewers can
rewatch or loop the video. Do not treat retention above 100% as invalid.

Do not claim certainty about causes. Frame reasons as likely hypotheses based on
the available data.

Respond with this exact JSON structure:
{{
  "likely_reasons": ["reason 1", "reason 2", "reason 3"],
  "retention_diagnosis": "what the retention percentage suggests",
  "specific_fixes": ["fix 1", "fix 2", "fix 3"],
  "should_republish": true or false,
  "republish_advice": "specific advice if it should be republished"
}}
"""

    raw = _call_llm(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 4. Thumbnail Recommendations ─────────────────────────────────────────────
def get_thumbnail_recommendations(patterns: dict) -> dict:
    """Generează recomandări generale pentru thumbnails."""
    cache_key = _make_cache_key(
        {
            "traffic": patterns.get("traffic", {}),
            "title_patterns": patterns.get("title_patterns", {}),
            "video_length": patterns.get("video_length", {}),
        },
        "thumbnail",
    )
    cached = _cache_get(cache_key)

    if cached:
        return {**cached, "from_cache": True}

    tp = patterns["title_patterns"]
    vl = patterns["video_length"]

    format_context = (
        f"{vl['better_format']} ({vl['multiplier']}x more views)"
        if vl.get("multiplier") is not None
        else f"{vl['better_format']} (no comparison baseline available)"
    )

    prompt = f"""
Provide YouTube thumbnail recommendations based on this channel's performance data.

Channel data:
- Better format: {format_context}
- Emoji in titles helps: {tp['emoji_helps']}
- Top traffic source: {patterns['traffic']['top_source']}

Make the recommendations specific and practical. Do not claim that title emoji
performance directly proves what thumbnail design will work.

Respond with this exact JSON structure:
{{
  "expression": "recommended facial expression or main subject",
  "text_overlay": "recommended text style and maximum number of words",
  "colors": "recommended color scheme and why",
  "composition": "recommended layout",
  "reasoning": "why these elements fit this channel"
}}
"""

    raw = _call_llm(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 5. Channel Audit & Growth Gaps ───────────────────────────────────────────
def get_channel_audit(patterns: dict) -> dict:
    """Generează un audit complet al canalului și identifică growth gaps."""
    cache_key = _make_cache_key(patterns, "channel_audit")
    cached = _cache_get(cache_key)

    if cached:
        return {**cached, "from_cache": True}

    ut = patterns["upload_times"]
    vl = patterns["video_length"]
    tr = patterns["traffic"]
    we = patterns["weak_engagement"]

    format_context = (
        f"{vl['better_format']} ({vl['multiplier']}x better performance)"
        if vl.get("multiplier") is not None
        else f"{vl['better_format']} (no comparison baseline available)"
    )

    prompt = f"""
Perform a complete YouTube channel audit and identify growth gaps.

Channel statistics:
- Best observed upload time: {ut['best_day']} at {ut['best_hour']}:00 UTC
- Better content format: {format_context}
- Total Shorts: {vl['total_shorts']}
- Total Long-form: {vl['total_longform']}
- Top traffic source: {tr['top_source']} ({tr['top_source_percentage']}% of views)
- Channel average retention: {we['channel_avg_retention']}%
- Videos with weak engagement: {we['total_weak_count']}

Important context:
- Upload-time statistics are observed associations, not proof of causation.
- YouTube Shorts retention can exceed 100% because of loops and replays.
- If the channel has no long-form videos, do not pretend there is a valid
  Shorts-vs-long-form comparison.

Respond with this exact JSON structure:
{{
  "channel_score": a number from 1 to 10,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "growth_gaps": ["gap 1", "gap 2", "gap 3"],
  "top_3_actions": ["action 1", "action 2", "action 3"],
  "traffic_diversity_score": a number from 1 to 10,
  "content_mix_advice": "specific advice on Shorts versus long-form strategy"
}}
"""

    raw = _call_llm(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 6. Next Video Ideas ───────────────────────────────────────────────────────
def get_next_video_ideas(top_titles: list, patterns: dict) -> dict:
    """
    Generează idei de clipuri viitoare bazate pe titlurile reale ale canalului.
    Input: lista de titluri top performante + patterns.
    """
    cache_key = _make_cache_key(
        {
            "titles": top_titles[:15],
            "title_patterns": patterns.get("title_patterns", {}),
            "video_length": patterns.get("video_length", {}),
        },
        "next_video_ideas",
    )
    cached = _cache_get(cache_key)

    if cached:
        return {**cached, "from_cache": True}

    vl = patterns["video_length"]
    tp = patterns["title_patterns"]

    titles_str = "\n".join(f"- {title}" for title in top_titles[:15])

    format_context = (
        f"{vl['better_format']} ({vl['multiplier']}x better views)"
        if vl.get("multiplier") is not None
        else f"{vl['better_format']} (no comparison baseline available)"
    )

    prompt = f"""
You are a YouTube content strategist. Based on these real top-performing video
titles, generate next video ideas that match the channel's style and audience.

Top-performing titles:
{titles_str}

Channel data:
- Better format: {format_context}
- Emoji in titles helps: {tp['emoji_helps']}
- Best title length bucket: {tp['best_title_length_bucket']}

Avoid copying the existing titles word-for-word. Produce original ideas that
follow the detected themes and style.

Respond with this exact JSON structure:
{{
  "video_ideas": [
    {{"title": "video title idea 1", "why": "why this could perform well"}},
    {{"title": "video title idea 2", "why": "why this could perform well"}},
    {{"title": "video title idea 3", "why": "why this could perform well"}},
    {{"title": "video title idea 4", "why": "why this could perform well"}},
    {{"title": "video title idea 5", "why": "why this could perform well"}}
  ],
  "content_pattern": "the main pattern followed by the top videos",
  "niche": "the dominant niche or theme of this channel"
}}
"""

    raw = _call_llm(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── 7. Thumbnail Based on Title ───────────────────────────────────────────────
def get_thumbnail_from_title(
    title: str,
    top_titles: list,
    patterns: dict,
) -> dict:
    """
    Generează recomandări de thumbnail specifice pentru un titlu dat.
    Se bazează pe titlurile care au performat bine pe canal.
    """
    cache_key = _make_cache_key(
        {
            "title": title,
            "top_titles": top_titles[:10],
            "traffic": patterns.get("traffic", {}),
            "title_patterns": patterns.get("title_patterns", {}),
        },
        "thumbnail_from_title",
    )
    cached = _cache_get(cache_key)

    if cached:
        return {**cached, "from_cache": True}

    tp = patterns["title_patterns"]
    vl = patterns["video_length"]

    top_str = "\n".join(f"- {top_title}" for top_title in top_titles[:10])

    prompt = f"""
You are a YouTube thumbnail designer. Create specific thumbnail recommendations
for this video title, based on what works for this channel.

Video title:
"{title}"

Top-performing titles on this channel:
{top_str}

Channel performance data:
- Emoji helps: {tp['emoji_helps']}
- Better format: {vl['better_format']}
- Top traffic source: {patterns['traffic']['top_source']}

The thumbnail recommendation must be practical and tailored to the exact title.
Do not claim certainty that a design will guarantee performance.

Respond with this exact JSON structure:
{{
  "main_subject": "the main visual element",
  "expression": "the facial expression or reaction",
  "text_overlay": "exact thumbnail text, maximum 4 words",
  "text_style": "color and style of the text overlay",
  "background": "background color and style",
  "composition": "how to arrange the elements",
  "hook_element": "one surprising visual hook",
  "reasoning": "why these choices fit the title and channel"
}}
"""

    raw = _call_llm(prompt)
    result = _parse_json_response(raw)
    _cache_set(cache_key, result)
    return result


# ── Master function ───────────────────────────────────────────────────────────
def get_full_insights(patterns: dict, topic: str = "") -> dict:
    """
    Rulează toate analizele și returnează insights complete.
    Folosit de dashboard.py și api.py.
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
    all_patterns = get_all_patterns()

    print(f"Generez insights cu {MODEL} via Groq...")
    all_insights = get_full_insights(
        all_patterns,
        topic="lifestyle/entertainment",
    )

    print(json.dumps(all_insights, indent=2, ensure_ascii=False))
