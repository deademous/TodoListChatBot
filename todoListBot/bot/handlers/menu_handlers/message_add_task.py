import json

import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class MessageAddTask(Handler):

    def can_handle(self, update: dict, state: str) -> bool:
        return (
            state is None
            and "message" in update
            and "text" in update["message"]
            and update["message"]["text"] == "➕ Добавить задачу"
        )

    def handle(self, update: dict, state: str) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]

        bot.database_client.update_user_state(telegram_id, "WAIT_TASK_NAME")

        reply_markup = json.dumps({"remove_keyboard": True})
        bot.telegram_client.sendMessage(
            chat_id=chat_id, text="Напишите, что нужно сделать:"
        )
        return HandlerStatus.STOP
