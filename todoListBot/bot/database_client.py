import json
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()


def recreate_database() -> None:
    connection = sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH"))
    with connection:
        connection.execute("DROP TABLE IF EXISTS telegram_updates")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telegram_updates
            (
                id INTEGER PRIMARY KEY,
                payload TEXT NOT NULL
            )
        """
        )

        # users table
        connection.execute("DROP TABLE IF EXISTS users")
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

        # tasks table
        connection.execute("DROP TABLE IF EXISTS tasks")
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
        )
        """
        )

        # user_settings table
        connection.execute("DROP TABLE IF EXISTS user_settings")
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


def ensure_user_exists(telegram_id: int) -> None:
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
                    "INSERT INTO user_settings (telegram_id) VALUES (?)", (telegram_id,)
                )


def persist_updates(updates: list) -> None:
    connection = sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH"))
    with connection:
        data = []
        for update in updates:
            data.append((json.dumps(update, ensure_ascii=False, indent=2),))
        connection.executemany(
            "INSERT INTO telegram_updates (payload) VALUES (?)",
            data,
        )
    connection.close()


def clear_user_state_and_temp_data(telegram_id: int) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        connection.execute(
            "UPDATE users SET state = NULL, data_json = NULL WHERE telegram_id = ?",
            (telegram_id,),
        )


def update_user_state(telegram_id: int, state: str | None) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET state = ? WHERE telegram_id = ?", (state, telegram_id)
            )


def get_user(telegram_id: int) -> dict:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            "SELECT id, telegram_id, state, data_json FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        result = cursor.fetchone()
        if result:
            return dict(result)
        return None


def update_user_data(telegram_id: int, new_data: dict) -> None:

    user = get_user(telegram_id)

    if user is None:
        return

    existing_data_str = user.get("data_json")

    existing_data = json.loads(existing_data_str) if existing_data_str else {}

    existing_data.update(new_data)

    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET data_json = ? WHERE telegram_id = ?",
                (json.dumps(existing_data, ensure_ascii=False, indent=2), telegram_id),
            )


def create_task(
    telegram_id: int, text: str, task_date: str | None, task_time: str | None
) -> int:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (telegram_id, text, task_date, task_time) VALUES (?, ?, ?, ?)",
            (telegram_id, text, task_date, task_time),
        )
        return cursor.lastrowid


def get_tasks_by_filter(telegram_id: int, filter_type: str) -> list[dict]:
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


def get_active_tasks(telegram_id: int) -> list[dict]:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            "SELECT * FROM tasks WHERE telegram_id = ? AND status = 'active' ORDER BY task_date, task_time",
            (telegram_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_user_settings(telegram_id: int) -> dict:
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
    telegram_id: int, setting_type: str, new_time: str
) -> None:
    if setting_type not in ("morning_digest_time", "evening_review_time"):
        return

    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        connection.execute(
            f"UPDATE user_settings SET {setting_type} = ? WHERE telegram_id = ?",
            (new_time, telegram_id),
        )


def update_task_status(task_id: int, new_status: str) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id)
            )


def update_task(
    task_id: int, task_date: str | None, task_time: str | None, status: str
) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE tasks SET task_date = ?, task_time = ?, status = ? WHERE id = ?",
                (task_date, task_time, status, task_id),
            )


def get_task_by_id(task_id: int) -> dict | None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
