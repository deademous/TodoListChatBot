import json

import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class TaskNameHandler(Handler):
    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state == "WAIT_TASK_NAME"
            and "message" in update
            and "text" in update["message"]
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]
        task_text = update["message"]["text"]

        bot.database_client.update_user_data(telegram_id, {"text": task_text})

        bot.database_client.update_user_state(telegram_id, "WAIT_TASK_DATE")

        inline_keyboard = json.dumps(
            {
                "inline_keyboard": [
                    [{"text": "Сегодня", "callback_data": "set_date_today"}],
                    [{"text": "Завтра", "callback_data": "set_date_tomorrow"}],
                    [{"text": "Без даты", "callback_data": "set_date_nodate"}],
                ]
            }
        )

        bot.telegram_client.sendMessage(
            chat_id=chat_id,
            text=f"Отлично! Задача: '{task_text}'. \nНа какой день?",
            reply_markup=inline_keyboard,
        )
        return HandlerStatus.STOP
