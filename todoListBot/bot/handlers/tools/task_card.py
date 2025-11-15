import json


def format_task_card_text(task: dict) -> str:

    if task.get("task_time"):
        time_str = f"[{task['task_time']}]"
    else:
        time_str = "[Без времени]"

    return f"{time_str} {task['text']}"


def get_task_card_reply_markup(task_id: int) -> str:

    return json.dumps(
        {
            "inline_keyboard": [
                [
                    {"text": "✅ Выполнить", "callback_data": f"task_done:{task_id}"},
                    {
                        "text": "🕑 Отложить",
                        "callback_data": f"task_postpone:{task_id}",
                    },
                    {"text": "❌ Отменить", "callback_data": f"task_cancel:{task_id}"},
                ]
            ]
        }
    )
