import bpy


class NodeShader:
    # Constant
    # Contrast
    # Gradient / Ramp color
    def __init__(self, base_color):
        self.base_color = self.__add_alpha(base_color, 1)
        self.material = self.create_color_ramp()

    def create_color_ramp(self):
        material = bpy.data.materials.new(name='ChartMat')
        material.use_nodes = True

        nodes = material.node_tree.nodes

        bsdf_node = nodes.get('Principled BSDF')

        cr_node = nodes.new('ShaderNodeValToRGB')
        cr_node.location = (-300, 0)

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

    def __add_alpha(self, color, alpha):
        return (color[0], color[1], color[2], alpha)

        

