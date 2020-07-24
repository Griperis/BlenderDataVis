# File: properties.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Common chart properties, example usage in one of chart implementations

import bpy
from data_vis.data_manager import DataManager


class DV_AxisPropertyGroup(bpy.types.PropertyGroup):
    '''Axis Settings, used with AxisFactory'''
    def range_updated(self, context):
        if self.x_range[0] == self.x_range[1]:
            self.x_range[1] += 1.0
        if self.y_range[0] == self.y_range[1]:
            self.y_range[1] += 1.0
        if self.z_range[0] == self.z_range[1]:
            self.z_range[1] += 1.0

    create: bpy.props.BoolProperty(
        name='Create Axis Object',
        default=True,
    )

    auto_steps: bpy.props.BoolProperty(
        name='Automatic Steps',
        default=True,
    )

    x_step: bpy.props.FloatProperty(
        name='Step of x axis',
        default=DataManager().get_step_size('x')
    )

    x_range: bpy.props.FloatVectorProperty(
        name='Range of x axis',
        size=2,
        update=range_updated,
        default=DataManager().get_range('x')
    )

    y_step: bpy.props.FloatProperty(
        name='Step of y axis',
        default=DataManager().get_step_size('y')
    )

    y_range: bpy.props.FloatVectorProperty(
        name='Range of y axis',
        size=2,
        update=range_updated,
        default=DataManager().get_range('y')
    )

    z_range: bpy.props.FloatVectorProperty(
        name='Range of y axis',
        size=2,
        update=range_updated,
        default=DataManager().get_range('z'),
    )

    z_step: bpy.props.FloatProperty(
        name='Step of z axis',
        default=DataManager().get_step_size('z')
    )

    z_position: bpy.props.EnumProperty(
        name='Z Axis Pos',
        items=(
            ('FRONT', 'Front', 'Left front corner'),
            ('BACK', 'Back', 'Left back corner'),
            ('RIGHT', 'Right', 'Right front corner'),
        ),
        default='FRONT'
    )

    thickness: bpy.props.FloatProperty(
        name='Thickness',
        min=0.001,
        max=0.02,
        default=0.005,
    )

    tick_mark_height: bpy.props.FloatProperty(
        name='Tick Mark Height',
        default=0.015,
        min=0.001,
        max=0.02,
    )

    padding: bpy.props.FloatProperty(
        name='Padding',
        default=0.1,
        min=0,
    )

    text_size: bpy.props.FloatProperty(
        name='Text size',
        default=0.05,
    )

    number_format: bpy.props.EnumProperty(
        name='Format',
        items=(
            ('0', 'Decimal', '123.456'),
            ('1', 'Scientific', '1.23e+05')
        )
    )

    decimal_places: bpy.props.IntProperty(
        name='Decimal places',
        default=2,
        min=0
    )


class DV_HeaderPropertyGroup(bpy.types.PropertyGroup):
    '''Header settings property group'''
    create: bpy.props.BoolProperty(
        name='Create header',
        default=True,
    )

    text: bpy.props.StringProperty(
        name='Text',
        default='None'
    )

    size: bpy.props.FloatProperty(
        name='Size',
        default=0.07,
        min=0.01,
    )


class DV_LabelPropertyGroup(bpy.types.PropertyGroup):
    '''Label settings, used with AxisFactory with AxisPropertyGroup'''
    create: bpy.props.BoolProperty(
        name='Create labels',
        default=True
    )

    from_data: bpy.props.BoolProperty(
        name='From data',
        default=True
    )

    x_label: bpy.props.StringProperty(
        name='X',
        default='X Label'
    )

    y_label: bpy.props.StringProperty(
        name='Y',
        default='Y Label'
    )

    z_label: bpy.props.StringProperty(
        name='Z',
        default='Z Label'
    )


class DV_ColorPropertyGroup(bpy.types.PropertyGroup):
    '''General color settings, ment to be used with ColorFactory'''
    use_shader: bpy.props.BoolProperty(
        name='Use Nodes',
        default=True,
        description='Uses Node Shading to color created objects. Not using this option may create material for every chart object when not using constant color type'
    )

    color_type: bpy.props.EnumProperty(
        name='Color Type',
        items=(
            ('0', 'Gradient', 'Gradient based on value'),
            ('1', 'Constant', 'One color'),
            ('2', 'Random', 'Random colors'),
        ),
        default='0',
        description='Type of coloring for chart'
    )

    color_shade: bpy.props.FloatVectorProperty(
        name='Base Color',
        subtype='COLOR',
        default=(0.0, 0.0, 1.0),
        min=0.0,
        max=1.0,
        description='Base color shade to work with'
    )


class DV_AnimationPropertyGroup(bpy.types.PropertyGroup):
    animate: bpy.props.BoolProperty(
        name='Animate',
        default=False
    )

    key_spacing: bpy.props.IntProperty(
        name='Keyframe spacing',
        default=20,
        min=1
    )


class DV_LegendPropertyGroup(bpy.types.PropertyGroup):
    create: bpy.props.BoolProperty(
        name='Create Legend'
    )

    position: bpy.props.EnumProperty(
        name='Position',
        items=(
            ('Right', 'Right', 'Legend on the right side'),
            ('Left', 'Left', 'Legend on the left side'),
        )
    )

    item_size: bpy.props.FloatProperty(
        name='Item Size',
        min=0.01,
        max=0.5,
        default=0.065,
    )


class DV_GeneralPropertyGroup(bpy.types.PropertyGroup):
    container_size: bpy.props.FloatVectorProperty(
        name='Container size',
        default=(1.0, 1.0, 1.0),
        size=3,
    )
