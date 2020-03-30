
import bpy
import math

from mathutils import Vector
from data_vis.data_manager import DataManager, DataType
from data_vis.colors import NodeShader


class CONST:
    GRAPH_Z_SCALE = 0.5
    HALF_PI = math.pi * 0.5


class DV_AxisPropertyGroup(bpy.types.PropertyGroup):
    create: bpy.props.BoolProperty(
        name='Create Axis',
        default=True
    )

    auto_ranges: bpy.props.BoolProperty(
        name='Automatic Axis Ranges',
        default=True
    )

    x_step: bpy.props.FloatProperty(
        name='Step of x axis',
        default=1.0
    )

    x_range: bpy.props.FloatVectorProperty(
        name='Range of x axis',
        size=2,
        default=(0.0, 1.0)
    )

    y_step: bpy.props.FloatProperty(
        name='Step of y axis',
        default=1.0
    )

    y_range: bpy.props.FloatVectorProperty(
        name='Range of y axis',
        size=2,
        default=(0.0, 1.0)
    )

    z_step: bpy.props.FloatProperty(
        name='Step of z axis',
        default=1.0
    )

    thickness: bpy.props.FloatProperty(
        name='Axis Thickness',
        default=0.01,
        description='How thick is the axis object'
    )

    tick_mark_height: bpy.props.FloatProperty(
        name='Axis Tick Mark Height',
        default=0.03
    )

    padding: bpy.props.FloatProperty(
        name='Padding',
        default=0.1
    )


class DV_LabelPropertyGroup(bpy.types.PropertyGroup):
    create: bpy.props.BoolProperty(
        name='Create labels',
        default=True
    )

    from_data: bpy.props.BoolProperty(
        name='From data',
        default=True
    )

    x_label: bpy.props.StringProperty(
        name='X',
        default='X Label'
    )

    y_label: bpy.props.StringProperty(
        name='Y',
        default='Y Label'
    )

    z_label: bpy.props.StringProperty(
        name='Z',
        default='Z Label'
    )


class DV_ColorPropertyGroup(bpy.types.PropertyGroup):
    use_shader: bpy.props.BoolProperty(
        name='Use Shader',
        default=True
    )

    color_type: bpy.props.EnumProperty(
        name='Shader Type',
        items=(
            ('0', 'Constant', 'One color'),
            ('1', 'Random', 'Random colors'),
            ('2', 'Gradient', 'Gradient based on value')
        ),
        default='2'
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Base Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0
    )


class Properties:
    '''
    Access to Blender properties related to addon, which are not in specific chart operators
    '''
    @staticmethod
    def get_text_size():
        return bpy.data.scenes[0].dv_props.text_size

    @staticmethod
    def get_axis_thickness():
        return bpy.data.scenes[0].dv_props.axis_thickness

    @staticmethod
    def get_axis_tick_mark_height():
        return bpy.data.scenes[0].dv_props.axis_tick_mark_height


