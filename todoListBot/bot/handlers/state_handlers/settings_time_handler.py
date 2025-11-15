import json
import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus
import re


def get_main_menu_keyboard() -> str:
    return json.dumps(
        {
            "keyboard": [
                [{"text": "➕ Добавить задачу"}],
                [{"text": "📅 Мои задачи"}, {"text": "⚙️ Настройки"}],
                [{"text": "❓ Помощь"}],
            ],
            "resize_keyboard": True,
        }
    )


def is_valid_time(time_str: str) -> bool:
    if re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)", time_str):
        return True
    return False


class SettingsTimeHandler(Handler):

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state in ("WAIT_SETTING_MORNING", "WAIT_SETTING_EVENING")
            and "message" in update
            and "text" in update["message"]
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]
        new_time = update["message"]["text"]

        if not is_valid_time(new_time):
            bot.telegram_client.sendMessage(
                chat_id,
                "Неверный формат. Пожалуйста, введите время в формате ЧЧ:ММ (например, 08:30 или 21:00).",
            )
            return HandlerStatus.STOP

        if state == "WAIT_SETTING_MORNING":
            setting_type = "morning_digest_time"
            setting_name = "утреннего дайджеста"
        else:
            setting_type = "evening_review_time"
            setting_name = "вечернего обзора"

        bot.database_client.update_user_setting_time(
            telegram_id, setting_type, new_time
        )

        bot.database_client.clear_user_state_and_temp_data(telegram_id)

        bot.telegram_client.sendMessage(
            chat_id=chat_id,
            text=f"✅ Готово! Время для {setting_name} обновлено на {new_time}.",
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
