import asyncio
from datetime import datetime, timedelta
from bot.domain.storage import Storage
from bot.domain.messenger import Messenger
from bot.handlers.tools.task_card import (
    format_task_card_text,
    get_task_card_reply_markup,
)


async def start_notifier(storage: Storage, messenger: Messenger) -> None:
    while True:
        try:
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

            due_tasks = await storage.get_due_tasks(current_date, current_time)

            for task in due_tasks:
                task_id = task["id"]
                chat_id = task["chat_id"]

                card_text = "⏰ НАПОМИНАНИЕ!\n" + format_task_card_text(task)
                card_markup = get_task_card_reply_markup(task_id)

                await messenger.send_message(
                    chat_id=chat_id, text=card_text, reply_markup=card_markup
                )

                await storage.mark_task_as_notified(task_id)

            morning_users = await storage.get_users_for_scheduled_notifications(
                current_time, "morning_digest_time"
            )

            for user in morning_users:
                chat_id = user["telegram_id"]

                tasks_for_digest = await storage.get_active_tasks_for_digest(
                    chat_id, current_date
                )

                await _send_task_list(
                    messenger,
                    chat_id,
                    "Утренний дайджест на сегодня",
                    tasks_for_digest,
                )

            evening_users = await storage.get_users_for_scheduled_notifications(
                current_time, "evening_review_time"
            )

            for user in evening_users:
                chat_id = user["telegram_id"]

                tasks_for_tomorrow = await storage.get_tasks_for_tomorrow(
                    chat_id, tomorrow_date
                )

                await _send_task_list(
                    messenger,
                    chat_id,
                    "Вечерний обзор задач на завтра",
                    tasks_for_tomorrow,
                )

        except Exception as e:
            print(f"Error in notifier: {e}")

        await asyncio.sleep(60)


async def _send_task_list(
    messenger: Messenger, chat_id: int, title: str, tasks: list[dict]
) -> None:
    header_text = f"{'☀️' if 'Утренний дайджест' in title else '🌙'} {title}\n"

    if not tasks:
        await messenger.send_message(chat_id=chat_id, text=f"{header_text}Список задач пуст!")
    else:
        await messenger.send_message(chat_id=chat_id, text=header_text)

        for task in tasks:
            card_text = format_task_card_text(task)
            card_markup = get_task_card_reply_markup(task["id"])
            await messenger.send_message(
                chat_id=chat_id, text=card_text, reply_markup=card_markup
            )
