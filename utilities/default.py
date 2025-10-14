from aiogram import Dispatcher, F
from aiogram.types import Message

async def show_settings(message: Message):
    """Показывает настройки"""
    settings_text = (
        "⚙️ <b>Настройки</b>\n\n"
        "Доступные опции:\n"
        "• Язык интерфейса\n"
        "• Формат чисел\n"
        "• Уведомления\n\n"
        "<i>Настройки будут доступны в будущих обновлениях</i>"
    )
    await message.answer(settings_text, parse_mode='HTML')

async def show_help(message: Message):
    """Показывает справку"""
    help_text = (
        "🤖 <b>YouTube Analytics Bot - Помощь</b>\n\n"
        "📊 <b>Функциональность:</b>\n"
        "• Анализ YouTube каналов по ключевым словам\n"
        "• Статистика по подписчикам и просмотрам\n"
        "• Анализ эффективности контента\n"
        "• Сравнительная аналитика\n\n"
        "🔍 <b>Как использовать:</b>\n"
        "1. Нажмите <b>📊 СТАТИСТИКА</b>\n"
        "2. Введите ключевые слова\n"
        "3. Выберите параметры поиска\n"
        "4. Получите детальный отчет\n\n"
        "⚡ <b>Быстрые команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка"
    )
    await message.answer(help_text, parse_mode='HTML')

def register_handlers(dp: Dispatcher):
    """Регистрирует обработчики из этого модуля"""
    # ТОЛЬКО специфичные обработчики с фильтрами
    dp.message.register(show_settings, F.text == "⚙️ Настройки")
    dp.message.register(show_help, F.text == "ℹ️ Помощь")
    # НЕ регистрируем handle_other_messages здесь!