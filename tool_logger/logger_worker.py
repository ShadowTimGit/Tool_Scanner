# logger_worker.py

from concurrent.futures import ProcessPoolExecutor

LOGGER_EXECUTOR = None


def get_logger_executor():
    global LOGGER_EXECUTOR

    if LOGGER_EXECUTOR is None:
        LOGGER_EXECUTOR = ProcessPoolExecutor(
            max_workers=1,
        )

    return LOGGER_EXECUTOR

def log_json_file(json_filepath):
    try:
        from logger import process_json_file

        success = process_json_file(
            json_filepath
        )

        if not success:
            print(
                f"ERROR: Logger failed: "
                f"{json_filepath}"
            )

    except Exception as error:
        print(
            f"ERROR: Logger exception: "
            f"{error}"
        )


def rebuild_logger():
    try:
        from logger import rebuild_workbook_from_json

        rebuild_workbook_from_json()

    except Exception as error:
        print(
            f"ERROR: Logger rebuild failed: "
            f"{error}"
        )


def submit_json(json_filepath):
    executor = get_logger_executor()

    try:
        executor.submit(
            log_json_file,
            json_filepath,
        )

    except Exception as error:
        print(
            f"ERROR: Could not submit logger job: "
            f"{error}"
        )


def submit_rebuild():
    get_logger_executor().submit(
        rebuild_logger,
    )