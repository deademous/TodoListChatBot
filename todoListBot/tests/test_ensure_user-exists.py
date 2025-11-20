from bot.dispatcher import Dispatcher
from bot.handlers.tools.ensure_user_exists import EnsureUserExists
from tests.mocks import Mock


def test_ensure_user_exists_handler():
    test_update = {
        "update_id": 1001,
        "message": {
            "message_id": 1,
            "from": {"id": 12345},
            "chat": {"id": 12345},
            "text": "/start",
        },
    }

    ensure_user_exists_called = False

    def ensure_user_exists(telegram_id: int) -> None:
        nonlocal ensure_user_exists_called
        ensure_user_exists_called = True
        assert telegram_id == 12345

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 12345
        return {"state": None, "data_json": "{}"}

    mock_storage = Mock(
        {
            "ensure_user_exists": ensure_user_exists,
            "get_user": get_user,
        }
    )
    mock_messenger = Mock({})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(EnsureUserExists())

    dispatcher.dispatch(test_update)

    assert ensure_user_exists_called
