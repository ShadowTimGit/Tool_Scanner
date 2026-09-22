import os
import json

from config import (
    OUTPUT_DIR,
    SETTINGS_FILE,
    LOG_DIR,
)


# ==================================================
# Paths
# ==================================================
def get_output_dir():
    try:
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            settings = json.load(file)

        return settings.get(
            "output_dir",
            OUTPUT_DIR,
        )

    except (
        OSError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        return OUTPUT_DIR
    
INPUT_ROOT = get_output_dir()
LOG_ROOT = LOG_DIR

BRANDS_FILE = os.path.join(
    "settings",
    "brands.json",
)


# ==================================================
# Default Brands
# ==================================================

DEFAULT_BRANDS = {
    "None": [
        "None",
    ],
}


# ==================================================
# Spreadsheet Headers
# ==================================================

PURCHASE_HEADERS = [
    "Date",
    "Invoice #",
    "eBay ID",
    "Brand",
    "Part Number",
    "Tool Name",
    "Size-1",
    "Size-2",
    "Drive",
    "Measurement",
    "Point",
    "Specialty Socket",
    #"Invoice Price",
    "Est. Value",
    "Est. Value Fraction",
    "Est. Purchase Price",
    "Sold",
    "File Path to Image",
    "File Path to JSON",
]

SALE_HEADERS = [
    "Date",
    "Invoice #",
    "eBay ID",
    "Brand",
    "Part Number",
    "Tool Name",
    "Size-1",
    "Size-2",
    "Drive",
    "Measurement",
    "Point",
    "Specialty Socket",
    "Invoice Price",
    "Inventory Found",
    "Profit",
    "File Path to Image",
    "File Path to JSON",
]


INVENTORY_HEADERS = [
    "Date",
    "Brand",
    "Part Number",
    "Tool Name",
    "Size-1",
    "Size-2",
    "Drive",
    "Measurement",
    "Point",
    "Specialty Socket",
    "Est. Value",
    "File Path to Image",
    "File Path to JSON",
]

SIMPLIFIED_INVENTORY_HEADERS = [
    "Tool",
    "Brand",
    "Quantity",
]

OVERVIEW_HEADERS = [
    "DATE",
    "Invoice #",
    "Platform",
    "Ebay ID",
    "Item Count",
    "Invoice Price",
]