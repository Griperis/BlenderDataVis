import bpy
import math
from mathutils import Vector


from data_vis.utils.data_utils import find_data_range, normalize_value, find_axis_range
from data_vis.general import OBJECT_OT_GenericChart, DV_LabelPropertyGroup, DV_ColorPropertyGroup, DV_AxisPropertyGroup
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

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return dm.is_type(DataType.Numerical, [2, 3]) or dm.is_type(DataType.Categorical, [2])

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        row = layout.row()
        row.prop(self, 'bar_size')

    def execute(self, context):
        self.init_data()

        tick_labels = []

        if self.dm.predicted_data_type == DataType.Categorical and self.data_type_as_enum() == DataType.Numerical:
            self.report({'ERROR'}, 'Cannot convert categorical data into numerical!')
            return {'CANCELLED'}

        if self.dm.override(self.data_type_as_enum(), int(self.dimensions)):
            self.init_ranges()

        self.create_container()
        color_factory = ColoringFactory(self.color_settings.color_shade, ColorType.str_to_type(self.color_settings.color_type), self.color_settings.use_shader)
        color_gen = color_factory.create(self.axis_settings.z_range, 2.0, self.container_object.location[2])

        if self.dimensions == '2':
            value_index = 1
        else:
            value_index = 2

        for i, entry in enumerate(self.data):
            if not self.in_axis_range_bounds_new(entry):
                continue

            bpy.ops.mesh.primitive_cube_add()
            bar_obj = context.active_object
            if self.data_type_as_enum() == DataType.Numerical:
                x_value = entry[0]
            else:
                tick_labels.append(entry[0])
                x_value = i
            x_norm = normalize_value(x_value, self.axis_settings.x_range[0], self.axis_settings.x_range[1])

            z_norm = normalize_value(entry[value_index], self.axis_settings.z_range[0], self.axis_settings.z_range[1])
            if z_norm >= 0.0 and z_norm <= 0.0001:
                z_norm = 0.0001
            if self.dimensions == '2':
                bar_obj.scale = (self.bar_size[0], self.bar_size[1], z_norm * 0.5)
                bar_obj.location = (x_norm, 0.0, z_norm * 0.5)
            else:
                y_norm = normalize_value(entry[1], self.axis_settings.y_range[0], self.axis_settings.y_range[1])
                bar_obj.scale = (self.bar_size[0], self.bar_size[1], z_norm * 0.5)
                bar_obj.location = (x_norm, y_norm, z_norm * 0.5)

            mat = color_gen.get_material(entry[value_index])
            bar_obj.data.materials.append(mat)
            bar_obj.active_material = mat
            bar_obj.parent = self.container_object

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                (self.axis_settings.x_step, self.axis_settings.y_step, self.axis_settings.z_step),
                (self.axis_settings.x_range, self.axis_settings.y_range, self.axis_settings.z_range),
                int(self.dimensions),
                self.axis_settings.thickness,
                self.axis_settings.tick_mark_height,
                tick_labels=(tick_labels, [], []),
                labels=self.labels,
                padding=self.axis_settings.padding,
                auto_steps=self.axis_settings.auto_steps,
                offset=0.0
            )
        self.select_container()
        return {'FINISHED'}
