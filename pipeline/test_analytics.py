"""
Test script: trage metrici din YouTube Analytics API pentru ultimele N zile,
agregat pe canal și (opțional) per video.

YouTube Analytics API foloseste un alt "service name" decat Data API:
- youtube (v3)            -> metadata (titluri, thumbnails, etc.)
- youtubeAnalytics (v2)   -> metrici (views, watch time, CTR, traffic sources)
"""

import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from googleapiclient.discovery import build
from auth.authenticate import get_authenticated_credentials


def build_analytics_client(creds):
    return build("youtubeAnalytics", "v2", credentials=creds)


def get_channel_metrics_last_n_days(analytics, channel_id, days=30):
    """
    Trage metrici zilnice agregate pe TOT canalul (nu per video),
    util ca prim test - cere mai puține permisiuni / e mai simplu de validat.
    """
    end_date = date.today() - timedelta(days=2)  # YouTube are delay de procesare
    start_date = end_date - timedelta(days=days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        metrics="views,estimatedMinutesWatched,averageViewDuration,"
                "averageViewPercentage,subscribersGained,subscribersLost",
        dimensions="day",
        sort="day"
    ).execute()

    return response


def get_video_metrics(analytics, channel_id, video_id, days=30):
    """
    Trage metrici zilnice "normale" pentru UN video specific
    (views, watch time, retention) - fara impressions/CTR.
    """
    end_date = date.today() - timedelta(days=2)
    start_date = end_date - timedelta(days=days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        metrics="views,estimatedMinutesWatched,averageViewDuration,"
                "averageViewPercentage",
        dimensions="day",
        filters=f"video=={video_id}",
        sort="day"
    ).execute()

    return response


def get_video_traffic_sources(analytics, channel_id, video_id, days=30):
    """
    Trage sursele de trafic (SEARCH, SUGGESTED, EXTERNAL, etc.) pentru UN video.
    Aceasta e o dimensiune separata - insightTrafficSourceType.
    """
    end_date = date.today() - timedelta(days=2)
    start_date = end_date - timedelta(days=days)

    response = analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        metrics="views,estimatedMinutesWatched",
        dimensions="insightTrafficSourceType",
        filters=f"video=={video_id}",
        sort="-views"
    ).execute()

    return response


def print_report(response, label):
    print(f"\n--- {label} ---")
    headers = [h["name"] for h in response.get("columnHeaders", [])]
    print(headers)

    rows = response.get("rows", [])
    if not rows:
        print("(fără date pentru acest interval — posibil prea recent sau fără trafic)")
        return

    for row in rows:
        print(row)


def main():
    creds = get_authenticated_credentials()
    analytics = build_analytics_client(creds)

    CHANNEL_ID = "UCJMEv8HiPnTeVp7g9J8XNYg"  # din Pasul 1, scriptul anterior

    print("=" * 60)
    print("TEST 1: Metrici agregate pe canal, ultimele 30 zile")
    print("=" * 60)
    channel_report = get_channel_metrics_last_n_days(analytics, CHANNEL_ID, days=30)
    print_report(channel_report, "Channel daily metrics")

    print("\n" + "=" * 60)
    print("TEST 2: Metrici (views/watch time) pentru UN video specific")
    print("=" * 60)
    TEST_VIDEO_ID = "hiIlMa1l6jw"  # primul video din lista anterioară
    video_report = get_video_metrics(analytics, CHANNEL_ID, TEST_VIDEO_ID, days=30)
    print_report(video_report, f"Video {TEST_VIDEO_ID} daily metrics")

    print("\n" + "=" * 60)
    print("TEST 3: Surse de trafic pentru același video")
    print("=" * 60)
    traffic_report = get_video_traffic_sources(analytics, CHANNEL_ID, TEST_VIDEO_ID, days=30)
    print_report(traffic_report, f"Video {TEST_VIDEO_ID} traffic sources")


if __name__ == "__main__":
    main()