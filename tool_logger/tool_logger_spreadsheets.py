import json
import os
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import (
    Alignment,
    Border,
    Font,
    PatternFill,
    Side,
)

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

#INPUT_ROOT tool logger config = OUTPUT_DIR (it triggers a function that pulls it from settings or default if settings doesnt exist)

from settings_menu.inventory_settings import (
    InventorySettings,
)

OUTPUT_DIR_LOG_NAME = "Converted_Tool_Logs"

PURCHASE_OUTPUT_DIR_NAME = "Purchases"

SALE_OUTPUT_DIR_NAME = "Sales"

SALE_INVOICE_PREFIX = "SALE"

# ==================================================
# Column Sizes
# ==================================================
small_col = 12
med_col = 15
average_col = 18
large_col = 22
file_loc_col = 50

# ==================================================
# Workbook
# ==================================================
WORKBOOK_NAME = "Tool_Log.xlsx"

# ==================================================
# Get Workbook Path
# ==================================================

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
# Format Header
# ==================================================

def format_header(worksheet):

    header_font = Font(
        bold=True
    )

    for cell in worksheet[1]:
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center"
        )


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

def format_sold_rows(
    worksheet,
):
    sold_fill = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE",
    )

    sold_column = None

    for cell in worksheet[1]:
        if cell.value == "Sold":
            sold_column = cell.column
            break

    if sold_column is None:
        return

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):
        sold_value = worksheet.cell(
            row=row_number,
            column=sold_column,
        ).value

        if str(
            sold_value
        ).strip().upper() == "YES":

            # Highlight ONLY the Sold cell,
            # not the entire purchase row.
            worksheet.cell(
                row=row_number,
                column=sold_column,
            ).fill = sold_fill

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


# ==================================================
# Overview Formatting
# ==================================================

def format_overview_sheet(worksheet):

    column_widths = {
        1: med_col,
        2: average_col,
        3: med_col,
        4: large_col,
        5: med_col,
        6: average_col,
        7: 10,
        8: 30,
        9: 18,
        10: 18,
        11: 18,
    }

    apply_common_formatting(
        worksheet,
        column_widths,
    )

    # ------------------------------------------------
    # Main table formatting
    # ------------------------------------------------

    for row in worksheet.iter_rows(
        min_row=2,
        max_row=worksheet.max_row,
        min_col=1,
        max_col=6,
    ):

        row[2].alignment = Alignment(
            horizontal="left",
            vertical="center",
        )

        row[3].alignment = Alignment(
            horizontal="left",
            vertical="center",
        )

        row[4].alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

        row[5].number_format = "0.00"

        row[5].alignment = Alignment(
            horizontal="right",
            vertical="center",
        )

    # ------------------------------------------------
    # Section styling
    # ------------------------------------------------

    section_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    section_font = Font(
        name="Arial",
        size=11,
        bold=True,
        color="FFFFFF",
    )

    label_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    value_fill = PatternFill(
        fill_type="solid",
        fgColor="F2F2F2",
    )

    # ------------------------------------------------
    # Purchase Information
    # ------------------------------------------------

    worksheet.merge_cells("H2:I2")

    for cell_reference in ("H2", "I2"):

        cell = worksheet[cell_reference]

        cell.fill = section_fill
        cell.font = section_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    worksheet["H2"] = "PURCHASE INFORMATION"

    worksheet.row_dimensions[2].height = 24

    for cell_reference in (
        "H3",
        "I3",
    ):

        cell = worksheet[cell_reference]

        cell.fill = label_fill
        cell.font = Font(
            name="Arial",
            size=11,
            bold=True,
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    for cell_reference in (
        "H4",
        "I4",
    ):

        cell = worksheet[cell_reference]

        cell.fill = value_fill
        cell.font = Font(
            name="Arial",
            size=11,
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    # ------------------------------------------------
    # Sales Information
    # ------------------------------------------------

    worksheet.merge_cells("H6:K6")

    for cell_reference in (
        "H6",
        "I6",
        "J6",
        "K6",
    ):

        cell = worksheet[cell_reference]

        cell.fill = section_fill
        cell.font = section_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    worksheet["H6"] = "SALES INFORMATION"

    worksheet.row_dimensions[6].height = 24

    for cell_reference in (
        "H7",
        "I7",
        "J7",
        "K7",
    ):

        cell = worksheet[cell_reference]

        cell.fill = label_fill
        cell.font = Font(
            name="Arial",
            size=11,
            bold=True,
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True,
        )

    for cell_reference in (
        "H8",
        "I8",
        "J8",
        "K8",
    ):

        cell = worksheet[cell_reference]

        cell.fill = value_fill
        cell.font = Font(
            name="Arial",
            size=11,
        )
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )

    # ------------------------------------------------
    # Number Formatting
    # ------------------------------------------------

    for cell_reference in (
        "I4",
        "I8",
        "J8",
        "K8",
    ):

        worksheet[cell_reference].number_format = "0.00"

    # ------------------------------------------------
    # Highlight Net Profit
    # ------------------------------------------------

    worksheet["K7"].fill = PatternFill(
        fill_type="solid",
        fgColor="E2F0D9",
    )

    worksheet["K8"].fill = PatternFill(
        fill_type="solid",
        fgColor="E2F0D9",
    )

    worksheet["K7"].font = Font(
        name="Arial",
        size=11,
        bold=True,
    )

    worksheet["K8"].font = Font(
        name="Arial",
        size=11,
        bold=True,
    )


# ==================================================
# Simplified Inventory Formatting
# ==================================================

def format_simplified_inventory_sheet(
    worksheet,
):
    column_widths = {
        1: large_col,
        2: large_col,
        3: med_col,
    }

    apply_common_formatting(
        worksheet,
        column_widths,
    )

    tool_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    tool_font = Font(
        name="Arial",
        size=11,
        bold=True,
    )

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):
        tool_cell = worksheet.cell(
            row=row_number,
            column=1,
        )

        brand_cell = worksheet.cell(
            row=row_number,
            column=2,
        )

        quantity_cell = worksheet.cell(
            row=row_number,
            column=3,
        )

        # Tool group row
        if (
            tool_cell.value is not None
            and str(tool_cell.value).strip()
        ):
            for column in range(1, 4):
                cell = worksheet.cell(
                    row=row_number,
                    column=column,
                )

                cell.fill = tool_fill
                cell.font = tool_font

        # Quantity
        if isinstance(
            quantity_cell.value,
            (int, float),
        ):
            quantity_cell.number_format = "0"
            quantity_cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

        brand_cell.alignment = Alignment(
            horizontal="left",
            vertical="center",
        )

