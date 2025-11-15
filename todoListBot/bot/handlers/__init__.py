from bot.handlers.tools.handler import Handler
from bot.handlers.tools.database_logger import DatabaseLogger
from bot.handlers.tools.ensure_user_exists import EnsureUserExists
from bot.handlers.state_handlers.message_start import MessageStart
from bot.handlers.state_handlers.task_name_handler import TaskNameHandler
from bot.handlers.menu_handlers.message_add_task import MessageAddTask
from bot.handlers.menu_handlers.message_show_tasks import MessageShowTasks
from bot.handlers.state_handlers.task_date_handler import TaskDateHandler
from bot.handlers.state_handlers.task_no_time_handler import TaskNoTimeHandler
from bot.handlers.state_handlers.task_time_handler import TaskTimeHandler
from bot.handlers.tools.callback_query_handler import CallbackQueryHandler
from bot.handlers.menu_handlers.message_settings import MessageSettings
from bot.handlers.menu_handlers.message_help import MessageHelp
from bot.handlers.state_handlers.settings_time_handler import SettingsTimeHandler


def get_handlers() -> list[Handler]:
    return [
        DatabaseLogger(),
        EnsureUserExists(),
        MessageStart(),
        MessageAddTask(),
        MessageShowTasks(),
        MessageSettings(),
        MessageHelp(),
        TaskNameHandler(),
        TaskDateHandler(),
        TaskTimeHandler(),
        TaskNoTimeHandler(),
        SettingsTimeHandler(),
        CallbackQueryHandler(),
    ]
