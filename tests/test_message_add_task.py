import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.menu_handlers.message_add_task import MessageAddTask
from tests.mocks import Mock
from bot.interface.keyboards import REMOVE_KEYBOARD


@pytest.mark.asyncio
async def test_message_add_task_handler():
    test_update = {
        "update_id": 1003,
        "message": {
            "message_id": 2,
            "from": {"id": 123},
            "chat": {"id": 123},
            "text": "➕ Добавить задачу",
        },
    }

    calls = {
        "update_state": False,
        "send_message": False
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 123
        return {"state": None, "data_json": "{}"}

    async def mock_update_user_state(telegram_id: int, state: str):
        assert telegram_id == 123
        assert state == "WAIT_TASK_NAME"
        calls["update_state"] = True

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 123
        assert text == "Напишите, что нужно сделать:"
        assert params.get("reply_markup") == REMOVE_KEYBOARD
        calls["send_message"] = True
        return {"ok": True}

    mock_storage = Mock({
        "get_user": mock_get_user,
        "update_user_state": mock_update_user_state,
    })
    mock_messenger = Mock({"send_message": mock_send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageAddTask())

    await dispatcher.dispatch(test_update)

    assert calls["update_state"]
    assert calls["send_message"]
