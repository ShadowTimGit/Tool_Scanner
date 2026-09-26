import json
import re
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from config import (
    SETTINGS_FILE,
    OUTPUT_DIR,
)

from openpyxl import load_workbook


# ==================================================
# Configuration
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

# Only this worksheet is processed.
INPUT_SHEET = "Item Master"

# JSON files are written here.
OUTPUT_DIR_LOG_NAME = "Converted_Tool_Logs"

PURCHASE_OUTPUT_DIR_NAME = "Purchases"

SALE_OUTPUT_DIR_NAME = "Sales"

# Generated sale invoice format:
# SALE-20260826-000001
SALE_INVOICE_PREFIX = "S"

# Existing image paths are not available in the
# old Item Master, so this stays blank.
DEFAULT_IMAGE_PATH = ""
DEFAULT_JSON_PATH = ""


# ==================================================
# Expected Headers
# ==================================================

REQUIRED_HEADERS = (
    "Date",
    "Order / Invoice #",
    "eBay Seller",
    "Brand",
    "Part Number",
    "Type",
    "Size",
    "Drive",
    "Measurement",
    "Point",
    "Specialty Socket (Y/N)",
    "Item Cost",
    "Qty Purchased",
    "Qty Sold",
    "Sale Price*",
    "Total Profit",
)

def select_input_file():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Item Master Workbook",
        filetypes=[
            (
                "Excel Files",
                "*.xlsx *.xlsm *.xltx *.xltm",
            ),
            (
                "All Files",
                "*.*",
            ),
        ],
    )

    root.destroy()

    if not file_path:
        print(
            "No file selected."
        )
        return None

    return file_path

# ==================================================
# General Helpers
# ==================================================

def normalize_header(
    value,
):
    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip(),
    )


def normalize_invoice(
    value,
):
    if value is None:
        return ""

    return str(
        value
    ).strip()


def clean_text(
    value,
):
    if value is None:
        return ""

    return str(
        value
    ).strip()


def parse_quantity(
    value,
    default=0,
):
    if value is None:
        return default

    text = str(
        value
    ).strip()

    if not text:
        return default

    if text.casefold() in {
        "na",
        "n/a",
        "none",
        "-",
    }:
        return 0

    try:
        return max(
            0,
            int(
                float(text)
            ),
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def parse_money(
    value,
    default=Decimal("0.00"),
):
    if value is None:
        return default

    if isinstance(
        value,
        Decimal,
    ):
        return value

    if isinstance(
        value,
        (int, float),
    ):
        return Decimal(
            str(value)
        )

    text = str(
        value
    ).strip()

    if not text:
        return default

    if text.casefold() in {
        "na",
        "n/a",
        "none",
        "-",
    }:
        return default

    negative = False

    if (
        text.startswith("(")
        and text.endswith(")")
    ):
        negative = True
        text = text[1:-1]

    text = (
        text
        .replace("$", "")
        .replace(",", "")
        .strip()
    )

    if text.startswith("-"):
        negative = True
        text = text[1:].strip()

    try:
        number = Decimal(text)

    except (
        InvalidOperation,
        ValueError,
    ):
        return default

    if negative:
        number *= -1

    return number


def money_as_float(
    value,
):
    return float(
        value.quantize(
            Decimal("0.01")
        )
    )


def format_date(
    value,
):
    if value is None:
        return ""

    if isinstance(
        value,
        datetime,
    ):
        return value.strftime(
            "%Y-%m-%d"
        )

    if isinstance(
        value,
        date,
    ):
        return value.strftime(
            "%Y-%m-%d"
        )

    text = str(
        value
    ).strip()

    if not text:
        return ""

    # Try several common formats used by Excel exports.
    formats = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y/%m/%d",
    )

    for fmt in formats:

        try:
            parsed = datetime.strptime(
                text,
                fmt,
            )

            return parsed.strftime(
                "%Y-%m-%d"
            )

        except ValueError:
            continue

    # Preserve unknown date formats instead
    # of destroying source information.
    return text


def safe_filename(
    value,
):
    value = clean_text(
        value
    )

    if not value:
        return "UNKNOWN"

    return re.sub(
        r'[^A-Za-z0-9._-]+',
        "_",
        value,
    )


# ==================================================
# Workbook Loading
# ==================================================

