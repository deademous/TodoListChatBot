import json
import logging
import os
import time

import asyncpg
from dotenv import load_dotenv
from bot.domain.storage import Storage

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class StoragePostgres(Storage):
    def __init__(self) -> None:
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            host = os.getenv("POSTGRES_HOST")
            port = os.getenv("POSTGRES_HOST_PORT")
            user = os.getenv("POSTGRES_USER")
            password = os.getenv("POSTGRES_PASSWORD")
            database = os.getenv("POSTGRES_DATABASE")

            if not all([host, port, user, password, database]):
                raise ValueError("Some POSTGRES_* environment variables are not set")

            self._pool = await asyncpg.create_pool(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=database,
            )
        return self._pool

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def recreate_database(self) -> None:
        method_name = "recreate_database"
        start_time = time.time()
        logger.info(f"[DB] → {method_name} - DROP/CREATE TABLES")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute("DROP TABLE IF EXISTS telegram_updates")
                await conn.execute("DROP TABLE IF EXISTS user_settings")
                await conn.execute("DROP TABLE IF EXISTS tasks")
                await conn.execute("DROP TABLE IF EXISTS users")

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS telegram_updates
                    (id SERIAL PRIMARY KEY, payload TEXT NOT NULL)
                    """
                )
                await conn.execute(
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
                await conn.execute(
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
                await conn.execute(
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

            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def persist_update(self, update: dict) -> None:
        method_name = "persist_update"
        start_time = time.time()
        payload = json.dumps(update, ensure_ascii=False, indent=2)
        logger.info(f"[DB] → {method_name} - INSERT INTO telegram_updates")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO telegram_updates (payload) VALUES ($1)",
                    payload,
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def ensure_user_exists(self, telegram_id: int) -> None:
        method_name = "ensure_user_exists"
        start_time = time.time()
        logger.info(f"[DB] → {method_name} - INSERT users/user_settings if not exists")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO users (telegram_id) VALUES ($1) ON CONFLICT (telegram_id) DO NOTHING",
                    telegram_id,
                )
                await conn.execute(
                    "INSERT INTO user_settings (telegram_id) VALUES ($1) ON CONFLICT (telegram_id) DO NOTHING",
                    telegram_id,
                )

            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_user(self, telegram_id: int) -> dict | None:
        method_name = "get_user"
        start_time = time.time()
        logger.info(f"[DB] → {method_name} - SELECT user")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, telegram_id, state, data_json FROM users WHERE telegram_id=$1",
                    telegram_id,
                )
                if row:
                    user_data = dict(row)
                    duration_ms = (time.time() - start_time) * 1000
                    logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
                    return user_data
                duration_ms = (time.time() - start_time) * 1000
                logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms (no result)")
                return None
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def clear_user_state_and_temp_data(self, telegram_id: int) -> None:
        method_name = "clear_user_state_and_temp_data"
        start_time = time.time()
        logger.info(f"[DB] → {method_name} - CLEAR state/data_json for user")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET state=NULL, data_json=NULL WHERE telegram_id=$1",
                    telegram_id,
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def update_user_state(self, telegram_id: int, state: str | None) -> None:
        method_name = "update_user_state"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET state=$1 WHERE telegram_id=$2",
                    state,
                    telegram_id,
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def update_user_data(self, telegram_id: int, new_data: dict) -> None:
        method_name = "update_user_data"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        user = await self.get_user(telegram_id)
        if not user:
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms (user not found)")
            return

        existing_data = json.loads(user["data_json"]) if user["data_json"] else {}
        existing_data.update(new_data)

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE users SET data_json=$1 WHERE telegram_id=$2",
                    json.dumps(existing_data, ensure_ascii=False, indent=2),
                    telegram_id,
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def create_task(
        self, telegram_id: int, text: str, task_date: str | None, task_time: str | None
    ) -> int:
        method_name = "create_task"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO tasks (telegram_id, text, task_date, task_time, status, notified)
                    VALUES ($1,$2,$3,$4,'active',FALSE)
                    RETURNING id
                    """,
                    telegram_id,
                    text,
                    task_date,
                    task_time,
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
            return row["id"] if row else 0
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_tasks_by_filter(
        self, telegram_id: int, filter_type: str
    ) -> list[dict]:
        method_name = "get_tasks_by_filter"
        start_time = time.time()
        logger.info(f"[DB] → {method_name} - filter={filter_type}")

        query = ""
        if filter_type == "show_today":
            query = "SELECT * FROM tasks WHERE telegram_id=$1 AND status='active' AND task_date=CAST(CURRENT_DATE AS TEXT)"
        elif filter_type == "show_tomorrow":
            query = "SELECT * FROM tasks WHERE telegram_id=$1 AND status='active' AND task_date=CAST(CURRENT_DATE + INTERVAL '1 day' AS TEXT)"
        elif filter_type == "show_nodate":
            query = "SELECT * FROM tasks WHERE telegram_id=$1 AND status='active' AND task_date IS NULL"
        else:
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms (invalid filter)")
            return []

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(query, telegram_id)
            result = [dict(r) for r in rows]
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[DB] ← {method_name} - {duration_ms:.2f}ms ({len(result)} rows)"
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_user_settings(self, telegram_id: int) -> dict:
        method_name = "get_user_settings"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT morning_digest_time, evening_review_time FROM user_settings WHERE telegram_id=$1",
                    telegram_id,
                )
            if row:
                result = dict(row)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
                return result
            return {"morning_digest_time": "09:00", "evening_review_time": "21:00"}
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def update_user_setting_time(
        self, telegram_id: int, setting_type: str, new_time: str
    ) -> None:
        method_name = "update_user_setting_time"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        if setting_type not in ("morning_digest_time", "evening_review_time"):
            logger.warning(f"[DB] ✗ {method_name} - Invalid setting_type")
            return

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"UPDATE user_settings SET {setting_type}=$1 WHERE telegram_id=$2",
                    new_time,
                    telegram_id,
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def update_task_status(self, task_id: int, new_status: str) -> None:
        method_name = "update_task_status"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE tasks SET status=$1 WHERE id=$2", new_status, task_id
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def update_task(
        self, task_id: int, task_date: str | None, task_time: str | None, status: str
    ) -> None:
        method_name = "update_task"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE tasks SET task_date=$1, task_time=$2, status=$3 WHERE id=$4",
                    task_date,
                    task_time,
                    status,
                    task_id,
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_task_by_id(self, task_id: int) -> dict | None:
        method_name = "get_task_by_id"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM tasks WHERE id=$1", task_id)
            if row:
                result = dict(row)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
                return result
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms (no result)")
            return None
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_due_tasks(self, current_date: str, current_time: str) -> list[dict]:
        method_name = "get_due_tasks"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT t.*, t.telegram_id AS chat_id FROM tasks t
                    WHERE t.status='active' AND t.task_date IS NOT NULL AND t.task_time IS NOT NULL
                    AND t.notified=FALSE
                    AND (t.task_date<$1 OR (t.task_date=$1 AND t.task_time<=$2))
                    """,
                    current_date,
                    current_time,
                )
            result = [dict(r) for r in rows]
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[DB] ← {method_name} - {duration_ms:.2f}ms ({len(result)} rows)"
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def mark_task_as_notified(self, task_id: int) -> None:
        method_name = "mark_task_as_notified"
        start_time = time.time()
        logger.info(f"[DB] → {method_name}")

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE tasks SET notified=TRUE WHERE id=$1", task_id
                )
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DB] ← {method_name} - {duration_ms:.2f}ms")
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_users_for_time_check(self, setting_type: str, current_time: str) -> list[dict]:
        method_name = "get_users_for_time_check"
        start_time = time.time()
        logger.info(
            f"[DB] → {method_name} - Get users for {setting_type} at {current_time}"
        )

        if setting_type not in ("morning_digest_time", "evening_review_time"):
            logger.warning(
                f"[DB] ✗ {method_name} - Invalid setting_type: {setting_type}"
            )
            return []

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT t1.telegram_id, t2.{setting_type} AS setting_time
                    FROM users t1
                    JOIN user_settings t2 ON t1.telegram_id = t2.telegram_id
                    WHERE t2.{setting_type} = $1
                    """,
                    current_time,
                )

            result = [dict(row) for row in rows]
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[DB] ← {method_name} - {duration_ms:.2f}ms ({len(result)} rows)"
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_active_tasks_for_digest(
        self, telegram_id: int, today_date: str
    ) -> list[dict]:
        method_name = "get_active_tasks_for_digest"
        start_time = time.time()
        logger.info(
            f"[DB] → {method_name} - Get active tasks for digest for {telegram_id} on {today_date}"
        )

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, text, task_date, task_time, status
                    FROM tasks
                    WHERE telegram_id = $1 
                        AND status = 'active'
                        AND (task_date = $2 OR task_date IS NULL)
                    ORDER BY CASE WHEN task_date IS NULL THEN 1 ELSE 0 END, 
                             task_time ASC, 
                             id ASC
                    """,
                    telegram_id,
                    today_date,
                )

            result = [dict(row) for row in rows]
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[DB] ← {method_name} - {duration_ms:.2f}ms ({len(result)} rows)"
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_tasks_for_tomorrow(
        self, telegram_id: int, tomorrow_date: str
    ) -> list[dict]:
        method_name = "get_tasks_for_tomorrow"
        start_time = time.time()
        logger.info(
            f"[DB] → {method_name} - Get tasks for tomorrow for {telegram_id} on {tomorrow_date}"
        )

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, text, task_date, task_time, status
                    FROM tasks
                    WHERE telegram_id = $1 
                        AND status = 'active'
                        AND task_date = $2
                    ORDER BY task_time ASC, id ASC
                    """,
                    telegram_id,
                    tomorrow_date,
                )

            result = [dict(row) for row in rows]
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[DB] ← {method_name} - {duration_ms:.2f}ms ({len(result)} rows)"
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def get_users_for_scheduled_notifications(
        self, current_time: str, setting_type: str
    ) -> list[dict]:
        method_name = "get_users_for_scheduled_notifications"
        start_time = time.time()
        logger.info(
            f"[DB] → {method_name} - Get users for scheduled notifications at {current_time} ({setting_type})"
        )

        if setting_type not in ("morning_digest_time", "evening_review_time"):
            logger.warning(
                f"[DB] ✗ {method_name} - Invalid setting_type: {setting_type}"
            )
            return []

        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT t1.telegram_id
                    FROM users AS t1
                    JOIN user_settings AS t2 ON t1.telegram_id = t2.telegram_id
                    WHERE t2.{setting_type} = $1
                    """,
                    current_time,
                )

            result = [dict(row) for row in rows]
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"[DB] ← {method_name} - {duration_ms:.2f}ms ({len(result)} rows)"
            )
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DB] ✗ {method_name} - {duration_ms:.2f}ms - Error: {e}")
            raise
