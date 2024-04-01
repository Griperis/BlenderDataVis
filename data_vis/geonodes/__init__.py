import bpy
from .charts import DV_GN_BarChart, DV_GN_PointChart, DV_GN_LineChart, DV_GN_SurfaceChart
from .data import DV_DataProperties
from .components import DV_AddNumericAxis, DV_AddHeading, DV_AddAxisLabel, DV_AddDataLabels, DV_AxisPanel, DV_DataLabelsPanel
from .animations import DV_AddInAnimation, DV_AddOutAnimation, DV_RemoveInOutAnimation, DV_AnimateData, DV_AnimatePanel 
from .modifier_utils import DV_RemoveModifier

CLASSES = [
    DV_DataProperties,
    DV_RemoveModifier,
    DV_GN_BarChart,
    DV_GN_PointChart,
    DV_GN_LineChart,
    DV_GN_SurfaceChart,
    DV_AddNumericAxis,
    DV_AddHeading,
    DV_AddAxisLabel,
    DV_AddDataLabels,
    DV_AxisPanel,
    DV_DataLabelsPanel,
    DV_AddInAnimation,
    DV_AddOutAnimation,
    DV_RemoveInOutAnimation,
    DV_AnimateData,
    DV_AnimatePanel
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)