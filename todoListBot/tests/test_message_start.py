from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.message_start import MessageStart
from tests.mocks import Mock
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


def test_message_start_handler():

    test_update = {
        "update_id": 1002,
        "message": {
            "message_id": 1,
            "from": {"id": 54321},
            "chat": {"id": 54321},
            "text": "/start",
        },
    }

    clear_user_data_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 54321
        return {"state": "SOME_STATE", "data_json": '{"text": "old data"}'}

    def clear_user_state_and_temp_data(telegram_id: int) -> None:
        assert telegram_id == 54321
        nonlocal clear_user_data_called
        clear_user_data_called = True

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 54321
        assert text == "Бот-Планировщик к вашим услугам!"
        assert params.get("reply_markup") == MAIN_MENU_KEYBOARD
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "clear_user_state_and_temp_data": clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(MessageStart())

    dispatcher.dispatch(test_update)

    assert clear_user_data_called
    assert send_message_called
