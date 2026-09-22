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
GITHUB_TOKEN="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"


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
            "Accept": (
                "application/vnd.github+json"
            ),
            "User-Agent": "ToolScanner",
        }

        if GITHUB_TOKEN:
            headers["Authorization"] = (
                f"Bearer {GITHUB_TOKEN}"
            )

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

        if is_newer_version(
            latest_version,
            current_version,
        ):
            callback(
                latest_version,
                data["html_url"],
                data["zipball_url"],
            )

    except Exception as e:
        print(
            f"Update check failed: {e}"
        )


def download_update(
    zip_url,
    callback,
):
    thread = threading.Thread(
        target=_download_update,
        args=(
            zip_url,
            callback,
        ),
        daemon=True,
    )

    thread.start()


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
            "Accept": (
                "application/vnd.github+json"
            ),
            "User-Agent": "ToolScanner",
        }

        if GITHUB_TOKEN:
            headers["Authorization"] = (
                f"Bearer {GITHUB_TOKEN}"
            )

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

        helper_dir = tempfile.mkdtemp(
            prefix="tool_scanner_helper_"
        )

        helper_path = os.path.join(
            helper_dir,
            "update_helper.py",
        )

        shutil.copy2(
            helper_source,
            helper_path,
        )

        import subprocess

        subprocess.Popen(
            [
                sys.executable,
                helper_path,
                str(os.getpid()),
                zip_path,
                project_dir,
            ],
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            ),
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

