import logging
from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from utilities.states import AuthStates
from utilities.keyboards import create_main_keyboard, create_cancel_keyboard, create_login_keyboard
from db.user_manager import UserManager

logger = logging.getLogger(__name__)
user_manager = UserManager()


async def start_login(message: Message, state: FSMContext):
    """Начало процесса входа"""
    await message.answer(
        "🔐 <b>Вход в систему</b>\n\n"
        "Введите ваш логин:",
        parse_mode='HTML',
        reply_markup=create_cancel_keyboard()
    )
    await state.set_state(AuthStates.waiting_username)


async def process_username(message: Message, state: FSMContext):
    """Обработка введенного логина"""
    username = message.text.strip()

    if len(username) < 3:
        await message.answer(
            "❌ Логин должен содержать минимум 3 символа.\n"
            "Введите логин еще раз:",
            reply_markup=create_cancel_keyboard()
        )
        return

    await state.update_data(username=username)

    await message.answer(
        "🔐 Теперь введите ваш пароль:",
        reply_markup=create_cancel_keyboard()
    )
    await state.set_state(AuthStates.waiting_password)


async def process_password(message: Message, state: FSMContext):
    """Обработка введенного пароля и авторизация"""
    password = message.text.strip()
    user_data = await state.get_data()
    username = user_data['username']
    telegram_id = message.from_user.id

    if not user_manager.connect():
        await message.answer(
            "❌ Ошибка подключения к базе данных. Попробуйте позже.",
            reply_markup=create_login_keyboard()
        )
        await state.clear()
        return

    try:
        # Проверяем существование пользователя
        if user_manager.check_user_exists(username=username, psswrd=password):
            # Получаем данные пользователя
            user_db_data = user_manager.get_user_by_username(username)

            if user_db_data and not user_db_data.get('telegram_id'):
                # Обновляем пользователя, добавляя telegram_id
                user_manager.update_user_telegram_id(username, telegram_id)
                logger.info(f"✅ Telegram ID {telegram_id} добавлен для пользователя {username}")

            await message.answer(
                f"✅ <b>Успешный вход!</b>\n\n"
                f"👋 Добро пожаловать, {username}!\n"
                f"Теперь вы можете создавать и просматривать свои черновики.",
                parse_mode='HTML',
                reply_markup=create_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Неверный логин или пароль.\n\n"
                "Попробуйте войти еще раз или создайте нового пользователя.",
                reply_markup=create_login_keyboard()
            )

    except Exception as e:
        logger.error(f"Error during login: {e}")
        await message.answer(
            "❌ Произошла ошибка при входе. Попробуйте позже.",
            reply_markup=create_login_keyboard()
        )
    finally:
        user_manager.close_connection()
        await state.clear()


async def start_register(message: Message, state: FSMContext):
    """Начало процесса регистрации"""
    await message.answer(
        "📝 <b>Регистрация нового пользователя</b>\n\n"
        "Придумайте и введите ваш логин:",
        parse_mode='HTML',
        reply_markup=create_cancel_keyboard()
    )
    await state.set_state(AuthStates.waiting_new_username)


async def process_new_username(message: Message, state: FSMContext):
    """Обработка нового логина"""
    username = message.text.strip()

    if len(username) < 3:
        await message.answer(
            "❌ Логин должен содержать минимум 3 символа.\n"
            "Введите логин еще раз:",
            reply_markup=create_cancel_keyboard()
        )
        return

    if not user_manager.connect():
        await message.answer(
            "❌ Ошибка подключения к базе данных. Попробуйте позже.",
            reply_markup=create_login_keyboard()
        )
        await state.clear()
        return

    try:
        # Проверяем, не занят ли логин
        if user_manager.check_user_exists(username=username):
            await message.answer(
                "❌ Пользователь с таким логином уже существует.\n"
                "Придумайте другой логин:",
                reply_markup=create_cancel_keyboard()
            )
            return

        await state.update_data(username=username)

        await message.answer(
            "🔐 Придумайте и введите ваш пароль:",
            reply_markup=create_cancel_keyboard()
        )
        await state.set_state(AuthStates.waiting_new_password)

    except Exception as e:
        logger.error(f"Error checking username: {e}")
        await message.answer(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=create_login_keyboard()
        )
        await state.clear()
    finally:
        user_manager.close_connection()


async def process_new_password(message: Message, state: FSMContext):
    """Обработка нового пароля и создание пользователя"""
    password = message.text.strip()
    user_data = await state.get_data()
    username = user_data['username']
    telegram_id = message.from_user.id

    if len(password) < 4:
        await message.answer(
            "❌ Пароль должен содержать минимум 4 символа.\n"
            "Введите пароль еще раз:",
            reply_markup=create_cancel_keyboard()
        )
        return

    if not user_manager.connect():
        await message.answer(
            "❌ Ошибка подключения к базе данных. Попробуйте позже.",
            reply_markup=create_login_keyboard()
        )
        await state.clear()
        return

    try:
        # Создаем пользователя с telegram_id
        if user_manager.create_user(
                username=username,
                psswrd=password,
                telegram_id=telegram_id,
                role='user'
        ):
            await message.answer(
                f"🎉 <b>Регистрация успешна!</b>\n\n"
                f"✅ Пользователь <b>{username}</b> создан.\n"
                f"🔐 Теперь вы можете войти в систему.",
                parse_mode='HTML',
                reply_markup=create_main_keyboard()
            )
        else:
            await message.answer(
                "❌ Не удалось создать пользователя. Попробуйте позже.",
                reply_markup=create_login_keyboard()
            )

    except Exception as e:
        logger.error(f"Error during registration: {e}")
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуйте позже.",
            reply_markup=create_login_keyboard()
        )
    finally:
        user_manager.close_connection()
        await state.clear()


async def cancel_auth(callback: CallbackQuery, state: FSMContext):
    """Отмена процесса авторизации/регистрации"""
    await callback.message.answer(
        "❌ Авторизация отменена.",
        reply_markup=create_login_keyboard()
    )
    await state.clear()
    await callback.answer()


def register_auth_handlers(dp: Dispatcher):
    """Регистрирует обработчики авторизации"""
    # Обработчики для кнопок входа и регистрации
    dp.message.register(start_login, F.text == "Войти")
    dp.message.register(start_register, F.text == "Создать пользователя")

    # Обработчики состояний авторизации
    dp.message.register(process_username, AuthStates.waiting_username)
    dp.message.register(process_password, AuthStates.waiting_password)
    dp.message.register(process_new_username, AuthStates.waiting_new_username)
    dp.message.register(process_new_password, AuthStates.waiting_new_password)

    # Обработчики callback-запросов
    dp.callback_query.register(cancel_auth, F.data == "cancel_auth")