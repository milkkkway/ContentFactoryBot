import logging
from typing import Dict, Any
from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from utilities.states import DraftStates
from utilities.keyboards import (
    create_main_keyboard,
    create_draft_actions_keyboard,
    create_drafts_list_keyboard,
    create_cancel_keyboard
)
from db.draft_manager import DraftManager

logger = logging.getLogger(__name__)


draft_temp_store: Dict[int, Dict[str, Any]] = {}


draft_manager = DraftManager()


async def start_create_draft(message: Message, state: FSMContext):

    user_id = message.from_user.id

    await message.answer(
        "📝 <b>Создание нового черновика</b>\n\n"
        "Пожалуйста, загрузите фото или видео для вашего поста:",
        parse_mode='HTML',
        reply_markup=create_cancel_keyboard()
    )
    await state.set_state(DraftStates.waiting_media)


async def process_media(message: Message, state: FSMContext):

    user_id = message.from_user.id
    media_file_id = None
    media_type = None

    if message.photo:
        media_file_id = message.photo[-1].file_id
        media_type = 'photo'
    elif message.video:
        media_file_id = message.video.file_id
        media_type = 'video'
    else:
        await message.answer(
            "❌ Пожалуйста, загрузите фото или видео.\n"
            "Поддерживаются только изображения и видеофайлы.",
            reply_markup=create_cancel_keyboard()
        )
        return


    draft_temp_store[user_id] = {
        'media_file_id': media_file_id,
        'media_type': media_type
    }

    await message.answer(
        "✅ Медиафайл получен!\n\n"
        "📌 Теперь введите заголовок для вашего поста:",
        reply_markup=create_cancel_keyboard()
    )
    await state.set_state(DraftStates.waiting_title)


async def process_title(message: Message, state: FSMContext):

    user_id = message.from_user.id
    title = message.text.strip()

    if len(title) < 2:
        await message.answer(
            "❌ Заголовок должен содержать минимум 2 символа.\n"
            "Пожалуйста, введите заголовок еще раз:",
            reply_markup=create_cancel_keyboard()
        )
        return

    if len(title) > 255:
        await message.answer(
            "❌ Заголовок слишком длинный (максимум 255 символов).\n"
            "Пожалуйста, введите более короткий заголовок:",
            reply_markup=create_cancel_keyboard()
        )
        return


    if user_id not in draft_temp_store:
        draft_temp_store[user_id] = {}
    draft_temp_store[user_id]['title'] = title

    await message.answer(
        "✅ Заголовок сохранен!\n\n"
        "📝 Теперь введите описание для вашего поста "
        "(или отправьте '-' чтобы пропустить):",
        reply_markup=create_cancel_keyboard()
    )
    await state.set_state(DraftStates.waiting_description)


