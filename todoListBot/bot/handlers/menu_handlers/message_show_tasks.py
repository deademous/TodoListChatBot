import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.handlers.tools.task_card import (
    format_task_card_text,
    get_task_card_reply_markup,
)


class MessageShowTasks(Handler):

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state is None
            and "message" in update
            and "text" in update["message"]
            and update["message"]["text"] == "📅 Мои задачи"
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["message"]["from"]["id"]
        chat_id = update["message"]["chat"]["id"]

        bot.database_client.clear_user_state_and_temp_data(telegram_id)

        task_groups = [
            ("📅 Задачи на Сегодня:", "show_today"),
            ("➡️ Задачи на Завтра:", "show_tomorrow"),
            ("📝 Задачи без даты:", "show_nodate"),
        ]

        found_any_tasks = False

        for header, filter_type in task_groups:
            tasks = bot.database_client.get_tasks_by_filter(telegram_id, filter_type)

            bot.telegram_client.sendMessage(
                chat_id=chat_id,
                text=f"\n{header}\n",
            )

            if not tasks:
                bot.telegram_client.sendMessage(chat_id=chat_id, text="Список пуст.")
                continue

            found_any_tasks = True

            for task in tasks:
                task_id = task["id"]

                card_text = format_task_card_text(task)

                card_markup = get_task_card_reply_markup(task_id)

                bot.telegram_client.sendMessage(
                    chat_id=chat_id,
                    text=card_text,
                    reply_markup=card_markup,
                )

        if not found_any_tasks:
            bot.telegram_client.sendMessage(
                chat_id=chat_id, text="У вас пока нет активных задач."
            )

        return HandlerStatus.STOP
