from aiogram.fsm.state import State, StatesGroup

class StatsStates(StatesGroup):
    waiting_keyword = State()
    waiting_region = State()
    waiting_num_posts = State()
    waiting_min_subs = State()
    waiting_min_vids = State()
    showing_results = State()

class AuthStates(StatesGroup):
    waiting_login = State()
    waiting_password = State()
    waiting_new_login = State()
    waiting_new_password = State()