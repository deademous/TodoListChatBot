import json
from datetime import datetime, timedelta
import re
from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.handlers.tools.task_card import format_task_card_text
from bot.interface.keyboards import MAIN_MENU_KEYBOARD


class PostponeHandler(Handler):

    def can_handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> bool:
        return state == "WAIT_POSTPONE_TIME"

    def handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> HandlerStatus:

        telegram_id = None
        callback_data = None
        chat_id = None

        postpone_task_id = data_json.get("postpone_task_id")

        if "message" in update:
            telegram_id = update["message"]["from"]["id"]
        elif "callback_query" in update:
            telegram_id = update["callback_query"]["from"]["id"]

        if not postpone_task_id:
            if telegram_id:
                storage.clear_user_state_and_temp_data(telegram_id)
            return HandlerStatus.STOP

        new_date = None
        new_time = None
        now = datetime.now()

        if "message" in update:
            telegram_id = update["message"]["from"]["id"]
            chat_id = update["message"]["chat"]["id"]
            input_text = update["message"]["text"].lower().strip()

            if "завтра" in input_text:
                new_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
                time_match = re.search(r"(\d{1,2}:\d{2})", input_text)
                new_time = time_match.group(1) if time_match else None
            elif re.search(r"(\d+)\s*(ч|h)", input_text):
                match = re.search(r"(\d+)\s*(ч|h)", input_text)
                hours = int(match.group(1))
                new_datetime = now + timedelta(hours=hours)
                new_date = new_datetime.strftime("%Y-%m-%d")
                new_time = new_datetime.strftime("%H:%M")
            elif re.search(r"(\d+)\s*(м|min)", input_text):
                match = re.search(r"(\d+)\s*(м|min)", input_text)
                minutes = int(match.group(1))
                new_datetime = now + timedelta(minutes=minutes)
                new_date = new_datetime.strftime("%Y-%m-%d")
                new_time = new_datetime.strftime("%H:%M")
            elif re.match(r"\d{1,2}\.\d{1,2}", input_text):
                try:
                    parts = input_text.split()
                    date_part = parts[0]
                    day, month = map(int, date_part.split("."))
                    target_date = datetime(now.year, month, day)
                    new_date = target_date.strftime("%Y-%m-%d")
                    new_time = parts[1] if len(parts) > 1 else None
                except:
                    new_date = None
                    new_time = None

            if not new_date:
                messenger.send_message(
                    chat_id=chat_id,
                    text="Не удалось распознать дату/время. Попробуйте формат 'завтра 18:00', '1ч' или '25.12'.",
                )
                return HandlerStatus.STOP

        elif "callback_query" in update:
            telegram_id = update["callback_query"]["from"]["id"]
            chat_id = update["callback_query"]["message"]["chat"]["id"]
            callback_data = update["callback_query"]["data"]

            messenger.answer_callback_query(update["callback_query"]["id"])

            if not callback_data.startswith("postpone:"):
                return HandlerStatus.STOP

            _, delay_type = callback_data.split(":")
            new_datetime = None

            if delay_type == "1h":
                new_datetime = now + timedelta(hours=1)
            elif delay_type == "3h":
                new_datetime = now + timedelta(hours=3)
            elif delay_type == "tomorrow" or delay_type == "1d":
                new_datetime = now + timedelta(days=1)

            if new_datetime:
                new_date = new_datetime.strftime("%Y-%m-%d")
                new_time = new_datetime.strftime("%H:%M")
            else:
                return HandlerStatus.STOP

        if telegram_id and new_date:
            storage.update_task(
                postpone_task_id,
                task_date=new_date,
                task_time=new_time,
                status="active",
            )
            storage.clear_user_state_and_temp_data(telegram_id)
            updated_task = storage.get_task_by_id(postpone_task_id)
            response_text = f"✅ Задача успешно отложена на {new_date} в {new_time or 'любое время'}."

            if updated_task:
                card_text = format_task_card_text(updated_task)
                response_text += f"\n\nОтложенная задача:\n{card_text}"

            reply_markup = MAIN_MENU_KEYBOARD

            messenger.send_message(
                chat_id=chat_id, text=response_text, reply_markup=reply_markup
            )
            return HandlerStatus.STOP

        return HandlerStatus.CONTINUE
