import json
import os
from datetime import datetime

import json
import os
from datetime import datetime

from openpyxl import Workbook, load_workbook

from tool_logger.tool_logger_extraction import extract_tool_info

from tool_logger.tool_logger_config import (
    PURCHASE_HEADERS,
    SALE_HEADERS,
    INVENTORY_HEADERS,
    SIMPLIFIED_INVENTORY_HEADERS,
    OVERVIEW_HEADERS,
    LOG_ROOT,
    INPUT_ROOT,
)

from settings_menu.inventory_settings import (
    InventorySettings,
)

from .formatting import (
    format_header,
    format_sold_rows,
    format_overview_sheet,
    format_simplified_inventory_sheet,
    format_image_hyperlinks,
    format_json_hyperlinks,
    format_invoice_total_rows,
    format_purchases_sheet,
    format_sale_profit_total_rows,
    format_sales_sheet,
    format_inventory_sheet,
    format_inventory_total_rows,
)


# ==================================================
# Workbook Configuration
# ==================================================

OUTPUT_DIR_LOG_NAME = "Converted_Tool_Logs"

SALE_INVOICE_PREFIX = "SALE"

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

# ==================================================
# Create Workbook If Needed
# ==================================================

def ensure_workbook():

    workbook_path = get_workbook_path()

    if os.path.exists(workbook_path):
        workbook = load_workbook(workbook_path)

        if "Simplified Inventory" not in workbook.sheetnames:
            simplified_inventory = workbook.create_sheet(
                "Simplified Inventory"
            )

            simplified_inventory.append(
                SIMPLIFIED_INVENTORY_HEADERS
            )

            format_header(
                simplified_inventory
            )

        if "Overview" not in workbook.sheetnames:
            overview = workbook.create_sheet(
                "Overview"
            )

            overview.append(
                OVERVIEW_HEADERS
            )

            format_header(
                overview
            )

        workbook.save(
            workbook_path
        )

        workbook.close()

        return workbook_path

    workbook = Workbook()

    purchases = workbook.active
    purchases.title = "Purchases"

    sales = workbook.create_sheet("Sales")
    inventory = workbook.create_sheet("Remaining Inventory")

    simplified_inventory = workbook.create_sheet(
        "Simplified Inventory"
    )

    overview = workbook.create_sheet(
        "Overview"
    )

    purchases.append(
        PURCHASE_HEADERS
    )

    sales.append(
        SALE_HEADERS
    )

    inventory.append(
        INVENTORY_HEADERS
    )

    simplified_inventory.append(
        SIMPLIFIED_INVENTORY_HEADERS
    )

    overview.append(
        OVERVIEW_HEADERS
    )

    for worksheet in (
        purchases,
        sales,
        inventory,
        simplified_inventory,
        overview,
    ):
        format_header(
            worksheet
        )

    workbook.save(
        workbook_path
    )

    workbook.close()

    return workbook_path


# ==================================================
# Read Sheet
# ==================================================

def load_sheet_rows(
    worksheet,
    headers,
):
    rows = []

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):
        values = []

        for column in range(
            1,
            len(headers) + 1,
        ):
            cell = worksheet.cell(
                row=row_number,
                column=column,
            )

            header = headers[column - 1]

            if header in {
                "File Path to JSON",
                "File Path to Image",
            } and cell.hyperlink:
                target = cell.hyperlink.target

                values.append(
                    str(target).strip()
                    if target
                    else cell.value
                )

            else:
                values.append(cell.value)

        if not any(
            value is not None
            and str(value).strip()
            for value in values
        ):
            continue

        # Skip generated summary rows.
        if (
            "Invoice Est. Sum" in values
            or "Sales:" in values
            or "Total Sales:" in values
            or "Profit:" in values
            or "Total Profit" in values
        ):
            continue

        row_data = {}

        for index, header in enumerate(headers):
            row_data[header] = values[index]

        rows.append(row_data)

    return rows


# ==================================================
# Matching Fields
# ==================================================

def tool_matches(
    purchase,
    sale,
):

    fields = (
        "Tool Name",
        "Part Number",
        "Size-1",
        "Size-2",
        "Brand",
        "Measurement",
        "Drive",
        "Point",
    )

    for field in fields:

        purchase_value = str(
            purchase.get(
                field,
                "",
            )
        ).strip().casefold()

        sale_value = str(
            sale.get(
                field,
                "",
            )
        ).strip().casefold()

        if purchase_value != sale_value:
            return False

    return True


# ==================================================
# Calculate Remaining Inventory
# ==================================================

def calculate_remaining_inventory(
    purchases,
    sales,
):

    remaining = []

    for purchase in purchases:
        purchase["Sold"] = "NO"

    for sale in sales:

        for purchase in purchases:

            if purchase.get("Sold") == "YES":
                continue

            if tool_matches(
                purchase,
                sale,
            ):
                purchase["Sold"] = "YES"
                break

    for purchase in purchases:

        if purchase.get("Sold") != "YES":
            remaining.append(
                purchase
            )

    return remaining


# ==================================================
# Sort Rows
# ==================================================

def sort_rows(
    rows,
):

    return sorted(
        rows,
        key=lambda row: (
            str(
                row.get(
                    "Tool Name",
                    "",
                )
            ).casefold(),

            str(
                row.get(
                    "Size-1",
                    "",
                )
            ).casefold(),

            str(
                row.get(
                    "Size-2",
                    "",
                )
            ).casefold(),

            str(
                row.get(
                    "Date",
                    "",
                )
            ),

            str(
                row.get(
                    "File Path to Image",
                    "",
                )
            ),
            str(
                row.get(
                    "File Path to JSON",
                    "",
                )

            ).casefold(),
        ),
    )

