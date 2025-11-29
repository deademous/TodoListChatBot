import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_date_handler import TaskDateHandler
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_task_date_handler():
    test_update = {
        "update_id": 1008,
        "callback_query": {
            "id": "cb_1",
            "from": {"id": 333},
            "message": {"message_id": 10, "chat": {"id": 333}},
            "data": "set_date_today",
        },
    }

    calls = {
        "update_data": False,
        "update_state": False,
        "edit_message": False,
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 333
        return {"state": "WAIT_TASK_DATE", "data_json": '{"text": "Купить молоко"}'}

    async def mock_update_user_data(telegram_id: int, data: dict):
        assert telegram_id == 333
        assert data["text"] == "Купить молоко"
        assert "date" in data
        calls["update_data"] = True

    async def mock_update_user_state(telegram_id: int, state: str):
        assert telegram_id == 333
        assert state == "WAIT_TASK_TIME"
        calls["update_state"] = True

    async def mock_edit_message_text(chat_id: int, message_id: int, text: str, **params):
        assert chat_id == 333
        assert message_id == 10
        assert "Укажите время" in text
        assert "set_time_notime" in params.get("reply_markup", "{}")
        calls["edit_message"] = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": mock_get_user,
            "update_user_data": mock_update_user_data,
            "update_user_state": mock_update_user_state,
        }
    )
    mock_messenger = Mock(
        {
            "edit_message_text": mock_edit_message_text,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskDateHandler())

    await dispatcher.dispatch(test_update)

    assert calls["update_data"]
    assert calls["update_state"]
    assert calls["edit_message"]
