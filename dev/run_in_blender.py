import subprocess
import argparse
import sys
import shutil
import os


def find_blender_executable() -> str:
    POSSIBLE_PATHS = [
        shutil.which("blender"),
        "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe",
    ]

    for path in POSSIBLE_PATHS:
        if path is not None and os.path.isfile(path):
            return path

    raise RuntimeError("Blender executable not found.")


def run_in_blender(script_path: str) -> int:
    p = subprocess.Popen(
        [
            find_blender_executable(),
            "--background",
            "-noaudio",
            "--factory-startup",
            "--python-exit-code",
            "1",
            "--python",
            script_path,
            "--",
            *sys.argv[sys.argv.index("--") + 1 :],
        ]
    )
    p.wait()
    return p.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--script_path", type=str, help="Path to the Blender script to run"
    )
    args, _ = parser.parse_known_args(sys.argv)
    sys.exit(run_in_blender(args.script_path))


if __name__ == "__main__":
    main()
