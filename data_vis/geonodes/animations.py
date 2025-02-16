# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
from . import data
from . import components
from . import modifier_utils


class AnimationNames:
    GROW_FROM_ZERO = "IN: Grow-from-zero"
    GROW_TO_ZERO = "OUT: Grow-to-zero"

    IN_ANIMATIONS = {GROW_FROM_ZERO}
    OUT_ANIMATIONS = {GROW_TO_ZERO}


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


def is_in_present(obj: bpy.types.Object) -> bool:
    return (
        len(
            AnimationNames.IN_ANIMATIONS
            & set(kb.name for kb in obj.data.shape_keys.key_blocks)
        )
        > 0
    )


def is_out_present(obj: bpy.types.Object) -> bool:
    return (
        len(
            AnimationNames.OUT_ANIMATIONS
            & set(kb.name for kb in obj.data.shape_keys.key_blocks)
        )
        > 0
    )


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


class DV_AnimationOperator(bpy.types.Operator):
    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.active_object is None or not components.is_chart(
            context.active_object
        ):
            return False

        return data.DataTypeValue.is_animated(data.get_chart_data_type(context.object))


class DV_AddInAnimation(DV_AnimationOperator):
    bl_idname = "data_vis.animate_in"
    bl_label = "Add In Animation"

    type_: bpy.props.EnumProperty(
        name="Animation Type",
        items=((AnimationNames.GROW_FROM_ZERO, "Grow", "Grow from zero"),),
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not super().poll(context):
            return False

        return get_action(context.active_object) is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if is_in_present(obj):
            self.report({"WARNING"}, "In animation already present, remove it first.")
            return {"CANCELLED"}

        # Infer the keyframe spacing from the existing keyframes, if they exist
        action = get_action(obj)
        keyframe_xs = [x.co[0] for x in action.fcurves[0].keyframe_points]
        if len(keyframe_xs) > 2:
            frame_spacing = keyframe_xs[2] - keyframe_xs[1]
        else:
            frame_spacing = 20

        frame_n = context.scene.frame_current
        if frame_n - frame_spacing <= 0:
            self.report(
                {"ERROR"},
                f"There is no space for in animation, please adjust the keyframes.",
            )
            return {"CANCELLED"}

        sk = obj.shape_key_add(name=self.type_, from_mix=True)
        sk.value = 0
        if self.type_ == AnimationNames.GROW_FROM_ZERO:
            for data in sk.data:
                data.co = (data.co[0], data.co[1], 0)
        else:
            raise RuntimeError(f"Unknown animation type '{self.type_}'")

        sk.value = 1
        sk.keyframe_insert(data_path="value", frame=frame_n - frame_spacing)
        for sk_other in obj.data.shape_keys.key_blocks:
            if sk_other != sk:
                sk_other.value = 0
                sk_other.keyframe_insert(
                    data_path="value", frame=frame_n - frame_spacing
                )

            sk.value = 0
            sk.keyframe_insert(data_path="value", frame=frame_n)

        ensure_animation_naming(obj)
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)


class DV_AddOutAnimation(DV_AnimationOperator):
    bl_idname = "data_vis.animate_out"
    bl_label = "Add Out Animation"

    type_: bpy.props.EnumProperty(
        name="Animation Type",
        items=((AnimationNames.GROW_TO_ZERO, "Shrink", "Shrink to zero"),),
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if not super().poll(context):
            return False

        return get_action(context.active_object) is not None

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if is_out_present(context.active_object):
            self.report(
                {"WARNING"}, "Out animation is already present, remove it first."
            )
            return {"CANCELLED"}

        # Infer the keyframe spacing and last keyframe from the existing keyframes, if they exist
        action = get_action(obj)
        keyframe_xs = [x.co[0] for x in action.fcurves[0].keyframe_points]

        sk = obj.shape_key_add(name=self.type_, from_mix=True)
        sk.value = 0

        if self.type_ == AnimationNames.GROW_TO_ZERO:
            for data in sk.data:
                data.co = (data.co[0], data.co[1], 0)
        else:
            raise RuntimeError(f"Unknown animation type '{self.type_}'")

        frame_n = (
            keyframe_xs[-1] if len(keyframe_xs) > 0 else context.scene.frame_current
        )
        sk.value = 0
        sk.keyframe_insert(data_path="value", frame=frame_n)
        for sk_other in obj.data.shape_keys.key_blocks:
            if sk_other != sk:
                sk_other.value = 0
                sk_other.keyframe_insert(data_path="value", frame=frame_n)

        if len(keyframe_xs) > 2:
            frame_spacing = keyframe_xs[-1] - keyframe_xs[-2]
            sk.value = 1
            sk.keyframe_insert(data_path="value", frame=frame_n + frame_spacing)

        ensure_animation_naming(obj)
        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)


class DV_RemoveInOutAnimation(DV_AnimationOperator):
    bl_idname = "data_vis.remove_in_out"
    bl_label = "Remove In/Out Animation"

    in_out: bpy.props.BoolProperty(default=True)

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        to_remove = (
            AnimationNames.IN_ANIMATIONS
            if self.in_out
            else AnimationNames.OUT_ANIMATIONS
        )
        for sk in obj.data.shape_keys.key_blocks:
            if sk.name in to_remove:
                obj.shape_key_remove(sk)

        return {"FINISHED"}


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


class DV_AnimateAxis(DV_AnimationOperator):
    bl_idname = "data_vis.animate_axis"
    bl_label = "Animate Axis"
    bl_description = "Animates selected axis of the chart"

    target_mod: bpy.props.StringProperty(
        name="Target Modifier",
        description="Name of the modifier to animate",
    )

    animation_type: bpy.props.EnumProperty(
        name="Animation Type",
        description="How the axis will be animated",
        items=(
            ("GROW", "Grow", "Grow the axis"),
            ("MOVE_IN", "Move In", "Move the axis in"),
        ),
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

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.active_object is not None and components.is_chart(
            context.active_object
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "animation_type")
        layout.prop(self, "animation_style")
        layout.prop(self, "reverse")
        layout.prop(self, "frames")

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

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)
