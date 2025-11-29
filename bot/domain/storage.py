from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    async def recreate_database(self) -> None: ...

    @abstractmethod
    async def persist_update(self, update: dict) -> None: ...

    @abstractmethod
    async def ensure_user_exists(self, telegram_id: int) -> None: ...

    @abstractmethod
    async def clear_user_state_and_temp_data(self, telegram_id: int) -> None: ...

    @abstractmethod
    async def update_user_state(self, telegram_id: int, state: str | None) -> None: ...

    @abstractmethod
    async def get_user(self, telegram_id: int) -> dict | None: ...

    @abstractmethod
    async def update_user_data(self, telegram_id: int, new_data: dict) -> None: ...

    @abstractmethod
    async def create_task(
        self, telegram_id: int, text: str, task_date: str | None, task_time: str | None
    ) -> int: ...

    @abstractmethod
    async def get_tasks_by_filter(
        self, telegram_id: int, filter_type: str
    ) -> list[dict]: ...

    @abstractmethod
    async def get_user_settings(self, telegram_id: int) -> dict: ...

    @abstractmethod
    async def update_user_setting_time(
        self, telegram_id: int, setting_type: str, new_time: str
    ) -> None: ...

    @abstractmethod
    async def get_due_tasks(
        self, current_date: str, current_time: str
    ) -> list[dict]: ...

    @abstractmethod
    async def mark_task_as_notified(self, task_id: int) -> None: ...

    @abstractmethod
    async def get_users_for_time_check(
        self, setting_type: str, current_time: str
    ) -> list[dict]: ...

    @abstractmethod
    async def get_active_tasks_for_digest(
        self, telegram_id: int, today_date: str
    ) -> list[dict]: ...

    @abstractmethod
    async def get_tasks_for_tomorrow(
        self, telegram_id: int, tomorrow_date: str
    ) -> list[dict]: ...
