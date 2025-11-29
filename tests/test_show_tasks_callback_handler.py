import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.tools.show_tasks_callback_handler import ShowTasksCallbackHandler
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_show_tasks_callback_handler():
    test_update = {
        "update_id": 1,
        "callback_query": {
            "id": "cb_1",
            "from": {"id": 123},
            "message": {"message_id": 10, "chat": {"id": 123}},
            "data": "show_today",
        },
    }

    mock_tasks = [
        {"id": 1, "text": "Задача 1", "task_time": "10:00", "status": "active"},
        {"id": 2, "text": "Задача 2", "task_time": None, "status": "active"},
    ]

    calls = {
        "get_tasks": False,
        "edit_message": False,
        "send_messages": [],
    }

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 123
        return {"state": None, "data_json": "{}"}

    async def mock_get_tasks_by_filter(telegram_id: int, filter_type: str):
        assert telegram_id == 123
        assert filter_type == "show_today"
        calls["get_tasks"] = True
        return mock_tasks

    async def mock_edit_message_text(chat_id: int, message_id: int, text: str, **params):
        assert chat_id == 123
        assert "Задачи на сегодня" in text
        calls["edit_message"] = True
        return {"ok": True}

    async def mock_send_message(chat_id: int, text: str, **params):
        calls["send_messages"].append(text)
        return {"ok": True}

    mock_storage = Mock({
        "get_user": mock_get_user,
        "get_tasks_by_filter": mock_get_tasks_by_filter,
    })
    mock_messenger = Mock({
        "edit_message_text": mock_edit_message_text,
        "send_message": mock_send_message,
        "answer_callback_query": lambda cb_id: None,
    })

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(ShowTasksCallbackHandler())

    await dispatcher.dispatch(test_update)

    assert calls["get_tasks"]
    assert calls["edit_message"]
    assert len(calls["send_messages"]) == 2
    assert "[10:00] Задача 1" in calls["send_messages"][0]
    assert "[Без времени] Задача 2" in calls["send_messages"][1]
