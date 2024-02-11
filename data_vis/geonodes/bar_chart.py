import bpy
from . import library
from . import components
from . import data
from . import modifier_utils
from .. import preferences
from .. import utils


@utils.logging.logged_operator
class DV_GN_BarChart(bpy.types.Operator):
    bl_idname = "data_vis.geonodes_bar_chart"
    bl_label = "Bar Chart"

    ACCEPTABLE_DATA_TYPES = {
        data.DataType.Data2D,
        data.DataType.Data2DA,
        data.DataType.Data3D,
        data.DataType.Data3DA
    }
    
    @classmethod
    def poll(cls, context: bpy.types.Context):
        return data.is_data_suitable(cls.ACCEPTABLE_DATA_TYPES)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(prefs.data, "data_type")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object("DV_BarChart", prefs.data.data_type)
        
        node_group = library.load_chart("DV_BarChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Bar Chart", 'NODES')
        modifier.node_group = node_group
        if data.DataType.is_animated(prefs.data.data_type):
            modifier_utils.set_input(modifier.node_group, "Override Z Range", None)

        components.mark_as_chart([obj])
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        return {'FINISHED'}
    
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        prefs = preferences.get_preferences(context)
        prefs.data.set_current_types(self.ACCEPTABLE_DATA_TYPES)
        return context.window_manager.invoke_props_dialog(self)