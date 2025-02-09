# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import mathutils
import numpy as np
import colorsys
from . import library
from . import components
from . import data
from .. import preferences
from ..icon_manager import IconManager
from .. import utils
from . import panel
from . import modifier_utils
from ..data_manager import DataManager


class DV_GN_Chart(bpy.types.Operator):
    ACCEPTABLE_DATA_TYPES = None

    color: bpy.props.FloatVectorProperty(
        name="Base Color",
        description="Base color of the chart, other colors are derived from this one",
        min=0.0,
        max=1.0,
        subtype="COLOR",
        default=(0.0, 0.0, 1.0),
        size=3,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return len(context.scene.data_list) > 0 and data.is_data_suitable(
            cls.ACCEPTABLE_DATA_TYPES
        )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def _add_chart_to_scene(
        self, context: bpy.types.Context, obj: bpy.types.Object
    ) -> None:
        obj.location = context.scene.cursor.location
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

    def _apply_material(
        self,
        modifier: bpy.types.NodesModifier,
        type_: library.MaterialType,
    ) -> None:
        material = library.load_material(type_).copy()
        base_color = mathutils.Color(self.color)
        if type_ == library.MaterialType.GradientRandom:
            color_ramp = material.node_tree.nodes["Color Ramp"].color_ramp
            color_ramp.elements[0].color = self._calc_hsv(*base_color.hsv)
            color_ramp.elements[1].color = self._calc_hsv(
                base_color.h - 0.16, base_color.s, base_color.v
            )
        elif type_ == library.MaterialType.Gradient:
            color_ramp = material.node_tree.nodes["Color Ramp"].color_ramp
            color_ramp.elements[0].color = self._calc_hsv(*base_color.hsv)
            color_ramp.elements[1].color = self._calc_hsv(
                base_color.h - 0.16, base_color.s, base_color.v
            )
        elif type_ == library.MaterialType.Sign:
            material.node_tree.nodes["Mix"].inputs["A"].default_value = self._calc_hsv(
                *base_color.hsv
            )
            material.node_tree.nodes["Mix"].inputs["B"].default_value = self._calc_hsv(
                base_color.h - 0.5, base_color.s, base_color.v
            )
        elif type_ == library.MaterialType.Constant:
            material.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (
                mathutils.Vector([*self.color, 1.0])
            )

        modifier_utils.set_input(modifier, "Material", material)

    def _calc_hsv(self, h: float, s: float, v: float) -> mathutils.Vector:
        if h < 0:
            h = 1.0 - h
        return mathutils.Vector([*colorsys.hsv_to_rgb(h, s, v), 1.0])


@utils.logging.logged_operator
class DV_GN_BarChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_bar_chart"
    bl_label = "Bar Chart"
    bl_description = "Creates a bar chart from selected data"

    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.Data2D,
        data.DataTypeValue.Data2DA,
        data.DataTypeValue.Data3D,
        data.DataTypeValue.Data3DA,
        data.DataTypeValue.CATEGORIC_Data2D,
        data.DataTypeValue.CATEGORIC_Data2DA,
    }

    # This has to be defined per each chart, otherwise we can't access the ACCEPTABLE_DATA_TYPES
    data_type: bpy.props.EnumProperty(
        name="Data Type",
        description="Type of data to use for the chart",
        items=lambda self, context: data.get_current_data_types_enum(
            self, context, DV_GN_BarChart.ACCEPTABLE_DATA_TYPES
        ),
    )

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(self, "data_type")
        layout.prop(prefs, "color_type")
        layout.prop(self, "color")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object("DV_BarChart", self.data_type)
        data_nodegroup = library.load_data_nodegroup()
        data_modifier: bpy.types.NodesModifier = obj.modifiers.new("Data", "NODES")
        data_modifier.node_group = data_nodegroup

        chart_nodegroup = library.load_chart("DV_BarChart")
        chart_modifier: bpy.types.NodesModifier = obj.modifiers.new(
            "Bar Chart", "NODES"
        )
        chart_modifier.node_group = chart_nodegroup

        components.mark_as_chart([obj])
        self._add_chart_to_scene(context, obj)
        self._apply_material(chart_modifier, prefs.color_type)
        modifier_utils.add_used_materials_to_object(chart_modifier, obj)
        return {"FINISHED"}


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
        data.DataTypeValue.CATEGORIC_Data2D,
        data.DataTypeValue.CATEGORIC_Data2DA,
        # TODO: A + W
    }

    # This has to be defined per each chart, otherwise we can't access the ACCEPTABLE_DATA_TYPES
    data_type: bpy.props.EnumProperty(
        name="Data Type",
        description="Type of data to use for the chart",
        items=lambda self, context: data.get_current_data_types_enum(
            self, context, DV_GN_PointChart.ACCEPTABLE_DATA_TYPES
        ),
    )

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(self, "data_type")
        layout.prop(prefs, "color_type")
        layout.prop(self, "color")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object("DV_PointChart", self.data_type)
        data_nodegroup = library.load_data_nodegroup()
        data_modifier: bpy.types.NodesModifier = obj.modifiers.new("Data", "NODES")
        data_modifier.node_group = data_nodegroup

        node_group = library.load_chart("DV_PointChart")
        chart_modifier: bpy.types.NodesModifier = obj.modifiers.new(
            "Point Chart", "NODES"
        )
        chart_modifier.node_group = node_group

        components.mark_as_chart([obj])
        self._add_chart_to_scene(context, obj)
        self._apply_material(chart_modifier, prefs.color_type)
        modifier_utils.add_used_materials_to_object(chart_modifier, obj)
        return {"FINISHED"}


