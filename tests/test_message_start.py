import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.message_start import MessageStart
from tests.mocks import Mock
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


@pytest.mark.asyncio
async def test_message_start_handler():
    test_update = {
        "update_id": 1002,
        "message": {
            "message_id": 1,
            "from": {"id": 54321},
            "chat": {"id": 54321},
            "text": "/start",
        },
    }

    calls = {
        "clear_user_data": False,
        "send_message": False,
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 54321
        return {"state": "SOME_STATE", "data_json": '{"text": "old data"}'}

    async def mock_clear_user_state_and_temp_data(telegram_id: int):
        assert telegram_id == 54321
        calls["clear_user_data"] = True

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 54321
        assert text == "Бот-Планировщик к вашим услугам!"
        assert params.get("reply_markup") == MAIN_MENU_KEYBOARD
        calls["send_message"] = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": mock_get_user,
            "clear_user_state_and_temp_data": mock_clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock({"send_message": mock_send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageStart())

    await dispatcher.dispatch(test_update)

    assert calls["clear_user_data"]
    assert calls["send_message"]
