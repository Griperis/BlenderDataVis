import bpy
from mathutils import Vector
import math

from data_vis.general import OBJECT_OT_GenericChart, DV_LabelPropertyGroup, DV_AxisPropertyGroup, DV_ColorPropertyGroup, DV_AnimationPropertyGroup, DV_HeaderPropertyGroup
from data_vis.operators.features.axis import AxisFactory
from data_vis.utils.data_utils import normalize_value
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

    anim_settings: bpy.props.PointerProperty(
        type=DV_AnimationPropertyGroup
    )
    
    header_settings: bpy.props.PointerProperty(
        type=DV_HeaderPropertyGroup
    )

    custom_object: bpy.props.BoolProperty(
        name='Custom object',
        default=False
    )

    @classmethod
    def poll(cls, context):
        return DataManager().is_type(DataType.Numerical, [2, 3])

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        row = layout.row()
        row.prop(self, 'point_scale')

        row = layout.row()
        row.prop(self, 'custom_object')
        if self.custom_object:
            row = layout.row()
            scene = context.scene
            row.prop_search(scene, 'dv_custom_obj_name', scene, 'objects', text='Object')

    def execute(self, context):
        self.init_data()

        if self.dimensions == '2':
            value_index = 1
        else:
            if len(self.data[0]) == 2:
                self.report({'ERROR'}, 'Data are only 2D!')
                return {'CANCELLED'}
            value_index = 2

        self.create_container()
        color_factory = ColoringFactory(self.get_name(), self.color_settings.color_shade, ColorType.str_to_type(self.color_settings.color_type), self.color_settings.use_shader)
        color_gen = color_factory.create(self.axis_settings.z_range, 1.0, self.container_object.location[2])

        custom_obj_name = context.scene.dv_custom_obj_name
        
        for i, entry in enumerate(self.data):

            # skip values outside defined axis range
            if not self.in_axis_range_bounds_new(entry):
                continue
            
            if not self.custom_object or custom_obj_name == '':
                bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8)
                point_obj = context.active_object
            else:
                src_obj = bpy.data.objects[custom_obj_name]
                point_obj = src_obj.copy()
                point_obj.data = src_obj.data.copy()
                context.collection.objects.link(point_obj)

            point_obj.scale = Vector((self.point_scale, self.point_scale, self.point_scale))

            mat = color_gen.get_material(entry[value_index])
            point_obj.data.materials.append(mat)
            point_obj.active_material = mat

            # normalize height
            x_norm = normalize_value(entry[0], self.axis_settings.x_range[0], self.axis_settings.x_range[1])
            z_norm = normalize_value(entry[value_index], self.axis_settings.z_range[0], self.axis_settings.z_range[1])
            if self.dimensions == '2':
                point_obj.location = (x_norm, 0.0, z_norm)
            else:
                y_norm = normalize_value(entry[1], self.axis_settings.y_range[0], self.axis_settings.y_range[1])
                point_obj.location = (x_norm, y_norm, z_norm)

            point_obj.parent = self.container_object

            if self.anim_settings.animate and self.dm.tail_length != 0:
                frame_n = context.scene.frame_current
                point_obj.keyframe_insert(data_path='location', frame=frame_n)
                dif = 2 if self.dimensions == '2' else 1
                for j in range(value_index + 1, value_index + self.dm.tail_length + dif):
                    frame_n += self.anim_settings.key_spacing
                    zn_norm = normalize_value(self.data[i][j], self.axis_settings.z_range[0], self.axis_settings.z_range[1])
                    point_obj.location[2] = zn_norm
                    point_obj.keyframe_insert(data_path='location', frame=frame_n)

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                self.axis_settings,
                self.chart_id,
                int(self.dimensions),
                labels=self.labels
            )

        if self.header_settings.create:
            self.create_header()
        self.select_container()
        return {'FINISHED'}
