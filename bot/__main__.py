from bot.dispatcher import Dispatcher
from bot.handlers import get_handlers
from bot.long_polling import start_long_polling
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.infrastructure.messenger_telegram import MessengerTelegram
from bot.infrastructure.storage_postgres import StoragePostgres
from bot.notifier import start_notifier
import threading


def main() -> None:
    try:
        storage: Storage = StoragePostgres()
        messenger: Messenger = MessengerTelegram()

        dispatcher = Dispatcher(storage, messenger)
        dispatcher.add_handlers(*get_handlers())

        notifier_thread = threading.Thread(
            target=start_notifier, args=(storage, messenger), daemon=True
        )
        notifier_thread.start()

        start_long_polling(dispatcher, messenger)

    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
