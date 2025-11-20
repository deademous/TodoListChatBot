from bot.dispatcher import Dispatcher
from bot.handlers.menu_handlers.message_help import MessageHelp
from tests.mocks import Mock


def test_message_help_handler():

    test_update = {
        "update_id": 1004,
        "message": {
            "message_id": 3,
            "from": {"id": 456},
            "chat": {"id": 456},
            "text": "❓ Помощь",
        },
    }

    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 456
        return {"state": None, "data_json": "{}"}

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 456
        assert "**Справка по боту-планировщику**" in text
        assert params.get("parse_mode") == "Markdown"
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock({"get_user": get_user})
    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageHelp())

    dispatcher.dispatch(test_update)

    assert send_message_called
