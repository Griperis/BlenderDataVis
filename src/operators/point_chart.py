import bpy

from src.general import OBJECT_OT_generic_chart, CONST, Properties
from src.operators.features.axis import Axis, AxisDir
from src.utils.data_utils import get_data_as_ll, find_data_range
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
            ('2D', '2D', 'Data + Top'),
            ('3D', '3D', 'Data + Data + Top')
        )
    )

    point_scale: bpy.props.FloatProperty(
        name='Point scale',
        default=0.1
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
        default=0.2
    )

    def execute(self, context):
        self.init_data()
        self.create_container()
        data_list = get_data_as_ll(self.data)

        # if self.dimensions == '3D' and not math.sqrt(len(data_matrix)).is_integer():
        #     self.report({'ERROR'}, 'Data is in invalid shape for 3D chart')
        #     return {'CANCELLED'}

        if self.dimensions == '2D':
            value_index = 1
        else:
            if len(data_list[0]) == 2:
                self.report({'ERROR'}, 'Data is only 2D!')
                return {'CANCELLED'}
            value_index = 2

        # fix length of data to parse
        data_min, data_max = find_data_range(data_list, self.x_axis_range, self.y_axis_range if self.dimensions == '3D' else None)
        
        data_value_range = data_max - data_min

        color_gen = ColorGen(self.color_shade, (data_min, data_max)) #reverse_iterator(sat_col_gen(len(self.data), *color_to_triplet(self.color_shade)))
        for i, entry in enumerate(data_list):
            if len(entry) > 3:
                self.report({'ERROR'}, 'Too many dimensions in data!')
                return {'CANCELLED'}
            
            # skip values outside defined axis range
            if not self.in_axis_range_bounds(entry):
                continue

            bpy.ops.mesh.primitive_ico_sphere_add()
            point_obj = context.active_object
            point_obj.scale = Vector((self.point_scale, self.point_scale, self.point_scale))
            point_obj.active_material = self.new_mat(color_gen.next(entry[value_index]), 1)

            # normalize height

            x_norm = (entry[0] - self.x_axis_range[0]) / (self.x_axis_range[1] - self.x_axis_range[0])
            z_norm = (entry[value_index] - data_min) / (data_max - data_min)
            if self.dimensions == '2D':
                point_obj.location = (x_norm, 0.0, z_norm)
            else:
                y_norm = (entry[1] - self.y_axis_range[0]) / (self.y_axis_range[1] - self.y_axis_range[0])
                point_obj.location = (x_norm, y_norm, z_norm)
    
            point_obj.parent = self.container_object

        x_axis = Axis(self.container_object, self.x_axis_step, self.x_axis_range, AxisDir.X)
        x_axis.create(self.padding, 0.0)
        y_axis = Axis(self.container_object, self.y_axis_step, self.y_axis_range, AxisDir.Y)
        y_axis.create(self.padding, 0.0)
        
        z_axis = Axis(self.container_object, self.z_axis_step, (data_min, data_max), AxisDir.Z)
        z_axis.create(self.padding, 0.0)
        return {'FINISHED'}

    def in_axis_range_bounds(self, entry):
        '''
        Checks whether the entry point defined as [x, y, z] is within user selected axis range
        returns False if not in range, else True
        '''
        entry_dims = len(entry)
        if entry_dims == 2 or entry_dims == 3:
            if entry[0] < self.x_axis_range[0] or entry[0] > self.x_axis_range[1]:
                return False

        if entry_dims == 3:
            if entry[1] < self.y_axis_range[0] or entry[1] > self.y_axis_range[1]:
                return False

        return True
