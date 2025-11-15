import json
from datetime import datetime, timedelta
import re

import bot.telegram_client
import bot.database_client
from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.handlers.tools.task_card import format_task_card_text


class PostponeHandler(Handler):

    def can_handle(self, update: dict, state: str, data_json: dict) -> bool:
        return state == "WAIT_POSTPONE_TIME"

    def handle(self, update: dict, state: str, data_json: dict) -> HandlerStatus:
        telegram_id = None
        callback_data = None
        chat_id = None

        postpone_task_id = data_json.get("postpone_task_id")

        if not postpone_task_id:
            bot.database_client.clear_user_state_and_temp_data(telegram_id)
            return HandlerStatus.STOP

        if "message" in update:
            telegram_id = update["message"]["from"]["id"]
            chat_id = update["message"]["chat"]["id"]
            input_text = update["message"]["text"].lower().strip()

            new_date = None
            new_time = None

            now = datetime.now()

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
                bot.telegram_client.sendMessage(
                    chat_id=chat_id,
                    text="Не удалось распознать дату/время. Попробуйте формат 'завтра 18:00', '1ч' или '25.12'.",
                )
                return HandlerStatus.STOP

        elif "callback_query" in update:
            telegram_id = update["callback_query"]["from"]["id"]
            chat_id = update["callback_query"]["message"]["chat"]["id"]
            callback_data = update["callback_query"]["data"]

            bot.telegram_client.answerCallbackQuery(update["callback_query"]["id"])

            if not callback_data.startswith("postpone:"):
                return HandlerStatus.STOP

            _, delay_type = callback_data.split(":")
            now = datetime.now()
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
            bot.database_client.update_task(
                postpone_task_id,
                task_date=new_date,
                task_time=new_time,
                status="active",
            )

            bot.database_client.clear_user_state_and_temp_data(telegram_id)

            updated_task = bot.database_client.get_task_by_id(postpone_task_id)

            response_text = f"✅ Задача успешно отложена на {new_date} в {new_time or 'любое время'}."

            if updated_task:
                card_text = format_task_card_text(updated_task)
                response_text += f"\n\nОтложенная задача:\n{card_text}"

            reply_markup = json.dumps(
                {
                    "keyboard": [
                        [{"text": "➕ Добавить задачу"}],
                        [{"text": "📅 Мои задачи"}, {"text": "⚙️ Настройки"}],
                        [{"text": "❓ Помощь"}],
                    ],
                    "resize_keyboard": True,
                }
            )

            bot.telegram_client.sendMessage(
                chat_id=chat_id, text=response_text, reply_markup=reply_markup
            )

            return HandlerStatus.STOP

        return HandlerStatus.CONTINUE
