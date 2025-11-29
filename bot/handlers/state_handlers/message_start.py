from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


class MessageStart(Handler):

    def can_handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> bool:
        return (
            "message" in update
            and "text" in update["message"]
            and update["message"]["text"] == "/start"
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

        await storage.clear_user_state_and_temp_data(telegram_id)

        reply_markup = MAIN_MENU_KEYBOARD

        messenger.send_message(
            chat_id=chat_id,
            text="Бот-Планировщик к вашим услугам!",
            reply_markup=reply_markup,
        )

        return HandlerStatus.STOP
