from bot.dispatcher import Dispatcher
from bot.handlers.tools.settings_callback_handler import SettingsCallbackHandler
from tests.mocks import Mock


def test_settings_callback_handler_morning():
    test_update = {
        "update_id": 2,
        "callback_query": {
            "id": "cb_2",
            "from": {"id": 456},
            "message": {"message_id": 20, "chat": {"id": 456}},
            "data": "set_morning",
        },
    }

    update_state_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def update_user_state(telegram_id: int, state: str) -> None:
        assert telegram_id == 456
        assert state == "WAIT_SETTING_MORNING"
        nonlocal update_state_called
        update_state_called = True

    def edit_message_text(chat_id: int, message_id: int, text: str, **params) -> dict:
        return {"ok": True}

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert "Введите новое время" in text
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_user_state": update_user_state,
        }
    )
    mock_messenger = Mock(
        {
            "edit_message_text": edit_message_text,
            "send_message": send_message,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(SettingsCallbackHandler())
    dispatcher.dispatch(test_update)

    assert update_state_called
    assert send_message_called
