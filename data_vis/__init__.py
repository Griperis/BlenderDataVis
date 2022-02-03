# Data Visualisation Addon - load data into Blender and create visualisations
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Entry point to the addon

bl_info = {
    'name': 'Data Vis',
    'author': 'Zdenek Dolezal',
    'description': 'Data visualisation addon',
    'blender': (2, 80, 0),
    'version': (2, 0, 0),
    'location': 'Object -> Add Mesh',
    'warning': '',
    'category': 'Generic'
}

import bpy
import bpy.utils.previews
import os

from .operators.bar_chart import OBJECT_OT_BarChart
from .operators.line_chart import OBJECT_OT_LineChart
from .operators.pie_chart import OBJECT_OT_PieChart
from .operators.point_chart import OBJECT_OT_PointChart
from .operators.surface_chart import OBJECT_OT_SurfaceChart
from .operators.bubble_chart import OBJECT_OT_BubbleChart
from .operators.label_align import OBJECT_OT_AlignLabels
from .properties import DV_AnimationPropertyGroup, DV_AxisPropertyGroup, DV_ColorPropertyGroup, DV_HeaderPropertyGroup, DV_LabelPropertyGroup, DV_LegendPropertyGroup, DV_GeneralPropertyGroup
from .data_manager import DataManager
from .docs import get_example_data_doc, draw_tooltip_button
from .icon_manager import IconManager
from .general import DV_ShowPopup, DV_DataInspect
from .utils import env_utils

icon_manager = IconManager()
data_manager = DataManager()


PERFORMANCE_WARNING_LINE_THRESHOLD = 150
EXAMPLE_DATA_FOLDER = 'example_data'


class FILE_OT_DVLoadFile(bpy.types.Operator):
    bl_idname = 'ui.dv_load_data'
    bl_label = 'Load New File'
    bl_options = {'REGISTER'}
    bl_description = 'Loads data from CSV file to property in first scene'

    filepath: bpy.props.StringProperty(
        name='CSV File',
        subtype='FILE_PATH'
    )

    def invoke(self, context, event):
        if self.filepath != '':
            return self.execute(context)

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        data_manager = DataManager()
        _, ext = os.path.splitext(self.filepath)
        if ext != '.csv':
            self.report({'WARNING'}, 'Only CSV files are supported!')
            return {'CANCELLED'}
        line_n = data_manager.load_data(self.filepath)


        report_type = {'INFO'}
        if line_n == 0:
            report_type = {'WARNING'}
        else:
            item = context.scene.data_list.add()
            _, item.name = os.path.split(self.filepath)
            item.filepath = self.filepath
        self.report(report_type, f'File: {self.filepath}, loaded {line_n} lines!')
        return {'FINISHED'}


class DV_OT_ReloadData(bpy.types.Operator):
    '''Reload data on current index in data list'''
    bl_idname = 'data_list.reload_data'
    bl_label = 'Reload Data'
    bl_option = {'REGISTER'}

    def execute(self, context):
        data_list = context.scene.data_list
        data_list_index = context.scene.data_list_index
        data_list[data_list_index].load()
        self.report({'INFO'}, 'Data reloaded!')
        return {'FINISHED'}


class DV_OT_PrintData(bpy.types.Operator):
    '''Prints data to blender console'''
    bl_idname = 'data_list.print_data'
    bl_label = 'Print Data'
    bl_option = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return data_manager.parsed_data

    def execute(self, context):
        data_manager.print_data()
        self.report({'INFO'}, 'Data printed into console!')
        return {'FINISHED'}


class DV_OT_RemoveData(bpy.types.Operator):
    '''Removes data entry from DV_UL_DataList'''
    bl_idname = 'data_list.remove_data'
    bl_label = 'Remove Item'
    bl_option = {'REGISTER'}

    def execute(self, context):
        index = context.scene.data_list_index
        context.scene.data_list.remove(index)
        return {'FINISHED'}



