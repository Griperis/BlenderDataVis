import bpy

from src.general import OBJECT_OT_generic_chart, DV_LabelPropertyGroup
from src.operators.features.axis import AxisFactory
from src.utils.data_utils import get_data_as_ll, find_data_range, normalize_value, find_axis_range, DataType
from src.utils.color_utils import sat_col_gen, color_to_triplet, reverse_iterator, ColorGen

from mathutils import Vector
import math


class OBJECT_OT_point_chart(OBJECT_OT_generic_chart):
    '''Creates point chart'''
    bl_idname = 'object.create_point_chart'
    bl_label = 'Point Chart'
    bl_options = {'REGISTER', 'UNDO'}

    dimensions: bpy.props.EnumProperty(
        name='Dimensions',
        items=(
            ('3', '3D', 'X, Y, Z'),
            ('2', '2D', 'X, Z'),
        )
    )

    point_scale: bpy.props.FloatProperty(
        name='Point scale',
        default=0.05
    )

    auto_ranges: bpy.props.BoolProperty(
        name='Automatic axis ranges',
        default=True
    )

    auto_steps: bpy.props.BoolProperty(
        name='Automatic axis steps',
        default=True
    )

    x_axis_step: bpy.props.FloatProperty(
        name='Step of x axis',
        default=1.0
    )

    x_axis_range: bpy.props.FloatVectorProperty(
        name='Range of x axis',
        size=2,
        default=(0.0, 1.0)
    )

    y_axis_step: bpy.props.FloatProperty(
        name='Step of y axis',
        default=1.0
    )

    y_axis_range: bpy.props.FloatVectorProperty(
        name='Range of y axis',
        size=2,
        default=(0.0, 1.0)
    )

    z_axis_step: bpy.props.FloatProperty(
        name='Step of z axis',
        default=1.0
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0
    )

    padding: bpy.props.FloatProperty(
        name='Padding',
        default=0.1,
        min=0.0
    )

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup
    )

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        row = layout.row()
        row.prop(self, 'point_scale')

        row = layout.row()
        row.prop(self, 'color_shade')

    def init_range(self, data):
        self.x_axis_range = find_axis_range(data, 0)
        self.y_axis_range = find_axis_range(data, 1)

    def execute(self, context):
        if not self.init_data(DataType.Numerical):
            return {'CANCELLED'}
        if self.auto_ranges:
            self.init_range(self.data)

        if self.dimensions == '2':
            value_index = 1
        else:
            if len(self.data[0]) == 2:
                self.report({'ERROR'}, 'Data are only 2D!')
                return {'CANCELLED'}
            value_index = 2

        self.create_container()
        # fix length of data to parse
        data_min, data_max = find_data_range(self.data, self.x_axis_range, self.y_axis_range if self.dimensions == '3' else None)
        
        color_gen = ColorGen(self.color_shade, (data_min, data_max))
        for i, entry in enumerate(self.data):
            
            # skip values outside defined axis range
            if not self.in_axis_range_bounds(entry):
                continue

            bpy.ops.mesh.primitive_ico_sphere_add()
            point_obj = context.active_object
            point_obj.scale = Vector((self.point_scale, self.point_scale, self.point_scale))
            point_obj.active_material = self.new_mat(color_gen.next(entry[value_index]), 1)

            # normalize height

            x_norm = normalize_value(entry[0], self.x_axis_range[0], self.x_axis_range[1]) 
            z_norm = normalize_value(entry[value_index], data_min, data_max)
            if self.dimensions == '2':
                point_obj.location = (x_norm, 0.0, z_norm)
            else:
                y_norm = normalize_value(entry[1], self.y_axis_range[0], self.y_axis_range[1])
                point_obj.location = (x_norm, y_norm, z_norm)
    
            point_obj.parent = self.container_object
        
        AxisFactory.create(
            self.container_object,
            (self.x_axis_step, self.y_axis_step, self.z_axis_step),
            (self.x_axis_range, self.y_axis_range, (data_min, data_max)),
            int(self.dimensions),
            labels=self.labels,
            padding=self.padding,
            auto_steps=self.auto_steps,
            offset=0.0
        )
        return {'FINISHED'}
