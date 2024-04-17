import bpy
from . import library
from . import components
from . import data
from .. import preferences
from .. import utils
from . import modifier_utils
from ..data_manager import DataManager


class DV_GN_Chart(bpy.types.Operator):
    ACCEPTABLE_DATA_TYPES = None

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return data.is_data_suitable(cls.ACCEPTABLE_DATA_TYPES)
    
    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        prefs = preferences.get_preferences(context)
        prefs.data.set_current_types(type(self).ACCEPTABLE_DATA_TYPES)
        return context.window_manager.invoke_props_dialog(self)
    
    def _add_chart_to_scene(self, context: bpy.types.Context, obj: bpy.types.Object) -> None:
        obj.location = context.scene.cursor.location
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)


@utils.logging.logged_operator
class DV_GN_BarChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_bar_chart"
    bl_label = "Bar Chart"

    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.Data2D,
        data.DataTypeValue.Data2DA,
        data.DataTypeValue.Data3D,
        data.DataTypeValue.Data3DA
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
        self._add_chart_to_scene(context, obj)
        return {'FINISHED'}


@utils.logging.logged_operator
class DV_GN_PointChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_point_chart"
    bl_label = "Point Chart"

    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.Data2D,
        data.DataTypeValue.Data2DA,
        data.DataTypeValue.Data3D,
        data.DataTypeValue.Data3DA,
        data.DataTypeValue.Data2DW,
        data.DataTypeValue.Data3DW,
        # TODO: A + W
    }

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(prefs.data, "data_type")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object("DV_PointChart", prefs.data.data_type)
        
        node_group = library.load_chart("DV_PointChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Point Chart", 'NODES')
        modifier.node_group = node_group

        components.mark_as_chart([obj])
        self._add_chart_to_scene(context, obj)
        return {'FINISHED'}


class DV_GN_LineChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_line_chart"
    bl_label = "Line Chart"

    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.Data2D,
        data.DataTypeValue.Data2DA,
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
        self._add_chart_to_scene(context, obj)
        return {'FINISHED'}
    

class DV_GN_SurfaceChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_surface_chart"
    bl_label = "Surface Chart"

    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.Data3D,
        data.DataTypeValue.Data3DA,
    }

    rbf_function: bpy.props.EnumProperty(
        name="Interpolation Method",
        items=utils.interpolation.TYPES_ENUM,
        description="See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html"
    )

    grid_x: bpy.props.IntProperty(
        name="Grid X",
        description="Size of the interpolated grid across X axis",
        min=1,
        default=20
    )

    grid_y: bpy.props.IntProperty(
        name="Grid Y",
        description="Size of the interpolated grid across Y axis",
        min=1,
        default=20
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        try:
            import scipy
        except ImportError:
            return False
        
        return super().poll(context)

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(prefs.data, "data_type")
        layout.prop(self, "rbf_function")
        layout.prop(self, "grid_x")
        layout.prop(self, "grid_y")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object(
            "DV_SurfaceChart",
            prefs.data.data_type,
            interpolation_config=data.InterpolationConfig(
                method=self.rbf_function,
                m=self.grid_x,
                n=self.grid_y
            )
        )
        
        node_group = library.load_chart("DV_SurfaceChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Surface Chart", 'NODES')
        modifier.node_group = node_group

        components.mark_as_chart([obj])
        self._add_chart_to_scene(context, obj)
        return {'FINISHED'}


class DV_GN_PieChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_pie_chart"
    bl_label = "Pie Chart"

    MAX_VALUES = 10
    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.CATEGORIC_Data2D,
    }

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if not super().poll(context):
            return False
        
        return DataManager().lines < cls.MAX_VALUES

    def execute(self, context: bpy.types.Context):
        obj = bpy.data.objects.new("DV_PieChart", bpy.data.meshes.new("DV_PieChart"))
        node_group = library.load_chart("DV_PieChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Pie Chart", 'NODES')
        modifier.node_group = node_group

        dm = DataManager()
        parsed_data = dm.get_parsed_data()
        total = 0
        count = min(len(parsed_data), DV_GN_PieChart.MAX_VALUES)
        for i in range(0, count):
            value = parsed_data[i][1]
            total += value
            label = parsed_data[i][0]     
            modifier_utils.set_input(modifier, f"Value {i + 1}", value)
            modifier_utils.set_input(modifier, f"Label {i + 1}", label)

        modifier_utils.set_input(modifier, "Total", float(total))
        modifier_utils.set_input(modifier, "Shown Labels", count)

        components.mark_as_chart([obj])
        data._mark_chart_data_type(obj, data.DataTypeValue.CATEGORIC_Data2D)
        self._add_chart_to_scene(context, obj)
        return {'FINISHED'}
