# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import logging
from ..utils import data_vis_logging

logger = logging.getLogger("data_vis")


@data_vis_logging.logged_operator
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


def get_input(modifier: bpy.types.NodesModifier, name: str) -> typing.Any | None:
    if modifier.node_group is None:
        logger.warning(f"Modifier {modifier.name} has no node group")
        return None

    input_ = modifier.node_group.interface.items_tree.get(name, None)
    if input_ is not None:
        return modifier[input_.identifier]
    return None


def animate_input(
    modifier: bpy.types.NodesModifier,
    name: str,
    start: tuple[int, typing.Any],
    end: tuple[int, typing.Any],
):
    if start[0] >= end[0]:
        raise ValueError("Start frame must be before the end frame")

    if modifier.node_group is None:
        logger.warning(f"Modifier {modifier.name} has no node group")
        return

    input_ = modifier.node_group.interface.items_tree.get(name, None)
    if input_ is not None:
        modifier[input_.identifier] = start[1]
        modifier.keyframe_insert(f'["{input_.identifier}"]', frame=start[0])
        modifier[input_.identifier] = end[1]
        modifier.keyframe_insert(f'["{input_.identifier}"]', frame=end[0])


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


def _get_geometry_nodes_used_materials(
    modifier: bpy.types.Modifier,
) -> typing.Set[bpy.types.Material]:
    materials = set()

    # Iterate through all inputs and find material ones
    if modifier.node_group:
        for item in modifier.node_group.interface.items_tree:
            if item.item_type == "PANEL":
                continue

            if item.in_out != "INPUT":
                continue

            if item.bl_socket_idname == "NodeSocketMaterial":
                material = modifier[item.identifier]
                if material:
                    materials.add(material)

        # Iterate through all nodes recursively and find material nodes
        def find_material_nodes(node_tree):
            for node in node_tree.nodes:
                if hasattr(node, "inputs"):
                    for input in node.inputs:
                        if input.bl_idname == "NodeSocketMaterial":
                            if input.default_value:
                                materials.add(input.default_value)
                if hasattr(node, "node_tree") and node.node_tree:
                    find_material_nodes(node.node_tree)

        find_material_nodes(modifier.node_group)

    return materials


def add_used_materials_to_object(
    modifier: bpy.types.Modifier,
    obj: bpy.types.Object,
) -> None:
    materials = _get_geometry_nodes_used_materials(modifier)
    for material in materials:
        if material.name not in obj.data.materials:
            obj.data.materials.append(material)
