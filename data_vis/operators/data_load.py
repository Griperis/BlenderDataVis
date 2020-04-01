import bpy
from data_vis.data_manager import DataManager


class FILE_OT_DVLoadFile(bpy.types.Operator):
    '''
    Loads data from CSV file to property in first scene
    '''
    bl_idname = 'ui.dv_load_data'
    bl_label = 'Load data'
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(
        name='CSV File',
        subtype='FILE_PATH'
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        data_manager = DataManager()
        line_n = data_manager.load_data(self.filepath)

        report_type = {'INFO'}
        if line_n == 0:
            report_type = {'WARNING'}
        self.report(report_type, f'File: {self.filepath}, loaded {line_n} lines!')
        return {'FINISHED'}
