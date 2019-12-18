import bpy
import bmesh
import csv
import math
from mathutils import Vector, Matrix
from .data_utils import get_col_float, get_col_str, col_values_sum, col_values_max, col_values_min_max, col_values_min, float_data_gen, float_range
from .color_utils import sat_col_gen, color_to_triplet

HALF_PI = math.pi * 0.5
GRAPH_Z_SCALE = 0.5


def is_fl_heading():
    return bpy.data.scenes[0].dv_props.is_heading


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
        self.container_object.empty_display_size = 1
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
    
    def create_y_axis(self, min_val, max_val, offset, padding):
        bpy.ops.object.empty_add()
        axis_cont = bpy.context.object
        axis_cont.name = 'Axis_Container'
        axis_cont.location = (0, 0, 0)
        axis_cont.parent = self.container_object

        bpy.ops.mesh.primitive_cube_add()
        line_obj = bpy.context.active_object
        line_obj.location = (0, 0, 0)

        line_obj.scale = (GRAPH_Z_SCALE + padding + offset * 0.5, 0.005, 0.005)
        line_obj.location.x += GRAPH_Z_SCALE + padding + offset * 0.5
        line_obj.parent = axis_cont

        line_obj.active_material = self.axis_mat

        spacing = 0.2 * GRAPH_Z_SCALE
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

            self.create_text_object(axis_cont, '{0:.3}'.format(float(val)), (i * spacing + offset, 0, 0.07), (HALF_PI, HALF_PI, 0))
            val += val_inc

        axis_cont.location += Vector((-padding, 0, -padding))
        axis_cont.rotation_euler.y -= HALF_PI
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
            to_rot = (HALF_PI, 0, 0)
            if dim == 'z':
                to_rot = (HALF_PI, 0, math.pi)
    
            self.create_text_object(axis_cont, vals[i], to_loc, to_rot)
        
        axis_cont.location += Vector((-padding, 0, -padding))
        if dim == 'z':
            axis_cont.rotation_euler.z += HALF_PI

        return v_len


    def create_text_object(self, axis_cont, text, location_offset, rotation_offset):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = str(text)
        to.data.align_x = 'CENTER'
        to.scale *= 0.05
        to.location = axis_cont.location
        to.location += Vector(location_offset)
        to.rotation_euler.x += rotation_offset[0]
        to.rotation_euler.y += rotation_offset[1]
        to.rotation_euler.z += rotation_offset[2]
        to.parent = axis_cont

    def new_mat(self, color, alpha, name='Mat'):
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = (*color, alpha)
        return mat

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
        
        found_min, res = col_values_min(self.data, self.column, self.start_from, self.nof_entries)
        if found_min <= 0:
            print('Warning: Pie chart does not support negative values!')
            return {'CANCELLED'}
        
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

        total = col_values_sum(self.data[self.start_from:self.start_from + self.nof_entries:], self.column)
        color_gen = sat_col_gen(self.nof_entries, *color_to_triplet(self.color_shade))
       
        prev_i = 0
        for i in range(self.start_from, self.start_from + self.nof_entries):
            
            if i >= len(self.data):
                break
            
            value, _ = get_col_float(self.data[i], self.column)

            portion = value / total

            increment = round(portion * self.vertices)
            
            # Ignore data with zero value
            if increment == 0:
                print('Warning: Data with zero value i: {}, value: {}! Useless for pie chart.'.format(i, value))
                continue

            portion_end_i = prev_i + increment
            slice_obj = self.join_slices(prev_i, portion_end_i)
            if slice_obj is None:
                raise Exception('Error occurred, try to increase number of vertices, i_from" {}, i_to: {}, inc: {}, val: {}'.format(prev_i, portion_end_i, increment, value))
                break

            slice_mat = self.new_mat(next(color_gen), 1)
            slice_obj.active_material = slice_mat
            slice_obj.parent = self.container_object
            label_rot_z = (((prev_i + portion_end_i) * 0.5) / self.vertices) * 2.0 * math.pi
            print('i: {} d: {}, p: {}, pfi: {}'.format(i, math.degrees(label_rot_z), portion, (prev_i + portion_end_i) * 0.5 / self.vertices))

            label_obj = self.add_value_label((1, 0, 0), (0, 0, label_rot_z), get_col_str(self.data[i], self.label_column), portion, 0.2)
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
        else:
            return None

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

    def add_value_label(self, location, rotation, label, portion, scale_multiplier):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = '{0}: {1:.2}'.format(label, portion)
        to.data.align_x = 'CENTER'
        to.rotation_euler = rotation
        to.location = Vector(location) @ to.rotation_euler.to_matrix()
        to.location.z += 0.2
        to.location.x *= -1
        to.scale *= scale_multiplier
        to.parent = self.container_object
        return to

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
        self.cuver_obj = None
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

        min_value, max_value = col_values_min_max(self.data, self.column, self.start_from, self.nof_entries)
        value_gen = float_data_gen(self.data, self.column, self.label_column)
        
        val_range = abs(min_value) + max_value

        norm_multiplier = GRAPH_Z_SCALE * 2.0 / val_range

        verts = []
        edges = []
        values = []
        labels = []
    
        for i in range(self.start_from, self.start_from + self.nof_entries):
            if i >= len(self.data):
                break

            value, _ = get_col_float(self.data[i], self.column)
            label = get_col_str(self.data[i], self.label_column)
            verts.append(((i - self.start_from) * self.x_delta, 0, value * norm_multiplier - min_value * norm_multiplier))
           
            values.append(value)
            labels.append(label)

            if i != 0:
                edges.append([i - self.start_from - 1, i - self.start_from])
        
        self.create_curve(verts, edges)
        self.add_value_labels(verts, values)
        bevel_obj = self.add_bevel_obj(self.curve_obj)
        
        self.create_axis(self.x_delta, labels, y_max=max_value, y_min=min_value, padding=(self.x_delta, self.x_delta, 0), offset=(self.x_delta, self.x_delta, 0))

        return {'FINISHED'}
    
    def add_value_labels(self, verts, values):
        for i, vert in enumerate(verts):
            bpy.ops.object.text_add()
            to = bpy.context.object
            to.data.body = str(values[i])
            to.location = vert
            to.data.align_x = 'CENTER'

            # TODO Whether label should be below or up (depends on the values next to it)
           
            st = 2  # steepness threshold

            if i - 1 >= 0 and i + 1 < len(values) and (values[i - 1] - st > values[i] or values[i + 1] - st > values[i]):
                to.location.z -= 0.05
                print('moving down')
            elif i - 1 >= 0 and values[i - 1] - st > values[i]:
                to.location.x += 0.05
                print('moving right')
            elif i + 1 < len(values) and values[i + 1] - st > values[i]:
                to.location.x -= 0.05
                print('moving left')
            else:
                print('moving up')
                to.location.z += 0.05

            to.location.z += 0.05
            to.rotation_euler.x += HALF_PI
            to.scale *= 0.05
            to.parent = self.container_object
            self.select_curve_obj()
            #bpy.ops.object.parent_set(type='VERTEX')

    def create_curve(self, verts, edges):
        m = bpy.data.meshes.new('line_mesh')
        self.curve_obj = bpy.data.objects.new('curve_obj', m)

        bpy.context.scene.collection.objects.link(self.curve_obj)
        self.curve_obj.parent = self.container_object
        m.from_pydata(verts, edges, [])
        m.update()

        self.select_curve_obj()
        
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

    def add_bevel_obj(self, curve_obj):
        bpy.ops.mesh.primitive_plane_add()
        bevel_obj = bpy.context.active_object
        bevel_obj.scale = self.bevel_obj_size
        
        bpy.ops.object.convert(target='CURVE')
        curve_obj.data.bevel_object = bevel_obj
        return bevel_obj

    def select_curve_obj(self):
        self.curve_obj.select_set(True)
        bpy.context.view_layer.objects.active = self.curve_obj


