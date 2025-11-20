from bot.dispatcher import Dispatcher
from bot.handlers.tools.task_action_callback_handler import TaskActionCallbackHandler
from tests.mocks import Mock


def test_task_action_done():
    test_update = {
        "update_id": 3,
        "callback_query": {
            "id": "cb_3",
            "from": {"id": 789},
            "message": {"message_id": 30, "chat": {"id": 789}},
            "data": "task_done:55",
        },
    }

    update_status_called = False
    edit_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def update_task_status(task_id: int, status: str) -> None:
        assert task_id == 55
        assert status == "done"
        nonlocal update_status_called
        update_status_called = True

    def get_task_by_id(task_id: int) -> dict:
        return {"id": 55, "text": "Тест", "task_time": "12:00", "status": "done"}

    def edit_message_text(chat_id: int, message_id: int, text: str, **params) -> dict:
        assert "✅ [ВЫПОЛНЕНО]" in text
        nonlocal edit_message_called
        edit_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_task_status": update_task_status,
            "get_task_by_id": get_task_by_id,
        }
    )
    mock_messenger = Mock(
        {
            "edit_message_text": edit_message_text,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskActionCallbackHandler())
    dispatcher.dispatch(test_update)

    assert update_status_called
    assert edit_message_called


def test_task_action_postpone_start():
    test_update = {
        "update_id": 4,
        "callback_query": {
            "id": "cb_4",
            "from": {"id": 999},
            "message": {"message_id": 40, "chat": {"id": 999}},
            "data": "task_postpone:66",
        },
    }

    update_data_called = False
    update_state_called = False
    delete_msg_called = False
    send_msg_called = False

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def update_temp_data(telegram_id: int, data: dict) -> None:
        assert data == {"postpone_task_id": 66}
        nonlocal update_data_called
        update_data_called = True

    def update_user_state(telegram_id: int, state: str) -> None:
        assert state == "WAIT_POSTPONE_TIME"
        nonlocal update_state_called
        update_state_called = True

    def delete_message(chat_id: int, message_id: int) -> dict:
        nonlocal delete_msg_called
        delete_msg_called = True
        return {"ok": True}

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert "На сколько отложить?" in text
        assert "inline_keyboard" in params.get("reply_markup", "")
        nonlocal send_msg_called
        send_msg_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_temp_data": update_temp_data,
            "update_user_state": update_user_state,
        }
    )
    mock_messenger = Mock(
        {
            "delete_message": delete_message,
            "send_message": send_message,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskActionCallbackHandler())
    dispatcher.dispatch(test_update)

    assert update_data_called
    assert update_state_called
    assert delete_msg_called
    assert send_msg_called