async def process_description(message: Message, state: FSMContext):

    user_id = message.from_user.id
    description = message.text.strip()

    if description == '-':
        description = ""


    draft_data = draft_temp_store.get(user_id)
    if not draft_data:
        await message.answer(
            "❌ Произошла ошибка. Начните создание черновика заново.",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
        return


    if not draft_manager.connect():
        await message.answer(
            "❌ Ошибка подключения к базе данных. Попробуйте позже.",
            reply_markup=create_main_keyboard()
        )
        await state.clear()
        return

    try:

        draft = draft_manager.create_draft(
            user_id=user_id,
            username=message.from_user.username or f"user_{user_id}",
            title=draft_data['title'],
            description=description,
            media_type=draft_data['media_type'],
            media_file_id=draft_data['media_file_id']
        )

        if draft:

            if user_id in draft_temp_store:
                del draft_temp_store[user_id]

            await message.answer(
                f"✅ <b>Черновик успешно создан!</b>\n\n"
                f"📌 <b>Заголовок:</b> {draft['title']}\n"
                f"📝 <b>Описание:</b> {draft['description'] or 'Не указано'}\n"
                f"🖼️ <b>Тип медиа:</b> {'Фото' if draft['media_type'] == 'photo' else 'Видео'}\n"
                f"📅 <b>Создан:</b> {draft['created_at'].strftime('%d.%m.%Y %H:%M')}",
                parse_mode='HTML',
                reply_markup=create_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Не удалось сохранить черновик. Попробуйте позже.",
                reply_markup=create_main_keyboard()
            )

    except Exception as e:
        logger.error(f"Error creating draft: {e}")
        await message.answer(
            "❌ Произошла ошибка при сохранении черновика.",
            reply_markup=create_main_keyboard()
        )
    finally:
        draft_manager.close_connection()
        await state.clear()


async def show_my_drafts(message: Message, state: FSMContext):

    user_id = message.from_user.id

    if not draft_manager.connect():
        await message.answer(
            "❌ Ошибка подключения к базе данных. Попробуйте позже.",
            reply_markup=create_main_keyboard()
        )
        return

    try:

        drafts = draft_manager.get_user_drafts(user_id)

        if not drafts:
            await message.answer(
                "📭 У вас пока нет черновиков.\n\n"
                "Создайте первый черновик, нажав кнопку «Создать черновик»",
                reply_markup=create_main_keyboard()
            )
            return

        await message.answer(
            f"📂 <b>Ваши черновики</b> (всего: {len(drafts)})\n\n"
            "Выберите черновик для просмотра:",
            parse_mode='HTML',
            reply_markup=create_drafts_list_keyboard(drafts)
        )

        await state.set_state(DraftStates.viewing_drafts)

    except Exception as e:
        logger.error(f"Error getting drafts: {e}")
        await message.answer(
            "❌ Произошла ошибка при загрузке черновиков.",
            reply_markup=create_main_keyboard()
        )
    finally:
        draft_manager.close_connection()


async def show_draft_details(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    draft_id = int(callback.data.split("_")[2])

    if not draft_manager.connect():
        await callback.message.answer(
            "❌ Ошибка подключения к базе данных.",
            reply_markup=create_main_keyboard()
        )
        await callback.answer()
        return

    try:

        draft = draft_manager.get_draft_by_id(draft_id, user_id)

        if not draft:
            await callback.message.answer(
                "❌ Черновик не найден или у вас нет доступа к нему.",
                reply_markup=create_main_keyboard()
            )
            await callback.answer()
            return


        draft_text = (
            f"📄 <b>Черновик #{draft['id']}</b>\n\n"
            f"📌 <b>Заголовок:</b> {draft['title']}\n"
            f"📝 <b>Описание:</b> {draft['description'] or 'Не указано'}\n"
            f"🖼️ <b>Тип медиа:</b> {'Фото' if draft['media_type'] == 'photo' else 'Видео'}\n"
            f"📅 <b>Создан:</b> {draft['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
            f"👤 <b>Автор:</b> {draft['username']}"
        )

        if draft['media_type'] == 'photo':
            await callback.message.answer_photo(
                photo=draft['media_file_id'],
                caption=draft_text,
                parse_mode='HTML',
                reply_markup=create_draft_actions_keyboard(draft_id)
            )
        else:
            await callback.message.answer_video(
                video=draft['media_file_id'],
                caption=draft_text,
                parse_mode='HTML',
                reply_markup=create_draft_actions_keyboard(draft_id)
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing draft: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при загрузке черновика.",
            reply_markup=create_main_keyboard()
        )
        await callback.answer()
    finally:
        draft_manager.close_connection()




async def handle_drafts_pagination(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    page = int(callback.data.split("_")[2])

    if not draft_manager.connect():
        await callback.answer("Ошибка подключения")
        return

    try:
        drafts = draft_manager.get_user_drafts(user_id)
        await callback.message.edit_reply_markup(
            reply_markup=create_drafts_list_keyboard(drafts, page)
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error paginating drafts: {e}")
        await callback.answer("Ошибка")
    finally:
        draft_manager.close_connection()


async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "🔙 Возвращаемся в главное меню",
        reply_markup=create_main_keyboard()
    )
    await state.clear()
    await callback.answer()


async def back_to_drafts_list(callback: CallbackQuery, state: FSMContext):

    await show_my_drafts(callback.message, state)
    await callback.answer()


async def cancel_draft_creation(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id


    if user_id in draft_temp_store:
        del draft_temp_store[user_id]

    await callback.message.answer(
        "❌ Создание черновика отменено.",
        reply_markup=create_main_keyboard()
    )
    await state.clear()
    await callback.answer()


async def delete_draft(callback: CallbackQuery, state: FSMContext):

    user_id = callback.from_user.id
    draft_id = int(callback.data.split("_")[2])

    if not draft_manager.connect():
        await callback.message.answer(
            "❌ Ошибка подключения к базе данных.",
            reply_markup=create_main_keyboard()
        )
        await callback.answer()
        return

    try:
        success = draft_manager.delete_draft(
            draft_id=draft_id,
            user_id=user_id,
            user_role='user'
        )

        if success:
            await callback.message.answer(
                "✅ Черновик успешно удален!",
                reply_markup=create_main_keyboard()
            )
        else:
            await callback.message.answer(
                "❌ Не удалось удалить черновик. Возможно, он не существует или у вас нет прав.",
                reply_markup=create_main_keyboard()
            )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error deleting draft: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при удалении черновика.",
            reply_markup=create_main_keyboard()
        )
        await callback.answer()
    finally:
        draft_manager.close_connection()


def register_draft_handlers(dp: Dispatcher):
    dp.message.register(start_create_draft, F.text == "📝 Создать черновик")
    dp.message.register(show_my_drafts, F.text == "📂 Мои черновики")

    dp.message.register(process_media, DraftStates.waiting_media)
    dp.message.register(process_title, DraftStates.waiting_title)
    dp.message.register(process_description, DraftStates.waiting_description)


    dp.callback_query.register(show_draft_details, F.data.startswith("view_draft_"))
    dp.callback_query.register(handle_drafts_pagination, F.data.startswith("drafts_page_"))
    dp.callback_query.register(delete_draft, F.data.startswith("delete_draft_"))
    dp.callback_query.register(back_to_main_menu, F.data == "back_to_main")
    dp.callback_query.register(back_to_drafts_list, F.data == "back_to_drafts")
    dp.callback_query.register(cancel_draft_creation, F.data == "cancel_draft")