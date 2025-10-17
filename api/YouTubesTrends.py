import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta, timezone

API_KEY = "AIzaSyCYg5e4a1MZB1uT2AW6IK27-wplqOfVZOk"
SERVICE_NAME = 'youtube'
VERSION = "v3"

def get_youtube_service():
    try:
        return build(SERVICE_NAME, VERSION, developerKey=API_KEY)
    except Exception as e:
        print(f"Ошибка инициализации YouTube API: {e}")
        return None

def parse_published_at(published_at):
    try:
        if published_at.endswith('Z'):
            published_at = published_at[:-1]
        published_date = datetime.fromisoformat(published_at)
        if published_date.tzinfo is None:
            published_date = published_date.replace(tzinfo=timezone.utc)
        return published_date
    except Exception as e:
        print(f"Ошибка парсинга даты {published_at}: {e}")
        return datetime.now(timezone.utc)

def calculate_virality_score(video_stats, published_at):
    views = video_stats.get('views', 0)
    likes = video_stats.get('likes', 0)
    comments = video_stats.get('comments', 0)

    if views == 0:
        return 0

    like_ratio = likes / views
    comment_ratio = comments / views

    published_date = parse_published_at(published_at)
    current_time = datetime.now(timezone.utc)
    days_ago = (current_time - published_date).days
    freshness_bonus = max(0, 1 - (days_ago / 30))

    virality_score = (
            like_ratio * 1000 +
            comment_ratio * 5000 +
            freshness_bonus * 0.1
    )

    return virality_score

def get_trending_videos(youtube, region_code, max_results=25):
    try:
        request_params = {
            'part': 'snippet,statistics',
            'chart': 'mostPopular',
            'regionCode': region_code,
            'maxResults': max_results
        }

        trending_response = youtube.videos().list(**request_params).execute()

        return trending_response.get('items', [])

    except HttpError as e:
        print(f"Ошибка HTTP {e.resp.status} при запросе трендовых видео: {e.content}")
        return []

def search_viral_videos(youtube, region_code, max_results=25, time_period='week'):
    try:
        now = datetime.now(timezone.utc)

        if time_period == 'today':
            published_after = now - timedelta(days=1)
        elif time_period == 'week':
            published_after = now - timedelta(weeks=1)
        elif time_period == 'month':
            published_after = now - timedelta(days=30)
        else:
            published_after = now - timedelta(weeks=1)

        published_after_str = published_after.isoformat().replace('+00:00', 'Z')

        viral_keywords = [
            "",
            "viral", "тренды", "популярное",
            "shorts", "reels", "вирусное видео",
            "смешное", "удивительное", "шокирующее"
        ]

        all_videos = []

        for keyword in viral_keywords[:3]:
            try:
                search_response = youtube.search().list(
                    part='snippet',
                    type='video',
                    order='viewCount',
                    regionCode=region_code,
                    publishedAfter=published_after_str,
                    q=keyword,
                    maxResults=20
                ).execute()

                video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

                if video_ids:
                    videos_details = youtube.videos().list(
                        id=','.join(video_ids),
                        part='snippet,statistics'
                    ).execute()

                    all_videos.extend(videos_details.get('items', []))

            except HttpError as e:
                print(f"Ошибка при поиске по ключевому слову '{keyword}': {e}")
                continue

        unique_videos = {}
        for video in all_videos:
            unique_videos[video['id']] = video

        videos_list = list(unique_videos.values())

        scored_videos = []
        for video in videos_list:
            video_stats = {
                'views': int(video['statistics'].get('viewCount', 0)),
                'likes': int(video['statistics'].get('likeCount', 0)),
                'comments': int(video['statistics'].get('commentCount', 0))
            }

            virality_score = calculate_virality_score(
                video_stats,
                video['snippet']['publishedAt']
            )

            scored_videos.append({
                'video': video,
                'virality_score': virality_score
            })

        scored_videos.sort(key=lambda x: x['virality_score'], reverse=True)

        return [item['video'] for item in scored_videos[:max_results]]

    except Exception as e:
        print(f"Ошибка при поиске вирусных видео: {e}")
        return []

