from aiogram.fsm.state import State, StatesGroup

class AuthStates(StatesGroup):
    """Состояния для процесса авторизации"""
    waiting_username = State()
    waiting_password = State()
    waiting_new_username = State()
    waiting_new_password = State()

class DraftStates(StatesGroup):
    """Состояния для работы с черновиками"""
    waiting_media = State()
    waiting_title = State()
    waiting_description = State()
    viewing_drafts = State()

class StatsStates(StatesGroup):
    """Состояния для работы со статистикой"""
    waiting_keyword = State()
    waiting_region = State()
    waiting_num_posts = State()
    waiting_min_subs = State()
    waiting_min_vids = State()
    showing_results = State()