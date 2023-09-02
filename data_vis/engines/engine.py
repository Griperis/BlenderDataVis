# File: docs.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0

import abc
import dataclasses
from data_vis.data_manager import ChartData
from data_vis.properties import DV_AnimationPropertyGroup, DV_LabelPropertyGroup, DV_AxisPropertyGroup, DV_ColorPropertyGroup, DV_GeneralPropertyGroup, DV_HeaderPropertyGroup, DV_LegendPropertyGroup


@dataclasses.dataclass
class ChartParameters:
    axis: DV_AxisPropertyGroup
    labels:  DV_LabelPropertyGroup
    animation: DV_AnimationPropertyGroup
    header: DV_HeaderPropertyGroup
    colors: DV_ColorPropertyGroup


class ChartEngine(abc.ABC):
    def __init__(self, data: ChartData):
        self.data = data
        
    def set_parameters(self, parameters: ChartParameters):
        self.parameters = parameters
        
    @abc.abstractmethod
    def bar_chart(self):
        pass

    @abc.abstractmethod
    def bubble_chart(self):
        pass
    
    @abc.abstractmethod
    def line_chart(self):
        pass
    
    @abc.abstractmethod
    def pie_chart(self):
        pass
    
    @abc.abstractmethod
    def point_chart(self):
        pass
    
    @abc.abstractmethod
    def surface_chart(self):
        pass
