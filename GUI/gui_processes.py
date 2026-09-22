import multiprocessing
import subprocess
import sys


# def run_image_analyzer():
#     try:
#         from image_analyzer_DEPRECATED import process_directory

#         process_directory()

#     except Exception as error:
#         print("IMAGE ANALYZER ERROR:")
#         print(error)
#         raise


class ProcessMixin:

    # def start_analyzer(self):
    #     self.stop_analyzer()

    #     self.analyzer_process = multiprocessing.Process(
    #         target=run_image_analyzer,
    #         name="ImageAnalyzer",
    #         daemon=True,
    #     )

    #     self.analyzer_process.start()

    #     print(
    #         "Image analyzer started."
    #     )

    #     self.status_label.config(
    #         text="Image analyzer running..."
    #     )

    #     self.analyze_button.config(
    #         text="Restart Analyzer"
    #     )

    # def stop_analyzer(self):
    #     if (
    #         self.analyzer_process is None
    #         or not self.analyzer_process.is_alive()
    #     ):
    #         return

    #     print(
    #         "Stopping image analyzer..."
    #     )

    #     self.analyzer_process.terminate()

    #     self.analyzer_process.join(
    #         timeout=2
    #     )

    #     if self.analyzer_process.is_alive():
    #         self.analyzer_process.kill()
    #         self.analyzer_process.join()

    # def check_analyzer(self):
    #     if not self.running:
    #         return

    #     process = self.analyzer_process

    #     if process is not None:
    #         if process.is_alive():
    #             self.analyze_button.config(
    #                 text="Restart Analyzer"
    #             )

    #         else:
    #             exit_code = process.exitcode

    #             if exit_code == 0:
    #                 self.status_label.config(
    #                     text="Image analysis complete."
    #                 )

    #                 print(
    #                     "Image analyzer completed."
    #                 )

    #             else:
    #                 self.status_label.config(
    #                     text=(
    #                         "Image analyzer stopped. "
    #                         "Click Restart Analyzer to retry."
    #                     )
    #                 )

    #                 print(
    #                     "Image analyzer stopped. "
    #                     f"Exit code: {exit_code}"
    #                 )

    #             self.analyze_button.config(
    #                 text="Analyze Images"
    #             )

    #             self.analyzer_process = None

    #     self.root.after(
    #         500,
    #         self.check_analyzer,
    #     )

    def run_logger(self):
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "logger.py",
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.stdout:
                print(
                    result.stdout,
                    end="",
                )

            if result.stderr:
                print(
                    result.stderr,
                    end="",
                )

            if result.returncode == 0:
                self.status_label.config(
                    text="Logger finished."
                )

                print(
                    "Logger finished successfully."
                )

            else:
                self.status_label.config(
                    text=(
                        "Logger failed. "
                        f"Exit code: {result.returncode}"
                    )
                )

                print(
                    "Logger failed. "
                    f"Exit code: {result.returncode}"
                )

        except subprocess.TimeoutExpired:
            self.status_label.config(
                text="Logger timed out."
            )

            print(
                "Logger timed out."
            )

        except Exception as error:
            self.status_label.config(
                text="Logger error."
            )

            print(
                f"Failed to run logger: {error}"
            )