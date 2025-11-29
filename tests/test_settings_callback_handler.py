import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.tools.settings_callback_handler import SettingsCallbackHandler
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_settings_callback_handler_morning():
    test_update = {
        "update_id": 2,
        "callback_query": {
            "id": "cb_2",
            "from": {"id": 456},
            "message": {"message_id": 20, "chat": {"id": 456}},
            "data": "set_morning",
        },
    }

    calls = {
        "update_state": False,
        "send_message": False,
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 456
        return {"state": None, "data_json": "{}"}

    async def mock_update_user_state(telegram_id: int, state: str):
        assert telegram_id == 456
        assert state == "WAIT_SETTING_MORNING"
        calls["update_state"] = True

    async def mock_edit_message_text(chat_id: int, message_id: int, text: str, **params):
        return {"ok": True}

    async def mock_send_message(chat_id: int, text: str, **params):
        assert "Введите новое время" in text
        calls["send_message"] = True
        return {"ok": True}

    async def mock_answer_callback_query(cb_id: str):
        assert cb_id == "cb_2"

    mock_storage = Mock({
        "get_user": mock_get_user,
        "update_user_state": mock_update_user_state,
    })
    mock_messenger = Mock({
        "edit_message_text": mock_edit_message_text,
        "send_message": mock_send_message,
        "answer_callback_query": mock_answer_callback_query,
    })

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(SettingsCallbackHandler())

    await dispatcher.dispatch(test_update)

    assert calls["update_state"]
    assert calls["send_message"]
