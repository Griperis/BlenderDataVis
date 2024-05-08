# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import logging

logger = logging.getLogger("data_vis")


class DV_RemoveModifier(bpy.types.Operator):
    bl_idname = "data_vis.remove_modifier"
    bl_label = "Remove Modifier"
    bl_description = "Removes given geometry nodes modifier from the object"
    bl_options = {'REGISTER', 'UNDO'}

    modifier_name: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            logger.warning("No object selected")
            return {'CANCELLED'}

        modifier = obj.modifiers.get(self.modifier_name, None)
        if modifier is None:
            logger.warning(
                f"Modifier {self.modifier_name} not found on object {obj.name}"
            )
            return {'CANCELLED'}

        obj.modifiers.remove(modifier)
        return {'FINISHED'}


def set_input(modifier: bpy.types.Modifier, name: str, value: typing.Any) -> None:
    if modifier.node_group is None:
        logger.warning(f"Modifier {modifier.name} has no node group")
        return

    input_ = modifier.node_group.interface.items_tree.get(name, None)
    if input_ is not None:
        modifier[input_.identifier] = value


def draw_modifier_inputs(
    modifier: bpy.types.Modifier,
    layout: bpy.types.UILayout,
    template: typing.Optional[typing.Dict[str, str]] = None,
) -> None:
    col = layout.column()
    col.label(text=f"{modifier.name}")
    for item in modifier.node_group.interface.items_tree:
        if item.item_type == "PANEL":
            col = layout.column()
            col.label(text=item.name)
            continue

        if item.in_out == "INPUT":
            if item.bl_socket_idname in {"NodeSocketGeometry"}:
                continue
            col.prop(modifier, f'["{item.identifier}"]', text=item.name)

    # TODO: Use the template :)
