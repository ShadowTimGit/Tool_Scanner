import json
import os
import sys

from performance_debug import print_perf_summary, time_block
from tool_logger.tool_logger_config import INPUT_ROOT
from tool_logger.tool_logger_extraction import extract_tool_info
from tool_logger.workbook import save_to_spreadsheet
from tool_logger.json_sync import sync_json_from_workbook
from tool_logger.tool_logger_spreadsheets import rebuild_workbook_from_json


# ==================================================
# Process JSON File
# ==================================================

def process_json_file(
    json_path,
):
    with time_block(
        "logger.process_json_file",
        json_path=os.path.basename(json_path),
    ):
        print(
            f"Processing: {json_path}"
        )

        if not os.path.exists(json_path):
            alternate_path = json_path.replace(
                "_Logged.json",
                "_Unlogged.json",
            )

            if os.path.exists(alternate_path):
                json_path = alternate_path

        with time_block(
            "logger.json_load",
            json_path=os.path.basename(json_path),
        ):
            with open(
                json_path,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        relative_path_updated = False

        for key in ("File Path to Image", "File Path to JSON"):
            if isinstance(data, dict) and data.get(key):
                path_value = str(data[key]).strip()
                if path_value and not os.path.isabs(path_value):
                    data[key] = os.path.abspath(path_value)
                    relative_path_updated = True

        if relative_path_updated:
            with open(
                json_path,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

        with time_block(
            "logger.extract_tool_info",
            record_size=len(data) if isinstance(data, dict) else 0,
        ):
            row_data = extract_tool_info(
                data,
            )

        logged_path = json_path.replace(
            "_Unlogged.json",
            "_Logged.json",
        )

        if logged_path != json_path:
            os.rename(
                json_path,
                logged_path,
            )

            json_path = logged_path

        row_data["File Path to JSON"] = json_path

        with time_block(
            "logger.save_to_spreadsheet",
            records=1 if row_data else 0,
        ):
            log_path = save_to_spreadsheet(
                row_data
            )

        print(
            f"  Logged: {log_path}"
        )

        return True


# ==================================================
# Process Directory
# ==================================================

def process_directory():
    print(
        "================================"
    )

    print(
        "TOOL LOGGER STARTED"
    )

    print(
        "================================"
    )

    if not os.path.exists(
        INPUT_ROOT
    ):
        print(
            f"Analysis directory does not "
            f"exist: {INPUT_ROOT}"
        )
        return


    processed_count = 0
    failed_count = 0

    # ------------------------------------------------
    # Process all unlogged JSON files
    # ------------------------------------------------

    for root, _, files in os.walk(
        INPUT_ROOT
    ):
        for filename in sorted(
            files
        ):
            if not filename.endswith(
                "_Unlogged.json"
            ):
                continue

            json_path = os.path.join(
                root,
                filename,
            )

            success = process_json_file(
                json_path,
            )

            if success:
                processed_count += 1
            else:
                failed_count += 1

    print(
        "================================"
    )

    print(
        "TOOL LOGGER FINISHED"
    )

    print(
        f"Logged: {processed_count}"
    )

    print(
        f"Failed: {failed_count}"
    )

    print(
        "================================"
    )


# ==================================================
# Main
# ==================================================
# python logger.py --rebuild
# 
# python logger.py --sync

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--rebuild":
            try:
                rebuild_workbook_from_json()

            except Exception as error:
                print(
                    f"Failed to rebuild spreadsheet: "
                    f"{error}"
                )

        elif sys.argv[1] == "--sync":
            try:
                sync_json_from_workbook()

            except Exception as error:
                print(
                    f"Failed to sync JSON files: "
                    f"{error}"
                )

        else:
            json_path = sys.argv[1]

            process_json_file(
                json_path,
            )

    else:
        process_directory()

    print_perf_summary()