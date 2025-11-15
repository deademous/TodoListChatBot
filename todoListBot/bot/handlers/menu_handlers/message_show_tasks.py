import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


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

        tasks = bot.database_client.get_active_tasks(telegram_id)

        if not tasks:
            text = "Задач пока нет."
        else:
            text = "Ваши активные задачи:\n"
            for task in tasks:
                text += f"\n• {task['text']}"

        bot.telegram_client.sendMessage(chat_id=chat_id, text=text)
        return HandlerStatus.STOP
