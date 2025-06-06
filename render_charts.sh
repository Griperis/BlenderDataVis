#!/bin/bash
# Runs automated chart rendering for visual comparison, result is in dev/tests/out
python dev/build.py --version 3.0.0 --output_folder dev/tests/intermediate --addon_package data_vis
python dev/run_in_blender.py --script_path dev/tests/render_charts.py -- dev/tests/intermediate/data_vis_3.0.0.zip dev/tests/data/ dev/tests/out