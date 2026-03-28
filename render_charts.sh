#!/bin/bash
# Runs automated chart rendering for visual comparison, result is in dev/tests/out
# Optional: set BLENDER env var to use a specific Blender executable
# e.g. BLENDER=/path/to/blender sh render_charts.sh
python dev/build.py --version 3.0.0 --output_folder dev/tests/intermediate --addon_package data_vis
BLENDER_ARG=${BLENDER:+--blender "$BLENDER"}
python dev/run_in_blender.py $BLENDER_ARG --script_path dev/tests/render_charts.py -- dev/tests/intermediate/data_vis_3.0.0.zip dev/tests/data/ dev/tests/out