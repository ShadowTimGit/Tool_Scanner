from settings_menu.inventory_settings import (
    InventorySettings,
)

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

        purchase_value = normalize_match_value(
            purchase.get(field, "")
        )

        sale_value = normalize_match_value(
            sale.get(field, "")
        )

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

def normalize_invoice(
    value,
):

    if value is None:
        return ""

    return str(
        value
    ).strip().casefold()



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

def normalize_match_value(value):
    if value is None:
        return ""

    value = (
        str(value)
        .strip()
        .casefold()
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
    )

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

    return value

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

