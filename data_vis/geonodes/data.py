# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import numpy as np
import dataclasses
from ..data_manager import DataManager, DataType


W_ATTRIBUTE_NAME = "@w"
DATA_TYPE_PROPERTY = "DV_DataType"


class DataTypeValue:
    """
    Individual values for data types that can be then compared and
    it can be easily detected what charts are suitable for given data.
    """

    Data2D = "2D"
    Data2DW = "2D+W"
    Data2DA = "2D+A"
    Data3D = "3D"
    Data3DW = "3D+W"
    Data3DA = "3D+A"
    CATEGORIC_Data2D = "Cat_2D"

    @staticmethod
    def is_animated(data: str) -> bool:
        return data.endswith("+A")


def get_data_types() -> typing.Set[str]:
    types = set()
    dm = DataManager()
    shape = dm.get_chart_data().parsed_data.shape
    if dm.predicted_data_type == DataType.Numerical:
        if shape[0] > 1:
            types.update({DataTypeValue.Data2D})
        if shape[0] > 2:
            types.update(
                {DataTypeValue.Data2DA, DataTypeValue.Data2DW, DataTypeValue.Data3D}
            )
        if shape[0] > 3:
            types.update({DataTypeValue.Data3DW, DataTypeValue.Data3DA})
    elif dm.predicted_data_type == DataType.Categorical:
        types.update({DataTypeValue.CATEGORIC_Data2D})

    return types


class DV_DataProperties(bpy.types.PropertyGroup):
    current_types: set[str] = set()
    data_type: bpy.props.EnumProperty(
        name="Selected Data Type",
        description="How to visualise given data",
        items=lambda self, context: self._get_data_types_enum(context),
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


def _preprocess_data(data, data_type: str):
    vert_positions = None
    ws = None
    z_ns = None
    if data_type.startswith(DataTypeValue.Data2D):
        # Add 0 to make positions always [x, 0, z]
        vert_positions = np.hstack(
            (data[:, :1], np.zeros((data.shape[0], 1)), data[:, 1:])
        )[:, :3]
        if data_type == DataTypeValue.Data2DW:
            # Create [x, 0, z] positions assign w attribute
            ws = data[:, 2]
        elif data_type == DataTypeValue.Data2DA:
            # Create [x, 0, z] and [x, 0, z_n] shape keys
            z_ns = data[:, 2:]
    elif data_type.startswith(DataTypeValue.Data3D):
        # Trim to 3 dims
        vert_positions = data[:, :3]
        if data_type == DataTypeValue.Data3DW:
            ws = data[:, 3]
        elif data_type == DataTypeValue.Data3DA:
            z_ns = data[:, 3:]
    else:
        raise RuntimeError(f"Unknown DataType {data_type}")

    return vert_positions, ws, z_ns


@dataclasses.dataclass
class InterpolationConfig:
    method: str
    m: int
    n: int


def _convert_data_to_geometry(
    data_type: str,
    connect_edges: bool = False,
    interpolation_config: InterpolationConfig | None = None,
):
    vert_positions, ws, z_ns = _preprocess_data(
        DataManager().get_chart_data().parsed_data, data_type
    )
    verts = []
    edges = []
    faces = []
    if interpolation_config is not None:
        try:
            from scipy import interpolate
            import numpy as np
        except ImportError:
            raise RuntimeError("SciPy is required for this operation")
        x = np.linspace(
            vert_positions[:, 0].min(),
            vert_positions[:, 0].max(),
            interpolation_config.m,
        )
        y = np.linspace(
            vert_positions[:, 1].min(),
            vert_positions[:, 1].max(),
            interpolation_config.n,
        )
        X, Y = np.meshgrid(x, y)

        res = interpolate.Rbf(
            vert_positions[:, 0],
            vert_positions[:, 1],
            vert_positions[:, 2],
            function=interpolation_config.method,
        )(X, Y)

        for row in range(interpolation_config.m):
            for col in range(interpolation_config.n):
                verts.append(
                    (
                        col / interpolation_config.m,
                        row / interpolation_config.n,
                        res[col][row],
                    )
                )
                if (
                    row < interpolation_config.m - 1
                    and col < interpolation_config.n - 1
                ):
                    faces.append(
                        (
                            col * interpolation_config.m + row,
                            (col + 1) * interpolation_config.m + row,
                            (col + 1) * interpolation_config.m + 1 + row,
                            col * interpolation_config.m + 1 + row,
                        )
                    )

        return verts, edges, faces, ws, z_ns
    else:
        if connect_edges:
            edges = [(i, i + 1) for i in range(len(vert_positions) - 1)]

        return vert_positions, edges, faces, ws, z_ns


def create_data_object(
    name: str,
    data_type: str,
    connect_edges: bool = False,
    interpolation_config: InterpolationConfig | None = None,
) -> bpy.types.Object:
    verts, edges, faces, ws, z_ns = _convert_data_to_geometry(
        data_type, connect_edges, interpolation_config
    )
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices=verts, edges=edges, faces=faces)
    if ws is not None:
        attr = mesh.attributes.new(W_ATTRIBUTE_NAME, "FLOAT", "POINT")
        attr.data.foreach_set("value", ws)

    obj = bpy.data.objects.new(name, mesh)
    obj.location = (0, 0, 0)
    obj.scale = (1, 1, 1)

    if z_ns is not None:
        # Create shape keys
        obj.shape_key_add(name="Basis")
        for i, z_col in enumerate(z_ns.transpose()):
            sk = obj.shape_key_add(name=f"Column: {i}")
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
