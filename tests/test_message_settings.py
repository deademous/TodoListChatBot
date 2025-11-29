import pytest
from bot.dispatcher import Dispatcher
from bot.handlers.menu_handlers.message_settings import MessageSettings
from tests.mocks import Mock
from bot.interface.keyboards import SETTINGS_KEYBOARD


@pytest.mark.asyncio
async def test_message_settings_handler():
    test_update = {
        "update_id": 2000,
        "message": {
            "message_id": 10,
            "from": {"id": 101},
            "chat": {"id": 101},
            "text": "⚙️ Настройки",
        },
    }

    send_message_called = False
    sent_text = ""
    sent_reply_markup = None

    async def mock_get_user(telegram_id: int):
        return {"state": None, "data_json": "{}"}

    async def mock_get_user_settings(telegram_id: int):
        assert telegram_id == 101
        return {"morning_digest_time": "08:00", "evening_review_time": "22:00"}

    async def mock_send_message(chat_id: int, text: str, **params):
        nonlocal send_message_called, sent_text, sent_reply_markup
        send_message_called = True
        sent_text = text
        sent_reply_markup = params.get("reply_markup")
        return {"ok": True}

    mock_storage = Mock(
        {"get_user": mock_get_user, "get_user_settings": mock_get_user_settings}
    )
    mock_messenger = Mock({"send_message": mock_send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageSettings())

    await dispatcher.dispatch(test_update)

    assert send_message_called
    assert "08:00" in sent_text
    assert "22:00" in sent_text
    assert sent_reply_markup == SETTINGS_KEYBOARD
