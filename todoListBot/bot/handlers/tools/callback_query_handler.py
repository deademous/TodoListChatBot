import json
import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.handlers.tools.task_card import format_task_card_text


class CallbackQueryHandler(Handler):

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return state is None and "callback_query" in update

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = update["callback_query"]["from"]["id"]
        chat_id = update["callback_query"]["message"]["chat"]["id"]
        message_id = update["callback_query"]["message"]["message_id"]
        callback_data = update["callback_query"]["data"]

        bot.telegram_client.answerCallbackQuery(update["callback_query"]["id"])

        if callback_data.startswith("show_"):
            tasks = bot.database_client.get_tasks_by_filter(telegram_id, callback_data)

            bot.telegram_client.editMessageText(
                chat_id=chat_id,
                message_id=message_id,
                text=f"Задачи ({callback_data}):",
            )

            if not tasks:
                bot.telegram_client.sendMessage(chat_id, "Список пуст!")
                return HandlerStatus.STOP

            for task in tasks:
                bot.telegram_client.sendMessage(
                    chat_id=chat_id,
                    text=f"• {task['text']} (Дата: {task['task_date']}, Время: {task['task_time']})",
                )

            return HandlerStatus.STOP

        elif callback_data.startswith("task_"):
            try:
                action, task_id_str = callback_data.split(":", 1)
                task_id = int(task_id_str)
            except ValueError:
                return HandlerStatus.STOP

            new_status = None

            if action == "task_done":
                new_status = "done"
            elif action == "task_cancel":
                new_status = "canceled"

            elif action == "task_postpone":
                bot.database_client.update_user_data(
                    telegram_id, {"postpone_task_id": task_id}
                )

                bot.database_client.update_user_state(telegram_id, "WAIT_POSTPONE_TIME")

                bot.telegram_client.deleteMessage(
                    chat_id=chat_id, message_id=message_id
                )

                inline_keyboard = json.dumps(
                    {
                        "inline_keyboard": [
                            [
                                {"text": "На 1 час", "callback_data": "postpone:1h"},
                                {"text": "На 3 часа", "callback_data": "postpone:3h"},
                            ],
                            [
                                {
                                    "text": "На Завтра",
                                    "callback_data": "postpone:tomorrow",
                                },
                                {"text": "На 1 день", "callback_data": "postpone:1d"},
                            ],
                        ]
                    }
                )

                bot.telegram_client.sendMessage(
                    chat_id=chat_id,
                    text="🕑 На сколько нужно отложить задачу? Выберите или введите дату/время (например, 'завтра 18:00' или '2ч'):",
                    reply_markup=inline_keyboard,
                )

                return HandlerStatus.STOP

            if new_status:
                bot.database_client.update_task_status(task_id, new_status)

                updated_task = bot.database_client.get_task_by_id(task_id)

                if updated_task:
                    new_card_text = format_task_card_text(updated_task)

                    bot.telegram_client.editMessageText(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=new_card_text,
                        reply_markup=json.dumps({"inline_keyboard": []}),
                    )

                return HandlerStatus.STOP

        return HandlerStatus.CONTINUE

        if callback_data == "set_morning":
            bot.database_client.update_user_state(telegram_id, "WAIT_SETTING_MORNING")

            bot.telegram_client.editMessageText(
                chat_id=chat_id,
                message_id=message_id,
                text="Вы выбрали 'Изменить утро'.",
            )
            bot.telegram_client.sendMessage(
                chat_id=chat_id,
                text="Введите новое время для утреннего дайджеста (в формате ЧЧ:ММ):",
            )
            return HandlerStatus.STOP

        if callback_data == "set_evening":
            bot.database_client.update_user_state(telegram_id, "WAIT_SETTING_EVENING")

            bot.telegram_client.editMessageText(
                chat_id=chat_id,
                message_id=message_id,
                text="Вы выбрали 'Изменить вечер'.",
            )
            bot.telegram_client.sendMessage(
                chat_id=chat_id,
                text="Введите новое время для вечернего обзора (в формате ЧЧ:ММ):",
            )
            return HandlerStatus.STOP

        return HandlerStatus.STOP
