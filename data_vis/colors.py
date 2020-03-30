import bpy
from enum import Enum


class NodeShader:
    class Type(Enum):
        Constant = 0
        Random = 1
        Gradient = 2

        def str_to_type(value):
            if str(value) == '0' or value == 'Constant':
                return NodeShader.Type.Constant
            if str(value) == '1' or value == 'Random':
                return NodeShader.Type.Random
            if str(value) == '2' or value == 'Gradient':
                return NodeShader.Type.Gradient

    def __init__(self, base_color, shader_type=Type.Constant):
        self.base_color = self.__add_alpha(base_color, 1)
        self.shader_type = shader_type

        if self.shader_type == NodeShader.Type.Random:
            self.material = self.create_random_shader()
        else:
            self.material = self.create_shader()

    def create_shader(self):
        material = bpy.data.materials.new(name='ChartMat')
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get('Principled BSDF')

        cr_node = nodes.new('ShaderNodeValToRGB')
        cr_node.location = (-300, 0)

        if self.shader_type == NodeShader.Type.Constant:
            cr_node.color_ramp.elements[0].color = self.base_color
            cr_node.color_ramp.elements[1].color = self.base_color
        elif self.shader_type == NodeShader.Type.Gradient:
            cr_node.color_ramp.elements[0].color = (1, 1, 1, 1)
            cr_node.color_ramp.elements[1].color = self.base_color

        math_node = nodes.new('ShaderNodeMath')
        math_node.location = (-500, 0)

        # normalize
        math_node.operation = 'MULTIPLY'
        math_node.inputs[1].default_value = 2.0

        xyz_sep_node = nodes.new('ShaderNodeSeparateXYZ')
        xyz_sep_node.location = (-700, 0)

        oi_node = nodes.new('ShaderNodeObjectInfo')
        oi_node.location = (-900, 0)

        links = material.node_tree.links
        links.new(oi_node.outputs[0], xyz_sep_node.inputs[0])
        links.new(xyz_sep_node.outputs[2], math_node.inputs[0])
        links.new(math_node.outputs[0], cr_node.inputs[0])
        links.new(cr_node.outputs[0], bsdf_node.inputs[0])

        return material

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

    def __add_alpha(self, color, alpha):
        return (color[0], color[1], color[2], alpha)

        

