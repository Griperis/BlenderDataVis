TYPES_ENUM = [
    ('multiquadric', 'Multiquadric', '[DEFAULT] sqrt((r/self.epsilon)**2 + 1'),
    ('inverse', 'Inverse', '1.0/sqrt((r/self.epsilon)**2 + 1'),
    ('gaussian', 'Gaussian', 'exp(-(r/self.epsilon)**2'),
    ('linear', 'Linear', 'r'),
    ('cubic', 'Cubic', 'r**3'),
    ('quintic', 'Quintic', 'r**5'),
    ('thin_plate', 'Thin Plate', 'r**2 * log(r)'),
]