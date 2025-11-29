import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_no_time_handler import TaskNoTimeHandler
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_task_no_time_handler():
    test_update = {
        "update_id": 1010,
        "callback_query": {
            "id": "cb_2",
            "from": {"id": 555},
            "message": {"message_id": 11, "chat": {"id": 555}},
            "data": "set_time_notime",
        },
    }

    calls = {
        "create_task": False,
        "clear_state": False,
        "edit_message": False,
        "send_message": 0,
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 555
        return {
            "state": "WAIT_TASK_TIME",
            "data_json": '{"text": "Проверить почту", "date": null}',
        }

    async def mock_create_task(
        telegram_id: int, text: str, task_date: str | None, task_time: str | None
    ):
        assert telegram_id == 555
        assert text == "Проверить почту"
        assert task_date is None
        assert task_time is None
        calls["create_task"] = True
        return 100

    async def mock_clear_user_state_and_temp_data(telegram_id: int):
        assert telegram_id == 555
        calls["clear_state"] = True

    async def mock_edit_message_text(
        chat_id: int, message_id: int, text: str, **params
    ):
        assert chat_id == 555
        assert message_id == 11
        assert "Готово! Задача создана (без времени)." in text
        calls["edit_message"] = True
        return {"ok": True}

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 555
        calls["send_message"] += 1
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": mock_get_user,
            "create_task": mock_create_task,
            "clear_user_state_and_temp_data": mock_clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock(
        {
            "send_message": mock_send_message,
            "edit_message_text": mock_edit_message_text,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskNoTimeHandler())

    await dispatcher.dispatch(test_update)

    assert calls["create_task"]
    assert calls["clear_state"]
    assert calls["edit_message"]
    assert calls["send_message"] == 2
