import bpy
import math
from mathutils import Matrix, Vector

from data_vis.utils.data_utils import get_data_as_ll, find_data_range
from data_vis.utils.color_utils import sat_col_gen, ColorGen
from data_vis.general import OBJECT_OT_GenericChart
from data_vis.data_manager import DataManager, DataType


class OBJECT_OT_PieChart(OBJECT_OT_GenericChart):
    '''Creates Pie Chart, supports 2D Categorical values without labels'''
    bl_idname = 'object.create_pie_chart'
    bl_label = 'Pie Chart'
    bl_options = {'REGISTER', 'UNDO'}

    vertices: bpy.props.IntProperty(
        name='Vertices',
        min=3,
        default=64
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0
    )

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return not dm.has_labels and dm.is_type(DataType.Categorical, 2)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'vertices')
        row = layout.row()
        row.prop(self, 'color_shade')

    def execute(self, context):
        self.slices = []
        self.materials = []
        self.init_data()

        data_min = min(self.data, key=lambda entry: entry[1])[1]
        if data_min <= 0:
            self.report({'ERROR'}, 'Pie chart support only positive values!')

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

        values_sum = sum(int(entry[1]) for entry in self.data)
        data_len = len(self.data)
        color_gen = ColorGen(self.color_shade, (0, data_len))

        prev_i = 0
        for i in range(len(self.data)):

            portion = self.data[i][1] / values_sum

            increment = round(portion * self.vertices)
            # Ignore data with zero value
            if increment == 0:
                print('Warning: Data with zero value i: {}, value: {}! Useless for pie chart.'.format(i, self.data[i][1]))
                continue

            portion_end_i = prev_i + increment
            slice_obj = self.join_slices(prev_i, portion_end_i)
            if slice_obj is None:
                raise Exception('Error occurred, try to increase number of vertices, i_from" {}, i_to: {}, inc: {}, val: {}'.format(prev_i, portion_end_i, increment, self.data[i][1]))
                break

            slice_mat = self.new_mat(color_gen.next(data_len - i), 1)
            slice_obj.active_material = slice_mat
            slice_obj.parent = self.container_object
            label_rot_z = (((prev_i + portion_end_i) * 0.5) / self.vertices) * 2.0 * math.pi
            label_obj = self.add_value_label((1, 0, 0), (0, 0, label_rot_z), self.data[i][0], portion, 0.2, self.data[i][1])
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
                 (0, 0, 0), (-1, 1, 0), (-1, -1, 0)]

        faces = [[0, 1, 2], [3, 4, 5], [0, 1, 3], [1, 3, 4], [0, 2, 3], [2, 3, 5], [1, 2, 4], [2, 4, 5]]

        mesh = bpy.data.meshes.new('pie_mesh')
        obj = bpy.data.objects.new(mesh.name, mesh)
        col = bpy.data.collections.get('Collection')
        col.objects.link(obj)
        obj.parent = self.container_object
        bpy.context.view_layer.objects.active = obj

        mesh.from_pydata(verts, [], faces)
        mesh.update()

        return obj

    def add_value_label(self, location, rotation, label, portion, scale_multiplier, value):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = '{0}: {1}'.format(label, value)
        to.data.align_x = 'CENTER'
        to.rotation_euler = rotation
        to.location = Vector(location) @ to.rotation_euler.to_matrix()
        to.location.z += 0.2
        to.location.x *= -1
        to.scale *= scale_multiplier
        to.parent = self.container_object
        return to
