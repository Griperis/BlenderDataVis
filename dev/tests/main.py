import bpy
import unittest
import os
import sys
import logging
import typing
import itertools
import json
import argparse

# Add the tests directory to the path, to be able to import it in Blender's python
# environment.
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(TESTS_DIR)
try:
    from tests import utils
finally:
    sys.path.remove(TESTS_DIR)


logger = logging.getLogger("data_vis")

_DEFAULT_ADDON_ZIP = "dev/tests/intermediate/data_vis_3.0.0.zip"


def _count_action_fcurves(action: bpy.types.Action) -> int:
    if bpy.app.version >= (5, 0, 0):
        return sum(
            len(channelbag.fcurves)
            for layer in action.layers
            for strip in layer.strips
            for channelbag in strip.channelbags
        )
    return len(action.fcurves)


def _parse_addon_zip() -> str:
    """Read the addon ZIP path from args after '--', falling back to the default."""
    if "--" in sys.argv:
        extra = sys.argv[sys.argv.index("--") + 1 :]
        parser = argparse.ArgumentParser()
        parser.add_argument("addon_zip", nargs="?", default=_DEFAULT_ADDON_ZIP)
        args, _ = parser.parse_known_args(extra)
        return args.addon_zip
    return _DEFAULT_ADDON_ZIP


class DataVisTestCase(unittest.TestCase):
    def setUp(self):
        self.clean_scene()
        self.data_folder = "dev/tests/data"
        utils.install_addon(_parse_addon_zip(), "data_vis")
        super().setUp()

    def tearDown(self):
        bpy.context.scene.data_list.clear()
        bpy.context.scene.data_list_index = 0
        utils.uninstall_addon("data_vis")
        super().tearDown()

    def load_data(self, filename: str) -> str:
        data_path = os.path.abspath(os.path.join(self.data_folder, filename))
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")

        bpy.ops.ui.dv_load_data(filepath=data_path)
        return data_path

    def clean_scene(self):
        bpy.data.batch_remove(
            itertools.chain(
                bpy.data.objects,
                bpy.data.materials,
                bpy.data.node_groups,
                bpy.data.meshes,
            )
        )

    def find_modifiers_by_node_group_name(
        self, obj: bpy.types.Object, node_group_name: str
    ) -> typing.Set[bpy.types.Modifier]:
        return {
            mod
            for mod in obj.modifiers
            if mod.type == "NODES"
            and mod.node_group is not None
            and mod.node_group.name == node_group_name
        }

    def assertChartComponent(self, datablock: bpy.types.ID) -> None:
        self.assertIn("DV_Component", datablock)
        self.assertTrue(datablock["DV_Component"])

    def assertDataTypeStored(self, chart_obj: bpy.types.Object) -> None:
        self.assertIn("DV_DataType", chart_obj)
        prop = json.loads(chart_obj["DV_DataType"])
        self.assertIn("data_type", prop)
        self.assertIn("shape", prop)

    def assertNodesModifier(self, chart_obj: bpy.types.Object, group_name: str) -> None:
        self.assertGreaterEqual(len(chart_obj.modifiers), 1)
        modifiers = self.find_modifiers_by_node_group_name(chart_obj, group_name)
        self.assertGreaterEqual(len(modifiers), 1)

    def assertNodesModifierInFront(
        self,
        obj: bpy.types.Object,
        first_node_group_name: str,
        second_node_group_name: str,
    ) -> None:
        first_mod = self.find_modifiers_by_node_group_name(
            obj, first_node_group_name
        ).pop()
        second_mod = self.find_modifiers_by_node_group_name(
            obj, second_node_group_name
        ).pop()
        self.assertLess(
            obj.modifiers.find(first_mod.name),
            obj.modifiers.find(second_mod.name),
        )


