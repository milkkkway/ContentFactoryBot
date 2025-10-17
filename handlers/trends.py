import logging
from typing import Dict, Any
from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from api.YouTubesTrends import (
    get_youtube_service,
    get_trending_videos,
    get_channel_info,
    calculate_virality_score,
    parse_published_at
)

from utilities.states import TrendsStates
from utilities.keyboards import (
    create_trends_region_keyboard,
    create_trends_navigation_keyboard,
    create_trend_details_keyboard,
    create_main_keyboard
)

logger = logging.getLogger(__name__)


trends_data_store: Dict[int, Dict[str, Any]] = {}


async def start_trends(message: Message, state: FSMContext):

    await message.answer(
        "📈 <b>Анализ YouTube трендов</b>\n\n"
        "Выберите регион для анализа трендов:",
        parse_mode='HTML',
        reply_markup=create_trends_region_keyboard()
    )
    await state.set_state(TrendsStates.waiting_region_trends)


async def process_trends_region(callback: CallbackQuery, state: FSMContext):

    region = callback.data.split("_")[2]
    user_id = callback.from_user.id

    await callback.message.edit_text(
        f"🌍 <b>Регион:</b> {region}\n\n"
        "⏳ <i>Ищу актуальные тренды... Это может занять несколько секунд.</i>",
        parse_mode='HTML'
    )

    try:

        youtube = get_youtube_service()
        if not youtube:
            raise Exception("Не удалось инициализировать YouTube API")


        trending_videos = get_trending_videos(youtube, region, max_results=15)

        if not trending_videos:
            await callback.message.edit_text(
                f"❌ <b>Не удалось получить тренды для региона {region}</b>\n\n"
                "Попробуйте выбрать другой регион.",
                parse_mode='HTML',
                reply_markup=create_trends_region_keyboard()
            )
            await callback.answer()
            return


        trends_data = []
        for video in trending_videos:
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
                    'description': video_snippet.get('description', '')[:200] + '...' if
                    len(video_snippet.get('description', '')) > 200 else
                    video_snippet.get('description', ''),
                    'published_at': video_snippet['publishedAt'],
                    'video_id': video['id'],
                    'link': f"https://www.youtube.com/watch?v={video['id']}",
                    'virality_score': round(virality_score, 2)
                },
                'metrics': stats_dict,
                'channel_info': channel_info
            }
            trends_data.append(video_data)


        trends_data.sort(key=lambda x: x['video_info']['virality_score'], reverse=True)

        if not trends_data:
            await callback.message.edit_text(
                f"❌ <b>Не удалось обработать тренды для региона {region}</b>\n\n"
                "Попробуйте выбрать другой регион.",
                parse_mode='HTML',
                reply_markup=create_trends_region_keyboard()
            )
            await callback.answer()
            return


        trends_data_store[user_id] = {
            'trends': trends_data,
            'current_trend_index': 0,
            'region': region
        }


        await show_trend(user_id, callback.message, state)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        await callback.message.edit_text(
            "❌ <b>Произошла ошибка при получении трендов</b>\n\n"
            "Попробуйте позже или выберите другой регион.",
            parse_mode='HTML',
            reply_markup=create_trends_region_keyboard()
        )
        await callback.answer()


async def show_trend(user_id: int, message: Message, state: FSMContext):

    user_data = trends_data_store.get(user_id)
    if not user_data or not user_data['trends']:
        await message.edit_text("❌ Данные трендов не найдены")
        return

    trends = user_data['trends']
    current_index = user_data['current_trend_index']
    region = user_data['region']

    if current_index >= len(trends):
        await message.edit_text(
            "✅ <b>Все тренды показаны!</b>\n\n"
            "Нажмите 'ТРЕНДЫ' для нового анализа.",
            parse_mode='HTML',
            reply_markup=create_main_keyboard()
        )
        await state.clear()
        return

    trend = trends[current_index]
    video_info = trend['video_info']
    metrics = trend['metrics']
    channel_info = trend['channel_info']


    trend_text = (
        f"📊 <b>Тренд {current_index + 1} из {len(trends)}</b>\n"
        f"🌍 <b>Регион:</b> {region}\n\n"
        f"🎬 <b>{video_info['title']}</b>\n\n"
        f"📈 <b>Виральность:</b> {video_info['virality_score']}\n"
        f"👁️ <b>Просмотры:</b> {metrics['views']:,}\n"
        f"👍 <b>Лайки:</b> {metrics['likes']:,}\n"
        f"💬 <b>Комментарии:</b> {metrics['comments']:,}\n\n"
        f"📺 <b>Канал:</b> {channel_info['title']}\n"
        f"👥 <b>Подписчики:</b> {channel_info['subscribers']:,}\n"
        f"📅 <b>Опубликовано:</b> {video_info['published_at'][:10]}"
    )

    await message.edit_text(
        trend_text,
        parse_mode='HTML',
        reply_markup=create_trends_navigation_keyboard(current_index, len(trends), region),
        disable_web_page_preview=True
    )

    await state.set_state(TrendsStates.viewing_trends)