def load_item_master(
    input_file,
):
    input_path = Path(
        input_file
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input workbook not found: "
            f"{input_path}"
        )

    workbook = load_workbook(
        input_path,
        data_only=True,
    )

    if INPUT_SHEET not in workbook.sheetnames:
        workbook.close()

        raise ValueError(
            f'Worksheet "{INPUT_SHEET}" '
            f"was not found."
        )

    worksheet = workbook[
        INPUT_SHEET
    ]

    if worksheet.max_row < 1:
        workbook.close()

        raise ValueError(
            f'Worksheet "{INPUT_SHEET}" '
            f"is empty."
        )

    headers = [
        normalize_header(
            cell.value
        )
        for cell in worksheet[1]
    ]

    header_map = {}

    for column_number, header in enumerate(
        headers,
        start=1,
    ):

        if header:
            header_map[
                header
            ] = column_number

    missing_headers = [
        header
        for header in REQUIRED_HEADERS
        if header not in header_map
    ]

    if missing_headers:
        workbook.close()

        raise ValueError(
            "Missing required headers:\n"
            + "\n".join(
                f"  - {header}"
                for header in missing_headers
            )
        )

    rows = []

    for row_number in range(
        2,
        worksheet.max_row + 1,
    ):

        row = {}

        has_data = False

        for header in REQUIRED_HEADERS:

            value = worksheet.cell(
                row=row_number,
                column=header_map[header],
            ).value

            row[header] = value

            if (
                value is not None
                and str(value).strip()
            ):
                has_data = True

        if not has_data:
            continue

        rows.append(
            row
        )

    workbook.close()

    return rows


# ==================================================
# Invoice Price Calculation
# ==================================================

def calculate_invoice_prices(
    source_rows,
):
    invoice_prices = defaultdict(
        Decimal
    )

    warnings = []

    for row_number, row in enumerate(
        source_rows,
        start=2,
    ):

        invoice = normalize_invoice(
            row.get(
                "Order / Invoice #"
            )
        )

        if not invoice:
            warnings.append(
                f"Row {row_number}: "
                "missing Order / Invoice #."
            )
            continue

        item_cost = parse_money(
            row.get(
                "Item Cost"
            )
        )

        quantity = parse_quantity(
            row.get(
                "Qty Purchased"
            ),
            default=1,
        )

        invoice_prices[
            invoice
        ] += (
            item_cost
            * quantity
        )

    return (
        dict(invoice_prices),
        warnings,
    )


# ==================================================
# Purchase Record
# ==================================================

def build_purchase_record(
    source_row,
    invoice_price,
    json_path,
    sold="NO",
):
    return {
        "Inventory Type": "purchase",

        "Date": format_date(
            source_row.get(
                "Date"
            )
        ),

        # Order / Invoice # becomes Invoice.
        "Invoice": normalize_invoice(
            source_row.get(
                "Order / Invoice #"
            )
        ),

        # eBay seller username becomes eBay ID.
        "eBay ID": clean_text(
            source_row.get(
                "eBay Seller"
            )
        ),

        "Part Number": clean_text(
            source_row.get(
                "Part Number"
            )
        ),

        "Brand": clean_text(
            source_row.get(
                "Brand"
            )
        ),

        # Part Number becomes Tool Name.
        "Tool Name": clean_text(
            source_row.get(
                "Type"
            )
        ),

        # Old Size becomes Size-1.
        "Size-1": clean_text(
            source_row.get(
                "Size"
            )
        ),

        # No second size exists in the old data.
        "Size-2": "",

        "Drive": clean_text(
            source_row.get(
                "Drive"
            )
        ),

        "Measurement": clean_text(
            source_row.get(
                "Measurement"
            )
        ),

        "Point": clean_text(
            source_row.get(
                "Point"
            )
        ),

        "Specialty Socket": clean_text(
            source_row.get(
                "Specialty Socket (Y/N)"
            )
        ),

        # This is retained internally so the JSON can
        # represent the invoice-level purchase price.
        #
        # It is NOT an Est. Value and should not be used
        # as the estimated tool value.
        "Invoice Price": money_as_float(
            invoice_price
        ),

        # Your normal workbook rebuild will generate:
        #
        # Est. Value
        # Est. Value Fraction
        # Est. Purchase Price
        #
        # They are deliberately omitted here.

        "Sold": sold,

        "File Path to Image": DEFAULT_IMAGE_PATH,
        "File Path to JSON": str(
            Path(json_path).resolve()
        ),
    }


