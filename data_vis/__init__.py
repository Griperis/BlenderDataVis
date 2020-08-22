# Data Visualisation Addon - load data into Blender and create visualisations
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Entry point to the addon

bl_info = {
    'name': 'Data Vis',
    'author': 'Zdenek Dolezal',
    'description': 'Data visualisation addon',
    'blender': (2, 80, 0),
    'version': (1, 4, 0),
    'location': 'Object -> Add Mesh',
    'warning': '',
    'category': 'Generic'
}

import bpy
import bpy.utils.previews
import os
import subprocess
import sys

from .operators.bar_chart import OBJECT_OT_BarChart
from .operators.line_chart import OBJECT_OT_LineChart
from .operators.pie_chart import OBJECT_OT_PieChart
from .operators.point_chart import OBJECT_OT_PointChart
from .operators.surface_chart import OBJECT_OT_SurfaceChart
from .operators.bubble_chart import OBJECT_OT_BubbleChart
from .operators.label_align import OBJECT_OT_AlignLabels
from .properties import DV_AnimationPropertyGroup, DV_AxisPropertyGroup, DV_ColorPropertyGroup, DV_HeaderPropertyGroup, DV_LabelPropertyGroup, DV_LegendPropertyGroup, DV_GeneralPropertyGroup
from .data_manager import DataManager
from .icon_manager import IconManager

icon_manager = IconManager()
data_manager = DataManager()

PERFORMANCE_WARNING_LINE_THRESHOLD = 150


class OBJECT_OT_InstallModules(bpy.types.Operator):
    '''Operator that tries to install scipy and numpy using pip into blender python'''
    bl_label = 'Install addon dependencies'
    bl_idname = 'object.install_modules'
    bl_options = {'REGISTER'}

    def execute(self, context):
        version = '{}.{}'.format(bpy.app.version[0], bpy.app.version[1])

        python_path = os.path.join(os.getcwd(), version, 'python', 'bin', 'python')
        try:
            self.install(python_path)
        except Exception as e:
            self.report({'ERROR'}, 'Error ocurred, try to install dependencies manually. \n Exception: {}'.format(str(e)))
        return {'FINISHED'}

    def install(self, python_path):
        import platform

        info = ''
        bp_pip = -1
        bp_res = -1

        p_pip = -1
        p_res = -1

        p3_pip = -1
        p3_res = -1
        try:
            bp_pip = subprocess.check_call([python_path, '-m', 'ensurepip', '--user'])
            bp_res = subprocess.check_call([python_path, '-m', 'pip', 'install', '--user', 'scipy'])
        except OSError as e:
            info = 'Python in blender folder failed: ' + str(e) + '\n'

        if bp_pip != 0 or bp_res != 0:
            if platform.system() == 'Linux':
                try:
                    p_pip = subprocess.check_call(['python', '-m', 'ensurepip', '--user'])
                    p_res = subprocess.check_call(['python', '-m', 'pip', 'install', '--user', 'scipy'])
                except OSError as e:
                    info += 'Python in PATH failed: ' + str(e) + '\n'

                if p_pip != 0 or p_res != 0:  
                    try:
                        # python3
                        p3_pip = subprocess.check_call(['python3', '-m', 'ensurepip', '--user'])
                        p3_res = subprocess.check_call(['python3', '-m', 'pip', 'install', '--user', 'scipy'])
                    except OSError as e:
                        info += 'Python3 in PATH failed: ' + str(e) + '\n'

        # if one approach worked
        if (bp_pip == 0 and bp_res == 0) or (p_pip == 0 and p_res == 0) or (p3_pip == 0 and p3_res == 0):
            self.report({'INFO'}, 'Scipy module should be succesfully installed, restart Blender now please! (Best effort approach)')
        else:
            raise Exception('Failed to install pip or scipy into blender python:\n' + str(info))


