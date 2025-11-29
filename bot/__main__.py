from bot.dispatcher import Dispatcher
from bot.handlers import get_handlers
from bot.long_polling import start_long_polling
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.infrastructure.messenger_telegram import MessengerTelegram
from bot.infrastructure.storage_postgres import StoragePostgres
from bot.notifier import start_notifier
import threading
import asyncio


async def main() -> None:
    storage: Storage = StoragePostgres()
    messenger: Messenger = MessengerTelegram()
    try:
        dispatcher = Dispatcher(storage, messenger)
        dispatcher.add_handlers(*get_handlers())

        notifier_thread = threading.Thread(
            target=start_notifier, args=(storage, messenger), daemon=True
        )
        notifier_thread.start()

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
