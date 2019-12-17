import bpy
import bmesh
import csv
import math
from mathutils import Vector, Matrix
from .data_utils import get_col_float, get_col_str, col_values_sum, col_values_max, float_data_gen
from .color_utils import sat_col_gen, color_to_triplet


class OBJECT_OT_generic_chart(bpy.types.Operator):
    '''Creates chart'''
    bl_idname = 'object.create_chart'
    bl_label = 'Generic chart operator'
    bl_options = {'REGISTER', 'UNDO'}

    data = None
    chart_origin = None

    def __init__(self):
        self.container_object = None
        self.arrow_container_objects = []

    @classmethod
    def poll(cls, context):
        '''Default behavior for every chart poll method (when data is not available, cannot create chart)'''
        return len(bpy.data.scenes[0].dv_props.data) > 0

    def execute(self, context):
        raise NotImplementedError('Execute method should be implemented in every chart operator!')

    def invoke(self, context, event):
        self.chart_origin = context.scene.cursor.location
        return context.window_manager.invoke_props_dialog(self)

    def init_data(self):
        self.data = bpy.data.scenes[0].dv_props.data

    def create_container(self):
        self.container_object = bpy.data.objects.new('empty', None)
        bpy.context.scene.collection.objects.link(self.container_object)
        self.container_object.empty_display_size = 2
        self.container_object.empty_display_type = 'PLAIN_AXES'
        self.container_object.name = 'Chart_Container'
        # set default location for parent object
        self.container_object.location = self.chart_origin

    def create_axis(self, dim=2):
        for d in range(dim):
            self.create_arrow(d + 1)
            
    def create_arrow(self, dim):
        '''
        Creates basic arrow that is positioned relatively to chart container object (left bottom corner),
        each arrow is but in its 'Axis' container.
        '''
        arrow_length = 15
        arrow_size = 0.1

        pointer_angle = 30
        pointer_length = 0.5
        
        arrow_container = bpy.data.objects.new('empty', None)
        self.arrow_container_objects.append(arrow_container)
        bpy.context.scene.collection.objects.link(arrow_container)
        arrow_container.parent = self.container_object
        arrow_container.name = 'Axis' + str(dim)

        arrow_container.location = (0, 0, 0)
        arrow_scale = (arrow_length, arrow_size, arrow_size)
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        obj = bpy.context.active_object
        obj.parent = arrow_container
        obj.scale = arrow_scale

        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        left = bpy.context.active_object
        left.parent = arrow_container
        left.scale = (pointer_length, arrow_size, arrow_size)

        right = left.copy()
        right.data = left.data.copy()
        bpy.context.scene.collection.objects.link(right)

        left.rotation_euler = (0, math.radians(pointer_angle), 0)
        right.rotation_euler = (0, math.radians(-pointer_angle), 0)
        left.location += Vector((arrow_scale[0] - 0.32, 0, left.scale[0] - 0.25))
        right.location += Vector((arrow_scale[0] - 0.32, 0, -left.scale[0] + 0.25))

        if dim == 1:
            arrow_container.location += Vector((arrow_scale[0] * 0.5, 0, -2))
            # x axis
        elif dim == 2:
            # y axis
            arrow_container.rotation_euler = (0, math.radians(-90), 0)
            arrow_container.location += Vector((-2, 0, arrow_scale[0] * 0.5))
        elif dim == 3:
            # z axis
            arrow_container.rotation_euler = (0, 0, math.radians(-90))
            arrow_container.location += Vector((-2, -2, arrow_scale[0] * 0.5))

    def create_x_label(self, label):
        ...
    
    def create_y_label(self, label):
        ...
    
    def create_z_label(self, label):
        ...