def sort_sale_rows(
    sales,
):

    return sorted(
        sales,
        key=lambda row: (
            normalize_invoice(
                row.get(
                    "Invoice #"
                )
            ),

            str(
                row.get(
                    "Tool Name",
                    "",
                )
            ).strip().casefold(),

            str(
                row.get(
                    "Brand",
                    "",
                )
            ).strip().casefold(),
        ),
    )

def normalize_invoice(
    value,
):

    if value is None:
        return ""

    return str(
        value
    ).strip().casefold()


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

        # Generated invoice summary row:
        # L = Invoice Est. Sum
        # M = Estimated total
        # N = Invoice Price
        # O = Actual invoice price
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

# ==================================================
# Convert Purchase Row
# ==================================================

def purchase_row(
    row,
    value_fraction_formula=None,
    purchase_price_formula=None,
):
    return [
        row.get("Date"),
        row.get("Invoice #"),
        row.get("eBay ID"),
        row.get("Brand"),
        row.get("Part Number"),
        row.get("Tool Name"),
        row.get("Size-1"),
        row.get("Size-2"),
        row.get("Drive"),
        row.get("Measurement"),
        row.get("Point"),
        row.get("Specialty Socket"),
        row.get("Est. Value"),
        value_fraction_formula,
        purchase_price_formula,
        row.get("Sold", "NO"),
        row.get("File Path to Image"),
        row.get("File Path to JSON"),
    ]

def build_purchase_display_rows(
    purchases,
    invoice_prices,
):

    display_rows = []

    current_invoice = None
    current_ebay_id = None
    invoice_total = 0.0
    invoice_price = 0.0
    excel_row = 2

    for purchase in purchases:

        ebay_id = normalize_invoice(purchase.get("eBay ID"))
        invoice = normalize_invoice(purchase.get("Invoice #"))

        # --------------------------------------------
        # New invoice group
        # --------------------------------------------

        if (
            current_invoice is not None
            and invoice != current_invoice
        ):

            display_rows.append(
                [
                    "",
                    "Username:",
                    current_ebay_id,
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Invoice Est. Sum",
                    invoice_total,
                    "Invoice Price",
                    invoice_price,
                    "",
                    "",
                ]
            )

            display_rows.append(
                [None] * len(PURCHASE_HEADERS)
            )
            excel_row += 2
            invoice_total = 0.0
            invoice_price = 0.0

        current_ebay_id = ebay_id
        current_invoice = invoice

        # --------------------------------------------
        # Get invoice price from invoice_prices
        # --------------------------------------------

        invoice_price = invoice_prices.get(
            current_ebay_id,
            0.0,
        )

        # --------------------------------------------
        # Purchase row
        # --------------------------------------------

        purchase_excel_row = excel_row

        value_fraction_formula = (
            f'=M{purchase_excel_row}/'
            f'SUMIFS(M:M,C:C,C{purchase_excel_row},L:L,"<>Invoice Est. Sum")'
        )

        purchase_price_formula = (
            f'=(M{purchase_excel_row}/'
            f'SUMIFS(M:M,C:C,C{purchase_excel_row},L:L,"<>Invoice Est. Sum"))*'
            f'SUMIFS(O:O,C:C,C{purchase_excel_row},L:L,"Invoice Est. Sum")'
        )

        display_rows.append(
            purchase_row(
                purchase,
                value_fraction_formula=(
                    value_fraction_formula
                ),
                purchase_price_formula=(
                    purchase_price_formula
                ),
            )
        )

        excel_row += 1

        invoice_total += (
            purchase.get(
                "Est. Value",
                5.00,
            )
            or 0.0
        )

    # --------------------------------------------
    # Final invoice total
    # --------------------------------------------

    if current_ebay_id is not None:

        display_rows.append(
            [
                "",
                "Username:",
                current_ebay_id,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "Invoice Est. Sum",
                invoice_total,
                "Invoice Price",
                invoice_price,
                "",
                "",
            ]
        )

    return display_rows

