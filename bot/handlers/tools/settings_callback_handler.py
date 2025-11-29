from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage


class SettingsCallbackHandler(Handler):
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
            and "callback_query" in update
            and update["callback_query"]["data"].startswith("set_")
            and not update["callback_query"]["data"].startswith("set_date_")
            and not update["callback_query"]["data"] == "set_time_notime"
        )

    async def handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> HandlerStatus:
        telegram_id = update["callback_query"]["from"]["id"]
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        message_id = update["callback_query"]["message"]["message_id"]
        callback_data = update["callback_query"]["data"]

        await messenger.answer_callback_query(update["callback_query"]["id"])

        if callback_data == "set_morning":
            await storage.update_user_state(telegram_id, "WAIT_SETTING_MORNING")
            await messenger.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Вы выбрали 'Изменить утро'.",
            )
            await messenger.send_message(
                chat_id=chat_id,
                text="Введите новое время для утреннего дайджеста (например, 09:00):",
            )

        elif callback_data == "set_evening":
            await storage.update_user_state(telegram_id, "WAIT_SETTING_EVENING")
            await messenger.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Вы выбрали 'Изменить вечер'.",
            )
            await messenger.send_message(
                chat_id=chat_id,
                text="Введите новое время для вечернего обзора (например, 21:00):",
            )

        return HandlerStatus.STOP
