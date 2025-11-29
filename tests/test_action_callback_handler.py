import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.tools.task_action_callback_handler import TaskActionCallbackHandler
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_task_action_done():
    test_update = {
        "update_id": 999,
        "callback_query": {
            "id": "cb_3",
            "from": {"id": 789},
            "message": {"message_id": 30, "chat": {"id": 789}},
            "data": "task_done:55",
        },
    }

    calls = {
        "update_status": False,
        "edit_message": False
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 789
        return {"state": None, "data_json": "{}"}

    async def mock_update_task_status(task_id: int, status: str):
        assert task_id == 55
        assert status == "done"
        calls["update_status"] = True

    async def mock_get_task_by_id(task_id: int):
        assert task_id == 55
        return {"id": 55, "text": "Тест", "task_time": "12:00", "status": "done"}

    async def mock_edit_message_text(chat_id: int, message_id: int, text: str, **params):
        assert chat_id == 789
        assert message_id == 30
        assert "✅ [ВЫПОЛНЕНО]" in text
        calls["edit_message"] = True
        return {"ok": True}

    async def mock_answer_callback_query(cb_id: str):
        assert cb_id == "cb_3"

    mock_storage = Mock(
        {
            "get_user": mock_get_user,
            "update_task_status": mock_update_task_status,
            "get_task_by_id": mock_get_task_by_id,
        }
    )
    mock_messenger = Mock(
        {
            "edit_message_text": mock_edit_message_text,
            "answer_callback_query": mock_answer_callback_query,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskActionCallbackHandler())

    await dispatcher.dispatch(test_update)

    assert calls["update_status"]
    assert calls["edit_message"]


@pytest.mark.asyncio
async def test_task_action_postpone_start():
    test_update = {
        "update_id": 999,
        "callback_query": {
            "id": "cb_4",
            "from": {"id": 999},
            "message": {"message_id": 40, "chat": {"id": 999}},
            "data": "task_postpone:66",
        },
    }

    calls = {
        "update_data": False,
        "update_state": False,
        "delete_msg": False,
        "send_msg": False
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 999
        return {"state": None, "data_json": "{}"}

    async def mock_update_user_data(telegram_id: int, data: dict):
        assert data == {"postpone_task_id": 66}
        calls["update_data"] = True

    async def mock_update_user_state(telegram_id: int, state):
        assert state == "WAIT_POSTPONE_TIME"
        calls["update_state"] = True

    async def mock_delete_message(chat_id: int, message_id: int):
        assert chat_id == 999
        assert message_id == 40
        calls["delete_msg"] = True
        return {"ok": True}

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 999
        assert "На сколько отложить?" in text
        assert "inline_keyboard" in params.get("reply_markup", "")
        calls["send_msg"] = True
        return {"ok": True}

    async def mock_answer_callback_query(cb_id: str):
        assert cb_id == "cb_4"

    mock_storage = Mock(
        {
            "get_user": mock_get_user,
            "update_user_data": mock_update_user_data,
            "update_user_state": mock_update_user_state,
        }
    )
    mock_messenger = Mock(
        {
            "delete_message": mock_delete_message,
            "send_message": mock_send_message,
            "answer_callback_query": mock_answer_callback_query,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskActionCallbackHandler())

    await dispatcher.dispatch(test_update)

    assert calls["update_data"]
    assert calls["update_state"]
    assert calls["delete_msg"]
    assert calls["send_msg"]
