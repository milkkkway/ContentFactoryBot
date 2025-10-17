import logging
from typing import Dict, Any
from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import api.YouTubeApi as YouTubeApi
from utilities.states import StatsStates
from utilities.keyboards import (
    create_region_keyboard,
    create_channel_navigation_keyboard
)
from utilities.formatters import format_number, format_channel_message, format_video_message

logger = logging.getLogger(__name__)

user_data_store: Dict[int, Dict[str, Any]] = {}


async def start_statistics(message: Message, state: FSMContext):
    await message.answer(
        "🔍 <b>Введите ключевые слова для поиска каналов:</b>\n\n"
        "<i>Пример: технологические обзоры, программирование, гейминг</i>",
        parse_mode='HTML'
    )
    await state.set_state(StatsStates.waiting_keyword)

async def process_keyword(message: Message, state: FSMContext):

    keyword = message.text.strip()

    if len(keyword) < 2:
        await message.answer("❌ <b>Слишком короткий запрос.</b> Введите минимум 2 символа:", parse_mode='HTML')
        return

    await state.update_data(keyword=keyword)
    await message.answer(
        "🌍 <b>Выберите регион для поиска:</b>",
        reply_markup=create_region_keyboard(),
        parse_mode='HTML'
    )
    await state.set_state(StatsStates.waiting_region)

async def process_region(callback: CallbackQuery, state: FSMContext):

    region = callback.data.split("_")[1]
    await state.update_data(region=region)

    await callback.message.edit_text(
        f"🌍 <b>Регион:</b> {region}\n\n"
        "📊 <b>Сколько последних видео анализировать для каждого канала?</b>\n\n"
        "<i>Рекомендуется: 5-10 видео для быстрого анализа</i>",
        parse_mode='HTML'
    )

    await callback.answer()
    await state.set_state(StatsStates.waiting_num_posts)

async def process_num_posts(message: Message, state: FSMContext):

    try:
        num_posts = int(message.text)
        if num_posts < 1 or num_posts > 50:
            await message.answer("❌ <b>Введите число от 1 до 50:</b>", parse_mode='HTML')
            return
    except ValueError:
        await message.answer("❌ <b>Пожалуйста, введите целое число:</b>", parse_mode='HTML')
        return

    await state.update_data(num_posts=num_posts)
    await message.answer(
        "👥 <b>Минимальное количество подписчиков для фильтрации:</b>\n\n"
        "<i>Пример: 10000 - только каналы с 10К+ подписчиков</i>",
        parse_mode='HTML'
    )
    await state.set_state(StatsStates.waiting_min_subs)

async def process_min_subs(message: Message, state: FSMContext):

    try:
        min_subs = int(message.text)
        if min_subs < 0:
            await message.answer("❌ <b>Число должно быть положительным:</b>", parse_mode='HTML')
            return
    except ValueError:
        await message.answer("❌ <b>Пожалуйста, введите целое число:</b>", parse_mode='HTML')
        return

    await state.update_data(min_subs=min_subs)
    await message.answer(
        "🎬 <b>Минимальное количество видео у канала:</b>\n\n"
        "<i>Пример: 10 - исключает новые каналы с малым количеством контента</i>",
        parse_mode='HTML'
    )
    await state.set_state(StatsStates.waiting_min_vids)

async def process_min_vids(message: Message, state: FSMContext):

    try:
        min_vids = int(message.text)
        if min_vids < 0:
            await message.answer("❌ <b>Число должно быть положительным:</b>", parse_mode='HTML')
            return
    except ValueError:
        await message.answer("❌ <b>Пожалуйста, введите целое число:</b>", parse_mode='HTML')
        return


    user_data = await state.get_data()
    await state.update_data(min_vids=min_vids)


    summary_text = (
        "✅ <b>Параметры анализа:</b>\n\n"
        f"🔍 <b>Ключевые слова:</b> {user_data['keyword']}\n"
        f"🌍 <b>Регион:</b> {user_data['region']}\n"
        f"📊 <b>Видео для анализа:</b> {user_data['num_posts']}\n"
        f"👥 <b>Мин. подписчики:</b> {format_number(user_data['min_subs'])}\n"
        f"🎬 <b>Мин. видео:</b> {min_vids}\n\n"
        "⏳ <i>Запускаю анализ... Это может занять несколько минут.</i>"
    )

    progress_msg = await message.answer(summary_text, parse_mode='HTML')

    try:

        results = YouTubeApi.main(
            search_query=user_data['keyword'],
            region=user_data['region'],
            num_posts=user_data['num_posts'],
            min_subscribers=user_data['min_subs'],
            min_videos=min_vids
        )


        user_data_store[message.from_user.id] = {
            'channels': results,
            'current_channel_index': 0
        }

        if not results or (isinstance(results, str) and "ERROR" in results):
            await progress_msg.edit_text(
                "❌ <b>Не удалось найти каналы по вашему запросу.</b>\n\n"
                "Попробуйте изменить параметры поиска.",
                parse_mode='HTML'
            )
            await state.clear()
            return

        if isinstance(results, str):
            await progress_msg.edit_text(
                f"❌ <b>Ошибка:</b> {results}",
                parse_mode='HTML'
            )
            await state.clear()
            return


        await show_channel(message.from_user.id, progress_msg, state)

    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        await progress_msg.edit_text(
            "❌ <b>Произошла ошибка при анализе.</b>\n\n"
            "Попробуйте позже или измените параметры поиска.",
            parse_mode='HTML'
        )
        await state.clear()

