"""
Test script: confirmă că OAuth + YouTube Data API funcționează,
trăgând ultimele 5 video-uri publicate pe canalul autentificat.
"""

import sys
import os

# permite import din auth/authenticate.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from googleapiclient.discovery import build
from auth.authenticate import get_authenticated_credentials


def get_my_channel_id(youtube):
    """Obține channel_id-ul canalului autentificat (al tău)."""
    response = youtube.channels().list(
        part="id,snippet,statistics",
        mine=True
    ).execute()

    channel = response["items"][0]
    return channel


def get_latest_videos(youtube, channel_id, max_results=5):
    """Trage ultimele N video-uri publicate pe canal."""
    response = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        order="date",
        type="video",
        maxResults=max_results
    ).execute()

    return response.get("items", [])


def main():
    creds = get_authenticated_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    print("=" * 50)
    print("PASUL 1: Informații despre canal")
    print("=" * 50)

    channel = get_my_channel_id(youtube)
    snippet = channel["snippet"]
    stats = channel["statistics"]

    print(f"Nume canal: {snippet['title']}")
    print(f"Channel ID: {channel['id']}")
    print(f"Subscriberi: {stats.get('subscriberCount', 'N/A')}")
    print(f"Total views: {stats.get('viewCount', 'N/A')}")
    print(f"Total video-uri: {stats.get('videoCount', 'N/A')}")

    print("\n" + "=" * 50)
    print("PASUL 2: Ultimele 5 video-uri")
    print("=" * 50)

    videos = get_latest_videos(youtube, channel["id"], max_results=5)

    if not videos:
        print("Nu am găsit video-uri (poate canalul e nou sau toate sunt private).")
        return

    for i, video in enumerate(videos, 1):
        video_id = video["id"]["videoId"]
        title = video["snippet"]["title"]
        published_at = video["snippet"]["publishedAt"]
        print(f"\n{i}. {title}")
        print(f"   video_id: {video_id}")
        print(f"   publicat: {published_at}")


if __name__ == "__main__":
    main()
