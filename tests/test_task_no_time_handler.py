from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_no_time_handler import TaskNoTimeHandler
from tests.mocks import Mock


def test_task_no_time_handler():
    test_update = {
        "update_id": 1010,
        "callback_query": {
            "id": "cb_2",
            "from": {"id": 555},
            "message": {"message_id": 11, "chat": {"id": 555}},
            "data": "set_time_notime",
        },
    }

    create_task_called = False
    clear_state_called = False
    edit_message_called = False
    send_message_calls = []

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 555
        return {
            "state": "WAIT_TASK_TIME",
            "data_json": '{"text": "Проверить почту", "date": null}',
        }

    def create_task(
        telegram_id: int, text: str, task_date: str | None, task_time: str | None
    ) -> int:
        assert telegram_id == 555
        assert text == "Проверить почту"
        assert task_date is None
        assert task_time is None
        nonlocal create_task_called
        create_task_called = True
        return 100  # ID новой задачи

    def clear_user_state_and_temp_data(telegram_id: int) -> None:
        assert telegram_id == 555
        nonlocal clear_state_called
        clear_state_called = True

    def edit_message_text(chat_id: int, message_id: int, text: str, **params) -> dict:
        assert chat_id == 555
        assert message_id == 11
        assert "Готово! Задача создана (без времени)." in text
        nonlocal edit_message_called
        edit_message_called = True
        return {"ok": True}

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 555
        send_message_calls.append({"text": text, "params": params})
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "create_task": create_task,
            "clear_user_state_and_temp_data": clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock(
        {
            "send_message": send_message,
            "edit_message_text": edit_message_text,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskNoTimeHandler())
    dispatcher.dispatch(test_update)

    assert create_task_called
    assert clear_state_called
    assert edit_message_called
    assert len(send_message_calls) == 2
    assert "Вы в главном меню." in send_message_calls[0]["text"]
    assert "[Без времени] Проверить почту" in send_message_calls[1]["text"]
