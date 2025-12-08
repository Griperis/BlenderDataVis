# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import typing
import json
import math
import numpy as np
import dataclasses
from ..data_manager import DataManager, DataType, ChartData
from ..utils import data_vis_logging
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
    CATEGORIC_Data2DA = "Cat_2D+A"

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
        if shape[1] > 1:
            types.update({DataTypeValue.Data2D})
        if shape[1] > 2:
            types.update(
                {DataTypeValue.Data2DA, DataTypeValue.Data2DW, DataTypeValue.Data3D}
            )
        if shape[1] > 3:
            types.update({DataTypeValue.Data3DW, DataTypeValue.Data3DA})
    elif dm.predicted_data_type == DataType.Categorical:
        if shape[1] > 1:
            types.update({DataTypeValue.CATEGORIC_Data2D})
        if shape[1] > 2:
            types.update({DataTypeValue.CATEGORIC_Data2DA})

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
        DataTypeValue.CATEGORIC_Data2DA: (
            "Categoric 2D + Animated",
            "Categoric 2D data with animated Z using shape keys",
        ),
    }

    def _get_data_types_enum(self, context: bpy.types.Context):
        types = get_data_types()
        return [
            (
                t,
                DV_DataProperties.DATA_TYPE_ENUM_MAPS[t][0],
                DV_DataProperties.DATA_TYPE_ENUM_MAPS[t][1],
            )
            for t in types
        ]


def get_current_data_types_enum(
    self, context: bpy.types.Context, current_types: set[str]
):
    types = get_data_types() & current_types
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
    axis_labels: typing.List[str] = dataclasses.field(default_factory=list)


def _store_chart_data_info(
    obj: bpy.types.Object,
    verts: np.ndarray,
    chart_data: ChartData,
    data: PreprocessedData,
    data_type: str,
    connect_edges: bool = False,
    interpolation_config: typing.Optional["InterpolationConfig"] = None,
) -> None:
    data_dict = {
        "data_type": data_type,
        "shape": verts.shape,
        "min": list(chart_data.min_),
        "max": list(chart_data.max_),
        "connect_edges": connect_edges,
    }
    if interpolation_config is not None:
        data_dict["interpolation"] = dataclasses.asdict(interpolation_config)
    if data is not None:
        if data.categories is not None:
            data_dict["categories"] = data.categories.tolist()
        if data.axis_labels is not None:
            data_dict["axis_labels"] = data.axis_labels

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
    elif DataTypeValue.is_categorical(data_type):
        # Equidistant spacing along x axis, y axis has values
        vert_positions = np.hstack(
            (
                np.linspace(0, data.shape[0] - 1, data.shape[0]).reshape(
                    data.shape[0], 1
                ),
                np.zeros((data.shape[0], 1)),
                data[:, 1:],
            )
        ).astype("float")[:, :3]
        categories = data[:, 0]
        if data_type == DataTypeValue.CATEGORIC_Data2DA:
            z_ns = data[:, 2:].astype("float")
    else:
        raise RuntimeError(f"Unknown DataType {data_type}")

    return PreprocessedData(vert_positions, ws, z_ns, categories, axis_labels=[])


@dataclasses.dataclass
class InterpolationConfig:
    method: str
    m: int
    n: int


