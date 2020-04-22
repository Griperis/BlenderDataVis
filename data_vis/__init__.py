bl_info = {
    'name': 'Data Vis',
    'author': 'Zdenek Dolezal',
    'description': 'Data visualisation addon',
    'blender': (2, 80, 0),
    'version': (1, 3, 1),
    'location': 'Object -> Add Mesh',
    'warning': '',
    'category': 'Generic'
}

import bpy
import bpy.utils.previews
import os
import subprocess
import sys

from .operators.data_load import FILE_OT_DVLoadFile
from .operators.bar_chart import OBJECT_OT_BarChart
from .operators.line_chart import OBJECT_OT_LineChart
from .operators.pie_chart import OBJECT_OT_PieChart
from .operators.point_chart import OBJECT_OT_PointChart
from .operators.surface_chart import OBJECT_OT_SurfaceChart
from .general import DV_LabelPropertyGroup, DV_ColorPropertyGroup, DV_AxisPropertyGroup, DV_AnimationPropertyGroup, DV_HeaderPropertyGroup
from .data_manager import DataManager

preview_collections = {}
data_manager = DataManager()


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


class DV_AddonPanel(bpy.types.Panel):
    '''
    Menu panel used for loading data and managing addon settings
    '''
    bl_label = 'DataVis'
    bl_idname = 'DV_PT_data_load'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DataVis'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator('ui.dv_load_data')

        box = layout.box()
        box.label(icon='WORLD_DATA', text='Data Information:')
        filename = data_manager.get_filename()
        if filename == '':
            box.label(text='File: No file loaded')
        else:
            box.label(text='File: ' + str(filename))
            box.label(text='Dims: ' + str(data_manager.dimensions))
            box.label(text='Labels: ' + str(data_manager.has_labels))
            lines = data_manager.lines
            if lines >= 150:
                lines = str(lines) + ' Warning (performace)!'
            else:
                lines = str(lines)     
            box.label(text='Lines: ' + lines)
            box.label(text='Type: ' + str(data_manager.predicted_data_type))


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
        main_icons = preview_collections['main']
        layout.operator(OBJECT_OT_BarChart.bl_idname, icon_value=main_icons['bar_chart'].icon_id)
        layout.operator(OBJECT_OT_LineChart.bl_idname, icon_value=main_icons['line_chart'].icon_id)
        layout.operator(OBJECT_OT_PieChart.bl_idname, icon_value=main_icons['pie_chart'].icon_id)
        layout.operator(OBJECT_OT_PointChart.bl_idname, icon_value=main_icons['point_chart'].icon_id)
        layout.operator(OBJECT_OT_SurfaceChart.bl_idname, icon_value=main_icons['surface_chart'].icon_id)


def chart_ops(self, context):
    icon = preview_collections['main']['addon_icon']
    self.layout.menu(OBJECT_OT_AddChart.bl_idname, icon_value=icon.icon_id)


def load_icons():
    pcoll = bpy.utils.previews.new()

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    for icon in os.listdir(icons_dir):
        name, ext = icon.split('.')
        if ext == 'png':
            pcoll.load(name, os.path.join(icons_dir, icon), 'IMAGE')

    preview_collections['main'] = pcoll


def remove_icons():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


classes = [
    DV_Preferences,
    OBJECT_OT_InstallModules,
    DV_LabelPropertyGroup,
    DV_ColorPropertyGroup,
    DV_AxisPropertyGroup,
    DV_AnimationPropertyGroup,
    DV_HeaderPropertyGroup,
    OBJECT_OT_AddChart,
    OBJECT_OT_BarChart,
    OBJECT_OT_PieChart,
    OBJECT_OT_PointChart,
    OBJECT_OT_LineChart,
    OBJECT_OT_SurfaceChart,
    FILE_OT_DVLoadFile,
    DV_AddonPanel,
]


def reload():
    unregister()
    register()


def register():
    load_icons()
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.VIEW3D_MT_add.append(chart_ops)


def unregister():
    remove_icons()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    bpy.types.VIEW3D_MT_add.remove(chart_ops)


if __name__ == '__main__':
    register()
