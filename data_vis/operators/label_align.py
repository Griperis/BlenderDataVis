import bpy
from mathutils import Vector, Quaternion
from math import radians


class DV_AlignLabels(bpy.types.Operator):
    bl_idname = 'data_vis.align_labels'
    bl_label = 'Align Labels'
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = 'Aligns labels to currently active camera or to the view'

    align_header: bpy.props.BoolProperty(
        default=True,
        name='Align Header',
        description='If true then header is aligned'
    )

    align_axis_labels: bpy.props.BoolProperty(
        default=True,
        name='Align Axis Labels',
        description='If true then axis labels are aligned'
    )

    align_target: bpy.props.EnumProperty(
        name='Align Target',
        description='Select target to align labels to',
        items=[
            ('view', 'View', 'Align to the scene 3D view location'),
            ('camera', 'Camera', 'Align to active camera')
        ]
    )

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.scene.camera is not None

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'align_header')
        layout.prop(self, 'align_axis_labels')
        layout.prop(self, 'align_target', text='')

    def execute(self, context):
        axis_count = 0
        is_pie = False
        for child in bpy.context.object.children:
            if 'Axis_Container_AxisDir.X' in child.name:
                self.align_labels(context, 'x', child)
                axis_count += 1
            elif 'Axis_Container_AxisDir.Y' in child.name:
                self.align_labels(context, 'y', child)
                axis_count += 1
            elif 'Axis_Container_AxisDir.Z' in child.name:
                self.align_labels(context, 'z', child)
                axis_count += 1

            if child.name.startswith('TextPie'):
                self.align_labels(context, 'to', child)
                is_pie = True
            if child.name == 'TextHeader':
                if not self.align_header:
                    continue
                self.align_labels(context, 'to', child)

        if axis_count in [2, 3] or is_pie:
            self.report({'INFO'}, 'Labels aligned!')
            return {'FINISHED'}
        else:   
            self.report({'WARNING'}, 'Select valid chart container!')
            return {'CANCELLED'}

    def invoke(self, context: bpy.types.Context, event):
        return context.window_manager.invoke_props_dialog(self)

    def align_labels(self, context, obj_type, obj):
        cam_vector = self.get_align_target_vector(context)

        if obj_type == 'to':
            obj.rotation_euler = cam_vector
            return
        
        if not self.align_axis_labels:
            return

        for child in obj.children:
            if child.name.startswith('Text'):
                if child.name.startswith('TextLabel') and not self.align_axis_labels:
                    continue
                if obj_type == 'z':
                    child.rotation_euler = (radians(180), radians(90) - cam_vector[2], radians(90))
                elif obj_type == 'y':
                    child.rotation_euler = Vector(cam_vector) - Vector(obj.rotation_euler)
                else:
                    child.rotation_euler = cam_vector
    
    def get_align_target_vector(self, context: bpy.types.Context):
        if self.align_target == 'camera':
            return context.scene.camera.rotation_euler
        elif self.align_target == 'view':
            return Quaternion.to_euler(context.region_data.view_rotation)
        else:
            raise ValueError('Invalid align target!')