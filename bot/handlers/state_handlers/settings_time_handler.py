from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.interface.keyboards import MAIN_MENU_KEYBOARD
from bot.handlers.tools.time_parser import normalize_time


class SettingsTimeHandler(Handler):

    def can_handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> bool:
        return (
            state in ("WAIT_SETTING_MORNING", "WAIT_SETTING_EVENING")
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
        new_time = update["message"]["text"]

        normalized_time = normalize_time(new_time)

        if not normalized_time:
            await messenger.send_message(
                chat_id,
                "Неверный формат. Введите время, например: '08:30', '9:00' или '21.00'.",
            )
            return HandlerStatus.STOP

        if state == "WAIT_SETTING_MORNING":
            setting_type = "morning_digest_time"
            setting_name = "утреннего дайджеста"
        else:
            setting_type = "evening_review_time"
            setting_name = "вечернего обзора"

        await storage.update_user_setting_time(
            telegram_id, setting_type, normalized_time
        )
        await storage.clear_user_state_and_temp_data(telegram_id)

        messenger.send_message(
            chat_id=chat_id,
            text=f"✅ Готово! Время для {setting_name} обновлено на {normalized_time}.",
            reply_markup=MAIN_MENU_KEYBOARD,
        )

        return HandlerStatus.STOP
