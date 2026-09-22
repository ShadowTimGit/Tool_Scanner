import multiprocessing
import tkinter as tk

from gui import ToolScannerGUI

# ==================================================
# Main
# ==================================================

if __name__ == "__main__":

    multiprocessing.freeze_support()

    root = tk.Tk()

    app = ToolScannerGUI(
        root
    )

    root.mainloop()