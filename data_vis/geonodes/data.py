import bpy
import typing
import numpy as np
from ..data_manager import DataManager
W_ATTRIBUTE_NAME = "@w"
DATA_TYPE_PROPERTY = "DV_DataType"

class DataType:
    Data2D = '2D'
    Data2DW = '2D+W'
    Data2DA = '2D+A'
    Data3D = '3D'
    Data3DW = '3D+W'
    Data3DA = '3D+A'

    @staticmethod
    def is_animated(data: str) -> bool:
        return data.endswith("+A")


def get_data_types() -> typing.Set[str]:
        types = set()
        shape = DataManager().get_chart_data().parsed_data.shape
        if shape[0] > 1:
            types.update({DataType.Data2D})
        if shape[0] > 2:
            types.update({DataType.Data2DA, DataType.Data2DW, DataType.Data3D})
        if shape[0] > 3:
            types.update({DataType.Data3DW, DataType.Data3DA})

        return types 


class DV_DataProperties(bpy.types.PropertyGroup):
    current_types: set[str] = set()
    data_type: bpy.props.EnumProperty(
        items=lambda self, context: self._get_data_types_enum(context)
        # (
        #     # 2 columns exactly
        #     (DataType.Data2D, '2D', '2D'),
        #     (DataType.Data2DW, '2D+W', '2D+W'),
        #     # 3+ columns
        #     (DataType.Data2DA, '2D+A', '2D+A'),
        #     # 3 columns exactly
        #     (DataType.Data3D, '3D', '3D'),
        #     # 4 columns exactly
        #     (DataType.Data3DW, '3D+W', '3D+W'),
        #     # 4+ columns
        #     (DataType.Data3DA, '3D+A', '3D+A'),

        #     # TODO: 
        #     # 2D+WA, 3D+WA - animated several @ws
        #     # 2D+W+A, 3D+W+A - @ws with animated z_ns
        # )
    )

    def set_current_types(self, current_types: set[str]) -> None:
        type(self).current_types = current_types

    def _get_data_types_enum(self, context: bpy.types.Context):
        types = get_data_types() & type(self).current_types
        return [(t, t, t) for t in types]


def _mark_chart_data_type(obj: bpy.types.Object, data_type: str) -> None:
    obj[DATA_TYPE_PROPERTY] = data_type


def get_chart_data_type(obj: bpy.types.Object) -> str | None:
    return obj.get(DATA_TYPE_PROPERTY, None)


def create_data_object(
    name: str,
    data_type: str,
    connect_edges: bool = False,
    create_faces: bool = False,
) -> bpy.types.Object:
    dm = DataManager()
    mesh = bpy.data.meshes.new(name) 
    data = dm.get_chart_data().parsed_data
    vert_positions = None
    ws = None
    z_ns = None
    if data_type.startswith(DataType.Data2D):
        # Add 0 to make positions always [x, 0, z]
        vert_positions = np.hstack((data[:, :1], np.zeros((data.shape[0], 1)), data[:, 1:]))[:,:3]
        if data_type == DataType.Data2DW:
            # Create [x, 0, z] positions assign w attribute
            ws = data[:, 2]
        elif data_type == DataType.Data2DA:
            # Create [x, 0, z] and [x, 0, z_n] shape keys
            z_ns = data[:, 2:]
    elif data_type.startswith(DataType.Data3D):
        # Trim to 3 dims
        vert_positions = data[:, :3]
        if data_type == DataType.Data3DW:
            ws = data[:, 3]
        elif data_type == DataType.Data3DA:
            z_ns = data[:, 3:]
    else:
        raise RuntimeError(f'Unknown DataType {data_type}')
    
    edges = []
    if connect_edges:
        edges = [(i, i + 1) for i in range(len(vert_positions) - 1)]
    
    mesh.from_pydata(vertices=vert_positions, edges=edges, faces=[])
    if ws is not None:
        attr = mesh.attributes.new(W_ATTRIBUTE_NAME, 'FLOAT', 'POINT')
        attr.data.foreach_set('value', ws)


    obj = bpy.data.objects.new(name, mesh)
    obj.location = (0, 0, 0)
    obj.scale = (1, 1, 1)

    if z_ns is not None:
        # Create shape keys
        obj.shape_key_add(name='Basis')
        for i, z_col in enumerate(z_ns.transpose()):
            sk = obj.shape_key_add(name=f'Column: {i}')
            sk.value = 0
            for j, z in enumerate(z_col):
                sk.data[j].co.z = z
    
        obj.data.shape_keys.name = "DV_Animation"
    _mark_chart_data_type(obj, data_type)
    return obj


def is_data_suitable(acceptable: typing.Set[str]):
    chart_data = DataManager().get_chart_data()
    if chart_data is None:
        return False
    
    types = get_data_types()
    return len(acceptable & types) > 0
    
