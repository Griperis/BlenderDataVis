import bpy
import math
from itertools import zip_longest
from mathutils import Vector


from data_vis.utils.data_utils import get_data_as_ll, find_data_range, find_axis_range, normalize_value, get_data_in_range, DataType
from data_vis.operators.features.axis import AxisFactory
from data_vis.general import OBJECT_OT_generic_chart, DV_LabelPropertyGroup
from data_vis.general import CONST


class OBJECT_OT_line_chart(OBJECT_OT_generic_chart):
    '''Creates line chart as a line or as curve'''
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

    auto_steps: bpy.props.BoolProperty(
        name='Automatic axis steps',
        default=True
    )

    auto_ranges: bpy.props.BoolProperty(
        name='Automatic axis ranges',
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

    z_axis_step: bpy.props.FloatProperty(
        name='Step of z axis',
        default=1.0
    )

    padding: bpy.props.FloatProperty(
        name='Padding',
        default=0.1,
        min=0.0
    )

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup
    )

    def __init__(self):
        self.only_2d = True
        self.x_delta = 0.2
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

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        if self.bevel_edges:
            row = layout.row()
            row.prop(self, 'rounded')
        row = layout.row()
        row.prop(self, 'bevel_edges')
        if self.bevel_edges:
            row = layout.row()
            row.prop(self, 'rounded')

    def execute(self, context):
        if not self.init_data(self.data_type_as_enum()):
            return {'CANCELLED'}
        if len(self.data[0]) > 2:
            self.report({'ERROR'}, 'Line chart supports X Y values only')
            return {'CANCELLED'}
        self.create_container()

        if self.data_type_as_enum() == DataType.Numerical:
            if self.auto_ranges:
                self.x_axis_range = find_axis_range(self.data, 0)
            data_min, data_max = find_data_range(self.data, self.x_axis_range)
            self.data = get_data_in_range(self.data, self.x_axis_range)
            sorted_data = sorted(self.data, key=lambda x: x[0])
        else:
            self.x_axis_range[0] = 0
            self.x_axis_range[1] = len(self.data) - 1
            data_min = min(self.data, key=lambda val: val[1])[1]
            data_max = max(self.data, key=lambda val: val[1])[1]
            sorted_data = self.data

        tick_labels = []
        if self.data_type_as_enum() == DataType.Numerical:
            normalized_vert_list = [(normalize_value(entry[0], self.x_axis_range[0], self.x_axis_range[1]), 0.0, normalize_value(entry[1], data_min, data_max)) for entry in sorted_data]
        else:
            normalized_vert_list = [(normalize_value(i, self.x_axis_range[0], self.x_axis_range[1]), 0.0, normalize_value(entry[1], data_min, data_max)) for i, entry in enumerate(sorted_data)]
            tick_labels = list(zip(*sorted_data))[0]

        edges = [[i - 1, i] for i in range(1, len(normalized_vert_list))]

        self.create_curve(normalized_vert_list, edges)
        self.add_bevel_obj()

        AxisFactory.create(
            self.container_object,
            (self.x_axis_step, 0, self.z_axis_step),
            (self.x_axis_range, [], (data_min, data_max)),
            2,
            tick_labels=(tick_labels, [], []),
            labels=self.labels,
            padding=self.padding,
            auto_steps=self.auto_steps,
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