class TestLoadData(DataVisTestCase):
    def test_load_multiple(self):
        data_1_path = self.load_data("species_2D.csv")
        data_2_path = self.load_data("x+y_3D.csv")
        self.assertEqual(len(bpy.context.scene.data_list), 2)
        self.assertDataLoadedInScene(data_1_path)
        self.assertDataLoadedInScene(data_2_path)

    def test_load_categorical(self):
        import data_vis

        data_path = self.load_data("species_2D.csv")
        dm = data_vis.DataManager()
        # Pre 3.0 API
        self.assertEqual(os.path.abspath(dm.filepath), data_path)
        self.assertDictEqual(dm.ranges, {"x": [0, 5], "z": [1.0, 15.0]})
        self.assertEqual(dm.lines, 6)
        self.assertEqual(dm.predicted_data_type, data_vis.DataType.Categorical)
        self.assertEqual(dm.dimensions, 2)
        self.assertEqual(dm.has_labels, True)
        self.assertEqual(dm.labels, ("species", "count"))
        self.assertEqual(dm.animable, False)
        self.assertEqual(dm.tail_length, -1)

        # 3.0 API
        self.assertSetEqual(
            data_vis.geonodes.data.get_data_types(),
            {data_vis.geonodes.data.DataTypeValue.CATEGORIC_Data2D},
        )

        chart_data = dm.get_chart_data()
        self.assertTupleEqual(chart_data.parsed_data.shape, (6, 2))
        self.assertEqual(chart_data.lines, 6)
        self.assertEqual(chart_data.labels, ("species", "count"))

    def test_load_numerical(self):
        import data_vis

        data_path = self.load_data("x+y_3D.csv")
        dm = data_vis.DataManager()
        # Pre 3.0 API
        self.assertEqual(os.path.abspath(dm.filepath), data_path)
        self.assertDictEqual(
            dm.ranges,
            {"x": [0.0, 8.0], "y": [0.0, 8.0], "z": [0.0, 64.0], "w": [0.0, 64.0]},
        )
        self.assertEqual(dm.lines, 81)
        self.assertEqual(dm.predicted_data_type, data_vis.DataType.Numerical)
        self.assertEqual(dm.dimensions, 3)
        self.assertEqual(dm.has_labels, True)
        self.assertEqual(dm.labels, ("x", "y", "x+y"))
        self.assertEqual(dm.animable, False)
        self.assertEqual(dm.tail_length, 0)

        # 3.0 API
        self.assertSetEqual(
            data_vis.geonodes.data.get_data_types(),
            {
                # 3D data can be used as 2D, or 2D + animation / weight
                data_vis.geonodes.data.DataTypeValue.Data2D,
                data_vis.geonodes.data.DataTypeValue.Data2DW,
                data_vis.geonodes.data.DataTypeValue.Data2DA,
                data_vis.geonodes.data.DataTypeValue.Data3D,
            },
        )

        chart_data = dm.get_chart_data()
        self.assertTupleEqual(chart_data.parsed_data.shape, (81, 3))
        self.assertEqual(chart_data.lines, 81)
        self.assertEqual(chart_data.labels, ("x", "y", "x+y"))

    def test_load_numerical_animable(self):
        import data_vis

        data_path = self.load_data("function-simple_3D_anim.csv")
        dm = data_vis.DataManager()
        # Pre 3.0 API
        self.assertEqual(os.path.abspath(dm.filepath), data_path)
        self.assertDictEqual(
            dm.ranges,
            {
                "x": [0.0, 1.0],
                "y": [0.0, 1.0],
                "z": [0.0, 3.0],
                "w": [0.0, 3.0],
                "z_anim": [0.0, 3.0],
            },
        )
        self.assertEqual(dm.lines, 4)
        self.assertEqual(dm.predicted_data_type, data_vis.DataType.Numerical)
        self.assertEqual(dm.dimensions, 3)
        self.assertEqual(dm.has_labels, True)
        self.assertEqual(dm.labels, ("x", "y", "res"))
        self.assertEqual(dm.animable, True)
        self.assertEqual(dm.tail_length, 4)

        # 3.0 API
        self.assertSetEqual(
            data_vis.geonodes.data.get_data_types(),
            {
                data_vis.geonodes.data.DataTypeValue.Data2D,
                data_vis.geonodes.data.DataTypeValue.Data2DW,
                data_vis.geonodes.data.DataTypeValue.Data2DA,
                data_vis.geonodes.data.DataTypeValue.Data3D,
                data_vis.geonodes.data.DataTypeValue.Data3DA,
                data_vis.geonodes.data.DataTypeValue.Data3DW,
            },
        )

        chart_data = dm.get_chart_data()
        self.assertTupleEqual(chart_data.parsed_data.shape, (4, 7))
        self.assertEqual(chart_data.lines, 4)
        self.assertEqual(chart_data.labels, ("x", "y", "res"))

    def assertDataLoadedInScene(self, filepath: str):
        data_name = os.path.basename(filepath)
        found = False
        for item in bpy.context.scene.data_list:
            if item.name != data_name:
                continue

            found = True
            self.assertEqual(item.name, data_name)
            self.assertEqual(item.filepath, filepath)
            # TODO: Assert data_info equal?

        self.assertTrue(found)


