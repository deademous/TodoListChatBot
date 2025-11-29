from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.handlers.tools.task_card import (
    format_task_card_text,
    get_task_card_reply_markup,
)


class ShowTasksCallbackHandler(Handler):
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
            and update["callback_query"]["data"].startswith("show_")
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

        messenger.answer_callback_query(update["callback_query"]["id"])

        tasks = await storage.get_tasks_by_filter(telegram_id, callback_data)

        title_map = {
            "show_today": "📅 Задачи на сегодня",
            "show_tomorrow": "➡️ Задачи на завтра",
            "show_nodate": "📝 Задачи без даты",
        }
        title = title_map.get(callback_data, "Задачи")

        messenger.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{title}:",
        )

        if not tasks:
            messenger.send_message(chat_id, "Список пуст!")
            return HandlerStatus.STOP

        for task in tasks:
            task_id = task["id"]
            card_text = format_task_card_text(task)
            card_markup = get_task_card_reply_markup(task_id)
            messenger.send_message(
                chat_id=chat_id, text=card_text, reply_markup=card_markup
            )

        return HandlerStatus.STOP
