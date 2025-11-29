from datetime import datetime, timedelta
from bot.handlers.tools.handler import Handler, HandlerStatus
from bot.domain.messenger import Messenger
from bot.domain.storage import Storage
from bot.handlers.tools.task_card import format_task_card_text
from bot.interface.keyboards import MAIN_MENU_KEYBOARD
from bot.handlers.tools.time_parser import normalize_time


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

    async def handle(
        self,
        update: dict,
        state: str,
        data_json: dict,
        storage: Storage,
        messenger: Messenger,
    ) -> HandlerStatus:

        telegram_id = None
        chat_id = None

        postpone_task_id = data_json.get("postpone_task_id")

        if "message" in update:
            telegram_id = update["message"]["from"]["id"]
            chat_id = update["message"]["chat"]["id"]
        elif "callback_query" in update:
            telegram_id = update["callback_query"]["from"]["id"]
            chat_id = update["callback_query"]["message"]["chat"]["id"]

        if not postpone_task_id:
            if telegram_id:
                await storage.clear_user_state_and_temp_data(telegram_id)
            return HandlerStatus.STOP

        new_date = None
        new_time = None
        now = datetime.now()

        if "message" in update:
            text = update["message"]["text"].strip()

            normalized_time = normalize_time(text)

            if normalized_time:
                new_date = now.strftime("%Y-%m-%d")
                new_time = normalized_time
            else:
                messenger.send_message(
                    chat_id,
                    "Неверный формат. Введите время, например: '08:30', '9:00' или '21.00'.",
                )
                return HandlerStatus.STOP

        elif "callback_query" in update:
            callback_data = update["callback_query"]["data"]

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
            await storage.update_task(
                postpone_task_id,
                task_date=new_date,
                task_time=new_time,
                status="active",
            )
            await storage.clear_user_state_and_temp_data(telegram_id)
            updated_task = await storage.get_task_by_id(postpone_task_id)

            time_display = new_time if new_time else "любое время"
            response_text = (
                f"✅ Задача успешно отложена на {new_date} в {time_display}."
            )

            if updated_task:
                card_text = format_task_card_text(updated_task)
                response_text += f"\n\nОтложенная задача:\n{card_text}"

            reply_markup = MAIN_MENU_KEYBOARD

            messenger.send_message(
                chat_id=chat_id, text=response_text, reply_markup=reply_markup
            )
            return HandlerStatus.STOP

        return HandlerStatus.STOP
