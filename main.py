import multiprocessing
import sys

from PySide6.QtWidgets import QApplication

from GUI.gui import ToolScannerGUI



# ==================================================
# Main
# ==================================================

if __name__ == "__main__":

    multiprocessing.freeze_support()

    app = QApplication(sys.argv)

    window = ToolScannerGUI()

    window.show()

    exit_code = app.exec()

    sys.exit(exit_code)