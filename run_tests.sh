#!/bin/bash
# Runs automated tests
# Optional: set BLENDER env var to use a specific Blender executable
# e.g. BLENDER=/path/to/blender sh run_tests.sh
python dev/build.py --version 3.0.0 --output_folder dev/tests/intermediate --addon_package data_vis
BLENDER_ARG=${BLENDER:+--blender "$BLENDER"}
python dev/run_in_blender.py $BLENDER_ARG --script_path dev/tests/main.py -- dev/tests/intermediate/data_vis_3.0.0.zip