async def show_next_trend(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    user_data = trends_data_store.get(user_id)

    if not user_data:
        await callback.answer("Данные устарели")
        return

    trends = user_data['trends']
    current_index = user_data['current_trend_index']

    if current_index >= len(trends) - 1:
        await callback.answer("Это последний тренд")
        return

    trends_data_store[user_id]['current_trend_index'] = current_index + 1

    await show_trend(user_id, callback.message, state)
    await callback.answer()


async def show_prev_trend(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    user_data = trends_data_store.get(user_id)

    if not user_data:
        await callback.answer("Данные устарели")
        return

    current_index = user_data['current_trend_index']

    if current_index <= 0:
        await callback.answer("Это первый тренд")
        return


    trends_data_store[user_id]['current_trend_index'] = current_index - 1


    await show_trend(user_id, callback.message, state)
    await callback.answer()


async def show_trend_details(callback: CallbackQuery, state: FSMContext):

    trend_index = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    user_data = trends_data_store.get(user_id)
    if not user_data:
        await callback.answer("Данные устарели")
        return

    trends = user_data['trends']
    region = user_data['region']

    if trend_index >= len(trends):
        await callback.answer("Тренд не найден")
        return


    trends_data_store[user_id]['current_trend_index'] = trend_index

    trend = trends[trend_index]
    video_info = trend['video_info']
    metrics = trend['metrics']
    channel_info = trend['channel_info']

    details_text = (
        f"📊 <b>Детальная информация</b>\n\n"
        f"🎬 <b>Название:</b> {video_info['title']}\n\n"
        f"📝 <b>Описание:</b>\n{video_info['description']}\n\n"
        f"📈 <b>Метрики:</b>\n"
        f"   • Виральность: {video_info['virality_score']}\n"
        f"   • Просмотры: {metrics['views']:,}\n"
        f"   • Лайки: {metrics['likes']:,}\n"
        f"   • Комментарии: {metrics['comments']:,}\n\n"
        f"📺 <b>Канал:</b>\n"
        f"   • Название: {channel_info['title']}\n"
        f"   • Подписчики: {channel_info['subscribers']:,}\n"
        f"   • Всего видео: {channel_info['video_count']:,}\n"
        f"   • Просмотры канала: {channel_info['total_views']:,}\n\n"
        f"🔗 <b>Ссылка:</b> {video_info['link']}\n"
        f"📅 <b>Опубликовано:</b> {video_info['published_at']}"
    )

    await callback.message.answer(
        details_text,
        parse_mode='HTML',
        reply_markup=create_trend_details_keyboard(
            trend_index,
            len(trends),
            region,
            video_info['link']
        ),
        disable_web_page_preview=True
    )
    await callback.answer()


async def change_trends_region(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "🌍 <b>Выберите новый регион для анализа трендов:</b>",
        parse_mode='HTML',
        reply_markup=create_trends_region_keyboard()
    )
    await state.set_state(TrendsStates.waiting_region_trends)
    await callback.answer()


async def back_to_trends_list(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    user_data = trends_data_store.get(user_id)

    if user_data:

        await show_trend(user_id, callback.message, state)
    else:
        await callback.message.edit_text(
            "❌ Данные устарели. Начните новый анализ трендов.",
            reply_markup=create_main_keyboard()
        )
        await state.clear()

    await callback.answer()


async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "🔙 Возвращаемся в главное меню",
        reply_markup=create_main_keyboard()
    )
    await state.clear()
    await callback.answer()


def register_trends_handlers(dp: Dispatcher):
    dp.message.register(start_trends, F.text == "ТРЕНДЫ")
    dp.callback_query.register(process_trends_region, F.data.startswith("trends_region_"))
    dp.callback_query.register(show_trend_details, F.data.startswith("trend_details_"))
    dp.callback_query.register(show_next_trend, F.data.startswith("next_trend_"))
    dp.callback_query.register(show_prev_trend, F.data.startswith("prev_trend_"))
    dp.callback_query.register(change_trends_region, F.data == "change_trends_region")
    dp.callback_query.register(back_to_trends_list, F.data == "back_to_trends_list")
    dp.callback_query.register(back_to_main_menu, F.data == "back_to_main")