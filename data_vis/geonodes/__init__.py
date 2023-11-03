import bpy
from .bar_chart import DV_GN_BarChart
from .data import DV_DataProperties

CLASSES = [
    DV_DataProperties,
    DV_GN_BarChart
]

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)