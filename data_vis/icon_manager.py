# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import os


class IconManager:
    class __IconManager:
        def __init__(self):
            self.preview_collections = {}

        def load_icons(self):
            """Loads pngs from icons folder into preview_collections['main']"""
            pcoll = bpy.utils.previews.new()

            icons_dir = os.path.join(os.path.dirname(__file__), "icons")
            for icon in os.listdir(icons_dir):
                name, ext = icon.split(".")
                if ext == "png":
                    pcoll.load(name, os.path.join(icons_dir, icon), "IMAGE")

            self.preview_collections["main"] = pcoll

        def remove_icons(self):
            for pcoll in self.preview_collections.values():
                bpy.utils.previews.remove(pcoll)
            self.preview_collections.clear()

        def get_icon(self, name, coll="main"):
            return self.preview_collections[coll][name]

        def get_icon_id(self, name, coll="main"):
            return self.preview_collections[coll][name].icon_id

    instance = None

    def __new__(cls):
        if not IconManager.instance:
            IconManager.instance = IconManager.__IconManager()
        return IconManager.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
