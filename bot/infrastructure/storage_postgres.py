import json
import os
import pg8000
from dotenv import load_dotenv
from bot.domain.storage import Storage


class StoragePostgres(Storage):

    def _get_connection(self):
        load_dotenv()

        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_HOST_PORT")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DATABASE")

        if not all([host, port, user, password, database]):
            raise ValueError("Erroor in one of env vars(StoragePgsql)")

        conn = pg8000.connect(
            host=host,
            port=int(port),
            user=user,
            password=password,
            database=database,
        )
        return conn

    @staticmethod
    def recreate_database() -> None:
        load_dotenv()
        host = os.getenv("POSTGRES_HOST")
        port = int(os.getenv("POSTGRES_HOST_PORT"))
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        database = os.getenv("POSTGRES_DATABASE")

        connection = pg8000.connect(
            host=host, port=port, user=user, password=password, database=database
        )

        with connection:
            with connection.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS telegram_updates")
                cursor.execute("DROP TABLE IF EXISTS user_settings")
                cursor.execute("DROP TABLE IF EXISTS tasks")
                cursor.execute("DROP TABLE IF EXISTS users")

                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS telegram_updates
                    ( id SERIAL PRIMARY KEY, payload TEXT NOT NULL )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users
                    (
                        id SERIAL PRIMARY KEY, 
                        telegram_id BIGINT NOT NULL UNIQUE, 
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                        state TEXT DEFAULT NULL,
                        data_json TEXT DEFAULT NULL
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks
                    (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT NOT NULL, 
                        text TEXT NOT NULL,
                        task_date TEXT DEFAULT NULL,
                        task_time TEXT DEFAULT NULL,
                        status TEXT NOT NULL DEFAULT 'active',
                        notified BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS user_settings
                    (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT NOT NULL UNIQUE,
                        morning_digest_time TEXT NOT NULL DEFAULT '09:00',
                        evening_review_time TEXT NOT NULL DEFAULT '21:00',
                        FOREIGN KEY (telegram_id) REFERENCES users (telegram_id)
                    )
                    """
                )
            connection.commit()

    def ensure_user_exists(self, telegram_id: int) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (telegram_id) VALUES (%s) ON CONFLICT (telegram_id) DO NOTHING",
                    (telegram_id,),
                )
                cursor.execute(
                    "INSERT INTO user_settings (telegram_id) VALUES (%s) ON CONFLICT (telegram_id) DO NOTHING",
                    (telegram_id,),
                )
            conn.commit()

    def persist_update(self, update: dict) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                data = json.dumps(update, ensure_ascii=False, indent=2)
                cursor.execute(
                    "INSERT INTO telegram_updates (payload) VALUES (%s)", (data,)
                )
            conn.commit()

    def clear_user_state_and_temp_data(self, telegram_id: int) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET state = NULL, data_json = NULL WHERE telegram_id = %s",
                    (telegram_id,),
                )
            conn.commit()

    def update_user_state(self, telegram_id: int, state: str | None) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET state = %s WHERE telegram_id = %s",
                    (state, telegram_id),
                )
            conn.commit()

    def get_user(self, telegram_id: int) -> dict | None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id, telegram_id, state, data_json FROM users WHERE telegram_id = %s",
                    (telegram_id,),
                )
                row = cursor.fetchone()
                if row:
                    columns = [col[0] for col in cursor.description]
                    return dict(zip(columns, row))
                return None
            conn.commit()

    def update_user_data(self, telegram_id: int, new_data: dict) -> None:
        user = self.get_user(telegram_id)
        if user is None:
            return

        existing_data_str = user.get("data_json")
        existing_data = json.loads(existing_data_str) if existing_data_str else {}
        existing_data.update(new_data)

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET data_json = %s WHERE telegram_id = %s",
                    (
                        json.dumps(existing_data, ensure_ascii=False, indent=2),
                        telegram_id,
                    ),
                )
            conn.commit()

    def create_task(
        self, telegram_id: int, text: str, task_date: str | None, task_time: str | None
    ) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tasks (telegram_id, text, task_date, task_time, status, notified)
                    VALUES (%s, %s, %s, %s, 'active', FALSE)
                    RETURNING id
                    """,
                    (telegram_id, text, task_date, task_time),
                )
                result = cursor.fetchone()
            conn.commit()
            return result[0] if result else 0

    def get_tasks_by_filter(self, telegram_id: int, filter_type: str) -> list[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                query = ""
                params = [telegram_id]

                if filter_type == "show_today":
                    query = "SELECT * FROM tasks WHERE telegram_id = %s AND status = 'active' AND task_date = CAST(CURRENT_DATE AS TEXT)"
                elif filter_type == "show_tomorrow":
                    query = "SELECT * FROM tasks WHERE telegram_id = %s AND status = 'active' AND task_date = CAST(CURRENT_DATE + INTERVAL '1 day' AS TEXT)"
                elif filter_type == "show_nodate":
                    query = "SELECT * FROM tasks WHERE telegram_id = %s AND status = 'active' AND task_date IS NULL"
                else:
                    return []

                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.commit()

    def get_user_settings(self, telegram_id: int) -> dict:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT morning_digest_time, evening_review_time FROM user_settings WHERE telegram_id = %s",
                    (telegram_id,),
                )
                row = cursor.fetchone()
                if row:
                    columns = [col[0] for col in cursor.description]
                    return dict(zip(columns, row))
                return {"morning_digest_time": "09:00", "evening_review_time": "21:00"}
            conn.commit()

    def update_user_setting_time(
        self, telegram_id: int, setting_type: str, new_time: str
    ) -> None:
        if setting_type not in ("morning_digest_time", "evening_review_time"):
            return

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"UPDATE user_settings SET {setting_type} = %s WHERE telegram_id = %s",
                    (new_time, telegram_id),
                )
            conn.commit()

    def update_task_status(self, task_id: int, new_status: str) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE tasks SET status = %s WHERE id = %s", (new_status, task_id)
                )
            conn.commit()

    def update_task(
        self, task_id: int, task_date: str | None, task_time: str | None, status: str
    ) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE tasks SET task_date = %s, task_time = %s, status = %s WHERE id = %s",
                    (task_date, task_time, status, task_id),
                )
            conn.commit()

    def get_task_by_id(self, task_id: int) -> dict | None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
                row = cursor.fetchone()
                if row:
                    columns = [col[0] for col in cursor.description]
                    return dict(zip(columns, row))
                return None
            conn.commit()

    def get_due_tasks(self, current_date: str, current_time: str) -> list[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT t.*, t.telegram_id AS chat_id FROM tasks t
                    WHERE t.status = 'active'
                    AND t.task_date IS NOT NULL
                    AND t.task_time IS NOT NULL
                    AND t.notified = FALSE
                    AND (t.task_date < %s OR (t.task_date = %s AND t.task_time <= %s))
                    ORDER BY t.task_date ASC, t.task_time ASC
                    """,
                    (current_date, current_date, current_time),
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.commit()

    def mark_task_as_notified(self, task_id: int) -> None:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE tasks SET notified = TRUE WHERE id = %s", (task_id,)
                )
            conn.commit()

    def get_users_for_time_check(
        self, setting_type: str, current_time: str
    ) -> list[dict]:
        if setting_type not in ("morning_digest_time", "evening_review_time"):
            return []

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT t1.telegram_id, t2.{setting_type} AS setting_time
                    FROM users t1
                    JOIN user_settings t2 ON t1.telegram_id = t2.telegram_id
                    WHERE t2.{setting_type} = %s
                    """,
                    (current_time,),
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.commit()

    def get_active_tasks_for_digest(
        self, telegram_id: int, today_date: str
    ) -> list[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, text, task_date, task_time, status
                    FROM tasks
                    WHERE telegram_id = %s 
                        AND status = 'active'
                        AND (task_date = %s OR task_date IS NULL)
                    ORDER BY CASE WHEN task_date IS NULL THEN 1 ELSE 0 END, 
                                task_time ASC, 
                                id ASC
                    """,
                    (telegram_id, today_date),
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.commit()

    def get_tasks_for_tomorrow(
        self, telegram_id: int, tomorrow_date: str
    ) -> list[dict]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, text, task_date, task_time, status
                    FROM tasks
                    WHERE telegram_id = %s 
                        AND status = 'active'
                        AND task_date = %s
                    ORDER BY task_time ASC, id ASC
                    """,
                    (telegram_id, tomorrow_date),
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.commit()

    def get_users_for_scheduled_notifications(
        self, current_time: str, setting_type: str
    ) -> list[dict]:
        if setting_type not in ("morning_digest_time", "evening_review_time"):
            return []

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT t1.telegram_id
                    FROM users AS t1
                    JOIN user_settings AS t2 ON t1.telegram_id = t2.telegram_id
                    WHERE t2.{setting_type} = %s
                    """,
                    (current_time,),
                )
                columns = [col[0] for col in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            conn.commit()