# ==================================================
# Sale Record
# ==================================================

def build_sale_record(
    source_row,
    sale_invoice,
    sale_price,
    json_path,
):
    return {
        "Inventory Type": "sale",

        "Date": format_date(
            source_row.get(
                "Date"
            )
        ),

        # Every sold item receives an individual
        # generated sale invoice number.
        "Invoice": sale_invoice,

        # The old Item Master contains the purchase
        # seller, not the sale buyer. There is no
        # buyer username available, so this is blank.
        "eBay ID": "",

        "Part Number": clean_text(
            source_row.get(
                "Part Number"
            )
        ),

        "Brand": clean_text(
            source_row.get(
                "Brand"
            )
        ),

        "Tool Name": clean_text(
            source_row.get(
                "Type"
            )
        ),

        "Size-1": clean_text(
            source_row.get(
                "Size"
            )
        ),

        "Size-2": "",

        "Drive": clean_text(
            source_row.get(
                "Drive"
            )
        ),

        "Measurement": clean_text(
            source_row.get(
                "Measurement"
            )
        ),

        "Point": clean_text(
            source_row.get(
                "Point"
            )
        ),

        "Specialty Socket": clean_text(
            source_row.get(
                "Specialty Socket (Y/N)"
            )
        ),

        # Sale Price becomes Invoice Price
        # on the individual sale record.
        "Invoice Price": money_as_float(
            sale_price
        ),


        "File Path to Image": DEFAULT_IMAGE_PATH,
        "File Path to JSON": str(
            Path(json_path).resolve()
        ),
    }


# ==================================================
# Sale Invoice Generator
# ==================================================

def make_sale_invoice(
    sale_date,
    counter,
):
    compact_date = (
        sale_date.replace(
            "-",
            "",
        )
        if sale_date
        else datetime.now().strftime(
            "%Y%m%d"
        )
    )

    return (
        f"{SALE_INVOICE_PREFIX}-"
        f"{compact_date}-"
        f"{counter:06d}"
    )


# ==================================================
# Conversion
# ==================================================

