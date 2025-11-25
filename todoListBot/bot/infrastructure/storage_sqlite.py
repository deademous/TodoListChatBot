import json
import os
import sqlite3
from dotenv import load_dotenv
from bot.domain.storage import Storage


class StorageSqlite(Storage):

    def __init__(self):
        load_dotenv()
        self._db_path = os.getenv("SQLITE_DATABASE_PATH")
        if not self._db_path:
            raise ValueError("SQLITE_DATABASE_PATH не найден в .env")

        if not os.path.exists(self._db_path):
            print(f"Файл БД не найден по пути {self._db_path}, создаю новый...")
            self.recreate_database()

    @staticmethod
    def recreate_database() -> None:
        load_dotenv()
        connection = sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH"))
        with connection:
            connection.execute("DROP TABLE IF EXISTS telegram_updates")
            connection.execute("DROP TABLE IF EXISTS users")
            connection.execute("DROP TABLE IF EXISTS tasks")
            connection.execute("DROP TABLE IF EXISTS user_settings")

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS telegram_updates
                ( id INTEGER PRIMARY KEY, payload TEXT NOT NULL )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users
                (
                    id INTEGER PRIMARY KEY, 
                    telegram_id INTEGER NOT NULL UNIQUE, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                    state TEXT DEFAULT NULL,
                    data_json TEXT DEFAULT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL, 
                    text TEXT NOT NULL,
                    task_date TEXT DEFAULT NULL,
                    task_time TEXT DEFAULT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    notified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings
                (
                    id INTEGER PRIMARY KEY,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    morning_digest_time TEXT NOT NULL DEFAULT '09:00',
                    evening_review_time TEXT NOT NULL DEFAULT '21:00',
                    FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                )
                """
            )
        connection.close()

    def ensure_user_exists(self, telegram_id: int) -> None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            with connection:
                cursor = connection.execute(
                    "SELECT 1 FROM users WHERE telegram_id = ?", (telegram_id,)
                )
                if cursor.fetchone() is None:
                    connection.execute(
                        "INSERT INTO users (telegram_id) VALUES (?)", (telegram_id,)
                    )
                    connection.execute(
                        "INSERT INTO user_settings (telegram_id) VALUES (?)",
                        (telegram_id,),
                    )

    def persist_update(self, update: dict) -> None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            data = (json.dumps(update, ensure_ascii=False, indent=2),)
            connection.execute(
                "INSERT INTO telegram_updates (payload) VALUES (?)", data
            )

    def clear_user_state_and_temp_data(self, telegram_id: int) -> None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.execute(
                "UPDATE users SET state = NULL, data_json = NULL WHERE telegram_id = ?",
                (telegram_id,),
            )

    def update_user_state(self, telegram_id: int, state: str | None) -> None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.execute(
                "UPDATE users SET state = ? WHERE telegram_id = ?", (state, telegram_id)
            )

    def get_user(self, telegram_id: int) -> dict | None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                "SELECT id, telegram_id, state, data_json FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None

    def update_user_data(self, telegram_id: int, new_data: dict) -> None:
        user = self.get_user(telegram_id)
        if user is None:
            return

        existing_data_str = user.get("data_json")
        existing_data = json.loads(existing_data_str) if existing_data_str else {}
        existing_data.update(new_data)

        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.execute(
                "UPDATE users SET data_json = ? WHERE telegram_id = ?",
                (json.dumps(existing_data, ensure_ascii=False, indent=2), telegram_id),
            )

    def create_task(
        self, telegram_id: int, text: str, task_date: str | None, task_time: str | None
    ) -> int:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            cursor = connection.execute(
                """
                INSERT INTO tasks (telegram_id, text, task_date, task_time, status, notified)
                VALUES (?, ?, ?, ?, 'active', 0)
                """,
                (telegram_id, text, task_date, task_time),
            )
            return cursor.lastrowid

    def get_tasks_by_filter(self, telegram_id: int, filter_type: str) -> list[dict]:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.row_factory = sqlite3.Row
            query = ""
            params = [telegram_id]

            if filter_type == "show_today":
                query = "SELECT * FROM tasks WHERE telegram_id = ? AND status = 'active' AND task_date = DATE('now')"
            elif filter_type == "show_tomorrow":
                query = "SELECT * FROM tasks WHERE telegram_id = ? AND status = 'active' AND task_date = DATE('now', '+1 day')"
            elif filter_type == "show_nodate":
                query = "SELECT * FROM tasks WHERE telegram_id = ? AND status = 'active' AND task_date IS NULL"
            else:
                return []

            cursor = connection.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_user_settings(self, telegram_id: int) -> dict:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                "SELECT morning_digest_time, evening_review_time FROM user_settings WHERE telegram_id = ?",
                (telegram_id,),
            )
            result = cursor.fetchone()
            if result:
                return dict(result)
            return {"morning_digest_time": "09:00", "evening_review_time": "21:00"}

    def update_user_setting_time(
        self, telegram_id: int, setting_type: str, new_time: str
    ) -> None:
        if setting_type not in ("morning_digest_time", "evening_review_time"):
            return

        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.execute(
                f"UPDATE user_settings SET {setting_type} = ? WHERE telegram_id = ?",
                (new_time, telegram_id),
            )

    def update_task_status(self, task_id: int, new_status: str) -> None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.execute(
                "UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id)
            )

    def update_task(
        self, task_id: int, task_date: str | None, task_time: str | None, status: str
    ) -> None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.execute(
                "UPDATE tasks SET task_date = ?, task_time = ?, status = ? WHERE id = ?",
                (task_date, task_time, status, task_id),
            )

    def get_task_by_id(self, task_id: int) -> dict | None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            result = cursor.fetchone()
            return dict(result) if result else None

    def get_due_tasks(self, current_date: str, current_time: str) -> list[dict]:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(
                """
                SELECT t.*, t.telegram_id AS chat_id FROM tasks t
                WHERE t.status = 'active'
                AND t.task_date IS NOT NULL
                AND t.task_time IS NOT NULL
                AND t.notified = 0
                AND (t.task_date < ? OR (t.task_date = ? AND t.task_time <= ?))
                ORDER BY t.task_date ASC, t.task_time ASC
                """,
                (current_date, current_date, current_time),
            )
            return [dict(row) for row in cursor.fetchall()]

    def mark_task_as_notified(self, task_id: int) -> None:
        with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
            connection.execute(
                "UPDATE tasks SET notified = 1 WHERE id = ?", (task_id,)
            )