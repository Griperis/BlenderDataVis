import os
import shutil
import zipfile
import re
import argparse

BUILDS_FOLDER = "../builds"


def remove_unwanted_dirs(folder: str, unwanted_dir_names: list[str]):
    for root, dir_names, files in os.walk(folder):
        for dir_name in dir_names:
            if dir_name in unwanted_dir_names:
                print(f"Removing '{dir_name}'")
                shutil.rmtree(os.path.join(root, dir_name))


def update_version_in_file(file_path: str, pattern: str, replacement: str):
    with open(file_path, "r") as file:
        content = file.read()
    content = re.sub(pattern, replacement, content)
    with open(file_path, "w") as file:
        file.write(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", type=str, help="The version of the addon.", required=True
    )
    parser.add_argument(
        "--addon_package", type=str, help="The name of the addon folder.", required=True
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        help="The folder to save the release zip.",
        required=False,
        default=".",
    )
    args = parser.parse_args()
    version = args.version
    addon_package = args.addon_package
    output_folder = os.path.abspath(args.output_folder)

    if os.path.exists(f"{BUILDS_FOLDER}/{addon_package}"):
        shutil.rmtree(f"{BUILDS_FOLDER}/{addon_package}")
    os.makedirs(f"{BUILDS_FOLDER}/{addon_package}")

    shutil.copytree(
        addon_package, f"{BUILDS_FOLDER}/{addon_package}", dirs_exist_ok=True
    )
    shutil.copy(
        f"{addon_package}/blender_manifest.toml", f"{BUILDS_FOLDER}/{addon_package}"
    )

    remove_unwanted_dirs(
        f"{BUILDS_FOLDER}/{addon_package}", ["__pycache__", "site-packages"]
    )

    init_file = f"{BUILDS_FOLDER}/{addon_package}/__init__.py"
    manifest_file = f"{BUILDS_FOLDER}/{addon_package}/blender_manifest.toml"

    version_tuple = tuple(map(int, version.split(".")))
    update_version_in_file(
        init_file, r"'version': \([0-9], [0-9], [0-9]\)", f"'version': {version_tuple}"
    )
    update_version_in_file(
        manifest_file,
        r'\bversion\b = "[0-9]+\.[0-9]+\.[0-9]+"',
        f'version = "{version}"',
    )

    zip_file = os.path.join(output_folder, f"{addon_package}_{version}.zip")
    if os.path.exists(zip_file):
        os.remove(zip_file)

    with zipfile.ZipFile(zip_file, "w") as zipf:
        for root, dirs, files in os.walk(f"{BUILDS_FOLDER}/{addon_package}"):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.join(
                        addon_package,
                        os.path.relpath(
                            os.path.join(root, file),
                            f"{BUILDS_FOLDER}/{addon_package}",
                        ),
                    ),
                )

    print(f"Release zip saved at '{zip_file}'")


if __name__ == "__main__":
    main()
