import json
import os
from datetime import datetime

from openpyxl import load_workbook

from tool_logger.tool_logger_extraction import extract_tool_info

from tool_logger.tool_logger_config import (
    LOG_ROOT,
)

from .calculations import (
    normalize_invoice,
)

from .workbook import (
    ensure_workbook,
    rebuild_workbook,
    get_workbook_path,
)

from .rows import (
    purchase_row,
    sale_row,
)

# ------------------------------------------------
# COMPLETE REBUILD
# ------------------------------------------------

def rebuild_workbook_from_json():
    from tool_logger.tool_logger_config import INPUT_ROOT

    purchases = []
    sales = []

    print(
        "================================"
    )

    print(
        "FULL SPREADSHEET REBUILD"
    )

    print(
        "================================"
    )

    # ------------------------------------------------
    # Read JSON files
    # ------------------------------------------------

    for root, _, files in os.walk(
        INPUT_ROOT
    ):
        for filename in sorted(files):

            if not (
                filename.endswith("_Logged.json")
                or filename.endswith("_Unlogged.json")
            ):
                continue

            json_path = os.path.join(
                root,
                filename,
            )

            if filename.endswith("_Unlogged.json"):
                logged_path = json_path.replace(
                    "_Unlogged.json",
                    "_Logged.json",
                )

                os.replace(
                    json_path,
                    logged_path,
                )

                print(
                    f"Renamed: {json_path} -> {logged_path}"
                )

                json_path = logged_path

            print(
                f"Reading: {json_path}"
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

                continue

            if not isinstance(
                data,
                dict,
            ):

                print(
                    "  Invalid JSON structure."
                )

                continue

            row = extract_tool_info(
                data,
            )

            if row is None:

                print(
                    "  Could not determine "
                    "tool information."
                )

                continue

            inventory_type = str(
                row.get(
                    "Inventory Type",
                    "Purchases",
                )
            ).strip().casefold()

            if inventory_type == "sales":
                sales.append(row)

            else:
                purchases.append(row)

    print()
    print(
        f"JSON purchases found: "
        f"{len(purchases)}"
    )

    print(
        f"JSON sales found: "
        f"{len(sales)}"
    )

    invoice_prices = {}

    for purchase in purchases:

        invoice = normalize_invoice(
            purchase.get(
                "eBay ID"
            )
        )

        if not invoice:
            continue

        if invoice in invoice_prices:
            continue

        try:
            invoice_prices[invoice] = float(
                purchase.get(
                    "Invoice Price",
                    0.0,
                )
                or 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            invoice_prices[invoice] = 0.0

    # ------------------------------------------------
    # Create a completely fresh workbook
    # ------------------------------------------------

    workbook_path = get_workbook_path()

    if os.path.exists(
        workbook_path
    ):

        base_name = (
            "OLD_Tool_Log_"
            + datetime.now().strftime(
                "%Y%m%d"
            )
        )

        counter = 1

        old_workbook_path = os.path.join(
            LOG_ROOT,
            base_name + ".xlsx",
        )

        while os.path.exists(
            old_workbook_path
        ):

            old_workbook_path = os.path.join(
                LOG_ROOT,
                f"{base_name}_{counter}.xlsx",
            )

            counter += 1

        print()
        print(
            "Moving existing workbook to:"
        )

        print(
            old_workbook_path
        )

        os.rename(
            workbook_path,
            old_workbook_path,
        )

    # ------------------------------------------------
    # Create fresh workbook
    # ------------------------------------------------

    ensure_workbook()

    workbook = load_workbook(
        workbook_path
    )

    purchases_sheet = workbook[
        "Purchases"
    ]

    sales_sheet = workbook[
        "Sales"
    ]

    # ------------------------------------------------
    # Write raw JSON data
    #
    # This intentionally goes through the same
    # purchase_row() / sale_row() functions used
    # by the normal logging process.
    # ------------------------------------------------

    for row in purchases:

        purchases_sheet.append(
            purchase_row(row)
        )

    for row in sales:

        sales_sheet.append(
            sale_row(row)
        )

    workbook.save(
        workbook_path
    )

    workbook.close()

    print()
    print(
        "Raw JSON data written to fresh "
        "workbook."
    )

    # ------------------------------------------------
    # Rebuild using the EXACT SAME processing
    # pipeline as the normal workbook rebuild.
    # ------------------------------------------------

    print()
    print(
        "Running standard workbook rebuild..."
    )

    rebuild_workbook(
        invoice_prices
    )

    print()
    print(
        "================================"
    )

    print(
        "FULL REBUILD COMPLETE"
    )

    print(
        "================================"
    )

    return workbook_path