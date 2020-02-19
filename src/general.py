
import bpy
import math

from mathutils import Vector


class CONST:
    GRAPH_Z_SCALE = 0.5
    HALF_PI = math.pi * 0.5


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
    