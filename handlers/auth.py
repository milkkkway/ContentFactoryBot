import logging
from aiogram import Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from utilities.keyboards import create_login_keyboard, create_main_keyboard
from utilities.states import AuthStates
from db.user_manager import UserManager

logger = logging.getLogger(__name__)

# Создаем экземпляр менеджера пользователей
user_manager = UserManager()

async def login_start(message: Message, state: FSMContext):
    """Начало процесса входа"""
    await message.answer(
        "🔐 <b>Вход в систему</b>\n\n"
        "Введите ваш логин:",
        parse_mode='HTML'
    )
    await state.set_state(AuthStates.waiting_login)

async def process_login(message: Message, state: FSMContext):
    """Обработка логина"""
    login = message.text.strip()

    if len(login) < 3:
        await message.answer("❌ <b>Логин должен содержать минимум 3 символа.</b>\nВведите логин:", parse_mode='HTML')
        return

    await state.update_data(login=login)
    await message.answer(
        "🔑 <b>Введите ваш пароль:</b>",
        parse_mode='HTML'
    )
    await state.set_state(AuthStates.waiting_password)

async def process_password(message: Message, state: FSMContext):
    """Обработка пароля и проверка пользователя"""
    password = message.text.strip()
    user_data = await state.get_data()
    login = user_data['login']

    # Подключаемся к базе данных
    if not user_manager.connect():
        await message.answer(
            "❌ <b>Ошибка подключения к базе данных.</b>\n\n"
            "Попробуйте позже.",
            parse_mode='HTML'
        )
        await state.clear()
        return

    try:
        # Проверяем существование пользователя
        if user_manager.check_user_exists(username=login, psswrd=password):
            await message.answer(
                "✅ <b>Вход выполнен успешно!</b>\n\n"
                "Теперь вы можете использовать все функции бота.",
                reply_markup=create_main_keyboard(),
                parse_mode='HTML'
            )
            await state.clear()
        else:
            await message.answer(
                "❌ <b>Неверный логин или пароль.</b>\n\n"
                "Попробуйте еще раз или создайте нового пользователя.",
                reply_markup=create_login_keyboard(),
                parse_mode='HTML'
            )
            await state.clear()

    except Exception as e:
        logger.error(f"Error during login: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка при входе.</b>\n\n"
            "Попробуйте позже.",
            parse_mode='HTML'
        )
        await state.clear()
    finally:
        user_manager.close_connection()

async def register_start(message: Message, state: FSMContext):
    """Начало процесса регистрации"""
    await message.answer(
        "👤 <b>Создание нового пользователя</b>\n\n"
        "Придумайте логин (минимум 3 символа):",
        parse_mode='HTML'
    )
    await state.set_state(AuthStates.waiting_new_login)

async def process_new_login(message: Message, state: FSMContext):
    """Обработка нового логина"""
    new_login = message.text.strip()

    if len(new_login) < 3:
        await message.answer("❌ <b>Логин должен содержать минимум 3 символа.</b>\nПридумайте логин:", parse_mode='HTML')
        return

    # Проверяем доступность логина
    if not user_manager.connect():
        await message.answer(
            "❌ <b>Ошибка подключения к базе данных.</b>\n\n"
            "Попробуйте позже.",
            parse_mode='HTML'
        )
        await state.clear()
        return

    try:
        if user_manager.check_user_exists(username=new_login):
            await message.answer(
                "❌ <b>Этот логин уже занят.</b>\n\n"
                "Придумайте другой логин:",
                parse_mode='HTML'
            )
            user_manager.close_connection()
            return
        else:
            await state.update_data(new_login=new_login)
            await message.answer(
                "🔑 <b>Придумайте пароль (минимум 4 символа):</b>",
                parse_mode='HTML'
            )
            await state.set_state(AuthStates.waiting_new_password)

    except Exception as e:
        logger.error(f"Error checking login: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка при проверке логина.</b>\n\n"
            "Попробуйте позже.",
            parse_mode='HTML'
        )
        await state.clear()
    finally:
        user_manager.close_connection()

async def process_new_password(message: Message, state: FSMContext):
    """Обработка нового пароля и создание пользователя"""
    password = message.text.strip()

    if len(password) < 4:
        await message.answer("❌ <b>Пароль должен содержать минимум 4 символа.</b>\nПридумайте пароль:", parse_mode='HTML')
        return

    user_data = await state.get_data()
    new_login = user_data['new_login']

    # Создаем пользователя
    if not user_manager.connect():
        await message.answer(
            "❌ <b>Ошибка подключения к базе данных.</b>\n\n"
            "Попробуйте позже.",
            parse_mode='HTML'
        )
        await state.clear()
        return

    try:
        if user_manager.create_user(new_login, password):
            await message.answer(
                "✅ <b>Пользователь успешно создан!</b>\n\n"
                "Теперь вы можете войти в систему.",
                reply_markup=create_login_keyboard(),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                "❌ <b>Не удалось создать пользователя.</b>\n\n"
                "Возможно, такой пользователь уже существует.",
                reply_markup=create_login_keyboard(),
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка при создании пользователя.</b>\n\n"
            "Попробуйте позже.",
            parse_mode='HTML'
        )
    finally:
        user_manager.close_connection()
        await state.clear()

def register_auth_handlers(dp: Dispatcher):
    """Регистрирует обработчики аутентификации"""
    # Обработчики начала аутентификации
    dp.message.register(login_start, F.text == "Войти")
    dp.message.register(register_start, F.text == "Создать пользователя")

    # Обработчики процесса входа
    dp.message.register(process_login, AuthStates.waiting_login)
    dp.message.register(process_password, AuthStates.waiting_password)

    # Обработчики процесса регистрации
    dp.message.register(process_new_login, AuthStates.waiting_new_login)
    dp.message.register(process_new_password, AuthStates.waiting_new_password)