class DV_AddonPanel(bpy.types.Panel):
    '''Menu panel used for loading data and managing addon settings'''
    bl_label = 'DataVis'
    bl_idname = 'DV_PT_data_load'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DataVis'


    def draw_header(self, context):
        layout = self.layout
        layout.template_icon(icon_value=icon_manager.get_icon_id('addon_icon'))

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
        row.label(text='Recently Loaded Files', icon='ALIGN_JUSTIFY')
        col = row.column(align=True)
        col.alignment = 'RIGHT'
        col.prop(preferences, 'show_data_examples', icon='HELP', text='')

        if preferences.show_data_examples:
            col = layout.column()
            row = col.row()
            row.enabled = False
            row.label(text='Data Examples')
            col.prop(preferences, 'example_category', text='')
            row = col.row(align=True)
            row.prop(preferences, 'example_data', text='')
            example_filepath = os.path.join(
                get_example_data_path(),
                preferences.example_category,
                preferences.example_data
            )

            # Column with no emboss for the data information popup
            col = row.column(align=False)
            col.emboss = 'NONE'
            popup = col.operator(DV_ShowPopup.bl_idname, icon='QUESTION', text='')
            popup.title = 'Data Information'
            popup.msg = get_example_data_doc(preferences.example_data)
            row.operator(FILE_OT_DVLoadFile.bl_idname, icon='IMPORT', text='').filepath = example_filepath
    
        layout.template_list('DV_UL_DataList', '', context.scene, 'data_list', context.scene, 'data_list_index')

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator(FILE_OT_DVLoadFile.bl_idname, text='Load File', icon='ADD').filepath = ''
        row.operator(DV_OT_RemoveData.bl_idname, text='Remove', icon='REMOVE')
        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(icon='WORLD_DATA', text='Data Information')
        draw_tooltip_button(row, 'data')

        filename = data_manager.get_filename()
        if filename == '':
            col.label(text='File: No file loaded. Reload!')
        else:
            self.create_label_row(col, 'File', str(filename))
            self.create_label_row(col, 'Dims', str(data_manager.get_dimensions()))
            self.create_label_row(col, 'Labels', str(data_manager.has_labels))

            lines = data_manager.lines
            row = self.create_label_row(col, 'Lines', lines)
            if lines >= PERFORMANCE_WARNING_LINE_THRESHOLD:
                row = col.row()
                row.alert = True
                row.label(text='Large data size, charts may generate slowly!', icon='ERROR')
            
            self.create_label_row(col, 'Type', str(data_manager.predicted_data_type).split('.')[1])
            
            data_list_index = context.scene.data_list_index
            data_list = context.scene.data_list
            if data_list_index < len(data_list) and data_list_index >= 0:
                col.label(text=context.scene.data_list[context.scene.data_list_index].filepath)

    def draw(self, context):
        layout = self.layout
        self.draw_data_list(context, layout)

        row = layout.row()
        row.menu('OBJECT_MT_Add_Chart', text='Create Chart', icon_value=icon_manager.get_icon_id('addon_icon'))
        row.scale_y = 2

        row = layout.row()
        row.operator('object.align_labels', icon='CAMERA_DATA')
        row.scale_y = 1.5

        scn = context.scene

        layout = layout.box()
        col = layout.column(align=True)
        col.label(text='General Chart Settings', icon='PREFERENCES')
        row = col.row(align=True)
        text_col = row.column(align=True)
        text_col.enabled = False
        text_col.label(text='Container Size')
        draw_tooltip_button(row, 'container_size')
        col.prop(scn.general_props, 'container_size', text='')


def update_space_type(self, context):
    try:
        if hasattr(bpy.types, 'DV_PT_data_load'):
            bpy.utils.unregister_class(DV_AddonPanel)
        DV_AddonPanel.bl_space_type = self.ui_space_type
        bpy.utils.register_class(DV_AddonPanel)
    except Exception as e:
        print('Setting Space Type error: ', str(e))


def update_category(self, context):
    try:
        if hasattr(bpy.types, 'DV_PT_data_load'):
            bpy.utils.unregister_class(DV_AddonPanel)
        DV_AddonPanel.bl_category = self.ui_category
        bpy.utils.register_class(DV_AddonPanel)
    except Exception as e:
        print('Setting Category error: ', str(e))


def update_region_type(self, context):
    try:
        if hasattr(bpy.types, 'DV_PT_data_load'):
            bpy.utils.unregister_class(DV_AddonPanel)
        DV_AddonPanel.bl_region_type = self.ui_region_type
        bpy.utils.register_class(DV_AddonPanel)
    except Exception as e:
        print('Setting Region Type error: ', str(e))


def get_preferences(context):
    return context.preferences.addons[__package__].preferences

def get_example_data_path():
    return os.path.join(
        bpy.utils.script_path_user(),
        "addons",
        __package__,
        EXAMPLE_DATA_FOLDER
    )