class TestAddCharts(DataVisTestCase):
    def test_add_chart_no_data(self):
        self.assertEqual(len(bpy.context.scene.data_list), 0)
        self.assertFalse(bpy.ops.data_vis.geonodes_bar_chart.poll())
        self.assertFalse(bpy.ops.data_vis.geonodes_line_chart.poll())
        self.assertFalse(bpy.ops.data_vis.geonodes_point_chart.poll())
        self.assertFalse(bpy.ops.data_vis.geonodes_pie_chart.poll())
        self.assertFalse(bpy.ops.data_vis.geonodes_surface_chart.poll())

    def test_added_chart_selected_and_active(self):
        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        self.assertEqual(len(bpy.context.selected_objects), 1)
        self.assertIsNotNone(bpy.context.active_object)
        self.assertChartComponent(bpy.context.active_object)
        self.assertDataTypeStored(bpy.context.active_object)
        self.assertTrue(bpy.context.active_object.name.startswith("DV_"))

    def test_add_bar_chart(self):
        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        self.assertChartComponent(bpy.context.active_object)
        self.assertDataTypeStored(bpy.context.active_object)
        self.assertNodesModifier(bpy.context.active_object, "DV_BarChart")
        self.assertNodesModifier(bpy.context.active_object, "DV_Data")
        self.assertNodesModifierInFront(
            bpy.context.active_object, "DV_Data", "DV_BarChart"
        )

    def test_add_line_chart(self):
        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_line_chart()
        self.assertChartComponent(bpy.context.active_object)
        self.assertDataTypeStored(bpy.context.active_object)
        self.assertNodesModifier(bpy.context.active_object, "DV_LineChart")
        self.assertNodesModifier(bpy.context.active_object, "DV_Data")
        self.assertNodesModifierInFront(
            bpy.context.active_object, "DV_Data", "DV_LineChart"
        )

    def test_add_point_chart(self):
        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_point_chart()
        self.assertChartComponent(bpy.context.active_object)
        self.assertDataTypeStored(bpy.context.active_object)
        self.assertNodesModifier(bpy.context.active_object, "DV_PointChart")
        self.assertNodesModifier(bpy.context.active_object, "DV_Data")
        self.assertNodesModifierInFront(
            bpy.context.active_object, "DV_Data", "DV_PointChart"
        )

    def test_add_pie_chart(self):
        self.load_data("species_2D.csv")
        bpy.ops.data_vis.geonodes_pie_chart()
        self.assertChartComponent(bpy.context.active_object)
        self.assertDataTypeStored(bpy.context.active_object)
        self.assertNodesModifier(bpy.context.active_object, "DV_PieChart")

    def test_add_surface_chart(self):
        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_surface_chart()
        self.assertChartComponent(bpy.context.active_object)
        self.assertDataTypeStored(bpy.context.active_object)
        self.assertNodesModifier(bpy.context.active_object, "DV_SurfaceChart")
        self.assertNodesModifier(bpy.context.active_object, "DV_Data")
        self.assertNodesModifierInFront(
            bpy.context.active_object, "DV_Data", "DV_SurfaceChart"
        )

    def test_add_pie_chart_invalid_data(self):
        self.load_data("x+y_3D.csv")
        self.assertFalse(bpy.ops.data_vis.geonodes_pie_chart.poll())

    def test_add_surface_chart_invalid_data(self):
        self.load_data("species_2D.csv")
        self.assertFalse(bpy.ops.data_vis.geonodes_surface_chart.poll())


