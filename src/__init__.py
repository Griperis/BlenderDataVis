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
from src.general import DV_LabelPropertyGroup
from src.general import CONST


class DV_AddonPanel(bpy.types.Panel):
    '''
    Menu panel used for loading data and managing addon settings
    '''
    bl_label = 'Data visualisation utilities'
    bl_idname = 'OBJECT_PT_dv'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_category = 'Data Visualisation Addon'

    def draw(self, context):
        layout = self.layout

        data_storage = bpy.data.scenes[0]

        layout.label(text='Chart settings')

        row = layout.row()
        row.label(text='Data', icon='WORLD_DATA')
        
        row = layout.row()
        row.operator('ui.dv_load_data')

        layout.label(text='Axis settings')
        
        row = layout.row()
        row.prop(data_storage.dv_props, 'text_size')

        row = layout.row()
        row.prop(data_storage.dv_props, 'axis_thickness')
        
        row = layout.row()
        row.prop(data_storage.dv_props, 'axis_tick_mark_height')


class DV_RowProp(bpy.types.PropertyGroup):
    '''
    One row of loaded data as string
    '''
    value: bpy.props.StringProperty()


class DV_PropertyGroup(bpy.types.PropertyGroup):
    '''
    General addon settings and data are stored in this property group.
    '''
    data: bpy.props.CollectionProperty(
        name='Data',
        type=DV_RowProp
    )

    text_size: bpy.props.FloatProperty(
        name='Text size',
        default=0.1,
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
    bpy.utils.register_class(DV_RowProp)
    bpy.utils.register_class(DV_PropertyGroup)
    bpy.utils.register_class(DV_LabelPropertyGroup)
    bpy.utils.register_class(OBJECT_OT_bar_chart)
    bpy.utils.register_class(OBJECT_OT_pie_chart)
    bpy.utils.register_class(OBJECT_OT_line_chart)
    bpy.utils.register_class(OBJECT_OT_point_chart)
    bpy.utils.register_class(FILE_OT_DVLoadFile)
    bpy.utils.register_class(DV_AddonPanel)
    bpy.utils.register_class(OBJECT_MT_AddChart)
    bpy.types.VIEW3D_MT_add.append(chart_ops)

    bpy.types.Scene.dv_props = bpy.props.PointerProperty(type=DV_PropertyGroup)


def unregister():
    bpy.utils.unregister_class(DV_PropertyGroup)
    bpy.utils.unregister_class(DV_RowProp)
    bpy.utils.unregister_class(OBJECT_MT_AddChart)
    bpy.utils.unregister_class(DV_AddonPanel)
    bpy.utils.unregister_class(OBJECT_OT_bar_chart)
    bpy.utils.unregister_class(OBJECT_OT_pie_chart)
    bpy.utils.unregister_class(OBJECT_OT_line_chart)
    bpy.utils.unregister_class(OBJECT_OT_point_chart)
    bpy.utils.unregister_class(FILE_OT_DVLoadFile)
    bpy.utils.unregister_class(DV_LabelPropertyGroup)
    bpy.types.VIEW3D_MT_add.remove(chart_ops)


if __name__ == '__main__':
    register()
