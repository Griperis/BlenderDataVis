import os
import bpy
import logging
logger = logging.getLogger("data_vis")

from .geonodes.data import DV_DataProperties
from .geonodes.library import MaterialType


EXAMPLE_DATA_FOLDER = 'example_data'
PANEL_CLASS = None

def update_space_type(self, context):
    if PANEL_CLASS is None:
        raise RuntimeError(f"Panel class was not provided to preferences!")
    try:
        if hasattr(bpy.types, 'DV_PT_data_load'):
            bpy.utils.unregister_class(PANEL_CLASS)
        PANEL_CLASS.bl_space_type = self.ui_space_type
        bpy.utils.register_class(PANEL_CLASS)
    except Exception as e:
        logger.exception('Setting Space Type error')


def update_category(self, context):
    if PANEL_CLASS is None:
        raise RuntimeError(f"Panel class was not provided to preferences!")
    try:
        if hasattr(bpy.types, 'DV_PT_data_load'):
            bpy.utils.unregister_class(PANEL_CLASS)
        PANEL_CLASS.bl_category = self.ui_category
        bpy.utils.register_class(PANEL_CLASS)
    except Exception as e:
        logger.exception('Setting Category error')


def update_region_type(self, context):
    if PANEL_CLASS is None:
        raise RuntimeError(f"Panel class was not provided to preferences!")
    try:
        if hasattr(bpy.types, 'DV_PT_data_load'):
            bpy.utils.unregister_class(PANEL_CLASS)
        PANEL_CLASS.bl_region_type = self.ui_region_type
        bpy.utils.register_class(PANEL_CLASS)
    except Exception as e:
        logger.exception('Setting Region Type error')


def get_example_data_path():
    return os.path.join(
        bpy.utils.script_path_user(),
        "addons",
        __package__,
        EXAMPLE_DATA_FOLDER
    )

class DV_Preferences(bpy.types.AddonPreferences):
    '''Preferences for data visualisation addon'''
    bl_idname = 'data_vis'

    ui_region_type: bpy.props.StringProperty(
        name='Region Type',
        default='UI',
        update=update_region_type
    )
    ui_space_type: bpy.props.StringProperty(
        name='Space Type',
        default='VIEW_3D',
        update=update_space_type
    )

    ui_category: bpy.props.StringProperty(
        name='Panel Category',
        default='DataVis',
        update=update_category
    )

    debug: bpy.props.BoolProperty(
        name='Toggle Debug Options',
        default=False
    )

    show_data_examples: bpy.props.BoolProperty(
        name='Show Data Examples',
        description='If true then data examples are shown and can be loaded',
        default=False,
    )

    example_category: bpy.props.EnumProperty(
        name='Data Type',
        description='Types of example data',
        items=lambda self, context: self.get_example_data_categories(context)
    )

    example_data: bpy.props.EnumProperty(
        name='Example Data',
        description='Select example data to load',
        items=lambda self, context: self.get_example_data(context)
    )

    addon_mode: bpy.props.EnumProperty(
        name='Addon Mode',
        description='Select mode for generating charts. Mode "Geometry Nodes" is recommended',
        items=lambda self, context: self.get_addon_mode(context),
    )

    data: bpy.props.PointerProperty(type=DV_DataProperties)

    color_type: bpy.props.EnumProperty(
        name='Color Type',
        items=MaterialType.as_enum_items(),
    )

    def get_addon_mode(self, context: bpy.types.Context):
        ret = []
        if bpy.app.version >= (4, 0, 0):
            ret.append(
                (
                    'GEONODES',
                    'Mode: Geometry Nodes',
                    'Charts and chart components are generated using geometry nodes'
                )
            )
        ret.append(
            (
                'LEGACY',
                'Mode: Legacy',
                'Charts are generated as objects, this was only option to addon version 3.0'
            )
        )
        return ret

    def get_example_data_categories(self, context):
        enum_items = []
        for i, _dir in enumerate(os.listdir(get_example_data_path())):
            # infer icon from data type
            icon = 'QUESTION'
            if _dir == 'categorical':
                icon = 'LINENUMBERS_ON'
            elif _dir == 'numerical':
                icon = 'FORCE_HARMONIC' 

            enum_items.append((_dir, _dir, _dir, icon, i))

        return enum_items

    def get_example_data(self, context):
        enum_items = []
        for file in os.listdir(os.path.join(get_example_data_path(), self.example_category)):
            enum_items.append((file, file, file))

        return sorted(enum_items)

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text='Customize position of addon panel', icon='TOOL_SETTINGS')
        box.prop(self, 'ui_region_type')
        box.prop(self, 'ui_space_type')
        box.prop(self, 'ui_category')
        box.label(text='Check console for possible errors!', icon='ERROR')

        box = layout.box()
        box.label(text='Other Settings', icon='PLUGIN')
        box.prop(self, 'debug')

def get_preferences(context):
    return context.preferences.addons[__package__].preferences