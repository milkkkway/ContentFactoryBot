import logging
from db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self):
        self.db = DatabaseManager()
        self.current_user_id = None

    def connect(self):
        """Подключение к базе данных"""
        return self.db.connect()

    def check_user_exists(self, username=None, psswrd=None, telegram_id=None):
        """Проверка существования пользователя"""
        if not self.db.connect():
            return False

        try:
            if username and psswrd:
                # Проверка по логину и паролю (для обычной авторизации)
                query = "SELECT id, role FROM users WHERE username = %s AND psswrd = %s"
                user = self.db.fetch_one(query, (username, psswrd))
            elif telegram_id:
                # Проверка по Telegram ID (для бота)
                query = "SELECT id, role FROM users WHERE telegram_id = %s"
                user = self.db.fetch_one(query, (telegram_id,))
            elif username:
                # Проверка только по username
                query = "SELECT id, role FROM users WHERE username = %s"
                user = self.db.fetch_one(query, (username,))
            else:
                logger.error("❌ Не указаны параметры для поиска пользователя")
                return False

            if user:
                user_id, role = user
                self.current_user_id = user_id
                logger.info(f"✅ Пользователь найден: ID={user_id}, Role={role}")
                return True
            else:
                logger.info("❌ Пользователь не найден")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка при проверке пользователя: {e}")
            return False

    def get_user_by_username(self, username):
        """Получение пользователя по username"""
        if not self.db.connect():
            return None

        try:
            query = "SELECT id, username, role, telegram_id FROM users WHERE username = %s"
            result = self.db.fetch_one(query, (username,))
            if result:
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'role': result[2],
                    'telegram_id': result[3]
                }
                logger.info(f"✅ Найден пользователь по username {username}: {user_data}")
                return user_data
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пользователя по username: {e}")
            return None

    def update_user_telegram_id(self, username, telegram_id):
        """Обновление telegram_id для существующего пользователя"""
        if not self.db.connect():
            return False

        try:
            query = "UPDATE users SET telegram_id = %s WHERE username = %s"
            result = self.db.execute_query(query, (telegram_id, username))

            if result:
                logger.info(f"✅ Telegram ID {telegram_id} обновлен для пользователя {username}")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении telegram_id: {e}")
            return False

    def update_user_telegram_id(self, username, telegram_id):
        """Обновление telegram_id для существующего пользователя"""
        if not self.db.connect():
            return False

        try:
            query = "UPDATE users SET telegram_id = %s WHERE username = %s"
            result = self.db.execute_query(query, (telegram_id, username))

            if result:
                logger.info(f"✅ Telegram ID {telegram_id} обновлен для пользователя {username}")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении telegram_id: {e}")
            return False

    def create_user(self, username, psswrd, telegram_id=None, role='user'):
        """Создание нового пользователя"""
        if not self.db.connect():
            return False

        # Проверяем, нет ли уже пользователя с таким username
        if self.check_user_exists(username=username):
            logger.error("❌ Пользователь с таким username уже существует")
            return False

        # Если указан telegram_id, проверяем его уникальность
        if telegram_id and self.check_user_exists(telegram_id=telegram_id):
            logger.error("❌ Пользователь с таким Telegram ID уже существует")
            return False

        try:
            if telegram_id:
                query = """
                INSERT INTO users (username, psswrd, telegram_id, role) 
                VALUES (%s, %s, %s, %s) 
                RETURNING id
                """
                result = self.db.execute_query(query, (username, psswrd, telegram_id, role))
            else:
                query = """
                INSERT INTO users (username, psswrd, role) 
                VALUES (%s, %s, %s) 
                RETURNING id
                """
                result = self.db.execute_query(query, (username, psswrd, role))

            if result:
                logger.info(
                    f"✅ Пользователь создан успешно! Username: {username}, Role: {role}, Telegram ID: {telegram_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка при создании пользователя: {e}")
            return False

    def get_current_user_id(self):
        """Получение ID текущего пользователя"""
        return self.current_user_id

    def get_user_role(self, user_id=None):
        """Получение роли пользователя"""
        if not self.db.connect():
            return None

        try:
            query = "SELECT role FROM users WHERE id = %s"
            result = self.db.fetch_one(query, (user_id or self.current_user_id,))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении роли пользователя: {e}")
            return None

    def get_user_by_telegram_id(self, telegram_id):
        """Получение пользователя по Telegram ID"""
        if not self.db.connect():
            return None

        try:
            query = "SELECT id, username, role FROM users WHERE telegram_id = %s"
            result = self.db.fetch_one(query, (telegram_id,))
            if result:
                user_data = {
                    'id': result[0],
                    'username': result[1],
                    'role': result[2]
                }
                logger.info(f"✅ Найден пользователь по Telegram ID {telegram_id}: {user_data}")
                return user_data
            logger.warning(f"⚠️ Пользователь с Telegram ID {telegram_id} не найден")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка при получении пользователя: {e}")
            return None

    def get_all_users(self):
        """Получение списка всех пользователей"""
        if not self.db.connect():
            return []

        try:
            query = "SELECT id, username, role, telegram_id, created_at FROM users ORDER BY id"
            users = self.db.fetch_all(query)

            if users:
                logger.info("📋 Получен список всех пользователей")
                formatted_users = []
                for user in users:
                    formatted_users.append({
                        'id': user[0],
                        'username': user[1],
                        'role': user[2],
                        'telegram_id': user[3],
                        'created_at': user[4]
                    })
                return formatted_users
            return []

        except Exception as e:
            logger.error(f"❌ Ошибка при получении списка пользователей: {e}")
            return []

    def close_connection(self):
        """Закрытие соединения с базой данных"""
        self.db.close_connection()