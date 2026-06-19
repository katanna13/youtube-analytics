"""
Pipeline principal de ingestion:
1. Trage TOATE video-urile canalului (cu paginare, peste limita de 50/request)
2. Pentru fiecare video, trage metrici zilnice (de la data publicării până azi-2zile)
3. Pentru fiecare video, trage traffic sources (agregat pe tot intervalul)
4. Salvează tot în SQLite, cu upsert (rulabil repetat, fără duplicate)

Notă: pentru un canal cu 342 video-uri, acest script face MULTE
request-uri către Analytics API (1 per video pentru metrici + 1 per video
pentru traffic). Quota default YouTube API = 10,000 unități/zi.
Fiecare query Analytics costă ~1-2 unități, deci 342 video-uri * 2 query-uri
= ~700 unități. Sigur sub limită, dar rulează cu răbdare (rate limiting + delay).
"""

import sys
import os
import time
from datetime import date, timedelta, datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from auth.authenticate import get_authenticated_credentials
from db.db import get_connection, init_db, upsert_video, upsert_daily_metric, upsert_traffic_source

CHANNEL_ID = "UCJMEv8HiPnTeVp7g9J8XNYg"
ANALYTICS_END_DATE = date.today() - timedelta(days=2)  # delay de procesare YouTube
REQUEST_DELAY_SECONDS = 0.3  # mic delay intre request-uri, ca sa nu lovim rate limits


def parse_duration_to_seconds(iso_duration):
    """Converteste ISO 8601 duration (ex: PT1M30S) in secunde."""
    import re
    match = re.match(
        r"P(?:\d+D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration
    )
    if not match:
        return 0
    h, m, s = match.groups()
    return int(h or 0) * 3600 + int(m or 0) * 60 + int(s or 0)
def get_uploads_playlist_id(youtube, channel_id):
    """Obține playlist-ul 'uploads' al canalului (toate video-urile)."""
    response = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    ).execute()

    return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

def get_all_video_ids(youtube, channel_id):
    """Trage TOATE video-urile canalului folosind uploads playlist (exhaustiv)."""

    uploads_playlist_id = get_uploads_playlist_id(youtube, channel_id)

    video_ids = []
    next_page_token = None

    while True:
        response = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        for item in response.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    return video_ids


def get_videos_metadata(youtube, video_ids):
    """
    Trage metadata completa (titlu, durata, etc.) pentru o lista de video_ids.
    videos().list() permite max 50 ID-uri per request.
    """
    all_metadata = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        response = youtube.videos().list(
            part="snippet,contentDetails",
            id=",".join(batch)
        ).execute()

        for item in response.get("items", []):
            snippet = item["snippet"]
            duration_sec = parse_duration_to_seconds(item["contentDetails"]["duration"])

            all_metadata.append({
                "video_id": item["id"],
                "channel_id": snippet["channelId"],
                "title": snippet["title"],
                "description": snippet.get("description", "")[:1000],  # truncat, nu avem nevoie de tot
                "published_at": snippet["publishedAt"],
                "duration_seconds": duration_sec,
                "category_id": snippet.get("categoryId"),
                "thumbnail_url": snippet["thumbnails"].get("high", {}).get("url", ""),
                "is_short": 1 if duration_sec <= 60 else 0
            })

        time.sleep(REQUEST_DELAY_SECONDS)

    return all_metadata


