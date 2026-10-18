import json
import os
import shutil
import sys
import tempfile
import threading
import urllib.request
import zipfile


GITHUB_API_URL = (
    "https://api.github.com/repos/"
    "ShadowTimGit/Tool_Scanner/releases/latest"
)

# Temporary testing only.
#
# Once the repository is public, set this to None.
#
# Do NOT commit a real token to GitHub.


def check_for_updates(
    current_version,
    callback,
):
    thread = threading.Thread(
        target=_check_for_updates,
        args=(
            current_version,
            callback,
        ),
        daemon=True,
    )

    thread.start()


def _check_for_updates(
    current_version,
    callback,
):
    try:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ToolScanner",
        }

        request = urllib.request.Request(
            GITHUB_API_URL,
            headers=headers,
        )

        with urllib.request.urlopen(
            request,
            timeout=10,
        ) as response:
            data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

        latest_version = (
            data["tag_name"]
            .lstrip("v")
        )

        print(f"Current version: {current_version}")
        print(f"Latest GitHub version: {latest_version}")

        if is_newer_version(
            latest_version,
            current_version,
        ):
            print("Update available!")

            callback(
                latest_version,
                data["html_url"],
                data["zipball_url"],
            )
        else:
            print("Already running the latest version.")

    except Exception as e:
        print(
            f"Update check failed: {e}"
        )



def download_update(zip_url, callback):
    import tempfile
    import threading
    import urllib.request
    import traceback

    def worker():
        temp_dir = None

        try:
            print("[UPDATER] Starting download...", flush=True)
            print(f"[UPDATER] URL: {zip_url}", flush=True)

            temp_dir = tempfile.mkdtemp(
                prefix="object_scanner_update_"
            )
            zip_path = os.path.join(
                temp_dir,
                "update.zip",
            )

            request = urllib.request.Request(
                zip_url,
                headers={
                    "User-Agent": "ObjectScanner-Updater"
                },
            )

            print("[UPDATER] Opening download URL...", flush=True)

            with urllib.request.urlopen(
                request,
                timeout=60,
            ) as response:
                total = int(
                    response.headers.get(
                        "Content-Length", 0
                    )
                )
                downloaded = 0

                with open(zip_path, "wb") as file:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break

                        file.write(chunk)
                        downloaded += len(chunk)

                        if total:
                            print(
                                f"[UPDATER] Downloaded "
                                f"{downloaded}/{total} bytes",
                                flush=True,
                            )

            print(
                f"[UPDATER] Download complete: {zip_path}",
                flush=True,
            )

            if not zipfile.is_zipfile(zip_path):
                raise RuntimeError(
                    "Downloaded file is not a valid ZIP archive."
                )

            print("[UPDATER] Calling download callback...", flush=True)
            callback(temp_dir, zip_path)

        except Exception as e:
            print(
                f"[UPDATER] Download failed: {e}",
                flush=True,
            )
            traceback.print_exc()

    threading.Thread(
        target=worker,
        daemon=True,
    ).start()



def _download_update(
    zip_url,
    callback,
):
    try:
        temp_dir = tempfile.mkdtemp(
            prefix="tool_scanner_update_"
        )

        zip_path = os.path.join(
            temp_dir,
            "update.zip",
        )

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ToolScanner",
        }

        request = urllib.request.Request(
            zip_url,
            headers=headers,
        )

        with urllib.request.urlopen(
            request,
            timeout=60,
        ) as response:
            with open(
                zip_path,
                "wb",
            ) as file:
                shutil.copyfileobj(
                    response,
                    file,
                )

        callback(
            temp_dir,
            zip_path,
        )

    except Exception as e:
        print(
            f"Update download failed: {e}"
        )


def start_update(
    zip_path,
    project_dir,
):
    try:
        helper_source = os.path.join(
            project_dir,
            "update_helper.py",
        )

        if not os.path.exists(
            helper_source
        ):
            raise FileNotFoundError(
                "update_helper.py was not found."
            )

        import subprocess

        subprocess.Popen(
            [
                sys.executable,
                helper_source,
                str(os.getpid()),
                zip_path,
                project_dir,
            ],
            cwd=project_dir,
        )

        return True

    except Exception as e:
        print(
            f"Failed to start updater: {e}"
        )

        return False


def is_newer_version(
    latest,
    current,
):
    try:
        latest_parts = tuple(
            int(part)
            for part in latest.split(".")
        )

        current_parts = tuple(
            int(part)
            for part in current.split(".")
        )

        return latest_parts > current_parts

    except (
        ValueError,
        TypeError,
    ):
        return False