def build_inventory_display_rows(
    inventory,
):

    display_rows = []

    current_tool_name = None
    group_total = 0.0
    inventory_total = 0.0

    # ------------------------------------------------
    # Sort by Tool Name, then Brand
    # ------------------------------------------------

    inventory = sorted(
        inventory,
        key=lambda row: (
            # Group by Tool Name
            str(
                row.get(
                    "Tool Name",
                    "",
                )
            ).strip().casefold(),

            # Then Brand
            str(
                row.get(
                    "Brand",
                    "",
                )
            ).strip().casefold(),

            # Then Measurement
            str(
                row.get(
                    "Measurement",
                    "",
                )
            ).strip().casefold(),

            # Then Size-1
            str(
                row.get(
                    "Size-1",
                    "",
                )
            ).strip().casefold(),
        ),
    )

    # ------------------------------------------------
    # Build grouped rows
    # ------------------------------------------------

    for row in inventory:

        tool_name = str(
            row.get(
                "Tool Name",
                "",
            )
        ).strip().casefold()

        # --------------------------------------------
        # New Tool Name group
        # --------------------------------------------

        if (
            current_tool_name is not None
            and tool_name != current_tool_name
        ):

            display_rows.append(
                [
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Est. Profit Sum",
                    group_total,
                    "",
                ]
            )

            # Empty row below total
            display_rows.append(
                [None] * len(INVENTORY_HEADERS)
            )

            group_total = 0.0

        current_tool_name = tool_name

        # --------------------------------------------
        # Inventory row
        # --------------------------------------------

        display_rows.append(
            inventory_row(row)
        )

        try:
            estimated_value = float(
                row.get(
                    "Est. Value",
                    0.0,
                )
                or 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            estimated_value = 0.0

        group_total += estimated_value
        inventory_total += estimated_value

    # ------------------------------------------------
    # Final Tool Name group total
    # ------------------------------------------------

    if current_tool_name is not None:

        display_rows.append(
            [
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "Est. Profit Sum",
                group_total,
                "",
            ]
        )

        # Empty row below final group total
        display_rows.append(
            [None] * len(INVENTORY_HEADERS)
        )

    # ------------------------------------------------
    # Entire Inventory Total
    # ------------------------------------------------

    display_rows.append(
        [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "Est. Inventory Sum",
            inventory_total,
            "",
        ]
    )

    return display_rows

# ==================================================
# Build Simplified Inventory
# ==================================================

def build_simplified_inventory_rows(
    inventory,
):
    grouped = {}

    for row in inventory:
        tool_name = str(
            row.get(
                "Tool Name",
                "",
            )
        ).strip()

        brand = str(
            row.get(
                "Brand",
                "",
            )
        ).strip()

        if not tool_name:
            continue

        if not brand:
            brand = "Unknown"

        tool_key = tool_name.casefold()
        brand_key = brand.casefold()

        if tool_key not in grouped:
            grouped[tool_key] = {
                "Tool": tool_name,
                "Brands": {},
            }

        if brand_key not in grouped[tool_key]["Brands"]:
            grouped[tool_key]["Brands"][brand_key] = {
                "Brand": brand,
            }

    display_rows = []

    # Row 1 is the header.
    excel_row = 2

    for tool_key in sorted(grouped):
        tool_group = grouped[tool_key]

        # ------------------------------------------------
        # Tool name row
        # ------------------------------------------------

        display_rows.append([
            tool_group["Tool"],
            "",
            "",
        ])

        tool_row = excel_row
        excel_row += 1

        # ------------------------------------------------
        # Brand rows
        # ------------------------------------------------

        for brand_key in sorted(
            tool_group["Brands"]
        ):
            brand_data = tool_group["Brands"][brand_key]

            display_rows.append([
                "",
                brand_data["Brand"],
                (
                    f"=COUNTIFS("
                    f"'Remaining Inventory'!$D:$D,"
                    f"A{tool_row},"
                    f"'Remaining Inventory'!$B:$B,"
                    f"B{excel_row}"
                    f")"
                ),
            ])

            excel_row += 1

        # ------------------------------------------------
        # Empty row between tool groups
        # ------------------------------------------------

        display_rows.append([
            None,
            None,
            None,
        ])

        excel_row += 1

    return display_rows


# ==================================================
# Build Overview
# ==================================================

def build_overview_rows(purchases):

    seen_ebay_ids = set()
    unique_purchases = []

    for purchase in purchases:

        ebay_id = str(
            purchase.get(
                "eBay ID",
                "",
            )
        ).strip()

        if not ebay_id or ebay_id in seen_ebay_ids:
            continue

        seen_ebay_ids.add(ebay_id)
        unique_purchases.append(purchase)

    rows = []

    # ------------------------------------------------
    # Main Overview rows
    # ------------------------------------------------

    for purchase in unique_purchases:

        overview_row = len(rows) + 2

        purchase_invoice = str(
            purchase.get(
                "Invoice #",
                "",
            )
        ).strip().upper()

        if "EB" in purchase_invoice:
            platform = "Ebay"

        elif "FB" in purchase_invoice:
            platform = "Facebook"

        elif "WN" in purchase_invoice:
            platform = "Whatnot"

        else:
            platform = ""

        rows.append([
            f'=INDEX(Purchases!$A:$A,'
            f'MATCH(D{overview_row},'
            f'Purchases!$C:$C,0))',

            f'=INDEX(Purchases!$B:$B,'
            f'MATCH(D{overview_row},'
            f'Purchases!$C:$C,0))',

            platform,

            purchase.get(
                "eBay ID",
                "",
            ),

            f'=COUNTIFS('
            f'Purchases!$C:$C,'
            f'D{overview_row},'
            f'Purchases!$L:$L,'
            f'"<>Invoice Est. Sum"'
            f')',

            f'=SUMIFS('
            f'Purchases!$O:$O,'
            f'Purchases!$C:$C,'
            f'D{overview_row},'
            f'Purchases!$L:$L,'
            f'"<>Invoice Est. Sum"'
            f')',

            "",
            "",
            "",
            "",
            "",
        ])

    # ------------------------------------------------
    # Make sure rows 2-8 exist for the summary.
    # ------------------------------------------------

    while len(rows) < 7:
        rows.append([""] * 11)

    purchase_end_row = max(
        2,
        len(unique_purchases) + 1,
    )

    # ------------------------------------------------
    # Purchase Information
    #
    # H2:I2 = section header
    # H3:I3 = labels
    # H4:I4 = values
    # ------------------------------------------------

    rows[0][7] = "PURCHASE INFORMATION"

    rows[1][7] = "Total Purchase Item Count"
    rows[1][8] = "Total Spent"

    rows[2][7] = f'=SUM(E2:E{purchase_end_row})'
    rows[2][8] = f'=SUM(F2:F{purchase_end_row})'

    # ------------------------------------------------
    # Sales Information
    #
    # H6:K6 = section header
    # H7:K7 = labels
    # H8:K8 = values
    # ------------------------------------------------

    rows[4][7] = "SALES INFORMATION"

    rows[5][7] = "Total Items Sold"
    rows[5][8] = "Total Sales"
    rows[5][9] = "Sales Profit"
    rows[5][10] = "Net Profit"

    rows[6][7] = (
        '=COUNTIFS('
        'Sales!$A:$A,"<>",'
        'Sales!$M:$M,">=0"'
        ')'
    )

    rows[6][8] = (
        '=SUMIFS('
        'Sales!$M:$M,'
        'Sales!$A:$A,"<>",'
        'Sales!$M:$M,">=0"'
        ')'
    )

    rows[6][9] = (
        '=SUMIFS('
        'Sales!$O:$O,'
        'Sales!$A:$A,"<>"'
        ')'
    )

    rows[6][10] = "=I8-I4"

    return rows



def purchase_sort_key(row):
    invoice = str(
        row.get("Invoice #", "")
    ).strip().casefold()

    ebay_id = str(
        row.get("eBay ID", "")
    ).strip().casefold()

    date_value = str(
        row.get(
            "Date",
            "",
        )
    )

    tool_name = str(
        row.get("Tool Name", "")
    ).strip().casefold()

    return (
        invoice == "",
        invoice,
        date_value,
        ebay_id,
        tool_name,
    )


# ==================================================
# Convert Sale Row
# ==================================================

def sale_row(
    row,
    profit_formula=None,
):
    try:
        invoice_price = float(
            row.get(
                "Invoice Price",
                0.0,
            )
            or 0.0
        )
    except (
        TypeError,
        ValueError,
    ):
        invoice_price = 0.0

    return [
        row.get("Date"),
        row.get("Invoice #"),
        row.get("eBay ID"),
        row.get("Brand"),
        row.get("Part Number"),
        row.get("Tool Name"),
        row.get("Size-1"),
        row.get("Size-2"),
        row.get("Drive"),
        row.get("Measurement"),
        row.get("Point"),
        row.get("Specialty Socket"),
        invoice_price,
        row.get("Inventory Found", "NO"),
        profit_formula,
        row.get("File Path to Image"),
        row.get("File Path to JSON"),
    ]

# ==================================================
# Convert Inventory Row
# ==================================================

def inventory_row(row):
    return [
        row.get("Date"),
        row.get("Brand"),
        row.get("Part Number"),
        row.get("Tool Name"),
        row.get("Size-1"),
        row.get("Size-2"),
        row.get("Drive"),
        row.get("Measurement"),
        row.get("Point"),
        row.get("Specialty Socket"),
        row.get("Est. Value"),
        row.get("File Path to Image"),
        row.get("File Path to JSON"),
    ]

# ==================================================
# Rebuild Sheet
# ==================================================

def rebuild_sheet(
    worksheet,
    headers,
    rows,
):

    worksheet.delete_rows(
        1,
        worksheet.max_row,
    )

    worksheet.append(headers)
    format_header(worksheet)

    for row in rows:
        worksheet.append(row)


def save_to_spreadsheet(
    row_data,
):

    workbook_path = ensure_workbook()

    workbook = load_workbook(
        workbook_path
    )

    inventory_type = row_data.get(
        "Inventory Type",
        "Purchases",
    )

    inventory_type = str(
        inventory_type
    ).strip().lower()

    if inventory_type == "sales":

        worksheet = workbook[
            "Sales"
        ]

        worksheet.append(
            sale_row(
                row_data
            )
        )

    else:

        worksheet = workbook[
            "Purchases"
        ]

        worksheet.append(
            purchase_row(
                row_data
            )
        )

    workbook.save(
        workbook_path
    )

    # ------------------------------------------------
    # Preserve all existing invoice prices.
    # ------------------------------------------------

    invoice_prices = load_invoice_prices(
        workbook[
            "Purchases"
        ]
    )

    if inventory_type != "sales":

        invoice = normalize_invoice(
            row_data.get(
                "eBay ID"
            )
        )

        if invoice:

            try:
                invoice_prices[invoice] = float(
                    row_data.get(
                        "Invoice Price",
                        invoice_prices.get(
                            invoice,
                            0.0,
                        ),
                    )
                    or 0.0
                )

            except (
                TypeError,
                ValueError,
            ):
                # If the new row does not contain a valid
                # invoice price, preserve the existing one.
                invoice_prices.setdefault(
                    invoice,
                    0.0,
                )


    # Recalculate Remaining Inventory
    rebuild_workbook(
        invoice_prices
    )

    workbook.close()

    return workbook_path

# ___________________________
# 
# ___________________________

def get_estimated_tool_value(
    tool_name,
    estimated_values,
):
    if not tool_name:
        return 5.00

    tool_name = str(
        tool_name
    ).strip()

    if not tool_name:
        return 5.00

    value = estimated_values.get(
        tool_name
    )

    if value is None:
        return 5.00

    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return 5.00


def build_purchase_excel_row_lookup(
    purchases,
):
    purchase_rows = {}

    current_ebay_id = None
    excel_row = 2

    for purchase in purchases:

        ebay_id = normalize_invoice(
            purchase.get(
                "eBay ID"
            )
        )

        # New invoice group does not add anything before
        # the first purchase, but every invoice change adds
        # a summary row and an empty row.
        if (
            current_ebay_id is not None
            and ebay_id != current_ebay_id
        ):
            excel_row += 2

        current_ebay_id = ebay_id

        json_path = purchase.get(
            "File Path to JSON"
        )

        if json_path:
            purchase_rows[
                str(json_path).strip()
            ] = excel_row

        excel_row += 1

    return purchase_rows

# ___________________________
# 
# ___________________________
def build_sale_display_rows(
    sales,
    purchase_excel_rows=None,
):

    display_rows = []

    current_tool_name = None

    if purchase_excel_rows is None:
        purchase_excel_rows = {}

    # Excel row tracking.
    #
    # Row 1 = headers, so the first sale will be row 2.
    excel_row = 2

    # Track the first and last actual sale row
    # for the current group.
    group_start_row = None
    group_last_row = None

    # Track all actual sale-row ranges for the
    # final ALL SALES formula.
    sale_ranges = []

    # ------------------------------------------------
    # Sort by Tool Name, Brand, then Size
    # ------------------------------------------------

    sales = sorted(
        sales,
        key=lambda row: (
            # Group by Tool Name
            str(
                row.get(
                    "Tool Name",
                    "",
                )
            ).strip().casefold(),

            # Then Brand
            str(
                row.get(
                    "Brand",
                    "",
                )
            ).strip().casefold(),

            # Then Size-1
            str(
                row.get(
                    "Size-1",
                    "",
                )
            ).strip().casefold(),

            # Then Size-2
            str(
                row.get(
                    "Size-2",
                    "",
                )
            ).strip().casefold(),
        ),
    )

    # ------------------------------------------------
    # Build grouped rows
    # ------------------------------------------------

    for sale in sales:

        tool_name = str(
            sale.get(
                "Tool Name",
                "",
            )
        ).strip().casefold()

        # --------------------------------------------
        # New Tool Name group
        # --------------------------------------------

        if (
            current_tool_name is not None
            and tool_name != current_tool_name
        ):

            # ----------------------------------------
            # Group total
            #
            # M = Invoice Price
            # N = Profit
            # ----------------------------------------

            display_rows.append(
                [
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "Sales:",
                    f"=SUM(M{group_start_row}:M{group_last_row})",
                    "Profit:",
                    f"=SUM(O{group_start_row}:O{group_last_row})",
                    "",
                    "",
                ]
            )

            excel_row += 1

            # Empty row below group total
            display_rows.append(
                [None] * len(SALE_HEADERS)
            )

            excel_row += 1

            # Reset group tracking.
            group_start_row = None
            group_last_row = None

        current_tool_name = tool_name

        # --------------------------------------------
        # Sale row
        # --------------------------------------------

        purchase_json = sale.get(
            "_Matched Purchase JSON"
        )

        purchase_excel_row = None

        if purchase_json:
            purchase_excel_row = purchase_excel_rows.get(
                str(purchase_json).strip()
            )

        sale_excel_row = excel_row

        if purchase_excel_row is not None:
            profit_formula = (
                f"=ROUND(M{sale_excel_row}"
                f"-Purchases!O{purchase_excel_row},2)"
            )
        else:
            profit_formula = (
                f"=ROUND(M{sale_excel_row},2)"
            )

        display_rows.append(
            sale_row(
                sale,
                profit_formula=profit_formula,
            )
        )

        # First sale row in this group.
        if group_start_row is None:
            group_start_row = excel_row

        # Last sale row in this group.
        group_last_row = excel_row

        # Save this actual sale range.
        sale_ranges.append(
            (
                excel_row,
                excel_row,
            )
        )

        excel_row += 1

    # ------------------------------------------------
    # Final Tool Name group total
    # ------------------------------------------------

    if current_tool_name is not None:

        display_rows.append(
            [
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "Sales:",
                f"=SUM(M{group_start_row}:M{group_last_row})",
                "Profit:",
                f"=SUM(O{group_start_row}:O{group_last_row})",
                "",
                "",
            ]
        )

        excel_row += 1

        # --------------------------------------------
        # Overall Sales Totals
        #
        # IMPORTANT:
        # We cannot use =SUM(M:M) because that would
        # include the group totals and double-count
        # them.
        # --------------------------------------------

        invoice_ranges = [
            f"M{start}:M{end}"
            for start, end in sale_ranges
        ]

        profit_ranges = [
            f"O{start}:O{end}"
            for start, end in sale_ranges
        ]

        invoice_formula = (
            f"=SUM({','.join(invoice_ranges)})"
        )

        profit_formula = (
            f"=SUM({','.join(profit_ranges)})"
        )

        display_rows.append(
            [
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "Total Sales:",
                invoice_formula,
                "Total Profit",
                profit_formula,
                "",
                "",
            ]
        )

        excel_row += 1

        # Empty row below overall total
        display_rows.append(
            [None] * len(SALE_HEADERS)
        )

    return display_rows

# ==================================================
# Calculate Sale Profits
# ==================================================

def calculate_sale_profits(
    purchases,
    sales,
):

    used_purchases = set()

    for sale in sales:

        sale["Inventory Found"] = "NO"

        # Used internally to connect this sale to the
        # exact purchase row after Purchases are sorted.
        sale["_Matched Purchase JSON"] = None

        for index, purchase in enumerate(purchases):

            if index in used_purchases:
                continue

            if not tool_matches(
                purchase,
                sale,
            ):
                continue

            sale["Inventory Found"] = "YES"

            sale["_Matched Purchase JSON"] = (
                purchase.get(
                    "File Path to JSON"
                )
            )

            used_purchases.add(index)

            break

    return sales

# ------------------------------------------------
# Calculate estimated value for each purchase
# ------------------------------------------------

def calculate_purchase_values(
    purchases,
    invoice_prices=None,
):
    inventory = InventorySettings.load_inventory()

    estimated_values = inventory.get(
        "estimated_values",
        {},
    )

    if invoice_prices is None:
        invoice_prices = {}

    # ------------------------------------------------
    # Calculate estimated value for each purchase
    # ------------------------------------------------

    for purchase in purchases:
        purchase["Est. Value"] = (
            get_estimated_tool_value(
                purchase.get("Tool Name"),
                estimated_values,
            )
        )

    return

def get_json_path_from_cell(
    cell,
):
    # The displayed cell value may only be the filename.
    # Use the hyperlink target when available so we recover
    # the original full filesystem path.
    if cell.hyperlink:
        target = cell.hyperlink.target

        if target:
            return str(
                target
            ).strip()

    if cell.value:
        return str(
            cell.value
        ).strip()

    return ""

def json_safe_value(value):
    """
    Convert Excel/Python values into values that can safely be
    stored in JSON and compared consistently later.
    """
    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def normalize_json_value(value):
    """
    Normalize values before comparing workbook data against JSON data.
    """
    if isinstance(value, datetime):
        return value.isoformat()

    return value


def build_json_data_from_row(
    worksheet,
    row_number,
    headers,
    header_columns,
    sheet_name,
    invoice_prices,
):
    """
    Build JSON in the same format as manually captured tool JSON.
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

    # Preserve the workbook/header order.
    for header in headers:

        if header in excluded_headers:
            continue

        if header not in header_columns:
            continue

        column = header_columns[header]

        value = worksheet.cell(
            row=row_number,
            column=column,
        ).value

        if header == "Invoice #":
            data["Invoice"] = json_safe_value(value)
        else:
            data[header] = json_safe_value(value)

    # ---------------------------------------------------------
    # Normalize missing image path.
    # ---------------------------------------------------------

    image_path = data.get("File Path to Image")

    if image_path is None or not str(image_path).strip():
        data["File Path to Image"] = "None"

    # ---------------------------------------------------------
    # Purchase JSON
    # ---------------------------------------------------------

    if sheet_name == "Purchases":

        data["Inventory Type"] = "Purchases"

        ebay_id = normalize_invoice(
            data.get("eBay ID")
        )

        if ebay_id and ebay_id in invoice_prices:
            data["Invoice Price"] = json_safe_value(
                invoice_prices[ebay_id]
            )

    # ---------------------------------------------------------
    # Sale JSON
    # ---------------------------------------------------------

    elif sheet_name == "Sales":

        data["Inventory Type"] = "Sales"

        # Make sure Invoice Price comes directly from
        # the sale row and is not accidentally omitted.
        if "Invoice Price" not in data:
            invoice_price_column = header_columns.get(
                "Invoice Price"
            )

            if invoice_price_column is not None:
                invoice_price = worksheet.cell(
                    row=row_number,
                    column=invoice_price_column,
                ).value

                data["Invoice Price"] = json_safe_value(
                    invoice_price
                )

    return data


def json_data_changed(
    existing_data,
    workbook_data,
):
    """
    Return True when the workbook contains information that differs
    from the JSON.
    """

    all_keys = set(existing_data) | set(workbook_data)

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


def create_new_json_path(
    sheet_name,
    row_number,
    worksheet,
    header_columns,
):
    # ---------------------------------------------------------
    # Determine Purchase / Sale folder.
    # ---------------------------------------------------------

    if sheet_name == "Purchases":
        sheet_folder = "Purchases"
    else:
        sheet_folder = "Sales"

    # ---------------------------------------------------------
    # Get invoice title.
    # ---------------------------------------------------------

    invoice_title_column = (
        header_columns.get("Invoice")
        or header_columns.get("Invoice #")
        or header_columns.get("Invoice Name")
    )

    if invoice_title_column is None:
        raise ValueError(
            f"Could not find invoice title column in {sheet_name}."
        )

    invoice_title = worksheet.cell(
        row=row_number,
        column=invoice_title_column,
    ).value

    if invoice_title is None or not str(invoice_title).strip():
        raise ValueError(
            f"Row {row_number} has no invoice title."
        )

    invoice_title = str(invoice_title).strip()

    # ---------------------------------------------------------
    # Make invoice title safe for use as a folder name.
    # ---------------------------------------------------------

    invalid_characters = '<>:"/\\|?*'

    safe_invoice_title = "".join(
        "_"
        if character in invalid_characters
        else character
        for character in invoice_title
    ).strip()

    if not safe_invoice_title:
        raise ValueError(
            f"Invoice title cannot be used as a folder name: "
            f"{invoice_title!r}"
        )

    # ---------------------------------------------------------
    # Get invoice date.
    # ---------------------------------------------------------

    date_column = (
        header_columns.get("Date")
        or header_columns.get("Invoice Date")
        or header_columns.get("Sale Date")
        or header_columns.get("Purchase Date")
    )

    if date_column is None:
        raise ValueError(
            f"Could not find date column in {sheet_name}."
        )

    invoice_date = worksheet.cell(
        row=row_number,
        column=date_column,
    ).value

    if invoice_date is None:
        raise ValueError(
            f"Row {row_number} has no invoice date."
        )

    # ---------------------------------------------------------
    # Convert date to YYYYMM.
    # ---------------------------------------------------------

    if hasattr(invoice_date, "year") and hasattr(
        invoice_date,
        "month",
    ):

        year_month = (
            f"{invoice_date.year:04d}"
            f"{invoice_date.month:02d}"
        )

    else:

        try:
            parsed_date = datetime.strptime(
                str(invoice_date).strip(),
                "%Y-%m-%d",
            )

            year_month = (
                f"{parsed_date.year:04d}"
                f"{parsed_date.month:02d}"
            )

        except ValueError as error:
            raise ValueError(
                f"Could not determine invoice date from "
                f"{invoice_date!r}."
            ) from error

    # ---------------------------------------------------------
    # Build:
    #
    # Output/
    #   Logs/
    #     Purchases/
    #       Invoice #/
    #
    # or
    #
    # Output/
    #   Logs/
    #     Sales/
    #       Invoice #/
    # ---------------------------------------------------------

    output_directory = INPUT_ROOT

    invoice_folder = os.path.join(
        output_directory,
        OUTPUT_DIR_LOG_NAME,
        sheet_folder,
        safe_invoice_title,
    )

    os.makedirs(
        invoice_folder,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Find next object number for this invoice.
    #
    # Example:
    #
    # S_202609_001.json
    # S_202609_002.json
    # S_202609_003.json
    #
    # Next = 004
    # ---------------------------------------------------------

    existing_numbers = []
    filename_prefix = f"{safe_invoice_title}_"
    filename_suffix = "_Logged.json"

    for filename in os.listdir(invoice_folder):
        if not filename.startswith(filename_prefix):
            continue

        if not filename.endswith(filename_suffix):
            continue

        number_part = filename[
            len(filename_prefix):-len(filename_suffix)
        ]

        if number_part.isdigit():
            existing_numbers.append(int(number_part))

    next_number = max(
        existing_numbers,
        default=0,
    ) + 1

    filename = (
        f"{safe_invoice_title}_"
        f"{next_number:03d}_Logged.json"
    )

    return os.path.join(
        invoice_folder,
        filename,
    )

def sync_json_from_workbook():

    workbook_path = get_workbook_path()

    if not os.path.exists(workbook_path):
        raise FileNotFoundError(
            f"Workbook does not exist: {workbook_path}"
        )

    workbook = load_workbook(
        workbook_path,
        data_only=False,
    )

    updated_count = 0
    created_count = 0
    skipped_count = 0

    sheets = (
        ("Purchases", PURCHASE_HEADERS),
        ("Sales", SALE_HEADERS),
    )

    try:

        for sheet_name, headers in sheets:

            if sheet_name not in workbook.sheetnames:
                continue

            worksheet = workbook[sheet_name]

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
                invoice_prices = load_invoice_prices(
                    worksheet
                )

            json_column = header_columns.get(
                "File Path to JSON"
            )

            if json_column is None:
                continue

            # -------------------------------------------------
            # Process each actual workbook row.
            # -------------------------------------------------

            for row_number in range(
                2,
                worksheet.max_row + 1,
            ):

                # ---------------------------------------------
                # Get all row values.
                # ---------------------------------------------

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

                # ---------------------------------------------
                # Skip completely empty rows.
                # ---------------------------------------------

                if not any(
                    value is not None
                    and str(value).strip()
                    for value in row_values
                ):
                    continue

                # ---------------------------------------------
                # Skip generated summary rows.
                # ---------------------------------------------

                summary_found = any(
                    isinstance(value, str)
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

                # ---------------------------------------------
                # Get JSON path from workbook.
                # ---------------------------------------------

                json_cell = worksheet.cell(
                    row=row_number,
                    column=json_column,
                )

                stored_json_path = get_json_path_from_cell(
                    json_cell
                )

                # ---------------------------------------------
                # Verify the stored JSON path.
                # ---------------------------------------------

                if (
                    stored_json_path
                    and os.path.isfile(stored_json_path)
                ):

                    json_path = os.path.abspath(
                        stored_json_path
                    )

                else:

                    json_path = create_new_json_path(
                        sheet_name,
                        row_number,
                        worksheet,
                        header_columns,
                    )

                    print(
                        f"JSON missing. "
                        f"Saving new JSON to: {json_path}"
                    )

                # ---------------------------------------------
                # Build workbook JSON data.
                # ---------------------------------------------

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

                workbook_data["File Path to JSON"] = os.path.abspath(
                    json_path
                )

                # ---------------------------------------------
                # JSON DOES NOT EXIST.
                # ---------------------------------------------

                if not os.path.isfile(json_path):

                    json_directory = os.path.dirname(
                        json_path
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

                        json_cell.value = (
                            os.path.basename(
                                json_path
                            )
                        )

                        json_cell.hyperlink = json_path
                        json_cell.style = "Hyperlink"

                        created_count += 1

                        print(
                            f"JSON created: {json_path}"
                        )

                    except (
                        OSError,
                        TypeError,
                    ) as error:

                        print(
                            f"Failed to create JSON: "
                            f"{json_path}"
                        )

                        print(
                            f"  {error}"
                        )

                        skipped_count += 1

                    continue

                # ---------------------------------------------
                # JSON EXISTS.
                # ---------------------------------------------

                print(
                    f"Comparing JSON: {json_path}"
                )

                try:

                    with open(
                        json_path,
                        "r",
                        encoding="utf-8",
                    ) as file:

                        existing_data = json.load(file)

                except (
                    OSError,
                    json.JSONDecodeError,
                ) as error:

                    print(
                        f"Failed to read JSON: "
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
                        f"Invalid JSON structure: "
                        f"{json_path}"
                    )

                    skipped_count += 1
                    continue

                # ---------------------------------------------
                # Compare workbook information to JSON.
                # ---------------------------------------------

                changed = (
                    existing_data != workbook_data
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
                            f"JSON updated: {json_path}"
                        )

                    except (
                        OSError,
                        TypeError,
                    ) as error:

                        print(
                            f"Failed to update JSON: "
                            f"{json_path}"
                        )

                        print(
                            f"  {error}"
                        )

                        skipped_count += 1
                        continue

                else:

                    print(
                        f"JSON unchanged: {json_path}"
                    )

                # ---------------------------------------------
                # Always make sure Excel points to actual JSON.
                # ---------------------------------------------

                json_cell.value = os.path.basename(
                    json_path
                )

                json_cell.hyperlink = json_path
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
        f"JSON sync complete. "
        f"Created: {created_count}, "
        f"Updated: {updated_count}, "
        f"Skipped: {skipped_count}"
    )

# ==================================================
# Rebuild Entire Workbook
# ==================================================

def rebuild_workbook(
    invoice_prices=None,
):

    workbook_path = ensure_workbook()

    workbook = load_workbook(
        workbook_path
    )

    purchases_sheet = workbook[
        "Purchases"
    ]

    sales_sheet = workbook[
        "Sales"
    ]

    inventory_sheet = workbook[
        "Remaining Inventory"
    ]

    simplified_inventory_sheet = workbook[
        "Simplified Inventory"
    ]

    overview_sheet = workbook[
        "Overview"
    ]

    # ------------------------------------------------
    # Load Existing Data
    # ------------------------------------------------

    purchases = load_sheet_rows(
        purchases_sheet,
        PURCHASE_HEADERS,
    )

    sales = load_sheet_rows(
        sales_sheet,
        SALE_HEADERS,
    )

    if invoice_prices is None:
        invoice_prices = load_invoice_prices(
            purchases_sheet
        )

    # ------------------------------------------------
    # Calculate Inventory
    # ------------------------------------------------

    remaining = calculate_remaining_inventory(
        purchases,
        sales,
    )

    calculate_purchase_values(
        purchases,
        invoice_prices,
    )

    calculate_sale_profits(
        purchases,
        sales,
    )

    # ------------------------------------------------
    # Sort
    # ------------------------------------------------

    purchases.sort(
        key=purchase_sort_key
    )

    remaining = sort_rows(
        remaining
    )

    # Build the exact Excel row lookup after Purchases
    # have been sorted.
    purchase_excel_rows = (
        build_purchase_excel_row_lookup(
            purchases
        )
    )

    # ------------------------------------------------
    # Rebuild Purchases
    # ------------------------------------------------

    rebuild_sheet(
        purchases_sheet,
        PURCHASE_HEADERS,
        build_purchase_display_rows(
            purchases,
            invoice_prices,
        )
    )

    # ------------------------------------------------
    # Rebuild Sales
    # ------------------------------------------------

    rebuild_sheet(
        sales_sheet,
        SALE_HEADERS,
        build_sale_display_rows(
            sales,
            purchase_excel_rows,
        ),
    )

    # ------------------------------------------------
    # Rebuild Inventory
    # ------------------------------------------------

    rebuild_sheet(
        inventory_sheet,
        INVENTORY_HEADERS,
        build_inventory_display_rows(
            remaining
        ),
    )

    # ------------------------------------------------
    # Rebuild Simplified Inventory
    # ------------------------------------------------

    rebuild_sheet(
        simplified_inventory_sheet,
        SIMPLIFIED_INVENTORY_HEADERS,
        build_simplified_inventory_rows(
            remaining
        ),
    )

    # ------------------------------------------------
    # Rebuild Overview
    # ------------------------------------------------

    rebuild_sheet(
        overview_sheet,
        OVERVIEW_HEADERS,
        build_overview_rows(
            purchases,
        ),
    )

    # ------------------------------------------------
    # Formatting
    # ------------------------------------------------

    format_purchases_sheet(
        purchases_sheet
    )

    format_sales_sheet(
        sales_sheet
    )

    format_inventory_sheet(
        inventory_sheet
    )

    format_simplified_inventory_sheet(
        simplified_inventory_sheet
    )

    format_overview_sheet(
        overview_sheet
    )

    format_image_hyperlinks(
        purchases_sheet
    )

    format_image_hyperlinks(
        sales_sheet
    )

    format_json_hyperlinks(
        inventory_sheet
    )

    format_json_hyperlinks(
        purchases_sheet
    )

    format_json_hyperlinks(
        sales_sheet
    )

    format_image_hyperlinks(
        inventory_sheet
    )

    # Apply special row formatting
    format_sold_rows(
        purchases_sheet
    )

    format_invoice_total_rows(
        purchases_sheet
    )

    format_inventory_total_rows(
        inventory_sheet
    )

    format_sale_profit_total_rows(
        sales_sheet
    )

    # ------------------------------------------------
    # Save
    # ------------------------------------------------

    workbook.save(
        workbook_path
    )

    workbook.close()

    return workbook_path


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

                os.rename(
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