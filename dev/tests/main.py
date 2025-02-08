import bpy
import unittest
import os
import sys
import logging
import itertools

# Add the tests directory to the path, to be able to import it in Blender's python
# environment.
TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(TESTS_DIR)
try:
    from tests import utils
finally:
    sys.path.remove(TESTS_DIR)


logger = logging.getLogger("data_vis")


class DataVisTestCase(unittest.TestCase):
    def setUp(self):
        self.clean_scene()
        self.data_folder = "dev/tests/data"
        utils.install_addon("dev/tests/intermediate/data_vis_3.0.0.zip", "data_vis")
        super().setUp()

    def tearDown(self):
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
    def test_add_bar_chart(self): ...

    def test_add_line_chart(self): ...

    def test_add_point_chart(self): ...

    def test_add_pie_chart(self): ...

    def test_add_surface_chart(self): ...


class TestAddAxis(DataVisTestCase):
    def test_add_categorical_axis(self): ...

    def test_add_numerical_axis(self): ...


class TestAddLabels(DataVisTestCase):
    def test_add_label(self): ...


class TestAddAnimation(DataVisTestCase):
    def test_animate_data(self): ...

    def test_add_in_animation(self): ...

    def test_add_out_animation(self): ...


if __name__ == "__main__":
    unittest.main(argv=["main"])
