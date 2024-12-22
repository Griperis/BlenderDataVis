# ©copyright Zdenek Dolezal 2024-, License GPL
# Generic Chart (non geonodes) - base class implementation, UI drawing

import bpy
import math
import typing

from mathutils import Vector
from .data_manager import DataManager, DataType
from .icon_manager import IconManager
from .utils.data_utils import find_axis_range, normalize_value
from .colors import ColorType


class OBJECT_OT_GenericChart(bpy.types.Operator):
    """
    Encapsulation of common methods for charts, when creating new chart operator inherit this
    Naming property pointers to property groups from properties.py correctly can handle UI drawing e. g. in bar_chart.py
    """

    bl_idname = "object.create_chart"
    bl_label = "Generic chart operator"
    bl_options = {'REGISTER', 'UNDO', "INTERNAL"}

    data = None
    axis_mat = None
    chart_id = 0

    def __init__(self):
        self.container_object = None
        self.labels = []
        self.dm = DataManager()
        self.prev_anim_setting = False
        self.prev_auto_step = False
        self.container_size = Vector((1, 1, 1))
        if hasattr(self, "dimensions"):
            self.dimensions = str(self.dm.get_dimensions())

        if hasattr(self, "data_type"):
            self.data_type = (
                "0" if self.dm.predicted_data_type == DataType.Numerical else "1"
            )

        self.chart_id = OBJECT_OT_GenericChart.chart_id
        OBJECT_OT_GenericChart.chart_id += 1

    def draw(self, context):
        layout = self.layout
        if hasattr(self, "data_type") or hasattr(self, "dimensions"):
            box = layout.box()
            box.label(
                icon_value=IconManager().get_icon("addon_icon").icon_id,
                text="Chart settings:",
            )
        if self.dm.predicted_data_type != DataType.Categorical and hasattr(
            self, "data_type"
        ):
            row = box.row()
            row.use_property_split = True
            row.prop(self, "data_type")

        numerical = True
        if hasattr(self, "data_type"):
            if self.data_type == "1":
                numerical = False

        if (
            hasattr(self, "dimensions")
            and self.dm.predicted_data_type != DataType.Categorical
        ):
            if hasattr(self, "only_2d") and self.only_2d is True:
                draw_dims = False
            else:
                draw_dims = True

            if numerical and draw_dims:
                row = box.row()
                row.use_property_split = True
                row.prop(self, "dimensions")
            else:
                self.dimensions = "2"
        if hasattr(self, "header_settings"):
            self.draw_header_settings(layout)
        if hasattr(self, "axis_settings"):
            self.draw_axis_settings(layout, numerical)
        if hasattr(self, "legend_settings"):
            self.draw_legend_settings(layout)
        if hasattr(self, "color_settings"):
            self.draw_color_settings(layout)
        if hasattr(self, "anim_settings"):
            self.draw_anim_settings(layout)

    def draw_header_settings(self, layout):
        box = layout.box()
        box.use_property_split = True
        row = box.row()
        row.label(text="Header:", icon="BOLD")
        row.prop(self.header_settings, "create")
        if self.header_settings.create:
            if self.header_settings.text == "None":
                self.header_settings.text = self.bl_label
            box.prop(self.header_settings, "text")
            box.prop(self.header_settings, "size")

    def draw_legend_settings(self, layout):
        box = layout.box()
        box.use_property_split = True
        row = box.row()
        row.label(icon="WORDWRAP_ON", text="Legend:")
        row.prop(self.legend_settings, "create")
        if self.legend_settings.create:
            box.prop(self.legend_settings, "position")
            box.prop(self.legend_settings, "item_size")

    def draw_anim_settings(self, layout):
        if not self.dm.animable:
            return
        box = layout.box()
        box.use_property_split = True
        row = box.row()
        row.label(icon="TIME", text="Animation:")
        row.prop(self.anim_settings, "animate")
        if self.anim_settings.animate:
            box.prop(self.anim_settings, "key_spacing")
        if self.anim_settings.animate != self.prev_anim_setting:
            self.use_anim_range(self.anim_settings.animate)
            self.prev_anim_setting = self.anim_settings.animate

        if hasattr(self, "extend_anim_draw"):
            self.extend_anim_draw(box)

    def draw_label_settings(self, box):
        box.use_property_split = True
        row = box.row()
        row.label(icon="FILE_FONT", text="Labels:")
        row.prop(self.label_settings, "create")
        if self.label_settings.create:
            if self.dm.has_labels:
                box.prop(self.label_settings, "from_data")
            if not self.label_settings.from_data or not self.dm.has_labels:
                col = box.column(align=True)
                col.prop(self.label_settings, "x_label")
                if self.dm.get_dimensions() == 3:
                    col.prop(self.label_settings, "y_label")
                col.prop(self.label_settings, "z_label")

    def draw_color_settings(self, layout):
        if hasattr(self, "color_settings"):
            box = layout.box()
            box.use_property_split = True
            row = box.row()
            row.label(icon="COLOR", text="Colors:")
            row.prop(self.color_settings, "use_shader")
            box.prop(self.color_settings, "color_type")
            if (
                not ColorType.str_to_type(self.color_settings.color_type)
                == ColorType.Random
            ):
                box.prop(self.color_settings, "color_shade")

    def draw_axis_settings(self, layout, numerical):
        box = layout.box()
        row = box.row()
        row.use_property_split = True
        row.label(icon="ORIENTATION_VIEW", text="Axis:")
        row.prop(self.axis_settings, "create")

        row = box.row()
        row.label(text="Data Ranges:", icon="ARROW_LEFTRIGHT")
        row = box.row()
        if self.dm.predicted_data_type != DataType.Categorical:
            row.prop(self.axis_settings, "x_range", text="X")
        if hasattr(self, "dimensions") and self.dimensions == "3":
            row = box.row()
            row.prop(self.axis_settings, "y_range", text="Y")
        row = box.row()
        row.prop(self.axis_settings, "z_range", text="Z")

        if not self.axis_settings.create:
            return

        row = box.row()
        row.use_property_split = True
        row.prop(self.axis_settings, "auto_steps")

        if self.prev_auto_step != self.axis_settings.auto_steps:
            self.axis_settings.x_step = self.dm.get_step_size("x")
            self.axis_settings.y_step = self.dm.get_step_size("y")
            self.axis_settings.z_step = self.dm.get_step_size("z")
            self.prev_auto_step = self.axis_settings.auto_steps

        if not self.axis_settings.auto_steps:
            row = box.row()
            row.prop(self.axis_settings, "x_step", text="X")
            if hasattr(self, "dimensions") and self.dimensions == "3":
                row.prop(self.axis_settings, "y_step", text="Y")
            row.prop(self.axis_settings, "z_step", text="Z")

        row = box.row()
        row.prop(self.axis_settings, "z_position")
        row = box.row()
        row.prop(self.axis_settings, "padding")
        row.prop(self.axis_settings, "thickness")
        row.prop(self.axis_settings, "tick_mark_height")
        box.separator()
        row = box.row()
        row.label(text="Ticks:", icon="FONT_DATA")
        row = box.row()
        row.prop(self.axis_settings, "number_format")
        row = box.row()
        row.prop(self.axis_settings, "text_size")
        row.prop(self.axis_settings, "decimal_places")
        box.separator()
        self.draw_label_settings(box)

    @classmethod
    def poll(cls, context):
        """Default behavior for every chart poll method (when data is not available, cannot create chart)"""
        return self.dm.parsed_data is not None

    def execute(self, context):
        raise NotImplementedError(
            "Execute method should be implemented in every chart operator!"
        )

    def invoke(self, context, event):
        """When user clicks on operator button, invoke is called, if subclass has axis_settings defined, ranges are initialized, if init_props is defined it is called"""
        if hasattr(self, "axis_settings"):
            self.init_ranges()

        if hasattr(self, "init_props"):
            self.init_props()

        self.container_size = context.scene.general_props.container_size

        return context.window_manager.invoke_props_dialog(self)

    def init_ranges(self):
        self.axis_settings.x_range = self.dm.get_range("x")
        self.axis_settings.y_range = self.dm.get_range("y")
        if (
            self.dm.dimensions > 2
            and hasattr(self, "dimensions")
            and self.dimensions == "2"
        ):
            self.axis_settings.y_range = self.dm.get_range("z")
        self.axis_settings.z_range = self.dm.get_range("z")
        if hasattr(self, "anim_settings") and self.anim_settings.animate:
            self.axis_settings.z_range = self.dm.get_range("z_anim")

    def use_anim_range(self, is_anim):
        if is_anim:
            self.axis_settings.z_range = self.dm.get_range("z_anim")
        else:
            self.axis_settings.z_range = self.dm.get_range("z")

    def create_container(self):
        bpy.ops.object.empty_add()
        self.container_object = bpy.context.object
        self.container_object.empty_display_type = "PLAIN_AXES"
        self.container_object.name = self.bl_label + "_" + str(self.chart_id)
        self.container_object.location = bpy.context.scene.cursor.location

    def data_type_as_enum(self):
        if not hasattr(self, "data_type"):
            return DataType.Numerical

        if self.data_type == "0":
            return DataType.Numerical
        elif self.data_type == "1":
            return DataType.Categorical

    def new_mat(self, color, alpha, name="Mat"):
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = (*color, alpha)
        return mat

    def init_data(self, subtype=None):
        if hasattr(self, "label_settings"):
            self.init_labels()

        if (
            hasattr(self, "anim_settings")
            and self.prev_anim_setting != self.anim_settings.animate
        ):
            self.use_anim_range(self.anim_settings.animate)
        self.data = self.dm.get_parsed_data(subtype=subtype)

    def init_labels(self):
        if not self.label_settings.create:
            self.labels = (None, None, None)
            return
        if self.dm.has_labels and self.label_settings.from_data:
            first_line = self.dm.get_labels()
            length = len(first_line)
            if length == 2:
                self.labels = (first_line[0], "", first_line[1])
            elif length == 3:
                self.labels = (first_line[0], first_line[1], first_line[2])
            else:
                self.report({'ERROR'}, "Unsupported number of labels on first line")
        else:
            self.labels = [
                self.label_settings.x_label,
                self.label_settings.y_label,
                self.label_settings.z_label,
            ]

    def init_range(self, data):
        self.axis_settings.x_range = find_axis_range(data, 0)
        self.axis_settings.y_range = find_axis_range(data, 1)

    def in_axis_range_bounds_new(self, entry):
        """
        Checks whether the entry point defined as [x, y, z] is within user selected axis range
        returns False if not in range, else True
        """
        entry_dims = len(entry)
        if entry_dims == 2 or entry_dims >= 3:
            if (
                hasattr(self, "data_type")
                and self.data_type_as_enum() != DataType.Numerical
            ):
                return True

            if (
                entry[0] < self.axis_settings.x_range[0]
                or entry[0] > self.axis_settings.x_range[1]
            ):
                return False

        if entry_dims >= 3:
            if (
                entry[1] < self.axis_settings.y_range[0]
                or entry[1] > self.axis_settings.y_range[1]
            ):
                return False

        return True

    def select_container(self):
        """Makes container object active and selects it"""
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = self.container_object
        self.container_object.select_set(True)

    def create_header(self, location=None, rotate=True):
        """Creates header at container + offset"""
        bpy.ops.object.text_add()
        obj = bpy.context.object
        obj.name = "TextHeader"
        obj.data.align_x = "CENTER"
        obj.data.body = self.header_settings.text
        if location is None:
            # default location
            obj.location = Vector(
                (self.container_size[0] * 0.5, 0, self.container_size[2] + 0.2)
            )
        else:
            obj.location = location

        obj.scale *= self.header_settings.size
        header_mat = bpy.data.materials.new(name="DV_HeaderMat_" + str(self.chart_id))
        obj.data.materials.append(header_mat)
        obj.active_material = header_mat
        if rotate:
            obj.rotation_euler.x = math.radians(90)
        obj.parent = self.container_object

    def get_name(self):
        """Returns chart container name"""
        return self.container_object.name

    def normalize_value(self, value, direction):
        axis_range = None
        size = None
        if direction == "x":
            axis_range = self.axis_settings.x_range
            size = self.container_size[0]
        elif direction == "y":
            axis_range = self.axis_settings.y_range
            size = self.container_size[1]
        elif direction == "z":
            axis_range = self.axis_settings.z_range
            size = self.container_size[2]

        if axis_range is None or size is None:
            return 0.5

        return size * normalize_value(value, axis_range[0], axis_range[1])


