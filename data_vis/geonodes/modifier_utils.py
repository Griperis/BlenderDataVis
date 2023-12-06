import bpy
import typing


def set_input(modifier: bpy.types.Modifier, name: str, value: typing.Any) -> None:
    input_ = modifier.node_group.interface.items_tree.get(name, None)
    if input_ is not None:
        modifier[input_.identifier] = value


def draw_modifier_inputs(
    modifier: bpy.types.Modifier,
    layout: bpy.types.UILayout,
    template: typing.Optional[typing.Dict[str, str]] = None
) -> None:
    col = layout.column()
    col.label(text=f"{modifier.name}")
    for item in modifier.node_group.interface.items_tree:
        if item.item_type == 'PANEL':
            col = layout.column()
            col.label(text=item.name)
            continue

        if item.in_out == 'INPUT':
            col.prop(modifier, f'["{item.identifier}"]', text=item.name)

    # TODO: Use the template :)
