import bpy


class ChartListItem_PG(bpy.types.PropertyGroup):
    chart_id: bpy.props.IntProperty(
        name='Chart ID',
        default=0
    )
    name: bpy.props.StringProperty(
        name='Chart Name',
        default=''
    )


class ChartManager:
    class __ChartManager:
        def __init__(self):
            self.chart_list = {}
            bpy.types.Scene.chart_list = bpy.props.CollectionProperty(type=ChartListItem_PG)
            bpy.types.Scene.chart_list_index = bpy.props.IntProperty()

        def add_chart(self, chart_id, obj):
            self.chart_list[str(chart_id)] = obj
            item = bpy.context.scene.chart_list.add()
            item.chart_id = chart_id
            item.name = obj.name

        def remove_chart(self):
            # TODO not generic
            scn = bpy.context.scene
            chart_id = scn.chart_list[scn.chart_list_index].chart_id

            obj_to_del = self.chart_list[str(chart_id)]
            obj_to_del.select_set(True)
            for child in obj_to_del.children:
                child.select_set(True)
                if child.children:
                    for subchild in child.children:
                        subchild.select_set(True)
            bpy.ops.object.delete()

            del self.chart_list[str(chart_id)]
            scn.chart_list.remove(scn.chart_list_index)

        def clean(self):
            bpy.context.scene.chart_list.clear()
            del bpy.types.Scene.chart_list
            del bpy.types.Scene.chart_list_index

    instance = None

    def __new__(cls):
        if not ChartManager.instance:
            ChartManager.instance = ChartManager.__ChartManager()
        return ChartManager.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
