# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
from . import data
from . import components
from . import modifier_utils
from . import library
from ..utils import data_vis_logging


def is_column_sk(sk: bpy.types.ShapeKey) -> bool:
    return sk.name.startswith("Column: ")


def get_action(obj: bpy.types.Object) -> bpy.types.Action | None:
    if (
        not components.is_chart(obj)
        or obj.data.shape_keys is None
        or obj.data.shape_keys.animation_data is None
        or obj.data.shape_keys.animation_data.action is None
    ):
        return None

    return obj.data.shape_keys.animation_data.action


def ensure_animation_naming(obj: bpy.types.Object):
    if not components.is_chart(obj) or get_action(obj) is None:
        return

    # This should be called only if the animation data already exist
    obj.data.shape_keys.animation_data.action.name = "DV_Action"


def get_shape_keys_z_range(
    obj: bpy.types.Object, start_idx: int = 0, end_idx: int = 6942042
) -> tuple[float, float]:
    min_z = float("inf")
    max_z = float("-inf")

    start_idx = max(0, start_idx)
    end_idx = min(len(obj.data.shape_keys.key_blocks) - 1, end_idx)

    key_blocks = obj.data.shape_keys.key_blocks
    for i in range(start_idx, end_idx + 1):
        sk = key_blocks[i]
        if sk != obj.data.shape_keys.reference_key:
            for v in sk.data:
                min_z = min(v.co.z, min_z)
                max_z = max(v.co.z, max_z)

    return min_z, max_z


def adjust_z_override_to_data(obj: bpy.types.Object, start_idx: int, end_idx: int):
    min_z, max_z = get_shape_keys_z_range(obj, start_idx, end_idx)
    chart_modiifer = components.get_chart_modifier(obj)
    modifier_utils.set_input(chart_modiifer, "Override Z Range", True)
    modifier_utils.set_input(chart_modiifer, "Z Min", min_z)
    modifier_utils.set_input(chart_modiifer, "Z Max", max_z)


@data_vis_logging.logged_operator
class DV_AnimationOperator(bpy.types.Operator):
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.active_object is None or not components.is_chart(
            context.active_object
        ):
            return False

        return data.DataTypeValue.is_animated(data.get_chart_data_type(context.object))


@data_vis_logging.logged_operator
class DV_AnimateData(DV_AnimationOperator):
    bl_idname = "data_vis.animate_data"
    bl_label = "Animate Data"
    bl_description = (
        "Animates the chart. The chart has to be created with animation support"
    )

    keyframe_spacing: bpy.props.IntProperty(name="Keyframe Spacing", default=20, min=1)

    start_idx: bpy.props.IntProperty(name="Start Index", default=0, min=0)

    end_idx: bpy.props.IntProperty(name="End Index", default=5, min=0)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "keyframe_spacing")
        layout.separator()
        row = layout.row(align=True)
        row.prop(self, "start_idx")
        row.prop(self, "end_idx")

        col = layout.column(align=True)
        col.label(text=f"From column {self.start_idx} to {self.end_idx}")
        col.label(text=f"Spaced at {self.keyframe_spacing} frames")
        col.label(text=f"Starting at frame {context.scene.frame_current}")

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        frame_n = context.scene.frame_current
        start_idx = max(0, self.start_idx)
        end_idx = min(self.end_idx, len(obj.data.shape_keys.key_blocks) - 1)
        self.report(
            {"INFO"},
            f"Animating data from column {start_idx} to {end_idx} spaced at {self.keyframe_spacing} frames",
        )
        for i in range(start_idx, end_idx + 1):
            sk = obj.data.shape_keys.key_blocks[i]
            if not is_column_sk(sk):
                continue

            # Set current shape key to active by using the value and disable others
            sk.value = 1
            sk.keyframe_insert(data_path="value", frame=frame_n)
            frame_n += self.keyframe_spacing
            for sko in obj.data.shape_keys.key_blocks:
                if sko != sk:
                    sko.value = 0
                    sko.keyframe_insert(data_path="value", frame=frame_n)

        adjust_z_override_to_data(obj, 0, len(obj.data.shape_keys.key_blocks) - 1)
        ensure_animation_naming(obj)

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)


# Animation types:
# - general - allow reversing the animation
# Axis:
# - animate axis geometry (grow, scale, move in, ...)
# - animate axis labels (fade in, fade out, ...)
# - animate step
# Above data labels:
# - popup above data labels (by index?)
# - grow from 0 to data value?
# Data animation:
# - scale in data points, popup data points by index, ...
# - geometry nodes modifier creating the animation (only one allowed?)
# - keyframed animate property of the geonodes modifier
# TODO: Header, Chart Labels, Legend animation - popup, fade in, fade out, ...


