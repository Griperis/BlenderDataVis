bl_info = {
    'name': 'DataVis',
    'author': 'Zdenek Dolezal',
    'description': '',
    'blender': (2, 80, 0),
    'version': (1, 0, 0),
    'location': 'Object -> Add Mesh',
    'warning': '',
    'category': 'Generic'
}

import bpy
import bpy.utils.previews
import os

from .operators.data_load import FILE_OT_DVLoadFile
from .operators.bar_chart import OBJECT_OT_BarChart
from .operators.line_chart import OBJECT_OT_LineChart
from .operators.pie_chart import OBJECT_OT_PieChart
from .operators.point_chart import OBJECT_OT_PointChart
from .general import DV_LabelPropertyGroup, DV_ColorPropertyGroup, DV_AxisPropertyGroup
from .data_manager import DataManager


class DV_AddonPanel(bpy.types.Panel):
    '''
    Menu panel used for loading data and managing addon settings
    '''
    bl_label = 'DataVis'
    bl_idname = 'OBJECT_PT_dv'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DataVis'

    def draw(self, context):
        layout = self.layout

        data_storage = bpy.data.scenes[0]
    
        row = layout.row()
        row.label(text='Data', icon='WORLD_DATA')

        row = layout.row()
        row.operator('ui.dv_load_data')

        box = layout.box()
        box.label(text='Dims: ' + str(data_manager.dimensions))
        box.label(text='Labels: ' + str(data_manager.has_labels))
        box.label(text='Type: ' + str(data_manager.predicted_data_type))

        layout.label(text='Axis settings')

        row = layout.row()
        row.prop(data_storage.dv_props, 'text_size')

        row = layout.row()
        row.prop(data_storage.dv_props, 'axis_thickness')

        row = layout.row()
        row.prop(data_storage.dv_props, 'axis_tick_mark_height')


class DV_PropertyGroup(bpy.types.PropertyGroup):
    '''
    General addon settings and data are stored in this property group.
    '''
    text_size: bpy.props.FloatProperty(
        name='Text size',
        default=0.05,
        description='Size of addon generated text'
    )

    axis_thickness: bpy.props.FloatProperty(
        name='Axis thickness',
        default=0.01,
        description='How thick is the axis object'
    )

    axis_tick_mark_height: bpy.props.FloatProperty(
        name='Axis tick mark height',
        default=0.03
    )


class OBJECT_MT_AddChart(bpy.types.Menu):
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


preview_collections = {}
data_manager = DataManager()


def chart_ops(self, context):
    icon = preview_collections['main']['addon_icon']
    self.layout.menu(OBJECT_MT_AddChart.bl_idname, icon_value=icon.icon_id)


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


def register():
    load_icons()
    bpy.utils.register_class(DV_PropertyGroup)
    bpy.utils.register_class(DV_LabelPropertyGroup)
    bpy.utils.register_class(DV_ColorPropertyGroup)
    bpy.utils.register_class(DV_AxisPropertyGroup)
    bpy.utils.register_class(OBJECT_OT_BarChart)
    bpy.utils.register_class(OBJECT_OT_PieChart)
    bpy.utils.register_class(OBJECT_OT_LineChart)
    bpy.utils.register_class(OBJECT_OT_PointChart)
    bpy.utils.register_class(FILE_OT_DVLoadFile)
    bpy.utils.register_class(DV_AddonPanel)
    bpy.utils.register_class(OBJECT_MT_AddChart)
    bpy.types.VIEW3D_MT_add.append(chart_ops)

    bpy.types.Scene.dv_props = bpy.props.PointerProperty(type=DV_PropertyGroup)


def unregister():
    remove_icons()
    bpy.utils.unregister_class(DV_PropertyGroup)
    bpy.utils.unregister_class(OBJECT_MT_AddChart)
    bpy.utils.unregister_class(DV_AddonPanel)
    bpy.utils.unregister_class(OBJECT_OT_BarChart)
    bpy.utils.unregister_class(OBJECT_OT_PieChart)
    bpy.utils.unregister_class(OBJECT_OT_LineChart)
    bpy.utils.unregister_class(OBJECT_OT_PointChart)
    bpy.utils.unregister_class(FILE_OT_DVLoadFile)
    bpy.utils.unregister_class(DV_LabelPropertyGroup)
    bpy.utils.unregister_class(DV_ColorPropertyGroup)
    bpy.utils.unregister_class(DV_AxisPropertyGroup)
    bpy.types.VIEW3D_MT_add.remove(chart_ops)


if __name__ == '__main__':
    register()
