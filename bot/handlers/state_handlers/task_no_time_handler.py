from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.handlers.tools.task_card import (
    format_task_card_text,
    get_task_card_reply_markup,
)
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


class TaskNoTimeHandler(Handler):

    def can_handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> bool:
        return (
            state == "WAIT_TASK_TIME"
            and "callback_query" in update
            and update["callback_query"]["data"] == "set_time_notime"
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

        messenger.answer_callback_query(update["callback_query"]["id"])

        task_text = data_json.get("text")
        task_date = data_json.get("date")

        task_id = await storage.create_task(telegram_id, task_text, task_date, None)
        await storage.clear_user_state_and_temp_data(telegram_id)

        messenger.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="Готово! Задача создана (без времени).",
        )

        messenger.send_message(
            chat_id=chat_id,
            text="Вы в главном меню.",
            reply_markup=MAIN_MENU_KEYBOARD,
        )

        new_task = {
            "id": task_id,
            "text": task_text,
            "task_date": task_date,
            "task_time": None,
        }
        card_text = format_task_card_text(new_task)
        card_markup = get_task_card_reply_markup(task_id)

        messenger.send_message(
            chat_id=chat_id, text=card_text, reply_markup=card_markup
        )

        return HandlerStatus.STOP
