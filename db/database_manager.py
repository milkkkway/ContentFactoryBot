import psycopg2
import logging
from typing import Optional, Tuple, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, dbname="postgres", user="postgres", password="2323420",
                 host="localhost", port="5432"):
        self.connection_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self.conn = None
        self.cursor = None

    def connect(self) -> bool:
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            logger.info("✅ Успешное подключение к базе данных")
            self._initialize_tables()
            return True

        except psycopg2.OperationalError as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
            return False
        except psycopg2.Error as e:
            logger.error(f"❌ Ошибка PostgreSQL: {e}")
            return False

    def _initialize_tables(self):
        try:
            create_users_table = """
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE,
                username VARCHAR(100) UNIQUE NOT NULL,
                psswrd VARCHAR(100) NOT NULL,
                role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user', 'moderator')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            create_drafts_table = """
            CREATE TABLE IF NOT EXISTS drafts (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                media_type VARCHAR(10) CHECK (media_type IN ('photo', 'video')),
                media_file_id VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_drafts_user_id ON drafts(user_id);
            CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON drafts(created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
            """

            self.cursor.execute(create_users_table)
            self.cursor.execute(create_drafts_table)
            self.conn.commit()
            logger.info("✅ Все таблицы инициализированы")

        except psycopg2.Error as e:
            logger.error(f"❌ Ошибка инициализации таблиц: {e}")
            self.conn.rollback()

    def execute_query(self, query: str, params: Tuple = None) -> Optional[Any]:
        if not self._check_connection():
            return None

        try:
            self.cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            logger.error(f"❌ Ошибка выполнения запроса: {e}")
            self.conn.rollback()
            return None

    def fetch_one(self, query: str, params: Tuple = None) -> Optional[Tuple]:
        if not self._check_connection():
            return None

        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchone()
        except psycopg2.Error as e:
            logger.error(f"❌ Ошибка получения записи: {e}")
            return None

    def fetch_all(self, query: str, params: Tuple = None) -> Optional[list]:
        if not self._check_connection():
            return None

        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except psycopg2.Error as e:
            logger.error(f"❌ Ошибка получения записей: {e}")
            return None

    def _check_connection(self) -> bool:
        if self.conn is None or self.cursor is None:
            logger.error("❌ Нет активного соединения с базой данных")
            return False
        return True

    def close_connection(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("🔌 Соединение с базой данных закрыто")