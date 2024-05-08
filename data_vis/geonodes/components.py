# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import math

from . import library
from . import modifier_utils
from . import panel
from .. import utils
import re

DV_COMPONENT_PROPERTY = "DV_Component"
DUPLICATE_SUFFIX_RE = re.compile(r"(\.\d+)$")


def is_chart(obj: bpy.types.Object | None) -> bool:
    if obj is None:
        return False
    return DV_COMPONENT_PROPERTY in obj


def is_chart_root(obj: bpy.types.Object | None) -> bool:
    if obj is None:
        return False
    return is_chart(obj) and obj.type == "EMPTY" and obj.parent is None


def mark_as_chart(objs: typing.Iterable[bpy.types.Object]) -> None:
    for obj in objs:
        obj[DV_COMPONENT_PROPERTY] = True


def remove_duplicate_suffix(name: str) -> str:
    return DUPLICATE_SUFFIX_RE.sub("", name)


def get_axis_on_chart(
    obj: bpy.types.Object,
) -> typing.Dict[str, typing.Optional[bpy.types.NodesModifier]]:
    ret = {"X": None, "Y": None, "Z": None}
    for mod in obj.modifiers:
        if mod.type == "NODES":
            if remove_duplicate_suffix(mod.node_group.name) == "DV_NumericAxis":
                split = mod.name.rsplit(" ", 1)
                if len(split) == 1:
                    continue

                axis = split[1]
                if axis in {"X", "Y", "Z"}:
                    ret[axis] = mod
    return ret


def get_chart_modifier(obj: bpy.types.Object) -> bpy.types.Modifier | None:
    return obj.modifiers[0] if len(obj.modifiers) > 0 else None


@utils.logging.logged_operator
class DV_AddNumericAxis(bpy.types.Operator):
    bl_idname = "data_vis.add_numeric_axis"
    bl_label = "Add Numeric Axis"
    bl_description = "Adds numeric axis modifier to the active chart"
    bl_options = {'REGISTER', 'UNDO'}

    axis: bpy.props.EnumProperty(
        name="Axis",
        items=[("X", "X", "X Axis"), ("Y", "Y", "Y Axis"), ("Z", "Z", "Z Axis")],
        description="Axis modifier will be setup based on the given direction",
    )

    pass_invoke: bpy.props.BoolProperty(options={"HIDDEN"}, default=True)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, "axis")

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Existing Axis")
        for axis, mod in self.existing_axis.items():
            if mod is None:
                continue

            col.label(text=f"[{axis}] {mod.name}")

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_chart(context.active_object)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        mod = obj.modifiers.new("Numeric Axis", type="NODES")
        mod.node_group = library.load_axis()
        mod.show_expanded = False
        # Setup the axis based on inputs, the min, max and step is calculated in the modifier
        # itself.
        if self.axis == "X":
            modifier_utils.set_input(mod, "Rotation", (0.0, 0.0, 0.0))
            modifier_utils.set_input(mod, "Offset", (0.0, -0.1, 0.0))
            modifier_utils.set_input(mod, "Range Source", 1)
            mod.name = "Numeric Axis X"
        elif self.axis == "Y":
            modifier_utils.set_input(mod, "Rotation", (0.0, 0.0, math.radians(90.0)))
            modifier_utils.set_input(mod, "Offset", (0.0, 0.1, 0.0))
            modifier_utils.set_input(mod, "Range Source", 2)
            mod.name = "Numeric Axis Y"
        elif self.axis == "Z":
            modifier_utils.set_input(mod, "Rotation", (0.0, math.radians(-90.0), 0.0))
            modifier_utils.set_input(mod, "Offset", (0.0, -0.1, 0.1))
            modifier_utils.set_input(mod, "Range Source", 3)
            mod.name = "Numeric Axis Z"
        else:
            raise ValueError(f"Unknown axis {self.axis}")

        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if self.pass_invoke:
            return self.execute(context)

        self.existing_axis = get_axis_on_chart(context.active_object)
        return context.window_manager.invoke_props_dialog(self)


@utils.logging.logged_operator
class DV_AddDataLabels(bpy.types.Operator):
    bl_idname = "data_vis.add_data_labels"
    bl_label = "Add Data Labels"
    bl_description = "Adds data labels above individual value points to active chart"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_chart(context.active_object)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        mod = obj.modifiers.new("Data Labels", type="NODES")
        mod.node_group = library.load_above_data_labels()
        return {'FINISHED'}


# TODO: Create a object that's in the middle of the axis and parented to the chart object
class DV_AddAxisLabel(bpy.types.Operator):
    bl_idname = "data_vis.add_axis_label"
    bl_label = "Add Axis Label"
    bl_options = {'REGISTER', 'UNDO'}

    # Adds a axis label to the selected chart
    def execute(self, context):
        return {'FINISHED'}


# TODO: Add heading to the chart
class DV_AddHeading(bpy.types.Operator):
    # Adds a heading to the selected chart
    bl_idname = "data_vis.add_heading"
    bl_label = "Add Heading"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}


class DV_AxisPanel(bpy.types.Panel, panel.DV_GN_PanelMixin):
    bl_idname = "DV_PT_axis_panel"
    bl_label = "Axis"

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon="ORIENTATION_VIEW")

    def draw_header_preset(self, context: bpy.types.Context):
        layout = self.layout
        layout.operator(
            DV_AddNumericAxis.bl_idname, text="", icon="ADD"
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
            modifier_utils.draw_modifier_inputs(mod, layout)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            layout.label(text="No active object")
            return

        if not is_chart(obj):
            layout.label(text="Active object is not a valid chart")
            return

        for axis, mod in get_axis_on_chart(obj).items():
            if mod is None:
                op = layout.operator(
                    DV_AddNumericAxis.bl_idname, text=f"Add {axis}", icon="ADD"
                )
                op.axis = axis
                op.pass_invoke = True
            else:
                self.draw_axis_inputs(mod, layout)


class DV_DataLabelsPanel(bpy.types.Panel, panel.DV_GN_PanelMixin):
    bl_idname = "DV_PT_data_labels_panel"
    bl_label = "Data Labels"

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon="SYNTAX_OFF")

    def draw_header_preset(self, context: bpy.types.Context):
        self.layout.operator(DV_AddDataLabels.bl_idname, text="", icon="ADD")

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        obj = context.active_object
        if obj is None:
            layout.label(text="No active object")
            return

        if not is_chart(obj):
            layout.label(text="Active object is not a valid chart")
            return

        for mod in filter(
            lambda m: m.type == "NODES"
            and remove_duplicate_suffix(m.node_group.name) == "DV_DataLabels",
            obj.modifiers,
        ):
            box = layout.box()
            row = box.row()
            # TODO: Allow removing the axis modifier from here
            row.prop(mod, "show_expanded", text="")
            row.label(text=mod.name)
            row.operator(
                modifier_utils.DV_RemoveModifier.bl_idname, text="", icon="X"
            ).modifier_name = mod.name
            if mod.show_expanded:
                modifier_utils.draw_modifier_inputs(mod, box)
