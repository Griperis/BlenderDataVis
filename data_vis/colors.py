import bpy
from enum import Enum


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
    
    def __init__(self, base_color, shader_type=ColorType.Constant, scale=1.0, location_z=0):
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
        material = bpy.data.materials.new(name='ChartMat')
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
        material = bpy.data.materials.new(name='ChartMat')
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
        material = bpy.data.materials.new(name='ChartMat')
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

    def __add_alpha(self, color, alpha):
        return (color[0], color[1], color[2], alpha)

