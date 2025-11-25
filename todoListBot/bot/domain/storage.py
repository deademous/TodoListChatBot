from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    def recreate_database(self) -> None: ...

    @abstractmethod
    def persist_update(self, update: dict) -> None: ...

    @abstractmethod
    def ensure_user_exists(self, telegram_id: int) -> None: ...

    @abstractmethod
    def clear_user_state_and_temp_data(self, telegram_id: int) -> None: ...

    @abstractmethod
    def update_user_state(self, telegram_id: int, state: str | None) -> None: ...

    @abstractmethod
    def get_user(self, telegram_id: int) -> dict | None: ...

    @abstractmethod
    def update_user_data(self, telegram_id: int, new_data: dict) -> None: ...

    @abstractmethod
    def create_task(
        self, telegram_id: int, text: str, task_date: str | None, task_time: str | None
    ) -> int: ...

    @abstractmethod
    def get_tasks_by_filter(self, telegram_id: int, filter_type: str) -> list[dict]: ...

    @abstractmethod
    def get_user_settings(self, telegram_id: int) -> dict: ...

    @abstractmethod
    def update_user_setting_time(
        self, telegram_id: int, setting_type: str, new_time: str
    ) -> None: ...

    @abstractmethod
    def get_due_tasks(self, current_date: str, current_time: str) -> list[dict]: ...

    @abstractmethod
    def mark_task_as_notified(self, task_id: int) -> None: ...