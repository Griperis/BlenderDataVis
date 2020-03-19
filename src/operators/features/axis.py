
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


class AxisFactory:
    @staticmethod
    def create(parent, axis_steps, axis_ranges, dim, labels=[], tick_labels=([], [], []), padding=0.0, offset=0.0):
        '''
        Factory method that creates all axis with all values specified by parameters
        parent - parent object for axis containers
        axis_steps - list of axis step sizes (x_step_size, y_step_size, z_step_size)
        axis_ranges - list of axis ranges ((x_min, x_max), (...), (...))
        dim - number of dimensions (2 or 3) in which to create axis
        labels - array of labels for each axis [x, y, z]
        '''
        if dim not in [2, 3]:
            raise AttributeError('Only 2 or 3 dim axis supported. {} is invalid number'.format(dim))
        
        for i in range(dim):
            if i == 0:
                direction = AxisDir.X
            elif i == 1:
                # y axis in 2D chart is z in blender 3D space
                if dim == 2:
                    direction = AxisDir.Z
                else:
                    direction = AxisDir.Y
            elif i == 2:
                direction = AxisDir.Z

            # create Y axis in 2D in Z direction using Z values
            dir_idx = i
            if dim == 2 and i == 1:
                dir_idx = 2
                axis = Axis(parent, axis_steps[dir_idx], axis_ranges[dir_idx], direction, tick_labels[dir_idx])
            else:
                axis = Axis(parent, axis_steps[dir_idx], axis_ranges[dir_idx], direction, tick_labels[dir_idx])
            axis.create(padding, offset, labels[dir_idx], True if dim == 2 else False)


class Axis:
    '''
    Abstraction for axis creation and its labeling
    parent - parent object for axis container
    step - space between axis ticks
    range - tuple/list of from..to values
    dir - direction of axis specified by AxisDir class
    hm - height multiplier to normalize chart height
    '''
    def __init__(self, parent, step, ax_range, ax_dir, labels):
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
        self.labels = labels

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
        '''
        Creates tick mark at x_location of self.thickness size and height of self.mark_height and
        ads it to axis container
        x_location - location of mark along x axis
        '''
        bpy.ops.mesh.primitive_cube_add()
        obj = bpy.context.active_object
        obj.scale = (self.thickness, self.thickness, self.mark_height)
        obj.location = (0, 0, 0)
        obj.location.x += x_location - self.thickness * 0.5
        obj.parent = self.axis_cont

    def create_ticks(self, start_pos):
        '''
        Creates tick marks from self.range with stepsize of self.step
        start_pos - starting position for all ticks (so it can start with offset)
        '''
        for value in float_range(self.range[0], self.range[1], self.step):
            tick_location = start_pos + (value - self.range[0]) / (self.range[1] - self.range[0])
            self.create_tick_mark(tick_location)
            if len(self.labels) == 0:
                self.create_tick_label(value, tick_location)
            else:
                self.create_tick_label(self.labels[int(value)], tick_location, rotate=True)

    def create(self, padding, offset, label, only_2d=False):
        '''
        Creates axis in range for dir dimension with spacing as set by ctor
        padding - how far should the axis start from the chart object (space around chart)
        offset - how the value should be offset to its position (e. g. bar_chart in middle of bar)
        only_2d - ignore y padding
        '''
        self.create_container()
        # create line with text by spacing in ax_range
        line_len = 1.0 + padding + offset
        axis_line = self.create_axis_line(line_len * 0.5)
        self.create_ticks(offset)
        if label is not None:
            self.create_label(label)

        if self.dir == AxisDir.X:
            if not only_2d:
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
            if not only_2d:
                self.axis_cont.location.y -= padding

    def create_label(self, value):
        obj = self.create_text_object(value)
        obj.parent = self.axis_cont
        obj.location = (1.3, 0, 0)
        self.rotate_text_object(obj)

    def create_tick_label(self, value, x_location, rotate=False):
        obj = self.create_text_object(value)
        if rotate:
            obj.rotation_euler.y = math.radians(45)
        obj.parent = self.axis_cont
        self.rotate_text_object(obj)
        if self.dir == AxisDir.Z:
            obj.location = (x_location, 0, 0.2)
        else:
            obj.location = (x_location, 0, -0.2)

    def create_text_object(self, value):
        bpy.ops.object.text_add()
        obj = bpy.context.object
        if type(value) is float:
            obj.data.body = '%.2f' % value
        else:
            obj.data.body = str(value)
        obj.data.align_x = 'CENTER'
        obj.scale *= self.text_size
        return obj

    def rotate_text_object(self, obj):
        if self.dir == AxisDir.Z:
            obj.rotation_euler.y = math.radians(90)
    
        if self.dir == AxisDir.Y:
            obj.rotation_euler.z = math.radians(180)

        obj.rotation_euler.x = math.radians(90)

