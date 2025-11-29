import json
from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.handlers.tools.task_card import format_task_card_text


class TaskActionCallbackHandler(Handler):
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
            and update["callback_query"]["data"].startswith("task_")
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

        try:
            action, task_id_str = callback_data.split(":", 1)
            task_id = int(task_id_str)
        except ValueError:
            return HandlerStatus.STOP

        if action == "task_postpone":
            await storage.update_user_data(telegram_id, {"postpone_task_id": task_id})
            await storage.update_user_state(telegram_id, "WAIT_POSTPONE_TIME")

            await messenger.delete_message(chat_id=chat_id, message_id=message_id)

            inline_keyboard = json.dumps(
                {
                    "inline_keyboard": [
                        [
                            {"text": "На 1 час", "callback_data": "postpone:1h"},
                            {"text": "На 3 часа", "callback_data": "postpone:3h"},
                        ],
                        [
                            {"text": "На Завтра", "callback_data": "postpone:tomorrow"},
                            {"text": "На 1 день", "callback_data": "postpone:1d"},
                        ],
                    ]
                }
            )
            await messenger.send_message(
                chat_id=chat_id,
                text="🕑 На сколько отложить? (кнопки или текст '1ч', 'завтра в 9'):",
                reply_markup=inline_keyboard,
            )
            return HandlerStatus.STOP

        new_status = "done" if action == "task_done" else "canceled"

        await storage.update_task_status(task_id, new_status)
        updated_task = await storage.get_task_by_id(task_id)

        if updated_task:
            new_card_text = format_task_card_text(updated_task)
            await messenger.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=new_card_text,
                reply_markup=json.dumps({"inline_keyboard": []}),
            )

        return HandlerStatus.STOP
