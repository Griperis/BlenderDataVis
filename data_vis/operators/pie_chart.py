# File: pie_chart.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Pie chart implementation

from data_vis.icon_manager import IconManager
import bpy
import math
import logging

logger = logging.getLogger("data_vis")

from data_vis.general import (
    OBJECT_OT_GenericChart,
    DV_HeaderPropertyGroup,
    DV_LegendPropertyGroup,
)
from data_vis.data_manager import DataManager, DataType
from data_vis.colors import ColorGen, ColorType
from data_vis.operators.features.legend import Legend


class OBJECT_OT_PieChart(OBJECT_OT_GenericChart):
    """Creates Pie Chart, supports 2D Categorical values without labels"""

    bl_idname = "object.create_pie_chart"
    bl_label = "Pie Chart"
    bl_options = {'REGISTER', 'UNDO'}

    header_settings: bpy.props.PointerProperty(type=DV_HeaderPropertyGroup)

    legend_settings: bpy.props.PointerProperty(type=DV_LegendPropertyGroup)

    vertices: bpy.props.IntProperty(name="Vertices", min=3, default=64)

    text_size: bpy.props.FloatProperty(name="Label Size", min=0.01, default=0.05)

    text_format: bpy.props.EnumProperty(
        name="Text Format",
        items=(
            (
                "label_percent",
                "Label And Percent",
                "Text will be formated as label with percents representing portion of pie",
            ),
            ("label_data", "Label And Data Value", "Label with value from data"),
            (
                "label_decimal",
                "Label And Decimal",
                "Label with decimal value (percent / 100)",
            ),
            ("percent", "Percent", "Only percent"),
            ("decimal", "Decimal", "Only decimal (percent / 100)"),
            ("data", "Data Value", "Only value from data"),
        ),
    )

    create_labels: bpy.props.BoolProperty(name="Create Labels", default=True)

    label_distance: bpy.props.FloatProperty(
        name="Label Distance",
        min=0.0,
        default=0.5,
    )

    scale_z_with_value: bpy.props.BoolProperty(
        name="Scale Slices With Value",
        default=False,
    )

    slice_size: bpy.props.FloatProperty(
        name="Slice Height",
        default=1,
    )

    color_shade: bpy.props.FloatVectorProperty(
        name="Base Color", subtype="COLOR", default=(0.0, 0.0, 1.0), min=0.0, max=1.0
    )

    color_type: bpy.props.EnumProperty(
        name="Coloring Type",
        items=(
            ("0", "Gradient", "Gradient based on value"),
            ("1", "Constant", "One color"),
            ("2", "Random", "Random colors"),
        ),
        default="0",
        description="Type of coloring for chart",
    )

    @classmethod
    def poll(cls, context):
        dm = DataManager()
        return dm.is_type(DataType.Categorical, [2])

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        layout.use_property_split = True
        box = layout.box()
        box.label(icon="COLOR", text="Color settings:")
        box.prop(self, "color_type")
        if self.color_type != "2":
            box.prop(self, "color_shade")

        box = layout.box()
        box.label(
            text="Pie Chart Settings", icon_value=IconManager().get_icon_id("pie_chart")
        )
        box.prop(self, "vertices")
        box.separator()
        box.prop(self, "scale_z_with_value")
        if self.scale_z_with_value:
            box.prop(self, "slice_size")
        box.separator()
        row = box.row()
        row.label(text="Create Slice Labels", icon="TRIA_RIGHT")
        row.prop(self, "create_labels")
        if self.create_labels:
            box.prop(self, "label_distance")
            box.prop(self, "text_format")
            box.prop(self, "text_size")

    def execute(self, context):
        self.slices = []
        self.materials = []
        self.init_data()

        data_min = min(self.data, key=lambda entry: entry[1])[1]
        if data_min <= 0:
            self.report({'ERROR'}, "Pie chart support only positive values!")
            return {'CANCELLED'}

        data_len = len(self.data)
        if data_len >= self.vertices:
            self.report(
                {'ERROR'},
                "There are more data than possible slices, "
                + "please increase the vertices value!",
            )
            return {'CANCELLED'}

        self.create_container()

        # create cylinder from triangles
        rot = 0
        rot_inc = 2.0 * math.pi / self.vertices
        scale = 1.0 / self.vertices * math.pi
        for i in range(0, self.vertices):
            cyl_slice = self.create_slice()
            cyl_slice.scale.y *= scale
            cyl_slice.rotation_euler.z = rot
            rot += rot_inc
            self.slices.append(cyl_slice)

        values_sum = sum(float(entry[1]) for entry in self.data)
        color_gen = ColorGen(
            self.color_shade, ColorType.str_to_type(self.color_type), (0, data_len)
        )

        prev_i = 0
        legend_data = {}
        for i in range(data_len):

            portion = self.data[i][1] / values_sum
            increment = round(portion * self.vertices)
            # Ignore data with zero value
            if increment == 0:
                logger.warning(
                    "Warning: Data with zero value i: {}, value: {}! Useless for pie chart.".format(
                        i, self.data[i][1]
                    )
                )
                continue

            portion_end_i = prev_i + increment
            slice_obj = self.join_slices(prev_i, portion_end_i)
            if slice_obj is None:
                raise RuntimeError(
                    'Error occurred, try to increase number of vertices, i_from" {}, i_to: {}, inc: {}, val: {}'.format(
                        prev_i, portion_end_i, increment, self.data[i][1]
                    )
                )

            slice_mat = color_gen.get_material(data_len - i)
            slice_obj.active_material = slice_mat

            if self.scale_z_with_value:
                slice_obj.scale.z = self.slice_size * portion

            slice_obj.parent = self.container_object
            if self.create_labels:
                rotation_z = ((prev_i + portion_end_i) * 0.5) / self.vertices
                label_obj = self.add_value_label(
                    self.label_distance,
                    rotation_z * 2.0 * math.pi + math.pi,
                    self.data[i][0],
                    self.data[i][1],
                    portion,
                )
                label_obj.rotation_euler = (0, 0, 0)
            prev_i += increment

            legend_data[str(slice_mat.name)] = self.data[i][0]

        if self.header_settings.create:
            self.create_header(location=(0, 0.7, 0.15), rotate=False)

        if self.legend_settings.create:
            Legend(self.chart_id, self.legend_settings).create(
                self.container_object, legend_data
            )

        self.select_container()
        return {'FINISHED'}

    def join_slices(self, i_from, i_to):
        bpy.ops.object.select_all(action="DESELECT")
        if i_to > len(self.slices) - 1:
            i_to = len(self.slices)
        for i in range(i_from, i_to):
            if i > len(self.slices) - 1:
                logger.error(
                    "IndexError: Cannot portion slices properly: i: {}, len(slices): {}, i_from: {}, i_to: {}".format(
                        i, len(self.slices), i_from, i_to
                    )
                )
                break
            self.slices[i].select_set(state=True)
            bpy.context.view_layer.objects.active = self.slices[i]
        if len(bpy.context.selected_objects) > 0:
            bpy.ops.object.join()
            return bpy.context.active_object
        else:
            return None

    def create_slice(self):
        """
        Creates a triangle (slice of pie chart)
        """
        slice_size = 0.5
        verts = [
            (0, 0, 0.1),
            (-slice_size, slice_size, 0.1),
            (-slice_size, -slice_size, 0.1),
            (0, 0, 0),
            (-slice_size, slice_size, 0),
            (-slice_size, -slice_size, 0),
        ]

        faces = [
            [0, 1, 2],
            [3, 4, 5],
            [0, 1, 3],
            [1, 3, 4],
            [0, 2, 3],
            [2, 3, 5],
            [1, 2, 4],
            [2, 4, 5],
        ]

        mesh = bpy.data.meshes.new("pie_mesh")
        obj = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = self.container_object
        bpy.context.view_layer.objects.active = obj

        mesh.from_pydata(verts, [], faces)
        mesh.update()

        return obj

    def get_formated_text(self, label, value, portion):
        if self.text_format == "label_percent":
            percent = portion * 100
            return f"{label}: {percent:3.2f}%"
        elif self.text_format == "label_data":
            return f"{label}: {value:0.2f}"
        elif self.text_format == "label_decimal":
            return f"{label}: {portion:0.2f}"
        elif self.text_format == "percent":
            percent = portion * 100
            return f"{percent:3.2f}%"
        elif self.text_format == "decimal":
            return f"{portion:0.2f}"
        elif self.text_format == "data":
            return f"{value:0.2f}"

    def add_value_label(self, distance, angle, label, value, portion):
        bpy.ops.object.text_add()
        to = bpy.context.object
        to.data.body = self.get_formated_text(label, value, portion)
        to.data.align_x = "CENTER"
        to.location = (math.cos(angle) * distance, math.sin(angle) * distance, 0.15)
        to.scale *= self.text_size
        to.parent = self.container_object
        to.name = "TextPie"

        mat = bpy.data.materials.get("DV_TextMat_" + str(self.chart_id))
        if mat is None:
            mat = bpy.data.materials.new(name="DV_TextMat_" + str(self.chart_id))

        to.data.materials.append(mat)
        to.active_material = mat
        return to
