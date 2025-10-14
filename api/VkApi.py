import requests
import json
from datetime import datetime

# --- SETTINGS ---
ACCESS_TOKEN = "99f02e9699f02e9699f02e96849acba814999f099f02e96f11ce8981b2b7c76307dba98"  # Замените на ваш токен VK API
API_VERSION = "5.131"
BASE_URL = "https://api.vk.com/method/"


# --- INIT ---
def get_vk_session():
    """Инициализация сессии для VK API"""
    try:
        # Проверяем доступность токена
        test_response = requests.get(
            f"{BASE_URL}users.get",
            params={
                "access_token": ACCESS_TOKEN,
                "v": API_VERSION
            }
        )
        if test_response.json().get('error'):
            return None
        return True
    except Exception as e:
        print(f"Ошибка инициализации VK API: {e}")
        return None


# --- SEARCH GROUPS (аналог поиска каналов) ---
def search_groups(query, country_code, max_results=10):
    """Поиск групп по ключевому слову и стране"""
    try:
        response = requests.get(
            f"{BASE_URL}groups.search",
            params={
                "q": query,
                "country_id": get_country_id(country_code),
                "count": max_results,
                "access_token": ACCESS_TOKEN,
                "v": API_VERSION
            }
        )

        data = response.json()
        if 'error' in data:
            print(f"Ошибка VK API: {data['error']['error_msg']}")
            return []

        return data.get('response', {}).get('items', [])
    except Exception as e:
        print(f"Ошибка при поиске групп: {e}")
        return []


def get_country_id(country_code):
    """Получение ID страны по коду"""
    country_map = {
        "RU": 1,  # Россия
        "US": 2,  # США
        # Добавьте другие страны по необходимости
    }
    return country_map.get(country_code, 1)  # По умолчанию Россия


# --- GET GROUP STATS ---
def get_group_stats(group_id):
    """Получение статистики группы"""
    try:
        # Получаем основную информацию о группе
        group_response = requests.get(
            f"{BASE_URL}groups.getById",
            params={
                "group_ids": abs(group_id),  # Используем абсолютное значение для group_id
                "fields": "members_count,description,status",
                "access_token": ACCESS_TOKEN,
                "v": API_VERSION
            }
        )

        group_data = group_response.json()
        if 'error' in group_data or not group_data.get('response'):
            return None

        group_info = group_data['response'][0]

        stats = {
            'title': group_info.get('name', ''),
            'description': group_info.get('description', ''),
            'subscriberCount': group_info.get('members_count', 0),
            'postCount': 0,  # Будет получено отдельно
            'avg_views': 0
        }
        return stats
    except Exception as e:
        print(f"Ошибка при получении статистики группы {group_id}: {e}")
        return None


# --- GET POSTS FROM GROUP ---
def get_group_posts(group_id, max_posts):
    """Получение постов из группы"""
    try:
        # Получаем посты со стены группы
        posts_response = requests.get(
            f"{BASE_URL}wall.get",
            params={
                "owner_id": group_id,  # Для групп owner_id отрицательный
                "count": max_posts,
                "extended": 1,
                "fields": "views,likes,comments",
                "access_token": ACCESS_TOKEN,
                "v": API_VERSION
            }
        )

        data = posts_response.json()
        if 'error' in data:
            print(f"Ошибка при получении постов: {data['error']['error_msg']}")
            return []

        return data.get('response', {}).get('items', [])
    except Exception as e:
        print(f"Ошибка при получении постов группы {group_id}: {e}")
        return []


def calculate_avg_views_vk(channel_data):
    """Расчет среднего количества просмотров для VK"""
    total_views = 0
    video_count = len(channel_data["posts"])

    for post in channel_data["posts"]:
        total_views += post["metrics"]["views"]

    channel_data["avg_views"] = total_views / video_count if video_count > 0 else 0
    return channel_data


def get_post_count(group_id):
    """Получение общего количества постов в группе"""
    try:
        response = requests.get(
            f"{BASE_URL}wall.get",
            params={
                "owner_id": group_id,
                "count": 1,  # Получаем только 1 пост, но в ответе есть общее количество
                "access_token": ACCESS_TOKEN,
                "v": API_VERSION
            }
        )

        data = response.json()
        if 'error' in data:
            return 0

        return data.get('response', {}).get('count', 0)
    except Exception as e:
        print(f"Ошибка при получении количества постов: {e}")
        return 0


def main_vk(search_query, region, num_posts, min_subscribers, min_posts):
    """
    Основная функция для VK API
    search_query - ключевые слова
    region - страна (RU, US)
    num_posts - количество постов для анализа
    min_subscribers - минимальное количество подписчиков
    min_posts - минимальное количество постов в группе
    """

    # Инициализация
    vk_session = get_vk_session()
    if not vk_session:
        return "VK INIT ERROR"

    # Поиск групп
    found_groups = search_groups(query=search_query, country_code=region, max_results=25)
    if not found_groups:
        return "GROUPS DIDN'T FOUND"

    competitors = []

    # Фильтрация по подписчикам и количеству постов
    for group in found_groups:
        group_id = -group['id']  # VK использует отрицательные ID для групп
        stats = get_group_stats(group_id)

        if stats:
            # Получаем общее количество постов в группе
            total_posts = get_post_count(group_id)
            stats['postCount'] = total_posts

            if stats['subscriberCount'] >= min_subscribers and total_posts >= min_posts:
                competitors.append({
                    'id': group_id,
                    'title': stats['title'],
                    'subscribers': stats['subscriberCount']
                })

    if not competitors:
        return []

    # Сбор данных о постах
    all_competitor_data = []

    for competitor in competitors:
        channel_data = {
            "channel_title": competitor['title'],
            "channel_id": str(competitor['id']),
            "subscribers": competitor['subscribers'],
            "avg_views": 0,
            "posts": []
        }

        posts = get_group_posts(competitor['id'], num_posts)

        if not posts:
            continue

        for post in posts:
            # Пропускаем рекламные посты и пустые
            if post.get('marked_as_ads') or not post.get('text'):
                continue

            # Извлекаем хэштеги из текста
            hashtags = []
            words = post['text'].split()
            for word in words:
                if word.startswith('#'):
                    hashtags.append(word[1:])  # Убираем символ #

            # Получаем метрики
            views = post.get('views', {}).get('count', 0) if post.get('views') else 0
            likes = post.get('likes', {}).get('count', 0) if post.get('likes') else 0
            comments = post.get('comments', {}).get('count', 0) if post.get('comments') else 0

            post_info = {
                "published_at": datetime.fromtimestamp(post['date']).isoformat() + 'Z',
                "title": post['text'][:100] + "..." if len(post['text']) > 100 else post['text'],
                # Используем начало текста как заголовок
                "description": post['text'],
                "tags/hashtags": hashtags,
                "link": f"https://vk.com/wall{post['owner_id']}_{post['id']}",
                "metrics": {
                    "views": views,
                    "likes": likes,
                    "comments": comments
                }
            }
            channel_data["posts"].append(post_info)

        channel_data = calculate_avg_views_vk(channel_data)
        all_competitor_data.append(channel_data)

    return all_competitor_data


# Пример использования
if __name__ == "__main__":
    result = main_vk(
        search_query="технологии",
        region="RU",
        num_posts=10,
        min_subscribers=10000,
        min_posts=50
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))