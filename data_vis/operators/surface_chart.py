# File: surface_chart.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Surface chart implementation

import bpy

from data_vis.general import OBJECT_OT_GenericChart
from data_vis.properties import (
    DV_AxisPropertyGroup,
    DV_LabelPropertyGroup,
    DV_AnimationPropertyGroup,
    DV_HeaderPropertyGroup,
)
from data_vis.colors import NodeShader
from data_vis.operators.features.axis import AxisFactory
from data_vis.data_manager import DataManager, DataType
from data_vis.utils import env_utils, interpolation


class OBJECT_OT_SurfaceChart(OBJECT_OT_GenericChart):
    """Creates Surface Chart (needs scipy in Blender python)"""

    bl_idname = "object.create_surface_chart"
    bl_label = "Surface Chart"
    bl_options = {'REGISTER', 'UNDO'}

    dimensions: bpy.props.EnumProperty(
        name="Dimensions", items=(("3", "3D", "X, Y, Z"),), options={"HIDDEN"}
    )

    density: bpy.props.IntProperty(
        name="Grid size",
        min=1,
        max=200,
        default=20,
    )

    rbf_function: bpy.props.EnumProperty(
        name="Interpolation Method",
        items=interpolation.TYPES_ENUM,
        description="See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html",
    )

    axis_settings: bpy.props.PointerProperty(type=DV_AxisPropertyGroup)

    label_settings: bpy.props.PointerProperty(type=DV_LabelPropertyGroup)

    anim_settings: bpy.props.PointerProperty(type=DV_AnimationPropertyGroup)

    header_settings: bpy.props.PointerProperty(type=DV_HeaderPropertyGroup)

    color_shade: bpy.props.FloatVectorProperty(
        name="Base Color",
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        description="Base color shade to work with",
    )

    @classmethod
    def poll(cls, context):
        for mod in ["scipy", "numpy"]:
            if not env_utils.is_module_installed(mod):
                return False

        return DataManager().is_type(DataType.Numerical, [3], only_3d=True)

    def draw(self, context):
        super().draw(context)
        layout = self.layout

        box = layout.box()
        box.label(icon='COLOR', text="Color Settings:")
        box.prop(self, "color_shade")

        row = layout.row()
        row.prop(self, "rbf_function")

        row = layout.row()
        row.prop(self, "density")

    def face(self, column, row):
        return (
            column * self.density + row,
            (column + 1) * self.density + row,
            (column + 1) * self.density + 1 + row,
            column * self.density + 1 + row,
        )

    def execute(self, context):
        import numpy as np
        from scipy import interpolate

        self.init_data()

        self.create_container()

        x = np.linspace(
            self.axis_settings.x_range[0], self.axis_settings.x_range[1], self.density
        )
        y = np.linspace(
            self.axis_settings.x_range[0], self.axis_settings.y_range[1], self.density
        )
        X, Y = np.meshgrid(x, y)

        px = [entry[0] for entry in self.data]
        py = [entry[1] for entry in self.data]
        f = [entry[2] for entry in self.data]

        rbfi = interpolate.Rbf(px, py, f, function=self.rbf_function)
        res = rbfi(X, Y)

        faces = []
        verts = []
        for row in range(self.density):
            for col in range(self.density):
                x_norm = self.container_size[0] * (row / self.density)
                y_norm = self.container_size[1] * (col / self.density)
                z_norm = self.normalize_value(res[row][col], "z")
                verts.append((x_norm, y_norm, z_norm))
                if row < self.density - 1 and col < self.density - 1:
                    fac = self.face(col, row)
                    faces.append(fac)

        mesh = bpy.data.meshes.new("DV_SurfaceChart_Mesh")
        mesh.from_pydata(verts, [], faces)

        obj = bpy.data.objects.new("SurfaceChart_Mesh_Obj", mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = self.container_object

        mat = NodeShader(
            self.get_name(),
            self.color_shade,
            scale=self.container_size[2],
            location_z=self.container_object.location[2],
        ).create_geometry_shader()
        obj.data.materials.append(mat)
        obj.active_material = mat

        if self.anim_settings.animate:
            verts = obj.data.vertices
            sk_basis = obj.shape_key_add(name="Basis")
            frame_n = context.scene.frame_current
            sk_basis.keyframe_insert(data_path="value", frame=frame_n)

            start_idx = 3  # cause of 3 dimensions supported and already parsed

            # Create shape keys
            for n in range(start_idx, start_idx + self.dm.tail_length):
                f = [entry[n] for entry in self.data]
                rbfi = interpolate.Rbf(px, py, f, function=self.rbf_function)
                res = rbfi(X, Y)

                sk = obj.shape_key_add(name="Column: " + str(n))

                for i in range(len(verts)):
                    z_norm = self.normalize_value(
                        res[i % self.density][i // self.density], "z"
                    )
                    sk.data[i].co.z = z_norm
                    sk.value = 0

                # add animation

            for sk in obj.data.shape_keys.key_blocks:
                frame_n += self.anim_settings.key_spacing
                sk.value = 1
                sk.keyframe_insert(data_path="value", frame=frame_n)
                for sko in obj.data.shape_keys.key_blocks:
                    if sko != sk:
                        sko.value = 0
                        sko.keyframe_insert(data_path="value", frame=frame_n)

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                self.axis_settings,
                3,
                self.chart_id,
                labels=self.labels,
                container_size=self.container_size,
            )

        if self.header_settings.create:
            self.create_header()
        self.select_container()
        return {'FINISHED'}
