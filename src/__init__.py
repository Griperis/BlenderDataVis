import bpy
import csv
from mathutils import Vector
from math import radians

bl_info = {
    "name": "Data Visualisation Addon",
    "author": "Zdenek Dolezal",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic"
}


class PANEL_PT_DVAddonPanel(bpy.types.Panel):
    bl_label = "Data visualisation utilities"
    bl_idname = "OBJECT_PT_data_vis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Data visualisation'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(bpy.data.scenes[0].dv_props, 'line_count')
        
        row = layout.row()
        row.label(text="Data", icon='WORLD_DATA')
        row.operator("ui.dv_load_data")


        row = layout.row()
        row.label(text="Select chart")
        row.operator("object.create_bar_chart")


class FILE_OT_DVLoadFiles(bpy.types.Operator):
    bl_idname = "ui.dv_load_data"
    bl_label = "Load data"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        name="CSV File",
        subtype="FILE_PATH"
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        lines_to_load = bpy.data.scenes[0].dv_props.line_count
        print('Filepath:', self.filepath, ' lines to load: ', lines_to_load)
        bpy.data.scenes[0].dv_props.data.clear()
        with open(self.filepath, 'r') as file:
            line_n = 0
            for row in file:
                line_n += 1
                if (line_n > lines_to_load):
                    break
                row_prop = bpy.data.scenes[0].dv_props.data.add()
                row_prop.value = row
        return {'FINISHED'}


class DV_TableRowProp(bpy.types.PropertyGroup):
    value: bpy.props.StringProperty()


class DV_PropertyGroup(bpy.types.PropertyGroup):
    """All addon settings and data are stored in this group"""
    data: bpy.props.CollectionProperty(
        name="Data",
        type=DV_TableRowProp
    )
    line_count: bpy.props.IntProperty(
        name="Number of lines",
        default=10
    )


class OBJECT_OT_bar_chart(bpy.types.Operator):
    """Creates bar chart"""
    bl_idname = "object.create_bar_chart"
    bl_label = "Create bar chart"
    bl_options = {'REGISTER', 'UNDO'}

    data = [1, 2, 3, 4]

    text_size: bpy.props.FloatProperty(
        name="Text size", 
        default=0.4
    )

    column: bpy.props.IntProperty(
        name="Select column",
        default=1
    )

    @classmethod
    def poll(cls, context):
        return len(bpy.data.scenes[0].dv_props.data) > 0

    def invoke(self, context, event):
        context.window_manager
        self.data = bpy.data.scenes[0].dv_props.data
        #self.create_example_chart(context)
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        self.create_example_chart(context)

        return {'FINISHED'}

    def create_example_chart(self, context):
        cursor = context.scene.cursor.location
        data_len = len(self.data)
        
        # Properties that can be changeable in future
        spacing = 2
        text_offset = 1
        max_chart_height = 10

        # Find max value in given data set to normalize data
        max_value = self.parse_col(max(self.data, key=lambda x: self.parse_col(x.value.split(',')[self.column])).value.split(',')[self.column])
        scale_multiplier = 1 / (max_value / max_chart_height) 

        position = cursor
        
        for i in range(data_len):

            # TODO check whether first row is heading or not
            if i == 0:
                continue

            row_data = self.data[i].value.split(',')
            bpy.ops.mesh.primitive_cube_add()
            new_obj = context.active_object

            new_obj.location = position
            position = position + Vector((spacing, 0, 0))
            
            # column value calculation
            col_value = self.parse_col(row_data[self.column])

            new_obj.scale.z *= col_value * scale_multiplier
            new_obj.location.z += col_value * scale_multiplier

            # Add label for each object
            bpy.ops.object.text_add()
            to = context.object
            to.data.body = str(col_value)
            to.data.align_x = 'CENTER'
            to.rotation_euler = (radians(90), 0, 0)
            to.location = new_obj.location
            to.location.z += col_value * scale_multiplier + text_offset
            to.scale *= self.text_size

            bpy.ops.object.text_add()
            tlo = context.object
            tlo.data.body = str(row_data[0])
            tlo.data.align_x = 'CENTER'
            tlo.rotation_euler = (radians(90), 0, 0)
            tlo.location = new_obj.location
            tlo.location.z -= col_value * scale_multiplier + text_offset
            tlo.scale *= self.text_size

    def parse_col(self, col_value):
        try:
            return float(col_value.replace('"', ''))
        except Exception:
            print('Cannot convert: ' + col_value)
            return 1.0


def register():
    bpy.utils.register_class(DV_TableRowProp)
    bpy.utils.register_class(DV_PropertyGroup)
    bpy.utils.register_class(OBJECT_OT_bar_chart)
    bpy.utils.register_class(FILE_OT_DVLoadFiles)
    bpy.utils.register_class(PANEL_PT_DVAddonPanel)

    bpy.types.Scene.dv_props = bpy.props.PointerProperty(type=DV_PropertyGroup)


def unregister():
    bpy.utils.unregister_class(DV_PropertyGroup)
    bpy.utils.unregister_class(DV_TableRowProp)
    bpy.utils.unregister_class(PANEL_PT_DVAddonPanel)
    bpy.utils.unregister_class(OBJECT_OT_bar_chart)
    bpy.utils.unregister_class(FILE_OT_DVLoadFiles)

