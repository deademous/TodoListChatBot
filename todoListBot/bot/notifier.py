from datetime import datetime
import time
from bot.domain.storage import Storage
from bot.domain.messenger import Messenger
from bot.handlers.tools.task_card import format_task_card_text, get_task_card_reply_markup


def start_notifier(storage: Storage, messenger: Messenger) -> None:

    while True:
        try:
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M") 
            
            due_tasks = storage.get_due_tasks(current_date, current_time)
            
            for task in due_tasks:
                task_id = task["id"]
                chat_id = task["chat_id"] 
                
                card_text = f"⏰ НАПОМИНАНИЕ! "
                card_text += f"{format_task_card_text(task)}"
                card_markup = get_task_card_reply_markup(task_id)

                messenger.send_message(
                    chat_id=chat_id, 
                    text=card_text, 
                    reply_markup=card_markup
                )
                
                storage.mark_task_as_notified(task_id)
                print(f"Sent reminder for task {task_id} to user {chat_id}")

        except Exception as e:
            print(f"Error in notifier: {e}")
            
        time.sleep(60)