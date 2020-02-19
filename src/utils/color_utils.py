from mathutils import Vector
from colorsys import hsv_to_rgb, rgb_to_hsv


def random_col_gen():
    ...


def color_variety_gen():
    ...


def rgb_col_gen(length, r, g, b):
    base_color = Vector((r, g, b))
    step_size = 1.0 / length
    step_size_vec = Vector((step_size, step_size, step_size, 0))
    for i in range(0, length):
        base_color = base_color - step_size_vec
        yield base_color


def reverse_iterator(iter):
    return reversed(list(iter))


def sat_col_gen(length, r, g, b):
    base_color_hsv = Vector(rgb_to_hsv(r, g, b))
    step_size = 1.0 / length
    step_size_vec = Vector((0, step_size, 0))
    for i in range(0, length):
        base_color_hsv = base_color_hsv - step_size_vec
        yield hsv_to_rgb(*vec3_to_triplet(base_color_hsv))


def vec3_to_triplet(vec):
    return (vec[0], vec[1], vec[2])


def color_to_triplet(col):
    return (col.r, col.g, col.b)
