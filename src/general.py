
import bpy
import math

from mathutils import Vector
from src.utils.data_utils import get_data_as_ll, DataType


class CONST:
    GRAPH_Z_SCALE = 0.5
    HALF_PI = math.pi * 0.5


# for future use
class DV_AxisPropertyGroup(bpy.types.PropertyGroup):
    auto_ranges: bpy.props.BoolProperty(
        name='Automatic axis ranges',
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

    _step: bpy.props.FloatProperty(
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
        name='Axis thickness',
        default=0.01,
        description='How thick is the axis object'
    )

    tick_mark_height: bpy.props.FloatProperty(
        name='Axis tick mark height',
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


class Properties:
    '''
    Access to Blender properties related to addon, which are not in specific chart operators 
    '''
    @staticmethod
    def get_data():
        return bpy.data.scenes[0].dv_props.data

    @staticmethod
    def get_text_size():
        return bpy.data.scenes[0].dv_props.text_size

    @staticmethod
    def get_axis_thickness():
        return bpy.data.scenes[0].dv_props.axis_thickness

    @staticmethod
    def get_axis_tick_mark_height():
        return bpy.data.scenes[0].dv_props.axis_tick_mark_height


class OBJECT_OT_generic_chart(bpy.types.Operator):
    '''Creates chart'''
    bl_idname = 'object.create_chart'
    bl_label = 'Generic chart operator'
    bl_options = {'REGISTER', 'UNDO'}

    data = None
    chart_origin = None
    axis_mat = None

    def __init__(self):
        self.container_object = None
        self.labels = []

    def draw(self, context):  
        layout = self.layout
        if hasattr(self, 'data_type'):
            row = layout.row()
            row.prop(self, 'data_type')

        only_2d = hasattr(self, 'only_2d')
        numerical = True
        if hasattr(self, 'data_type'):
            if self.data_type == '1':
                numerical = False

        only_2d = only_2d or not numerical
    
        if not only_2d:
            row = layout.row()
            row.prop(self, 'dimensions')

        if numerical:
            row = layout.row()
            row.label(text='Axis ranges:')
            row.prop(self, 'auto_ranges')

        if not self.auto_ranges:
            row = layout.row()
            row.prop(self, 'x_axis_range')
            if not only_2d and self.dimensions == '3':
                row = layout.row()
                row.prop(self, 'y_axis_range')
        
        row = layout.row()
        row.label(text='Axis steps:')
        row.prop(self, 'auto_steps')
        if not self.auto_steps:
            row = layout.row()
            if numerical:
                row.prop(self, 'x_axis_step', text='x')
            if not only_2d and self.dimensions == '3':
                row.prop(self, 'y_axis_step', text='y')
            row.prop(self, 'z_axis_step', text='z')

        row = layout.row()
        row.prop(self, 'padding')

        row = layout.row()
        row.label(text='Label settings:')

        if hasattr(self, 'label_settings'):
            row.prop(self.label_settings, 'create')
            if self.label_settings.create:
                row.prop(self.label_settings, 'from_data')
                if not self.label_settings.from_data:
                    row = layout.row()
                    row.prop(self.label_settings, 'x_label')
                    if not only_2d and self.dimensions == '3':
                        row.prop(self.label_settings, 'y_label')
                    row.prop(self.label_settings, 'z_label')

    @classmethod
    def poll(cls, context):
        '''Default behavior for every chart poll method (when data is not available, cannot create chart)'''
        return len(bpy.data.scenes[0].dv_props.data) > 0

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

    def create_axis(self, spacing, x_vals, y_max=None, y_min=0, z_vals=None, padding=(0, 0, 0), offset=(0, 0, 0)):
        self.axis_mat = self.new_mat((1, 1, 1), 1, name='Axis_Mat')
        length = self.create_one_axis(spacing, x_vals, offset[0], padding[0])
        if y_max:
            cont = self.create_y_axis(y_min, y_max, offset[1], padding[1])
            if z_vals:
                cont.location.x += 2 * length
        if z_vals:
            self.create_one_axis(spacing, z_vals, offset[2], padding[2], dim='z')

    def data_type_as_enum(self):
        if not hasattr(self, 'data_type'):
            return DataType.Numerical

        if self.data_type == '0':
            return DataType.Numerical
        elif self.data_type == '1':
            return DataType.Categorical

    def create_y_axis(self, min_val, max_val, offset, padding):
        bpy.ops.object.empty_add()
        axis_cont = bpy.context.object
        axis_cont.name = 'Axis_Container'
        axis_cont.location = (0, 0, 0)
        axis_cont.parent = self.container_object

        bpy.ops.mesh.primitive_cube_add()
        line_obj = bpy.context.active_object
        line_obj.location = (0, 0, 0)

        line_obj.scale = (CONST.GRAPH_Z_SCALE + padding + offset * 0.5, 0.005, 0.005)
        line_obj.location.x += CONST.GRAPH_Z_SCALE + padding + offset * 0.5
        line_obj.parent = axis_cont

        line_obj.active_material = self.axis_mat

        spacing = 0.2 * CONST.GRAPH_Z_SCALE
        val_inc = (abs(min_val) + max_val) * 0.1
        val = min_val
        for i in range(0, 11):
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.active_object
            obj.scale = (0.005, 0.005, 0.02)
            obj.location = (0, 0, 0)
            obj.location.x += i * spacing + offset
            obj.parent = axis_cont
            obj.active_material = self.axis_mat

            self.create_text_object(axis_cont, '{0:.3}'.format(float(val)), (i * spacing + offset, 0, 0.07), (CONST.HALF_PI, CONST.HALF_PI, 0))
            val += val_inc

        axis_cont.location += Vector((-padding, 0, -padding))
        axis_cont.rotation_euler.y -= CONST.HALF_PI
        return axis_cont

    def create_one_axis(self, spacing, vals, offset, padding, dim='x'):
        bpy.ops.object.empty_add()
        axis_cont = bpy.context.object
        axis_cont.name = 'Axis_Container'
        axis_cont.location = (0, 0, 0)
        axis_cont.parent = self.container_object
        # TODO WHAT self.axis_containers.append(axis_cont)
        
        v_len = ((len(vals) - 1) * spacing) * 0.5 + padding + offset * 0.5
        bpy.ops.mesh.primitive_cube_add()
        line_obj = bpy.context.active_object
        line_obj.location = (0, 0, 0)

        line_obj.scale = (v_len, 0.005, 0.005)
        line_obj.location.x += v_len
        line_obj.parent = axis_cont
        line_obj.active_material = self.axis_mat

        for i in range(0, len(vals)):
            bpy.ops.mesh.primitive_cube_add()
            obj = bpy.context.active_object
            obj.scale = (0.005, 0.005, 0.02)
            obj.location = (0, 0, 0)
            obj.location.x += i * spacing + offset
            obj.parent = axis_cont
            obj.active_material = self.axis_mat

            to_loc = (i * spacing + offset, 0, -0.07)
            to_rot = (CONST.HALF_PI, 0, 0)
            if dim == 'z':
                to_rot = (CONST.HALF_PI, 0, math.pi)
    
            self.create_text_object(axis_cont, vals[i], to_loc, to_rot)
        
        axis_cont.location += Vector((-padding, 0, -padding))
        if dim == 'z':
            axis_cont.rotation_euler.z += CONST.HALF_PI

        return v_len

    def create_text_object(self, parent, text, location_offset, rotation_offset):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = str(text)
        to.data.align_x = 'CENTER'
        to.scale *= 0.05
        to.location = parent.location
        to.location += Vector(location_offset)
        to.rotation_euler.x += rotation_offset[0]
        to.rotation_euler.y += rotation_offset[1]
        to.rotation_euler.z += rotation_offset[2]
        to.parent = parent

    def new_mat(self, color, alpha, name='Mat'):
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = (*color, alpha)
        return mat

    def init_data(self, data_type):
        data = list(bpy.data.scenes[0].dv_props.data)
        if hasattr(self, 'label_settings'):
            self.init_labels(data)
        try:
            self.data = get_data_as_ll(data, data_type)
        except Exception as e:
            print(e)
            self.report({'ERROR'}, 'Data should be in X, Y, Z format (2 or 3 dimensions are currently supported).\nData should be in format according to chart type!')
            return False
        
        return True

    def init_labels(self, data):
        if not self.label_settings.create:
            self.labels = [None, None, None]
            return
        if self.label_settings.from_data:
            first_line = data.pop(0).value.split(',')
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
