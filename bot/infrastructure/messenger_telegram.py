import os
import time
import logging
import aiohttp
from dotenv import load_dotenv
from bot.domain.messenger import Messenger

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s.%(msecs)03d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class MessengerTelegram(Messenger):
    def __init__(self) -> None:
        self._token = os.getenv("TELEGRAM_TOKEN")
        if not self._token:
            raise ValueError("TELEGRAM_TOKEN не найден в .env")
        self._base_uri = f"https://api.telegram.org/bot{self._token}"
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(self, method: str, **params) -> dict:
        url = f"{self._base_uri}/{method}"
        start_time = time.time()
        logger.info(f"[HTTP] → POST {method} started")

        try:
            session = await self._get_session()
            async with session.post(url, json=params) as response:
                response_json = await response.json()
                assert response_json["ok"]

                duration_ms = (time.time() - start_time) * 1000
                logger.info(f"[HTTP] ← POST {method} finished - {duration_ms:.2f}ms")
                return response_json["result"]

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"[HTTP] ✗ POST {method} failed - {duration_ms:.2f}ms - Error: {e}")
            raise

    async def close(self) -> None:
        """Закрыть HTTP-сессию."""
        if self._session and not self._session.closed:
            await self._session.close()

    # Методы Telegram API
    async def send_message(self, chat_id: int, text: str, **params) -> dict:
        return await self._make_request("sendMessage", chat_id=chat_id, text=text, **params)

    async def get_updates(self, **params) -> list:
        return await self._make_request("getUpdates", **params)

    async def delete_message(self, chat_id: int, message_id: int) -> dict:
        return await self._make_request("deleteMessage", chat_id=chat_id, message_id=message_id)

    async def answer_callback_query(self, callback_query_id: str, **params) -> dict:
        return await self._make_request("answerCallbackQuery", callback_query_id=callback_query_id, **params)

    async def edit_message_text(self, chat_id: int, message_id: int, text: str, **params) -> dict:
        return await self._make_request("editMessageText", chat_id=chat_id, message_id=message_id, text=text, **params)

    async def edit_message_reply_markup(self, chat_id: int, message_id: int, **params) -> dict:
        return await self._make_request("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id, **params)
