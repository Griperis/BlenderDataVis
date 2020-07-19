# File: axis.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Axis creation related classes and implementation


from enum import Enum
from mathutils import Vector
import bpy
import math

from data_vis.utils.data_utils import float_range


class AxisDir(Enum):
    X = 0
    Y = 1
    Z = 2


class AxisFactory:
    @staticmethod
    def create(parent, axis_settings, dim, chart_id, labels=(None, None, None), tick_labels=([], [], []), offset=0.0):
        '''
        Factory method that creates all axis with all values specified by parameters
        parent - parent object for axis containers
        axis_settings: DV_AxisPropertyGroup
        labels - tuple of labels for each axis (x, y, z)
        tick_labels - tuple of lists containing values to display next to ticks on axis
        '''
        if dim not in [2, 3]:
            raise AttributeError('Only 2 or 3 dim axis supported. {} is invalid number'.format(dim))
        
        steps = [axis_settings.x_step, axis_settings.y_step, axis_settings.z_step]
        ranges = [axis_settings.x_range, axis_settings.y_range, axis_settings.z_range]
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
            
            dir_idx = i
            if dim == 2 and i == 1:
                dir_idx = 2

            axis = Axis(
                parent,
                chart_id,
                steps[dir_idx],
                ranges[dir_idx],
                direction,
                tick_labels[dir_idx],
                axis_settings.thickness,
                axis_settings.tick_mark_height,
                axis_settings.auto_steps,
                axis_settings.text_size,
                axis_settings.number_format,
                axis_settings.decimal_places
            )
            axis.create(axis_settings.padding, offset, labels[dir_idx], axis_settings.z_position, dim == 2)


class Axis:
    '''
    Abstraction for axis creation and its labeling
    parent - parent object for axis container
    step - space between axis ticks
    range - tuple/list of from..to values
    dir - direction of axis specified by AxisDir class
    labels - custom labels for axis ticks
    tick-height - height of tick mark
    auto_step - creates 10 uniform steps across axis
    '''
    def __init__(self, parent, chart_id, step, ax_range, ax_dir, tick_labels, thickness, tick_height, auto_step=False, text_size=0.05, number_format='0', decimal_places=2):
        self.range = ax_range
        if not auto_step:
            self.step = step
        else:
            self.step = (self.range[1] - self.range[0]) / 10

        if len(tick_labels) > 0:
            if auto_step:
                if len(tick_labels) > 10:
                    self.step = (len(tick_labels) - 1) / 10
                else:
                    self.step = 1

        self.parent_object = parent
        self.thickness = thickness
        self.mark_height = tick_height
        self.text_size = text_size
        if isinstance(ax_dir, AxisDir):
            self.dir = ax_dir
        else:
            raise AttributeError('Use AxisDir enumeration as ax_range param')

        self.axis_cont = None
        self.tick_labels = tick_labels
        self.create_format_string(number_format, decimal_places)
        self.create_materials(chart_id)

        self.text_objs = []
        self.tick_objs = []
        self.axis_obj = None

    def create_format_string(self, number_format, decimal_places):
        '''Creates format string specified by axis options'''
        if number_format == '0':
            self.number_fmt = '{:.' + str(decimal_places) + 'f}'
        elif number_format == '1':
            self.number_fmt = '{:.' + str(decimal_places) + 'e}'
        else:
            raise AttributeError('Unknown number format')

    def create_materials(self, chart_id):
        '''Creates materials for axis, ticks and text'''
        self.axis_mat = bpy.data.materials.get('DV_AxisMat_' + str(chart_id))
        if self.axis_mat is None:
            self.axis_mat = bpy.data.materials.new(name='DV_AxisMat_' + str(chart_id))
    
        self.tick_mat = bpy.data.materials.get('DV_TickMat_' + str(chart_id))
        if self.tick_mat is None:
            self.tick_mat = bpy.data.materials.new(name='DV_TickMat_' + str(chart_id))

        self.text_mat = bpy.data.materials.get('DV_TextMat_' + str(chart_id))
        if self.text_mat is None:
            self.text_mat = bpy.data.materials.new(name='DV_TextMat_' + str(chart_id))

    def create_container(self):
        '''Creates container for axis, with default name 'Axis_Container_DIM' where DIM is X, Y or Z'''
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
        obj.data.materials.append(self.axis_mat)
        obj.active_material = self.axis_mat
        self.axis_obj = obj
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
        obj.data.materials.append(self.tick_mat)
        obj.active_material = self.tick_mat
        self.tick_objs.append(obj)

    def create_ticks(self, start_pos):
        '''
        Creates tick marks from self.range with stepsize of self.step
        start_pos - starting position for all ticks (so it can start with offset)
        '''
        for value in float_range(self.range[0], self.range[1], self.step):
            tick_location = start_pos + (value - self.range[0]) / (self.range[1] - self.range[0])
            self.create_tick_mark(tick_location)
            if len(self.tick_labels) == 0:
                self.create_tick_label(value, tick_location)
            else:
                self.create_tick_label(self.tick_labels[int(value)], tick_location, rotate=True)

    def create(self, padding, offset, label, position='FRONT', only_2d=False):
        '''
        Creates axis in range for dir dimension with spacing as set by ctor
        padding - how far should the axis start from the chart object (space around chart)
        offset - how the value should be offset to its position (e. g. bar_chart in middle of bar)
        only_2d - ignore y padding
        '''
        self.create_container()
        # create line with text by spacing in ax_range
        line_len = 1.0 + padding + offset
        if (self.dir == AxisDir.X and position == 'RIGHT') or (self.dir == AxisDir.Y and position == 'BACK'):
            # add padding for right
            line_len += padding

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

            if position == 'BACK':
                self.axis_cont.location.y += line_len + padding
            elif position == 'RIGHT':
                self.axis_cont.location.x += line_len + padding
                for to in self.text_objs:
                    to.location.z = -0.1

    def create_label(self, value):
        '''Creates axis label (description) with value'''
        obj = self.create_text_object(value)
        obj.parent = self.axis_cont
        obj.name = 'TextLabel_' + str(self.dir)
        obj.location = (1.2, 0, 0)
        self.rotate_text_object(obj)

    def create_tick_label(self, value, x_location, rotate=False):
        '''Creates tick label with value on x_location offset'''
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
            obj.data.body = self.number_fmt.format(value)
        else:
            obj.data.body = str(value)
        obj.data.align_x = 'CENTER'
        obj.scale *= self.text_size
        obj.data.materials.append(self.text_mat)
        obj.active_material = self.text_mat
        self.text_objs.append(obj)
        return obj

    def rotate_text_object(self, obj):
        '''Rotates text object 45 degrees to fit more text'''
        if self.dir == AxisDir.Z:
            obj.rotation_euler.y = math.radians(90)

        if self.dir == AxisDir.Y:
            obj.rotation_euler.z = math.radians(180)

        obj.rotation_euler.x = math.radians(90)

