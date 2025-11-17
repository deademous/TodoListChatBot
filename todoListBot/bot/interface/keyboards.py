import json

MAIN_MENU_KEYBOARD = json.dumps(
    {
        "keyboard": [
            [{"text": "➕ Добавить задачу"}],
            [{"text": "📅 Мои задачи"}, {"text": "⚙️ Настройки"}],
            [{"text": "❓ Помощь"}],
        ],
        "resize_keyboard": True,
    }
)

REMOVE_KEYBOARD = json.dumps({"remove_keyboard": True})

SETTINGS_KEYBOARD = json.dumps(
            {
                "inline_keyboard": [
                    [{"text": "☀️ Изменить утро", "callback_data": "set_morning"}],
                    [{"text": "🌙 Изменить вечер", "callback_data": "set_evening"}],
                ]
            }
        )

TASK_DATE_KEYBOARD = json.dumps(
            {
                "inline_keyboard": [
                    [{"text": "Сегодня", "callback_data": "set_date_today"}],
                    [{"text": "Завтра", "callback_data": "set_date_tomorrow"}],
                    [{"text": "Без даты", "callback_data": "set_date_nodate"}],
                ]
            }
        )