from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_time_handler import TaskTimeHandler
from tests.mocks import Mock


def test_task_time_handler():

    test_update = {
        "update_id": 1009,
        "message": {
            "message_id": 7,
            "from": {"id": 444},
            "chat": {"id": 444},
            "text": "14:30",
        },
    }

    create_task_called = False
    clear_state_called = False
    send_message_calls = []

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 444
        return {
            "state": "WAIT_TASK_TIME",
            "data_json": '{"text": "Позвонить другу", "date": "2025-01-01"}',
        }

    def create_task(telegram_id: int, text: str, task_date: str, task_time: str) -> int:
        assert telegram_id == 444
        assert text == "Позвонить другу"
        assert task_date == "2025-01-01"
        assert task_time == "14:30"
        nonlocal create_task_called
        create_task_called = True
        return 99  # ID новой задачи

    def clear_user_state_and_temp_data(telegram_id: int) -> None:
        assert telegram_id == 444
        nonlocal clear_state_called
        clear_state_called = True

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 444
        send_message_calls.append({"text": text, "params": params})
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "create_task": create_task,
            "clear_user_state_and_temp_data": clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskTimeHandler())
    dispatcher.dispatch(test_update)

    assert create_task_called
    assert clear_state_called
    assert len(send_message_calls) == 2
    assert "Готово! Задача создана:" in send_message_calls[0]["text"]
    assert "[14:30] Позвонить другу" in send_message_calls[1]["text"]
    assert "task_done:99" in send_message_calls[1]["params"].get("reply_markup", "{}")
