bl_info = {
    'name': 'Data Visualisation Addon',
    'author': 'Zdenek Dolezal',
    'description': '',
    'blender': (2, 80, 0),
    'version': (0, 0, 3),
    'location': '',
    'warning': '',
    'category': 'Generic'
}

import bpy

from src.operators.data_load import FILE_OT_DVLoadFile
from src.operators.bar_chart import OBJECT_OT_bar_chart
from src.operators.line_chart import OBJECT_OT_line_chart
from src.operators.pie_chart import OBJECT_OT_pie_chart
from src.operators.point_chart import OBJECT_OT_point_chart


class PANEL_PT_DVAddonPanel(bpy.types.Panel):
    '''
    Menu panel used for loading and managing data
    '''
    bl_label = 'Data visualisation utilities'
    bl_idname = 'OBJECT_PT_dv'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'Data Visualisation Addon'

    def draw(self, context):
        layout = self.layout

        first_scene = bpy.data.scenes[0]

        layout.label(text='Chart settings')
        row = layout.row()
        row.prop(first_scene.dv_props, 'width')
        row.prop(first_scene.dv_props, 'height')

        row = layout.row()
        row.label(text='Data', icon='WORLD_DATA')
        row.operator('ui.dv_load_data')


class DV_TableRowProp(bpy.types.PropertyGroup):
    '''
    One row of loaded data as string
    '''
    value: bpy.props.StringProperty()


class DV_PropertyGroup(bpy.types.PropertyGroup):
    '''
    All addon settings and data are stored in this property group.
    '''
    data: bpy.props.CollectionProperty(
        name='Data',
        type=DV_TableRowProp
    )
    width: bpy.props.FloatProperty(
        name='Width',
        default=1.0
        
    )
    height: bpy.props.FloatProperty(
        name='Height',
        default=1.0
    )


class OBJECT_MT_AddChart(bpy.types.Menu):
    '''
    Menu panel grouping chart related operators in Blender AddObject panel
    '''
    bl_idname = 'OBJECT_MT_Add_Chart'
    bl_label = 'Add chart'

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_bar_chart.bl_idname, icon='PLUGIN')
        layout.operator(OBJECT_OT_line_chart.bl_idname, icon='PLUGIN')
        layout.operator(OBJECT_OT_pie_chart.bl_idname, icon='PLUGIN')
        layout.operator(OBJECT_OT_point_chart.bl_idname, icon='PLUGIN')


def chart_ops(self, context):
    self.layout.menu(OBJECT_MT_AddChart.bl_idname, icon='PLUGIN')


def register():
    bpy.utils.register_class(DV_TableRowProp)
    bpy.utils.register_class(DV_PropertyGroup)
    bpy.utils.register_class(OBJECT_OT_bar_chart)
    bpy.utils.register_class(OBJECT_OT_pie_chart)
    bpy.utils.register_class(OBJECT_OT_line_chart)
    bpy.utils.register_class(OBJECT_OT_point_chart)
    bpy.utils.register_class(FILE_OT_DVLoadFile)
    bpy.utils.register_class(PANEL_PT_DVAddonPanel)
    bpy.utils.register_class(OBJECT_MT_AddChart)
    bpy.types.VIEW3D_MT_add.append(chart_ops)

    bpy.types.Scene.dv_props = bpy.props.PointerProperty(type=DV_PropertyGroup)


def unregister():
    bpy.utils.unregister_class(DV_PropertyGroup)
    bpy.utils.unregister_class(DV_TableRowProp)
    bpy.utils.unregister_class(OBJECT_MT_AddChart)
    bpy.utils.unregister_class(PANEL_PT_DVAddonPanel)
    bpy.utils.unregister_class(OBJECT_OT_bar_chart)
    bpy.utils.unregister_class(OBJECT_OT_pie_chart)
    bpy.utils.unregister_class(OBJECT_OT_line_chart)
    bpy.utils.unregister_class(OBJECT_OT_point_chart)
    bpy.utils.unregister_class(FILE_OT_DVLoadFile)
    bpy.types.VIEW3D_MT_add.remove(chart_ops)


if __name__ == '__main__':
    register()
