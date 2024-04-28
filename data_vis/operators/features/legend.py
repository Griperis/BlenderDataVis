# File: legend.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Provides Legend class to work with legend

import bpy


class Legend:
    """Handles legend creation"""

    def __init__(self, chart_id, settings):
        """
        Creates instance of legend class
        Parameters:
        chart_id - id of chart
        settings - DV_LegendPropertyGroup
        """
        self.settings = settings
        self.chart_id = chart_id
        self.items = []
        self.get_materials()

    def create(self, container, entries):
        """
        Creates legend container and items
        Parameters:
        container - parent object for legend
        entries - list of tuples to display (material_name, value)
        """
        bpy.ops.object.empty_add()
        self.leg_container = bpy.context.active_object
        self.leg_container.parent = container
        self.leg_container.name = "Legend_" + str(self.chart_id)

        bpy.ops.mesh.primitive_plane_add()
        self.background = bpy.context.active_object
        self.background.data.materials.append(self.legend_mat)
        self.background.active_material = self.legend_mat
        self.background.parent = self.leg_container
        self.background.location = (0, 0, 0)

        size_x = self.create_items(entries)
        padding = 0.1
        self.background.scale = (size_x * 0.5 + padding, 0.5 + padding, 1)
        self.background.location.x = size_x * 0.5 - self.settings.item_size

        if self.settings.position == "Right":
            self.leg_container.location = (1, 0, 0)
        elif self.settings.position == "Left":
            self.leg_container.location = (-1 - size_x, 0, 0)

    def get_materials(self):
        """Gets or creates materials for legend"""
        self.text_mat = bpy.data.materials.get("DV_TextMat_" + str(self.chart_id))
        if self.text_mat is None:
            self.text_mat = bpy.data.materials.new(
                name="DV_TextMat_" + str(self.chart_id)
            )

        self.legend_mat = bpy.data.materials.new(
            name="DV_LegendMat_" + str(self.chart_id)
        )
        self.legend_mat.diffuse_color = (0, 0, 0, 1)

    def create_items(self, entries):
        """Creates legend items"""
        idx = 0
        x_pos = 0
        longest_entry = 0
        size_x = 0

        for mat_name, entry in entries.items():
            y_pos = 2 * idx * (self.settings.item_size + 0.02) - (
                0.5 - self.settings.item_size
            )
            if y_pos >= 0.5 - self.settings.item_size:
                # overflow, reset y increase x
                x_pos += longest_entry * self.settings.item_size
                idx = 0
                y_pos = 2 * idx * (self.settings.item_size + 0.02) - (
                    0.5 - self.settings.item_size
                )
                size_x += longest_entry * self.settings.item_size
                longest_entry = 0
            plane_mat = bpy.data.materials.get(mat_name)
            bpy.ops.mesh.primitive_plane_add()
            plane_obj = bpy.context.object
            plane_obj.parent = self.leg_container
            plane_obj.scale *= self.settings.item_size
            plane_obj.data.materials.append(plane_mat)
            plane_obj.active_material = plane_mat
            plane_obj.location = (x_pos, y_pos, 0.01)

            bpy.ops.object.text_add()
            text_obj = bpy.context.object
            text_obj.parent = self.leg_container
            text_obj.scale *= self.settings.item_size
            text_obj.data.materials.append(self.text_mat)
            text_obj.active_material = self.text_mat
            text_obj.data.body = str(entry)
            text_obj.data.align_y = "CENTER"
            text_obj.location = (x_pos + self.settings.item_size + 0.02, y_pos, 0.01)

            if len(entry) > longest_entry:
                longest_entry = len(entry)

            self.items.append((plane_obj, text_obj))
            idx += 1

        # scale larger with one entry
        if longest_entry == 1:
            longest_entry = 2
        # add last column of items to size and shift it by item size, add padding
        return size_x + longest_entry * self.settings.item_size

    def colorbar(self, material):
        """Creates colorbar with specified material"""
        bpy.ops.mesh.primitive_plane_add()
        plane = bpy.context.active_object
        plane.data.materials.append(material)
        plane.active_material = material
