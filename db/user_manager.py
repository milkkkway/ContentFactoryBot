import psycopg2
from psycopg2 import sql

class UserManager:
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

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            self.cursor = self.conn.cursor()
            print("Успешное подключение к базе данных")
            self._create_users_table()
            return True

        except psycopg2.OperationalError as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            print("Проверьте:")
            print("1. Запущен ли сервер PostgreSQL")
            print("2. Правильность пароля")
            print("3. Доступность хоста и порта")
            return False
        except psycopg2.Error as e:
            print(f"❌ Ошибка PostgreSQL: {e}")
            return False

    def _create_users_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            psswrd VARCHAR(100) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            self.cursor.execute(create_table_query)
            self.conn.commit()
            print("✅ Таблица users готова к работе")
        except psycopg2.Error as e:
            print(f"❌ Ошибка создания таблицы: {e}")

    def _check_connection(self):
        if self.conn is None or self.cursor is None:
            print("❌ Нет активного соединения с базой данных")
            return False
        return True

    def check_user_exists(self, username=None, psswrd=None):
        if not self._check_connection():
            return False

        if not username and not psswrd:
            print("❌ Укажите username или psswrd для поиска")
            return False

        try:
            if username and psswrd:
                # Проверка по логину И паролю
                query = "SELECT * FROM users WHERE username = %s AND psswrd = %s"
                self.cursor.execute(query, (username, psswrd))
            elif username:
                query = "SELECT * FROM users WHERE username = %s"
                self.cursor.execute(query, (username,))
            else:
                query = "SELECT * FROM users WHERE psswrd = %s"
                self.cursor.execute(query, (psswrd,))

            user = self.cursor.fetchone()

            if user:
                print(f"✅ Пользователь найден: ID={user[0]}, Username={user[1]}, psswrd={user[2]}")
                return True
            else:
                print("❌ Пользователь не найден")
                return False

        except psycopg2.Error as e:
            print(f"❌ Ошибка при проверке пользователя: {e}")
            return False

    def create_user(self, username, psswrd):
        """
        Создание нового пользователя
        """
        if not self._check_connection():
            return False

        # Сначала проверяем, нет ли уже такого пользователя
        if self.check_user_exists(username=username) or self.check_user_exists(psswrd=psswrd):
            print("❌ Пользователь с таким username или psswrd уже существует")
            return False

        try:
            insert_query = """
            INSERT INTO users (username, psswrd) 
            VALUES (%s, %s) 
            RETURNING id
            """
            self.cursor.execute(insert_query, (username, psswrd))
            user_id = self.cursor.fetchone()[0]
            self.conn.commit()

            print(f"✅ Пользователь создан успешно! ID: {user_id}")
            return True

        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"❌ Ошибка при создании пользователя: {e}")
            return False

    def get_all_users(self):
        """Получение списка всех пользователей"""
        if not self._check_connection():
            return []

        try:
            self.cursor.execute("SELECT * FROM users ORDER BY id")
            users = self.cursor.fetchall()

            if users:
                print("\n📋 Список всех пользователей:")
                for user in users:
                    print(f"ID: {user[0]}, Username: {user[1]}, psswrd: {user[2]}, Created: {user[3]}")
            else:
                print("📭 В базе данных нет пользователей")

            return users

        except psycopg2.Error as e:
            print(f"❌ Ошибка при получении списка пользователей: {e}")
            return []

    def close_connection(self):
        """Закрытие соединения с базой данных"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("🔌 Соединение с базой данных закрыто")

def main():
    print("🚀 Запуск менеджера пользователей PostgreSQL")

    user_manager = UserManager(
        dbname="postgres",
        user="postgres",
        password="2323420",
        host="localhost",
        port="5432"
    )

    # Устанавливаем соединение
    if not user_manager.connect():
        return

    # 1. Создаем нового пользователя
    print("\n1. Создание нового пользователя:")
    user_manager.create_user("ivan_petrov", "ivan@example.com")

    # 2. Проверяем существование пользователя
    print("\n2. Проверка пользователя:")
    user_manager.check_user_exists(username="ivan_petrov")

    # 3. Пытаемся создать пользователя с существующим psswrd
    print("\n3. Попытка создать дубликат:")
    user_manager.create_user("another_user", "ivan@example.com")

    # 4. Создаем еще одного пользователя
    print("\n4. Создание второго пользователя:")
    user_manager.create_user("maria_sidorova", "maria@example.com")

    # 5. Получаем всех пользователей
    print("\n5. Полный список пользователей:")
    user_manager.get_all_users()

    # 6. Проверяем несуществующего пользователя
    print("\n6. Проверка несуществующего пользователя:")
    user_manager.check_user_exists(username="nonexistent_user")

    # Закрываем соединение
    user_manager.close_connection()

if __name__ == "__main__":
    main()