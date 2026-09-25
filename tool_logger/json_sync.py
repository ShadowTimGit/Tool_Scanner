import json
import os

from datetime import datetime

from openpyxl import load_workbook

from tool_logger.tool_logger_config import (
    PURCHASE_HEADERS,
    SALE_HEADERS,
    INPUT_ROOT,
)

from .calculations import (
    normalize_invoice,
)

from .workbook_paths import (
    get_workbook_path,
)

OUTPUT_DIR_LOG_NAME = "Converted_Tool_Logs"


# =========================================================
# Invoice Prices
# =========================================================

def load_invoice_prices(
    worksheet,
):

    invoice_prices = {}

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):

        row_values = [
            worksheet.cell(
                row=row_number,
                column=column,
            ).value
            for column in range(
                1,
                worksheet.max_column + 1,
            )
        ]

        if "Invoice Est. Sum" not in row_values:
            continue

        invoice = normalize_invoice(
            row_values[2]
        )

        if not invoice:
            continue

        try:
            invoice_price = float(
                row_values[14]
                or 0.0
            )

        except (
            TypeError,
            ValueError,
        ):
            invoice_price = 0.0

        invoice_prices[invoice] = invoice_price

    return invoice_prices


# =========================================================
# JSON Path Helpers
# =========================================================

def get_cell_path_value(
    cell,
):
    """
    Return the real stored path for a hyperlink cell.

    Excel often displays only the filename while the hyperlink
    target contains the absolute path we need to persist.
    """

    if cell is None:
        return ""

    hyperlink = getattr(
        cell,
        "hyperlink",
        None,
    )

    if hyperlink:
        target = getattr(
            hyperlink,
            "target",
            None,
        )

        if target:
            return str(
                target
            ).strip()

    if cell.value is not None:
        return str(
            cell.value
        ).strip()

    return ""


def get_json_path_from_cell(
    cell,
):
    """
    Get the JSON path stored in an Excel cell.

    Prefer the hyperlink target because the displayed value
    may only contain the filename.
    """

    return get_cell_path_value(cell)


def normalize_json_path(
    path,
):
    """
    Normalize a stored JSON path.

    Absolute paths are used directly.

    Relative paths are first checked relative to the current
    working directory and then relative to INPUT_ROOT.
    """

    if not path:
        return ""

    path = os.path.expanduser(
        str(path).strip()
    )

    if not path:
        return ""

    # -----------------------------------------------------
    # Absolute path.
    # -----------------------------------------------------

    if os.path.isabs(path):

        return os.path.abspath(
            os.path.normpath(path)
        )

    # -----------------------------------------------------
    # Relative path from current working directory.
    #
    # This preserves compatibility with existing workbook
    # hyperlinks that may already work this way.
    # -----------------------------------------------------

    current_directory_path = os.path.abspath(
        os.path.normpath(path)
    )

    if os.path.isfile(
        current_directory_path
    ):

        return current_directory_path

    # -----------------------------------------------------
    # Relative path from INPUT_ROOT.
    # -----------------------------------------------------

    input_root_path = os.path.abspath(
        os.path.join(
            INPUT_ROOT,
            path,
        )
    )

    if os.path.isfile(
        input_root_path
    ):

        return input_root_path

    return ""


def find_json_by_filename(
    filename,
):
    """
    Search INPUT_ROOT for an existing JSON file with the
    requested filename.

    This is a fallback for workbooks where the Excel cell
    contains only a filename or contains a stale hyperlink.
    """

    if not filename:
        return ""

    filename = os.path.basename(
        str(filename).strip()
    )

    if not filename:
        return ""

    for root, directories, files in os.walk(
        INPUT_ROOT
    ):

        # Do not modify directories while walking.
        directories[:] = sorted(
            directories
        )

        if filename in files:

            return os.path.abspath(
                os.path.join(
                    root,
                    filename,
                )
            )

    return ""


