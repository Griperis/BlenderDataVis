# File: general.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Generic Chart - base class implementation, UI drawing

import bpy
import math

from mathutils import Vector
from data_vis.data_manager import DataManager, DataType
from data_vis.utils.data_utils import find_axis_range
from data_vis.colors import ColorType
from data_vis.properties import DV_AnimationPropertyGroup, DV_AxisPropertyGroup, DV_ColorPropertyGroup, DV_HeaderPropertyGroup, DV_LabelPropertyGroup, DV_LegendPropertyGroup


class OBJECT_OT_GenericChart(bpy.types.Operator):
    '''
    Encapsulation of common methods for charts, when creating new chart operator inherit this
    Naming property pointers to property groups from properties.py correctly can handle UI drawing e. g. in bar_chart.py
    '''
    bl_idname = 'object.create_chart'
    bl_label = 'Generic chart operator'
    bl_options = {'REGISTER', 'UNDO'}

    data = None
    axis_mat = None
    chart_id = 0

    def __init__(self):
        self.container_object = None
        self.labels = []
        self.dm = DataManager()
        self.prev_anim_setting = False
        if hasattr(self, 'dimensions'):
            self.dimensions = str(self.dm.dimensions)

        if hasattr(self, 'data_type'):
            self.data_type = '0' if self.dm.predicted_data_type == DataType.Numerical else '1'

        self.chart_id = OBJECT_OT_GenericChart.chart_id
        OBJECT_OT_GenericChart.chart_id += 1

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(icon='WORLD_DATA', text='Chart settings:')
        if self.dm.predicted_data_type != DataType.Categorical and hasattr(self, 'data_type'):
            row = box.row()
            row.prop(self, 'data_type')

        only_2d = hasattr(self, 'dimensions')
        numerical = True
        if hasattr(self, 'data_type'):
            if self.data_type == '1':
                numerical = False

        only_2d = only_2d or not numerical

        if hasattr(self, 'dimensions') and self.dm.predicted_data_type != DataType.Categorical:
            if numerical:
                row = box.row()
                row.prop(self, 'dimensions')
            else:
                self.dimensions = '2'
        
        self.draw_header_settings(layout)
        self.draw_axis_settings(layout, numerical)
        self.draw_legend_settings(layout)
        self.draw_color_settings(layout)
        self.draw_anim_settings(layout)

    def draw_header_settings(self, layout):
        if hasattr(self, 'header_settings'):

            box = layout.box()
            box.label(text='Header:', icon='BOLD')
            row = box.row()
            row.prop(self.header_settings, 'create')
            if self.header_settings.create:
                row = box.row()
                if self.header_settings.text == 'None':
                    self.header_settings.text = self.bl_label
                row.prop(self.header_settings, 'text')
                row.prop(self.header_settings, 'size')
    
    def draw_legend_settings(self, layout):
        if hasattr(self, 'legend_settings'):
            box = layout.box()
            row = box.row()
            row.label(icon='WORDWRAP_ON', text='Legend:')
            row.prop(self.legend_settings, 'create')
            if self.legend_settings.create:
                box.prop(self.legend_settings, 'position')
                box.prop(self.legend_settings, 'item_size')

    def draw_anim_settings(self, layout):
        if not self.dm.animable:
            return
        if hasattr(self, 'anim_settings'):
            box = layout.box()
            box.label(icon='TIME', text='Animation:')
            box.prop(self.anim_settings, 'animate')
            if self.anim_settings.animate:
                box.prop(self.anim_settings, 'key_spacing')
            if self.anim_settings.animate != self.prev_anim_setting:
                self.use_anim_range(self.anim_settings.animate)
                self.prev_anim_setting = self.anim_settings.animate

    def draw_label_settings(self, box):
        if hasattr(self, 'label_settings'):
            row = box.row()
            row.label(icon='FILE_FONT', text='Labels:')
            row.prop(self.label_settings, 'create')
            if self.label_settings.create:
                if self.dm.has_labels:
                    box.prop(self.label_settings, 'from_data')
                if not self.label_settings.from_data or not self.dm.has_labels:
                    row = box.row()
                    row.prop(self.label_settings, 'x_label')
                    if self.dm.dimensions == 3:
                        row.prop(self.label_settings, 'y_label')
                    row.prop(self.label_settings, 'z_label')

    def draw_color_settings(self, layout):
        if hasattr(self, 'color_settings'):
            box = layout.box()
            box.label(icon='COLOR', text='Colors:')
            box.prop(self.color_settings, 'use_shader')
            box.prop(self.color_settings, 'color_type')
            if not ColorType.str_to_type(self.color_settings.color_type) == ColorType.Random:
                box.prop(self.color_settings, 'color_shade')
 
    def draw_axis_settings(self, layout, numerical):
        if not hasattr(self, 'axis_settings'):
            return

        box = layout.box()
        box.label(icon='ORIENTATION_VIEW', text='Axis:')

        row = box.row()
        row.label(text='Ranges:', icon='ARROW_LEFTRIGHT')
        row = box.row()
        if self.dm.predicted_data_type != DataType.Categorical:
            row.prop(self.axis_settings, 'x_range', text='X')
        if hasattr(self, 'dimensions') and self.dimensions == '3':
            row = box.row()
            row.prop(self.axis_settings, 'y_range', text='Y')
        row = box.row()
        row.prop(self.axis_settings, 'z_range', text='Z')
        box.prop(self.axis_settings, 'auto_steps')

        if not self.axis_settings.auto_steps:
            row = box.row()
            if numerical:
                row.prop(self.axis_settings, 'x_step')
            if hasattr(self, 'dimensions') and self.dimensions == '3':
                row.prop(self.axis_settings, 'y_step', text='Y')
            row.prop(self.axis_settings, 'z_step', text='Z')

        row = box.row()
        row.prop(self.axis_settings, 'create')
        if not self.axis_settings.create:
            return
        row = box.row()
        row.prop(self.axis_settings, 'z_position')
        row = box.row()
        row.prop(self.axis_settings, 'padding')
        row.prop(self.axis_settings, 'thickness')
        row.prop(self.axis_settings, 'tick_mark_height')
        box.separator()
        row = box.row()
        row.label(text='Ticks:', icon='FONT_DATA')
        box.prop(self.axis_settings, 'number_format')
        row = box.row()
        row.prop(self.axis_settings, 'text_size')
        row.prop(self.axis_settings, 'decimal_places')
        box.separator()
        self.draw_label_settings(box)

    @classmethod
    def poll(cls, context):
        '''Default behavior for every chart poll method (when data is not available, cannot create chart)'''
        return self.dm.parsed_data is not None

    def execute(self, context):
        raise NotImplementedError('Execute method should be implemented in every chart operator!')

    def invoke(self, context, event):
        '''When user clicks on operator button, invoke is called, if subclass has axis_settings defined, ranges are initialized, if init_props is defined it is called'''
        if hasattr(self, 'axis_settings'):
            self.init_ranges()
        
        if hasattr(self, 'init_props'):
            self.init_props()

        return context.window_manager.invoke_props_dialog(self)

    def init_ranges(self):
        self.axis_settings.x_range = self.dm.get_range('x')
        self.axis_settings.y_range = self.dm.get_range('y')
        self.axis_settings.z_range = self.dm.get_range('z')
        if hasattr(self, 'anim_settings') and self.anim_settings.animate:
            self.axis_settings.z_range = self.dm.get_range('z_anim')

    def use_anim_range(self, is_anim):
        if is_anim:
            self.axis_settings.z_range = self.dm.get_range('z_anim')
        else:
            self.axis_settings.z_range = self.dm.get_range('z')

    def create_container(self):
        bpy.ops.object.empty_add()
        self.container_object = bpy.context.object
        self.container_object.empty_display_type = 'PLAIN_AXES'
        self.container_object.name = self.bl_label + '_' + str(self.chart_id)
        self.container_object.location = bpy.context.scene.cursor.location

    def data_type_as_enum(self):
        if not hasattr(self, 'data_type'):
            return DataType.Numerical

        if self.data_type == '0':
            return DataType.Numerical
        elif self.data_type == '1':
            return DataType.Categorical

    def new_mat(self, color, alpha, name='Mat'):
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = (*color, alpha)
        return mat

    def init_data(self):
        if hasattr(self, 'label_settings'):
            self.init_labels()

        if hasattr(self, 'anim_settings') and self.prev_anim_setting != self.anim_settings.animate:
            self.use_anim_range(self.anim_settings.animate)
        self.data = self.dm.get_parsed_data()

    def init_labels(self):
        if not self.label_settings.create:
            self.labels = (None, None, None)
            return
        if self.dm.has_labels and self.label_settings.from_data:
            first_line = self.dm.get_labels()
            length = len(first_line)
            if length == 2:
                self.labels = (first_line[0], '', first_line[1])
            elif length == 3:
                self.labels = (first_line[0], first_line[1], first_line[2])
            else:
                self.report({'ERROR'}, 'Unsupported number of labels on first line')
        else:
            self.labels = [self.label_settings.x_label, self.label_settings.y_label, self.label_settings.z_label]

    def init_range(self, data):
        self.axis_settings.x_range = find_axis_range(data, 0)
        self.axis_settings.y_range = find_axis_range(data, 1)

    def in_axis_range_bounds_new(self, entry):
        '''
        Checks whether the entry point defined as [x, y, z] is within user selected axis range
        returns False if not in range, else True
        '''
        entry_dims = len(entry)
        if entry_dims == 2 or entry_dims >= 3:
            if hasattr(self, 'data_type') and self.data_type_as_enum() != DataType.Numerical:
                return True

            if entry[0] < self.axis_settings.x_range[0] or entry[0] > self.axis_settings.x_range[1]:
                return False

        if entry_dims >= 3:
            if entry[1] < self.axis_settings.y_range[0] or entry[1] > self.axis_settings.y_range[1]:
                return False

        return True

    def select_container(self):
        '''Makes container object active and selects it'''
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = self.container_object
        self.container_object.select_set(True)

    def create_header(self, offset=(0.5, 0, 1.2), rotate=True):
        '''Creates header at container + offset'''
        bpy.ops.object.text_add()
        obj = bpy.context.object
        obj.data.align_x = 'CENTER'
        obj.data.body = self.header_settings.text
        obj.location = Vector(offset)
        obj.scale *= self.header_settings.size
        header_mat = bpy.data.materials.new(name='DV_HeaderMat_' + str(self.chart_id))
        obj.data.materials.append(header_mat)
        obj.active_material = header_mat
        if rotate:
            obj.rotation_euler.x = math.radians(90)
        obj.parent = self.container_object

    def get_name(self):
        '''Returns chart container name'''
        return self.container_object.name
