import bot.telegram_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class MessageHelp(Handler):

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return (
            state is None
            and "message" in update
            and "text" in update["message"]
            and (
                update["message"]["text"] == "❓ Помощь"
                or update["message"]["text"] == "/help"
            )
        )

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        chat_id = update["message"]["chat"]["id"]

        text = (
            "**Справка по боту-планировщику**\n\n"
            "Я помогу вам не забыть о делах.\n\n"
            "**Основные команды:**\n"
            "• `➕ Добавить задачу` - запуск пошагового создания новой задачи.\n"
            "• `📅 Мои задачи` - просмотр активных задач (на сегодня, завтра и без даты).\n"
            "• `⚙️ Настройки` - установка времени для утренних и вечерних уведомлений.\n\n"
            "Бот автоматически напомнит вам о задачах с установленным временем."
        )

        bot.telegram_client.sendMessage(
            chat_id=chat_id, text=text, parse_mode="Markdown"
        )
        return HandlerStatus.STOP
