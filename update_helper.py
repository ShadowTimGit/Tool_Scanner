import os
import shutil
import subprocess
import sys
import time
import zipfile


def log(message):
    print(
        f"[UPDATE HELPER] {message}",
        flush=True,
    )


def wait_for_process(
    process_id,
):
    log(
        f"Waiting for process {process_id}..."
    )

    try:
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        SYNCHRONIZE = 0x00100000

        kernel32 = ctypes.windll.kernel32

        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION
            | SYNCHRONIZE,
            False,
            process_id,
        )

        if not handle:
            log(
                "Process is already closed."
            )
            return

        INFINITE = 0xFFFFFFFF

        result = kernel32.WaitForSingleObject(
            handle,
            INFINITE,
        )

        kernel32.CloseHandle(
            handle
        )

        if result == 0:
            log(
                "Object Scanner has closed."
            )
        else:
            raise RuntimeError(
                f"WaitForSingleObject failed: "
                f"{result}"
            )

    except Exception as e:
        log(
            f"Process wait failed: {e}"
        )
        raise

def find_source_directory(extract_dir):
    for root, dirs, files in os.walk(extract_dir):
        dirs[:] = [
            d for d in dirs
            if d not in (".git", ".venv", "__pycache__")
        ]

        if "main.py" in files:
            log(f"Found application source: {root}")
            return root

    raise FileNotFoundError(
        f"Could not find main.py in extracted ZIP: {extract_dir}"
    )


def copy_directory_contents(
    source_dir,
    destination_dir,
):
    log(
        f"Copying files from:\n"
        f"{source_dir}\n"
        f"to:\n"
        f"{destination_dir}"
    )

    for name in os.listdir(
        source_dir
    ):
        if name in (
            ".git",
            ".venv",
        ):
            log(
                f"Skipping: {name}"
            )

            continue

        source_path = os.path.join(
            source_dir,
            name,
        )

        destination_path = os.path.join(
            destination_dir,
            name,
        )

        if os.path.isdir(
            source_path
        ):
            log(
                f"Copying directory: {name}"
            )

            shutil.copytree(
                source_path,
                destination_path,
                dirs_exist_ok=True,
            )

        else:
            log(
                f"Copying file: {name}"
            )

            shutil.copy2(
                source_path,
                destination_path,
            )


def restart_application(
    project_dir,
):
    main_path = os.path.join(
        project_dir,
        "main.py",
    )

    log(
        f"Restarting: {main_path}"
    )

    log(f"Python executable: {sys.executable}")
    log(f"Working directory: {project_dir}")
    log(f"main.py exists: {os.path.isfile(main_path)}")

    subprocess.Popen(
        [
            sys.executable,
            main_path,
        ],
        cwd=project_dir,
    )


def perform_update(
    process_id,
    zip_path,
    project_dir,
):
    extract_dir = os.path.join(
        os.path.dirname(zip_path),
        "extracted",
    )

    try:
        log("Updater started.")

        log(
            f"Process ID: {process_id}"
        )

        log(
            f"ZIP: {zip_path}"
        )

        log(
            f"Project directory: {project_dir}"
        )

        if not os.path.exists(
            zip_path
        ):
            raise FileNotFoundError(
                f"ZIP does not exist: {zip_path}"
            )

        wait_for_process(
            process_id
        )

        log(
            f"Creating extraction directory: "
            f"{extract_dir}"
        )

        os.makedirs(
            extract_dir,
            exist_ok=True,
        )

        log("Extracting ZIP...")

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as zip_file:
            zip_file.extractall(
                extract_dir
            )

        log("ZIP extracted.")

        source_dir = find_source_directory(
            extract_dir
        )

        log(
            f"Source directory: {source_dir}"
        )

        copy_directory_contents(
            source_dir,
            project_dir,
        )

        log("Update files copied.")

        if not os.path.isfile(
            os.path.join(project_dir, "main.py")
        ):
            raise FileNotFoundError(
                "main.py is missing from the project directory."
            )

        log("Verified main.py exists.")

        restart_application(
            project_dir
        )

        log(
            "Update completed successfully."
        )

    except Exception as e:
        log(
            f"UPDATE FAILED: {e}"
        )

        input(
            "Press Enter to close..."
        )


def main():
    log(
        f"Arguments: {sys.argv}"
    )

    if len(sys.argv) != 4:
        log(
            "Invalid arguments."
        )

        input(
            "Press Enter to close..."
        )

        return

    try:
        process_id = int(
            sys.argv[1]
        )

    except ValueError:
        log(
            "Invalid process ID."
        )

        input(
            "Press Enter to close..."
        )

        return

    zip_path = sys.argv[2]

    project_dir = sys.argv[3]

    perform_update(
        process_id,
        zip_path,
        project_dir,
    )


if __name__ == "__main__":
    main()