# Data Visualisation Addon - load data into Blender and create visualisations
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Entry point to the addon

bl_info = {
    "name": "Data Vis",
    "author": "Zdenek Dolezal",
    "description": "Data visualisation addon",
    "blender": (2, 80, 0),
    "version": (2, 1, 0),
    "location": "Object -> Add Mesh",
    "warning": "",
    "category": "Generic",
}

import bpy
import bpy.utils.previews
import os

# import logging first, so it is initialized before all other modules
from .utils import data_vis_logging

from .operators.bar_chart import OBJECT_OT_BarChart
from .operators.line_chart import OBJECT_OT_LineChart
from .operators.pie_chart import OBJECT_OT_PieChart
from .operators.point_chart import OBJECT_OT_PointChart
from .operators.surface_chart import OBJECT_OT_SurfaceChart
from .operators.bubble_chart import OBJECT_OT_BubbleChart
from .operators.label_align import DV_AlignLabels
from .properties import (
    DV_AnimationPropertyGroup,
    DV_AxisPropertyGroup,
    DV_ColorPropertyGroup,
    DV_HeaderPropertyGroup,
    DV_LabelPropertyGroup,
    DV_LegendPropertyGroup,
    DV_GeneralPropertyGroup,
)
from .data_manager import DataManager, DataType
from .docs import get_example_data_doc, draw_tooltip_button
from .icon_manager import IconManager
from .general import DV_ShowPopup, DV_DataInspect, DV_DataOpenFile
from .utils import env_utils
from . import preferences as prefs
from . import geonodes
from .preferences import DV_Preferences, get_preferences, get_example_data_path

icon_manager = IconManager()
data_manager = DataManager()


PERFORMANCE_WARNING_LINE_THRESHOLD = 150
EXAMPLE_DATA_FOLDER = "example_data"


@data_vis_logging.logged_operator
class FILE_OT_DVLoadFile(bpy.types.Operator):
    bl_idname = "ui.dv_load_data"
    bl_label = "Load New File"
    bl_options = {"REGISTER"}
    bl_description = "Loads data from CSV file to property in first scene"

    filepath: bpy.props.StringProperty(name="CSV File", subtype="FILE_PATH")

    def invoke(self, context, event):
        if self.filepath != "":
            return self.execute(context)

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        data_manager = DataManager()
        _, ext = os.path.splitext(self.filepath)
        if ext != ".csv":
            self.report({"WARNING"}, "Only CSV files are supported!")
            return {"CANCELLED"}

        for i, item in enumerate(context.scene.data_list):
            if item.filepath == self.filepath:
                context.scene.data_list_index = i
                self.report({"WARNING"}, f"File {self.filepath} already loaded!")
                return {"CANCELLED"}

        line_n = data_manager.load_data(self.filepath)

        report_type = {"INFO"}
        if line_n == 0:
            report_type = {"WARNING"}
        else:
            item = context.scene.data_list.add()
            _, item.name = os.path.split(self.filepath)
            item.filepath = self.filepath

            context.scene.data_list_index = len(context.scene.data_list) - 1
        self.report(report_type, f"File: {self.filepath}, loaded {line_n} lines!")
        return {"FINISHED"}


@data_vis_logging.logged_operator
class DV_OT_ReloadData(bpy.types.Operator):
    """Reload data on current index in data list"""

    bl_idname = "data_list.reload_data"
    bl_label = "Reload Data"
    bl_option = {"REGISTER"}

    def execute(self, context):
        data_list = context.scene.data_list
        data_list_index = context.scene.data_list_index
        data_list[data_list_index].load()
        self.report({"INFO"}, "Data reloaded!")
        return {"FINISHED"}


@data_vis_logging.logged_operator
class DV_OT_PrintData(bpy.types.Operator):
    """Prints data to blender console"""

    bl_idname = "data_list.print_data"
    bl_label = "Print Data"
    bl_option = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return data_manager.parsed_data

    def execute(self, context):
        data_manager.print_data()
        self.report({"INFO"}, "Data printed into console!")
        return {"FINISHED"}


@data_vis_logging.logged_operator
class DV_OT_RemoveData(bpy.types.Operator):
    """Removes data entry from DV_UL_DataList"""

    bl_idname = "data_list.remove_data"
    bl_label = "Remove Item"
    bl_option = {"REGISTER"}

    def execute(self, context):
        index = context.scene.data_list_index
        context.scene.data_list.remove(index)
        return {"FINISHED"}


