import bpy
import math
from mathutils import Vector


from src.utils.data_utils import get_col_float, get_col_str, col_values_sum, col_values_min_max
from src.utils.color_utils import sat_col_gen, color_to_triplet, reverse_iterator
from src.general import OBJECT_OT_generic_chart, CONST


class OBJECT_OT_bar_chart(OBJECT_OT_generic_chart):
    '''Creates bar chart'''
    bl_idname = 'object.create_bar_chart'
    bl_label = 'Bar Chart'
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
        name='Ending index',
        default=10
    )

    dimensions: bpy.props.EnumProperty(
        name='Dimensions',
        items=(
            ('1', '2D', 'Data + Top'),
            ('2', '3D', 'Data + Data + Top')
        )
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

        if self.start_from > len(self.data) or self.start_from + self.nof_entries > len(self.data):
            self.report('ERROR_INVALID_INPUT', 'Selected values are out of range of data')
            return {'CANCELLED'}
            
        #self.data = self.data[self.start_from:self.start_from + self.nof_entries:]
        
        self.create_chart(context)

        return {'FINISHED'}
    
    def add_label(self, cube_obj, index):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = get_col_str(self.data[index], self.label_column)
        to.location = cube_obj.location
        to.location.z += abs(cube_obj.scale.z) + 0.05
        to.data.align_x = 'CENTER'
        to.parent = self.container_object
        to.rotation_euler.x += CONST.HALF_PI
        to.scale *= 0.05

    def create_chart(self, context):
        # Properties that can be changeable in future
        spacing = 0.2
        text_offset = 1

        # Find max value in given data set to normalize data
        #max_value, _ = col_values_max(self.data, self.column, start=self.start_from, nof=self.nof_entries) 
        color_gen = reverse_iterator(sat_col_gen(self.nof_entries + 1, *color_to_triplet(self.color_shade)))
        #chart_mat = self.new_mat((1, 1, 1), 1, name='Bar_Chart_Mat')
        if self.dimensions == '1':
            min_value, max_value = col_values_min_max(self.data, self.column, start=self.start_from, nof=self.nof_entries)
            val_range = abs(min_value) + max_value
            z_scale_multiplier = CONST.GRAPH_Z_SCALE / val_range

            location = Vector((0, 0, 0))
            values = []
            for i in range(self.start_from, self.start_from + self.nof_entries):
                col_value, result = get_col_float(self.data[i], self.column)
                values.append(col_value)

                bpy.ops.mesh.primitive_cube_add()
                cube_obj = context.active_object
                cube_obj.active_material = self.new_mat(next(color_gen), 1)
                cube_obj.location = (i * spacing + spacing * 0.5, 0, 0)
                cube_obj.scale.x = spacing * 0.5
                cube_obj.scale.y = spacing * 0.5
                
                if result is False:
                    col_value = 1.0

                if col_value == 0:
                    col_value = 0.01

                cube_obj.scale.z = col_value * z_scale_multiplier
                cube_obj.location.z = col_value * z_scale_multiplier - 2 * min_value * z_scale_multiplier
                
                self.add_label(cube_obj, i)

                cube_obj.parent = self.container_object
                
            if self.axis_setting:
                self.create_axis(spacing, values, max_value, min_value, offset=(spacing, spacing * 0.5, 0), padding=(spacing * 0.5, spacing * 0.5, 0))
        else:
            min_value, max_value = col_values_min_max(self.data, 2, start=self.start_from, nof=self.nof_entries + 1)
            print('maxik:', max_value)
            val_range = abs(min_value) + max_value
            z_scale_multiplier = CONST.GRAPH_Z_SCALE / val_range

            location = Vector((0, 0, 0))
            x_vals = set()

            z_vals = set()
            tops = []
            for i in range(self.start_from, self.start_from + self.nof_entries + 1):
                col_x, _ = get_col_float(self.data[i], 0)
                col_y, _ = get_col_float(self.data[i], 1)
                top, _ = get_col_float(self.data[i], 2)
                tops.append(top)
                x_vals.add(col_x)
                z_vals.add(col_y)

                bpy.ops.mesh.primitive_cube_add()
                cube_obj = context.active_object
                cube_obj.active_material = self.new_mat(next(color_gen), 1)
                cube_obj.location = (col_x * spacing + spacing * 0.5, col_y * spacing + spacing * 0.5, 0)
                cube_obj.scale.x = spacing * 0.5
                cube_obj.scale.y = spacing * 0.5
                
                if top == 0:
                    top = 0.01

                cube_obj.scale.z = top * z_scale_multiplier
                cube_obj.location.z = top * z_scale_multiplier - 2 * min_value * z_scale_multiplier
                cube_obj.parent = self.container_object
                
            if self.axis_setting:
                self.create_axis(spacing, list(x_vals), max_value, min_value, z_vals=list(z_vals), offset=(spacing, spacing * 0.5, spacing * 0.5), padding=(spacing * 0.5, spacing * 0.5, spacing * 0.5))