class OBJECT_OT_pie_chart(OBJECT_OT_generic_chart):
    '''Creates pie chart'''
    bl_idname = 'object.create_pie_chart'
    bl_label = 'Create pie chart'
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(
        name='Vertices',
        min=3,
        default=64
    )

    column: bpy.props.IntProperty(
        name='Column',
        default=1
    )

    label_column: bpy.props.IntProperty(
        name='Label column',
        default=0
    )

    start_from: bpy.props.IntProperty(
        name='Starting index',
        default=0
    )

    nof_entries: bpy.props.IntProperty(
        name='Entries',
        default=10
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0
    )

    def __init__(self):
        self.slices = []
        self.materials = []
    
    def execute(self, context):
        self.slices = []
        self.materials = []
        self.init_data()
        self.create_container()

        # create cylinder from triangles
        rot = 0
        rot_inc = 2.0 * math.pi / self.vertices
        scale = 1.0 / self.vertices * math.pi
        for i in range(0, self.vertices):
            cyl_slice = self.create_slice()
            cyl_slice.scale.y *= scale
            cyl_slice.rotation_euler.z = rot
            rot += rot_inc
            self.slices.append(cyl_slice)

        if bpy.data.scenes[0].dv_props.is_heading and self.start_from == 0:
            self.start_from = 1

        total = col_values_sum(self.data[self.start_from:self.start_from + self.nof_entries:], self.column)
        color_gen = sat_col_gen(self.nof_entries, *color_to_triplet(self.color_shade))
       
        prev_i = 0
        for i in range(self.start_from, self.start_from + self.nof_entries):
            value, _ = get_col_float(self.data[i], self.column)
            portion = value / total

            increment = round(portion * self.vertices)
            portion_end_i = prev_i + increment
            slice_obj = self.join_slices(prev_i, portion_end_i)

            slice_mat = self.new_mat(next(color_gen), 1)
            slice_obj.active_material = slice_mat
            label_rot_z = (((prev_i + portion_end_i) * 0.5) / self.vertices) * 2.0 * math.pi
            print('i: {} d: {}, p: {}, pfi: {}'.format(i, math.degrees(label_rot_z), portion, (prev_i + portion_end_i) * 0.5 / self.vertices))
            label_obj = self.add_value_label((1, 0, 0), (0, 0, label_rot_z), get_col_str(self.data[i], self.label_column), 0.2)
            label_obj.rotation_euler = (0, 0, 0)
            prev_i += increment
   
        return {'FINISHED'}

    def join_slices(self, i_from, i_to):
        bpy.ops.object.select_all(action='DESELECT')
        for i in range(i_from, i_to):
            if i > len(self.slices) - 1:
                print('IndexError: Cannot portion slices properly: i: {}, len(slices): {}, i_from: {}, i_to: {}'.format(i, len(self.slices), i_from, i_to))
                break
            self.slices[i].select_set(state=True)
            bpy.context.view_layer.objects.active = self.slices[i]
        if len(bpy.context.selected_objects) > 0:
            bpy.ops.object.join()
            return bpy.context.active_object

    def create_slice(self):
        '''
        Creates a triangle (slice of pie chart)
        '''
        verts = [(0, 0, 0.1), (-1, 1, 0.1), (-1, -1, 0.1), 
                 (0, 0, 0), (-1, 1, 0), (-1, -1, 0)
        ]

        facs = [[0, 1, 2], [3, 4, 5], [0, 1, 3], [1, 3, 4], [0, 2, 3], [2, 3, 5], [1, 2, 4], [2, 4, 5]]

        mesh = bpy.data.meshes.new('pie_mesh')  # add the new mesh
        obj = bpy.data.objects.new(mesh.name, mesh)
        col = bpy.data.collections.get('Collection')
        col.objects.link(obj)
        obj.parent = self.container_object
        bpy.context.view_layer.objects.active = obj

        mesh.from_pydata(verts, [], facs)
        mesh.update()

        return obj

    def add_value_label(self, location, rotation, col_text_value, scale_multiplier):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = str(col_text_value)
        to.data.align_x = 'CENTER'
        to.rotation_euler = rotation
        to.location = Vector(location) @ to.rotation_euler.to_matrix()
        to.location.z += 0.2
        to.location.x *= -1
        to.scale *= scale_multiplier
        to.parent = self.container_object
        return to

    def new_mat(self, color, alpha):
        mat = bpy.data.materials.new(name='Mat' + str(len(bpy.data.materials)))
        mat.diffuse_color = (*color, alpha)
        return mat

    def create_axis(self, dim):
        pass

    def create_labels(self):
        pass


