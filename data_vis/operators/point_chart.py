import bpy
from mathutils import Vector
import math

from data_vis.general import OBJECT_OT_GenericChart, DV_LabelPropertyGroup, DV_AxisPropertyGroup, DV_ColorPropertyGroup
from data_vis.operators.features.axis import AxisFactory
from data_vis.utils.data_utils import find_data_range, normalize_value, find_axis_range
from data_vis.utils.color_utils import sat_col_gen, color_to_triplet, reverse_iterator, ColorGen
from data_vis.colors import ColoringFactory, ColorType
from data_vis.data_manager import DataManager, DataType


class OBJECT_OT_PointChart(OBJECT_OT_GenericChart):
    '''Creates Point Chart, supports 2D and 3D Numerical values with or w/o labels'''
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

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup
    )

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup
    )

    color_settings: bpy.props.PointerProperty(
        type=DV_ColorPropertyGroup
    )

    @classmethod
    def poll(cls, context):
        return DataManager().is_type(DataType.Numerical, 3)

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        row = layout.row()
        row.prop(self, 'point_scale')

    def execute(self, context):
        self.init_data()
        if self.axis_settings.auto_ranges:
            self.init_range(self.data)

        if self.dimensions == '2':
            value_index = 1
        else:
            if len(self.data[0]) == 2:
                self.report({'ERROR'}, 'Data are only 2D!')
                return {'CANCELLED'}
            value_index = 2

        self.create_container()
        data_min, data_max = find_data_range(self.data, self.axis_settings.x_range, self.axis_settings.y_range if self.dimensions == '3' else None)
        color_factory = ColoringFactory(self.color_settings.color_shade, ColorType.str_to_type(self.color_settings.color_type), self.color_settings.use_shader)
        color_gen = color_factory.create((data_min, data_max), 1.0, self.container_object.location[2])
        
        for i, entry in enumerate(self.data):

            # skip values outside defined axis range
            if not self.in_axis_range_bounds_new(entry):
                continue

            bpy.ops.mesh.primitive_uv_sphere_add()
            point_obj = context.active_object
            point_obj.scale = Vector((self.point_scale, self.point_scale, self.point_scale))

            mat = color_gen.get_material(entry[value_index])
            point_obj.data.materials.append(mat)
            point_obj.active_material = mat

            # normalize height
            x_norm = normalize_value(entry[0], self.axis_settings.x_range[0], self.axis_settings.x_range[1])
            z_norm = normalize_value(entry[value_index], data_min, data_max)
            if self.dimensions == '2':
                point_obj.location = (x_norm, 0.0, z_norm)
            else:
                y_norm = normalize_value(entry[1], self.axis_settings.y_range[0], self.axis_settings.y_range[1])
                point_obj.location = (x_norm, y_norm, z_norm)

            point_obj.parent = self.container_object

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                (self.axis_settings.x_step, self.axis_settings.y_step, self.axis_settings.z_step),
                (self.axis_settings.x_range, self.axis_settings.y_range, (data_min, data_max)),
                int(self.dimensions),
                self.axis_settings.thickness,
                self.axis_settings.tick_mark_height,
                labels=self.labels,
                padding=self.axis_settings.padding,
                auto_steps=self.axis_settings.auto_steps,
                offset=0.0
            )
        return {'FINISHED'}
