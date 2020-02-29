import bpy

from src.general import OBJECT_OT_generic_chart, CONST
from src.utils.data_utils import get_data_as_ll, col_values_min_max
from src.utils.color_utils import sat_col_gen, color_to_triplet, reverse_iterator

from mathutils import Vector


class OBJECT_OT_point_chart(OBJECT_OT_generic_chart):
    '''Creates point chart'''
    bl_idname = 'object.create_point_chart'
    bl_label = 'Point Chart'
    bl_options = {'REGISTER', 'UNDO'}

    dimensions: bpy.props.EnumProperty(
        name='Dimensions',
        items=(
            ('1', '2D', 'Data + Top'),
            ('2', '3D', 'Data + Data + Top')
        )
    )

    point_scale: bpy.props.FloatProperty(
        name='Point scale',
        default=0.1
    )

    axis_step: bpy.props.FloatProperty(
        name='Axis step',
        default=1.0
    )
    x_axis_range: bpy.props.FloatVectorProperty(
        name='Range of x axis',
        size=2
    )
    y_axis_range: bpy.props.FloatVectorProperty(
        name='Range of y axis',
        size=2
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0
    )

    def execute(self, context):
        self.init_data()
        self.create_container()
        data_matrix = get_data_as_ll(self.data)

        if self.dimensions == '3D' and not math.sqrt(len(data_matrix)).is_integer():
            self.report({'ERROR'}, 'Data is in invalid shape for 3D chart')

        # fix pro 2D (aby se poslal spravny parametr)
        data_min, data_max = col_values_min_max(self.data, 3, 0, len(self.data))
        data_range = abs(data_min) + data_max
        z_scale_multiplier = CONST.GRAPH_Z_SCALE / data_range

        color_gen = reverse_iterator(sat_col_gen(len(self.data), *color_to_triplet(self.color_shade)))

        for i, row in enumerate(data_matrix):
            if len(row) > 3:
                self.report({'ERROR'}, 'Too many dimensions in data!')
                return {'CANCELLED'}
            bpy.ops.mesh.primitive_ico_sphere_add()
            sphere_obj = context.active_object
            sphere_obj.scale = Vector((self.point_scale, self.point_scale, self.point_scale))
            sphere_obj.active_material = self.new_mat(next(color_gen), 1)

            # normalize height
            row[2] *= z_scale_multiplier
            sphere_obj.location = Vector(row)

        return {'FINISHED'}
