from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.handlers.tools.task_card import (
    format_task_card_text,
    get_task_card_reply_markup,
)
from bot.interface.keyboards import MAIN_MENU_KEYBOARD
from bot.handlers.tools.time_parser import normalize_time


class TaskTimeHandler(Handler):

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
            and "message" in update
            and "text" in update["message"]
        )

    def handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> HandlerStatus:

        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]
        task_time_text = update["message"]["text"]

        normalized_time = normalize_time(task_time_text)
        if not normalized_time:
            messenger.send_message(
                chat_id=chat_id,
                text="Непонятный формат времени. Попробуйте '14:30', '18.00' или просто '9'.",
            )
            return HandlerStatus.STOP

        task_text = data_json.get("text")
        task_date = data_json.get("date")

        task_id = storage.create_task(
            telegram_id, task_text, task_date, normalized_time
        )
        storage.clear_user_state_and_temp_data(telegram_id)

        messenger.send_message(
            chat_id=chat_id,
            text="Готово! Задача создана:",
            reply_markup=MAIN_MENU_KEYBOARD,
        )

        new_task = {
            "id": task_id,
            "text": task_text,
            "task_date": task_date,
            "task_time": normalized_time,
        }
        card_text = format_task_card_text(new_task)
        card_markup = get_task_card_reply_markup(task_id)

        messenger.send_message(
            chat_id=chat_id, text=card_text, reply_markup=card_markup
        )

        return HandlerStatus.STOP