class DV_AddonPanel(bpy.types.Panel):
    """Menu panel used for loading data and managing addon settings"""

    bl_label = "DataVis"
    bl_idname = "DV_PT_data_load"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DataVis"

    def draw_header(self, context):
        layout = self.layout
        layout.template_icon(icon_value=icon_manager.get_icon_id("addon_icon"))

    def draw_header_preset(self, context):
        self.layout.operator(
            "wm.url_open",
            text="",
            icon_value=icon_manager.get_icon("github_icon").icon_id,
            emboss=False,
        ).url = "https://github.com/Griperis/BlenderDataVis"

    def create_label_row(self, layout, label, value):
        row = layout.row(align=True)
        label_col = row.column(align=True)
        label_col.enabled = False
        label_col.label(text=str(label))
        row.label(text=str(value))
        return row

    def draw_data_list(self, context, layout):
        preferences = get_preferences(context)
        row = layout.row(align=True)
        row.label(text="Recently Loaded Files", icon="ALIGN_JUSTIFY")
        col = row.column(align=True)
        col.alignment = "RIGHT"
        col.prop(preferences, "show_data_examples", icon="HELP", text="")

        if preferences.show_data_examples:
            col = layout.column()
            row = col.row()
            row.enabled = False
            row.label(text="Data Examples")
            col.prop(preferences, "example_category", text="")
            row = col.row(align=True)
            row.prop(preferences, "example_data", text="")
            example_filepath = os.path.join(
                get_example_data_path(),
                preferences.example_category,
                preferences.example_data,
            )

            # Column with no emboss for the data information popup
            col = row.column(align=False)
            col.emboss = "NONE"
            popup = col.operator(DV_ShowPopup.bl_idname, icon="QUESTION", text="")
            popup.title = "Data Information"
            popup.msg = get_example_data_doc(preferences.example_data)
            row.operator(
                FILE_OT_DVLoadFile.bl_idname, icon="IMPORT", text=""
            ).filepath = example_filepath

        layout.template_list(
            "DV_UL_DataList",
            "",
            context.scene,
            "data_list",
            context.scene,
            "data_list_index",
        )

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator(
            FILE_OT_DVLoadFile.bl_idname, text="Load File", icon="ADD"
        ).filepath = ""
        row.operator(DV_OT_RemoveData.bl_idname, text="Remove", icon="REMOVE")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(icon="WORLD_DATA", text="Data Information")
        draw_tooltip_button(row, "data")

        filename = data_manager.get_filename()
        if filename == "":
            col.label(text="File: No file loaded. Reload!")
        else:
            self.create_label_row(col, "File", str(filename))
            self.create_label_row(col, "Dims", str(data_manager.get_dimensions()))
            self.create_label_row(col, "Labels", str(data_manager.has_labels))

            lines = data_manager.lines
            row = self.create_label_row(col, "Lines", lines)
            if lines >= PERFORMANCE_WARNING_LINE_THRESHOLD:
                row = col.row()
                row.alert = True
                row.label(
                    text="Large data size, charts may generate slowly!", icon="ERROR"
                )

            self.create_label_row(
                col, "Type", str(data_manager.predicted_data_type).split(".")[1]
            )

            data_list_index = context.scene.data_list_index
            data_list = context.scene.data_list
            if data_list_index < len(data_list) and data_list_index >= 0:
                col.label(
                    text=context.scene.data_list[context.scene.data_list_index].filepath
                )

    def draw(self, context):
        layout = self.layout
        layout.prop(get_preferences(context), "addon_mode", text="")
        layout.separator()
        self.draw_data_list(context, layout)

        prefs = get_preferences(context)
        if prefs.addon_mode == "LEGACY":
            self._draw_legacy_ui(context, layout)
        elif prefs.addon_mode == "GEONODES":
            if bpy.app.version < (4, 2, 0):
                row = layout.row()
                row.alert = True
                row.label(
                    text="Geometry nodes mode is available in 4.2 and higher!",
                    icon="ERROR",
                )
                return

            self._draw_geonodes_ui(context, layout)

    def _draw_geonodes_ui(self, context, layout):
        row = layout.row()
        row.scale_y = 2
        row.menu(
            "OBJECT_MT_Add_Chart",
            text="Create Chart",
            icon_value=icon_manager.get_icon_id("addon_icon"),
        )

    def _draw_legacy_ui(self, context, layout):
        row = layout.row()
        row.menu(
            "OBJECT_MT_Add_Chart",
            text="Create Chart",
            icon_value=icon_manager.get_icon_id("addon_icon"),
        )
        row.scale_y = 2

        row = layout.row()
        row.operator(DV_AlignLabels.bl_idname, icon="CAMERA_DATA")
        row.scale_y = 1.5

        scn = context.scene

        layout = layout.box()
        col = layout.column(align=True)
        col.label(text="General Chart Settings", icon="PREFERENCES")
        row = col.row(align=True)
        text_col = row.column(align=True)
        text_col.enabled = False
        text_col.label(text="Container Size")
        draw_tooltip_button(row, "container_size")
        col.prop(scn.general_props, "container_size", text="")


# Provide the PANEL_CLASS reference to preferences, so UI position can be updated
prefs.PANEL_CLASS = DV_AddonPanel