def convert_item_master(
    input_file=None,
):

    if not input_file:
        input_file = select_input_file()

    if not input_file:
        return

    source_rows = load_item_master(
        input_file
    )

    invoice_prices, warnings = (
        calculate_invoice_prices(
            source_rows
        )
    )

    output_path = Path(
        get_output_dir()
    ) / OUTPUT_DIR_LOG_NAME

    purchase_output_path = (
        output_path
        / PURCHASE_OUTPUT_DIR_NAME
    )

    sale_output_path = (
        output_path
        / SALE_OUTPUT_DIR_NAME
    )
    
    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    purchase_output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    sale_output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    purchase_records = []
    sale_records = []

    sale_counter = 1

    # Maps each purchase invoice to its generated sale invoice.
    sale_invoices = {}

    # Tracks the next item number within each sale invoice.
    sale_item_counters = {}

    # Used to make purchase filenames unique.
    purchase_counter = 1

    for row_number, source_row in enumerate(
        source_rows,
        start=2,
    ):

        invoice = normalize_invoice(
            source_row.get(
                "Order / Invoice #"
            )
        )

        if not invoice:
            continue

        invoice_price = invoice_prices.get(
            invoice,
            Decimal("0.00"),
        )

        # ------------------------------------------
        # Purchase quantity
        # ------------------------------------------

        quantity_purchased = parse_quantity(
            source_row.get(
                "Qty Purchased"
            ),
            default=1,
        )

        sale_status = clean_text(
            source_row.get(
                "Qty Sold"
            )
        ).casefold()

        if quantity_purchased <= 0:
            warnings.append(
                f"Row {row_number}: "
                f"invalid Qty Purchased; "
                f"no purchase records created."
            )
            continue

        for item_number in range(
            1,
            quantity_purchased + 1,
        ):

            if sale_status in {
                "sold",
                "giveaway",
            }:
                sold_status = "YES"
            else:
                sold_status = "NO"

            filename = (
                f"Purchase_"
                f"{purchase_counter:06d}_"
                f"{safe_filename(invoice)}"
                f"_Logged.json"
            )

            json_path = purchase_output_path / filename

            purchase_record = build_purchase_record(
                source_row,
                invoice_price,
                json_path,
                sold_status,
            )

            purchase_records.append(
                purchase_record
            )
            with open(
                json_path,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    purchase_record,
                    file,
                    indent=4,
                )

            purchase_counter += 1

        # ------------------------------------------
        # Sale / giveaway status
        # ------------------------------------------

        sale_status = clean_text(
            source_row.get(
                "Qty Sold"
            )
        ).casefold()

        sale_price = parse_money(
            source_row.get(
                "Sale Price*"
            )
        )

        # ------------------------------------------
        # Create sale records
        # ------------------------------------------

        if sale_status == "sold":

            sale_date = format_date(
                source_row.get(
                    "Date"
                )
            )

            # Reuse the same generated sale invoice
            # for every row belonging to the same
            # original purchase invoice.
            if invoice not in sale_invoices:

                sale_invoices[invoice] = make_sale_invoice(
                    sale_date,
                    sale_counter,
                )

                sale_counter += 1

            sale_invoice = sale_invoices[invoice]

            if sale_invoice not in sale_item_counters:
                sale_item_counters[sale_invoice] = 1

            for _ in range(
                quantity_purchased
            ):

                item_number = sale_item_counters[
                    sale_invoice
                ]

                sale_item_counters[
                    sale_invoice
                ] += 1

                filename = (
                    f"Sale_"
                    f"{safe_filename(sale_invoice)}"
                    f"_Item_{item_number:03d}"
                    f"_Logged.json"
                )

                json_path = sale_output_path / filename

                sale_record = build_sale_record(
                    source_row,
                    sale_invoice,
                    sale_price,
                    json_path,
                )

                sale_records.append(
                    sale_record
                )

                with open(
                    json_path,
                    "w",
                    encoding="utf-8",
                ) as file:

                    json.dump(
                        sale_record,
                        file,
                        indent=4,
                    )

    # ==================================================
    # Conversion Manifest
    # ==================================================

    manifest = {
        "source_file": str(
            Path(input_file)
        ),
        "source_sheet": INPUT_SHEET,

        "purchase_records_created": len(
            purchase_records
        ),

        "sale_records_created": len(
            sale_records
        ),

        "invoice_count": len(
            invoice_prices
        ),

        "invoice_prices": {
            invoice: money_as_float(
                price
            )
            for invoice, price
            in sorted(
                invoice_prices.items()
            )
        },

        "warnings": warnings,

        "field_mapping": {
            "Order / Invoice #": "Invoice",
            "eBay Seller": "eBay ID",
            "Part Number": "Part Number",
            "Brand": "Brand",
            "Type": "Tool Name",
            "Size": "Size-1",
            "Drive": "Drive",
            "Measurement": "Measurement",
            "Point": "Point",
            "Specialty Socket (Y/N)": (
                "Specialty Socket"
            ),
            "Qty Purchased": (
                "individual purchase records"
            ),
            "Qty Sold": (
                "individual sale records"
            ),
            "Sale Price*": (
                "sale Invoice Price"
            ),
            "Item Cost": (
                "used only to calculate "
                "purchase Invoice Price"
            ),
        },

        "excluded_fields": [
            "Type",
            "Item Cost as Est. Value",
            "Est. Value",
            "Est. Value Fraction",
            "Est. Purchase Price",
        ],
    }

    with open(
        output_path / "conversion_manifest.json",
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            manifest,
            file,
            indent=4,
        )

    # ==================================================
    # Console Summary
    # ==================================================

    print(
        "================================"
    )

    print(
        "ITEM MASTER CONVERSION COMPLETE"
    )

    print(
        "================================"
    )

    print(
        f"Source rows: "
        f"{len(source_rows)}"
    )

    print(
        f"Purchase records created: "
        f"{len(purchase_records)}"
    )

    print(
        f"Sale records created: "
        f"{len(sale_records)}"
    )

    print(
        f"Invoices found: "
        f"{len(invoice_prices)}"
    )

    print(
        f"Output directory: "
        f"{output_path.resolve()}"
    )

    if warnings:

        print()
        print(
            "Warnings:"
        )

        for warning in warnings:
            print(
                f"  - {warning}"
            )


# ==================================================
# Main
# ==================================================

if __name__ == "__main__":
    convert_item_master()