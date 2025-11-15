import json
import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class MessageStart(Handler):

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            "message" in update
            and "text" in update["message"]
            and update["message"]["text"] == "/start"
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]

        bot.database_client.clear_user_state_and_temp_data(telegram_id)

        reply_markup = json.dumps(
            {
                "keyboard": [
                    [{"text": "➕ Добавить задачу"}],
                    [{"text": "📅 Мои задачи"}, {"text": "⚙️ Настройки"}],
                    [{"text": "❓ Помощь"}],
                ],
                "resize_keyboard": True,
            }
        )

        bot.telegram_client.sendMessage(
            chat_id=chat_id,
            text="Бот-Планировщик к вашим услугам!",
            reply_markup=reply_markup,
        )

        return HandlerStatus.STOP
