import json
import os

from config import (
    DEFAULT_BOX,
    DEFAULT_CROP,
    DEFAULT_CAMERA_WIDTH,
    DEFAULT_CAMERA_HEIGHT,
    SETTINGS_FILE,
)


# ==================================================
# Camera Resolution
# ==================================================

SUPPORTED_RESOLUTIONS = [
    (320, 240),
    (640, 480),
    (800, 600),
    (1024, 576),
    (1280, 720),
    (1920, 1080),
]


# ==================================================
# Interactive Box Settings
# ==================================================

MIN_BOX_WIDTH = 20
MIN_BOX_HEIGHT = 20


class CameraSettings:

    def __init__(self):

        self.camera_width = (
            DEFAULT_CAMERA_WIDTH
        )

        self.camera_height = (
            DEFAULT_CAMERA_HEIGHT
        )

        self.scan_box = None

        self.crop_box = list(
            DEFAULT_CROP
        )

        # -------------------------
        # Counting box
        # -------------------------

        self.counting_box = list(
            DEFAULT_CROP
        )

        self.load()


    # ==================================================
    # Load
    # ==================================================

    def load(self):

        self.load_camera_resolution()
        self.load_boxes()


    # ==================================================
    # Load Camera Resolution
    # ==================================================

    def load_camera_resolution(self):

        if not os.path.exists(
            SETTINGS_FILE
        ):
            return

        try:

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:

                settings = json.load(file)

            resolution = settings.get(
                "camera_resolution"
            )

            if not isinstance(
                resolution,
                dict,
            ):
                return

            width = int(
                resolution.get(
                    "width",
                    DEFAULT_CAMERA_WIDTH,
                )
            )

            height = int(
                resolution.get(
                    "height",
                    DEFAULT_CAMERA_HEIGHT,
                )
            )

            if (
                width,
                height,
            ) in SUPPORTED_RESOLUTIONS:

                self.camera_width = width
                self.camera_height = height

            else:

                print(
                    f"Unsupported saved camera "
                    f"resolution: "
                    f"{width}x{height}. "
                    f"Using default."
                )

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):

            print(
                f"Could not load camera resolution "
                f"from {SETTINGS_FILE}. "
                f"Using default."
            )


    # ==================================================
    # Load Boxes
    # ==================================================

    def load_boxes(self):

        self.scan_box = None

        self.crop_box = list(
            DEFAULT_CROP
        )

        # -------------------------
        # Default counting box
        # -------------------------

        self.counting_box = list(
            DEFAULT_CROP
        )

        if not os.path.exists(
            SETTINGS_FILE
        ):
            return

        try:

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8",
            ) as file:

                settings = json.load(file)

            # -------------------------
            # Scan box
            # -------------------------

            scan_settings = settings.get(
                "scan_box"
            )

            if scan_settings:

                x = int(
                    scan_settings.get(
                        "x",
                        DEFAULT_BOX[0],
                    )
                )

                y = int(
                    scan_settings.get(
                        "y",
                        DEFAULT_BOX[1],
                    )
                )

                width = int(
                    scan_settings.get(
                        "width",
                        DEFAULT_BOX[2]
                        - DEFAULT_BOX[0],
                    )
                )

                height = int(
                    scan_settings.get(
                        "height",
                        DEFAULT_BOX[3]
                        - DEFAULT_BOX[1],
                    )
                )

                self.scan_box = [
                    x,
                    y,
                    x + width,
                    y + height,
                ]

            # -------------------------
            # Crop box
            # -------------------------

            crop_settings = settings.get(
                "crop_box"
            )

            if crop_settings:

                x = int(
                    crop_settings.get(
                        "x",
                        DEFAULT_CROP[0],
                    )
                )

                y = int(
                    crop_settings.get(
                        "y",
                        DEFAULT_CROP[1],
                    )
                )

                width = int(
                    crop_settings.get(
                        "width",
                        DEFAULT_CROP[2]
                        - DEFAULT_CROP[0],
                    )
                )

                height = int(
                    crop_settings.get(
                        "height",
                        DEFAULT_CROP[3]
                        - DEFAULT_CROP[1],
                    )
                )

                self.crop_box = [
                    x,
                    y,
                    x + width,
                    y + height,
                ]

            # -------------------------
            # Counting box
            # -------------------------

            counting_settings = settings.get(
                "counting_box"
            )

            if counting_settings:

                x = int(
                    counting_settings.get(
                        "x",
                        DEFAULT_CROP[0],
                    )
                )

                y = int(
                    counting_settings.get(
                        "y",
                        DEFAULT_CROP[1],
                    )
                )

                width = int(
                    counting_settings.get(
                        "width",
                        DEFAULT_CROP[2]
                        - DEFAULT_CROP[0],
                    )
                )

                height = int(
                    counting_settings.get(
                        "height",
                        DEFAULT_CROP[3]
                        - DEFAULT_CROP[1],
                    )
                )

                self.counting_box = [
                    x,
                    y,
                    x + width,
                    y + height,
                ]

        except (
            OSError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ):

            print(
                f"Could not load settings from "
                f"{SETTINGS_FILE}. "
                f"Using default settings."
            )

            self.scan_box = None

            self.crop_box = list(
                DEFAULT_CROP
            )

            self.counting_box = list(
                DEFAULT_CROP
            )


    # ==================================================
    # Save
    # ==================================================

    def save(self):

        settings = {}

        if os.path.exists(
            SETTINGS_FILE
        ):

            try:

                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8",
                ) as file:

                    existing_settings = (
                        json.load(file)
                    )

                if isinstance(
                    existing_settings,
                    dict,
                ):

                    settings = (
                        existing_settings
                    )

            except (
                OSError,
                ValueError,
                TypeError,
                json.JSONDecodeError,
            ):

                settings = {}

        # -------------------------
        # Scan box
        # -------------------------

        if self.scan_box is not None:

            settings["scan_box"] = {
                "x": self.scan_box[0],
                "y": self.scan_box[1],
                "width": (
                    self.scan_box[2]
                    - self.scan_box[0]
                ),
                "height": (
                    self.scan_box[3]
                    - self.scan_box[1]
                ),
            }

        # -------------------------
        # Crop box
        # -------------------------

        settings["crop_box"] = {
            "x": self.crop_box[0],
            "y": self.crop_box[1],
            "width": (
                self.crop_box[2]
                - self.crop_box[0]
            ),
            "height": (
                self.crop_box[3]
                - self.crop_box[1]
            ),
        }

        # -------------------------
        # Counting box
        # -------------------------

        if self.counting_box is not None:

            settings["counting_box"] = {
                "x": self.counting_box[0],
                "y": self.counting_box[1],
                "width": (
                    self.counting_box[2]
                    - self.counting_box[0]
                ),
                "height": (
                    self.counting_box[3]
                    - self.counting_box[1]
                ),
            }

        # -------------------------
        # Camera resolution
        # -------------------------

        settings["camera_resolution"] = {
            "width": self.camera_width,
            "height": self.camera_height,
        }

        try:

            with open(
                SETTINGS_FILE,
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    settings,
                    file,
                    indent=4,
                )

        except OSError as error:

            print(
                f"Could not save settings: "
                f"{error}"
            )


    # ==================================================
    # Clamp Box
    # ==================================================

    def clamp_box(
        self,
        box,
        frame_width,
        frame_height,
    ):

        if box is None:
            return None

        x1, y1, x2, y2 = box

        box_width = max(
            MIN_BOX_WIDTH,
            x2 - x1,
        )

        box_height = max(
            MIN_BOX_HEIGHT,
            y2 - y1,
        )

        box_width = min(
            box_width,
            frame_width,
        )

        box_height = min(
            box_height,
            frame_height,
        )

        x1 = max(
            0,
            min(
                x1,
                frame_width - box_width,
            ),
        )

        y1 = max(
            0,
            min(
                y1,
                frame_height - box_height,
            ),
        )

        x2 = x1 + box_width
        y2 = y1 + box_height

        return [
            int(x1),
            int(y1),
            int(x2),
            int(y2),
        ]