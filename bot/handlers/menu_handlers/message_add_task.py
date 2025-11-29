from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.interface.keyboards import REMOVE_KEYBOARD
import asyncio


class MessageAddTask(Handler):

    def can_handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> bool:
        return (
            state is None
            and "message" in update
            and "text" in update["message"]
            and update["message"]["text"] == "➕ Добавить задачу"
        )

    async def handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> HandlerStatus:

        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]

        await storage.update_user_state(telegram_id, "WAIT_TASK_NAME")

        reply_markup = REMOVE_KEYBOARD

        messenger.send_message(
            chat_id=chat_id,
            text="Напишите, что нужно сделать:",
            reply_markup=reply_markup,
        )
        return HandlerStatus.STOP
