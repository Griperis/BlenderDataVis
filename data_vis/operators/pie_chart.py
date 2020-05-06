import bpy
import math
from mathutils import Matrix, Vector

from data_vis.utils.data_utils import find_data_range
from data_vis.general import OBJECT_OT_GenericChart, DV_HeaderPropertyGroup, DV_LegendPropertyGroup
from data_vis.data_manager import DataManager, DataType
from data_vis.colors import ColorGen, ColorType
from data_vis.operators.features.legend import Legend


class OBJECT_OT_PieChart(OBJECT_OT_GenericChart):
    '''Creates Pie Chart, supports 2D Categorical values without labels'''
    bl_idname = 'object.create_pie_chart'
    bl_label = 'Pie Chart'
    bl_options = {'REGISTER', 'UNDO'}

    header_settings: bpy.props.PointerProperty(
        type=DV_HeaderPropertyGroup
    )

    legend_settings: bpy.props.PointerProperty(
        type=DV_LegendPropertyGroup
    )

    vertices: bpy.props.IntProperty(
        name='Vertices',
        min=3,
        default=64
    )

    text_size: bpy.props.FloatProperty(
        name='Label Size',
        min=0.01,
        default=0.05
    )

    create_labels: bpy.props.BoolProperty(
        name='Create Labels',
        default=True
    )

    label_distance: bpy.props.FloatProperty(
        name='Label Distance',
        min=0.0,
        default=0.5,
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0
    )

    color_type: bpy.props.EnumProperty(
        name='Coloring Type',
        items=(
            ('0', 'Gradient', 'Gradient based on value'),
            ('1', 'Constant', 'One color'),
            ('2', 'Random', 'Random colors'),
        ),
        default='0',
        description='Type of coloring for chart'
    )

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return not dm.has_labels and dm.is_type(DataType.Categorical, [2])

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        box = layout.box()
        box.label(icon='COLOR', text='Color settings:')
        box.prop(self, 'color_type')
        if self.color_type != '2':
            box.prop(self, 'color_shade')

        box = layout.box()
        box.prop(self, 'vertices')
        box.prop(self, 'create_labels')
        if self.create_labels:
            box.prop(self, 'label_distance')
            box.prop(self, 'text_size')

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
        color_gen = ColorGen(self.color_shade, ColorType.str_to_type(self.color_type), (0, data_len))

        prev_i = 0
        legend_data = {}
        for i in range(data_len):

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

            slice_mat = color_gen.get_material(data_len - i)
            slice_obj.active_material = slice_mat
            slice_obj.parent = self.container_object
            if self.create_labels:
                label_rot_z = (((prev_i + portion_end_i) * 0.5) / self.vertices) * 2.0 * math.pi
                label_obj = self.add_value_label((self.label_distance, 0, 0), (0, 0, label_rot_z), self.data[i][0], portion, self.data[i][1])
                label_obj.rotation_euler = (0, 0, 0)
            prev_i += increment

            legend_data[str(slice_mat.name)] = self.data[i][0] 

        if self.header_settings.create:
            self.create_header((0, 0.7, 0.15), False)

        if self.legend_settings.create:
            Legend(self.chart_id, self.legend_settings, legend_data).create(self.container_object)
    
        self.select_container()
        return {'FINISHED'}

    def join_slices(self, i_from, i_to):
        bpy.ops.object.select_all(action='DESELECT')
        if i_to > len(self.slices) - 1:
            i_to = len(self.slices) - 1
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
        slice_size = 0.5
        verts = [(0, 0, 0.1), (-slice_size, slice_size, 0.1), (-slice_size, -slice_size, 0.1),
                 (0, 0, 0), (-slice_size, slice_size, 0), (-slice_size, -slice_size, 0)]

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

    def add_value_label(self, location, rotation, label, portion, value):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = '{0}: {1}'.format(label, value)
        to.data.align_x = 'CENTER'
        to.rotation_euler = rotation
        to.location = Vector(location) @ to.rotation_euler.to_matrix()
        to.location.z += 0.15
        to.scale *= self.text_size
        to.parent = self.container_object

        mat = bpy.data.materials.get('DV_TextMat_' + str(self.chart_id))
        if mat is None:
            mat = bpy.data.materials.new(name='DV_TextMat_' + str(self.chart_id))

        to.data.materials.append(mat)
        to.active_material = mat
        return to
