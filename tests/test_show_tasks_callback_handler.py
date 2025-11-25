from bot.dispatcher import Dispatcher
from bot.handlers.tools.show_tasks_callback_handler import ShowTasksCallbackHandler
from tests.mocks import Mock


def test_show_tasks_callback_handler():

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

    get_tasks_called = False
    edit_message_called = False
    send_message_calls = []

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def get_tasks_by_filter(telegram_id: int, filter_type: str) -> list[dict]:
        assert telegram_id == 123
        assert filter_type == "show_today"
        nonlocal get_tasks_called
        get_tasks_called = True
        return mock_tasks

    def edit_message_text(chat_id: int, message_id: int, text: str, **params) -> dict:
        assert chat_id == 123
        assert "Задачи на сегодня" in text
        nonlocal edit_message_called
        edit_message_called = True
        return {"ok": True}

    def send_message(chat_id: int, text: str, **params) -> dict:
        send_message_calls.append(text)
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "get_tasks_by_filter": get_tasks_by_filter,
        }
    )
    mock_messenger = Mock(
        {
            "edit_message_text": edit_message_text,
            "send_message": send_message,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(ShowTasksCallbackHandler())
    dispatcher.dispatch(test_update)

    assert get_tasks_called
    assert edit_message_called
    assert len(send_message_calls) == 2
    assert "[10:00] Задача 1" in send_message_calls[0]
    assert "[Без времени] Задача 2" in send_message_calls[1]
