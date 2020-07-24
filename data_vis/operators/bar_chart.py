# File: bar_chart.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Bar chart implementation

import bpy
import math
from mathutils import Vector


from data_vis.utils.data_utils import normalize_value
from data_vis.general import OBJECT_OT_GenericChart
from data_vis.properties import DV_LabelPropertyGroup, DV_ColorPropertyGroup, DV_AxisPropertyGroup, DV_AnimationPropertyGroup, DV_HeaderPropertyGroup
from data_vis.operators.features.axis import AxisFactory
from data_vis.data_manager import DataManager, DataType
from data_vis.colors import ColoringFactory, ColorType


class OBJECT_OT_BarChart(OBJECT_OT_GenericChart):
    '''Creates Bar Chart, supports 2D and 3D Numerical Data and 2D categorical data with or w/o labels'''
    bl_idname = 'object.create_bar_chart'
    bl_label = 'Bar Chart'
    bl_options = {'REGISTER', 'UNDO'}

    dimensions: bpy.props.EnumProperty(
        name='Dimensions',
        items=(
            ('3', '3D', 'X, Y, Z'),
            ('2', '2D', 'X, Z'),
        )
    )

    data_type: bpy.props.EnumProperty(
        name='Chart type',
        items=(
            ('0', 'Numerical', 'X, [Y] relative to Z'),
            ('1', 'Categorical', 'Label and value'),
        ),
    )

    bar_size: bpy.props.FloatVectorProperty(
        name='Bar size',
        size=2,
        default=(0.05, 0.05)
    )

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup
    )

    color_settings: bpy.props.PointerProperty(
        type=DV_ColorPropertyGroup
    )

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup
    )

    anim_settings: bpy.props.PointerProperty(
        type=DV_AnimationPropertyGroup
    )

    header_settings: bpy.props.PointerProperty(
        type=DV_HeaderPropertyGroup
    )

    use_obj: bpy.props.EnumProperty(
        name='Object',
        items=(
            ('Bar', 'Bar', 'Scaled cube'),
            ('Cylinder', 'Cylinder', 'Scaled cylinder'),
            ('Custom', 'Custom', 'Select custom object'),
        )
    )

    custom_obj_name: bpy.props.StringProperty(
        name='Custom'
    )

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return dm.is_type(DataType.Numerical, [2, 3]) or dm.is_type(DataType.Categorical, [2])

    def init_props(self):
        if self.dm.is_type(DataType.Categorical, [2]):
            size = 1 / (2 * len(self.dm.get_parsed_data()) + 1)
            if size <= 0.05:
                self.bar_size[0] = size

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        box = layout.box()
        box.prop(self, 'use_obj')
        if self.use_obj == 'Custom':
            box.prop_search(self, 'custom_obj_name', context.scene, 'objects')

        row = box.row()
        row.prop(self, 'bar_size')

    def execute(self, context):
        self.init_data()

        tick_labels = []

        if self.dm.predicted_data_type == DataType.Categorical and self.data_type_as_enum() == DataType.Numerical:
            self.report({'ERROR'}, 'Cannot convert categorical data into numerical!')
            return {'CANCELLED'}

        self.dm.override(self.data_type_as_enum(), int(self.dimensions))

        self.create_container()
        color_factory = ColoringFactory(self.get_name(), self.color_settings.color_shade, ColorType.str_to_type(self.color_settings.color_type), self.color_settings.use_shader)
        color_gen = color_factory.create(self.axis_settings.z_range, 2.0, self.container_object.location[2])

        if self.dimensions == '2':
            value_index = 1
        else:
            value_index = 2

        for i, entry in enumerate(self.data):
            if not self.in_axis_range_bounds_new(entry):
                continue
            
            if self.use_obj == 'Bar' or (self.use_obj == 'Custom' and self.custom_obj_name == ''):
                bpy.ops.mesh.primitive_cube_add()
                bar_obj = context.active_object
            elif self.use_obj == 'Cylinder':
                bpy.ops.mesh.primitive_cylinder_add(vertices=16)
                bar_obj = context.active_object
            elif self.use_obj == 'Custom':
                if self.custom_obj_name not in bpy.data.objects:
                    self.report({'ERROR'}, 'Selected object is part of the chart or is deleted!')
                    return {'CANCELLED'}
                src_obj = bpy.data.objects[self.custom_obj_name]
                bar_obj = src_obj.copy()
                bar_obj.data = src_obj.data.copy()
                context.collection.objects.link(bar_obj)

            if self.data_type_as_enum() == DataType.Numerical:
                x_value = entry[0]
            else:
                tick_labels.append(entry[0])
                x_value = i

            x_norm = self.normalize_value(x_value, 'x')
            z_norm = self.normalize_value(entry[value_index], 'z')
            if z_norm >= 0.0 and z_norm <= 0.0005:
                z_norm = 0.0005
            if self.dimensions == '2':
                bar_obj.scale = (self.bar_size[0], self.bar_size[1], z_norm * 0.5)
                bar_obj.location = (x_norm, 0.0, z_norm * 0.5)
            else:
                y_norm = self.normalize_value(entry[1], 'y')
                bar_obj.scale = (self.bar_size[0], self.bar_size[1], z_norm * 0.5)
                bar_obj.location = (x_norm, y_norm, z_norm * 0.5)

            mat = color_gen.get_material(entry[value_index])
            bar_obj.data.materials.append(mat)
            bar_obj.active_material = mat
            bar_obj.parent = self.container_object

            if self.anim_settings.animate and self.dm.tail_length != 0:
                frame_n = context.scene.frame_current
                bar_obj.keyframe_insert(data_path='location', frame=frame_n)
                bar_obj.keyframe_insert(data_path='scale', frame=frame_n)
                dif = 2 if self.dimensions == '2' else 1
                for j in range(value_index + 1, value_index + self.dm.tail_length + dif):
                    frame_n += self.anim_settings.key_spacing
                    zn_norm = self.normalize_value(self.data[i][j], 'z')
                    if zn_norm >= 0.0 and zn_norm <= 0.0005:
                        zn_norm = 0.0005
                    bar_obj.scale[2] = zn_norm * 0.5
                    bar_obj.location[2] = zn_norm * 0.5
                    bar_obj.keyframe_insert(data_path='location', frame=frame_n)
                    bar_obj.keyframe_insert(data_path='scale', frame=frame_n)

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                self.axis_settings,
                int(self.dimensions),
                self.chart_id,
                labels=self.labels,
                tick_labels=(tick_labels, [], []),
            )
        
        if self.header_settings.create:
            self.create_header()
        self.select_container()
        return {'FINISHED'}
