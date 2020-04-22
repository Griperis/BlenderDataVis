import bpy
import math

from data_vis.general import OBJECT_OT_GenericChart, DV_AxisPropertyGroup, DV_LabelPropertyGroup, DV_ColorPropertyGroup, DV_AnimationPropertyGroup, DV_HeaderPropertyGroup
from data_vis.utils.data_utils import normalize_value
from data_vis.colors import NodeShader
from data_vis.operators.features.axis import AxisFactory
from data_vis.data_manager import DataManager, DataType

try:
    import numpy as np
    from scipy import interpolate
    modules_available = True
except ImportError as e:
    print('Warning: Modules not installed in blender python: numpy, scipy')
    modules_available = False


class OBJECT_OT_SurfaceChart(OBJECT_OT_GenericChart):
    '''Creates Surface Chart (needs scipy in Blender python)'''
    bl_idname = 'object.create_surface_chart'
    bl_label = 'Surface Chart'
    bl_options = {'REGISTER', 'UNDO'}

    dimensions: bpy.props.EnumProperty(
        name='Dimensions',
        items=(
            ('3', '3D', 'X, Y, Z'),
        ),
        options={'HIDDEN'}
    )

    density: bpy.props.IntProperty(
        name='Grid size',
        min=1,
        max=200,
        default=20,
    )

    rbf_function: bpy.props.EnumProperty(
        name='RBF Method',
        items=(
            ('multiquadric', 'Multiquadric', '[DEFAULT] sqrt((r/self.epsilon)**2 + 1'),
            ('inverse', 'Inverse', '1.0/sqrt((r/self.epsilon)**2 + 1'),
            ('gaussian', 'Gaussian', 'exp(-(r/self.epsilon)**2'),
            ('linear', 'Linear', 'r'),
            ('cubic', 'Cubic', 'r**3'),
            ('quintic', 'Quintic', 'r**5'),
            ('thin_plate', 'Thin Plate', 'r**2 * log(r)'),
        ),
        description='See: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html',
    )

    axis_settings: bpy.props.PointerProperty(
        type=DV_AxisPropertyGroup
    )

    label_settings: bpy.props.PointerProperty(
        type=DV_LabelPropertyGroup
    )

    anim_settings: bpy.props.PointerProperty(
        type=DV_AnimationPropertyGroup
    )

    header_settings: bpy.props.PointerProperty(
        type=DV_HeaderPropertyGroup
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
        return modules_available and DataManager().is_type(DataType.Numerical, [3])

    def draw(self, context):
        super().draw(context)
        layout = self.layout

        box = layout.box()
        box.label(icon='COLOR', text='Color Settings:')
        box.prop(self, 'color_shade')

        row = layout.row()
        row.prop(self, 'rbf_function')
   
        row = layout.row()
        row.prop(self, 'density')

    def face(self, column, row):
        return (column * self.density + row,
                (column + 1) * self.density + row,
                (column + 1) * self.density + 1 + row,
                column * self.density + 1 + row)

    def execute(self, context):
        self.init_data()

        self.create_container()

        x = np.linspace(self.axis_settings.x_range[0], self.axis_settings.x_range[1], self.density)
        y = np.linspace(self.axis_settings.x_range[0], self.axis_settings.y_range[1], self.density)
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
                x_norm = row / self.density
                y_norm = col / self.density
                z_norm = normalize_value(res[row][col], self.axis_settings.z_range[0], self.axis_settings.z_range[1])
                verts.append((x_norm, y_norm, z_norm))
                if row < self.density - 1 and col < self.density - 1:
                    fac = self.face(col, row)
                    faces.append(fac)

        mesh = bpy.data.meshes.new('DV_SurfaceChart_Mesh')
        mesh.from_pydata(verts, [], faces)

        obj = bpy.data.objects.new('SurfaceChart_Mesh_Obj', mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = self.container_object

        mat = NodeShader(self.get_name(), self.color_shade, location_z=self.container_object.location[2]).create_geometry_shader()
        obj.data.materials.append(mat)
        obj.active_material = mat

        if self.anim_settings.animate:
            verts = obj.data.vertices
            sk_basis = obj.shape_key_add(name='Basis')
            frame_n = context.scene.frame_current
            sk_basis.keyframe_insert(data_path='value', frame=frame_n)

            start_idx = 3  # cause of 3 dimensions supported and already parsed

            # Create shape keys
            for n in range(start_idx, start_idx + self.dm.tail_length):
                f = [entry[n] for entry in self.data]
                rbfi = interpolate.Rbf(px, py, f, function=self.rbf_function)
                res = rbfi(X, Y)

                sk = obj.shape_key_add(name='Column: ' + str(n))

                for i in range(len(verts)):
                    z_norm = normalize_value(res[i % self.density][i // self.density], self.axis_settings.z_range[0], self.axis_settings.z_range[1])
                    sk.data[i].co.z = z_norm
                    sk.value = 0

                # add animation
            
            for sk in obj.data.shape_keys.key_blocks:
                frame_n += self.anim_settings.key_spacing
                sk.value = 1
                sk.keyframe_insert(data_path='value', frame=frame_n)
                for sko in obj.data.shape_keys.key_blocks:
                    if sko != sk:
                        sko.value = 0
                        sko.keyframe_insert(data_path='value', frame=frame_n)

        if self.axis_settings.create:
            AxisFactory.create(
                self.container_object,
                self.axis_settings,
                3,
                self.chart_id,
                labels=self.labels,
            )

        if self.header_settings.create:
            self.create_header()
        self.select_container()
        return {'FINISHED'}