def format_image_hyperlinks(
    worksheet,
):
    image_column = None

    for cell in worksheet[1]:
        if cell.value == "File Path to Image":
            image_column = cell.column
            break

    if image_column is None:
        return

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):
        cell = worksheet.cell(
            row=row_number,
            column=image_column,
        )

        if not cell.value:
            continue

        image_path = str(
            cell.value
        ).strip()

        if not image_path:
            continue

        if not os.path.exists(image_path):
            continue

        cell.hyperlink = image_path
        cell.value = os.path.basename(image_path)
        cell.style = "Hyperlink"

def format_json_hyperlinks(
    worksheet,
):
    image_column = None

    for cell in worksheet[1]:
        if cell.value == "File Path to JSON":
            image_column = cell.column
            break

    if image_column is None:
        return

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):
        cell = worksheet.cell(
            row=row_number,
            column=image_column,
        )

        if not cell.value:
            continue

        json_path = str(
            cell.value
        ).strip()

        if not json_path:
            continue

        if not os.path.exists(json_path):
            continue

        cell.hyperlink = json_path
        cell.value = os.path.basename(json_path)
        cell.style = "Hyperlink"

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

def format_invoice_total_rows(
    worksheet,
):

    total_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):

        label_found = False

        for cell in worksheet[row_number]:

            if cell.value == "Invoice Est. Sum":
                label_found = True
                break

        if not label_found:
            continue

        for column in range(
            1,
            worksheet.max_column + 1,
        ):

            cell = worksheet.cell(
                row=row_number,
                column=column,
            )

            cell.font = Font(
                name="Arial",
                size=11,
                bold=True,
            )

            cell.fill = total_fill

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


# ==================================================
# Common Worksheet Formatting
# ==================================================

