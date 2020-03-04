
from src.general import Properties
from src.utils.data_utils import float_range

from enum import Enum
from mathutils import Vector
import bpy
import math


class AxisDir(Enum):
    X = 0
    Y = 1
    Z = 2


class Axis:
    '''
    Abstraction for axis creation and its labeling
    parent - parent object for axis container
    step - space between axis ticks
    range - tuple/list of from..to values
    dir - direction of axis specified by AxisDir class
    hm - height multiplier to normalize chart height
    '''
    def __init__(self, parent, step, ax_range, ax_dir):
        self.step = step
        self.range = ax_range
        self.parent_object = parent
        self.thickness = Properties.get_axis_thickness()
        self.mark_height = Properties.get_axis_tick_mark_height()
        self.text_size = Properties.get_text_size()
        if isinstance(ax_dir, AxisDir):
            self.dir = ax_dir
        else:
            raise AttributeError('Use AxisDir enumeration as ax_range param')

        self.axis_cont = None

    def create_container(self):
        '''
        Creates container for axis, with default name 'Axis_Container_DIM' where DIM is X, Y or Z
        '''
        bpy.ops.object.empty_add()
        self.axis_cont = bpy.context.object
        self.axis_cont.name = 'Axis_Container_' + str(self.dir)
        self.axis_cont.location = (0, 0, 0)
        self.axis_cont.parent = self.parent_object

    def create_axis_line(self, length):
        '''
        Creates rectangular line of size Properties.axis_thickness and of length specified by parameter
        The line is created in x direction
        returns - line obj
        '''
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.parent = self.axis_cont
        obj.location = (0, 0, 0)
        
        obj.scale = (length, self.thickness, self.thickness)
        obj.location.x += length
        return obj

    def create_tick_mark(self, x_location):
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.scale = (self.thickness, self.thickness, self.mark_height)
        obj.location = (0, 0, 0)
        obj.location.x += x_location
        obj.parent = self.axis_cont

    def create_ticks(self, start_pos):
        for value in float_range(self.range[0], self.range[1], self.step):
            tick_location = start_pos + (value - self.range[0]) / (self.range[1] - self.range[0])
            self.create_tick_mark(tick_location)
            self.create_tick_label(value, tick_location)

    def create(self, padding, offset):
        '''
        Creates axis in range for dir dimension with spacing as set by ctor
        padding - how far should the axis start from the chart object (space around chart)
        offset -  how the value should be offset to its position (e. g. bar_chart in middle of bar)
        '''
        self.create_container()
        # create line with text by spacing in ax_range
        line_len = 1.0 + padding + offset
        axis_line = self.create_axis_line(line_len * 0.5)
        self.create_ticks(offset)

        #think about - padding to bottom, padding left and right, so axis match on ends, so it looks visualy pleasing...
        if self.dir == AxisDir.X:
            self.axis_cont.location.y -= padding
            axis_line.location.x -= padding
            self.axis_cont.location.z -= padding
            # increase the length of axis in y direction to match the start
        elif self.dir == AxisDir.Y:
            axis_line.location.x -= padding
            self.axis_cont.rotation_euler = (0, 0, math.pi * 0.5)
            self.axis_cont.location.x -= padding
            self.axis_cont.location.z -= padding
        elif self.dir == AxisDir.Z:
            axis_line.location.x -= padding
            self.axis_cont.rotation_euler = (0, -math.pi * 0.5, 0)
            self.axis_cont.location.x -= padding
            self.axis_cont.location.y -= padding

    def create_tick_label(self, value, x_location):
        bpy.ops.object.text_add()
        obj = bpy.context.object
        obj.data.body = '%.2f' % value
        obj.data.align_x = 'CENTER'
        obj.scale *= self.text_size
        obj.parent = self.axis_cont
        if self.dir == AxisDir.Z:
            obj.rotation_euler.y = math.radians(90)
            obj.location = (x_location, 0, 0.2)
        else:
            obj.location = (x_location, 0, -0.2)

        if self.dir == AxisDir.Y:
            obj.rotation_euler.z = math.radians(180)

        obj.rotation_euler.x = math.radians(90)


