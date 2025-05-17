# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import math

from . import library
from . import modifier_utils
from . import data
from ..utils import data_vis_logging
import re
import logging

logger = logging.getLogger("data_vis")


DV_COMPONENT_PROPERTY = "DV_Component"
DUPLICATE_SUFFIX_RE = re.compile(r"(\.\d+)$")
AXIS_NODE_GROUPS = ("DV_CategoricalAxis", "DV_NumericAxis")


class AxisType:
    NUMERIC = "Numeric"
    CATEGORICAL = "Categorical"


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
        if mod.node_group is None:
            continue

        if mod.type == "NODES":
            if remove_duplicate_suffix(mod.node_group.name) in AXIS_NODE_GROUPS:
                split = mod.name.rsplit(" ", 1)
                if len(split) == 1:
                    continue

                axis = split[1]
                if axis in {"X", "Y", "Z"}:
                    ret[axis] = mod
    return ret


def get_compatible_axis(obj: bpy.types.Object) -> typing.Dict[str, str]:
    ret = {"X": None, "Y": None, "Z": None}
    data_type = data.get_chart_data_type(obj)
    ret["Z"] = AxisType.NUMERIC
    if data.DataTypeValue.is_3d(data_type):
        ret["Y"] = AxisType.NUMERIC

    if data.DataTypeValue.is_categorical(data_type):
        ret["X"] = AxisType.CATEGORICAL
    else:
        ret["X"] = AxisType.NUMERIC

    return ret


def get_data_modifier(obj: bpy.types.Object) -> bpy.types.Modifier | None:
    return obj.modifiers[0] if len(obj.modifiers) > 0 else None