class OBJECT_OT_GenericChart(bpy.types.Operator):
    '''Creates chart'''
    bl_idname = 'object.create_chart'
    bl_label = 'Generic chart operator'
    bl_options = {'REGISTER', 'UNDO'}

    data = None
    axis_mat = None

    def __init__(self):
        self.container_object = None
        self.labels = []
        self.chart_origin = (0, 0, 0)
        self.dm = DataManager()
        if hasattr(self, 'dimensions'):
            self.dimensions = str(self.dm.dimensions)

        if hasattr(self, 'data_type'):
            self.data_type = '0' if self.dm.predicted_data_type == DataType.Numerical else '1'

    def draw(self, context):
        layout = self.layout
        if hasattr(self, 'data_type'):
            row = layout.row()
            row.prop(self, 'data_type')

        only_2d = hasattr(self, 'dimensions')
        numerical = True
        if hasattr(self, 'data_type'):
            if self.data_type == '1':
                numerical = False

        only_2d = only_2d or not numerical

        if hasattr(self, 'dimensions') and self.dm.predicted_data_type != DataType.Categorical:
            row = layout.row()
            row.prop(self, 'dimensions')

        if numerical:
            row = layout.row()
            row.label(text='Axis ranges:')
            row.prop(self, 'auto_ranges')

        if not self.auto_ranges:
            row = layout.row()
            row.prop(self, 'x_axis_range')
            if self.dm.dimensions == 3:
                row = layout.row()
                row.prop(self, 'y_axis_range')

        row = layout.row()
        row.label(text='Axis steps:')
        row.prop(self, 'auto_steps')
        if not self.auto_steps:
            row = layout.row()
            if numerical:
                row.prop(self, 'x_axis_step', text='x')
            if self.dm.dimensions == 3:
                row.prop(self, 'y_axis_step', text='y')
            row.prop(self, 'z_axis_step', text='z')

        row = layout.row()
        row.prop(self, 'padding')

        self.draw_label_settings(layout)
        self.draw_color_settings(layout)

    def draw_label_settings(self, layout):
        if hasattr(self, 'label_settings'):
            row = layout.row()
            row.label(text='Label settings:')
            row.prop(self.label_settings, 'create')
            if self.label_settings.create:
                row.prop(self.label_settings, 'from_data')
                if not self.label_settings.from_data:
                    row = layout.row()
                    row.prop(self.label_settings, 'x_label')
                    if self.dm.dimensions == 3:
                        row.prop(self.label_settings, 'y_label')
                    row.prop(self.label_settings, 'z_label')
    
    def draw_color_settings(self, layout):
        if hasattr(self, 'color_settings'):
            box = layout.box()
            box.label(text='Color settings')
            box.prop(self.color_settings, 'use_shader')
            if self.color_settings.use_shader:
                box.prop(self.color_settings, 'color_type')
            if not NodeShader.Type.str_to_type(self.color_settings.color_type) == NodeShader.Type.Random:
                box.prop(self.color_settings, 'color_shade')

    @classmethod
    def poll(cls, context):
        '''Default behavior for every chart poll method (when data is not available, cannot create chart)'''
        return self.dm.parsed_data is not None

    def execute(self, context):
        raise NotImplementedError('Execute method should be implemented in every chart operator!')

    def invoke(self, context, event):
        self.chart_origin = context.scene.cursor.location
        return context.window_manager.invoke_props_dialog(self)

    def create_container(self):
        bpy.ops.object.empty_add()
        self.container_object = bpy.context.object
        self.container_object.empty_display_type = 'PLAIN_AXES'
        self.container_object.name = 'Chart_Container'
        # set default location for parent object
        self.container_object.location = self.chart_origin

    def data_type_as_enum(self):
        if not hasattr(self, 'data_type'):
            return DataType.Numerical

        if self.data_type == '0':
            return DataType.Numerical
        elif self.data_type == '1':
            return DataType.Categorical

    def new_mat(self, color, alpha, name='Mat'):
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = (*color, alpha)
        return mat

    def init_data(self):
        if hasattr(self, 'label_settings'):
            self.init_labels()
        data = self.dm.get_parsed_data()

        self.data = data
        return True

    def init_labels(self):
        if not self.label_settings.create:
            self.labels = (None, None, None)
            return
        if self.dm.has_labels:
            first_line = self.dm.get_labels()
            length = len(first_line)
            if length == 2:
                self.labels = (first_line[0], '', first_line[1])
            elif length == 3:
                self.labels = (first_line[0], first_line[1], first_line[2])
            else:
                self.report({'ERROR'}, 'Unsupported number of labels on first line')
        else:
            self.labels = [self.label_settings.x_label, self.label_settings.y_label, self.label_settings.z_label]

    def in_axis_range_bounds(self, entry):
        '''
        Checks whether the entry point defined as [x, y, z] is within user selected axis range
        returns False if not in range, else True
        '''
        entry_dims = len(entry)
        if entry_dims == 2 or entry_dims == 3:
            if hasattr(self, 'data_type') and self.data_type != '0':
                return True

            if entry[0] < self.x_axis_range[0] or entry[0] > self.x_axis_range[1]:
                return False

        if entry_dims == 3:
            if entry[1] < self.y_axis_range[0] or entry[1] > self.y_axis_range[1]:
                return False

        return True
