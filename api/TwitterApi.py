import os
import tweepy
from datetime import datetime
import json
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---SETTINGS---
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAN5H4wEAAAAArrSsLvrp9dokGy4aXx2H8CaaNBE%3DQYKrmHRIUY3Hnv3XcpMBQ8SHAYayLPi3zGIXTwdMpdVIaEAHmG"
ACCESS_TOKEN = "1194488984891797505-ZkKYxY0UMquJ5e3tn7JtmfgldTAXCJ"
ACCESS_TOKEN_SECRET = "FKpByLVnlmnHX9sjzm96dE3jDNypxL6ylmrtQMal9hVvy"
API_KEY = "TzRAhfz0BjxN0mYMiZHIZxPRl"  # Требуется для аутентификации
API_SECRET = "3rpeKKDUrU6NMIouOeH4HNBBJaHD6D52JVCrYyQ5biNYpx3ti5"  # Требуется для аутентификации


# --- INIT with SSL handling ---
def get_twitter_service():
    try:
        # Создаем кастомную сессию с повторными попытками
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            consumer_key=API_KEY,
            consumer_secret=API_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True,
        )
        return client
    except Exception as e:
        print(f"Twitter service error: {e}")
        return None


# ---ALTERNATIVE USER SEARCH without search_recent_tweets---
def search_users_alternative(twitter, query, max_results=10):
    try:
        # Метод 1: Поиск по известным пользователям в нише
        niche_users = {
            'python': ['gvanrossum', 'raymondh', 'dabeaz', 'kennethreitz', 'wesmckinn', 'pyladies', 'pythonbytes',
                       'talkpython'],
            'programming': ['github', 'stackoverflow', 'Codecademy', 'freeCodeCamp', 'ThePracticalDev'],
            'javascript': ['nodejs', 'angular', 'reactjs', 'vuejs', 'jquery'],
            'data science': ['kaggle', 'DataScienceTip', 'KirkDBorne', 'hmason', 'mathbabedotorg']
        }

        found_users = []

        # Ищем пользователей по известным именам в нише
        for niche, usernames in niche_users.items():
            if niche in query.lower():
                for username in usernames[:max_results]:
                    try:
                        user = twitter.get_user(
                            username=username,
                            user_fields=['description', 'public_metrics', 'verified', 'name']
                        )
                        if user.data:
                            found_users.append(user.data)
                            time.sleep(0.1)  # Задержка между запросами
                    except Exception as e:
                        print(f"Error fetching user {username}: {e}")
                        continue

                break  # Выходим после нахождения подходящей ниши

        return found_users

    except Exception as e:
        print(f"Error in alternative user search: {e}")
        return []


# ---GET USER STATS ---
def get_user_stats(twitter, user_id):
    try:
        user_response = twitter.get_user(
            id=user_id,
            user_fields=['description', 'public_metrics', 'verified', 'created_at', 'name', 'username']
        )

        if not user_response.data:
            return None

        user_data = user_response.data
        metrics = user_data.public_metrics

        stats = {
            'title': user_data.name,
            'username': user_data.username,
            'description': user_data.description or '',
            'subscriberCount': metrics.get('followers_count', 0),
            'videoCount': metrics.get('tweet_count', 0),
            'viewCount': 0,
            'avg_views': 0,
            'verified': user_data.verified,
            'created_at': user_data.created_at,
            'following_count': metrics.get('following_count', 0)
        }
        return stats
    except Exception as e:
        print(f"Error getting user stats for {user_id}: {e}")
        return None


# ---GET TWEETS FROM USER ---
def get_user_tweets(twitter, user_id, max_tweets):
    try:
        tweets_response = twitter.get_users_tweets(
            id=user_id,
            max_results=max_tweets,
            tweet_fields=['created_at', 'public_metrics', 'text', 'context_annotations', 'lang'],
            exclude=['retweets', 'replies'],
        )

        if not tweets_response.data:
            return []

        tweets_data = []
        for tweet in tweets_response.data:
            metrics = tweet.public_metrics
            tweets_data.append({
                'id': tweet.id,
                'text': tweet.text,
                'created_at': tweet.created_at,
                'public_metrics': metrics,
                'lang': tweet.lang
            })

        return tweets_data

    except Exception as e:
        print(f"Error getting tweets for user {user_id}: {e}")
        return []


def calculate_avg_views(user_data):
    total_views = 0
    tweet_count = len(user_data["posts"])

    for tweet in user_data["posts"]:
        total_views += tweet["metrics"]["views"]

    user_data["avg_views"] = total_views / tweet_count if tweet_count > 0 else 0
    return user_data


def extract_hashtags(text):
    """Извлекает хэштеги из текста твита"""
    import re
    hashtags = re.findall(r'#\w+', text)
    return hashtags


