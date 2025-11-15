from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.database_client import get_user
import json

class Dispatcher:
    def __init__(self):
        self._handlers: list[Handler] = []

    def add_handler(self, *handlers: list[Handler]) -> None:
        for handler in handlers:
            self._handlers.append(handler)

    def _get_telegram_id_from_update(self, update: dict) -> int | None:
        if "message" in update:
            return update["message"]["from"]["id"]
        elif "callback_query" in update:
            return update["callback_query"]["from"]["id"]
        return None

    def dispatch(self, update: dict) -> None:
        telegram_id = self._get_telegram_id_from_update(update)
        user = get_user(telegram_id) if telegram_id else None
        
        user_state = user.get("state") if user else None
        data_json_str = user.get("data_json") if user else "{}"
        
        if data_json_str is None:
            data_json_str = "{}"
            
        data_json = json.loads(data_json_str)
        
        for handler in self._handlers:
            if handler.can_handle(update, user_state, data_json):
                signal = handler.handle(update, user_state, data_json)
                if signal == HandlerStatus.STOP:
                    break