def resolve_existing_json_path(
    stored_json_path,
):
    """
    Resolve an existing JSON path using several increasingly
    broad checks.

    Returns an absolute path when the file exists.
    Returns an empty string when it cannot be found.
    """

    if not stored_json_path:
        return ""

    # -----------------------------------------------------
    # 1. Try the stored path exactly.
    # -----------------------------------------------------

    resolved_path = normalize_json_path(
        stored_json_path
    )

    if resolved_path:
        return resolved_path

    # -----------------------------------------------------
    # 2. If the stored path failed, search INPUT_ROOT by
    #    filename.
    # -----------------------------------------------------

    filename = os.path.basename(
        str(stored_json_path).strip()
    )

    return find_json_by_filename(
        filename
    )


def resolve_existing_image_path(
    stored_image_path,
):
    """
    Resolve an existing image path using the same logic as JSON:

    1. prefer the hyperlink target
    2. accept absolute paths
    3. resolve relative paths against the current working dir
    4. resolve relative paths against INPUT_ROOT
    5. fall back to filename search in INPUT_ROOT
    """

    if not stored_image_path:
        return ""

    candidate = str(stored_image_path).strip()

    if not candidate or candidate.lower() == "none":
        return ""

    if os.path.isabs(candidate):
        path = os.path.abspath(os.path.normpath(candidate))
        return path if os.path.exists(path) else ""

    current_directory_path = os.path.abspath(
        os.path.normpath(candidate)
    )
    if os.path.exists(current_directory_path):
        return current_directory_path

    input_root_path = os.path.abspath(
        os.path.join(
            INPUT_ROOT,
            candidate,
        )
    )
    if os.path.exists(input_root_path):
        return input_root_path

    for root, _, files in os.walk(INPUT_ROOT):
        if os.path.basename(candidate) in files:
            return os.path.abspath(
                os.path.join(
                    root,
                    os.path.basename(candidate),
                )
            )

    return ""


# =========================================================
# JSON Value Helpers
# =========================================================

def json_safe_value(
    value,
):
    """
    Convert Excel/Python values into values that can safely
    be stored in JSON.
    """

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:

        return value

    return str(value)


def normalize_json_value(
    value,
):
    """
    Normalize values before comparing workbook data
    against JSON data.
    """

    if isinstance(
        value,
        datetime,
    ):
        return value.isoformat()

    return value


# =========================================================
# Build JSON
# =========================================================

def build_json_data_from_row(
    worksheet,
    row_number,
    headers,
    header_columns,
    sheet_name,
    invoice_prices,
):
    """
    Build JSON in the same format as manually captured
    tool JSON.
    """

    excluded_headers = {
        "File Path to JSON",
        "Sold",
        "Est. Value",
        "Est. Value Fraction",
        "Est. Purchase Price",
        "Inventory Found",
        "Profit",
    }

    data = {}

    # -----------------------------------------------------
    # Preserve workbook/header order.
    # -----------------------------------------------------

    for header in headers:

        if header in excluded_headers:
            continue

        if header not in header_columns:
            continue

        column = header_columns[
            header
        ]

        cell = worksheet.cell(
            row=row_number,
            column=column,
        )

        value = cell.value

        if header == "File Path to Image":
            target_value = get_cell_path_value(cell)
            if target_value:
                resolved_target = resolve_existing_image_path(
                    target_value
                )
                value = resolved_target or target_value
            else:
                value = ""

        if header == "Invoice #":

            data["Invoice"] = json_safe_value(
                value
            )

        else:

            data[header] = json_safe_value(
                value
            )

    # -----------------------------------------------------
    # Normalize missing image path.
    # -----------------------------------------------------

    image_path = data.get(
        "File Path to Image"
    )

    if image_path is None or not str(image_path).strip():
        data["File Path to Image"] = "None"
    else:
        resolved_image_path = resolve_existing_image_path(
            image_path
        )
        if resolved_image_path:
            data["File Path to Image"] = resolved_image_path
        else:
            data["File Path to Image"] = str(image_path).strip()

    # -----------------------------------------------------
    # Purchase JSON.
    # -----------------------------------------------------

    if sheet_name == "Purchases":

        data["Inventory Type"] = "Purchases"

        ebay_id = normalize_invoice(
            data.get("eBay ID")
        )

        if (
            ebay_id
            and ebay_id in invoice_prices
        ):

            data["Invoice Price"] = (
                json_safe_value(
                    invoice_prices[
                        ebay_id
                    ]
                )
            )

    # -----------------------------------------------------
    # Sale JSON.
    # -----------------------------------------------------

    elif sheet_name == "Sales":

        data["Inventory Type"] = "Sales"

        if "Invoice Price" not in data:

            invoice_price_column = (
                header_columns.get(
                    "Invoice Price"
                )
            )

            if invoice_price_column is not None:

                invoice_price = worksheet.cell(
                    row=row_number,
                    column=invoice_price_column,
                ).value

                data["Invoice Price"] = (
                    json_safe_value(
                        invoice_price
                    )
                )

    return data