def get_channel_info(youtube, channel_id):
    try:
        channel_response = youtube.channels().list(
            id=channel_id,
            part='snippet,statistics'
        ).execute()

        if not channel_response.get('items'):
            return None

        channel_data = channel_response['items'][0]

        return {
            'title': channel_data['snippet']['title'],
            'description': channel_data['snippet']['description'],
            'subscribers': int(channel_data['statistics'].get('subscriberCount', 0)),
            'video_count': int(channel_data['statistics'].get('videoCount', 0)),
            'total_views': int(channel_data['statistics'].get('viewCount', 0))
        }

    except HttpError as e:
        print(f"Ошибка при получении информации о канале: {e}")
        return None

def get_video_categories(youtube, region_code):
    try:
        categories_response = youtube.videoCategories().list(
            part='snippet',
            regionCode=region_code
        ).execute()

        categories = []
        for category in categories_response.get('items', []):
            categories.append({
                'id': category['id'],
                'title': category['snippet']['title']
            })

        return categories

    except HttpError as e:
        print(f"Ошибка при получении категорий: {e}")
        return []

def main(search_type='trending', region='US', max_results=20, time_period='week'):
    youtube = get_youtube_service()
    if not youtube:
        return "YOUTUBE INIT ERROR"

    print(f"Поиск вирусных видео для региона: {region}, тип: {search_type}")

    if search_type == 'trending':
        videos = get_trending_videos(youtube, region, max_results)
    elif search_type == 'viral':
        videos = search_viral_videos(youtube, region, max_results, time_period)
    else:
        return "Неверный тип поиска. Используйте 'trending' или 'viral'"

    if not videos:
        return f"Видео не найдены для региона {region}. Попробуйте другой регион или тип поиска."

    viral_videos_data = []

    for video in videos:
        video_snippet = video['snippet']
        video_stats = video['statistics']
        channel_id = video_snippet['channelId']

        channel_info = get_channel_info(youtube, channel_id)

        if not channel_info:
            continue

        stats_dict = {
            'views': int(video_stats.get('viewCount', 0)),
            'likes': int(video_stats.get('likeCount', 0)),
            'comments': int(video_stats.get('commentCount', 0))
        }

        virality_score = calculate_virality_score(stats_dict, video_snippet['publishedAt'])

        video_data = {
            'video_info': {
                'title': video_snippet['title'],
                'description': video_snippet['description'][:200] + '...' if len(
                    video_snippet['description']) > 200 else video_snippet['description'],
                'published_at': video_snippet['publishedAt'],
                'video_id': video['id'],
                'link': f"https://www.youtube.com/watch?v={video['id']}",
                'virality_score': round(virality_score, 2)
            },
            'metrics': stats_dict,
            'channel_info': channel_info
        }

        viral_videos_data.append(video_data)

    viral_videos_data.sort(key=lambda x: x['video_info']['virality_score'], reverse=True)

    return viral_videos_data[:max_results]

if __name__ == "__main__":
    regions_to_test = ['US', 'RU', 'BR', 'IN', 'JP', 'KR', 'DE', 'FR', 'GB']

    for region in regions_to_test:
        print(f"\n{'=' * 60}")
        print(f"ТЕСТИРУЕМ РЕГИОН: {region}")
        print(f"{'=' * 60}")

        print(f"\n--- ТРЕНДОВЫЕ ВИДЕО В {region} ---")
        result = main(search_type='trending', region=region, max_results=5)

        if isinstance(result, list):
            for i, video in enumerate(result, 1):
                print(f"{i}. {video['video_info']['title']}")
                print(f"   Просмотры: {video['metrics']['views']:,}")
                print(f"   Виральность: {video['video_info']['virality_score']}")
                print(f"   Канал: {video['channel_info']['title']}")
                print("-" * 50)
        else:
            print(f"❌ Тренды не доступны: {result}")

        print(f"\n--- ВИРУСНЫЕ ВИДЕО В {region} (за неделю) ---")
        result = main(search_type='viral', region=region, max_results=5, time_period='week')

        if isinstance(result, list):
            for i, video in enumerate(result, 1):
                print(f"{i}. {video['video_info']['title']}")
                print(f"   Просмотры: {video['metrics']['views']:,}")
                print(f"   Виральность: {video['video_info']['virality_score']}")
                print(f"   Канал: {video['channel_info']['title']}")
                print("-" * 50)
        else:
            print(f"❌ Вирусные видео не найдены: {result}")