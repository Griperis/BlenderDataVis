import bpy
import math
from mathutils import Vector


from src.utils.data_utils import float_data_gen, col_values_min_max, get_col_float, get_col_str
from src.general import OBJECT_OT_generic_chart
from src.general import CONST


class OBJECT_OT_line_chart(OBJECT_OT_generic_chart):
    '''Creates line chart as a line or as curve'''
    bl_idname = 'object.create_line_chart'
    bl_label = 'Line Chart'
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
        name='Ending index',
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

        norm_multiplier = CONST.GRAPH_Z_SCALE * 2.0 / val_range

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
        
        self.create_axis(self.x_delta, labels, y_max=max_value, y_min=min_value, padding=(self.x_delta * 0.5, self.x_delta * 0.5, 0), offset=(self.x_delta * 0.5, self.x_delta * 0.5, 0))

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
            to.rotation_euler.x += CONST.HALF_PI
            to.scale *= 0.05
            to.parent = self.container_object
            self.select_curve_obj()

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
