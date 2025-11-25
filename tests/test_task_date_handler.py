from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.task_date_handler import TaskDateHandler
from tests.mocks import Mock


def test_task_date_handler():
    test_update = {
        "update_id": 1008,
        "callback_query": {
            "id": "cb_1",
            "from": {"id": 333},
            "message": {"message_id": 10, "chat": {"id": 333}},
            "data": "set_date_today",
        },
    }

    update_data_called = False
    update_state_called = False
    edit_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 333
        return {"state": "WAIT_TASK_DATE", "data_json": '{"text": "Купить молоко"}'}

    def update_user_data(telegram_id: int, data: dict) -> None:
        assert telegram_id == 333
        assert data["text"] == "Купить молоко"
        assert "date" in data
        nonlocal update_data_called
        update_data_called = True

    def update_user_state(telegram_id: int, state: str) -> None:
        assert telegram_id == 333
        assert state == "WAIT_TASK_TIME"
        nonlocal update_state_called
        update_state_called = True

    def edit_message_text(chat_id: int, message_id: int, text: str, **params) -> dict:
        assert chat_id == 333
        assert message_id == 10
        assert "Укажите время" in text
        assert "set_time_notime" in params.get("reply_markup", "{}")
        nonlocal edit_message_called
        edit_message_called = True
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
            "edit_message_text": edit_message_text,
            "answer_callback_query": lambda cb_id: None,
        }
    )

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(TaskDateHandler())
    dispatcher.dispatch(test_update)

    assert update_data_called
    assert update_state_called
    assert edit_message_called
