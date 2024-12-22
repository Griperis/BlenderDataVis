# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import json
import numpy as np
import dataclasses
from ..data_manager import DataManager, DataType
import logging

logger = logging.getLogger("data_vis")

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

    @staticmethod
    def is_categorical(data: str) -> bool:
        return data.startswith("Cat_")

    @staticmethod
    def is_3d(data: str) -> bool:
        return "3D" in data

    @staticmethod
    def is_2d(data: str) -> bool:
        return "2D" in data


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

    # Map of "DATA TYPE": (string name, description)
    DATA_TYPE_ENUM_MAPS = {
        DataTypeValue.Data2D: ("2D", "Simple 2D data"),
        DataTypeValue.Data2DW: (
            "2D + Weights",
            "2D data with weights that can manipulate certain chart properties",
        ),
        DataTypeValue.Data2DA: (
            "2D + Animated",
            "2D data with animated Z using shape keys",
        ),
        DataTypeValue.Data3D: ("3D", "Simple 3D data"),
        DataTypeValue.Data3DW: (
            "3D + Weights",
            "3D data with weights that can manipulate certain chart properties",
        ),
        DataTypeValue.Data3DA: (
            "3D + Animated",
            "3D data with animated Z using shape keys",
        ),
        DataTypeValue.CATEGORIC_Data2D: ("Categoric 2D", "Simple Categoric 2D data"),
    }

    def set_current_types(self, current_types: set[str]) -> None:
        type(self).current_types = current_types

    def _get_data_types_enum(self, context: bpy.types.Context):
        types = get_data_types() & type(self).current_types
        return [
            (
                t,
                DV_DataProperties.DATA_TYPE_ENUM_MAPS[t][0],
                DV_DataProperties.DATA_TYPE_ENUM_MAPS[t][1],
            )
            for t in types
        ]


@dataclasses.dataclass
class PreprocessedData:
    vert_positions: np.ndarray
    ws: np.ndarray | None = None
    z_ns: np.ndarray | None = None
    categories: np.ndarray | None = None


def _store_chart_data_info(
    obj: bpy.types.Object, verts: np.ndarray, data: PreprocessedData, data_type: str
) -> None:
    data_dict = {
        "data_type": data_type,
        "shape": verts.shape,
    }
    if data is not None and data.categories is not None:
        data_dict["categories"] = data.categories.tolist()

    obj[DATA_TYPE_PROPERTY] = json.dumps(data_dict)


def get_chart_data_info(obj: bpy.types.Object) -> typing.Dict[str, typing.Any]:
    try:
        return json.loads(obj.get(DATA_TYPE_PROPERTY, "{}"))
    except Exception:
        logger.exception(f"Failed to parse stored data on {obj.name}")
        return None


def get_chart_data_type(obj: bpy.types.Object) -> str:
    chart_data_info = get_chart_data_info(obj)
    if chart_data_info is None:
        return "None"
    return chart_data_info.get("data_type", "None")


def _preprocess_data(data, data_type: str) -> PreprocessedData:
    vert_positions = None
    ws = None
    z_ns = None
    categories = None
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
    elif data_type == DataTypeValue.CATEGORIC_Data2D:
        # Equidistant spacing along x axis, y axis has values
        vert_positions = np.hstack(
            (
                np.linspace(0, data.shape[0] - 1, data.shape[0]).reshape(
                    data.shape[0], 1
                ),
                np.zeros((data.shape[0], 1)),
                data[:, 1:],
            )
        ).astype("float")
        categories = data[:, 0]
    else:
        raise RuntimeError(f"Unknown DataType {data_type}")

    return PreprocessedData(vert_positions, ws, z_ns, categories)


@dataclasses.dataclass
class InterpolationConfig:
    method: str
    m: int
    n: int


def _convert_data_to_geometry(
    data_type: str,
    connect_edges: bool = False,
    interpolation_config: InterpolationConfig | None = None,
) -> tuple[list, list, list, PreprocessedData]:
    data = _preprocess_data(DataManager().get_chart_data().parsed_data, data_type)
    verts = []
    edges = []
    faces = []
    # 1D array of categories in order of their values
    if interpolation_config is not None:
        try:
            from scipy import interpolate
            import numpy as np
        except ImportError:
            raise RuntimeError("SciPy is required for this operation")
        x = np.linspace(
            data.vert_positions[:, 0].min(),
            data.vert_positions[:, 0].max(),
            interpolation_config.m,
        )
        y = np.linspace(
            data.vert_positions[:, 1].min(),
            data.vert_positions[:, 1].max(),
            interpolation_config.n,
        )
        X, Y = np.meshgrid(x, y)

        res = interpolate.Rbf(
            data.vert_positions[:, 0],
            data.vert_positions[:, 1],
            data.vert_positions[:, 2],
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

        return verts, edges, faces, data
    else:
        if connect_edges:
            edges = [(i, i + 1) for i in range(len(data.vert_positions) - 1)]

        return data.vert_positions, edges, faces, data


def create_data_object(
    name: str,
    data_type: str,
    connect_edges: bool = False,
    interpolation_config: InterpolationConfig | None = None,
) -> bpy.types.Object:
    verts, edges, faces, data = _convert_data_to_geometry(
        data_type, connect_edges, interpolation_config
    )
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices=verts, edges=edges, faces=faces)
    if data.ws is not None:
        attr = mesh.attributes.new(W_ATTRIBUTE_NAME, "FLOAT", "POINT")
        attr.data.foreach_set("value", data.ws)

    obj = bpy.data.objects.new(name, mesh)
    obj.location = (0, 0, 0)
    obj.scale = (1, 1, 1)

    if data.z_ns is not None:
        # Create shape keys
        obj.shape_key_add(name="Basis")
        for i, z_col in enumerate(data.z_ns.transpose()):
            sk = obj.shape_key_add(name=f"Column: {i}")
            sk.value = 0
            for j, z in enumerate(z_col):
                sk.data[j].co.z = z

        obj.data.shape_keys.name = "DV_Animation"

    _store_chart_data_info(obj, verts, data, data_type)
    return obj


def is_data_suitable(acceptable: typing.Set[str]):
    chart_data = DataManager().get_chart_data()
    if chart_data is None:
        return False

    types = get_data_types()
    return len(acceptable & types) > 0
