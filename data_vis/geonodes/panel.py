# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
from . import modifier_utils
from . import components
from . import animations
from .. import preferences
from ..icon_manager import IconManager


class DV_GN_PanelMixin:
    bl_parent_id = "DV_PT_data_load"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DataVis"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return preferences.get_preferences(context).addon_mode == "GEONODES"


class DV_ChartPanel(bpy.types.Panel, DV_GN_PanelMixin):
    bl_idname = "DV_PT_chart_panel"
    bl_label = "Chart"

    @classmethod
    def poll(self, context: bpy.types.Context):
        return components.is_chart(context.active_object)

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon_value=IconManager().get_icon_id("addon_icon"))

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            layout.label(text="No active object")
            return

        if not components.is_chart(obj):
            layout.label(text="Active object is not a valid chart")
            return

        for mod in filter(
            lambda m: m.type == "NODES"
            and components.remove_duplicate_suffix(m.node_group.name) == "DV_Data",
            obj.modifiers,
        ):
            box = layout.box()
            row = box.row()
            row.prop(mod, "show_expanded", text="")
            row.label(text=mod.name)
            row.operator(
                modifier_utils.DV_RemoveModifier.bl_idname, text="", icon="X"
            ).modifier_name = mod.name
            if mod.show_expanded:
                modifier_utils.draw_modifier_inputs(mod, box)

        for mod in filter(
            lambda m: m.type == "NODES"
            and components.remove_duplicate_suffix(m.node_group.name).startswith("DV_")
            and components.remove_duplicate_suffix(m.node_group.name).endswith("Chart"),
            obj.modifiers,
        ):
            box = layout.box()
            row = box.row()
            row.prop(mod, "show_expanded", text="")
            row.label(text=mod.name)
            row.operator(
                modifier_utils.DV_RemoveModifier.bl_idname, text="", icon="X"
            ).modifier_name = mod.name
            if mod.show_expanded:
                modifier_utils.draw_modifier_inputs(mod, box)


class DV_AxisPanel(bpy.types.Panel, DV_GN_PanelMixin):
    bl_idname = "DV_PT_axis_panel"
    bl_label = "Axis"

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon="ORIENTATION_VIEW")

    def draw_header_preset(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(
            components.DV_AddAxis.bl_idname, text="", icon="ADD"
        ).pass_invoke = False

    def draw_axis_inputs(
        self, mod: bpy.types.NodesModifier, layout: bpy.types.UILayout
    ) -> None:
        box = layout.box()
        row = box.row()
        row.prop(mod, "show_expanded", text="")
        row.label(text=mod.name)
        row.operator(
            modifier_utils.DV_RemoveModifier.bl_idname, text="", icon="X"
        ).modifier_name = mod.name
        if mod.show_expanded:
            modifier_utils.draw_modifier_inputs(mod, box)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            layout.label(text="No active object")
            return

        if not components.is_chart(obj):
            layout.label(text="Active object is not a valid chart")
            return

        compatible_axis = components.get_compatible_axis(obj)
        for axis, mod in components.get_axis_on_chart(obj).items():
            if mod is None:
                axis_type = compatible_axis.get(axis, None)
                if axis_type is not None:
                    op = layout.operator(
                        components.DV_AddAxis.bl_idname,
                        text=f"Add {axis} ({axis_type})",
                        icon="ADD",
                    )
                    op.axis = axis
                    op.axis_type = compatible_axis[axis]
                    op.pass_invoke = True
            else:
                self.draw_axis_inputs(mod, layout)


class DV_DataLabelsPanel(bpy.types.Panel, DV_GN_PanelMixin):
    bl_idname = "DV_PT_data_labels_panel"
    bl_label = "Data Labels"

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon="SYNTAX_OFF")

    def draw_header_preset(self, context: bpy.types.Context):
        self.layout.operator(components.DV_AddDataLabels.bl_idname, text="", icon="ADD")

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object
        if obj is None:
            layout.label(text="No active object")
            return

        if not components.is_chart(obj):
            layout.label(text="Active object is not a valid chart")
            return

        for mod in filter(
            lambda m: m.type == "NODES"
            and components.remove_duplicate_suffix(m.node_group.name)
            == "DV_DataLabels",
            obj.modifiers,
        ):
            box = layout.box()
            row = box.row()
            row.prop(mod, "show_expanded", text="")
            row.label(text=mod.name)
            row.operator(
                modifier_utils.DV_RemoveModifier.bl_idname, text="", icon="X"
            ).modifier_name = mod.name
            if mod.show_expanded:
                modifier_utils.draw_modifier_inputs(mod, box)


class DV_AnimatePanel(bpy.types.Panel, DV_GN_PanelMixin):
    bl_idname = "DV_PT_animate_panel"
    bl_label = "Animation"

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon="ORIENTATION_VIEW")

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.operator(animations.DV_AnimateData.bl_idname, text="Animate")

        row = layout.row(align=True)
        row.operator(animations.DV_AddInAnimation.bl_idname, text="In Animation")
        row.operator(
            animations.DV_RemoveInOutAnimation.bl_idname, text="", icon="X"
        ).in_out = True

        row = layout.row(align=True)
        row.operator(animations.DV_AddOutAnimation.bl_idname, text="Out Animation")
        row.operator(
            animations.DV_RemoveInOutAnimation.bl_idname, text="", icon="X"
        ).in_out = False
