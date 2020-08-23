# File: bubble_chart.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Bubble chart implementation

import bpy

from data_vis.general import OBJECT_OT_GenericChart
from data_vis.properties import DV_AnimationPropertyGroup, DV_AxisPropertyGroup, DV_ColorPropertyGroup, DV_HeaderPropertyGroup, DV_LabelPropertyGroup
from data_vis.colors import ColoringFactory, ColorType
from data_vis.operators.features.axis import AxisFactory
from data_vis.data_manager import DataManager, DataType, DataSubtype
from data_vis.utils.data_utils import normalize_value


class OBJECT_OT_BubbleChart(OBJECT_OT_GenericChart):
    '''Creates Bubble Chart, XYW or XYZW data needed'''
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

    bubble_size: bpy.props.FloatVectorProperty(
        name='Bubble size',
        size=2,
        default=(0.005, 0.1),
    )

    anim_settings: bpy.props.PointerProperty(
        type=DV_AnimationPropertyGroup
    )

    anim_type: bpy.props.EnumProperty(
        name='Animated Property',
        items=(
            ('size', 'Size', 'size'),
            ('z', 'Z', 'z')
        )
    )

    def __init__(self):
        super().__init__()
        self.only_2d = False if self.dm.has_subtype(DataSubtype.XYZW) else True
        if self.only_2d:
            self.dimensions = '2'

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return dm.is_type(DataType.Numerical, 3) and dm.has_compatible_subtype([DataSubtype.XYW, DataSubtype.XYZW])

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        box = layout.box()
        box.prop(self, 'bubble_size')

    def extend_anim_draw(self, box):
        if self.anim_settings.animate:
            box.prop(self, 'anim_type')

    def execute(self, context):
        self.init_data(subtype=self.determine_subtype())
        self.create_container()

        color_factory = ColoringFactory(self.get_name(), self.color_settings.color_shade, ColorType.str_to_type(self.color_settings.color_type), self.color_settings.use_shader)
        color_gen = color_factory.create(self.axis_settings.z_range, 1.0, self.container_object.location[2])

        w_idx = 2 if self.dimensions == '2' else 3
        w_range = self.dm.get_range('w')
        v_idx = w_idx - 1
        for i, entry in enumerate(self.data):
            if not self.in_axis_range_bounds_new(entry):
                continue
            
            bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8)
            bubble_obj = context.active_object

            bubble_obj.scale *= (self.bubble_size[1] - self.bubble_size[0]) * normalize_value(entry[w_idx], w_range[0], w_range[1]) + self.bubble_size[0]

            x_norm = self.normalize_value(entry[0], 'x')
            z_norm = self.normalize_value(entry[v_idx], 'z')
            if self.dimensions == '2':
                bubble_obj.location = (x_norm, 0.0, z_norm)
            else:
                y_norm = self.normalize_value(entry[1], 'y')
                bubble_obj.location = (x_norm, y_norm, z_norm)

            
            mat = color_gen.get_material(entry[v_idx])
            bubble_obj.data.materials.append(mat)
            bubble_obj.active_material = mat

            bubble_obj.parent = self.container_object
                        
            if self.anim_settings.animate:
                frame_n = context.scene.frame_current

                if self.anim_type == 'z':
                    bubble_obj.keyframe_insert(data_path='location', frame=frame_n)
                elif self.anim_type == 'size':
                    bubble_obj.keyframe_insert(data_path='scale', frame=frame_n)

                anim_data = self.dm.parsed_data[i][w_idx + 1:]
                for j in range(len(anim_data)):
                    frame_n += self.anim_settings.key_spacing
                    zn_norm = self.normalize_value(anim_data[j], 'z')

                    if self.anim_type == 'z':
                        bubble_obj.location[2] = zn_norm
                        bubble_obj.keyframe_insert(data_path='location', frame=frame_n)
                    
                    elif self.anim_type == 'size':
                        scale = (self.bubble_size[1] - self.bubble_size[0]) * normalize_value(anim_data[j], w_range[0], w_range[1]) + self.bubble_size[0]
                        bubble_obj.scale = (scale, scale, scale)
                        bubble_obj.keyframe_insert(data_path='scale', frame=frame_n)

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                self.axis_settings,
                int(self.dimensions),
                self.chart_id,
                labels=self.labels,
                container_size=self.container_size,
            )

        self.select_container()
        return {'FINISHED'}

    def determine_subtype(self):
        '''Determines data subtype by user input'''
        if self.dimensions == '2':
            return DataSubtype.XYW
        elif self.dimensions == '3':
            return DataSubtype.XYZW
