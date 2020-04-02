import bpy
from scipy.interpolate import griddata
import numpy as np
import math

from data_vis.general import OBJECT_OT_GenericChart, DV_AxisPropertyGroup, DV_LabelPropertyGroup, DV_ColorPropertyGroup
from data_vis.utils.data_utils import find_data_range, normalize_value
from data_vis.colors import NodeShader
from data_vis.operators.features.axis import AxisFactory


class OBJECT_OT_SurfaceChart(OBJECT_OT_GenericChart):
    '''Creates Surface Chart'''
    bl_idname = 'object.create_surface_chart'
    bl_label = 'Surface Chart'
    bl_options = {'REGISTER', 'UNDO'}

    density: bpy.props.IntProperty(
        name='Density of grid',
        min=1,
        default=10,
    )

    interpolation_method: bpy.props.EnumProperty(
        name='Interpolation method',
        items=(
            ('nearest', 'Nearest', 'nearest'),
            ('linear', 'Linear', 'linear'),
            ('cubic', 'Cubic', 'cubic'),
        )
    )

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup
    )

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Base Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        description='Base color shade to work with'
    )

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        super().draw(context)
        layout = self.layout
        
        row = layout.row()
        row.prop(self, 'interpolation_method')
        
        row = layout.row()
        row.prop(self, 'density')

        row = layout.row()
        row.prop(self, 'color_shade')

    def face(self, column, row):
        return (column * self.density + row,
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
        f = [normalize_value(entry[2], data_min, data_max) for entry in self.data]
        res = griddata((px, py), f, (X, Y), self.interpolation_method, 0.0)

        faces = []
        verts = []
        for row in range(self.density):
            for col in range(self.density):
                x_norm = row / self.density
                y_norm = col / self.density
                z_norm = res[row][col]
                verts.append((x_norm, y_norm, z_norm))
                if row < self.density - 1 and col < self.density - 1:
                    fac = self.face(col, row)
                    faces.append(fac)

        mesh = bpy.data.meshes.new('DV_SurfaceChart_Mesh')
        mesh.from_pydata(verts, [], faces)

        obj = bpy.data.objects.new('SurfaceChart_Mesh_Obj', mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = self.container_object

        mat = NodeShader(self.color_shade, location_z=self.container_object.location[2]).create_geometry_shader()
        obj.data.materials.append(mat)
        obj.active_material = mat

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                (self.axis_settings.x_step, self.axis_settings.y_step, self.axis_settings.z_step),
                (self.axis_settings.x_range, self.axis_settings.y_range, (data_min, data_max)),
                3,
                self.axis_settings.thickness,
                self.axis_settings.tick_mark_height,
                padding=self.axis_settings.padding,
                auto_steps=self.axis_settings.auto_steps,
                offset=0.0
            )

        return {'FINISHED'}

