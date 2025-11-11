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
            state TEXT DEFAULT NULL
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
            status TEXT NOT NULL DEFAULT 'active',
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


def clear_user_state(telegram_id: int) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET state = NULL WHERE telegram_id = ?",
                (telegram_id,),
            )


def update_user_state(telegram_id: int, state: str) -> None:
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
                "SELECT id, telegram_id, state FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None


def update_user_data(telegram_id: int, order_json: str) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        with connection:
            connection.execute(
                "UPDATE users SET order_json = ? WHERE telegram_id = ?",
                (json.dumps(order_json, ensure_ascii=False, indent=2), telegram_id),
            )


def create_task(telegram_id: int, text: str) -> None:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        connection.execute(
            "INSERT INTO tasks (telegram_id, text) VALUES (?, ?)", (telegram_id, text)
        )


def get_active_tasks(telegram_id: int) -> list[dict]:
    with sqlite3.connect(os.getenv("SQLITE_DATABASE_PATH")) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.execute(
            "SELECT id, text FROM tasks WHERE telegram_id = ? AND status = 'active'",
            (telegram_id,),
        )
        return [dict(row) for row in cursor.fetchall()]
