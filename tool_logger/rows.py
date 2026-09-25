from .tool_logger_config import (
    PURCHASE_HEADERS,
    SALE_HEADERS,
    INVENTORY_HEADERS,
)

from .calculations import (
    normalize_invoice,
)

def size_value(value):
    if value is None:
        return ""

    value = str(value).strip()

    fractions = {
        "½": "1/2",
        "⅓": "1/3",
        "⅔": "2/3",
        "¼": "1/4",
        "¾": "3/4",
        "⅕": "1/5",
        "⅖": "2/5",
        "⅗": "3/5",
        "⅘": "4/5",
        "⅙": "1/6",
        "⅚": "5/6",
        "⅛": "1/8",
        "⅜": "3/8",
        "⅝": "5/8",
        "⅞": "7/8",
    }

    for fraction, replacement in fractions.items():
        value = value.replace(
            fraction,
            replacement,
        )

    value = (
        value
        .replace("“", '"')
        .replace("”", '"')
        .replace("″", '"')
    )

    return value

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
        size_value(row.get("Size-1")),
        size_value(row.get("Size-2")),
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

    # ------------------------------------------------
    # Storefront Sales Volume
    #
    # H10:I10 = section header
    # H11:I13 = labels
    # I11:I13 = values
    # ------------------------------------------------

    while len(rows) < 13:
        rows.append([""] * 11)

    rows[8][7] = "Purchase Platform Volume"

    rows[9][7] = "Ebay Sales"
    rows[10][7] = "WhatNot Sales"
    rows[11][7] = "Facebook Sales"

    rows[9][8] = f'=COUNTIF($C$2:$C${purchase_end_row},"Ebay")'
    rows[10][8] = f'=COUNTIF($C$2:$C${purchase_end_row},"Whatnot")'
    rows[11][8] = f'=COUNTIF($C$2:$C${purchase_end_row},"Facebook")'

    return rows


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
        size_value(row.get("Size-1")),
        size_value(row.get("Size-2")),
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
        size_value(row.get("Size-1")),
        size_value(row.get("Size-2")),
        row.get("Drive"),
        row.get("Measurement"),
        row.get("Point"),
        row.get("Specialty Socket"),
        row.get("Est. Value"),
        row.get("File Path to Image"),
        row.get("File Path to JSON"),
    ]



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
