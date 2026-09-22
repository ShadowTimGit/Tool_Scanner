import os
import shutil
import subprocess
import sys
import time
import zipfile


def wait_for_process(
    process_id,
):
    while True:
        try:
            os.kill(
                process_id,
                0,
            )

            time.sleep(0.5)

        except OSError:
            break


def find_source_directory(
    extract_dir,
):
    entries = os.listdir(
        extract_dir
    )

    directories = [
        entry
        for entry in entries
        if os.path.isdir(
            os.path.join(
                extract_dir,
                entry,
            )
        )
    ]

    if len(directories) == 1:
        return os.path.join(
            extract_dir,
            directories[0],
        )

    return extract_dir


def copy_directory_contents(
    source_dir,
    destination_dir,
):
    for name in os.listdir(
        source_dir
    ):
        source_path = os.path.join(
            source_dir,
            name,
        )

        destination_path = os.path.join(
            destination_dir,
            name,
        )

        if name == ".git":
            continue

        if name == ".venv":
            continue

        if os.path.isdir(
            source_path
        ):
            shutil.copytree(
                source_path,
                destination_path,
                dirs_exist_ok=True,
            )

        else:
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
        print(
            "Waiting for Object Scanner to close..."
        )

        wait_for_process(
            process_id
        )

        print(
            "Extracting update..."
        )

        os.makedirs(
            extract_dir,
            exist_ok=True,
        )

        with zipfile.ZipFile(
            zip_path,
            "r",
        ) as zip_file:
            zip_file.extractall(
                extract_dir
            )

        source_dir = find_source_directory(
            extract_dir
        )

        print(
            "Installing update..."
        )

        copy_directory_contents(
            source_dir,
            project_dir,
        )

        print(
            "Starting Object Scanner..."
        )

        restart_application(
            project_dir
        )

    except Exception as e:
        print(
            f"Update installation failed: {e}"
        )


def main():
    if len(sys.argv) != 4:
        return

    process_id = int(
        sys.argv[1]
    )

    zip_path = sys.argv[2]

    project_dir = sys.argv[3]

    perform_update(
        process_id,
        zip_path,
        project_dir,
    )


if __name__ == "__main__":
    main()