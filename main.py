import multiprocessing
import tkinter as tk

from gui import ToolScannerGUI
from performance_debug import print_perf_summary

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
    print_perf_summary()