from bot.handlers.tools.handler import Handler, HandlerStatus
import json
import logging
import time
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

class Dispatcher:
    def __init__(self, storage: Storage, messenger: Messenger):
        self._handlers: list[Handler] = []
        self._storage: Storage = storage
        self._messenger: Messenger = messenger

    def add_handlers(self, *handlers: list[Handler]) -> None:
        for handler in handlers:
            self._handlers.append(handler)

    def _get_telegram_id_from_update(self, update: dict) -> int | None:
        if "message" in update:
            return update["message"]["from"]["id"]
        elif "callback_query" in update:
            return update["callback_query"]["from"]["id"]
        return None

    def dispatch(self, update: dict) -> None:
        update_id = update["update_id"]
        start_time = time.time()
        logger.info(f"[DISPATCH {update_id}] → dispatch started 🏃‍♂️")

        try:
            telegram_id = self._get_telegram_id_from_update(update)
            user = self._storage.get_user(telegram_id) if telegram_id else None

            user_state = user.get("state") if user else None
            data_json_str = user.get("data_json") if user else "{}"

            if data_json_str is None:
                data_json_str = "{}"

            data_json = json.loads(data_json_str)

            for handler in self._handlers:
                if handler.can_handle(
                    update,
                    user_state,
                    data_json,
                    self._storage,
                    self._messenger,
                ):
                    signal = handler.handle(
                        update,
                        user_state,
                        data_json,
                        self._storage,
                        self._messenger,
                    )
                    if signal == HandlerStatus.STOP:
                        break

            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"[DISPATCH {update_id}] ← dispatch finished - {duration_ms:.2f}ms\n")

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[DISPATCH {update_id}] ✗ dispatch failed - {duration_ms:.2f}ms - Error: {e}\n")
            raise
