import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus


class DatabaseLogger(Handler):
    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return True
    
    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        bot.database_client.persist_updates([update])
        return HandlerStatus.CONTINUE  