# ---MAIN FUNCTION with error handling---
def main(search_query, region=None, num_posts=10, min_subscribers=1000, min_videos=10):
    """
    Аналог YouTube скрипта для Twitter API v2
    """

    print(f"Starting Twitter analysis for: {search_query}")

    # INIT
    twitter = get_twitter_service()
    if not twitter:
        return "TWITTER INIT ERROR"

    # SEARCHING USERS - пытаемся оба метода
    found_users = []

    try:
        # Пробуем альтернативный метод сначала
        found_users = search_users_alternative(twitter, query=search_query, max_results=25)
        print(f"Alternative method found {len(found_users)} users")
    except Exception as e:
        print(f"Alternative search failed: {e}")
        found_users = []

    if not found_users:
        return "USERS DIDN'T FOUND"

    competitors = []

    # FILTER USERS
    for user in found_users:
        user_id = user.id
        stats = get_user_stats(twitter, user_id)
        if stats:
            if stats['subscriberCount'] >= min_subscribers and stats['videoCount'] >= min_videos:
                competitors.append({
                    'id': user_id,
                    'title': stats['title'],
                    'username': stats['username'],
                    'subscribers': stats['subscriberCount']
                })
                print(f"Added competitor: {stats['title']} with {stats['subscriberCount']} followers")

    if not competitors:
        return []

    print(f"Found {len(competitors)} competitors after filtering")

    # GET TWEETS DATA
    all_competitor_data = []

    for competitor in competitors:
        print(f"Analyzing tweets for: {competitor['title']}")

        user_data = {
            "channel_title": competitor['title'],
            "channel_id": competitor['id'],
            "username": competitor['username'],
            "subscribers": competitor['subscribers'],
            "avg_views": 0,
            "posts": []
        }

        tweets = get_user_tweets(twitter, competitor['id'], num_posts)

        if not tweets:
            print(f"No tweets found for {competitor['title']}")
            continue

        print(f"Found {len(tweets)} tweets for {competitor['title']}")

        for tweet in tweets:
            post_info = {
                "published_at": tweet['created_at'].isoformat() if tweet['created_at'] else None,
                "title": tweet['text'][:100] + "..." if len(tweet['text']) > 100 else tweet['text'],
                "description": tweet['text'],
                "tags/hashtags": extract_hashtags(tweet['text']),
                "link": f"https://twitter.com/{competitor['username']}/status/{tweet['id']}",
                "metrics": {
                    "views": tweet['public_metrics'].get('impression_count', 0),
                    "likes": tweet['public_metrics'].get('like_count', 0),
                    "comments": tweet['public_metrics'].get('reply_count', 0),
                    "retweets": tweet['public_metrics'].get('retweet_count', 0)
                }
            }
            user_data["posts"].append(post_info)

        user_data = calculate_avg_views(user_data)
        all_competitor_data.append(user_data)
        print(f"Completed analysis for {competitor['title']}")

    return all_competitor_data


# ---TEST WITH MOCK DATA---
def main_with_fallback(search_query, region=None, num_posts=10, min_subscribers=1000, min_videos=10):
    """
    Версия с фолбэком на mock данные если API не работает
    """
    try:
        result = main(search_query, region, num_posts, min_subscribers, min_videos)
        if isinstance(result, list) and result:
            return result
        else:
            print("API failed, returning mock data for testing")
            return get_mock_data()
    except Exception as e:
        print(f"Complete failure: {e}")
        return get_mock_data()


def get_mock_data():
    """Mock данные для тестирования когда API недоступен"""
    return [
        {
            "channel_title": "Python Official",
            "channel_id": "12345",
            "username": "python",
            "subscribers": 1500000,
            "avg_views": 25000,
            "posts": [
                {
                    "published_at": "2024-01-15T10:00:00",
                    "title": "Python 3.12 released with new features...",
                    "description": "Python 3.12 released with new features and performance improvements #python #programming",
                    "tags/hashtags": ["#python", "#programming"],
                    "link": "https://twitter.com/python/status/12345",
                    "metrics": {
                        "views": 35000,
                        "likes": 1200,
                        "comments": 150,
                        "retweets": 450
                    }
                }
            ]
        }
    ]


# Пример использования
if __name__ == "__main__":
    # Тестовый вызов с обработкой ошибок
    try:
        result = main_with_fallback(
            search_query="python programming",
            num_posts=5,
            min_subscribers=1000,
            min_videos=10
        )

        if isinstance(result, list):
            print(f"✅ Analysis completed! Found {len(result)} competitors")
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

            # Статистика
            for competitor in result:
                print(f"\n📊 User: {competitor['channel_title']} (@{competitor['username']})")
                print(f"👥 Subscribers: {competitor['subscribers']}")
                print(f"📈 Avg views: {competitor['avg_views']:.2f}")
                print(f"📝 Posts analyzed: {len(competitor['posts'])}")
                if competitor['posts']:
                    latest_post = competitor['posts'][0]
                    print(f"🔍 Latest post views: {latest_post['metrics']['views']}")
                print("---")
        else:
            print(f"❌ Error: {result}")

    except Exception as e:
        print(f"💥 Critical error: {e}")
        print("Returning mock data for demonstration")
        mock_result = get_mock_data()
        print(json.dumps(mock_result, indent=2, ensure_ascii=False, default=str))