import os

DEFAULT_VIDEO_SOURCE = 0

OUTPUT_DIR = "Output/Images"

# LOG_DIR = os.path.join(OUTPUT_DIR, "Logs")

# DOCUMENTS_DIR = (
#     Path.home()
#     / "Documents"
#     / "ToolLogger"
# )

# OUTPUT_DIR = str(
#     DOCUMENTS_DIR
#     / "Output"
#     / "Images"
#     / "Inventory"
# )

# LOG_DIR = str(
#     DOCUMENTS_DIR
#     / "Output"
#     / "Logs"
# )

# SETTINGS_FILE = str(
#     DOCUMENTS_DIR
#     / "Settings"
#     / "settings.json"
# )

MIN_RED_PERCENT = 5.0

DEFAULT_CAMERA_WIDTH = 30

DEFAULT_CAMERA_HEIGHT = 30

# Minimum detection confidence
CONFIDENCE = 0.50

# Model to start with
MODEL = "yolo11s.pt"

# ==================================================
# Default Scan Dot Settings
# ==================================================

DEFAULT_SCAN_WIDTH = 25
DEFAULT_SCAN_HEIGHT = 25
DEFAULT_HEIGHT_DISPLACEMENT = 25

# ==================================================
# Default Scan Box Settings
# ==================================================

DEFAULT_BOX_X = 300
DEFAULT_BOX_Y = 25

DEFAULT_BOX_WIDTH = 50
DEFAULT_BOX_HEIGHT = 50

DEFAULT_BOX = (
    DEFAULT_BOX_X,
    DEFAULT_BOX_Y,
    DEFAULT_BOX_X + DEFAULT_BOX_WIDTH,
    DEFAULT_BOX_Y + DEFAULT_BOX_HEIGHT,
)

# ==================================================
# Default Preview Crop Settings
# ==================================================

DEFAULT_CROP_X = 25
DEFAULT_CROP_Y = 75

DEFAULT_CROP_WIDTH = 500
DEFAULT_CROP_HEIGHT = 250

DEFAULT_CROP = (
    DEFAULT_CROP_X,
    DEFAULT_CROP_Y,
    DEFAULT_CROP_X + DEFAULT_CROP_WIDTH,
    DEFAULT_CROP_Y + DEFAULT_CROP_HEIGHT,
)

DEFAULT_SIZE = "None"
# ==================================================
# Saved User Settings
# ==================================================

# The scan box and preview crop box positions/sizes
# adjusted with the mouse are stored here.
#
# Example:
#
# settings.json
#
# {
#     "scan_box": {
#         "x": 300,
#         "y": 25,
#         "width": 50,
#         "height": 50
#     },
#     "crop_box": {
#         "x": 25,
#         "y": 75,
#         "width": 500,
#         "height": 250
#     }
# }

SETTINGS_FILE = "settings_menu/settings/settings.json"