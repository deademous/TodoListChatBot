from bot.handlers.tools.handler import Handler
from bot.handlers.tools.database_logger import DatabaseLogger
from bot.handlers.tools.ensure_user_exists import EnsureUserExists
from bot.handlers.state_handlers.message_start import MessageStart
from bot.handlers.state_handlers.task_name_handler import TaskNameHandler
from bot.handlers.menu_handlers.message_add_task import MessageAddTask
from bot.handlers.menu_handlers.message_show_tasks import MessageShowTasks


def get_handlers() -> list[Handler]:
    return [
        DatabaseLogger(),
        EnsureUserExists(),
        MessageStart(),
        MessageAddTask(),
        MessageShowTasks(),
        TaskNameHandler(),
    ]
