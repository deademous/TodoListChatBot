import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


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