def apply_common_formatting(
    worksheet,
    column_widths,
):

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    header_font = Font(
        name="Arial",
        size=11,
        bold=True,
        color="FFFFFF",
    )

    body_font = Font(
        name="Arial",
        size=11,
        color="000000",
    )

    highlighted_font = Font(
        name="Arial",
        size=11,
        italic=True,
        color="9C6500",
    )

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    # ------------------------------------------------
    # Column widths
    # ------------------------------------------------

    for column, width in column_widths.items():

        worksheet.column_dimensions[
            worksheet.cell(
                row=1,
                column=column,
            ).column_letter
        ].width = width

    # ------------------------------------------------
    # Header
    # ------------------------------------------------

    for cell in worksheet[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
        )
        cell.border = thin_border

    worksheet.row_dimensions[1].height = 22

    # ------------------------------------------------
    # Body
    # ------------------------------------------------

    alternate_fill = PatternFill(
        fill_type="solid",
        fgColor="F3F6F9",
    )

    for row_number, row in enumerate(
        worksheet.iter_rows(
            min_row=2,
            max_row=worksheet.max_row,
        ),
        start=2,
    ):
        for cell in row:
            cell.font = body_font
            cell.border = thin_border

            # Alternate normal data rows for readability.
            if row_number % 2 == 0:
                cell.fill = alternate_fill

            if cell.alignment.horizontal:
                horizontal = cell.alignment.horizontal
            else:
                horizontal = None

            cell.alignment = Alignment(
                horizontal=horizontal,
                vertical="center",
            )

    # ------------------------------------------------
    # Remove filters
    # ------------------------------------------------

    worksheet.auto_filter.ref = None

    # ------------------------------------------------
    # Freeze header
    # ------------------------------------------------

    worksheet.freeze_panes = "A2"


# ==================================================
# Purchases Formatting
# ==================================================

def format_purchases_sheet(
    worksheet,
):

    column_widths = {
        1: med_col,
        2: med_col,
        3: med_col,
        4: med_col,
        5: med_col,        
        6: med_col,
        7: med_col,
        8: med_col,
        9: small_col,
        10: average_col,
        11: small_col,
        12: average_col,
        13: large_col,
        14: large_col,
        15: large_col,
        16: med_col,
        17: file_loc_col,
        18: file_loc_col,
    }

    apply_common_formatting(
        worksheet,
        column_widths,
    )

    # Center selected columns
    center_headers = {
        "Sold",
        "Specialty Socket",
        "Est. Value",
        "Est. Value Fraction",
    }

    for header_cell in worksheet[1]:

        if header_cell.value not in center_headers:
            continue

        column = header_cell.column

        for row_number in range(
            2,
            worksheet.max_row + 1,
        ):

            worksheet.cell(
                row=row_number,
                column=column,
            ).alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

    # Price/value formatting
    price_headers = {
        #"Invoice Price",
        "Est. Value",
        "Est. Value Fraction",
        "Est. Purchase Price",
    }

    for header_cell in worksheet[1]:

        if header_cell.value not in price_headers:
            continue

        column = header_cell.column

        for row_number in range(
            2,
            worksheet.max_row + 1,
        ):

            cell = worksheet.cell(
                row=row_number,
                column=column,
            )

            cell.number_format = "0.00"

# ==================================================
# Sale Profit Total Formatting
# ==================================================

def format_sale_profit_total_rows(
    worksheet,
):
    total_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    total_font = Font(
        bold=True,
    )

    revenue_labels = {
        "Sales:",
        "Total Sales:",
    }

    profit_labels = {
        "Profit:",
        "Sales Profit:",
        "Total Profit:",
    }

    for row_number in range(
        1,
        worksheet.max_row + 1,
    ):
        row_values = [
            worksheet.cell(
                row=row_number,
                column=column_number,
            ).value
            for column_number in range(
                1,
                worksheet.max_column + 1,
            )
        ]

        if not any(
            value in revenue_labels
            or value in profit_labels
            for value in row_values
        ):
            continue

        # Format the entire summary row
        for column_number in range(
            1,
            worksheet.max_column + 1,
        ):
            cell = worksheet.cell(
                row=row_number,
                column=column_number,
            )

            cell.font = total_font
            cell.fill = total_fill

        # Format the value immediately after each label.
        # This preserves your existing column placement.
        for column_number in range(
            1,
            worksheet.max_column,
        ):
            label = worksheet.cell(
                row=row_number,
                column=column_number,
            ).value

            if (
                label in revenue_labels
                or label in profit_labels
            ):
                value_cell = worksheet.cell(
                    row=row_number,
                    column=column_number + 1,
                )

                value_cell.number_format = "0.00"

                value_cell.alignment = Alignment(
                    horizontal="right",
                    vertical="center",
                )
        
# ==================================================
# Sales Formatting
# ==================================================

