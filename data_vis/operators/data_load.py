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
        bpy.data.scenes[0].dv_props.data.clear()
        data_manager = DataManager()
        line_n = data_manager.load_data(self.filepath)

        # with open(self.filepath, 'r') as file:
        #     line_n = 0
        #     for row in file:
        #         line_n += 1
        #         row_prop = bpy.data.scenes[0].dv_props.data.add()
        #         row_prop.value = row

        report_type = {'INFO'}
        if line_n == 0:
            report_type = {'WARNING'}
        self.report(report_type, f'File: {self.filepath}, loaded {line_n} lines!')
        return {'FINISHED'}

