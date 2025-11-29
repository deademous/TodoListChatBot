import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.tools.database_logger import DatabaseLogger
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_database_logger_handler():

    test_update = {
        "update_id": 1000,
        "message": {
            "message_id": 1,
            "from": {"id": 123},
            "chat": {"id": 123},
            "text": "test",
        },
    }

    calls = {
        "persist_update": False
    }

    async def mock_persist_update(update: dict):
        calls["persist_update"] = True
        assert update == test_update

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 123
        return {"state": None, "data_json": "{}"}

    mock_storage = Mock(
        {
            "persist_update": mock_persist_update,
            "get_user": mock_get_user,
        }
    )
    mock_messenger = Mock({})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(DatabaseLogger())

    await dispatcher.dispatch(test_update)

    assert calls["persist_update"]