async def show_channel(user_id: int, message: Message, state: FSMContext):

    user_data = user_data_store.get(user_id)
    if not user_data or not user_data['channels']:
        await message.edit_text("❌ Данные не найдены")
        return

    channels = user_data['channels']
    current_index = user_data['current_channel_index']

    if current_index >= len(channels):
        await message.edit_text(
            "✅ <b>Анализ завершен!</b>\n\n"
            "Все каналы показаны. Нажмите /start для нового анализа.",
            parse_mode='HTML'
        )
        await state.clear()
        return

    channel = channels[current_index]
    channel_text = format_channel_message(channel)


    channel_text = (
        f"📊 <b>Канал {current_index + 1} из {len(channels)}</b>\n\n"
        f"{channel_text}"
    )

    await message.edit_text(
        channel_text,
        reply_markup=create_channel_navigation_keyboard(current_index, len(channels)),
        parse_mode='HTML'
    )

    await state.set_state(StatsStates.showing_results)

async def show_next_channel(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    user_data = user_data_store.get(user_id)

    if not user_data:
        await callback.answer("Данные устарели")
        return

    channels = user_data['channels']
    current_index = user_data['current_channel_index']

    if current_index >= len(channels) - 1:
        await callback.answer("Это последний канал")
        return


    user_data_store[user_id]['current_channel_index'] = current_index + 1

    await show_channel(user_id, callback.message, state)
    await callback.answer()

async def show_prev_channel(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = user_data_store.get(user_id)

    if not user_data:
        await callback.answer("Данные устарели")
        return

    current_index = user_data['current_channel_index']

    if current_index <= 0:
        await callback.answer("Это первый канал")
        return

    user_data_store[user_id]['current_channel_index'] = current_index - 1

    await show_channel(user_id, callback.message, state)
    await callback.answer()

async def show_channel_details(callback: CallbackQuery, state: FSMContext):
    channel_index = int(callback.data.split("_")[2])
    user_id = callback.from_user.id

    user_data = user_data_store.get(user_id)
    if not user_data:
        await callback.answer("Данные устарели, начните новый анализ")
        return

    channels = user_data['channels']
    if channel_index >= len(channels):
        await callback.answer("Канал не найден")
        return


    user_data_store[user_id]['current_channel_index'] = channel_index

    channel = channels[channel_index]
    videos = channel['posts']

    if not videos:
        await callback.message.answer(
            "❌ <b>Нет данных о видео для этого канала</b>",
            parse_mode='HTML'
        )
        return


    video = videos[0]
    video_text = (
        f"🎬 <b>{channel['channel_title']}</b>\n"
        f"📹 <b>Видео 1 из {len(videos)}</b>\n\n"
        f"{format_video_message(video)}"
    )

    user_data_store[user_id]['current_video_index'] = 0
    user_data_store[user_id]['current_channel_details'] = channel_index

    builder = InlineKeyboardBuilder()
    if len(videos) > 1:
        builder.row(InlineKeyboardButton(
            text="➡️ Следующее видео",
            callback_data=f"next_video_{channel_index}"
        ))
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад к каналам",
        callback_data="back_to_channels"
    ))

    await callback.message.answer(
        video_text,
        reply_markup=builder.as_markup(),
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    await callback.answer()

async def show_next_video(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = user_data_store.get(user_id)

    if not user_data:
        await callback.answer("Данные устарели")
        return

    channel_index = user_data.get('current_channel_details')
    if channel_index is None:
        await callback.answer("Ошибка навигации")
        return

    channel = user_data['channels'][channel_index]
    videos = channel['posts']
    current_video_index = user_data.get('current_video_index', 0) + 1

    if current_video_index >= len(videos):
        await callback.answer("Это последнее видео")
        return

    user_data_store[user_id]['current_video_index'] = current_video_index

    video = videos[current_video_index]
    video_text = (
        f"🎬 <b>{channel['channel_title']}</b>\n"
        f"📹 <b>Видео {current_video_index + 1} из {len(videos)}</b>\n\n"
        f"{format_video_message(video)}"
    )

    builder = InlineKeyboardBuilder()

    if current_video_index > 0:
        builder.row(
            InlineKeyboardButton(text="⬅️ Предыдущее", callback_data=f"prev_video_{channel_index}"),
            InlineKeyboardButton(text="➡️ Следующее", callback_data=f"next_video_{channel_index}")
        )
    else:
        builder.row(InlineKeyboardButton(text="➡️ Следующее", callback_data=f"next_video_{channel_index}"))

    builder.row(InlineKeyboardButton(text="⬅️ Назад к каналам", callback_data="back_to_channels"))

    await callback.message.edit_text(
        video_text,
        reply_markup=builder.as_markup(),
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    await callback.answer()

async def show_prev_video(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_data = user_data_store.get(user_id)

    if not user_data:
        await callback.answer("Данные устарели")
        return

    channel_index = user_data.get('current_channel_details')
    if channel_index is None:
        await callback.answer("Ошибка навигации")
        return

    current_video_index = user_data.get('current_video_index', 0) - 1

    if current_video_index < 0:
        await callback.answer("Это первое видео")
        return

    user_data_store[user_id]['current_video_index'] = current_video_index

    channel = user_data['channels'][channel_index]
    videos = channel['posts']
    video = videos[current_video_index]

    video_text = (
        f"🎬 <b>{channel['channel_title']}</b>\n"
        f"📹 <b>Видео {current_video_index + 1} из {len(videos)}</b>\n\n"
        f"{format_video_message(video)}"
    )

    builder = InlineKeyboardBuilder()

    if current_video_index < len(videos) - 1:
        builder.row(
            InlineKeyboardButton(text="⬅️ Предыдущее", callback_data=f"prev_video_{channel_index}"),
            InlineKeyboardButton(text="➡️ Следующее", callback_data=f"next_video_{channel_index}")
        )
    else:
        builder.row(InlineKeyboardButton(text="⬅️ Предыдущее", callback_data=f"prev_video_{channel_index}"))

    builder.row(InlineKeyboardButton(text="⬅️ Назад к каналам", callback_data="back_to_channels"))

    await callback.message.edit_text(
        video_text,
        reply_markup=builder.as_markup(),
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    await callback.answer()

async def trend_search(message: Message, state: FSMContext):
    from handlers.trends import start_trends
    await start_trends(message, state)

async def back_to_channels(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_data = user_data_store.get(user_id)

    if user_data:
        await show_channel(user_id, callback.message, state)
    else:
        await callback.message.edit_text(
            "❌ Данные устарели. Начните новый анализ с помощью /start",
            parse_mode='HTML'
        )
        await state.clear()

    await callback.answer()

def register_statistics_handlers(dp: Dispatcher):
    dp.message.register(start_statistics, F.text == "📊 СТАТИСТИКА ПО ПАРАМЕТРАМ")
    dp.message.register(trend_search, F.text == "ТРЕНДЫ")
    dp.message.register(process_keyword, StatsStates.waiting_keyword)
    dp.message.register(process_num_posts, StatsStates.waiting_num_posts)
    dp.message.register(process_min_subs, StatsStates.waiting_min_subs)
    dp.message.register(process_min_vids, StatsStates.waiting_min_vids)
    dp.callback_query.register(process_region, F.data.startswith("region_"))
    dp.callback_query.register(show_channel_details, F.data.startswith("channel_details_"))
    dp.callback_query.register(show_next_video, F.data.startswith("next_video_"))
    dp.callback_query.register(show_prev_video, F.data.startswith("prev_video_"))
    dp.callback_query.register(back_to_channels, F.data == "back_to_channels")
    dp.callback_query.register(show_next_channel, F.data.startswith("next_channel_"))
    dp.callback_query.register(show_prev_channel, F.data.startswith("prev_channel_"))