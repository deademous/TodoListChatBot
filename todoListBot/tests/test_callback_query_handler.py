import json
from bot.dispatcher import Dispatcher
from bot.handlers.tools.callback_query_handler import CallbackQueryHandler
from tests.mocks import Mock


def test_callback_query_handler_task_done():
    test_update = {
        "update_id": 1014,
        "callback_query": {
            "id": "cb_4",
            "from": {"id": 999},
            "message": {"message_id": 15, "chat": {"id": 999}},
            "data": "task_done:123",
        },
    }

    update_status_called = False
    get_task_called = False
    edit_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def update_task_status(task_id: int, status: str) -> None:
        assert task_id == 123
        assert status == "done"
        nonlocal update_status_called
        update_status_called = True

    def get_task_by_id(task_id: int) -> dict:
        assert task_id == 123
        nonlocal get_task_called
        get_task_called = True
        return {"id": 123, "text": "Задача", "task_time": "10:00", "status": "done"}

    def edit_message_text(chat_id: int, message_id: int, text: str, **params) -> dict:
        assert chat_id == 999
        assert message_id == 15
        assert "✅ [ВЫПОЛНЕНО]" in text
        assert params.get("reply_markup") == json.dumps({"inline_keyboard": []})
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
    dispatcher.add_handlers(CallbackQueryHandler())
    dispatcher.dispatch(test_update)

    assert update_status_called
    assert get_task_called
    assert edit_message_called


def test_callback_query_handler_task_postpone():
    test_update = {
        "update_id": 1015,
        "callback_query": {
            "id": "cb_5",
            "from": {"id": 1000},
            "message": {"message_id": 16, "chat": {"id": 1000}},
            "data": "task_postpone:124",
        },
    }

    update_data_called = False
    update_state_called = False
    delete_message_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def update_user_data(telegram_id: int, data: dict) -> None:
        assert telegram_id == 1000
        assert data == {"postpone_task_id": 124}
        nonlocal update_data_called
        update_data_called = True

    def update_user_state(telegram_id: int, state: str) -> None:
        assert telegram_id == 1000
        assert state == "WAIT_POSTPONE_TIME"
        nonlocal update_state_called
        update_state_called = True

    def delete_message(chat_id: int, message_id: int) -> dict:
        assert chat_id == 1000
        assert message_id == 16
        nonlocal delete_message_called
        delete_message_called = True
        return {"ok": True}

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 1000
        assert "🕑 На сколько нужно отложить задачу?" in text
        assert "inline_keyboard" in params.get("reply_markup", "{}")
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
    mock_messenger = Mock(
        {
            "delete_message": delete_message,
            "send_message": send_message,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(CallbackQueryHandler())
    dispatcher.dispatch(test_update)

    assert update_data_called
    assert update_state_called
    assert delete_message_called
    assert send_message_called


def test_callback_query_handler_set_morning():
    test_update = {
        "update_id": 1016,
        "callback_query": {
            "id": "cb_6",
            "from": {"id": 1001},
            "message": {"message_id": 17, "chat": {"id": 1001}},
            "data": "set_morning",
        },
    }

    update_state_called = False
    edit_message_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        return {"state": None, "data_json": "{}"}

    def update_user_state(telegram_id: int, state: str) -> None:
        assert telegram_id == 1001
        assert state == "WAIT_SETTING_MORNING"
        nonlocal update_state_called
        update_state_called = True

    def edit_message_text(chat_id: int, message_id: int, text: str, **params) -> dict:
        assert chat_id == 1001
        assert message_id == 17
        nonlocal edit_message_called
        edit_message_called = True
        return {"ok": True}

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 1001
        assert "Введите новое время" in text
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_user_state": update_user_state,
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
    dispatcher.add_handlers(CallbackQueryHandler())
    dispatcher.dispatch(test_update)

    assert update_state_called
    assert edit_message_called
    assert send_message_called
