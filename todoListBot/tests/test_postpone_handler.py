from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.postpone_handler import PostponeHandler
from tests.mocks import Mock
from datetime import datetime, timedelta
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


def test_postpone_handler_callback():

    test_update = {
        "update_id": 1013,
        "callback_query": {
            "id": "cb_3",
            "from": {"id": 888},
            "message": {"message_id": 12, "chat": {"id": 888}},
            "data": "postpone:1h",
        },
    }

    update_task_called = False
    clear_state_called = False
    get_task_called = False
    send_message_called = False

    expected_time = (datetime.now() + timedelta(hours=1)).strftime("%H:%M")

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 888
        return {"state": "WAIT_POSTPONE_TIME", "data_json": '{"postpone_task_id": 123}'}

    def update_task(task_id: int, task_date: str, task_time: str, status: str) -> None:
        assert task_id == 123
        assert status == "active"
        assert task_time == expected_time
        nonlocal update_task_called
        update_task_called = True

    def clear_user_state_and_temp_data(telegram_id: int) -> None:
        assert telegram_id == 888
        nonlocal clear_state_called
        clear_state_called = True

    def get_task_by_id(task_id: int) -> dict:
        assert task_id == 123
        nonlocal get_task_called
        get_task_called = True
        return {
            "id": 123,
            "text": "Тестовая задача",
            "task_time": expected_time,
            "status": "active",
        }

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 888
        assert "✅ Задача успешно отложена" in text
        assert params.get("reply_markup") == MAIN_MENU_KEYBOARD
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_task": update_task,
            "clear_user_state_and_temp_data": clear_user_state_and_temp_data,
            "get_task_by_id": get_task_by_id,
        }
    )
    mock_messenger = Mock(
        {"send_message": send_message, "answer_callback_query": lambda cb_id: None}
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(PostponeHandler())
    dispatcher.dispatch(test_update)

    assert update_task_called
    assert clear_state_called
    assert get_task_called
    assert send_message_called
