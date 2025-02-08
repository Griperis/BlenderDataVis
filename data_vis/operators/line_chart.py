# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import math


from ..utils.data_utils import (
    normalize_value,
    get_data_in_range,
)
from .features.axis import AxisFactory
from ..general import OBJECT_OT_GenericChart
from ..properties import (
    DV_LabelPropertyGroup,
    DV_AxisPropertyGroup,
    DV_HeaderPropertyGroup,
)
from ..data_manager import DataManager, DataType
from ..colors import NodeShader, ColorGen, ColorType


class OBJECT_OT_LineChart(OBJECT_OT_GenericChart):
    """Creates Line Chart, supports 2D Numerical or Categorical values with or w/o labels"""

    bl_idname = "object.create_line_chart"
    bl_label = "Line Chart"
    bl_options = {"REGISTER", "UNDO"}

    bevel_edges: bpy.props.BoolProperty(
        name="Bevel edges", description="Can have bad affect on data from large dataset"
    )

    data_type: bpy.props.EnumProperty(
        name="Chart type",
        items=(
            ("0", "Numerical", "X relative to Z or Y"),
            ("1", "Categorical", "Label and value"),
        ),
    )

    rounded: bpy.props.EnumProperty(
        name="Settings",
        items=(("1", "Rounded", "Beveled corners"), ("2", "Sharp", "Sharp corners")),
    )

    label_settings: bpy.props.PointerProperty(type=DV_LabelPropertyGroup)

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup,
    )

    header_settings: bpy.props.PointerProperty(type=DV_HeaderPropertyGroup)

    color_shade: bpy.props.FloatVectorProperty(
        name="Base Color",
        subtype="COLOR",
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        description="Base color shade to work with",
    )

    use_shader: bpy.props.BoolProperty(
        name="Use Nodes",
        default=True,
    )

    series_label: bpy.props.BoolProperty(
        name="Series Label", description="Creates color and label for series"
    )

    series_label_text: bpy.props.StringProperty(name="Label Text", default="Series")

    series_label_size: bpy.props.FloatProperty(name="Size", default=0.07)

    def __init__(self):
        super().__init__()
        self.only_2d = True
        self.bevel_obj_size = (0.01, 0.01, 0.01)
        self.bevel_settings = {
            "rounded": {
                "segments": 5,
                "offset": 0.05,
                "profile": 0.6,
            },
            "sharp": {
                "segments": 3,
                "offset": 0.02,
                "profile": 1.0,
            },
        }

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return dm.is_type(DataType.Numerical, [2]) or dm.is_type(
            DataType.Categorical, [2]
        )

    def draw(self, context):
        super().draw(context)
        layout = self.layout

        box = layout.box()
        box.label(icon="COLOR", text="Colors:")
        box.prop(self, "use_shader")
        box.prop(self, "color_shade")

        box = layout.box()
        box.prop(self, "bevel_edges")
        if self.bevel_edges:
            box.prop(self, "rounded")

        box.separator()
        box.prop(self, "series_label")
        if self.series_label:
            box.prop(self, "series_label_text")
            box.prop(self, "series_label_size")

    def execute(self, context):
        self.init_data()

        if (
            self.dm.predicted_data_type == DataType.Categorical
            and self.data_type_as_enum() == DataType.Numerical
        ):
            self.report({"ERROR"}, "Cannot convert categorical data into numerical!")
            return {"CANCELLED"}

        self.create_container()

        if self.data_type_as_enum() == DataType.Numerical:
            self.data = get_data_in_range(self.data, self.axis_settings.x_range)
            sorted_data = sorted(self.data, key=lambda x: x[0])
        else:
            sorted_data = self.data

        tick_labels = []
        if self.data_type_as_enum() == DataType.Numerical:
            normalized_vert_list = [
                (
                    self.normalize_value(entry[0], "x"),
                    0.0,
                    self.normalize_value(entry[1], "z"),
                )
                for entry in sorted_data
            ]
        else:
            normalized_vert_list = [
                (
                    normalize_value(i, 0, len(self.data)),
                    0.0,
                    self.normalize_value(entry[1], "z"),
                )
                for i, entry in enumerate(sorted_data)
            ]
            tick_labels = list(zip(*sorted_data))[0]

        edges = [[i - 1, i] for i in range(1, len(normalized_vert_list))]

        self.create_curve(normalized_vert_list, edges)
        self.add_bevel_obj()
        if self.use_shader:
            mat = NodeShader(
                self.get_name(),
                self.color_shade,
                scale=self.container_size[2],
                location_z=self.container_object.location[2],
            ).create_geometry_shader()
        else:
            mat = ColorGen(
                self.color_shade, ColorType.Constant, self.axis_settings.z_range
            ).get_material()

        self.curve_obj.data.materials.append(mat)
        self.curve_obj.active_material = mat

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                self.axis_settings,
                2,
                self.chart_id,
                labels=self.labels,
                tick_labels=(tick_labels, [], []),
                container_size=self.container_size,
            )

        if self.series_label:
            self.create_series_label(mat)

        if self.header_settings.create:
            self.create_header()

        self.select_container()
        return {"FINISHED"}

    def create_series_label(self, material):
        """Creates label for series specified with material"""
        bpy.ops.object.empty_add()
        container = bpy.context.active_object

        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.align_x = "LEFT"
        to.data.align_y = "CENTER"
        to.name = "SeriesLabel"
        to.location = (self.series_label_size + 0.02, 0, 0)
        to.scale *= self.series_label_size
        to.parent = container
        to.data.body = str(self.series_label_text)
        to.data.materials.append(
            bpy.data.materials.get("DV_TextMat_" + str(self.chart_id))
        )

        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        plane.data.materials.append(material)
        plane.active_material = material
        plane.scale = (self.series_label_size - 0.01, self.series_label_size - 0.01, 1)
        plane.location = (0, 0, 0)
        plane.parent = container

        container.location = (1.2, 0, 0.5)
        container.rotation_euler = (math.radians(90), 0, 0)
        container.parent = self.container_object

    def create_curve(self, verts, edges):
        """Creates object wit hdata from verts and edges"""
        m = bpy.data.meshes.new("line_mesh")
        self.curve_obj = bpy.data.objects.new("line_chart_curve", m)

        bpy.context.scene.collection.objects.link(self.curve_obj)
        self.curve_obj.parent = self.container_object
        m.from_pydata(verts, edges, [])
        m.update()

        self.select_curve_obj()
        if self.bevel_edges:
            self.bevel_curve_obj()

        bpy.ops.object.convert(target="CURVE")

    def bevel_curve_obj(self):
        """Bevels curve object"""
        bpy.ops.object.mode_set(mode="EDIT")
        opts = (
            self.bevel_settings["rounded"]
            if self.rounded == "1"
            else self.bevel_settings["sharp"]
        )
        # vertex_only argument doesn't exists above 2.83.0
        if bpy.app.version > (2, 83, 0):
            bpy.ops.mesh.bevel(
                segments=opts["segments"],
                offset=opts["offset"],
                offset_type="OFFSET",
                profile=opts["profile"],
            )
        else:
            bpy.ops.mesh.bevel(
                segments=opts["segments"],
                offset=opts["offset"],
                offset_type="OFFSET",
                profile=opts["profile"],
                vertex_only=True,
            )
        bpy.ops.object.mode_set(mode="OBJECT")

    def add_bevel_obj(self):
        """Adds bevel object to existing curve"""
        bpy.ops.mesh.primitive_plane_add()
        bevel_obj = bpy.context.active_object
        bevel_obj.scale = self.bevel_obj_size
        bevel_obj.parent = self.container_object

        bpy.ops.object.convert(target="CURVE")
        if hasattr(self.curve_obj.data, "bevel_mode"):
            self.curve_obj.data.bevel_mode = "OBJECT"
        self.curve_obj.data.bevel_object = bevel_obj
        return bevel_obj

    def select_curve_obj(self):
        self.curve_obj.select_set(True)
        bpy.context.view_layer.objects.active = self.curve_obj
