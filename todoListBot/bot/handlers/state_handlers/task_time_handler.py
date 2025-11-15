import json
import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class TaskTimeHandler(Handler):
    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state == "WAIT_TASK_TIME"
            and "message" in update
            and "text" in update["message"]
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]
        task_time_text = update["message"]["text"]

        task_text = data_json.get("text")
        task_date = data_json.get("date")

        bot.database_client.create_task(
            telegram_id, task_text, task_date, task_time_text
        )

        bot.database_client.clear_user_state_and_temp_data(telegram_id)

        bot.telegram_client.sendMessage(
            chat_id=chat_id,
            text="Готово! Задача создана.",
            reply_markup=json.dumps(
                {
                    "keyboard": [
                        [{"text": "➕ Добавить задачу"}],
                        [{"text": "📅 Мои задачи"}, {"text": "⚙️ Настройки"}],
                        [{"text": "❓ Помощь"}],
                    ],
                    "resize_keyboard": True,
                }
            ),
        )
        return HandlerStatus.STOP
