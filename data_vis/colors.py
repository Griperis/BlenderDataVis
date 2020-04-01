import bpy
import random
from enum import Enum
from colorsys import rgb_to_hsv, hsv_to_rgb


class ColorType(Enum):
    Constant = 0
    Random = 1
    Gradient = 2

    def str_to_type(value):
        if str(value) == '0' or value == 'Constant':
            return ColorType.Constant
        if str(value) == '1' or value == 'Random':
            return ColorType.Random
        if str(value) == '2' or value == 'Gradient':
            return ColorType.Gradient


class NodeShader:
    def __init__(self, base_color, shader_type, scale=1.0, location_z=0):
        self.base_color = self.__add_alpha(base_color, 1)
        self.shader_type = shader_type
        self.scale = scale

        if self.shader_type == ColorType.Random:
            self.material = self.create_random_shader()
        elif self.shader_type == ColorType.Constant:
            self.material = self.create_const_shader()
        elif self.shader_type == ColorType.Gradient:
            self.material = self.create_gradient_shader(location_z)
        else:
            raise AttributeError('Unsupported shader type!')

    def create_random_shader(self):
        material = bpy.data.materials.new(name='DV_ChartMat')
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get('Principled BSDF')

        cr_node = nodes.new('ShaderNodeValToRGB')
        cr_node.location = (-300, 0)

        cr_node.color_ramp.elements.new(position=0.5)
        cr_node.color_ramp.elements[0].color = (1, 0, 0, 1)
        cr_node.color_ramp.elements[0].position = 0.1
        cr_node.color_ramp.elements[1].color = (0, 1, 0, 1)
        cr_node.color_ramp.elements[2].color = (0, 0, 1, 1)
        cr_node.color_ramp.elements[2].position = 0.9

        oi_node = nodes.new('ShaderNodeObjectInfo')
        oi_node.location = (-900, 0)

        links = material.node_tree.links
        links.new(oi_node.outputs[4], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

    def create_const_shader(self):
        material = bpy.data.materials.new(name='DV_ChartMat')
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get('Principled BSDF')

        cr_node = nodes.new('ShaderNodeValToRGB')
        cr_node.location = (-300, 0)

        cr_node.color_ramp.elements[0].color = self.base_color
        cr_node.color_ramp.elements[1].color = self.base_color

        mul_node = nodes.new('ShaderNodeMath')
        mul_node.location = (-500, 0)

        # normalize
        mul_node.operation = 'MULTIPLY'
        mul_node.inputs[1].default_value = self.scale

        xyz_sep_node = nodes.new('ShaderNodeSeparateXYZ')
        xyz_sep_node.location = (-700, 0)

        oi_node = nodes.new('ShaderNodeObjectInfo')
        oi_node.location = (-900, 0)

        links = material.node_tree.links
        links.new(oi_node.outputs[0], xyz_sep_node.inputs[0])
        links.new(xyz_sep_node.outputs[2], mul_node.inputs[0])
        links.new(mul_node.outputs[0], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

    def create_gradient_shader(self, location_z):
        material = bpy.data.materials.new(name='DV_ChartMat')
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get('Principled BSDF')

        cr_node = nodes.new('ShaderNodeValToRGB')
        cr_node.location = (-300, 0)
    
        cr_node.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr_node.color_ramp.elements[1].color = self.base_color

        mul_node = nodes.new('ShaderNodeMath')
        mul_node.location = (-500, 0)

        # normalize
        mul_node.operation = 'MULTIPLY'
        mul_node.inputs[1].default_value = self.scale

        # Normalize the position when creating shader
        sub_node = nodes.new('ShaderNodeMath')
        sub_node.location = (-700, 0)
        sub_node.operation = 'SUBTRACT'
        sub_node.inputs[1].default_value = location_z

        xyz_sep_node = nodes.new('ShaderNodeSeparateXYZ')
        xyz_sep_node.location = (-900, 0)

        oi_node = nodes.new('ShaderNodeObjectInfo')
        oi_node.location = (-1100, 0)

        links = material.node_tree.links
        links.new(oi_node.outputs[0], xyz_sep_node.inputs[0])
        links.new(xyz_sep_node.outputs[2], sub_node.inputs[0])
        links.new(sub_node.outputs[0], mul_node.inputs[0])
        links.new(mul_node.outputs[0], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

    def get_material(self, *args):
        return self.material

    def __add_alpha(self, color, alpha):
        return (color[0], color[1], color[2], alpha)


class ColorGen:
    def __init__(self, base_color, color_type, value_range):
        self.base_color = rgb_to_hsv(*base_color)
        self.value_range = value_range
        self.color_type = color_type
        if self.color_type == ColorType.Constant:
            self.material = bpy.data.materials.new(name='DV_ChartMat')
            self.material.diffuse_color = (*base_color, 1.0)
    
    def get_material(self, value=1.0):
        if self.color_type == ColorType.Constant:
            return self.material
        elif self.color_type == ColorType.Gradient:
            material = bpy.data.materials.new(name='DV_ChartMat')
            norm = (value - self.value_range[0]) / (self.value_range[1] - self.value_range[0])
            color = hsv_to_rgb(self.base_color[0], self.base_color[1] * norm, self.base_color[2])
            material.diffuse_color = (*color, 1.0)
            return material
        elif self.color_type == ColorType.Random:
            material = bpy.data.materials.new(name='DV_ChartMat')
            material.diffuse_color = (*hsv_to_rgb(random.random(), 1.0, 1.0), 1.0)
            return material


class ColoringFactory:
    def __init__(self, base_color, color_type, use_shader):
        self.base_color = base_color
        self.color_type = color_type
        self.use_shader = use_shader

    def create(self, value_range=(0, 1), scale=1.0, location_z=0):
        if self.use_shader:
            return NodeShader(self.base_color, self.color_type, scale, location_z)
        else:
            return ColorGen(self.base_color, self.color_type, value_range)
