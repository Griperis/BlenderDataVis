import bpy
import bmesh
import csv
from mathutils import Vector
from math import radians


class OBJECT_OT_create_chart(bpy.types.Operator):
    """Creates chart"""
    bl_idname = "object.create_chart"
    bl_label = "Generic chart operator"
    bl_options = {'REGISTER', 'UNDO'}

    data = None

    def __init__(self):
        self.container_object = None

    @classmethod
    def poll(cls, context):
        """Default behavior for every chart poll method (when data is not available, cannot create chart)"""
        return len(bpy.data.scenes[0].dv_props.data) > 0

    def execute(self, context):
        raise NotImplementedError("Execute method should be implemented in every chart operator!")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def init_data(self):
        self.data = bpy.data.scenes[0].dv_props.data

    def create_container(self):
        self.container_object = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(self.container_object)
        self.container_object.empty_display_size = 2
        self.container_object.empty_display_type = 'PLAIN_AXES'
        self.container_object.name = "Chart_Container"
        # How to fix that?
        self.container_object.rotation_euler = (radians(180), 0, 0)

    def create_axis(self, dim=2):
        for d in range(dim):
            self.create_arrow(d + 1)
            
    def create_arrow(self, dim):
        
        arrow_length = 10
        arrow_size = 0.1

        pointer_angle = 30
        pointer_length = 0.5

        chart_origin = bpy.context.scene.cursor.location
        
        arrow_container = bpy.data.objects.new("empty", None)
        bpy.context.scene.collection.objects.link(arrow_container)
        arrow_container.parent = self.container_object
        arrow_container.name = "Axis"

        arrow_container.location = chart_origin
        arrow_scale = (arrow_length, arrow_size, arrow_size)
        bpy.ops.mesh.primitive_cube_add(location=chart_origin)
        obj = bpy.context.active_object
        obj.parent = arrow_container
        obj.scale = arrow_scale

        bpy.ops.mesh.primitive_cube_add(location=chart_origin)
        left = bpy.context.active_object
        left.parent = arrow_container
        left.scale = (pointer_length, arrow_size, arrow_size)

        right = left.copy()
        right.data = left.data.copy()
        bpy.context.scene.collection.objects.link(right)

        left.rotation_euler = (0, radians(pointer_angle), 0)
        right.rotation_euler = (0, radians(-pointer_angle), 0)
        left.location += (arrow_scale[0] - 0.32, 0, left.scale[0] - 0.25)
        right.location += (arrow_scale[0] - 0.32, 0, -left.scale[0] + 0.25)

        if dim == 1:
            arrow_container.location += Vector((arrow_scale[0] * 0.5, 0, -2))
            # x axis
        elif dim == 2:
            # y axis
            arrow_container.rotation_euler = (0, radians(-90), 0)
            arrow_container.location += Vector((-2, 0, arrow_scale[0] * 0.5))
        elif dim == 3:
            # z axis
            arrow_container.rotation_euler = (0, 0, radians(-90))
            arrow_container.location += Vector((-2, -2, arrow_scale[0] * 0.5))

    def create_labels(self, context):
        ...


class OBJECT_OT_pie_chart(OBJECT_OT_create_chart):
    """Creates pie chart"""
    bl_idname = "object.create_pie_chart"
    bl_label = "Create pie chart"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        self.init_data()
        bpy.ops.mesh.primitive_cylinder_add()
        obj = context.active_object
        obj.parent = self.container_object
        bpy.ops.object.create_chart_axis()
        return {'FINISHED'}


class OBJECT_OT_bar_chart(OBJECT_OT_create_chart):
    """Creates bar chart"""
    bl_idname = "object.create_bar_chart"
    bl_label = "Create bar chart"
    bl_options = {'REGISTER', 'UNDO'}

    heading = None

    text_size: bpy.props.FloatProperty(
        name="Text size",
        default=0.4
    )

    column: bpy.props.IntProperty(
        name="Column",
        default=1
    )

    label_column: bpy.props.IntProperty(
        name="Label column",
        default=1
    )

    start_from: bpy.props.IntProperty(
        name="Starting index",
        default=0
    )

    nof_entries: bpy.props.IntProperty(
        name="Entries",
        default=10
    )

    def execute(self, context):
        self.init_data()
        self.create_container()
        self.create_axis(2)
        if self.start_from > len(self.data) or self.start_from + self.nof_entries > len(self.data):
            self.report('ERROR_INVALID_INPUT', 'Selected values are out of range of data')
            return {'CANCELLED'}

        if bpy.data.scenes[0].dv_props.is_heading:
            self.heading = self.data[0].value.split(',')
        else:
            self.heading = None
            
        self.data = self.data[self.start_from:self.start_from + self.nof_entries:]
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
        max_value = self.parse_col_value(max(self.data, key=lambda x: self.parse_col_value(x.value.split(',')[self.column])).value.split(',')[self.column])
        scale_multiplier = 1 / (max_value[0] / max_chart_height) 

        position = cursor

        # Add heading
        if (self.heading is not None):
            bpy.ops.object.text_add(location=(position + Vector(((self.nof_entries * spacing) / 2.0 - spacing, 0, 26))))
            to = context.object
            to.data.body = str(self.heading[self.column])
            to.data.align_x = 'CENTER'
            to.rotation_euler = (radians(90), 0, 0)

        for i in range(data_len):

            # First row should be heading
            row_data = self.data[i].value.split(',')

            bpy.ops.mesh.primitive_cube_add()
            new_obj = context.active_object
            new_obj.location = position
            position = position + Vector((spacing, 0, 0))
            
            # column value calculation
            col_value, result = self.parse_col_value(row_data[self.column])

            if result is False:
                col_value = 1.0
                col_text_value = 'N/A'
            else:
                col_text_value = str(col_value)

            new_obj.scale.z *= col_value * scale_multiplier
            new_obj.location.z += col_value * scale_multiplier
            new_obj.parent = self.container_object

            # Add value label
            bpy.ops.object.text_add()
            to = context.object
            to.data.body = str(col_text_value)
            to.data.align_x = 'CENTER'
            to.rotation_euler = (radians(90), 0, 0)
            to.location = new_obj.location
            to.location.z += col_value * scale_multiplier + text_offset
            to.scale *= self.text_size
            to.parent = self.container_object


            # Description label
            bpy.ops.object.text_add()
            tlo = context.object
            tlo.data.body = str(row_data[self.label_column])
            tlo.data.align_x = 'CENTER'
            tlo.rotation_euler = (radians(90), 0, 0)
            tlo.location = new_obj.location
            tlo.location.z -= col_value * scale_multiplier + text_offset
            tlo.scale *= self.text_size
            tlo.parent = self.container_object

    def create_label():
        ...

    def parse_col_value(self, col_value):
        try:
            return (float(col_value.replace('"', '')), True)
        except (TypeError, ValueError) as exc:
            print('Cannot convert: ' + col_value)
            return (1.0, False)


class FILE_OT_DVLoadFiles(bpy.types.Operator):
    """Loads data from CSV file"""
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
        load_all = bpy.data.scenes[0].dv_props.all_lines
        bpy.data.scenes[0].dv_props.data.clear()
        with open(self.filepath, 'r') as file:
            line_n = 0
            for row in file:
                line_n += 1
                if (not load_all and line_n > lines_to_load):
                    break
                row_prop = bpy.data.scenes[0].dv_props.data.add()
                row_prop.value = row
        print(f'File: {self.filepath}, loaded {line_n} lines!')
        return {'FINISHED'}

