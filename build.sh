#!/bin/bash

VERSION="3.0.0"
BUILDS_FOLDER="builds"

rm -rf ${BUILDS_FOLDER}/data_vis
mkdir -p ${BUILDS_FOLDER}/data_vis

# copy addon source files, remove pycache and site-packages
cp -r data_vis/* ${BUILDS_FOLDER}/data_vis
cp -r data_vis/blender_manifest.toml ${BUILDS_FOLDER}/data_vis
rm -rf `find ${BUILDS_FOLDER}/data_vis -type d -name __pycache__`
rm -rf `find ${BUILDS_FOLDER}/data_vis -type d -name site-packages`

# change version in bl_info to match one in this file
sed -i "s/'version': ([0-9], [0-9], [0-9])/'version': (`echo ${VERSION} | sed -e 's/\./, /g'`)/" ${BUILDS_FOLDER}/data_vis/__init__.py
# change version in blender_manifest to match one in this file
sed -i "s/\bversion\b = \"[0-9]\.[0-9]\.[0-9]\"/version = \"`echo ${VERSION}`\"/" ${BUILDS_FOLDER}/data_vis/blender_manifest.toml

# remove old zip, zip everything
rm -f data_vis*.zip
cd ${BUILDS_FOLDER}; zip -r ../data_vis_${VERSION}.zip data_vis/*
echo "Release zip saved at 'data_vis_${VERSION}.zip'"