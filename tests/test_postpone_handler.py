import pytest
from datetime import datetime, timedelta

from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.postpone_handler import PostponeHandler
from tests.mocks import Mock
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


@pytest.mark.asyncio
async def test_postpone_handler_callback():
    test_update = {
        "update_id": 1013,
        "callback_query": {
            "id": "cb_3",
            "from": {"id": 888},
            "message": {"message_id": 12, "chat": {"id": 888}},
            "data": "postpone:1h",
        },
    }

    calls = {
        "update_task": False,
        "clear_state": False,
        "get_task": False,
        "send_message": False,
    }

    expected_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 888
        return {"state": "WAIT_POSTPONE_TIME", "data_json": '{"postpone_task_id": 123}'}

    async def mock_update_task(task_id: int, task_date: str, task_time: str, status: str):
        assert task_id == 123
        assert status == "active"
        assert task_time == expected_time
        calls["update_task"] = True

    async def mock_clear_user_state_and_temp_data(telegram_id: int):
        assert telegram_id == 888
        calls["clear_state"] = True

    async def mock_get_task_by_id(task_id: int):
        assert task_id == 123
        calls["get_task"] = True
        return {
            "id": 123,
            "text": "Тестовая задача",
            "task_time": expected_time,
            "status": "active",
        }

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 888
        assert "✅ Задача успешно отложена" in text
        assert params.get("reply_markup") == MAIN_MENU_KEYBOARD
        calls["send_message"] = True
        return {"ok": True}

    async def mock_answer_callback_query(cb_id: str):
        assert cb_id == "cb_3"

    mock_storage = Mock({
        "get_user": mock_get_user,
        "update_task": mock_update_task,
        "clear_user_state_and_temp_data": mock_clear_user_state_and_temp_data,
        "get_task_by_id": mock_get_task_by_id,
    })
    mock_messenger = Mock({
        "send_message": mock_send_message,
        "answer_callback_query": mock_answer_callback_query,
    })

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(PostponeHandler())

    await dispatcher.dispatch(test_update)

    assert calls["update_task"]
    assert calls["clear_state"]
    assert calls["get_task"]
    assert calls["send_message"]