class OBJECT_OT_line_chart(OBJECT_OT_generic_chart):
    '''Creates line chart as a line or as curve'''
    bl_idname = 'object.create_line_chart'
    bl_label = 'Create line chart'
    bl_options = {'REGISTER', 'UNDO'}

    column: bpy.props.IntProperty(
        name='Column',
        default=1
    )

    label_column: bpy.props.IntProperty(
        name='Label column',
        default=0
    )

    start_from: bpy.props.IntProperty(
        name='Starting index',
        default=0
    )

    nof_entries: bpy.props.IntProperty(
        name='Entries',
        default=10
    )

    rounded: bpy.props.EnumProperty(
        name='Rounded',
        items=(
            ('1', 'Rounded', 'Rounded corners'),
            ('2', 'Sharp', 'Sharp corners')
        )

    )

    def __init__(self):
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
    
    def execute(self, context):
        self.init_data()
        self.create_container()

        max_value, _ = col_values_max(self.data, self.column)
        value_gen = float_data_gen(self.data, self.column, self.label_column)
        
        norm_multiplier = 1.0 / max_value

        verts = []
        edges = []

        for i in range(self.start_from, self.start_from + self.nof_entries):
            value, _ = get_col_float(self.data[i], self.column)
            verts.append(((i - self.start_from) * self.x_delta, 0, value * norm_multiplier))
            if i != 0:
                edges.append([i - self.start_from - 1, i - self.start_from])
        
        curve_obj = self.create_curve(verts, edges)
        bevel_obj = self.add_bevel_obj(curve_obj)

        return {'FINISHED'}
    
    def create_curve(self, verts, edges):
        m = bpy.data.meshes.new('line_mesh')
        curve_obj = bpy.data.objects.new('curve_obj', m)

        bpy.context.scene.collection.objects.link(curve_obj)
        curve_obj.parent = self.container_object
        m.from_pydata(verts, edges, [])
        m.update()

        curve_obj.select_set(True)
        bpy.context.view_layer.objects.active = curve_obj
        
        self.bevel_curve_obj()

        bpy.ops.object.convert(target='CURVE')
        return curve_obj

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

    def add_bevel_obj(self, curve_obj):
        bpy.ops.mesh.primitive_plane_add()
        bevel_obj = bpy.context.active_object
        bevel_obj.scale = self.bevel_obj_size
        
        bpy.ops.object.convert(target='CURVE')
        curve_obj.data.bevel_object = bevel_obj
        return bevel_obj



class OBJECT_OT_point_chart(OBJECT_OT_generic_chart):
    '''Creates point chart'''
    ...


