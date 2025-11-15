import json
from datetime import datetime, timedelta
import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class TaskDateHandler(Handler):
    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state == "WAIT_TASK_DATE" and 
            "callback_query" in update and 
            update["callback_query"]["data"].startswith("set_date_")
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["callback_query"]["from"]["id"]
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        message_id = update["callback_query"]["message"]["message_id"]
        callback_data = update["callback_query"]["data"]

        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        bot.telegram_client.answerCallbackQuery(update["callback_query"]["id"])

        today = datetime.now().strftime('%Y-%m-%d')
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        date_map = {
            "set_date_today": today,
            "set_date_tomorrow": tomorrow,
            "set_date_nodate": None
        }
        task_date = date_map.get(callback_data)
        
        data_json["date"] = task_date
        bot.database_client.update_user_data(telegram_id, data_json)
        
        bot.database_client.update_user_state(telegram_id, "WAIT_TASK_TIME")
        
        inline_keyboard = json.dumps({
            "inline_keyboard": [[{"text": "⏰ Без времени", "callback_data": "set_time_notime"}]]
        })
        
        bot.telegram_client.editMessageText(
            chat_id = chat_id,
            message_id = message_id,
            text = "Хорошо. Укажите время (в формате ЧЧ:ММ) или нажмите 'Без времени'",
            reply_markup = inline_keyboard
        )
        bot.telegram_client.answerCallbackQuery(update["callback_query"]["id"])
        return HandlerStatus.STOP