class OBJECT_OT_AddChart(bpy.types.Menu):
    """
    Menu panel grouping chart related operators in Blender AddObject panel
    """

    bl_idname = "OBJECT_MT_Add_Chart"
    bl_label = "Chart"

    def draw(self, context):
        layout = self.layout
        if len(context.scene.data_list) == 0:
            layout.label(text="Load data in the N panel first!", icon="ERROR")
            layout.separator()

        prefs = get_preferences(context)
        if prefs.addon_mode == "LEGACY":
            layout.operator(
                OBJECT_OT_BarChart.bl_idname,
                icon_value=icon_manager.get_icon("bar_chart").icon_id,
            )
            layout.operator(
                OBJECT_OT_LineChart.bl_idname,
                icon_value=icon_manager.get_icon("line_chart").icon_id,
            )
            layout.operator(
                OBJECT_OT_PieChart.bl_idname,
                icon_value=icon_manager.get_icon("pie_chart").icon_id,
            )
            layout.operator(
                OBJECT_OT_PointChart.bl_idname,
                icon_value=icon_manager.get_icon("point_chart").icon_id,
            )
            layout.operator(
                OBJECT_OT_BubbleChart.bl_idname,
                icon_value=icon_manager.get_icon("bubble_chart").icon_id,
            )
            layout.operator(
                OBJECT_OT_SurfaceChart.bl_idname,
                icon_value=icon_manager.get_icon("surface_chart").icon_id,
            )
        elif prefs.addon_mode == "GEONODES":
            layout.operator(
                geonodes.charts.DV_GN_BarChart.bl_idname,
                icon_value=icon_manager.get_icon("bar_chart").icon_id,
            )
            layout.operator(
                geonodes.charts.DV_GN_LineChart.bl_idname,
                icon_value=icon_manager.get_icon("line_chart").icon_id,
            )
            layout.operator(
                geonodes.charts.DV_GN_PieChart.bl_idname,
                icon_value=icon_manager.get_icon("pie_chart").icon_id,
            )
            layout.operator(
                geonodes.charts.DV_GN_PointChart.bl_idname,
                icon_value=icon_manager.get_icon("point_chart").icon_id,
            )
            layout.operator(
                geonodes.charts.DV_GN_SurfaceChart.bl_idname,
                icon_value=icon_manager.get_icon("surface_chart").icon_id,
            )
        else:
            raise ValueError(f"unknown addon mode: {prefs.addon_mode}")


class DV_DL_PropertyGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name="Name of item",
        default="Unnamed",
    )
    filepath: bpy.props.StringProperty()
    data_info: bpy.props.StringProperty()

    def load(self):
        data_manager.load_data(self.filepath)


class DV_UL_DataList(bpy.types.UIList):
    """
    Loaded data list
    """

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=f"{item.name}")
        if index == context.scene.data_list_index:
            row = layout.row(align=True)
            row.operator(DV_OT_ReloadData.bl_idname, icon="FILE_REFRESH", text="")
            row.operator(DV_DataInspect.bl_idname, icon="VIEWZOOM", text="")
            row.operator(
                DV_DataOpenFile.bl_idname, icon="FILEBROWSER", text=""
            ).filepath = item.filepath
            if get_preferences(context).debug:
                row.operator(DV_OT_PrintData.bl_idname, icon="OUTPUT", text="")


def chart_ops(self, context):
    icon = icon_manager.get_icon("addon_icon")
    self.layout.menu(OBJECT_OT_AddChart.bl_idname, icon_value=icon.icon_id)


classes = [
    DV_Preferences,
    DV_ShowPopup,
    DV_DataInspect,
    DV_DataOpenFile,
    DV_LabelPropertyGroup,
    DV_ColorPropertyGroup,
    DV_AxisPropertyGroup,
    DV_AnimationPropertyGroup,
    DV_HeaderPropertyGroup,
    DV_LegendPropertyGroup,
    DV_GeneralPropertyGroup,
    DV_DL_PropertyGroup,
    DV_UL_DataList,
    DV_OT_PrintData,
    DV_OT_RemoveData,
    DV_OT_ReloadData,
    OBJECT_OT_AddChart,
    OBJECT_OT_BarChart,
    OBJECT_OT_PieChart,
    OBJECT_OT_PointChart,
    OBJECT_OT_LineChart,
    OBJECT_OT_SurfaceChart,
    OBJECT_OT_BubbleChart,
    DV_AlignLabels,
    FILE_OT_DVLoadFile,
]


def reload_data(self, context):
    data_list = context.scene.data_list
    if self.data_list_index < len(data_list) and self.data_list_index >= 0:
        data_list[self.data_list_index].load()


def reload():
    unregister()
    register()


def register():
    env_utils.ensure_python_modules_new_thread(["scipy"])

    # Register the addon panel first, so other panels can depend on it
    bpy.utils.register_class(DV_AddonPanel)

    icon_manager.load_icons()
    geonodes.register()
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.general_props = bpy.props.PointerProperty(
        type=DV_GeneralPropertyGroup
    )
    bpy.types.Scene.data_list = bpy.props.CollectionProperty(type=DV_DL_PropertyGroup)
    bpy.types.Scene.data_list_index = bpy.props.IntProperty(update=reload_data)
    bpy.types.VIEW3D_MT_add.append(chart_ops)


def unregister():
    icon_manager.remove_icons()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    geonodes.unregister()
    bpy.utils.unregister_class(DV_AddonPanel)

    bpy.types.VIEW3D_MT_add.remove(chart_ops)
    del bpy.types.Scene.general_props
    del bpy.types.Scene.data_list_index
    del bpy.types.Scene.data_list
