import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
# ---SETTINGS---
API_KEY = "AIzaSyCYg5e4a1MZB1uT2AW6IK27-wplqOfVZOk"
SERVICE_NAME = 'youtube'
VERSION = "v3"



# --- INIT ---
def get_youtube_service():
    try:
        return build(SERVICE_NAME, VERSION, developerKey=API_KEY)
    except Exception as e:
        return None

# ---SEARCH CHANNELS ---
def search_channels(youtube, query, region_code, max_results=10):
    try:
        search_response = youtube.search().list(
            q=query,
            type='channel',
            part='snippet',
            maxResults=max_results,
            regionCode=region_code
        ).execute()

        return search_response.get('items', [])
    except HttpError as e:
        print(f"Произошла ошибка HTTP {e.resp.status}: {e.content}")
        return []


def calculate_avg_views(channel_data):
    total_views = 0
    video_count = len(channel_data["posts"])

    for video in channel_data["posts"]:
        total_views += video["metrics"]["views"]

    channel_data["avg_views"] = total_views / video_count if video_count > 0 else 0
    return channel_data

def get_channel_stats(youtube, channel_id):
    try:
        channel_response = youtube.channels().list(
            id=channel_id,
            part='snippet,statistics'
        ).execute()

        if not channel_response.get('items'):
            return None

        channel_data = channel_response['items'][0]

        stats = {
            'title': channel_data['snippet']['title'],
            'description': channel_data['snippet']['description'],
            'subscriberCount': int(channel_data['statistics'].get('subscriberCount', 0)),
            'videoCount': int(channel_data['statistics'].get('videoCount', 0)),
            'viewCount': int(channel_data['statistics'].get('viewCount', 0)),
            'avg_views': 0
        }
        return stats
    except HttpError as e:
        print(f"Произошла ошибка HTTP {e.resp.status} при запросе статистики канала {channel_id}: {e.content}")
        return None

# ---GET VIDEOS FROM CHANNEL ---
def get_channel_videos(youtube, channel_id, max_videos):
    try:
        # RECIEVE ID OF "uploads"
        channel_response = youtube.channels().list(
            id=channel_id,
            part='contentDetails'
        ).execute()

        if not channel_response.get('items'):
            return []

        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # GET VIDEOS FROM "upload"
        playlist_items_response = youtube.playlistItems().list(
            playlistId=uploads_playlist_id,
            part='snippet',
            maxResults=max_videos
        ).execute()

        video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_items_response.get('items', [])]

        if not video_ids:
            return []

        # Получаем детали для каждого видео (включая статистику)
        video_details_response = youtube.videos().list(
            id=','.join(video_ids),
            part='snippet,statistics'
        ).execute()

        return video_details_response.get('items', [])

    except HttpError as e:
        print(f"Произошла ошибка HTTP {e.resp.status} при запросе видео с канала {channel_id}: {e.content}")
        return []


def main(search_query, region, num_posts, min_subscribers, min_videos):


    youtube = get_youtube_service()
    if not youtube:
        print(API_KEY,VERSION,SERVICE_NAME)
        return ("YOUTUBE INIT ERROR")


    found_channels = search_channels(youtube, query=search_query, region_code=region, max_results=25)
    if not found_channels:
        return ("CHANNELS DIDNT FOUND")



    competitors = []


    for channel in found_channels:
        channel_id = channel['id']['channelId']
        stats = get_channel_stats(youtube, channel_id)
        if stats:
            if stats['subscriberCount'] >= min_subscribers and stats['videoCount'] >= min_videos:
                competitors.append({
                    'id': channel_id,
                    'title': stats['title'],
                    'subscribers': stats['subscriberCount']
                })


    if not competitors:
        return []



    all_competitor_data = []

    for competitor in competitors:
        channel_data = {
            "channel_title": competitor['title'],
            "channel_id": competitor['id'],
            "subscribers": competitor['subscribers'],
            "avg_views": 0,
            "posts": []
        }

        videos = get_channel_videos(youtube, competitor['id'], num_posts)

        if not videos:
            continue

        for video in videos:
            video_snippet = video['snippet']
            video_stats = video['statistics']

            post_info = {
                "published_at": video_snippet['publishedAt'],
                "title": video_snippet['title'],
                "description": video_snippet['description'],
                "tags/hashtags": video_snippet.get('tags', []),
                "link": f"https://www.youtube.com/watch?v={video['id']}",
                "metrics": {
                    "views": int(video_stats.get('viewCount', 0)),
                    "likes": int(video_stats.get('likeCount', 0)),
                    "comments": int(video_stats.get('commentCount', 0))
                }
            }
            channel_data["posts"].append(post_info)
        channel_data=calculate_avg_views(channel_data)
        all_competitor_data.append(channel_data)
    return all_competitor_data