@data_vis_logging.logged_operator
class DV_AddAxis(bpy.types.Operator):
    bl_idname = "data_vis.add_axis"
    bl_label = "Add Axis"
    bl_description = "Adds axis modifier to the active chart"
    bl_options = {"REGISTER", "UNDO"}

    axis: bpy.props.EnumProperty(
        name="Axis",
        items=[("X", "X", "X Axis"), ("Y", "Y", "Y Axis"), ("Z", "Z", "Z Axis")],
        description="Axis modifier will be setup based on the given direction",
    )

    axis_type: bpy.props.EnumProperty(
        name="Axis Type",
        items=[
            (AxisType.NUMERIC, "Numeric", "Numeric Axis"),
            (AxisType.CATEGORICAL, "Categorical", "Categorical Axis"),
        ],
        description="Type of the axis",
    )

    pass_invoke: bpy.props.BoolProperty(options={"HIDDEN"}, default=True)

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        layout.prop(self, "axis")
        layout.prop(self, "axis_type")

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Existing Axis")
        for axis, mod in self.existing_axis.items():
            if mod is None:
                continue

            col.label(text=f"[{axis}] {mod.name}")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return is_chart(context.active_object)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        # TODO: Handle axis combinations (auto axis) and throw exceptions
        axis_name_prefix = f"{self.axis_type} Axis"
        mod = obj.modifiers.new(axis_name_prefix, type="NODES")
        self._load_axis_modifier(mod)
        mod.show_expanded = False
        # Setup the axis based on inputs, the min, max and step is calculated in the modifier
        # itself.
        if self.axis == "X":
            modifier_utils.set_input(mod, "Rotation", (0.0, 0.0, 0.0))
            modifier_utils.set_input(mod, "Offset", (0.0, -0.1, 0.0))
            modifier_utils.set_input(mod, "Range Source", 1)
            mod.name = f"{axis_name_prefix} X"
        elif self.axis == "Y":
            modifier_utils.set_input(mod, "Rotation", (0.0, 0.0, math.radians(90.0)))
            modifier_utils.set_input(mod, "Offset", (0.0, 0.1, 0.0))
            modifier_utils.set_input(mod, "Range Source", 2)
            mod.name = f"{axis_name_prefix} Y"
        elif self.axis == "Z":
            modifier_utils.set_input(mod, "Rotation", (0.0, math.radians(-90.0), 0.0))
            modifier_utils.set_input(mod, "Offset", (0.0, -0.1, 0.1))
            modifier_utils.set_input(mod, "Range Source", 3)
            mod.name = f"{axis_name_prefix} Z"
        else:
            raise ValueError(f"Unknown axis {self.axis}")

        if self.axis_type == AxisType.CATEGORICAL:
            self._setup_categorical_axis(obj, mod)

        self._try_set_axis_ranges(obj, mod)
        self._add_labels_if_available(obj, mod)

        modifier_utils.add_used_materials_to_object(mod, obj)
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if self.pass_invoke:
            return self.execute(context)

        self.existing_axis = get_axis_on_chart(context.active_object)
        return context.window_manager.invoke_props_dialog(self)

    def _load_axis_modifier(self, mod: bpy.types.NodesModifier) -> None:
        if self.axis_type == AxisType.NUMERIC:
            mod.node_group = library.load_numeric_axis()
        elif self.axis_type == AxisType.CATEGORICAL:
            mod.node_group = library.load_categorical_axis()
        else:
            raise ValueError(f"Unknown axis type {self.axis_type}")

    def _setup_categorical_axis(
        self, obj: bpy.types.Object, mod: bpy.types.NodesModifier
    ) -> None:
        assert is_chart(obj)
        data_from_obj = data.get_chart_data_info(obj)
        if data_from_obj is None:
            logger.error(f"No data found on the chart {obj.name}")
            return

        modifier_utils.set_input(mod, "Tick Count", len(data_from_obj["categories"]))
        modifier_utils.set_input(mod, "Labels", ",".join(data_from_obj["categories"]))

    def _add_labels_if_available(
        self, obj: bpy.types.Object, mod: bpy.types.NodesModifier
    ) -> None:
        assert is_chart(obj)
        data_from_obj = data.get_chart_data_info(obj)
        if data_from_obj is None:
            logger.error(f"No data found on the chart {obj.name}")
            return

        axis_labels = data_from_obj["axis_labels"]
        if len(axis_labels) == 0:
            return
        if self.axis == "X" and len(axis_labels) > 0:
            modifier_utils.set_input(mod, "Axis Label Text", axis_labels[0])

        if self.axis == "Y" and len(axis_labels) > 1:
            modifier_utils.set_input(mod, "Axis Label Text", axis_labels[1])

        if self.axis == "Z" and len(axis_labels) == 2:
            modifier_utils.set_input(mod, "Axis Label Text", axis_labels[1])
        elif len(axis_labels) == 3:
            modifier_utils.set_input(mod, "Axis Label Text", axis_labels[2])

    def _try_set_axis_ranges(
        self, obj: bpy.types.Object, mod: bpy.types.NodesModifier
    ) -> None:
        assert is_chart(obj)
        data_from_obj = data.get_chart_data_info(obj)
        if data_from_obj is None:
            logger.error(f"No data found on the chart {obj.name}")
            return

        min_ = data_from_obj["min"]
        max_ = data_from_obj["max"]

        if self.axis == "X":
            modifier_utils.set_input(mod, "Min", float(min_[0]))
            modifier_utils.set_input(mod, "Max", float(max_[0]))
        elif self.axis == "Y":
            modifier_utils.set_input(mod, "Min", float(min_[1]))
            modifier_utils.set_input(mod, "Max", float(max_[1]))
        elif self.axis == "Z":
            modifier_utils.set_input(mod, "Min", float(min_[2]))
            modifier_utils.set_input(mod, "Max", float(max_[2]))


@data_vis_logging.logged_operator
class DV_AddDataLabels(bpy.types.Operator):
    bl_idname = "data_vis.add_data_labels"
    bl_label = "Add Data Labels"
    bl_description = "Adds data labels above individual value points to active chart"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_chart(context.active_object)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        mod = obj.modifiers.new("Data Labels", type="NODES")
        mod.node_group = library.load_above_data_labels()
        modifier_utils.add_used_materials_to_object(mod, obj)
        return {"FINISHED"}
