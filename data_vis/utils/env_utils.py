# File: env_utils.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Python environment utilities

import os
import sys
import bpy
import importlib
import typing
import threading
import subprocess


MODULES_FOLDER = 'site-packages'


def get_python_path():
    if bpy.app.version >= (2, 91, 0):
        return sys.executable
    else:
        return bpy.app.binary_path_python


def get_modules_path():
    return os.path.realpath(
        os.path.join(
            bpy.utils.script_path_user(),
            'addons',
            'data_vis', 
            MODULES_FOLDER
        )
    )


def ensure_module_path_in_sys_path():
    modules_path = get_modules_path()
    if modules_path not in sys.path:
        sys.path.append(modules_path)


def ensure_python_module(module_name: str):
    ensure_module_path_in_sys_path()
    if is_module_installed(module_name):
        return

    python_path = get_python_path()
    command = [str(python_path), '-m', 'pip', 'install', module_name, '--target', get_modules_path()]
    print(f'Running command \'{command}\'', file=sys.stderr)
    subprocess.run(command)
    print(f'Finished running command \'{command}\'', file=sys.stderr)


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