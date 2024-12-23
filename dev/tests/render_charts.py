import argparse
import dataclasses
import typing
import os
import sys
import math

os.environ.setdefault("DV_TESTING", "1")

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(TESTS_DIR)
try:
    from tests import utils
finally:
    sys.path.remove(TESTS_DIR)

try:
    import bpy
except ImportError:
    raise RuntimeError("This script must be run from within Blender.")


@dataclasses.dataclass
class ChartConfiguration:
    name: str
    data_file: str
    data_type: str
    operator: typing.Callable
    axis: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    out_rotation: typing.Tuple[float, float, float] = (0, 0, 0)
    out_location: typing.Tuple[float, float, float] = (0, 0, 0)

    @property
    def output_filepath(self) -> str:
        return f"{self.name.replace(' ', '_').lower()}.png"

    @property
    def readable_name(self) -> str:
        return f"{self.name} as '{self.data_type}' from '{self.data_file}'"


CONFIGURATIONS = [
    ChartConfiguration(
        "Bar Chart Categorical 2D",
        "species_2D.csv",
        "Cat_2D",
        bpy.ops.data_vis.geonodes_bar_chart,
        axis={"X": "Categorical", "Z": "Numeric"},
    ),
    ChartConfiguration(
        "Line Chart Categorical 2D",
        "species_2D.csv",
        "Cat_2D",
        bpy.ops.data_vis.geonodes_line_chart,
        axis={"X": "Categorical", "Z": "Numeric"},
    ),
    ChartConfiguration(
        "Point Chart Categorical 2D",
        "species_2D.csv",
        "Cat_2D",
        bpy.ops.data_vis.geonodes_point_chart,
        axis={"X": "Categorical", "Y": "Numeric"},
    ),
    ChartConfiguration(
        "Pie Chart Categorical 2D",
        "species_2D.csv",
        "Cat_2D",
        bpy.ops.data_vis.geonodes_pie_chart,
        axis={"X": "Categorical", "Y": "Numeric"},
        out_rotation=(math.radians(90), 0, 0),
        out_location=(0.5, 0.5, 0.5),
    ),
    ChartConfiguration(
        "Bar Chart Numerical 3D",
        "x+y_3D.csv",
        "3D",
        bpy.ops.data_vis.geonodes_bar_chart,
        axis={"X": "Numeric", "Y": "Numeric", "Z": "Numeric"},
    ),
    ChartConfiguration(
        "Point Chart Numerical 3D",
        "x+y_3D.csv",
        "3D",
        bpy.ops.data_vis.geonodes_point_chart,
        axis={"X": "Numeric", "Y": "Numeric", "Z": "Numeric"},
    ),
    ChartConfiguration(
        "Surface Chart Numerical 3D",
        "x+y_3D.csv",
        "3D",
        bpy.ops.data_vis.geonodes_surface_chart,
        axis={"X": "Numeric", "Y": "Numeric", "Z": "Numeric"},
    ),
]


def get_preferences() -> bpy.types.AddonPreferences:
    return bpy.context.preferences.addons["data_vis"].preferences


def setup_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)

    camera = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    camera.location = (0.5, -3.0, 0.5)
    camera.rotation_euler = (math.radians(90), 0, 0)
    bpy.context.scene.collection.objects.link(camera)
    bpy.context.scene.camera = camera

    light = bpy.data.objects.new("Light", bpy.data.lights.new("Light", "POINT"))
    light.location = (0.5, -2.0, 0.5)
    light.data.energy = 100
    bpy.context.scene.collection.objects.link(light)

    bpy.context.scene.render.resolution_x = 512
    bpy.context.scene.render.resolution_y = 512
    bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"


def render_configurations(
    input_data_dir: str,
    output_dir: str,
):
    for configuration in CONFIGURATIONS:
        setup_scene()
        print(f"Rendering {configuration.readable_name}")
        bpy.ops.ui.dv_load_data(
            filepath=os.path.join(input_data_dir, configuration.data_file)
        )
        configuration.operator(data_type=configuration.data_type)
        bpy.context.active_object.rotation_euler = configuration.out_rotation
        bpy.context.active_object.location = configuration.out_location
        for axis, axis_type in configuration.axis.items():
            bpy.ops.data_vis.add_axis(axis=axis, axis_type=axis_type)
        bpy.context.scene.render.filepath = os.path.join(
            output_dir, configuration.output_filepath
        )
        bpy.ops.render.render(write_still=True)


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :]
    parser = argparse.ArgumentParser()
    parser.add_argument("ADDON_ZIP", type=str, help="Path to the addon .zip file.")
    parser.add_argument(
        "INPUT_DATA_DIR", type=str, help="Path to the input data folder."
    )
    parser.add_argument("OUTPUT_DIR", type=str, help="Path to the output folder.")
    args = parser.parse_args(argv)

    addon_zip = os.path.abspath(args.ADDON_ZIP)
    input_data_dir = os.path.abspath(args.INPUT_DATA_DIR)
    output_dir = os.path.abspath(args.OUTPUT_DIR)

    if not os.path.isfile(addon_zip):
        print(f"The addon .zip file '{addon_zip}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(input_data_dir):
        print(f"The input data folder '{input_data_dir}' does not exist.")
        sys.exit(1)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    with utils.InstalledAddon(addon_zip, "data_vis"):
        render_configurations(input_data_dir, output_dir)


if __name__ == "__main__":
    main()