class DV_GN_LineChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_line_chart"
    bl_label = "Line Chart"
    bl_description = (
        "Creates a line chart from selected data, the data points "
        "are connected with edges."
    )

    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.Data2D,
        data.DataTypeValue.Data2DA,
        data.DataTypeValue.CATEGORIC_Data2D,
        data.DataTypeValue.CATEGORIC_Data2DA,
    }
    # This has to be defined per each chart, otherwise we can't access the ACCEPTABLE_DATA_TYPES
    data_type: bpy.props.EnumProperty(
        name="Data Type",
        description="Type of data to use for the chart",
        items=lambda self, context: data.get_current_data_types_enum(
            self, context, DV_GN_LineChart.ACCEPTABLE_DATA_TYPES
        ),
    )

    def draw(self, context: bpy.types.Context) -> None:
        prefs = preferences.get_preferences(context)
        layout = self.layout
        layout.prop(self, "data_type")
        layout.prop(prefs, "color_type")
        layout.prop(self, "color")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object(
            "DV_LineChart", self.data_type, connect_edges=True
        )
        data_nodegroup = library.load_data_nodegroup()
        data_modifier: bpy.types.NodesModifier = obj.modifiers.new("Data", "NODES")
        data_modifier.node_group = data_nodegroup

        node_group = library.load_chart("DV_LineChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Line Chart", "NODES")
        modifier.node_group = node_group

        components.mark_as_chart([obj])
        self._add_chart_to_scene(context, obj)
        self._apply_material(modifier, prefs.color_type)
        modifier_utils.add_used_materials_to_object(modifier, obj)
        return {"FINISHED"}


