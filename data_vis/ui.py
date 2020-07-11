import bpy
from data_vis.chart_manager import ChartManager


class DV_UL_ChartList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        layout.label(text=item.name)

class DV_OT_ChartListActions(bpy.types.Operator):
    '''
    Manipulates with chart list
    '''
    bl_idname = 'chart_list.action'
    bl_label = 'Chart list actions'
    bl_description = 'Add or remove charts from chart list'

    action: bpy.props.EnumProperty(
        items=(
            ('ADD', 'Add', ''),
            ('REMOVE', 'Remove', ''),
            ('PRINT', 'Print', '')
        )
    )

    def invoke(self, context, event):
        if self.action == 'ADD':
            bpy.ops.wm.call_menu(name='OBJECT_MT_Add_Chart')
        elif self.action == 'REMOVE':
            ChartManager().remove_chart()
        elif self.action == 'PRINT':
            print(ChartManager().chart_list)


        return {'FINISHED'}

    