# Code inspired from thread at blender.stackexchange
# https://blender.stackexchange.com/questions/109711/how-to-popup-simple-message-box-from-python-console
class DV_ShowPopup(bpy.types.Operator):
    bl_idname = "data_vis.show_popup"
    bl_label = "Show Popup"

    msg: bpy.props.StringProperty()
    title: bpy.props.StringProperty(default="Info")
    icon: bpy.props.StringProperty(default="QUESTION")

    def execute(self, context):
        def draw(self_, context):
            column = self_.layout.column(align=True)
            for line in self.msg.split("\n"):
                column.label(text=line)

        context.window_manager.popup_menu(draw, title=self.title, icon=self.icon)
        return {'FINISHED'}


class DV_DataInspect(bpy.types.Operator):
    bl_idname = "data_vis.data_inspect"
    bl_label = "Inspect Data"
    bl_description = "Displays active data from data list"

    start_col_index: bpy.props.IntProperty(default=0, options={"HIDDEN"})

    max_displayed_cols: bpy.props.IntProperty(
        name="Max Displayed Columns",
        description="How many columns to display",
        default=5,
        min=0,
    )

    should_scroll_right: bpy.props.BoolProperty(
        name="Scroll Right",
        description="When clicked display next columns",
        default=False,
    )
    should_scroll_left: bpy.props.BoolProperty(
        name="Scroll Left",
        description="When clicked display previous columns",
        # Fake first scroll to not have complicated redraw logic
        default=True,
    )

    show_values: bpy.props.BoolProperty(
        name="Show Values",
        description="When clicked data values are shown",
        default=False,
    )

    def handle_property_input(self, data):
        if data is None:
            return

        cols = len(data[1])
        if self.should_scroll_left:
            self.should_scroll_left = False
            if self.start_col_index > 0:
                self.start_col_index -= 1

        if self.should_scroll_right:
            self.should_scroll_right = False
            if self.start_col_index <= cols - 1:
                self.start_col_index += 1

    def draw(self, context):
        layout = self.layout
        metadata_index = context.scene.data_list_index
        metadata_list = context.scene.data_list
        # valid index is ensured by invoke method
        metadata = metadata_list[metadata_index]
        col = layout.column(align=True)
        col.enabled = False
        col.label(text=f"Name: {metadata.name}")
        col.label(text=f"Filepath: {metadata.filepath}")
        col.label(text=f"Info: {metadata.data_info}")

        data_manager = DataManager()

        col = layout.column(align=True)
        col.label(text=f'Range X: {self._format_range(data_manager.get_range("x"))}')
        col.label(text=f'Range Y: {self._format_range(data_manager.get_range("y"))}')
        col.label(text=f'Range Z: {self._format_range(data_manager.get_range("z"))}')

        row = layout.row()
        row.prop(self, "show_values")
        if not self.show_values:
            return

        row = layout.row(align=True)
        row.prop(self, "should_scroll_left", text="", icon="TRIA_LEFT")
        row.prop(self, "max_displayed_cols", text="Displayed Columns")
        row.prop(self, "should_scroll_right", text="", icon="TRIA_RIGHT")

        # TODO: not super fast, but gets the job done
        parsed_data = data_manager.get_parsed_data()
        self.handle_property_input(parsed_data)

        row = layout.row()
        start_index = self.start_col_index
        max_index = start_index + self.max_displayed_cols - 1
        for i in range(len(parsed_data[1])):
            if i < start_index or i > max_index:
                continue
            col = row.column()
            for j in range(len(parsed_data)):
                col.label(text=str(parsed_data[j][i]))

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context: bpy.types.Context, event):
        metadata_index = context.scene.data_list_index
        metadata_list = context.scene.data_list
        if metadata_index < 0 or metadata_index >= len(metadata_list):
            self.report({'ERROR'}, "Invalid data index!")
            return {'CANCELLED'}

        metadata = metadata_list[metadata_index]
        metadata.load()
        return context.window_manager.invoke_props_dialog(self, width=500)

    def _format_range(self, range: typing.Tuple) -> str:
        return str(tuple(f"{x:.2f}" for x in range)).replace("'", "")
