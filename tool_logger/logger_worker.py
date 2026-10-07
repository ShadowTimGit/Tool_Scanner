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

        return process_json_file(
            json_filepath
        )

    except Exception as error:
        print(
            f"ERROR: Logger exception: "
            f"{error}"
        )

        return False


def rebuild_logger():
    try:
        from logger import rebuild_workbook_from_json

        rebuild_workbook_from_json()

    except Exception as error:
        print(
            f"ERROR: Logger rebuild failed: "
            f"{error}"
        )


def submit_json(
    json_filepath,
    on_complete=None,
):
    executor = get_logger_executor()

    try:
        future = executor.submit(
            log_json_file,
            json_filepath,
        )

        if on_complete is not None:
            future.add_done_callback(
                on_complete
            )

        return future

    except Exception as error:
        print(
            f"ERROR: Could not submit logger job: "
            f"{error}"
        )

        return None


def submit_rebuild():
    get_logger_executor().submit(
        rebuild_logger,
    )

def remove_crop_file_and_workbook(
    json_filepath,
    image_filepath,
):
    try:
        import os
        from tool_logger.workbook import remove_row_from_workbook_by_path

        if json_filepath and os.path.exists(json_filepath):
            os.remove(json_filepath)

        if image_filepath and os.path.exists(image_filepath):
            os.remove(image_filepath)

        return remove_row_from_workbook_by_path(
            json_path=json_filepath,
            image_path=image_filepath,
        )

    except Exception as error:
        print(
            f"ERROR: Remove crop failed: "
            f"{error}"
        )

        return False

def submit_remove_crop(
    json_filepath,
    image_filepath,
    on_complete=None,
):
    executor = get_logger_executor()

    try:
        future = executor.submit(
            remove_crop_file_and_workbook,
            json_filepath,
            image_filepath,
        )

        if on_complete is not None:
            future.add_done_callback(
                on_complete
            )

        return future

    except Exception as error:
        print(
            f"ERROR: Could not submit crop removal: "
            f"{error}"
        )

        return None