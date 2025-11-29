from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.interface.keyboards import TASK_DATE_KEYBOARD


class TaskNameHandler(Handler):

    def can_handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> bool:
        return (
            state == "WAIT_TASK_NAME"
            and "message" in update
            and "text" in update["message"]
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
        task_text = update["message"]["text"]

        data_json["text"] = task_text
        await storage.update_user_data(telegram_id, data_json)

        await storage.update_user_state(telegram_id, "WAIT_TASK_DATE")
        inline_keyboard = TASK_DATE_KEYBOARD

        messenger.send_message(
            chat_id=chat_id,
            text=f"Отлично! Задача: '{task_text}'. \nНа какой день?",
            reply_markup=inline_keyboard,
        )
        return HandlerStatus.STOP
