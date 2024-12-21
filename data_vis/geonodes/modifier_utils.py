# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import logging

logger = logging.getLogger("data_vis")


class DV_RemoveModifier(bpy.types.Operator):
    bl_idname = "data_vis.remove_modifier"
    bl_label = "Remove Modifier"
    bl_description = "Removes given geometry nodes modifier from the object"
    bl_options = {"REGISTER", "UNDO"}

    modifier_name: bpy.props.StringProperty()

    def execute(self, context: bpy.types.Context):
        obj = context.active_object
        if obj is None:
            logger.warning("No object selected")
            return {"CANCELLED"}

        modifier = obj.modifiers.get(self.modifier_name, None)
        if modifier is None:
            logger.warning(
                f"Modifier {self.modifier_name} not found on object {obj.name}"
            )
            return {"CANCELLED"}

        obj.modifiers.remove(modifier)
        return {"FINISHED"}


def set_input(modifier: bpy.types.Modifier, name: str, value: typing.Any) -> None:
    if modifier.node_group is None:
        logger.warning(f"Modifier {modifier.name} has no node group")
        return

    input_ = modifier.node_group.interface.items_tree.get(name, None)
    if input_ is not None:
        modifier[input_.identifier] = value


def draw_modifier_input(
    modifier: bpy.types.Modifier,
    item: bpy.types.NodeTreeInterfaceItem,
    layout: bpy.types.UILayout,
) -> None:
    if item.bl_socket_idname in {"NodeSocketGeometry"}:
        return

    if item.bl_socket_idname == "NodeSocketObject":
        layout.prop_search(
            modifier,
            f'["{item.identifier}"]',
            bpy.data,
            "objects",
            text=item.name,
            icon="OBJECT_DATA",
        )
    elif item.bl_socket_idname == "NodeSocketMaterial":
        layout.prop_search(
            modifier,
            f'["{item.identifier}"]',
            bpy.data,
            "materials",
            text=item.name,
            icon="MATERIAL_DATA",
        )
    elif item.bl_socket_idname == "NodeSocketCollection":
        layout.prop_search(
            modifier,
            f'["{item.identifier}"]',
            bpy.data,
            "collections",
            text=item.name,
            icon="OUTLINER_COLLECTION",
        )
    else:
        layout.prop(modifier, f'["{item.identifier}"]', text=item.name)


def draw_modifier_inputs(
    modifier: bpy.types.Modifier,
    layout: bpy.types.UILayout,
) -> None:
    col = layout.column()
    col.label(text=f"{modifier.name}")
    for item in modifier.node_group.interface.items_tree:
        if item.item_type == "PANEL":
            col = layout.box()
            row = col.row()
            row.enabled = False
            row.label(text=item.name)
            continue

        if item.in_out == "INPUT":
            draw_modifier_input(modifier, item, col)
