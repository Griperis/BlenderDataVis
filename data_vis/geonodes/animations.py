import bpy

class DV_AddInAnimation(bpy.types.Operator):
    # Adds one of effect (grow, ...) as a first shape key, keyframes it
    ...


class DV_AddOutAnimation(bpy.types.Operator):
    # Adds one of effects (shrink, ...) as a last shape key, keyframes it
    ...


class DV_AnimateData(bpy.types.Operator):
    # Keyframes the data shape keys
    ...