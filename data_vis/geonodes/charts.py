import bpy
import typing
from . import library
from . import components
from . import data
from .. import preferences
from .. import utils


class DV_GN_Chart(bpy.types.Operator):
    ACCEPTABLE_DATA_TYPES = None

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return data.is_data_suitable(cls.ACCEPTABLE_DATA_TYPES)
    
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        prefs = preferences.get_preferences(context)
        prefs.data.set_current_types(type(self).ACCEPTABLE_DATA_TYPES)
        return context.window_manager.invoke_props_dialog(self)


@utils.logging.logged_operator
class DV_GN_BarChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_bar_chart"
    bl_label = "Bar Chart"

    ACCEPTABLE_DATA_TYPES = {
        data.DataType.Data2D,
        data.DataType.Data2DA,
        data.DataType.Data3D,
        data.DataType.Data3DA
    }
    
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

        components.mark_as_chart([obj])
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        return {'FINISHED'}


@utils.logging.logged_operator
class DV_GN_PointChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_point_chart"
    bl_label = "Point Chart"

    ACCEPTABLE_DATA_TYPES = {
        data.DataType.Data2D,
        data.DataType.Data2DA,
        data.DataType.Data3D,
        data.DataType.Data3DA,
        data.DataType.Data2DW,
        data.DataType.Data3DW,
        # TODO: A + W
    }

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(prefs.data, "data_type")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object("DV_BubbleChart", prefs.data.data_type)
        
        node_group = library.load_chart("DV_BubbleChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Bubble Chart", 'NODES')
        modifier.node_group = node_group

        components.mark_as_chart([obj])
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        return {'FINISHED'}


class DV_GN_LineChart(DV_GN_Chart):
    ACCEPTABLE_DATA_TYPES = {
        data.DataType.Data2D,
        data.DataType.Data2DA,
    }

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(prefs.data, "data_type")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object("DV_LineChart", prefs.data.data_type, connect_edges=True)
        
        node_group = library.load_chart("DV_LineChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Line Chart", 'NODES')
        modifier.node_group = node_group

        components.mark_as_chart([obj])
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)
        return {'FINISHED'}
    

class DV_GN_SurfaceChart(DV_GN_Chart):
    ...


class DV_GN_PieChart(DV_GN_Chart):
    ...