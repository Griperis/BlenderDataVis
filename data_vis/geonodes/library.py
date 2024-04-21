import bpy
import os


class MaterialType:
    GradientRandom = "DV_GradientRandom"
    Gradient = "DV_Gradient"
    Sign = "DV_Sign"
    Constant = "DV_Constant"

    @classmethod
    def as_enum_items(cls):
        return [(x, x.replace("DV_", ""), x) for x in [cls.Gradient, cls.GradientRandom, cls.Constant, cls.Sign]]


GEONODES_BLENDS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../blends/chart_geonodes.blend"))


def _load_nodegroup(name: str, link: bool = True) -> bpy.types.NodeGroup:
    if not os.path.isfile(GEONODES_BLENDS_PATH):
        raise FileNotFoundError(f"Geometry nodes library couldn't be found at {GEONODES_BLENDS_PATH}")
    
    library: bpy.types.Library = bpy.data.libraries.get(os.path.basename(GEONODES_BLENDS_PATH))
    if library is not None:
        library.reload()

    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]

    with bpy.data.libraries.load(GEONODES_BLENDS_PATH, link=link) as (data_from, data_to):
        assert name in data_from.node_groups
        data_to.node_groups = [name]

    return data_to.node_groups[0]


def load_material(name: str, link: bool = True) -> bpy.types.Material:
    if not os.path.isfile(GEONODES_BLENDS_PATH):
        raise FileNotFoundError(f"Geometry nodes library couldn't be found at {GEONODES_BLENDS_PATH}")

    libary: bpy.types.Library = bpy.data.libraries.get(os.path.basename(GEONODES_BLENDS_PATH))
    if libary is not None:
        libary.reload()

    if name in bpy.data.materials:
        return bpy.data.materials[name]

    with bpy.data.libraries.load(GEONODES_BLENDS_PATH, link=link) as (data_from, data_to):
        assert name in data_from.materials
        data_to.materials = [name]

    return data_to.materials[0]


def load_chart(name: str, link: bool = True):
    return _load_nodegroup(name, link)


def load_axis(link: bool = True) -> bpy.types.NodeGroup:
    return _load_nodegroup("DV_NumericAxis", link)


def load_above_data_labels(link: bool = True) -> bpy.types.NodeGroup:
    return _load_nodegroup("DV_DataLabels", link)
