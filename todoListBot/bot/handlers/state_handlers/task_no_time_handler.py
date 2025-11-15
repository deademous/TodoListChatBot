import json
import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class TaskNoTimeHandler(Handler):
    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state == "WAIT_TASK_TIME" and
            "callback_query" in update and
            update["callback_query"]["data"] == "set_time_notime"
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["callback_query"]["from"]["id"]
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        message_id = update["callback_query"]["message"]["message_id"]

        task_text = data_json.get("text")
        task_date = data_json.get("date")
        
        bot.database_client.create_task(telegram_id, task_text, task_date, None)
        
        bot.database_client.clear_user_state_and_temp_data(telegram_id)
        
        bot.telegram_client.editMessageText(
            chat_id = chat_id,
            message_id = message_id,
            text = "Готово! Задача создана (без времени)."
        )
        bot.telegram_client.answerCallbackQuery(update["callback_query"]["id"])
        
        bot.telegram_client.sendMessage(
            chat_id = chat_id,
            text = "Вы в главном меню.",
            reply_markup = json.dumps({
        "keyboard": [
            [{"text": "➕ Добавить задачу"}],
            [{"text": "📅 Мои задачи"}, {"text": "⚙️ Настройки"}],
            [{"text": "❓ Помощь"}]
        ],
        "resize_keyboard": True
    })
        )
        
        return HandlerStatus.STOP