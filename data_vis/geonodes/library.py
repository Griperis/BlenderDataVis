import bpy
import os


GEONODES_BLENDS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../blends/chart_geonodes.blend"))


def _load_nodegroup(name: str) -> bpy.types.NodeGroup:
    if not os.path.isfile(GEONODES_BLENDS_PATH):
        raise FileNotFoundError(f"Geometry nodes library couldn't be found at {GEONODES_BLENDS_PATH}")
    with bpy.data.libraries.load(GEONODES_BLENDS_PATH, link=False) as (data_from, data_to):
        assert name in data_from.node_groups
        data_to.node_groups = [name]

    return data_to.node_groups[0]


def load_chart(name: str):
    return _load_nodegroup(name)


def load_axis() -> bpy.types.NodeGroup:
    return _load_nodegroup("DV_NumericAxis")


def load_above_data_labels() -> bpy.types.NodeGroup:
    return _load_nodegroup("DV_DataLabels")