import bpy
import math
from mathutils import Matrix, Vector

from src.utils.data_utils import col_values_min, col_values_sum, get_col_float, get_col_str
from src.utils.color_utils import sat_col_gen, color_to_triplet
from src.general import OBJECT_OT_generic_chart, CONST


class OBJECT_OT_pie_chart(OBJECT_OT_generic_chart):
    '''Creates pie chart'''
    bl_idname = 'object.create_pie_chart'
    bl_label = 'Pie Chart'
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
        name='Ending index',
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
            self.report({'WARNING'}, 'Pie chart does not support negative values')
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