class OBJECT_OT_bar_chart(OBJECT_OT_generic_chart):
    '''Creates bar chart'''
    bl_idname = 'object.create_bar_chart'
    bl_label = 'Create bar chart'
    bl_options = {'REGISTER', 'UNDO'}

    heading = None

    text_size: bpy.props.FloatProperty(
        name='Text size',
        default=0.8
    )

    column: bpy.props.IntProperty(
        name='Column',
        default=1
    )
    create_labels: bpy.props.BoolProperty(
        name='Create labels',
        default=True
    )
    label_column: bpy.props.IntProperty(
        name='Label column',
        default=0
    )

    start_from: bpy.props.IntProperty(
        name='Starting index',
        default=0
    )

    nof_entries: bpy.props.IntProperty(
        name='Entries',
        default=10
    )

    def execute(self, context):
        self.init_data()
        self.create_container()
        self.create_axis(2)
        if self.start_from > len(self.data) or self.start_from + self.nof_entries > len(self.data):
            self.report('ERROR_INVALID_INPUT', 'Selected values are out of range of data')
            return {'CANCELLED'}

        if bpy.data.scenes[0].dv_props.is_heading:
            self.heading = self.data[0].value.split(',')
        else:
            self.heading = None
            
        self.data = self.data[self.start_from:self.start_from + self.nof_entries:]
        self.create_example_chart(context)

        return {'FINISHED'}
       
    def create_example_chart(self, context):
        data_len = len(self.data)
        
        # Properties that can be changeable in future
        spacing = 2
        text_offset = 1
        max_chart_height = 10

        # Find max value in given data set to normalize data
        max_value = self.parse_col_value(max(self.data, key=lambda x: self.parse_col_value(x.value.split(',')[self.column])).value.split(',')[self.column])
        scale_multiplier = 1 / (max_value[0] / max_chart_height)

        position = Vector((0, 0, 0))

        # Add heading
        if self.heading:
            bpy.ops.object.text_add(location=(position + Vector(((self.nof_entries * spacing) / 2.0 - spacing, 0, 26))))
            to = context.object
            to.data.body = str(self.heading[self.column])
            to.data.align_x = 'CENTER'
            to.rotation_euler = (math.radians(90), 0, 0)
            to.parent = self.container_object

        for i in range(data_len):

            if i is 0 and bpy.data.scenes[0].dv_props.is_heading:
                continue
    
            row_data = self.data[i].value.split(',')

            bpy.ops.mesh.primitive_cube_add()
            new_obj = context.active_object
            new_obj.location = position
            position = position + Vector((spacing, 0, 0))
            
            # column value calculation
            col_value, result = self.parse_col_value(row_data[self.column])

            if result is False:
                col_value = 1.0
                col_text_value = 'N/A'
            else:
                col_text_value = str(col_value)

            new_obj.scale.z *= col_value * scale_multiplier
            new_obj.location.z += col_value * scale_multiplier
            new_obj.parent = self.container_object
            
            if self.create_labels:
                self.add_value_label(context, new_obj.location, col_value, col_text_value, scale_multiplier, text_offset)
                self.add_desc_label(context, new_obj.location, row_data, col_value, scale_multiplier, text_offset)            
    
    def add_value_label(self, context, no_loc, col_value, col_text_value, scale_multiplier, text_offset):
        bpy.ops.object.text_add()
        to = context.object
        to.data.body = str(col_text_value)
        to.data.align_x = 'CENTER'
        to.rotation_euler = (math.radians(90), 0, 0)
        to.location = no_loc
        to.location.z += col_value * scale_multiplier + text_offset
        to.scale *= self.text_size
        to.parent = self.container_object

    def add_desc_label(self, context, no_loc, row_data, col_value, scale_multiplier, text_offset):
        bpy.ops.object.text_add()
        to = context.object
        to.data.body = str(row_data[self.label_column])
        to.data.align_x = 'CENTER'
        to.rotation_euler = (math.radians(90), 0, 0)
        to.location = no_loc
        to.location.z -= col_value * scale_multiplier + text_offset
        to.scale *= self.text_size
        to.parent = self.container_object

    def parse_col_value(self, col_value):
        try:
            return (float(col_value.replace('\'', '')), True)
        except (TypeError, ValueError) as exc:
            print('Cannot convert: ' + col_value)
            return (1.0, False)


class FILE_OT_DVLoadFiles(bpy.types.Operator):
    '''Loads data from CSV file'''
    bl_idname = 'ui.dv_load_data'
    bl_label = 'Load data'
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        name='CSV File',
        subtype='FILE_PATH'
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        lines_to_load = bpy.data.scenes[0].dv_props.line_count
        load_all = bpy.data.scenes[0].dv_props.all_lines
        bpy.data.scenes[0].dv_props.data.clear()
        with open(self.filepath, 'r') as file:
            line_n = 0
            for row in file:
                line_n += 1
                if not load_all and line_n > lines_to_load:
                    break
                row_prop = bpy.data.scenes[0].dv_props.data.add()
                row_prop.value = row
        print(f'File: {self.filepath}, loaded {line_n} lines!')
        return {'FINISHED'}