# =========================================================
# Compare JSON
# =========================================================

def json_data_changed(
    existing_data,
    workbook_data,
):
    """
    Return True when workbook information differs from JSON.

    File Path to JSON is intentionally ignored because the
    workbook may contain a relative filename while JSON
    contains an absolute path.
    """

    all_keys = (
        set(existing_data)
        | set(workbook_data)
    )

    for key in all_keys:

        if key == "File Path to JSON":
            continue

        existing_value = normalize_json_value(
            existing_data.get(key)
        )

        workbook_value = normalize_json_value(
            workbook_data.get(key)
        )

        if existing_value != workbook_value:
            return True

    return False


# =========================================================
# Create New JSON Path
# =========================================================

def create_new_json_path(
    sheet_name,
    row_number,
    worksheet,
    header_columns,
):
    # -----------------------------------------------------
    # Determine Purchase / Sale folder.
    # -----------------------------------------------------

    if sheet_name == "Purchases":
        sheet_folder = "Purchases"

    else:
        sheet_folder = "Sales"

    # -----------------------------------------------------
    # Get invoice title.
    # -----------------------------------------------------

    invoice_title_column = (
        header_columns.get("Invoice")
        or header_columns.get("Invoice #")
        or header_columns.get("Invoice Name")
    )

    if invoice_title_column is None:

        raise ValueError(
            f"Could not find invoice title column "
            f"in {sheet_name}."
        )

    invoice_title = worksheet.cell(
        row=row_number,
        column=invoice_title_column,
    ).value

    if (
        invoice_title is None
        or not str(invoice_title).strip()
    ):

        raise ValueError(
            f"Row {row_number} has no invoice title."
        )

    invoice_title = str(
        invoice_title
    ).strip()

    # -----------------------------------------------------
    # Make invoice title safe for folder/filename use.
    # -----------------------------------------------------

    invalid_characters = '<>:"/\\|?*'

    safe_invoice_title = "".join(
        "_"
        if character in invalid_characters
        else character
        for character in invoice_title
    ).strip()

    if not safe_invoice_title:

        raise ValueError(
            "Invoice title cannot be used as a folder "
            f"name: {invoice_title!r}"
        )

    # -----------------------------------------------------
    # Build invoice folder.
    # -----------------------------------------------------

    invoice_folder = os.path.join(
        INPUT_ROOT,
        OUTPUT_DIR_LOG_NAME,
        sheet_folder,
        safe_invoice_title,
    )

    os.makedirs(
        invoice_folder,
        exist_ok=True,
    )

    # -----------------------------------------------------
    # Find next object number.
    # -----------------------------------------------------

    existing_numbers = []

    filename_prefix = (
        f"{safe_invoice_title}_"
    )

    filename_suffix = (
        "_Logged.json"
    )

    for filename in os.listdir(
        invoice_folder
    ):

        if not filename.startswith(
            filename_prefix
        ):
            continue

        if not filename.endswith(
            filename_suffix
        ):
            continue

        number_part = filename[
            len(filename_prefix):
            -len(filename_suffix)
        ]

        if number_part.isdigit():

            existing_numbers.append(
                int(number_part)
            )

    next_number = (
        max(
            existing_numbers,
            default=0,
        )
        + 1
    )

    filename = (
        f"{safe_invoice_title}_"
        f"{next_number:03d}_Logged.json"
    )

    return os.path.abspath(
        os.path.join(
            invoice_folder,
            filename,
        )
    )


