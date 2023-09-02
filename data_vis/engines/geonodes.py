# File: docs.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0

import bpy
from data_vis.engines.engine import ChartEngine


class GeonodesChartEngine(ChartEngine):
    def data_as_mesh(self):
        mesh = bpy.data.meshes.new('Mesh')
        mesh.from_pydata(vertices=self.data.as_vertices(), edges=[], faces=[])
        return mesh
    
    def bar_chart(self):
        pass

    def bubble_chart(self):
        pass
    
    def line_chart(self):
        pass
    
    def pie_chart(self):
        pass
    
    def point_chart(self):
        pass
    
    def surface_chart(self):
        pass
    
    def _load_chart_geonodes(self, chart_name: str):
        ...
    
    def _get_geonodes_chart_library_path(self):
        return ""