def fetch_daily_metrics_for_video(analytics, channel_id, video_id, start_date, end_date):
    """Trage metrici zilnice pentru un video, intre start_date si end_date."""
    try:
        response = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            metrics="views,estimatedMinutesWatched,averageViewDuration,"
                    "averageViewPercentage,subscribersGained,subscribersLost",
            dimensions="day",
            filters=f"video=={video_id}",
            sort="day"
        ).execute()
    except HttpError as e:
        print(f"  [WARN] Eroare la metrici pentru {video_id}: {e}")
        return []

    headers = [h["name"] for h in response.get("columnHeaders", [])]
    rows = response.get("rows", [])

    results = []
    for row in rows:
        row_dict = dict(zip(headers, row))
        # skip zile fara nicio activitate, ca sa nu umplem DB cu zerouri inutile
        if row_dict.get("views", 0) == 0:
            continue
        results.append({
            "video_id": video_id,
            "date": row_dict["day"],
            "views": row_dict.get("views", 0),
            "estimated_minutes_watched": row_dict.get("estimatedMinutesWatched", 0),
            "average_view_duration": row_dict.get("averageViewDuration", 0),
            "average_view_percentage": row_dict.get("averageViewPercentage", 0),
            "subscribers_gained": row_dict.get("subscribersGained", 0),
            "subscribers_lost": row_dict.get("subscribersLost", 0),
        })

    return results


def fetch_traffic_sources_for_video(analytics, channel_id, video_id, start_date, end_date):
    """Trage traffic sources agregate (pe tot intervalul) pentru un video."""
    try:
        response = analytics.reports().query(
            ids=f"channel=={channel_id}",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            metrics="views,estimatedMinutesWatched",
            dimensions="insightTrafficSourceType",
            filters=f"video=={video_id}",
            sort="-views"
        ).execute()
    except HttpError as e:
        print(f"  [WARN] Eroare la traffic sources pentru {video_id}: {e}")
        return []

    headers = [h["name"] for h in response.get("columnHeaders", [])]
    rows = response.get("rows", [])

    results = []
    for row in rows:
        row_dict = dict(zip(headers, row))
        results.append({
            "video_id": video_id,
            "traffic_source_type": row_dict["insightTrafficSourceType"],
            "views": row_dict.get("views", 0),
            "estimated_minutes_watched": row_dict.get("estimatedMinutesWatched", 0),
        })

    return results


def main():
    print("Inițializare bază de date...")
    init_db()

    creds = get_authenticated_credentials()
    youtube = build("youtube", "v3", credentials=creds)
    analytics = build("youtubeAnalytics", "v2", credentials=creds)

    conn = get_connection()

    print("\nPasul 1: Tragem toate ID-urile de video-uri...")
    video_ids = get_all_video_ids(youtube, CHANNEL_ID)
    print(f"Găsite {len(video_ids)} video-uri.")

    print("\nPasul 2: Tragem metadata pentru toate video-urile...")
    videos_metadata = get_videos_metadata(youtube, video_ids)

    print("Salvăm metadata în DB...")
    for video in videos_metadata:
        upsert_video(conn, video)
    conn.commit()
    print(f"Salvate {len(videos_metadata)} video-uri.")

    print("\nPasul 3: Tragem metrici zilnice + traffic sources per video.")
    print("(asta durează cel mai mult - 2 request-uri per video)\n")

    today = date.today()

    for idx, video in enumerate(videos_metadata, 1):
        video_id = video["video_id"]
        published_date = datetime.fromisoformat(
            video["published_at"].replace("Z", "+00:00")
        ).date()

        start_date = published_date
        end_date = min(ANALYTICS_END_DATE, today)

        if start_date > end_date:
            # video publicat in ultimele 2 zile, inca fara date procesate
            continue

        print(f"[{idx}/{len(videos_metadata)}] {video_id} - {video['title'][:50]}")

        # Metrici zilnice
        daily_metrics = fetch_daily_metrics_for_video(
            analytics, CHANNEL_ID, video_id, start_date, end_date
        )
        for metric in daily_metrics:
            upsert_daily_metric(conn, metric)

        # Traffic sources
        traffic = fetch_traffic_sources_for_video(
            analytics, CHANNEL_ID, video_id, start_date, end_date
        )
        for source in traffic:
            upsert_traffic_source(conn, source)

        conn.commit()
        time.sleep(REQUEST_DELAY_SECONDS)

    conn.close()
    print("\n✅ Ingestion completă!")


if __name__ == "__main__":
    main()