import bpy
from data_vis import preferences


class DV_GN_PanelMixin:
    bl_parent_id = "DV_PT_data_load"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DataVis"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return preferences.get_preferences(context).addon_mode == "GEONODES"
