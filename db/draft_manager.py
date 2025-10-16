import logging
from db.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DraftManager:
    def __init__(self):
        self.db = DatabaseManager()

    def connect(self):
        """Подключение к базе данных"""
        return self.db.connect()

    def create_draft(self, user_id, username, title, description, media_type, media_file_id):
        """Создание нового черновика - альтернативная версия"""
        logger.info(f"🔄 Попытка создания черновика для user_id: {user_id}")

        if not self.db.connect():
            logger.error("❌ Не удалось подключиться к базе данных")
            return None

        try:
            # Сначала выполняем INSERT
            insert_query = """
            INSERT INTO drafts (user_id, username, title, description, media_type, media_file_id) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            insert_params = (user_id, username, title, description, media_type, media_file_id)

            insert_result = self.db.execute_query(insert_query, insert_params)

            if not insert_result:
                logger.error("❌ Не удалось выполнить INSERT")
                return None

            # Затем получаем ID созданного черновика
            select_query = """
            SELECT id, created_at FROM drafts 
            WHERE user_id = %s AND title = %s 
            ORDER BY created_at DESC LIMIT 1
            """
            select_params = (user_id, title)

            result = self.db.fetch_one(select_query, select_params)

            if result:
                draft_id, created_at = result
                logger.info(f"✅ УСПЕХ: Создан черновик {draft_id}")
                return {
                    'id': draft_id,
                    'user_id': user_id,
                    'username': username,
                    'title': title,
                    'description': description,
                    'media_type': media_type,
                    'media_file_id': media_file_id,
                    'created_at': created_at
                }
            else:
                logger.error("❌ Не удалось получить ID созданного черновика")
                return None

        except Exception as e:
            logger.error(f"❌ ОШИБКА при создании черновика: {e}")
            return None

    def get_user_drafts(self, user_id):
        """Получение ВСЕХ черновиков пользователя по Telegram ID"""
        logger.info(f"🔄 Получение черновиков для user_id: {user_id}")

        if not self.db.connect():
            logger.error("❌ Не удалось подключиться к базе данных")
            return []

        try:
            query = """
            SELECT id, title, description, media_type, media_file_id, created_at 
            FROM drafts 
            WHERE user_id = %s 
            ORDER BY created_at DESC
            """
            drafts = self.db.fetch_all(query, (user_id,))

            logger.info(f"📋 Найдено черновиков: {len(drafts) if drafts else 0}")

            formatted_drafts = []
            if drafts:
                for draft in drafts:
                    formatted_drafts.append({
                        'id': draft[0],
                        'title': draft[1],
                        'description': draft[2],
                        'media_type': draft[3],
                        'media_file_id': draft[4],
                        'created_at': draft[5]
                    })
                logger.info(f"✅ УСПЕХ: Форматировано {len(formatted_drafts)} черновиков")
            else:
                logger.info("ℹ️ Черновики не найдены")

            return formatted_drafts

        except Exception as e:
            logger.error(f"❌ ОШИБКА при получении черновиков: {e}")
            return []

    def get_draft_by_id(self, draft_id, user_id):
        """Получение конкретного черновика по ID и Telegram ID пользователя"""
        logger.info(f"🔄 Получение черновика {draft_id} для user_id: {user_id}")

        if not self.db.connect():
            return None

        try:
            query = """
            SELECT id, user_id, username, title, description, media_type, media_file_id, created_at 
            FROM drafts 
            WHERE id = %s AND user_id = %s
            """
            draft = self.db.fetch_one(query, (draft_id, user_id))

            if draft:
                logger.info(f"✅ УСПЕХ: Черновик {draft_id} найден")
                return {
                    'id': draft[0],
                    'user_id': draft[1],
                    'username': draft[2],
                    'title': draft[3],
                    'description': draft[4],
                    'media_type': draft[5],
                    'media_file_id': draft[6],
                    'created_at': draft[7]
                }
            else:
                logger.warning(f"⚠️ Черновик {draft_id} не найден для пользователя {user_id}")
            return None

        except Exception as e:
            logger.error(f"❌ ОШИБКА при получении черновика: {e}")
            return None

    def update_draft(self, draft_id, user_id, title=None, description=None):
        """Обновление черновика - по Telegram ID"""
        if not self.db.connect():
            return False

        try:
            update_fields = []
            params = []

            if title is not None:
                update_fields.append("title = %s")
                params.append(title)
            if description is not None:
                update_fields.append("description = %s")
                params.append(description)

            if not update_fields:
                return False

            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.extend([draft_id, user_id])

            query = f"UPDATE drafts SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s"
            result = self.db.execute_query(query, params)

            if result and self.db.cursor.rowcount > 0:
                logger.info(f"✅ Черновик {draft_id} обновлен пользователем {user_id}")
                return True
            else:
                logger.warning(f"⚠️ Попытка обновления чужого черновика {draft_id} пользователем {user_id}")
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении черновика: {e}")
            return False

    def delete_draft(self, draft_id, user_id, user_role='user'):
        """Удаление черновика - по Telegram ID"""
        if not self.db.connect():
            return False

        try:
            if user_role in ['admin', 'moderator']:
                # Админы могут удалять любые черновики
                query = "DELETE FROM drafts WHERE id = %s"
                params = (draft_id,)
                logger.info(f"🛡️ Админ {user_id} удаляет черновик {draft_id}")
            else:
                # Обычные пользователи - только свои
                query = "DELETE FROM drafts WHERE id = %s AND user_id = %s"
                params = (draft_id, user_id)
                logger.info(f"✅ Пользователь {user_id} удаляет свой черновик {draft_id}")

            result = self.db.execute_query(query, params)

            if result and self.db.cursor.rowcount > 0:
                logger.info(f"✅ Черновик {draft_id} удален пользователем {user_id}")
                return True
            else:
                logger.warning(f"⚠️ Неудачная попытка удаления черновика {draft_id} пользователем {user_id}")
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка при удалении черновика: {e}")
            return False

    def close_connection(self):
        """Закрытие соединения с базой данных"""
        self.db.close_connection()