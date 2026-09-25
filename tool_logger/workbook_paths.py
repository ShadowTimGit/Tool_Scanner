import os

from tool_logger.tool_logger_config import (
    LOG_ROOT,
)


WORKBOOK_NAME = "Tool_Log.xlsx"


def get_workbook_path():

    os.makedirs(
        LOG_ROOT,
        exist_ok=True,
    )

    return os.path.join(
        LOG_ROOT,
        WORKBOOK_NAME,
    )