def _convert_data_to_geometry(
    data_type: str,
    chart_data: ChartData,
    connect_edges: bool = False,
    interpolation_config: InterpolationConfig | None = None,
) -> tuple[list, list, list, PreprocessedData]:
    data = _preprocess_data(chart_data.parsed_data, data_type)
    data.axis_labels = chart_data.labels
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

        # Interpolate data points into a grid
        data_x = data.vert_positions[:, 0]
        data_y = data.vert_positions[:, 1]
        res = interpolate.Rbf(
            data_x,
            data_y,
            data.vert_positions[:, 2],
            function=interpolation_config.method,
        )(X, Y)

        if data.z_ns is not None:
            # Interpolate data points for animation into a grid
            data.z_ns = np.array(
                [
                    interpolate.Rbf(
                        data_x,
                        data_y,
                        z,
                        function=interpolation_config.method,
                    )(X, Y).reshape(-1)
                    for z in data.z_ns.T
                ]
            ).T

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

        return np.array(verts), edges, faces, data
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
    chart_data = DataManager().get_chart_data()
    verts, edges, faces, data = _convert_data_to_geometry(
        data_type, chart_data, connect_edges, interpolation_config
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

    _store_chart_data_info(
        obj, verts, chart_data, data, data_type, connect_edges, interpolation_config
    )
    return obj


@data_vis_logging.logged_operator
class DV_RegenerateData(bpy.types.Operator):
    bl_idname = "data_vis.regenerate_data"
    bl_label = "Regenerate Data"
    bl_description = (
        "Recomputes mesh data for the active chart using the currently loaded data"
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        if obj is None:
            return False
        if DataManager().get_chart_data() is None:
            return False
        from . import components

        return components.is_chart(obj)

    def execute(self, context: bpy.types.Context):
        obj: bpy.types.Object = context.active_object
        chart_data = DataManager().get_chart_data()
        if chart_data is None:
            self.report({"ERROR"}, "No data loaded. Load data to regenerate chart.")
            return {"CANCELLED"}

        chart_data_info = get_chart_data_info(obj)
        if not chart_data_info:
            self.report({"ERROR"}, "Chart has no stored data information.")
            return {"CANCELLED"}

        data_type = chart_data_info.get("data_type")
        if not data_type or data_type == "None":
            self.report({"ERROR"}, "Chart data type missing.")
            return {"CANCELLED"}

        if data_type not in get_data_types():
            self.report(
                {"ERROR"},
                f"Loaded data is not compatible with chart type '{data_type}'.",
            )
            return {"CANCELLED"}

        interpolation_cfg_dict = chart_data_info.get("interpolation")
        interpolation_cfg = None
        if interpolation_cfg_dict is not None:
            try:
                interpolation_cfg = InterpolationConfig(
                    method=interpolation_cfg_dict.get("method"),
                    m=int(interpolation_cfg_dict.get("m")),
                    n=int(interpolation_cfg_dict.get("n")),
                )
            except Exception:
                logger.exception("Failed to parse stored interpolation config")
                self.report({"ERROR"}, "Invalid interpolation config stored on chart.")
                return {"CANCELLED"}
        else:
            interpolation_cfg = self._infer_interpolation_config(obj)

        connect_edges = chart_data_info.get("connect_edges")
        if connect_edges is None:
            connect_edges = self._infer_connect_edges(obj)
        connect_edges = bool(connect_edges)

        try:
            verts, edges, faces, preprocessed_data = _convert_data_to_geometry(
                data_type,
                chart_data,
                connect_edges=connect_edges,
                interpolation_config=interpolation_cfg,
            )
        except Exception as exc:
            logger.exception("Failed to regenerate chart data")
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        old_mesh = obj.data
        old_mesh_name = old_mesh.name
        old_materials = [mat for mat in old_mesh.materials]
        new_mesh = bpy.data.meshes.new(old_mesh.name)
        new_mesh.from_pydata(vertices=verts, edges=edges, faces=faces)
        if preprocessed_data.ws is not None:
            attr = new_mesh.attributes.new(W_ATTRIBUTE_NAME, "FLOAT", "POINT")
            attr.data.foreach_set("value", preprocessed_data.ws)
        for mat in old_materials:
            if mat is not None:
                new_mesh.materials.append(mat)

        obj.data = new_mesh

        if preprocessed_data.z_ns is not None:
            obj.shape_key_add(name="Basis")
            for i, z_col in enumerate(preprocessed_data.z_ns.transpose()):
                sk = obj.shape_key_add(name=f"Column: {i}")
                sk.value = 0
                for j, z in enumerate(z_col):
                    sk.data[j].co.z = z

            obj.data.shape_keys.name = "DV_Animation"

        _store_chart_data_info(
            obj,
            verts,
            chart_data,
            preprocessed_data,
            data_type,
            connect_edges,
            interpolation_cfg,
        )

        if old_mesh != new_mesh and old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
            new_mesh.name = old_mesh_name

        return {"FINISHED"}

    def _infer_interpolation_config(
        self, obj: bpy.types.Object
    ) -> typing.Optional[InterpolationConfig]:
        verts_count = len(obj.data.vertices)
        faces_count = len(obj.data.polygons)
        if verts_count == 0 or faces_count == 0:
            return None

        limit = int(math.sqrt(verts_count)) + 2
        for m in range(2, limit):
            if verts_count % m != 0:
                continue
            n = verts_count // m
            if (m - 1) * (n - 1) == faces_count:
                return InterpolationConfig(method="multiquadric", m=m, n=n)

        return None

    def _infer_connect_edges(self, obj: bpy.types.Object) -> bool:
        from . import components

        for mod in obj.modifiers:
            if (
                mod.type == "NODES"
                and mod.node_group is not None
                and components.remove_duplicate_suffix(mod.node_group.name)
                == "DV_LineChart"
            ):
                return True
        return False


def is_data_suitable(acceptable: typing.Set[str]):
    chart_data = DataManager().get_chart_data()
    if chart_data is None:
        return False

    types = get_data_types()
    return len(acceptable & types) > 0
