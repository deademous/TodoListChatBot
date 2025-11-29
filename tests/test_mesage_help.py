import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.menu_handlers.message_help import MessageHelp
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_message_help_handler():

    test_update = {
        "update_id": 1004,
        "message": {
            "message_id": 3,
            "from": {"id": 456},
            "chat": {"id": 456},
            "text": "❓ Помощь",
        },
    }

    calls = {
        "send_message": False
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 456
        return {"state": None, "data_json": "{}"}

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 456
        assert "**Справка по боту-планировщику**" in text
        assert params.get("parse_mode") == "Markdown"
        calls["send_message"] = True
        return {"ok": True}

    mock_storage = Mock({"get_user": mock_get_user})
    mock_messenger = Mock({"send_message": mock_send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageHelp())

    await dispatcher.dispatch(test_update)

    assert calls["send_message"]
