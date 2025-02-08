#!/bin/bash
# Runs automated tests
python dev/build.py --version 3.0.0 --output_folder dev/tests/intermediate --addon_package data_vis
python dev/run_in_blender.py --script_path dev/tests/main.py