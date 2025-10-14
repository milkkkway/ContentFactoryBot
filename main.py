import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import Message

from utilities.default import register_handlers as register_default_handlers
from handlers.auth import register_auth_handlers
from handlers.statistics import register_statistics_handlers
from utilities.keyboards import create_login_keyboard

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
    welcome_text = (
        "🤖 <b>Content Factory Bot</b>\n\n"
        "Для начала работы необходимо войти или создать пользователя."
    )
    await message.answer(welcome_text, reply_markup=create_login_keyboard(), parse_mode='HTML')

# Регистрация всех обработчиков в ПРАВИЛЬНОМ порядке
register_auth_handlers(dp)  # Сначала аутентификация
register_default_handlers(dp)
register_statistics_handlers(dp)  # Затем статистика

# Обработчик по умолчанию должен быть ЗАРЕГИСТРИРОВАН ПОСЛЕДНИМ
@dp.message()
async def handle_other_messages(message: Message):
    """Обработчик ВСЕХ остальных сообщений (по умолчанию)"""
    if message.text:
        await message.answer(
            "🤖 Используйте кнопки меню или команды:\n"
            "/start - начать работу\n"
            "/help - получить справку",
            reply_markup=create_login_keyboard()  # Показываем клавиатуру регистрации
        )

async def main():
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())