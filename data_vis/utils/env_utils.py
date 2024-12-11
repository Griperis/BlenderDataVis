# ©copyright Zdenek Dolezal 2024-, License GPL

import os
import sys
import bpy
import importlib
import typing
import threading
import subprocess
import logging

logger = logging.getLogger("data_vis")


MODULES_FOLDER = "site-packages"


def get_python_path():
    if bpy.app.version >= (2, 91, 0):
        return sys.executable
    else:
        return bpy.app.binary_path_python


def get_modules_path():
    return os.path.realpath(os.path.abspath(os.path.join(__file__, "..", "..", MODULES_FOLDER)))


def ensure_module_path_in_sys_path():
    modules_path = get_modules_path()
    if modules_path not in sys.path:
        sys.path.append(modules_path)


def ensure_python_module(module_name: str):
    ensure_module_path_in_sys_path()
    if is_module_installed(module_name):
        return

    python_path = get_python_path()
    command = [
        str(python_path),
        "-m",
        "pip",
        "install",
        module_name,
        "--target",
        get_modules_path(),
    ]
    logger.info(f"Running command '{command}'")
    subprocess.run(command)
    logger.info(f"Finished running command '{command}'")


def ensure_python_modules(module_names: typing.List[str]):
    for module_name in module_names:
        ensure_python_module(module_name)


def ensure_python_modules_new_thread(module_names: typing.List[str]):
    thread = threading.Thread(target=ensure_python_modules, args=(module_names,))
    thread.start()


def is_module_installed(module_name: str):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False
