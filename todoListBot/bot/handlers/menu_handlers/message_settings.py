import json
import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class MessageSettings(Handler):

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state is None
            and "message" in update
            and "text" in update["message"]
            and (
                update["message"]["text"] == "⚙️ Настройки"
                or update["message"]["text"] == "/settings"
            )
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]

        settings = bot.database_client.get_user_settings(telegram_id)
        current_morning = settings.get("morning_digest_time", "09:00")
        current_evening = settings.get("evening_review_time", "21:00")

        text = (
            f"Здесь можно настроить уведомления.\n\n"
            f"• Утренний дайджест: `{current_morning}`\n"
            f"• Вечерний обзор: `{current_evening}`"
        )

        inline_keyboard = json.dumps(
            {
                "inline_keyboard": [
                    [{"text": "☀️ Изменить утро", "callback_data": "set_morning"}],
                    [{"text": "🌙 Изменить вечер", "callback_data": "set_evening"}],
                ]
            }
        )

        bot.telegram_client.sendMessage(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=inline_keyboard,
        )
        return HandlerStatus.STOP
