from bot.dispatcher import Dispatcher
from bot.handlers.tools.database_logger import DatabaseLogger
from tests.mocks import Mock


def test_database_logger_handler():

    test_update = {
        "update_id": 1000,
        "message": {
            "message_id": 1,
            "from": {"id": 123},
            "chat": {"id": 123},
            "text": "test",
        },
    }

    persist_update_called = False

    def persist_update(update: dict) -> None:
        nonlocal persist_update_called
        persist_update_called = True
        assert update == test_update

    def get_user(telegram_id: int) -> dict | None:
        assert telegram_id == 123
        return {"state": None, "data_json": "{}"}

    mock_storage = Mock(
        {
            "persist_update": persist_update,
            "get_user": get_user,
        }
    )
    mock_messenger = Mock({})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    db_logger = DatabaseLogger()
    dispatcher.add_handlers(db_logger)

    dispatcher.dispatch(test_update)

    assert persist_update_called
