import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.menu_handlers.message_show_tasks import MessageShowTasks
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_message_show_tasks_handler_with_tasks():
    test_update = {
        "update_id": 1006,
        "message": {
            "message_id": 5,
            "from": {"id": 111},
            "chat": {"id": 111},
            "text": "📅 Мои задачи",
        },
    }

    calls = {
        "clear_state": False,
        "get_tasks": [],
        "send_message": []
    }

    mock_tasks_today = [
        {"id": 1, "text": "Купить молоко", "task_time": "14:00", "status": "active"}
    ]
    mock_tasks_tomorrow = []
    mock_tasks_nodate = [
        {"id": 2, "text": "Позвонить", "task_time": None, "status": "active"}
    ]

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 111
        return {"state": None, "data_json": "{}"}

    async def mock_clear_user_state_and_temp_data(telegram_id: int):
        assert telegram_id == 111
        calls["clear_state"] = True

    async def mock_get_tasks_by_filter(telegram_id: int, filter_type: str):
        assert telegram_id == 111
        calls["get_tasks"].append(filter_type)
        if filter_type == "show_today":
            return mock_tasks_today
        if filter_type == "show_tomorrow":
            return mock_tasks_tomorrow
        if filter_type == "show_nodate":
            return mock_tasks_nodate
        return []

    async def mock_send_message(chat_id: int, text: str, **params):
        assert chat_id == 111
        calls["send_message"].append({"text": text, "params": params})
        return {"ok": True}

    mock_storage = Mock({
        "get_user": mock_get_user,
        "clear_user_state_and_temp_data": mock_clear_user_state_and_temp_data,
        "get_tasks_by_filter": mock_get_tasks_by_filter,
    })
    mock_messenger = Mock({"send_message": mock_send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageShowTasks())

    await dispatcher.dispatch(test_update)

    assert calls["clear_state"]
    assert len(calls["get_tasks"]) == 3

    send_messages = calls["send_message"]
    assert len(send_messages) == 6
    assert "📅 Задачи на Сегодня:" in send_messages[0]["text"]
    assert "[14:00] Купить молоко" in send_messages[1]["text"]
    assert "task_done:1" in send_messages[1]["params"].get("reply_markup", "{}")
    assert "➡️ Задачи на Завтра:" in send_messages[2]["text"]
    assert "Список пуст." in send_messages[3]["text"]
    assert "📝 Задачи без даты:" in send_messages[4]["text"]
    assert "[Без времени] Позвонить" in send_messages[5]["text"]
    assert "task_done:2" in send_messages[5]["params"].get("reply_markup", "{}")
