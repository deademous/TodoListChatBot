import json

import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class TaskNameHandler(Handler):
    def can_handle(self, update: dict, state: str) -> bool:
        return (
            state == "WAIT_TASK_NAME"
            and "message" in update
            and "text" in update["message"]
        )

    def handle(self, update: dict, state: str) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]
        task_text = update["message"]["text"]

        bot.database_client.create_task(telegram_id, task_text)

        bot.database_client.clear_user_state(telegram_id)

        reply_markup = json.dumps(
            {
                "keyboard": [
                    [{"text": "➕ Добавить задачу"}],
                    [{"text": "📅 Мои задачи"}],
                ],
                "resize_keyboard": True,
            }
        )

        bot.telegram_client.sendMessage(
            chat_id=chat_id, text=f"✅ Задача '{task_text}' добавлена."
        )
        return HandlerStatus.STOP