class DV_Preferences(bpy.types.AddonPreferences):
    '''Preferences for data visualisation addon'''
    bl_idname = 'data_vis'

    ui_region_type: bpy.props.StringProperty(
        name='Region Type',
        default='UI',
        update=update_region_type
    )
    ui_space_type: bpy.props.StringProperty(
        name='Space Type',
        default='VIEW_3D',
        update=update_space_type
    )

    ui_category: bpy.props.StringProperty(
        name='Panel Category',
        default='DataVis',
        update=update_category
    )

    debug: bpy.props.BoolProperty(
        name='Toggle Debug Options',
        default=False
    )

    show_data_examples: bpy.props.BoolProperty(
        name='Show Data Examples',
        description='If true then data examples are shown and can be loaded',
        default=False,
    )

    example_category: bpy.props.EnumProperty(
        name='Data Type',
        description='Types of example data',
        items=lambda self, context: self.get_example_data_categories(context)
    )

    example_data: bpy.props.EnumProperty(
        name='Example Data',
        description='Select example data to load',
        items=lambda self, context: self.get_example_data(context)
    )

    def get_example_data_categories(self, context):
        enum_items = []
        for i, _dir in enumerate(os.listdir(get_example_data_path())):
            # infer icon from data type
            icon = 'QUESTION'
            if _dir == 'categorical':
                icon = 'LINENUMBERS_ON'
            elif _dir == 'numerical':
                icon = 'FORCE_HARMONIC' 

            enum_items.append((_dir, _dir, _dir, icon, i))

        return enum_items

    def get_example_data(self, context):
        enum_items = []
        for file in os.listdir(os.path.join(get_example_data_path(), self.example_category)):
            enum_items.append((file, file, file))

        return sorted(enum_items)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text='Customize position of addon panel', icon='TOOL_SETTINGS')
        box.prop(self, 'ui_region_type')
        box.prop(self, 'ui_space_type')
        box.prop(self, 'ui_category')
        box.label(text='Check console for possible errors!', icon='ERROR')

        box = layout.box()
        box.label(text='Other Settings', icon='PLUGIN')
        box.prop(self, 'debug')


class OBJECT_OT_AddChart(bpy.types.Menu):
    '''
    Menu panel grouping chart related operators in Blender AddObject panel
    '''
    bl_idname = 'OBJECT_MT_Add_Chart'
    bl_label = 'Chart'

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_BarChart.bl_idname, icon_value=icon_manager.get_icon('bar_chart').icon_id)
        layout.operator(OBJECT_OT_LineChart.bl_idname, icon_value=icon_manager.get_icon('line_chart').icon_id)
        layout.operator(OBJECT_OT_PieChart.bl_idname, icon_value=icon_manager.get_icon('pie_chart').icon_id)
        layout.operator(OBJECT_OT_PointChart.bl_idname, icon_value=icon_manager.get_icon('point_chart').icon_id)
        layout.operator(OBJECT_OT_BubbleChart.bl_idname, icon_value=icon_manager.get_icon('bubble_chart').icon_id)
        layout.operator(OBJECT_OT_SurfaceChart.bl_idname, icon_value=icon_manager.get_icon('surface_chart').icon_id)


class DV_DL_PropertyGroup(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Name of item',
        default='Unnamed',
    )
    filepath: bpy.props.StringProperty()
    data_info: bpy.props.StringProperty()

    def load(self):
        data_manager.load_data(self.filepath)



class DV_UL_DataList(bpy.types.UIList):
    '''
    Loaded data list
    '''
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=f'{item.name}')
        if index == context.scene.data_list_index:
            row = layout.row(align=True)
            row.operator(DV_OT_ReloadData.bl_idname, icon='FILE_REFRESH', text='')
            row.operator(DV_DataInspect.bl_idname, icon='VIEWZOOM', text='')
            if get_preferences(context).debug:
                row.operator(DV_OT_PrintData.bl_idname, icon='OUTPUT', text='')


def chart_ops(self, context):
    icon = icon_manager.get_icon('addon_icon')
    self.layout.menu(OBJECT_OT_AddChart.bl_idname, icon_value=icon.icon_id)


classes = [
    DV_Preferences,
    DV_ShowPopup,
    DV_DataInspect,
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
    OBJECT_OT_AlignLabels,
    FILE_OT_DVLoadFile,
    DV_AddonPanel,
]


def reload_data(self, context):
    data_list = context.scene.data_list
    data_list[self.data_list_index].load()


def reload():
    unregister()
    register()


def register():
    for module in ['scipy', 'numpy']:
        env_utils.ensure_python_module(module)

    icon_manager.load_icons()
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.general_props = bpy.props.PointerProperty(type=DV_GeneralPropertyGroup)
    bpy.types.Scene.data_list = bpy.props.CollectionProperty(type=DV_DL_PropertyGroup)
    bpy.types.Scene.data_list_index = bpy.props.IntProperty(update=reload_data)
    bpy.types.VIEW3D_MT_add.append(chart_ops)

def unregister():
    icon_manager.remove_icons()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    bpy.types.VIEW3D_MT_add.remove(chart_ops)
    del bpy.types.Scene.general_props
    del bpy.types.Scene.data_list_index
    del bpy.types.Scene.data_list


if __name__ == '__main__':
    register()