class OBJECT_OT_point_chart(OBJECT_OT_generic_chart):
    '''Creates point chart'''
    ...


class OBJECT_OT_bar_chart(OBJECT_OT_generic_chart):
    '''Creates bar chart'''
    bl_idname = 'object.create_bar_chart'
    bl_label = 'Create bar chart'
    bl_options = {'REGISTER', 'UNDO'}

    column: bpy.props.IntProperty(
        name='Column',
        default=1
    )
    axis_setting: bpy.props.BoolProperty(
        name='Create Axis',
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

    dimensions: bpy.props.EnumProperty(
        name='Dimensions',
        items=(
            ('1', '2D', 'Data + Top'),
            ('2', '3D', 'Data + Data + Top')
        )
    )

    def execute(self, context):
        self.init_data()
        self.create_container()

        if self.start_from > len(self.data) or self.start_from + self.nof_entries > len(self.data):
            self.report('ERROR_INVALID_INPUT', 'Selected values are out of range of data')
            return {'CANCELLED'}
            
        #self.data = self.data[self.start_from:self.start_from + self.nof_entries:]
        
        self.create_chart(context)

        return {'FINISHED'}
       
    def create_chart(self, context):
        
        # Properties that can be changeable in future
        spacing = 0.2
        text_offset = 1

        # Find max value in given data set to normalize data
        #max_value, _ = col_values_max(self.data, self.column, start=self.start_from, nof=self.nof_entries) 
        
        if self.dimensions == '1':
            min_value, max_value = col_values_min_max(self.data, self.column, start=self.start_from, nof=self.nof_entries)
            val_range = abs(min_value) + max_value
            z_scale_multiplier = GRAPH_Z_SCALE / val_range

            location = Vector((0, 0, 0))
            values = []
            for i in range(self.start_from, self.start_from + self.nof_entries):
                col_value, result = get_col_float(self.data[i], self.column)
                values.append(col_value)

                bpy.ops.mesh.primitive_cube_add()
                cube_obj = context.active_object
                cube_obj.location = (i * spacing + spacing * 0.5, 0, 0)
                cube_obj.scale.x = spacing * 0.5
                cube_obj.scale.y = spacing * 0.5
                
                if result is False:
                    col_value = 1.0

                if col_value == 0:
                    col_value = 0.01

                cube_obj.scale.z = col_value * z_scale_multiplier
                cube_obj.location.z = col_value * z_scale_multiplier - 2 * min_value * z_scale_multiplier
                
                bpy.ops.object.text_add()
                to = bpy.context.object
                to.data.body = str(col_value)
                to.location = cube_obj.location
                to.location.z += abs(cube_obj.scale.z) + 0.05
                to.data.align_x = 'CENTER'
                to.parent = self.container_object
                to.rotation_euler.x += HALF_PI
                to.scale *= 0.05
                
                cube_obj.parent = self.container_object
                
            if self.axis_setting:
                self.create_axis(spacing, values, max_value, min_value, offset=(spacing, spacing * 0.5, 0), padding=(spacing * 0.5, spacing * 0.5, 0))
        else:
            min_value, max_value = col_values_min_max(self.data, 2, start=self.start_from, nof=self.nof_entries)
            val_range = abs(min_value) + max_value
            z_scale_multiplier = GRAPH_Z_SCALE / val_range

            location = Vector((0, 0, 0))
            x_vals = [0, 1, 2, 3]
            z_vals = [0, 1, 2, 3]
            tops = []
            for i in range(self.start_from, self.start_from + self.nof_entries + 1):
                col_x, _ = get_col_float(self.data[i], 0)
                col_y, _ = get_col_float(self.data[i], 1)
                top, _ = get_col_float(self.data[i], 2)
                tops.append(top)
                
                bpy.ops.mesh.primitive_cube_add()
                cube_obj = context.active_object
                cube_obj.location = (col_x * spacing + spacing * 0.5, col_y * spacing + spacing * 0.5, 0)
                cube_obj.scale.x = spacing * 0.5
                cube_obj.scale.y = spacing * 0.5
                
                if top == 0:
                    top = 0.01

                cube_obj.scale.z = top * z_scale_multiplier
                cube_obj.location.z = top * z_scale_multiplier - 2 * min_value * z_scale_multiplier
                cube_obj.parent = self.container_object
                
            if self.axis_setting:
                self.create_axis(spacing, x_vals, max_value, min_value, z_vals=z_vals, offset=(spacing, spacing * 0.5, spacing * 0.5), padding=(spacing * 0.5, spacing * 0.5, spacing * 0.5))


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