def format_sales_sheet(
    worksheet,
):

    column_widths = {
        1: med_col,
        2: med_col,
        3: med_col,
        4: med_col,
        5: med_col,
        6: med_col,
        7: med_col,
        8: med_col,
        9: small_col,
        10: average_col,
        11: small_col,
        12: average_col,
        13: average_col,  
        14: average_col,   
        15: average_col,   
        16: file_loc_col,
        17: file_loc_col,
    }

    apply_common_formatting(
        worksheet,
        column_widths,
    )

    # Center Inventory Found
    for header_cell in worksheet[1]:

        if header_cell.value != "Inventory Found":
            continue

        column = header_cell.column

        for row_number in range(
            2,
            worksheet.max_row + 1,
        ):

            worksheet.cell(
                row=row_number,
                column=column,
            ).alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

    # Price formatting
    price_headers = {
        "Invoice Price",
        "Profit",
    }

    for header_cell in worksheet[1]:

        if header_cell.value not in price_headers:
            continue

        column = header_cell.column

        for row_number in range(
            2,
            worksheet.max_row + 1,
        ):

            cell = worksheet.cell(
                row=row_number,
                column=column,
            )

            if isinstance(
                cell.value,
                (int, float),
            ):
                cell.number_format = "0.00"


# ==================================================
# Inventory Formatting
# ==================================================

def format_inventory_sheet(
    worksheet,
):

    column_widths = {
        1: med_col,
        2: med_col,
        3: med_col,       
        4: med_col,
        5: med_col,
        6: med_col,
        7: small_col,
        8: med_col,
        9: med_col,
        10: average_col,
        11: large_col,
        12: file_loc_col,
        13: file_loc_col,
    }

    apply_common_formatting(
        worksheet,
        column_widths,
    )

    # Centered Headers
    center_headers = {
        "Specialty Socket",
        "Inventory Found",
        "Est. Value",
    }

    for header_cell in worksheet[1]:

        if header_cell.value not in center_headers:
            continue

        column = header_cell.column

        for row_number in range(
            2,
            worksheet.max_row + 1,
        ):

            worksheet.cell(
                row=row_number,
                column=column,
            ).alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

    # Estimated value formatting
    for header_cell in worksheet[1]:

        if header_cell.value != "Est. Value":
            continue

        column = header_cell.column

        for row_number in range(
            2,
            worksheet.max_row + 1,
        ):

            cell = worksheet.cell(
                row=row_number,
                column=column,
            )

            if isinstance(
                cell.value,
                (int, float),
            ):
                cell.number_format = "0.00"


def format_inventory_total_rows(
    worksheet,
):

    total_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAF7",
    )

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):

        label = worksheet.cell(
            row=row_number,
            column=10,
        ).value

        if label not in {
            "Est. Profit Sum",
            "Est. Inventory Sum",
        }:
            continue

        for column in range(
            1,
            worksheet.max_column + 1,
        ):

            cell = worksheet.cell(
                row=row_number,
                column=column,
            )

            cell.font = Font(
                name="Arial",
                size=11,
                bold=True,
            )

            cell.fill = total_fill

            if column == 11:
                cell.number_format = "0.00"
                cell.alignment = Alignment(
                    horizontal="center",
                    vertical="center",
                )

# ==================================================
# Save Row
# ==================================================

def save_to_spreadsheet(
    row_data,
):

    workbook_path = ensure_workbook()

    workbook = load_workbook(
        workbook_path
    )

    inventory_type = row_data.get(
        "Inventory Type",
        "purchase",
    )

    inventory_type = str(
        inventory_type
    ).strip().lower()

    if inventory_type == "sale":

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

    if inventory_type != "sale":

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
    Build the JSON representation of one workbook row.
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

    if sheet_name == "Purchases":

        data["Inventory Type"] = "purchase"

        invoice = normalize_invoice(
            data.get("eBay ID")
        )

        if invoice and invoice in invoice_prices:
            data["Invoice Price"] = json_safe_value(
                invoice_prices[invoice]
            )

    elif sheet_name == "Sales":

        data["Inventory Type"] = "sale"

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
    # Determine Purchase / Sale prefix and folder.
    # ---------------------------------------------------------

    if sheet_name == "Purchases":
        prefix = "P"
        sheet_folder = "Purchases"
    else:
        prefix = "S"
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
                    "purchase",
                )
            ).strip().casefold()

            if inventory_type == "sale":
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