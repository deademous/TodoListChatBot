import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_name_handler import TaskNameHandler
from tests.mocks import Mock
from bot.interface.keyboards import TASK_DATE_KEYBOARD


@pytest.mark.asyncio
async def test_task_name_handler():
    test_update = {
        "update_id": 1007,
        "message": {
            "message_id": 6,
            "from": {"id": 222},
            "chat": {"id": 222},
            "text": "Купить молоко",
        },
    }

    calls = {
        "update_data": False,
        "update_state": False,
        "send_message": False,
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 222
        return {"state": "WAIT_TASK_NAME", "data_json": "{}"}

    async def mock_update_user_data(telegram_id: int, data: dict):
        assert telegram_id == 222
        assert data == {"text": "Купить молоко"}
        calls["update_data"] = True

    async def mock_update_user_state(telegram_id: int, state: str):
        assert telegram_id == 222
        assert state == "WAIT_TASK_DATE"
        calls["update_state"] = True

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 222
        assert "На какой день?" in text
        assert params.get("reply_markup") == TASK_DATE_KEYBOARD
        calls["send_message"] = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": mock_get_user,
            "update_user_data": mock_update_user_data,
            "update_user_state": mock_update_user_state,
        }
    )
    mock_messenger = Mock({"send_message": mock_send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskNameHandler())

    await dispatcher.dispatch(test_update)

    assert calls["update_data"]
    assert calls["update_state"]
    assert calls["send_message"]
