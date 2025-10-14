from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def create_login_keyboard() -> ReplyKeyboardMarkup:
    """Создает главную клавиатуру"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Войти")],
            [KeyboardButton(text="Создать пользователя")]
        ],
        resize_keyboard=True
    )
    return keyboard

def create_main_keyboard() -> ReplyKeyboardMarkup:
    """Создает главную клавиатуру"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 СТАТИСТИКА")],
            [KeyboardButton(text="ℹ️ Помощь"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def create_region_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для выбора региона"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Россия", callback_data="region_RU"),
        InlineKeyboardButton(text="🇺🇸 США", callback_data="region_US")
    )
    return builder.as_markup()


def create_channel_navigation_keyboard(current_index: int, total_channels: int) -> InlineKeyboardMarkup:
    """Создает клавиатуру для навигации по каналам"""
    builder = InlineKeyboardBuilder()

    # Кнопки навигации
    buttons = []
    if current_index > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Предыдущий", callback_data=f"prev_channel_{current_index}"))

    buttons.append(InlineKeyboardButton(text="🔍 Подробнее", callback_data=f"channel_details_{current_index}"))

    if current_index < total_channels - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Следующий", callback_data=f"next_channel_{current_index}"))

    builder.row(*buttons)



    return builder.as_markup()


def create_channel_details_keyboard(channel_index: int, total_channels: int) -> InlineKeyboardMarkup:
    """Создает кнопку 'Подробнее' для канала с навигацией"""
    builder = InlineKeyboardBuilder()

    # Основная кнопка
    builder.row(InlineKeyboardButton(
        text="🔍 Подробнее о видео",
        callback_data=f"channel_details_{channel_index}"
    ))

    # Навигация между каналами
    nav_buttons = []
    if channel_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Пред. канал", callback_data=f"prev_channel_{channel_index}"))

    nav_buttons.append(InlineKeyboardButton(text="📋 К списку", callback_data="back_to_channels"))

    if channel_index < total_channels - 1:
        nav_buttons.append(InlineKeyboardButton(text="След. канал ➡️", callback_data=f"next_channel_{channel_index}"))

    builder.row(*nav_buttons)

    return builder.as_markup()


def create_back_to_channels_keyboard() -> InlineKeyboardMarkup:
    """Создает кнопку 'Назад к каналам'"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад к каналам",
        callback_data="back_to_channels"
    ))
    return builder.as_markup()