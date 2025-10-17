from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def create_login_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Войти")],
            [KeyboardButton(text="Создать пользователя")]
        ],
        resize_keyboard=True
    )
    return keyboard


def create_main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 СТАТИСТИКА ПО ПАРАМЕТРАМ")],
            [KeyboardButton(text="ТРЕНДЫ")],
            [KeyboardButton(text="📝 Создать черновик"), KeyboardButton(text="📂 Мои черновики")],
            [KeyboardButton(text="ℹ️ Помощь"), KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )
    return keyboard


def create_region_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Россия", callback_data="region_RU"),
        InlineKeyboardButton(text="🇺🇸 США", callback_data="region_US")
    )
    builder.row(
        InlineKeyboardButton(text="🇧🇷 Бразилия", callback_data="region_BR"),
        InlineKeyboardButton(text="🇮🇳 Индия", callback_data="region_IN")
    )
    builder.row(
        InlineKeyboardButton(text="🇯🇵 Япония", callback_data="region_JP"),
        InlineKeyboardButton(text="🇰🇷 Корея", callback_data="region_KR")
    )
    builder.row(
        InlineKeyboardButton(text="🇩🇪 Германия", callback_data="region_DE"),
        InlineKeyboardButton(text="🇫🇷 Франция", callback_data="region_FR")
    )
    return builder.as_markup()


def create_channel_navigation_keyboard(current_index: int, total_channels: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons = []
    if current_index > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Предыдущий", callback_data=f"prev_channel_{current_index}"))

    buttons.append(InlineKeyboardButton(text="🔍 Подробнее", callback_data=f"channel_details_{current_index}"))

    if current_index < total_channels - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Следующий", callback_data=f"next_channel_{current_index}"))

    builder.row(*buttons)
    return builder.as_markup()


def create_channel_details_keyboard(channel_index: int, total_channels: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔍 Подробнее о видео",
        callback_data=f"channel_details_{channel_index}"
    ))

    nav_buttons = []
    if channel_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Пред. канал", callback_data=f"prev_channel_{channel_index}"))

    nav_buttons.append(InlineKeyboardButton(text="📋 К списку", callback_data="back_to_channels"))

    if channel_index < total_channels - 1:
        nav_buttons.append(InlineKeyboardButton(text="След. канал ➡️", callback_data=f"next_channel_{channel_index}"))

    builder.row(*nav_buttons)
    return builder.as_markup()


def create_back_to_channels_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="⬅️ Назад к каналам",
        callback_data="back_to_channels"
    ))
    return builder.as_markup()


def create_draft_actions_keyboard(draft_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_draft_{draft_id}"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_draft_{draft_id}")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_drafts")
    )

    return builder.as_markup()


def create_drafts_list_keyboard(drafts: list, current_page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start_idx = current_page * page_size
    end_idx = start_idx + page_size
    current_drafts = drafts[start_idx:end_idx]

    for draft in current_drafts:
        builder.row(
            InlineKeyboardButton(
                text=f"📄 {draft['title'][:20]}...",
                callback_data=f"view_draft_{draft['id']}"
            )
        )

    nav_buttons = []
    if current_page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"drafts_page_{current_page - 1}"))

    nav_buttons.append(InlineKeyboardButton(text="📋 В меню", callback_data="back_to_main"))

    if end_idx < len(drafts):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"drafts_page_{current_page + 1}"))

    builder.row(*nav_buttons)

    return builder.as_markup()


def create_cancel_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_draft"))
    return builder.as_markup()



def create_back_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main"))
    return builder.as_markup()


def create_statistics_period_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="📅 Сегодня", callback_data="stats_today"),
        InlineKeyboardButton(text="📅 Неделя", callback_data="stats_week")
    )
    builder.row(
        InlineKeyboardButton(text="📅 Месяц", callback_data="stats_month"),
        InlineKeyboardButton(text="📅 Все время", callback_data="stats_all")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    )

    return builder.as_markup()


def create_auth_cancel_keyboard() -> InlineKeyboardMarkup:

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_auth"))
    return builder.as_markup()


def create_trends_region_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇺🇸 США", callback_data="trends_region_US"),
        InlineKeyboardButton(text="🇷🇺 Россия", callback_data="trends_region_RU")
    )
    builder.row(
        InlineKeyboardButton(text="🇧🇷 Бразилия", callback_data="trends_region_BR"),
        InlineKeyboardButton(text="🇮🇳 Индия", callback_data="trends_region_IN")
    )
    builder.row(
        InlineKeyboardButton(text="🇯🇵 Япония", callback_data="trends_region_JP"),
        InlineKeyboardButton(text="🇰🇷 Корея", callback_data="trends_region_KR")
    )
    builder.row(
        InlineKeyboardButton(text="🇩🇪 Германия", callback_data="trends_region_DE"),
        InlineKeyboardButton(text="🇫🇷 Франция", callback_data="trends_region_FR")
    )
    builder.row(
        InlineKeyboardButton(text="🇬🇧 Великобритания", callback_data="trends_region_GB")
    )
    return builder.as_markup()


def create_trends_navigation_keyboard(current_index: int, total_trends: int, region: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Предыдущий", callback_data=f"prev_trend_{current_index}"))

    nav_buttons.append(InlineKeyboardButton(text="🔍 Подробнее", callback_data=f"trend_details_{current_index}"))

    if current_index < total_trends - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Следующий", callback_data=f"next_trend_{current_index}"))

    builder.row(*nav_buttons)

    builder.row(InlineKeyboardButton(text="🌍 Сменить регион", callback_data="change_trends_region"))

    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main"))

    return builder.as_markup()


def create_trend_details_keyboard(trend_index: int, total_trends: int, region: str,
                                  video_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="📺 Смотреть видео", url=video_url))

    nav_buttons = []
    if trend_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Пред. тренд", callback_data=f"prev_trend_{trend_index}"))

    nav_buttons.append(InlineKeyboardButton(text="📋 К списку", callback_data="back_to_trends_list"))

    if trend_index < total_trends - 1:
        nav_buttons.append(InlineKeyboardButton(text="След. тренд ➡️", callback_data=f"next_trend_{trend_index}"))

    builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(text="🌍 Другой регион", callback_data="change_trends_region"),
        InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_main")
    )

    return builder.as_markup()
