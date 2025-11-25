from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_name_handler import TaskNameHandler
from tests.mocks import Mock
from bot.interface.keyboards import TASK_DATE_KEYBOARD


def test_task_name_handler():

    test_update = {
        "update_id": 1007,
        "message": {
            "message_id": 6,
            "from": {"id": 222},
            "chat": {"id": 222},
            "text": "Купить молоко",
        },
    }

    update_data_called = False
    update_state_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 222
        return {"state": "WAIT_TASK_NAME", "data_json": "{}"}

    def update_user_data(telegram_id: int, data: dict) -> None:
        assert telegram_id == 222
        assert data == {"text": "Купить молоко"}
        nonlocal update_data_called
        update_data_called = True

    def update_user_state(telegram_id: int, state: str) -> None:
        assert telegram_id == 222
        assert state == "WAIT_TASK_DATE"
        nonlocal update_state_called
        update_state_called = True

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 222
        assert "На какой день?" in text
        assert params.get("reply_markup") == TASK_DATE_KEYBOARD
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_user_data": update_user_data,
            "update_user_state": update_user_state,
        }
    )

    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskNameHandler())
    dispatcher.dispatch(test_update)

    assert update_data_called
    assert update_state_called
    assert send_message_called