# =========================================================
# Sync JSON From Workbook
# =========================================================

def sync_json_from_workbook():

    workbook_path = get_workbook_path()

    if not os.path.exists(
        workbook_path
    ):

        raise FileNotFoundError(
            f"Workbook does not exist: "
            f"{workbook_path}"
        )

    workbook = load_workbook(
        workbook_path,
        data_only=False,
    )

    updated_count = 0
    created_count = 0
    skipped_count = 0

    sheets = (
        (
            "Purchases",
            PURCHASE_HEADERS,
        ),
        (
            "Sales",
            SALE_HEADERS,
        ),
    )

    try:

        for sheet_name, headers in sheets:

            if sheet_name not in workbook.sheetnames:
                continue

            worksheet = workbook[
                sheet_name
            ]

            header_columns = {
                cell.value: cell.column
                for cell in worksheet[1]
                if cell.value is not None
            }

            # -------------------------------------------------
            # Build invoice-price lookup for Purchases.
            # -------------------------------------------------

            invoice_prices = {}

            if sheet_name == "Purchases":

                invoice_prices = (
                    load_invoice_prices(
                        worksheet
                    )
                )

            json_column = header_columns.get(
                "File Path to JSON"
            )

            if json_column is None:
                continue

            # -------------------------------------------------
            # Process workbook rows.
            # -------------------------------------------------

            for row_number, row_values in enumerate(
                worksheet.iter_rows(
                    min_row=2,
                    values_only=True,
                ),
                start=2,
            ):

                # -------------------------------------------------
                # Skip empty rows.
                # -------------------------------------------------

                if not any(
                    value is not None
                    and str(value).strip()
                    for value in row_values
                ):
                    continue

                # -------------------------------------------------
                # Skip generated summary rows.
                # -------------------------------------------------

                summary_found = any(
                    isinstance(
                        value,
                        str,
                    )
                    and (
                        value.strip() in {
                            "Total Sales:",
                            "Total Purchases:",
                            "Invoice Est. Sum",
                            "Sales:",
                            "Profit:",
                            "Total Profit:",
                        }
                        or value.strip().startswith(
                            (
                                "Total Sales:",
                                "Total Purchases:",
                                "Invoice Est. Sum",
                                "Sales:",
                                "Profit:",
                                "Total Profit:",
                            )
                        )
                    )
                    for value in row_values
                )

                if summary_found:
                    continue

                # -------------------------------------------------
                # Get stored JSON path.
                # -------------------------------------------------

                json_cell = worksheet.cell(
                    row=row_number,
                    column=json_column,
                )

                stored_json_path = (
                    get_json_path_from_cell(
                        json_cell
                    )
                )

                if not stored_json_path and json_column <= len(row_values):
                    json_cell_value = row_values[
                        json_column - 1
                    ]

                    if json_cell_value is not None:
                        stored_json_path = str(
                            json_cell_value
                        ).strip()

                # -------------------------------------------------
                # Resolve existing JSON.
                #
                # This now:
                #
                # 1. Checks the stored absolute path.
                # 2. Checks relative paths.
                # 3. Checks INPUT_ROOT.
                # 4. Searches INPUT_ROOT by filename.
                # -------------------------------------------------

                json_path = (
                    resolve_existing_json_path(
                        stored_json_path
                    )
                )

                # -------------------------------------------------
                # JSON path cannot be resolved.
                #
                # Create a new one only after all existing-path
                # checks fail.
                # -------------------------------------------------

                if not json_path:

                    json_path = (
                        create_new_json_path(
                            sheet_name,
                            row_number,
                            worksheet,
                            header_columns,
                        )
                    )

                    print(
                        "JSON missing. "
                        f"Saving new JSON to: {json_path}"
                    )

                else:

                    print(
                        f"JSON found: {json_path}"
                    )

                # -------------------------------------------------
                # Build workbook JSON data.
                # -------------------------------------------------

                workbook_data = (
                    build_json_data_from_row(
                        worksheet=worksheet,
                        row_number=row_number,
                        headers=headers,
                        header_columns=header_columns,
                        sheet_name=sheet_name,
                        invoice_prices=invoice_prices,
                    )
                )

                # -------------------------------------------------
                # Do not use the workbook's potentially stale
                # path as JSON data. Store the actual resolved
                # path.
                # -------------------------------------------------

                workbook_data[
                    "File Path to JSON"
                ] = json_path

                # -------------------------------------------------
                # JSON DOES NOT EXIST.
                # -------------------------------------------------

                if not os.path.isfile(
                    json_path
                ):

                    json_directory = (
                        os.path.dirname(
                            json_path
                        )
                    )

                    if json_directory:

                        os.makedirs(
                            json_directory,
                            exist_ok=True,
                        )

                    try:

                        with open(
                            json_path,
                            "w",
                            encoding="utf-8",
                        ) as file:

                            json.dump(
                                workbook_data,
                                file,
                                indent=4,
                                ensure_ascii=False,
                            )

                        created_count += 1

                        print(
                            f"JSON created: "
                            f"{json_path}"
                        )

                    except (
                        OSError,
                        TypeError,
                    ) as error:

                        print(
                            "Failed to create JSON: "
                            f"{json_path}"
                        )

                        print(
                            f"  {error}"
                        )

                        skipped_count += 1

                        continue

                # -------------------------------------------------
                # JSON EXISTS.
                # -------------------------------------------------

                else:

                    print(
                        f"Comparing JSON: "
                        f"{json_path}"
                    )

                    try:

                        with open(
                            json_path,
                            "r",
                            encoding="utf-8",
                        ) as file:

                            existing_data = json.load(
                                file
                            )

                    except (
                        OSError,
                        json.JSONDecodeError,
                    ) as error:

                        print(
                            "Failed to read JSON: "
                            f"{json_path}"
                        )

                        print(
                            f"  {error}"
                        )

                        skipped_count += 1

                        continue

                    if not isinstance(
                        existing_data,
                        dict,
                    ):

                        print(
                            "Invalid JSON structure: "
                            f"{json_path}"
                        )

                        skipped_count += 1

                        continue

                    # -------------------------------------------------
                    # Compare workbook data to JSON.
                    # -------------------------------------------------

                    changed = (
                        json_data_changed(
                            existing_data,
                            workbook_data,
                        )
                    )

                    if changed:

                        try:

                            with open(
                                json_path,
                                "w",
                                encoding="utf-8",
                            ) as file:

                                json.dump(
                                    workbook_data,
                                    file,
                                    indent=4,
                                    ensure_ascii=False,
                                )

                            updated_count += 1

                            print(
                                f"JSON updated: "
                                f"{json_path}"
                            )

                        except (
                            OSError,
                            TypeError,
                        ) as error:

                            print(
                                "Failed to update JSON: "
                                f"{json_path}"
                            )

                            print(
                                f"  {error}"
                            )

                            skipped_count += 1

                            continue

                    else:

                        print(
                            f"JSON unchanged: "
                            f"{json_path}"
                        )

                # -------------------------------------------------
                # Always repair the Excel JSON reference.
                #
                # Display only the filename, while the hyperlink
                # contains the actual absolute path.
                # -------------------------------------------------

                json_cell.value = (
                    os.path.basename(
                        json_path
                    )
                )

                json_cell.hyperlink = (
                    os.path.abspath(
                        json_path
                    )
                )

                json_cell.style = "Hyperlink"

        # -----------------------------------------------------
        # Save workbook.
        # -----------------------------------------------------

        workbook.save(
            workbook_path
        )

    finally:

        workbook.close()

    print(
        "JSON sync complete. "
        f"Created: {created_count}, "
        f"Updated: {updated_count}, "
        f"Skipped: {skipped_count}"
    )