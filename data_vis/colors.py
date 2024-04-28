# File: colors.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Color related code

import bpy
import random
from enum import Enum
from colorsys import rgb_to_hsv, hsv_to_rgb


class ColorType(Enum):
    """Supported color types"""

    Constant = 0
    Random = 1
    Gradient = (2,)
    Custom = 3

    def str_to_type(value):
        if str(value) == "0" or value == "Gradient":
            return ColorType.Gradient
        if str(value) == "1" or value == "Constant":
            return ColorType.Constant
        if str(value) == "2" or value == "Random":
            return ColorType.Random


class NodeShader:
    """Creates different types of node shaders depending on function arguments"""

    def __init__(
        self,
        container_name,
        base_color,
        shader_type=ColorType.Custom,
        scale=1.0,
        location_z=0,
    ):
        self.base_color = self.__add_alpha(base_color, 1)
        self.shader_type = shader_type
        self.scale = scale
        self.location_z = location_z
        self.container_name = container_name

        if self.shader_type == ColorType.Random:
            self.material = self.create_random_shader()
        elif self.shader_type == ColorType.Constant:
            self.material = self.create_const_shader()
        elif self.shader_type == ColorType.Gradient:
            self.material = self.create_gradient_shader()
        elif self.shader_type != ColorType.Custom:
            raise AttributeError("Unsupported shader type!")

    def create_random_shader(self):
        material = bpy.data.materials.new(name="DV_ChartMat")
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get("Principled BSDF")

        cr_node = nodes.new("ShaderNodeValToRGB")
        cr_node.location = (-300, 0)

        cr_node.color_ramp.elements.new(position=0.5)
        cr_node.color_ramp.elements[0].color = (1, 0, 0, 1)
        cr_node.color_ramp.elements[0].position = 0.1
        cr_node.color_ramp.elements[1].color = (0, 1, 0, 1)
        cr_node.color_ramp.elements[2].color = (0, 0, 1, 1)
        cr_node.color_ramp.elements[2].position = 0.9

        oi_node = nodes.new("ShaderNodeObjectInfo")
        oi_node.location = (-900, 0)

        links = material.node_tree.links
        links.new(oi_node.outputs[4], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

    def create_const_shader(self):
        material = bpy.data.materials.new(name="DV_ChartMat")
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get("Principled BSDF")

        cr_node = nodes.new("ShaderNodeValToRGB")
        cr_node.location = (-300, 0)

        cr_node.color_ramp.elements[0].color = self.base_color
        cr_node.color_ramp.elements[1].color = self.base_color

        mul_node = nodes.new("ShaderNodeMath")
        mul_node.location = (-500, 0)

        # normalize
        mul_node.operation = "MULTIPLY"
        mul_node.inputs[1].default_value = self.scale

        xyz_sep_node = nodes.new("ShaderNodeSeparateXYZ")
        xyz_sep_node.location = (-700, 0)

        oi_node = nodes.new("ShaderNodeObjectInfo")
        oi_node.location = (-900, 0)

        links = material.node_tree.links
        links.new(oi_node.outputs[0], xyz_sep_node.inputs[0])
        links.new(xyz_sep_node.outputs[2], mul_node.inputs[0])
        links.new(mul_node.outputs[0], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

    def create_gradient_shader(self):
        material = bpy.data.materials.new(name="DV_ChartMat")
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get("Principled BSDF")

        cr_node = nodes.new("ShaderNodeValToRGB")
        cr_node.location = (-300, 0)

        cr_node.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr_node.color_ramp.elements[1].color = self.base_color

        sub_node = self.__create_z_sub_node(nodes, material, -700)
        mul_node = self.__create_z_mul_node(nodes, material, -500, self.scale)

        xyz_sep_node = nodes.new("ShaderNodeSeparateXYZ")
        xyz_sep_node.location = (-900, 0)

        oi_node = nodes.new("ShaderNodeObjectInfo")
        oi_node.location = (-1100, 0)

        links = material.node_tree.links
        links.new(oi_node.outputs[0], xyz_sep_node.inputs[0])
        links.new(xyz_sep_node.outputs[2], sub_node.inputs[0])
        links.new(sub_node.outputs[0], mul_node.inputs[0])
        links.new(mul_node.outputs[0], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

    def create_geometry_shader(self):
        material = bpy.data.materials.new(name="DV_ChartMat")
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get("Principled BSDF")

        cr_node = nodes.new("ShaderNodeValToRGB")
        cr_node.location = (-300, 0)

        cr_node.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr_node.color_ramp.elements[1].color = self.base_color

        # Normalize the position when creating shader
        sub_node = self.__create_z_sub_node(nodes, material, -500)
        mul_node = self.__create_z_mul_node(nodes, material, -700, self.scale)

        xyz_sep_node = nodes.new("ShaderNodeSeparateXYZ")
        xyz_sep_node.location = (-900, 0)

        geometry_node = nodes.new("ShaderNodeNewGeometry")
        geometry_node.location = (-1200, 0)

        links = material.node_tree.links
        links.new(geometry_node.outputs[0], xyz_sep_node.inputs[0])
        links.new(xyz_sep_node.outputs[2], sub_node.inputs[0])
        links.new(sub_node.outputs[0], mul_node.inputs[0])
        links.new(mul_node.outputs[0], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

    def get_material(self, *args):
        return self.material

    def __create_z_mul_node(self, nodes, material, location_x, base_scale=1.0):
        mul_node = nodes.new("ShaderNodeMath")
        mul_node.location = (location_x, 0)
        mul_node.operation = "MULTIPLY"
        mul_node.name = "MathMulScale"

        drv = material.node_tree.driver_add(
            'nodes["MathMulScale"].inputs[1].default_value'
        )
        var = drv.driver.variables.new()
        var.type = "TRANSFORMS"
        var.name = "z_scale"

        target = var.targets[0]
        target.id = bpy.data.objects.get(self.container_name)
        target.transform_type = "SCALE_Z"

        drv.driver.expression = f"{base_scale} * (1.0 / {var.name})"

        return mul_node

    def __create_z_sub_node(self, nodes, material, location_x):
        sub_node = nodes.new("ShaderNodeMath")
        sub_node.location = (location_x, 0)
        sub_node.operation = "SUBTRACT"
        sub_node.name = "MathSubLoc"

        drv = material.node_tree.driver_add(
            'nodes["MathSubLoc"].inputs[1].default_value'
        )
        var = drv.driver.variables.new()
        var.type = "TRANSFORMS"
        var.name = "z_pos"

        target = var.targets[0]
        target.id = bpy.data.objects.get(self.container_name)
        target.transform_type = "LOC_Z"
        target.transform_space = "WORLD_SPACE"

        drv.driver.expression = var.name

        return sub_node

    def __add_alpha(self, color, alpha):
        return (color[0], color[1], color[2], alpha)


class ColorGen:
    """Creates materials for every data entry"""

    def __init__(self, base_color, color_type, value_range):
        self.base_color = rgb_to_hsv(*base_color)
        self.value_range = value_range
        self.color_type = color_type
        if self.color_type == ColorType.Constant:
            self.material = bpy.data.materials.new(name="DV_ChartMat")
            self.material.diffuse_color = (*base_color, 1.0)

    def get_material(self, value=1.0):
        """Returns material based ColorType, if ColorType is gradient, values is needed"""
        if self.color_type == ColorType.Constant:
            return self.material
        elif self.color_type == ColorType.Gradient:
            material = bpy.data.materials.new(name="DV_ChartMat")
            norm = (value - self.value_range[0]) / (
                self.value_range[1] - self.value_range[0]
            )
            color = hsv_to_rgb(
                self.base_color[0], self.base_color[1] * norm, self.base_color[2]
            )
            material.diffuse_color = (*color, 1.0)
            return material
        elif self.color_type == ColorType.Random:
            material = bpy.data.materials.new(name="DV_ChartMat")
            material.diffuse_color = (*hsv_to_rgb(random.random(), 1.0, 1.0), 1.0)
            return material


class ColoringFactory:
    """Factory, that can instantiate NodeShader or ColorGen based on similar settings"""

    def __init__(self, container_name, base_color, color_type, use_shader):
        self.container_name = container_name
        self.base_color = base_color
        self.color_type = color_type
        self.use_shader = use_shader

    def create(self, value_range=(0, 1), scale=1.0, location_z=0):
        if self.use_shader:
            return NodeShader(
                self.container_name, self.base_color, self.color_type, scale, location_z
            )
        else:
            return ColorGen(self.base_color, self.color_type, value_range)
