import json
import threading
import urllib.request


GITHUB_API_URL = (
    "https://api.github.com/repos/"
    "ShadowTimGit/Tool_Scanner/releases/latest"
)


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
        request = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                "Accept": (
                    "application/vnd.github+json"
                ),
                "User-Agent": "ToolScanner",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=5,
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
            )

    except Exception:
        pass


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