class TestAddAxis(DataVisTestCase):
    def test_add_categorical_axis(self):
        import data_vis

        self.load_data("species_2D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        bpy.ops.data_vis.add_axis(
            axis="X",
            axis_type=data_vis.geonodes.components.AxisType.CATEGORICAL,
            pass_invoke=True,
        )
        modifiers = self.find_modifiers_by_node_group_name(
            bpy.context.active_object, "DV_CategoricalAxis"
        )
        self.assertEqual(len(modifiers), 1)

    def test_add_numerical_axis(self):
        import data_vis

        self.load_data("species_2D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        bpy.ops.data_vis.add_axis(
            axis="Z",
            axis_type=data_vis.geonodes.components.AxisType.NUMERIC,
            pass_invoke=True,
        )
        modifiers = self.find_modifiers_by_node_group_name(
            bpy.context.active_object, "DV_NumericAxis"
        )
        self.assertEqual(len(modifiers), 1)


class TestModifierOrdering(DataVisTestCase):
    def test_axis_after_chart_modifier(self):
        import data_vis

        self.load_data("species_2D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        bpy.ops.data_vis.add_axis(
            axis="X",
            axis_type=data_vis.geonodes.components.AxisType.CATEGORICAL,
            pass_invoke=True,
        )
        self.assertNodesModifierInFront(
            bpy.context.active_object, "DV_BarChart", "DV_CategoricalAxis"
        )

    def test_axis_after_chart_modifier_numerical(self):
        import data_vis

        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        bpy.ops.data_vis.add_axis(
            axis="Z",
            axis_type=data_vis.geonodes.components.AxisType.NUMERIC,
            pass_invoke=True,
        )
        self.assertNodesModifierInFront(
            bpy.context.active_object, "DV_BarChart", "DV_NumericAxis"
        )

    def test_data_labels_after_chart_modifier(self):
        self.load_data("species_2D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        bpy.ops.data_vis.add_data_labels()
        self.assertNodesModifierInFront(
            bpy.context.active_object, "DV_BarChart", "DV_DataLabels"
        )

    def test_multiple_axes_after_chart_modifier(self):
        import data_vis

        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        bpy.ops.data_vis.add_axis(
            axis="X",
            axis_type=data_vis.geonodes.components.AxisType.NUMERIC,
            pass_invoke=True,
        )
        bpy.ops.data_vis.add_axis(
            axis="Z",
            axis_type=data_vis.geonodes.components.AxisType.NUMERIC,
            pass_invoke=True,
        )
        chart_obj = bpy.context.active_object
        # Both axis modifiers must come after the chart modifier
        axis_mods = self.find_modifiers_by_node_group_name(chart_obj, "DV_NumericAxis")
        self.assertEqual(len(axis_mods), 2)
        chart_mod_idx = list(chart_obj.modifiers).index(
            self.find_modifiers_by_node_group_name(chart_obj, "DV_BarChart").pop()
        )
        for mod in axis_mods:
            self.assertGreater(chart_obj.modifiers.find(mod.name), chart_mod_idx)


class TestDataTypeProperty(DataVisTestCase):
    def _get_stored_prop(self, chart_obj):
        import data_vis

        return data_vis.geonodes.data.get_chart_data_info(chart_obj)

    def test_data_type_stored_numerical_2d(self):
        import data_vis

        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data2D
        )
        info = self._get_stored_prop(bpy.context.active_object)
        self.assertIsNotNone(info)
        self.assertEqual(info["data_type"], data_vis.geonodes.data.DataTypeValue.Data2D)
        self.assertIn("shape", info)
        self.assertIn("min", info)
        self.assertIn("max", info)

    def test_data_type_stored_categorical(self):
        import data_vis

        self.load_data("species_2D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        info = self._get_stored_prop(bpy.context.active_object)
        self.assertIsNotNone(info)
        self.assertEqual(
            info["data_type"], data_vis.geonodes.data.DataTypeValue.CATEGORIC_Data2D
        )

    def test_data_type_stored_animated(self):
        import data_vis

        self.load_data("function-simple_3D_anim.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data2DA
        )
        info = self._get_stored_prop(bpy.context.active_object)
        self.assertIsNotNone(info)
        self.assertEqual(
            info["data_type"], data_vis.geonodes.data.DataTypeValue.Data2DA
        )
        self.assertTrue(
            data_vis.geonodes.data.DataTypeValue.is_animated(info["data_type"])
        )

    def test_data_type_helpers_consistent(self):
        import data_vis

        self.load_data("x+y_3D.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data3D
        )
        chart_obj = bpy.context.active_object
        data_type = data_vis.geonodes.data.get_chart_data_type(chart_obj)
        self.assertEqual(data_type, data_vis.geonodes.data.DataTypeValue.Data3D)
        self.assertTrue(data_vis.geonodes.data.DataTypeValue.is_3d(data_type))
        self.assertFalse(data_vis.geonodes.data.DataTypeValue.is_animated(data_type))
        self.assertFalse(data_vis.geonodes.data.DataTypeValue.is_categorical(data_type))

    def test_get_chart_data_type_returns_none_for_non_chart(self):
        import data_vis

        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.active_object
        data_type = data_vis.geonodes.data.get_chart_data_type(cube)
        self.assertEqual(data_type, "None")


class TestAddLabels(DataVisTestCase):
    def test_add_above_data_labels(self):
        self.load_data("species_2D.csv")
        bpy.ops.data_vis.geonodes_bar_chart()
        bpy.ops.data_vis.add_data_labels()
        self.assertNodesModifier(bpy.context.active_object, "DV_DataLabels")


class TestAddAnimation(DataVisTestCase):
    def test_shape_keys_created_2D(self):
        import data_vis

        self.load_data("function-simple_3D_anim.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data2DA
        )
        chart_obj = bpy.context.active_object
        # Basis + 5 columns
        self.assertEqual(len(chart_obj.data.shape_keys.key_blocks), 6)

    def test_shape_keys_created_3D(self):
        import data_vis

        self.load_data("function-simple_3D_anim.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data3DA
        )
        chart_obj = bpy.context.active_object
        # Basis + 4 columns
        self.assertEqual(len(chart_obj.data.shape_keys.key_blocks), 5)

    def test_add_animation(self):
        import data_vis

        self.load_data("function-simple_3D_anim.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data2DA
        )
        bpy.ops.data_vis.animate_data()
        chart_obj = bpy.context.active_object
        self.assertIsNotNone(chart_obj.data.shape_keys.animation_data)
        self.assertEqual(
            _count_action_fcurves(chart_obj.data.shape_keys.animation_data.action), 1
        )

    def test_add_data_transition_animation(self):
        import data_vis

        self.load_data("function-simple_3D_anim.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data2DA
        )
        bpy.context.scene.frame_current = 50
        bpy.ops.data_vis.data_transition_animation(animation_type="GROW_BY_INDEX")
        chart_obj = bpy.context.active_object
        self.assertIsNotNone(chart_obj.animation_data)
        self.assertEqual(_count_action_fcurves(chart_obj.animation_data.action), 1)

    def test_add_data_transition_animation_reversed(self):
        import data_vis

        self.load_data("function-simple_3D_anim.csv")
        bpy.ops.data_vis.geonodes_bar_chart(
            data_type=data_vis.geonodes.data.DataTypeValue.Data2DA
        )
        bpy.context.scene.frame_current = 50
        bpy.ops.data_vis.data_transition_animation(
            animation_type="GROW_BY_INDEX", reverse=True
        )
        chart_obj = bpy.context.active_object
        self.assertIsNotNone(chart_obj.animation_data)
        self.assertEqual(_count_action_fcurves(chart_obj.animation_data.action), 1)


if __name__ == "__main__":
    unittest.main(argv=["main"])
