import cv2
import json
import os

from datetime import datetime

from tool_logger.logger_worker import submit_json

from settings_menu.config import (
    OUTPUT_DIR,
    SETTINGS_FILE,
)

from GUI.gui_constants import (
    INVENTORY_PURCHASE,
    INVENTORY_SALE,
)

from Camera.object_tracker import (
    MIN_FRAMES,
)


# ==================================================
# Camera / Capture Settings
# ==================================================

CROP_MODE_EXPANDED = "Expanded Object (25%)"
CROP_MODE_OBJECTS = "All Objects in Counting Box"
CROP_MODE_PREVIEW = "Preview Crop Box"
CROP_MODE_FULL = "Full Image"


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


class CameraCaptureMixin:

    # ==================================================
    # Estimated Values
    # ==================================================

    def get_estimated_value(
        self,
        tool_name,
    ):

        if not tool_name:
            return 5.00

        value = self.estimated_values.get(
            str(tool_name).strip()
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

    # ==================================================
    # Metadata
    # ==================================================

    def set_metadata(
        self,
        tool=None,
        size_1=None,
        size_2=None,
        brand=None,
        measurement=None,
        drive=None,
        point=None,
        specialty_socket=None,
        invoice=None,
        ebay_id=None,
        estimated_value=None,
        number_sold=None,
        part_number=None,
        invoice_price=None,
        profit=None,
        image_date=None,
    ):

        self.tool = tool
        self.size_1 = size_1
        self.size_2 = size_2
        self.brand = brand
        self.measurement = measurement
        self.drive = drive
        self.point = point
        self.specialty_socket = (
            specialty_socket
        )

        self.invoice = (
            invoice.strip()
            if invoice
            else "DEFAULT"
        )

        self.ebay_id = (
            ebay_id.strip()
            if ebay_id
            else "None"
        )

        self.invoice_price = (
            invoice_price.strip()
            if invoice_price
            else "0"
        )

        self.part_number = (
            part_number.strip()
            if part_number
            else "NA"
        )

        self.estimated_value = (
            self.get_estimated_value(
                tool
            )
        )

        self.number_sold = number_sold
        self.profit = profit
        self.image_date = image_date

    def get_capture_output_dir(self):

        invoice = (
            self.invoice.strip()
            if self.invoice
            else "DEFAULT"
        )

        return os.path.join(
            self.output_dir,
            self.inventory_type,
            invoice,
            self.tool,
            self.brand,
        )

    def get_file_prefix(self):

        invoice = (
            self.invoice.strip()
            if self.invoice
            else "DEFAULT"
        )

        return (
            f"{invoice}_{self.tool}_{self.brand}_"
        )

    # ==================================================
    # Capture Crop Helpers
    # ==================================================

    def expanded_object_box(
        self,
        box,
        frame,
    ):

        if box is None:
            return None

        x1, y1, x2, y2 = box

        width = x2 - x1
        height = y2 - y1

        expand_x = width * 0.25
        expand_y = height * 0.25

        frame_height, frame_width = (
            frame.shape[:2]
        )

        return [
            max(
                0,
                int(x1 - expand_x),
            ),
            max(
                0,
                int(y1 - expand_y),
            ),
            min(
                frame_width,
                int(x2 + expand_x),
            ),
            min(
                frame_height,
                int(y2 + expand_y),
            ),
        ]

    def crop_from_box(
        self,
        frame,
        box,
    ):

        if (
            frame is None
            or box is None
        ):
            return None

        height, width = (
            frame.shape[:2]
        )

        x1, y1, x2, y2 = [
            int(value)
            for value in box
        ]

        x1 = max(
            0,
            min(x1, width),
        )

        x2 = max(
            0,
            min(x2, width),
        )

        y1 = max(
            0,
            min(y1, height),
        )

        y2 = max(
            0,
            min(y2, height),
        )

        if (
            x2 <= x1
            or y2 <= y1
        ):
            return None

        crop = frame[
            y1:y2,
            x1:x2,
        ].copy()

        if crop.size == 0:
            return None

        return crop

    def get_capture_crop(
        self,
        frame,
        objects,
    ):

        if self.crop_mode == CROP_MODE_FULL:
            return frame.copy()

        if self.crop_mode == CROP_MODE_PREVIEW:
            return self.crop_from_box(
                frame,
                self.crop_box,
            )

        if self.crop_mode == CROP_MODE_EXPANDED:

            for object_id, obj in objects.items():

                if obj["frames"] < MIN_FRAMES:
                    continue

                box = [
                    obj["x"],
                    obj["y"],
                    obj["x"] + obj["w"],
                    obj["y"] + obj["h"],
                ]

                if self.object_center_inside_counting_box(
                    box
                ):

                    expanded = (
                        self.expanded_object_box(
                            box,
                            frame,
                        )
                    )

                    return self.crop_from_box(
                        frame,
                        expanded,
                    )

            return None

        if self.crop_mode == CROP_MODE_OBJECTS:

            boxes = []

            for object_id, obj in objects.items():

                if obj["frames"] < MIN_FRAMES:
                    continue

                box = [
                    obj["x"],
                    obj["y"],
                    obj["x"] + obj["w"],
                    obj["y"] + obj["h"],
                ]

                if self.object_center_inside_counting_box(
                    box
                ):
                    boxes.append(box)

            if not boxes:
                return None

            x1 = min(
                box[0]
                for box in boxes
            )

            y1 = min(
                box[1]
                for box in boxes
            )

            x2 = max(
                box[2]
                for box in boxes
            )

            y2 = max(
                box[3]
                for box in boxes
            )

            return self.crop_from_box(
                frame,
                [x1, y1, x2, y2],
            )

        return None

    # ==================================================
    # Manual Snapshot
    # ==================================================

    def save_manual_snapshot(
        self,
        frame,
    ):

        if frame is None:
            return None

        output_dir = os.path.join(
            self.output_dir,
            "Manual_Captures",
        )

        os.makedirs(
            output_dir,
            exist_ok=True,
        )

        timestamp = (
            datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )

        filename = (
            f"ManualCapture_{timestamp}.jpg"
        )

        filepath = os.path.join(
            output_dir,
            filename,
        )

        if not cv2.imwrite(
            filepath,
            frame,
        ):
            return None

        print(
            f"Saved manual snapshot: {filepath}"
        )

        return filepath

    # ==================================================
    # Capture Current Counting Area
    # ==================================================

    def capture_counting_area(
        self,
        frame,
        objects,
        object_id=None,
    ):

        if (
            not self.tool
            or not self.brand
        ):

            print(
                "Tool and brand must be selected before capturing."
            )

            return None

        crop = self.get_capture_crop(
            frame,
            objects,
        )

        if crop is None:
            return None

        today = datetime.now()

        self.output_dir = os.path.abspath(
            get_output_dir()
        )

        output_dir = (
            self.get_capture_output_dir()
        )

        os.makedirs(
            output_dir,
            exist_ok=True,
        )

        crop_number = (
            self.get_next_tool_number()
        )

        if crop_number is None:
            return None

        prefix = self.get_file_prefix()

        filename = (
            f"{prefix}{crop_number:03d}_Unlogged.jpg"
        )

        filepath = os.path.join(
            output_dir,
            filename,
        )

        json_filename = (
            f"{prefix}{crop_number:03d}_Logged.json"
        )

        json_filepath = os.path.join(
            output_dir,
            json_filename,
        )

        absolute_image_path = (
            os.path.abspath(
                filepath
            )
        )

        absolute_json_path = (
            os.path.abspath(
                json_filepath
            )
        )

        metadata = {
            "Tool Name": self.tool,
            "Size-1": self.size_1,
            "Size-2": self.size_2,
            "Brand": self.brand,
            "Measurement": self.measurement,
            "Drive": self.drive,
            "Point": self.point,
            "Specialty Socket": self.specialty_socket,
            "Invoice": (
                self.invoice.strip()
                if self.invoice
                else "DEFAULT"
            ),
            "eBay ID": self.ebay_id,
            "Part Number": self.part_number,
            "Invoice Price": self.invoice_price,
            "Date": today.strftime("%Y-%m-%d"),
            "Inventory Type": self.inventory_type,
            "File Path to Image": absolute_image_path,
            "File Path to JSON": absolute_json_path,
        }

        if not cv2.imwrite(
            filepath,
            crop,
        ):
            print(
                f"ERROR: Could not save image: "
                f"{filepath}"
            )
            return None

        try:

            with open(
                json_filepath,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    metadata,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

        except OSError as error:

            print(
                f"ERROR: Could not save metadata JSON: "
                f"{error}"
            )

            return None

        session_entry = {
            "json_path": absolute_json_path,
            "image_path": absolute_image_path,
            "tool_name": self.tool,
            "brand_name": self.brand,
            "display_name": (
                f"{self.tool} / {self.brand}"
            ),
        }


        def on_logger_complete(
            future,
        ):
            try:
                success = future.result()

            except Exception as error:
                print(
                    f"ERROR: Logger completion failed: "
                    f"{error}"
                )
                return

            if not success:
                return

            self.recent_session_crops.insert(
                0,
                session_entry,
            )

            if len(
                self.recent_session_crops
            ) > 25:

                self.recent_session_crops = (
                    self.recent_session_crops[:25]
                )

            if self.recent_crops_callback:
                self.recent_crops_callback()


        submit_json(
            absolute_json_path,
            on_complete=on_logger_complete,
        )
        
        self.crop_number += 1

        self.last_capture_time = (
            cv2.getTickCount()
            / cv2.getTickFrequency()
        )

        print(
            f"Saved object: {filepath}"
        )

        return filepath

    # ==================================================
    # Crop Object
    # ==================================================

    def crop_object(
        self,
        frame,
        box,
    ):

        if frame is None:
            return None

        if self.crop_box is None:
            return None

        (
            x1,
            y1,
            x2,
            y2,
        ) = self.crop_box

        height, width = (
            frame.shape[:2]
        )

        x1 = max(
            0,
            min(
                int(x1),
                width,
            ),
        )

        x2 = max(
            0,
            min(
                int(x2),
                width,
            ),
        )

        y1 = max(
            0,
            min(
                int(y1),
                height,
            ),
        )

        y2 = max(
            0,
            min(
                int(y2),
                height,
            ),
        )

        if (
            x2 <= x1
            or y2 <= y1
        ):
            return None

        crop = frame[
            y1:y2,
            x1:x2,
        ].copy()

        if crop.size == 0:
            return None

        return crop

    # ==================================================
    # Capture Object
    # ==================================================

    def capture_object(
        self,
        frame,
        box,
    ):

        if (
            not self.tool
            or not self.brand
        ):

            print(
                "Tool and brand must be selected before capturing."
            )

            return None

        if frame is None:
            return None

        original = frame.copy()

        today = datetime.now()

        self.output_dir = os.path.abspath(
            get_output_dir()
        )

        output_dir = (
            self.get_capture_output_dir()
        )

        os.makedirs(
            output_dir,
            exist_ok=True,
        )

        crop_number = (
            self.get_next_tool_number()
        )

        if crop_number is None:
            return None

        prefix = self.get_file_prefix()

        filename = (
            f"{prefix}{crop_number:03d}_Unlogged.jpg"
        )

        filepath = os.path.join(
            output_dir,
            filename,
        )

        json_filename = (
            f"{prefix}{crop_number:03d}_Logged.json"
        )

        json_filepath = os.path.join(
            output_dir,
            json_filename,
        )

        absolute_image_path = (
            os.path.abspath(filepath)
        )

        absolute_json_path = (
            os.path.abspath(
                json_filepath
            )
        )

        metadata = {
            "Tool Name": self.tool,
            "Size-1": self.size_1,
            "Size-2": self.size_2,
            "Brand": self.brand,
            "Measurement": self.measurement,
            "Drive": self.drive,
            "Point": self.point,
            "Specialty Socket": self.specialty_socket,
            "Invoice": (
                self.invoice.strip()
                if self.invoice
                else "DEFAULT"
            ),
            "eBay ID": self.ebay_id,
            "Part Number": self.part_number,
            "Estimated Value": self.estimated_value,
            "Number Sold": self.number_sold,
            "Invoice Price": self.invoice_price,
            "Profit": self.profit,
            "Date": today.strftime("%Y-%m-%d"),
            "Inventory Type": self.inventory_type,
            "File Path to Image": absolute_image_path,
            "File Path to JSON": absolute_json_path,
        }

        if not cv2.imwrite(
            filepath,
            original,
        ):
            print(
                f"ERROR: Could not save image: "
                f"{filepath}"
            )
            return None

        try:

            with open(
                json_filepath,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    metadata,
                    file,
                    indent=4,
                    ensure_ascii=False,
                )

        except OSError as error:

            print(
                f"ERROR: Could not save metadata JSON: "
                f"{error}"
            )

            return None

        submit_json(
            absolute_json_path
        )

        self.crop_number += 1

        self.last_capture_time = (
            cv2.getTickCount()
            / cv2.getTickFrequency()
        )

        print(
            f"Saved object: {filepath}"
        )

        return filepath

    # ==================================================
    # Tool Number
    # ==================================================

    def get_next_tool_number(self):

        if (
            not self.tool
            or not self.brand
        ):
            return None

        self.output_dir = os.path.abspath(
            get_output_dir()
        )

        output_dir = (
            self.get_capture_output_dir()
        )

        os.makedirs(
            output_dir,
            exist_ok=True,
        )

        prefix = self.get_file_prefix()

        existing_files = [
            f
            for f in os.listdir(output_dir)
            if (
                f.startswith(prefix)
                and f.endswith(".jpg")
            )
        ]

        numbers = []

        for filename in existing_files:

            try:

                number_part = (
                    filename[
                        len(prefix):
                    ].split("_")[0]
                )

                numbers.append(
                    int(number_part)
                )

            except (
                ValueError,
                IndexError,
            ):
                continue

        return max(
            numbers,
            default=0,
        ) + 1