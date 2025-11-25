from bot.dispatcher import Dispatcher
from bot.handlers.menu_handlers.message_show_tasks import MessageShowTasks
from tests.mocks import Mock


def test_message_show_tasks_handler_with_tasks():
    test_update = {
        "update_id": 1006,
        "message": {
            "message_id": 5,
            "from": {"id": 111},
            "chat": {"id": 111},
            "text": "📅 Мои задачи",
        },
    }

    clear_state_called = False
    get_tasks_calls = []
    send_message_calls = []

    mock_tasks_today = [
        {"id": 1, "text": "Купить молоко", "task_time": "14:00", "status": "active"}
    ]
    mock_tasks_tomorrow = []
    mock_tasks_nodate = [
        {"id": 2, "text": "Позвонить", "task_time": None, "status": "active"}
    ]

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def clear_user_state_and_temp_data(telegram_id: int) -> None:
        assert telegram_id == 111
        nonlocal clear_state_called
        clear_state_called = True

    def get_tasks_by_filter(telegram_id: int, filter_type: str) -> list[dict]:
        assert telegram_id == 111
        get_tasks_calls.append(filter_type)
        if filter_type == "show_today":
            return mock_tasks_today
        if filter_type == "show_tomorrow":
            return mock_tasks_tomorrow
        if filter_type == "show_nodate":
            return mock_tasks_nodate
        return []

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 111
        send_message_calls.append({"text": text, "params": params})
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "clear_user_state_and_temp_data": clear_user_state_and_temp_data,
            "get_tasks_by_filter": get_tasks_by_filter,
        }
    )
    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageShowTasks())
    dispatcher.dispatch(test_update)

    assert clear_state_called
    assert len(get_tasks_calls) == 3

    assert len(send_message_calls) == 6
    assert "📅 Задачи на Сегодня:" in send_message_calls[0]["text"]
    assert "[14:00] Купить молоко" in send_message_calls[1]["text"]
    assert "task_done:1" in send_message_calls[1]["params"].get("reply_markup", "{}")
    assert "➡️ Задачи на Завтра:" in send_message_calls[2]["text"]
    assert "Список пуст." in send_message_calls[3]["text"]
    assert "📝 Задачи без даты:" in send_message_calls[4]["text"]
    assert "[Без времени] Позвонить" in send_message_calls[5]["text"]
    assert "task_done:2" in send_message_calls[5]["params"].get("reply_markup", "{}")
