from abc import ABC, abstractmethod


class Messenger(ABC):
    @abstractmethod
    async def send_message(self, chat_id: int, text: str, **params) -> dict: ...

    @abstractmethod
    async def get_updates(self, **params) -> dict: ...

    @abstractmethod
    async def answer_callback_query(self, callback_query_id: str, **params) -> dict: ...

    @abstractmethod
    async def delete_message(self, chat_id: int, message_id: int) -> dict: ...

    @abstractmethod
    async def edit_message_text(
        self, chat_id: int, message_id: int, text: str, **params
    ) -> dict: ...

    @abstractmethod
    async def edit_message_reply_markup(
        self, chat_id: int, message_id: int, **params
    ) -> dict: ...
