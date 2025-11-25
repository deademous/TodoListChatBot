from bot.dispatcher import Dispatcher
from bot.handlers.state_handlers.settings_time_handler import SettingsTimeHandler
from tests.mocks import Mock
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


def test_settings_time_handler_valid():
    test_update = {
        "update_id": 1011,
        "message": {
            "message_id": 8,
            "from": {"id": 666},
            "chat": {"id": 666},
            "text": "08:00",
        },
    }

    update_setting_called = False
    clear_state_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 666
        return {"state": "WAIT_SETTING_MORNING", "data_json": "{}"}

    def update_user_setting_time(
        telegram_id: int, setting_type: str, new_time: str
    ) -> None:
        assert telegram_id == 666
        assert setting_type == "morning_digest_time"
        assert new_time == "08:00"
        nonlocal update_setting_called
        update_setting_called = True

    def clear_user_state_and_temp_data(telegram_id: int) -> None:
        assert telegram_id == 666
        nonlocal clear_state_called
        clear_state_called = True

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 666
        assert "✅ Готово!" in text
        assert params.get("reply_markup") == MAIN_MENU_KEYBOARD
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_user_setting_time": update_user_setting_time,
            "clear_user_state_and_temp_data": clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(SettingsTimeHandler())
    dispatcher.dispatch(test_update)

    assert update_setting_called
    assert clear_state_called
    assert send_message_called


def test_settings_time_handler_invalid():
    """
    Тестирует FSM 'WAIT_SETTING_EVENING' с невалидным временем.
    """
    test_update = {
        "update_id": 1012,
        "message": {
            "message_id": 9,
            "from": {"id": 777},
            "chat": {"id": 777},
            "text": "abc",
        },
    }

    update_setting_called = False
    clear_state_called = False
    send_message_called = False

    def get_user(telegram_id: int) -> dict | None:
        return {"state": "WAIT_SETTING_EVENING", "data_json": "{}"}

    def update_user_setting_time(
        telegram_id: int, setting_type: str, new_time: str
    ) -> None:
        nonlocal update_setting_called
        update_setting_called = True

    def clear_user_state_and_temp_data(telegram_id: int) -> None:
        nonlocal clear_state_called
        clear_state_called = True

    def send_message(chat_id: int, text: str, **params) -> dict:
        assert chat_id == 777
        assert "Неверный формат" in text
        nonlocal send_message_called
        send_message_called = True
        return {"ok": True}

    mock_storage = Mock(
        {
            "get_user": get_user,
            "update_user_setting_time": update_user_setting_time,
            "clear_user_state_and_temp_data": clear_user_state_and_temp_data,
        }
    )
    mock_messenger = Mock({"send_message": send_message})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(SettingsTimeHandler())
    dispatcher.dispatch(test_update)

    assert not update_setting_called
    assert not clear_state_called
    assert send_message_called
