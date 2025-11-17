import json
import os
import urllib.request
from dotenv import load_dotenv
from bot.domain.messenger import Messenger


class MessengerTelegram(Messenger):

    def __init__(self):
        load_dotenv()
        self._token = os.getenv("TELEGRAM_TOKEN")
        self._base_uri = os.getenv("TELEGRAM_BASE_URI")
        if not self._token or not self._base_uri:
            raise ValueError("TELEGRAM_TOKEN или TELEGRAM_BASE_URI не найдены в .env")

    def _make_request(self, method: str, **params) -> dict:
        json_data = json.dumps(params).encode("utf-8")
        request = urllib.request.Request(
            method="POST",
            url=f"{self._base_uri}/{method}",
            data=json_data,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode("utf-8")
            response_json = json.loads(response_body)
            assert response_json["ok"]
            return response_json["result"]

    def send_message(self, chat_id: int, text: str, **params) -> dict:
        return self._make_request("sendMessage", chat_id=chat_id, text=text, **params)

    def get_updates(self, **params) -> dict:
        return self._make_request("getUpdates", **params)

    def delete_message(self, chat_id: int, message_id: int) -> dict:
        return self._make_request(
            "deleteMessage",
            chat_id=chat_id,
            message_id=message_id,
        )

    def answer_callback_query(self, callback_query_id: str, **params) -> dict:
        return self._make_request(
            "answerCallbackQuery",
            callback_query_id=callback_query_id,
            **params,
        )

    def edit_message_text(
        self, chat_id: int, message_id: int, text: str, **params
    ) -> dict:
        return self._make_request(
            "editMessageText",
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            **params,
        )

    def edit_message_reply_markup(
        self, chat_id: int, message_id: int, **params
    ) -> dict:
        return self._make_request(
            "editMessageReplyMarkup", chat_id=chat_id, message_id=message_id, **params
        )
