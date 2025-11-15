import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class EnsureUserExists(Handler):
    def _get_telegram_id(self, update: dict) -> int | None:
        if "message" in update:
            return update["message"]["from"]["id"]
        elif "callback_query" in update:
            return update["callback_query"]["from"]["id"]
        return None

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return self._get_telegram_id(update) is not None

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = self._get_telegram_id(update)
        if telegram_id:
            bot.database_client.ensure_user_exists(telegram_id)
        return HandlerStatus.CONTINUE