class FILE_OT_DVLoadFile(bpy.types.Operator):
    '''
    Loads data from CSV file to property in first scene
    '''
    bl_idname = 'ui.dv_load_data'
    bl_label = 'Load New File'
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        name='CSV File',
        subtype='FILE_PATH'
    )

    def invoke(self, context, event):
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
        data_list[data_list_index].load(context)
        self.report({'INFO'}, 'Data reloaded!')
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

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text='Recently Loaded Files')
        box.template_list('DV_UL_DataList', '', context.scene, 'data_list', context.scene, 'data_list_index')
        row = box.row()
        row.operator('ui.dv_load_data')
        row.operator('data_list.remove_data')

        box.label(icon='WORLD_DATA', text='Data Information:')

        filename = data_manager.get_filename()
        if filename == '':
            box.label(text='File: No file loaded')
        else:
            box.label(text='File: ' + str(filename))
            box.label(text='Dims: ' + str(data_manager.get_dimensions()))
            box.label(text='Labels: ' + str(data_manager.has_labels))
            lines = data_manager.lines
            if lines >= PERFORMANCE_WARNING_LINE_THRESHOLD:
                lines = str(lines) + ' Warning (performace)!'
            else:
                lines = str(lines)     
            box.label(text='Lines: ' + lines)
            box.label(text='Type: ' + str(data_manager.predicted_data_type))
            
            data_list_index = context.scene.data_list_index
            data_list = context.scene.data_list
            if data_list_index < len(data_list) and data_list_index >= 0:
                box.label(text=context.scene.data_list[context.scene.data_list_index].filepath)

        box = layout.box()
        box.label(text='Chart Manipulation')
        box.use_property_split = True
        row = box.row()
        row.menu('OBJECT_MT_Add_Chart', text='Create Chart', icon_value=icon_manager.get_icon_id('addon_icon'))
        row.scale_y = 2

        row = box.row()
        row.operator('object.align_labels', icon='CAMERA_DATA')
        row.scale_y = 1.75

        scn = context.scene

        box = layout.box()
        box.label(text='General Chart Settings')
        box.label(text='Default Container Size')
        box.prop(scn.general_props, 'container_size', text='')


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

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text='Python dependencies', icon='PLUS')
        row = box.row()
        row.scale_y = 2.0
        try:
            import scipy
            import numpy
            row.label(text='Dependencies already installed...')
        except ImportError:
            row.operator('object.install_modules')
            row = box.row()
            version = '{}.{}'.format(bpy.app.version[0], bpy.app.version[1])
            row.label(text='Or use pip to install scipy into python which Blender uses!')
            row = box.row()
            row.label(text='Blender has to be restarted after this process!')

        box = layout.box()
        box.label(text='Customize position of addon panel', icon='TOOL_SETTINGS')
        box.prop(self, 'ui_region_type')
        box.prop(self, 'ui_space_type')
        box.prop(self, 'ui_category')
        box.label(text='Check console for possible errors!', icon='ERROR')


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

    def load(self, context):
        data_manager.load_data(self.filepath)



class DV_UL_DataList(bpy.types.UIList):
    '''
    Loaded data list
    '''
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(icon='ALIGN_JUSTIFY', text=f'{item.name}')
        if index == context.scene.data_list_index:
            layout.operator(DV_OT_ReloadData.bl_idname, icon='FILE_REFRESH', text='')


def chart_ops(self, context):
    icon = icon_manager.get_icon('addon_icon')
    self.layout.menu(OBJECT_OT_AddChart.bl_idname, icon_value=icon.icon_id)


classes = [
    DV_Preferences,
    OBJECT_OT_InstallModules,
    DV_LabelPropertyGroup,
    DV_ColorPropertyGroup,
    DV_AxisPropertyGroup,
    DV_AnimationPropertyGroup,
    DV_HeaderPropertyGroup,
    DV_LegendPropertyGroup,
    DV_GeneralPropertyGroup,
    DV_DL_PropertyGroup,
    DV_UL_DataList,
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
    data_list[self.data_list_index].load(context)


def reload():
    unregister()
    register()


def register():

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
