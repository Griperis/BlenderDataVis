# ©copyright Zdenek Dolezal 2024-, License GPL

import bpy
import os


class MaterialType:
    GradientRandom = "DV_GradientRandom"
    Gradient = "DV_Gradient"
    Sign = "DV_Sign"
    Constant = "DV_Constant"
    HueRandom = "DV_HueRandom"

    @classmethod
    def as_enum_items(cls):
        return [
            (x, x.replace("DV_", ""), x)
            for x in [
                cls.Gradient,
                cls.GradientRandom,
                cls.HueRandom,
                cls.Constant,
                cls.Sign,
            ]
        ]


GEONODES_BLENDS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../blends/chart_geonodes.blend")
)


def _load_nodegroup(name: str, link: bool = True) -> bpy.types.NodeTree:
    if not os.path.isfile(GEONODES_BLENDS_PATH):
        raise FileNotFoundError(
            f"Geometry nodes library couldn't be found at {GEONODES_BLENDS_PATH}"
        )

    library: bpy.types.Library = bpy.data.libraries.get(
        os.path.basename(GEONODES_BLENDS_PATH)
    )
    if library is not None:
        library.reload()

        if (name, library.filepath) in bpy.data.node_groups:
            return bpy.data.node_groups[(name, library.filepath)]

    with bpy.data.libraries.load(GEONODES_BLENDS_PATH, link=link) as (
        data_from,
        data_to,
    ):
        assert name in data_from.node_groups
        data_to.node_groups = [name]

    return data_to.node_groups[0]


def load_material(name: str, link: bool = True) -> bpy.types.Material:
    if not os.path.isfile(GEONODES_BLENDS_PATH):
        raise FileNotFoundError(
            f"Geometry nodes library couldn't be found at {GEONODES_BLENDS_PATH}"
        )

    library: bpy.types.Library = bpy.data.libraries.get(
        os.path.basename(GEONODES_BLENDS_PATH)
    )
    if library is not None:
        library.reload()

        if (name, library.filepath) in bpy.data.materials:
            return bpy.data.materials[(name, library.filepath)]

    with bpy.data.libraries.load(GEONODES_BLENDS_PATH, link=link) as (
        data_from,
        data_to,
    ):
        assert name in data_from.materials, f"{name} not in {GEONODES_BLENDS_PATH}"
        data_to.materials = [name]

    return data_to.materials[0]


def load_data_nodegroup(link: bool = True) -> bpy.types.NodeTree:
    return _load_nodegroup("DV_Data", link)


def load_chart(name: str, link: bool = True) -> bpy.types.NodeTree:
    return _load_nodegroup(name, link)


def load_numeric_axis(link: bool = True) -> bpy.types.NodeTree:
    return _load_nodegroup("DV_NumericAxis", link)


def load_categorical_axis(link: bool = True) -> bpy.types.NodeTree:
    return _load_nodegroup("DV_CategoricalAxis", link)


def load_above_data_labels(link: bool = True) -> bpy.types.NodeTree:
    return _load_nodegroup("DV_DataLabels", link)


def load_data_animation(name: str, link: bool = True) -> bpy.types.NodeTree:
    return _load_nodegroup(f"DV_DataAnim_{name}", link)
