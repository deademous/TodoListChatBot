from bot.dispatcher import Dispatcher
from bot.handlers.menu_handlers.message_add_task import MessageAddTask
from tests.mocks import Mock
from bot.interface.keyboards import REMOVE_KEYBOARD


def test_message_add_task_handler():
    test_update = {
        "update_id": 1003,
        "message": {
            "message_id": 2,
            "from": {"id": 123},
            "chat": {"id": 123},
            "text": "➕ Добавить задачу",
        },
    }

    update_state_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 123
        return {"state": None, "data_json": "{}"}

    def update_user_state(telegram_id: int, state: str) -> None:
        assert telegram_id == 123
        assert state == "WAIT_TASK_NAME"
        nonlocal update_state_called
        update_state_called = True

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 123
        assert text == "Напишите, что нужно сделать:"
        assert params.get("reply_markup") == REMOVE_KEYBOARD
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_user_state": update_user_state,
        }
    )
    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageAddTask())

    dispatcher.dispatch(test_update)

    assert update_state_called
    assert send_message_called
