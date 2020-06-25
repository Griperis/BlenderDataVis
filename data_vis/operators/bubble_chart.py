# File: bubble_chart.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Bubble chart implementation

import bpy

from data_vis.general import OBJECT_OT_GenericChart
from data_vis.properties import DV_AxisPropertyGroup, DV_ColorPropertyGroup, DV_HeaderPropertyGroup, DV_LabelPropertyGroup
from data_vis.colors import ColoringFactory
from data_vis.operators.features.axis import AxisFactory
from data_vis.data_manager import DataManager, DataType


class OBJECT_OT_BubbleChart(OBJECT_OT_GenericChart):
    '''Creates Bubble Chart'''
    bl_idname = 'object.create_bubble_chart'
    bl_label = 'Bubble Chart'
    bl_options = {'REGISTER', 'UNDO'}

    dimensions: bpy.props.EnumProperty(
        name='Dimensions',
        items=(
            ('3', '3D', 'X, Y, Z'),
            ('2', '2D', 'X, Z'),
        )
    )

    color_settings: bpy.props.PointerProperty(
        type=DV_ColorPropertyGroup
    )

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup
    )

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup

    )

    header_settings: bpy.props.PointerProperty(
        type=DV_HeaderPropertyGroup
    )

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return dm.is_type(DataType.Numerical, 4)

    def draw(self, context):
        super().draw(context)

    def execute(self, context):
        self.init_data()
        self.create_container()

        print(self.dm)
        for i, entry in enumerate(self.data):
            if not self.in_axis_range_bounds_new(entry):
                continue

        return {'FINISHED'}
