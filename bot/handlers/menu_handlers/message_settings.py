from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.interface.keyboards import SETTINGS_KEYBOARD


class MessageSettings(Handler):

    def can_handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> bool:
        return (
            state is None
            and "message" in update
            and "text" in update["message"]
            and (
                update["message"]["text"] == "⚙️ Настройки"
                or update["message"]["text"] == "/settings"
            )
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

        settings = await storage.get_user_settings(telegram_id)
        current_morning = settings.get("morning_digest_time", "09:00")
        current_evening = settings.get("evening_review_time", "21:00")

        text = (
            f"Здесь можно настроить уведомления.\n\n"
            f"• Утренний дайджест: `{current_morning}`\n"
            f"• Вечерний обзор: `{current_evening}`"
        )

        messenger.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=SETTINGS_KEYBOARD,
        )
        return HandlerStatus.STOP