class DV_AnimateModifierOperator(DV_AnimationOperator):
    target_mod: bpy.props.StringProperty(
        name="Target Modifier",
        description="Name of the modifier to animate",
    )

    # This field is overriden by the subclasses and specific animations
    animation_type: bpy.props.EnumProperty(
        name="Animation Type",
        description="How the component will be animated",
    )

    animation_style: bpy.props.EnumProperty(
        name="Interpolation",
        description="Defines the animation style, choose the interpolation type",
        items=(
            ("LINEAR", "Linear", "Linear interpolation"),
            ("CUBIC", "Cubic", "Cubic interpolation"),
            ("BOUNCE", "Bounce", "Bounce interpolation"),
        ),
    )

    reverse: bpy.props.BoolProperty(
        name="Reverse", description="Reverse the animation", default=False
    )

    frames: bpy.props.IntProperty(
        name="Duration",
        description="Duration of the animation in frames",
        min=1,
        default=20,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "animation_type")
        layout.prop(self, "animation_style")
        layout.prop(self, "reverse")
        layout.prop(self, "frames")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None and components.is_chart(
            context.active_object
        )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def _animate(
        self,
        context: bpy.types.Context,
        modifier: bpy.types.NodesModifier,
        current_animation: dict,
    ) -> None:
        start_frame = context.scene.frame_current
        end_frame = start_frame + self.frames

        for input_name, (start_value, end_value) in current_animation.items():
            if self.reverse:
                start_value, end_value = end_value, start_value

            modifier_utils.animate_input(
                modifier, input_name, (start_frame, start_value), (end_frame, end_value)
            )

        for fcurve in context.active_object.animation_data.action.fcurves:
            for input_name in current_animation:
                if fcurve.data_path.startswith(f'modifiers["{modifier.name}"]'):
                    fcurve.keyframe_points[0].interpolation = self.animation_style


@data_vis_logging.logged_operator
class DV_AnimateAxis(DV_AnimationOperator):
    bl_idname = "data_vis.animate_axis"
    bl_label = "Animate Axis"
    bl_description = "Animates selected axis of the chart"

    animation_type: bpy.props.EnumProperty(
        name="Animation Type",
        description="How the axis will be animated",
        items=(
            ("GROW", "Grow", "Grow the axis"),
            ("MOVE_IN", "Move In", "Move the axis in"),
        ),
    )

    def execute(self, context: bpy.types.Context):
        modifier = context.active_object.modifiers.get(self.target_mod, None)
        if modifier is None:
            raise ValueError(f"Modifier {self.target_mod} not found")

        ANIMATION_PROPERTIES_MAP = {
            "GROW": {
                "Length": [0.0, 1.0],
                "Thickness": [0.0, 0.1],
                "Label Size": [0.0, 0.05],
            },
            "MOVE_IN": {
                "Offset": [
                    (-5.0, -5.0, -5.0),
                    tuple(modifier_utils.get_input(modifier, "Offset")),
                ]
            },
        }

        current_animation = ANIMATION_PROPERTIES_MAP[self.animation_type]
        self._animate(context, modifier, current_animation)
        return {"FINISHED"}


@data_vis_logging.logged_operator
class DV_AnimateAboveDataLabels(DV_AnimateModifierOperator):
    bl_idname = "data_vis.animate_above_data_labels"
    bl_label = "Animate Labels"
    bl_description = "Animates above data labels of the chart"

    animation_type: bpy.props.EnumProperty(
        name="Animation Type",
        description="How the labels will be animated",
        items=(("SCALE", "Scale", "Scale the labels"),),
    )

    def execute(self, context: bpy.types.Context):
        modifier = context.active_object.modifiers.get(self.target_mod, None)
        if modifier is None:
            raise ValueError(f"Modifier {self.target_mod} not found")

        ANIMATION_PROPERTIES_MAP = {
            "SCALE": {
                "Labels Scale": [0.0, 0.05],
            },
        }

        current_animation = ANIMATION_PROPERTIES_MAP[self.animation_type]
        self._animate(context, modifier, current_animation)
        return {"FINISHED"}


@data_vis_logging.logged_operator
class DV_AddDataTransitionAnimation(DV_AnimateModifierOperator):
    bl_idname = "data_vis.data_effect_animation"
    bl_label = "Data Effect Animation"
    bl_description = "Adds animated effect to the chart"

    animation_type: bpy.props.EnumProperty(
        name="Animation Type",
        description="How the data effect will be animated",
        items=(
            ("EXPLODE", "Explode", "Explode the data points"),
            ("GROW", "Grow", "Grow the data points"),
            ("GROW_BY_INDEX", "Grow by index", "Grow the data points by index"),
            ("POPUP_BY_INDEX", "Popup by index", "Popup the data points by index"),
        ),
    )

    def execute(self, context: bpy.types.Context):
        ENUM_MOD_MAP = {
            "EXPLODE": "Explode",
            "GROW": "Grow",
            "GROW_BY_INDEX": "GrowByIndex",
            "POPUP_BY_INDEX": "PopupByIndex",
        }

        # Remove existing modifiers
        for modifier in list(context.active_object.modifiers):
            if modifier.type != "NODES":
                continue

            if modifier.node_group is None:
                continue

            if components.remove_duplicate_suffix(modifier.name).endswith(
                tuple(ENUM_MOD_MAP.values())
            ):
                context.active_object.modifiers.remove(modifier)

        node_group = library.load_data_animation(ENUM_MOD_MAP[self.animation_type])
        modifier: bpy.types.NodesModifier = context.active_object.modifiers.new(
            f"Data {ENUM_MOD_MAP[self.animation_type]}", type="NODES"
        )
        modifier.node_group = node_group

        idx = context.active_object.modifiers.find(modifier.name)
        context.active_object.modifiers.move(idx, 1)

        self._animate(context, modifier, {"Animate": [0.0, 1.0]})
        return {"FINISHED"}
