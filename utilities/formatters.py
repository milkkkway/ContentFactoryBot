from typing import Dict, Any
from datetime import datetime

def format_number(num: int) -> str:
    """Форматирует числа с разделителями"""
    return f"{num:,}".replace(",", " ")

def format_channel_message(channel: Dict[str, Any]) -> str:
    """Форматирует сообщение с информацией о канале"""
    message = (
        f"🎬 <b>{channel['channel_title']}</b>\n"
        f"👥 <b>Подписчики:</b> {format_number(channel['subscribers'])}\n"
        f"📊 <b>Средние просмотры:</b> {format_number(int(channel['avg_views']))}\n"
        f"📈 <b>Видео для анализа:</b> {len(channel['posts'])}\n"
        f"🆔 <code>{channel['channel_id']}</code>"
    )
    return message

def format_video_message(video: Dict[str, Any]) -> str:
    """Форматирует сообщение с информацией о видео"""
    published_date = datetime.fromisoformat(video['published_at'].replace('Z', '+00:00'))
    formatted_date = published_date.strftime("%d.%m.%Y %H:%M")

    message = (
        f"📹 <b>{video['title'][:100]}{'...' if len(video['title']) > 100 else ''}</b>\n"
        f"📅 <b>Опубликовано:</b> {formatted_date}\n"
        f"👀 <b>Просмотры:</b> {format_number(video['metrics']['views'])}\n"
        f"❤️ <b>Лайки:</b> {format_number(video['metrics']['likes'])}\n"
        f"💬 <b>Комментарии:</b> {format_number(video['metrics']['comments'])}\n"
        f"🔗 <a href='{video['link']}'>Смотреть на YouTube</a>"
    )

    if video['tags/hashtags']:
        tags = " ".join([f"#{tag}" for tag in video['tags/hashtags'][:5]])
        message += f"\n🏷️ <b>Теги:</b> {tags}"

    return message