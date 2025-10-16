#!/usr/bin/env python3
"""
Скрипт для исправления структуры базы данных
"""

import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fix_database():
    """Исправление структуры базы данных"""

    connection_params = {
        'dbname': "postgres",
        'user': "postgres",
        'password': "2323420",
        'host': "localhost",
        'port': "5432"
    }

    try:
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        logger.info("✅ Подключение к базе данных установлено")

        # 1. Изменяем тип user_id в drafts на BIGINT
        logger.info("🔄 Изменяем тип user_id в таблице drafts...")
        cursor.execute("""
        ALTER TABLE drafts ALTER COLUMN user_id TYPE BIGINT
        """)
        logger.info("✅ Тип user_id изменен на BIGINT")

        # 2. Изменяем тип telegram_id в users на BIGINT
        logger.info("🔄 Изменяем тип telegram_id в таблице users...")
        cursor.execute("""
        ALTER TABLE users ALTER COLUMN telegram_id TYPE BIGINT
        """)
        logger.info("✅ Тип telegram_id изменен на BIGINT")

        # 3. Удаляем внешний ключ если он существует
        logger.info("🔄 Проверяем и удаляем внешний ключ...")
        cursor.execute("""
        ALTER TABLE drafts DROP CONSTRAINT IF EXISTS drafts_user_id_fkey
        """)
        logger.info("✅ Внешний ключ удален")

        conn.commit()
        logger.info("🎉 База данных успешно исправлена!")

    except psycopg2.Error as e:
        logger.error(f"❌ Ошибка исправления базы данных: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.info("🔌 Соединение закрыто")


if __name__ == "__main__":
    fix_database()