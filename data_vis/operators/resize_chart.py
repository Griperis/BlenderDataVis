import bpy


class OBJECT_OT_ResizeChart(bpy.types.Operator):
    '''Resizes selected chart to new specified dimensions'''
    bl_idname = 'object.resize_chart'
    bl_label = 'Resize Chart'
    bl_options = {'REGISTER'}

    source: bpy.props.EnumProperty(
        items=(
            ('default', 'Default Container Size', 'Resizes chart to dimensions specified in default container size')
        )
    )

    new_dimensions: bpy.props.FloatVectorProperty(

    )
