from bot.domain.storage import Storage
from bot.domain.messenger import Messenger 
from bot.handlers.tools.handler import Handler, HandlerStatus


class DatabaseLogger(Handler):
    def can_handle(self, update: dict, state: str, data_json: dict, storage: Storage, messenger: Messenger) -> bool:
        return True
    
    def handle(self, update: dict, state: str, data_json: dict, storage: Storage, messenger: Messenger) -> HandlerStatus:
        storage.persist_update(update) 
        return HandlerStatus.CONTINUE