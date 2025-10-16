import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message

from utilities.default import register_handlers as register_default_handlers
from handlers.auth import register_auth_handlers
from handlers.statistics import register_statistics_handlers
from handlers.draft import register_draft_handlers
from utilities.keyboards import create_login_keyboard, create_main_keyboard
from db.user_manager import UserManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токена бота
BOT_TOKEN = '7379575266:AAFaPpFPuHYPcWrJdd5VHe75Bj0-ZHUrjDI'

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    user_manager = UserManager()
    if user_manager.connect():
        try:
            user_data = user_manager.get_user_by_telegram_id(user_id)
            if user_data:
                welcome_text = (
                    f"👋 <b>С возвращением, {user_data['username']}!</b>\n\n"
                    "Вы уже авторизованы в системе. "
                    "Можете создавать и просматривать свои черновики."
                )
                await message.answer(welcome_text, reply_markup=create_main_keyboard(), parse_mode='HTML')
            else:
                welcome_text = (
                    "🤖 <b>Content Factory Bot</b>\n\n"
                    "Для начала работы необходимо войти или создать пользователя."
                )
                await message.answer(welcome_text, reply_markup=create_login_keyboard(), parse_mode='HTML')
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            welcome_text = (
                "🤖 <b>Content Factory Bot</b>\n\n"
                "Для начала работы необходимо войти или создать пользователя."
            )
            await message.answer(welcome_text, reply_markup=create_login_keyboard(), parse_mode='HTML')
        finally:
            user_manager.close_connection()
    else:
        await message.answer(
            "❌ Ошибка подключения к базе данных. Попробуйте позже.",
            reply_markup=create_login_keyboard()
        )


# Регистрация всех обработчиков в ПРАВИЛЬНОМ порядке
register_auth_handlers(dp)  # ДОЛЖНО БЫТЬ ПЕРВЫМ!
register_default_handlers(dp)
register_statistics_handlers(dp)
register_draft_handlers(dp)


# Обработчик по умолчанию
@dp.message()
async def handle_other_messages(message: Message):
    if message.text:
        await message.answer(
            "🤖 Используйте кнопки меню или команды:\n"
            "/start - начать работу\n"
            "/help - получить справку",
            reply_markup=create_login_keyboard()
        )


async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())