class DV_GN_SurfaceChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_surface_chart"
    bl_label = "Surface Chart"
    bl_description = (
        "Creates a surface chart from selected data, the data points "
        "are interpolated to create a smooth surface. Requires scipy in Blender Python"
    )

    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.Data3D,
        data.DataTypeValue.Data3DA,
    }

    # This has to be defined per each chart, otherwise we can't access the ACCEPTABLE_DATA_TYPES
    data_type: bpy.props.EnumProperty(
        name="Data Type",
        description="Type of data to use for the chart",
        items=lambda self, context: data.get_current_data_types_enum(
            self, context, DV_GN_SurfaceChart.ACCEPTABLE_DATA_TYPES
        ),
    )

    rbf_function: bpy.props.EnumProperty(
        name="Interpolation Method",
        items=utils.interpolation.TYPES_ENUM,
        description="See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html",
    )

    grid_x: bpy.props.IntProperty(
        name="Grid X",
        description="Size of the interpolated grid across X axis",
        min=1,
        default=20,
    )

    grid_y: bpy.props.IntProperty(
        name="Grid Y",
        description="Size of the interpolated grid across Y axis",
        min=1,
        default=20,
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
        layout.prop(self, "data_type")
        layout.prop(prefs, "color_type")
        layout.prop(self, "color")
        layout.prop(self, "rbf_function")
        layout.prop(self, "grid_x")
        layout.prop(self, "grid_y")

    def execute(self, context: bpy.types.Context):
        prefs = preferences.get_preferences(context)
        obj: bpy.types.Object = data.create_data_object(
            "DV_SurfaceChart",
            self.data_type,
            interpolation_config=data.InterpolationConfig(
                method=self.rbf_function, m=self.grid_x, n=self.grid_y
            ),
        )
        data_nodegroup = library.load_data_nodegroup()
        data_modifier: bpy.types.NodesModifier = obj.modifiers.new("Data", "NODES")
        data_modifier.node_group = data_nodegroup

        node_group = library.load_chart("DV_SurfaceChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Surface Chart", "NODES")
        modifier.node_group = node_group

        components.mark_as_chart([obj])
        self._add_chart_to_scene(context, obj)
        self._apply_material(modifier, prefs.color_type)
        modifier_utils.add_used_materials_to_object(modifier, obj)
        return {"FINISHED"}


class DV_GN_PieChart(DV_GN_Chart):
    bl_idname = "data_vis.geonodes_pie_chart"
    bl_label = "Pie Chart"
    bl_description = (
        "Creates a pie chart from selected data. Maximum of " "10 values are supported"
    )

    MAX_VALUES = 10
    ACCEPTABLE_DATA_TYPES = {
        data.DataTypeValue.CATEGORIC_Data2D,
    }

    # This has to be defined per each chart, otherwise we can't access the ACCEPTABLE_DATA_TYPES
    data_type: bpy.props.EnumProperty(
        name="Data Type",
        description="Type of data to use for the chart",
        items=lambda self, context: data.get_current_data_types_enum(
            self, context, DV_GN_PieChart.ACCEPTABLE_DATA_TYPES
        ),
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if not super().poll(context):
            return False

        return DataManager().lines < cls.MAX_VALUES

    def execute(self, context: bpy.types.Context):
        obj = bpy.data.objects.new("DV_PieChart", bpy.data.meshes.new("DV_PieChart"))
        node_group = library.load_chart("DV_PieChart")
        modifier: bpy.types.NodesModifier = obj.modifiers.new("Pie Chart", "NODES")
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
        data._store_chart_data_info(
            obj, np.array(parsed_data), None, data.DataTypeValue.CATEGORIC_Data2D
        )
        self._add_chart_to_scene(context, obj)
        modifier_utils.add_used_materials_to_object(modifier, obj)
        return {"FINISHED"}


class DV_ChartPanel(bpy.types.Panel, panel.DV_GN_PanelMixin):
    bl_idname = "DV_PT_chart_panel"
    bl_label = "Chart"

    @classmethod
    def poll(self, context: bpy.types.Context):
        return components.is_chart(context.active_object)

    def draw_header(self, context: bpy.types.Context):
        self.layout.label(text="", icon_value=IconManager().get_icon_id("addon_icon"))

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        obj = context.active_object
        if obj is None:
            layout.label(text="No active object")
            return

        if not components.is_chart(obj):
            layout.label(text="Active object is not a valid chart")
            return

        for mod in filter(
            lambda m: m.type == "NODES"
            and components.remove_duplicate_suffix(m.node_group.name).startswith("DV_")
            and components.remove_duplicate_suffix(m.node_group.name).endswith("Chart"),
            obj.modifiers,
        ):
            box = layout.box()
            row = box.row()
            row.prop(mod, "show_expanded", text="")
            row.label(text=mod.name)
            row.operator(
                modifier_utils.DV_RemoveModifier.bl_idname, text="", icon="X"
            ).modifier_name = mod.name
            if mod.show_expanded:
                modifier_utils.draw_modifier_inputs(mod, box)
