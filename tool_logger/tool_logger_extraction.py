import os
from datetime import datetime


def _normalize_path(value):
    if value is None:
        return value

    value = str(value).strip()

    if not value or value.lower() == "none":
        return value

    if os.path.isabs(value):
        return value

    return os.path.abspath(value)


# ==================================================
# Extract Tool Information
# ==================================================

def extract_tool_info(
    data,
):
    # ------------------------------------------------
    # Basic information
    # ------------------------------------------------

    tool_name = data.get(
        "Tool Name"
    )

    size_1 = data.get(
        "Size-1"
    )

    size_2 = data.get(
        "Size-2"
    )

    brand = data.get(
        "Brand"
    )

    part_number = data.get(
        "Part Number"
    )

    measurement = data.get(
        "Measurement"
    )

    drive = data.get(
        "Drive"
    )

    point = data.get(
        "Point"
    )

    specialty_socket = data.get(
        "Specialty Socket"
    )

    invoice = data.get(
        "Invoice"
    )

    ebay_id = data.get(
        "eBay ID"
    )

    estimated_value = data.get(
        "Estimated Value"
    )

    number_sold = data.get(
        "Number Sold"
    )

    invoice_price = data.get(
        "Invoice Price"
    )

    profit = data.get(
        "Profit"
    )

    image_date = data.get(
        "Date"
    )

    image_path = data.get(
        "File Path to Image"
    )

    json_path = data.get(
        "File Path to JSON"
    )

    inventory_type = data.get(
        "Inventory Type",
        "Purchases",
    )

    # ------------------------------------------------
    # Normalize inventory type
    # ------------------------------------------------

    if not isinstance(
        inventory_type,
        str,
    ):
        inventory_type = "Purchases"

    inventory_type = (
        inventory_type
        .strip()
        .lower()
    )

    if inventory_type not in (
        "purchases",
        "sales",
    ):
        inventory_type = "purchases"

    # ------------------------------------------------
    # Validate required fields
    # ------------------------------------------------

    if not tool_name:
        print(
            "  Missing tool in JSON."
        )
        return None

    if not image_date:
        print(
            "  Missing date in JSON."
        )
        return None


    # ------------------------------------------------
    # Normalize optional fields
    # ------------------------------------------------

    if not size_1:
        size_1 = "NA"

    if not size_2:
        size_2 = "NA"

    if not brand:
        brand = "NA"

    if not part_number:
        part_number = "NA"

    if not measurement:
        measurement = "NA"

    if not drive:
        drive = "NA"

    if not point:
        point = "NA"

    if not specialty_socket:
        specialty_socket = "NA"

    if not invoice:
        invoice = "DEFAULT"

    if not ebay_id:
        ebay_id = "None"

    if not estimated_value:
        estimated_value = "NA"

    if not number_sold:
        number_sold = "1"

    if not invoice_price:
        invoice_price = "None"

    if not profit:
        profit = "NA"

    # ------------------------------------------------
    # Validate date
    # ------------------------------------------------

    try:
        image_date = datetime.strptime(
            str(image_date),
            "%Y-%m-%d",
        ).strftime(
            "%Y-%m-%d"
        )

    except ValueError:
        print(
            f"  Invalid date in JSON: "
            f"{image_date}"
        )
        return None

    # ------------------------------------------------
    # Image path
    # ------------------------------------------------

    absolute_image_path = _normalize_path(
        image_path
    )

    absolute_json_path = _normalize_path(
        json_path
    )
    # ------------------------------------------------
    # Spreadsheet row
    # ------------------------------------------------

    return {
        "Tool Name": tool_name,
        "Size-1": size_1,
        "Size-2": size_2,
        "Brand": brand,
        "Part Number": part_number,
        "Measurement": measurement,
        "Drive": drive,
        "Point": point,
        "Specialty Socket": specialty_socket,
        "Invoice #": invoice,
        "eBay ID": ebay_id,
        "Estimated Value": estimated_value,
        "Number Sold": number_sold,
        "Invoice Price": invoice_price,
        "Profit": profit,
        "Date": image_date,
        "Inventory Type": inventory_type,
        "File Path to Image": absolute_image_path,
        "File Path to JSON": absolute_json_path,
    }