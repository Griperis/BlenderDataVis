import bpy
from scipy.interpolate import griddata
import numpy as np
import math

from data_vis.general import OBJECT_OT_GenericChart, DV_AxisPropertyGroup
from data_vis.utils.data_utils import find_data_range, normalize_value


class OBJECT_OT_SurfaceChart(OBJECT_OT_GenericChart):
    '''Creates Surface Chart'''
    bl_idname = 'object.create_surface_chart'
    bl_label = 'Surface Chart'
    bl_options = {'REGISTER', 'UNDO'}

    density: bpy.props.IntProperty(
        name='Density of grid',
        min=1,
        default=50,
    )

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        row = layout.row()
        row.prop(self, 'density')

    def face(self, column, row):
        return (column* self.density + row,
        (column + 1) * self.density + row,
        (column + 1) * self.density + 1 + row,
        column * self.density + 1 + row)

    def execute(self, context):
        self.init_data()
        if self.axis_settings.auto_ranges:
            self.init_range(self.data)

        self.create_container()

        x = np.linspace(0, 1, self.density)
        y = np.linspace(0, 1, self.density)
        X, Y = np.meshgrid(x, y)

        data_min, data_max = find_data_range(self.data, self.axis_settings.x_range, self.axis_settings.y_range)

        px = [entry[0] for entry in self.data]
        py = [entry[1] for entry in self.data]
        f = [entry[2] for entry in self.data]

        res = griddata((px, py), f, (X, Y))

        faces = []
        verts = []
        for x in range(self.density):
            for y in range(self.density):
                x_norm = x / self.density
                y_norm = y / self.density
                value = res[x][y]
                if math.isnan(value):
                    value = 0.0
                z_norm = normalize_value(value, data_min, data_max)
                # bpy.ops.mesh.primitive_uv_sphere_add()
                # obj = context.active_object
                # obj.scale = (0.02, 0.02, 0.02)
                # obj.location = (, y / nof_points, res[x][y])
                verts.append((x_norm, y_norm, z_norm))

        mesh = bpy.data.meshes.new('DV_SurfaceChart_Mesh')
        mesh.from_pydata(verts, [], faces)

        obj = bpy.data.objects.new('SurfaceChart', mesh)
        bpy.context.scene.collection.objects.link(obj)

        return {'FINISHED'}

