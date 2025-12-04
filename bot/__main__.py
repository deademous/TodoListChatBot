from bot.dispatcher import Dispatcher
from bot.handlers import get_handlers
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.infrastructure.messenger_telegram import MessengerTelegram
from bot.infrastructure.storage_postgres import StoragePostgres
from bot.notifier import start_notifier
import bot.long_polling
import asyncio


async def main() -> None:
    storage: Storage = StoragePostgres()
    messenger: Messenger = MessengerTelegram()
    try:
        dispatcher = Dispatcher(storage, messenger)
        dispatcher.add_handlers(*get_handlers())

        asyncio.create_task(start_notifier(storage, messenger))

        await bot.long_polling.start_long_polling(dispatcher, messenger)
    except KeyboardInterrupt:
        print("\nBye!")
    finally:
        if hasattr(messenger, "close"):
            await messenger.close()
        if hasattr(storage, "close"):
            await storage.close()


if __name__ == "__main__":
    asyncio.run(main())
