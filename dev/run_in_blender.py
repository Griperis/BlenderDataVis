import subprocess
import argparse
import sys
import shutil
import os


def find_blender_executable() -> str:
    POSSIBLE_PATHS = [
        shutil.which("blender"),
        "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe",
    ]

    for path in POSSIBLE_PATHS:
        if path is not None and os.path.isfile(path):
            return path

    raise RuntimeError("Blender executable not found.")


def run_in_blender(script_path: str, blender_executable: str) -> int:
    if "--" in sys.argv:
        additional_args = sys.argv[sys.argv.index("--") + 1 :]
    else:
        additional_args = []
    args = []
    args += [blender_executable]
    args += ["--background"]
    args += ["-noaudio"]
    args += ["--python-exit-code", "1"]
    args += ["--factory-startup"]
    args += ["--python", script_path]
    args += ["--"]
    args += additional_args
    p = subprocess.Popen(args)
    p.wait()
    return p.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--script_path", type=str, help="Path to the Blender script to run"
    )
    parser.add_argument(
        "--blender", type=str, default=None, help="Path to the Blender executable"
    )
    args, _ = parser.parse_known_args(sys.argv)
    blender = args.blender if args.blender else find_blender_executable()
    sys.exit(run_in_blender(os.path.abspath(args.script_path), blender))


if __name__ == "__main__":
    main()
