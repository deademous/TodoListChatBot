import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_time_handler import TaskTimeHandler
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_task_time_handler():
    test_update = {
        "update_id": 1009,
        "message": {
            "message_id": 7,
            "from": {"id": 444},
            "chat": {"id": 444},
            "text": "14:30",
        },
    }

    calls = {
        "create_task": False,
        "clear_state": False,
        "send_message": 0,
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 444
        return {
            "state": "WAIT_TASK_TIME",
            "data_json": '{"text": "Позвонить другу", "date": "2025-01-01"}',
        }

    async def mock_create_task(telegram_id: int, text: str, task_date: str, task_time: str):
        assert telegram_id == 444
        assert text == "Позвонить другу"
        assert task_date == "2025-01-01"
        assert task_time == "14:30"
        calls["create_task"] = True
        return 99

    async def mock_clear_user_state_and_temp_data(telegram_id: int):
        assert telegram_id == 444
        calls["clear_state"] = True

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 444
        calls["send_message"] += 1
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": mock_get_user,
            "create_task": mock_create_task,
            "clear_user_state_and_temp_data": mock_clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock({"send_message": mock_send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskTimeHandler())

    await dispatcher.dispatch(test_update)

    assert calls["create_task"]
    assert calls["clear_state"]
    assert calls["send_message"] == 2
