import bpy
import os


def install_addon(filepath: str, module_name: str):
    """
    Installs the Blender addon from the given filepath.

    :param filepath: Path to the addon file.
    """
    bpy.ops.preferences.addon_install(filepath=filepath)
    bpy.ops.preferences.addon_enable(module=module_name)
    bpy.ops.wm.save_userpref()


def uninstall_addon(module_name: str):
    """
    Uninstalls the Blender addon with the given module name.

    :param module_name: Name of the addon module.
    """

    bpy.ops.preferences.addon_disable(module=module_name)
    # TODO: This throws AttributeError from within the operator implementation
    # bpy.ops.preferences.addon_remove(module=module_name)
    bpy.ops.wm.save_userpref()


class InstalledAddon:
    """
    Context manager that installs the Blender addon from the given filepath
    and uninstalls it on exit.

    :param filepath: Path to the addon file.
    """

    def __init__(self, filepath: str, module_name: str):
        self.filepath = filepath
        self.module_name = module_name

    def __enter__(self):
        install_addon(self.filepath, self.module_name)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        uninstall_addon(self.module_name)
