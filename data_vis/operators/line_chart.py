import bpy
import math
from mathutils import Vector


from data_vis.utils.data_utils import find_data_range, find_axis_range, normalize_value, get_data_in_range
from data_vis.operators.features.axis import AxisFactory
from data_vis.general import OBJECT_OT_GenericChart, DV_LabelPropertyGroup, DV_AxisPropertyGroup
from data_vis.data_manager import DataManager, DataType
from data_vis.colors import NodeShader, ColorGen, ColorType


class OBJECT_OT_LineChart(OBJECT_OT_GenericChart):
    '''Creates Line Chart, supports 2D Numerical or Categorical values with or w/o labels'''
    bl_idname = 'object.create_line_chart'
    bl_label = 'Line Chart'
    bl_options = {'REGISTER', 'UNDO'}

    bevel_edges: bpy.props.BoolProperty(
        name='Bevel edges'
    )

    data_type: bpy.props.EnumProperty(
        name='Chart type',
        items=(
            ('0', 'Numerical', 'X relative to Z or Y'),
            ('1', 'Categorical', 'Label and value'),
        )
    )

    rounded: bpy.props.EnumProperty(
        name='Settings',
        items=(
            ('1', 'Rounded', 'Beveled corners'),
            ('2', 'Sharp', 'Sharp corners')
        )
    )

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup
    )

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup,
        options={'SKIP_SAVE'}
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Base Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        description='Base color shade to work with'
    )

    use_shader: bpy.props.BoolProperty(
        name='Use Nodes',
        default=False,
    )

    def __init__(self):
        super().__init__()
        self.only_2d = True
        self.bevel_obj_size = (0.01, 0.01, 0.01)
        self.bevel_settings = {
            'rounded': {
                'segments': 5,
                'offset': 0.05,
                'profile': 0.6,
            },
            'sharp': {
                'segments': 3,
                'offset': 0.02,
                'profile': 1.0,
            },
        }

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return dm.is_type(DataType.Numerical, [2]) or dm.is_type(DataType.Categorical, [2])

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        box = layout.box()
        if self.bevel_edges:
            box.prop(self, 'rounded')
        box.prop(self, 'bevel_edges')

        box = layout.box()
        box.prop(self, 'use_shader')
        box.prop(self, 'color_shade')

    def execute(self, context):
        self.init_data()

        self.create_container()

        if self.data_type_as_enum() == DataType.Numerical:
            self.data = get_data_in_range(self.data, self.axis_settings.x_range)
            sorted_data = sorted(self.data, key=lambda x: x[0])
        else:
            sorted_data = self.data

        tick_labels = []
        if self.data_type_as_enum() == DataType.Numerical:
            normalized_vert_list = [(normalize_value(entry[0], self.axis_settings.x_range[0], self.axis_settings.x_range[1]), 0.0, normalize_value(entry[1], self.axis_settings.z_range[0], self.axis_settings.z_range[1])) for entry in sorted_data]
        else:
            normalized_vert_list = [(normalize_value(i, self.axis_settings.x_range[0], self.axis_settings.x_range[1]), 0.0, normalize_value(entry[1], self.axis_settings.z_range[0], self.axis_settings.z_range[1])) for i, entry in enumerate(sorted_data)]
            tick_labels = list(zip(*sorted_data))[0]

        edges = [[i - 1, i] for i in range(1, len(normalized_vert_list))]

        self.create_curve(normalized_vert_list, edges)
        self.add_bevel_obj()
        if self.use_shader:
            mat = NodeShader(self.color_shade, location_z=self.container_object.location[2]).create_geometry_shader()
        else:
            mat = ColorGen(self.color_shade, ColorType.Constant, self.axis_settings.z_range).get_material()

        self.curve_obj.data.materials.append(mat)
        self.curve_obj.active_material = mat

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                (self.axis_settings.x_step, 0, self.axis_settings.z_step),
                (self.axis_settings.x_range, [], self.axis_settings.z_range),
                2,
                self.axis_settings.thickness,
                self.axis_settings.tick_mark_height,
                tick_labels=(tick_labels, [], []),
                labels=self.labels,
                padding=self.axis_settings.padding,
                auto_steps=self.axis_settings.auto_steps,
                offset=0.0
            )
        return {'FINISHED'}

    def create_curve(self, verts, edges):
        m = bpy.data.meshes.new('line_mesh')
        self.curve_obj = bpy.data.objects.new('line_chart_curve', m)

        bpy.context.scene.collection.objects.link(self.curve_obj)
        self.curve_obj.parent = self.container_object
        m.from_pydata(verts, edges, [])
        m.update()

        self.select_curve_obj()
        if self.bevel_edges:
            self.bevel_curve_obj()

        bpy.ops.object.convert(target='CURVE')

    def bevel_curve_obj(self):
        bpy.ops.object.mode_set(mode='EDIT')
        opts = self.bevel_settings['rounded'] if self.rounded == '1' else self.bevel_settings['sharp']
        bpy.ops.mesh.bevel(
            segments=opts['segments'],
            offset=opts['offset'],
            offset_type='OFFSET',
            profile=opts['profile'],
            vertex_only=True
        )
        bpy.ops.object.mode_set(mode='OBJECT')

    def add_bevel_obj(self):
        bpy.ops.mesh.primitive_plane_add()
        bevel_obj = bpy.context.active_object
        bevel_obj.scale = self.bevel_obj_size

        bpy.ops.object.convert(target='CURVE')
        self.curve_obj.data.bevel_object = bevel_obj
        return bevel_obj

    def select_curve_obj(self):
        self.curve_obj.select_set(True)
        bpy.context.view_layer.objects.active = self.curve_obj
