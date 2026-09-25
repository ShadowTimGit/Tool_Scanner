import json
import os
import sys

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
    print(
        f"Processing: {json_path}"
    )

    try:
        with open(
            json_path,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ) as error:
        print(
            f"  Failed to read JSON: "
            f"{error}"
        )
        return False

    if not isinstance(
        data,
        dict,
    ):
        print(
            "  Invalid JSON structure."
        )
        return False

    row_data = extract_tool_info(
        data,
    )

    if row_data is None:
        print(
            "  Could not determine "
            "tool information."
        )
        return False

    # ------------------------------------------------
    # Save to spreadsheet
    # ------------------------------------------------

    try:
        log_path = save_to_spreadsheet(
            row_data
        )

    except Exception as error:
        print(
            f"  Failed to save spreadsheet: "
            f"{error}"
        )
        return False

    # ------------------------------------------------
    # Rename JSON
    # ------------------------------------------------

    logged_path = json_path.replace(
        "_Unlogged.json",
        "_Logged.json",
    )

    if logged_path == json_path:
        print(
            "  JSON filename does not "
            "contain _Unlogged."
        )
        return False

    try:
        os.rename(
            json_path,
            logged_path,
        )

    except OSError as error:
        print(
            f"  Failed to rename JSON: "
            f"{error}"
        )
        return False

    print(
        f"  Logged: {log_path}"
    )

    print(
        f"  Renamed: "
        f"{os.path.basename(json_path)} "
        f"-> "
        f"{os.path.basename(logged_path)}"
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