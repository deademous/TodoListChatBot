import pytest

from bot.dispatcher import Dispatcher
from bot.handlers.tools.ensure_user_exists import EnsureUserExists
from tests.mocks import Mock


@pytest.mark.asyncio
async def test_ensure_user_exists_handler():
    test_update = {
        "update_id": 1001,
        "message": {
            "message_id": 1,
            "from": {"id": 12345},
            "chat": {"id": 12345},
            "text": "/start",
        },
    }

    calls = {"ensure_user_exists": False}

    async def mock_ensure_user_exists(telegram_id: int):
        assert telegram_id == 12345
        calls["ensure_user_exists"] = True

    async def mock_get_user(telegram_id: int):
        assert telegram_id == 12345
        return {"state": None, "data_json": "{}"}

    mock_storage = Mock(
        {
            "ensure_user_exists": mock_ensure_user_exists,
            "get_user": mock_get_user,
        }
    )
    mock_messenger = Mock({})

    dispatcher = Dispatcher(mock_storage, mock_messenger)
    dispatcher.add_handlers(EnsureUserExists())

    await dispatcher.dispatch(test_update)

    assert calls["ensure_user_exists"]
